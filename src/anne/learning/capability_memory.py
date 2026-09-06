"""Persistent, bounded procedural capability memory.

Promoted capabilities are stored as auditable JSON records outside the source tree.
This module stores methods and evidence summaries; it never rewrites Python code.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence import LearningCandidate


class CapabilityMemory:
    """Persist verified procedural capabilities with atomic writes."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    def get(self, capability_id: str) -> dict[str, Any] | None:
        record = self._load().get(capability_id)
        return record if isinstance(record, dict) else None

    def list(self) -> list[dict[str, Any]]:
        return list(self._load().values())

    def promote(self, candidate: LearningCandidate) -> dict[str, Any]:
        if not candidate.promotion_ready():
            raise ValueError("Capability promotion gate is not satisfied")

        record = {
            "capability_id": candidate.capability_id,
            "version": 1,
            "status": "PROMOTED",
            "hypothesis": candidate.hypothesis,
            "method": candidate.method,
            "confidence": candidate.confidence,
            "tests_passed": candidate.tests_passed,
            "tests_total": candidate.tests_total,
            "test_accuracy": candidate.test_accuracy,
            "transfer_passed": candidate.transfer_passed,
            "regression_passed": candidate.regression_passed,
            "sandbox_passed": candidate.sandbox_passed,
            "evidence": [
                {
                    "source": item.source,
                    "claim": item.claim,
                    "kind": item.kind,
                    "provenance": item.provenance,
                    "confidence": item.confidence,
                    "simulated": item.simulated,
                }
                for item in candidate.evidence
            ],
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "source": "ANNE evidence-gated learning",
        }
        records = self._load()
        records[candidate.capability_id] = record
        self._atomic_write(records)
        candidate.promoted = True
        return record

    def _atomic_write(self, records: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="capabilities-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
