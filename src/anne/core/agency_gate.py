"""Fail-closed authorization boundary between cognition and external agency."""
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

class AgencyGate:
    """External action gate. MITOS can propose; policy must authorize."""
    def __init__(self, review_risk_threshold: float = 0.50) -> None:
        if not 0.0 <= review_risk_threshold <= 1.0:
            raise ValueError("review_risk_threshold must be in [0, 1]")
        self.review_risk_threshold = review_risk_threshold

    def authorize(self, proposal: ActionProposal, *, safety_allowed: bool, human_review_required: bool = False) -> Authorization:
        if not 0.0 <= proposal.risk <= 1.0:
            raise ValueError("risk must be in [0, 1]")
        if not safety_allowed:
            return Authorization(ActionDecision.DENY, "safety policy rejected action")
        if not proposal.provenance:
            return Authorization(ActionDecision.DENY, "missing provenance")
        if not proposal.reversible:
            return Authorization(ActionDecision.REVIEW, "irreversible action requires review")
        if proposal.risk >= self.review_risk_threshold:
            return Authorization(ActionDecision.REVIEW, "risk exceeds review threshold")
        if human_review_required:
            return Authorization(ActionDecision.REVIEW, "policy requires review")
        return Authorization(ActionDecision.ALLOW, "explicit policy gate passed")
