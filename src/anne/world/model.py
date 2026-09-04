"""Belief state and conservative contradiction resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from anne.semantics.core import Evidence


@dataclass
class Belief:
    subject: str
    predicate: str
    object: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    status: str = "active"  # active | contradicted | disputed | expired

    @property
    def key(self) -> tuple[str, str]:
        return self.subject, self.predicate


class BeliefStore:
    """In-memory world model with explicit uncertainty and provenance."""

    def __init__(self) -> None:
        self.beliefs: list[Belief] = []

    def add(self, belief: Belief) -> Belief:
        conflicts = [
            item
            for item in self.beliefs
            if item.status == "active" and item.key == belief.key and item.object != belief.object
        ]
        if conflicts:
            for item in conflicts:
                item.status = "disputed"
            belief.status = "disputed"
        self.beliefs.append(belief)
        return belief

    def supported_by(self, evidence: Evidence, subject: str, predicate: str, object: str) -> Belief:
        """Add a belief only with a traceable evidence identifier."""
        return self.add(
            Belief(
                subject=subject,
                predicate=predicate,
                object=object,
                confidence=max(0.0, min(1.0, evidence.confidence)),
                evidence_ids=[evidence.id],
            )
        )

    def query(self, subject: str | None = None, predicate: str | None = None) -> list[Belief]:
        return [
            belief
            for belief in self.beliefs
            if (subject is None or belief.subject == subject)
            and (predicate is None or belief.predicate == predicate)
        ]


__all__ = ["Belief", "BeliefStore"]
