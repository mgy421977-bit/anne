"""Hypothesis generation and ranking support for ANNE's SEE/GÖR stage."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence

from anne.core.cognitive_state import Hypothesis
from anne.mythos.engine import MythosEngine


@dataclass(frozen=True)
class HypothesisView:
    """Ranked view of a hypothesis after contextual scoring."""

    hypothesis: Hypothesis
    score: float
    rank: int
    novelty: float
    evidence_support: float


class HypothesisEngine:
    """Builds a diverse candidate set and ranks it without discarding uncertainty."""

    def __init__(self, mythos: MythosEngine | None = None) -> None:
        self.mythos = mythos or MythosEngine()

    @staticmethod
    def _normalize_probability(value: float) -> float:
        return max(0.01, min(0.99, float(value)))

    @staticmethod
    def _claim_key(claim: str) -> str:
        words = " ".join(claim.lower().split()).strip()
        return hashlib.sha1(words.encode("utf-8")).hexdigest()

    @classmethod
    def _novelty(cls, claim: str, prior_claims: Sequence[str]) -> float:
        if not prior_claims:
            return 1.0
        tokens = set(claim.lower().split())
        best_overlap = 0.0
        for prior in prior_claims:
            other = set(prior.lower().split())
            union = tokens | other
            overlap = len(tokens & other) / len(union) if union else 1.0
            best_overlap = max(best_overlap, overlap)
        return round(1.0 - best_overlap, 3)

    @staticmethod
    def _evidence_support(hypothesis: Hypothesis) -> float:
        if not hypothesis.tested:
            return 0.25
        result = (hypothesis.result or "").lower()
        if any(token in result for token in ("supported", "desteklendi")):
            return 1.0
        if any(token in result for token in ("weak", "zayıf")):
            return 0.5
        if any(token in result for token in ("rejected", "reddedildi")):
            return 0.05
        return 0.4

    @staticmethod
    def uncertainty(probabilities: Sequence[float]) -> float:
        """Return normalized entropy in [0, 1] for the candidate distribution."""
        if not probabilities:
            return 0.0
        values = [max(0.0, float(p)) for p in probabilities]
        total = sum(values)
        if total <= 0:
            return 1.0
        normalized = [p / total for p in values if p > 0]
        if len(normalized) <= 1:
            return 0.0
        entropy = -sum(p * math.log(p) for p in normalized)
        return round(entropy / math.log(len(normalized)), 3)

    def generate(self, topic: str, count: int = 4, prior: float = 0.5) -> list[Hypothesis]:
        """Generate several candidates while preventing exact duplicate claims."""
        if count <= 0:
            return []

        candidates: list[Hypothesis] = []
        seen: set[str] = set()
        current_prior = self._normalize_probability(prior)
        previous_claim = ""

        for index in range(count):
            candidate = self.mythos.generate_hypothesis(
                topic,
                prior_confidence=current_prior,
                previous_claim=previous_claim,
            )
            key = self._claim_key(candidate.claim)
            if key in seen:
                candidate.claim = (
                    f"[ALT·{index + 1}] {candidate.claim}"
                )
            seen.add(self._claim_key(candidate.claim))
            candidate.probability = self._normalize_probability(candidate.probability)
            candidates.append(candidate)
            previous_claim = candidate.claim
            # Do not let a chain become self-confirming; keep later candidates
            # anchored to the original prior instead of the latest winner.
            current_prior = self._normalize_probability(
                (current_prior + candidate.probability) / 2.0
            )

        return candidates

    def rank(
        self,
        hypotheses: Sequence[Hypothesis],
        related_memory_scores: Sequence[float] = (),
    ) -> list[HypothesisView]:
        """Rank every candidate using probability, novelty and evidence."""
        if not hypotheses:
            return []

        memory_support = (
            sum(float(score) for score in related_memory_scores) / len(related_memory_scores)
            if related_memory_scores
            else 0.0
        )
        prior_claims: list[str] = []
        views: list[HypothesisView] = []

        for hypothesis in hypotheses:
            hypothesis.probability = self._normalize_probability(hypothesis.probability)
            novelty = self._novelty(hypothesis.claim, prior_claims)
            evidence = self._evidence_support(hypothesis)
            contextual = min(1.0, 0.65 * hypothesis.probability + 0.2 * evidence + 0.15 * memory_support)
            score = 0.75 * contextual + 0.25 * novelty
            views.append(
                HypothesisView(
                    hypothesis=hypothesis,
                    score=round(score, 4),
                    rank=0,
                    novelty=novelty,
                    evidence_support=round(evidence, 3),
                )
            )
            prior_claims.append(hypothesis.claim)

        views.sort(key=lambda view: (view.score, view.hypothesis.probability), reverse=True)
        return [
            HypothesisView(
                hypothesis=view.hypothesis,
                score=view.score,
                rank=index,
                novelty=view.novelty,
                evidence_support=view.evidence_support,
            )
            for index, view in enumerate(views, start=1)
        ]
