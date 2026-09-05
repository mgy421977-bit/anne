"""Experience records for the MITOS -> ANNE learning loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExperienceStatus(str, Enum):
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTION = "PREDICTION"
    TESTED = "TESTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class ExperienceRecord:
    """Evidence-bearing lifecycle record; simulation is never observation."""
    hypothesis_id: str
    goal: str
    claim: str
    status: ExperienceStatus = ExperienceStatus.HYPOTHESIS
    predicted_outcome: str | None = None
    observed_outcome: str | None = None
    prediction_error: float | None = None
    context: dict[str, Any] = field(default_factory=dict)
    source: str = "mitos"
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def is_learning_evidence(self) -> bool:
        return self.status in {
            ExperienceStatus.VERIFIED,
            ExperienceStatus.FAILED,
            ExperienceStatus.INCONCLUSIVE,
        } and self.prediction_error is not None

    def update_from_outcome(
        self,
        observed_outcome: str,
        prediction_error: float,
        status: ExperienceStatus,
        evidence: list[str] | None = None,
    ) -> None:
        if status not in {
            ExperienceStatus.VERIFIED,
            ExperienceStatus.FAILED,
            ExperienceStatus.INCONCLUSIVE,
        }:
            raise ValueError("outcome status must be VERIFIED, FAILED or INCONCLUSIVE")
        self.observed_outcome = observed_outcome
        self.prediction_error = max(0.0, min(1.0, prediction_error))
        self.status = status
        if evidence:
            self.evidence.extend(evidence)
        # Confidence follows observed error; it is not proof by itself.
        self.confidence = round(max(0.0, 1.0 - self.prediction_error), 3)
