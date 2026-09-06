"""Executable orchestration loop for the canonical ANNE architecture.

The runtime is deliberately provider- and hardware-neutral.  Model output is
never promoted to FACT by this layer; observations, hypotheses, predictions,
outcomes, and experience remain explicitly typed.  External actions are
optional and must pass AgencyGate before an executor is called.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from anne.core.agency_gate import ActionDecision, ActionProposal, AgencyGate
from anne.core.cognitive_cycle import (
    CognitiveCycle,
    EvidenceKind,
    Observation,
    Prediction,
)
from anne.memory.local_memory import LocalMemory
from anne.mythos.engine import MitosEngine


class ModelAdapter(Protocol):
    """Minimal model contract required by ANNE Runtime."""

    def ask(self, prompt: str, system_instruction: str | None = None) -> str:
        ...


class ActionExecutor(Protocol):
    """Explicit side-effect adapter; implementing it grants no authority."""

    def execute(self, proposal: ActionProposal) -> Any:
        ...


@dataclass(frozen=True)
class RuntimeConfig:
    """Hard runtime bounds for one cognitive cycle."""

    max_memory_items: int = 8
    max_mitos_candidates: int = 3
    allow_external_actions: bool = False

    def validate(self) -> None:
        if self.max_memory_items < 1:
            raise ValueError("max_memory_items must be positive")
        if self.max_mitos_candidates < 1:
            raise ValueError("max_mitos_candidates must be positive")


@dataclass
class RuntimeResult:
    """Reconstructable result of one ANNE runtime cycle."""

    cycle: CognitiveCycle
    response: str
    memory_path: str | None
    authorization: str | None = None
    action_result: Any = None
    mitos_candidates: list[dict[str, Any]] = field(default_factory=list)


class ANNERuntime:
    """Connects memory, MITOS, model reasoning, verification and agency."""

    SYSTEM = """You are ANNE, the executive cognitive runtime.

Follow the evidence hierarchy strictly:
- user input and tool observations are observations, not automatically facts;
- model-generated ideas are hypotheses or beliefs unless independently verified;
- simulations are not observations;
- memory is context, not truth;
- do not claim learning unless future behavior has measurably changed.

MITOS is an exploratory subconscious-inspired layer. Its candidates are ideas
for investigation, not authorization or facts. ANNE remains the executive
authority for value, safety, planning and external action.
"""

    def __init__(
        self,
        model: ModelAdapter,
        memory: LocalMemory | None = None,
        mitos: MitosEngine | None = None,
        agency_gate: AgencyGate | None = None,
        action_executor: ActionExecutor | None = None,
        config: RuntimeConfig | None = None,
    ) -> None:
        self.model = model
        self.memory = memory or LocalMemory(":memory:")
        self.mitos = mitos or MitosEngine(seed=0)
        self.agency_gate = agency_gate or AgencyGate()
        self.action_executor = action_executor
        self.config = config or RuntimeConfig()
        self.config.validate()

    def run(
        self,
        goal: str,
        *,
        source: str = "user",
        action: ActionProposal | None = None,
    ) -> RuntimeResult:
        """Run one bounded observe → explore → reason → verify cycle."""
        if not goal.strip():
            raise ValueError("goal is required")

        cycle = CognitiveCycle(goal=goal)
        observation = Observation(
            content=goal,
            source=source,
            observed_at=datetime.now(UTC).isoformat(),
            provenance=(f"source:{source}",),
        )
        cycle.add_observation(observation)
        cycle.context["memory"] = self.memory.context(self.config.max_memory_items)

        candidates = self.mitos.generate(
            goal, batch_size=self.config.max_mitos_candidates
        )
        cycle.hypothesis_ids.extend(candidate.id for candidate in candidates)
        cycle.status = cycle.status.EXPLORED

        candidate_text = "\n".join(
            f"- {candidate.id}: {candidate.claim} "
            f"(discovery_value={candidate.discovery_value:.3f})"
            for candidate in candidates
        )
        prompt = (
            f"GOAL:\n{goal}\n\n"
            f"MEMORY CONTEXT:\n{cycle.context['memory']}\n\n"
            f"MITOS EXPLORATION CANDIDATES:\n{candidate_text}\n\n"
            "Produce the best bounded response. Clearly distinguish what is "
            "observed from what is inferred or proposed."
        )
        response = self.model.ask(prompt, system_instruction=self.SYSTEM).strip()
        if not response:
            raise RuntimeError("model returned an empty response")

        cycle.predictions.append(
            Prediction(
                hypothesis_id=candidates[0].id,
                expected_outcome=response,
                probability=candidates[0].probability,
                confidence=candidates[0].testability,
                provenance=(candidates[0].id,),
            )
        )
        cycle.plan = {"mode": "bounded_reasoning", "external_action": bool(action)}
        cycle.status = cycle.status.PLANNED

        authorization_text: str | None = None
        action_result: Any = None
        if action is not None:
            if not self.config.allow_external_actions:
                authorization_text = "DENY: external actions disabled by runtime configuration"
                cycle.block(authorization_text)
            else:
                authorization = self.agency_gate.authorize(
                    action,
                    safety_allowed=True,
                )
                authorization_text = f"{authorization.decision.value}: {authorization.reason}"
                if authorization.decision is ActionDecision.ALLOW:
                    cycle.authorize(authorization.reason)
                    if self.action_executor is None:
                        cycle.block("ALLOW was reached but no action executor is configured")
                        authorization_text = "BLOCKED: no action executor configured"
                    else:
                        action_result = self.action_executor.execute(action)
                        cycle.action = {"action": action.action, "target": action.target}
                        cycle.status = cycle.status.ACTED
                else:
                    cycle.block(authorization.reason)
        else:
            cycle.authorize("no external action requested")

        cycle.record_outcome(
            # A model response is not treated as an external observation.
            # The outcome is therefore marked unobserved; this prevents a
            # single generation from being mistaken for verified learning.
            __import__("anne.core.cognitive_cycle", fromlist=["Outcome"]).Outcome(
                prediction_id=cycle.predictions[0].hypothesis_id,
                observed_outcome=response,
                observed=False,
                source="model",
                provenance=("model_generation", EvidenceKind.BELIEF.value),
            )
        )
        cycle.status = cycle.status.COMPLETED

        memory_path = self.memory.save(
            goal,
            response,
            "No new durable learning; no independently observed outcome yet.",
            confidence=cycle.predictions[0].confidence,
        )
        return RuntimeResult(
            cycle=cycle,
            response=response,
            memory_path=memory_path,
            authorization=authorization_text,
            action_result=action_result,
            mitos_candidates=[candidate.__dict__ for candidate in candidates],
        )


__all__ = [
    "ActionExecutor",
    "ModelAdapter",
    "RuntimeConfig",
    "RuntimeResult",
    "ANNERuntime",
]
