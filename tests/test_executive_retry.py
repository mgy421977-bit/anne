from anne.core.cognitive_orchestrator import CognitiveOrchestrator
from anne.core.failure_recovery import FailureRecoveryController
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.candidate import Candidate, SelectionResult, TaskMode


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
    result = CognitiveOrchestrator(pipeline, max_retries=1).run("2 + 2", seed=1)
    assert result.status in {"EXECUTED", "BOUNDED", "ABORTED"}
    assert result.lineage
    assert result.retry_count >= 0
