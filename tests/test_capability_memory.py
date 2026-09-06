from pathlib import Path

from anne.learning.capability_memory import CapabilityMemory
from anne.learning.evidence import EvidenceItem, LearningCandidate
from anne.learning.percentage import PercentageLearner


class StubResearcher:
    def research(self, query: str):
        return [
            EvidenceItem(
                source="stub",
                claim="A percentage is a fraction out of 100.",
                kind="web",
                provenance="test",
                confidence=1.0,
            )
        ]


def test_promoted_capability_persists_and_reloads(tmp_path: Path) -> None:
    memory = CapabilityMemory(tmp_path / "capabilities.json")
    learner = PercentageLearner(StubResearcher())
    result = learner.learn("500'ün yüzde 12'si kaç?")

    assert result.candidate.promotion_ready() is True
    memory.promote(result.candidate)

    reloaded = CapabilityMemory(tmp_path / "capabilities.json")
    record = reloaded.get("turkish_percentage_v1")
    assert record is not None
    assert record["status"] == "PROMOTED"
    assert record["method"] == "x * (y / 100)"
    assert PercentageLearner().solve("800'ün yüzde 15'i kaç?") == "120"


def test_unverified_candidate_cannot_be_promoted(tmp_path: Path) -> None:
    memory = CapabilityMemory(tmp_path / "capabilities.json")
    candidate = LearningCandidate(
        capability_id="unsafe_test",
        hypothesis="bad",
        method="bad",
    )
    try:
        memory.promote(candidate)
    except ValueError:
        pass
    else:
        raise AssertionError("Unverified capability must not be promoted")
