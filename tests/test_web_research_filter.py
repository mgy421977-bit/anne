from anne.learning.evidence import EvidenceItem
from anne.learning.web_research import WebResearcher


def test_unrelated_ges_place_result_is_rejected() -> None:
    assert not WebResearcher._is_relevant(
        "GES nedir?",
        "Gesi Bağları, Kayseri'nin bir yerleşim yeridir.",
        "Gesi Bağları",
    )


def test_solar_ges_result_is_accepted() -> None:
    assert WebResearcher._is_relevant(
        "GES nedir?",
        "Güneş enerji santrali (GES), güneş ışığını elektrik enerjisine dönüştürür.",
        "Güneş enerji santrali",
    )


def test_low_relevance_is_not_answered() -> None:
    evidence = [
        EvidenceItem(
            source="unrelated",
            claim="Tamamen alakasız bir sonuç.",
            kind="web",
            provenance="test://unrelated",
            confidence=0.95,
        )
    ]
    assert WebResearcher.answer("BESS nasıl çalışır?", evidence) is None
