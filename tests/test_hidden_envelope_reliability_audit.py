import argparse

import numpy as np
import pytest

from autodrift.hidden_envelope_reliability_audit import (
    ReliabilityThresholds,
    aggregate_lift_rows,
    parse_sample_limits,
    summarize_target_shift,
    target_distribution_rows,
)


def test_parse_sample_limits_sorts_unique_positive_values():
    assert parse_sample_limits("800,400,800") == (400, 800)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_sample_limits("1")


def test_target_distribution_rows_records_quantiles():
    rows = target_distribution_rows(
        checkpoint_label="m105",
        sample_limit=4,
        probe_seed=9510,
        targets={"future_yaw_response": np.asarray([1.0, 2.0, 3.0, 4.0], dtype=np.float32)},
    )

    assert rows[0]["checkpoint_label"] == "m105"
    assert rows[0]["samples"] == 4
    assert np.isclose(rows[0]["mean"], 2.5)
    assert np.isclose(rows[0]["p50"], 2.5)


def test_summarize_target_shift_reports_mean_range_across_probe_seeds():
    rows = [
        {
            "checkpoint_label": "m105",
            "sample_limit": 800,
            "probe_seed": 9510,
            "target": "future_yaw_response",
            "mean": 1.0,
            "std": 0.1,
        },
        {
            "checkpoint_label": "m105",
            "sample_limit": 800,
            "probe_seed": 9511,
            "target": "future_yaw_response",
            "mean": 3.0,
            "std": 0.2,
        },
    ]

    summary = summarize_target_shift(rows)

    assert len(summary) == 1
    assert np.isclose(summary[0]["target_mean_mean"], 2.0)
    assert np.isclose(summary[0]["target_mean_range"], 2.0)


def test_aggregate_lift_rows_tracks_split_variance_and_gate_parts():
    rows = [
        {
            "checkpoint_label": "m105",
            "sample_limit": 800,
            "target": "future_yaw_response",
            "response_hidden_minus_reset_test_r2": 0.2,
        },
        {
            "checkpoint_label": "m105",
            "sample_limit": 800,
            "target": "future_yaw_response",
            "response_hidden_minus_reset_test_r2": -0.1,
        },
    ]

    summary = aggregate_lift_rows(
        rows,
        ReliabilityThresholds(
            mean_lift_threshold=0.0,
            min_lift_threshold=0.0,
            pass_fraction_threshold=1.0,
        ),
    )

    assert len(summary) == 1
    assert np.isclose(summary[0]["lift_mean"], 0.05)
    assert np.isclose(summary[0]["lift_min"], -0.1)
    assert np.isclose(summary[0]["pass_fraction"], 0.5)
    assert summary[0]["mean_pass"] is True
    assert summary[0]["min_pass"] is False
    assert summary[0]["passed"] is False
