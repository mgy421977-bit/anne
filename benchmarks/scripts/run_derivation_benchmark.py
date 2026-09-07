"""Run Mathematical Derivation Benchmark #01 with an external oracle."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import sympy as sp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from anne.core.derivation_engine import DerivationEngine


SOURCE_EQUATIONS = ("v = u + a*t", "s = u*t + (1/2)*a*t**2")
ELIMINATION_VARIABLE = "t"
ORACLE = sp.sympify("v**2 - u**2 - 2*a*s")


def run() -> dict[str, object]:
    engine = DerivationEngine()
    generated = engine.derive_elimination(SOURCE_EQUATIONS, ELIMINATION_VARIABLE)
    verified = engine.verify(generated, ORACLE)
    required = ["parse", "identify_elimination_variable", "isolate", "substitute", "expand", "simplify"]
    operations = [step.operation for step in verified.steps]
    trace_ok = operations == required
    deterministic = engine.derive_elimination(SOURCE_EQUATIONS, ELIMINATION_VARIABLE).result == generated.result
    passed = bool(verified.verified and trace_ok and deterministic)
    return {
        "benchmark": "derivation-01",
        "passed": passed,
        "result": sp.sstr(verified.result),
        "verified": verified.verified,
        "trace_ok": trace_ok,
        "deterministic": deterministic,
        "steps": [
            {"operation": s.operation, "expression": s.expression, "note": s.note}
            for s in verified.steps
        ],
    }


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
