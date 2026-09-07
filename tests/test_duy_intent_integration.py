from anne.core.cognitive_state import Consciousness
from anne.core.intent import IntentKind
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory


def test_duy_persists_intent_frame_in_state() -> None:
    pipeline = AnnePipeline(memory=FractalMemory(":memory:"))
    state = pipeline.duy(
        "Benim adıma bunu hemen gerçekleştir.",
        [Consciousness(id="user")],
    )

    assert state.intent == IntentKind.ACTION_REQUEST.value
    assert state.intent_confidence >= 0.8
    assert state.requires_authority_check is True
    assert state.context_map == {}


def test_bak_exposes_intent_frame_to_downstream_stages() -> None:
    pipeline = AnnePipeline(memory=FractalMemory(":memory:"))
    state = pipeline.duy(
        "Bu iddianın dayanağı nedir?",
        [Consciousness(id="user")],
    )
    state = pipeline.bak(state)

    assert state.intent == IntentKind.EVIDENCE_REQUEST.value
    assert state.context_map["intent"] == IntentKind.EVIDENCE_REQUEST.value
    assert state.context_map["requires_evidence"] is True
    assert state.context_map["requires_authority_check"] is False
