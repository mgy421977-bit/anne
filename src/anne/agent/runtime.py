"""ANNE tool-using agent runtime with native OpenRouter tool calling."""

from __future__ import annotations

import json
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
    """Coordinates model reasoning, safe tools, and persistent GitHub memory."""

    MAX_TOOL_ROUNDS = 4

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine), an experimental AI cognitive agent.
You are not a claim of AGI or consciousness.
Use DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent repository facts. When current repository or workspace information is needed, use tools.
Prefer the minimum number of tool calls needed to obtain evidence. If the user names a specific file,
read that file directly before exploring other locations.
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
                "description": "Read one UTF-8 text file from the configured ANNE GitHub repository. Use this first when the user gives an exact file path.",
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
                "description": "Search repository code for a query when the exact location is unknown or additional evidence is needed.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_list",
                "description": "List files in the local ANNE Windows workspace.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "local_read",
                "description": "Read a UTF-8 text file in the local ANNE Windows workspace.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
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

    def _openrouter_run(self, user_input: str, memory_context: str) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM},
            {
                "role": "user",
                "content": f"PERSISTENT MEMORY:\n{memory_context}\n\nCURRENT USER INPUT:\n{user_input}",
            },
        ]
        tools_used: list[str] = []

        for _ in range(self.MAX_TOOL_ROUNDS):
            data = self.model.chat(messages, tools=self.TOOL_SCHEMAS)  # type: ignore[attr-defined]
            choices = data.get("choices") or []
            if not choices:
                return (
                    "<RESPONSE>OpenRouter returned no choices.</RESPONSE>"
                    "<LEARNING>No new durable learning.</LEARNING><CONFIDENCE>0.0</CONFIDENCE>",
                    tools_used,
                )
            message = choices[0].get("message") or {}
            tool_calls = message.get("tool_calls") or []
            messages.append(message)

            if not tool_calls:
                return str(message.get("content") or ""), tools_used

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

        # We have enough evidence to ask for synthesis without exposing tools again.
        synthesis_messages = messages + [
            {
                "role": "user",
                "content": (
                    "SYNTHESIZE NOW. Do not call any more tools. Use only the evidence already "
                    "collected above and return the required final response format."
                ),
            }
        ]
        final_data = self.model.chat(synthesis_messages, tools=None)  # type: ignore[attr-defined]
        final_message = (final_data.get("choices") or [{}])[0].get("message") or {}
        raw = str(final_message.get("content") or "")
        if raw:
            return raw, tools_used
        return (
            "<RESPONSE>The agent collected evidence but could not synthesize a final answer.</RESPONSE>"
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
