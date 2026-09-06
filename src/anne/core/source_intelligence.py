"""Source-quality ranking for ANNE's evidence gate.

This is a deterministic ranking layer, not a truth oracle. It prioritizes
first-party and official sources for questions where authority matters and
keeps source provenance visible.
"""
from __future__ import annotations

from urllib.parse import urlparse


OFFICIAL_SUFFIXES = (".gov.tr", ".gov", ".mil.tr", ".edu.tr")
HIGH_AUTHORITY_HINTS = (
    "resmi gazete", "mevzuat", "bakanlık", "bakanligi", "epdk", "tkdk",
    "kosgeb", "tübitak", "tubitak", "teias", "yok", "e-devlet",
)
LOW_QUALITY_HINTS = (
    "wiktionary", "dictionary", "may refer to", "disambiguation",
    "forum", "pinterest", "quora",
)


def source_score(source: str, claim: str = "", *, authority_required: bool = False) -> float:
    value = f"{source} {claim}".lower()
    parsed = urlparse(source if "://" in source else "https://" + source)
    host = parsed.netloc.lower()
    score = 0.50
    if any(host.endswith(suffix) for suffix in OFFICIAL_SUFFIXES):
        score += 0.35
    if any(hint in value for hint in HIGH_AUTHORITY_HINTS):
        score += 0.15
    if any(hint in value for hint in LOW_QUALITY_HINTS):
        score -= 0.45
    if authority_required and not any(host.endswith(suffix) for suffix in OFFICIAL_SUFFIXES) and not any(hint in value for hint in HIGH_AUTHORITY_HINTS):
        score -= 0.10
    return max(0.0, min(1.0, round(score, 3)))


def rank_evidence(items, *, authority_required: bool = False):
    """Return evidence sorted by deterministic source quality, preserving items."""
    return sorted(items, key=lambda item: source_score(getattr(item, "source", ""), getattr(item, "claim", ""), authority_required=authority_required), reverse=True)


def requires_authority(question: str) -> bool:
    text = (question or "").lower()
    return any(term in text for term in (
        "devlet desteği", "teşvik", "destek", "hibe", "mevzuat", "yasal", "kanun",
        "başvuru şart", "2026", "2027", "resmi", "epdk", "tarife",
    ))
