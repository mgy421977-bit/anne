"""Traceable symbolic-style derivation primitives for ANNE."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


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
    valid: bool = True

    def add(self, expression: str, operation: str, justification: str) -> None:
        self.steps.append(DerivationStep(len(self.steps) + 1, expression, operation, justification))


class SymbolicDerivationEngine:
    """Records explicit transformations; it never asks an LLM to perform arithmetic."""

    def derive(self, goal: str, steps: list[tuple[str, str, str]], conclusion: str) -> DerivationResult:
        result = DerivationResult(goal=goal, conclusion=conclusion)
        for expression, operation, justification in steps:
            result.add(expression, operation, justification)
        return result

    def verify_chain(self, result: DerivationResult, checker: Callable[[DerivationStep], bool]) -> bool:
        result.valid = all(checker(step) for step in result.steps)
        return result.valid


__all__ = ["DerivationStep", "DerivationResult", "SymbolicDerivationEngine"]
