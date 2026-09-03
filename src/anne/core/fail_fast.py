"""Deterministic fail-fast pre-gate — runs before ANLA.

Purpose: cheap, inspectable rejection of obvious unsafe / out-of-scope inputs
so the semantic layer is reserved for the grey zone.

This is an explicit rule list, not a learned safety model and not a claim of
comprehensive content moderation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

# Transparent taboo / high-risk intent patterns (EN + TR). Expand carefully.
_DEFAULT_PATTERNS: Sequence[tuple[str, str]] = (
    (r"\b(hack|exploit|ransomware)\b", "security_abuse_intent"),
    (r"\b(bomb\s*making|build\s+a\s+bomb)\b", "violent_harm_intent"),
    (r"\b(self[- ]?harm|suicide\s+method)\b", "self_harm_intent"),
    (r"\b(çocuk\s+porn|child\s+porn)\b", "csam_intent"),
    (r"\b(sil\s+tüm\s+veri|wipe\s+all\s+data)\b", "destructive_ops_intent"),
    (r"(?<!\S)rm\s+-rf\s+/(?:\s|$)", "destructive_ops_intent"),
)

_MAX_CHARS_DEFAULT = 12_000


@dataclass(frozen=True)
class FailFastResult:
    passed: bool
    reason: str
    rule_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "rule_id": self.rule_id,
        }


class FailFastGate:
    """Lightweight deterministic pre-filter."""

    def __init__(
        self,
        patterns: Sequence[tuple[str, str]] | None = None,
        max_chars: int = _MAX_CHARS_DEFAULT,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self.max_chars = max_chars
        src = patterns if patterns is not None else _DEFAULT_PATTERNS
        self._compiled = [(re.compile(p, re.IGNORECASE), rid) for p, rid in src]

    def check(self, text: str) -> FailFastResult:
        if not self.enabled:
            return FailFastResult(True, "fail_fast_disabled")

        if text is None:
            return FailFastResult(False, "empty_input", "empty")

        stripped = text.strip()
        if not stripped:
            return FailFastResult(False, "empty_input", "empty")

        if len(stripped) > self.max_chars:
            return FailFastResult(
                False,
                f"input_exceeds_max_chars:{self.max_chars}",
                "max_chars",
            )

        for cre, rule_id in self._compiled:
            if cre.search(stripped):
                return FailFastResult(False, f"matched_rule:{rule_id}", rule_id)

        return FailFastResult(True, "ok")
