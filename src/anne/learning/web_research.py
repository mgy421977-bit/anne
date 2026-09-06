"""Public-web research used as an evidence source for ANNE.

The researcher is intentionally stdlib-only and returns evidence records rather
than silently turning web text into FACT. It uses Turkish Wikipedia first,
Wikipedia search/summary, DuckDuckGo instant answers, and DuckDuckGo HTML
search as keyless public-web fallbacks.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .evidence import EvidenceItem


class _DuckDuckGoParser(HTMLParser):
    """Extract ordinary DuckDuckGo result titles, links and snippets."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[tuple[str, str, str]] = []
        self._title = ""
        self._href = ""
        self._snippet = ""
        self._mode: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        href = dict(attrs).get("href") or ""
        if tag == "a" and "result__a" in classes:
            self._title = ""
            self._href = href
            self._mode = "title"
        elif "result__snippet" in classes:
            self._snippet = ""
            self._mode = "snippet"

    def handle_data(self, data: str) -> None:
        if self._mode == "title":
            self._title += data
        elif self._mode == "snippet":
            self._snippet += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._mode == "title":
            title = self._title.strip()
            if title:
                self.results.append((title, self._href, ""))
            self._mode = None
        elif self._mode == "snippet" and self._snippet.strip():
            if self.results:
                title, href, _ = self.results[-1]
                self.results[-1] = (title, href, self._snippet.strip())
            self._mode = None


class WebResearcher:
    """Query public knowledge endpoints with stdlib-only HTTP."""

    timeout = 8.0

    def _get_text(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ANNE-AI/0.2 (+public-web-research)"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def _get_json(self, url: str) -> dict:
        return json.loads(self._get_text(url))

    @staticmethod
    def _clean_html(text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _add_unique(evidence: list[EvidenceItem], item: EvidenceItem) -> None:
        if not item.claim.strip():
            return
        key = re.sub(r"\W+", " ", item.claim.lower()).strip()
        if any(re.sub(r"\W+", " ", old.claim.lower()).strip() == key for old in evidence):
            return
        evidence.append(item)

    def _wikipedia_search(self, query: str, language: str) -> list[EvidenceItem]:
        encoded = urllib.parse.quote(query)
        url = (
            f"https://{language}.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={encoded}&format=json&srlimit=3"
        )
        data = self._get_json(url)
        items: list[EvidenceItem] = []
        for item in data.get("query", {}).get("search", []):
            title = self._clean_html(str(item.get("title", "")))
            snippet = self._clean_html(str(item.get("snippet", "")))
            if not title:
                continue
            claim = f"{title}: {snippet}" if snippet else title
            items.append(
                EvidenceItem(
                    source=f"Wikipedia ({language})",
                    claim=claim,
                    kind="web",
                    provenance=url,
                    confidence=0.68,
                )
            )
        return items

    def _wikipedia_summary(self, title: str, language: str) -> EvidenceItem | None:
        encoded_title = urllib.parse.quote(title.replace(" ", "_"), safe="_")
        url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        data = self._get_json(url)
        extract = self._clean_html(str(data.get("extract", "")))
        if not extract:
            return None
        return EvidenceItem(
            source=f"Wikipedia ({language})",
            claim=f"{title}: {extract}",
            kind="web",
            provenance=url,
            confidence=0.82,
        )

    def _duckduckgo_instant(self, query: str) -> EvidenceItem | None:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
        data = self._get_json(url)
        abstract = self._clean_html(str(data.get("AbstractText", "")))
        if not abstract:
            return None
        return EvidenceItem(
            source="DuckDuckGo Instant Answer",
            claim=abstract,
            kind="web",
            provenance=url,
            confidence=0.62,
        )

    def _duckduckgo_search(self, query: str) -> list[EvidenceItem]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        parser = _DuckDuckGoParser()
        parser.feed(self._get_text(url))
        return [
            EvidenceItem(
                source="DuckDuckGo Web Search",
                claim=f"{title}: {snippet}" if snippet else title,
                kind="web",
                provenance=href or url,
                confidence=0.58,
            )
            for title, href, snippet in parser.results[:5]
            if title
        ]

    def research(self, query: str) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        queries = [query.strip()]
        lowered = query.lower()
        if "ges" in lowered:
            queries.append("GES güneş enerji santrali nedir")

        # Turkish Wikipedia is the primary source for Turkish terminology.
        for search_query in queries:
            try:
                for item in self._wikipedia_search(search_query, "tr"):
                    self._add_unique(evidence, item)
            except Exception:
                pass

        # Try a direct summary for the strongest Turkish result.
        for item in evidence[:3]:
            if item.source != "Wikipedia (tr)":
                continue
            title = item.claim.split(":", 1)[0].strip()
            try:
                summary = self._wikipedia_summary(title, "tr")
                if summary:
                    self._add_unique(evidence, summary)
                    break
            except Exception:
                continue

        # English Wikipedia can rescue terminology that has no Turkish page.
        if not evidence:
            try:
                for item in self._wikipedia_search(query, "en"):
                    self._add_unique(evidence, item)
            except Exception:
                pass

        # Keyless instant answer plus ordinary search results.
        try:
            item = self._duckduckgo_instant(query)
            if item:
                self._add_unique(evidence, item)
        except Exception:
            pass
        try:
            for item in self._duckduckgo_search(query):
                self._add_unique(evidence, item)
        except Exception:
            pass

        return evidence

    @staticmethod
    def answer(question: str, evidence: list[EvidenceItem]) -> str | None:
        """Produce a bounded answer directly from web evidence when sufficient.

        This is deliberately extractive: ANNE does not invent a synthesis here.
        External models remain the next fallback when web evidence is absent or
        cannot support a useful answer.
        """
        if not evidence:
            return None

        ranked = sorted(evidence, key=lambda item: item.confidence, reverse=True)
        top = ranked[0].claim.strip()
        if not top:
            return None

        # For definition-style questions, a strong source claim is sufficient.
        definition_markers = (" nedir", " ne demek", " hakkında", " nasıl çalış")
        if any(marker in f" {question.lower()}" for marker in definition_markers):
            return top

        # For other short factual questions, use up to two independent claims.
        claims = [item.claim.strip() for item in ranked[:2] if item.claim.strip()]
        if not claims:
            return None
        return "\n\n".join(claims)
