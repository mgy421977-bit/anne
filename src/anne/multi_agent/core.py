"""Bounded multi-agent collaboration primitives for ANNE."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class AgentRole:
    name: str
    purpose: str
    permissions: frozenset[str] = frozenset()


@dataclass
class AgentMessage:
    agent: str
    role: str
    conclusion: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.5
    dissent: str | None = None
    round_number: int = 0

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))


@dataclass
class SharedWorkspace:
    task: str
    messages: list[AgentMessage] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    unresolved_disagreements: list[str] = field(default_factory=list)
    phase: str = "deliberate"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def publish(self, message: AgentMessage) -> None:
        self.messages.append(message)
        self.facts.update(message.evidence)

    def record_disagreement(self, disagreement: str) -> None:
        if disagreement not in self.unresolved_disagreements:
            self.unresolved_disagreements.append(disagreement)


@dataclass
class CollaborationResult:
    task: str
    consensus: str | None
    confidence: float
    messages: list[AgentMessage]
    unresolved_disagreements: list[str]
    rounds: int
    status: str  # consensus | dissent | no_evidence


__all__ = ["AgentMessage", "AgentRole", "CollaborationResult", "SharedWorkspace"]
