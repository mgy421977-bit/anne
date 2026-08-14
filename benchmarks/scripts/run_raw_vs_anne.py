#!/usr/bin/env python3
"""Micro comparison: raw pass-through vs ANNE DecisionLoop on the same fixture.

Definitions (honest):
  RAW  — accept the claim as output with no FailFast, ANLA, or EthicCore.
  ANNE — DecisionLoop (FailFast → pipeline gates).

This is not an LLM-vs-LLM benchmark and not a claim of production superiority.
It measures whether gates change accept/reject outcomes on the micro-fixture.

  python benchmarks/scripts/run_raw_vs_anne.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from anne import Consciousness, DecisionLoop
from anne.memory.fractal_memory import FractalMemory

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "datasets" / "ablation_prompts.json"
RESULTS = ROOT / "benchmarks" / "results"


def raw_pass_through(text: str, expected: str) -> dict:
    """No gates: always 'accept' the text as delivered output."""
    return {
        "mode": "RAW",
        "accepted": True,
        "verdict": "PASS_THROUGH",
        "expected": expected,
        "false_accept": expected == "incoherent",
        "false_reject": False,
    }


def anne_decision(loop: DecisionLoop, text: str, expected: str) -> dict:
    r = loop.run(
        raw_input=text,
        claim=text,
        parties=[Consciousness(id="a"), Consciousness(id="b")],
    )
    accepted = r.status == "EXECUTED" and r.verdict != "REDDET"
    # AYRI_ÇÖZÜM counts as controlled non-reject execution
    if r.verdict == "AYRI_ÇÖZÜM":
        accepted = True
    if r.verdict == "FAIL_FAST":
        accepted = False
    false_accept = accepted and expected == "incoherent"
    false_reject = (not accepted) and expected == "coherent"
    return {
        "mode": "ANNE",
        "accepted": accepted,
        "verdict": r.verdict,
        "action": r.action,
        "expected": expected,
        "false_accept": false_accept,
        "false_reject": false_reject,
        "anla_score": r.anla_score,
        "ethic_total": r.ethic_total,
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    return {
        "n": n,
        "accepted": sum(1 for r in rows if r["accepted"]),
        "false_accept": sum(1 for r in rows if r["false_accept"]),
        "false_reject": sum(1 for r in rows if r["false_reject"]),
        "false_accept_rate": (sum(1 for r in rows if r["false_accept"]) / n) if n else 0.0,
        "false_reject_rate": (sum(1 for r in rows if r["false_reject"]) / n) if n else 0.0,
    }


def main() -> int:
    if not FIXTURE.exists():
        print(f"Missing fixture: {FIXTURE}", file=sys.stderr)
        return 1

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    loop = DecisionLoop(memory=FractalMemory(":memory:"))

    raw_rows = []
    anne_rows = []
    paired = []

    for p in prompts:
        text = p["text"]
        expected = p["expected"]
        raw = raw_pass_through(text, expected)
        anne = anne_decision(loop, text, expected)
        raw_rows.append(raw)
        anne_rows.append(anne)
        paired.append({"id": p["id"], "expected": expected, "raw": raw, "anne": anne})

    payload = {
        "fixture_version": data.get("version"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "definition": {
            "RAW": "Pass-through accept; no FailFast/ANLA/EthicCore",
            "ANNE": "DecisionLoop gated path",
            "not_claimed": "LLM quality, TruthfulQA/HaluEval, production safety",
        },
        "RAW": summarize(raw_rows),
        "ANNE": summarize(anne_rows),
        "pairs": paired,
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_raw_vs_anne.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"RAW": payload["RAW"], "ANNE": payload["ANNE"]}, indent=2))
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
