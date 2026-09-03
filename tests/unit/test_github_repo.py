from __future__ import annotations

from typing import Any

import pytest

from anne.tools.github_repo import GitHubRepoTool


def _tool() -> GitHubRepoTool:
    return GitHubRepoTool("token", "owner/repo", "main")


def test_protected_branches_cannot_be_mutated() -> None:
    tool = _tool()

    with pytest.raises(PermissionError, match="protected branch"):
        tool.create_file("src/test.py", "print('x')", branch="main", message="test")

    with pytest.raises(PermissionError, match="protected branch"):
        tool.delete_file("src/test.py", "sha", branch="master", message="test")


def test_update_requires_current_sha() -> None:
    tool = _tool()

    with pytest.raises(ValueError, match="SHA"):
        tool.update_file("src/test.py", "new", "", branch="feature/test", message="test")


def test_create_branch_resolves_source_sha_and_creates_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tool()
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_get(url: str) -> dict[str, Any]:
        calls.append(("GET", url, None))
        return {"object": {"sha": "source-sha"}}

    def fake_request(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        calls.append((method, url, payload))
        return {"object": {"sha": "source-sha"}}

    monkeypatch.setattr(tool, "_get", fake_get)
    monkeypatch.setattr(tool, "_request", fake_request)

    result = tool.create_branch("feature/test", from_ref="main")

    assert result == {"branch": "feature/test", "sha": "source-sha"}
    assert calls[1][0] == "POST"
    assert calls[1][2] == {
        "ref": "refs/heads/feature/test",
        "sha": "source-sha",
    }


def test_file_mutations_send_expected_contents_api_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tool()
    requests: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        requests.append((method, url, payload))
        if method == "DELETE":
            return {"commit": {"sha": "commit-delete"}}
        return {
            "commit": {"sha": f"commit-{method.lower()}"},
            "content": {"sha": "content-sha"},
        }

    monkeypatch.setattr(tool, "_request", fake_request)

    created = tool.create_file(
        "src/new.py",
        "hello",
        branch="feature/test",
        message="feat: add file",
    )
    updated = tool.update_file(
        "src/new.py",
        "updated",
        "old-sha",
        branch="feature/test",
        message="fix: update file",
    )
    deleted = tool.delete_file(
        "src/new.py",
        "new-sha",
        branch="feature/test",
        message="refactor: remove file",
    )

    assert created["commit_sha"] == "commit-put"
    assert updated["content_sha"] == "content-sha"
    assert deleted["commit_sha"] == "commit-delete"
    assert requests[0][2]["branch"] == "feature/test"
    assert requests[1][2]["sha"] == "old-sha"
    assert requests[2][2]["sha"] == "new-sha"


def test_create_pull_request_never_allows_protected_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tool()
    monkeypatch.setattr(tool, "_request", lambda *args, **kwargs: {})

    with pytest.raises(PermissionError, match="protected branch"):
        tool.create_pull_request(
            "test",
            head="main",
            base="main",
            body="body",
        )
