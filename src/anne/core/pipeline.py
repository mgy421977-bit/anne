"""Six-stage cognitive pipeline orchestrator.

Order: optional FailFast → DUY → BAK → GÖR → ANLA → HİSSET → YAP.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from anne.core.anla_score import MAX_ANLA_RETRIES, DEFAULT_TAU, passes_anla
from anne.core.cognitive_state import CognitiveState, Consciousness, Hypothesis
from anne.core.ethic_core import EthicCore
from anne.core.fail_fast import FailFastGate, FailFastResult
from anne.core.hypothesis_engine import HypothesisEngine
from anne.memory.fractal_memory import FractalMemory


class AnnePipeline:
    """Executes FailFast? → DUY → BAK → GÖR → ANLA → HİSSET → YAP."""

    def __init__(
        self,
        memory: FractalMemory,
        anla_enabled: bool = True,
        anla_tau: float = DEFAULT_TAU,
        max_anla_retries: int = MAX_ANLA_RETRIES,
        fail_fast_enabled: bool = True,
        fail_fast_gate: FailFastGate | None = None,
        hypothesis_engine: HypothesisEngine | None = None,
    ) -> None:
        self.memory = memory
        self.ethic = EthicCore()
        self.hypothesis_engine = hypothesis_engine or HypothesisEngine()
        self.anla_enabled = anla_enabled
        self.anla_tau = anla_tau
        self.max_anla_retries = max_anla_retries
        self.fail_fast_enabled = fail_fast_enabled
        self.fail_fast_gate = fail_fast_gate or FailFastGate(enabled=fail_fast_enabled)

    def fail_fast(self, raw_input: str) -> FailFastResult:
        """Deterministic pre-gate before cognitive stages."""
        if not self.fail_fast_enabled:
            return FailFastResult(True, "fail_fast_disabled")
        return self.fail_fast_gate.check(raw_input)

    def duy(
        self, raw_input: str, consciousnesses: Sequence[Consciousness]
    ) -> CognitiveState:
        state = CognitiveState()
        state.raw_input = raw_input
        state.affected_consciousnesses = list(consciousnesses)
        lowered = raw_input.lower()
        if any(w in lowered for w in ["conflict", "çatışma", "savaş", "vs", "karşı"]):
            state.input_type = "conflict"
        elif any(w in lowered for w in ["?", "neden", "nasıl", "ne", "why", "how"]):
            state.input_type = "query"
        elif any(w in lowered for w in ["zarar", "tehlike", "risk", "harm", "danger"]):
            state.input_type = "risk"
        else:
            state.input_type = "explore"
        return state

    def bak(self, state: CognitiveState) -> CognitiveState:
        past = self.memory.get_similar_decisions(state.raw_input)
        state.related_memories = past
        rules = self.memory.get_strong_rules()
        state.context_map = {
            "input_type": state.input_type,
            "consciousness_count": len(state.affected_consciousnesses),
            "past_similar_count": len(past),
            "has_prior_knowledge": len(past) > 0,
            "active_rules": [r[0] for r in rules],
        }
        return state

    def gor(
        self, state: CognitiveState, hypotheses: Sequence[Hypothesis]
    ) -> CognitiveState:
        """SEE/GÖR: inspect the full candidate set and preserve uncertainty."""
        if not hypotheses:
            state.attention_focus = ""
            state.priority_score = 0.0
            state.uncertainty = 0.0
            state.hypothesis_rankings = []
            return state

        memory_scores = [float(m[1]) for m in state.related_memories if len(m) > 1 and m[1] is not None]
        ranked = self.hypothesis_engine.rank(hypotheses, memory_scores)
        state.hypothesis_rankings = [
            {
                "rank": view.rank,
                "hypothesis_id": view.hypothesis.id,
                "claim": view.hypothesis.claim,
                "probability": view.hypothesis.probability,
                "score": view.score,
                "novelty": view.novelty,
                "evidence_support": view.evidence_support,
                "tested": view.hypothesis.tested,
                "result": view.hypothesis.result,
            }
            for view in ranked
        ]

        winner = ranked[0]
        state.attention_focus = winner.hypothesis.claim
        state.priority_score = winner.score
        state.uncertainty = self.hypothesis_engine.uncertainty(
            [view.hypothesis.probability for view in ranked]
        )

        # Preserve every meaningful alternative rather than inspecting only the
        # last candidate. A dynamic floor keeps rare hypotheses visible while
        # preventing near-zero noise from overwhelming attention.
        preserve_floor = max(
            0.05,
            min(0.30, winner.hypothesis.probability - 0.20),
        )
        for view in ranked[1:]:
            probability = view.hypothesis.probability
            score_gap = winner.score - view.score
            if probability >= preserve_floor or score_gap < 0.25:
                state.low_prob_preserved.append(
                    {
                        "hypothesis": view.hypothesis.claim,
                        "probability": probability,
                        "score": view.score,
                        "rank": view.rank,
                        "note": "Alternative preserved for uncertainty-aware reasoning",
                    }
                )

        state.context_map["hypothesis_count"] = len(ranked)
        state.context_map["preserve_floor"] = round(preserve_floor, 3)
        state.context_map["uncertainty"] = state.uncertainty
        return state

    def anla(
        self, state: CognitiveState, hypothesis: Hypothesis
    ) -> CognitiveState:
        """Semantic Validation Layer + ethical synthesis."""
        text = hypothesis.claim or state.raw_input
        semantic_ok = True
        s_anla = 1.0

        if self.anla_enabled:
            failures = self.memory.get_recent_failures(limit=5)
            retries = 0
            semantic_ok, s_anla = passes_anla(text, failures, tau=self.anla_tau)
            while not semantic_ok and retries < self.max_anla_retries:
                self.memory.save_failure_trace(
                    cycle_id=hypothesis.id or "cycle",
                    stage="ANLA",
                    raw_input=state.raw_input,
                    reason=f"S_ANLA={s_anla}<{self.anla_tau}",
                    meta_tag="semantic_reject",
                    hypothesis_id=hypothesis.id,
                    ethic_total=0.0,
                )
                retries += 1
                failures = self.memory.get_recent_failures(limit=5)
                semantic_ok, s_anla = passes_anla(text, failures, tau=self.anla_tau)
                if not semantic_ok and retries >= self.max_anla_retries:
                    break

            state.context_map["anla_score"] = s_anla
            state.context_map["anla_retries"] = retries
            state.context_map["anla_passed"] = semantic_ok

            if not semantic_ok:
                state.logic_valid = False
                state.ethic_score = None
                return state

        score = self.ethic.evaluate(
            hypothesis=hypothesis,
            consciousnesses=state.affected_consciousnesses,
            input_type=state.input_type,
            related_memories=state.related_memories,
        )
        state.ethic_score = score
        state.logic_valid = score.total > 0.0
        self.memory.save_learned_rule(
            f"type:{state.input_type}→{score.verdict}", score.total
        )
        return state

    def hisset(self, state: CognitiveState) -> CognitiveState:
        empathy_map: dict[str, Any] = {}
        for c in state.affected_consciousnesses:
            others = [o for o in state.affected_consciousnesses if o.id != c.id]
            rels = [self.memory.get_empathy_strength(c.id, o.id) for o in others]
            avg_rel = sum(rels) / len(rels) if rels else 0.5
            impact = (state.ethic_score.total if state.ethic_score else 0.5) * avg_rel
            empathy_map[c.id] = {
                "perspective_weight": c.weight,
                "avg_relation_strength": round(avg_rel, 3),
                "estimated_impact": round(impact, 3),
            }
        state.empathy_map = empathy_map
        return state

    def yap(
        self,
        state: CognitiveState,
        hypothesis: Hypothesis,
        group_a: Optional[Sequence[Consciousness]] = None,
        group_b: Optional[Sequence[Consciousness]] = None,
    ) -> CognitiveState:
        if not state.logic_valid and state.ethic_score is None:
            state.action = "REDDET"
            state.output = {
                "verdict": "REDDET",
                "action": "HALT",
                "reason": "Semantic Validation Layer blocked output",
                "anla_score": state.context_map.get("anla_score"),
                "anla_retries": state.context_map.get("anla_retries"),
                "note": "SFT recorded; max retries reached.",
            }
            return state

        score = state.ethic_score
        verdict = score.verdict if score else "UNKNOWN"

        if verdict == "AYRI_ÇÖZÜM" and group_a and group_b:
            output: dict[str, Any] = {
                "verdict": verdict,
                "action": "SEPARATE_SOLUTIONS",
                "group_a": {
                    "for": [c.id for c in group_a],
                    "recommendation": "Independent process for Group A",
                },
                "group_b": {
                    "for": [c.id for c in group_b],
                    "recommendation": "Independent process for Group B",
                },
                "note": "No side taken. 1 == 1.",
            }
            for ca in group_a:
                for cb in group_b:
                    self.memory.update_empathy(ca.id, cb.id, conflict=True, resolved=True)
        elif verdict == "ONAYLA":
            output = {
                "verdict": verdict,
                "action": "PROCEED",
                "hypothesis": hypothesis.claim,
                "source": hypothesis.source,
                "confidence": hypothesis.probability,
                "reasoning": score.reasoning if score else "",
                "empathy_summary": {
                    cid: v["estimated_impact"] for cid, v in state.empathy_map.items()
                },
                "uncertainty": state.uncertainty,
                "alternatives_preserved": len(state.low_prob_preserved),
            }
        else:
            output = {
                "verdict": verdict,
                "action": "HALT",
                "reasoning": score.reasoning if score else "",
                "low_prob_preserved": state.low_prob_preserved,
                "uncertainty": state.uncertainty,
                "note": "Alternatives preserved for uncertainty-aware reasoning.",
            }

        state.action = verdict
        state.output = output
        return state

    def run_with_hypotheses(
        self,
        raw_input: str,
        consciousnesses: Sequence[Consciousness],
        hypotheses: Sequence[Hypothesis],
        selected_index: int = 0,
        group_a: Optional[Sequence[Consciousness]] = None,
        group_b: Optional[Sequence[Consciousness]] = None,
    ) -> tuple[FailFastResult, CognitiveState | None]:
        """Run the complete pipeline over a candidate set.

        GÖR ranks every candidate, while ANLA validates the selected candidate.
        The selected index is applied after ranking, so callers can explicitly
        test an alternative without losing the rest of the candidate set.
        """
        if not hypotheses:
            raise ValueError("At least one hypothesis is required")

        ff = self.fail_fast(raw_input)
        if not ff.passed:
            self.memory.save_failure_trace(
                cycle_id=hypotheses[0].id or "cycle",
                stage="FAIL_FAST",
                raw_input=raw_input,
                reason=ff.reason,
                meta_tag=ff.rule_id or "fail_fast",
                hypothesis_id=hypotheses[0].id,
                ethic_total=0.0,
            )
            return ff, None

        state = self.duy(raw_input, consciousnesses)
        state.context_map["fail_fast"] = ff.as_dict()
        state = self.bak(state)
        state = self.gor(state, hypotheses)
        ranked_ids = [item["hypothesis_id"] for item in state.hypothesis_rankings]
        safe_index = max(0, min(selected_index, len(ranked_ids) - 1))
        selected_id = ranked_ids[safe_index]
        selected = next(h for h in hypotheses if h.id == selected_id)
        state.context_map["selected_hypothesis_id"] = selected.id
        state = self.anla(state, selected)
        if state.logic_valid or state.ethic_score is not None:
            state = self.hisset(state)
        state = self.yap(state, selected, group_a, group_b)
        return ff, state

    def run_with_fail_fast(
        self,
        raw_input: str,
        consciousnesses: Sequence[Consciousness],
        hypothesis: Hypothesis,
    ) -> tuple[FailFastResult, CognitiveState | None]:
        """Backward-compatible single-hypothesis entry point."""
        return self.run_with_hypotheses(raw_input, consciousnesses, [hypothesis])
