"""Resilient public-web retrieval for ANNE.

The existing WebResearcher is intentionally conservative, but a long question
can contain many concepts and therefore score too low as one search query.
This adapter decomposes long questions into bounded, generic search probes and
reuses the existing evidence model. It does not add domain-specific facts.
"""
from __future__ import annotations

import re
from typing import Iterable

from .evidence import EvidenceItem
from .web_research import WebResearcher


class ReliableWebResearcher(WebResearcher):
    """Use the normal researcher first, then focused probes when needed."""

    max_focus_queries = 4
    min_focus_terms = 3
    max_focus_terms = 8

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

    def research(self, query: str) -> list[EvidenceItem]:
        query = query.strip()
        if not query:
            return []

        primary = super().research(query)
        if len(primary) >= 2:
            return primary

        collected = list(primary)
        for probe in self._focus_queries(query):
            try:
                collected.extend(super().research(probe))
            except Exception:
                continue
            merged = self._merge(collected, self.max_evidence)
            if len(merged) >= 4:
                return merged

        return self._merge(collected, self.max_evidence)


__all__ = ["ReliableWebResearcher"]
