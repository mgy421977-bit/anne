"""Conservative evidence and hypothesis verification primitives."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VerificationResult:
    claim: str
    support: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    confidence: float = 0.0
    status: str = "unverified"


class VerificationEngine:
    """Scores claims from explicit support/conflict without pretending search is truth."""

    def verify(self, claim: str, evidence: list[str] | None = None, counter_evidence: list[str] | None = None) -> VerificationResult:
        support = [x.strip() for x in (evidence or []) if x and x.strip()]
        conflicts = [x.strip() for x in (counter_evidence or []) if x and x.strip()]
        if not support and not conflicts:
            return VerificationResult(claim=claim, confidence=0.0, status="unverified")
        raw = 0.5 + min(0.4, 0.08 * len(support)) - min(0.45, 0.12 * len(conflicts))
        confidence = max(0.0, min(0.95, raw))
        status = "supported" if confidence >= 0.70 and not conflicts else "conflicted" if conflicts else "partially_supported"
        return VerificationResult(claim=claim, support=support, conflicts=conflicts, confidence=round(confidence, 3), status=status)

    @staticmethod
    def needs_more_evidence(result: VerificationResult, threshold: float = 0.70) -> bool:
        return result.status in {"unverified", "conflicted"} or result.confidence < threshold


__all__ = ["VerificationEngine", "VerificationResult"]
