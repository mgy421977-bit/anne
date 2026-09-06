from anne.repository_governance import BranchAction, BranchEvidence, BranchRisk, RepositoryGovernor


def test_default_branch_is_never_deletable() -> None:
    finding = RepositoryGovernor().evaluate(BranchEvidence(name="main", is_default=True, duplicate_of="other"))
    assert finding.action is BranchAction.KEEP
    assert finding.risk is BranchRisk.CRITICAL


def test_unique_work_is_preserved() -> None:
    finding = RepositoryGovernor().evaluate(
        BranchEvidence(name="research", has_unique_files=True, duplicate_of="other", preserved_elsewhere=True)
    )
    assert finding.action is BranchAction.KEEP


def test_open_pr_is_preserved() -> None:
    finding = RepositoryGovernor().evaluate(
        BranchEvidence(name="feature", has_open_pr=True, duplicate_of="other", preserved_elsewhere=True)
    )
    assert finding.action is BranchAction.KEEP


def test_duplicate_with_preserved_copy_can_be_deleted() -> None:
    finding = RepositoryGovernor().evaluate(
        BranchEvidence(
            name="old-copy",
            duplicate_of="main",
            preserved_elsewhere=True,
            last_activity_days=30,
        )
    )
    assert finding.action is BranchAction.DELETE
    assert finding.risk is BranchRisk.LOW


def test_duplicate_without_preservation_must_be_archived() -> None:
    finding = RepositoryGovernor().evaluate(BranchEvidence(name="old-copy", duplicate_of="main"))
    assert finding.action is BranchAction.ARCHIVE
    assert finding.risk is BranchRisk.HIGH


def test_unknown_branch_is_review() -> None:
    finding = RepositoryGovernor().evaluate(BranchEvidence(name="unknown"))
    assert finding.action is BranchAction.REVIEW
