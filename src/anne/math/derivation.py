"""Traceable derivation engine — wires SymbolicMathEngine into an audit trail."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import sympy as sp

from anne.math.symbolic import EliminationResult, SymbolicMathEngine


@dataclass(frozen=True)
class DerivationStep:
    index: int
    expression: str
    operation: str
    justification: str


@dataclass
class DerivationResult:
    goal: str
    steps: list[DerivationStep] = field(default_factory=list)
    conclusion: str = ""
    relation: sp.Equality | None = None
    valid: bool = True

    def add(self, expression: str, operation: str, justification: str) -> None:
        self.steps.append(
            DerivationStep(len(self.steps) + 1, expression, operation, justification)
        )


class SymbolicDerivationEngine:
    """Produces an inspectable derivation via SymbolicMathEngine elimination."""

    def __init__(self, symbolic: SymbolicMathEngine | None = None) -> None:
        self.symbolic = symbolic or SymbolicMathEngine()

    def derive_elimination(
        self,
        equations: list[str],
        variable: str,
        goal: str = "",
    ) -> DerivationResult:
        elim: EliminationResult = self.symbolic.eliminate(equations, variable)
        result = DerivationResult(
            goal=goal or f"eliminate {variable}",
            conclusion=str(elim.relation),
            relation=elim.relation,
        )
        for step in elim.steps:
            result.add(step.expression, step.operation, step.reason)
        return result

    def derive(
        self,
        goal: str,
        steps: list[tuple[str, str, str]],
        conclusion: str,
    ) -> DerivationResult:
        result = DerivationResult(goal=goal, conclusion=conclusion)
        for expression, operation, justification in steps:
            result.add(expression, operation, justification)
        return result

    def verify_chain(
        self, result: DerivationResult, checker: Callable[[DerivationStep], bool]
    ) -> bool:
        result.valid = all(checker(step) for step in result.steps)
        return result.valid


__all__ = ["DerivationStep", "DerivationResult", "SymbolicDerivationEngine"]
