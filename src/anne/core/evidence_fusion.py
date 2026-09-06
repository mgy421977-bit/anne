"""Deterministic evidence fusion for corroboration and contradiction checks.

Fusion is deliberately conservative: multiple snippets from the same source do
not count as independent support. The layer does not prove truth; it decides
whether retrieved evidence is sufficiently corroborated to support an answer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from anne.learning.evidence import EvidenceItem


@dataclass(frozen=True)
class FusionResult:
    sufficient: bool
    confidence: float
    support_count: int
    independent_sources: int
    contradiction_count: int
    selected: tuple[EvidenceItem, ...]
    reason: str


def _tokens(text: str) -> set[str]:
    normalized = (text or "").lower()
    normalized = normalized.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
    normalized = normalized.replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return {t for t in re.findall(r"[a-z0-9]{2,}", normalized)}


def _domain(source: str) -> str:
    raw = source if "://" in source else "https://" + source
    host = urlparse(raw).netloc.lower()
    return host.removeprefix("www.") or source.lower().strip()


def _similarity(a: str, b: str) -> float:
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _contradicts(a: str, b: str) -> bool:
    left, right = (a or "").lower(), (b or "").lower()
    pairs = (
        (" not ", " is "), (" no ", " yes "), ("false", "true"),
        ("impossible", "possible"), ("cannot", "can"), ("yok", "var"),
        ("değil", "dir"), ("olamaz", "olabilir"),
        ("çalışmaz", "çalışır"), ("çalışmıyor", "çalışıyor"),
        ("desteklenmez", "desteklenir"), ("desteklenmiyor", "destekleniyor"),
    )
    normalized_pairs = []
    for x, y in pairs:
        nx = x.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
        ny = y.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
        normalized_pairs.append((nx, ny))
    normalized_left = f" {left.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')} "
    normalized_right = f" {right.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')} "
    return any((x in normalized_left and y in normalized_right) or (y in normalized_left and x in normalized_right) for x, y in normalized_pairs)


def fuse_evidence(items: list[EvidenceItem], *, authority_required: bool = False,
                  min_support: int = 2, min_confidence: float = 0.72) -> FusionResult:
    usable = [i for i in items if i.claim.strip() and not i.simulated]
    usable.sort(key=lambda i: i.confidence, reverse=True)
    selected: list[EvidenceItem] = []
    domains: set[str] = set()
    contradictions = 0

    for item in usable:
        if any(_similarity(item.claim, old.claim) >= 0.90 for old in selected):
            continue
        if any(_contradicts(item.claim, old.claim) for old in selected):
            contradictions += 1
            continue
        selected.append(item)
        domains.add(_domain(item.provenance or item.source))
        if len(selected) >= 8:
            break

    support = len(selected)
    independent = len(domains)
    weighted = sum(i.confidence for i in selected) / support if support else 0.0
    corroboration_bonus = min(0.12, max(0, independent - 1) * 0.06)
    confidence = min(1.0, weighted + corroboration_bonus)
    if authority_required:
        official = [i for i in selected if _domain(i.provenance or i.source).endswith((".gov.tr", ".gov", ".mil.tr", ".edu.tr"))]
        if official:
            confidence = min(1.0, confidence + 0.08)
        else:
            confidence = min(confidence, 0.68)

    sufficient = support >= min_support and independent >= min_support and confidence >= min_confidence and contradictions == 0
    if contradictions:
        reason = "contradictory_evidence"
    elif support < min_support or independent < min_support:
        reason = "insufficient_independent_support"
    elif confidence < min_confidence:
        reason = "confidence_below_gate"
    else:
        reason = "corroborated"
    return FusionResult(sufficient, round(confidence, 3), support, independent, contradictions, tuple(selected), reason)
