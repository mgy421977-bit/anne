from anne.core.learning_engine import LearningEngine
from anne.memory.fractal_experience import Experience


def test_success_strengthens_rule(tmp_path):
    engine = LearningEngine(tmp_path)
    exp = Experience(task="fabrika", patterns=["yüksek gündüz tüketimi"], confidence=0.9, outcome="başarılı")
    first = engine.learn(exp)
    assert first[0].successes == 1
    assert first[0].confidence > 0.50


def test_failure_weakens_rule(tmp_path):
    engine = LearningEngine(tmp_path)
    exp = Experience(task="fabrika", patterns=["yüksek gündüz tüketimi"], confidence=0.8, outcome="başarısız")
    first = engine.learn(exp, success=True)
    before = first[0].confidence
    after = engine.learn(exp, success=False)[0].confidence
    assert after < before


def test_three_successes_promote_rule(tmp_path):
    engine = LearningEngine(tmp_path)
    for _ in range(3):
        engine.learn(Experience(task="fabrika", patterns=["gündüz tüketimi"], confidence=0.9), success=True)
    rules = engine.applicable(["gündüz", "tüketimi"])
    assert rules[0].status == "learned"
    assert rules[0].successes == 3
