"""Evidence-first synthesis for MITOS research swarms."""
from __future__ import annotations

from dataclasses import dataclass, field

from .agent_swarm import EvidencePackage


@dataclass(frozen=True)
class SynthesisFinding:
    statement: str
    supporting_sources: tuple[str, ...] = ()
    confidence: float = 0.0
    status: str = "HYPOTHESIS"


@dataclass
class MitosSynthesis:
    findings: list[SynthesisFinding] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    next_missions: list[str] = field(default_factory=list)

    @classmethod
    def from_packages(cls, packages: list[EvidencePackage]) -> "MitosSynthesis":
        result = cls()
        source_claims: dict[str, list[str]] = {}
        for package in packages:
            for item in package.findings:
                source_claims.setdefault(item.claim, []).append(item.source)
                result.findings.append(
                    SynthesisFinding(
                        statement=item.claim,
                        supporting_sources=(item.source,),
                        confidence=item.confidence,
                        status=item.evidence_kind,
                    )
                )
            result.contradictions.extend(package.contradictions)
            result.unresolved_questions.extend(package.open_questions)
        # Same claim independently supported by multiple sources is stronger,
        # but is still not promoted to FACT without an explicit verification step.
        for claim, sources in source_claims.items():
            if len(sources) > 1:
                result.findings.append(
                    SynthesisFinding(
                        statement=f"Cross-supported: {claim}",
                        supporting_sources=tuple(sorted(set(sources))),
                        confidence=min(0.99, 0.5 + 0.1 * len(set(sources))),
                        status="CROSS_CHECKED",
                    )
                )
        return result

    def next_research_needed(self) -> bool:
        return bool(self.contradictions or self.unresolved_questions or self.next_missions)
