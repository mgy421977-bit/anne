# ruff: noqa: E501
"""ANNE tool-using agent runtime with bounded native tool calling."""

from __future__ import annotations

import contextlib
import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from anne.agent.github_memory import GitHubMemory
from anne.core.cognitive_runtime import CognitiveWorkspace, HierarchicalPlanner, Metacognition
from anne.core.decision_loop import DecisionLoop
from anne.multi_agent import AgentRole, CollaborationResult, MultiAgentCoordinator, Worker
from anne.neuro_symbolic.audit import NeuroSymbolicValidator
from anne.safety.policy import ToolPolicy, redact_sensitive
from anne.semantics.core import frame_from_text
from anne.semantics.structured import Ontology, parse_structured_frame
from anne.tools.github_repo import GitHubRepoTool
from anne.tools.local_files import LocalFilesTool


@dataclass
class AgentResult:
    response: str
    learning: str
    confidence: float
    memory_path: str | None
    tools_used: list[str] = field(default_factory=list)
    cognitive_review: dict[str, Any] = field(default_factory=dict)


class AnneAgent:
    """Coordinates reasoning models, safe tools, and persistent GitHub memory."""

    MAX_TOOL_ROUNDS = 1
    MAX_FINAL_RETRIES = 0

    SYSTEM = """You are ANNE (Adaptive Neural Nexus Engine), an experimental AI cognitive agent.
You are not a claim of AGI or consciousness.
Use DUY -> BAK -> GÖR -> ANLA -> HİSSET -> YAP as a reasoning discipline.
Treat persistent memory as prior context, not unquestionable truth.
Do not invent repository facts. Use tools when evidence is required.
Use the minimum number of tools necessary.
If authoritative repository evidence has already been provided,
analyze it directly and do not reread it.
If the user names an exact file path, it may already be preloaded as authoritative evidence.
Do not call directory listing or code search when the requested file can be read directly.
Never expose or request API keys or tokens.

Final response format:
<RESPONSE>answer for the user</RESPONSE>
<LEARNING>
1-3 concise reusable facts, insights, or lessons learned,
or No new durable learning.
</LEARNING>
<SEMANTIC_FRAME>
optional JSON object with text, entities, relations, claims, evidence, confidence;
omit only when no semantic extraction is useful.
</SEMANTIC_FRAME>
<CONFIDENCE>number from 0 to 1</CONFIDENCE>"""

    TOOL_SCHEMAS: list[dict[str, Any]] = [
        {"type": "function", "function": {"name": "github_read_file", "description": "Read one UTF-8 text file from the configured ANNE GitHub repository. Use this first for an exact path.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "github_list", "description": "List a repository directory only when the location is unknown.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "github_search", "description": "Search repository code only when the exact location or additional evidence is unknown.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "local_list", "description": "List files in the local ANNE Windows workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "local_read", "description": "Read a UTF-8 file in the local ANNE Windows workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    ]

    def __init__(self, model: Any, memory: Any, workspace: str | Path | None = None) -> None:
        self.model = model
        self.memory = memory
        self.github_tools = (
            GitHubRepoTool(memory.token, memory.repository, memory.branch)
            if getattr(memory, "token", "")
            else None
        )
        self.local_tools = LocalFilesTool(workspace or Path.cwd())
        self.planner = HierarchicalPlanner()
        self.metacognition = Metacognition()
        self.semantic_validator = NeuroSymbolicValidator()
        self.ontology = Ontology()
        self.tool_policy = ToolPolicy()
        self.collaborator = MultiAgentCoordinator(
            roles=[
                AgentRole("researcher", "collect relevant evidence"),
                AgentRole("critic", "challenge assumptions"),
                AgentRole("planner", "propose a verifiable next step"),
            ],
            max_rounds=2,
        )
        self.decision_loop = DecisionLoop()
        self.workspace: CognitiveWorkspace | None = None
        self.tools: dict[str, Callable[..., Any]] = {
            "local_list": self.local_tools.list,
            "local_read": self.local_tools.read,
        }
        if self.github_tools is not None:
            self.tools.update(
                {
                    "github_read_file": self.github_tools.read_file,
                    "github_list": self.github_tools.list_directory,
                    "github_search": self.github_tools.search_code,
                }
            )

    def collaborate(self, task: str, workers: dict[str, Worker]) -> CollaborationResult:
        return self.collaborator.collaborate(task, workers)

    @staticmethod
    def _section(text: str, name: str) -> str:
        start, end = f"<{name}>", f"</{name}>"
        if start in text and end in text:
            return text.split(start, 1)[1].split(end, 1)[0].strip()
        return ""

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        decision = self.tool_policy.authorize(name, arguments)
        if not decision.allowed:
            return {"ok": False, "error": decision.reason}
        tool = self.tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool: {name}"}
        try:
            result = tool(**arguments)
            if self.workspace is not None:
                self.workspace.record_tool_result(name, result, ok=True)
            return {"ok": True, "result": result}
        except Exception as exc:
            if self.workspace is not None:
                self.workspace.record_tool_result(name, str(exc), ok=False)
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _explicit_repo_paths(user_input: str) -> list[str]:
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
        if self.github_tools is None:
            return
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
                    + json.dumps(evidence, ensure_ascii=False)
                    + "\n\nAnalyze this evidence directly. Do not call github_read_file again for these paths."
                ),
            }
        )

    def _tool_run(
        self,
        user_input: str,
        memory_context: str,
        external_context: str = "",
    ) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM},
            {
                "role": "user",
                "content": (
                    f"PERSISTENT MEMORY:\n{memory_context}\n\n"
                    f"RESEARCH FILE CONTEXT:\n{external_context or '(none)'}\n\n"
                    f"CURRENT USER INPUT:\n{user_input}"
                ),
            },
        ]
        tools_used: list[str] = []
        self._prefetch_explicit_repo_evidence(user_input, messages, tools_used)
        tool_schemas = self.TOOL_SCHEMAS
        if self.github_tools is None:
            tool_schemas = [
                schema
                for schema in self.TOOL_SCHEMAS
                if schema["function"]["name"]
                not in {"github_read_file", "github_list", "github_search"}
            ]
        for _ in range(self.MAX_TOOL_ROUNDS):
            data = self.model.chat(messages, tools=tool_schemas)
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
                self._execute_tool(name, arguments)
                tools_used.append(name)
            messages.append(
                {
                    "role": "tool",
                    "content": "Tool calls executed. Continue with the final structured response.",
                }
            )
        data = self.model.chat(messages, tools=[])
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = str(message.get("content") or "").strip()
            if content:
                return content, tools_used
        return "<RESPONSE>No response generated.</RESPONSE>\n<LEARNING>No new durable learning.</LEARNING>\n<CONFIDENCE>0</CONFIDENCE>", tools_used

    def run(
        self,
        user_input: str,
        memory_context: str,
        external_context: str = "",
    ) -> AgentResult:
        self.workspace = CognitiveWorkspace(task=user_input)
        self.planner.create_plan(self.workspace)
        self.workspace.observations.append("Task received and bounded plan created")
        response_text, tools_used = self._tool_run(user_input, memory_context, external_context)
        response = self._section(response_text, "RESPONSE") or response_text
        learning = self._section(response_text, "LEARNING") or "No new durable learning."
        semantic_text = self._section(response_text, "SEMANTIC_FRAME")
        confidence_text = self._section(response_text, "CONFIDENCE")
        try:
            confidence = max(0.0, min(1.0, float(confidence_text)))
        except ValueError:
            confidence = 0.5
        frame = frame_from_text(response)
        semantic_valid = False
        if semantic_text:
            with contextlib.suppress(Exception):
                frame = parse_structured_frame(semantic_text)
                semantic_valid = True
        review = self.metacognition.review(self.workspace, response)
        review_dict = asdict(review)
        review_dict["semantic_valid"] = semantic_valid
        review_dict["semantic_frame_type"] = type(frame).__name__
        return AgentResult(
            response=redact_sensitive(response),
            learning=redact_sensitive(learning),
            confidence=confidence,
            memory_path=getattr(self.memory, "path", None),
            tools_used=tools_used,
            cognitive_review=review_dict,
        )
