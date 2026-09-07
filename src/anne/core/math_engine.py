"""Deterministic numerical math backend for ANNE."""

from __future__ import annotations

import math


class MathEngine:
    """Provide small, explicit numerical operations used by reasoning components."""

    def add(self, left: float, right: float) -> float:
        return left + right

    def subtract(self, left: float, right: float) -> float:
        return left - right

    def multiply(self, left: float, right: float) -> float:
        return left * right

    def divide(self, left: float, right: float) -> float:
        if right == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return left / right

    def power(self, base: float, exponent: float) -> float:
        return math.pow(base, exponent)

    def sqrt(self, value: float) -> float:
        if value < 0:
            raise ValueError("Square root requires a non-negative value")
        return math.sqrt(value)
