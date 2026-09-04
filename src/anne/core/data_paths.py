"""Central persistent data locations for ANNE.

Program files stay with the application; durable ANNE state lives on a dedicated
user-selected data drive. The default Windows location is E:\\ANNE_DATA when E:
exists. ANNE_DATA_DIR can override it.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_WINDOWS_ROOT = Path("E:/ANNE_DATA")
DEFAULT_ROOT = Path.home() / ".anne"


def anne_data_root() -> Path:
    configured = os.environ.get("ANNE_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    if DEFAULT_WINDOWS_ROOT.drive and DEFAULT_WINDOWS_ROOT.parent.exists():
        return DEFAULT_WINDOWS_ROOT
    return DEFAULT_ROOT


def anne_memory_root() -> Path:
    return anne_data_root() / "memory"


def anne_knowledge_root() -> Path:
    return anne_data_root() / "knowledge"


def anne_patterns_root() -> Path:
    return anne_data_root() / "patterns"


def anne_lessons_root() -> Path:
    return anne_data_root() / "lessons"


def anne_conversations_root() -> Path:
    return anne_data_root() / "conversations"


def anne_logs_root() -> Path:
    return anne_data_root() / "logs"


def ensure_data_dirs() -> Path:
    root = anne_data_root()
    for path in (
        root,
        anne_memory_root(),
        anne_knowledge_root(),
        anne_patterns_root(),
        anne_lessons_root(),
        anne_conversations_root(),
        anne_logs_root(),
    ):
        path.mkdir(parents=True, exist_ok=True)
    return root


__all__ = [
    "anne_data_root",
    "anne_memory_root",
    "anne_knowledge_root",
    "anne_patterns_root",
    "anne_lessons_root",
    "anne_conversations_root",
    "anne_logs_root",
    "ensure_data_dirs",
]
