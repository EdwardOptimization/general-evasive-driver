import argparse
import math

import numpy as np
import pandas as pd

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.hidden_swap_gate import DecisionSnapshot
from autodrift.outcome_sensitive_corpus import (
    ProbeConfig,
    build_outcome_sensitive_row,
    obstacle_override_config,
    parse_float_list,
    probe_action,
    relocate_obstacle_snapshot,
    select_outcome_sensitive_corpus,
    should_probe,
    snapshot_relocation_grid,
    source_outcome_metrics,
    summarize_outcomes,
)


def test_parse_float_list_requires_positive_values():
    assert parse_float_list("8,10.5, 12") == [8.0, 10.5, 12.0]

    try:
        parse_float_list("8,0")
    except argparse.ArgumentTypeError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("zero target distance should be rejected")


def test_source_outcome_metrics_accepts_margin_gap():
    rows = [
        {
            "variant": "normal",
            "success": True,
            "min_clearance_margin": 0.08,
            "return": 3.0,
            "terminal_reason": "obstacle_completed",
        },
        {
            "variant": "hidden_swap",
            "success": True,
            "min_clearance_margin": 0.03,
            "return": 2.0,
            "terminal_reason": "obstacle_completed",
            "first_action_distance": 0.2,
            "action_trajectory_distance_mean": 0.1,
        },
    ]

    metrics = source_outcome_metrics(
        "nominal",
        rows,
        min_margin_gap=0.02,
        min_normal_margin=0.0,
        max_normal_margin=None,
        require_normal_success=True,
    )

    assert metrics["nominal_accepted_outcome_sensitive"]
    assert metrics["nominal_margin_gap_accept"]
    assert not metrics["nominal_success_drop"]
    assert np.isclose(metrics["nominal_margin_gap"], 0.05)
    assert metrics["nominal_wrong_history_first_action_distance"] == 0.2


def test_obstacle_override_config_updates_only_requested_ranges():
    config = DriftEnvConfig(
        obstacle=ObstacleTaskConfig(distance_range=(3.0, 25.0), half_width_range=(0.4, 1.0))
    )

    changed = obstacle_override_config(
        config,
        distance_range=(5.0, 12.0),
        half_width_range=(0.8, 1.2),
        perception_reveal_step=20,
        perception_reveal_distance=14.0,
    )

    assert changed.obstacle.distance_range == (5.0, 12.0)
    assert changed.obstacle.half_width_range == (0.8, 1.2)
    assert changed.obstacle.perception_reveal_step == 20
    assert changed.obstacle.perception_reveal_distance == 14.0
    assert config.obstacle.distance_range == (3.0, 25.0)


def test_snapshot_relocation_grid_requires_distances_when_enabled():
    assert snapshot_relocation_grid(None, None, None) == [(None, 0.0, None)]

    try:
        snapshot_relocation_grid(None, [0.0], [0.8])
    except ValueError as exc:
        assert "distances" in str(exc)
    else:
        raise AssertionError("relocation without distances should be rejected")

    grid = snapshot_relocation_grid([8.0, 10.0], [-0.5, 0.5], [0.7])
    assert grid == [(8.0, -0.5, 0.7), (8.0, 0.5, 0.7), (10.0, -0.5, 0.7), (10.0, 0.5, 0.7)]


def test_relocate_obstacle_snapshot_preserves_history_and_updates_current_obstacle():
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
    snapshot = DecisionSnapshot(
        condition="nominal",
        seed=123,
        step=int(info["step"]),
        observation=obs.copy(),
        hidden=None,
        env=env,
        info={**info, "active_probe_steps": 4},
        obstacle_distance=float(info["obstacle_distance"]),
        snapshot_score=0.0,
    )

    relocated = relocate_obstacle_snapshot(
        snapshot,
        body_longitudinal=9.0,
        body_lateral=-1.0,
        half_width=0.8,
    )

    relocated_body = relocated.env._body_point(relocated.env.obstacle_position)
    assert snapshot.env.obstacle_scenario.obstacle_half_width == 0.5
    assert np.allclose(relocated_body, [9.0, -1.0], atol=1e-5)
    assert relocated.info["active_probe_steps"] == 4
    assert relocated.info["snapshot_relocated"]
    assert relocated.info["relocated_obstacle_half_width"] == 0.8
    expected_margin = math.hypot(9.0, -1.0) - (config.obstacle.ego_half_width + 0.8)
    assert np.isclose(relocated.info["min_clearance_margin"], expected_margin)
    assert np.isclose(relocated.observation[44], 1.0)
    assert np.isclose(relocated.observation[45], 9.0 / 80.0)
    assert np.isclose(relocated.observation[46], -1.0 / 20.0)
    assert np.isclose(relocated.observation[49], 0.8 / 5.0)


def test_probe_action_is_bounded_and_uses_pedal_levels():
    config = ProbeConfig(
        strategy="steer_brake",
        steer_amplitude=0.2,
        brake_level=0.15,
        throttle_level=0.1,
        period_steps=20,
        until_step=None,
        until_distance=None,
    )

    action = probe_action("steer_brake", 5, config)

    assert action.shape == (3,)
    assert np.all(action >= -1.0)
    assert np.all(action <= 1.0)
    assert np.isclose(action[0], 0.2)
    assert np.isclose(action[1], -1.0)
    assert np.isclose(action[2], -0.7)


