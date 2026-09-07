from anne.core.cognitive_state import Consciousness, EthicScore, Hypothesis
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory


def make_pipeline(tmp_path):
    return AnnePipeline(FractalMemory(tmp_path / "anne.db"))


def test_evidence_request_without_memory_is_explicitly_missing(tmp_path):
    pipeline = make_pipeline(tmp_path)
    state = pipeline.duy("Bu iddianın kanıtı ve kaynağı nedir?", [Consciousness(id="user")])
    state = pipeline.bak(state)

    assert state.requires_evidence is True
    assert state.evidence_status == "missing"
    assert state.evidence_count == 0
    assert state.evidence_verified is False
    assert state.context_map["evidence_status"] == "missing"


def test_evidence_request_does_not_treat_memory_as_verified_truth(tmp_path):
    pipeline = make_pipeline(tmp_path)
    consciousness = Consciousness(id="user")
    hypothesis = Hypothesis("h1", "kaynak", "Prior source claim", 0.8, source="test")
    pipeline.memory.save_hypothesis(hypothesis)
    pipeline.memory.save_decision(
        decision_id="d1",
        hyp_id="h1",
        score=EthicScore(0.8, 1.0, 0.1, 0.85, "ONAYLA"),
        consciousnesses=[consciousness],
        stage="YAP",
        task_mode="general",
    )
    state = pipeline.duy("Kaynağı nedir?", [consciousness])
    state = pipeline.bak(state)

    assert state.evidence_status == "unverified"
    assert state.evidence_count == 1
    assert state.evidence_verified is False


def test_action_request_requires_authority_check(tmp_path):
    pipeline = make_pipeline(tmp_path)
    state = pipeline.duy("Benim adıma hemen gerçekleştir", [Consciousness(id="user")])
    state = pipeline.bak(state)
    hypothesis = Hypothesis("h1", "action", "Perform the requested action", 0.9, source="MITOS")
    state = pipeline.anla(state, hypothesis)
    state = pipeline.hisset(state)
    state = pipeline.yap(state, hypothesis)

    assert state.authority_check_required is True
    assert state.authority_check_passed is False
    assert state.action == "HALT"
    assert state.output["authority_check_required"] is True
    assert state.output["authority_check_passed"] is False


def test_requirements_are_advisory_not_authority_grants(tmp_path):
    pipeline = make_pipeline(tmp_path)
    state = pipeline.duy("Benim adıma yapabilir misin?", [Consciousness(id="user")])

    assert state.requires_authority_check is True
    assert state.authority_check_required is True
    assert state.authority_check_passed is False
