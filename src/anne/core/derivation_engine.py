"""Inspectable derivation trace built on the symbolic math backend."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from anne.core.symbolic_math_engine import SymbolicMathEngine


@dataclass(frozen=True)
class DerivationStep:
    operation: str
    expression: str
    note: str


@dataclass(frozen=True)
class DerivationResult:
    steps: tuple[DerivationStep, ...]
    result: sp.Expr
    verified: bool = False


class DerivationEngine:
    """Produce a deterministic, auditable derivation from source equations."""

    def __init__(self, math: SymbolicMathEngine | None = None) -> None:
        self.math = math or SymbolicMathEngine()

    def derive_elimination(self, equations: tuple[str, str], variable: str) -> DerivationResult:
        first = self.math.parse_equation(equations[0])
        second = self.math.parse_equation(equations[1])
        isolated = self.math.isolate(first, variable)
        substituted = self.math.substitute(second, variable, isolated)
        expanded = sp.expand(substituted)
        simplified = self.math.simplify_relation(expanded)
        steps = (
            DerivationStep("parse", "; ".join(equations), "Parsed source equations."),
            DerivationStep("identify_elimination_variable", variable, "Variable occurs in both equations."),
            DerivationStep("isolate", f"{variable} = {sp.sstr(isolated)}", f"Isolated {variable} from the first equation."),
            DerivationStep("substitute", sp.sstr(substituted), f"Substituted {variable} into the second equation."),
            DerivationStep("expand", sp.sstr(expanded), "Expanded the substituted expression."),
            DerivationStep("simplify", sp.sstr(simplified), "Normalized the algebraic relation."),
        )
        return DerivationResult(steps=steps, result=simplified)

    def verify(self, result: DerivationResult, oracle: sp.Expr | str) -> DerivationResult:
        verified = self.math.verify_identity(result.result, oracle)
        return DerivationResult(steps=result.steps, result=result.result, verified=verified)
