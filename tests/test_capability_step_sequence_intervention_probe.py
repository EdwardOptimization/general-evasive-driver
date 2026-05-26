import argparse

import numpy as np
import pandas as pd
import pytest

from autodrift.capability_step_sequence_intervention_probe import (
    _result_class,
    mismatch_observation,
    parse_int_list,
    select_source_rows,
)


def test_parse_int_list_rejects_empty_and_nonpositive():
    assert parse_int_list("4,8,12") == (4, 8, 12)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_int_list("")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_int_list("4,0")


def test_select_source_rows_caps_fault_pairs_by_ranked_reset_gap():
    rows = pd.DataFrame(
        [
            {"pairing_rule": "a->b", "reset_margin_gap": 0.1, "reset_action_l2_gap": 0.3},
            {"pairing_rule": "a->b", "reset_margin_gap": 0.4, "reset_action_l2_gap": 0.1},
            {"pairing_rule": "a->b", "reset_margin_gap": 0.2, "reset_action_l2_gap": 0.2},
            {"pairing_rule": "c->d", "reset_margin_gap": 0.3, "reset_action_l2_gap": 0.4},
        ]
    )

    selected = select_source_rows(rows, max_source_rows=3, per_fault_pair_cap=2)

    assert len(selected) == 3
    assert selected[selected["pairing_rule"] == "a->b"]["reset_margin_gap"].tolist() == [0.4, 0.2]
    assert selected[selected["pairing_rule"] == "c->d"]["reset_margin_gap"].tolist() == [0.3]


def test_mismatch_observation_replaces_only_requested_channels():
    preferred = np.arange(72, dtype=np.float32)
    wrong = 100.0 + np.arange(72, dtype=np.float32)

    commands = mismatch_observation(preferred, wrong, "wrong_commands_preferred_response")
    assert np.all(commands[:9] == preferred[:9])
    assert np.all(commands[9:12] == wrong[9:12])
    assert np.all(commands[12:] == preferred[12:])

    response = mismatch_observation(preferred, wrong, "wrong_response_preferred_commands")
    assert np.all(response[:9] == wrong[:9])
    assert np.all(response[9:] == preferred[9:])


def test_result_class_separates_temporal_from_cross_fault_positive():
    result = _result_class(
        accepted_rows=20,
        accepted_cross_fault_rows=0,
        accepted_temporal_rows=20,
        action_critical_rows=30,
        normal_failed_rows=0,
        total_rows=60,
        unique_cross_fault_pairs=0,
        unique_cross_fault_seeds=0,
        unique_temporal_fault_pairs=4,
        unique_temporal_seeds=8,
    )

    assert result == "sequence_temporal_history_positive"

    result = _result_class(
        accepted_rows=20,
        accepted_cross_fault_rows=20,
        accepted_temporal_rows=0,
        action_critical_rows=30,
        normal_failed_rows=0,
        total_rows=60,
        unique_cross_fault_pairs=4,
        unique_cross_fault_seeds=8,
        unique_temporal_fault_pairs=0,
        unique_temporal_seeds=0,
    )

    assert result == "sequence_cross_fault_positive"
