from __future__ import annotations

from dataclasses import dataclass

import pytest

from anne.compute import ComputeBackend, ComputeGovernor, ComputeRequest, ComputeResult, EnergyBudget


@dataclass
class FakeExecutor:
    backend: ComputeBackend
    energy: float | None = None

    def execute(self, request: ComputeRequest) -> ComputeResult:
        return ComputeResult(
            backend=self.backend,
            output=f"{self.backend.value}:{request.task}",
            compute_units=0.5,
            latency_seconds=0.1,
            energy_joules=self.energy,
            quality_score=0.9,
        )


def test_governor_uses_requested_backend() -> None:
    governor = ComputeGovernor()
    governor.register(FakeExecutor(ComputeBackend.CPU, energy=2.0))
    governor.register(FakeExecutor(ComputeBackend.GPU, energy=4.0))
    result = governor.execute(ComputeRequest("reason", backend=ComputeBackend.GPU))
    assert result.backend is ComputeBackend.GPU


def test_governor_does_not_assume_quantum_is_cheaper() -> None:
    governor = ComputeGovernor()
    governor.register(FakeExecutor(ComputeBackend.QUANTUM, energy=20.0))
    result = governor.execute(ComputeRequest("simulate", backend=ComputeBackend.QUANTUM))
    assert result.energy_joules == 20.0


def test_energy_budget_is_enforced_when_telemetry_exists() -> None:
    governor = ComputeGovernor(energy_budget=EnergyBudget(max_joules=5.0))
    governor.register(FakeExecutor(ComputeBackend.CPU, energy=6.0))
    with pytest.raises(RuntimeError, match="energy budget"):
        governor.execute(ComputeRequest("reason"))


def test_missing_energy_telemetry_does_not_create_a_fake_value() -> None:
    governor = ComputeGovernor(energy_budget=EnergyBudget(max_joules=5.0))
    governor.register(FakeExecutor(ComputeBackend.CPU, energy=None))
    result = governor.execute(ComputeRequest("reason"))
    assert result.energy_joules is None


def test_negative_budget_is_rejected() -> None:
    with pytest.raises(ValueError):
        ComputeRequest("reason", max_compute_units=-1).validate()
