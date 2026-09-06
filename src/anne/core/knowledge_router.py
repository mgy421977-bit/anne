"""Generic knowledge routing over ANNE's evidence-gated KnowledgeResolver.

The router is intentionally thin: KnowledgeResolver owns memory, web research,
validation, provider fallback and fail-closed behavior. This module only makes
the routing decision explicit at the cognitive boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from anne.learning.knowledge_resolver import KnowledgeResolution, KnowledgeResolver


@dataclass(frozen=True)
class KnowledgeRoute:
    """Auditable route decision for a user question."""

    route: str
    resolution: KnowledgeResolution


class KnowledgeRouter:
    """Route questions without creating domain-specific knowledge branches."""

    def __init__(self, resolver: KnowledgeResolver | None = None) -> None:
        self.resolver = resolver or KnowledgeResolver()

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
