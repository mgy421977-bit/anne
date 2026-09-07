from anne.core.cognitive_state import Consciousness, EthicScore, Hypothesis
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory


def make_pipeline(tmp_path):
    return AnnePipeline(FractalMemory(tmp_path / "anne.db"))


def test_missing_evidence_blocks_decision(tmp_path):
    pipeline = make_pipeline(tmp_path)
    state = pipeline.duy("Bu iddianın kanıtı nedir?", [Consciousness(id="user")])
    state = pipeline.bak(state)
    state = pipeline.gor(state, [Hypothesis("h1", "iddia", "Unsupported claim", 0.95)])
    state = pipeline.anla(state, Hypothesis("h1", "iddia", "Unsupported claim", 0.95))
    state = pipeline.yap(state, Hypothesis("h1", "iddia", "Unsupported claim", 0.95))

    assert state.context_map["evidence_gate"] == "blocked"
    assert state.action == "ABSTAIN"
    assert state.output["action"] == "HALT"
    assert state.evidence_status == "missing"


def test_unverified_memory_does_not_enable_decision(tmp_path):
    pipeline = make_pipeline(tmp_path)
    consciousness = Consciousness(id="user")
    prior = Hypothesis("prior", "kaynak", "Prior source claim", 0.8, source="memory")
    pipeline.memory.save_hypothesis(prior)
    pipeline.memory.save_decision(
        decision_id="prior-decision",
        hyp_id="prior",
        score=EthicScore(0.8, 1.0, 0.1, 0.85, "ONAYLA"),
        consciousnesses=[consciousness],
        stage="YAP",
        task_mode="general",
    )

    state = pipeline.duy("Kaynağı nedir?", [consciousness])
    state = pipeline.bak(state)
    hypothesis = Hypothesis("h1", "kaynak", "Prior source claim", 0.95, source="memory")
    state = pipeline.gor(state, [hypothesis])
    state = pipeline.anla(state, hypothesis)
    state = pipeline.yap(state, hypothesis)

    assert state.evidence_status == "unverified"
    assert state.evidence_verified is False
    assert state.context_map["evidence_gate"] == "blocked"
    assert state.action == "ABSTAIN"


def test_non_evidence_request_preserves_existing_decision_path(tmp_path):
    pipeline = make_pipeline(tmp_path)
    state = pipeline.duy("Merhaba Anne", [Consciousness(id="user")])
    state = pipeline.bak(state)
    hypothesis = Hypothesis("h1", "greeting", "Hello", 0.95)
    state = pipeline.gor(state, [hypothesis])
    state = pipeline.anla(state, hypothesis)

    assert state.context_map["evidence_gate"] == "passed"
    assert state.ethic_score is not None
