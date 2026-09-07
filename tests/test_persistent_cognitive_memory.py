from __future__ import annotations

from anne.core.decision_loop import DecisionLoop
from anne.memory.fractal_memory import FractalMemory


def test_cognitive_cycle_persists_hypothesis_and_decision(tmp_path) -> None:
    db_path = str(tmp_path / "anne.db")

    first = DecisionLoop(memory_db_path=db_path)
    result = first.run_cognitive(
        "Explore a bounded technical option",
        seed=7,
    )
    assert result.selection is not None
    assert result.selection.accepted

    second = DecisionLoop(memory_db_path=db_path)
    rows = second.memory.get_similar_decisions("Explore a bounded technical option")

    assert rows
    assert rows[0][0] == result.state.ethic_score.verdict

    hypotheses = second.memory.conn.execute(
        "SELECT COUNT(*) FROM hypotheses"
    ).fetchone()[0]
    decisions = second.memory.conn.execute(
        "SELECT COUNT(*) FROM decisions"
    ).fetchone()[0]
    rules = second.memory.conn.execute(
        "SELECT COUNT(*) FROM learned_rules"
    ).fetchone()[0]

    assert hypotheses >= 1
    assert decisions >= 1
    assert rules >= 1
