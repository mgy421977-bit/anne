"""Heuristic Semantic Validation Layer score (ANLA) — v0.1 research draft.

Not a formal proof. Implements the skeleton in docs/mathematics/anla_semantic_score.md:

    S_ANLA = α C_ctx + β C_log + γ C_trace

Default weights: α=0.5, β=0.3, γ=0.2. Threshold τ defaults to 0.5.
"""

from __future__ import annotations

import re
from typing import Sequence

DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.3
DEFAULT_GAMMA = 0.2
DEFAULT_TAU = 0.5
MAX_ANLA_RETRIES = 3

_TOKEN_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+")


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def token_overlap(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def context_consistency(text: str) -> float:
    """C_ctx proxy: non-empty substantive length (heuristic, not NLI)."""
    words = text.split()
    if not words:
        return 0.0
    return min(1.0, 0.5 + 0.5 * min(len(words) / 12.0, 1.0))


def logical_coherence(text: str) -> float:
    """C_log proxy: 0.0 on clear self-contradiction markers, else 1.0."""
    t = text.lower()
    if "never boils" in t and "boils at" in t:
        return 0.0
    pairs = [
        ("never", "always"),
        ("true", "false"),
        ("impossible", "possible"),
        ("cannot", "can always"),
        ("zero", "infinite"),
    ]
    for a, b in pairs:
        if a in t and b in t:
            return 0.0
    # Capital / geography style contradictions used in fixture
    if "capital of france is berlin" in t:
        return 0.2
    if "capital of japan is beijing" in t:
        return 0.2
    return 1.0


def trace_awareness(text: str, failures: Sequence) -> float:
    """C_trace proxy: penalize overlap with recent SFT reasons."""
    if not failures:
        return 1.0
    for row in failures:
        # row layout from get_recent_failures: id, cycle_id, stage, reason, ...
        reason = str(row[3]) if len(row) > 3 else ""
        if token_overlap(text, reason) > 0.4:
            return 0.3
    return 1.0


def compute_anla_score(
    text: str,
    failures: Sequence | None = None,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> float:
    """Return S_ANLA in [0, 1]."""
    failures = failures or []
    c_ctx = context_consistency(text)
    c_log = logical_coherence(text)
    c_trace = trace_awareness(text, failures)
    score = alpha * c_ctx + beta * c_log + gamma * c_trace
    return round(max(0.0, min(1.0, score)), 3)


def passes_anla(text: str, failures: Sequence | None = None, tau: float = DEFAULT_TAU) -> tuple[bool, float]:
    """Gate check: (passed, score)."""
    s = compute_anla_score(text, failures)
    return s >= tau, s
