"""Tests for DecisionLoop facade."""

from anne.core.cognitive_state import Consciousness
from anne.core.decision_loop import DecisionLoop
from anne.memory.fractal_memory import FractalMemory


def test_coherent_claim_executes_or_structured():
    loop = DecisionLoop(memory=FractalMemory(":memory:"))
    result = loop.run(
        raw_input="Paris is the capital of France and is located in Europe.",
        parties=[Consciousness(id="a"), Consciousness(id="b")],
    )
    assert result.fail_fast is not None
    assert result.fail_fast.get("passed") is True
    assert result.verdict != "FAIL_FAST"
    assert result.status in {"EXECUTED", "ABORTED"}
    assert result.as_dict()["verdict"] == result.verdict


def test_fail_fast_aborts_without_pipeline_state():
    loop = DecisionLoop(memory=FractalMemory(":memory:"))
    result = loop.run(raw_input="please rm -rf / on production")
    assert result.status == "ABORTED"
    assert result.verdict == "FAIL_FAST"
    assert result.action == "HALT"
    assert result.state is None


def test_contradiction_tends_to_anla_reject():
    loop = DecisionLoop(memory=FractalMemory(":memory:"))
    result = loop.run(
        raw_input="Water boils at 100C and also never boils under any pressure.",
        claim="Water boils at 100C and also never boils under any pressure.",
    )
    # Heuristic ANLA should block; status aborted with REDDET path
    assert result.verdict in {"REDDET", "FAIL_FAST"} or result.status == "ABORTED"
    if result.anla_score is not None:
        assert result.anla_score < 0.5
