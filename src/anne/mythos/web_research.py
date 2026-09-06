"""MITOS bridge for bounded specialist information gathering.

MITOS is the exploratory information-gathering layer. It plans scoped
research missions, collects observations and provenance, and returns evidence
packages to ANNE. MITOS does not decide truth, answer the user, or promote
findings to FACT; epistemic evaluation and the final decision belong to ANNE.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from anne.learning.evidence import EvidenceItem as AnneEvidenceItem
from anne.learning.web_research import WebResearcher
from .agent_swarm import AgentRole, EvidenceItem, EvidencePackage, MitosAgentSwarm, ResearchMission


@dataclass(frozen=True)
class MitosResearchResult:
    """Collected research returned from MITOS to ANNE.

    ``completed`` means that a mission executed and reported. It does not mean
    that the findings are true, sufficient, or selected for the final answer.
    ANNE owns evaluation, verification, synthesis, and decision.
    """

    evidence: tuple[AnneEvidenceItem, ...]
    trace: tuple[str, ...]
    missions: int
    completed: int


class MitosWebResearch:
    """Plan and collect bounded web evidence for ANNE.

    MITOS may explore multiple specialist perspectives, including incomplete
    or contradictory results. It returns what it found; ANNE decides what the
    evidence means.
    """

    MAX_PARALLEL_MISSIONS = 3

    def __init__(self, web: WebResearcher | None = None) -> None:
        self.web = web or WebResearcher()

    @staticmethod
    def _missions(question: str) -> list[ResearchMission]:
        q = question.strip()
        facets = (
            (AgentRole.ECONOMICS, "economic and financing information"),
            (AgentRole.MANUFACTURING, "technical investment information and industrial applicability"),
            (AgentRole.RISK, "current official support, regulatory and implementation information"),
        )
        return [
            ResearchMission(
                objective=f"Collect information about {facet} relevant to the user's question. Do not decide the final answer.",
                scope=f"Question: {q}\nFocus: {facet}.\nOutput: sources, claims, uncertainty and open questions.",
                role=role,
                allowed_tools=("public_web",),
                search_budget=8,
                compute_budget=0.25,
                runtime_seconds=30,
            )
            for role, facet in facets
        ]

    @staticmethod
    def _query(mission: ResearchMission) -> str:
        """Keep the retrieval query focused on the user question plus one facet.

        Mission-control prose is not sent to the search engine because it can
        dilute retrieval relevance and cause unrelated results to outrank the
        actual subject.
        """
        scope = mission.scope
        question = scope.split("Question:", 1)[-1].split("\nFocus:", 1)[0].strip()
        focus = scope.split("\nFocus:", 1)[-1].split("\nOutput:", 1)[0].strip()
        return f"{question} {focus}".strip()

    def _run_agent(self, agent) -> tuple[object, list[AnneEvidenceItem], EvidencePackage | None, str]:
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
            return agent, findings, package, f"MITOS | agent={agent.agent_id}; role={mission.role.value}; web_evidence={len(findings)}; status=COLLECTED"
        except Exception as exc:
            return agent, [], None, f"MITOS | agent={agent.agent_id}; role={mission.role.value}; status=FAILED; error={exc}"

    def research(self, question: str) -> MitosResearchResult:
        missions = self._missions(question)
        swarm = MitosAgentSwarm()
        agents = swarm.create(missions)
        trace = [
            f"MITOS | information collection started; missions={len(missions)}; agents_authorized={len(agents)}",
            "MITOS | authority=RESEARCH_ONLY; truth/fact/final-answer decisions belong to ANNE",
        ]
        collected: list[AnneEvidenceItem] = []
        completed = 0

        with ThreadPoolExecutor(max_workers=min(self.MAX_PARALLEL_MISSIONS, max(1, len(agents)))) as executor:
            futures = [executor.submit(self._run_agent, agent) for agent in agents]
            for future in as_completed(futures):
                agent, findings, package, status_line = future.result()
                if package is not None:
                    swarm.submit(package)
                    completed += 1
                    collected.extend(findings)
                else:
                    reservation = swarm.reservations.pop(agent.agent_id, None)
                    if reservation:
                        swarm.governor.release(reservation)
                trace.append(status_line)

        trace.append(
            f"MITOS | collection complete; evidence_items={len(collected)}; missions_completed={completed}/{len(missions)}; handing evidence to ANNE"
        )
        return MitosResearchResult(tuple(collected), tuple(trace), len(missions), completed)


__all__ = ["MitosResearchResult", "MitosWebResearch"]
