import pandas as pd
import pytest

from autodrift.boundary_fragile_row_guard import compare_fragile_replay_rows, validate_replay_rows_frame


def _row(
    *,
    policy: str,
    row_id: int,
    success_drop: bool,
    normal_success: bool = True,
    wrong_success: bool = False,
    target: str = "future_lateral_accel_response",
) -> dict[str, object]:
    if not success_drop:
        wrong_success = normal_success
    return {
        "policy": policy,
        "checkpoint": f"{policy}.pt",
        "row_id": row_id,
        "target": target,
        "physical_pair_key": f"9530:{row_id}:9540:{row_id + 3}",
        "normal_success": normal_success,
        "wrong_history_success": wrong_success,
        "success_drop": success_drop,
        "normal_margin": 0.02,
        "wrong_history_margin": -0.01 if success_drop else 0.01,
        "margin_gap": 0.03 if success_drop else 0.01,
    }


def test_validate_replay_rows_frame_requires_boundary_replay_columns():
    frame = pd.DataFrame([_row(policy="base", row_id=67, success_drop=True)])

    validate_replay_rows_frame(frame)

    with pytest.raises(ValueError, match="missing columns"):
        validate_replay_rows_frame(frame.drop(columns=["success_drop"]))


def test_fragile_row_guard_rejects_lost_required_success_drop():
    frame = pd.DataFrame(
        [
            _row(policy="base", row_id=67, success_drop=True),
            _row(policy="candidate", row_id=67, success_drop=False),
        ]
    )

    summary, rows = compare_fragile_replay_rows(
        frame,
        baseline_policy="base",
        candidate_policy="candidate",
        required_row_ids=[67],
        max_lost_success_drop_rows=0,
    )

    assert not summary["gate_pass"]
    assert summary["lost_success_drop_rows"] == [67]
    assert summary["changed_success_drop_rows"] == [67]
    assert not summary["required_success_drop_retention_pass"]
    assert rows[0]["status"] == "lost_success_drop"


def test_fragile_row_guard_accepts_retained_required_success_drop():
    frame = pd.DataFrame(
        [
            _row(policy="base", row_id=67, success_drop=True),
            _row(policy="candidate", row_id=67, success_drop=True),
        ]
    )

    summary, rows = compare_fragile_replay_rows(
        frame,
        baseline_policy="base",
        candidate_policy="candidate",
        required_row_ids=[67],
        max_lost_success_drop_rows=0,
    )

    assert summary["gate_pass"]
    assert summary["lost_success_drop_rows"] == []
    assert summary["changed_success_drop_rows"] == []
    assert rows[0]["status"] == "retained_success_drop"


def test_fragile_row_guard_detects_row_swaps_even_when_count_matches():
    frame = pd.DataFrame(
        [
            _row(policy="base", row_id=67, success_drop=True),
            _row(policy="base", row_id=68, success_drop=False),
            _row(policy="candidate", row_id=67, success_drop=False),
            _row(policy="candidate", row_id=68, success_drop=True),
        ]
    )

    summary, _ = compare_fragile_replay_rows(
        frame,
        baseline_policy="base",
        candidate_policy="candidate",
        required_row_ids=[],
        max_lost_success_drop_rows=0,
    )

    assert summary["baseline_success_drop_count"] == 1
    assert summary["candidate_success_drop_count"] == 1
    assert not summary["gate_pass"]
    assert summary["lost_success_drop_rows"] == [67]
    assert summary["gained_success_drop_rows"] == [68]
