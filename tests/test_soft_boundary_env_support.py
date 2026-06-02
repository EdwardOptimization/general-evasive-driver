from __future__ import annotations

import math

import numpy as np

from autodrift.dynamics import VehicleState
from autodrift.env import AutoDriftEnv, DriftEnvConfig


def _env(*, enabled: bool, tolerance: float = 0.2) -> AutoDriftEnv:
    return AutoDriftEnv(
        DriftEnvConfig(
            track_radius=10.0,
            track_width=2.0,
            soft_offtrack_metric_enabled=enabled,
            soft_offtrack_tolerance_m=tolerance,
        )
    )


def _frame(env: AutoDriftEnv, *, lateral_error: float):
    radius = env.config.track_radius + lateral_error
    env.state = VehicleState(
        x=radius,
        y=0.0,
        psi=math.pi / 2.0,
        vx=8.0,
        vy=0.0,
        yaw_rate=0.0,
        steer=0.0,
        drive_force=0.0,
    )
    return env.track.frame(env.state.x, env.state.y, env.state.psi)


def test_default_offtrack_termination_is_unchanged() -> None:
    env = _env(enabled=False)
    frame = _frame(env, lateral_error=2.05)

    assert env._termination_reason(frame) == "off_track"
    info = env._info(frame)
    assert info["soft_offtrack_metric_enabled"] is False
    assert info["soft_offtrack_violation"] is False
    assert info["hard_offtrack_failure"] is True


def test_soft_boundary_continues_inside_tolerance_and_terminates_beyond_it() -> None:
    env = _env(enabled=True, tolerance=0.2)
    inside = _frame(env, lateral_error=2.05)
    outside = _frame(env, lateral_error=2.25)

    assert env._termination_reason(inside) is None
    assert env._soft_offtrack_violation(inside) is True
    assert env._hard_offtrack_failure(inside) is False
    assert env._termination_reason(outside) == "off_track"
    assert env._soft_offtrack_violation(outside) is False
    assert env._hard_offtrack_failure(outside) is True


def test_soft_boundary_observation_shape_is_unchanged() -> None:
    base = AutoDriftEnv(DriftEnvConfig(track_radius=10.0, track_width=2.0))
    soft = _env(enabled=True, tolerance=0.2)

    assert base.observation_space.shape == soft.observation_space.shape


def test_soft_boundary_step_diagnostics_accumulate() -> None:
    env = _env(enabled=True, tolerance=0.2)
    env.reset(seed=1)
    env.state = VehicleState(
        x=env.config.track_radius + env.config.track_width + 0.05,
        y=0.0,
        psi=math.pi / 2.0,
        vx=8.0,
        vy=0.0,
        yaw_rate=0.0,
        steer=0.0,
        drive_force=0.0,
    )

    _, _, terminated, _, info = env.step(np.zeros(3, dtype=np.float32))

    assert terminated is False
    assert info["soft_offtrack_violation"] is True
    assert info["soft_offtrack_step_count"] == 1
    assert info["soft_offtrack_duration_s"] == env.config.dt
    assert info["hard_offtrack_failure"] is False
