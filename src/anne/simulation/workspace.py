"""Global Cognitive Workspace for deterministic simulation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Workspace:
    """Shared integration surface; it stores typed state, not authority."""

    state: dict[str, Any] = field(default_factory=dict)
    broadcasts: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, source: str, kind: str, payload: Any) -> None:
        item = {"source": source, "kind": kind, "payload": payload}
        self.state[f"{source}:{kind}"] = payload
        self.broadcasts.append(item)

    def read(self, source: str, kind: str, default: Any = None) -> Any:
        return self.state.get(f"{source}:{kind}", default)
