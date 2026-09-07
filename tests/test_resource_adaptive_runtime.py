from __future__ import annotations

from anne.core.cognitive_orchestrator import CognitiveOrchestrator
from anne.core.decision_loop import DecisionLoop
from anne.core.fractal_loop import FractalBudget, FractalThinkingLoop
from anne.core.pipeline import AnnePipeline
from anne.core.resource_profile import ResourceProfile, Substrate
from anne.memory.fractal_memory import FractalMemory


def test_decision_loop_defaults_to_minimal_profile() -> None:
    loop = DecisionLoop()
    assert loop.resource_profile == ResourceProfile.minimal()
    assert loop.orchestrator.candidate_batch_size == 2


def test_orchestrator_cannot_exceed_profile_candidate_budget() -> None:
    memory = FractalMemory(":memory:")
    profile = ResourceProfile.scaled(capacity=2)
    orchestrator = CognitiveOrchestrator(
        AnnePipeline(memory=memory),
        resource_profile=profile,
        candidate_batch_size=100,
    )
    assert orchestrator.candidate_batch_size == profile.max_mitos_candidates


def test_fractal_loop_uses_profile_budget_by_default() -> None:
    memory = FractalMemory(":memory:")
    profile = ResourceProfile.scaled(capacity=4)
    loop = FractalThinkingLoop(memory, resource_profile=profile)
    assert loop.budget.max_depth == profile.max_fractal_depth
    assert loop.budget.max_iterations == profile.max_iterations


def test_explicit_fractal_budget_remains_a_bounded_override() -> None:
    memory = FractalMemory(":memory:")
    profile = ResourceProfile.scaled(capacity=4)
    loop = FractalThinkingLoop(
        memory,
        budget=FractalBudget(max_depth=1, max_iterations=2),
        resource_profile=profile,
    )
    assert loop.budget.max_depth == 1
    assert loop.budget.max_iterations == 2


def test_substrate_label_does_not_change_safety_configuration() -> None:
    classical = ResourceProfile.minimal(Substrate.CLASSICAL)
    quantum = ResourceProfile.minimal(Substrate.QUANTUM)
    assert classical.cpu_units == quantum.cpu_units == 1
    assert classical.reasoning_budget == quantum.reasoning_budget == 1
    assert classical.max_mitos_candidates == quantum.max_mitos_candidates == 2
    assert classical.max_fractal_depth == quantum.max_fractal_depth == 1
    assert classical.max_iterations == quantum.max_iterations == 4
