"""ANNE tool-using agent runtime with bounded native tool calling."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from anne.agent.github_memory import GitHubMemory
from anne.core.cognitive_runtime import (
    CognitiveWorkspace,
    HierarchicalPlanner,
    Metacognition,
)
from anne.core.decision_loop import DecisionLoop
from anne.neuro_symbolic.audit import NeuroSymbolicValidator
from anne.providers.gemini import GeminiProvider
from anne.providers.openrouter import OpenRouterProvider
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

    TOOL_SCHEMAS = [
        {
            "type": "function",
            "function": {
                "name": "github_read_file",
                "description": (
                    "Read one UTF-8 text file from the configured ANNE GitHub "
                    "repository. Use this first for an exact path."
                ),
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
                "description": (
                    "Search repository code only when the exact location or "
                    "additional evidence is unknown."
                ),
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
        self.github_tools = GitHubRepoTool(
            memory.token, memory.repository, memory.branch
        )
        self.local_tools = LocalFilesTool(workspace or Path.cwd())
        self.planner = HierarchicalPlanner()
        self.metacognition = Metacognition()
        self.semantic_validator = NeuroSymbolicValidator()
        self.ontology = Ontology()
        self.decision_loop = DecisionLoop()
        self.workspace: CognitiveWorkspace | None = None
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
            result = tool(**arguments)
            workspace = getattr(self, "workspace", None)
            if workspace is not None:
                workspace.record_tool_result(name, result, ok=True)
            return {"ok": True, "result": result}
        except Exception as exc:
            workspace = getattr(self, "workspace", None)
            if workspace is not None:
                workspace.record_tool_result(name, str(exc), ok=False)
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _explicit_repo_paths(user_input: str) -> list[str]:
        """Extract explicit src/anne/... paths for deterministic prefetching."""
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
                    "AUTHORITATIVE REPOSITORY EVIDENCE "
                    "(prefetched directly by ANNE):\n"
                    f"{json.dumps(evidence, ensure_ascii=False)}\n\n"
                    "Analyze this evidence directly. Do not call "
                    "github_read_file again for these paths."
                ),
            }
        )

    def _openrouter_run(
        self,
        user_input: str,
        memory_context: str,
    ) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM},
            {
                "role": "user",
                "content": (
                    f"PERSISTENT MEMORY:\n{memory_context}\n\n"
                    f"CURRENT USER INPUT:\n{user_input}"
                ),
            },
        ]
        tools_used: list[str] = []

        self._prefetch_explicit_repo_evidence(
            user_input, messages, tools_used
        )

        model = cast(OpenRouterProvider, self.model)

        for _ in range(self.MAX_TOOL_ROUNDS):
            data = model.chat(messages, tools=self.TOOL_SCHEMAS)
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
                    arguments = (
                        json.loads(raw_args)
                        if isinstance(raw_args, str)
                        else raw_args
                    )
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

        synthesis = messages + [
            {
                "role": "user",
                "content": (
                    "SYNTHESIZE NOW. Do not use tools. Produce the final "
                    "response using only the evidence already collected. "
                    "Follow the required <RESPONSE>, <LEARNING>, "
                    "<CONFIDENCE> format."
                ),
            }
        ]
        for _ in range(self.MAX_FINAL_RETRIES + 1):
            try:
                final_data = model.chat(synthesis, tools=None)
            except Exception:
                continue
            final_choices = final_data.get("choices") or []
            if final_choices:
                raw = str(
                    (final_choices[0].get("message") or {}).get("content")
                    or ""
                ).strip()
                if raw:
                    return raw, tools_used

        return (
            "<RESPONSE>"
            "The model did not return a final synthesis after the available "
            "evidence was collected."
            "</RESPONSE><LEARNING>No new durable learning.</LEARNING>"
            "<CONFIDENCE>0.2</CONFIDENCE>",
            tools_used,
        )

    def run(self, user_input: str) -> AgentResult:
        self.workspace = CognitiveWorkspace(task=user_input)
        self.workspace.semantic_frame = frame_from_text(user_input)
        self.workspace.observations.append("User input grounded as traceable evidence")
        self.workspace.transition("DUY")
        self.planner.create_plan(self.workspace)
        self.workspace.transition("BAK")

        # The deterministic decision loop is a mandatory preflight.  It does
        # not replace model reasoning; it controls whether reasoning proceeds.
        preflight = self.decision_loop.run(user_input, probability=0.7)
        if preflight.status == "ABORTED":
            response = preflight.output.get("reason", "Request blocked by ANNE safety gates.")
            learning = "A request was blocked during deterministic preflight."
            memory_path = self.memory.save(user_input, str(response), learning, 0.2)
            review = self.metacognition.review(self.workspace, str(response))
            return AgentResult(
                str(response), learning, 0.2, memory_path, [], review.__dict__
            )

        self.workspace.transition("GÖR")
        memory_context = self.memory.context(limit=8)
        if isinstance(self.model, OpenRouterProvider):
            raw, tools_used = self._openrouter_run(
                user_input, memory_context
            )
        else:
            raw = self.model.ask(
                f"PERSISTENT MEMORY:\n{memory_context}\n\n"
                f"CURRENT USER INPUT:\n{user_input}",
                system_instruction=self.SYSTEM,
            )
            tools_used = []

        self.workspace.transition("ANLA")
        response = self._section(raw, "RESPONSE") or raw.strip()
        structured = self._section(raw, "SEMANTIC_FRAME")
        if structured:
            try:
                self.workspace.semantic_frame = parse_structured_frame(structured)
                issues = self.ontology.validate(self.workspace.semantic_frame)
                self.workspace.observations.append(
                    f"Model semantic frame parsed; ontology issues={len(issues)}"
                )
            except (ValueError, TypeError):
                self.workspace.observations.append(
                    "Model semantic frame invalid; text grounding retained"
                )
        learning = (
            self._section(raw, "LEARNING")
            or "No new durable learning."
        )
        try:
            confidence = float(self._section(raw, "CONFIDENCE"))
        except ValueError:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        self.workspace.uncertainty = 1.0 - confidence
        self.workspace.transition("HİSSET")

        # Verify the generated answer through the same deterministic gate.
        verification = self.decision_loop.run(response, probability=confidence)
        if verification.status == "ABORTED":
            response = "ANNE could not safely validate the generated response."
            learning = "The generated response failed post-generation validation."
            confidence = min(confidence, 0.2)

        self.workspace.transition("YAP")
        review = self.metacognition.review(self.workspace, response)
        self.workspace.reasoning_audit = self.semantic_validator.audit(
            conclusion=response,
            evidence=self.workspace.semantic_frame.evidence,
            assumptions=self.workspace.active_hypotheses,
        ).__dict__
        review_data = {**review.__dict__, "reasoning_audit": self.workspace.reasoning_audit}
        self.workspace.transition("ÖĞREN")
        memory_path = self.memory.save(
            user_input, response, learning, confidence
        )
        return AgentResult(
            response,
            learning,
            confidence,
            memory_path,
            tools_used,
            review_data,
        )
