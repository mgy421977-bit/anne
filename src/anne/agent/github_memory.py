"""GitHub-backed long-term memory for ANNE.

Each learning is stored as a separate timestamped JSON document under /memory.
No API keys or access tokens are ever written to memory.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any


class GitHubMemory:
    """Small GitHub Contents API client used as ANNE's persistent memory store."""

    def __init__(self, token: str, repository: str, branch: str = "main") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        if "/" not in repository:
            raise ValueError("Repository must be in owner/name form")
        self.token = token
        self.repository = repository
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repository}"

    def _request(self, path: str) -> Any:
        request = urllib.request.Request(
            self.base_url + path,
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
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {exc.code}: {body[:300]}") from exc

    def recent(self, limit: int = 8) -> list[dict[str, Any]]:
        """Return the newest memory entries by filename."""
        try:
            items = self._request(f"/contents/memory?ref={self.branch}")
        except RuntimeError as exc:
            if "404" in str(exc):
                return []
            raise
        files = [item for item in items if item.get("type") == "file" and item["name"].endswith(".json")]
        files.sort(key=lambda item: item["name"], reverse=True)
        memories: list[dict[str, Any]] = []
        for item in files[:limit]:
            data = self._request(f"/contents/{item['path']}?ref={self.branch}")
            import base64
            raw = base64.b64decode(data["content"]).decode("utf-8")
            memories.append(json.loads(raw))
        return memories

    def context(self, limit: int = 8) -> str:
        memories = self.recent(limit=limit)
        if not memories:
            return "No persistent memories have been recorded yet."
        lines = []
        for memory in memories:
            lines.append(
                f"[{memory.get('timestamp', '')}] USER: {memory.get('user_input', '')}\n"
                f"LEARNING: {memory.get('learning', '')}\n"
                f"RESPONSE: {memory.get('response', '')}"
            )
        return "\n\n---\n\n".join(lines)

    def save(self, user_input: str, response: str, learning: str, confidence: float = 0.5) -> str:
        """Persist one interaction as a new file; never mutate old memory."""
        timestamp = datetime.now(UTC)
        stamp = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
        path = f"memory/{stamp}.json"
        payload = {
            "schema_version": 1,
            "timestamp": timestamp.isoformat(),
            "agent": "ANNE",
            "user_input": user_input[:12000],
            "response": response[:20000],
            "learning": learning[:12000],
            "confidence": max(0.0, min(1.0, float(confidence))),
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        encoded = __import__("base64").b64encode(content.encode("utf-8")).decode("ascii")
        body = json.dumps(
            {"message": "memory: record ANNE learning", "content": encoded, "branch": self.branch}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/contents/{path}",
            data=body,
            method="PUT",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "ANNE-Windows-Tinker",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response_obj:
                result = json.loads(response_obj.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub memory write failed {exc.code}: {error[:300]}") from exc
        return str(result.get("content", {}).get("path", path))
