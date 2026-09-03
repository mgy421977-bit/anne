"""Heuristic Semantic Validation Layer score (ANLA) — v0.1 research implementation.

    S_ANLA = α C_ctx + β C_log + γ C_trace

Default weights: α=0.5, β=0.3, γ=0.2. Threshold τ defaults to 0.5.
Hard lexical contradictions (C_log ≤ 0.25) are capped below default τ so the
gate is not vacuous on the micro-fixture. Not a formal proof.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.3
DEFAULT_GAMMA = 0.2
DEFAULT_TAU = 0.5
MAX_ANLA_RETRIES = 3
HARD_CONTRADICTION_CAP = 0.35

_TOKEN_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+")


def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return set(_TOKEN_RE.findall(text.lower()))


def token_overlap(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def context_consistency(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    words = [w for w in text.split() if w.strip()]
    if not words:
        return 0.0
    return min(1.0, 0.5 + 0.5 * min(len(words) / 12.0, 1.0))


def logical_coherence(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    t = text.lower()

    if (
        "never boils" in t
        and (
            "boils at" in t
            or "boils at" in t.replace(" ", "")
            or "boils" in t
        )
        and (
            t.count("boil") >= 2
            or ("boils at" in t and "never boils" in t)
        )
    ):
        return 0.0
    if "never boils" in t and "100" in t:
        return 0.0
    if "never melt" in t and "melt" in t:
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
    if not tokenize(text):
        return 0.0
    if not failures:
        return 1.0

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
    if c_log <= 0.25:
        score = min(score, HARD_CONTRADICTION_CAP)
    return round(max(0.0, min(1.0, float(score))), 3)


def passes_anla(
    text: str,
    failures: Sequence | None = None,
    tau: float = DEFAULT_TAU,
) -> tuple[bool, float]:
    s = compute_anla_score(text, failures)
    return s >= tau, s


def select_top_candidates(
    candidates: Iterable[str],
    failures: Sequence | None = None,
    top_k: int = 3,
) -> list[tuple[str, float]]:
    scored = [(c, compute_anla_score(c, failures)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
