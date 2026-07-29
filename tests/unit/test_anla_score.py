"""Unit tests for heuristic ANLA score."""

from anne.core.anla_score import compute_anla_score, logical_coherence, passes_anla


def test_contradiction_low_score():
    text = "Water boils at 100C and also never boils under any pressure."
    assert logical_coherence(text) == 0.0
    s = compute_anla_score(text)
    assert s < 0.5


def test_coherent_passes():
    text = "Water boils at 100 degrees Celsius at standard atmospheric pressure."
    ok, s = passes_anla(text)
    assert ok is True
    assert s >= 0.5


def test_france_berlin_penalty():
    text = "The capital of France is Berlin according to this draft."
    assert logical_coherence(text) < 1.0
