"""Budget-aware compute routing for ANNE.

The governor chooses among available backends without assuming that a
particular hardware class is inherently more energy efficient. Actual energy
measurements, when available, are recorded as telemetry.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .abstraction import ComputeBackend, ComputeExecutor, ComputeRequest, ComputeResult


@dataclass(frozen=True)
class EnergyBudget:
    """Optional energy ceiling for one compute request."""

    max_joules: float | None = None

    def validate(self) -> None:
        if self.max_joules is not None and self.max_joules < 0:
            raise ValueError("energy budget cannot be negative")


@dataclass
class ComputeGovernor:
    """Selects an eligible backend using explicit resource constraints."""

    executors: dict[ComputeBackend, ComputeExecutor] = field(default_factory=dict)
    energy_budget: EnergyBudget = field(default_factory=EnergyBudget)

    def register(self, executor: ComputeExecutor) -> None:
        self.executors[executor.backend] = executor

    def choose(self, request: ComputeRequest) -> ComputeBackend:
        request.validate()
        if request.backend in self.executors:
            return request.backend
        if not self.executors:
            raise RuntimeError("no compute backend is registered")
        # Deterministic fallback. Energy is never guessed from backend names.
        return next(iter(self.executors))

    def execute(self, request: ComputeRequest) -> ComputeResult:
        backend = self.choose(request)
        result = self.executors[backend].execute(request)
        if result.latency_seconds > request.max_latency_seconds:
            raise RuntimeError("compute exceeded latency budget")
        if result.compute_units > request.max_compute_units:
            raise RuntimeError("compute exceeded compute-unit budget")
        if self.energy_budget.max_joules is not None and result.energy_joules is not None:
            if result.energy_joules > self.energy_budget.max_joules:
                raise RuntimeError("compute exceeded energy budget")
        return result
