"""Bounded Fractal Thinking Loop for Phase 1a.

Frame → branch → reframe is an orchestration pattern, not an unrestricted
recursive agent. Every branch re-enters the existing FailFast/ANLA/ethical path.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.gap_fill import GapFiller
from anne.core.pipeline import AnnePipeline
from anne.core.resource_profile import ResourceProfile
from anne.memory.fractal_memory import FractalMemory
from anne.mythos.candidate import TaskMode
from anne.mythos.generate import generate_candidates
from anne.mythos.selection import CandidateSelector


@dataclass(frozen=True)
class FractalBudget:
    max_depth: int = 3
    max_iterations: int = 8


@dataclass
class FractalNode:
    cycle_id: str
    parent_cycle_id: str | None
    depth: int
    scale_role: str
    question: str
    claim: str
    status: str = "started"
    stage_reached: str = "FRAME"
    gap_detected: bool = False
    confidence: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class FractalResult:
    status: str
    answer: str
    root_cycle_id: str
    selected_claim: str
    confidence: float
    nodes: list[FractalNode]
    iterations: int
    stop_reason: str


class FractalThinkingLoop:
    """Provider-agnostic bounded recursive controller."""

    def __init__(
        self,
        memory: FractalMemory,
        pipeline: AnnePipeline | None = None,
        *,
        budget: FractalBudget | None = None,
        selector: CandidateSelector | None = None,
        gap_filler: GapFiller | None = None,
        resource_profile: ResourceProfile | None = None,
    ) -> None:
        self.memory = memory
        self.pipeline = pipeline or AnnePipeline(memory=memory)
        self.resource_profile = resource_profile or ResourceProfile.minimal()
        profile_budget = FractalBudget(
            max_depth=self.resource_profile.max_fractal_depth,
            max_iterations=self.resource_profile.max_iterations,
        )
        self.budget = budget or profile_budget
        self.selector = selector or CandidateSelector()
        self.gap_filler = gap_filler or GapFiller()

    @staticmethod
    def _gap(text: str) -> bool:
        markers = (
            "unknown",
            "uncertain",
            "unclear",
            "missing",
            "unresolved",
            "contradiction",
            "gap",
            "bilinmiyor",
            "belirsiz",
            "çelişki",
            "eksik",
            "kanıt yok",
        )
        lowered = text.lower()
        return any(marker in lowered for marker in markers)

    def _record(self, node: FractalNode, task_mode: TaskMode) -> None:
        self.memory.save_scale_event(
            cycle_id=node.cycle_id,
            parent_cycle_id=node.parent_cycle_id,
            depth=node.depth,
            scale_role=node.scale_role,
            task_mode=task_mode.value,
            question=node.question,
            selected_claim=node.claim,
            status=node.status,
            stage_reached=node.stage_reached,
        )

    def _failure(self, node: FractalNode, reason: str, task_mode: TaskMode) -> None:
        self.memory.save_failure_trace(
            cycle_id=node.cycle_id,
            stage=node.stage_reached,
            raw_input=node.question,
            reason=reason,
            meta_tag="fractal_loop",
            hypothesis_id=node.metadata.get("hypothesis_id", ""),
            depth=node.depth,
            parent_cycle_id=node.parent_cycle_id,
            task_mode=task_mode.value,
            scale_role=node.scale_role,
        )

    def run(
        self,
        question: str,
        hypothesis: Hypothesis,
        *,
        parties: Sequence[Consciousness] | None = None,
        task_mode: TaskMode = TaskMode.GENERAL,
    ) -> FractalResult:
        people = list(parties) if parties else [Consciousness(id="user")]
        root_id = f"fc_{uuid4().hex[:12]}"
        root = FractalNode(
            root_id,
            None,
            0,
            "frame",
            question,
            hypothesis.claim,
            metadata={"hypothesis_id": hypothesis.id},
        )
        nodes = [root]
        self._record(root, task_mode)
        current_question, current = question, hypothesis
        last_answer = current.claim
        iterations = 0

        while iterations < self.budget.max_iterations:
            iterations += 1
            node = (
                root
                if iterations == 1
                else FractalNode(
                    f"fc_{uuid4().hex[:12]}",
                    nodes[-1].cycle_id,
                    min(nodes[-1].depth + 1, self.budget.max_depth),
                    "branch",
                    current_question,
                    current.claim,
                    metadata={"hypothesis_id": current.id},
                )
            )
            if node is not root:
                nodes.append(node)
                self._record(node, task_mode)

            ff, state = self.pipeline.run_with_fail_fast(
                current_question, people, current
            )
            if not ff.passed:
                node.status = "failed"
                node.stage_reached = "FAIL_FAST"
                self._record(node, task_mode)
                self._failure(node, ff.reason, task_mode)
                return FractalResult(
                    "aborted",
                    "",
                    root_id,
                    current.claim,
                    0.0,
                    nodes,
                    iterations,
                    "fail_fast",
                )
            assert state is not None
            node.stage_reached = "YAP"
            node.confidence = float(
                state.context_map.get("anla_score") or current.probability
            )
            last_answer = str(
                state.output.get("reasoning")
                or state.output.get("hypothesis")
                or current.claim
            )
            node.gap_detected = (
                self._gap(current_question + " " + current.claim)
                or not state.logic_valid
            )
            if state.logic_valid and not node.gap_detected:
                node.status = "integrated"
                self._record(node, task_mode)
                return FractalResult(
                    "completed",
                    last_answer,
                    root_id,
                    current.claim,
                    node.confidence,
                    nodes,
                    iterations,
                    "validated",
                )

            if node.depth >= self.budget.max_depth:
                node.status = "stopped"
                node.stage_reached = "REFRAME"
                self._record(node, task_mode)
                self._failure(
                    node,
                    "fractal_depth_budget_exhausted",
                    task_mode,
                )
                return FractalResult(
                    "bounded",
                    last_answer,
                    root_id,
                    current.claim,
                    node.confidence,
                    nodes,
                    iterations,
                    "max_depth",
                )

            # Memory relations are priors, not truth. The gap filler requires
            # sufficient agreement before a reframe is allowed.
            relations = self.memory.get_similar_decisions(current_question, limit=5)
            rules = self.memory.get_strong_rules(limit=5)
            _ = self.gap_filler.assess(
                relations,
                rules,
                low_score=state.priority_score,
                high_score=max((float(r[1]) for r in rules), default=0.0),
            )
            candidates = generate_candidates(
                current_question,
                batch_size=min(3, self.resource_profile.max_mitos_candidates),
            )
            selection = self.selector.select(candidates, task_mode=task_mode)
            if not selection.accepted or selection.candidate is None:
                node.status = "abstained"
                node.stage_reached = "GAP"
                self._record(node, task_mode)
                self._failure(node, "gap_fill_abstain", task_mode)
                return FractalResult(
                    "bounded",
                    last_answer,
                    root_id,
                    current.claim,
                    node.confidence,
                    nodes,
                    iterations,
                    "abstain",
                )

            selected = selection.candidate
            reframe = FractalNode(
                f"fc_{uuid4().hex[:12]}",
                node.cycle_id,
                node.depth + 1,
                "reframe",
                current_question,
                selected.claim,
                confidence=selection.score,
                stage_reached="REFRAME",
                metadata={"hypothesis_id": selected.id},
            )
            nodes.append(reframe)
            self._record(reframe, task_mode)
            current = Hypothesis(
                id=selected.id,
                topic=selected.goal[:48],
                claim=selected.claim,
                probability=selected.probability,
                source="MITOS",
            )
            current_question = selected.goal
            reframe.status = "integrated"
            reframe.stage_reached = "INTEGRATE"
            self._record(reframe, task_mode)

        self._failure(
            nodes[-1],
            "fractal_iteration_budget_exhausted",
            task_mode,
        )
        nodes[-1].status = "stopped"
        nodes[-1].stage_reached = "STOP"
        self._record(nodes[-1], task_mode)
        return FractalResult(
            "bounded",
            last_answer,
            root_id,
            current.claim,
            nodes[-1].confidence,
            nodes,
            iterations,
            "max_iterations",
        )


__all__ = ["FractalBudget", "FractalNode", "FractalResult", "FractalThinkingLoop"]
