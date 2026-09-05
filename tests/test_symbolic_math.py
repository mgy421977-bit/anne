import sympy as sp

from anne.math.symbolic import SymbolicMathEngine


def test_elimination_derives_without_target_input():
    engine = SymbolicMathEngine()
    result = engine.eliminate(
        ["v = u + a*t", "s = u*t + (a*t^2)/2"],
        variable="t",
        target="v",
    )
    assert sp.simplify(result.relation.lhs**2 - (sp.Symbol("u")**2 + 2*sp.Symbol("a")*sp.Symbol("s"))) == 0
    assert len(result.steps) >= 3
