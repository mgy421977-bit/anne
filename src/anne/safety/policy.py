"""Conservative local safety policies for tools and persistent memory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Bare tokens and labeled secrets. Replacements avoid forcing "prefix=[REDACTED]".
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Bearer <token>
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+=/]{8,}"), "Bearer [REDACTED]"),
    # OpenAI-style project keys
    (re.compile(r"\bsk-proj-[A-Za-z0-9_\-]{8,}\b"), "[REDACTED]"),
    # GitHub fine-grained PAT
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"), "[REDACTED]"),
    # Classic GitHub PAT / generic sk_ / ghp_
    (re.compile(r"\b(?:sk|ghp)_[A-Za-z0-9_\-]{12,}\b"), "[REDACTED]"),
    # key/token/password/secret = value (preserve key name, redact value only)
    (
        re.compile(
            r"(?i)((?:api[_ -]?key|token|password|secret)\s*[:=]\s*)([^\s,;]+)"
        ),
        r"\1[REDACTED]",
    ),
)


def redact_sensitive(text: str) -> str:
    """Redact common credentials before text enters durable memory."""
    redacted = text
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
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
