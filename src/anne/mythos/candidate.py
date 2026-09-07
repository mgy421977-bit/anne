"""Phase 1a MITOS candidate contracts.

MITOS proposes bounded candidates. ANNE remains responsible for selection,
validation, ethics, and action. Candidates are never authoritative facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from anne.mythos.engine import HypothesisCandidate


class TaskMode(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    EXPLORATORY = "exploratory"
    SAFETY = "safety"


@dataclass(frozen=True)
class SelectionResult:
    candidate: HypothesisCandidate | None
    accepted: bool
    score: float
    reason: str
    considered: int


__all__ = ["HypothesisCandidate", "SelectionResult", "TaskMode"]
