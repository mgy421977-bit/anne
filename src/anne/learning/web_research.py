"""Public-web research and relevance filtering for ANNE."""
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
        attributes = dict(attrs)
        classes = attributes.get("class") or ""
        href = attributes.get("href") or ""
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
    """Query public knowledge endpoints and reject weakly related results."""

    timeout = 8.0
    minimum_relevance = 0.42
    max_evidence = 8

    _STOPWORDS = {
        "ve", "veya", "ile", "bir", "bu", "şu", "için", "olan", "olarak",
        "nedir", "nasıl", "neden", "ne", "hangi", "hakkında", "bilgi",
        "anlat", "açıkla", "mı", "mi", "mu", "mü", "the", "and", "what",
        "how", "why", "about", "is", "are",
    }

    _ALIASES = {
        "ges": {"ges", "güneş", "gunes", "fotovoltaik", "photovoltaic", "solar", "pv"},
        "bess": {"bess", "batarya", "battery", "enerji", "depolama", "storage"},
        "res": {"res", "rüzgar", "ruzgar", "wind", "türbin", "turbin"},
        "hes": {"hes", "hidroelektrik", "hydroelectric", "hidro", "su"},
        "epc": {"epc", "mühendislik", "muhendislik", "tedarik", "kurulum", "engineering", "procurement", "construction"},
        "athena": {"athena", "anne", "ai", "yapay", "zeka"},
    }

    def _get_text(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": "ANNE-AI/0.2 (+public-web-research)"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def _get_json(self, url: str) -> dict:
        return json.loads(self._get_text(url))

    @staticmethod
    def _clean_html(text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
        return re.sub(r"[^a-z0-9]+", " ", text).strip()

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {token for token in cls._normalize(text).split() if len(token) > 1 and token not in cls._STOPWORDS}

    @classmethod
    def _topic_terms(cls, query: str) -> set[str]:
        terms = cls._tokens(query)
        normalized = cls._normalize(query)
        for key, aliases in cls._ALIASES.items():
            if re.search(rf"\b{re.escape(key)}\b", normalized):
                terms.update(aliases)
        return terms

    @classmethod
    def _relevance(cls, query: str, claim: str, title: str = "") -> float:
        query_terms = cls._tokens(query)
        topic_terms = cls._topic_terms(query)
        text = f"{title} {claim}"
        text_terms = cls._tokens(text)
        if not query_terms or not text_terms:
            return 0.0
        direct = len(query_terms & text_terms) / max(1, len(query_terms))
        topic = len(topic_terms & text_terms) / max(1, len(topic_terms))
        exact_phrase = cls._normalize(query) in cls._normalize(text)
        score = 0.72 * direct + 0.28 * topic
        if exact_phrase:
            score += 0.12
        return min(1.0, score)

    @classmethod
    def _is_relevant(cls, query: str, claim: str, title: str = "") -> bool:
        normalized_query = cls._normalize(query)
        raw_text = f"{title} {claim}"
        normalized_text = cls._normalize(raw_text)

        # Technical acronyms are case-sensitive in the source text. A title-case
        # word such as "Bess" (the film/person/name) must not satisfy "BESS".
        # Accept an exact uppercase acronym or at least two expansion terms.
        for acronym, aliases in cls._ALIASES.items():
            if re.search(rf"\b{re.escape(acronym)}\b", normalized_query):
                exact_acronym = bool(re.search(rf"\b{re.escape(acronym.upper())}\b", raw_text))
                expansion_aliases = aliases - {acronym}
                expansion_hits = sum(
                    bool(re.search(rf"\b{re.escape(alias)}\b", normalized_text))
                    for alias in expansion_aliases
                )
                if not exact_acronym and expansion_hits < 2:
                    return False
        return cls._relevance(query, claim, title) >= cls.minimum_relevance

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
        url = f"https://{language}.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=5"
        data = self._get_json(url)
        items: list[EvidenceItem] = []
        for item in data.get("query", {}).get("search", []):
            title = self._clean_html(str(item.get("title", "")))
            snippet = self._clean_html(str(item.get("snippet", "")))
            if not title:
                continue
            claim = f"{title}: {snippet}" if snippet else title
            if not self._is_relevant(query, claim, title):
                continue
            score = self._relevance(query, claim, title)
            items.append(EvidenceItem(source=f"Wikipedia ({language})", claim=claim, kind="web", provenance=url, confidence=min(0.9, 0.55 + score * 0.35)))
        return items

    def _wikipedia_summary(self, title: str, language: str, query: str) -> EvidenceItem | None:
        encoded_title = urllib.parse.quote(title.replace(" ", "_"), safe="_")
        url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        data = self._get_json(url)
        extract = self._clean_html(str(data.get("extract", "")))
        if not extract or not self._is_relevant(query, extract, title):
            return None
        score = self._relevance(query, extract, title)
        return EvidenceItem(source=f"Wikipedia ({language})", claim=f"{title}: {extract}", kind="web", provenance=url, confidence=min(0.95, 0.65 + score * 0.3))

    def _duckduckgo_instant(self, query: str) -> EvidenceItem | None:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
        data = self._get_json(url)
        abstract = self._clean_html(str(data.get("AbstractText", "")))
        if not abstract or not self._is_relevant(query, abstract):
            return None
        return EvidenceItem(source="DuckDuckGo Instant Answer", claim=abstract, kind="web", provenance=url, confidence=min(0.86, 0.5 + self._relevance(query, abstract) * 0.36))

    def _duckduckgo_search(self, query: str) -> list[EvidenceItem]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        parser = _DuckDuckGoParser()
        parser.feed(self._get_text(url))
        items: list[EvidenceItem] = []
        for title, href, snippet in parser.results[:10]:
            if not self._is_relevant(query, snippet, title):
                continue
            score = self._relevance(query, snippet, title)
            items.append(EvidenceItem(source="DuckDuckGo Web Search", claim=f"{title}: {snippet}" if snippet else title, kind="web", provenance=href or url, confidence=min(0.84, 0.46 + score * 0.38)))
        return items

    def research(self, query: str) -> list[EvidenceItem]:
        query = query.strip()
        if not query:
            return []
        evidence: list[EvidenceItem] = []

        queries = [query]
        normalized = self._normalize(query)
        if re.search(r"\bges\b", normalized):
            queries.append("güneş enerji santrali GES fotovoltaik")
        elif re.search(r"\bbess\b", normalized):
            queries.append("battery energy storage system BESS batarya enerji depolama")
        elif re.search(r"\bres\b", normalized):
            queries.append("rüzgar enerji santrali RES")
        elif re.search(r"\bhes\b", normalized):
            queries.append("hidroelektrik santral HES")

        for search_query in queries:
            try:
                for item in self._wikipedia_search(search_query, "tr"):
                    self._add_unique(evidence, item)
            except Exception:
                pass

        for item in list(evidence[:5]):
            if item.source != "Wikipedia (tr)":
                continue
            title = item.claim.split(":", 1)[0].strip()
            try:
                summary = self._wikipedia_summary(title, "tr", query)
                if summary:
                    self._add_unique(evidence, summary)
            except Exception:
                continue

        if len(evidence) < 2:
            try:
                for item in self._wikipedia_search(query, "en"):
                    self._add_unique(evidence, item)
            except Exception:
                pass

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

        evidence.sort(key=lambda item: item.confidence, reverse=True)
        return evidence[: self.max_evidence]

    @staticmethod
    def answer(question: str, evidence: list[EvidenceItem]) -> str | None:
        if not evidence:
            return None
        ranked = sorted(evidence, key=lambda item: item.confidence, reverse=True)
        if ranked[0].confidence < 0.60:
            return None
        top = ranked[0].claim.strip()
        if not top:
            return None
        definition_markers = (" nedir", " ne demek", " hakkında", " nasıl çalış")
        if any(marker in f" {question.lower()}" for marker in definition_markers):
            return top
        claims = [item.claim.strip() for item in ranked[:2] if item.claim.strip()]
        return "\n\n".join(claims) if claims else None
