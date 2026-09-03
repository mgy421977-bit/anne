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

    def _fractal_connections(
        self, patterns: list[tuple[Any, ...]]
    ) -> list[dict[str, Any]]:
        connections: list[dict[str, Any]] = []
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i + 1 :]:
                w1 = set(str(p1[0]).replace("→", "").split())
                w2 = set(str(p2[0]).replace("→", "").split())
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

    def _synthesize(
        self,
        patterns: list[tuple[Any, ...]],
        rules: list[tuple[Any, ...]],
    ) -> dict[str, float]:
        synthesis: dict[str, float] = {}
        if not patterns:
            return synthesis

        verdict_counts: dict[str, int] = defaultdict(int)
        for pattern in patterns:
            verdict = str(pattern[3]) if len(pattern) > 3 else ""
            frequency = int(pattern[1]) if len(pattern) > 1 else 0
            if verdict:
                verdict_counts[verdict] += frequency
        total = sum(verdict_counts.values()) or 1
        for verdict, count in verdict_counts.items():
            if count / total > 0.3:
                synthesis[f"dominant:{verdict}"] = round(count / total, 3)

        avgs = [
            float(pattern[2])
            for pattern in patterns
            if len(pattern) > 2 and float(pattern[2]) > 0
        ]
        if avgs:
            quality = sum(avgs) / len(avgs)
            synthesis[f"quality:{quality:.3f}"] = round(quality, 3)

        if rules:
            confidences = [float(rule[1]) for rule in rules if len(rule) > 1]
            if confidences:
                average_confidence = sum(confidences) / len(confidences)
                synthesis[f"rule_conf:{average_confidence:.3f}"] = round(
                    average_confidence, 3
                )
        return synthesis
