from anne.core.knowledge_router import KnowledgeRouter
from anne.learning.knowledge_resolver import KnowledgeResolution


class StubResolver:
    def __init__(self, resolution):
        self.resolution = resolution

    def resolve(self, question):
        assert question
        return self.resolution


def resolution(*, answer, provider, memory_hit=False):
    return KnowledgeResolution(
        answer=answer,
        trace=(),
        provider=provider,
        evidence=(),
        confidence=0.8,
        memory_hit=memory_hit,
    )


def test_known_memory_route():
    router = KnowledgeRouter(resolver=StubResolver(resolution(answer="cevap", provider="user-memory", memory_hit=True)))
    result = router.resolve("BESS nedir?")
    assert result.route == "KNOWN"
    assert result.resolution.answer == "cevap"


def test_unknown_web_route():
    router = KnowledgeRouter(resolver=StubResolver(resolution(answer="cevap", provider="web")))
    assert router.resolve("Yeni bir konu nedir?").route == "UNKNOWN_WEB"


def test_provider_fallback_route():
    router = KnowledgeRouter(resolver=StubResolver(resolution(answer="cevap", provider="OpenRouter")))
    assert router.resolve("Karmaşık bir soru?").route == "UNKNOWN_PROVIDER_FALLBACK"


def test_fail_closed_route():
    router = KnowledgeRouter(resolver=StubResolver(resolution(answer=None, provider=None)))
    result = router.resolve("Bilmiyorum?")
    assert result.route == "UNKNOWN_FAIL_CLOSED"
    assert result.resolution.answer is None
