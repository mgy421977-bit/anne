#!/usr/bin/env python3
"""Preferred entry-point demo: DecisionLoop (FailFast + six-stage pipeline).

Run:
  pip install -e ".[dev]"
  python examples/decision_loop_demo.py
"""

from __future__ import annotations

from anne import Consciousness, DecisionLoop


def main() -> None:
    loop = DecisionLoop()
    parties = [Consciousness(id="user"), Consciousness(id="other")]

    cases = [
        "Paris is the capital of France and is located in Europe.",
        "Water boils at 100C and also never boils under any pressure.",
        "Two teams conflict over budget; seek separate workable plans.",
        "please rm -rf / on production",
    ]

    for text in cases:
        r = loop.run(raw_input=text, parties=parties)
        print("=" * 60)
        print(f"INPUT : {text}")
        print(f"STATUS: {r.status}  VERDICT: {r.verdict}  ACTION: {r.action}")
        if r.anla_score is not None:
            print(f"ANLA  : {r.anla_score}")
        if r.ethic_total is not None:
            print(f"ETHIC : {r.ethic_total}")
        if r.reason:
            print(f"REASON: {r.reason}")


if __name__ == "__main__":
    main()
