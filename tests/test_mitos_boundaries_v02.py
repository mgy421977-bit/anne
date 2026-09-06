import pytest

from anne.agent.autonomy import AgentState, AutonomousSystem, MissionContract, OptimizationProposal
from anne.core.agency_gate import ActionDecision, ActionProposal, AgencyGate
from anne.mythos.agent_swarm import AgentRole, EvidenceItem, EvidencePackage, MitosAgentSwarm, ResearchMission, ResourceGovernor
from anne.mythos.engine import MitosEngine


def make_mission() -> ResearchMission:
    return ResearchMission("bounded question", "bounded scope", AgentRole.PHYSICS)


def test_evidence_package_must_match_agent_and_mission():
    swarm = MitosAgentSwarm(ResourceGovernor(max_agents=1))
    agent = swarm.create([make_mission()])[0]
    agent.start()
    package = EvidencePackage("wrong", agent.agent_id, AgentRole.PHYSICS)
    with pytest.raises(ValueError):
        swarm.submit(package)


def test_evidence_requires_provenance():
    item = EvidenceItem("claim", "source", "EVIDENCE", 0.5)
    with pytest.raises(ValueError):
        item.validate()


def test_resource_reservation_is_released_once():
    governor = ResourceGovernor(max_agents=1)
    mission = make_mission()
    reservation = governor.reserve(mission)
    assert reservation is not None
    governor.release(reservation)
    assert governor.active_agents == 0
    with pytest.raises(RuntimeError):
        governor.release(reservation)


def test_agency_gate_requires_provenance_and_reviews_risky_actions():
    gate = AgencyGate(review_risk_threshold=0.5)
    missing = gate.authorize(ActionProposal("x", risk=0.1), safety_allowed=True)
    assert missing.decision is ActionDecision.DENY
    risky = gate.authorize(ActionProposal("x", risk=0.9, provenance=("e1",)), safety_allowed=True)
    assert risky.decision is ActionDecision.REVIEW


def test_autonomous_system_rejects_invalid_state_transition():
    system = AutonomousSystem(MissionContract("mission", "scope"))
    with pytest.raises(RuntimeError):
        system.complete()
    system.authorize()
    system.start()
    system.observe({"score": 1.0})
    system.complete()
    assert system.state is AgentState.COMPLETED


def test_optimization_requires_real_verification_evidence_and_metrics():
    proposal = OptimizationProposal("sys1", "v1", "v2", {"score": 1.1}, "routing change", True, True)
    assert not proposal.promotable()
    verified = OptimizationProposal(
        "sys1", "v1", "v2", {"score": 1.1}, "routing change", True, True,
        verification_evidence=("benchmark-42",), baseline_metrics={"score": 1.0}, observed_metrics={"score": 1.1},
    )
    assert verified.promotable()


def test_mitos_seed_reproduces_values_and_ids_within_a_fresh_engine():
    first = MitosEngine(seed=7).generate("bounded goal", 5)
    second = MitosEngine(seed=7).generate("bounded goal", 5)
    assert [(x.id, x.claim, x.discovery_value) for x in first] == [(x.id, x.claim, x.discovery_value) for x in second]


def test_mission_cannot_remove_mandatory_specialist_restrictions():
    with pytest.raises(ValueError):
        ResearchMission(
            "question", "scope", AgentRole.PHYSICS,
            forbidden_actions=("external_side_effects",),
        ).validate()
