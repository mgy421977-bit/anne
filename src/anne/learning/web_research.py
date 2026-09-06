"""Minimal public-web researcher used as an evidence source.

It deliberately returns evidence records rather than silently turning web text
into facts. Network failures are non-fatal and leave the candidate unpromoted.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from .evidence import EvidenceItem


class WebResearcher:
    """Query public knowledge endpoints with stdlib-only HTTP."""

    timeout = 8.0

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": "ANNE-AI/0.1"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove search-result markup before evidence reaches the audit trace."""
        text = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def research(self, query: str) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        encoded = urllib.parse.quote(query)

        # Wikipedia gives a useful public reference without requiring an API key.
        try:
            url = (
                "https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={encoded}&format=json&srlimit=3"
            )
            data = self._get_json(url)
            for item in data.get("query", {}).get("search", []):
                title = self._clean_html(str(item.get("title", "")))
                snippet = self._clean_html(str(item.get("snippet", "")))
                if title:
                    evidence.append(
                        EvidenceItem(
                            source="Wikipedia",
                            claim=f"{title}: {snippet}",
                            kind="web",
                            provenance=url,
                            confidence=0.60,
                        )
                    )
        except Exception:
            pass

        # DuckDuckGo's instant-answer endpoint is another independent public source.
        try:
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
            data = self._get_json(url)
            abstract = self._clean_html(str(data.get("AbstractText", "")))
            if abstract:
                evidence.append(
                    EvidenceItem(
                        source="DuckDuckGo Instant Answer",
                        claim=abstract,
                        kind="web",
                        provenance=url,
                        confidence=0.55,
                    )
                )
        except Exception:
            pass

        return evidence
