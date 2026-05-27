import pandas as pd
import pytest

from autodrift.family_aggregate_intersection_selector import (
    build_diversity_summary,
    build_policy_pass_matrix,
    run_family_aggregate_intersection_selector,
    select_intersection_rows,
)


def _family_row(row_id: int, source_label: str = "a", pair_index: int = 0) -> dict[str, object]:
    return {
        "family_row_id": row_id,
        "source_row_index": row_id + 100,
        "source_checkpoint_label": source_label,
        "source_checkpoint_path": f"{source_label}.pt",
        "source_checkpoint_family": "family",
        "checkpoint_label": source_label,
        "physical_pair_key": f"{1000 + pair_index}:10:{2000 + pair_index}:20",
        "boundary_geometry_key": f"geom:{pair_index}",
        "duplicate_geometry_group_id": f"g{pair_index:03d}",
        "duplicate_geometry_group_size": 1,
        "duplicate_geometry_source_labels": source_label,
        "target": "future_yaw_response" if pair_index % 2 else "future_braking_deceleration",
        "left_seed": 1000 + pair_index,
        "right_seed": 2000 + pair_index,
        "left_step": 10 + pair_index,
        "right_step": 20,
        "relocated_obstacle_body_x": 20.0,
        "relocated_obstacle_body_y": 0.2,
        "relocated_obstacle_half_width": 1.4,
        "normal_margin": 0.1,
        "margin_gap": 0.2,
        "normal_success": True,
        "success_drop": True,
    }


def _replay_row(
    row_id: int,
    policy: str,
    *,
    normal_success: bool = True,
    wrong_history_success: bool = False,
    margin_gap: float = 0.2,
) -> dict[str, object]:
    return {
        "policy": policy,
        "family_row_id": row_id,
        "normal_success": normal_success,
        "wrong_history_success": wrong_history_success,
        "success_drop": bool(normal_success and not wrong_history_success),
        "normal_margin": 0.1 if normal_success else -0.01,
        "wrong_history_margin": 0.01 if wrong_history_success else -0.1,
        "margin_gap": margin_gap,
    }


def test_policy_pass_matrix_keeps_only_all_policy_success_drop_rows():
    family = pd.DataFrame(
        [
            _family_row(0, "a", 0),
            _family_row(1, "b", 1),
        ]
    )
    replay_rows = []
    for policy in ("a", "b"):
        replay_rows.append(_replay_row(0, policy))
        replay_rows.append(_replay_row(1, policy, wrong_history_success=policy == "a"))
    replay = pd.DataFrame(replay_rows)

    kept, dropped, matrix = select_intersection_rows(
        family_frame=family,
        replay_frame=replay,
        expected_policies=("a", "b"),
    )

    assert kept["family_row_id"].tolist() == [0]
    assert dropped["family_row_id"].tolist() == [1]
    failed = matrix[matrix["family_row_id"] == 1].iloc[0]
    assert failed["failed_policy_labels"] == "a"
    assert "wrong_history_success" in failed["failure_reasons"]


def test_policy_pass_matrix_fails_closed_for_missing_policy_replay():
    family = pd.DataFrame([_family_row(0, "a", 0)])
    replay = pd.DataFrame([_replay_row(0, "a")])

    matrix = build_policy_pass_matrix(
        family_frame=family,
        replay_frame=replay,
        expected_policies=("a", "b"),
    )

    row = matrix.iloc[0]
    assert not row["all_policy_pass"]
    assert row["failed_policy_labels"] == "b"
    assert row["failure_reasons"] == "missing_policy_replay"


def test_diversity_summary_passes_expected_thresholds():
    rows = pd.DataFrame([_family_row(i, source_label=f"s{i % 4}", pair_index=i) for i in range(12)])

    summary = build_diversity_summary(
        rows,
        min_rows=10,
        min_physical_pairs=10,
        min_source_labels=4,
        min_targets=2,
        min_left_steps=10,
        max_physical_pair_fraction=0.20,
        max_source_label_fraction=0.40,
    )

    assert summary["gate_pass"]
    assert summary["rows"] == 12
    assert summary["physical_pairs"] == 12
    assert summary["source_labels"] == 4


def test_run_selector_writes_outputs(tmp_path):
    family = pd.DataFrame([_family_row(i, source_label=f"s{i % 4}", pair_index=i) for i in range(12)])
    replay_rows = []
    for row_id in range(12):
        for policy in ("s0", "s1", "s2", "s3"):
            replay_rows.append(_replay_row(row_id, policy))
    replay = pd.DataFrame(replay_rows)
    family_csv = tmp_path / "family.csv"
    replay_csv = tmp_path / "replay.csv"
    family.to_csv(family_csv, index=False)
    replay.to_csv(replay_csv, index=False)

    summary = run_family_aggregate_intersection_selector(
        family_rows_csv=family_csv,
        cross_family_replay_rows_csv=replay_csv,
        run_dir=tmp_path / "run",
        expected_policies=("s0", "s1", "s2", "s3"),
        min_rows=10,
        min_physical_pairs=10,
        min_source_labels=4,
        min_targets=2,
        min_left_steps=10,
        max_physical_pair_fraction=0.20,
        max_source_label_fraction=0.40,
    )

    assert summary["passed"]
    assert summary["kept_rows"] == 12
    assert summary["dropped_rows"] == 0
    assert (tmp_path / "run" / "family_intersection_rows.csv").exists()
    assert (tmp_path / "run" / "dropped_cross_family_rows.csv").exists()
    assert (tmp_path / "run" / "policy_pass_matrix.csv").exists()
    assert (tmp_path / "run" / "summary.json").exists()
    assert summary["replay_started"] is False
    assert summary["objective_optimization_started"] is False


def test_run_selector_rejects_sparse_output(tmp_path):
    family = pd.DataFrame([_family_row(0, source_label="a", pair_index=0)])
    replay = pd.DataFrame([_replay_row(0, "a")])
    family_csv = tmp_path / "family.csv"
    replay_csv = tmp_path / "replay.csv"
    family.to_csv(family_csv, index=False)
    replay.to_csv(replay_csv, index=False)

    summary = run_family_aggregate_intersection_selector(
        family_rows_csv=family_csv,
        cross_family_replay_rows_csv=replay_csv,
        run_dir=tmp_path / "run",
        expected_policies=("a",),
        min_rows=10,
    )

    assert not summary["passed"]
    assert summary["decision"] == "family_aggregate_intersection_selector_reject"


def test_validate_rejects_duplicate_policy_rows(tmp_path):
    family = pd.DataFrame([_family_row(0, source_label="a", pair_index=0)])
    replay = pd.DataFrame([_replay_row(0, "a"), _replay_row(0, "a")])

    with pytest.raises(ValueError, match="unique by family_row_id and policy"):
        build_policy_pass_matrix(
            family_frame=family,
            replay_frame=replay,
            expected_policies=("a",),
        )
