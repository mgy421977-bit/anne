"""ANNE runtime extension that exposes the guarded self-improvement workflow."""

from __future__ import annotations

from typing import Any

from anne.agent.runtime import AgentResult, AnneAgent
from anne.agent.self_improvement import ChangeSpec, SelfImprovementEngine, SelfImprovementPlan


class SelfImprovingAnneAgent(AnneAgent):
    """AnneAgent with one high-level, guarded self-improvement tool.

    The model must provide an explicit plan. The engine enforces feature-branch
    and SHA safeguards before any repository mutation. Pull requests are opened,
    never merged.
    """

    SELF_IMPROVEMENT_SCHEMA = {
        "type": "function",
        "function": {
            "name": "github_self_improve",
            "description": (
                "Execute an approved ANNE code-improvement plan: create a feature "
                "branch, apply create/update/delete changes, and open a PR. "
                "Use only for an implementation task explicitly requested or approved."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "branch": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "base": {"type": "string"},
                    "changes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "action": {
                                    "type": "string",
                                    "enum": ["create", "update", "delete"],
                                },
                                "content": {"type": "string"},
                                "sha": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["path", "action", "message"],
                        },
                    },
                },
                "required": ["task", "branch", "title", "body", "changes"],
            },
        },
    }

    TOOL_SCHEMAS = AnneAgent.TOOL_SCHEMAS + [SELF_IMPROVEMENT_SCHEMA]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.self_improvement = SelfImprovementEngine(self.github_tools)
        self.tools["github_self_improve"] = self._execute_self_improvement

    def _execute_self_improvement(self, **arguments: Any) -> dict[str, Any]:
        raw_changes = arguments.get("changes")
        if not isinstance(raw_changes, list):
            raise ValueError("changes must be an array")

        changes = tuple(
            ChangeSpec(
                path=str(item.get("path", "")),
                content=item.get("content"),
                sha=item.get("sha"),
                action=str(item.get("action", "update")),
                message=str(item.get("message", "ANNE: self-improvement")),
            )
            for item in raw_changes
            if isinstance(item, dict)
        )

        plan = SelfImprovementPlan(
            task=str(arguments.get("task", "")),
            branch=str(arguments.get("branch", "")),
            changes=changes,
            title=str(arguments.get("title", "")),
            body=str(arguments.get("body", "")),
            base=str(arguments.get("base", "main")),
        )
        result = self.self_improvement.apply(plan)
        return self.self_improvement.summarize(result)


__all__ = ["SelfImprovingAnneAgent", "AgentResult"]
