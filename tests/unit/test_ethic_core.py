"""Unit tests for EthicCore."""

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


def test_high_confidence_tends_approve():
    core = EthicCore()
    hyp = Hypothesis(id="h3", topic="safe", claim="beneficial", probability=0.95)
    cons = [Consciousness(id="A"), Consciousness(id="B")]
    score = core.evaluate(hyp, cons, input_type="explore")
    assert score.total >= 0.7
    assert score.verdict == "ONAYLA"


def test_risk_input_raises_harm():
    core = EthicCore()
    hyp = Hypothesis(id="h4", topic="danger", claim="risky act", probability=0.5)
    cons = [Consciousness(id="A")]
    score_explore = core.evaluate(hyp, cons, input_type="explore")
    score_risk = core.evaluate(hyp, cons, input_type="risk")
    assert score_risk.harm >= score_explore.harm


def test_unequal_weights_reduce_equality():
    core = EthicCore()
    hyp = Hypothesis(id="h5", topic="bias", claim="x", probability=0.8)
    cons = [
        Consciousness(id="A", weight=1.0),
        Consciousness(id="B", weight=5.0),
    ]
    score = core.evaluate(hyp, cons)
    assert score.equality < 1.0


def test_zero_consciousness_edge():
    core = EthicCore()
    hyp = Hypothesis(id="h6", topic="empty", claim="x", probability=0.5)
    score = core.evaluate(hyp, [])
    assert score.goodness == 0.0
    assert score.verdict in {"ONAYLA", "AYRI_ÇÖZÜM", "REDDET"}
