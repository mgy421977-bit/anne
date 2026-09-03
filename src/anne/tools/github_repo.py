"""Read-only GitHub tools for the ANNE agent."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class GitHubRepoTool:
    """Small, read-only GitHub Contents/Search API client."""

    def __init__(self, token: str, repository: str, branch: str = "main") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        if "/" not in repository:
            raise ValueError("Repository must use owner/name format")
        self.token = token
        self.repository = repository
        self.branch = branch
        self.base = f"https://api.github.com/repos/{repository}"

    def _get(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ANNE-Windows-Tinker",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {exc.code}: {detail[:500]}") from exc

    def read_file(self, path: str) -> str:
        safe = path.strip().lstrip("/")
        if not safe or ".." in safe.split("/"):
            raise ValueError("Invalid repository path")
        encoded = urllib.parse.quote(safe, safe="/")
        data = self._get(f"{self.base}/contents/{encoded}?ref={urllib.parse.quote(self.branch)}")
        if data.get("type") != "file":
            raise ValueError(f"Not a file: {safe}")
        raw = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
        if len(raw) > 50000:
            return raw[:50000] + "\n...[truncated at 50,000 characters]"
        return raw

    def list_directory(self, path: str = "") -> list[str]:
        safe = path.strip().lstrip("/")
        if ".." in safe.split("/"):
            raise ValueError("Invalid repository path")
        encoded = urllib.parse.quote(safe, safe="/")
        suffix = f"/{encoded}" if encoded else ""
        data = self._get(f"{self.base}/contents{suffix}?ref={urllib.parse.quote(self.branch)}")
        if not isinstance(data, list):
            raise ValueError(f"Not a directory: {safe or '/'}")
        return [f"{item.get('type', 'unknown')}: {item.get('path', '')}" for item in data[:200]]

    def search_code(self, query: str) -> list[str]:
        if not query.strip():
            return []
        q = urllib.parse.quote(f"{query.strip()} repo:{self.repository}")
        data = self._get(f"https://api.github.com/search/code?q={q}&per_page=10")
        results = data.get("items", [])
        return [f"{item.get('path')}: {item.get('html_url')}" for item in results]
