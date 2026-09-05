"""Bridge between deterministic mathematics and physics calculations."""
from __future__ import annotations
from dataclasses import dataclass
from anne.physics.constants import MU_EARTH
from anne.physics.orbital import circular_orbit_velocity

@dataclass(frozen=True)
class OrbitCalculation:
    radius_m: float
    velocity_m_s: float
    method: str

def earth_circular_orbit(radius_m: float) -> OrbitCalculation:
    return OrbitCalculation(radius_m, circular_orbit_velocity(MU_EARTH, radius_m), "two_body_circular_orbit")
