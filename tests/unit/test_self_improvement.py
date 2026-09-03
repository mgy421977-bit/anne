from __future__ import annotations

from typing import Any

import pytest

from anne.agent.self_improvement import (
    ChangeSpec,
    SelfImprovementEngine,
    SelfImprovementPlan,
)


class _FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def create_branch(self, branch: str, from_ref: str | None = None) -> dict[str, str]:
        self.calls.append(("create_branch", (branch,), {"from_ref": from_ref}))
        return {"branch": branch, "sha": "branch-sha"}

    def get_file(self, path: str, branch: str) -> dict[str, str]:
        self.calls.append(("get_file", (path,), {"branch": branch}))
        return {"path": path, "branch": branch, "sha": "resolved-sha", "content": "old"}

    def create_file(self, path: str, content: str, branch: str, message: str) -> dict[str, str]:
        self.calls.append(("create_file", (path, content), {"branch": branch, "message": message}))
        return {"path": path, "branch": branch, "commit_sha": "create-sha"}

    def update_file(self, path: str, content: str, sha: str, branch: str, message: str) -> dict[str, str]:
        self.calls.append(
            ("update_file", (path, content, sha), {"branch": branch, "message": message})
        )
        return {"path": path, "branch": branch, "commit_sha": "update-sha"}

    def delete_file(self, path: str, sha: str, branch: str, message: str) -> dict[str, str]:
        self.calls.append(
            ("delete_file", (path, sha), {"branch": branch, "message": message})
        )
        return {"path": path, "branch": branch, "commit_sha": "delete-sha"}

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, str | bool | None]:
        self.calls.append(
            ("create_pull_request", (title, head, base, body), {})
        )
        return {"number": 99, "url": "https://example.test/pr/99", "state": "open"}


def test_plan_requires_feature_branch() -> None:
    plan = SelfImprovementPlan(
        task="test",
        branch="main",
        changes=(ChangeSpec(path="src/test.py", content="x", action="create"),),
        title="test",
        body="test",
    )
    with pytest.raises(ValueError, match="must start"):
        SelfImprovementEngine.validate_plan(plan)


def test_apply_resolves_missing_sha_before_update() -> None:
    github = _FakeGitHub()
    engine = SelfImprovementEngine(github)  # type: ignore[arg-type]
    plan = SelfImprovementPlan(
        task="Improve SEE",
        branch="anne/improve-see",
        changes=(
            ChangeSpec(
                path="src/existing.py",
                content="updated",
                action="update",
                message="fix: improve module",
            ),
        ),
        title="feat: improve SEE",
        body="Improve multi-hypothesis reasoning.",
    )

    result = engine.apply(plan)

    assert result.commits == ["branch-sha", "update-sha"]
    assert [call[0] for call in github.calls] == [
        "create_branch",
        "get_file",
        "update_file",
        "create_pull_request",
    ]
    assert github.calls[2][1][2] == "resolved-sha"


def test_apply_creates_branch_applies_changes_and_opens_pr() -> None:
    github = _FakeGitHub()
    engine = SelfImprovementEngine(github)  # type: ignore[arg-type]
    plan = SelfImprovementPlan(
        task="Improve SEE",
        branch="anne/improve-see",
        changes=(
            ChangeSpec(
                path="src/new.py",
                content="print('x')",
                action="create",
                message="feat: add new module",
            ),
            ChangeSpec(
                path="src/existing.py",
                content="updated",
                sha="current-sha",
                action="update",
                message="fix: improve module",
            ),
        ),
        title="feat: improve SEE",
        body="Improve multi-hypothesis reasoning.",
    )

    result = engine.apply(plan)

    assert result.branch == "anne/improve-see"
    assert result.commits == ["branch-sha", "create-sha", "update-sha"]
    assert result.pull_request is not None
    assert result.pull_request["number"] == 99
    assert [call[0] for call in github.calls] == [
        "create_branch",
        "create_file",
        "update_file",
        "create_pull_request",
    ]
    assert result.pull_request["state"] == "open"


def test_summary_explicitly_requires_human_review() -> None:
    github = _FakeGitHub()
    engine = SelfImprovementEngine(github)  # type: ignore[arg-type]
    result = engine.apply(
        SelfImprovementPlan(
            task="test",
            branch="anne/improve-test",
            changes=(ChangeSpec(path="src/test.py", content="x", action="create"),),
            title="test",
            body="body",
        )
    )
    summary = engine.summarize(result)
    assert summary["merged"] is False
    assert summary["human_review_required"] is True
