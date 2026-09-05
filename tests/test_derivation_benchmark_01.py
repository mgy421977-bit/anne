import sympy as sp
from anne.core.derivation_engine import DerivationEngine


def test_kinematic_elimination_derives_target_relation() -> None:
    engine = DerivationEngine()
    result = engine.derive_elimination(
        ("v = u + a*t", "s = u*t + (1/2)*a*t**2"), "t"
    )
    oracle = sp.sympify("v**2 - u**2 - 2*a*s")
    checked = engine.verify(result, oracle)
    assert checked.verified is True
    assert [step.operation for step in checked.steps] == [
        "parse", "identify_elimination_variable", "isolate", "substitute", "expand", "simplify"
    ]
