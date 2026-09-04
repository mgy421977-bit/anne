"""Centralized persistent-data paths for ANNE."""

from __future__ import annotations

import os
from pathlib import Path


def anne_data_root() -> Path:
    """Return ANNE's durable data root.

    ANNE_DATA_DIR overrides the location. On Windows, E:\\ANNE_DATA is the
    preferred default when the E: drive exists; otherwise the user's local
    profile is used as a safe fallback. Other platforms use ~/.anne/data.
    """
    override = os.environ.get("ANNE_DATA_DIR", "").strip()
    if override:
        root = Path(override).expanduser()
    elif os.name == "nt" and Path("E:/").exists():
        root = Path("E:/ANNE_DATA")
    else:
        root = Path.home() / ".anne" / "data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def anne_memory_root() -> Path:
    root = anne_data_root() / "memory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def anne_knowledge_root() -> Path:
    root = anne_data_root() / "knowledge"
    root.mkdir(parents=True, exist_ok=True)
    return root


__all__ = ["anne_data_root", "anne_memory_root", "anne_knowledge_root"]
