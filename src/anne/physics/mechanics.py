"""Deterministic classical-mechanics relations."""
from __future__ import annotations


def velocity_from_acceleration(u: float, a: float, t: float) -> float:
    return u + a * t


def displacement_from_acceleration(u: float, a: float, t: float) -> float:
    return u * t + 0.5 * a * t * t


def kinematic_identity(u: float, a: float, t: float) -> tuple[float, float]:
    return velocity_from_acceleration(u, a, t), displacement_from_acceleration(u, a, t)
