import pytest

from anne.core.resource_profile import ResourceProfile, Substrate


def test_minimal_profile_is_small_and_bounded() -> None:
    profile = ResourceProfile.minimal()
    assert profile.substrate is Substrate.CLASSICAL
    assert profile.max_mitos_candidates == 2
    assert profile.max_fractal_depth == 1
    assert profile.max_iterations == 4


def test_scaled_profile_increases_budget_without_changing_substrate_contract() -> None:
    profile = ResourceProfile.scaled(substrate=Substrate.QUANTUM, capacity=4)
    assert profile.substrate is Substrate.QUANTUM
    assert profile.max_mitos_candidates == 8
    assert profile.max_fractal_depth == 3
    assert profile.max_iterations == 16


def test_invalid_capacity_is_rejected() -> None:
    with pytest.raises(ValueError):
        ResourceProfile.scaled(capacity=0)


def test_negative_limits_are_rejected() -> None:
    with pytest.raises(ValueError):
        ResourceProfile(max_iterations=0)
