import pandas as pd

from autodrift.trajectory_terminal_boundary_source_miner import (
    assigned_split,
    classify_source_result,
    select_source_rows,
)


def test_select_source_rows_deduplicates_head_replays():
    rows = pd.DataFrame(
        [
            {
                "surface": "fresh",
                "target": "aes",
                "variant": "wrong_matched_history",
                "split": "source_holdout_validation",
                "physical_pair_key": "fresh:1:2",
                "source_index": 7,
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 10,
                "right_step": 11,
                "sequence_length": 5,
                "head_seed": 6890,
            },
            {
                "surface": "fresh",
                "target": "aes",
                "variant": "wrong_matched_history",
                "split": "source_holdout_validation",
                "physical_pair_key": "fresh:1:2",
                "source_index": 7,
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 10,
                "right_step": 11,
                "sequence_length": 5,
                "head_seed": 6891,
            },
        ]
    )

    selected = select_source_rows(rows, max_scenarios=10)

    assert len(selected) == 1
    assert selected.iloc[0]["source_row_id"] == 0
    assert selected.iloc[0]["left_seed"] == 1


def test_classify_source_result_requires_history_for_positive():
    result = classify_source_result(
        accepted_rows=80,
        trajectory_sensitive_rows=80,
        history_action_critical_rows=0,
        normal_success_candidates=80,
        normal_failed_rejected=0,
        unique_seeds=40,
        unique_sources=40,
        max_seed_dominance=0.05,
        max_source_dominance=0.05,
        min_accepted_rows=80,
        min_trajectory_rows=50,
        min_history_rows=20,
        min_unique_seeds=20,
        min_unique_sources=20,
        max_seed_dominance_threshold=0.10,
        max_source_dominance_threshold=0.25,
    )

    assert result == "history_insensitive"


def test_classify_source_result_accepts_diverse_history_sensitive_source():
    result = classify_source_result(
        accepted_rows=90,
        trajectory_sensitive_rows=70,
        history_action_critical_rows=25,
        normal_success_candidates=100,
        normal_failed_rejected=0,
        unique_seeds=40,
        unique_sources=40,
        max_seed_dominance=0.05,
        max_source_dominance=0.08,
        min_accepted_rows=80,
        min_trajectory_rows=50,
        min_history_rows=20,
        min_unique_seeds=20,
        min_unique_sources=20,
        max_seed_dominance_threshold=0.10,
        max_source_dominance_threshold=0.25,
    )

    assert result == "source_positive"


def test_assigned_split_is_deterministic():
    assert assigned_split(0, 0.2) == "heldout"
    assert assigned_split(1, 0.2) == "train"
