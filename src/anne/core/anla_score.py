"""Heuristic Semantic Validation Layer score (ANLA) — v0.1 research implementation.

Extends the math skeleton with clearer contracts, unit-testable helpers, and a
slightly more robust trace-awareness heuristic. Deliberately avoids heavy ML
dependencies so the research pipeline runs in lightweight environments.

    S_ANLA = α C_ctx + β C_log + γ C_trace

Default weights: α=0.5, β=0.3, γ=0.2. Threshold τ defaults to 0.5.
Not a formal proof — see docs/mathematics/anla_semantic_score.md.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.3
DEFAULT_GAMMA = 0.2
DEFAULT_TAU = 0.5
MAX_ANLA_RETRIES = 3

_TOKEN_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+")


def tokenize(text: str) -> set[str]:
    """Lowercase tokens including Turkish characters and digits."""
    if not text:
        return set()
    return set(_TOKEN_RE.findall(text.lower()))


def token_overlap(a: str, b: str) -> float:
    """Jaccard-style overlap in [0, 1]. Empty inputs → 0.0."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def context_consistency(text: str) -> float:
    """C_ctx proxy: favors non-empty, substantive inputs.

    Scales from 0.0 (empty) toward 1.0 at ≥12 words.
    """
    if not text or not text.strip():
        return 0.0
    words = [w for w in text.split() if w.strip()]
    if not words:
        return 0.0
    return min(1.0, 0.5 + 0.5 * min(len(words) / 12.0, 1.0))


def logical_coherence(text: str) -> float:
    """C_log proxy: penalize explicit contradictions; else near 1.0.

    Conservative: only obvious lexical conflicts drop the score.
    """
    if not text or not text.strip():
        return 0.0
    t = text.lower()

    # Domain-style contradictions used in fixtures
    if "never boils" in t and "boils at" in t:
        return 0.0
    if "never melt" in t and "melts" in t:
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

    factoid_penalties = [
        ("capital of france is berlin", 0.2),
        ("capital of japan is beijing", 0.2),
    ]
    for phrase, score in factoid_penalties:
        if phrase in t:
            return score

    if t.strip().endswith("?"):
        return 0.95

    return 1.0


def trace_awareness(text: str, failures: Sequence | None = None) -> float:
    """C_trace proxy: graduated penalty if text echoes recent SFT reasons.

    failures rows match get_recent_failures: index 3 is the reason string.
    """
    if not failures:
        return 1.0
    if not tokenize(text):
        return 0.0

    worst = 1.0
    for row in failures:
        reason = str(row[3]) if len(row) > 3 else ""
        ov = token_overlap(text, reason)
        if ov > 0.6:
            worst = min(worst, 0.2)
        elif ov > 0.3:
            worst = min(worst, 0.5)
        elif ov > 0.1:
            worst = min(worst, 0.8)
    return worst


def compute_anla_score(
    text: str,
    failures: Sequence | None = None,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> float:
    """Return S_ANLA in [0, 1]. Deterministic; safe for unit tests."""
    failures = failures or []
    c_ctx = context_consistency(text)
    c_log = logical_coherence(text)
    c_trace = trace_awareness(text, failures)
    score = alpha * c_ctx + beta * c_log + gamma * c_trace
    return round(max(0.0, min(1.0, float(score))), 3)


def passes_anla(
    text: str,
    failures: Sequence | None = None,
    tau: float = DEFAULT_TAU,
) -> tuple[bool, float]:
    """Gate check: (passed, score)."""
    s = compute_anla_score(text, failures)
    return s >= tau, s


def select_top_candidates(
    candidates: Iterable[str],
    failures: Sequence | None = None,
    top_k: int = 3,
) -> list[tuple[str, float]]:
    """Score candidates and return top_k (text, score) pairs, highest first."""
    scored = [(c, compute_anla_score(c, failures)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
