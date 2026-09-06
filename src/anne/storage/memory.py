"""In-memory artifact store for tests and ephemeral sandbox runs."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .artifact import ArtifactMetadata


class MemoryStore:
    """Non-durable store; contents disappear when the process exits."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}
        self._metadata: dict[str, ArtifactMetadata] = {}

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream", data_class: str = "EPHEMERAL") -> ArtifactMetadata:
        key = key.strip("/")
        if not key:
            raise ValueError("artifact key must be non-empty")
        self._data[key] = bytes(data)
        metadata = ArtifactMetadata(
            key=key, content_type=content_type, size_bytes=len(data),
            created_at=datetime.now(timezone.utc), sha256=hashlib.sha256(data).hexdigest(), data_class=data_class,
        )
        self._metadata[key] = metadata
        return metadata

    def get(self, key: str) -> bytes:
        return self._data[key.strip("/")]

    def exists(self, key: str) -> bool:
        return key.strip("/") in self._data

    def delete(self, key: str) -> None:
        key = key.strip("/")
        self._data.pop(key, None)
        self._metadata.pop(key, None)

    def list(self, prefix: str = "") -> list[str]:
        prefix = prefix.strip("/")
        return sorted(key for key in self._data if key.startswith(prefix))
