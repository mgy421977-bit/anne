"""Small persistent terminology memory for ANNE learning candidates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeMemory:
    """Persist user-provided terminology without treating it as ground truth."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            str(key): value
            for key, value in payload.items()
            if isinstance(value, dict)
        }

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def save_term(self, *, term: str, meaning: str, source: str) -> None:
        """Store a term as a candidate learned from the supplied source."""
        normalized = term.strip()
        if not normalized:
            raise ValueError("term must not be empty")
        if not meaning.strip():
            raise ValueError("meaning must not be empty")
        if not source.strip():
            raise ValueError("source must not be empty")
        records = self._load()
        records[normalized] = {
            "term": normalized,
            "meaning": meaning.strip(),
            "source": source.strip(),
            "status": "LEARNED_CANDIDATE",
        }
        self._save(records)

    def get_term(self, term: str) -> dict[str, Any] | None:
        """Return a stored candidate, or ``None`` when the term is unknown."""
        normalized = term.strip()
        if not normalized:
            return None
        return self._load().get(normalized)


__all__ = ["KnowledgeMemory"]
