"""
ANNE – Adaptive Neural Nexus Engine

Six-stage cognitive architecture with ethical core, fractal memory,
and Mythos curiosity engine.
"""

from anne.bridge import AnneMythosBridge
from anne.core.cognitive_state import CognitiveState, Consciousness, EthicScore, Hypothesis
from anne.core.ethic_core import EthicCore
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.engine import MythosEngine

__version__ = "0.1.0"
__all__ = [
    "AnneMythosBridge",
    "CognitiveState",
    "Consciousness",
    "EthicScore",
    "Hypothesis",
    "EthicCore",
    "FractalMemory",
    "MythosEngine",
]
