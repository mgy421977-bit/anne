"""MITOS specialist-agent factory.

MITOS may decide which specialist capabilities are needed, but every agent is
created with an explicit, finite MissionContract. Network access belongs to
workers, not to MITOS itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Mapping


@dataclass(frozen=True)
class ResourceBudget:
    max_runtime_s: int = 1200
    max_requests: int = 100
    max_compute_seconds: int = 1800
    max_storage_mb: int = 1024


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    objective: str
    role: str
    allowed_tools: FrozenSet[str] = frozenset()
    forbidden_actions: FrozenSet[str] = frozenset({"external_action", "agent_creation", "system_mutation"})
    budget: ResourceBudget = field(default_factory=ResourceBudget)
    output_schema: str = "EvidencePackage"


@dataclass(frozen=True)
class ResearchRequest:
    role: str
    objective: str
    tools: FrozenSet[str]
    budget: ResourceBudget = field(default_factory=ResourceBudget)


@dataclass(frozen=True)
class ResearchAgent:
    contract: MissionContract
    network_enabled: bool = False
    active: bool = False


class AgentFactory:
    """Creates disposable, capability-limited research workers."""

    def create(self, request: ResearchRequest, mission_id: str) -> ResearchAgent:
        contract = MissionContract(
            mission_id=mission_id,
            objective=request.objective,
            role=request.role,
            allowed_tools=request.tools,
            budget=request.budget,
        )
        network_enabled = "web_search" in request.tools or "literature_search" in request.tools
        return ResearchAgent(contract=contract, network_enabled=network_enabled, active=True)

    def close(self, agent: ResearchAgent) -> ResearchAgent:
        return ResearchAgent(contract=agent.contract, network_enabled=agent.network_enabled, active=False)


class MitosResourceGovernor:
    """Hard resource boundary between MITOS planning and agent execution."""

    def __init__(self, max_agents: int = 8):
        if max_agents < 1:
            raise ValueError("max_agents must be positive")
        self.max_agents = max_agents
        self._active = 0

    @property
    def active_agents(self) -> int:
        return self._active

    def admit(self) -> bool:
        if self._active >= self.max_agents:
            return False
        self._active += 1
        return True

    def release(self) -> None:
        self._active = max(0, self._active - 1)

    def can_allocate(self, count: int) -> bool:
        return count >= 0 and self._active + count <= self.max_agents


SPECIALIST_CAPABILITIES: Mapping[str, FrozenSet[str]] = {
    "chemistry": frozenset({"web_search", "literature_search", "symbolic_math"}),
    "physics": frozenset({"web_search", "literature_search", "symbolic_math", "simulation"}),
    "patent_literature": frozenset({"web_search", "literature_search"}),
    "economics": frozenset({"web_search", "literature_search", "calculator"}),
    "simulation": frozenset({"simulation", "symbolic_math"}),
    "manufacturing": frozenset({"web_search", "literature_search", "calculator"}),
    "risk": frozenset({"web_search", "literature_search", "calculator"}),
}
