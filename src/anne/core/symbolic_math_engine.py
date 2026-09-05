"""Small deterministic symbolic-math backend for auditable derivations."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class SymbolicEquation:
    lhs: sp.Expr
    rhs: sp.Expr


class SymbolicMathEngine:
    """Parse, transform, normalize, and independently verify symbolic relations."""

    def parse_equation(self, text: str) -> SymbolicEquation:
        left, separator, right = text.partition("=")
        if not separator:
            raise ValueError(f"Equation must contain '=': {text!r}")
        return SymbolicEquation(sp.sympify(left.strip()), sp.sympify(right.strip()))

    def equation_expression(self, equation: SymbolicEquation) -> sp.Expr:
        return sp.expand(equation.lhs - equation.rhs)

    def isolate(self, equation: SymbolicEquation, variable: str) -> sp.Expr:
        symbol = sp.Symbol(variable)
        solutions = sp.solve(self.equation_expression(equation), symbol)
        if len(solutions) != 1:
            raise ValueError(f"Could not uniquely isolate {variable!r}: {equation}")
        return sp.simplify(solutions[0])

    def substitute(self, equation: SymbolicEquation, variable: str, value: sp.Expr) -> sp.Expr:
        symbol = sp.Symbol(variable)
        return sp.expand(equation.lhs.subs(symbol, value) - equation.rhs.subs(symbol, value))

    def simplify_relation(self, expression: sp.Expr) -> sp.Expr:
        return sp.factor(sp.cancel(sp.expand(expression)))

    def verify_identity(self, left: sp.Expr | str, right: sp.Expr | str) -> bool:
        left_expr = sp.sympify(left)
        right_expr = sp.sympify(right)
        return sp.simplify(left_expr - right_expr) == 0
