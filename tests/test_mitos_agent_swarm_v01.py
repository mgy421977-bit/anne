from anne.mythos.agent_swarm import (
    AgentRole,
    EvidenceItem,
    EvidencePackage,
    MitosAgentSwarm,
    ResearchMission,
    ResourceGovernor,
)
from anne.mythos.synthesis import MitosSynthesis


def mission(role: AgentRole) -> ResearchMission:
    return ResearchMission(
        objective="Investigate a bounded research question",
        scope="Assigned specialist scope only",
        role=role,
        allowed_tools=("web_search", "public_literature")
        if role is not AgentRole.SIMULATION
        else ("sandbox_simulation",),
        search_budget=10,
        compute_budget=1.0,
        runtime_seconds=60,
    )


def test_governor_limits_agent_count():
    swarm = MitosAgentSwarm(ResourceGovernor(max_agents=2))
    agents = swarm.create([mission(AgentRole.PHYSICS), mission(AgentRole.CHEMISTRY), mission(AgentRole.RISK)])
    assert len(agents) == 2


def test_agents_do_not_get_agent_creation_authority():
    swarm = MitosAgentSwarm(ResourceGovernor(max_agents=1))
    agent = swarm.create([mission(AgentRole.PHYSICS)])[0]
    assert "agent_creation" in agent.mission.forbidden_actions


def test_evidence_preserves_provenance_and_synthesis():
    swarm = MitosAgentSwarm()
    agent = swarm.create([mission(AgentRole.PHYSICS)])[0]
    agent.start()
    package = agent.report(
        EvidencePackage(
            mission_id="m1",
            agent_id=agent.agent_id,
            role=AgentRole.PHYSICS,
            findings=[
                EvidenceItem(
                    claim="Candidate mechanism is mathematically consistent under stated assumptions",
                    source="public-paper-A",
                    evidence_kind="HYPOTHESIS",
                    confidence=0.7,
                    uncertainty="No experimental confirmation",
                    provenance="paper-A:section-4",
                )
            ],
        )
    )
    swarm.submit(package)
    synthesis = MitosSynthesis.from_packages(swarm.evidence)
    assert synthesis.findings[0].supporting_sources == ("public-paper-A",)
    assert synthesis.findings[0].status == "HYPOTHESIS"
