"""Core data structures for the ANNE cognitive pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Consciousness:
    """A unit of consciousness tracked by the system.

    Axiom: weight is always 1.0 (equality). exists is always True
    unless explicitly marked otherwise by higher-level logic.
    """

    id: str
    weight: float = 1.0
    exists: bool = True
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    """Hypothesis produced by the Mythos curiosity engine."""

    id: str
    topic: str
    claim: str
    probability: float
    iteration: int = 0
    tested: bool = False
    result: Optional[str] = None
    confidence_delta: float = 0.0
    source: str = "placeholder"  # "api" | "placeholder"


@dataclass
class EthicScore:
    """Result of the ethical evaluation at the ANLA stage."""

    goodness: float
    equality: float
    harm: float
    total: float
    verdict: str  # ONAYLA | REDDET | AYRI_ÇÖZÜM
    reasoning: str = ""


@dataclass
class CognitiveState:
    """Mutable state that flows through the six-stage pipeline."""

    # DUY
    raw_input: str = ""
    input_type: str = ""  # explore | conflict | query | risk
    intent: str = "general"
    intent_confidence: float = 0.0
    requires_evidence: bool = False
    requires_authority_check: bool = False
    ambiguity: float = 1.0

    # Cognitive requirements / evidence boundary
    evidence_status: str = "not_required"  # available | missing | conflicting | unverified
    evidence_count: int = 0
    evidence_verified: bool = False
    authority_check_required: bool = False
    authority_check_passed: bool = False

    # BAK
    context_map: dict[str, Any] = field(default_factory=dict)
    related_memories: list[Any] = field(default_factory=list)

    # GÖR
    priority_score: float = 0.0
    attention_focus: str = ""
    low_prob_preserved: list[dict[str, Any]] = field(default_factory=list)

    # ANLA
    logic_valid: bool = False
    ethic_score: Optional[EthicScore] = None

    # HİSSET
    empathy_map: dict[str, Any] = field(default_factory=dict)
    affected_consciousnesses: list[Consciousness] = field(default_factory=list)

    # YAP
    action: str = ""
    output: dict[str, Any] = field(default_factory=dict)
