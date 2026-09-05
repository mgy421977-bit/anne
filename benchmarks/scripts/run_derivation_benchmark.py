"""Benchmark #01: derive v^2 = u^2 + 2*a*s without giving ANNE the target."""
from __future__ import annotations
import sympy as sp
from anne.core.derivation_engine import DerivationEngine

EQUATIONS = ("v = u + a*t", "s = u*t + (1/2)*a*t**2")
TARGET = sp.Symbol("v")**2 - sp.Symbol("u")**2 - 2*sp.Symbol("a")*sp.Symbol("s")


def run() -> bool:
    result = DerivationEngine().derive_elimination(EQUATIONS, "t")
    checked = DerivationEngine().verify(result, TARGET)
    print(f"verified={checked.verified}")
    for step in checked.steps:
        print(f"{step.operation}: {step.expression}")
    return checked.verified


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
