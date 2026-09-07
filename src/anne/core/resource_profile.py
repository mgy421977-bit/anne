"""Substrate-aware resource budgeting for ANNE.

ANNE's cognitive invariants are substrate-independent. This module only
controls how much bounded computation the host can afford. It does not
change safety, semantic, provenance, or agency policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Substrate(StrEnum):
    """Execution substrate category, intentionally descriptive rather than predictive."""

    CLASSICAL = "classical"
    QUANTUM = "quantum"
    BIO_QUANTUM = "bio_quantum"


@dataclass(frozen=True)
class ResourceProfile:
    """Bounded runtime resources available to one ANNE cognitive cycle."""

    substrate: Substrate = Substrate.CLASSICAL
    cpu_units: int = 1
    memory_units: int = 1
    reasoning_budget: int = 1
    max_mitos_candidates: int = 2
    max_fractal_depth: int = 1
    max_iterations: int = 4

    def __post_init__(self) -> None:
        values = (
            self.cpu_units,
            self.memory_units,
            self.reasoning_budget,
            self.max_mitos_candidates,
            self.max_fractal_depth,
            self.max_iterations,
        )
        if any(value < 1 for value in values):
            raise ValueError("resource limits must be positive")

    @classmethod
    def minimal(
        cls, substrate: Substrate = Substrate.CLASSICAL
    ) -> ResourceProfile:
        """Return the smallest useful bounded profile."""
        return cls(substrate=substrate)

    @classmethod
    def scaled(
        cls,
        *,
        substrate: Substrate = Substrate.CLASSICAL,
        capacity: int = 1,
    ) -> ResourceProfile:
        """Scale bounded exploration without changing cognitive invariants.

        Capacity is an abstract host budget, not a benchmark score and not a
        claim about the capabilities of quantum or biological hardware.
        """
        if capacity < 1:
            raise ValueError("capacity must be positive")
        return cls(
            substrate=substrate,
            cpu_units=capacity,
            memory_units=capacity,
            reasoning_budget=capacity,
            max_mitos_candidates=min(2 * capacity, 32),
            max_fractal_depth=min(1 + capacity // 2, 8),
            max_iterations=min(4 * capacity, 32),
        )
