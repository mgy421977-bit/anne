"""Bounded specialist-agent orchestration for MITOS."""
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
    mission_id: str = field(default_factory=lambda: f"mission_{uuid4().hex[:12]}")
    allowed_tools: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ("external_side_effects", "system_modification", "credential_access", "financial_transaction", "agent_creation")
    search_budget: int = 25
    compute_budget: float = 1.0
    runtime_seconds: int = 600
    output_schema: str = "EvidencePackage"
    def validate(self) -> None:
        if not self.objective.strip() or not self.scope.strip() or not self.mission_id.strip():
            raise ValueError("objective, scope and mission_id are required")
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
        if not self.claim.strip() or not self.source.strip() or not self.provenance.strip():
            raise ValueError("claim, source and provenance are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

@dataclass(frozen=True)
class EvidencePackage:
    mission_id: str
    agent_id: str
    role: AgentRole
    findings: tuple[EvidenceItem, ...] = ()
    contradictions: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()
    simulation_results: tuple[str, ...] = ()
    def validate(self) -> None:
        if not self.mission_id.strip() or not self.agent_id.strip():
            raise ValueError("mission_id and agent_id are required")
        for finding in self.findings:
            finding.validate()

@dataclass
class ResearchAgent:
    mission: ResearchMission
    agent_id: str = field(default_factory=lambda: f"agent_{uuid4().hex[:12]}")
    status: str = "CREATED"
    def authorize(self) -> None:
        self.mission.validate(); self.status = "AUTHORIZED"
    def start(self) -> None:
        if self.status != "AUTHORIZED": raise RuntimeError("agent must be authorized before start")
        self.status = "RUNNING"
    def report(self, package: EvidencePackage) -> EvidencePackage:
        if self.status != "RUNNING": raise RuntimeError("agent must be running before reporting")
        package.validate()
        if package.agent_id != self.agent_id or package.mission_id != self.mission.mission_id or package.role != self.mission.role:
            raise ValueError("evidence package does not belong to this agent or mission")
        self.status = "COMPLETED"; return package

@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    mission_id: str
    search_budget: int
    compute_budget: float
    runtime_seconds: int
    released: bool = False

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
    reservations: dict[str, Reservation] = field(default_factory=dict)
    def reserve(self, mission: ResearchMission) -> str | None:
        mission.validate()
        if self.active_agents + 1 > self.max_agents or self.searches_reserved + mission.search_budget > self.max_total_searches or self.compute_reserved + mission.compute_budget > self.max_total_compute or self.runtime_reserved + mission.runtime_seconds > self.max_total_runtime_seconds:
            return None
        rid = f"res_{uuid4().hex[:12]}"
        self.active_agents += 1; self.searches_reserved += mission.search_budget; self.compute_reserved += mission.compute_budget; self.runtime_reserved += mission.runtime_seconds
        self.reservations[rid] = Reservation(rid, mission.mission_id, mission.search_budget, mission.compute_budget, mission.runtime_seconds)
        return rid
    def release(self, reservation_id: str) -> None:
        reservation = self.reservations.get(reservation_id)
        if reservation is None: raise KeyError("unknown reservation")
        if reservation.released: raise RuntimeError("reservation already released")
        self.active_agents -= 1; self.searches_reserved -= reservation.search_budget; self.compute_reserved -= reservation.compute_budget; self.runtime_reserved -= reservation.runtime_seconds
        self.reservations[reservation_id] = Reservation(reservation.reservation_id, reservation.mission_id, reservation.search_budget, reservation.compute_budget, reservation.runtime_seconds, True)

class MitosAgentSwarm:
    """Creates temporary specialist agents under explicit bounded missions."""
    def __init__(self, governor: ResourceGovernor | None = None) -> None:
        self.governor = governor or ResourceGovernor(); self.agents: list[ResearchAgent] = []; self.evidence: list[EvidencePackage] = []; self.reservations: dict[str, str] = {}; self._submitted: set[tuple[str, str]] = set()
    def create(self, missions: list[ResearchMission]) -> list[ResearchAgent]:
        created: list[ResearchAgent] = []
        for mission in missions:
            reservation_id = self.governor.reserve(mission)
            if reservation_id is None: break
            agent = ResearchAgent(mission); agent.authorize(); self.agents.append(agent); self.reservations[agent.agent_id] = reservation_id; created.append(agent)
        return created
    def submit(self, package: EvidencePackage) -> None:
        agent = next((a for a in self.agents if a.agent_id == package.agent_id), None)
        if agent is None: raise ValueError("unknown agent")
        key = (package.mission_id, package.agent_id)
        if key in self._submitted: raise ValueError("evidence package already submitted")
        agent.report(package); self.evidence.append(package); self._submitted.add(key)
        reservation_id = self.reservations.pop(agent.agent_id, None)
        if reservation_id is not None: self.governor.release(reservation_id)
