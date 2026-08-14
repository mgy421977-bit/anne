"""DecisionLoop — thin facade over FailFast + AnnePipeline.

Ensures a single entry path: no application module should bypass fail-fast,
semantic validation (ANLA), or ethical evaluation when using this API.

Design intent (see governance/CORE_RULES.md):
  R1 Respect · R2 Protect · R3 Precaution

This is not a consciousness engine, not an unhackable core, and not AGI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence
from uuid import uuid4

from anne.core.cognitive_state import CognitiveState, Consciousness, Hypothesis
from anne.core.fail_fast import FailFastResult
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory


@dataclass
class DecisionResult:
    """Normalized outcome of one decision cycle."""

    status: str  # EXECUTED | ABORTED
    verdict: str  # ONAYLA | REDDET | AYRI_ÇÖZÜM | FAIL_FAST | UNKNOWN
    action: str  # PROCEED | HALT | SEPARATE_SOLUTIONS | ...
    output: dict[str, Any] = field(default_factory=dict)
    fail_fast: Optional[dict[str, Any]] = None
    anla_score: Optional[float] = None
    ethic_total: Optional[float] = None
    state: Optional[CognitiveState] = None
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "verdict": self.verdict,
            "action": self.action,
            "output": self.output,
            "fail_fast": self.fail_fast,
            "anla_score": self.anla_score,
            "ethic_total": self.ethic_total,
            "reason": self.reason,
        }


class DecisionLoop:
    """Mandatory path: FailFast → six-stage pipeline → structured result.

    Higher layers (apps, bridges) should call ``run`` instead of inventing
    a parallel decision path that skips gates.
    """

    def __init__(
        self,
        memory: FractalMemory | None = None,
        pipeline: AnnePipeline | None = None,
        anla_enabled: bool = True,
        fail_fast_enabled: bool = True,
    ) -> None:
        self.memory = memory or FractalMemory(":memory:")
        self.pipeline = pipeline or AnnePipeline(
            memory=self.memory,
            anla_enabled=anla_enabled,
            fail_fast_enabled=fail_fast_enabled,
        )

    def run(
        self,
        raw_input: str,
        claim: str | None = None,
        parties: Sequence[Consciousness] | None = None,
        hypothesis: Hypothesis | None = None,
        probability: float = 0.7,
    ) -> DecisionResult:
        """Execute one full decision cycle.

        Parameters
        ----------
        raw_input:
            User or system input text.
        claim:
            Optional hypothesis claim; defaults to raw_input.
        parties:
            Decision-scope party records (not a claim of machine consciousness).
        hypothesis:
            Optional pre-built Hypothesis; otherwise one is synthesized.
        probability:
            Prior for synthesized hypothesis.
        """
        parties = list(parties) if parties else [Consciousness(id="user")]
        text_claim = claim if claim is not None else raw_input
        hyp = hypothesis or Hypothesis(
            id=f"h_{uuid4().hex[:12]}",
            topic=text_claim[:48],
            claim=text_claim,
            probability=probability,
            source="decision_loop",
        )

        ff, state = self.pipeline.run_with_fail_fast(raw_input, parties, hyp)

        if not ff.passed:
            return DecisionResult(
                status="ABORTED",
                verdict="FAIL_FAST",
                action="HALT",
                output={
                    "verdict": "FAIL_FAST",
                    "action": "HALT",
                    "reason": ff.reason,
                    "rule_id": ff.rule_id,
                },
                fail_fast=ff.as_dict(),
                reason=ff.reason,
            )

        assert state is not None
        out = state.output or {}
        verdict = out.get("verdict") or state.action or "UNKNOWN"
        action = out.get("action") or ("HALT" if verdict == "REDDET" else "UNKNOWN")

        aborted = verdict in {"REDDET", "FAIL_FAST"} or action == "HALT"
        # AYRI_ÇÖZÜM is a controlled outcome, not a hard abort
        if verdict == "AYRI_ÇÖZÜM":
            aborted = False

        ethic_total = state.ethic_score.total if state.ethic_score else None
        anla_score = state.context_map.get("anla_score")

        return DecisionResult(
            status="ABORTED" if aborted else "EXECUTED",
            verdict=str(verdict),
            action=str(action),
            output=out,
            fail_fast=ff.as_dict(),
            anla_score=anla_score if isinstance(anla_score, (int, float)) else None,
            ethic_total=ethic_total,
            state=state,
            reason=str(out.get("reason") or out.get("note") or ""),
        )
