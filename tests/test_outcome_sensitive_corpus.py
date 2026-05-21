import argparse

import numpy as np
import pandas as pd

from autodrift.env import DriftEnvConfig, ObstacleTaskConfig
from autodrift.outcome_sensitive_corpus import (
    build_outcome_sensitive_row,
    obstacle_override_config,
    parse_float_list,
    select_outcome_sensitive_corpus,
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
            },
        ]
    )

    summary = summarize_outcomes(frame)
    selected = select_outcome_sensitive_corpus(frame, top_k=5)

    assert int(summary.loc[0, "candidates"]) == 2
    assert int(summary.loc[0, "accepted_outcome_sensitive_pairs"]) == 1
    assert int(summary.loc[0, "margin_gap_accept_pairs"]) == 1
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
