"""Bounded ambiguity handling for ANNE.

Ambiguity is distinct from uncertainty and confidence.  This module only
controls whether the current request is sufficiently specified to continue;
it never grants authority and never treats confidence as truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AmbiguityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class AmbiguityDecision:
    level: AmbiguityLevel
    action: str
    reason: str


class AmbiguityBoundary:
    """Translate a bounded ambiguity score into a conservative next step."""

    MEDIUM_THRESHOLD = 0.50
    HIGH_THRESHOLD = 0.75

    @classmethod
    def classify(cls, ambiguity: float) -> AmbiguityLevel:
        value = max(0.0, min(1.0, ambiguity))
        if value >= cls.HIGH_THRESHOLD:
            return AmbiguityLevel.HIGH
        if value >= cls.MEDIUM_THRESHOLD:
            return AmbiguityLevel.MEDIUM
        return AmbiguityLevel.LOW

    @classmethod
    def decide(cls, ambiguity: float) -> AmbiguityDecision:
        level = cls.classify(ambiguity)
        if level is AmbiguityLevel.HIGH:
            return AmbiguityDecision(
                level, "ABSTAIN", "Request is too ambiguous to continue safely."
            )
        if level is AmbiguityLevel.MEDIUM:
            return AmbiguityDecision(
                level, "CLARIFY", "Request needs clarification before a bounded decision."
            )
        return AmbiguityDecision(level, "CONTINUE", "Request is sufficiently specified.")


__all__ = ["AmbiguityBoundary", "AmbiguityDecision", "AmbiguityLevel"]
