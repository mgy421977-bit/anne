"""Phase 1b executive orchestration with bounded recovery.

Flow: FailFast → DUY → BAK → GÖR → MITOS → SELECT → ANLA → HİSSET → YAP.
MITOS proposes; ANNE selects. Recovery can reframe a failed cycle but cannot
bypass existing safety, semantic, ethics, or agency boundaries.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import uuid4

from anne.core.cognitive_state import CognitiveState, Consciousness, Hypothesis
from anne.core.fail_fast import FailFastResult
from anne.core.failure_recovery import FailureRecoveryController, FailureSignal
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
    retry_count: int = 0
    lineage: tuple[str, ...] = ()
    stop_reason: str = ""


class CognitiveOrchestrator:
    """Single guarded executive path with optional bounded recovery."""

    def __init__(
        self,
        pipeline: AnnePipeline,
        *,
        selector: CandidateSelector | None = None,
        candidate_batch_size: int | None = None,
        resource_profile: ResourceProfile | None = None,
        max_retries: int = 1,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.pipeline = pipeline
        self.selector = selector or CandidateSelector()
        self.resource_profile = resource_profile or ResourceProfile.minimal()
        self.candidate_batch_size = min(
            candidate_batch_size or self.resource_profile.max_mitos_candidates,
            self.resource_profile.max_mitos_candidates,
        )
        self.max_retries = max_retries

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _failure_reason(state: CognitiveState) -> str:
        output = state.output or {}
        return str(
            output.get("reason")
            or output.get("reasoning")
            or "logic_or_semantic_failure"
        )

    @staticmethod
    def _is_success(state: CognitiveState) -> bool:
        return bool(state.logic_valid) and state.action != "HALT"

    def run(
        self,
        raw_input: str,
        *,
        parties: Sequence[Consciousness] | None = None,
        task_mode: TaskMode = TaskMode.GENERAL,
        seed: int | None = None,
    ) -> OrchestrationResult:
        people = list(parties) if parties else [Consciousness(id="user")]
        ff = self.pipeline.fail_fast(raw_input)
        stage_trace: list[str] = ["FAIL_FAST"]
        if not ff.passed:
            return OrchestrationResult(
                "ABORTED", ff, None, None, tuple(stage_trace), ff.reason,
                stop_reason="fail_fast",
            )

        current_question = raw_input.strip()
        if not current_question:
            state = self.pipeline.duy(raw_input, people)
            stage_trace.append("DUY")
            return OrchestrationResult(
                "ABORTED", ff, state, None, tuple(stage_trace), "empty_input",
                stop_reason="empty_input",
            )

        root_cycle_id = f"or_{uuid4().hex[:12]}"
        lineage = [root_cycle_id]
        seen_questions = {self._normalize(current_question)}
        retry_count = 0
        previous_confidence: float | None = None
        last_state: CognitiveState | None = None
        last_selection: SelectionResult | None = None
        last_reason = ""
        trace: list[str] = []

        while True:
            cycle_id = lineage[-1]
            trace.extend(["DUY", "BAK", "GÖR", "MITOS", "SELECT"])
            state = self.pipeline.duy(current_question, people)
            state = self.pipeline.bak(state)

            from anne.mythos.engine import MitosEngine

            engine_seed = None if seed is None else seed + retry_count
            engine = MitosEngine(seed=engine_seed)
            candidates = generate_candidates(
                current_question,
                batch_size=self.candidate_batch_size,
                engine=engine,
            )
            selection = self.selector.select(candidates, task_mode=task_mode)
            last_state = state
            last_selection = selection

            if not selection.accepted or selection.candidate is None:
                reason = selection.reason or "mitos_selection_reject"
                failure = FailureSignal(
                    FailureRecoveryController.classify(reason, "SELECT"),
                    reason,
                    "SELECT",
                    cycle_id,
                    retry_count,
                )
                self.pipeline.memory.save_failure_trace(
                    cycle_id=cycle_id,
                    stage="SELECT",
                    raw_input=current_question,
                    reason=reason,
                    meta_tag="executive_retry",
                    task_mode=task_mode.value,
                    scale_role="frame",
                )
                last_reason = reason
            else:
                selected = selection.candidate
                hypothesis = Hypothesis(
                    id=selected.id,
                    topic=selected.goal[:48],
                    claim=selected.claim,
                    probability=selected.probability,
                    source="MITOS",
                )
                self.pipeline.memory.save_hypothesis(
                    hypothesis, task_mode=task_mode.value,
                )
                state = self.pipeline.gor(state, [hypothesis])
                trace.extend(["ANLA", "HİSSET", "YAP"])
                state = self.pipeline.anla(state, hypothesis)
                if state.logic_valid or state.ethic_score is not None:
                    state = self.pipeline.hisset(state)
                state = self.pipeline.yap(state, hypothesis)
                last_state = state
                confidence = float(
                    state.context_map.get("anla_score") or selected.probability
                )
                if self._is_success(state):
                    if retry_count and previous_confidence is not None:
                        delta = confidence - previous_confidence
                        if delta <= 0:
                            last_reason = "post_retry_no_improvement"
                            self.pipeline.memory.save_failure_trace(
                                cycle_id=cycle_id,
                                stage="POST_RETRY_EVALUATION",
                                raw_input=current_question,
                                reason=last_reason,
                                meta_tag="executive_retry",
                                task_mode=task_mode.value,
                                scale_role="frame",
                            )
                            return OrchestrationResult(
                                "BOUNDED", ff, state, selection,
                                tuple(stage_trace + trace), last_reason,
                                retry_count=retry_count,
                                lineage=tuple(lineage),
                                stop_reason=last_reason,
                            )
                    if state.ethic_score is not None:
                        self.pipeline.memory.save_decision(
                            decision_id=f"dec_{uuid4().hex[:12]}",
                            hyp_id=hypothesis.id,
                            score=state.ethic_score,
                            consciousnesses=people,
                            stage="YAP",
                            task_mode=task_mode.value,
                        )
                    reason = str(
                        state.output.get("reason")
                        or state.output.get("reasoning")
                        or ""
                    )
                    return OrchestrationResult(
                        "EXECUTED", ff, state, selection,
                        tuple(stage_trace + trace), reason,
                        retry_count=retry_count,
                        lineage=tuple(lineage),
                        stop_reason="validated",
                    )
                last_reason = self._failure_reason(state)
                failure = FailureSignal(
                    FailureRecoveryController.classify(last_reason, "YAP"),
                    last_reason,
                    "YAP",
                    cycle_id,
                    retry_count,
                )
                self.pipeline.memory.save_failure_trace(
                    cycle_id=cycle_id,
                    stage="YAP",
                    raw_input=current_question,
                    reason=last_reason,
                    meta_tag="executive_retry",
                    hypothesis_id=hypothesis.id,
                    depth=retry_count,
                    task_mode=task_mode.value,
                    scale_role="frame",
                )
                previous_confidence = confidence

            if retry_count >= self.max_retries:
                return OrchestrationResult(
                    "BOUNDED", ff, last_state, last_selection,
                    tuple(stage_trace + trace), last_reason,
                    retry_count=retry_count,
                    lineage=tuple(lineage),
                    stop_reason="retry_budget_exhausted",
                )

            plan = FailureRecoveryController.plan(
                failure, current_question, attempt=retry_count + 1,
            )
            retry = FailureRecoveryController.authorize_retry(
                attempt=retry_count,
                max_retries=self.max_retries,
                seen_questions=seen_questions,
                question=plan.question,
            )
            if not retry.allowed:
                self.pipeline.memory.save_failure_trace(
                    cycle_id=cycle_id,
                    stage="RETRY_GATE",
                    raw_input=current_question,
                    reason=retry.reason,
                    meta_tag="executive_retry",
                    task_mode=task_mode.value,
                    scale_role="frame",
                )
                return OrchestrationResult(
                    "BOUNDED", ff, last_state, last_selection,
                    tuple(stage_trace + trace), retry.reason,
                    retry_count=retry_count,
                    lineage=tuple(lineage),
                    stop_reason=retry.reason,
                )

            retry_count = retry.next_attempt
            current_question = plan.question
            seen_questions.add(self._normalize(current_question))
            lineage.append(f"or_{uuid4().hex[:12]}")
            trace.extend(["FAILURE", "CLASSIFY", "REFRAME", "RETRY_GATE"])


__all__ = ["CognitiveOrchestrator", "OrchestrationResult"]
