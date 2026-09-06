from datetime import datetime, timezone

from anne.core.temporal_intelligence import apply_freshness, freshness_score, is_time_sensitive
from anne.learning.evidence import EvidenceItem


def item(claim: str, source: str = "example.gov.tr") -> EvidenceItem:
    return EvidenceItem(source=source, claim=claim, kind="web", provenance=f"https://{source}", confidence=0.9)


def test_detects_time_sensitive_questions():
    assert is_time_sensitive("2026 devlet teşvikleri güncel mi?")
    assert is_time_sensitive("What is the latest status?")
    assert not is_time_sensitive("GES nedir?")


def test_recent_explicit_date_is_fresh():
    score, dated = freshness_score(
        item("Program updated 2026-08-15"),
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    assert dated is True
    assert score == 1.0


def test_old_explicit_date_is_stale_for_sensitive_question():
    result = apply_freshness(
        "2026 güncel teşvikler nelerdir?",
        [item("Program published 2023-01-10", "old.gov.tr")],
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    assert result.time_sensitive is True
    assert result.stale_count == 1
    assert result.usable == ()
    assert result.reason == "stale_or_undated_evidence"


def test_non_sensitive_question_does_not_discard_older_evidence():
    result = apply_freshness(
        "GES nedir?",
        [item("GES is a solar electricity system, 2020-01-01")],
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    assert result.time_sensitive is False
    assert len(result.usable) == 1


def test_undated_evidence_is_retained_but_marked_lower_freshness():
    result = apply_freshness(
        "2026 güncel teknoloji nedir?",
        [item("Technology overview without an explicit publication date")],
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    assert result.dated_count == 0
    assert len(result.usable) == 1
    assert result.freshness_confidence == 0.55
