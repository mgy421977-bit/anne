from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.decision_loop import DecisionLoop
from anne.core.pipeline import AnnePipeline
from anne.core.cognitive_orchestrator import CognitiveOrchestrator
from anne.core.fail_fast import FailFastResult
from anne.core.ambiguity import AmbiguityBoundary, AmbiguityLevel
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.candidate import Candidate, TaskMode
from anne.mythos.selection import CandidateSelector
from anne.mythos.gap_filler import GapFiller


def candidate(harm_risk=0.1):
    return Candidate(
        id="c1", goal="bounded goal", claim="bounded claim", probability=0.9,
        harm_risk=harm_risk,
    )


def test_candidate_selector_hard_gate_rejects_high_harm():
    result = CandidateSelector().select([candidate(harm_risk=0.9)], task_mode=TaskMode.GENERAL)
    assert not result.accepted
    assert result.reason == "no_candidate_passed_hard_gate"


def test_gap_filler_abstains_on_disagreement():
    result = GapFiller().assess(["low"], ["high"], low_score=0.4, high_score=0.9)
    assert result.abstained
    assert not result.filled
    assert result.reason == "path_disagreement"


def test_cognitive_orchestrator_keeps_ambiguity_and_mitos_selection_before_anla(tmp_path):
    loop = DecisionLoop(memory=FractalMemory(str(tmp_path / "anne.db")))
    result = loop.run_cognitive(
        "Explore a bounded technical option",
        task_mode=TaskMode.TECHNICAL,
        seed=7,
    )
    assert result.stage_trace[:7] == (
        "FAIL_FAST",
        "DUY",
        "BAK",
        "AMBIGUITY",
        "GÖR",
        "MITOS",
        "SELECT",
    )
    assert result.selection is not None
    assert result.selection.candidate is not None
    assert "ANLA" in result.stage_trace
    assert "YAP" in result.stage_trace


def test_cognitive_orchestrator_rejected_selection_cannot_reach_anla_or_yap(
    tmp_path, monkeypatch
):
    rejected = candidate(harm_risk=0.01)
    monkeypatch.setattr(
        "anne.core.cognitive_orchestrator.generate_candidates",
        lambda *args, **kwargs: [rejected],
    )
    loop = DecisionLoop(memory=FractalMemory(str(tmp_path / "anne.db")))

    result = loop.run_cognitive("Explore a bounded technical option")

    assert result.status == "BOUNDED"
    assert result.selection is not None
    assert not result.selection.accepted
    assert result.stage_trace == (
        "FAIL_FAST",
        "DUY",
        "BAK",
        "AMBIGUITY",
        "GÖR",
        "MITOS",
        "SELECT",
    )
    assert "ANLA" not in result.stage_trace
    assert "YAP" not in result.stage_trace


def test_anla_rejection_forces_halt_before_action(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "anne.core.pipeline.passes_anla",
        lambda *args, **kwargs: (False, 0.1),
    )
    memory = FractalMemory(str(tmp_path / "anne.db"))
    pipeline = AnnePipeline(memory=memory, anla_enabled=True, max_anla_retries=1)
    hypothesis = Hypothesis(
        "h1",
        "technical",
        "a semantically rejected claim",
        0.8,
    )
    state = pipeline.duy("Evaluate this option", [Consciousness(id="user")])
    state = pipeline.bak(state)
    state = pipeline.gor(state, [hypothesis])
    state = pipeline.anla(state, hypothesis)
    assert state.logic_valid is False
    state = pipeline.yap(state, hypothesis)
    assert state.action == "HALT"
