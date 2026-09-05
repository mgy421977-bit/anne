from anne.core.cognitive_core import AnneCognitiveCore
from anne.memory.fractal_experience import Experience, FractalExperienceMemory


def test_fractal_memory_round_trip(tmp_path):
    memory = FractalExperienceMemory(tmp_path)
    assert memory.remember(Experience(task="GES yatırım", concepts=["ges"], patterns=["gündüz tüketimi"], lessons=["öz tüketim önce incelenmeli"]))
    recalled = memory.recall("GES yatırım")
    assert len(recalled) == 1
    assert recalled[0].patterns == ["gündüz tüketimi"]


def test_core_runs_without_llm(tmp_path):
    memory = FractalExperienceMemory(tmp_path)
    core = AnneCognitiveCore(memory=memory)
    run = core.run("GES yatırımını araştır", internet=False)
    assert run.state.phase == "DUY"
    assert run.state.concepts
    assert run.presentation
    assert memory.stats()["experiences"] == 1


def test_repeated_experience_becomes_pattern_candidate(tmp_path):
    memory = FractalExperienceMemory(tmp_path)
    for i in range(2):
        memory.remember(Experience(task=f"fabrika {i}", patterns=["yüksek gündüz tüketimi"], confidence=0.8))
    core = AnneCognitiveCore(memory=memory)
    candidates = core.patterns.discover()
    assert candidates
    assert candidates[0].occurrences == 2
    assert core.patterns.promote(candidates[0]) is not None
