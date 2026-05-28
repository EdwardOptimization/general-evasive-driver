from __future__ import annotations

import numpy as np
import pytest

from autodrift.four_wheel_dynamics import (
    FourWheelDriftModel,
    FourWheelFaultScales,
    FourWheelState,
    FourWheelVehicleParams,
)


def _state() -> FourWheelState:
    return FourWheelState(x=0.0, y=0.0, psi=0.0, vx=18.0, vy=0.2, yaw_rate=0.0)


def _brake_action() -> np.ndarray:
    return np.asarray([0.0, -1.0, 1.0], dtype=np.float32)


def test_nominal_four_wheel_step_is_finite():
    model = FourWheelDriftModel()
    state, forces = model.step(_state(), np.asarray([0.1, 0.0, -1.0], dtype=np.float32), 0.02)

    assert np.all(np.isfinite(state.as_array()))
    assert np.isfinite(forces.total_fx)
    assert np.isfinite(forces.total_fy)
    assert np.isfinite(forces.yaw_moment)
    assert len(forces.wheels) == 4


def test_split_mu_braking_creates_signed_yaw_moment():
    base_state = FourWheelState(x=0.0, y=0.0, psi=0.0, vx=18.0, vy=0.0, yaw_rate=0.0, brake_force=6000.0)
    left_low = FourWheelDriftModel(fault_scales=FourWheelFaultScales.split_mu(left_scale=0.25, right_scale=1.0))
    right_low = FourWheelDriftModel(fault_scales=FourWheelFaultScales.split_mu(left_scale=1.0, right_scale=0.25))

    _, left_low_forces = left_low.step(base_state, _brake_action(), 0.02)
    _, right_low_forces = right_low.step(base_state, _brake_action(), 0.02)

    assert left_low_forces.yaw_moment < -100.0
    assert right_low_forces.yaw_moment > 100.0
    assert left_low_forces.yaw_moment * right_low_forces.yaw_moment < 0.0


def test_single_wheel_brake_pull_creates_signed_yaw_moment():
    base_state = FourWheelState(x=0.0, y=0.0, psi=0.0, vx=18.0, vy=0.0, yaw_rate=0.0)
    left_pull = FourWheelDriftModel(fault_scales=FourWheelFaultScales.single_wheel_brake_pull("front_left", brake_scale=2.0))
    right_pull = FourWheelDriftModel(
        fault_scales=FourWheelFaultScales.single_wheel_brake_pull("front_right", brake_scale=2.0)
    )

    _, left_forces = left_pull.step(base_state, _brake_action(), 0.02)
    _, right_forces = right_pull.step(base_state, _brake_action(), 0.02)

    assert left_forces.yaw_moment > 100.0
    assert right_forces.yaw_moment < -100.0
    assert left_forces.yaw_moment * right_forces.yaw_moment < 0.0


def test_single_wheel_grip_collapse_reduces_capacity():
    nominal = FourWheelDriftModel()
    collapsed = FourWheelDriftModel(
        fault_scales=FourWheelFaultScales.single_wheel_grip_collapse(
            "rear_left",
            mu_scale=0.2,
            lateral_stiffness_scale=0.2,
        )
    )
    state = _state()
    action = np.asarray([0.2, 0.2, 0.0], dtype=np.float32)

    _, nominal_forces = nominal.step(state, action, 0.02)
    _, collapsed_forces = collapsed.step(state, action, 0.02)

    assert collapsed_forces.wheel("rear_left").mu_capacity < 0.25 * nominal_forces.wheel("rear_left").mu_capacity
    assert abs(collapsed_forces.wheel("rear_left").fy_wheel) < abs(nominal_forces.wheel("rear_left").fy_wheel)


def test_unknown_wheel_fault_name_rejected():
    with pytest.raises(ValueError, match="unknown wheel"):
        FourWheelFaultScales.single_wheel_brake_pull("middle_left", brake_scale=2.0)
