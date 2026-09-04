"""Inspectable semantic frames, evidence, and provenance primitives."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Entity:
    id: str
    label: str
    kind: str = "unknown"
    confidence: float = 0.5


@dataclass(frozen=True)
class Relation:
    subject: str
    predicate: str
    object: str
    confidence: float = 0.5


@dataclass(frozen=True)
class Claim:
    text: str
    source_id: str
    confidence: float = 0.5
    status: str = "unverified"  # unverified | supported | disputed | rejected


@dataclass
class Provenance:
    source_type: str  # user | file | web | tool | model
    source_ref: str
    observed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    content_hash: str = ""
    verified: bool = False

    @classmethod
    def from_content(cls, source_type: str, source_ref: str, content: str) -> Provenance:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(source_type, source_ref, content_hash=digest)


@dataclass
class Evidence:
    id: str
    content: str
    provenance: Provenance
    confidence: float = 0.5


@dataclass
class SemanticFrame:
    text: str
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.5


def frame_from_text(
    text: str, source_type: str = "user", source_ref: str = "input"
) -> SemanticFrame:
    """Create a conservative frame without pretending extraction is understanding.

    The deterministic extractor preserves the original text as evidence and
    treats capitalized tokens as candidate entities. A future neural parser can
    replace this function while keeping the same contract.
    """
    provenance = Provenance.from_content(source_type, source_ref, text)
    evidence = Evidence(id="e1", content=text, provenance=provenance, confidence=0.8)
    words = [word.strip(".,!?():;\"'") for word in text.split()]
    entities = [
        Entity(id=f"entity_{index}", label=word, kind="candidate", confidence=0.4)
        for index, word in enumerate(words[:20])
        if word and word[0].isupper()
    ]
    claim = Claim(text=text, source_id=evidence.id, confidence=0.8)
    return SemanticFrame(
        text=text, entities=entities, claims=[claim], evidence=[evidence], confidence=0.8
    )


__all__ = [
    "Claim",
    "Entity",
    "Evidence",
    "Provenance",
    "Relation",
    "SemanticFrame",
    "frame_from_text",
]
