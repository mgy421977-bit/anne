"""Bounded memory policy for simulation and later offline storage."""

from dataclasses import dataclass

from anne.calculation.memory_policy import MemoryClass


@dataclass(frozen=True)
class MemoryDecision:
    memory_class: MemoryClass
    durable: bool
    reason: str


class MemoryGovernor:
    def decide(self, memory_class: MemoryClass) -> MemoryDecision:
        if memory_class is MemoryClass.EPHEMERAL:
            return MemoryDecision(memory_class, False, "time-sensitive/transient information")
        return MemoryDecision(memory_class, True, "reusable experience, knowledge or procedure")
