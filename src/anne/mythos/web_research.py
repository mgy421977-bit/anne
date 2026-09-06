"""MITOS bridge for bounded specialist web research.

MITOS plans scoped research missions; the shared ANNE WebResearcher performs
retrieval. MITOS never becomes an external-action authority.
"""
from __future__ import annotations

from dataclasses import dataclass

from anne.learning.evidence import EvidenceItem as AnneEvidenceItem
from anne.learning.web_research import WebResearcher
from .agent_swarm import AgentRole, EvidenceItem, EvidencePackage, MitosAgentSwarm, ResearchMission


@dataclass(frozen=True)
class MitosResearchResult:
    evidence: tuple[AnneEvidenceItem, ...]
    trace: tuple[str, ...]
    missions: int
    completed: int


class MitosWebResearch:
    """Turns an ANNE evidence gap into bounded MITOS research missions."""

    def __init__(self, web: WebResearcher | None = None) -> None:
        self.web = web or WebResearcher()

    @staticmethod
    def _missions(question: str) -> list[ResearchMission]:
        q = question.strip()
        facets = (
            (AgentRole.ECONOMICS, "economic and financing options"),
            (AgentRole.MANUFACTURING, "technical investment options and industrial applicability"),
            (AgentRole.RISK, "current official support, regulatory and implementation constraints"),
        )
        return [
            ResearchMission(
                objective=f"Research {facet} relevant to the user's question.",
                scope=f"Question: {q}\nFocus: {facet}.",
                role=role,
                allowed_tools=("public_web",),
                search_budget=8,
                compute_budget=0.25,
                runtime_seconds=120,
            )
            for role, facet in facets
        ]

    @staticmethod
    def _query(mission: ResearchMission) -> str:
        return mission.scope.split("Question:", 1)[-1].split("\nFocus:", 1)[0].strip() + " " + mission.objective

    def research(self, question: str) -> MitosResearchResult:
        missions = self._missions(question)
        swarm = MitosAgentSwarm()
        agents = swarm.create(missions)
        trace = [f"MITOS | research gap detected; missions={len(missions)}; agents_authorized={len(agents)}"]
        collected: list[AnneEvidenceItem] = []
        completed = 0

        for agent in agents:
            agent.start()
            mission = agent.mission
            try:
                findings = self.web.research(self._query(mission))
                package_items = tuple(
                    EvidenceItem(
                        claim=item.claim,
                        source=item.source,
                        evidence_kind="OBSERVATION",
                        confidence=item.confidence,
                        provenance=item.provenance,
                    )
                    for item in findings
                )
                package = EvidencePackage(
                    mission_id=mission.mission_id,
                    agent_id=agent.agent_id,
                    role=mission.role,
                    findings=package_items,
                    open_questions=() if findings else ("No public-web evidence returned for this mission.",),
                )
                swarm.submit(package)
                completed += 1
                trace.append(f"MITOS | agent={agent.agent_id}; role={mission.role.value}; web_evidence={len(findings)}; status=COMPLETED")
                collected.extend(findings)
            except Exception as exc:
                trace.append(f"MITOS | agent={agent.agent_id}; role={mission.role.value}; status=FAILED; error={exc}")
                reservation = swarm.reservations.pop(agent.agent_id, None)
                if reservation:
                    swarm.governor.release(reservation)

        trace.append(f"MITOS | synthesis input={len(collected)} evidence items; returning evidence to ANNE")
        return MitosResearchResult(tuple(collected), tuple(trace), len(missions), completed)


__all__ = ["MitosResearchResult", "MitosWebResearch"]
