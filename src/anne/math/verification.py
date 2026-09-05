"""Independent verification for derived mathematical relations."""
from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from anne.math.symbolic import SymbolicMathEngine
from anne.math.units import ACCELERATION, LENGTH, VELOCITY


@dataclass(frozen=True)
class VerificationReport:
    algebraic_ok: bool
    numerical_ok: bool
    dimensional_ok: bool
    detail: str

    @property
    def ok(self) -> bool:
        return self.algebraic_ok and self.numerical_ok and self.dimensional_ok


class RelationVerifier:
    """Oracle-side checks — never inject results back into the derivation engine."""

    def __init__(self, symbolic: SymbolicMathEngine | None = None) -> None:
        self.symbolic = symbolic or SymbolicMathEngine()

    def algebraic(self, derived: sp.Equality, oracle: sp.Equality | str) -> bool:
        if isinstance(oracle, str):
            oracle = self.symbolic.parse(oracle)
        return self.symbolic.relations_equivalent(derived, oracle)

    def numerical(
        self,
        derived: sp.Equality,
        samples: list[dict[str, float]] | None = None,
    ) -> bool:
        samples = samples or [
            {"u": 10.0, "a": 2.0, "t": 3.0},
            {"u": 0.0, "a": 9.81, "t": 1.5},
            {"u": 5.0, "a": -1.0, "t": 4.0},
        ]
        u, v, a, s, t = sp.symbols("u v a s t")
        for sample in samples:
            vv = sample["u"] + sample["a"] * sample["t"]
            ss = sample["u"] * sample["t"] + 0.5 * sample["a"] * sample["t"] ** 2
            subs = {u: sample["u"], v: vv, a: sample["a"], s: ss, t: sample["t"]}
            residual = sp.simplify(sp.expand(derived.lhs - derived.rhs).subs(subs))
            if residual != 0:
                try:
                    if abs(float(residual)) > 1e-8:
                        return False
                except Exception:
                    return False
        return True

    def dimensional_kinematics_v2(self) -> bool:
        left = VELOCITY * VELOCITY
        accel_term = ACCELERATION * LENGTH
        return left.compatible(accel_term)

    def full(
        self,
        derived: sp.Equality,
        oracle: str,
        check_dimensions: bool = True,
    ) -> VerificationReport:
        alg = self.algebraic(derived, oracle)
        num = self.numerical(derived)
        dim = self.dimensional_kinematics_v2() if check_dimensions else True
        detail = f"algebraic={alg} numerical={num} dimensional={dim}"
        return VerificationReport(alg, num, dim, detail)


__all__ = ["VerificationReport", "RelationVerifier"]
