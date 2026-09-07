"""Deterministic intent and context framing for ANNE's DUY stage.

This is an inspectable routing layer, not a language model and not a claim of
understanding. It creates a bounded task frame that downstream stages can use.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntentKind(StrEnum):
    GREETING = "greeting"
    QUESTION = "question"
    EVIDENCE_REQUEST = "evidence_request"
    UNCERTAINTY = "uncertainty"
    COMPARISON = "comparison"
    PLANNING = "planning"
    ACTION_REQUEST = "action_request"
    SELF_CORRECTION = "self_correction"
    RISK = "risk"
    GENERAL = "general"


@dataclass(frozen=True)
class IntentFrame:
    intent: IntentKind
    confidence: float
    requires_evidence: bool
    requires_authority_check: bool
    ambiguity: float


class IntentClassifier:
    """Small deterministic classifier used only to frame the next stages."""

    def classify(self, text: str) -> IntentFrame:
        normalized = " ".join(text.casefold().split())
        if not normalized:
            return IntentFrame(IntentKind.GENERAL, 1.0, False, False, 1.0)

        if normalized in {"merhaba", "selam", "merhaba anne", "selam anne"}:
            return IntentFrame(IntentKind.GREETING, 1.0, False, False, 0.0)

        if any(marker in normalized for marker in ("benim adıma", "hemen gerçekleştir", "yapabilir misin")):
            return IntentFrame(IntentKind.ACTION_REQUEST, 0.9, False, True, 0.1)

        if any(marker in normalized for marker in (
            "dayanağı", "dayanak", "kanıt", "kaynak", "kaynağı", "kaynağın",
            "evidence", "source",
        )):
            return IntentFrame(IntentKind.EVIDENCE_REQUEST, 0.9, True, False, 0.2)

        if any(marker in normalized for marker in ("kesin doğru", "emin misin", "ne kadar eminsin", "belirsiz")):
            return IntentFrame(IntentKind.UNCERTAINTY, 0.9, True, False, 0.2)

        if any(marker in normalized for marker in ("yanlış", "hata", "kendini düzelt", "önceki karar")):
            return IntentFrame(IntentKind.SELF_CORRECTION, 0.85, True, False, 0.25)

        if any(marker in normalized for marker in ("risk", "tehlike", "zarar", "güvenli", "harm", "danger")):
            return IntentFrame(IntentKind.RISK, 0.9, True, True, 0.2)

        if any(marker in normalized for marker in ("karşılaştır", "hangisi", "mi daha", "vs", "seçenek")):
            return IntentFrame(IntentKind.COMPARISON, 0.8, True, False, 0.3)

        if any(marker in normalized for marker in ("önce", "adımlar", "plan", "nasıl iler", "hangi bilgileri")):
            return IntentFrame(IntentKind.PLANNING, 0.8, True, False, 0.3)

        if "?" in normalized or any(marker in normalized for marker in ("neden", "nasıl", "ne ", "why", "how")):
            return IntentFrame(IntentKind.QUESTION, 0.75, False, False, 0.35)

        return IntentFrame(IntentKind.GENERAL, 0.55, False, False, 0.5)


__all__ = ["IntentClassifier", "IntentFrame", "IntentKind"]
