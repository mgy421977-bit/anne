"""Run Mathematical Derivation Benchmark #01 against the deterministic engine."""
from __future__ import annotations
import sympy as sp
from anne.core.derivation_engine import DerivationEngine


def main() -> int:
    engine = DerivationEngine()
    result = engine.derive_elimination(
        ("v = u + a*t", "s = u*t + (1/2)*a*t**2"), "t"
    )
    oracle = sp.sympify("v**2 - u**2 - 2*a*s")
    checked = engine.verify(result, oracle)
    print(f"verified={checked.verified}")
    for step in checked.steps:
        print(f"{step.operation}: {step.expression}")
    return 0 if checked.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
