import sympy as sp

from anne.core.derivation_engine import DerivationEngine


def test_kinematic_derivation_without_target_in_generation():
    result = DerivationEngine().derive_elimination(
        ("v = u + a*t", "s = u*t + (1/2)*a*t**2"), "t"
    )
    target = sp.Symbol("v") ** 2 - sp.Symbol("u") ** 2 - 2 * sp.Symbol("a") * sp.Symbol("s")
    verified = DerivationEngine().verify(result, target)
    assert verified.verified
    assert [step.operation for step in result.steps] == [
        "parse", "identify_elimination_variable", "isolate", "substitute", "expand", "simplify"
    ]
