"""Shared competitive workspace for ANNE cognitive subsystems."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkspaceItem:
    source: str
    content: Any
    salience: float = 0.0
    confidence: float = 0.0
    novelty: float = 0.0
    risk: float = 0.0

    @property
    def priority(self) -> float:
        return self.salience * 0.4 + self.confidence * 0.2 + self.novelty * 0.25 - self.risk * 0.15


@dataclass
class GlobalWorkspace:
    """Bounded broadcast space; subsystems compete, ANNE selects."""
    capacity: int = 12
    items: list[WorkspaceItem] = field(default_factory=list)

    def publish(self, item: WorkspaceItem) -> None:
        self.items.append(item)
        self.items.sort(key=lambda x: x.priority, reverse=True)
        del self.items[self.capacity :]

    def winners(self, limit: int = 3) -> list[WorkspaceItem]:
        return self.items[: max(0, limit)]

    def clear(self) -> None:
        self.items.clear()
