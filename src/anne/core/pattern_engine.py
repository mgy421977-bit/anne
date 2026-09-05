"""Pattern extraction and conservative rule promotion for ANNE."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from anne.memory.fractal_experience import Experience, FractalExperienceMemory


@dataclass
class PatternCandidate:
    pattern: str
    occurrences: int
    confidence: float
    supporting_experiences: list[str] = field(default_factory=list)


class PatternEngine:
    """Turns repeated experience observations into candidates, not unquestioned rules."""

    def __init__(self, memory: FractalExperienceMemory | None = None) -> None:
        self.memory = memory or FractalExperienceMemory()

    def discover(self, min_occurrences: int = 2, limit: int = 20) -> list[PatternCandidate]:
        items = self.memory.load(10000)
        buckets: dict[str, list[Experience]] = {}
        for item in items:
            for pattern in set(p.strip() for p in item.patterns if p.strip()):
                buckets.setdefault(pattern, []).append(item)
        candidates = []
        for pattern, supporters in buckets.items():
            if len(supporters) < max(1, min_occurrences):
                continue
            avg_conf = sum(x.confidence for x in supporters) / len(supporters)
            confidence = min(0.95, 0.35 + 0.10 * len(supporters) + 0.40 * avg_conf)
            candidates.append(PatternCandidate(pattern, len(supporters), round(confidence, 3), [x.task for x in supporters[:5]]))
        return sorted(candidates, key=lambda x: (x.confidence, x.occurrences), reverse=True)[:max(1, limit)]

    def relevant(self, query: str, limit: int = 8) -> list[PatternCandidate]:
        terms = set(query.lower().split())
        candidates = self.discover(limit=100)
        scored = [(len(terms & set(c.pattern.lower().split())), c) for c in candidates]
        scored.sort(key=lambda x: (x[0], x[1].confidence), reverse=True)
        return [c for score, c in scored[:max(1, limit)] if score > 0]

    @staticmethod
    def promote(candidate: PatternCandidate, min_confidence: float = 0.75) -> str | None:
        if candidate.confidence < min_confidence:
            return None
        return f"RULE CANDIDATE: {candidate.pattern} (confidence={candidate.confidence:.2f}, occurrences={candidate.occurrences})"


__all__ = ["PatternCandidate", "PatternEngine"]
