from anne.mythos.web_research import MitosWebResearch


class FakeWeb:
    def __init__(self):
        self.queries = []

    def research(self, query):
        self.queries.append(query)
        from anne.learning.evidence import EvidenceItem
        return [EvidenceItem(source="example.gov.tr", claim=f"evidence for {query}", kind="web", provenance="https://example.gov.tr/source", confidence=0.8)]


def test_mitos_creates_specialist_missions_and_uses_web():
    web = FakeWeb()
    result = MitosWebResearch(web).research("2026 Türkiye sanayi enerji teşvikleri")
    assert result.missions == 3
    assert result.completed == 3
    assert len(web.queries) == 3
    assert len(result.evidence) == 3
    assert any("MITOS | agent=" in line for line in result.trace)
