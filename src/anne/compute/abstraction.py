"""Provider-neutral compute contracts.

ANNE asks for computation; a backend decides how it is executed. This keeps
cognitive logic independent from CPU, GPU, NPU, quantum, or hybrid hardware.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ComputeBackend(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"
    QUANTUM = "quantum"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class ComputeRequest:
    """Hardware-independent description of a computation."""

    task: str
    backend: ComputeBackend = ComputeBackend.CPU
    max_compute_units: float = 1.0
    max_latency_seconds: float = 30.0
    quality_target: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.task.strip():
            raise ValueError("task is required")
        if self.max_compute_units < 0 or self.max_latency_seconds < 0:
            raise ValueError("compute and latency budgets cannot be negative")
        if not 0.0 <= self.quality_target <= 1.0:
            raise ValueError("quality_target must be between 0 and 1")


@dataclass(frozen=True)
class ComputeResult:
    """Result plus telemetry used for future routing decisions."""

    backend: ComputeBackend
    output: Any
    compute_units: float = 0.0
    latency_seconds: float = 0.0
    energy_joules: float | None = None
    quality_score: float | None = None


class ComputeExecutor(Protocol):
    """Backend contract implemented by concrete execution providers."""

    backend: ComputeBackend

    def execute(self, request: ComputeRequest) -> ComputeResult: ...
