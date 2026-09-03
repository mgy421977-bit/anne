"""Deterministic local hypothesis generation for ANNE's SEE/GÖR stage."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Sequence

from anne.core.cognitive_state import Hypothesis
from anne.memory.fractal_memory import FractalMemory


@dataclass(frozen=True)
class HypothesisTemplate:
    """A deterministic hypothesis template triggered by input semantics."""

    name: str
    trigger_keywords: tuple[str, ...]
    claim_template: str
    probability_base: float


@dataclass(frozen=True)
class HypothesisView:
    """Ranked candidate view used by SEE/GÖR."""

    hypothesis: Hypothesis
    score: float
    rank: int
    novelty: float
    evidence_support: float


class HypothesisEngine:
    """Generate and rank hypotheses without requiring an external model."""

    DEFAULT_TEMPLATES: tuple[HypothesisTemplate, ...] = (
        HypothesisTemplate(
            "failure_pattern",
            ("hata", "error", "fail", "başarısız", "problem", "sorun"),
            "Bu girdi geçmişteki benzer başarısızlıklarla ilişkili olabilir; kök neden yeniden ortaya çıkabilir.",
            0.62,
        ),
        HypothesisTemplate(
            "risk_check",
            ("risk", "tehlike", "zarar", "danger", "harm", "güvenlik", "security"),
            "Bu girdi risk içeren bir durum olabilir; zarar ihtimali ve güvenlik kısıtları ayrıca doğrulanmalıdır.",
            0.58,
        ),
        HypothesisTemplate(
            "goal_alignment",
            ("hedef", "goal", "amaç", "objective", "istenen", "desired"),
            "Belirtilen hedef, mevcut yaklaşımın uygunluğu ve ölçülebilir sonuçları üzerinden değerlendirilebilir.",
            0.56,
        ),
        HypothesisTemplate(
            "consistency_check",
            ("tutarlı", "consistent", "uyumlu", "çelişki", "contradiction"),
            "Girdi önceki bilgi veya kararlarla kısmen çelişiyor olabilir; tutarlılık yeniden kontrol edilmelidir.",
            0.54,
        ),
        HypothesisTemplate(
            "novelty_exploration",
            ("yeni", "new", "deneme", "try", "keşfet", "explore", "araştır"),
            "Bu girdi yeni bir alan açıyor olabilir; mevcut bellekteki benzerlikler yetersiz kalabilir ve keşif gerekebilir.",
            0.50,
        ),
        HypothesisTemplate(
            "query_explanation",
            ("neden", "nasıl", "why", "how", "ne", "what", "nedir"),
            "Girdi bir açıklama veya nedensel ilişki arıyor olabilir; alternatif açıklamalar birlikte değerlendirilmelidir.",
            0.52,
        ),
    )

    def __init__(
        self,
        memory: FractalMemory | None = None,
        templates: Sequence[HypothesisTemplate] | None = None,
        max_hypotheses: int = 5,
    ) -> None:
        self.memory = memory
        self.templates = tuple(templates or self.DEFAULT_TEMPLATES)
        self.max_hypotheses = max(1, max_hypotheses)

    @staticmethod
    def _normalize_probability(value: float) -> float:
        return round(max(0.01, min(0.99, float(value))), 4)

    @staticmethod
    def _claim_key(claim: str) -> str:
        canonical = " ".join(claim.casefold().split())
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in re.findall(r"[\wçğıöşüİĞÖŞÜ]+", text.casefold()) if len(token) > 1}

    @classmethod
    def _novelty(cls, claim: str, prior_claims: Sequence[str]) -> float:
        if not prior_claims:
            return 1.0
        tokens = cls._tokens(claim)
        if not tokens:
            return 0.0
        best = 0.0
        for prior in prior_claims:
            other = cls._tokens(prior)
            union = tokens | other
            overlap = len(tokens & other) / len(union) if union else 1.0
            best = max(best, overlap)
        return round(1.0 - best, 3)

    @staticmethod
    def _memory_evidence(memory: FractalMemory | None) -> float:
        if memory is None:
            return 0.0
        rules = memory.get_strong_rules(limit=5)
        if not rules:
            return 0.0
        confidences = [float(row[1]) for row in rules if len(row) > 1]
        return round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    def _memory_hypotheses(self, raw_input: str) -> list[Hypothesis]:
        if self.memory is None:
            return []
        input_tokens = self._tokens(raw_input)
        candidates: list[Hypothesis] = []
        for row in self.memory.get_recent_failures(limit=20):
            if len(row) < 7:
                continue
            _, _, stage, reason, meta_tag, ethic_total, _ = row
            text = f"{stage} {reason} {meta_tag}".strip()
            overlap = len(input_tokens & self._tokens(text)) / max(len(input_tokens), 1)
            if overlap > 0:
                probability = min(0.85, 0.48 + overlap * 0.45)
                claim = (
                    "Geçmiş SFT izleri bu girdideki örüntünün daha önce "
                    f"{stage} aşamasında sorun ürettiğine işaret ediyor; benzer hata tekrarlanabilir."
                )
                candidates.append(
                    Hypothesis(
                        id="",
                        topic="failure_memory",
                        claim=claim,
                        probability=self._normalize_probability(probability),
                        source="memory",
                        confidence_delta=float(ethic_total or 0.0),
                    )
                )
        for row in self.memory.get_strong_rules(limit=10):
            if len(row) < 2:
                continue
            rule, confidence = str(row[0]), float(row[1])
            overlap = len(input_tokens & self._tokens(rule)) / max(len(input_tokens), 1)
            if overlap > 0:
                candidates.append(
                    Hypothesis(
                        id="",
                        topic="rule_memory",
                        claim=f"Öğrenilmiş kural '{rule[:100]}' bu duruma uygulanabilir ve kontrol edilmelidir.",
                        probability=self._normalize_probability(0.45 + confidence * 0.45),
                        source="memory",
                    )
                )
        return candidates

    def generate(
        self,
        raw_input: str,
        context: dict[str, Any] | None = None,
        count: int | None = None,
    ) -> list[Hypothesis]:
        """Generate a stable candidate set from input, context and local memory."""
        context = context or {}
        target = max(1, min(count or self.max_hypotheses, self.max_hypotheses))
        candidates = self._memory_hypotheses(raw_input)
        lowered = raw_input.casefold()

        for template in self.templates:
            matches = sum(1 for keyword in template.trigger_keywords if keyword.casefold() in lowered)
            if matches == 0:
                continue
            boost = 0.08 * min(matches, 3)
            candidates.append(
                Hypothesis(
                    id="",
                    topic=template.name,
                    claim=template.claim_template,
                    probability=self._normalize_probability(template.probability_base + boost),
                    source="local_template",
                    confidence_delta=0.0,
                )
            )

        if not candidates:
            topic = str(context.get("topic") or "genel durum")
            candidates.append(
                Hypothesis(
                    id="",
                    topic="neutral_exploration",
                    claim=f"Bu girdi '{topic}' hakkında birden fazla açıklama gerektiren bir durum olabilir; ek kanıt toplanmalıdır.",
                    probability=0.45,
                    source="local_default",
                )
            )

        memory_support = self._memory_evidence(self.memory)
        unique: list[Hypothesis] = []
        seen: set[str] = set()
        for hypothesis in candidates:
            key = self._claim_key(hypothesis.claim)
            if key in seen:
                continue
            seen.add(key)
            hypothesis.id = f"hyp_{key[:12]}"
            if memory_support > 0:
                hypothesis.probability = self._normalize_probability(
                    hypothesis.probability * 0.9 + memory_support * 0.1
                )
            unique.append(hypothesis)

        unique.sort(key=lambda item: (-item.probability, item.topic, item.id))
        return unique[:target]

    @classmethod
    def uncertainty(cls, probabilities: Sequence[float]) -> float:
        if not probabilities:
            return 0.0
        values = [max(0.0, float(value)) for value in probabilities]
        total = sum(values)
        if total <= 0:
            return 1.0
        normalized = [value / total for value in values if value > 0]
        if len(normalized) <= 1:
            return 0.0
        entropy = -sum(value * math.log(value) for value in normalized)
        return round(entropy / math.log(len(normalized)), 3)

    @staticmethod
    def _evidence_support(hypothesis: Hypothesis) -> float:
        if not hypothesis.tested:
            return 0.25 if hypothesis.source.startswith("local") else 0.2
        result = (hypothesis.result or "").casefold()
        if "supported" in result or "desteklendi" in result:
            return 1.0
        if "weak" in result or "zayıf" in result:
            return 0.5
        if "rejected" in result or "reddedildi" in result:
            return 0.05
        return 0.4

    def rank(
        self,
        hypotheses: Sequence[Hypothesis],
        related_memory_scores: Sequence[float] = (),
    ) -> list[HypothesisView]:
        """Rank all candidates while preserving novelty and uncertainty."""
        if not hypotheses:
            return []
        memory_support = (
            sum(float(score) for score in related_memory_scores) / len(related_memory_scores)
            if related_memory_scores
            else 0.0
        )
        views: list[HypothesisView] = []
        prior_claims: list[str] = []
        for hypothesis in hypotheses:
            novelty = self._novelty(hypothesis.claim, prior_claims)
            evidence = self._evidence_support(hypothesis)
            contextual = min(
                1.0,
                0.65 * hypothesis.probability + 0.2 * evidence + 0.15 * memory_support,
            )
            score = round(0.75 * contextual + 0.25 * novelty, 4)
            views.append(HypothesisView(hypothesis, score, 0, novelty, round(evidence, 3)))
            prior_claims.append(hypothesis.claim)
        views.sort(key=lambda view: (view.score, view.hypothesis.probability, view.hypothesis.id), reverse=True)
        return [
            HypothesisView(
                view.hypothesis,
                view.score,
                index,
                view.novelty,
                view.evidence_support,
            )
            for index, view in enumerate(views, start=1)
        ]
