from anne.learning.reliable_web import ReliableWebResearcher


def test_focus_queries_decompose_long_question_without_domain_rules():
    question = (
        "Türkiye'de 2026 yılında sanayi tesisleri için GES, enerji verimliliği, "
        "batarya enerji depolama ve karbon azaltımı yatırımlarını karşılaştır. "
        "Hangi yatırımın hangi koşullarda daha avantajlı olduğunu, güncel devlet "
        "teşviklerini ve finansman seçeneklerini de değerlendir."
    )
    probes = ReliableWebResearcher._focus_queries(question)
    assert probes
    assert len(probes) <= ReliableWebResearcher.max_focus_queries
    assert any("GES" in probe or "enerji" in probe for probe in probes)
    assert any("teşvik" in probe or "finansman" in probe for probe in probes)


def test_focus_queries_keep_short_questions_cheap():
    assert ReliableWebResearcher._focus_queries("BESS nedir?") == []


def test_loose_parser_recovers_bing_style_result():
    html = (
        '<li class="b_algo"><h2><a href="https://example.gov.tr/page">'
        'Enerji verimliliği destekleri</a></h2></li>'
    )
    from anne.learning.reliable_web import _LooseSearchParser

    parser = _LooseSearchParser()
    parser.feed(html)
    assert parser.results == [("Enerji verimliliği destekleri", "https://example.gov.tr/page", "")]
