from __future__ import annotations

from anne.neuro_symbolic.audit import NeuroSymbolicValidator, PlanStep
from anne.semantics.core import Provenance, frame_from_text
from anne.world.model import Belief, BeliefStore


def test_frame_preserves_source_provenance_and_hash() -> None:
    frame = frame_from_text("Alice sent the report", source_ref="ticket-1")
    assert frame.evidence[0].provenance.source_ref == "ticket-1"
    assert len(frame.evidence[0].provenance.content_hash) == 64
    assert frame.claims[0].source_id == frame.evidence[0].id


def test_belief_store_marks_conflicting_beliefs_disputed() -> None:
    store = BeliefStore()
    evidence = frame_from_text("source").evidence[0]
    store.supported_by(evidence, "report", "status", "open")
    store.add(Belief("report", "status", "closed", 0.7, [evidence.id]))
    assert {belief.status for belief in store.query("report", "status")} == {"disputed"}


def test_validator_requires_traceable_evidence() -> None:
    audit = NeuroSymbolicValidator().audit("conclusion", [])
    assert audit.evidence_ids == []
    assert audit.calibration_status == "needs_review"
    assert audit.recommended_next_check is not None


def test_plan_step_requires_expected_effect_for_verification() -> None:
    step = PlanStep("p1", "read file", expected_effects=["file loaded"])
    assert step.verify("unexpected") is False
    assert step.status == "failed"
    assert step.verify("file loaded") is True
    assert step.status == "verified"


def test_provenance_is_deterministic_for_same_content() -> None:
    first = Provenance.from_content("file", "a.txt", "same")
    second = Provenance.from_content("file", "a.txt", "same")
    assert first.content_hash == second.content_hash
