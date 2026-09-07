def test_mythos_web_bridge_imports_without_learning_cycle():
    from anne.learning.knowledge_resolver import KnowledgeResolver
    from anne.mythos.web_research import MitosWebResearch

    assert KnowledgeResolver is not None
    assert MitosWebResearch is not None
