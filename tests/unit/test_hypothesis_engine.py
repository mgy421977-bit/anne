from __future__ import annotations

from anne.core.cognitive_state import Hypothesis
from anne.core.hypothesis_engine import HypothesisEngine


def _h(hid: str, claim: str, probability: float, tested: bool = True, result: str = "supported") -> Hypothesis:
    return Hypothesis(
        id=hid,
        topic="topic",
        claim=claim,
        probability=probability,
        tested=tested,
        result=result,
    )


def test_rank_considers_all_candidates_and_preserves_novelty() -> None:
    engine = HypothesisEngine.__new__(HypothesisEngine)
    hypotheses = [
        _h("a", "A system improves through feedback", 0.70),
        _h("b", "A system improves through feedback loops", 0.68),
        _h("c", "The observed effect is caused by external noise", 0.60),
        _h("d", "A rare hidden mechanism explains the effect", 0.18, result="weak"),
    ]

    ranked = engine.rank(hypotheses, related_memory_scores=[0.6, 0.8])

    assert len(ranked) == 4
    assert [item.rank for item in ranked] == [1, 2, 3, 4]
    assert ranked[0].hypothesis.id in {"a", "b", "c"}
    assert any(item.hypothesis.id == "d" for item in ranked)
    assert ranked[-1].novelty > 0


def test_uncertainty_is_zero_for_one_candidate_and_high_for_balanced_candidates() -> None:
    engine = HypothesisEngine.__new__(HypothesisEngine)

    assert engine.uncertainty([0.9]) == 0.0
    balanced = engine.uncertainty([0.25, 0.25, 0.25, 0.25])
    assert balanced == 1.0


def test_rank_changes_when_evidence_changes() -> None:
    engine = HypothesisEngine.__new__(HypothesisEngine)
    supported = _h("supported", "Supported explanation", 0.55, result="supported")
    weak = _h("weak", "Alternative explanation", 0.60, result="weak")

    ranked = engine.rank([supported, weak])

    assert ranked[0].hypothesis.id == "supported"
