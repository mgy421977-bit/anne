from __future__ import annotations

import pytest

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


def test_persistent_memory_is_used_by_bak_and_gor_on_next_cycle(tmp_path) -> None:
    db_path = str(tmp_path / "anne.db")
    goal = "Explore a bounded technical option"

    first = DecisionLoop(memory_db_path=db_path)
    first_result = first.run_cognitive(goal, seed=7)
    assert first_result.selection is not None
    assert first_result.selection.accepted
    assert first_result.state is not None
    assert first_result.selection.candidate is not None
    assert first_result.state.ethic_score is not None

    second = DecisionLoop(memory_db_path=db_path)
    second_result = second.run_cognitive(goal, seed=7)

    assert second_result.state is not None
    state = second_result.state
    assert state.context_map["past_similar_count"] >= 1
    assert state.context_map["has_prior_knowledge"] is True
    assert state.related_memories

    candidate_probability = second_result.selection.candidate.probability
    memory_scores = [memory[1] for memory in state.related_memories if memory[1]]
    assert memory_scores

    expected_priority = candidate_probability * 0.7 + (
        sum(memory_scores) / len(memory_scores)
    ) * 0.3
    assert state.priority_score == pytest.approx(expected_priority)


__all__ = ["FractalMemory"]
