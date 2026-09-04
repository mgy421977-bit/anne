"""Deterministic coordinator for bounded specialist collaboration."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence

from anne.multi_agent.core import (
    AgentMessage,
    AgentRole,
    CollaborationResult,
    SharedWorkspace,
)

Worker = Callable[[str, SharedWorkspace, int], AgentMessage]


class MultiAgentCoordinator:
    """Runs independent specialists, then aggregates without erasing dissent."""

    def __init__(self, roles: Sequence[AgentRole], max_rounds: int = 2) -> None:
        if not roles:
            raise ValueError("At least one agent role is required")
        if max_rounds < 1 or max_rounds > 5:
            raise ValueError("max_rounds must be between 1 and 5")
        self.roles = list(roles)
        self.max_rounds = max_rounds

    def collaborate(self, task: str, workers: dict[str, Worker]) -> CollaborationResult:
        workspace = SharedWorkspace(task=task)
        for round_number in range(1, self.max_rounds + 1):
            workspace.phase = "deliberate" if round_number == 1 else "review"
            for role in self.roles:
                worker = workers.get(role.name)
                if worker is None:
                    workspace.record_disagreement(f"Missing worker for role: {role.name}")
                    continue
                message = worker(task, workspace, round_number)
                message.round_number = round_number
                workspace.publish(message)
            if self._has_consensus(workspace):
                break
        workspace.phase = "conclude"
        consensus, confidence = self._aggregate(workspace)
        status = "consensus" if consensus else "dissent" if workspace.messages else "no_evidence"
        return CollaborationResult(
            task=task,
            consensus=consensus,
            confidence=confidence,
            messages=list(workspace.messages),
            unresolved_disagreements=list(workspace.unresolved_disagreements),
            rounds=max((item.round_number for item in workspace.messages), default=0),
            status=status,
        )

    @staticmethod
    def _has_consensus(workspace: SharedWorkspace) -> bool:
        conclusions = [item.conclusion.strip() for item in workspace.messages]
        return len(conclusions) >= 2 and len(set(conclusions)) == 1

    @staticmethod
    def _aggregate(workspace: SharedWorkspace) -> tuple[str | None, float]:
        if not workspace.messages:
            return None, 0.0
        counts = Counter(
            item.conclusion.strip()
            for item in workspace.messages
            if item.conclusion.strip()
        )
        if not counts:
            return None, 0.0
        conclusion, votes = counts.most_common(1)[0]
        tied = sum(1 for count in counts.values() if count == votes) > 1
        if tied or votes < 2:
            for item in workspace.messages:
                if item.conclusion.strip() != conclusion:
                    workspace.record_disagreement(
                        f"{item.agent} disagrees with consensus candidate: {item.conclusion}"
                    )
            return None, round(
                sum(item.confidence for item in workspace.messages)
                / len(workspace.messages),
                3,
            )
        confidence = (
            sum(
                item.confidence
                for item in workspace.messages
                if item.conclusion.strip() == conclusion
            )
            / votes
        )
        return conclusion, round(confidence, 3)


__all__ = ["MultiAgentCoordinator", "Worker"]
