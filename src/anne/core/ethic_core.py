"""Ethical Core – operational axioms applied at every decision node."""

from __future__ import annotations

from typing import Any, Sequence

from anne.core.cognitive_state import Consciousness, EthicScore, Hypothesis


class EthicCore:
    """Implements the six operational axioms of ANNE.

    Axioms are mathematical operations, not soft guidelines.
    """

    def evaluate(
        self,
        hypothesis: Hypothesis,
        consciousnesses: Sequence[Consciousness],
        input_type: str = "explore",
        related_memories: list[Any] | None = None,
    ) -> EthicScore:
        """Compute the Human-First Action Decision Score (ADS)."""
        related_memories = related_memories or []

        existing = [c for c in consciousnesses if c.exists]
        goodness = len(existing) / max(len(consciousnesses), 1)

        weights = [c.weight for c in existing]
        if weights:
            mean_w = sum(weights) / len(weights)
            variance = sum((w - mean_w) ** 2 for w in weights) / len(weights)
            equality = 1.0 / (1.0 + variance)
        else:
            equality = 0.0

        base_harm = (1.0 - hypothesis.probability) * 0.4
        if related_memories:
            past_verdicts = [m[0] for m in related_memories if m]
            reject_ratio = past_verdicts.count("REDDET") / max(len(past_verdicts), 1)
            base_harm = base_harm * 0.6 + reject_ratio * 0.4
        if input_type == "risk":
            base_harm = min(base_harm + 0.2, 1.0)
        harm = round(base_harm, 3)

        total = (goodness * 0.4) + (equality * 0.4) - (harm * 0.2)
        total = round(max(0.0, min(1.0, total)), 3)

        if total >= 0.7:
            verdict = "ONAYLA"
            reasoning = (
                f"Goodness={goodness:.3f}, Equality={equality:.3f} high. "
                f"Harm={harm:.3f} acceptable."
            )
        elif total >= 0.4:
            verdict = "AYRI_ÇÖZÜM"
            reasoning = "Conflict or uncertainty detected. Independent solutions for each party."
        else:
            verdict = "REDDET"
            reasoning = (
                f"Harm={harm:.3f} high or equality={equality:.3f} degraded. "
                "Action does not benefit all consciousnesses."
            )

        return EthicScore(
            goodness=round(goodness, 3),
            equality=round(equality, 3),
            harm=harm,
            total=total,
            verdict=verdict,
            reasoning=reasoning,
        )
