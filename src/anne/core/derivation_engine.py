"""Inspectable derivation trace built on the symbolic math backend."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from anne.core.symbolic_math_engine import SymbolicEquation, SymbolicMathEngine


@dataclass(frozen=True)
class DerivationStep:
    operation: str
    expression: str
    note: str


@dataclass(frozen=True)
class DerivationResult:
    steps: tuple[DerivationStep, ...]
    result: sp.Expr
    verified: bool


class DerivationEngine:
    """Produce a deterministic, auditable derivation from source equations."""

    def __init__(self, math: SymbolicMathEngine | None = None) -> None:
        self.math = math or SymbolicMathEngine()

    def derive_kinematic_elimination(self) -> DerivationResult:
        first = self.math.parse_equation("v = u + a*t")
        second = self.math.parse_equation("s = u*t + (1/2)*a*t**2")
        t_value = self.math.isolate(first, "t")
        substituted = self.math.substitute(second, "t", t_value)
        simplified = self.math.simplify_relation(substituted)
        steps = (
            DerivationStep("parse", "v = u + a*t; s = u*t + (1/2)*a*t**2", "Parsed source equations."),
            DerivationStep("identify_elimination_variable", "t", "t occurs in both equations."),
            DerivationStep("isolate", "t = (v - u)/a", "Isolated t from the first equation."),
            DerivationStep("substitute", str(substituted), "Substituted t into the second equation."),
            DerivationStep("expand", str(sp.expand(substituted)), "Expanded the substituted expression."),
            DerivationStep("simplify", str(simplified), "Normalized the algebraic relation."),
        )
        return DerivationResult(steps=steps, result=simplified, verified=False)

    def verify(self, result: DerivationResult, oracle: sp.Expr | str) -> DerivationResult:
        verified = self.math.verify_identity(result.result, oracle)
        return DerivationResult(steps=result.steps, result=result.result, verified=verified)
