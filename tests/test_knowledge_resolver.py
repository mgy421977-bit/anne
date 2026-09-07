from __future__ import annotations

from pathlib import Path

from anne.learning.evidence import EvidenceItem
from anne.learning.knowledge_memory import KnowledgeMemory
from anne.learning.knowledge_resolver import KnowledgeResolver


class StubWeb:
    def research(self, query: str):
        return [
            EvidenceItem(
                source="stub-web",
                claim="Stub evidence for the question.",
                kind="web",
                provenance="test://web",
                confidence=0.9,
            )
        ]

    @staticmethod
    def answer(question: str, evidence):
        return None


class AnsweringStubWeb(StubWeb):
    @staticmethod
    def answer(question: str, evidence):
        return "Web-derived answer."


def test_openrouter_is_first_provider_and_answer_is_saved(tmp_path: Path, monkeypatch) -> None:
    memory = KnowledgeMemory(tmp_path / "knowledge.json")
    resolver = KnowledgeResolver(web=StubWeb(), memory=memory)
    calls: list[str] = []

    monkeypatch.setattr(resolver, "_openrouter", lambda question, evidence: calls.append("openrouter") or "OpenRouter answer")
    monkeypatch.setattr(resolver, "_gemini", lambda question, evidence: calls.append("gemini") or "Gemini answer")

    result = resolver.resolve("Athena nedir?")

    assert result.answer == "OpenRouter answer"
    assert result.provider == "OpenRouter"
    assert calls == ["openrouter"]
    saved = memory.get("Athena nedir?")
    assert saved is not None
    assert saved["status"] == "LEARNED_CANDIDATE"
    assert saved["provider"] == "OpenRouter"


def test_gemini_is_second_fallback(tmp_path: Path, monkeypatch) -> None:
    memory = KnowledgeMemory(tmp_path / "knowledge.json")
    resolver = KnowledgeResolver(web=StubWeb(), memory=memory)
    calls: list[str] = []

    def fail_openrouter(question, evidence):
        calls.append("openrouter")
        raise RuntimeError("simulated OpenRouter failure")

    monkeypatch.setattr(resolver, "_openrouter", fail_openrouter)
    monkeypatch.setattr(resolver, "_gemini", lambda question, evidence: calls.append("gemini") or "Gemini answer")

    result = resolver.resolve("BESS nasıl çalışır?")

    assert result.answer == "Gemini answer"
    assert result.provider == "Gemini"
    assert calls == ["openrouter", "gemini"]


def test_sufficient_web_evidence_answers_before_provider(tmp_path: Path, monkeypatch) -> None:
    memory = KnowledgeMemory(tmp_path / "knowledge.json")
    resolver = KnowledgeResolver(web=AnsweringStubWeb(), memory=memory)

    monkeypatch.setattr(resolver, "_openrouter", lambda question, evidence: (_ for _ in ()).throw(RuntimeError("must not run")))
    monkeypatch.setattr(resolver, "_gemini", lambda question, evidence: (_ for _ in ()).throw(RuntimeError("must not run")))

    result = resolver.resolve("GES nedir?")

    assert result.answer == "Web-derived answer."
    assert result.provider == "web"
    assert result.confidence == 0.9


def test_existing_knowledge_is_reused_without_provider(tmp_path: Path) -> None:
    memory = KnowledgeMemory(tmp_path / "knowledge.json")
    memory.save(
        question="GES nedir?",
        answer="Kaydedilmiş cevap.",
        evidence=[],
        provider="OpenRouter",
        confidence=0.7,
    )
    resolver = KnowledgeResolver(web=StubWeb(), memory=memory)

    result = resolver.resolve("GES nedir?")

    assert result.answer == "Kaydedilmiş cevap."
    assert result.memory_hit is True
    assert result.provider == "OpenRouter"
