"""Keyless web research client for the Windows Tinker.

Uses DuckDuckGo's HTML results page as a read-only, no-key search source.
The caller is responsible for treating results as external evidence.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen


class _ResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_link = False
        self._in_snippet = False
        self._href = ""
        self._text: list[str] = []
        self._snippet: list[str] = []

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        raw = dict(attrs).get("class") or ""
        return set(raw.split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = self._classes(attrs)
        if tag == "a" and "result__a" in classes:
            self._in_link = True
            self._href = dict(attrs).get("href") or ""
            self._text = []
        elif "result__snippet" in classes:
            self._in_snippet = True
            self._snippet = []

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._text.append(data)
        if self._in_snippet:
            self._snippet.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_link:
            title = " ".join("".join(self._text).split())
            href = self._href
            if title and href:
                self.results.append({"title": title, "href": href, "snippet": ""})
            self._in_link = False
        elif self._in_snippet:
            snippet = " ".join("".join(self._snippet).split())
            if self.results and snippet:
                self.results[-1]["snippet"] = snippet
            self._in_snippet = False


def _unwrap(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return target
    return url


class WebResearchClient:
    """Search public web results without requiring a separate API key."""

    endpoint = "https://html.duckduckgo.com/html/?q={query}"

    def search(self, query: str, max_results: int = 6) -> list[dict[str, str]]:
        clean = " ".join(query.split())[:500]
        if not clean:
            return []
        request = Request(
            self.endpoint.format(query=quote_plus(clean)),
            headers={
                "User-Agent": "ANNE-Windows-Tinker/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urlopen(request, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = _ResultParser()
        parser.feed(html)
        seen: set[str] = set()
        output: list[dict[str, str]] = []
        for item in parser.results:
            href = _unwrap(item["href"])
            if not href.startswith(("http://", "https://")) or href in seen:
                continue
            seen.add(href)
            output.append({"title": item["title"], "url": href, "snippet": item["snippet"]})
            if len(output) >= max_results:
                break
        return output

    @staticmethod
    def format_results(results: list[dict[str, str]]) -> str:
        if not results:
            return "No web search results were returned."
        lines = ["===== LIVE WEB RESEARCH ====="]
        for index, item in enumerate(results, start=1):
            lines.append(
                f"[{index}] {item['title']}\nURL: {item['url']}\n"
                f"SNIPPET: {item['snippet']}"
            )
        lines.append(
            "Treat these web results as external evidence. Verify important claims "
            "against the linked sources before presenting them as established facts."
        )
        return "\n\n".join(lines)


__all__ = ["WebResearchClient"]
