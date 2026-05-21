import math

import numpy as np
import pandas as pd
import torch

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.wrong_history_boundary_relocation_surface import (
    candidate_half_widths,
    relocate_outcome_snapshot,
    select_wrong_history_candidates,
    summarize_boundary_relocation_rows,
)


def test_candidate_half_widths_targets_normal_margin_without_duplicates():
    widths = candidate_half_widths(
        base_half_width=0.6,
        original_normal_margin=0.18,
        target_normal_margins=(0.01, 0.05, 0.20),
        half_width_inflations=(0.0, 0.13),
        min_half_width=0.4,
        max_half_width=1.0,
    )

    assert widths == [0.6, 0.73, 0.77]


def test_candidate_half_widths_filters_invalid_range_and_sorts():
    widths = candidate_half_widths(
        base_half_width=0.6,
        original_normal_margin=1.5,
        target_normal_margins=(0.01, 0.10),
        half_width_inflations=(-0.3, 0.0, 0.2),
        min_half_width=0.5,
        max_half_width=1.0,
    )

    assert widths == [0.6, 0.8]


def test_relocate_outcome_snapshot_updates_obstacle_and_observation():
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
    snapshot = OutcomeSnapshot(
        seed=123,
        step=int(info["step"]),
        observation=obs.copy(),
        hidden=torch.zeros(1, 8),
        env=env,
        info=info,
    )

    relocated = relocate_outcome_snapshot(
        snapshot,
        body_longitudinal=9.0,
        body_lateral=-1.0,
        half_width=0.8,
    )

    body = relocated.env._body_point(relocated.env.obstacle_position)
    assert np.allclose(body, [9.0, -1.0], atol=1e-5)
    assert snapshot.env.obstacle_scenario.obstacle_half_width == 0.5
    assert relocated.env.obstacle_scenario.obstacle_half_width == 0.8
    expected_margin = math.hypot(9.0, -1.0) - (config.obstacle.ego_half_width + 0.8)
    assert np.isclose(relocated.info["min_clearance_margin"], expected_margin)
    assert np.isclose(relocated.observation[44], 1.0)
    assert np.isclose(relocated.observation[45], 9.0 / 80.0)
    assert np.isclose(relocated.observation[46], -1.0 / 20.0)
    assert np.isclose(relocated.observation[49], 0.8 / 5.0)


def test_select_wrong_history_candidates_limits_by_checkpoint_target():
    frame = pd.DataFrame(
        [
            {
                "variant": "wrong_matched_history",
                "checkpoint_label": "a",
                "target": "brake",
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 3,
                "right_step": 4,
                "normal_margin": 0.2,
                "margin_gap": 0.01,
                "first_action_distance": 0.1,
            },
            {
                "variant": "wrong_matched_history",
                "checkpoint_label": "a",
                "target": "brake",
                "left_seed": 5,
                "right_seed": 6,
                "left_step": 7,
                "right_step": 8,
                "normal_margin": 0.2,
                "margin_gap": 0.02,
                "first_action_distance": 0.05,
            },
            {
                "variant": "reset_hidden",
                "checkpoint_label": "a",
                "target": "brake",
                "left_seed": 9,
                "right_seed": 10,
                "left_step": 11,
                "right_step": 12,
                "normal_margin": 0.2,
                "margin_gap": 1.0,
                "first_action_distance": 1.0,
            },
        ]
    )

    selected = select_wrong_history_candidates(
        frame,
        max_pairs_per_checkpoint_target=1,
        min_base_action_distance=0.0,
        min_base_margin_gap=None,
    )

    assert len(selected) == 1
    assert selected.iloc[0]["left_seed"] == 5


def test_summary_reports_wrong_history_surface_separately():
    rows = [
        {
            "checkpoint_label": "m",
            "target": "yaw",
            "variant": "wrong_matched_history",
            "candidate_id": 0,
            "source_pair_id": 10,
            "accepted": True,
            "normal_near_boundary": True,
            "success_drop": True,
            "normal_success": True,
            "variant_success": False,
            "normal_margin": 0.01,
            "variant_margin": -0.02,
            "margin_gap": 0.03,
            "base_wrong_margin_gap": 0.001,
            "base_wrong_first_action_distance": 0.1,
        },
        {
            "checkpoint_label": "m",
            "target": "yaw",
            "variant": "reset_hidden",
            "candidate_id": 0,
            "source_pair_id": 10,
            "accepted": False,
            "normal_near_boundary": True,
            "success_drop": False,
            "normal_success": True,
            "variant_success": True,
            "normal_margin": 0.01,
            "variant_margin": 0.01,
            "margin_gap": 0.0,
            "base_wrong_margin_gap": 0.001,
            "base_wrong_first_action_distance": 0.1,
        },
    ]

    summary = summarize_boundary_relocation_rows(rows, min_accepted_wrong_rows=1)
    aggregate = summary[-1]

    assert aggregate["surface_found"]
    assert aggregate["accepted_wrong_history_rows"] == 1
    assert aggregate["accepted_reset_rows"] == 0
    assert aggregate["wrong_history_success_drop_count"] == 1
