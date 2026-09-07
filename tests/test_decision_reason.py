from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory
from anne.core.decision_loop import DecisionLoop


def test_yap_exposes_reason_for_approved_decision(tmp_path):
    memory = FractalMemory(str(tmp_path / "anne.db"))
    pipeline = AnnePipeline(memory=memory)
    state = pipeline.duy("Merhaba ANNE", [Consciousness(id="user")])
    state = pipeline.bak(state)
    hypothesis = Hypothesis(
        id="h_reason",
        topic="greeting",
        claim="Test the bounded cognitive loop safely.",
        probability=0.9,
        source="MITOS",
    )
    state = pipeline.gor(state, [hypothesis])
    state = pipeline.anla(state, hypothesis)
    state = pipeline.hisset(state)
    state = pipeline.yap(state, hypothesis)

    assert state.output["verdict"] == "ONAYLA"
    assert state.output["reason"] == state.ethic_score.reasoning
    assert state.output["reason"]


def test_cognitive_result_propagates_reason(tmp_path):
    loop = DecisionLoop(memory_db_path=str(tmp_path / "anne.db"))
    result = loop.run_cognitive("Merhaba ANNE", seed=1)

    assert result.state is not None
    assert result.reason
    assert result.reason == result.state.output["reason"]
