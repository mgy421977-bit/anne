from anne.language.engine import LanguageEngine


def test_turkish_vocabulary_and_morphology():
    engine = LanguageEngine()
    result = engine.analyze("Evlerimde kitaplarım var.")

    assert "evlerimde" in result.tokens
    assert "kitaplarım" in result.tokens
    assert result.grammar["language"] == "tr"
    assert any(item["root"] == "ev" for item in result.morphology)
    assert any(item["root"] == "kitap" for item in result.morphology)


def test_unknown_words_are_explicit():
    result = LanguageEngine().analyze("ANNE öğreniyor")
    assert "anne" in result.unknown_words
    assert "öğreniyor" in result.unknown_words


def test_core_can_use_language_without_llm():
    from anne.core.cognitive_core import AnneCognitiveCore

    run = AnneCognitiveCore().run("Evler güzel.")
    assert run.language is not None
    assert run.language.grammar["language"] == "tr"
    assert any(item["root"] == "ev" for item in run.language.known_words)
