"""MITOS hypothesis engine with backward-compatible legacy Mythos support."""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from enum import Enum

from anne.core.cognitive_state import Hypothesis

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


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

    def validate(self) -> None:
        if not self.goal.strip() or not self.claim.strip():
            raise ValueError("goal and claim are required")
        for name in ("probability", "discovery_value", "novelty", "testability", "harm_risk", "reversibility", "expected_benefit", "test_cost"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


class MythosEngine:
    """Legacy curiosity engine retained for existing ANNE callers."""

    def __init__(self, seed: int | None = None) -> None:
        self.iteration = 0
        self.random = random.Random(seed)
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.use_api = ANTHROPIC_AVAILABLE and bool(self.api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.use_api else None

    def generate_hypothesis(self, topic: str, prior_confidence: float = 0.5, previous_claim: str = "") -> Hypothesis:
        self.iteration += 1
        hyp_id = f"hyp_{int(time.time() * 1000)}_{self.iteration}"
        noise = self.random.uniform(-0.05, 0.1)
        prob = max(0.01, min(0.99, prior_confidence + noise + (0.03 * self.iteration)))
        delta = round(prob - prior_confidence, 3)
        level = "high" if prob > 0.7 else "medium" if prob > 0.4 else "low"
        return Hypothesis(id=hyp_id, topic=topic, claim=f"[PH·{self.iteration}] '{topic}' — pattern detected with {level} confidence.", probability=round(prob, 3), iteration=self.iteration, confidence_delta=delta, source="placeholder")

    def test_hypothesis(self, h: Hypothesis) -> Hypothesis:
        h.tested = True
        outcome = "supported" if h.probability > 0.5 else "weak"
        h.result = f"[TEST·{h.iteration}] {outcome}. p={h.probability:.3f} Δ={h.confidence_delta:+.3f}"
        return h

    def curiosity_loop(self, topic: str, max_iterations: int = 4, prior: float = 0.5) -> list[Hypothesis]:
        hypotheses: list[Hypothesis] = []
        current_prior = prior
        previous_claim = ""
        for _ in range(max_iterations):
            h = self.test_hypothesis(self.generate_hypothesis(topic, current_prior, previous_claim))
            hypotheses.append(h)
            current_prior = h.probability
            previous_claim = h.claim
        return sorted(hypotheses, key=lambda x: x.probability, reverse=True)


class MitosEngine:
    """Bounded, deterministic candidate generator for the MITOS discovery API."""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)
        self._candidate_counter = 0

    def generate(self, goal: str, batch_size: int = 10) -> list[HypothesisCandidate]:
        if not goal.strip():
            raise ValueError("goal is required")
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        modes = list(ExplorationMode)
        candidates: list[HypothesisCandidate] = []
        for index in range(batch_size):
            self._candidate_counter += 1
            mode = modes[index % len(modes)]
            probability = self.random.uniform(0.05, 0.95)
            novelty = self.random.uniform(0.25, 0.95)
            testability = self.random.uniform(0.45, 1.0)
            expected_benefit = self.random.uniform(0.2, 1.0)
            test_cost = self.random.uniform(0.05, 0.8)
            discovery_value = round(0.30 * novelty + 0.25 * testability + 0.25 * expected_benefit + 0.20 * (1.0 - test_cost), 4)
            candidate = HypothesisCandidate(
                id=f"cand_{self._candidate_counter:08d}", goal=goal,
                claim=self._claim(goal, mode, index), mode=mode,
                probability=round(probability, 4), discovery_value=discovery_value,
                novelty=round(novelty, 4), testability=round(testability, 4),
                harm_risk=0.0, reversibility=1.0,
                expected_benefit=round(expected_benefit, 4), test_cost=round(test_cost, 4),
            )
            candidate.validate()
            candidates.append(candidate)
        return candidates

    @staticmethod
    def _claim(goal: str, mode: ExplorationMode, index: int) -> str:
        templates = {
            ExplorationMode.HYPOTHESIS: "A testable pathway may satisfy the goal under bounded assumptions.",
            ExplorationMode.CURIOSITY: "An overlooked constraint or opportunity may materially change the solution space.",
            ExplorationMode.ASSOCIATION: "A cross-domain analogy may reveal a testable alternative pathway.",
        }
        return f"[{mode.value}:{index}] {templates[mode]} Goal: {goal}"


__all__ = ["ExplorationMode", "HypothesisCandidate", "MythosEngine", "MitosEngine"]
