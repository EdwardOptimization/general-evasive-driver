import pandas as pd

from autodrift.projection_aware_boundary_outcome_gate import (
    classify_projection_outcome,
    projection_tail_requested_snapshot_steps,
    summarize_projection_outcomes,
)


def test_projection_tail_requested_snapshot_steps_collects_offsets() -> None:
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

    requests = projection_tail_requested_snapshot_steps(rows, tail_offsets=(0, 2, 8))

    assert requests == {
        10: {20, 22, 28},
        11: {30, 32, 38},
    }


def test_summarize_projection_outcomes_counts_wrong_projected_rows() -> None:
    rows = [
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "tail_offset": 0,
            "variant": "wrong_projected_once",
            "variant_family": "wrong_projected_once",
            "normal_success": True,
            "variant_success": False,
            "success_drop": True,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "proof_margin_gap": False,
            "proof_candidate": True,
            "normal_margin": 0.2,
            "variant_margin": -0.1,
            "margin_gap": 0.3,
            "first_action_distance": 0.12,
            "action_trajectory_distance_mean": 0.15,
            "action_trajectory_distance_max": 0.2,
        },
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "tail_offset": 0,
            "variant": "wrong_projected_once",
            "variant_family": "wrong_projected_once",
            "normal_success": True,
            "variant_success": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "proof_margin_gap": True,
            "proof_candidate": True,
            "normal_margin": 0.3,
            "variant_margin": 0.1,
            "margin_gap": 0.2,
            "first_action_distance": 0.08,
            "action_trajectory_distance_mean": 0.10,
            "action_trajectory_distance_max": 0.15,
        },
    ]

    summary = summarize_projection_outcomes(rows)

    assert len(summary) == 1
    assert summary[0]["variant"] == "wrong_projected_once"
    assert summary[0]["proof_candidate_count"] == 2
    assert summary[0]["event_row_count"] == 1
    assert summary[0]["success_drop_count"] == 1


def test_classify_projection_outcome_detects_positive_wrong_history_event() -> None:
    rows = [
        {
            "variant": "wrong_projected_once",
            "variant_family": "wrong_projected_once",
            "proof_candidate": True,
            "success_drop": True,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "config": "short",
            "target": "future_yaw_response",
            "projected_obstacle_bucket": "a",
            "projection_bucket": "p",
            "first_action_distance": 0.1,
            "action_trajectory_distance_mean": 0.1,
        }
    ]

    summary = classify_projection_outcome(rows, invalid_count=0, input_pair_count=1)

    assert summary["classification"] == "positive_projected_wrong_history_outcome_proof"
    assert summary["wrong_projected_once_total_event_rows"] == 1


def test_classify_projection_outcome_reports_fast_correction_no_effect() -> None:
    rows = [
        {
            "variant": "wrong_projected_once",
            "variant_family": "wrong_projected_once",
            "proof_candidate": False,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "config": "short",
            "target": "future_yaw_response",
            "projected_obstacle_bucket": "a",
            "projection_bucket": "p",
            "first_action_distance": 0.05,
            "action_trajectory_distance_mean": 0.05,
        }
    ]

    summary = classify_projection_outcome(rows, invalid_count=0, input_pair_count=1)

    assert summary["classification"] == "fast_correction_no_effect"
    assert summary["wrong_projected_once_total_proof_candidate_count"] == 0
