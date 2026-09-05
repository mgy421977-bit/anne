"""Provider-neutral artifact storage contract for ANNE."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ArtifactMetadata:
    """Minimal provenance metadata kept with a stored artifact."""

    key: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    created_at: datetime = datetime.now(timezone.utc)
    sha256: str = ""
    data_class: str = "PRIVATE_CLOUD"


class ArtifactStore(Protocol):
    """Provider-neutral interface used by memory, MITOS and experiments."""

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream", data_class: str = "PRIVATE_CLOUD") -> ArtifactMetadata: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...

    def delete(self, key: str) -> None: ...

    def list(self, prefix: str = "") -> list[str]: ...
