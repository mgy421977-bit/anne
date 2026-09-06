"""MITOS curiosity and hypothesis engines.

The legacy ``MythosEngine`` remains available for compatibility. ``MitosEngine``
provides the bounded candidate API used by the cognitive architecture.
"""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from enum import Enum

from anne.core.cognitive_state import Hypothesis


class ExplorationMode(str, Enum):
    HYPOTHESIS = "hypothesis"
    CURIOSITY = "curiosity"
    ASSOCIATION = "association"


@dataclass(frozen=True)
class HypothesisCandidate:
    id: str
    goal: str
    claim: str
    mode: ExplorationMode
    probability: float
    discovery_value: float
    novelty: float
    testability: float
    harm_risk: float
    reversibility: float
    expected_benefit: float
    test_cost: float


class MitosEngine:
    """Deterministic, bounded candidate generator for MITOS planning."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)
        self.iteration = 0

    def generate(self, goal: str, batch_size: int = 10) -> list[HypothesisCandidate]:
        if not goal.strip():
            raise ValueError("goal is required")
        if batch_size < 0 or batch_size > 100:
            raise ValueError("batch_size must be between 0 and 100")
        candidates: list[HypothesisCandidate] = []
        modes = list(ExplorationMode)
        for index in range(batch_size):
            self.iteration += 1
            mode = modes[index % len(modes)]
            probability = round(self.random.uniform(0.1, 0.9), 3)
            novelty = round(self.random.uniform(0.2, 0.95), 3)
            testability = round(self.random.uniform(0.3, 0.95), 3)
            candidates.append(
                HypothesisCandidate(
                    id=f"mitos_{self.iteration:06d}",
                    goal=goal,
                    claim=f"[{mode.value}] Testable research hypothesis for: {goal}",
                    mode=mode,
                    probability=probability,
                    discovery_value=round(
                        probability * 0.4 + novelty * 0.35 + testability * 0.25, 3
                    ),
                    novelty=novelty,
                    testability=testability,
                    harm_risk=0.0,
                    reversibility=1.0,
                    expected_benefit=round(novelty * 0.7, 3),
                    test_cost=round(0.1 + (1.0 - testability) * 0.5, 3),
                )
            )
        return candidates


try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class MythosEngine:
    """Legacy curiosity loop retained for backwards compatibility."""

    SYSTEM_PROMPT = (
        "Sen MYTHOS merak motorusun. Görevin bir konuyu derinlemesine araştırmak için "
        "hipotezler üret. Yanıtını SADECE JSON formatında ver."
    )

    def __init__(self, seed: int | None = None) -> None:
        self.iteration = 0
        self.random = random.Random(seed)
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.use_api = ANTHROPIC_AVAILABLE and bool(self.api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.use_api else None

    def generate_hypothesis(
        self, topic: str, prior_confidence: float = 0.5, previous_claim: str = ""
    ) -> Hypothesis:
        self.iteration += 1
        hyp_id = f"hyp_{int(time.time() * 1000)}_{self.iteration}"
        if self.use_api:
            return self._generate_via_api(hyp_id, topic, prior_confidence, previous_claim)
        return self._generate_placeholder(hyp_id, topic, prior_confidence)

    def _generate_via_api(self, hyp_id: str, topic: str, prior: float, previous: str) -> Hypothesis:
        client = self.client
        if client is None:
            return self._generate_placeholder(hyp_id, topic, prior)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Konu: {topic}\nÖnceki: {previous}"}],
            )
            raw = str(getattr(response.content[0], "text", "")).strip()
            data = json.loads(raw.replace("```json", "").replace("```", ""))
            probability = max(0.01, min(0.99, float(data.get("probability", prior))))
            return Hypothesis(
                hyp_id,
                topic,
                data.get("claim", topic),
                probability,
                self.iteration,
                confidence_delta=round(probability - prior, 3),
                source="api",
            )
        except Exception:
            return self._generate_placeholder(hyp_id, topic, prior)

    def _generate_placeholder(self, hyp_id: str, topic: str, prior: float) -> Hypothesis:
        probability = max(
            0.01, min(0.99, prior + self.random.uniform(-0.05, 0.1) + 0.03 * self.iteration)
        )
        return Hypothesis(
            hyp_id,
            topic,
            f"[PH·{self.iteration}] '{topic}' pattern detected",
            round(probability, 3),
            self.iteration,
            confidence_delta=round(probability - prior, 3),
        )

    def test_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        hypothesis.tested = True
        outcome = "supported" if hypothesis.probability > 0.5 else "weak"
        hypothesis.result = (
            f"[TEST·{hypothesis.iteration}] {outcome}. p={hypothesis.probability:.3f}"
        )
        return hypothesis

    def curiosity_loop(
        self, topic: str, max_iterations: int = 4, prior: float = 0.5
    ) -> list[Hypothesis]:
        results: list[Hypothesis] = []
        for _ in range(max_iterations):
            results.append(self.test_hypothesis(self.generate_hypothesis(topic, prior)))
            prior = results[-1].probability
        return sorted(results, key=lambda item: item.probability, reverse=True)
