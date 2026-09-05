"""Bounded specialist-agent orchestration for MITOS.

MITOS is ANNE's subconscious-inspired exploration layer: it decides what
needs investigation, creates temporary specialist workers, and receives
evidence back for synthesis. Specialist agents never inherit MITOS authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AgentRole(str, Enum):
    CHEMISTRY = "chemistry"
    PHYSICS = "physics"
    PATENT_LITERATURE = "patent_literature"
    ECONOMICS = "economics"
    SIMULATION = "simulation"
    MANUFACTURING = "manufacturing"
    RISK = "risk"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ResearchMission:
    objective: str
    scope: str
    role: AgentRole
    allowed_tools: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = (
        "external_side_effects",
        "system_modification",
        "credential_access",
        "financial_transaction",
        "agent_creation",
    )
    search_budget: int = 25
    compute_budget: float = 1.0
    runtime_seconds: int = 600
    output_schema: str = "EvidencePackage"

    def validate(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not self.scope.strip():
            raise ValueError("scope is required")
        if self.search_budget < 0 or self.compute_budget < 0 or self.runtime_seconds < 0:
            raise ValueError("research budgets cannot be negative")
        required = {"external_side_effects", "credential_access", "system_modification", "financial_transaction", "agent_creation"}
        if not required.issubset(self.forbidden_actions):
            raise ValueError("specialist mission is missing mandatory safety restrictions")


@dataclass(frozen=True)
class EvidenceItem:
    claim: str
    source: str
    evidence_kind: str
    confidence: float = 0.0
    uncertainty: str = ""
    provenance: str = ""

    def validate(self) -> None:
        if not self.claim.strip() or not self.source.strip():
            raise ValueError("claim and source are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class EvidencePackage:
    mission_id: str
    agent_id: str
    role: AgentRole
    findings: list[EvidenceItem] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    simulation_results: list[str] = field(default_factory=list)


@dataclass
class ResearchAgent:
    mission: ResearchMission
    agent_id: str = field(default_factory=lambda: f"agent_{uuid4().hex[:12]}")
    status: str = "CREATED"

    def authorize(self) -> None:
        self.mission.validate()
        self.status = "AUTHORIZED"

    def start(self) -> None:
        if self.status != "AUTHORIZED":
            raise RuntimeError("agent must be authorized before start")
        self.status = "RUNNING"

    def report(self, package: EvidencePackage) -> EvidencePackage:
        if self.status != "RUNNING":
            raise RuntimeError("agent must be running before reporting")
        if package.mission_id != self.agent_id and package.agent_id != self.agent_id:
            raise ValueError("evidence package does not belong to this agent")
        for finding in package.findings:
            finding.validate()
        self.status = "COMPLETED"
        return package


@dataclass
class ResourceGovernor:
    max_agents: int = 8
    max_total_searches: int = 200
    max_total_compute: float = 10.0
    max_total_runtime_seconds: int = 3600
    active_agents: int = 0
    searches_reserved: int = 0
    compute_reserved: float = 0.0
    runtime_reserved: int = 0

    def reserve(self, mission: ResearchMission) -> bool:
        mission.validate()
        if self.active_agents + 1 > self.max_agents:
            return False
        if self.searches_reserved + mission.search_budget > self.max_total_searches:
            return False
        if self.compute_reserved + mission.compute_budget > self.max_total_compute:
            return False
        if self.runtime_reserved + mission.runtime_seconds > self.max_total_runtime_seconds:
            return False
        self.active_agents += 1
        self.searches_reserved += mission.search_budget
        self.compute_reserved += mission.compute_budget
        self.runtime_reserved += mission.runtime_seconds
        return True

    def release(self, mission: ResearchMission) -> None:
        self.active_agents = max(0, self.active_agents - 1)
        self.searches_reserved = max(0, self.searches_reserved - mission.search_budget)
        self.compute_reserved = max(0.0, self.compute_reserved - mission.compute_budget)
        self.runtime_reserved = max(0, self.runtime_reserved - mission.runtime_seconds)


class MitosAgentSwarm:
    """Creates only specialist agents justified by a bounded research plan."""

    def __init__(self, governor: ResourceGovernor | None = None) -> None:
        self.governor = governor or ResourceGovernor()
        self.agents: list[ResearchAgent] = []
        self.evidence: list[EvidencePackage] = []

    def create(self, missions: list[ResearchMission]) -> list[ResearchAgent]:
        created: list[ResearchAgent] = []
        for mission in missions:
            if not self.governor.reserve(mission):
                break
            agent = ResearchAgent(mission)
            agent.authorize()
            self.agents.append(agent)
            created.append(agent)
        return created

    def submit(self, package: EvidencePackage) -> None:
        self.evidence.append(package)
