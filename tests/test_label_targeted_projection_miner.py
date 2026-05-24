import pandas as pd

from autodrift.label_targeted_projection_miner import (
    build_label_targeted_projection_candidates,
    parse_label_values,
    select_label_targeted_projected_pairs,
    summarize_label_targeted_projection,
)


def test_parse_label_values_requires_nonempty() -> None:
    assert parse_label_values("drift_required, unavoidable") == ("drift_required", "unavoidable")

    try:
        parse_label_values("")
    except Exception as exc:
        assert "label" in str(exc)
    else:
        raise AssertionError("empty label list should be rejected")


def test_build_label_targeted_projection_candidates_expands_width_scales() -> None:
    source_pairs = pd.DataFrame(
        [
            {
                "left_obstacle_distance": 5.0,
                "left_obstacle_lateral_offset": -1.0,
                "normal_min_clearance_margin": 0.2,
                "action_trajectory_distance_mean": 0.1,
                "target_z_delta": 2.0,
            }
        ]
    )

    candidates = build_label_targeted_projection_candidates(
        source_pairs=source_pairs,
        absolute_longitudinal=(4.0, 8.0),
        lateral_deltas=(0.0,),
        half_width_scales=(0.75, 1.0),
        min_longitudinal=3.0,
        diagnostic_projection_l2_max=4.0,
        max_projected_candidates=0,
    )

    assert len(candidates) == 4
    assert set(candidates["half_width_scale"]) == {0.75, 1.0}
    assert candidates["proof_surface_type"].eq("label_targeted_obstacle_boundary_projection").all()


def test_select_label_targeted_projected_pairs_requires_allowed_projected_label() -> None:
    rows = []
    for index in range(8):
        rows.append(
            {
                "probe_seed": 13000 + index % 2,
                "left_seed": 20000 + index,
                "projected_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
                "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
                "config": "short" if index < 4 else "warmup",
                "projected_obstacle_distance": 6.0 + index,
                "projected_obstacle_lateral_offset": -1.0 + 0.1 * index,
                "projection_l2": 1.0,
                "half_width_delta_abs": 0.1,
                "normal_min_clearance_margin": 0.1 * index,
                "first_action_distance": 0.03,
                "action_trajectory_distance_mean": 0.06,
                "action_trajectory_distance_max": 0.08,
                "target_z_delta": 2.0,
                "pair_action_boundary_score": 2.0,
            }
        )

    selected = select_label_targeted_projected_pairs(
        pd.DataFrame(rows),
        target_projected_labels=("drift_required",),
        candidate_margin_max=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        primary_projection_l2_max=8.0,
        primary_half_width_delta_abs_max=0.4,
        max_rows=8,
        max_per_probe_seed=8,
        max_per_left_seed=1,
        max_per_label=8,
        max_per_target=8,
        max_per_config=8,
        max_per_obstacle_bucket=8,
        max_per_projection_bucket=8,
    )

    assert len(selected) == 4
    assert selected["projected_obstacle_label"].eq("drift_required").all()
    assert selected["primary_projection"].all()


def test_summarize_label_targeted_projection_gate_passes_when_thresholds_met() -> None:
    targeted = pd.DataFrame(
        [
            {
                "probe_seed": 13000 + index % 2,
                "projected_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
                "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
                "config": "short" if index % 2 == 0 else "warmup",
                "normal_min_clearance_margin": 0.25 if index < 2 else 0.75,
                "action_trajectory_distance_mean": 0.10,
                "projection_l2": 2.0,
                "half_width_delta_abs": 0.1,
                "primary_projection": True,
            }
            for index in range(4)
        ]
    )

    summary = summarize_label_targeted_projection(
        source_pairs=targeted,
        projected_pairs=targeted,
        scored_pairs=targeted,
        targeted_pairs=targeted,
        min_pair_count=4,
        min_probe_seed_count=2,
        min_projected_obstacle_label_count=2,
        min_target_count=2,
        min_config_count=2,
        max_single_seed_share=0.50,
        max_single_projected_label_share=0.50,
        max_single_config_share=0.50,
        min_margin_le_0_50_rows=2,
        min_margin_le_1_00_rows=4,
        min_trajectory_mean=0.04,
        min_trajectory_p90=0.08,
        max_projection_l2_p50=5.0,
        max_projection_l2_p90=8.0,
        max_half_width_delta_abs_p90=0.4,
        min_primary_projection_share=0.8,
    )

    assert summary["projection_gate_pass"]
    assert summary["outcome_gate_admitted"]
