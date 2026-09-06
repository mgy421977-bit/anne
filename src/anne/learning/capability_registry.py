"""General capability registry for ANNE's verified procedural skills."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .capability_memory import CapabilityMemory


class CapabilityRegistry:
    """Route capability lookup and promotion through persistent memory."""

    def __init__(self, path: Path) -> None:
        self.memory = CapabilityMemory(path)

    def get(self, capability_id: str) -> dict[str, Any] | None:
        return self.memory.get(capability_id)

    def list(self) -> list[dict[str, Any]]:
        return self.memory.list()

    def has(self, capability_id: str) -> bool:
        record = self.get(capability_id)
        return bool(record and record.get("status") == "PROMOTED")

    def promote(self, candidate: Any) -> dict[str, Any]:
        return self.memory.promote(candidate)
