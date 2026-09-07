"""Resilient public-web retrieval for ANNE.

The existing WebResearcher is intentionally conservative, but a long question
can contain many concepts and therefore score too low as one search query.
This adapter decomposes long questions into bounded, generic search probes and
adds parser fallbacks for public search pages when the primary HTML shape
changes. It does not add domain-specific facts.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Iterable
import urllib.parse

from .evidence import EvidenceItem
from .web_research import WebResearcher


class _LooseSearchParser(HTMLParser):
    """Recover search result links from common public HTML layouts."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[tuple[str, str, str]] = []
        self._title = ""
        self._href = ""
        self._snippet = ""
        self._mode: str | None = None
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        classes = attrs_map.get("class") or ""
        href = attrs_map.get("href") or ""
        if tag == "a" and (
            "result-link" in classes
            or "result__a" in classes
            or "b_algo" in classes
            or "bing" in classes.lower()
        ):
            self._title = ""
            self._href = href
            self._snippet = ""
            self._mode = "title"
            self._depth = 0
        elif tag == "h2" and self._mode is None:
            self._mode = "title_heading"
            self._title = ""
            self._depth = 1
        elif self._mode in {"title", "title_heading"} and tag in {"h2", "a"}:
            self._depth += 1
        elif self._mode is None and any(marker in classes for marker in ("result__snippet", "b_caption")):
            self._mode = "snippet"
            self._snippet = ""

    def handle_data(self, data: str) -> None:
        if self._mode in {"title", "title_heading"}:
            self._title += data
        elif self._mode == "snippet":
            self._snippet += data

    def handle_endtag(self, tag: str) -> None:
        if self._mode == "title" and tag == "a":
            title = self._title.strip()
            if title and self._href:
                self.results.append((title, self._href, ""))
            self._mode = None
            self._depth = 0
        elif self._mode == "title_heading" and tag == "h2":
            title = self._title.strip()
            if title and self._href:
                self.results.append((title, self._href, ""))
            self._mode = None
            self._depth = 0
        elif self._mode == "snippet" and self._snippet.strip():
            if self.results:
                title, href, _ = self.results[-1]
                self.results[-1] = (title, href, self._snippet.strip())
            self._mode = None


