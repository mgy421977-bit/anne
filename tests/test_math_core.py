import math

from anne.math.engine import MathEngine
from anne.math.derivation import SymbolicDerivationEngine


def test_deterministic_arithmetic():
    engine = MathEngine()
    assert engine.add(2, 3).value == 5
    assert engine.multiply(6, 7).value == 42
    assert engine.divide(1, 0).valid is False
    assert math.isclose(engine.sqrt(81).value, 9)


def test_numerical_calculus():
    engine = MathEngine()
    derivative = engine.derivative(lambda x: x * x, 3.0)
    integral = engine.integrate(lambda x: x, 0.0, 2.0, steps=1000)
    assert math.isclose(derivative.value, 6.0, rel_tol=1e-5)
    assert math.isclose(integral.value, 2.0, rel_tol=1e-5)


def test_derivation_is_traceable():
    engine = SymbolicDerivationEngine()
    result = engine.derive(
        "solve x + 3 = 7",
        [
            ("x + 3 = 7", "start", "given equation"),
            ("x + 3 - 3 = 7 - 3", "subtract 3", "same operation on both sides"),
            ("x = 4", "simplify", "arithmetic simplification"),
        ],
        "x = 4",
    )
    assert len(result.steps) == 3
    assert result.conclusion == "x = 4"
