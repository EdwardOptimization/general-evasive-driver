import numpy as np
import pandas as pd

from autodrift.terminal_boundary_anchor_miner import (
    build_anchor_wrong_history_candidates,
    pair_action_boundary_score,
    preliminary_anchor_candidates,
    select_terminal_boundary_anchor_pairs,
    summarize_anchor_mining,
)


def _source_row(index: int, *, config: str = "short", seed: int | None = None, probe_seed: int = 13000) -> dict:
    return {
        "source_index": index,
        "checkpoint_label": "m399",
        "config": config,
        "env_config": f"configs/{config}.json",
        "probe_seed": probe_seed,
        "episode": index,
        "seed": seed if seed is not None else 20000 + index,
        "step": 10 + index,
        "obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
        "obstacle_distance": 8.0 + index,
        "obstacle_lateral_offset": 0.1 * index,
    }


def test_preliminary_anchor_candidates_filters_distance_and_caps_per_config_seed() -> None:
    rows = [_source_row(index, probe_seed=13000) for index in range(5)]
    rows.append({**_source_row(99, probe_seed=13000), "obstacle_distance": 100.0})

    selected = preliminary_anchor_candidates(
        rows,
        max_anchor_obstacle_distance=20.0,
        max_per_config_seed=3,
    )

    assert len(selected) == 3
    assert all(float(row["obstacle_distance"]) <= 20.0 for row in selected)
    assert [row["source_index"] for row in selected] == [0, 1, 2]


def test_build_anchor_wrong_history_candidates_uses_low_current_distance_and_target_delta() -> None:
    rows = [_source_row(index) for index in range(4)]
    anchors = [
        {
            **rows[0],
            "normal_min_clearance_margin": 0.4,
            "normal_success": True,
            "normal_collision": False,
            "normal_terminal_reason": "running",
        }
    ]
    features = {
        "match_features": np.asarray(
            [
                [0.0, 0.0],
                [0.01, 0.01],
                [0.03, 0.03],
                [3.0, 3.0],
            ],
            dtype=np.float32,
        ),
        "target:future_braking_deceleration": np.asarray([0.0, 3.0, 0.1, 0.0], dtype=np.float32),
        "target:future_yaw_response": np.asarray([0.0, 0.1, 3.0, 0.0], dtype=np.float32),
        "target:future_lateral_accel_response": np.asarray([0.0, 0.1, 0.1, 3.0], dtype=np.float32),
    }

    candidates, threshold = build_anchor_wrong_history_candidates(
        anchors=anchors,
        source_rows=rows,
        features=features,
        nearest_k=3,
        max_current_distance_quantile=1.0,
        min_target_z_delta=0.5,
        same_config_only=True,
        exclude_same_seed=True,
        max_pair_score_candidates=0,
    )

    assert threshold > 0.0
    assert candidates
    assert {row["target"] for row in candidates} >= {
        "future_braking_deceleration",
        "future_yaw_response",
    }
    assert all(row["left_seed"] != row["right_seed"] for row in candidates)


def test_select_terminal_boundary_anchor_pairs_applies_soft_action_and_caps() -> None:
    rows = []
    for index in range(10):
        row = {
            "probe_seed": 13000 + index % 4,
            "left_seed": 20000 + index,
            "left_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
            "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
            "config": "short" if index < 5 else "warmup",
            "left_obstacle_distance": 10.0 + index,
            "left_obstacle_lateral_offset": 0.2 * index,
            "normal_min_clearance_margin": 0.05 * index,
            "first_action_distance": 0.03,
            "action_trajectory_distance_mean": 0.05,
            "action_trajectory_distance_max": 0.07,
            "target_z_delta": 2.0,
        }
        row["pair_action_boundary_score"] = pair_action_boundary_score(row, candidate_margin_max=2.0)
        rows.append(row)

    selected = select_terminal_boundary_anchor_pairs(
        pd.DataFrame(rows),
        candidate_margin_max=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        max_rows=6,
        max_per_probe_seed=3,
        max_per_left_seed=1,
        max_per_label=4,
        max_per_target=4,
        max_per_config=3,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    assert len(selected) == 6
    assert selected["config"].value_counts().max() <= 3
    assert selected["soft_action_pass"].all()
    assert selected["normal_min_clearance_margin"].max() <= 2.0


def test_summarize_anchor_mining_gate_passes_when_thresholds_met() -> None:
    anchors = pd.DataFrame(
        [
            {
                "anchor_margin_pass": True,
                "probe_seed": 13000 + index % 2,
                "obstacle_label": "drift_required",
                "config": "short",
            }
            for index in range(4)
        ]
    )
    targeted = pd.DataFrame(
        [
            {
                "probe_seed": 13000 + index % 2,
                "left_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
                "target": "future_yaw_response",
                "config": "short" if index % 2 == 0 else "warmup",
                "normal_min_clearance_margin": 0.25 if index < 2 else 0.75,
                "action_trajectory_distance_mean": 0.10,
                "first_action_distance": 0.05,
            }
            for index in range(4)
        ]
    )

    summary = summarize_anchor_mining(
        source_rows=[],
        anchor_candidates=[],
        scored_anchors=anchors,
        candidate_pairs=targeted,
        scored_pairs=targeted,
        targeted_pairs=targeted,
        current_distance_threshold=0.1,
        min_anchor_count=4,
        min_pair_count=4,
        min_probe_seed_count=2,
        min_obstacle_label_count=2,
        min_config_count=2,
        max_single_seed_share=0.50,
        max_single_label_share=0.50,
        max_single_config_share=0.50,
        min_margin_le_0_50_rows=2,
        min_margin_le_1_00_rows=4,
        min_trajectory_mean=0.04,
        min_trajectory_p90=0.08,
    )

    assert summary["terminal_boundary_anchor_gate_pass"]
    assert summary["outcome_gate_admitted"]
