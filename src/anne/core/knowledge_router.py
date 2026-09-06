"""Generic knowledge routing over ANNE's evidence-gated KnowledgeResolver.

The router is intentionally thin: KnowledgeResolver owns memory, web research,
validation, provider fallback and fail-closed behavior. This module only makes
the routing decision explicit at the cognitive boundary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from anne.learning.knowledge_resolver import KnowledgeResolution, KnowledgeResolver
from anne.learning.reliable_web import ReliableWebResearcher


@dataclass(frozen=True)
class KnowledgeRoute:
    """Auditable route decision for a user question."""

    route: str
    resolution: KnowledgeResolution


class _ResearchAwareResolver(KnowledgeResolver):
    """Keep terminology memory from hijacking multi-part questions."""

    _COMPLEX_MARKERS = (
        "?", "hangi", "nasıl", "neden", "karşılaştır", "avantaj", "dezavantaj",
        "koşullarda", "seçenek", "güncel", "teşvik", "finansman", "what", "how", "why",
        "compare", "which",
    )

    def __init__(self) -> None:
        super().__init__(web=ReliableWebResearcher())

    def _term_answer(self, question: str) -> KnowledgeResolution | None:
        normalized = question.strip().lower()
        tokens = re.findall(r"\b[\wÇĞİÖŞÜçğıöşü%+-]+\b", normalized)
        if len(tokens) > 5 or any(marker in normalized for marker in self._COMPLEX_MARKERS):
            return None
        return super()._term_answer(question)


class KnowledgeRouter:
    """Route questions without creating domain-specific knowledge branches."""

    def __init__(self, resolver: KnowledgeResolver | None = None) -> None:
        self.resolver = resolver or _ResearchAwareResolver()

    def resolve(self, question: str) -> KnowledgeRoute:
        if not question.strip():
            raise ValueError("question is required")
        resolution = self.resolver.resolve(question)
        if resolution.memory_hit:
            route = "KNOWN"
        elif resolution.provider == "web":
            route = "UNKNOWN_WEB"
        elif resolution.provider in {"OpenRouter", "Gemini"}:
            route = "UNKNOWN_PROVIDER_FALLBACK"
        else:
            route = "UNKNOWN_FAIL_CLOSED"
        return KnowledgeRoute(route=route, resolution=resolution)


__all__ = ["KnowledgeRoute", "KnowledgeRouter"]
