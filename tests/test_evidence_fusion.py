from anne.core.evidence_fusion import fuse_evidence
from anne.learning.evidence import EvidenceItem


def item(source, claim, confidence=0.8):
    return EvidenceItem(source=source, claim=claim, kind="web", provenance=source, confidence=confidence)


def test_two_independent_sources_corrobate():
    result = fuse_evidence([
        item("https://energy.gov.tr/a", "Güneş enerjisi elektrik üretiminde kullanılır."),
        item("https://www.iea.org/a", "Solar energy is used to generate electricity."),
    ])
    assert result.sufficient
    assert result.independent_sources == 2
    assert result.contradiction_count == 0


def test_same_source_duplicates_do_not_count_twice():
    result = fuse_evidence([
        item("https://example.com/a", "BESS elektrik enerjisi depolamak için kullanılır."),
        item("https://example.com/a", "BESS sistemleri elektrik enerjisini depolamak için kullanılır."),
    ])
    assert not result.sufficient
    assert result.independent_sources == 1
    assert result.reason == "insufficient_independent_support"


def test_contradiction_blocks_fusion():
    result = fuse_evidence([
        item("https://a.example/a", "Sistem çalışır."),
        item("https://b.example/a", "Sistem çalışmaz."),
    ])
    assert not result.sufficient
    assert result.contradiction_count >= 1
    assert result.reason == "contradictory_evidence"


def test_authority_required_needs_official_source():
    result = fuse_evidence([
        item("https://example.com/a", "2026 desteği bulunmaktadır.", 0.95),
        item("https://blog.example/b", "2026 desteği bulunmaktadır.", 0.95),
    ], authority_required=True)
    assert not result.sufficient
