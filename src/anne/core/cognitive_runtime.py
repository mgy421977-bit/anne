"""Structured cognitive runtime primitives for ANNE v0.2.

These components deliberately remain deterministic and inspectable.  The LLM may
suggest interpretations or plans, but the runtime owns state transitions,
limits, and verification metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Goal:
    """A bounded goal with explicit lifecycle state."""

    id: str
    description: str
    status: str = "pending"  # pending | active | completed | failed
    parent_id: str | None = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class CognitiveWorkspace:
    """Global workspace shared by perception, planning, action, and review."""

    task: str
    goals: list[Goal] = field(default_factory=list)
    active_hypotheses: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    semantic_frame: Any = None
    reasoning_audit: dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 1.0
    phase: str = "DUY"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def transition(self, phase: str) -> None:
        allowed = {"DUY", "BAK", "GÖR", "ANLA", "HİSSET", "YAP", "ÖĞREN"}
        if phase not in allowed:
            raise ValueError(f"Unknown cognitive phase: {phase}")
        self.phase = phase

    def add_goal(self, description: str, parent_id: str | None = None) -> Goal:
        goal = Goal(id=f"g{len(self.goals) + 1}", description=description, parent_id=parent_id)
        self.goals.append(goal)
        return goal

    def record_tool_result(self, name: str, result: Any, ok: bool) -> None:
        self.tool_results.append({"name": name, "result": result, "ok": ok})


class HierarchicalPlanner:
    """Small, bounded planner; it creates inspectable sub-goals, not free loops."""

    def __init__(self, max_goals: int = 6) -> None:
        if max_goals < 1:
            raise ValueError("max_goals must be positive")
        self.max_goals = max_goals

    def create_plan(self, workspace: CognitiveWorkspace) -> list[Goal]:
        if workspace.goals:
            return workspace.goals
        root = workspace.add_goal(workspace.task)
        root.status = "active"
        for description in ("understand task", "gather evidence", "verify result"):
            if len(workspace.goals) >= self.max_goals:
                break
            workspace.add_goal(description, parent_id=root.id)
        return workspace.goals

    def next_goal(self, workspace: CognitiveWorkspace) -> Goal | None:
        return next((goal for goal in workspace.goals if goal.status == "pending"), None)


@dataclass
class MetacognitiveReview:
    """Evidence-based review produced after an action or model response."""

    known: list[str]
    unknown: list[str]
    assumptions: list[str]
    confidence: float
    needs_verification: bool


class Metacognition:
    """Tracks epistemic limits without treating model confidence as truth."""

    def review(self, workspace: CognitiveWorkspace, response: str = "") -> MetacognitiveReview:
        successful = sum(1 for item in workspace.tool_results if item.get("ok"))
        failed = len(workspace.tool_results) - successful
        known = list(workspace.observations)
        if successful:
            known.append(f"{successful} tool result(s) returned successfully")
        unknown: list[str] = []
        if not known:
            unknown.append("No external evidence was collected")
        if failed:
            unknown.append(f"{failed} tool result(s) failed")
        assumptions = list(workspace.active_hypotheses)
        confidence = max(
            0.0,
            min(1.0, 0.8 + 0.1 * successful - 0.15 * failed - 0.3 * workspace.uncertainty),
        )
        return MetacognitiveReview(
            known=known,
            unknown=unknown,
            assumptions=assumptions,
            confidence=confidence,
            needs_verification=bool(unknown or assumptions or not response.strip()),
        )


__all__ = [
    "CognitiveWorkspace",
    "Goal",
    "HierarchicalPlanner",
    "Metacognition",
    "MetacognitiveReview",
]
