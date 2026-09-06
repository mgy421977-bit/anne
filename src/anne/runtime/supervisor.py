"""Evidence-gated supervisor for ANNE's bounded self-development loop."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from anne.mythos.engine import HypothesisCandidate, MitosEngine


class DevelopmentDecision(str, Enum):
    REJECT = "REJECT"
    PROPOSE = "PROPOSE"
    SANDBOX = "SANDBOX"
    PROMOTE = "PROMOTE"


@dataclass(frozen=True)
class DevelopmentProposal:
    candidate_id: str
    goal: str
    change: str
    decision: DevelopmentDecision
    reason: str
    required_tests: tuple[str, ...]


class DevelopmentSupervisor:
    """Keeps MITOS exploratory and gives promotion authority to ANNE's gates.

    This prototype never executes generated code and never promotes a change from
    a hypothesis alone. A future executor may consume the proposal after sandbox,
    benchmark, policy and rollback checks have passed.
    """

    def __init__(self, mitos: MitosEngine | None = None) -> None:
        self.mitos = mitos or MitosEngine(seed=7)

    def propose(self, goal: str, batch_size: int = 5) -> list[DevelopmentProposal]:
        candidates = self.mitos.generate(goal, batch_size=batch_size)
        return [self._evaluate(candidate) for candidate in candidates]

    def _evaluate(self, candidate: HypothesisCandidate) -> DevelopmentProposal:
        candidate.validate()
        tests = (
            "existing regression suite",
            "deterministic capability test",
            "sandbox comparison against last-known-good",
        )
        if candidate.harm_risk > 0.2 or candidate.reversibility < 0.8:
            return DevelopmentProposal(
                candidate.id, candidate.goal, candidate.claim,
                DevelopmentDecision.REJECT,
                "Risk/reversibility gate failed.", tests,
            )
        if candidate.testability < 0.55:
            return DevelopmentProposal(
                candidate.id, candidate.goal, candidate.claim,
                DevelopmentDecision.REJECT,
                "The change is not sufficiently testable yet.", tests,
            )
        return DevelopmentProposal(
            candidate.id, candidate.goal, candidate.claim,
            DevelopmentDecision.PROPOSE,
            "Candidate is testable and reversible, but evidence is insufficient for promotion.",
            tests,
        )

    @staticmethod
    def promotion_allowed(
        *, regression_passed: bool,
        capability_passed: bool,
        sandbox_passed: bool,
        policy_passed: bool,
        rollback_ready: bool,
    ) -> bool:
        """Return True only when every promotion gate is explicitly green."""
        return all((
            regression_passed,
            capability_passed,
            sandbox_passed,
            policy_passed,
            rollback_ready,
        ))

    @staticmethod
    def decision_from_evidence(**evidence: bool) -> DevelopmentDecision:
        """Map explicit evidence to a promotion decision; missing evidence rejects."""
        if not evidence or not all(evidence.values()):
            return DevelopmentDecision.REJECT
        return DevelopmentDecision.PROMOTE


__all__ = ["DevelopmentDecision", "DevelopmentProposal", "DevelopmentSupervisor"]
