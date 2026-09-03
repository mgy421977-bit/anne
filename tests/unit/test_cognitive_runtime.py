from __future__ import annotations

import pytest

from anne.core.cognitive_runtime import (
    CognitiveWorkspace,
    HierarchicalPlanner,
    Metacognition,
)


def test_workspace_rejects_unknown_phase_and_records_tool_results() -> None:
    workspace = CognitiveWorkspace("research task")
    with pytest.raises(ValueError):
        workspace.transition("UNKNOWN")
    workspace.record_tool_result("search", "evidence", ok=True)
    assert workspace.tool_results[0]["name"] == "search"


def test_planner_creates_bounded_hierarchical_goals() -> None:
    workspace = CognitiveWorkspace("build a report")
    goals = HierarchicalPlanner(max_goals=3).create_plan(workspace)
    assert len(goals) == 3
    assert goals[0].status == "active"
    assert all(goal.parent_id == goals[0].id for goal in goals[1:])
    assert HierarchicalPlanner().next_goal(workspace) is not None


def test_metacognition_marks_missing_evidence() -> None:
    workspace = CognitiveWorkspace("answer a question")
    review = Metacognition().review(workspace, "answer")
    assert review.known == []
    assert "No external evidence" in review.unknown[0]
    assert review.needs_verification is True


def test_metacognition_rewards_successful_evidence() -> None:
    workspace = CognitiveWorkspace("inspect repository")
    workspace.record_tool_result("read", "file contents", ok=True)
    review = Metacognition().review(workspace, "answer")
    assert review.confidence > 0.5
    assert review.needs_verification is False
