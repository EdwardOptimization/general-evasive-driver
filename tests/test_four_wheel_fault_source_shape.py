from __future__ import annotations

import numpy as np

from autodrift.four_wheel_dynamics import FourWheelState
from autodrift.four_wheel_fault_source_shape import (
    build_action_lattice,
    build_human_view_observation,
    build_scenarios,
    obstacle_margin,
)


def test_human_view_observation_has_clean_shape_and_slots():
    state = FourWheelState(x=0.0, y=0.0, psi=0.0, vx=18.0, vy=0.5, yaw_rate=0.1, brake_force=6000.0)
    obs = build_human_view_observation(
        state=state,
        previous_action=(0.0, -1.0, 1.0),
        obstacle_body_x=10.0,
        obstacle_body_y=-0.3,
        obstacle_half_width=0.85,
    )

    assert obs.shape == (72,)
    assert np.all(np.isfinite(obs))
    assert obs[0] == 0.9
    assert obs[8] == 1.0
    assert obs[44] == 1.0
    assert obs[45] == 10.0 / 80.0
    assert obs[46] == -0.3 / 8.0


def test_action_lattice_contains_left_and_right_sequences():
    candidates = build_action_lattice(sequence_length=8)

    templates = {candidate["template"] for candidate in candidates}
    assert "left_steer_brake" in templates
    assert "right_steer_brake" in templates
    assert "counter_left" in templates
    assert "counter_right" in templates
    assert len({tuple(candidate["candidate_vector"].tolist()) for candidate in candidates}) == len(candidates)
    assert all(candidate["sequence"].shape == (8, 3) for candidate in candidates)


def test_obstacle_margin_detects_collision_and_completion():
    obstacle_world = np.asarray([0.0, 0.0], dtype=np.float64)
    colliding = FourWheelState(x=0.0, y=0.0, psi=0.0, vx=0.0, vy=0.0, yaw_rate=0.0)
    passed = FourWheelState(x=6.0, y=4.0, psi=0.0, vx=0.0, vy=0.0, yaw_rate=0.0)

    margin, collision, completed, _, _ = obstacle_margin(
        colliding,
        obstacle_world,
        obstacle_half_width=0.85,
        obstacle_half_length=1.0,
        vehicle_half_width=0.9,
        vehicle_half_length=2.2,
    )
    assert margin < 0.0
    assert collision
    assert not completed

    margin, collision, completed, _, _ = obstacle_margin(
        passed,
        obstacle_world,
        obstacle_half_width=0.85,
        obstacle_half_length=1.0,
        vehicle_half_width=0.9,
        vehicle_half_length=2.2,
    )
    assert margin > 0.0
    assert not collision
    assert completed


def test_build_scenarios_uses_established_brake_state():
    scenarios = build_scenarios()

    assert scenarios
    assert all(scenario.state.brake_force > 0.0 for scenario in scenarios)
    assert {scenario.obstacle_body_y for scenario in scenarios} == {-0.35, 0.0, 0.35}
