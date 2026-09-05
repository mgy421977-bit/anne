from anne.core.cognitive_core import AnneCognitiveCore
from anne.core.learning_engine import LearningEngine
from anne.memory.fractal_experience import Experience, FractalExperienceMemory


PATTERN = "gündüz tüketimi öz tüketim"


def _experience(i: int, outcome: str = "başarılı") -> Experience:
    return Experience(
        task=f"fabrika enerji vakası {i}",
        concepts=["fabrika", "enerji", "tüketim"],
        patterns=[PATTERN],
        outcome=outcome,
        confidence=0.85,
        uncertainty=0.15,
        lessons=["tüketim profili yatırım kararında belirleyici"] if outcome == "başarılı" else ["kural her bağlamda geçerli değil"],
    )


def test_three_successes_promote_rule(tmp_path):
    memory = FractalExperienceMemory(tmp_path / "memory")
    learning = LearningEngine(tmp_path / "patterns")
    for i in range(1, 4):
        assert learning.learn(_experience(i, "başarılı"), success=True)

    rules = learning.applicable(["gündüz", "tüketimi", "öz", "tüketim"])
    rule = next(r for r in rules if r.pattern == PATTERN)
    assert rule.observations == 3
    assert rule.successes == 3
    assert rule.failures == 0
    assert rule.status == "learned"
    assert rule.confidence >= 0.75


def test_failure_weakens_rule(tmp_path):
    learning = LearningEngine(tmp_path / "patterns")
    for i in range(1, 4):
        learning.learn(_experience(i, "başarılı"), success=True)
    before = next(r for r in learning.applicable(["gündüz", "tüketimi"]) if r.pattern == PATTERN).confidence

    learning.learn(_experience(4, "başarısız"), success=False)
    after = next(r for r in learning.applicable(["gündüz", "tüketimi"]) if r.pattern == PATTERN)
    assert after.confidence < before
    assert after.failures == 1
    assert after.status == "candidate"


def test_new_problem_applies_learned_rule(tmp_path):
    memory = FractalExperienceMemory(tmp_path / "memory")
    learning = LearningEngine(tmp_path / "patterns")
    for i in range(1, 4):
        learning.learn(_experience(i, "başarılı"), success=True)

    core = AnneCognitiveCore(memory=memory, learning=learning)
    run = core.run(
        "Fabrikanın gündüz tüketimi yüksek; GES yatırımında öz tüketim nasıl değerlendirilmelidir?"
    )

    assert run.applied_rules
    assert any(rule.pattern == PATTERN and rule.status == "learned" for rule in run.applied_rules)
    assert any("learned rule applied" in observation for observation in run.state.observations)
    assert any(item.startswith("LEARNED:") for item in run.state.evidence)


def test_mismatched_context_does_not_apply_rule(tmp_path):
    memory = FractalExperienceMemory(tmp_path / "memory")
    learning = LearningEngine(tmp_path / "patterns")
    for i in range(1, 4):
        learning.learn(_experience(i, "başarılı"), success=True)

    core = AnneCognitiveCore(memory=memory, learning=learning)
    run = core.run("İşletmenin gece vardiyası ağırlıklı; güneşlenme saatlerinde yük yok.")

    assert not run.applied_rules
