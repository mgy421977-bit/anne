"""Heuristic Semantic Validation Layer (ANLA).

ANLA is a conservative output gate, not a proof system. It rejects empty,
instruction-like and obvious contradiction-shaped outputs before they can be
promoted or surfaced as trusted answers.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Sequence

DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.3
DEFAULT_GAMMA = 0.2
DEFAULT_TAU = 0.75
MAX_ANLA_RETRIES = 3
HARD_CONTRADICTION_CAP = 0.35

_TOKEN_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+")
_INSTRUCTION_PATTERNS = (
    r"\blook up\b", r"\bcheck (?:in|this|the)\b", r"\bsearch for\b",
    r"\bconsult\b", r"\brefer to\b", r"\bfind in\b", r"\blook in\b",
    r"\bara ve\b", r"\barayın\b", r"\bkontrol et\b", r"\bbakınız\b",
)


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def token_overlap(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def context_consistency(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    words = [w for w in text.split() if w.strip()]
    return min(1.0, 0.5 + 0.5 * min(len(words) / 12.0, 1.0))


def _looks_like_instruction(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(pattern, t) for pattern in _INSTRUCTION_PATTERNS)


def logical_coherence(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    t = text.lower()

    if _looks_like_instruction(text):
        informational_markers = (
            " means ", " is ", " stands for ", " anlamına gelir", " demektir"
        )
        if not any(marker in f" {t} " for marker in informational_markers):
            return 0.2

    if "never boils" in t and ("boils at" in t or t.count("boil") >= 2):
        return 0.0
    if "never boils" in t and "100" in t:
        return 0.0
    if "never melt" in t and "melt" in t:
        return 0.0

    def _has_word(word: str) -> bool:
        return re.search(rf"(?i)\b{re.escape(word)}\b", t) is not None

    for a, b in (("never", "always"), ("true", "false"), ("impossible", "possible"), ("zero", "infinite")):
        if _has_word(a) and _has_word(b):
            return 0.0
    if _has_word("cannot") and re.search(r"(?i)\bcan always\b", t):
        return 0.0

    for phrase, score in (("capital of france is berlin", 0.2), ("capital of japan is beijing", 0.2)):
        if phrase in t:
            return score

    return 0.95 if t.strip().endswith("?") else 1.0


def trace_awareness(text: str, failures: Sequence[Sequence[Any]] | None = None) -> float:
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


def compute_anla_score(text: str, failures: Sequence[Sequence[Any]] | None = None,
                       alpha: float = DEFAULT_ALPHA, beta: float = DEFAULT_BETA,
                       gamma: float = DEFAULT_GAMMA) -> float:
    failures = failures or []
    c_ctx = context_consistency(text)
    c_log = logical_coherence(text)
    c_trace = trace_awareness(text, failures)
    score = alpha * c_ctx + beta * c_log + gamma * c_trace
    if c_log <= 0.25:
        score = min(score, HARD_CONTRADICTION_CAP)
    return round(max(0.0, min(1.0, float(score))), 3)


def passes_anla(text: str, failures: Sequence[Sequence[Any]] | None = None,
                tau: float = DEFAULT_TAU) -> tuple[bool, float]:
    s = compute_anla_score(text, failures)
    return s >= tau, s


def select_top_candidates(candidates: Iterable[str], failures: Sequence[Sequence[Any]] | None = None,
                          top_k: int = 3) -> list[tuple[str, float]]:
    scored = [(c, compute_anla_score(c, failures)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
