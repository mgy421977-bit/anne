"""Phase 1a executive orchestration.

Flow: FailFast → DUY → BAK → GÖR → MITOS → SELECT → ANLA → HİSSET → YAP.
MITOS proposes; ANNE selects. Existing safety and semantic gates remain in path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import uuid4

from anne.core.cognitive_state import CognitiveState, Consciousness, Hypothesis
from anne.core.fail_fast import FailFastResult
from anne.core.pipeline import AnnePipeline
from anne.core.resource_profile import ResourceProfile
from anne.mythos.candidate import SelectionResult, TaskMode
from anne.mythos.generate import generate_candidates
from anne.mythos.selection import CandidateSelector


@dataclass(frozen=True)
class OrchestrationResult:
    status: str
    fail_fast: FailFastResult
    state: CognitiveState | None
    selection: SelectionResult | None
    stage_trace: tuple[str, ...]
    reason: str = ""


class CognitiveOrchestrator:
    """Single executive path for Phase 1a cognitive cycles."""

    def __init__(
        self,
        pipeline: AnnePipeline,
        *,
        selector: CandidateSelector | None = None,
        candidate_batch_size: int | None = None,
        resource_profile: ResourceProfile | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.selector = selector or CandidateSelector()
        self.resource_profile = resource_profile or ResourceProfile.minimal()
        self.candidate_batch_size = min(
            candidate_batch_size or self.resource_profile.max_mitos_candidates,
            self.resource_profile.max_mitos_candidates,
        )

    def run(
        self,
        raw_input: str,
        *,
        parties: Sequence[Consciousness] | None = None,
        task_mode: TaskMode = TaskMode.GENERAL,
        seed: int | None = None,
    ) -> OrchestrationResult:
        stage_trace: list[str] = ["FAIL_FAST"]
        people = list(parties) if parties else [Consciousness(id="user")]
        ff = self.pipeline.fail_fast(raw_input)
        if not ff.passed:
            return OrchestrationResult("ABORTED", ff, None, None, tuple(stage_trace), ff.reason)

        stage_trace.append("DUY")
        state = self.pipeline.duy(raw_input, people)
        stage_trace.append("BAK")
        state = self.pipeline.bak(state)
        stage_trace.append("GÖR")
        goal = raw_input.strip()
        if not goal:
            return OrchestrationResult("ABORTED", ff, state, None, tuple(stage_trace), "empty_input")

        stage_trace.append("MITOS")
        from anne.mythos.engine import MitosEngine
        engine = MitosEngine(seed=seed)
        candidates = generate_candidates(goal, batch_size=self.candidate_batch_size, engine=engine)
        stage_trace.append("SELECT")
        selection = self.selector.select(candidates, task_mode=task_mode)
        if not selection.accepted or selection.candidate is None:
            self.pipeline.memory.save_failure_trace(
                cycle_id=f"or_{uuid4().hex[:12]}",
                stage="SELECT",
                raw_input=raw_input,
                reason=selection.reason,
                meta_tag="mitos_selection_reject",
                task_mode=task_mode.value,
                scale_role="frame",
            )
            return OrchestrationResult("BOUNDED", ff, state, selection, tuple(stage_trace), selection.reason)

        selected = selection.candidate
        hypothesis = Hypothesis(
            id=selected.id,
            topic=selected.goal[:48],
            claim=selected.claim,
            probability=selected.probability,
            source="MITOS",
        )
        state = self.pipeline.gor(state, [hypothesis])
        stage_trace.append("ANLA")
        state = self.pipeline.anla(state, hypothesis)
        if state.logic_valid or state.ethic_score is not None:
            stage_trace.append("HİSSET")
            state = self.pipeline.hisset(state)
        stage_trace.append("YAP")
        state = self.pipeline.yap(state, hypothesis)
        status = "EXECUTED" if state.action != "HALT" else "ABORTED"
        return OrchestrationResult(status, ff, state, selection, tuple(stage_trace), "")


__all__ = ["CognitiveOrchestrator", "OrchestrationResult"]
