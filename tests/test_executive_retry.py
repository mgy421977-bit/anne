from anne.core.cognitive_orchestrator import CognitiveOrchestrator
from anne.core.failure_recovery import FailureRecoveryController
from anne.core.pipeline import AnnePipeline
from anne.core.decision_loop import DecisionLoop
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.candidate import HypothesisCandidate, SelectionResult, TaskMode


def _candidate(goal: str, claim: str, probability: float = 0.7) -> HypothesisCandidate:
    return HypothesisCandidate(
        id=goal.replace(" ", "_").lower(),
        goal=goal,
        claim=claim,
        probability=probability,
    )


def test_retry_controller_stops_repeated_frames() -> None:
    decision = FailureRecoveryController.authorize_retry(
        attempt=1,
        max_retries=2,
        seen_questions={"same frame"},
        question="Same   Frame",
    )
    assert decision.allowed is False
    assert decision.reason == "oscillation_detected"


def test_orchestrator_rejects_negative_retry_budget(tmp_path) -> None:
    memory = FractalMemory(tmp_path / "anne.db")
    pipeline = AnnePipeline(memory=memory)
    try:
        CognitiveOrchestrator(pipeline, max_retries=-1)
    except ValueError as exc:
        assert "max_retries" in str(exc)
    else:
        raise AssertionError("negative retry budget must be rejected")


def test_orchestrator_success_exposes_lineage(tmp_path) -> None:
    memory = FractalMemory(tmp_path / "anne.db")
    pipeline = AnnePipeline(memory=memory)
    result = DecisionLoop(memory=memory).run_cognitive("2 + 2", seed=1)
    assert result.status in {"EXECUTED", "BOUNDED", "ABORTED"}
    assert result.lineage
    assert result.retry_count >= 0


def test_candidate_contract_matches_runtime() -> None:
    candidate = _candidate("first", "first claim")
    assert candidate.goal == "first"
    assert candidate.claim == "first claim"
    assert candidate.probability == 0.7


def test_selector_result_contract_matches_candidate() -> None:
    candidate = _candidate("first", "first claim")
    result = SelectionResult(
        candidate=candidate,
        accepted=True,
        score=0.8,
        reason="accepted",
        considered=1,
    )
    assert result.candidate is candidate
    assert result.accepted is True
    assert result.considered == 1
