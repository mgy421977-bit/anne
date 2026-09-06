from pathlib import Path

from anne.learning.knowledge_memory import KnowledgeMemory
from anne.learning.web_research import WebResearcher


def test_user_terminology_persists_and_is_retrievable(tmp_path: Path) -> None:
    memory = KnowledgeMemory(tmp_path / "knowledge.json")
    memory.save_term(term="GES", meaning="Güneş Enerjisi Sistemi", source="user")
    record = memory.get_term("GES")
    assert record is not None
    assert record["meaning"] == "Güneş Enerjisi Sistemi"
    assert record["status"] == "LEARNED_CANDIDATE"


def test_ges_does_not_match_gesi_baglari() -> None:
    assert not WebResearcher._is_relevant(
        "GES nedir?",
        "Gesi Bağları, Kayseri'nin Gesi beldesi kökenli olduğu düşünülen türkü.",
        "Gesi Bağları",
    )


def test_ges_matches_solar_generation_result() -> None:
    assert WebResearcher._is_relevant(
        "GES nedir?",
        "Güneş enerji santrali (GES), güneş ışığını elektrik enerjisine dönüştürür.",
        "Güneş enerji santrali",
    )
