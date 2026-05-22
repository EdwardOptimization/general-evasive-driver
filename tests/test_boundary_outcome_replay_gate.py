import pandas as pd
import pytest

from autodrift.boundary_outcome_replay_gate import (
    compare_policy_replays,
    summarize_replay_rows,
    validate_corpus_frame,
)


def _row(
    *,
    policy: str,
    row_id: int,
    target: str = "future_braking_deceleration",
    normal_success: bool = True,
    wrong_success: bool = False,
    normal_margin: float = 0.02,
    wrong_margin: float = -0.01,
) -> dict[str, object]:
    return {
        "policy": policy,
        "checkpoint": f"{policy}.pt",
        "row_id": row_id,
        "target": target,
        "physical_pair_key": f"{row_id}:10:{row_id + 100}:20",
        "left_seed": row_id,
        "right_seed": row_id + 100,
        "left_step": 10,
        "right_step": 20,
        "relocated_obstacle_body_x": 8.0,
        "relocated_obstacle_body_y": -0.5,
        "relocated_obstacle_half_width": 0.8,
        "normal_success": normal_success,
        "wrong_history_success": wrong_success,
        "success_drop": normal_success and not wrong_success,
        "normal_margin": normal_margin,
        "wrong_history_margin": wrong_margin,
        "margin_gap": normal_margin - wrong_margin,
        "normal_first_action_distance": 0.0,
        "wrong_history_first_action_distance": 0.1,
        "normal_trajectory_distance_mean": 0.0,
        "wrong_history_trajectory_distance_mean": 0.2,
    }


def test_validate_corpus_frame_requires_fixed_boundary_columns():
    frame = pd.DataFrame(
        [
            {
                "row_id": 0,
                "target": "future_braking_deceleration",
                "physical_pair_key": "1:10:2:20",
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 10,
                "right_step": 20,
                "relocated_obstacle_body_x": 8.0,
                "relocated_obstacle_body_y": 0.0,
                "relocated_obstacle_half_width": 0.8,
            }
        ]
    )

    validate_corpus_frame(frame)

    with pytest.raises(ValueError, match="missing columns"):
        validate_corpus_frame(frame.drop(columns=["row_id"]))


def test_summarize_replay_rows_reports_policy_and_target_aggregate():
    rows = [
        _row(policy="base", row_id=0, target="brake"),
        _row(policy="base", row_id=1, target="yaw", wrong_success=True),
        _row(policy="candidate", row_id=0, target="brake"),
    ]

    summary = summarize_replay_rows(rows)
    aggregate = [row for row in summary if row["policy"] == "base" and row["target"] == "__all__"][0]

    assert aggregate["rows"] == 2
    assert aggregate["normal_success_rate"] == pytest.approx(1.0)
    assert aggregate["wrong_history_success_rate"] == pytest.approx(0.5)
    assert aggregate["success_drop_count"] == 1


def test_compare_policy_replays_accepts_retained_candidate():
    rows = [
        _row(policy="base", row_id=0, normal_margin=0.02, wrong_margin=-0.01),
        _row(policy="base", row_id=1, normal_margin=0.03, wrong_margin=0.00),
        _row(policy="candidate", row_id=0, normal_margin=0.021, wrong_margin=-0.012),
        _row(policy="candidate", row_id=1, normal_margin=0.031, wrong_margin=-0.002),
    ]

    comparison = compare_policy_replays(
        rows,
        baseline_policy="base",
        candidate_policy="candidate",
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.001,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
    )

    assert comparison["gate_pass"]
    assert comparison["normal_margin_mean_delta"] > 0.0
    assert comparison["margin_gap_mean_delta"] > 0.0


def test_compare_policy_replays_rejects_normal_margin_regression():
    rows = [
        _row(policy="base", row_id=0, normal_margin=0.02, wrong_margin=-0.01),
        _row(policy="base", row_id=1, normal_margin=0.03, wrong_margin=0.00),
        _row(policy="candidate", row_id=0, normal_margin=0.00, wrong_margin=-0.01),
        _row(policy="candidate", row_id=1, normal_margin=0.01, wrong_margin=0.00),
    ]

    comparison = compare_policy_replays(
        rows,
        baseline_policy="base",
        candidate_policy="candidate",
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.001,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
    )

    assert not comparison["gate_pass"]
    assert not comparison["normal_margin_retention_pass"]
