import pandas as pd
import pytest

from autodrift.boundary_margin_split_replay_guard import (
    classify_margin_rows,
    evaluate_margin_split_replay,
)


def _row(
    *,
    policy: str,
    row_id: int,
    success_drop: bool,
    normal_margin: float,
    wrong_history_margin: float,
    normal_success: bool = True,
    wrong_success: bool = False,
) -> dict[str, object]:
    if not success_drop:
        wrong_success = normal_success
    return {
        "policy": policy,
        "checkpoint": f"{policy}.pt",
        "row_id": row_id,
        "target": "future_lateral_accel_response",
        "physical_pair_key": f"9530:{row_id}:9540:{row_id + 3}",
        "normal_success": normal_success,
        "wrong_history_success": wrong_success,
        "success_drop": success_drop,
        "normal_margin": normal_margin,
        "wrong_history_margin": wrong_history_margin,
        "margin_gap": normal_margin - wrong_history_margin,
    }


def test_classify_margin_rows_splits_robust_watchlist_and_knife_edge():
    frame = pd.DataFrame(
        [
            _row(policy="ref", row_id=1, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.002),
            _row(policy="ref", row_id=2, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.0008),
            _row(policy="ref", row_id=3, success_drop=True, normal_margin=0.0002, wrong_history_margin=-0.01),
            _row(policy="ref", row_id=4, success_drop=False, normal_margin=0.01, wrong_history_margin=0.01),
        ]
    )

    rows = classify_margin_rows(
        frame,
        class_reference_policy="ref",
        robust_threshold=0.001,
        knife_edge_threshold=0.0005,
    )

    assert [(row["row_id"], row["row_class"]) for row in rows] == [
        (1, "robust"),
        (2, "watchlist"),
        (3, "knife_edge"),
    ]


def test_margin_split_guard_rejects_lost_robust_rows():
    reference = pd.DataFrame(
        [
            _row(policy="ref", row_id=1, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.002),
            _row(policy="ref", row_id=2, success_drop=True, normal_margin=0.0002, wrong_history_margin=-0.01),
        ]
    )
    candidate = pd.DataFrame(
        [
            _row(policy="candidate", row_id=1, success_drop=False, normal_margin=0.01, wrong_history_margin=0.001),
            _row(policy="candidate", row_id=2, success_drop=True, normal_margin=0.0002, wrong_history_margin=-0.01),
        ]
    )

    summary, _, class_summary = evaluate_margin_split_replay(
        class_reference_frame=reference,
        candidate_frame=candidate,
        class_reference_policy="ref",
        candidate_policy="candidate",
        robust_threshold=0.001,
        knife_edge_threshold=0.0005,
    )

    assert not summary["gate_pass"]
    assert summary["lost_robust_rows"] == [1]
    assert summary["lost_knife_edge_rows"] == []
    assert [row for row in class_summary if row["row_class"] == "robust"][0]["lost_row_ids"] == [1]


def test_margin_split_guard_reports_knife_edge_loss_without_failing_robust_gate():
    reference = pd.DataFrame(
        [
            _row(policy="ref", row_id=1, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.002),
            _row(policy="ref", row_id=2, success_drop=True, normal_margin=0.0002, wrong_history_margin=-0.01),
        ]
    )
    candidate = pd.DataFrame(
        [
            _row(policy="candidate", row_id=1, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.002),
            _row(policy="candidate", row_id=2, success_drop=False, normal_margin=0.0002, wrong_history_margin=0.001),
        ]
    )

    summary, rows, _ = evaluate_margin_split_replay(
        class_reference_frame=reference,
        candidate_frame=candidate,
        class_reference_policy="ref",
        candidate_policy="candidate",
        robust_threshold=0.001,
        knife_edge_threshold=0.0005,
    )

    assert summary["gate_pass"]
    assert summary["lost_robust_rows"] == []
    assert summary["lost_knife_edge_rows"] == [2]
    assert [row for row in rows if row["row_id"] == 2][0]["status"] == "lost"


def test_margin_split_guard_requires_ordered_thresholds():
    frame = pd.DataFrame(
        [_row(policy="ref", row_id=1, success_drop=True, normal_margin=0.01, wrong_history_margin=-0.002)]
    )

    with pytest.raises(ValueError, match="robust_threshold"):
        classify_margin_rows(
            frame,
            class_reference_policy="ref",
            robust_threshold=0.0001,
            knife_edge_threshold=0.0005,
        )
