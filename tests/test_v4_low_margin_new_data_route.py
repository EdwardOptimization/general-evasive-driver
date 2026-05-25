from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.v4_low_margin_new_data_route import (
    WARMUP_MODES,
    build_fault_variants,
    build_source_groups,
    classify_new_data_route_result,
    plan_boundary_candidates,
    select_source_balanced_rows,
    warmup_action_delta,
)


def _fault(name: str, family: str = "front_lateral_authority_drop", params=None) -> FaultSpec:
    return FaultSpec(
        name=name,
        family=family,
        severity="extreme",
        activation_step=30,
        params=params or {"cf_scale": 0.2},
        fidelity_class="current_model_proxy",
    )


def test_warmup_action_delta_is_bounded_and_mode_specific():
    natural = warmup_action_delta(
        "natural_policy",
        step_index=0,
        steer_amplitude=0.08,
        brake_amplitude=0.08,
        period_steps=8,
    )
    assert natural.tolist() == [0.0, 0.0, 0.0]
    steer = warmup_action_delta(
        "steer_pulse_left_right",
        step_index=2,
        steer_amplitude=0.08,
        brake_amplitude=0.08,
        period_steps=8,
    )
    assert abs(float(steer[0])) <= 0.08
    assert float(steer[2]) == 0.0
    brake = warmup_action_delta(
        "brake_tap",
        step_index=0,
        steer_amplitude=0.08,
        brake_amplitude=0.08,
        period_steps=8,
    )
    assert float(brake[0]) == 0.0
    assert 0.0 < float(brake[2]) <= 0.08


def test_build_fault_variants_and_source_groups_keep_diversity():
    faults = [
        _fault("front", "front_lateral_authority_drop"),
        _fault("rear", "rear_lateral_authority_drop", {"cr_scale": 0.2}),
        _fault("brake", "brake_authority_drop", {"max_brake_force_scale": 0.3}),
    ]
    variants = build_fault_variants(
        faults,
        max_base_faults=3,
        max_fault_specs=9,
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    assert len(variants) == 9
    assert any("__m811_fault_activation_step_" in fault.name for fault in variants)
    assert any("__m811_fault_severity_" in fault.name for fault in variants)

    groups = build_source_groups(
        seed_start=10,
        seed_count=6,
        fault_specs=variants,
        warmup_modes=WARMUP_MODES,
        max_source_groups=24,
    )
    assert len(groups) == 24
    assert len({row["seed"] for row in groups}) == 6
    assert len({row["warmup_mode"] for row in groups}) == len(WARMUP_MODES)
    assert len({row["preferred_fault_family"] for row in groups}) >= 3


def test_plan_boundary_candidates_uses_source_axes_and_geometry_axes():
    meta = {
        "source_group_id": 1,
        "snapshot_uid": "1:2:30",
        "source_index": 3,
        "seed": 10,
        "step": 30,
        "warmup_mode": "combined_micro_probe",
        "preferred_fault": "front",
        "preferred_fault_family": "front_lateral_authority_drop",
        "preferred_fault_severity": "extreme",
        "wrong_fault": "nominal",
        "wrong_fault_family": "nominal",
        "fault_family_pair": "front_lateral_authority_drop->nominal",
        "source_axis": "warmup_probe_mode",
        "horizon": 6,
        "source_obstacle_body_x": 20.0,
        "source_obstacle_body_y": 0.5,
        "source_obstacle_half_width": 0.8,
        "fault_activation_step_delta": 0,
        "fault_severity_delta": 0.0,
        "fault_param_key": "",
        "road_curvature_bucket": "current_track",
        "initial_speed_bucket": "4",
    }
    source_result = {
        "min_clearance_margin": -0.0002,
        "success": False,
        "collision": True,
        "terminal_reason": "collision",
    }
    rows = plan_boundary_candidates(
        meta,
        source_result,
        alpha=0.2,
        target_margins=(0.000025,),
        obstacle_timing_deltas=(-0.1, 0.1),
        lateral_deltas=(-0.2, 0.2),
        half_width_deltas=(-0.003, 0.003),
        collision_margin_floor=-0.001,
        safe_margin_ceiling=0.01,
        diagnostic_safe_margin_ceiling=0.2,
        max_candidates_per_snapshot=20,
    )
    axes = {row["boundary_axis"] for row in rows}
    assert "warmup_probe_mode" in axes
    assert "obstacle_timing" in axes
    assert "obstacle_lateral_offset" in axes
    assert "obstacle_half_width" in axes
    assert any(row["obstacle_half_width_delta"] < 0.0 for row in rows)


def test_select_and_classify_new_data_route_rows():
    rows = []
    for idx in range(30):
        rows.append(
            {
                "candidate_id": idx,
                "seed": idx % 10,
                "source_group_id": idx % 15,
                "source_index": idx,
                "fault_family_pair": f"pair{idx % 5}",
                "warmup_mode": "natural_policy" if idx % 2 == 0 else "brake_tap",
                "boundary_axis": ["obstacle_timing", "obstacle_lateral_offset", "fault_severity"][idx % 3],
                "min_clearance_margin": 0.00002,
            }
        )
    selected = select_source_balanced_rows(
        rows,
        max_rows_per_seed=4,
        max_rows_per_source_group=3,
        max_rows_per_fault_pair=8,
        max_rows_per_boundary_axis=12,
    )
    assert selected
    assert (
        classify_new_data_route_result(
            actor_changed=False,
            residual_changed=False,
            warmup_artifact_rows=0,
            replay_errors=0,
                accepted_rows=selected,
                min_rows=30,
                min_seeds=8,
                min_source_groups=10,
                min_source_indices=30,
                min_fault_pairs=5,
                min_warmup_modes=2,
                min_boundary_axes=3,
                max_seed_dominance=0.2,
                max_source_group_dominance=0.2,
                max_fault_pair_dominance=0.3,
                max_boundary_axis_dominance=0.6,
            )
            == "v4_low_margin_new_data_route_pass"
    )
    assert (
        classify_new_data_route_result(
            actor_changed=False,
            residual_changed=False,
            warmup_artifact_rows=1,
            replay_errors=0,
                accepted_rows=selected,
                min_rows=30,
                min_seeds=8,
                min_source_groups=10,
                min_source_indices=30,
                min_fault_pairs=5,
                min_warmup_modes=2,
                min_boundary_axes=3,
                max_seed_dominance=0.2,
                max_source_group_dominance=0.2,
                max_fault_pair_dominance=0.3,
                max_boundary_axis_dominance=0.6,
            )
            == "v4_low_margin_new_data_route_warmup_probe_artifact"
    )
