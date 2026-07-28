"""Six-stage cognitive pipeline orchestrator."""

from __future__ import annotations

from typing import Optional, Sequence

from anne.core.cognitive_state import CognitiveState, Consciousness, Hypothesis
from anne.core.ethic_core import EthicCore
from anne.memory.fractal_memory import FractalMemory


class AnnePipeline:
    """Executes DUY → BAK → GÖR → ANLA → HİSSET → YAP."""

    def __init__(self, memory: FractalMemory) -> None:
        self.memory = memory
        self.ethic = EthicCore()

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
        if not hypotheses:
            return state
        best = hypotheses[0]
        state.attention_focus = best.claim
        state.priority_score = best.probability
        lowest = hypotheses[-1]
        if lowest.probability < 0.3:
            state.low_prob_preserved.append(
                {
                    "hypothesis": lowest.claim,
                    "probability": lowest.probability,
                    "note": "Low probability – preserved",
                }
            )
        if state.related_memories:
            scores = [m[1] for m in state.related_memories if m[1]]
            if scores:
                state.priority_score = (
                    state.priority_score * 0.7 + (sum(scores) / len(scores)) * 0.3
                )
        return state

    def anla(
        self, state: CognitiveState, hypothesis: Hypothesis
    ) -> CognitiveState:
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
        empathy_map = {}
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
        score = state.ethic_score
        verdict = score.verdict if score else "UNKNOWN"

        if verdict == "AYRI_ÇÖZÜM" and group_a and group_b:
            output = {
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
            }
        else:
            output = {
                "verdict": verdict,
                "action": "HALT",
                "reasoning": score.reasoning if score else "",
                "low_prob_preserved": state.low_prob_preserved,
                "note": "Low-probability alternatives preserved.",
            }

        state.action = verdict
        state.output = output
        return state
