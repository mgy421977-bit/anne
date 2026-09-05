from anne.core.agency_gate import ActionDecision, ActionProposal, AgencyGate
from anne.core.cognitive_cycle import CognitiveCycle, Prediction, PredictionError


def test_cycle_requires_behavior_change_for_learning_evidence():
    cycle = CognitiveCycle(goal="test")
    cycle.learning_updates.append({"behavior_changed": False, "evidence_ids": ["e1"]})
    assert not cycle.learning_is_evidenced()
    cycle.learning_updates.append({"behavior_changed": True, "evidence_ids": ["e2"]})
    assert cycle.learning_is_evidenced()


def test_prediction_bounds_and_outcome():
    cycle = CognitiveCycle(goal="test")
    cycle.add_prediction(Prediction("h1", "yes", 0.2, 0.4))
    cycle.record_outcome(
        type("OutcomeLike", (), {"prediction_id": "p1", "observed_outcome": "no", "observed": True, "source": "test", "provenance": ()})(),
        PredictionError("p1", 0.2, "mismatch"),
    )
    assert cycle.status.value == "COMPLETED"
    assert len(cycle.prediction_errors) == 1


def test_agency_gate_fails_closed():
    gate = AgencyGate()
    proposal = ActionProposal("external-action", risk=0.1)
    result = gate.authorize(proposal, safety_allowed=False)
    assert result.decision is ActionDecision.DENY
