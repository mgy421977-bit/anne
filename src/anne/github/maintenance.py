"""Safe GitHub branch maintenance using a user-supplied token.

The token is read only from GITHUB_TOKEN and is never persisted by ANNE.
Destructive operations require an explicit apply=True call and are limited to
branches that no longer contain commits absent from the configured base branch.
Open PR head branches and the default branch are never candidates for deletion.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class MaintenancePlan:
    base_branch: str
    candidates: tuple[str, ...]
    protected: tuple[str, ...]


class GitHubMaintenance:
    def __init__(self, owner: str, repo: str, *, token: str | None = None, timeout: float = 10.0) -> None:
        self.owner = owner
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout = timeout
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

    def _request(self, method: str, path: str) -> object:
        request = Request(
            f"https://api.github.com/repos/{self.owner}/{self.repo}{path}",
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except HTTPError as exc:
            raise RuntimeError(f"GitHub API error {exc.code} on {method} {path}") from exc

    def plan_merged_cleanup(self, *, base_branch: str = "main") -> MaintenancePlan:
        repo = self._request("GET", "")
        default_branch = repo.get("default_branch", "main") if isinstance(repo, dict) else "main"
        branches = self._request("GET", "/branches?per_page=100")
        open_prs = self._request("GET", "/pulls?state=open&per_page=100")
        open_heads = {
            pr.get("head", {}).get("ref")
            for pr in open_prs if isinstance(pr, dict)
        }
        protected = {default_branch, base_branch, *open_heads}
        candidates: list[str] = []
        for item in branches if isinstance(branches, list) else []:
            name = item.get("name")
            if not name or name in protected:
                continue
            comparison = self._request("GET", f"/compare/{name}...{base_branch}")
            if isinstance(comparison, dict) and comparison.get("status") == "behind" and comparison.get("ahead_by") == 0:
                candidates.append(name)
        return MaintenancePlan(base_branch, tuple(sorted(candidates)), tuple(sorted(protected)))

    def delete_branch(self, branch: str, *, apply: bool = False) -> str:
        if branch in {"main", "master"}:
            raise ValueError("refusing to delete a default/protected branch")
        if not apply:
            return f"DRY-RUN: would delete {branch}"
        self._request("DELETE", f"/git/refs/heads/{branch}")
        return f"DELETED: {branch}"

    def apply_plan(self, plan: MaintenancePlan, *, apply: bool = False) -> tuple[str, ...]:
        return tuple(self.delete_branch(branch, apply=apply) for branch in plan.candidates)


__all__ = ["GitHubMaintenance", "MaintenancePlan"]
