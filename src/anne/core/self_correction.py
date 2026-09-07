"""Bounded SFT-driven self-correction planning for ANNE Phase 1b."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureClass(str, Enum):
    FACTUAL = "factual"
    SEMANTIC = "semantic"
    LOGICAL = "logical"
    ETHICAL = "ethical"
    PROCEDURAL = "procedural"
    UNCERTAINTY = "uncertainty"
    EVIDENCE_GAP = "evidence_gap"
    EXECUTION_RISK = "execution_risk"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LearningSignal:
    failure_class: FailureClass
    strategy: str
    lesson: str
    confidence: float
    safe_to_reuse: bool = False


@dataclass(frozen=True)
class ReframePlan:
    original: str
    reframed: str
    failure_class: FailureClass
    retry_index: int
    max_retries: int
    signal: LearningSignal

    @property
    def exhausted(self) -> bool:
        return self.retry_index >= self.max_retries


class SelfCorrectionPlanner:
    """Translate failure traces into bounded, non-authoritative correction plans."""

    MAX_RETRIES = 2

    _MAP = {
        "semantic_reject": FailureClass.SEMANTIC,
        "anla": FailureClass.SEMANTIC,
        "evidence_gap": FailureClass.EVIDENCE_GAP,
        "uncertainty": FailureClass.UNCERTAINTY,
        "ethical": FailureClass.ETHICAL,
        "fail_fast": FailureClass.EXECUTION_RISK,
        "execution": FailureClass.EXECUTION_RISK,
        "logical": FailureClass.LOGICAL,
        "factual": FailureClass.FACTUAL,
        "procedural": FailureClass.PROCEDURAL,
    }

    def classify(self, meta_tag: str, reason: str = "") -> FailureClass:
        text = f"{meta_tag} {reason}".lower()
        for key, value in self._MAP.items():
            if key in text:
                return value
        return FailureClass.UNKNOWN

    def plan(self, original: str, *, meta_tag: str = "", reason: str = "",
             retry_index: int = 0, max_retries: int = MAX_RETRIES) -> ReframePlan:
        failure_class = self.classify(meta_tag, reason)
        strategy = {
            FailureClass.FACTUAL: "request_or_recheck_evidence",
            FailureClass.SEMANTIC: "clarify_claim_and_revalidate",
            FailureClass.LOGICAL: "rebuild_reasoning_from_constraints",
            FailureClass.ETHICAL: "halt_and_require_safe_alternative",
            FailureClass.PROCEDURAL: "reorder_and_verify_steps",
            FailureClass.UNCERTAINTY: "reduce_claim_scope_and_expose_uncertainty",
            FailureClass.EVIDENCE_GAP: "seek_missing_evidence_or_abstain",
            FailureClass.EXECUTION_RISK: "do_not_execute; reassess_authority",
            FailureClass.UNKNOWN: "reassess_without_assuming_cause",
        }[failure_class]
        lesson = f"Previous attempt failed as {failure_class.value}; do not treat it as validated knowledge."
        signal = LearningSignal(failure_class, strategy, lesson, 0.5, False)
        prefix = {
            FailureClass.ETHICAL: "SAFE ALTERNATIVE: ",
            FailureClass.UNCERTAINTY: "UNCERTAINTY-AWARE: ",
            FailureClass.EVIDENCE_GAP: "EVIDENCE REQUIRED: ",
        }.get(failure_class, "RECHECK: ")
        reframed = prefix + original.strip()
        return ReframePlan(original, reframed, failure_class, retry_index, max_retries, signal)
