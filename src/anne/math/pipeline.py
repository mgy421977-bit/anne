"""Computation-core pipeline: equations \u2192 derivation \u2192 independent verification."""
from __future__ import annotations

from dataclasses import dataclass

from anne.math.benchmark import KINEMATICS_ELIMINATION, DerivationBenchmark
from anne.math.derivation import DerivationResult, SymbolicDerivationEngine
from anne.math.verification import RelationVerifier, VerificationReport


@dataclass(frozen=True)
class ComputationOutcome:
    derivation: DerivationResult
    verification: VerificationReport
    benchmark_name: str

    @property
    def passed(self) -> bool:
        return self.verification.ok and bool(self.derivation.conclusion)


class ComputationPipeline:
    """Deterministic computation path \u2014 no LLM calls."""

    def __init__(self) -> None:
        self.engine = SymbolicDerivationEngine()
        self.verifier = RelationVerifier()

    def run_kinematics_benchmark(
        self, benchmark: DerivationBenchmark = KINEMATICS_ELIMINATION
    ) -> ComputationOutcome:
        # Hidden target is used only by the verifier, never by the engine inputs.
        derivation = self.engine.derive_elimination(
            list(benchmark.givens),
            variable="t",
            goal=benchmark.goal,
        )
        assert derivation.relation is not None
        report = self.verifier.full(derivation.relation, benchmark.hidden_target)
        derivation.valid = report.ok
        return ComputationOutcome(derivation, report, benchmark.name)


__all__ = ["ComputationOutcome", "ComputationPipeline"]
