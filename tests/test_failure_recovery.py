from anne.core.failure_recovery import (
    FailureKind,
    FailureRecoveryController,
    FailureSignal,
)


def test_failure_is_classified_and_reframed_without_authority() -> None:
    failure = FailureSignal(
        kind=FailureKind.SEMANTIC,
        reason="Semantic Validation Layer blocked output",
        stage="YAP",
        cycle_id="cycle-1",
        depth=1,
    )
    plan = FailureRecoveryController.plan(failure, "BESS nedir?", attempt=2)

    assert plan.strategy == "clarify_claim"
    assert plan.question.startswith("Clarify the claim:")
    assert plan.parent_cycle_id == "cycle-1"
    assert plan.depth == 2
    assert plan.attempt == 2


def test_retry_budget_is_hard_boundary() -> None:
    decision = FailureRecoveryController.authorize_retry(
        attempt=3,
        max_retries=3,
        seen_questions=set(),
        question="new frame",
    )

    assert decision.allowed is False
    assert decision.reason == "retry_budget_exhausted"


def test_retry_rejects_repeated_frame_as_oscillation() -> None:
    decision = FailureRecoveryController.authorize_retry(
        attempt=1,
        max_retries=3,
        seen_questions={"same frame"},
        question="same frame",
    )

    assert decision.allowed is False
    assert decision.reason == "oscillation_detected"


def test_retry_authorization_is_bounded_and_non_authoritative() -> None:
    decision = FailureRecoveryController.authorize_retry(
        attempt=1,
        max_retries=3,
        seen_questions={"original"},
        question="new frame",
    )

    assert decision.allowed is True
    assert decision.next_attempt == 2
    assert decision.reason == "retry_authorized"
