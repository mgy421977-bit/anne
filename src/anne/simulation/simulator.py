"""Executable deterministic cognitive-cycle harness."""

from dataclasses import dataclass, field
from typing import Callable

from .metrics import SimulationMetrics
from .world import SimulatedWorld


@dataclass
class CognitiveSimulator:
    """Runs observe -> predict -> act -> observe -> error cycles.

    The policy is injected so the simulator can test ANNE components independently
    from any external LLM or API provider.
    """

    world: SimulatedWorld = field(default_factory=SimulatedWorld)
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    policy: Callable[[dict[str, float | int]], str] | None = None
    experiences: list[dict[str, object]] = field(default_factory=list)

    def step(self) -> dict[str, object]:
        before = self.world.observe()
        action = self.policy(before) if self.policy else "wait"
        predicted_efficiency = before["efficiency"]
        result = self.world.apply(action)
        observed_efficiency = result["efficiency"]
        self.metrics.record(float(predicted_efficiency), float(observed_efficiency))
        error = float(observed_efficiency) - float(predicted_efficiency)
        experience = {
            "before": before,
            "action": action,
            "prediction": {"efficiency": predicted_efficiency},
            "observation": result,
            "prediction_error": error,
            "learning_is_evidenced": False,
        }
        self.experiences.append(experience)
        return experience

    def run(self, cycles: int) -> list[dict[str, object]]:
        if cycles < 1:
            raise ValueError("cycles must be >= 1")
        return [self.step() for _ in range(cycles)]
