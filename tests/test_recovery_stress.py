from anne.core.failure_recovery import FailureRecoveryController, FailureSignal
from anne.mythos.candidate import TaskMode


def test_failure_taxonomy_is_conservative_and_stage_aware() -> None:
    assert FailureRecoveryController.classify("semantic validation failed", "ANLA").value == "semantic"
    assert FailureRecoveryController.classify("insufficient evidence", "SELECT").value == "evidence_gap"
    assert FailureRecoveryController.classify("retry budget exhausted", "RETRY_GATE").value == "budget"
    assert FailureRecoveryController.classify("unexpected condition", "YAP").value == "unknown"


def test_reframe_changes_frame_without_granting_authority() -> None:
    failure = FailureSignal(
        kind=FailureRecoveryController.classify("insufficient evidence", "SELECT"),
        reason="insufficient evidence",
        stage="SELECT",
        cycle_id="root",
        depth=0,
    )
    plan = FailureRecoveryController.plan(failure, "Evaluate BESS project", attempt=1)

    assert plan.parent_cycle_id == "root"
    assert plan.depth == 1
    assert plan.attempt == 1
    assert "missing evidence" in plan.question.lower()
    assert "authorize" not in plan.question.lower()


def test_retry_gate_hard_bounds_attempts_and_seen_frames() -> None:
    first = FailureRecoveryController.authorize_retry(
        attempt=0,
        max_retries=1,
        seen_questions={"root"},
        question="reframed root",
    )
    assert first.allowed is True
    assert first.next_attempt == 1

    exhausted = FailureRecoveryController.authorize_retry(
        attempt=1,
        max_retries=1,
        seen_questions={"root", "reframed root"},
        question="third frame",
    )
    assert exhausted.allowed is False
    assert exhausted.reason == "retry_budget_exhausted"

    oscillating = FailureRecoveryController.authorize_retry(
        attempt=0,
        max_retries=2,
        seen_questions={"root", "reframed root"},
        question="reframed   root",
    )
    assert oscillating.allowed is False
    assert oscillating.reason == "oscillation_detected"


def test_task_mode_does_not_change_recovery_safety_contract() -> None:
    assert TaskMode.GENERAL.value == "general"
    assert TaskMode.TECHNICAL.value == "technical"
