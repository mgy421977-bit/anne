"""Deterministic, model-independent numerical mathematics for ANNE."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class CalculationResult:
    expression: str
    value: float
    method: str
    valid: bool = True
    error_estimate: float | None = None


class MathEngine:
    """Small deterministic calculation kernel; natural-language parsing is separate."""

    def add(self, a: float, b: float) -> CalculationResult:
        return CalculationResult(f"{a} + {b}", a + b, "addition")

    def subtract(self, a: float, b: float) -> CalculationResult:
        return CalculationResult(f"{a} - {b}", a - b, "subtraction")

    def multiply(self, a: float, b: float) -> CalculationResult:
        return CalculationResult(f"{a} * {b}", a * b, "multiplication")

    def divide(self, a: float, b: float) -> CalculationResult:
        if b == 0:
            return CalculationResult(f"{a} / {b}", math.nan, "division", valid=False)
        return CalculationResult(f"{a} / {b}", a / b, "division")

    def power(self, a: float, b: float) -> CalculationResult:
        return CalculationResult(f"{a} ** {b}", a**b, "power")

    def sqrt(self, a: float) -> CalculationResult:
        if a < 0:
            return CalculationResult(f"sqrt({a})", math.nan, "square_root", valid=False)
        return CalculationResult(f"sqrt({a})", math.sqrt(a), "square_root")

    def derivative(self, function: Callable[[float], float], x: float, step: float = 1e-6) -> CalculationResult:
        if step <= 0:
            raise ValueError("step must be positive")
        value = (function(x + step) - function(x - step)) / (2.0 * step)
        error = abs(function(x + 2 * step) - 2 * function(x) + function(x - 2 * step)) / (8.0 * step)
        return CalculationResult("d/dx f(x)", value, "central_difference", error_estimate=error)

    def integrate(self, function: Callable[[float], float], a: float, b: float, steps: int = 1000) -> CalculationResult:
        if steps < 1:
            raise ValueError("steps must be >= 1")
        h = (b - a) / steps
        total = 0.5 * (function(a) + function(b))
        for i in range(1, steps):
            total += function(a + i * h)
        return CalculationResult(f"integral[{a},{b}] f(x)dx", total * h, "trapezoidal_rule")


__all__ = ["CalculationResult", "MathEngine"]
