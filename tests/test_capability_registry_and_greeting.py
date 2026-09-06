from pathlib import Path

from anne.learning.capability_registry import CapabilityRegistry
from anne.learning.greeting import GreetingLearner
from anne.language.tr.core import TurkishLanguageEngine


def test_greeting_learning_promotes_and_reuses(tmp_path: Path) -> None:
    registry = CapabilityRegistry(tmp_path / "capabilities.json")
    learner = GreetingLearner(registry)

    first = learner.learn("merhaba")
    assert first.answer == "Merhaba!"
    assert registry.has("turkish_greeting_v1")

    answer, trace = learner.answer_from_memory("merhabalar") or (None, [])
    assert answer == "Merhaba!"
    assert "no web research required" not in " ".join(trace).lower()


def test_language_engine_routes_greeting(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANNE_RUNTIME_DIR", str(tmp_path))
    engine = TurkishLanguageEngine()
    analysis = engine.analyze("merhaba")
    assert analysis.intent == "greeting"
    assert engine.respond(analysis) == "Merhaba!"
