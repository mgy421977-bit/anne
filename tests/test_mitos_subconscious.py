from anne.mythos.subconscious import (
    EvidencePackage,
    MitosSubconscious,
    ResearchMission,
    SpecialistRole,
)


def test_specialist_agents_are_bounded_and_cannot_create_agents():
    mission = ResearchMission("Can an alternative propulsion concept reduce travel time?", SpecialistRole.PHYSICS)
    agent = MitosSubconscious(max_concurrent_agents=1).create_agents([mission])[0]
    assert agent.mission.max_searches == 25
    assert "agent_creation" in agent.mission.forbidden_actions
    assert "external_side_effects" in agent.mission.forbidden_actions


def test_mitos_synthesizes_evidence_without_turning_simulation_into_fact():
    result = MitosSubconscious.synthesize([
        EvidencePackage("m1", SpecialistRole.PHYSICS, ("finding A",), ("source-1",)),
        EvidencePackage("m2", SpecialistRole.SIMULATION, ("finding A",), ("source-2",), simulated=True),
    ])
    assert result["findings"] == ("finding A",)
    assert result["evidence_count"] == 2


def test_resource_governor_rejects_excess_agents():
    missions = [
        ResearchMission(f"q{i}", SpecialistRole.GENERAL)
        for i in range(3)
    ]
    try:
        MitosSubconscious(max_concurrent_agents=2).create_agents(missions)
    except ValueError as exc:
        assert "agent limit" in str(exc)
    else:
        raise AssertionError("expected agent limit rejection")
