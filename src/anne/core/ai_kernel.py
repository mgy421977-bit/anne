"""ANNE model-independent cognitive engine with learned knowledge feedback."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

PHASES = ("DUY", "BAK", "GÖR", "ANLA", "HİSSET", "YAP", "ÖĞREN")


@dataclass
class Hypothesis:
    text: str
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)


@dataclass
class CognitiveState:
    task: str
    phase: str = "DUY"
    concepts: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    known: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    uncertainty: float = 1.0
    cycle: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AnneCognitiveEngine:
    """Inspectable DUY→BAK→GÖR→ANLA→HİSSET→YAP→ÖĞREN loop."""

    STOPWORDS = {
        "ve", "veya", "ile", "bir", "bu", "şu", "için", "nasıl", "neden", "ne",
        "mi", "mı", "mu", "mü", "de", "da", "en", "çok", "olan", "olanın",
        "the", "and", "or", "with", "for", "what", "why", "how", "are", "is",
    }

    def __init__(self, max_concepts: int = 12, max_hypotheses: int = 5) -> None:
        self.max_concepts = max(1, max_concepts)
        self.max_hypotheses = max(1, max_hypotheses)
        self.state: CognitiveState | None = None

    def start(self, task: str) -> CognitiveState:
        self.state = CognitiveState(task=task)
        return self.state

    def _require_state(self) -> CognitiveState:
        if self.state is None:
            raise RuntimeError("Cognitive cycle has not been started")
        return self.state

    def _set_phase(self, phase: str) -> None:
        state = self._require_state()
        if phase not in PHASES:
            raise ValueError(f"Unknown cognitive phase: {phase}")
        state.phase = phase

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]{3,}", text.lower())

    def duy(self, text: str) -> list[str]:
        state = self._require_state()
        self._set_phase("DUY")
        state.concepts = []
        for token in self._tokens(text):
            if token in self.STOPWORDS or token in state.concepts:
                continue
            state.concepts.append(token)
            if len(state.concepts) >= self.max_concepts:
                break
        state.observations.append(f"DUY: {len(state.concepts)} kavram algılandı")
        return list(state.concepts)

    def bak(self, memory: str = "", evidence: list[str] | None = None, knowledge: str = "") -> None:
        state = self._require_state()
        self._set_phase("BAK")
        if memory.strip():
            state.observations.append("BAK: geçmiş bağlam incelendi")
            state.known.append("Persistent memory was available")
        for item in evidence or []:
            item = item.strip()
            if item and item not in state.evidence:
                state.evidence.append(item)
                state.known.append(item)

        # Learned knowledge is treated as provisional evidence only when it is
        # relevant to the current concepts. This makes learning influence future cycles.
        learned_hits = 0
        for raw in knowledge.splitlines():
            item = raw.strip()
            if not item or item.startswith("["):
                continue
            item_tokens = set(self._tokens(item))
            overlap = item_tokens.intersection(state.concepts)
            if overlap and item not in state.known:
                state.known.append(item)
                learned_hits += 1
                if item not in state.evidence:
                    state.evidence.append(f"LEARNED: {item}")
        if learned_hits:
            state.observations.append(f"BAK: öğrenilmiş bilgiden {learned_hits} ilgili kayıt bulundu")
        if not state.evidence:
            state.unknown.append("No explicit or learned evidence matched the task")

    def gor(self) -> list[str]:
        state = self._require_state()
        self._set_phase("GÖR")
        patterns: list[str] = []
        if len(state.concepts) >= 2:
            patterns.append("concept relationship")
        learned = [item for item in state.evidence if item.startswith("LEARNED:")]
        if learned:
            patterns.append("learned knowledge match")
        if state.evidence:
            patterns.append("evidence-backed pattern")
        if not patterns:
            patterns.append("insufficient pattern evidence")
        state.observations.extend(f"GÖR: {pattern}" for pattern in patterns)
        return patterns

    def anla(self, text: str) -> list[Hypothesis]:
        state = self._require_state()
        self._set_phase("ANLA")
        intent = self.infer_intent(text)
        candidates: list[Hypothesis] = []
        if intent == "question":
            candidates.extend([
                Hypothesis("Soruyu mevcut kanıt ve öğrenilmiş bilgiyle açıklamak", 0.45),
                Hypothesis("Eksik kanıtı araştırarak açıklamak", 0.35),
            ])
        elif intent == "research":
            candidates.extend([
                Hypothesis("Kaynakları karşılaştırıp ortak bulguyu çıkarmak", 0.45),
                Hypothesis("Çelişen kaynakları ayrı hipotezler olarak tutmak", 0.35),
            ])
        elif intent == "action":
            candidates.extend([
                Hypothesis("Görevi küçük doğrulanabilir adımlara bölmek", 0.50),
                Hypothesis("Önce gereksinimleri doğrulamak", 0.30),
            ])
        else:
            candidates.append(Hypothesis("Girdiyi bağlama yerleştirip sonraki adımı seçmek", 0.40))

        learned = [item for item in state.evidence if item.startswith("LEARNED:")]
        for hypothesis in candidates:
            if learned:
                hypothesis.score += min(0.20, 0.05 * len(learned))
                hypothesis.evidence.extend(learned[:3])
            hypothesis.score += min(0.20, 0.03 * len(state.evidence))
        state.hypotheses = sorted(candidates, key=lambda h: h.score, reverse=True)[: self.max_hypotheses]
        return list(state.hypotheses)

    def hisset(self) -> float:
        state = self._require_state()
        self._set_phase("HİSSET")
        evidence_bonus = min(0.40, 0.05 * len(state.evidence))
        learned_bonus = min(0.15, 0.05 * sum(item.startswith("LEARNED:") for item in state.evidence))
        best = max((hypothesis.score for hypothesis in state.hypotheses), default=0.20)
        state.confidence = max(0.0, min(1.0, best * 0.7 + evidence_bonus * 0.8 + learned_bonus))
        state.uncertainty = max(0.0, min(1.0, 1.0 - state.confidence))
        if state.unknown:
            state.uncertainty = min(1.0, state.uncertainty + 0.10)
        if state.confidence < 0.55 or state.unknown:
            state.observations.append("HİSSET: doğrulama ihtiyacı yüksek")
        else:
            state.observations.append("HİSSET: mevcut kanıtla yeterli güven")
        return state.confidence

    def yap(self) -> list[str]:
        state = self._require_state()
        self._set_phase("YAP")
        best = max(state.hypotheses, key=lambda item: item.score, default=None)
        actions: list[str] = []
        if state.unknown or state.confidence < 0.55:
            actions.append("Eksik kanıtı belirle, araştır ve doğrula")
        elif best:
            actions.append(f"En güçlü hipotezi uygula: {best.text}")
        else:
            actions.append("Sonraki doğrulanabilir adımı seç")
        actions.append("Sonucu gözle, karşılaştır ve yeni ders çıkar")
        state.actions = actions
        return list(actions)

    def ogren(self, outcome: str, lesson: str = "") -> list[str]:
        state = self._require_state()
        self._set_phase("ÖĞREN")
        state.cycle += 1
        text = lesson.strip() or outcome.strip()
        if text and text not in state.lessons:
            state.lessons.append(text)
        state.observations.append(f"ÖĞREN: {len(state.lessons)} ders birikmiş durumda")
        return list(state.lessons)

    def cycle(
        self,
        text: str,
        memory: str = "",
        evidence: list[str] | None = None,
        knowledge: str = "",
        outcome: str = "",
        lesson: str = "",
    ) -> CognitiveState:
        self.start(text)
        self.duy(text)
        self.bak(memory, evidence, knowledge)
        self.gor()
        self.anla(text)
        self.hisset()
        self.yap()
        self.ogren(outcome, lesson)
        self._set_phase("DUY")
        return self._require_state()

    def infer_intent(self, text: str) -> str:
        lowered = text.lower().strip()
        if lowered.endswith("?") or any(word in lowered for word in ("nedir", "nasıl", "neden", "ne zaman", "hangi")):
            return "question"
        if any(word in lowered for word in ("araştır", "incele", "karşılaştır", "analiz")):
            return "research"
        if any(word in lowered for word in ("yap", "oluştur", "hazırla", "geliştir", "yaz")):
            return "action"
        return "statement"

    def snapshot(self) -> dict[str, Any]:
        return asdict(self._require_state())


AnneAIKernel = AnneCognitiveEngine
__all__ = ["AnneAIKernel", "AnneCognitiveEngine", "CognitiveState", "Hypothesis", "PHASES"]
