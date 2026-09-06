"""Temporal freshness intelligence for evidence-gated knowledge resolution.

This layer does not invent dates. It extracts explicit dates from evidence text,
uses retrieval time only as a provenance floor, and applies stricter gates when
a question is explicitly time-sensitive.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from anne.learning.evidence import EvidenceItem


@dataclass(frozen=True)
class TemporalResult:
    time_sensitive: bool
    usable: tuple[EvidenceItem, ...]
    stale_count: int
    dated_count: int
    freshness_confidence: float
    reason: str


_TIME_MARKERS = (
    "latest", "current", "today", "now", "this year", "this month",
    "recent", "recently", "2025", "2026", "2027", "güncel", "günümüzde",
    "bugün", "şimdi", "son", "bu yıl", "bu ay", "mevcut", "yeni",
)
_DATE_PATTERNS = (
    re.compile(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b"),
    re.compile(r"\b(20\d{2})\b"),
)


def is_time_sensitive(question: str) -> bool:
    normalized = (question or "").lower()
    return any(marker in normalized for marker in _TIME_MARKERS)


def _dates(text: str) -> list[datetime]:
    found: list[datetime] = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text or ""):
            groups = match.groups()
            try:
                if len(groups) == 3:
                    if len(groups[0]) == 4:
                        year, month, day = map(int, groups)
                    else:
                        day, month, year = map(int, groups)
                    found.append(datetime(year, month, day, tzinfo=timezone.utc))
                elif len(groups) == 1:
                    found.append(datetime(int(groups[0]), 12, 31, tzinfo=timezone.utc))
            except ValueError:
                continue
    return found


def freshness_score(item: EvidenceItem, *, now: datetime | None = None) -> tuple[float, bool]:
    now = now or datetime.now(timezone.utc)
    dates = _dates(f"{item.claim} {item.provenance}")
    if not dates:
        return (0.55, False)
    latest = max(dates)
    age_days = max(0, (now - latest).days)
    if age_days <= 90:
        return (1.0, True)
    if age_days <= 365:
        return (0.85, True)
    if age_days <= 730:
        return (0.65, True)
    return (0.35, True)


def apply_freshness(
    question: str,
    items: list[EvidenceItem],
    *,
    now: datetime | None = None,
    min_score: float = 0.65,
) -> TemporalResult:
    sensitive = is_time_sensitive(question)
    if not items:
        return TemporalResult(sensitive, tuple(), 0, 0, 0.0, "no_evidence")
    scored: list[tuple[float, bool, EvidenceItem]] = [
        (*freshness_score(item, now=now), item) for item in items if not item.simulated
    ]
    dated_count = sum(1 for _, dated, _ in scored if dated)
    stale_count = sum(1 for score, dated, _ in scored if dated and score < min_score)
    if not sensitive:
        usable = tuple(item for _, _, item in scored)
        confidence = sum(score for score, _, _ in scored) / len(scored) if scored else 0.0
        return TemporalResult(False, usable, stale_count, dated_count, round(confidence, 3), "not_time_sensitive")

    usable = tuple(item for score, dated, item in scored if not dated or score >= min_score)
    confidence = sum(score for score, _, _ in scored) / len(scored) if scored else 0.0
    reason = "fresh_evidence" if usable else "stale_or_undated_evidence"
    return TemporalResult(True, usable, stale_count, dated_count, round(confidence, 3), reason)
