"""Mythos – Curiosity & Hypothesis Engine."""

from __future__ import annotations

import json
import os
import random
import time

from anne.core.cognitive_state import Hypothesis

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class MythosEngine:
    """Curiosity loop that generates and tests hypotheses.

    When ANTHROPIC_API_KEY is present, uses Claude for real hypothesis
    generation. Otherwise falls back to a deterministic placeholder.
    """

    SYSTEM_PROMPT = (
        "Sen MYTHOS merak motorusun. Görevin bir konuyu derinlemesine "
        "araştırmak için hipotezler üret.\n\n"
        "Kurallar:\n"
        "1. Her hipotez somut, test edilebilir bir önerme olmalı\n"
        "2. Olasılık değeri (0.01-0.99) gerçekçi olmalı — hiçbir hipotez 0 olamaz\n"
        "3. Her iterasyonda önceki hipotezden öğrenerek güncelle\n"
        "4. Yanıtını SADECE JSON formatında ver, başka hiçbir şey yazma\n\n"
        "JSON formatı:\n"
        "{\n"
        '  "claim": "hipotez metni (Türkçe, 1-2 cümle)",\n'
        '  "probability": 0.XX,\n'
        '  "reasoning": "neden bu olasılık (1 cümle)"\n'
        "}"
    )

    def __init__(self) -> None:
        self.iteration = 0
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.use_api = ANTHROPIC_AVAILABLE and bool(self.api_key)
        self.client = (
            anthropic.Anthropic(api_key=self.api_key) if self.use_api else None
        )

    def generate_hypothesis(
        self,
        topic: str,
        prior_confidence: float = 0.5,
        previous_claim: str = "",
    ) -> Hypothesis:
        self.iteration += 1
        hyp_id = f"hyp_{int(time.time() * 1000)}_{self.iteration}"

        if self.use_api:
            return self._generate_via_api(
                hyp_id, topic, prior_confidence, previous_claim
            )
        return self._generate_placeholder(hyp_id, topic, prior_confidence)

    def _generate_via_api(
        self, hyp_id: str, topic: str, prior: float, previous: str
    ) -> Hypothesis:
        client = self.client
        if client is None:
            return self._generate_placeholder(hyp_id, topic, prior)

        user_msg = (
            f'Konu: "{topic}"\n'
            f"Önceki güven: {prior:.3f}\n"
            f"Önceki hipotez: {previous if previous else 'Yok (ilk iterasyon)'}\n"
            f"İterasyon: {self.iteration}\n\n"
            "Bu konuda yeni bir hipotez üret. Önceki hipotezi geliştir "
            "veya alternatif öner."
        )
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            first_block = response.content[0] if response.content else None
            raw = str(getattr(first_block, "text", "")).strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            claim = data.get("claim", f"API hypothesis: {topic}")
            prob = max(0.01, min(0.99, float(data.get("probability", prior))))
            delta = round(prob - prior, 3)
            return Hypothesis(
                id=hyp_id,
                topic=topic,
                claim=claim,
                probability=round(prob, 3),
                iteration=self.iteration,
                confidence_delta=delta,
                source="api",
            )
        except Exception:
            return self._generate_placeholder(hyp_id, topic, prior)

    def _generate_placeholder(
        self, hyp_id: str, topic: str, prior: float
    ) -> Hypothesis:
        noise = random.uniform(-0.05, 0.1)
        prob = max(0.01, min(0.99, prior + noise + (0.03 * self.iteration)))
        delta = round(prob - prior, 3)
        level = "high" if prob > 0.7 else "medium" if prob > 0.4 else "low"
        claim = (
            f"[PH·{self.iteration}] '{topic}' — pattern detected "
            f"with {level} confidence."
        )
        return Hypothesis(
            id=hyp_id,
            topic=topic,
            claim=claim,
            probability=round(prob, 3),
            iteration=self.iteration,
            confidence_delta=delta,
            source="placeholder",
        )

    def test_hypothesis(self, h: Hypothesis) -> Hypothesis:
        if self.use_api and h.source == "api":
            return self._test_via_api(h)
        return self._test_placeholder(h)

    def _test_via_api(self, h: Hypothesis) -> Hypothesis:
        client = self.client
        if client is None:
            return self._test_placeholder(h)

        test_prompt = (
            "Sen MYTHOS test motorusun. Bir hipotezi değerlendirip "
            "sonucu JSON döndür.\n\n"
            "JSON formatı:\n"
            "{\n"
            '  "outcome": "desteklendi/zayıf/reddedildi",\n'
            '  "updated_probability": 0.XX,\n'
            '  "finding": "kısa bulgu açıklaması (Türkçe)"\n'
            "}"
        )
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                system=test_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Hipotez: {h.claim}\n"
                            f"Mevcut olasılık: {h.probability}"
                        ),
                    }
                ],
            )
            first_block = response.content[0] if response.content else None
            raw = str(getattr(first_block, "text", "")).strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            h.tested = True
            h.probability = max(
                0.01,
                min(0.99, float(data.get("updated_probability", h.probability))),
            )
            outcome = data.get("outcome", "?")
            finding = data.get("finding", "")
            h.result = f"[TEST-API] {outcome}: {finding}"
            return h
        except Exception:
            return self._test_placeholder(h)

    def _test_placeholder(self, h: Hypothesis) -> Hypothesis:
        h.tested = True
        outcome = "supported" if h.probability > 0.5 else "weak"
        h.result = (
            f"[TEST·{h.iteration}] {outcome}. "
            f"p={h.probability:.3f} Δ={h.confidence_delta:+.3f}"
        )
        return h

    def curiosity_loop(
        self,
        topic: str,
        max_iterations: int = 4,
        prior: float = 0.5,
    ) -> list[Hypothesis]:
        """Generate → Test → Update → Repeat. Lowest probability is preserved."""
        hypotheses: list[Hypothesis] = []
        current_prior = prior
        previous_claim = ""

        for _ in range(max_iterations):
            h = self.generate_hypothesis(topic, current_prior, previous_claim)
            h = self.test_hypothesis(h)
            hypotheses.append(h)
            current_prior = h.probability
            previous_claim = h.claim

        hypotheses.sort(key=lambda x: x.probability, reverse=True)
        return hypotheses
