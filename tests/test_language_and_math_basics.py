from decimal import Decimal

from anne.language.tr.core import TurkishLanguageEngine
from anne.math.engine import MathEngine


def test_turkish_weather_question_is_detected_without_llm():
    engine = TurkishLanguageEngine()
    result = engine.analyze("Hava nasıl?")
    assert result.intent == "weather"
    assert "hava" in result.tokens
    assert engine.respond(result, weather={"location": "İzmir", "temperature_c": 24, "condition": "açık"}) == (
        "İzmir için sıcaklık 24 °C. Durum: açık."
    )


def test_turkish_question_has_structural_roles():
    result = TurkishLanguageEngine().analyze("Sen nasılsın?")
    assert result.intent == "question"
    assert result.roles["sen"] == "pronoun"
    assert result.roles["nasılsın"] == "question_word" or "nasıl" in result.tokens


def test_math_basic_operations_are_deterministic():
    engine = MathEngine()
    assert engine.calculate("2 + 3").value == Decimal("5")
    assert engine.calculate("7 * 8").value == Decimal("56")
    assert engine.calculate("10 / 4").value == Decimal("2.5")
    assert engine.calculate_words("12", "eksi", "5").value == Decimal("7")


def test_math_engine_rejects_code_execution():
    engine = MathEngine()
    try:
        engine.calculate("__import__('os').system('echo unsafe')")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe expression was accepted")
