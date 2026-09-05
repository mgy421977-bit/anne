"""Bounded autonomous-system contracts for ANNE.

These primitives describe what ANNE may design and supervise. They do not
execute external side effects; concrete executors must enforce the contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AgentState(str, Enum):
    PROPOSED = "PROPOSED"
    AUTHORIZED = "AUTHORIZED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class MissionContract:
    mission: str
    scope: str
    allowed_tools: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    compute_budget: float = 0.0
    runtime_seconds: int = 0
    agent_count_limit: int = 1
    success_metrics: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.compute_budget < 0:
            raise ValueError("compute_budget cannot be negative")
        if self.runtime_seconds < 0:
            raise ValueError("runtime_seconds cannot be negative")
        if self.agent_count_limit < 1:
            raise ValueError("agent_count_limit must be >= 1")


@dataclass
class AutonomousSystem:
    mission: MissionContract
    system_id: str = field(default_factory=lambda: f"sys_{uuid4().hex[:12]}")
    version: str = "v1"
    state: AgentState = AgentState.PROPOSED
    baseline_version: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    anomalies: list[str] = field(default_factory=list)
    safety_events: list[str] = field(default_factory=list)

    def authorize(self) -> None:
        self.mission.validate()
        self.state = AgentState.AUTHORIZED

    def start(self) -> None:
        if self.state is not AgentState.AUTHORIZED:
            raise RuntimeError("system must be authorized before start")
        self.state = AgentState.RUNNING

    def observe(self, metrics: dict[str, float]) -> None:
        self.metrics.update(metrics)
        if self.state is AgentState.RUNNING:
            self.state = AgentState.REPORTING

    def complete(self) -> None:
        self.state = AgentState.COMPLETED

    def block(self, reason: str) -> None:
        self.safety_events.append(reason)
        self.state = AgentState.BLOCKED


@dataclass(frozen=True)
class OptimizationProposal:
    system_id: str
    base_version: str
    candidate_version: str
    predicted_metrics: dict[str, float]
    change_summary: str
    reversible: bool = True
    safety_checked: bool = False

    def promotable(self) -> bool:
        return self.reversible and self.safety_checked
