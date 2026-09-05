"""MITOS subconscious orchestration primitives.

MITOS is modeled as an exploratory subconscious layer: it may generate
questions, associations, hypotheses and bounded research missions, but it
never receives executive authority. Specialist agents are temporary workers
with explicit contracts and resource limits. Their outputs return as evidence
for MITOS synthesis; only ANNE can evaluate and authorize consequential work.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class SpecialistRole(str, Enum):
    CHEMISTRY = "CHEMISTRY"
    PHYSICS = "PHYSICS"
    LITERATURE_PATENT = "LITERATURE_PATENT"
    ECONOMICS = "ECONOMICS"
    SIMULATION = "SIMULATION"
    MANUFACTURING = "MANUFACTURING"
    RISK = "RISK"
    GENERAL = "GENERAL"


@dataclass(frozen=True)
class ResearchMission:
    question: str
    role: SpecialistRole
    allowed_tools: tuple[str, ...] = ("web_search",)
    forbidden_actions: tuple[str, ...] = (
        "external_side_effects",
        "credential_access",
        "financial_transaction",
        "system_modification",
        "agent_creation",
    )
    max_searches: int = 25
    compute_seconds: int = 300
    runtime_seconds: int = 600
    max_output_items: int = 50

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question cannot be empty")
        if self.max_searches < 1 or self.compute_seconds < 1 or self.runtime_seconds < 1:
            raise ValueError("research budgets must be positive")
        if self.max_output_items < 1:
            raise ValueError("max_output_items must be positive")
        if "agent_creation" not in self.forbidden_actions:
            raise ValueError("specialist agents cannot create agents")
        if "external_side_effects" not in self.forbidden_actions:
            raise ValueError("research agents must be side-effect free")


@dataclass(frozen=True)
class EvidencePackage:
    mission_id: str
    role: SpecialistRole
    findings: tuple[str, ...]
    sources: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    simulated: bool = False
    provenance: str = ""


@dataclass(frozen=True)
class ResearchAgent:
    mission: ResearchMission
    agent_id: str = field(default_factory=lambda: f"agent_{uuid4().hex[:10]}")

    def validate(self) -> None:
        self.mission.validate()


class MitosSubconscious:
    """Creates bounded research workers and synthesizes their evidence."""

    def __init__(self, max_concurrent_agents: int = 7) -> None:
        if max_concurrent_agents < 1:
            raise ValueError("max_concurrent_agents must be >= 1")
        self.max_concurrent_agents = max_concurrent_agents

    def create_agents(self, missions: list[ResearchMission]) -> list[ResearchAgent]:
        if len(missions) > self.max_concurrent_agents:
            raise ValueError("MITOS resource governor: agent limit exceeded")
        agents = [ResearchAgent(mission=m) for m in missions]
        for agent in agents:
            agent.validate()
        return agents

    @staticmethod
    def synthesize(evidence: list[EvidencePackage]) -> dict[str, object]:
        findings: list[str] = []
        sources: list[str] = []
        uncertainties: list[str] = []
        contradictions: list[str] = []
        for package in evidence:
            findings.extend(package.findings)
            sources.extend(package.sources)
            uncertainties.extend(package.uncertainties)
            contradictions.extend(package.contradictions)
        return {
            "findings": tuple(dict.fromkeys(findings)),
            "sources": tuple(dict.fromkeys(sources)),
            "uncertainties": tuple(dict.fromkeys(uncertainties)),
            "contradictions": tuple(dict.fromkeys(contradictions)),
            "evidence_count": len(evidence),
        }
