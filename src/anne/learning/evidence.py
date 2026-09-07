"""Structured evidence records used by ANNE's learning/research layer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceItem:
    """A provenance-carrying, non-authoritative piece of evidence."""

    source: str
    claim: str
    kind: str
    provenance: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.claim.strip():
            raise ValueError("claim must not be empty")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        if not self.provenance.strip():
            raise ValueError("provenance must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


__all__ = ["EvidenceItem"]
