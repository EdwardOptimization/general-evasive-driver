import numpy as np
import pandas as pd
import torch

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.obstacle_boundary_projection_miner import (
    build_projection_candidates,
    projection_grid_for_source,
    relocate_outcome_snapshot,
    select_projected_pairs,
    summarize_projection_mining,
)


def test_projection_grid_clamps_longitudinal_and_deduplicates() -> None:
    grid = projection_grid_for_source(
        source_x=1.0,
        source_y=-1.0,
        longitudinal_deltas=(-2.0, 0.0, 1.0),
        absolute_longitudinal=(3.0,),
        lateral_deltas=(0.0, 0.5),
        min_longitudinal=3.0,
    )

    positions = {(row["projected_obstacle_body_x"], row["projected_obstacle_body_y"]) for row in grid}
    assert positions == {(3.0, -1.0), (3.0, -0.5)}
    assert all(row["projection_l2"] >= 0.0 for row in grid)


def test_relocate_outcome_snapshot_preserves_hidden_and_updates_obstacle_observation() -> None:
    config = DriftEnvConfig(
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(20.0, 20.0),
            half_width_range=(0.5, 0.5),
            finish_on_pass=True,
        )
    )
    env = AutoDriftEnv(config)
    obs, info = env.reset(seed=123)
    hidden = np.ones((1, 4), dtype=np.float32)
    snapshot = OutcomeSnapshot(
        seed=123,
        step=int(info["step"]),
        observation=obs.copy(),
        hidden=torch.as_tensor(hidden),
        env=env,
        info=info,
    )

    relocated = relocate_outcome_snapshot(
        snapshot,
        body_longitudinal=8.0,
        body_lateral=-1.5,
    )

    assert isinstance(relocated, OutcomeSnapshot)
    assert np.allclose(relocated.hidden.detach().cpu().numpy(), hidden)
    assert relocated.info["snapshot_relocated"]
    assert np.isclose(relocated.observation[45], 8.0 / 80.0)
    assert np.isclose(relocated.observation[46], -1.5 / 20.0)


def test_build_projection_candidates_filters_by_diagnostic_cap() -> None:
    source_pairs = pd.DataFrame(
        [
            {
                "left_obstacle_distance": 4.0,
                "left_obstacle_lateral_offset": -1.0,
                "normal_min_clearance_margin": 0.2,
                "action_trajectory_distance_mean": 0.1,
                "target_z_delta": 2.0,
            }
        ]
    )

    candidates = build_projection_candidates(
        source_pairs=source_pairs,
        longitudinal_deltas=(0.0, 8.0),
        absolute_longitudinal=(),
        lateral_deltas=(0.0,),
        min_longitudinal=3.0,
        primary_projection_l2_max=3.0,
        diagnostic_projection_l2_max=6.0,
        max_projected_candidates=0,
    )

    assert len(candidates) == 1
    assert bool(candidates.iloc[0]["primary_projection"])
    assert candidates.iloc[0]["proof_surface_type"] == "obstacle_boundary_projection"


def test_select_projected_pairs_applies_projection_and_source_caps() -> None:
    rows = []
    for index in range(12):
        row = {
            "probe_seed": 13000 + index % 4,
            "left_seed": 20000 + index,
            "projected_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
            "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
            "config": "short" if index < 6 else "warmup",
            "projected_obstacle_distance": 5.0 + index * 0.2,
            "projected_obstacle_lateral_offset": -1.0 + 0.1 * index,
            "projection_l2": 0.5 + 0.1 * index,
            "projection_family": "primary",
            "normal_min_clearance_margin": 0.1 * index,
            "first_action_distance": 0.03,
            "action_trajectory_distance_mean": 0.06,
            "action_trajectory_distance_max": 0.08,
            "target_z_delta": 2.0,
            "pair_action_boundary_score": 2.0,
        }
        rows.append(row)

    selected = select_projected_pairs(
        pd.DataFrame(rows),
        candidate_margin_max=2.0,
        first_action_threshold=0.02,
        trajectory_mean_threshold=0.02,
        trajectory_max_threshold=0.05,
        primary_projection_l2_max=6.0,
        max_rows=8,
        max_per_probe_seed=3,
        max_per_left_seed=1,
        max_per_label=5,
        max_per_target=5,
        max_per_config=4,
        max_per_obstacle_bucket=8,
        max_per_projection_bucket=8,
    )

    assert len(selected) == 8
    assert selected["config"].value_counts().max() <= 4
    assert selected["primary_projection"].all()
    assert selected["soft_action_pass"].all()


def test_summarize_projection_mining_gate_passes_when_thresholds_met() -> None:
    targeted = pd.DataFrame(
        [
            {
                "probe_seed": 13000 + index % 2,
                "projected_obstacle_label": "drift_required" if index % 2 == 0 else "unavoidable",
                "target": "future_yaw_response" if index % 2 == 0 else "future_braking_deceleration",
                "config": "short" if index % 2 == 0 else "warmup",
                "normal_min_clearance_margin": 0.25 if index < 2 else 0.75,
                "action_trajectory_distance_mean": 0.10,
                "first_action_distance": 0.05,
                "projection_l2": 1.0 + 0.1 * index,
                "primary_projection": True,
                "projection_family": "primary",
            }
            for index in range(4)
        ]
    )

    summary = summarize_projection_mining(
        source_pairs=targeted,
        projected_pairs=targeted,
        scored_pairs=targeted,
        targeted_pairs=targeted,
        min_pair_count=4,
        min_probe_seed_count=2,
        min_obstacle_label_count=2,
        min_target_count=2,
        min_config_count=2,
        max_single_seed_share=0.50,
        max_single_label_share=0.50,
        max_single_config_share=0.50,
        min_margin_le_0_50_rows=2,
        min_margin_le_1_00_rows=4,
        min_trajectory_mean=0.04,
        min_trajectory_p90=0.08,
        max_projection_l2_p50=3.0,
        max_projection_l2_p90=6.0,
        min_primary_projection_share=0.80,
    )

    assert summary["projection_gate_pass"]
    assert summary["outcome_gate_admitted"]
