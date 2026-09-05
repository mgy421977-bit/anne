import math
from anne.physics.constants import C, MU_EARTH
from anne.physics.mechanics import kinematic_identity
from anne.physics.orbital import circular_orbit_velocity, escape_velocity

def test_kinematics_definitions():
    v, s = kinematic_identity(10.0, 3.0, 4.0)
    assert v == 22.0
    assert s == 64.0

def test_orbital_primitives():
    v = circular_orbit_velocity(MU_EARTH, 6_771_000.0)
    ve = escape_velocity(MU_EARTH, 6_771_000.0)
    assert math.isclose(ve, math.sqrt(2) * v, rel_tol=1e-12)
    assert C > 2.9e8
