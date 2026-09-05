from anne.math.benchmark import KINEMATICS_ELIMINATION
from anne.math.derivation import SymbolicDerivationEngine


def test_benchmark_input_does_not_expose_target():
    benchmark = KINEMATICS_ELIMINATION
    prompt_material = "\n".join((*benchmark.givens, benchmark.goal))
    assert benchmark.hidden_target not in prompt_material


def test_full_derivation_chain_matches_oracle():
    benchmark = KINEMATICS_ELIMINATION
    engine = SymbolicDerivationEngine()
    result = engine.derive(
        benchmark.goal,
        [
            ("v = u + a*t", "given", "initial relation"),
            ("t = (v-u)/a", "solve for t", "isolate t"),
            ("s = u*(v-u)/a + a*((v-u)/a)^2/2", "substitute", "replace t"),
            ("2*a*s = 2*u*(v-u) + (v-u)^2", "multiply and simplify", "clear denominator"),
            ("2*a*s = v^2-u^2", "expand and collect", "algebraic simplification"),
            ("v^2 = u^2 + 2*a*s", "rearrange", "isolate v^2"),
        ],
        benchmark.hidden_target,
    )
    assert result.valid
    assert result.conclusion == benchmark.hidden_target
    assert len(result.steps) == 6
