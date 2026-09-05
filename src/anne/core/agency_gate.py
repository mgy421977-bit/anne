"""Explicit authorization boundary between cognition and external agency."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    """Fail-closed action gate.

    MITOS proposals are never sufficient authorization. Callers must provide
    an explicit policy decision before an external action is permitted.
    """

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
        if human_review_required:
            return Authorization(ActionDecision.REVIEW, "policy requires review")
        return Authorization(ActionDecision.ALLOW, "explicit policy gate passed")
