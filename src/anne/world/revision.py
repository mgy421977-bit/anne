"""Evidence-weighted belief revision and causal hypotheses."""

from __future__ import annotations

from dataclasses import dataclass, field

from anne.world.model import Belief, BeliefStore


@dataclass
class CausalHypothesis:
    cause: str
    effect: str
    mechanism: str
    confidence: float
    supporting_evidence: list[str] = field(default_factory=list)
    counterevidence: list[str] = field(default_factory=list)
    status: str = "unverified"


class BeliefRevision:
    """Revises beliefs conservatively; conflicts remain visible as disputed."""

    def __init__(self, store: BeliefStore | None = None) -> None:
        self.store = store or BeliefStore()
        self.causal_hypotheses: list[CausalHypothesis] = []

    def revise(self, belief: Belief, source_reliability: float = 0.5) -> Belief:
        belief.confidence = max(
            0.0,
            min(1.0, belief.confidence * max(0.0, min(1.0, source_reliability))),
        )
        return self.store.add(belief)

    def add_causal(self, hypothesis: CausalHypothesis) -> CausalHypothesis:
        hypothesis.confidence = max(0.0, min(1.0, hypothesis.confidence))
        hypothesis.status = "supported" if hypothesis.supporting_evidence else "needs_review"
        self.causal_hypotheses.append(hypothesis)
        return hypothesis


__all__ = ["BeliefRevision", "CausalHypothesis"]
