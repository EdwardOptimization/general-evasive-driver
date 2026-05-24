import pandas as pd

from autodrift.boundary_mechanism_projection_selector import (
    build_boundary_mechanism_candidates,
    projected_obstacle_bucket_key,
    select_boundary_mechanism_rows,
    summarize_boundary_mechanism_selection,
)


def _row(index: int) -> dict[str, object]:
    return {
        "probe_seed": 13000 + index % 3,
        "left_seed": 20000 + index,
        "source_pair_id": index,
        "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
        "config": "short" if index % 2 == 0 else "warmup",
        "projected_obstacle_distance": 3.0 + index,
        "projected_obstacle_lateral_offset": -2.0 + 0.25 * index,
        "projected_obstacle_body_y": -2.0 + 0.25 * index,
        "projection_l2": 0.5 + 0.05 * index,
        "projection_dy": 0.0,
        "half_width_delta_abs": 0.1,
        "projected_obstacle_label": "unavoidable",
        "normal_min_clearance_margin": 0.2 if index < 4 else 0.8,
        "first_action_distance": 0.03,
        "action_trajectory_distance_mean": 0.07,
        "action_trajectory_distance_max": 0.10,
        "target_z_delta": 2.0,
    }


def test_projected_obstacle_bucket_key_uses_projected_geometry() -> None:
    bucket = projected_obstacle_bucket_key(
        {
            "projected_obstacle_distance": 6.0,
            "projected_obstacle_lateral_offset": -1.2,
        },
        distance_width=5.0,
        lateral_width=1.0,
    )

    assert bucket == "distance=5.000-10.000|lateral=-2.000--1.000"


def test_build_boundary_mechanism_candidates_filters_boundary_signal_and_projection() -> None:
    frame = pd.DataFrame([_row(0), _row(1), _row(2)])
    frame.loc[1, "normal_min_clearance_margin"] = 3.0
    frame.loc[2, "projection_l2"] = 8.0

    candidates = build_boundary_mechanism_candidates(
        frame,
        max_normal_margin=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        max_projection_l2=6.0,
        max_half_width_delta_abs=0.8,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
        projection_l2_bucket_width=1.0,
        projection_lateral_bucket_width=0.5,
    )

    assert len(candidates) == 1
    assert bool(candidates.iloc[0]["boundary_pass"])
    assert bool(candidates.iloc[0]["soft_action_pass"])
    assert bool(candidates.iloc[0]["bounded_projection_pass"])


def test_select_boundary_mechanism_rows_applies_geometry_and_source_caps() -> None:
    candidates = build_boundary_mechanism_candidates(
        pd.DataFrame([_row(index) for index in range(12)]),
        max_normal_margin=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        max_projection_l2=6.0,
        max_half_width_delta_abs=0.8,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
        projection_l2_bucket_width=1.0,
        projection_lateral_bucket_width=0.5,
    )

    selected = select_boundary_mechanism_rows(
        candidates,
        max_rows=8,
        max_per_probe_seed=4,
        max_per_left_seed=1,
        max_per_source_pair=1,
        max_per_target=4,
        max_per_config=4,
        max_per_obstacle_bucket=4,
        max_per_projection_bucket=4,
    )

    assert len(selected) == 8
    assert selected["target"].value_counts().max() <= 4
    assert selected["config"].value_counts().max() <= 4
    assert selected["projected_obstacle_bucket"].value_counts().max() <= 4


def test_summarize_boundary_mechanism_selection_gate_passes_when_thresholds_met() -> None:
    targeted = build_boundary_mechanism_candidates(
        pd.DataFrame([_row(index) for index in range(8)]),
        max_normal_margin=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        max_projection_l2=6.0,
        max_half_width_delta_abs=0.8,
        obstacle_distance_bucket_width=2.0,
        obstacle_lateral_bucket_width=0.5,
        projection_l2_bucket_width=0.25,
        projection_lateral_bucket_width=0.25,
    )

    summary = summarize_boundary_mechanism_selection(
        scored_pairs=targeted,
        candidates=targeted,
        targeted_pairs=targeted,
        min_pair_count=8,
        min_probe_seed_count=3,
        min_target_count=2,
        min_config_count=2,
        min_projected_obstacle_bucket_count=4,
        min_projection_bucket_count=2,
        max_single_seed_share=0.50,
        max_single_config_share=0.50,
        max_single_target_share=0.50,
        max_single_obstacle_bucket_share=0.25,
        max_single_projection_bucket_share=0.50,
        min_margin_le_0_50_rows=4,
        min_margin_le_1_00_rows=8,
        min_trajectory_mean=0.04,
        min_trajectory_p90=0.06,
    )

    assert summary["mechanism_gate_pass"]
    assert summary["outcome_gate_admitted"]
    assert not summary["scenario_label_diversity_required"]
