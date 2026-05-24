import argparse

import numpy as np
import pandas as pd

from autodrift.action_divergent_wrong_history_corpus import (
    action_sequence_distance,
    action_sequence_prefix,
    load_surface_pairs,
    parse_surface_path,
    preferred_key_for_pair,
    preferred_sequence_keys,
    rejection_reason_for_candidate,
    write_action_divergent_corpus,
)


def test_parse_surface_path():
    surface, path = parse_surface_path("fresh=/tmp/pairs.csv")

    assert surface == "fresh"
    assert str(path) == "/tmp/pairs.csv"
    try:
        parse_surface_path("bad")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("invalid surface mapping was accepted")


def test_action_sequence_prefix_pads_last_action():
    actions = [np.array([1.0, 0.0, 0.0], dtype=np.float32)]

    sequence = action_sequence_prefix(actions, 3)

    assert sequence.shape == (3, 3)
    assert np.allclose(sequence[2], [1.0, 0.0, 0.0])


def test_action_sequence_distance_reports_first_mean_max():
    left = np.zeros((2, 3), dtype=np.float32)
    right = np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 12.0]], dtype=np.float32)

    distance = action_sequence_distance(left, right)

    assert distance["first_l2"] == 5.0
    assert distance["mean_l2"] == 8.5
    assert distance["max_l2"] == 12.0


def test_rejection_reason_for_candidate_is_structured():
    reason = rejection_reason_for_candidate(
        first_l2=0.001,
        sequence_mean_l2=0.002,
        preferred_rejected_mean_l2=0.003,
        margin_gap=0.004,
        normal_margin=1.0,
        wrong_margin=0.999,
        min_wrong_first_action_l2=0.002,
        min_wrong_action_sequence_mean_l2=0.006,
        min_preferred_rejected_action_mean_l2=0.010,
        min_margin_gap=0.010,
    )

    assert "wrong_first_action_l2_below_threshold" in reason
    assert "wrong_action_sequence_mean_l2_below_threshold" in reason
    assert "preferred_rejected_action_mean_l2_below_threshold" in reason
    assert "margin_gap_below_threshold" in reason


def test_load_surface_pairs_adds_surface_and_source_index(tmp_path):
    path = tmp_path / "pairs.csv"
    pd.DataFrame(
        {
            "target": ["future_yaw_response"],
            "left_seed": [1],
            "right_seed": [2],
            "left_step": [3],
            "right_step": [4],
        }
    ).to_csv(path, index=False)

    pairs = load_surface_pairs({"fresh": path})

    assert pairs.loc[0, "surface"] == "fresh"
    assert pairs.loc[0, "config"] == "fresh"
    assert pairs.loc[0, "source_index"] == 0
    assert pairs.loc[0, "physical_pair_key"] == "fresh:1:2"


def test_preferred_sequence_keys_and_pair_key(tmp_path):
    path = tmp_path / "accepted_sequences.csv"
    pd.DataFrame(
        {
            "surface": ["ood"],
            "target": ["future_lateral_accel_response"],
            "left_seed": [10],
            "right_seed": [11],
            "left_step": [12],
            "right_step": [13],
        }
    ).to_csv(path, index=False)

    keys = preferred_sequence_keys(path)
    pair = pd.Series(
        {
            "surface": "ood",
            "target": "future_lateral_accel_response",
            "left_seed": 10,
            "right_seed": 11,
            "left_step": 12,
            "right_step": 13,
        }
    )

    assert preferred_key_for_pair(pair) in keys


def test_write_empty_action_divergent_corpus(tmp_path):
    output = tmp_path / "corpus.npz"

    write_action_divergent_corpus(
        output_npz=output,
        rows=[],
        corpus={
            "observation": [],
            "normal_hidden": [],
            "variant_hidden": [],
            "preferred_action_sequence": [],
            "rejected_action_sequence": [],
            "normal_base_action_sequence": [],
            "variant_base_action_sequence": [],
        },
        obs_dim=72,
        hidden_dim=64,
        max_sequence_length=9,
    )

    data = np.load(output)
    assert data["observation"].shape == (0, 72)
    assert data["preferred_action_sequence"].shape == (0, 9, 3)
    assert data["rejected_action_sequence"].shape == (0, 9, 3)
