"""Deterministic MITOS candidate evaluation and ANNE selection boundary.

MITOS proposes alternatives; ANNE evaluates and selects. This module is
LLM-free and network-free so the executive gate can be regression-tested
independently of model quality.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterable

from anne.core.anla_score import compute_anla_score
from anne.mythos.engine import HypothesisCandidate


class Decision(str, Enum):
    SELECT = "SELECT"
    ABSTAIN = "ABSTAIN"
    RESEARCH = "RESEARCH"
    RETRY = "RETRY"


class TaskMode(str, Enum):
    FACTUAL = "FACTUAL"
    RESEARCH = "RESEARCH"
    CREATIVE = "CREATIVE"
    TECHNICAL = "TECHNICAL"
    PLANNING = "PLANNING"
    HYPOTHESIS = "HYPOTHESIS"


@dataclass(frozen=True)
class Candidate:
    id: str
    content: str
    source: str = "MITOS"
    generation_mode: str = "hypothesis"
    task_mode: TaskMode = TaskMode.HYPOTHESIS
    confidence: float = 0.5
    novelty: float = 0.5
    metadata: dict[str, object] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_id: str
    accepted: bool
    decision: Decision
    final_score: float
    reasons: tuple[str, ...]
    safety: float
    ethics: float
    anla: float
    relevance: float
    consistency: float
    novelty: float
    clarity: float


@dataclass(frozen=True)
class SelectionResult:
    winner: Candidate | None
    evaluations: tuple[CandidateEvaluation, ...]
    rejected: tuple[str, ...]
    decision: Decision
    reason: str


_INSTRUCTION_RE = re.compile(
    r"(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|rules?)",
    re.I,
)
_DANGEROUS_ACTION_RE = re.compile(
    r"\b(?:build|make|deploy|execute|steal|exfiltrate|weaponize|detonate)\b.{0,80}\b"
    r"(?:weapon|explosive|malware|ransomware|credential|password|keylogger)\b",
    re.I,
)
_WORD_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]+", re.UNICODE)
_STOPWORDS = {
    "ve", "ile", "bir", "bu", "için", "de", "da", "the", "and", "with", "a", "an", "to", "of"
}


class CandidateSelector:
    """Evaluate a candidate pool and select only a gated winner."""

    # relevance, consistency, ANLA, safety, ethics, novelty, clarity
    PROFILES = {
        TaskMode.FACTUAL: (0.25, 0.15, 0.25, 0.10, 0.10, 0.05, 0.10),
        TaskMode.RESEARCH: (0.22, 0.15, 0.25, 0.10, 0.10, 0.08, 0.10),
        TaskMode.CREATIVE: (0.10, 0.15, 0.10, 0.10, 0.20, 0.20, 0.15),
        TaskMode.TECHNICAL: (0.23, 0.15, 0.25, 0.10, 0.10, 0.07, 0.10),
        TaskMode.PLANNING: (0.20, 0.15, 0.20, 0.15, 0.15, 0.05, 0.10),
        TaskMode.HYPOTHESIS: (0.15, 0.20, 0.15, 0.15, 0.15, 0.10, 0.10),
    }
    SCORE_THRESHOLD = 0.60
    ANLA_THRESHOLD = 0.75
    RELEVANCE_THRESHOLD = 0.25

    def evaluate(
        self,
        candidate: Candidate,
        context: str = "",
        peer_contents: Iterable[str] = (),
    ) -> CandidateEvaluation:
        content = candidate.content.strip()
        if not content:
            return self._reject(candidate, "empty candidate")
        if _INSTRUCTION_RE.search(content):
            return self._reject(candidate, "instruction-like candidate")
        harm_risk = float(candidate.metadata.get("harm_risk", 0.0) or 0.0)
        if harm_risk > 0.0 or _DANGEROUS_ACTION_RE.search(content):
            return self._reject(candidate, "safety gate failed")
        if str(candidate.metadata.get("ethics", "GREEN")).upper() == "RED":
            return self._reject(candidate, "ethics gate failed")

        relevance = self._relevance(context, content) if context else 1.0
        clarity = min(1.0, len(_WORD_RE.findall(content)) / 18.0)
        anla = compute_anla_score(content)
        consistency = 1.0 if not self._contradictory(content) else 0.25
        safety = max(0.0, min(1.0, 1.0 - harm_risk))
        ethics = 1.0 if str(candidate.metadata.get("ethics", "GREEN")).upper() != "YELLOW" else 0.6
        novelty = self._batch_novelty(candidate.novelty, content, peer_contents)
        mode = candidate.task_mode if isinstance(candidate.task_mode, TaskMode) else TaskMode.HYPOTHESIS
        weights = self.PROFILES[mode]
        values = (relevance, consistency, anla, safety, ethics, novelty, clarity)
        score = round(sum(w * v for w, v in zip(weights, values)), 4)
        accepted = (
            score >= self.SCORE_THRESHOLD
            and anla >= self.ANLA_THRESHOLD
            and relevance >= self.RELEVANCE_THRESHOLD
        )
        reason = (
            "passed safety, ethics, ANLA and content gates"
            if accepted
            else "below deterministic selection threshold"
        )
        return CandidateEvaluation(
            candidate.id,
            accepted,
            Decision.SELECT if accepted else Decision.ABSTAIN,
            score,
            (reason,),
            safety,
            ethics,
            anla,
            relevance,
            consistency,
            novelty,
            clarity,
        )

    def select(self, candidates: Iterable[Candidate], context: str = "") -> SelectionResult:
        pool = list(candidates)
        evaluations = tuple(
            self.evaluate(c, context, (p.content for p in pool if p.id != c.id))
            for c in pool
        )
        accepted = [e for e in evaluations if e.accepted]
        if not accepted:
            if pool:
                decision = (
                    Decision.RESEARCH
                    if any(e.relevance < self.RELEVANCE_THRESHOLD for e in evaluations)
                    else Decision.RETRY
                )
                return SelectionResult(
                    None,
                    evaluations,
                    tuple(e.candidate_id for e in evaluations),
                    decision,
                    "no candidate passed the gate",
                )
            return SelectionResult(None, (), (), Decision.ABSTAIN, "candidate pool is empty")

        winner_eval = max(
            accepted,
            key=lambda e: (e.final_score, e.anla, e.relevance, e.novelty, e.candidate_id),
        )
        winner = next(c for c in pool if c.id == winner_eval.candidate_id)
        rejected = tuple(e.candidate_id for e in evaluations if e.candidate_id != winner.id)
        return SelectionResult(
            winner,
            evaluations,
            rejected,
            Decision.SELECT,
            "highest gated candidate score",
        )

    @staticmethod
    def from_hypothesis(
        candidate: HypothesisCandidate,
        task_mode: TaskMode = TaskMode.HYPOTHESIS,
    ) -> Candidate:
        return Candidate(
            id=candidate.id,
            content=candidate.claim,
            source="MITOS",
            generation_mode=candidate.mode.value,
            task_mode=task_mode,
            confidence=candidate.probability,
            novelty=candidate.novelty,
            metadata={
                "harm_risk": candidate.harm_risk,
                "expected_benefit": candidate.expected_benefit,
                "testability": candidate.testability,
            },
        )

    @staticmethod
    def _relevance(context: str, content: str) -> float:
        q = set(_WORD_RE.findall(context.lower())) - _STOPWORDS
        c = set(_WORD_RE.findall(content.lower()))
        return len(q & c) / max(1, len(q))

    @staticmethod
    def _batch_novelty(base: float, content: str, peers: Iterable[str]) -> float:
        """Penalize near-duplicate candidates without introducing model judgment."""
        base = max(0.0, min(1.0, base))
        words = set(_WORD_RE.findall(content.lower()))
        if not words:
            return 0.0
        max_similarity = 0.0
        for peer in peers:
            peer_words = set(_WORD_RE.findall(peer.lower()))
            if peer_words:
                similarity = len(words & peer_words) / max(1, len(words | peer_words))
                max_similarity = max(max_similarity, similarity)
        return round(max(0.0, base * (1.0 - 0.65 * max_similarity)), 4)

    @staticmethod
    def _contradictory(content: str) -> bool:
        pairs = (
            ("always", "never"),
            ("her zaman", "asla"),
            ("mümkün", "imkânsız"),
            ("mümkün", "mümkün değil"),
        )
        lower = content.lower()
        return any(a in lower and b in lower for a, b in pairs)

    @staticmethod
    def _reject(candidate: Candidate, reason: str) -> CandidateEvaluation:
        return CandidateEvaluation(
            candidate.id,
            False,
            Decision.ABSTAIN,
            0.0,
            (reason,),
            0.0 if "safety" in reason else 1.0,
            0.0 if "ethics" in reason else 1.0,
            0.0,
            0.0,
            0.0,
            max(0.0, min(1.0, candidate.novelty)),
            0.0,
        )


__all__ = [
    "Candidate",
    "CandidateEvaluation",
    "CandidateSelector",
    "Decision",
    "SelectionResult",
    "TaskMode",
]
