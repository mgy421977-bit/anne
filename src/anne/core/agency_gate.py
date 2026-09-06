"""Explicit authorization boundary between cognition and external agency."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionDecision(str, Enum):
    DENY = "DENY"
    REVIEW = "REVIEW"
    ALLOW = "ALLOW"


@dataclass(frozen=True)
class ActionProposal:
    action: str
    target: str = ""
    reversible: bool = True
    risk: float = 0.0
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class Authorization:
    decision: ActionDecision
    reason: str
    policy_version: str = "v1"


@dataclass
class AgencyGate:
    """Fail-closed action gate.

    MITOS proposals are never sufficient authorization. Callers must provide
    an explicit policy decision before an external action is permitted.
    """

    review_risk_threshold: float = 0.8

    def __post_init__(self) -> None:
        if not 0.0 <= self.review_risk_threshold <= 1.0:
            raise ValueError("review_risk_threshold must be in [0, 1]")

    def authorize(
        self,
        proposal: ActionProposal,
        *,
        safety_allowed: bool,
        human_review_required: bool = False,
    ) -> Authorization:
        if not 0.0 <= proposal.risk <= 1.0:
            raise ValueError("risk must be in [0, 1]")
        if not safety_allowed:
            return Authorization(ActionDecision.DENY, "safety policy rejected action")
        if not proposal.provenance:
            return Authorization(ActionDecision.DENY, "action lacks provenance")
        if proposal.risk >= self.review_risk_threshold or not proposal.reversible:
            return Authorization(
                ActionDecision.REVIEW,
                "high-risk or irreversible action requires review",
            )
        if human_review_required:
            return Authorization(ActionDecision.REVIEW, "policy requires review")
        return Authorization(ActionDecision.ALLOW, "explicit policy gate passed")
