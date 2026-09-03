"""ANNE tool-using agent runtime with bounded native tool calling."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from anne.agent.github_memory import GitHubMemory
from anne.providers.gemini import GeminiProvider
from anne.providers.openrouter import OpenRouterProvider
from anne.tools.github_repo import GitHubRepoTool
from anne.tools.local_files import LocalFilesTool


@dataclass
class AgentResult:
    response: str
    learning: str
    confidence: float
    memory_path: str | None
    tools_used: list[str] = field(default_factory=list)


class AnneAgent:
    """Coordinates reasoning models, safe tools, and persistent GitHub memory."""

    # Keep the OpenRouter call budget deliberately small. Exact repository paths are
    # prefetched deterministically, so one tool round is normally enough.
    MAX_TOOL_ROUNDS = 1
    # A failed/empty final response gets one synthesis attempt, not repeated retries.
    MAX_FINAL_RETRIES = 0

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine), an experimental AI cognitive agent.
You are not a claim of AGI or consciousness.
Use DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent repository facts. Use tools when evidence is required.
Use the minimum number of tools necessary.
If authoritative repository evidence has already been provided, analyze it directly and do not reread it.
If the user names an exact file path, it may already be preloaded as authoritative evidence.
Do not call directory listing or code search when the requested file can be read directly.
Never expose or request API keys or tokens.

Final response format:
<RESPONSE>answer for the user</RESPONSE>
<LEARNING>1-3 concise reusable facts, insights, or lessons learned, or No new durable learning.</LEARNING>
<CONFIDENCE>number from 0 to 1</CONFIDENCE>"""

    TOOL_SCHEMAS = [
        {
            "type": "function",
            "function": {
                "name": "github_read_file",
                "description": "Read one UTF-8 text file from the configured ANNE GitHub repository. Use this first for an exact path.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "github_list",
                "description": "List a repository directory only when the location is unknown.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "github_search",
                "description": "Search repository code only when the exact location or additional evidence is unknown.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_list",
                "description": "List files in the local ANNE Windows workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_read",
                "description": "Read a UTF-8 file in the local ANNE Windows workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
    ]

    def __init__(
        self,
        model: GeminiProvider | OpenRouterProvider,
        memory: GitHubMemory,
        workspace: str | Path | None = None,
    ) -> None:
        self.model = model
        self.memory = memory
        self.github_tools = GitHubRepoTool(memory.token, memory.repository, memory.branch)
        self.local_tools = LocalFilesTool(workspace or Path.cwd())
        self.tools: dict[str, Callable[..., Any]] = {
            "github_read_file": self.github_tools.read_file,
            "github_list": self.github_tools.list_directory,
            "github_search": self.github_tools.search_code,
            "local_list": self.local_tools.list,
            "local_read": self.local_tools.read,
        }

    @staticmethod
    def _section(text: str, name: str) -> str:
        start, end = f"<{name}>", f"</{name}>"
        if start in text and end in text:
            return text.split(start, 1)[1].split(end, 1)[0].strip()
        return ""

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        try:
            return {"ok": True, "result": tool(**arguments)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _explicit_repo_paths(user_input: str) -> list[str]:
        """Extract all explicit src/anne/... paths so they can be read without another LLM turn."""
        pattern = r"(?:`|\s)(src/anne/[A-Za-z0-9_./-]+)(?:`|\s|$)"
        seen: set[str] = set()
        paths: list[str] = []
        for match in re.finditer(pattern, user_input):
            path = match.group(1)
            if path not in seen:
                paths.append(path)
                seen.add(path)
        return paths[:8]

    def _prefetch_explicit_repo_evidence(
        self,
        user_input: str,
        messages: list[dict[str, Any]],
        tools_used: list[str],
    ) -> None:
        paths = self._explicit_repo_paths(user_input)
        if not paths:
            return

        evidence: list[dict[str, Any]] = []
        for path in paths:
            result = self._execute_tool("github_read_file", {"path": path})
            tools_used.append("github_read_file")
            evidence.append({"path": path, "evidence": result})

        messages.append(
            {
                "role": "user",
                "content": (
                    "AUTHORITATIVE REPOSITORY EVIDENCE (prefetched directly by ANNE):\n"
                    f"{json.dumps(evidence, ensure_ascii=False)}\n\n"
                    "Analyze this evidence directly. Do not call github_read_file again for these paths."
                ),
            }
        )

    def _openrouter_run(self, user_input: str, memory_context: str) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM},
            {
                "role": "user",
                "content": f"PERSISTENT MEMORY:\n{memory_context}\n\nCURRENT USER INPUT:\n{user_input}",
            },
        ]
        tools_used: list[str] = []

        self._prefetch_explicit_repo_evidence(user_input, messages, tools_used)

        for _ in range(self.MAX_TOOL_ROUNDS):
            data = self.model.chat(messages, tools=self.TOOL_SCHEMAS)  # type: ignore[attr-defined]
            choices = data.get("choices") or []
            if not choices:
                break

            message = choices[0].get("message") or {}
            tool_calls = message.get("tool_calls") or []
            messages.append(message)

            if not tool_calls:
                content = str(message.get("content") or "").strip()
                if content:
                    return content, tools_used
                break

            for call in tool_calls:
                fn = call.get("function") or {}
                name = str(fn.get("name") or "")
                raw_args = fn.get("arguments", "{}")
                try:
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    arguments = {}
                if not isinstance(arguments, dict):
                    arguments = {}
                result = self._execute_tool(name, arguments)
                tools_used.append(name)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": str(call.get("id") or ""),
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Exactly one tool-free synthesis request is used after a tool round or an
        # empty content response. This keeps the API call budget bounded.
        synthesis = messages + [
            {
                "role": "user",
                "content": (
                    "SYNTHESIZE NOW. Do not use tools. Produce the final response using only "
                    "the evidence already collected. Follow the required "
                    "<RESPONSE>, <LEARNING>, <CONFIDENCE> format."
                ),
            }
        ]
        for _ in range(self.MAX_FINAL_RETRIES + 1):
            try:
                final_data = self.model.chat(synthesis, tools=None)  # type: ignore[attr-defined]
            except Exception:
                continue
            final_choices = final_data.get("choices") or []
            if final_choices:
                raw = str((final_choices[0].get("message") or {}).get("content") or "").strip()
                if raw:
                    return raw, tools_used

        return (
            "<RESPONSE>The model did not return a final synthesis after the available evidence was collected.</RESPONSE>"
            "<LEARNING>No new durable learning.</LEARNING><CONFIDENCE>0.2</CONFIDENCE>",
            tools_used,
        )

    def run(self, user_input: str) -> AgentResult:
        memory_context = self.memory.context(limit=8)
        if isinstance(self.model, OpenRouterProvider):
            raw, tools_used = self._openrouter_run(user_input, memory_context)
        else:
            raw = self.model.ask(
                f"PERSISTENT MEMORY:\n{memory_context}\n\nCURRENT USER INPUT:\n{user_input}",
                system_instruction=self.SYSTEM,
            )
            tools_used = []

        response = self._section(raw, "RESPONSE") or raw.strip()
        learning = self._section(raw, "LEARNING") or "No new durable learning."
        try:
            confidence = float(self._section(raw, "CONFIDENCE"))
        except ValueError:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        memory_path = self.memory.save(user_input, response, learning, confidence)
        return AgentResult(response, learning, confidence, memory_path, tools_used)
