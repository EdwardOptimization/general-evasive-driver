from autodrift.v4_low_margin_boundary_window_retarget import (
    classify_boundary_window_result,
    plan_retarget_candidates,
    select_boundary_anchor_rows,
)


def _row(**kwargs):
    base = {
        "branch": "normal",
        "alpha": "0.2",
        "contrast_group_id": "g0",
        "seed": "1",
        "source_index": "2",
        "step": "30",
        "preferred_fault": "front_fault",
        "preferred_fault_family": "front_lateral_authority_drop",
        "preferred_fault_severity": "extreme",
        "wrong_fault": "combined_fault",
        "wrong_fault_family": "combined_fault",
        "wrong_fault_severity": "extreme",
        "fault_family_pair": "front_lateral_authority_drop->combined_fault",
        "variant": "zero_command_obs",
        "horizon": "4",
        "min_clearance_margin": "0.0",
        "success": "true",
        "collision": "false",
        "terminal_reason": "obstacle_completed",
    }
    base.update(kwargs)
    return base


def test_select_boundary_anchor_rows_splits_collision_safe_and_diagnostic():
    rows = [
        _row(contrast_group_id="c|4|zero_command_obs|0", variant="normal", min_clearance_margin="-0.0002", success="false", collision="true"),
        _row(contrast_group_id="s|4|zero_command_obs|0", variant="normal", min_clearance_margin="0.005", success="true", collision="false"),
        _row(contrast_group_id="d|4|zero_command_obs|0", variant="normal", min_clearance_margin="0.12", success="true", collision="false"),
        _row(contrast_group_id="far", min_clearance_margin="0.3", success="true", collision="false"),
        _row(contrast_group_id="other_alpha", alpha="0.125", min_clearance_margin="-0.0002", collision="true"),
    ]

    anchors = select_boundary_anchor_rows(
        rows,
        alpha=0.2,
        collision_margin_floor=-0.001,
        safe_margin_ceiling=0.01,
        diagnostic_safe_margin_ceiling=0.2,
    )

    assert [row["anchor_pool"] for row in anchors] == [
        "collision_edge",
        "safe_edge",
        "diagnostic_safe",
    ]


def test_plan_retarget_candidates_targets_half_width_boundary():
    anchors = [
        {
            "anchor_id": 0,
            "anchor_pool": "collision_edge",
            "source_margin": -0.0002,
            "seed": 1,
            "source_index": 2,
            "fault_family_pair": "a->b",
        },
        {
            "anchor_id": 1,
            "anchor_pool": "safe_edge",
            "source_margin": 0.005,
            "seed": 3,
            "source_index": 4,
            "fault_family_pair": "c->d",
        },
    ]

    plan = plan_retarget_candidates(
        anchors,
        target_margins=(0.000025,),
        distance_deltas=(0.1,),
        max_half_width_delta=0.01,
        max_distance_delta=0.25,
        max_candidates_per_anchor=8,
    )

    half_width = [row for row in plan if row["retarget_axis"] == "obstacle_half_width"]
    assert len(half_width) == 2
    assert half_width[0]["half_width_delta_m"] < 0.0
    assert half_width[1]["half_width_delta_m"] > 0.0
    distance = [row for row in plan if row["retarget_axis"] == "obstacle_distance"]
    assert distance[0]["obstacle_distance_delta_m"] > 0.0
    assert distance[1]["obstacle_distance_delta_m"] < 0.0


def test_classify_boundary_window_result_requires_axis_and_source_diversity():
    rows = [
        {
            "seed": seed,
            "source_index": source,
            "fault_family_pair": f"pair{pair}",
            "retarget_axis": axis,
        }
        for seed, source, pair, axis in [
            (1, 1, 1, "obstacle_half_width"),
            (2, 2, 2, "obstacle_half_width"),
            (3, 3, 3, "obstacle_half_width"),
            (4, 4, 4, "obstacle_half_width"),
        ]
    ]
    assert (
        classify_boundary_window_result(
            actor_changed=False,
            residual_changed=False,
            reconstruction_failures=0,
            accepted_rows=rows,
            min_rows=4,
            min_seeds=4,
            min_source_indices=4,
            min_fault_pairs=4,
            max_seed_dominance=0.5,
            max_source_index_dominance=0.5,
            max_fault_pair_dominance=0.5,
        )
        == "v4_low_margin_boundary_window_geometry_only_diagnostic"
    )
    rows[-1]["retarget_axis"] = "obstacle_distance"
    assert (
        classify_boundary_window_result(
            actor_changed=False,
            residual_changed=False,
            reconstruction_failures=0,
            accepted_rows=rows,
            min_rows=4,
            min_seeds=4,
            min_source_indices=4,
            min_fault_pairs=4,
            max_seed_dominance=0.5,
            max_source_index_dominance=0.5,
            max_fault_pair_dominance=0.5,
        )
        == "v4_low_margin_boundary_window_pass"
    )
