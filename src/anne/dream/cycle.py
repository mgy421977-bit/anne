"""Dream Cycle – offline pattern synthesis and rule discovery."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from anne.memory.fractal_memory import FractalMemory


class DreamCycle:
    """Passive learning mode triggered every N processing cycles.

    Analyzes accumulated patterns, finds fractal connections,
    and synthesizes new rules.
    """

    def __init__(self, memory: FractalMemory) -> None:
        self.memory = memory

    def run(self) -> dict[str, Any]:
        top = self.memory.get_top_patterns(10)
        rules = self.memory.get_strong_rules(5)
        connections = self._fractal_connections(top)
        synthesis = self._synthesize(top, rules)

        for rule, conf in synthesis.items():
            self.memory.save_learned_rule(f"DREAM:{rule}", conf)

        return {
            "top_patterns": top,
            "rules": rules,
            "connections": connections,
            "synthesis": synthesis,
        }

    def _fractal_connections(self, patterns: list) -> list[dict]:
        connections = []
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i + 1 :]:
                w1 = set(p1[0].replace("→", "").split())
                w2 = set(p2[0].replace("→", "").split())
                common = w1 & w2
                if common:
                    connections.append(
                        {
                            "a": p1[0],
                            "b": p2[0],
                            "shared": list(common),
                            "strength": len(common) / max(len(w1), len(w2)),
                        }
                    )
        return connections[:10]

    def _synthesize(self, patterns: list, rules: list) -> dict[str, float]:
        s: dict[str, float] = {}
        if not patterns:
            return s

        vc: dict[str, int] = defaultdict(int)
        for p in patterns:
            if p[3]:
                vc[p[3]] += p[1]
        total = sum(vc.values()) or 1
        for v, c in vc.items():
            if c / total > 0.3:
                s[f"dominant:{v}"] = round(c / total, 3)

        avgs = [p[2] for p in patterns if p[2] > 0]
        if avgs:
            s[f"quality:{sum(avgs)/len(avgs):.3f}"] = round(sum(avgs) / len(avgs), 3)

        if rules:
            ac = sum(r[1] for r in rules) / len(rules)
            s[f"rule_conf:{ac:.3f}"] = round(ac, 3)
        return s
