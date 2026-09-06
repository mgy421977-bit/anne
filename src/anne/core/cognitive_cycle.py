"""Typed end-to-end cognitive cycle contract for ANNE.

This module defines orchestration state and lifecycle boundaries. It intentionally
contains no hidden model calls or external side effects; execution is delegated
to explicit adapters so that each stage can be tested and audited independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class EvidenceKind(str, Enum):
    OBSERVATION = "OBSERVATION"
    FACT = "FACT"
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTION = "PREDICTION"
    BELIEF = "BELIEF"
    RULE = "RULE"
    SIMULATION = "SIMULATION"
    EXPERIENCE = "EXPERIENCE"


class CycleStatus(str, Enum):
    CREATED = "CREATED"
    OBSERVED = "OBSERVED"
    EXPLORED = "EXPLORED"
    EVALUATED = "EVALUATED"
    PLANNED = "PLANNED"
    AUTHORIZED = "AUTHORIZED"
    ACTED = "ACTED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Observation:
    content: Any
    source: str
    observed_at: str
    provenance: tuple[str, ...] = ()
    kind: EvidenceKind = EvidenceKind.OBSERVATION


@dataclass(frozen=True)
class Prediction:
    hypothesis_id: str
    expected_outcome: Any
    probability: float
    confidence: float
    provenance: tuple[str, ...] = ()
    kind: EvidenceKind = EvidenceKind.PREDICTION


@dataclass(frozen=True)
class Outcome:
    prediction_id: str
    observed_outcome: Any
    observed: bool
    source: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class PredictionError:
    prediction_id: str
    magnitude: float | None
    qualitative: str


@dataclass
class CognitiveCycle:
    """Reconstructable state for one ANNE decision/learning cycle."""

    goal: str
    cycle_id: str = field(default_factory=lambda: f"cycle_{uuid4().hex[:12]}")
    status: CycleStatus = CycleStatus.CREATED
    observations: list[Observation] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    workspace_ids: list[str] = field(default_factory=list)
    hypothesis_ids: list[str] = field(default_factory=list)
    predictions: list[Prediction] = field(default_factory=list)
    value_assessment: dict[str, Any] = field(default_factory=dict)
    safety_decision: dict[str, Any] = field(default_factory=dict)
    plan: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    outcomes: list[Outcome] = field(default_factory=list)
    prediction_errors: list[PredictionError] = field(default_factory=list)
    experience_ids: list[str] = field(default_factory=list)
    learning_updates: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)

    def add_observation(self, observation: Observation) -> None:
        self.observations.append(observation)
        self.provenance.extend(observation.provenance)
        self.status = CycleStatus.OBSERVED

    def add_prediction(self, prediction: Prediction) -> None:
        if not 0.0 <= prediction.probability <= 1.0:
            raise ValueError("prediction probability must be in [0, 1]")
        if not 0.0 <= prediction.confidence <= 1.0:
            raise ValueError("prediction confidence must be in [0, 1]")
        self.predictions.append(prediction)

    def record_outcome(self, outcome: Outcome, error: PredictionError | None = None) -> None:
        self.outcomes.append(outcome)
        if error is not None:
            self.prediction_errors.append(error)
        self.status = CycleStatus.COMPLETED

    def block(self, reason: str) -> None:
        self.safety_decision = {"allowed": False, "reason": reason}
        self.status = CycleStatus.BLOCKED

    def authorize(self, reason: str = "") -> None:
        self.safety_decision = {"allowed": True, "reason": reason}
        self.status = CycleStatus.AUTHORIZED

    def learning_is_evidenced(self) -> bool:
        """Require an explicit future-behavior update, not merely a memory record."""
        return any(
            bool(update.get("behavior_changed")) and bool(update.get("evidence_ids"))
            for update in self.learning_updates
        )
