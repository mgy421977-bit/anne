"""Executable protocol connecting MITOS exploration to ANNE evaluation.

The loop deliberately stops before external action. A caller supplies the
ANNE evaluation function and, after a real test, records the outcome.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from anne.core.global_workspace import GlobalWorkspace, WorkspaceItem
from anne.mythos.engine import HypothesisCandidate, MitosEngine
from anne.mythos.experience import ExperienceRecord


@dataclass(frozen=True)
class DiscoveryBatch:
    goal: str
    candidates: list[HypothesisCandidate]
    shortlisted: list[HypothesisCandidate]


class MitosAnneLoop:
    """Bounded discovery loop: generate -> broadcast -> ANNE gate."""

    def __init__(self, engine: MitosEngine | None = None, workspace: GlobalWorkspace | None = None) -> None:
        self.engine = engine or MitosEngine()
        self.workspace = workspace or GlobalWorkspace()

    def propose(
        self,
        goal: str,
        batch_size: int = 10,
        evaluator: Callable[[HypothesisCandidate], bool] | None = None,
    ) -> DiscoveryBatch:
        candidates = self.engine.generate(goal, batch_size=batch_size)
        for candidate in candidates:
            self.workspace.publish(
                WorkspaceItem(
                    source="MITOS",
                    content=candidate,
                    salience=candidate.discovery_value,
                    confidence=candidate.probability,
                    novelty=candidate.novelty,
                    risk=candidate.harm_risk,
                )
            )
        gate = evaluator or (lambda c: c.harm_risk <= 0.0 and c.testability >= 0.25)
        shortlisted = [c for c in self.workspace.winners(batch_size) if gate(c.content)]
        return DiscoveryBatch(goal, candidates, [c.content for c in shortlisted])

    @staticmethod
    def begin_experience(candidate: HypothesisCandidate) -> ExperienceRecord:
        return ExperienceRecord(
            hypothesis_id=candidate.id,
            goal=candidate.goal,
            claim=candidate.claim,
            predicted_outcome="pending test",
            confidence=candidate.probability,
            context={
                "mode": candidate.mode.value,
                "novelty": candidate.novelty,
                "testability": candidate.testability,
                "expected_benefit": candidate.expected_benefit,
                "harm_risk": candidate.harm_risk,
                "test_cost": candidate.test_cost,
            },
        )
