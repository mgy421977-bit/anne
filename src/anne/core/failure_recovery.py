"""Bounded failure -> reframe -> retry coordination for ANNE Phase 1b.

The controller is deliberately non-authoritative: a failure can suggest a
reframe, but it cannot bypass FailFast, semantic validation, ethics, or the
existing agency boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureKind(StrEnum):
    """Coarse failure classes used to choose a bounded recovery strategy."""

    FAIL_FAST = "fail_fast"
    SEMANTIC = "semantic"
    LOGIC = "logic"
    EVIDENCE_GAP = "evidence_gap"
    BUDGET = "budget"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureSignal:
    """A structured, non-authoritative description of one failed attempt."""

    kind: FailureKind
    reason: str
    stage: str
    cycle_id: str
    depth: int


@dataclass(frozen=True)
class ReframePlan:
    """A bounded instruction for producing the next attempt."""

    strategy: str
    question: str
    parent_cycle_id: str
    depth: int
    attempt: int


@dataclass(frozen=True)
class RetryDecision:
    """Whether the controller permits one more bounded attempt."""

    allowed: bool
    reason: str
    next_attempt: int


class FailureRecoveryController:
    """Plan recovery without granting the recovery path extra authority."""

    _STRATEGIES = {
        FailureKind.FAIL_FAST: "narrow_scope",
        FailureKind.SEMANTIC: "clarify_claim",
        FailureKind.LOGIC: "restate_assumptions",
        FailureKind.EVIDENCE_GAP: "seek_missing_evidence",
        FailureKind.BUDGET: "reduce_scope",
        FailureKind.UNKNOWN: "restate_problem",
    }

    @classmethod
    def classify(cls, reason: str, stage: str) -> FailureKind:
        """Classify using explicit stage/reason markers, conservatively."""
        text = f"{stage} {reason}".lower()
        if "fail_fast" in text or stage.upper() == "FAIL_FAST":
            return FailureKind.FAIL_FAST
        if "semantic" in text:
            return FailureKind.SEMANTIC
        if "logic" in text or "invalid" in text:
            return FailureKind.LOGIC
        if any(marker in text for marker in ("gap", "missing", "unknown", "uncertain")):
            return FailureKind.EVIDENCE_GAP
        if "budget" in text or "iteration" in text or "depth" in text:
            return FailureKind.BUDGET
        return FailureKind.UNKNOWN

    @classmethod
    def plan(
        cls,
        failure: FailureSignal,
        question: str,
        *,
        attempt: int,
    ) -> ReframePlan:
        strategy = cls._STRATEGIES[failure.kind]
        prefix = {
            "narrow_scope": "Narrow the problem scope: ",
            "clarify_claim": "Clarify the claim: ",
            "restate_assumptions": "Restate the assumptions: ",
            "seek_missing_evidence": "Identify the missing evidence: ",
            "reduce_scope": "Reduce the problem scope: ",
            "restate_problem": "Restate the problem: ",
        }[strategy]
        return ReframePlan(
            strategy=strategy,
            question=prefix + question.strip(),
            parent_cycle_id=failure.cycle_id,
            depth=failure.depth + 1,
            attempt=attempt,
        )

    @staticmethod
    def authorize_retry(
        *,
        attempt: int,
        max_retries: int,
        seen_questions: set[str],
        question: str,
    ) -> RetryDecision:
        """Permit retry only when budget remains and the frame is new."""
        next_attempt = attempt + 1
        if next_attempt > max_retries:
            return RetryDecision(False, "retry_budget_exhausted", next_attempt)
        normalized = " ".join(question.lower().split())
        if normalized in seen_questions:
            return RetryDecision(False, "oscillation_detected", next_attempt)
        return RetryDecision(True, "retry_authorized", next_attempt)


__all__ = [
    "FailureKind",
    "FailureRecoveryController",
    "FailureSignal",
    "ReframePlan",
    "RetryDecision",
]
