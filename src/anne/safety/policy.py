"""Conservative local safety policies for tools and persistent memory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{12,}\b"),
)


def redact_sensitive(text: str) -> str:
    """Redact common credentials before text enters durable memory."""
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda match: match.group(0).split("=", 1)[0].split(":", 1)[0]
            + "=[REDACTED]",
            redacted,
        )
    return redacted


@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    reason: str


class ToolPolicy:
    """Allowlist tool names and reject suspicious path arguments."""

    def __init__(self, allowed_tools: set[str] | None = None) -> None:
        self.allowed_tools = allowed_tools or {
            "github_read_file",
            "github_list",
            "github_search",
            "local_list",
            "local_read",
        }

    def authorize(self, name: str, arguments: dict[str, Any] | None = None) -> ToolDecision:
        if name not in self.allowed_tools:
            return ToolDecision(False, f"Tool is not allowlisted: {name}")
        for value in (arguments or {}).values():
            suspicious = ("../", "rm -rf", "delete")
            if isinstance(value, str) and any(
                token in value.lower() for token in suspicious
            ):
                return ToolDecision(False, "Suspicious tool argument blocked")
        return ToolDecision(True, "allowlisted read operation")


__all__ = ["ToolDecision", "ToolPolicy", "redact_sensitive"]
