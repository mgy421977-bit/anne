"""Small, deterministic Turkish language motor used before any LLM.

This is intentionally a foundation, not a claim of complete Turkish grammar.
It performs normalization, tokenization, intent detection, a conservative
suffix scan, simple sentence-role heuristics and deterministic response
construction. LLMs may enrich an answer later, but they are not the Turkish
language authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class TurkishAnalysis:
    original: str
    normalized: str
    tokens: tuple[str, ...]
    intent: str
    morphology: dict[str, tuple[str, ...]] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)


_SUFFIXES = (
    "siniz", "sınız", "sunuz", "sünüz", "misiniz", "mısınız", "musunuz", "müsünüz",
    "dir", "dır", "dur", "dür", "ler", "lar", "dan", "den", "tan", "ten",
    "da", "de", "ta", "te", "ı", "i", "u", "ü", "a", "e", "ın", "in", "un", "ün",
)


class TurkishLanguageEngine:
    """Deterministic Turkish parsing and response generation primitives."""

    def normalize(self, text: str) -> str:
        text = text.strip().lower()
        text = text.replace("×", "*").replace("÷", "/")
        text = re.sub(r"\s+", " ", text)
        return text

    def tokenize(self, text: str) -> tuple[str, ...]:
        return tuple(re.findall(r"[a-zçğıöşü0-9]+", self.normalize(text)))

    def analyze_morphology(self, tokens: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        result: dict[str, tuple[str, ...]] = {}
        for token in tokens:
            found = []
            stem = token
            for suffix in sorted(_SUFFIXES, key=len, reverse=True):
                if len(stem) > len(suffix) + 1 and stem.endswith(suffix):
                    found.append(suffix)
                    stem = stem[: -len(suffix)]
                    break
            result[token] = (stem, *found)
        return result

    def detect_intent(self, normalized: str) -> str:
        if any(x in normalized for x in ("hava nasıl", "hava durumu", "yağmur yağacak", "sıcaklık kaç")):
            return "weather"
        # Arithmetic must be classified before generic question detection,
        # because natural Turkish math questions often end with '?'.
        if any(op in normalized for op in ("+", "-", "*", "/")) or re.search(
            r"\d+(?:\.\d+)?\s+(artı|eksi|çarpı|bölü)\s+\d+(?:\.\d+)?", normalized
        ):
            return "math"
        if normalized.endswith("?") or normalized.startswith(("ne ", "nasıl ", "kaç ", "kim ", "neden ", "nerede ")):
            return "question"
        return "statement"

    def infer_roles(self, tokens: tuple[str, ...]) -> dict[str, str]:
        roles: dict[str, str] = {}
        for token in tokens:
            if token in {"ben", "sen", "o", "biz", "siz", "onlar"}:
                roles[token] = "pronoun"
            elif token in {"nasıl", "ne", "kaç", "kim", "neden", "nerede"}:
                roles[token] = "question_word"
        return roles

    def analyze(self, text: str) -> TurkishAnalysis:
        normalized = self.normalize(text)
        tokens = self.tokenize(normalized)
        return TurkishAnalysis(
            original=text,
            normalized=normalized,
            tokens=tokens,
            intent=self.detect_intent(normalized),
            morphology=self.analyze_morphology(tokens),
            roles=self.infer_roles(tokens),
        )

    def respond(self, analysis: TurkishAnalysis, *, weather: dict | None = None) -> str:
        if analysis.intent == "weather":
            if weather is None:
                return "Hava durumu için güncel gözlem verisine ihtiyacım var."
            place = weather.get("location", "bulunduğunuz konum")
            temp = weather.get("temperature_c")
            condition = weather.get("condition", "belirlenemedi")
            if temp is None:
                return f"{place} için hava durumu: {condition}."
            return f"{place} için sıcaklık {temp:g} °C. Durum: {condition}."
        if analysis.intent == "math":
            return "Matematik işlemi algılandı; hesaplama motoruna aktarılmalı."
        if analysis.intent == "question":
            return "Soruyu anladım; gerekli gözlem veya bilgi kaynağını belirlemeliyim."
        return "İfadenizi anladım."


__all__ = ["TurkishAnalysis", "TurkishLanguageEngine"]
