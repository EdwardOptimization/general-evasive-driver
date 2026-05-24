from pathlib import Path

import pandas as pd
import pytest

from autodrift.natural_wrong_history_action_sensitive_selector import (
    action_sensitive_score,
    parse_env_config_map,
    select_action_sensitive_rows,
    snapshot_requests,
)


def test_parse_env_config_map_requires_name_path() -> None:
    assert parse_env_config_map("short=configs/example.json") == ("short", Path("configs/example.json"))
    with pytest.raises(ValueError):
        parse_env_config_map("configs/example.json")
    with pytest.raises(ValueError):
        parse_env_config_map("=configs/example.json")


def test_snapshot_requests_adds_offsets_for_both_sides() -> None:
    rows = pd.DataFrame(
        [
            {
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 10,
                "right_step": 20,
            }
        ]
    )

    assert snapshot_requests(rows, (0, 3)) == {1: {10, 13}, 2: {20, 23}}


def test_action_sensitive_selection_applies_thresholds_and_caps() -> None:
    rows = []
    for index in range(8):
        rows.append(
            {
                "probe_seed": 100 + index % 4,
                "left_seed": 200 + index,
                "left_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
                "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
                "config": "short_reveal" if index < 4 else "warmup_capability",
                "decision_offset": index % 4,
                "left_obstacle_distance": 8.0 + index,
                "left_obstacle_lateral_offset": 0.1 * index,
                "first_action_distance": 0.20,
                "action_trajectory_distance_mean": 0.15,
                "action_trajectory_distance_max": 0.30,
                "target_z_delta": 2.0,
                "visible_distance": 0.05,
                "visible_threshold": 0.10,
            }
        )
    frame = pd.DataFrame(rows)
    frame["action_sensitive_score"] = [action_sensitive_score(row) for row in frame.to_dict(orient="records")]

    selected = select_action_sensitive_rows(
        frame,
        first_action_threshold=0.12,
        trajectory_mean_threshold=0.12,
        trajectory_max_threshold=0.25,
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
    assert selected["stage1_pass"].all()
    assert selected["trajectory_pass"].all()
