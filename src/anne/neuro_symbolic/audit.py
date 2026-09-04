"""Neuro-symbolic contracts for auditing hypotheses and plans."""

from __future__ import annotations

from dataclasses import dataclass, field

from anne.semantics.core import Evidence


@dataclass
class PlanStep:
    id: str
    action: str
    preconditions: list[str] = field(default_factory=list)
    expected_effects: list[str] = field(default_factory=list)
    risk_level: float = 0.0
    required_tools: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | verified | failed
    verification: str = ""

    def verify(self, observed_effect: str) -> bool:
        self.verification = observed_effect
        self.status = "verified" if observed_effect in self.expected_effects else "failed"
        return self.status == "verified"


@dataclass
class ReasoningAudit:
    conclusion: str
    evidence_ids: list[str]
    assumptions: list[str]
    unresolved_questions: list[str]
    alternative_hypotheses: list[str]
    confidence: float
    calibration_status: str = "uncalibrated"
    recommended_next_check: str | None = None


class NeuroSymbolicValidator:
    """Checks structural evidence requirements around neural suggestions."""

    def audit(
        self,
        conclusion: str,
        evidence: list[Evidence],
        assumptions: list[str] | None = None,
        alternatives: list[str] | None = None,
    ) -> ReasoningAudit:
        assumptions = assumptions or []
        alternatives = alternatives or []
        ids = [item.id for item in evidence]
        unresolved = [] if evidence else ["No traceable evidence is attached to the conclusion"]
        confidence = min(1.0, sum(item.confidence for item in evidence) / max(len(evidence), 1))
        if assumptions:
            confidence *= 0.8
        status = "supported" if evidence and not assumptions else "needs_review"
        return ReasoningAudit(
            conclusion=conclusion,
            evidence_ids=ids,
            assumptions=assumptions,
            unresolved_questions=unresolved,
            alternative_hypotheses=alternatives,
            confidence=round(confidence, 3),
            calibration_status=status,
            recommended_next_check=unresolved[0] if unresolved else None,
        )


__all__ = ["NeuroSymbolicValidator", "PlanStep", "ReasoningAudit"]
