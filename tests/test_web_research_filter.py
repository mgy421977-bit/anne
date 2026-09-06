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


def test_title_case_acronym_collision_is_rejected() -> None:
    assert not WebResearcher._is_relevant(
        "BESS nedir?",
        "Young Bess is a historical film title.",
        "Young Bess",
    )


def test_real_acronym_result_is_accepted() -> None:
    assert WebResearcher._is_relevant(
        "BESS nedir?",
        "BESS (Battery Energy Storage System) is a battery energy storage system.",
        "Battery Energy Storage System",
    )


def test_generic_non_acronym_question_is_supported() -> None:
    assert WebResearcher._is_relevant(
        "Kuantum bilgisayar nedir?",
        "Kuantum bilgisayar, kuantum bitleri kullanarak hesaplama yapan bir bilgisayar türüdür.",
        "Kuantum bilgisayar",
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
