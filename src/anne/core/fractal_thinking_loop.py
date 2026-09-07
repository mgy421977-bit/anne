"""Bounded recursive Fractal Thinking Loop (FTL).

FTL adds an explicit multi-scale orchestration layer around the existing
six-stage cognitive pipeline. It does not replace ANLA, HİSSET, YAP, or the
agency gate. A gap may trigger a relation scan and candidate generation;
validated results are integrated back into the parent frame.

The implementation is deliberately provider-agnostic. Applications may supply
semantic gap detection, relation scanning, candidate generation, and
validation callbacks. The default relation scanner uses persisted memory only;
it never invents an external fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence
from uuid import uuid4

from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.pipeline import AnnePipeline
from anne.memory.fractal_memory import FractalMemory


@dataclass(frozen=True)
class FractalBudget:
    """Hard bounds preventing unbounded recursive cognition."""

    max_depth: int = 3
    max_iterations: int = 8


@dataclass
class FractalNode:
    """Traceable result of one FTL scale."""

    cycle_id: str
    parent_cycle_id: str | None
    depth: int
    scale_role: str
    question: str
    claim: str = ""
    status: str = "started"
    stage_reached: str = ""
    gap_detected: bool = False
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FractalResult:
    """Normalized FTL result with the complete scale trace."""

    status: str
    answer: str
    root_cycle_id: str
    selected_claim: str = ""
    confidence: float = 0.0
    nodes: list[FractalNode] = field(default_factory=list)
    iterations: int = 0
    stop_reason: str = ""


GapDetector = Callable[[str, Hypothesis, FractalNode], bool]
RelationScanner = Callable[[str, FractalNode, FractalMemory], Sequence[Any]]
CandidateGenerator = Callable[[str, Sequence[Any], FractalNode], Sequence[Hypothesis]]
Validator = Callable[[Hypothesis, Sequence[Any], FractalNode], tuple[bool, float, str]]
Integrator = Callable[[str, Hypothesis, FractalNode], str]


def _default_gap_detector(question: str, hypothesis: Hypothesis, node: FractalNode) -> bool:
    """Conservative gap detector based on explicit uncertainty markers.

    Low prior confidence alone is not treated as a hallucination. A recursive
    search is requested only when the input or hypothesis explicitly signals
    uncertainty, incompleteness, contradiction, or an unresolved relation.
    """
    text = f"{question} {hypothesis.claim}".lower()
    markers = (
        "unknown", "uncertain", "unclear", "missing", "unresolved",
        "contradiction", "gap", "bilinmiyor", "belirsiz", "çelişki",
        "eksik", "kanıt yok",
    )
    return any(marker in text for marker in markers)


def _default_relation_scanner(question: str, node: FractalNode, memory: FractalMemory) -> Sequence[Any]:
    """Return persisted relationships relevant to the current scale."""
    relations: list[Any] = []
    relations.extend(memory.get_similar_decisions(question, limit=5))
    relations.extend(memory.get_strong_rules(limit=5))
    return relations


def _default_candidate_generator(
    question: str, relations: Sequence[Any], node: FractalNode
) -> Sequence[Hypothesis]:
    """Convert persisted relation records into non-authoritative candidates."""
    candidates: list[Hypothesis] = []
    for index, relation in enumerate(relations[:5]):
        claim = str(relation[2] if len(relation) > 2 else relation[0])
        candidates.append(
            Hypothesis(
                id=f"fh_{uuid4().hex[:12]}",
                topic=question[:48],
                claim=claim,
                probability=0.5 - min(index * 0.05, 0.2),
                source="fractal_memory_relation",
            )
        )
    return candidates


def _default_validator(
    hypothesis: Hypothesis, relations: Sequence[Any], node: FractalNode
) -> tuple[bool, float, str]:
    """Validate candidates conservatively against available relation evidence."""
    if not hypothesis.claim.strip():
        return False, 0.0, "empty_candidate"
    evidence_score = min(0.85, 0.55 + 0.05 * min(len(relations), 6))
    return True, evidence_score, "memory_relation_candidate"


def _default_integrator(parent_question: str, hypothesis: Hypothesis, node: FractalNode) -> str:
    return hypothesis.claim


class FractalCognitiveLoop:
    """Bounded recursive scale controller for ANNE's cognitive pipeline."""

    def __init__(
        self,
        memory: FractalMemory,
        pipeline: AnnePipeline | None = None,
        *,
        budget: FractalBudget | None = None,
        gap_detector: GapDetector | None = None,
        relation_scanner: RelationScanner | None = None,
        candidate_generator: CandidateGenerator | None = None,
        validator: Validator | None = None,
        integrator: Integrator | None = None,
    ) -> None:
        self.memory = memory
        self.pipeline = pipeline or AnnePipeline(memory=memory)
        self.budget = budget or FractalBudget()
        self.gap_detector = gap_detector or _default_gap_detector
        self.relation_scanner = relation_scanner or _default_relation_scanner
        self.candidate_generator = candidate_generator or _default_candidate_generator
        self.validator = validator or _default_validator
        self.integrator = integrator or _default_integrator

    def _record(
        self,
        node: FractalNode,
        *,
        selected_claim: str | None = None,
        status: str | None = None,
        stage_reached: str | None = None,
    ) -> None:
        if selected_claim is not None:
            node.claim = selected_claim
        if status is not None:
            node.status = status
        if stage_reached is not None:
            node.stage_reached = stage_reached
        self.memory.save_scale_event(
            cycle_id=node.cycle_id,
            parent_cycle_id=node.parent_cycle_id,
            depth=node.depth,
            scale_role=node.scale_role,
            task_mode=str(node.metadata.get("task_mode", "general")),
            question=node.question,
            selected_claim=node.claim,
            status=node.status,
            stage_reached=node.stage_reached,
        )

    def _failure(self, node: FractalNode, reason: str, stage: str = "FTL") -> None:
        self.memory.save_failure_trace(
            cycle_id=node.cycle_id,
            stage=stage,
            raw_input=node.question,
            reason=reason,
            meta_tag="fractal_loop",
            hypothesis_id=node.metadata.get("hypothesis_id", ""),
            depth=node.depth,
            parent_cycle_id=node.parent_cycle_id,
            task_mode=str(node.metadata.get("task_mode", "general")),
            scale_role=node.scale_role,
        )

    def run(
        self,
        question: str,
        hypothesis: Hypothesis,
        consciousnesses: Sequence[Consciousness] | None = None,
        *,
        task_mode: str = "general",
    ) -> FractalResult:
        """Run frame → branch → gap/reframe → validation → integration."""
        parties = list(consciousnesses) if consciousnesses else [Consciousness(id="user")]
        root_id = f"fc_{uuid4().hex[:12]}"
        root = FractalNode(
            cycle_id=root_id,
            parent_cycle_id=None,
            depth=0,
            scale_role="frame",
            question=question,
            claim=hypothesis.claim,
            metadata={"task_mode": task_mode, "hypothesis_id": hypothesis.id},
        )
        nodes: list[FractalNode] = [root]
        self._record(root, status="started", stage_reached="FRAME")

        current_question = question
        current_hypothesis = hypothesis
        iterations = 0
        last_answer = ""

        while iterations < self.budget.max_iterations:
            iterations += 1
            node = root if iterations == 1 else FractalNode(
                cycle_id=f"fc_{uuid4().hex[:12]}",
                parent_cycle_id=nodes[-1].cycle_id,
                depth=min(nodes[-1].depth + 1, self.budget.max_depth),
                scale_role="branch",
                question=current_question,
                claim=current_hypothesis.claim,
                metadata={"task_mode": task_mode, "hypothesis_id": current_hypothesis.id},
            )
            if node is not root:
                nodes.append(node)
                self._record(node, status="started", stage_reached="BRANCH")

            ff, state = self.pipeline.run_with_fail_fast(current_question, parties, current_hypothesis)
            if not ff.passed:
                self._failure(node, ff.reason, stage="FAIL_FAST")
                self._record(node, status="failed", stage_reached="FAIL_FAST")
                return FractalResult("aborted", "", root_id, current_hypothesis.claim, 0.0, nodes, iterations, "fail_fast")

            assert state is not None
            last_answer = str(state.output.get("reasoning") or state.output.get("hypothesis") or current_hypothesis.claim)
            node.confidence = float(state.context_map.get("anla_score") or current_hypothesis.probability)
            self._record(node, status="validated" if state.logic_valid else "rejected", stage_reached="ANLA")

            gap = self.gap_detector(current_question, current_hypothesis, node)
            node.gap_detected = gap
            if not gap and state.logic_valid:
                self._record(node, status="integrated", stage_reached="YAP")
                return FractalResult("completed", last_answer, root_id, current_hypothesis.claim, node.confidence, nodes, iterations, "validated")

            if node.depth >= self.budget.max_depth:
                self._failure(node, "fractal_depth_budget_exhausted")
                self._record(node, status="stopped", stage_reached="REFRAME")
                return FractalResult("bounded", last_answer, root_id, current_hypothesis.claim, node.confidence, nodes, iterations, "max_depth")

            relations = list(self.relation_scanner(current_question, node, self.memory))
            candidates = list(self.candidate_generator(current_question, relations, node))
            if not candidates:
                self._failure(node, "gap_detected_without_candidate")
                self._record(node, status="stopped", stage_reached="GAP")
                return FractalResult("bounded", last_answer, root_id, current_hypothesis.claim, node.confidence, nodes, iterations, "no_candidate")

            best: tuple[Hypothesis, float, str] | None = None
            for candidate in candidates:
                ok, score, reason = self.validator(candidate, relations, node)
                if ok and (best is None or score > best[1]):
                    best = (candidate, score, reason)
            if best is None:
                self._failure(node, "all_gap_candidates_rejected")
                self._record(node, status="rejected", stage_reached="VALIDATE")
                return FractalResult("bounded", last_answer, root_id, current_hypothesis.claim, node.confidence, nodes, iterations, "candidate_rejected")

            selected, score, reason = best
            reframe = FractalNode(
                cycle_id=f"fc_{uuid4().hex[:12]}",
                parent_cycle_id=node.cycle_id,
                depth=node.depth + 1,
                scale_role="reframe",
                question=current_question,
                claim=selected.claim,
                confidence=score,
                metadata={"task_mode": task_mode, "validation_reason": reason, "hypothesis_id": selected.id},
            )
            nodes.append(reframe)
            self._record(reframe, status="validated", stage_reached="VALIDATE")

            integrated = self.integrator(current_question, selected, reframe)
            self._record(reframe, selected_claim=integrated, status="integrated", stage_reached="INTEGRATE")
            current_hypothesis = selected
            current_question = integrated

        self._failure(nodes[-1], "fractal_iteration_budget_exhausted")
        self._record(nodes[-1], status="stopped", stage_reached="STOP")
        return FractalResult("bounded", last_answer, root_id, current_hypothesis.claim, nodes[-1].confidence, nodes, iterations, "max_iterations")
