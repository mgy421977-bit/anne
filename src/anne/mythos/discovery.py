"""Discovery orchestration: MITOS explores, ANNE evaluates."""
from __future__ import annotations

from dataclasses import dataclass

from anne.mythos.engine import HypothesisCandidate, MitosEngine


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    accepted: bool
    score: float
    reason: str


class DiscoveryDrive:
    """Intrinsic-discovery scaffold that remains bounded by ANNE policy."""

    def __init__(self, engine: MitosEngine | None = None) -> None:
        self.engine = engine or MitosEngine()

    def generate(self, goal: str, batch_size: int = 10) -> list[HypothesisCandidate]:
        return self.engine.generate(goal, batch_size=batch_size)

    @staticmethod
    def evaluate(candidate: HypothesisCandidate) -> Evaluation:
        # Hard gate first: no external action is authorised here.
        if candidate.harm_risk > 0.0:
            return Evaluation(candidate.id, False, 0.0, "harm risk requires ANNE safety review")
        score = candidate.discovery_value
        accepted = score >= 0.35 and candidate.testability >= 0.25
        reason = "candidate is testable and low-risk" if accepted else "below discovery gate"
        return Evaluation(candidate.id, accepted, round(score, 4), reason)

    def shortlist(self, candidates: list[HypothesisCandidate], limit: int = 3) -> list[HypothesisCandidate]:
        evaluated = [(self.evaluate(c), c) for c in candidates]
        evaluated.sort(key=lambda pair: pair[0].score, reverse=True)
        return [candidate for evaluation, candidate in evaluated if evaluation.accepted][:limit]
