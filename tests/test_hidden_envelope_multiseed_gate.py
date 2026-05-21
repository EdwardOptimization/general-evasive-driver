import argparse

import numpy as np
import pytest

from autodrift.hidden_envelope_multiseed_gate import (
    aggregate_hidden_lift_rows,
    evaluate_aggregate_gates,
    parse_checkpoint_spec,
    parse_seed_list,
)


def test_parse_checkpoint_spec_requires_label_and_path():
    spec = parse_checkpoint_spec("m105=runs/checkpoint.pt")

    assert spec.label == "m105"
    assert str(spec.path) == "runs/checkpoint.pt"

    with pytest.raises(argparse.ArgumentTypeError):
        parse_checkpoint_spec("runs/checkpoint.pt")


def test_parse_seed_list_rejects_empty_values():
    assert parse_seed_list("9510,9511") == (9510, 9511)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_list("")


def test_aggregate_hidden_lift_rows_reports_min_mean_and_pass_fraction():
    rows = [
        {
            "checkpoint_label": "m105",
            "target": "future_yaw_response",
            "response_hidden_minus_reset_test_r2": 0.2,
        },
        {
            "checkpoint_label": "m105",
            "target": "future_yaw_response",
            "response_hidden_minus_reset_test_r2": -0.1,
        },
    ]

    aggregate = aggregate_hidden_lift_rows(rows, min_lift_threshold=0.0)

    assert len(aggregate) == 1
    assert np.isclose(aggregate[0]["lift_mean"], 0.05)
    assert np.isclose(aggregate[0]["lift_min"], -0.1)
    assert np.isclose(aggregate[0]["pass_fraction"], 0.5)


def test_evaluate_aggregate_gates_requires_mean_min_and_fraction():
    aggregate = [
        {
            "checkpoint_label": "m105",
            "target": "future_yaw_response",
            "probe_count": 2,
            "lift_mean": 0.05,
            "lift_min": -0.1,
            "lift_max": 0.2,
            "pass_count": 1,
            "pass_fraction": 0.5,
            "min_lift_threshold": 0.0,
        }
    ]

    gates = evaluate_aggregate_gates(
        aggregate,
        mean_lift_threshold=0.0,
        min_lift_threshold=0.0,
        pass_fraction_threshold=1.0,
    )

    assert gates[0]["mean_pass"] is True
    assert gates[0]["min_pass"] is False
    assert gates[0]["fraction_pass"] is False
    assert gates[0]["passed"] is False
