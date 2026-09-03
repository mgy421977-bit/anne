"""Sandboxed, read-only local Windows workspace tool for ANNE."""

from __future__ import annotations

from pathlib import Path


class LocalFilesTool:
    """Read-only access constrained to a configured workspace directory."""

    def __init__(self, workspace: str | Path) -> None:
        self.root = Path(workspace).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, path: str) -> Path:
        candidate = (self.root / path.strip().lstrip("/\\")).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Path escapes ANNE workspace") from exc
        return candidate

    def list(self, path: str = "") -> list[str]:
        directory = self._safe(path)
        if not directory.exists():
            raise FileNotFoundError(str(directory))
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {path}")
        results: list[str] = []
        for item in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:200]:
            results.append(f"{'dir' if item.is_dir() else 'file'}: {item.relative_to(self.root)}")
        return results

    def read(self, path: str) -> str:
        file_path = self._safe(path)
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")
        size = file_path.stat().st_size
        if size > 100_000:
            raise ValueError("File is larger than the 100 KB read limit")
        return file_path.read_text(encoding="utf-8", errors="replace")
