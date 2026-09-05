"""Evidence collection and synthesis boundary for MITOS."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class EvidencePackage:
    agent_id: str
    mission_id: str
    findings: Tuple[str, ...] = ()
    sources: Tuple[str, ...] = ()
    contradictions: Tuple[str, ...] = ()
    uncertainties: Tuple[str, ...] = ()
    simulated: bool = False


@dataclass(frozen=True)
class MitosSynthesis:
    mission_id: str
    packages: Tuple[EvidencePackage, ...]
    findings: Tuple[str, ...]
    contradictions: Tuple[str, ...]
    open_questions: Tuple[str, ...]


class EvidenceSynthesizer:
    """Combines agent reports without upgrading simulation into fact."""

    def synthesize(self, mission_id: str, packages: Tuple[EvidencePackage, ...]) -> MitosSynthesis:
        findings: list[str] = []
        contradictions: list[str] = []
        questions: list[str] = []
        for package in packages:
            prefix = "SIMULATION: " if package.simulated else "EVIDENCE: "
            findings.extend(prefix + item for item in package.findings)
            contradictions.extend(package.contradictions)
            questions.extend(package.uncertainties)
        return MitosSynthesis(
            mission_id=mission_id,
            packages=packages,
            findings=tuple(findings),
            contradictions=tuple(contradictions),
            open_questions=tuple(dict.fromkeys(questions)),
        )
