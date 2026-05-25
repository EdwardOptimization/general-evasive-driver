from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.v4_low_margin_boundary_axis_expansion import (
    classify_boundary_axis_expansion_result,
    modify_fault_for_axis,
    plan_axis_expansion_candidates,
    select_axis_balanced_rows,
)


def _anchor(**kwargs):
    base = {
        "anchor_id": 0,
        "anchor_pool": "collision_edge",
        "contrast_group_id": "c|4|zero_command_obs|0",
        "seed": 1,
        "source_index": 2,
        "step": 36,
        "preferred_fault": "front_fault",
        "preferred_fault_family": "front_lateral_authority_drop",
        "preferred_fault_severity": "extreme",
        "wrong_fault": "combined_fault",
        "wrong_fault_family": "combined_fault",
        "wrong_fault_severity": "extreme",
        "fault_family_pair": "front_lateral_authority_drop->combined_fault",
        "variant": "zero_command_obs",
        "horizon": 4,
        "alpha": 0.2,
        "source_margin": -0.0002,
        "source_success": False,
        "source_collision": True,
        "source_terminal_reason": "collision",
    }
    base.update(kwargs)
    return base


def test_plan_axis_expansion_candidates_includes_lateral_step_fault_and_brackets():
    fault = FaultSpec(
        name="front_fault",
        family="front_lateral_authority_drop",
        severity="extreme",
        activation_step=30,
        params={"cf_scale": 0.2},
    )
    plan = plan_axis_expansion_candidates(
        [_anchor()],
        faults_by_name={"front_fault": fault},
        target_margins=(0.000025,),
        lateral_deltas=(-0.1, 0.1),
        step_offsets=(-1, 1),
        fault_activation_deltas=(-1, 1),
        fault_severity_deltas=(-0.04, 0.04),
        distance_bracket_deltas=(-0.1, 0.1),
        half_width_bracket_deltas=(-0.003, 0.003),
        max_candidates_per_anchor=None,
    )

    axes = {row["retarget_axis"] for row in plan}
    assert "obstacle_half_width" in axes
    assert "obstacle_lateral_offset" in axes
    assert "source_step_neighborhood" in axes
    assert "fault_activation_step" in axes
    assert "fault_severity" in axes
    assert "bracketed_obstacle_distance" in axes
    assert "bracketed_obstacle_half_width" in axes
    lateral = [row for row in plan if row["retarget_axis"] == "obstacle_lateral_offset"]
    assert {row["obstacle_y_delta_m"] for row in lateral} == {-0.1, 0.1}
    steps = [row for row in plan if row["retarget_axis"] == "source_step_neighborhood"]
    assert {row["target_step"] for row in steps} == {35, 37}


def test_modify_fault_for_axis_clamps_positive_scale_and_changes_activation():
    base = FaultSpec(
        name="delay_fault",
        family="delay_noise_fault",
        severity="extreme",
        activation_step=2,
        params={"steer_tau_scale": 0.01},
    )
    activation = modify_fault_for_axis(
        base,
        {
            "retarget_axis": "fault_activation_step",
            "fault_activation_step_delta": -5,
        },
    )
    assert activation.activation_step == 0
    severity = modify_fault_for_axis(
        base,
        {
            "retarget_axis": "fault_severity",
            "fault_param_key": "steer_tau_scale",
            "fault_severity_delta": -2.0,
        },
    )
    assert severity.params["steer_tau_scale"] > 0.0


def test_select_axis_balanced_rows_enforces_axis_and_source_caps():
    rows = []
    for index in range(12):
        rows.append(
            {
                "candidate_id": index,
                "seed": 1 if index < 8 else 2,
                "source_index": index % 3,
                "fault_family_pair": "a->b",
                "retarget_axis": "obstacle_half_width" if index < 8 else "fault_severity",
                "min_clearance_margin": 0.00002,
            }
        )
    selected = select_axis_balanced_rows(
        rows,
        max_rows_per_seed=3,
        max_rows_per_source_index=2,
        max_rows_per_fault_pair=20,
        max_rows_per_axis=4,
    )

    assert len(selected) <= 6
    assert sum(1 for row in selected if row["seed"] == 1) <= 3
    assert sum(1 for row in selected if row["retarget_axis"] == "obstacle_half_width") <= 4


def test_classify_boundary_axis_expansion_result_distinguishes_axis_and_source_failures():
    rows = [
        {
            "seed": seed,
            "source_index": source,
            "fault_family_pair": f"pair{pair}",
            "retarget_axis": axis,
            "retarget_axis_family": family,
        }
        for seed, source, pair, axis, family in [
            (1, 1, 1, "obstacle_half_width", "obstacle_half_width"),
            (2, 2, 2, "obstacle_lateral_offset", "obstacle_lateral_offset"),
            (3, 3, 3, "bracketed_obstacle_half_width", "bracketed_obstacle_half_width"),
            (4, 4, 4, "bracketed_obstacle_distance", "bracketed_obstacle_distance"),
        ]
    ]
    assert (
        classify_boundary_axis_expansion_result(
            actor_changed=False,
            residual_changed=False,
            reconstruction_failures=0,
            accepted_rows=rows,
            min_rows=4,
            min_seeds=4,
            min_source_indices=4,
            min_fault_pairs=4,
            min_retarget_axes=3,
            max_seed_dominance=0.5,
            max_source_index_dominance=0.5,
            max_fault_pair_dominance=0.5,
            max_axis_dominance=0.6,
            min_axis_rows=1,
            min_axes_with_min_rows=3,
        )
        == "v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic"
    )
    rows[-1]["retarget_axis"] = "fault_severity"
    rows[-1]["retarget_axis_family"] = "fault_severity"
    assert (
        classify_boundary_axis_expansion_result(
            actor_changed=False,
            residual_changed=False,
            reconstruction_failures=0,
            accepted_rows=rows,
            min_rows=4,
            min_seeds=4,
            min_source_indices=4,
            min_fault_pairs=4,
            min_retarget_axes=3,
            max_seed_dominance=0.5,
            max_source_index_dominance=0.5,
            max_fault_pair_dominance=0.5,
            max_axis_dominance=0.6,
            min_axis_rows=1,
            min_axes_with_min_rows=3,
        )
        == "v4_low_margin_boundary_axis_expansion_pass"
    )
