"""Persistent memory for externally researched answers and learned terminology."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class KnowledgeMemory:
    """Persist knowledge separately from procedural capability memory."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @staticmethod
    def normalize(question: str) -> str:
        return " ".join(question.strip().lower().split())

    @staticmethod
    def normalize_term(term: str) -> str:
        term = term.strip().lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g")
        term = term.replace("ü", "u").replace("ö", "o").replace("ç", "c")
        return re.sub(r"[^a-z0-9]+", " ", term).strip()

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    def get(self, question: str) -> dict[str, Any] | None:
        record = self._load().get(self.normalize(question))
        return record if isinstance(record, dict) else None

    def get_term(self, term: str) -> dict[str, Any] | None:
        record = self._load().get(f"term::{self.normalize_term(term)}")
        return record if isinstance(record, dict) else None

    def list(self) -> list[dict[str, Any]]:
        return [record for record in self._load().values() if isinstance(record, dict)]

    def save(self, *, question: str, answer: str, evidence: list[dict[str, Any]], provider: str, confidence: float, status: str = "LEARNED_CANDIDATE") -> dict[str, Any]:
        key = self.normalize(question)
        records = self._load()
        previous = records.get(key, {})
        record = {
            "question": question, "normalized_question": key, "answer": answer,
            "status": status, "confidence": max(0.0, min(1.0, confidence)),
            "provider": provider, "evidence": evidence,
            "version": int(previous.get("version", 0)) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "ANNE research → verification → knowledge memory",
        }
        records[key] = record
        self._atomic_write(records)
        return record

    def save_term(self, *, term: str, meaning: str, source: str = "user") -> dict[str, Any]:
        """Store an explicit user-supplied terminology mapping as a candidate fact."""
        normalized_term = self.normalize_term(term)
        key = f"term::{normalized_term}"
        records = self._load()
        previous = records.get(key, {})
        record = {
            "type": "terminology", "term": term.strip(),
            "normalized_term": normalized_term, "meaning": meaning.strip(),
            "status": "LEARNED_CANDIDATE", "confidence": 0.95,
            "provider": source, "version": int(previous.get("version", 0)) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "explicit user knowledge → knowledge memory",
        }
        records[key] = record
        self._atomic_write(records)
        return record

    def _atomic_write(self, records: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="knowledge-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
