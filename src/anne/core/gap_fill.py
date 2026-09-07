"""Bounded semantic gap-fill decision.

The component does not manufacture missing facts. It compares available low/high
context paths and explicitly abstains when the gap cannot be closed safely.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class GapAssessment:
    gap: float
    low_score: float
    high_score: float
    filled: bool
    abstained: bool
    reason: str
    evidence: tuple[Any, ...] = ()


class GapFiller:
    """Compare two bounded evidence paths without treating confidence as truth."""

    def __init__(self, *, fill_threshold: float = 0.70, margin: float = 0.10) -> None:
        self.fill_threshold = fill_threshold
        self.margin = margin

    def assess(
        self,
        low_evidence: Sequence[Any],
        high_evidence: Sequence[Any],
        *,
        low_score: float = 0.0,
        high_score: float = 0.0,
    ) -> GapAssessment:
        low = max(0.0, min(1.0, low_score))
        high = max(0.0, min(1.0, high_score))
        gap = round(abs(high - low), 4)
        evidence = tuple(high_evidence if high >= low else low_evidence)
        if not evidence:
            return GapAssessment(gap, low, high, False, True, "no_evidence")
        if max(low, high) < self.fill_threshold:
            return GapAssessment(gap, low, high, False, True, "insufficient_evidence", evidence)
        if gap > self.margin:
            return GapAssessment(gap, low, high, False, True, "path_disagreement", evidence)
        return GapAssessment(gap, low, high, True, False, "gap_bounded", evidence)


__all__ = ["GapAssessment", "GapFiller"]
