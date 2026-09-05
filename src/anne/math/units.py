"""Minimal SI dimensional analysis primitives for mathematical verification."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    length: int = 0
    mass: int = 0
    time: int = 0
    current: int = 0
    temperature: int = 0

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(*(a + b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(*(a - b for a, b in zip(self.as_tuple(), other.as_tuple())))

    def as_tuple(self) -> tuple[int, ...]:
        return (self.length, self.mass, self.time, self.current, self.temperature)

    def compatible(self, other: "Dimension") -> bool:
        return self == other


DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
TIME = Dimension(time=1)
VELOCITY = LENGTH / TIME
ACCELERATION = VELOCITY / TIME


__all__ = [
    "Dimension", "DIMENSIONLESS", "LENGTH", "TIME", "VELOCITY", "ACCELERATION"
]
