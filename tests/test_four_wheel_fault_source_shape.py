from __future__ import annotations

import numpy as np

from autodrift.four_wheel_dynamics import FourWheelState
from autodrift.four_wheel_fault_source_shape import (
    build_action_lattice,
    build_fault_cases,
    build_fault_pairs,
    build_human_view_observation,
    build_scenarios,
    build_scenarios_for_profile,
    build_source_repair_scenarios,
    build_source_expansion_scenarios,
    build_viability_calibration_scenarios,
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


def test_mixed_action_lattice_contains_drive_sensitive_templates():
    candidates = build_action_lattice(sequence_length=8, action_profile="mixed_emergency_v1")

    templates = {candidate["template"] for candidate in candidates}
    assert "left_steer_throttle" in templates
    assert "right_power_recovery" in templates
    assert len(candidates) > len(build_action_lattice(sequence_length=8))


def test_source_repair_action_lattice_contains_multiphase_templates():
    candidates = build_action_lattice(sequence_length=9, action_profile="source_repair_v1")

    templates = {candidate["template"] for candidate in candidates}
    assert "delayed_left_pulse" in templates
    assert "brake_then_right_swerve" in templates
    assert "left_power_hold" in templates
    assert all(candidate["sequence"].shape == (9, 3) for candidate in candidates)


def test_source_expansion_fault_profile_covers_target_families():
    faults = build_fault_cases("source_expansion_v1")
    pairs = build_fault_pairs(faults, "source_expansion_v1")

    families = {fault.family for fault in faults}
    family_pairs = {f"{left.family}->{right.family}" for left, right in pairs}
    assert {
        "left_right_split_mu",
        "single_wheel_grip_collapse",
        "single_wheel_brake_pull",
        "halfshaft_torque_loss",
        "global_friction_step",
        "steering_actuator_fault",
        "load_cg_perturbation",
        "tire_blowout_like",
    } <= families
    assert "halfshaft_torque_loss->halfshaft_torque_loss" in family_pairs
    assert "tire_blowout_like->tire_blowout_like" in family_pairs
    assert any(fault.params_override for fault in faults if fault.family == "steering_actuator_fault")
    assert any(fault.scales.longitudinal_drag != (0.0, 0.0, 0.0, 0.0) for fault in faults)


def test_source_repair_fault_profile_adds_parameter_repair_pairs():
    faults = build_fault_cases("source_repair_v1")
    pairs = build_fault_pairs(faults, "source_repair_v1")

    names = {fault.name for fault in faults}
    family_pairs = {f"{left.family}->{right.family}" for left, right in pairs}
    assert "global_friction_0p20" in names
    assert "very_slow_steer_tau" in names
    assert "very_heavy_high_inertia" in names
    assert "rear_left_halfshaft_loss_0p0" in names
    assert "global_friction_step->global_friction_step" in family_pairs
    assert "steering_actuator_fault->steering_actuator_fault" in family_pairs
    assert "load_cg_perturbation->load_cg_perturbation" in family_pairs


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


def test_viability_calibration_profile_expands_distance_and_width_axes():
    scenarios = build_viability_calibration_scenarios()

    assert len(scenarios) == 180
    assert {scenario.state.vx for scenario in scenarios} == {14.0, 15.0, 16.0}
    assert {scenario.obstacle_body_x for scenario in scenarios} == {12.0, 13.0, 14.0, 15.0, 16.0}
    assert {scenario.obstacle_body_y for scenario in scenarios} == {-0.25, 0.0, 0.25}
    assert {scenario.obstacle_half_width for scenario in scenarios} == {0.55, 0.65, 0.75, 0.85}
    assert all(scenario.state.brake_force > 0.0 for scenario in scenarios)
    assert build_scenarios_for_profile("viability_calibration") == scenarios


def test_source_expansion_profile_adds_timing_and_speed_bins():
    scenarios = build_source_expansion_scenarios()

    assert scenarios
    assert {scenario.speed_bin for scenario in scenarios} == {"medium", "high"}
    assert {scenario.obstacle_timing_bin for scenario in scenarios} == {"late", "medium"}
    assert all(scenario.curvature_bin == "straight" for scenario in scenarios)
    assert build_scenarios_for_profile("source_expansion_v1") == scenarios


def test_source_repair_profile_adds_drive_and_curvature_states():
    scenarios = build_source_repair_scenarios()

    assert scenarios
    assert any(scenario.state.drive_force > 0.0 and scenario.state.brake_force == 0.0 for scenario in scenarios)
    assert any(abs(scenario.state.yaw_rate) > 0.0 for scenario in scenarios)
    assert any(scenario.curvature_bin != "straight" for scenario in scenarios)
    assert build_scenarios_for_profile("source_repair_v1") == scenarios
