from __future__ import annotations

from dataclasses import dataclass

from anne.core.agency_gate import ActionDecision, ActionProposal
from anne.core.cognitive_cycle import CycleStatus
from anne.core.runtime import ANNERuntime, RuntimeConfig
from anne.memory.local_memory import LocalMemory
from anne.mythos.engine import MitosEngine


@dataclass
class FakeModel:
    calls: int = 0

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        self.calls += 1
        assert system_instruction is not None
        assert "MITOS EXPLORATION CANDIDATES" in prompt
        return "Bounded model response."


@dataclass
class FakeExecutor:
    calls: int = 0

    def execute(self, proposal: ActionProposal) -> str:
        self.calls += 1
        return f"executed:{proposal.action}"


def test_runtime_connects_observation_mitos_model_and_memory() -> None:
    memory = LocalMemory(":memory:")
    runtime = ANNERuntime(
        model=FakeModel(),
        memory=memory,
        mitos=MitosEngine(seed=7),
        config=RuntimeConfig(max_mitos_candidates=3),
    )

    result = runtime.run("Investigate a bounded solution")

    assert result.response == "Bounded model response."
    assert len(result.mitos_candidates) == 3
    assert result.cycle.observations[0].kind.value == "OBSERVATION"
    assert result.cycle.predictions[0].kind.value == "PREDICTION"
    assert result.cycle.outcomes[0].observed is False
    assert result.cycle.learning_is_evidenced() is False
    assert result.memory_path == "local:interactions/1"
    assert result.cycle.status is CycleStatus.COMPLETED


def test_external_action_is_denied_by_default_without_executor_call() -> None:
    executor = FakeExecutor()
    runtime = ANNERuntime(model=FakeModel(), action_executor=executor)

    result = runtime.run(
        "Prepare an action",
        action=ActionProposal(
            action="write_file",
            target="example.txt",
            provenance=("user_request",),
        ),
    )

    assert result.authorization is not None
    assert result.authorization.startswith(ActionDecision.DENY.value)
    assert executor.calls == 0
    assert result.cycle.status is CycleStatus.BLOCKED


def test_allowed_reversible_action_requires_explicit_runtime_enablement() -> None:
    executor = FakeExecutor()
    runtime = ANNERuntime(
        model=FakeModel(),
        action_executor=executor,
        config=RuntimeConfig(allow_external_actions=True),
    )

    result = runtime.run(
        "Execute a low-risk action",
        action=ActionProposal(
            action="safe_test",
            target="sandbox",
            reversible=True,
            risk=0.1,
            provenance=("verified_test",),
        ),
    )

    assert result.authorization is not None
    assert result.authorization.startswith(ActionDecision.ALLOW.value)
    assert result.action_result == "executed:safe_test"
    assert executor.calls == 1
    assert result.cycle.status is CycleStatus.COMPLETED
