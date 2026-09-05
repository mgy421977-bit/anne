from anne.math.units import ACCELERATION, ENERGY, FORCE, LENGTH, MASS, TIME, VELOCITY


def test_velocity_and_energy_dimensions():
    assert VELOCITY.compatible(LENGTH / TIME)
    assert FORCE.compatible(MASS * ACCELERATION)
    assert ENERGY.compatible(FORCE * LENGTH)
