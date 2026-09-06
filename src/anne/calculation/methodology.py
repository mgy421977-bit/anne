"""Versioned calculation methods with explicit assumptions and provenance."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class CalculationResult:
    value: float
    method_id: str
    method_version: str
    assumptions: dict[str, float | str]
    sources: tuple[str, ...] = ()


@dataclass
class CalculationMethod:
    method_id: str
    version: str
    formula: Callable[[dict[str, float]], float]
    assumptions: dict[str, float | str] = field(default_factory=dict)
    sources: tuple[str, ...] = ()

    def calculate(self, inputs: dict[str, float]) -> CalculationResult:
        return CalculationResult(
            value=float(self.formula(inputs)),
            method_id=self.method_id,
            method_version=self.version,
            assumptions=dict(self.assumptions),
            sources=self.sources,
        )

    def compare(self, inputs: dict[str, float], expected: float) -> float:
        """Return absolute error for backtesting; lower is better."""
        return abs(self.calculate(inputs).value - expected)
