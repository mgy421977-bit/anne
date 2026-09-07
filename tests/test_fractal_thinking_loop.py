from __future__ import annotations

from anne.core.cognitive_state import Hypothesis
from anne.core.fractal_thinking_loop import FractalBudget, FractalCognitiveLoop
from anne.memory.fractal_memory import FractalMemory


def test_scale_event_and_failure_schema_are_persisted(tmp_path) -> None:
    memory = FractalMemory(str(tmp_path / "anne.db"))
    memory.save_scale_event(
        cycle_id="root",
        parent_cycle_id=None,
        depth=0,
        scale_role="frame",
        task_mode="technical",
        question="root question",
        selected_claim="root claim",
        status="started",
        stage_reached="FRAME",
    )
    memory.save_failure_trace(
        cycle_id="child",
        stage="ANLA",
        raw_input="child question",
        reason="uncertain",
        depth=1,
        parent_cycle_id="root",
        task_mode="technical",
        scale_role="branch",
    )

    events = memory.get_scale_events(parent_cycle_id=None)
    failures = memory.get_failures_at_depth(1)

    assert events[0][0] == "root"
    assert events[0][2] == 0
    assert events[0][3] == "frame"
    assert failures[0][2] == "root"
    assert failures[0][3] == 1
    assert failures[0][4] == "technical"


def test_fractal_loop_records_frame_branch_reframe_and_integrate(tmp_path) -> None:
    memory = FractalMemory(str(tmp_path / "anne.db"))
    calls = {"count": 0}

    def gap_detector(question, hypothesis, node):
        calls["count"] += 1
        return calls["count"] == 1

    def relation_scanner(question, node, memory):
        return [("relation", 0.8, "validated relation", question)]

    def candidate_generator(question, relations, node):
        return [
            Hypothesis(
                id="candidate-1",
                topic=question,
                claim="validated relation",
                probability=0.7,
                source="test",
            )
        ]

    def validator(hypothesis, relations, node):
        return True, 0.9, "test_validation"

    loop = FractalCognitiveLoop(
        memory,
        budget=FractalBudget(max_depth=3, max_iterations=3),
        gap_detector=gap_detector,
        relation_scanner=relation_scanner,
        candidate_generator=candidate_generator,
        validator=validator,
        integrator=lambda parent, hyp, node: hyp.claim,
    )

    result = loop.run(
        "Resolve an uncertain technical relation",
        Hypothesis(
            id="root-h",
            topic="technical",
            claim="initial claim",
            probability=0.7,
            source="test",
        ),
        task_mode="technical",
    )

    assert result.status == "completed"
    assert result.stop_reason == "validated"
    assert result.iterations == 2
    assert any(node.scale_role == "frame" for node in result.nodes)
    assert any(node.scale_role == "branch" for node in result.nodes)
    assert any(node.scale_role == "reframe" for node in result.nodes)

    events = memory.get_scale_events(limit=50)
    roles = {row[3] for row in events}
    stages = {row[8] for row in events}
    assert {"frame", "branch", "reframe"}.issubset(roles)
    assert "INTEGRATE" in stages
    assert any(row[2] >= 1 and row[1] is not None for row in events)


def test_fractal_loop_hard_stops_at_depth_budget(tmp_path) -> None:
    memory = FractalMemory(str(tmp_path / "anne.db"))
    loop = FractalCognitiveLoop(
        memory,
        budget=FractalBudget(max_depth=0, max_iterations=2),
        gap_detector=lambda q, h, n: True,
    )

    result = loop.run(
        "unknown technical relation",
        Hypothesis("root", "technical", "unknown claim", 0.2, source="test"),
        task_mode="technical",
    )

    assert result.status == "bounded"
    assert result.stop_reason == "max_depth"
    failures = memory.get_failures_at_depth(0)
    assert failures
    assert failures[0][5] == "frame"
