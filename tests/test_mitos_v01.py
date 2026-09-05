from anne.core.global_workspace import GlobalWorkspace, WorkspaceItem
from anne.mythos.engine import ExplorationMode, MitosEngine
from anne.mythos.experience import ExperienceRecord, ExperienceStatus
from anne.mythos.discovery import DiscoveryDrive


def test_mitos_batch_is_bounded_and_reproducible():
    a = MitosEngine(seed=7).generate("create value with zero capital", 10)
    b = MitosEngine(seed=7).generate("create value with zero capital", 10)
    assert len(a) == 10
    assert [x.claim for x in a] == [x.claim for x in b]
    assert {x.mode for x in a} == set(ExplorationMode)


def test_low_probability_high_value_candidate_is_not_automatically_removed():
    candidates = MitosEngine(seed=1).generate("find a harmless opportunity", 8)
    candidate = candidates[0]
    assert 0.0 < candidate.probability < 1.0
    assert candidate.harm_risk == 0.0
    assert candidate.reversibility == 1.0


def test_experience_becomes_learning_evidence_only_after_outcome():
    record = ExperienceRecord("h1", "goal", "claim")
    assert not record.is_learning_evidence
    record.update_from_outcome("observed", 0.2, ExperienceStatus.VERIFIED, ["evidence-1"])
    assert record.is_learning_evidence
    assert record.confidence == 0.8


def test_workspace_keeps_high_priority_items_within_capacity():
    workspace = GlobalWorkspace(capacity=2)
    workspace.publish(WorkspaceItem("a", "low", salience=0.1))
    workspace.publish(WorkspaceItem("b", "high", salience=0.9))
    workspace.publish(WorkspaceItem("c", "mid", salience=0.5))
    assert len(workspace.items) == 2
    assert workspace.winners(1)[0].source == "b"


def test_discovery_drive_returns_safe_shortlist():
    drive = DiscoveryDrive(MitosEngine(seed=3))
    candidates = drive.generate("find a legal zero-capital service", 20)
    shortlist = drive.shortlist(candidates, 5)
    assert len(shortlist) <= 5
    assert all(c.harm_risk == 0.0 for c in shortlist)
