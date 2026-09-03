"""ANNE tool-using agent runtime.

Gemini is the reasoning engine; ANNE owns tool execution, validation, and memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from anne.agent.github_memory import GitHubMemory
from anne.providers.gemini import GeminiProvider
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
    """Coordinates Gemini reasoning, safe tools, and persistent GitHub memory."""

    MAX_TOOL_ROUNDS = 5

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine), an experimental AI cognitive agent.
You are not a claim of AGI or consciousness.
Use DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent repository facts. When current repo information is needed, use a tool.

AVAILABLE TOOLS:
- github_read_file: read one UTF-8 text file from the configured ANNE GitHub repository.
- github_list: list a repository directory.
- github_search: search repository code.
- local_list: list files in the configured local Windows workspace (read-only).
- local_read: read one UTF-8 text file in that workspace (read-only).

TOOL PROTOCOL:
When a tool is needed, return ONLY:
<TOOL_CALL>
{"name":"tool_name","arguments":{"key":"value"}}
</TOOL_CALL>
Do not mix a tool call with a final response.
After a tool result is supplied, continue reasoning and call another tool if necessary.
When you can answer without more tools, return exactly:
<RESPONSE>
answer for the user
</RESPONSE>
<LEARNING>
1-3 concise reusable facts, insights, or lessons learned. If nothing durable was learned, say: No new durable learning.
</LEARNING>
<CONFIDENCE>
number from 0 to 1
</CONFIDENCE>

Never request or expose secrets, API keys, or tokens. Never claim a file was changed unless a write tool explicitly reports success.
"""

    def __init__(
        self,
        gemini: GeminiProvider,
        memory: GitHubMemory,
        github_tools: GitHubRepoTool | None = None,
        workspace: str | Path | None = None,
    ) -> None:
        self.gemini = gemini
        self.memory = memory
        self.github_tools = github_tools or GitHubRepoTool(
            token=memory.token,
            repository=memory.repository,
            branch=memory.branch,
        )
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
        start = f"<{name}>"
        end = f"</{name}>"
        if start in text and end in text:
            return text.split(start, 1)[1].split(end, 1)[0].strip()
        return ""

    @staticmethod
    def _tool_call(text: str) -> dict[str, Any] | None:
        body = AnneAgent._section(text, "TOOL_CALL")
        if not body:
            return None
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            return {"error": "Invalid tool call JSON"}
        if not isinstance(value, dict):
            return {"error": "Tool call must be a JSON object"}
        return value

    def _execute_tool(self, call: dict[str, Any]) -> tuple[str, str]:
        name = str(call.get("name", ""))
        arguments = call.get("arguments", {})
        if name not in self.tools:
            return name, json.dumps({"error": f"Unknown tool: {name}"})
        if not isinstance(arguments, dict):
            return name, json.dumps({"error": "arguments must be an object"})
        try:
            result = self.tools[name](**arguments)
            return name, json.dumps({"ok": True, "result": result}, ensure_ascii=False)
        except Exception as exc:
            return name, json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    def run(self, user_input: str) -> AgentResult:
        memory_context = self.memory.context(limit=8)
        prompt = (
            f"PERSISTENT MEMORY:\n{memory_context}\n\n"
            f"CURRENT USER INPUT:\n{user_input}\n\n"
            "Use tools when current repository or local workspace evidence is required."
        )
        tools_used: list[str] = []
        raw = ""

        for _ in range(self.MAX_TOOL_ROUNDS):
            raw = self.gemini.ask(prompt, system_instruction=self.SYSTEM)
            call = self._tool_call(raw)
            if not call:
                break
            tool_name, result = self._execute_tool(call)
            if tool_name:
                tools_used.append(tool_name)
            prompt = (
                f"PREVIOUS CONTEXT:\n{prompt}\n\n"
                f"TOOL USED: {tool_name}\nTOOL RESULT:\n{result}\n\n"
                "Use this evidence. Continue with another tool if needed; otherwise produce the final response format."
            )

        response = self._section(raw, "RESPONSE") or raw.strip()
        learning = self._section(raw, "LEARNING") or "No new durable learning."
        confidence_text = self._section(raw, "CONFIDENCE")
        try:
            confidence = float(confidence_text)
        except ValueError:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        memory_path = self.memory.save(user_input, response, learning, confidence)
        return AgentResult(response, learning, confidence, memory_path, tools_used)
