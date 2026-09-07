"""ANNE-side selection of MITOS proposals.

The selector is intentionally conservative: MITOS generates, ANNE selects.
No candidate is synthesized into a new claim here.
"""
from __future__ import annotations

from collections.abc import Sequence

from anne.mythos.candidate import HypothesisCandidate, SelectionResult, TaskMode


class CandidateSelector:
    """Hard-gate then soft-score MITOS candidates."""

    def __init__(self, *, min_testability: float = 0.25, max_harm_risk: float = 0.0) -> None:
        self.min_testability = min_testability
        self.max_harm_risk = max_harm_risk

    def select(
        self,
        candidates: Sequence[HypothesisCandidate],
        *,
        task_mode: TaskMode = TaskMode.GENERAL,
    ) -> SelectionResult:
        considered = len(candidates)
        eligible: list[tuple[float, HypothesisCandidate]] = []
        for candidate in candidates:
            candidate.validate()
            if candidate.harm_risk > self.max_harm_risk:
                continue
            if candidate.testability < self.min_testability:
                continue
            score = self._score(candidate, task_mode)
            eligible.append((score, candidate))

        if not eligible:
            return SelectionResult(
                None,
                False,
                0.0,
                "no_candidate_passed_hard_gate",
                considered,
            )
        score, candidate = max(eligible, key=lambda item: item[0])
        return SelectionResult(
            candidate,
            True,
            round(score, 4),
            "selected_by_bounded_score",
            considered,
        )

    @staticmethod
    def _score(candidate: HypothesisCandidate, task_mode: TaskMode) -> float:
        # Task mode changes weighting only; it never bypasses the hard gate.
        novelty_weight = 0.12 if task_mode == TaskMode.TECHNICAL else 0.18
        testability_weight = 0.25 if task_mode == TaskMode.TECHNICAL else 0.20
        score = (
            0.20 * candidate.probability
            + 0.18 * candidate.discovery_value
            + novelty_weight * candidate.novelty
            + testability_weight * candidate.testability
            + 0.10 * candidate.reversibility
            + 0.10 * candidate.expected_benefit
            + 0.05 * (1.0 - candidate.test_cost)
            - 0.20 * candidate.harm_risk
        )
        return max(0.0, min(1.0, score))


__all__ = ["CandidateSelector"]
