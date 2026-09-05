"""Initial two-body orbital mechanics primitives."""
from __future__ import annotations
import math


def circular_orbit_velocity(mu: float, radius_m: float) -> float:
    if mu <= 0 or radius_m <= 0:
        raise ValueError("mu and radius must be positive")
    return math.sqrt(mu / radius_m)


def escape_velocity(mu: float, radius_m: float) -> float:
    if mu <= 0 or radius_m <= 0:
        raise ValueError("mu and radius must be positive")
    return math.sqrt(2.0 * mu / radius_m)
