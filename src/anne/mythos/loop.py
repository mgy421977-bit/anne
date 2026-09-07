"""Executable protocol connecting MITOS exploration to ANNE evaluation.

MITOS may generate and broadcast hypotheses, but it never selects the
operational winner. ANNE's deterministic selector is the executive gate.
The loop stops before external action; downstream code must perform any
separate authorization and execution step.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from anne.core.global_workspace import GlobalWorkspace, WorkspaceItem
from anne.mythos.candidate_selection import CandidateSelector, Decision, SelectionResult, TaskMode
from anne.mythos.engine import HypothesisCandidate, MitosEngine
from anne.mythos.experience import ExperienceRecord


@dataclass(frozen=True)
class DiscoveryBatch:
    goal: str
    candidates: list[HypothesisCandidate]
    shortlisted: list[HypothesisCandidate]
    selection: SelectionResult | None = None


class MitosAnneLoop:
    """Bounded discovery loop: generate -> publish -> ANNE select."""

    def __init__(
        self,
        engine: MitosEngine | None = None,
        workspace: GlobalWorkspace | None = None,
        selector: CandidateSelector | None = None,
    ) -> None:
        self.engine = engine or MitosEngine()
        self.workspace = workspace or GlobalWorkspace()
        self.selector = selector or CandidateSelector()
        self.last_selection: SelectionResult | None = None

    def propose(
        self,
        goal: str,
        batch_size: int = 10,
        evaluator: Callable[[HypothesisCandidate], bool] | None = None,
        task_mode: TaskMode = TaskMode.HYPOTHESIS,
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

        # The selector evaluates only this generation batch. Workspace history
        # is telemetry/context, never an alternative authority for selection.
        selection = self.selector.select(
            (self.selector.from_hypothesis(c, task_mode=task_mode) for c in candidates),
            context=goal,
        )
        self.last_selection = selection
        winner = selection.winner
        shortlisted: list[HypothesisCandidate] = []
        if winner is not None and selection.decision is Decision.SELECT:
            selected = next((c for c in candidates if c.id == winner.id), None)
            # Backward-compatible evaluator hook may reject the selected
            # candidate, but it cannot promote a different candidate.
            if selected is not None and (evaluator is None or evaluator(selected)):
                shortlisted = [selected]

        return DiscoveryBatch(goal, candidates, shortlisted, selection)

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
