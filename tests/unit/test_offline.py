from __future__ import annotations

from anne.memory.local_memory import LocalMemory
from anne.providers.local import LocalProvider


def test_local_memory_persists_context(tmp_path) -> None:
    memory = LocalMemory(tmp_path / "offline.db")
    path = memory.save("question", "answer", "lesson", 0.8)
    assert path.startswith("local:interactions/")
    assert "question" in memory.context()
    assert "lesson" in memory.context()


def test_local_provider_has_no_api_key_requirement() -> None:
    ollama = LocalProvider(model="test", backend="ollama")
    compatible = LocalProvider(
        model="test", backend="openai-compatible", endpoint="http://127.0.0.1:8080/"
    )
    assert ollama.endpoint == "http://127.0.0.1:11434"
    assert compatible.endpoint == "http://127.0.0.1:8080"
    assert not hasattr(ollama, "api_key")
