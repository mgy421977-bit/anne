"""Benchmark #01: derive v^2 = u^2 + 2 a s without leaking the target into the engine."""
from __future__ import annotations

from anne.math.benchmark import KINEMATICS_ELIMINATION
from anne.math.pipeline import ComputationPipeline
from anne.math.symbolic import SymbolicMathEngine


def test_kinematics_elimination_matches_oracle():
    pipe = ComputationPipeline()
    outcome = pipe.run_kinematics_benchmark()
    assert outcome.passed, outcome.verification.detail
    assert outcome.derivation.relation is not None
    engine = SymbolicMathEngine()
    oracle = engine.parse(KINEMATICS_ELIMINATION.hidden_target)
    assert engine.relations_equivalent(outcome.derivation.relation, oracle)
    ops = {step.operation for step in outcome.derivation.steps}
    assert "isolate" in ops
    assert "substitute" in ops


def test_target_not_in_givens():
    assert KINEMATICS_ELIMINATION.hidden_target not in KINEMATICS_ELIMINATION.givens
    for g in KINEMATICS_ELIMINATION.givens:
        assert "v^2" not in g and "v**2" not in g
