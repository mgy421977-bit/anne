"""Swappable stage protocol — enables ablation by config, not by rewrite.

Default pipeline stages can be replaced with user-defined implementations that
share the same Context contract. This is scaffolding for research ablations
(e.g. ANLA off, custom validators), not a plugin marketplace claim.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StageContext:
    """Mutable bag passed between stages."""

    raw_input: str = ""
    input_type: str = "explore"
    halted: bool = False
    halt_reason: str = ""
    halt_stage: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    # Optional handles injected by the orchestrator
    memory: Any = None
    cognitive_state: Any = None
    hypothesis: Any = None


class Stage(ABC):
    """One cognitive stage."""

    name: str = "stage"

    @abstractmethod
    def process(self, ctx: StageContext) -> StageContext:
        """Transform context; set ctx.halted to short-circuit the pipeline."""


class PassThroughStage(Stage):
    """No-op stage for ablation (e.g. ANLA off)."""

    name = "pass_through"

    def process(self, ctx: StageContext) -> StageContext:
        ctx.meta[f"{self.name}_ran"] = True
        return ctx


class FailFastStage(Stage):
    """Wraps FailFastGate as a Stage."""

    name = "fail_fast"

    def __init__(self, gate: Any) -> None:
        self.gate = gate

    def process(self, ctx: StageContext) -> StageContext:
        result = self.gate.check(ctx.raw_input)
        ctx.meta["fail_fast"] = result.as_dict()
        if not result.passed:
            ctx.halted = True
            ctx.halt_stage = self.name
            ctx.halt_reason = result.reason
        return ctx


class StagePipeline:
    """Ordered list of Stage instances."""

    def __init__(self, stages: list[Stage] | None = None) -> None:
        self.stages = list(stages or [])

    def run(self, ctx: StageContext) -> StageContext:
        for stage in self.stages:
            ctx = stage.process(ctx)
            if ctx.halted:
                ctx.meta["halted_after"] = stage.name
                break
        return ctx
