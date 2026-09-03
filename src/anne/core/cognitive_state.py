"""Core data structures for the ANNE cognitive pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Consciousness:
    """A unit of consciousness tracked by the system."""

    id: str
    weight: float = 1.0
    exists: bool = True
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    """A candidate explanation considered by the ANNE reasoning system."""

    id: str
    topic: str
    claim: str
    probability: float
    iteration: int = 0
    tested: bool = False
    result: Optional[str] = None
    confidence_delta: float = 0.0
    source: str = "placeholder"


@dataclass
class EthicScore:
    """Result of the ethical evaluation at the ANLA stage."""

    goodness: float
    equality: float
    harm: float
    total: float
    verdict: str
    reasoning: str = ""


@dataclass
class CognitiveState:
    """Mutable state that flows through the six-stage cognitive pipeline."""

    raw_input: str = ""
    input_type: str = ""
    context_map: dict[str, Any] = field(default_factory=dict)
    related_memories: list[Any] = field(default_factory=list)
    priority_score: float = 0.0
    attention_focus: str = ""
    low_prob_preserved: list[dict[str, Any]] = field(default_factory=list)
    hypothesis_rankings: list[dict[str, Any]] = field(default_factory=list)
    uncertainty: float = 0.0
    logic_valid: bool = False
    ethic_score: Optional[EthicScore] = None
    empathy_map: dict[str, Any] = field(default_factory=dict)
    affected_consciousnesses: list[Consciousness] = field(default_factory=list)
    action: str = ""
    output: dict[str, Any] = field(default_factory=dict)
