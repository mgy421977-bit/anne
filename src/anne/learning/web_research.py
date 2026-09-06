"""Generic public-web research for ANNE.

The web layer is topic-agnostic. It searches unknown questions without
hard-coding GES, BESS, RES, HES, EPC, or any other domain vocabulary.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .evidence import EvidenceItem


class _DuckDuckGoParser(HTMLParser):
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
    """Generic public-web retrieval with conservative evidence filtering."""

    timeout = 8.0
    minimum_relevance = 0.28
    max_evidence = 8

    # Compatibility marker for older local modules. No domain vocabulary is
    # stored here; the retrieval engine remains domain-neutral.
    _ACRONYM_EXPANSIONS: dict[str, set[str]] = {}

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
            headers={"User-Agent": "ANNE-AI/0.4 (+generic-public-web-research)"},
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
        clean = re.sub(r"[?!.]+$", "", query.strip()).strip()
        variants = [clean]
        normalized = cls._normalize(clean)
        if normalized and normalized != clean.lower():
            variants.append(normalized)

        lowered = clean.lower()
        if " nedir" in f" {lowered}":
            subject = re.sub(r"\bnedir\b", "", clean, flags=re.I).strip()
            if subject:
                variants.extend([subject, f"{subject} definition"])
        elif " kimdir" in f" {lowered}":
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
    def _acronym_token(cls, query: str) -> str | None:
        tokens = [
            token for token in re.findall(r"\b[A-Za-zÇĞİÖŞÜçğıöşü]{2,12}\b", query)
            if token.lower() not in cls._STOPWORDS
        ]
        if len(tokens) == 1 and tokens[0].isupper():
            return tokens[0]
        return None

    @classmethod
    def _acronym_matches(cls, query: str, title: str, claim: str) -> bool:
        """Require semantic acronym evidence, not just an uppercase collision."""
        acronym = cls._acronym_token(query)
        if acronym is None:
            return True

        title_text = title.strip()
        body = claim.strip()
        if title_text and re.match(rf"^{re.escape(title_text)}\s*:\s*", body, flags=re.I):
            body = re.sub(
                rf"^{re.escape(title_text)}\s*:\s*", "", body, count=1, flags=re.I
            )

        full_text = f"{title_text} {body}"
        token = re.escape(acronym)

        # Explicit expansion/definition patterns are strongest and domain-neutral.
        expansion_patterns = (
            rf"\([^)]{{2,120}}\b{token}\b[^)]{{0,120}}\)",
            rf"\b{token}\b\s+(?:stands?\s+for|means|refers?\s+to)\b",
            rf"\b{token}\b\s+(?:is|are)\s+(?:an?|the)\b",
            rf"\b(?:abbreviation|acronym)\s+(?:for|of)\b[^.{{0,120}}]*\b{token}\b",
        )
        if any(re.search(pattern, full_text, flags=re.I) for pattern in expansion_patterns):
            return True

        # A bare uppercase occurrence is not sufficient. It must have a
        # definition-like contextual signal, otherwise disambiguation pages such
        # as "Bess or BESS may refer to..." are rejected.
        uppercase_occurrences = re.findall(rf"\b{token}\b", full_text)
        if uppercase_occurrences:
            definition_markers = (
                "battery", "system", "energy", "storage", "computer", "protocol",
                "standard", "technology", "software", "hardware", "network", "method",
                "process", "device", "service", "organization", "programme", "program",
                "platform", "model", "algorithm", "term", "abbreviation", "acronym",
                "sistem", "teknoloji", "standardi", "terim",
            )
            normalized = cls._normalize(full_text)
            if any(marker in normalized for marker in definition_markers):
                return True

        normalized_body = cls._normalize(body)
        normalized_token = cls._normalize(acronym)
        occurrences = len(re.findall(rf"\b{re.escape(normalized_token)}\b", normalized_body))
        return occurrences >= 2

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
        if not cls._acronym_matches(query, title, claim):
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

        for search_query in variants:
            try:
                for item in self._wikipedia_search(search_query, "tr"):
                    self._add_unique(evidence, item)
            except Exception:
                continue

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

        if len(evidence) < 3:
            for search_query in variants[:2]:
                try:
                    for item in self._wikipedia_search(search_query, "en"):
                        self._add_unique(evidence, item)
                except Exception:
                    continue

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
        claims = [item.claim.strip() for item in ranked[:2] if item.claim.strip()]
        return "\n\n".join(dict.fromkeys(claims)) if claims else None