def test_should_probe_until_reveal_or_thresholds():
    config = ProbeConfig(
        strategy="steer_sine",
        steer_amplitude=0.1,
        brake_level=0.0,
        throttle_level=0.0,
        period_steps=20,
        until_step=10,
        until_distance=14.0,
    )

    assert should_probe({"step": 20, "obstacle_perception_visible": False}, config)
    assert should_probe({"step": 5, "obstacle_perception_visible": True, "obstacle_distance": 10.0}, config)
    assert should_probe({"step": 20, "obstacle_perception_visible": True, "obstacle_distance": 20.0}, config)
    assert not should_probe({"step": 20, "obstacle_perception_visible": True, "obstacle_distance": 10.0}, config)


def test_source_outcome_metrics_accepts_success_drop():
    rows = [
        {
            "variant": "normal",
            "success": True,
            "min_clearance_margin": 0.01,
            "return": 1.0,
            "terminal_reason": "obstacle_completed",
        },
        {
            "variant": "hidden_swap",
            "success": False,
            "min_clearance_margin": -0.10,
            "return": -5.0,
            "terminal_reason": "collision",
        },
    ]

    metrics = source_outcome_metrics(
        "perturbed",
        rows,
        min_margin_gap=0.20,
        min_normal_margin=0.0,
        max_normal_margin=0.05,
        require_normal_success=True,
    )

    assert metrics["perturbed_accepted_outcome_sensitive"]
    assert metrics["perturbed_success_drop"]
    assert metrics["perturbed_wrong_history_terminal_reason"] == "collision"


def test_summarize_and_select_outcome_sensitive_rows():
    frame = pd.DataFrame(
        [
            {
                "seed": 1,
                "pair_status": "paired",
                "accepted_visible_match": True,
                "accepted_outcome_sensitive": True,
                "accepted_nominal_outcome_sensitive": True,
                "accepted_perturbed_outcome_sensitive": False,
                "success_drop_count": 0,
                "nominal_margin_gap_accept": True,
                "perturbed_margin_gap_accept": False,
                "visible_observation_distance": 0.1,
                "max_margin_gap": 0.04,
                "outcome_score": 0.03,
                "nominal_active_probe_steps": 7,
                "perturbed_active_probe_steps": 8,
            },
            {
                "seed": 2,
                "pair_status": "paired",
                "accepted_visible_match": True,
                "accepted_outcome_sensitive": False,
                "accepted_nominal_outcome_sensitive": False,
                "accepted_perturbed_outcome_sensitive": False,
                "success_drop_count": 0,
                "nominal_margin_gap_accept": False,
                "perturbed_margin_gap_accept": False,
                "visible_observation_distance": 0.2,
                "max_margin_gap": 0.01,
                "outcome_score": 0.00,
                "nominal_active_probe_steps": 5,
                "perturbed_active_probe_steps": 6,
            },
        ]
    )

    summary = summarize_outcomes(frame)
    selected = select_outcome_sensitive_corpus(frame, top_k=5)

    assert int(summary.loc[0, "candidates"]) == 2
    assert int(summary.loc[0, "accepted_outcome_sensitive_pairs"]) == 1
    assert int(summary.loc[0, "margin_gap_accept_pairs"]) == 1
    assert summary.loc[0, "nominal_active_probe_steps_mean"] == 6.0
    assert summary.loc[0, "perturbed_active_probe_steps_mean"] == 7.0
    assert list(selected["seed"]) == [1]


def test_summarize_outcomes_treats_missing_boolean_values_as_false():
    frame = pd.DataFrame(
        [
            {
                "seed": 1,
                "pair_status": "missing_nominal",
                "accepted_visible_match": False,
                "accepted_outcome_sensitive": False,
                "accepted_nominal_outcome_sensitive": False,
                "accepted_perturbed_outcome_sensitive": False,
            },
            {
                "seed": 2,
                "pair_status": "paired",
                "accepted_visible_match": True,
                "accepted_outcome_sensitive": False,
                "accepted_nominal_outcome_sensitive": False,
                "accepted_perturbed_outcome_sensitive": False,
                "nominal_margin_gap_accept": np.nan,
                "perturbed_margin_gap_accept": np.nan,
                "success_drop_count": np.nan,
            },
        ]
    )

    summary = summarize_outcomes(frame)

    assert int(summary.loc[0, "margin_gap_accept_pairs"]) == 0
    assert int(summary.loc[0, "success_drop_pairs"]) == 0
    assert int(summary.loc[0, "paired_candidates"]) == 1


def test_build_outcome_sensitive_row_reports_missing_snapshots():
    row, replays = build_outcome_sensitive_row(
        9,
        10.0,
        None,
        None,
        model=None,
        nominal_config=None,
        perturbed_config=None,
        max_visible_distance=0.5,
        max_response_distance=0.2,
        max_context_distance=0.2,
        min_margin_gap=0.02,
        min_normal_margin=0.0,
        max_normal_margin=None,
        require_normal_success=True,
        max_continuation_steps=0,
    )

    assert row["pair_status"] == "missing_both"
    assert not row["accepted_outcome_sensitive"]
    assert replays == []
