"""Generic public-web research for ANNE.

The web layer is deliberately topic-agnostic. It must work for energy,
science, people, companies, regulations, products, software, history, or
any other unknown question. Domain-specific knowledge belongs in evidence,
not in the retrieval engine.
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
    """Search public web sources without hard-coding domain-specific topics."""

    timeout = 8.0
    minimum_relevance = 0.28
    max_evidence = 8

    _STOPWORDS = {
        "ve", "veya", "ile", "bir", "bu", "şu", "için", "olan", "olarak",
        "nedir", "nasıl", "neden", "ne", "hangi", "hakkında", "bilgi",
        "anlat", "açıkla", "mı", "mi", "mu", "mü", "the", "and", "what",
        "how", "why", "about", "is", "are", "a", "an", "of", "to", "in",
    }

    @staticmethod
    def _get_text(url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ANNE-AI/0.3 (+generic-public-web-research)"},
        )
        with urllib.request.urlopen(request, timeout=WebResearcher.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    @classmethod
    def _get_json(cls, url: str) -> dict:
        return json.loads(cls._get_text(url))

    @staticmethod
    def _clean_html(text: str) -> str:
        text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = (
            text.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
            .replace("ü", "u").replace("ö", "o").replace("ç", "c")
        )
        return re.sub(r"[^a-z0-9]+", " ", text).strip()

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {
            token for token in cls._normalize(text).split()
            if len(token) > 1 and token not in cls._STOPWORDS
        }

    @classmethod
    def _query_variants(cls, query: str) -> list[str]:
        """Create generic search variants; no domain-specific vocabulary."""
        clean = re.sub(r"[?!.]+$", "", query.strip()).strip()
        variants = [clean]
        normalized = cls._normalize(clean)
        if normalized != clean.lower():
            variants.append(normalized)

        # Definition/identity variants help search engines without requiring
        # ANNE to know anything about the subject in advance.
        lowered = clean.lower()
        if lowered.endswith("nedir") or " nedir" in lowered:
            subject = re.sub(r"\bnedir\b", "", clean, flags=re.I).strip()
            if subject:
                variants.extend([f"{subject} definition", subject])
        elif lowered.endswith("kimdir") or " kimdir" in lowered:
            subject = re.sub(r"\bkimdir\b", "", clean, flags=re.I).strip()
            if subject:
                variants.extend([subject, f"{subject} biography"])
        elif "nasıl çalış" in lowered or "nasil calis" in lowered:
            subject = re.sub(r"nasıl çalışır|nasil calisir", "", clean, flags=re.I).strip()
            if subject:
                variants.extend([subject, f"{subject} how it works"])

        result: list[str] = []
        seen: set[str] = set()
        for item in variants:
            item = item.strip()
            if item and item.lower() not in seen:
                seen.add(item.lower())
                result.append(item)
        return result[:4]

    @classmethod
    def _is_acronym_query(cls, query: str) -> bool:
        tokens = [t for t in re.findall(r"\b[A-Za-zÇĞİÖŞÜçğıöşü]{2,10}\b", query) if t.lower() not in cls._STOPWORDS]
        return len(tokens) == 1 and tokens[0].isupper()

    @classmethod
    def _acronym_matches(cls, query: str, text: str) -> bool:
        """Avoid title-case word collisions for acronym-only questions.

        Example: ``BESS nedir?`` must not accept a result about the name
        ``Bess``. This is a generic lexical safety rule, not a BESS-specific
        knowledge rule.
        """
        if not cls._is_acronym_query(query):
            return True
        acronym = next(
            token for token in re.findall(r"\b[A-Za-zÇĞİÖŞÜçğıöşü]{2,10}\b", query)
            if token.lower() not in cls._STOPWORDS
        )
        if re.search(rf"\b{re.escape(acronym)}\b", text):
            return True
        return bool(re.search(rf"\b{re.escape(acronym.lower())}\b", cls._normalize(text))) and acronym.lower() == cls._normalize(acronym)

    @classmethod
    def _relevance(cls, query: str, claim: str, title: str = "") -> float:
        query_terms = cls._tokens(query)
        text = f"{title} {claim}"
        text_terms = cls._tokens(text)
        if not query_terms or not text_terms:
            return 0.0
        direct = len(query_terms & text_terms) / max(1, len(query_terms))
        title_terms = cls._tokens(title)
        title_overlap = len(query_terms & title_terms) / max(1, len(query_terms))
        phrase = cls._normalize(query)
        normalized_text = cls._normalize(text)
        exact_phrase = bool(phrase) and phrase in normalized_text
        score = 0.62 * direct + 0.23 * title_overlap
        if exact_phrase:
            score += 0.15
        return min(1.0, score)

    @classmethod
    def _is_relevant(cls, query: str, claim: str, title: str = "") -> bool:
        text = f"{title} {claim}"
        if not cls._acronym_matches(query, text):
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
        url = (
            f"https://{language}.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={encoded}&format=json&srlimit=6"
        )
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
            items.append(EvidenceItem(
                source=f"Wikipedia ({language})",
                claim=claim,
                kind="web",
                provenance=url,
                confidence=min(0.90, 0.50 + score * 0.40),
            ))
        return items

    def _wikipedia_summary(self, title: str, language: str, query: str) -> EvidenceItem | None:
        encoded_title = urllib.parse.quote(title.replace(" ", "_"), safe="_")
        url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        data = self._get_json(url)
        extract = self._clean_html(str(data.get("extract", "")))
        if not extract or not self._is_relevant(query, extract, title):
            return None
        score = self._relevance(query, extract, title)
        return EvidenceItem(
            source=f"Wikipedia ({language})",
            claim=f"{title}: {extract[:2200]}",
            kind="web",
            provenance=url,
            confidence=min(0.95, 0.62 + score * 0.33),
        )

    def _duckduckgo_instant(self, query: str) -> EvidenceItem | None:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
        data = self._get_json(url)
        abstract = self._clean_html(str(data.get("AbstractText", "")))
        if not abstract or not self._is_relevant(query, abstract):
            return None
        score = self._relevance(query, abstract)
        return EvidenceItem(
            source="DuckDuckGo Instant Answer",
            claim=abstract[:2200],
            kind="web",
            provenance=url,
            confidence=min(0.86, 0.46 + score * 0.40),
        )

    def _duckduckgo_search(self, query: str) -> list[EvidenceItem]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        parser = _DuckDuckGoParser()
        parser.feed(self._get_text(url))
        items: list[EvidenceItem] = []
        for title, href, snippet in parser.results[:12]:
            claim = f"{title}: {snippet}" if snippet else title
            if not self._is_relevant(query, claim, title):
                continue
            score = self._relevance(query, claim, title)
            items.append(EvidenceItem(
                source="DuckDuckGo Web Search",
                claim=claim[:2200],
                kind="web",
                provenance=href or url,
                confidence=min(0.84, 0.44 + score * 0.40),
            ))
        return items

    def research(self, query: str) -> list[EvidenceItem]:
        query = query.strip()
        if not query:
            return []
        evidence: list[EvidenceItem] = []
        variants = self._query_variants(query)

        # Search every unknown question through the same generic retrieval path.
        # No GES/BESS/RES/etc. routing is required here.
        for search_query in variants:
            try:
                for item in self._wikipedia_search(search_query, "tr"):
                    self._add_unique(evidence, item)
            except Exception:
                continue

        # Enrich only the strongest discovered Wikipedia candidates.
        for item in list(evidence[:6]):
            if not item.source.startswith("Wikipedia"):
                continue
            title = item.claim.split(":", 1)[0].strip()
            language = "tr" if "(tr)" in item.source else "en"
            try:
                summary = self._wikipedia_summary(title, language, query)
                if summary:
                    self._add_unique(evidence, summary)
            except Exception:
                continue

        # English Wikipedia is a generic fallback, not a domain-specific rescue.
        if len(evidence) < 3:
            for search_query in variants[:2]:
                try:
                    for item in self._wikipedia_search(search_query, "en"):
                        self._add_unique(evidence, item)
                except Exception:
                    continue

        # DuckDuckGo provides a second independent public-web path.
        for search_query in variants[:2]:
            try:
                item = self._duckduckgo_instant(search_query)
                if item:
                    self._add_unique(evidence, item)
            except Exception:
                continue
            try:
                for item in self._duckduckgo_search(search_query):
                    self._add_unique(evidence, item)
            except Exception:
                continue

        evidence.sort(key=lambda item: item.confidence, reverse=True)
        return evidence[: self.max_evidence]

    @staticmethod
    def answer(question: str, evidence: list[EvidenceItem]) -> str | None:
        """Return a bounded evidence-based answer candidate.

        This is intentionally conservative. If web evidence is not strong
        enough, KnowledgeResolver escalates to OpenRouter and then Gemini.
        """
        if not evidence:
            return None
        ranked = sorted(evidence, key=lambda item: item.confidence, reverse=True)
        if ranked[0].confidence < 0.60:
            return None

        top = ranked[0].claim.strip()
        if not top:
            return None

        question_lower = question.lower()
        definition_markers = (" nedir", " ne demek", " hakkında", " nasıl çalış")
        if any(marker in f" {question_lower}" for marker in definition_markers):
            return top

        claims: list[str] = []
        for item in ranked[:2]:
            claim = item.claim.strip()
            if claim and claim not in claims:
                claims.append(claim)
        return "\n\n".join(claims) if claims else None
