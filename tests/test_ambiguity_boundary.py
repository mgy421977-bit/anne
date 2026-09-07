from anne.core.ambiguity import AmbiguityBoundary, AmbiguityLevel
from anne.core.cognitive_orchestrator import CognitiveOrchestrator
from anne.core.pipeline import AnnePipeline
from anne.core.response_surface import ResponseComposer
from anne.memory.fractal_memory import FractalMemory


def make_orchestrator(tmp_path):
    return CognitiveOrchestrator(AnnePipeline(FractalMemory(tmp_path / "anne.db")))


def test_low_ambiguity_continues():
    decision = AmbiguityBoundary.decide(0.20)
    assert decision.level is AmbiguityLevel.LOW
    assert decision.action == "CONTINUE"


def test_medium_ambiguity_requests_clarification():
    decision = AmbiguityBoundary.decide(0.60)
    assert decision.level is AmbiguityLevel.MEDIUM
    assert decision.action == "CLARIFY"


def test_high_ambiguity_abstains():
    decision = AmbiguityBoundary.decide(0.90)
    assert decision.level is AmbiguityLevel.HIGH
    assert decision.action == "ABSTAIN"


def test_boundary_thresholds_are_deterministic():
    assert AmbiguityBoundary.classify(0.49) is AmbiguityLevel.LOW
    assert AmbiguityBoundary.classify(0.50) is AmbiguityLevel.MEDIUM
    assert AmbiguityBoundary.classify(0.74) is AmbiguityLevel.MEDIUM
    assert AmbiguityBoundary.classify(0.75) is AmbiguityLevel.HIGH


def test_out_of_range_scores_are_clamped():
    assert AmbiguityBoundary.classify(-1.0) is AmbiguityLevel.LOW
    assert AmbiguityBoundary.classify(2.0) is AmbiguityLevel.HIGH


def test_ambiguity_is_not_confidence():
    low = AmbiguityBoundary.decide(0.20)
    high = AmbiguityBoundary.decide(0.90)
    assert low.action == "CONTINUE"
    assert high.action == "ABSTAIN"
    assert low.reason != high.reason


def test_medium_ambiguity_returns_clarification_before_mitos(tmp_path):
    result = make_orchestrator(tmp_path).run("Bir şey yap")

    assert result.status == "BOUNDED"
    assert result.stop_reason == "ambiguity_medium"
    assert result.selection is None
    assert result.state is not None
    assert result.state.action == "CLARIFY"
    assert result.state.output["action"] == "CLARIFY"
    assert result.stage_trace == ("FAIL_FAST", "DUY", "BAK", "AMBIGUITY")
    assert result.state.context_map["ambiguity_level"] == "medium"


def test_high_ambiguity_abstains_before_mitos(tmp_path):
    result = make_orchestrator(tmp_path).run("Bunu yap")

    assert result.status == "BOUNDED"
    assert result.stop_reason == "ambiguity_high"
    assert result.selection is None
    assert result.state is not None
    assert result.state.action == "ABSTAIN"
    assert result.state.output["action"] == "HALT"
    assert result.stage_trace == ("FAIL_FAST", "DUY", "BAK", "AMBIGUITY")
    assert result.state.context_map["ambiguity_level"] == "high"


def test_high_ambiguity_does_not_grant_authority(tmp_path):
    result = make_orchestrator(tmp_path).run("Bunu gerçekleştir")

    assert result.state is not None
    assert result.state.authority_check_required is True
    assert result.state.authority_check_passed is False
    assert result.state.action == "ABSTAIN"


def test_clarification_is_rendered_without_internal_fields(tmp_path):
    result = make_orchestrator(tmp_path).run("Bir şey yap")
    response = ResponseComposer().compose("Bir şey yap", result)

    assert response == "Bunu doğru yapabilmem için biraz daha netleştirir misin?"
    assert "Goodness=" not in response
    assert "ambiguity" not in response.lower()


def test_normal_specific_request_still_reaches_mitos(tmp_path):
    result = make_orchestrator(tmp_path).run("Merhaba Anne")

    assert result.state is not None
    assert result.stage_trace[:7] == (
        "FAIL_FAST", "DUY", "BAK", "AMBIGUITY", "GÖR", "MITOS", "SELECT"
    )
    assert result.selection is not None
