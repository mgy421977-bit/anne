from anne.math.units import ACCELERATION, LENGTH, TIME, VELOCITY


def test_kinematics_dimensions():
    assert VELOCITY == LENGTH / TIME
    assert ACCELERATION == VELOCITY / TIME
    assert (ACCELERATION * LENGTH) == (VELOCITY * VELOCITY)
    assert (ACCELERATION * TIME * TIME) == LENGTH
