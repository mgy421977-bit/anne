"""MITOS generation boundary for Phase 1a."""
from __future__ import annotations

from anne.mythos.candidate import HypothesisCandidate
from anne.mythos.engine import MitosEngine


def generate_candidates(
    goal: str,
    *,
    batch_size: int = 6,
    engine: MitosEngine | None = None,
) -> list[HypothesisCandidate]:
    """Generate proposals only; this function performs no selection or synthesis."""
    return (engine or MitosEngine()).generate(goal, batch_size=batch_size)


__all__ = ["generate_candidates"]
