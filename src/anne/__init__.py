"""ANNE – Adaptive Neural Nexus Engine.

Six-stage cognitive architecture with ethical core and fractal memory.
The cognitive pipeline can run without an LLM; providers are optional adapters.
"""

from __future__ import annotations

from typing import Sequence

from anne.bridge import AnneMythosBridge
from anne.core.cognitive_state import CognitiveState, Consciousness, EthicScore, Hypothesis
from anne.core.decision_loop import DecisionLoop, DecisionResult
from anne.core.ethic_core import EthicCore
from anne.core.fail_fast import FailFastGate
from anne.core.pipeline import AnnePipeline
from anne.core.hypothesis_engine import HypothesisEngine
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.engine import MythosEngine

__version__ = "0.1.0"


def run_pipeline(
    raw_input: str,
    consciousnesses: Sequence[Consciousness] | None = None,
    *,
    memory: FractalMemory | None = None,
    hypothesis: Hypothesis | None = None,
) -> CognitiveState:
    """Run ANNE's deterministic six-stage pipeline without creating an agent."""
    local_memory = memory or FractalMemory(":memory:")
    pipeline = AnnePipeline(local_memory)
    people = list(consciousnesses or [Consciousness(id="C1")])
    _, state = pipeline.run_with_fail_fast(raw_input, people, hypothesis=hypothesis)
    if state is None:
        raise RuntimeError("ANNE pipeline was blocked by FailFast")
    return state


__all__ = [
    "AnneMythosBridge",
    "AnnePipeline",
    "CognitiveState",
    "Consciousness",
    "DecisionLoop",
    "DecisionResult",
    "EthicScore",
    "Hypothesis",
    "HypothesisEngine",
    "EthicCore",
    "FailFastGate",
    "FractalMemory",
    "MythosEngine",
    "run_pipeline",
]
