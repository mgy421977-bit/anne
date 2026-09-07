from __future__ import annotations

import sympy as sp

from anne.core.derivation_engine import DerivationEngine


EQUATIONS = ("v = u + a*t", "s = u*t + (1/2)*a*t**2")
ORACLE = sp.sympify("v**2 - u**2 - 2*a*s")


def test_benchmark_01_derives_and_verifies_without_oracle_in_engine() -> None:
    engine = DerivationEngine()
    generated = engine.derive_elimination(EQUATIONS, "t")
    assert engine.verify(generated, ORACLE).verified
    assert [step.operation for step in generated.steps] == [
        "parse",
        "identify_elimination_variable",
        "isolate",
        "substitute",
        "expand",
        "simplify",
    ]
    assert "v**2 - u**2 - 2*a*s" not in " ".join(step.expression for step in generated.steps)


def test_benchmark_01_is_deterministic() -> None:
    engine = DerivationEngine()
    first = engine.derive_elimination(EQUATIONS, "t")
    second = engine.derive_elimination(EQUATIONS, "t")
    assert first.result == second.result
    assert first.steps == second.steps
