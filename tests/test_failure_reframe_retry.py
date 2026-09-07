from anne.core.failure_recovery import (
    FailureKind,
    FailureRecoveryController,
    FailureSignal,
)


def test_failure_is_classified_and_reframed_without_authority_escalation() -> None:
    failure = FailureSignal(
        kind=FailureRecoveryController.classify(
            "Semantic Validation Layer blocked output", "YAP"
        ),
        reason="Semantic Validation Layer blocked output",
        stage="YAP",
        cycle_id="fc_root",
        depth=0,
    )

    assert failure.kind is FailureKind.SEMANTIC
    plan = FailureRecoveryController.plan(failure, "answer the question", attempt=1)

    assert plan.strategy == "clarify_claim"
    assert plan.parent_cycle_id == "fc_root"
    assert plan.depth == 1
    assert plan.question != "answer the question"
    assert "answer the question" in plan.question


def test_retry_requires_budget_and_a_new_frame() -> None:
    first = FailureRecoveryController.authorize_retry(
        attempt=1,
        max_retries=3,
        seen_questions={"original question"},
        question="new frame",
    )
    assert first.allowed is True
    assert first.reason == "retry_authorized"
    assert first.next_attempt == 2

    repeated = FailureRecoveryController.authorize_retry(
        attempt=2,
        max_retries=3,
        seen_questions={"original question", "same frame"},
        question="same frame",
    )
    assert repeated.allowed is False
    assert repeated.reason == "oscillation_detected"

    exhausted = FailureRecoveryController.authorize_retry(
        attempt=3,
        max_retries=3,
        seen_questions={"original question"},
        question="new frame",
    )
    assert exhausted.allowed is False
    assert exhausted.reason == "retry_budget_exhausted"


def test_failure_classification_is_conservative() -> None:
    assert FailureRecoveryController.classify("missing evidence", "YAP") is FailureKind.EVIDENCE_GAP
    assert FailureRecoveryController.classify("logic invalid", "ANLA") is FailureKind.LOGIC
    assert FailureRecoveryController.classify("fractal_iteration_budget_exhausted", "STOP") is FailureKind.BUDGET
    assert FailureRecoveryController.classify("ordinary failure", "YAP") is FailureKind.UNKNOWN
