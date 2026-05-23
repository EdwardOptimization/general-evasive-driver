import pandas as pd
import pytest

from autodrift.tail_aligned_wrong_history_gate import (
    parse_tail_offsets,
    summarize_tail_outcomes,
    summarize_tail_proof_candidates,
    tail_requested_snapshot_steps,
)


def test_parse_tail_offsets_deduplicates_and_rejects_negative_values():
    assert parse_tail_offsets("4,8,8,12") == (4, 8, 12)
    with pytest.raises(ValueError, match="non-negative"):
        parse_tail_offsets("4,-1")


def test_tail_requested_snapshot_steps_collects_left_and_right_tail_offsets():
    rows = pd.DataFrame(
        [
            {
                "left_seed": 10,
                "left_step": 20,
                "right_seed": 11,
                "right_step": 30,
            }
        ]
    )

    requests = tail_requested_snapshot_steps(rows, tail_offsets=(4, 12))

    assert requests == {
        10: {24, 32},
        11: {34, 42},
    }


def test_summarize_tail_outcomes_counts_offset_specific_proof_rows():
    rows = [
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "tail_offset": 12,
            "variant": "wrong_tail_once",
            "variant_family": "wrong_tail_once",
            "normal_success": True,
            "variant_success": False,
            "success_drop": True,
            "collision_gap": True,
            "obstacle_completion_drop": False,
            "proof_margin_gap": False,
            "proof_candidate": True,
            "normal_margin": 0.1,
            "variant_margin": -0.1,
            "margin_gap": 0.2,
            "first_action_distance": 0.3,
            "action_trajectory_distance_mean": 0.4,
            "action_trajectory_distance_max": 0.5,
        },
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "tail_offset": 12,
            "variant": "wrong_tail_once",
            "variant_family": "wrong_tail_once",
            "normal_success": True,
            "variant_success": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "proof_margin_gap": True,
            "proof_candidate": True,
            "normal_margin": 0.4,
            "variant_margin": 0.3,
            "margin_gap": 0.1,
            "first_action_distance": 0.1,
            "action_trajectory_distance_mean": 0.2,
            "action_trajectory_distance_max": 0.3,
        },
    ]

    summary = summarize_tail_outcomes(rows)

    assert len(summary) == 1
    assert summary[0]["tail_offset"] == 12
    assert summary[0]["proof_candidate_count"] == 2
    assert summary[0]["success_drop_count"] == 1
    assert summary[0]["collision_gap_count"] == 1
    assert summary[0]["proof_margin_gap_count"] == 1


def test_summarize_tail_proof_candidates_reports_best_offset_and_source_diversity():
    rows = []
    for index, seed in enumerate([1, 2, 3]):
        rows.append(
            {
                "variant_family": "wrong_tail_once",
                "tail_offset": 12,
                "proof_candidate": True,
                "success_drop": index == 0,
                "collision_gap": index == 1,
                "obstacle_completion_drop": index == 2,
                "probe_seed": seed,
                "left_obstacle_label": "drift_required" if index < 2 else "unavoidable",
                "target": "future_yaw_response" if index < 2 else "future_braking_deceleration",
            }
        )
    rows.append(
        {
            "variant_family": "wrong_tail_once",
            "tail_offset": 4,
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "drift_required",
            "target": "future_yaw_response",
        }
    )

    summary = summarize_tail_proof_candidates(rows)

    assert summary["best_tail_offset"] == 12
    assert summary["best_tail_proof_candidate_count"] == 3
    assert summary["best_tail_success_or_collision_or_completion_rows"] == 3
    assert summary["best_tail_probe_seed_count"] == 3
    assert summary["best_tail_obstacle_label_count"] == 2
    assert summary["best_tail_target_count"] == 2
    assert summary["wrong_tail_once_total_proof_candidate_count"] == 4
