from __future__ import annotations

from decimal import Decimal

from anne.learning.percentage import PercentageLearner


class StubResearcher:
    def research(self, query: str):
        from anne.learning.evidence import EvidenceItem

        return [
            EvidenceItem(
                source="stub",
                claim="A percentage is a fraction out of 100.",
                kind="web",
                provenance="test",
                confidence=1.0,
            )
        ]


def test_percentage_learning_builds_verified_candidate() -> None:
    learner = PercentageLearner(StubResearcher())
    result = learner.learn("1250'nin yüzde 30'u kaç?")

    assert result.candidate.capability_id == "turkish_percentage_v1"
    assert result.candidate.test_accuracy == 1.0
    assert result.candidate.transfer_passed is True
    assert result.candidate.regression_passed is True
    assert result.candidate.sandbox_passed is True
    assert result.candidate.promotion_ready() is True
    assert result.answer == "375"


def test_percentage_learning_supports_transfer_case() -> None:
    learner = PercentageLearner(StubResearcher())
    result = learner.learn("800'ün yüzde 15'i kaç?")

    assert result.candidate.capability_id == "turkish_percentage_v1"
    assert result.candidate.test_accuracy == 1.0
    assert result.candidate.transfer_passed is True
    assert result.answer == "120"


def test_percentage_learning_does_not_claim_unknown_question() -> None:
    learner = PercentageLearner(StubResearcher())
    result = learner.learn("bana yüzde hesabını öğret")

    assert result.answer is None
    assert result.candidate.promoted is False


def test_percentage_expected_math() -> None:
    assert Decimal("800") * (Decimal("15") / Decimal("100")) == Decimal("120")
