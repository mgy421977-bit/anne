from anne.core.ai_kernel import AnneAIKernel


def test_kernel_understands_question_and_builds_plan() -> None:
    kernel = AnneAIKernel()
    result = kernel.reason("ANNE nedir ve nasıl çalışır?")
    assert result.intent == "question"
    assert result.concepts
    assert "Soruyu ayrıştır" in result.plan
    assert 0.0 <= result.confidence <= 1.0


def test_kernel_research_intent_uses_evidence() -> None:
    kernel = AnneAIKernel()
    result = kernel.reason("Bu konuyu araştır ve analiz et.", ["kaynak-1"])
    assert result.intent == "research"
    assert result.knowledge.evidence == ["kaynak-1"]
    assert result.confidence > 0.35
