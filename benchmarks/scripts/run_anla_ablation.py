#!/usr/bin/env python3
"""ANLA on vs off ablation scaffold.

Uses shared heuristic from anne.core.anla_score.
Does not claim production hallucination metrics.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from anne.core.anla_score import DEFAULT_TAU, compute_anla_score
from anne.core.cognitive_state import Consciousness, Hypothesis
from anne.core.ethic_core import EthicCore
from anne.memory.fractal_memory import FractalMemory

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "datasets" / "ablation_prompts.json"
RESULTS = ROOT / "benchmarks" / "results"


def git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def run_condition(prompts: list, anla_on: bool, tau: float = DEFAULT_TAU) -> dict:
    core = EthicCore()
    mem = FractalMemory(":memory:")
    cons = [Consciousness(id="A"), Consciousness(id="B")]
    blocked = 0
    passed = 0
    false_pass = 0
    false_block = 0
    retries = 0

    for p in prompts:
        text = p["text"]
        expected = p["expected"]
        failures = mem.get_recent_failures(limit=5) if anla_on else []

        if anla_on:
            s = compute_anla_score(text, failures)
            if s < tau:
                blocked += 1
                retries += 1
                mem.save_failure_trace(
                    cycle_id=p["id"],
                    stage="ANLA",
                    raw_input=text,
                    reason=f"S_ANLA={s}<{tau}",
                    meta_tag="ablation",
                    ethic_total=0.0,
                )
                if expected == "coherent":
                    false_block += 1
                continue

        hyp = Hypothesis(
            id=p["id"],
            topic=text[:48],
            claim=text,
            probability=0.7 if expected == "coherent" else 0.35,
        )
        score = core.evaluate(hyp, cons)
        passed += 1
        if expected == "incoherent" and score.verdict != "REDDET":
            false_pass += 1

    return {
        "anla": "ON" if anla_on else "OFF",
        "passed": passed,
        "blocked": blocked,
        "false_pass": false_pass,
        "false_block": false_block,
        "retry_events": retries,
        "n": len(prompts),
        "tau": tau,
    }


def main() -> int:
    if not FIXTURE.exists():
        print(f"Missing fixture: {FIXTURE}", file=sys.stderr)
        return 1
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    payload = {
        "fixture_version": data.get("version"),
        "git_sha": git_sha(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ANLA_OFF": run_condition(prompts, anla_on=False),
        "ANLA_ON": run_condition(prompts, anla_on=True),
        "note": "Heuristic scaffold only — not a published benchmark claim.",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_anla_ablation.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
