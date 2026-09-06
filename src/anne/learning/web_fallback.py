"""Broad public-web retrieval fallback for ANNE.

This module supplements the conservative primary WebResearcher when retrieval
returns too little evidence. It is generic and does not contain domain answers.
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .evidence import EvidenceItem


class _SearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[tuple[str, str, str]] = []
        self._title = ""
        self._href = ""
        self._snippet = ""
        self._mode: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        classes = attrs_map.get("class") or ""
        if tag == "a" and ("b_algo" in classes or "result__a" in classes):
            self._title = ""
            self._href = attrs_map.get("href") or ""
            self._mode = "title"
        elif "b_caption" in classes or "result__snippet" in classes:
            self._snippet = ""
            self._mode = "snippet"

    def handle_data(self, data: str) -> None:
        if self._mode == "title":
            self._title += data
        elif self._mode == "snippet":
            self._snippet += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._mode == "title":
            title = re.sub(r"\s+", " ", self._title).strip()
            if title:
                self.results.append((title, self._href, ""))
            self._mode = None
        elif self._mode == "snippet" and self._snippet.strip():
            if self.results:
                title, href, _ = self.results[-1]
                self.results[-1] = (title, href, re.sub(r"\s+", " ", self._snippet).strip())
            self._mode = None


def _normalize(text: str) -> str:
    text = text.lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    stop = {"ve", "ile", "bir", "bu", "şu", "için", "olan", "olarak", "de", "da", "the", "and", "for", "with", "this", "that", "how", "what", "which"}
    return {x for x in _normalize(text).split() if len(x) > 2 and x not in stop}


def _relevance(query: str, text: str) -> float:
    q = _tokens(query)
    t = _tokens(text)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ANNE-AI/0.5 (+public-web-research)"})
    with urllib.request.urlopen(req, timeout=10.0) as response:
        return response.read().decode("utf-8", errors="replace")


def _search(query: str) -> list[EvidenceItem]:
    encoded = urllib.parse.quote_plus(query)
    urls = [
        f"https://www.bing.com/search?q={encoded}&count=10",
        f"https://html.duckduckgo.com/html/?q={encoded}",
    ]
    for url in urls:
        try:
            parser = _SearchParser()
            parser.feed(_get(url))
            found: list[EvidenceItem] = []
            for title, href, snippet in parser.results[:10]:
                claim = f"{title}: {snippet}" if snippet else title
                score = _relevance(query, claim)
                if score < 0.18:
                    continue
                confidence = min(0.90, 0.48 + score * 0.35)
                if re.search(r"\.gov\.tr(?:/|$)", href, re.I):
                    confidence = min(0.98, confidence + 0.12)
                found.append(EvidenceItem(source="Broad Web Search", claim=claim[:2200], kind="web", provenance=href or url, confidence=confidence))
            if found:
                return found
        except Exception:
            continue
    return []


def research_fallback(question: str) -> list[EvidenceItem]:
    """Run several short, concept-focused public-web searches."""
    q = question.strip()
    if not q:
        return []
    variants = [
        q,
        " ".join(sorted(_tokens(q))) + " 2026",
    ]
    if any(term in _normalize(q) for term in ("tesvik", "destek", "hibe", "finansman", "devlet")):
        variants.extend([
            "Türkiye 2026 sanayi enerji verimliliği teşvikleri site:gov.tr",
            "Türkiye 2026 GES sanayi teşvikleri site:gov.tr",
            "Türkiye 2026 enerji depolama teşvikleri site:gov.tr",
            "Türkiye 2026 karbon azaltımı destekleri site:gov.tr",
            "Türkiye 2026 sanayi enerji finansmanı KOSGEB TKDK kalkınma bankası site:gov.tr",
        ])
    else:
        variants.extend([
            "Türkiye 2026 GES sanayi enerji verimliliği",
            "Türkiye 2026 batarya enerji depolama sanayi",
            "Türkiye 2026 karbon azaltımı sanayi",
        ])
    evidence: list[EvidenceItem] = []
    seen: set[str] = set()
    for variant in variants[:8]:
        for item in _search(variant):
            key = re.sub(r"\W+", " ", item.claim.lower()).strip()
            if key and key not in seen:
                seen.add(key)
                evidence.append(item)
    evidence.sort(key=lambda x: x.confidence, reverse=True)
    return evidence[:10]
