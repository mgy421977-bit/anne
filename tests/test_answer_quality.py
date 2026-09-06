from anne.agent.runtime import AnneAgent


def test_short_acknowledgement_is_retried_for_research_request() -> None:
    assert AnneAgent._needs_answer_retry(
        "İfadenizi anladım.",
        "Türkiye'de 2026 yılında GES desteklerini araştır",
    )


def test_substantive_answer_is_not_retried() -> None:
    assert not AnneAgent._needs_answer_retry(
        "GES, enerji verimliliği ve BESS için yatırım koşullarını, varsayımları "
        "ve kaynak doğrulama adımlarını karşılaştırırım.",
        "Türkiye'de sanayi tesisleri için GES ve BESS karşılaştır",
    )
