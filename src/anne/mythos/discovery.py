"""Discovery orchestration: MITOS explores, ANNE evaluates."""
from __future__ import annotations

from dataclasses import dataclass

from anne.mythos.candidate_selection import CandidateEvaluation, CandidateSelector, SelectionResult, TaskMode
from anne.mythos.engine import HypothesisCandidate, MitosEngine


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    accepted: bool
    score: float
    reason: str


class DiscoveryDrive:
    """Intrinsic-discovery scaffold: MITOS proposes, ANNE selects."""

    def __init__(self, engine: MitosEngine | None = None, selector: CandidateSelector | None = None) -> None:
        self.engine = engine or MitosEngine()
        self.selector = selector or CandidateSelector()
        self.last_selection: SelectionResult | None = None

    def generate(self, goal: str, batch_size: int = 10) -> list[HypothesisCandidate]:
        return self.engine.generate(goal, batch_size=batch_size)

    def evaluate(self, candidate: HypothesisCandidate) -> Evaluation:
        result = self.selector.select([self.selector.from_hypothesis(candidate)], context=candidate.goal)
        evaluation = result.evaluations[0]
        return Evaluation(evaluation.candidate_id, evaluation.accepted, evaluation.final_score,
                          "; ".join(evaluation.reasons))

    def select(self, candidates: list[HypothesisCandidate], context: str = "", task_mode: TaskMode = TaskMode.HYPOTHESIS) -> SelectionResult:
        pool = [self.selector.from_hypothesis(c, task_mode=task_mode) for c in candidates]
        self.last_selection = self.selector.select(pool, context=context)
        return self.last_selection

    def shortlist(self, candidates: list[HypothesisCandidate], limit: int = 3) -> list[HypothesisCandidate]:
        result = self.select(candidates, context=candidates[0].goal if candidates else "")
        if result.winner is None:
            return []
        by_id = {c.id: c for c in candidates}
        selected = [by_id[result.winner.id]]
        # Preserve bounded alternatives for downstream ANLA/YAP; never more than limit.
        for evaluation in sorted(result.evaluations, key=lambda e: e.final_score, reverse=True):
            if len(selected) >= limit:
                break
            if evaluation.accepted and evaluation.candidate_id != result.winner.id:
                selected.append(by_id[evaluation.candidate_id])
        return selected


__all__ = ["DiscoveryDrive", "Evaluation", "CandidateEvaluation", "SelectionResult"]
