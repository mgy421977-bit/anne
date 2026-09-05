"""Human-readable presentation without requiring an LLM."""
from __future__ import annotations

from typing import Any


class PresentationEngine:
    """Renders cognitive state into deterministic text; LLMs can replace this later."""

    def render(self, state: dict[str, Any], title: str = "ANNE") -> str:
        lines = [f"{title}", "=" * len(title)]
        lines.append(f"Görev: {state.get('task', '')}")
        lines.append(f"Güven: {float(state.get('confidence', 0.0)):.0%}")
        lines.append(f"Belirsizlik: {float(state.get('uncertainty', 1.0)):.0%}")
        concepts = state.get("concepts", [])
        if concepts:
            lines.append("Kavramlar: " + ", ".join(str(x) for x in concepts))
        evidence = state.get("evidence", [])
        if evidence:
            lines.append("Kanıt:")
            lines.extend(f"- {x}" for x in evidence[:8])
        actions = state.get("actions", [])
        if actions:
            lines.append("Sonraki adım:")
            lines.extend(f"- {x}" for x in actions)
        unknown = state.get("unknown", [])
        if unknown:
            lines.append("Eksikler:")
            lines.extend(f"- {x}" for x in unknown[:5])
        lessons = state.get("lessons", [])
        if lessons:
            lines.append("Öğrenilen:")
            lines.extend(f"- {x}" for x in lessons[-5:])
        return "\n".join(lines)


__all__ = ["PresentationEngine"]
