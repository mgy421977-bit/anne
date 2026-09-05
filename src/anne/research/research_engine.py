"""Research orchestration independent from any LLM provider."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from anne.tools.web_research import WebResearchClient


@dataclass
class ResearchFinding:
    title: str
    url: str
    snippet: str
    source_type: str = "web"
    verified: bool = False
    relevance: float = 0.0


@dataclass
class ResearchResult:
    query: str
    findings: list[ResearchFinding] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ResearchEngine:
    """Searches external sources and returns evidence; it never treats search as truth."""

    def __init__(self, client: WebResearchClient | None = None) -> None:
        self.client = client or WebResearchClient()

    def research(self, query: str, max_results: int = 6) -> ResearchResult:
        clean = " ".join(query.split()).strip()
        if not clean:
            return ResearchResult(query="", warnings=["Empty research query"])
        raw = self.client.search(clean, max_results=max_results)
        findings = [
            ResearchFinding(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                snippet=str(item.get("snippet", "")),
            )
            for item in raw
            if isinstance(item, dict)
        ]
        return ResearchResult(query=clean, findings=findings, queries=[clean])

    @staticmethod
    def evidence(result: ResearchResult) -> list[str]:
        return [
            f"SOURCE: {item.title} | {item.url} | {item.snippet}"
            for item in result.findings
            if item.title or item.snippet
        ]

    @staticmethod
    def summary(result: ResearchResult) -> dict[str, Any]:
        return {
            "query": result.query,
            "result_count": len(result.findings),
            "sources": [item.url for item in result.findings if item.url],
            "warnings": list(result.warnings),
        }


__all__ = ["ResearchEngine", "ResearchFinding", "ResearchResult"]
