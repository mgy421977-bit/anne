"""Evidence-gated repository self-governance for ANNE."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BranchAction(str, Enum):
    KEEP = "KEEP"
    REVIEW = "REVIEW"
    ARCHIVE = "ARCHIVE"
    DELETE = "DELETE"


class BranchRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class BranchEvidence:
    name: str
    is_default: bool = False
    is_protected: bool = False
    has_open_pr: bool = False
    has_unique_commits: bool = False
    has_unique_files: bool = False
    is_active_base: bool = False
    referenced_by_active_work: bool = False
    preserved_elsewhere: bool = False
    duplicate_of: str = ""
    last_activity_days: int | None = None


@dataclass(frozen=True)
class BranchFinding:
    action: BranchAction
    risk: BranchRisk
    confidence: float
    reasons: tuple[str, ...]

    @property
    def destructive(self) -> bool:
        return self.action in {BranchAction.ARCHIVE, BranchAction.DELETE}


@dataclass(frozen=True)
class BranchPolicy:
    min_delete_confidence: float = 0.995
    require_preserved_copy: bool = True


class RepositoryGovernor:
    """Fail-closed policy engine; it evaluates but never performs Git operations."""

    def __init__(self, policy: BranchPolicy | None = None) -> None:
        self.policy = policy or BranchPolicy()
        if not 0.0 <= self.policy.min_delete_confidence <= 1.0:
            raise ValueError("min_delete_confidence must be in [0, 1]")

    def evaluate(self, evidence: BranchEvidence) -> BranchFinding:
        if not evidence.name.strip():
            raise ValueError("branch name is required")

        protected_reasons: list[str] = []
        if evidence.is_default:
            protected_reasons.append("default branch is immutable")
        if evidence.is_protected:
            protected_reasons.append("branch is protected")
        if evidence.has_open_pr:
            protected_reasons.append("branch has an open pull request")
        if evidence.has_unique_commits or evidence.has_unique_files:
            protected_reasons.append("branch contains unique knowledge")
        if evidence.is_active_base:
            protected_reasons.append("branch is an active base")
        if evidence.referenced_by_active_work:
            protected_reasons.append("active work references this branch")

        if protected_reasons:
            return BranchFinding(BranchAction.KEEP, BranchRisk.CRITICAL, 1.0, tuple(protected_reasons))

        if not evidence.duplicate_of:
            return BranchFinding(BranchAction.REVIEW, BranchRisk.MEDIUM, 0.0, ("no duplicate relationship established",))

        if self.policy.require_preserved_copy and not evidence.preserved_elsewhere:
            return BranchFinding(BranchAction.ARCHIVE, BranchRisk.HIGH, 0.95, ("duplicate candidate lacks a preserved copy",))

        confidence = 1.0
        if confidence < self.policy.min_delete_confidence:
            return BranchFinding(BranchAction.REVIEW, BranchRisk.MEDIUM, confidence, ("delete confidence below policy threshold",))

        reasons = [f"duplicate of {evidence.duplicate_of}", "preserved elsewhere"]
        if evidence.last_activity_days is not None:
            reasons.append(f"inactive for {evidence.last_activity_days} days")
        return BranchFinding(BranchAction.DELETE, BranchRisk.LOW, confidence, tuple(reasons))
