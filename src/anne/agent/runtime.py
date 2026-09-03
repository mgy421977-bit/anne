"""ANNE tool-using agent runtime.

Gemini and OpenRouter are reasoning engines; ANNE owns tool execution,
validation, and persistent memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from anne.agent.github_memory import GitHubMemory
from anne.providers.openrouter import OpenRouterProvider
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
    """Coordinates model reasoning, safe tools, and persistent GitHub memory."""

    MAX_TOOL_ROUNDS = 3

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine), an experimental AI cognitive agent.
You are not a claim of AGI or consciousness.
Use DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent repository facts. When current repository information is needed, use a tool.

Available tools:
- github_read_file: read one UTF-8 file from the configured repository.
- github_list: list a repository directory.
- github_search: search repository code.
- local_list: list files in the local ANNE workspace.
- local_read: read a UTF-8 file in the local ANNE workspace.

When tools are available, prefer them whenever the user asks about current repository or workspace state.
Never expose or request API keys or tokens.

Final response must contain exactly these tags:
<RESPONSE>
answer for the user
</RESPONSE>
<LEARNING>
1-3 concise reusable facts, insights, or lessons learned. If nothing durable was learned, say: No new durable learning.
</LEARNING>
<CONFIDENCE>
number from 0 to 1
</CONFIDENCE>"""

    TOOL_SCHEMAS = [
        {
            "type": "function",
            "function": {
                "name": "github_read_file",
                "description": "Read a UTF-8 text file from the configured ANNE GitHub repository.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "github_list",
                "description": "List a directory in the configured ANNE GitHub repository.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "github_search",
                "description": "Search repository code for a query.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_list",
                "description": "List files in the local ANNE workspace.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_read",
                "description": "Read a UTF-8 text file in the local ANNE workspace.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            },
        },
    ]

    def __init__(
        self,
        gemini: GeminiProvider | OpenRouterProvider,
        memory: GitHubMemory,
        github_tools: GitHubRepoTool | None = None,
        workspace: str | Path | None = None,
    ) -> None:
        self.model = gemini
        self.memory = memory
        self.github_tools = github_tools or GitHubRepoTool(
            token=memory.token, repository=memory.repository, branch=memory.branch
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

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        try:
            return {"ok": True, "result": tool(**arguments)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _openrouter_run(self, user_input: str, memory_context: str) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM},
            {"role": "user", "content": f"PERSISTENT MEMORY:\n{memory_context}\n\nCURRENT USER INPUT:\n{user_input}"},
        ]
        tools_used: list[str] = []
        for _ in range(self.MAX_TOOL_ROUNDS):
            data = self.model.chat(messages, tools=self.TOOL_SCHEMAS)  # type: ignore[attr-defined]
            message = data.get("choices", [{}])[0].get("message", {})
            tool_calls = message.get("tool_calls") or []
            messages.append(message)
            if not tool_calls:
                return str(message.get("content") or ""), tools_used
            for call in tool_calls:
                fn = call.get("function", {})
                name = str(fn.get("name", ""))
                raw_args = fn.get("arguments", "{}")
                try:
                    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    arguments = {}
                result = self._execute_tool(name, arguments)
                tools_used.append(name)
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": json.dumps(result, ensure_ascii=False)})
        return "<RESPONSE>Agent tool loop limit reached.</RESPONSE><LEARNING>No new durable learning.</LEARNING><CONFIDENCE>0.3</CONFIDENCE>", tools_used

    def run(self, user_input: str) -> AgentResult:
        memory_context = self.memory.context(limit=8)
        if isinstance(self.model, OpenRouterProvider):
            raw, tools_used = self._openrouter_run(user_input, memory_context)
        else:
            prompt = (
                f"PERSISTENT MEMORY:\n{memory_context}\n\nCURRENT USER INPUT:\n{user_input}\n\n"
                "Use the supplied reasoning context. Current repository tools are managed by ANNE."
            )
            raw = self.model.ask(prompt, system_instruction=self.SYSTEM)
            tools_used = []

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
