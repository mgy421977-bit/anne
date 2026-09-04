"""ANNE native AI kernel: deterministic reasoning independent of any LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Knowledge:
    facts: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class KernelResult:
    intent: str
    concepts: list[str]
    knowledge: Knowledge
    plan: list[str]
    confidence: float
    response: str


class AnneAIKernel:
    """Model-independent AI layer for perception, reasoning and planning.

    It deliberately does not pretend to be a foundation model. Its value is
    inspectable state, lightweight inference, contradiction detection and
    bounded planning that remain available when no LLM is running.
    """

    STOPWORDS = {
        "ve", "veya", "ile", "bir", "bu", "şu", "için", "nasıl", "neden",
        "ne", "mi", "mı", "mu", "mü", "de", "da", "en", "çok", "olan",
        "olanın", "the", "and", "or", "with", "for", "what", "why", "how",
    }

    def __init__(self, max_concepts: int = 12) -> None:
        if max_concepts < 1:
            raise ValueError("max_concepts must be positive")
        self.max_concepts = max_concepts
        self.knowledge = Knowledge()

    def perceive(self, text: str) -> list[str]:
        tokens = re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]{3,}", text.lower())
        concepts: list[str] = []
        for token in tokens:
            if token in self.STOPWORDS or token in concepts:
                continue
            concepts.append(token)
            if len(concepts) >= self.max_concepts:
                break
        return concepts

    def infer_intent(self, text: str) -> str:
        lowered = text.lower().strip()
        if lowered.endswith("?") or any(word in lowered for word in ("nedir", "nasıl", "neden", "ne zaman", "hangi")):
            return "question"
        if any(word in lowered for word in ("araştır", "incele", "karşılaştır", "analiz")):
            return "research"
        if any(word in lowered for word in ("yap", "oluştur", "hazırla", "geliştir", "yaz")):
            return "action"
        return "statement"

    def update_knowledge(self, text: str, evidence: list[str] | None = None) -> Knowledge:
        intent = self.infer_intent(text)
        concepts = self.perceive(text)
        if intent == "question":
            question = text.strip()
            if question and question not in self.knowledge.questions:
                self.knowledge.questions.append(question)
        else:
            for concept in concepts:
                fact = f"Observed concept: {concept}"
                if fact not in self.knowledge.facts:
                    self.knowledge.facts.append(fact)
        if evidence:
            for item in evidence:
                if item and item not in self.knowledge.evidence:
                    self.knowledge.evidence.append(item)
        return self.knowledge

    def detect_contradictions(self) -> list[tuple[str, str]]:
        contradictions: list[tuple[str, str]] = []
        facts = self.knowledge.facts
        positive = [f for f in facts if not f.lower().startswith(("not ", "değil "))]
        negative = [f for f in facts if f.lower().startswith(("not ", "değil "))]
        for pos in positive:
            term = pos.split(": ", 1)[-1]
            if any(term == neg.split(": ", 1)[-1].removeprefix("değil ") for neg in negative):
                contradictions.append((pos, next(neg for neg in negative if term in neg)))
        return contradictions

    def plan(self, text: str) -> list[str]:
        intent = self.infer_intent(text)
        if intent == "research":
            return ["Tanımla", "Kanıt topla", "Kaynakları karşılaştır", "Belirsizlikleri işaretle", "Sonuçlandır"]
        if intent == "action":
            return ["Hedefi tanımla", "Gereksinimleri çıkar", "Uygula", "Doğrula"]
        if intent == "question":
            return ["Soruyu ayrıştır", "Bilinenleri ayır", "Eksikleri belirle", "Yanıtı oluştur"]
        return ["Girdiyi yorumla", "Bağlamı güncelle", "Uygun sonraki adımı seç"]

    def reason(self, text: str, evidence: list[str] | None = None) -> KernelResult:
        concepts = self.perceive(text)
        knowledge = self.update_knowledge(text, evidence=evidence)
        contradictions = self.detect_contradictions()
        plan = self.plan(text)
        confidence = 0.35
        if concepts:
            confidence += 0.15
        if knowledge.evidence:
            confidence += min(0.3, 0.05 * len(knowledge.evidence))
        confidence -= min(0.25, 0.1 * len(contradictions))
        confidence = max(0.0, min(1.0, confidence))
        if contradictions:
            response = "Çelişen bilgiler tespit edildi; doğrulama gerekiyor."
        elif self.infer_intent(text) == "question":
            response = "Soruyu ayrıştırdım. Eksik kanıt varsa araştırma veya ek bağlam gerekiyor."
        else:
            response = "Girdi işlendi; ANNE kendi bağlamını güncelledi ve sonraki adımı belirledi."
        return KernelResult(
            intent=self.infer_intent(text),
            concepts=concepts,
            knowledge=knowledge,
            plan=plan,
            confidence=confidence,
            response=response,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "facts": list(self.knowledge.facts),
            "questions": list(self.knowledge.questions),
            "hypotheses": list(self.knowledge.hypotheses),
            "evidence": list(self.knowledge.evidence),
        }


__all__ = ["AnneAIKernel", "Knowledge", "KernelResult"]
