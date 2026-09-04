"""Structured semantic-frame parsing and conservative ontology checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from anne.semantics.core import (
    Claim,
    Entity,
    Evidence,
    Provenance,
    Relation,
    SemanticFrame,
)

ALLOWED_ENTITY_KINDS = {"person", "organization", "place", "object", "event", "unknown"}
ALLOWED_PREDICATES = {
    "causes",
    "prevents",
    "enables",
    "owns",
    "located_in",
    "measured_at",
    "has_status",
    "related_to",
    "unknown",
}


@dataclass(frozen=True)
class OntologyIssue:
    path: str
    message: str


class Ontology:
    """Small explicit vocabulary; unknown concepts are reported, not discarded."""

    def validate(self, frame: SemanticFrame) -> list[OntologyIssue]:
        issues: list[OntologyIssue] = []
        for index, entity in enumerate(frame.entities):
            if entity.kind not in ALLOWED_ENTITY_KINDS:
                issues.append(
                    OntologyIssue(
                        f"entities[{index}].kind",
                        f"Unsupported kind: {entity.kind}",
                    )
                )
        for index, relation in enumerate(frame.relations):
            if relation.predicate not in ALLOWED_PREDICATES:
                issues.append(
                    OntologyIssue(
                        f"relations[{index}].predicate",
                        f"Unsupported predicate: {relation.predicate}",
                    )
                )
        return issues


def _number(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def parse_structured_frame(
    payload: str | dict[str, Any], source_ref: str = "model"
) -> SemanticFrame:
    """Parse model JSON while preserving invalid concepts for audit.

    The function is intentionally non-throwing for malformed optional fields;
    malformed top-level JSON does raise so callers can use a deterministic
    text-grounding fallback.
    """
    data = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(data, dict):
        raise ValueError("Semantic frame must be a JSON object")
    text = str(data.get("text", ""))
    provenance = Provenance.from_content("model", source_ref, text)
    evidence = [
        Evidence(
            id=str(item.get("id", f"e{index + 1}")),
            content=str(item.get("content", text)),
            provenance=provenance,
            confidence=_number(item.get("confidence"), 0.5),
        )
        for index, item in enumerate(data.get("evidence", []))
        if isinstance(item, dict)
    ]
    if not evidence and text:
        evidence = [Evidence("e1", text, provenance, 0.5)]
    entities = [
        Entity(
            id=str(item.get("id", f"entity_{index + 1}")),
            label=str(item.get("label", "")),
            kind=str(item.get("kind", "unknown")),
            confidence=_number(item.get("confidence")),
        )
        for index, item in enumerate(data.get("entities", []))
        if isinstance(item, dict) and str(item.get("label", ""))
    ]
    relations = [
        Relation(
            subject=str(item.get("subject", "")),
            predicate=str(item.get("predicate", "unknown")),
            object=str(item.get("object", "")),
            confidence=_number(item.get("confidence")),
        )
        for item in data.get("relations", [])
        if isinstance(item, dict)
    ]
    claims = [
        Claim(
            text=str(item.get("text", "")),
            source_id=str(item.get("source_id", "e1")),
            confidence=_number(item.get("confidence")),
            status=str(item.get("status", "unverified")),
        )
        for item in data.get("claims", [])
        if isinstance(item, dict) and str(item.get("text", ""))
    ]
    return SemanticFrame(
        text=text,
        entities=entities,
        relations=relations,
        claims=claims,
        evidence=evidence,
        confidence=_number(data.get("confidence"), 0.5),
    )


__all__ = [
    "ALLOWED_ENTITY_KINDS",
    "ALLOWED_PREDICATES",
    "Ontology",
    "OntologyIssue",
    "parse_structured_frame",
]
