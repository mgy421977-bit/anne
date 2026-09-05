"""Fresh derivation benchmark: target result is intentionally not supplied to ANNE."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DerivationBenchmark:
    name: str
    givens: tuple[str, ...]
    goal: str
    hidden_target: str


# The hidden target is kept only as an oracle for the test harness, not exposed
# through the benchmark input given to a derivation agent.
KINEMATICS_ELIMINATION = DerivationBenchmark(
    name="constant_acceleration_time_elimination",
    givens=("v = u + a*t", "s = u*t + (a*t^2)/2"),
    goal="eliminate t and derive a relation containing only v, u, a, s",
    hidden_target="v^2 = u^2 + 2*a*s",
)
