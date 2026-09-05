import math
from anne.math.physics_bridge import earth_circular_orbit
from anne.physics.constants import MU_EARTH

def test_math_physics_bridge():
    result = earth_circular_orbit(6_771_000.0)
    expected = math.sqrt(MU_EARTH / 6_771_000.0)
    assert math.isclose(result.velocity_m_s, expected, rel_tol=1e-12)
