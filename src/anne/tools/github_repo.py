"""GitHub repository tools for the ANNE agent.

Reads are broadly available; repository mutations are intentionally restricted
from protected branches. ANNE should create a feature branch, make changes
there, run validation, and open a pull request rather than writing directly
to ``main`` or ``master``.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class GitHubRepoTool:
    """Small GitHub Contents/Search API client with guarded write support."""

    PROTECTED_BRANCHES = {"main", "master"}

    def __init__(self, token: str, repository: str, branch: str = "main") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        if "/" not in repository:
            raise ValueError("Repository must use owner/name format")
        self.token = token
        self.repository = repository
        self.branch = branch
        self.base = f"https://api.github.com/repos/{repository}"

    @staticmethod
    def _safe_path(path: str) -> str:
        safe = path.strip().lstrip("/")
        if not safe or ".." in safe.split("/"):
            raise ValueError("Invalid repository path")
        return safe

    @classmethod
    def _safe_branch(cls, branch: str | None) -> str:
        safe = (branch or "").strip()
        if not safe or safe == "HEAD" or ".." in safe.split("/"):
            raise ValueError("Invalid repository branch")
        return safe

    @classmethod
    def _writable_branch(cls, branch: str | None) -> str:
        safe = cls._safe_branch(branch)
        if safe.lower() in cls.PROTECTED_BRANCHES:
            raise PermissionError(
                f"Protected branch '{safe}' is read-only for ANNE write tools; "
                "create a feature branch first"
            )
        return safe

    def _request(self, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
        body = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ANNE-Windows-Tinker",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {exc.code}: {detail[:500]}") from exc

    def _get(self, url: str) -> Any:
        return self._request("GET", url)

    def read_file(self, path: str, branch: str | None = None) -> str:
        return str(self.get_file(path, branch=branch)["content"])

    def get_file(self, path: str, branch: str | None = None) -> dict[str, str]:
        safe = self._safe_path(path)
        ref = self._safe_branch(branch or self.branch)
        encoded = urllib.parse.quote(safe, safe="/")
        data = self._get(
            f"{self.base}/contents/{encoded}?ref={urllib.parse.quote(ref, safe='')}",
        )
        if data.get("type") != "file":
            raise ValueError(f"Not a file: {safe}")
        raw = base64.b64decode(data.get("content", "")).decode(
            "utf-8", errors="replace"
        )
        if len(raw) > 50000:
            raw = raw[:50000] + "\n...[truncated at 50,000 characters]"
        return {
            "path": safe,
            "branch": ref,
            "sha": str(data.get("sha", "")),
            "content": raw,
        }

    def list_directory(self, path: str = "", branch: str | None = None) -> list[str]:
        safe = path.strip().lstrip("/")
        if ".." in safe.split("/"):
            raise ValueError("Invalid repository path")
        ref = self._safe_branch(branch or self.branch)
        encoded = urllib.parse.quote(safe, safe="/")
        suffix = f"/{encoded}" if encoded else ""
        data = self._get(
            f"{self.base}/contents{suffix}?ref={urllib.parse.quote(ref, safe='')}",
        )
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

    def create_branch(self, branch: str, from_ref: str | None = None) -> dict[str, str]:
        new_branch = self._safe_branch(branch)
        if new_branch.lower() in self.PROTECTED_BRANCHES:
            raise ValueError(f"Cannot create protected branch name: {new_branch}")
        source = self._safe_branch(from_ref or self.branch)
        source_data = self._get(
            f"{self.base}/git/ref/heads/{urllib.parse.quote(source, safe='')}",
        )
        source_sha = str(source_data.get("object", {}).get("sha", ""))
        if not source_sha:
            raise RuntimeError(f"Could not resolve source branch: {source}")

        result = self._request(
            "POST",
            f"{self.base}/git/refs",
            {"ref": f"refs/heads/{new_branch}", "sha": source_sha},
        )
        return {"branch": new_branch, "sha": str(result.get("object", {}).get("sha", source_sha))}

    def create_file(
        self,
        path: str,
        content: str,
        branch: str | None = None,
        message: str = "ANNE: create file",
    ) -> dict[str, str]:
        safe = self._safe_path(path)
        target = self._writable_branch(branch or self.branch)
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        result = self._request(
            "PUT",
            f"{self.base}/contents/{urllib.parse.quote(safe, safe='/')}",
            {"message": message, "content": encoded, "branch": target},
        )
        return {
            "path": safe,
            "branch": target,
            "commit_sha": str(result.get("commit", {}).get("sha", "")),
            "content_sha": str(result.get("content", {}).get("sha", "")),
        }

    def update_file(
        self,
        path: str,
        content: str,
        sha: str,
        branch: str | None = None,
        message: str = "ANNE: update file",
    ) -> dict[str, str]:
        safe = self._safe_path(path)
        target = self._writable_branch(branch or self.branch)
        if not sha.strip():
            raise ValueError("Current file SHA is required for an update")
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        result = self._request(
            "PUT",
            f"{self.base}/contents/{urllib.parse.quote(safe, safe='/')}",
            {
                "message": message,
                "content": encoded,
                "sha": sha,
                "branch": target,
            },
        )
        return {
            "path": safe,
            "branch": target,
            "commit_sha": str(result.get("commit", {}).get("sha", "")),
            "content_sha": str(result.get("content", {}).get("sha", "")),
        }

    def delete_file(
        self,
        path: str,
        sha: str,
        branch: str | None = None,
        message: str = "ANNE: delete file",
    ) -> dict[str, str]:
        safe = self._safe_path(path)
        target = self._writable_branch(branch or self.branch)
        if not sha.strip():
            raise ValueError("Current file SHA is required for deletion")
        result = self._request(
            "DELETE",
            f"{self.base}/contents/{urllib.parse.quote(safe, safe='/')}",
            {"message": message, "sha": sha, "branch": target},
        )
        return {
            "path": safe,
            "branch": target,
            "commit_sha": str(result.get("commit", {}).get("sha", "")),
        }

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict[str, str | bool | None]:
        safe_head = self._writable_branch(head)
        safe_base = self._safe_branch(base)
        if not title.strip():
            raise ValueError("Pull request title is required")
        result = self._request(
            "POST",
            f"{self.base}/pulls",
            {
                "title": title.strip(),
                "head": safe_head,
                "base": safe_base,
                "body": body,
            },
        )
        return {
            "number": result.get("number"),
            "url": result.get("html_url"),
            "title": result.get("title"),
            "head": safe_head,
            "base": safe_base,
            "state": result.get("state"),
        }
