from anne.learning.knowledge_resolver import KnowledgeResolver


def test_provider_order_is_single_attempt_then_fallback(monkeypatch):
    calls = []

    monkeypatch.setenv("ANNE_PRIMARY_PROVIDER", "OpenRouter")

    def openrouter(question, evidence):
        calls.append("OpenRouter")
        raise RuntimeError("unavailable")

    def gemini(question, evidence):
        calls.append("Gemini")
        return "BESS, Battery Energy Storage System anlamına gelir."

    monkeypatch.setattr(KnowledgeResolver, "_openrouter", staticmethod(openrouter))
    monkeypatch.setattr(KnowledgeResolver, "_gemini", staticmethod(gemini))

    class FakeWeb:
        def research(self, question):
            return []

        def answer(self, question, evidence):
            return None

    resolver = KnowledgeResolver(web=FakeWeb())
    result = resolver.resolve("BESS nedir?")

    assert result.provider == "Gemini"
    assert calls == ["OpenRouter", "Gemini"]


def test_successful_primary_does_not_call_fallback(monkeypatch):
    calls = []
    monkeypatch.setenv("ANNE_PRIMARY_PROVIDER", "OpenRouter")

    def openrouter(question, evidence):
        calls.append("OpenRouter")
        return "BESS, Battery Energy Storage System anlamına gelir."

    def gemini(question, evidence):
        calls.append("Gemini")
        return "Gemini should not be called."

    monkeypatch.setattr(KnowledgeResolver, "_openrouter", staticmethod(openrouter))
    monkeypatch.setattr(KnowledgeResolver, "_gemini", staticmethod(gemini))

    class FakeWeb:
        def research(self, question):
            return []

        def answer(self, question, evidence):
            return None

    resolver = KnowledgeResolver(web=FakeWeb())
    result = resolver.resolve("BESS nedir?")

    assert result.provider == "OpenRouter"
    assert calls == ["OpenRouter"]
