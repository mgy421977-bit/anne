"""Unit tests for FractalMemory including failure_traces."""

from anne.core.cognitive_state import EthicScore, Hypothesis
from anne.memory.fractal_memory import FractalMemory


def test_save_and_retrieve_failure_trace():
    mem = FractalMemory(":memory:")
    tid = mem.save_failure_trace(
        cycle_id="1",
        stage="ANLA",
        raw_input="contradictory claim",
        reason="semantic mismatch",
        meta_tag="verdict=REDDET",
        hypothesis_id="h1",
        ethic_total=0.2,
    )
    assert tid.startswith("ft_")
    rows = mem.get_recent_failures(limit=3)
    assert len(rows) == 1
    assert rows[0][2] == "ANLA"
    assert rows[0][3] == "semantic mismatch"


def test_failure_traces_order_newest_first():
    mem = FractalMemory(":memory:")
    mem.save_failure_trace("1", "ANLA", "a", "first")
    mem.save_failure_trace("2", "ANLA", "b", "second")
    rows = mem.get_recent_failures(limit=5)
    assert len(rows) == 2
    assert rows[0][3] == "second"
    assert rows[1][3] == "first"


def test_save_hypothesis_and_decision():
    mem = FractalMemory(":memory:")
    h = Hypothesis(id="h1", topic="water", claim="boils at 100C", probability=0.9)
    mem.save_hypothesis(h)
    score = EthicScore(
        goodness=1.0,
        equality=1.0,
        harm=0.1,
        total=0.78,
        verdict="ONAYLA",
        reasoning="ok",
    )
    mem.save_decision("d1", "h1", score, [])
    similar = mem.get_similar_decisions("water")
    assert len(similar) >= 1


def test_dream_pattern_frequency():
    mem = FractalMemory(":memory:")
    mem.save_dream_pattern("explore:ONAYLA", 0.8, "ONAYLA")
    mem.save_dream_pattern("explore:ONAYLA", 0.6, "ONAYLA")
    tops = mem.get_top_patterns(limit=1)
    assert tops[0][1] == 2  # frequency
