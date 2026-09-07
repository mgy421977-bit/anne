from __future__ import annotations

from anne.core.cognitive_state import Hypothesis
from anne.core.decision_loop import DecisionLoop
from anne.core.fractal_loop import FractalBudget
from anne.core.gap_fill import GapFiller
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.candidate import TaskMode
from anne.mythos.engine import HypothesisCandidate, ExplorationMode
from anne.mythos.generate import generate_candidates
from anne.mythos.selection import CandidateSelector


def candidate(**overrides):
    values = dict(id="c", goal="goal", claim="claim", mode=ExplorationMode.HYPOTHESIS,
                  probability=.7, discovery_value=.8, novelty=.7, testability=.8,
                  harm_risk=0.0, reversibility=1.0, expected_benefit=.8, test_cost=.2)
    values.update(overrides)
    return HypothesisCandidate(**values)


def test_mitos_generates_and_anne_selects_without_synthesis():
    generated = generate_candidates("bounded technical exploration", batch_size=4)
    assert len(generated) == 4
    result = CandidateSelector().select(generated, task_mode=TaskMode.TECHNICAL)
    assert result.accepted
    assert result.candidate is not None
    assert result.candidate.claim in {c.claim for c in generated}


def test_selector_hard_gate_rejects_harm():
    result = CandidateSelector().select([candidate(harm_risk=.01)])
    assert not result.accepted
    assert result.reason == "no_candidate_passed_hard_gate"


def test_gap_filler_abstains_on_disagreement():
    result = GapFiller().assess(["low"], ["high"], low_score=.4, high_score=.9)
    assert result.abstained
    assert not result.filled
    assert result.reason == "path_disagreement"


def test_cognitive_orchestrator_keeps_mitos_selection_before_anla(tmp_path):
    loop = DecisionLoop(memory=FractalMemory(str(tmp_path / "anne.db")))
    result = loop.run_cognitive("Explore a bounded technical option", task_mode=TaskMode.TECHNICAL, seed=7)
    assert result.stage_trace[:6] == ("FAIL_FAST", "DUY", "BAK", "GÖR", "MITOS", "SELECT")
    assert result.selection is not None
    assert result.selection.candidate is not None
    assert "ANLA" in result.stage_trace
    assert "YAP" in result.stage_trace


def test_fractal_loop_has_hard_budget_and_scale_trace(tmp_path):
    memory = FractalMemory(str(tmp_path / "anne.db"))
    loop = DecisionLoop(memory=memory)
    result = loop.run_fractal(
        "Resolve an unknown technical relation",
        hypothesis=Hypothesis("root", "technical", "unknown claim", .2, source="test"),
        budget=FractalBudget(max_depth=0, max_iterations=2),
        task_mode=TaskMode.TECHNICAL,
    )
    assert result.status == "bounded"
    assert result.stop_reason == "max_depth"
    events = memory.get_scale_events(limit=20)
    assert events
    assert events[0][2] == 0
    failures = memory.get_failures_at_depth(0)
    assert failures
