"""ANNE's first Windows-friendly agent loop."""

from __future__ import annotations

from dataclasses import dataclass

from anne.providers.gemini import GeminiProvider
from anne.agent.github_memory import GitHubMemory


@dataclass
class AgentResult:
    response: str
    learning: str
    confidence: float
    memory_path: str | None


class AnneAgent:
    """Coordinates Gemini reasoning with persistent GitHub memory."""

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine).
You are an experimental AI cognitive agent, not a claim of AGI or consciousness.
Use the stages DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent facts. State uncertainty when evidence is weak.
After answering, produce a learning record that can be safely reused later.
Return exactly this format:
<RESPONSE>
answer for the user
</RESPONSE>
<LEARNING>
1-3 concise reusable facts, insights, preferences, or lessons learned. If nothing new was learned, say: No new durable learning.
</LEARNING>
<CONFIDENCE>
number from 0 to 1
</CONFIDENCE>"""

    def __init__(self, gemini: GeminiProvider, memory: GitHubMemory) -> None:
        self.gemini = gemini
        self.memory = memory

    @staticmethod
    def _section(text: str, name: str) -> str:
        start = f"<{name}>"
        end = f"</{name}>"
        if start in text and end in text:
            return text.split(start, 1)[1].split(end, 1)[0].strip()
        return ""

    def run(self, user_input: str) -> AgentResult:
        context = self.memory.context(limit=8)
        prompt = (
            f"PERSISTENT MEMORY:\n{context}\n\n"
            f"CURRENT USER INPUT:\n{user_input}\n\n"
            "Use the memory only when relevant. Prefer the current user's request over stale memory."
        )
        raw = self.gemini.ask(prompt, system_instruction=self.SYSTEM)
        response = self._section(raw, "RESPONSE") or raw.strip()
        learning = self._section(raw, "LEARNING") or "No new durable learning."
        confidence_text = self._section(raw, "CONFIDENCE")
        try:
            confidence = float(confidence_text)
        except ValueError:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        memory_path = self.memory.save(user_input, response, learning, confidence)
        return AgentResult(response, learning, confidence, memory_path)
