"""Downstream cognitive requirements derived from the DUY intent frame.

Requirements are advisory routing signals. They never grant authority and do
not replace FailFast, semantic validation, ethics, or agency boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass

from anne.core.intent import IntentFrame


@dataclass(frozen=True)
class CognitiveRequirements:
    """Explicit downstream requirements for one cognitive cycle."""

    requires_evidence: bool
    requires_authority_check: bool
    ambiguity: float

    @classmethod
    def from_intent(cls, frame: IntentFrame) -> "CognitiveRequirements":
        return cls(
            requires_evidence=frame.requires_evidence,
            requires_authority_check=frame.requires_authority_check,
            ambiguity=max(0.0, min(1.0, frame.ambiguity)),
        )


__all__ = ["CognitiveRequirements"]
