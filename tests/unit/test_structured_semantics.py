from __future__ import annotations

import json

from anne.semantics.structured import Ontology, parse_structured_frame


def test_structured_frame_parses_and_preserves_evidence_links() -> None:
    frame = parse_structured_frame(
        json.dumps(
            {
                "text": "The plant is in Izmir",
                "confidence": 0.9,
                "entities": [{"id": "plant", "label": "plant", "kind": "object"}],
                "claims": [{"text": "The plant is in Izmir", "source_id": "e1"}],
                "evidence": [{"id": "e1", "content": "meter record", "confidence": 0.8}],
            }
        )
    )
    assert frame.evidence[0].id == frame.claims[0].source_id
    assert frame.confidence == 0.9
    assert Ontology().validate(frame) == []


def test_ontology_reports_unknown_kind_and_predicate() -> None:
    frame = parse_structured_frame(
        {
            "text": "x",
            "entities": [{"label": "x", "kind": "alien"}],
            "relations": [{"subject": "x", "predicate": "teleports", "object": "y"}],
        }
    )
    issues = Ontology().validate(frame)
    assert len(issues) == 2
    assert issues[0].path == "entities[0].kind"
    assert issues[1].path == "relations[0].predicate"
