"""Small evidence-gated learning data model.

Learning is not declared from a source answer alone. A candidate needs
provenance, tests, transfer evidence and a reversible promotion state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


EvidenceKind = Literal["web", "calculation", "experiment", "observation"]


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    claim: str
    kind: EvidenceKind
    provenance: str
    confidence: float
    simulated: bool = False


@dataclass
class LearningCandidate:
    capability_id: str
    hypothesis: str
    method: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    tests_passed: int = 0
    tests_total: int = 0
    transfer_passed: bool = False
    regression_passed: bool = False
    sandbox_passed: bool = False
    confidence: float = 0.0
    promoted: bool = False

    @property
    def test_accuracy(self) -> float:
        if self.tests_total == 0:
            return 0.0
        return self.tests_passed / self.tests_total

    def promotion_ready(self) -> bool:
        return bool(
            self.evidence
            and self.test_accuracy >= 1.0
            and self.transfer_passed
            and self.regression_passed
            and self.sandbox_passed
        )


@dataclass(frozen=True)
class LearningResult:
    question: str
    candidate: LearningCandidate
    trace: tuple[str, ...]
    answer: str | None
