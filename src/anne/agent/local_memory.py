"""Local durable memory for offline ANNE Tinker sessions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class LocalMemory:
    """Small JSON memory store used when GitHub credentials are not supplied."""

    token = ""
    repository = "local/anne"
    branch = "local"

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path.home() / ".anne" / "memory")
        self.root.mkdir(parents=True, exist_ok=True)

    def _files(self) -> list[Path]:
        return sorted(self.root.glob("*.json"), reverse=True)

    def recent(self, limit: int = 8) -> list[dict[str, Any]]:
        memories: list[dict[str, Any]] = []
        for path in self._files()[:limit]:
            try:
                memories.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return memories

    def context(self, limit: int = 8) -> str:
        memories = self.recent(limit)
        if not memories:
            return "No persistent local memories have been recorded yet."
        return "\n\n---\n\n".join(
            f"[{m.get('timestamp', '')}] USER: {m.get('user_input', '')}\n"
            f"LEARNING: {m.get('learning', '')}\n"
            f"RESPONSE: {m.get('response', '')}"
            for m in memories
        )

    def save(
        self,
        user_input: str,
        response: str,
        learning: str,
        confidence: float = 0.5,
    ) -> str:
        timestamp = datetime.now(UTC)
        path = self.root / f"{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
        payload = {
            "schema_version": 1,
            "timestamp": timestamp.isoformat(),
            "agent": "ANNE",
            "user_input": user_input[:12000],
            "response": response[:20000],
            "learning": learning[:12000],
            "confidence": max(0.0, min(1.0, float(confidence))),
            "storage": "local",
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return str(path)
