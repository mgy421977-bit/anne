"""Guarded self-improvement workflow for ANNE.

The engine turns an approved implementation plan into a feature-branch change set,
then opens a pull request. It never writes to protected branches and never merges.
The workflow is intentionally explicit so reasoning and repository mutation remain
separable and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from anne.tools.github_repo import GitHubRepoTool


@dataclass(frozen=True)
class ChangeSpec:
    """One repository mutation in a self-improvement plan."""

    path: str
    content: str | None = None
    sha: str | None = None
    action: str = "update"  # create | update | delete
    message: str = "ANNE: apply self-improvement"


@dataclass(frozen=True)
class SelfImprovementPlan:
    """Complete, auditable mutation plan proposed after analysis."""

    task: str
    branch: str
    changes: tuple[ChangeSpec, ...]
    title: str
    body: str
    base: str = "main"


@dataclass
class SelfImprovementResult:
    """Outcome of applying a validated plan and opening its pull request."""

    branch: str
    commits: list[str] = field(default_factory=list)
    pull_request: dict[str, str | bool | None] | None = None


class SelfImprovementEngine:
    """Execute an approved ANNE code-improvement plan safely."""

    BRANCH_PREFIX = "anne/improve-"

    def __init__(self, github: GitHubRepoTool) -> None:
        self.github = github

    @classmethod
    def validate_plan(cls, plan: SelfImprovementPlan) -> None:
        branch = plan.branch.strip()
        if not branch.startswith(cls.BRANCH_PREFIX):
            raise ValueError(
                f"Self-improvement branches must start with {cls.BRANCH_PREFIX}"
            )
        if not plan.changes:
            raise ValueError("Self-improvement plan must contain at least one change")
        for change in plan.changes:
            action = change.action.lower().strip()
            if action not in {"create", "update", "delete"}:
                raise ValueError(f"Unsupported change action: {change.action}")
            if action in {"create", "update"} and change.content is None:
                raise ValueError(f"Content is required for {action}: {change.path}")

    def apply(
        self,
        plan: SelfImprovementPlan,
        *,
        create_branch: bool = True,
    ) -> SelfImprovementResult:
        """Apply the plan on a feature branch and open a pull request.

        Existing-file SHA values may be supplied by the planner. When omitted,
        the engine retrieves the current file SHA from the newly created branch
        immediately before update/delete, preventing stale writes.
        """
        self.validate_plan(plan)
        result = SelfImprovementResult(branch=plan.branch)

        if create_branch:
            branch_result = self.github.create_branch(
                plan.branch,
                from_ref=plan.base,
            )
            result.commits.append(branch_result["sha"])

        for change in plan.changes:
            action = change.action.lower().strip()
            if action == "create":
                assert change.content is not None
                written = self.github.create_file(
                    change.path,
                    change.content,
                    branch=plan.branch,
                    message=change.message,
                )
            else:
                current_sha = change.sha
                if not current_sha:
                    current = self.github.get_file(
                        change.path,
                        branch=plan.branch,
                    )
                    current_sha = current["sha"]
                if not current_sha:
                    raise RuntimeError(
                        f"Could not resolve current SHA for {action}: {change.path}"
                    )
                if action == "update":
                    assert change.content is not None
                    written = self.github.update_file(
                        change.path,
                        change.content,
                        sha=current_sha,
                        branch=plan.branch,
                        message=change.message,
                    )
                else:
                    written = self.github.delete_file(
                        change.path,
                        sha=current_sha,
                        branch=plan.branch,
                        message=change.message,
                    )
            commit_sha = str(written.get("commit_sha", ""))
            if commit_sha:
                result.commits.append(commit_sha)

        result.pull_request = self.github.create_pull_request(
            title=plan.title,
            head=plan.branch,
            base=plan.base,
            body=(
                f"## Self-improvement task\n{plan.task}\n\n"
                f"{plan.body}\n\n"
                "## Validation gate\n"
                "Changes were applied only on a feature branch. CI must validate "
                "the branch before human review. ANNE does not merge this PR."
            ),
        )
        return result

    @staticmethod
    def summarize(result: SelfImprovementResult) -> dict[str, Any]:
        """Return a compact machine-readable audit summary."""
        return {
            "branch": result.branch,
            "commits": list(result.commits),
            "pull_request": result.pull_request,
            "merged": False,
            "human_review_required": True,
        }
