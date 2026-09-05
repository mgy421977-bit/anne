"""Symbolic algebra primitives used by ANNE's derivation layer."""
from __future__ import annotations

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class SymbolicStep:
    expression: str
    operation: str
    reason: str


@dataclass(frozen=True)
class EliminationResult:
    variable: str
    relation: sp.Equality
    steps: tuple[SymbolicStep, ...]


class SymbolicMathEngine:
    """Performs exact symbolic transformations; no language model is involved."""

    _DEFAULT_NAMES = ("u", "v", "a", "s", "t", "x", "y", "z", "r", "mu")

    def parse(self, equation: str) -> sp.Equality:
        if "=" not in equation:
            raise ValueError(f"Not an equation: {equation!r}")
        left, right = equation.split("=", 1)
        names = {name: sp.Symbol(name) for name in self._DEFAULT_NAMES}
        return sp.Eq(
            sp.sympify(left.strip(), locals=names),
            sp.sympify(right.strip(), locals=names),
        )

    def relations_equivalent(self, left: sp.Equality, right: sp.Equality) -> bool:
        """True if the two equations describe the same algebraic constraint."""
        try:
            a = sp.simplify(sp.expand(left.lhs - left.rhs))
            b = sp.simplify(sp.expand(right.lhs - right.rhs))
            if a == 0 and b == 0:
                return True
            if sp.simplify(a - b) == 0:
                return True
            if b != 0:
                ratio = sp.simplify(sp.together(a / b))
                if ratio is not None and ratio.is_number and ratio != 0:
                    return True
            return False
        except Exception:
            return False

    def eliminate(
        self,
        equations: list[str],
        variable: str,
        prefer_square: bool = True,
    ) -> EliminationResult:
        if len(equations) < 2:
            raise ValueError("At least two equations are required for elimination")
        parsed = [self.parse(equation) for equation in equations]
        var = sp.Symbol(variable)
        solved = sp.solve(parsed[0], var, dict=True)
        if not solved:
            raise ValueError(f"Could not isolate {variable}")
        value = solved[0][var]
        substituted = sp.simplify(parsed[1].subs(var, value))
        steps: list[SymbolicStep] = [
            SymbolicStep(str(parsed[0]), "given", "starting relation"),
            SymbolicStep(str(parsed[1]), "given", "second relation"),
            SymbolicStep(f"{variable} = {sp.sstr(value)}", "isolate", f"solve for {variable}"),
            SymbolicStep(str(substituted), "substitute", f"replace {variable}"),
        ]

        zero = sp.simplify(sp.expand(substituted.lhs - substituted.rhs))
        steps.append(SymbolicStep(f"{zero} = 0", "expand", "canonical zero form"))

        relation = self._prefer_kinematic_square(zero) if prefer_square else sp.Eq(zero, 0)
        if relation is None:
            relation = sp.Eq(zero, 0)
        steps.append(SymbolicStep(str(relation), "rearrange", "derived relation"))

        return EliminationResult(variable=variable, relation=relation, steps=tuple(steps))

    def _prefer_kinematic_square(self, zero_form: sp.Expr) -> sp.Equality | None:
        """If zero form matches classic kinematics, return v^2 = u^2 + 2 a s."""
        u, v, a, s = map(sp.Symbol, ("u", "v", "a", "s"))
        target_zero = sp.expand(u**2 - v**2 + 2 * a * s)
        z = sp.expand(zero_form)
        for scale in (1, -1, sp.Rational(1, 2), sp.Rational(-1, 2), 2, -2, a, -a):
            try:
                if sp.simplify(z - scale * target_zero) == 0:
                    return sp.Eq(v**2, u**2 + 2 * a * s)
            except Exception:
                continue
            try:
                if sp.simplify(sp.together(z / target_zero) - scale) == 0:
                    return sp.Eq(v**2, u**2 + 2 * a * s)
            except Exception:
                continue
        if z.has(v):
            solved = sp.solve(sp.Eq(z, 0), v**2)
            if solved:
                return sp.Eq(v**2, sp.simplify(solved[0]))
        return None


__all__ = ["SymbolicMathEngine", "SymbolicStep", "EliminationResult"]
