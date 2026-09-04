from __future__ import annotations

import pytest

from anne.multi_agent import AgentMessage, AgentRole, MultiAgentCoordinator


def test_multi_agent_reaches_consensus_with_bounded_rounds() -> None:
    coordinator = MultiAgentCoordinator(
        [AgentRole("researcher", "evidence"), AgentRole("critic", "review")],
        max_rounds=2,
    )

    def worker(name: str):
        def run(task: str, workspace, round_number: int) -> AgentMessage:
            return AgentMessage(name, name, "verify first", ["meter-data"], 0.8)

        return run

    result = coordinator.collaborate(
        "size a battery", {"researcher": worker("researcher"), "critic": worker("critic")}
    )
    assert result.status == "consensus"
    assert result.consensus == "verify first"
    assert result.rounds == 1


def test_multi_agent_preserves_dissent_instead_of_forcing_consensus() -> None:
    coordinator = MultiAgentCoordinator(
        [AgentRole("researcher", "evidence"), AgentRole("critic", "review")]
    )

    def worker(conclusion: str):
        def run(task: str, workspace, round_number: int) -> AgentMessage:
            return AgentMessage(conclusion, "specialist", conclusion, confidence=0.6)

        return run

    result = coordinator.collaborate(
        "choose a design",
        {"researcher": worker("choose A"), "critic": worker("choose B")},
    )
    assert result.status == "dissent"
    assert result.consensus is None
    assert result.unresolved_disagreements


def test_coordinator_requires_bounded_configuration() -> None:
    with pytest.raises(ValueError):
        MultiAgentCoordinator([])
    with pytest.raises(ValueError):
        MultiAgentCoordinator([AgentRole("a", "test")], max_rounds=6)
