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

    def parse(self, equation: str) -> sp.Equality:
        left, right = equation.split("=", 1)
        names = {name: sp.Symbol(name) for name in ("u", "v", "a", "s", "t", "x", "y", "z")}
        return sp.Eq(sp.sympify(left.strip(), locals=names), sp.sympify(right.strip(), locals=names))

    def eliminate(self, equations: list[str], variable: str, target: str) -> EliminationResult:
        parsed = [self.parse(equation) for equation in equations]
        var = sp.Symbol(variable)
        solved = sp.solve(parsed[0], var, dict=True)
        if not solved:
            raise ValueError(f"Could not isolate {variable}")
        value = solved[0][var]
        substituted = sp.simplify(parsed[1].subs(var, value))
        steps = [
            SymbolicStep(str(parsed[0]), "given", "starting relation"),
            SymbolicStep(f"{variable} = {sp.sstr(value)}", "isolate", f"solve for {variable}"),
            SymbolicStep(str(substituted), "substitute", f"replace {variable}"),
        ]
        expression = sp.expand(substituted.lhs - substituted.rhs)
        relation = sp.Eq(sp.expand(expression), 0)
        solved_target = sp.solve(relation, sp.Symbol(target), dict=True)
        if solved_target:
            target_value = solved_target[0][sp.Symbol(target)]
            relation = sp.Eq(sp.Symbol(target), sp.factor(target_value))
            steps.append(SymbolicStep(str(relation), "rearrange", f"isolate {target}"))
        else:
            steps.append(SymbolicStep(str(relation), "simplify", "canonical zero form"))
        return EliminationResult(variable=variable, relation=relation, steps=tuple(steps))


__all__ = ["SymbolicMathEngine", "SymbolicStep", "EliminationResult"]
