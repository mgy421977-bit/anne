"""Local filesystem implementation of the ANNE artifact store."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .artifact import ArtifactMetadata


class LocalArtifactStore:
    """Durable local artifact store for offline/runtime use."""

    def __init__(self, root: str | Path = ".anne/storage") -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        normalized = key.strip("/")
        if not normalized or ".." in Path(normalized).parts:
            raise ValueError("artifact key must be a non-empty relative path")
        path = (self.root / normalized).resolve()
        if self.root != path and self.root not in path.parents:
            raise ValueError("artifact key escapes storage root")
        return path

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream", data_class: str = "PRIVATE_CLOUD") -> ArtifactMetadata:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return ArtifactMetadata(
            key=key.strip("/"), content_type=content_type, size_bytes=len(data),
            created_at=datetime.now(timezone.utc), sha256=hashlib.sha256(data).hexdigest(), data_class=data_class,
        )

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def list(self, prefix: str = "") -> list[str]:
        base = self._path(prefix) if prefix else self.root
        if base.is_file():
            return [base.relative_to(self.root).as_posix()]
        if not base.exists():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file())
