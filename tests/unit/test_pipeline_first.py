from __future__ import annotations

from anne import Consciousness, FractalMemory, run_pipeline
from anne.core.hypothesis_engine import HypothesisEngine


def test_hypothesis_engine_is_deterministic_without_external_api() -> None:
    engine = HypothesisEngine(max_hypotheses=5)
    first = engine.generate("Bu yeni yaklaşım neden riskli olabilir?")
    second = engine.generate("Bu yeni yaklaşım neden riskli olabilir?")

    assert [(h.id, h.claim, h.probability) for h in first] == [
        (h.id, h.claim, h.probability) for h in second
    ]
    assert first
    assert all(h.source.startswith("local") for h in first)


def test_pipeline_generates_hypotheses_when_none_is_supplied() -> None:
    memory = FractalMemory(":memory:")
    pipeline = __import__("anne").AnnePipeline(memory)
    _, state = pipeline.run_with_fail_fast(
        "Yeni bir fikri araştırmak istiyorum.",
        [Consciousness(id="C1")],
        hypothesis=None,
    )

    assert state is not None
    assert state.hypothesis_rankings
    assert state.context_map["hypothesis_count"] >= 1
    assert 0.0 <= state.uncertainty <= 1.0


def test_public_run_pipeline_needs_no_llm() -> None:
    state = run_pipeline("Nasıl daha güvenli bir yaklaşım geliştirebiliriz?")
    assert state.action in {"ONAYLA", "AYRI_ÇÖZÜM", "REDDET"}
    assert state.hypothesis_rankings
