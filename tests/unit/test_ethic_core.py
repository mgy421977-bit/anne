"""Basic unit tests for EthicCore."""

from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.ethic_core import EthicCore


def test_equality_axiom():
    core = EthicCore()
    hyp = Hypothesis(id="h1", topic="test", claim="test claim", probability=0.8)
    cons = [Consciousness(id="A"), Consciousness(id="B")]
    score = core.evaluate(hyp, cons)
    assert score.equality == 1.0
    assert score.verdict in {"ONAYLA", "AYRI_ÇÖZÜM", "REDDET"}


def test_low_probability_still_scored():
    core = EthicCore()
    hyp = Hypothesis(id="h2", topic="test", claim="low conf", probability=0.05)
    cons = [Consciousness(id="A")]
    score = core.evaluate(hyp, cons)
    assert 0.0 <= score.total <= 1.0
