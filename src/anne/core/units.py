"""Minimal dimensional-analysis primitives for ANNE physics validation."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Dimensions:
    """Physical dimensions represented as M, L, T exponents."""
    mass: int = 0
    length: int = 0
    time: int = 0

    def multiply(self, other: "Dimensions") -> "Dimensions":
        return Dimensions(self.mass + other.mass, self.length + other.length, self.time + other.time)

    def divide(self, other: "Dimensions") -> "Dimensions":
        return Dimensions(self.mass - other.mass, self.length - other.length, self.time - other.time)

    def power(self, exponent: int) -> "Dimensions":
        return Dimensions(self.mass * exponent, self.length * exponent, self.time * exponent)


class Units:
    MASS = Dimensions(mass=1)
    LENGTH = Dimensions(length=1)
    TIME = Dimensions(time=1)
    VELOCITY = LENGTH.divide(TIME)
    ACCELERATION = LENGTH.divide(TIME.power(2))
    FORCE = MASS.multiply(ACCELERATION)
    ENERGY = FORCE.multiply(LENGTH)

    @staticmethod
    def compatible(left: Dimensions, right: Dimensions) -> bool:
        return left == right
