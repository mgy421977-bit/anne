from anne.learning.evidence import EvidenceItem as AnneEvidenceItem
from anne.mythos.web_research import MitosWebResearch


class StubWebResearcher:
    def research(self, query: str):
        return [
            AnneEvidenceItem(
                source="stub.example",
                claim=f"Collected information for: {query}",
                kind="web",
                provenance="https://stub.example/evidence",
                confidence=0.8,
            )
        ]


def test_mitos_collects_and_returns_evidence_without_deciding_truth():
    result = MitosWebResearch(StubWebResearcher()).research("compare investment options")

    assert result.evidence
    assert result.completed == result.missions == 3
    assert any("RESEARCH_ONLY" in line for line in result.trace)
    assert any("handing evidence to ANNE" in line for line in result.trace)
    assert not any("FACT" in line and "MITOS" in line for line in result.trace)


def test_mitos_missions_explicitly_forbid_final_answer_decision():
    missions = MitosWebResearch._missions("test question")

    assert len(missions) == 3
    assert all("Do not decide the final answer" in mission.objective for mission in missions)
    assert all(mission.output_schema == "EvidencePackage" for mission in missions)