class ReliableWebResearcher(WebResearcher):
    """Use normal retrieval first, then focused and parser-safe fallbacks."""

    max_focus_queries = 4
    min_focus_terms = 3
    max_focus_terms = 8
    max_fallback_queries = 4

    def __init__(self) -> None:
        super().__init__()
        self.last_diagnostics: list[str] = []

    @classmethod
    def _focus_queries(cls, query: str) -> list[str]:
        """Build generic topical probes without knowing the user's domain."""
        raw = re.sub(r"[?!.]+", ",", query.strip())
        clauses = [part.strip() for part in re.split(r"[,;:\n]+", raw) if part.strip()]
        probes: list[str] = []

        for clause in clauses:
            terms = [
                token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9%+-]{2,}", clause)
                if cls._normalize(token) not in cls._STOPWORDS
            ]
            if cls.min_focus_terms <= len(terms) <= cls.max_focus_terms:
                probes.append(" ".join(terms))
            elif len(terms) > cls.max_focus_terms:
                probes.append(" ".join(terms[: cls.max_focus_terms]))

        terms = [
            token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9%+-]{2,}", query)
            if cls._normalize(token) not in cls._STOPWORDS
        ]
        if len(terms) > cls.max_focus_terms:
            step = max(1, (len(terms) - cls.max_focus_terms) // 3 or 1)
            for start in range(0, len(terms), step):
                window = terms[start : start + cls.max_focus_terms]
                if len(window) >= cls.min_focus_terms:
                    probes.append(" ".join(window))
                if len(probes) >= cls.max_focus_queries:
                    break

        result: list[str] = []
        seen: set[str] = set()
        original = query.strip().lower()
        for probe in probes:
            key = probe.lower().strip()
            if key and key != original and key not in seen:
                seen.add(key)
                result.append(probe)
            if len(result) >= cls.max_focus_queries:
                break
        return result

    @staticmethod
    def _merge(evidence: Iterable[EvidenceItem], limit: int) -> list[EvidenceItem]:
        result: list[EvidenceItem] = []
        seen: set[str] = set()
        for item in evidence:
            key = re.sub(r"\W+", " ", item.claim.lower()).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(item)
            if len(result) >= limit:
                break
        return result

    def _loose_bing_search(self, query: str) -> list[EvidenceItem]:
        """Bing fallback with a looser parser than the legacy class-selector parser."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded}&count=10"
        parser = _LooseSearchParser()
        parser.feed(self._get_text(url))
        items: list[EvidenceItem] = []
        for title, href, snippet in parser.results[:12]:
            claim = f"{title}: {snippet}" if snippet else title
            if not self._is_relevant(query, claim, title):
                continue
            score = self._relevance(query, claim, title)
            confidence = min(0.86, 0.45 + score * 0.41)
            if re.search(r"\.gov\.tr(?:/|$)", href or "", flags=re.I):
                confidence = min(0.99, confidence + 0.12)
            items.append(EvidenceItem(source="Bing Web Search", claim=claim[:2200], kind="web", provenance=href or url, confidence=confidence))
        return items

    def _duckduckgo_lite_search(self, query: str) -> list[EvidenceItem]:
        """DuckDuckGo Lite fallback; its result markup is intentionally simple."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded}"
        parser = _LooseSearchParser()
        parser.feed(self._get_text(url))
        items: list[EvidenceItem] = []
        for title, href, snippet in parser.results[:12]:
            claim = f"{title}: {snippet}" if snippet else title
            if not self._is_relevant(query, claim, title):
                continue
            score = self._relevance(query, claim, title)
            confidence = min(0.85, 0.44 + score * 0.41)
            if re.search(r"\.gov\.tr(?:/|$)", href or "", flags=re.I):
                confidence = min(0.98, confidence + 0.12)
            items.append(EvidenceItem(source="DuckDuckGo Lite", claim=claim[:2200], kind="web", provenance=href or url, confidence=confidence))
        return items

    def research(self, query: str) -> list[EvidenceItem]:
        query = query.strip()
        self.last_diagnostics = []
        if not query:
            return []

        primary = super().research(query)
        self.last_diagnostics.append(f"primary={len(primary)}")
        if len(primary) >= 2:
            return primary

        collected = list(primary)
        for probe in self._focus_queries(query):
            try:
                found = super().research(probe)
                collected.extend(found)
                self.last_diagnostics.append(f"focus={len(found)} query={probe[:100]}")
            except Exception as exc:
                self.last_diagnostics.append(f"focus_error={type(exc).__name__} query={probe[:100]}")
            merged = self._merge(collected, self.max_evidence)
            if len(merged) >= 4:
                return merged

        # The legacy parser can legitimately return zero when a search engine
        # changes its HTML. Try parser-safe public fallbacks before giving up.
        for probe in [query, *self._focus_queries(query)[: self.max_fallback_queries]]:
            try:
                found = self._duckduckgo_lite_search(probe)
                collected.extend(found)
                self.last_diagnostics.append(f"ddg_lite={len(found)} query={probe[:100]}")
            except Exception as exc:
                self.last_diagnostics.append(f"ddg_lite_error={type(exc).__name__}")
            try:
                found = self._loose_bing_search(probe)
                collected.extend(found)
                self.last_diagnostics.append(f"bing_loose={len(found)} query={probe[:100]}")
            except Exception as exc:
                self.last_diagnostics.append(f"bing_loose_error={type(exc).__name__}")
            merged = self._merge(collected, self.max_evidence)
            if len(merged) >= 4:
                return merged

        return self._merge(collected, self.max_evidence)


__all__ = ["ReliableWebResearcher"]
