import pytest

from anne.core.intent import IntentClassifier, IntentKind


@pytest.fixture
def classifier() -> IntentClassifier:
    return IntentClassifier()


def test_greeting_is_framed_without_extra_authority(classifier: IntentClassifier) -> None:
    frame = classifier.classify("Merhaba ANNE")
    assert frame.intent is IntentKind.GREETING
    assert frame.confidence == 1.0
    assert not frame.requires_evidence
    assert not frame.requires_authority_check


def test_evidence_request_requires_evidence(classifier: IntentClassifier) -> None:
    frame = classifier.classify("Bu iddianın dayanağı nedir?")
    assert frame.intent is IntentKind.EVIDENCE_REQUEST
    assert frame.requires_evidence


def test_action_request_requires_authority_check(classifier: IntentClassifier) -> None:
    frame = classifier.classify("Benim adıma bunu hemen gerçekleştir.")
    assert frame.intent is IntentKind.ACTION_REQUEST
    assert frame.requires_authority_check


def test_risk_frame_is_conservative(classifier: IntentClassifier) -> None:
    frame = classifier.classify("Bu işlem güvenli mi, riskli bir durum var mı?")
    assert frame.intent is IntentKind.RISK
    assert frame.requires_evidence
    assert frame.requires_authority_check


def test_empty_input_is_ambiguous_and_non_authoritative(classifier: IntentClassifier) -> None:
    frame = classifier.classify("   ")
    assert frame.intent is IntentKind.GENERAL
    assert frame.ambiguity == 1.0
    assert not frame.requires_authority_check
