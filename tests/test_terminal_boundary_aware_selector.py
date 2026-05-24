import pandas as pd

from autodrift.terminal_boundary_aware_selector import (
    build_terminal_boundary_candidates,
    low_margin_bonus,
    select_terminal_boundary_rows,
    terminal_boundary_score,
)


def test_low_margin_bonus_prefers_low_margin() -> None:
    assert low_margin_bonus(0.0, 2.0) > low_margin_bonus(1.5, 2.0)
    assert low_margin_bonus(3.0, 2.0) == 0.0


def test_terminal_boundary_candidate_filter_requires_boundary_and_soft_action() -> None:
    frame = pd.DataFrame(
        [
            {
                "normal_min_clearance_margin": 0.5,
                "first_action_distance": 0.03,
                "action_trajectory_distance_mean": 0.05,
                "action_trajectory_distance_max": 0.05,
                "target_z_delta": 1.0,
                "left_obstacle_label": "unavoidable",
            },
            {
                "normal_min_clearance_margin": 3.0,
                "first_action_distance": 0.20,
                "action_trajectory_distance_mean": 0.20,
                "action_trajectory_distance_max": 0.20,
                "target_z_delta": 4.0,
                "left_obstacle_label": "drift_required",
            },
            {
                "normal_min_clearance_margin": 0.2,
                "first_action_distance": 0.01,
                "action_trajectory_distance_mean": 0.01,
                "action_trajectory_distance_max": 0.01,
                "target_z_delta": 4.0,
                "left_obstacle_label": "drift_required",
            },
        ]
    )

    candidates = build_terminal_boundary_candidates(
        frame,
        max_normal_margin=2.0,
        first_action_threshold=0.04,
        trajectory_mean_threshold=0.04,
        trajectory_max_threshold=0.08,
    )

    assert len(candidates) == 1
    assert candidates.iloc[0]["boundary_pass"]
    assert candidates.iloc[0]["soft_action_pass"]


def test_terminal_boundary_selection_applies_caps() -> None:
    rows = []
    for index in range(8):
        row = {
            "probe_seed": 100 + index % 4,
            "left_seed": 200 + index,
            "left_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
            "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
            "config": "boundary_short_reveal" if index < 4 else "boundary_warmup",
            "decision_offset": index % 4,
            "left_obstacle_distance": 8.0 + index,
            "left_obstacle_lateral_offset": 0.1 * index,
            "normal_min_clearance_margin": 0.1 * index,
            "first_action_distance": 0.08,
            "action_trajectory_distance_mean": 0.07,
            "action_trajectory_distance_max": 0.10,
            "target_z_delta": 2.0,
        }
        row["terminal_boundary_score"] = terminal_boundary_score(row, boundary_margin=2.0)
        rows.append(row)
    frame = pd.DataFrame(rows)

    selected = select_terminal_boundary_rows(
        frame,
        max_rows=4,
        max_per_probe_seed=2,
        max_per_left_seed=1,
        max_per_label=3,
        max_per_target=3,
        max_per_config=2,
        max_per_offset=2,
        max_per_obstacle_bucket=4,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    assert len(selected) == 4
    assert selected["config"].value_counts().max() <= 2
    assert selected["normal_min_clearance_margin"].is_monotonic_increasing
