#!/usr/bin/env python3
"""Minimal demonstration of the ANNE six-stage pipeline."""

from anne import AnneMythosBridge, Consciousness


def main() -> None:
    bridge = AnneMythosBridge(db_path=":memory:")
    consciousnesses = [Consciousness(id=f"C{i}") for i in range(1, 5)]

    result = bridge.process(
        topic="Renewable energy optimization under equity constraints",
        consciousnesses=consciousnesses,
        max_iterations=3,
    )

    print(f"Cycle: {result['cycle']}")
    print(f"Topic: {result['topic']}")
    for r in result["results"]:
        h = r["hypothesis"]
        e = r["ethic"]
        print(
            f"  HYP p={h['probability']:.3f} → {e['verdict']} "
            f"(good={e['goodness']:.2f} eq={e['equality']:.2f} harm={e['harm']:.2f})"
        )


if __name__ == "__main__":
    main()
