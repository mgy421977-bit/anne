"""Bounded specialist collaboration for ANNE."""

from .coordinator import MultiAgentCoordinator, Worker
from .core import AgentMessage, AgentRole, CollaborationResult, SharedWorkspace

__all__ = [
    "AgentMessage",
    "AgentRole",
    "CollaborationResult",
    "MultiAgentCoordinator",
    "SharedWorkspace",
    "Worker",
]
