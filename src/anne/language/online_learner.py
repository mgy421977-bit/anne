"""On-demand Turkish vocabulary acquisition for ANNE.

Uses the public Turkish Wiktionary MediaWiki API for machine-readable lookup.
The TDK dictionary is kept as the human-reference source in LanguageEngine.
Unknown words are learned only when requested; no model weights are changed.
"""
from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


class TurkishOnlineLearner:
    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout
        self.cache: dict[str, dict[str, Any]] = {}

    def lookup(self, word: str) -> dict[str, Any] | None:
        word = word.strip().lower()
        if not word:
            return None
        if word in self.cache:
            return dict(self.cache[word])
        url = (
            "https://tr.wiktionary.org/w/api.php?action=query&prop=extracts"
            f"&explaintext=1&redirects=1&titles={quote(word)}&format=json"
        )
        try:
            req = Request(url, headers={"User-Agent": "ANNE-AI/0.6 language learner"})
            with urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            pages = payload.get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            extract = html.unescape(page.get("extract", "")).strip()
            if not extract or page.get("missing") is not None:
                return None
            pos = "bilinmiyor"
            for candidate in ("isim", "fiil", "sıfat", "zarf", "zamir", "bağlaç", "edat", "ünlem"):
                if re.search(rf"\b{re.escape(candidate)}\b", extract, re.I):
                    pos = candidate
                    break
            item = {
                "word": word,
                "root": word,
                "pos": pos,
                "meaning": extract.splitlines()[0][:500],
                "source": "tr.wiktionary.org",
            }
            self.cache[word] = item
            return dict(item)
        except Exception:
            return None

    def learn_unknown(self, words: list[str]) -> list[dict[str, Any]]:
        learned: list[dict[str, Any]] = []
        for word in dict.fromkeys(words):
            item = self.lookup(word)
            if item:
                learned.append(item)
        return learned


__all__ = ["TurkishOnlineLearner"]
