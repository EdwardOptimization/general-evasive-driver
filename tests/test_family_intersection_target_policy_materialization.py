import pandas as pd
import pytest

from autodrift.boundary_outcome_corpus_objective import validate_boundary_row_frame
from autodrift.family_intersection_target_policy_materialization import (
    materialize_target_policy_rows,
    run_target_policy_materialization,
)


def _intersection_row(row_id: int, source_label: str = "source", pair_index: int = 0) -> dict[str, object]:
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
        "normal_margin": 0.01,
        "variant_margin": -0.01,
        "margin_gap": 0.02,
        "normal_success": True,
        "variant_success": False,
        "success_drop": True,
        "normal_first_steer": 0.1,
        "normal_first_throttle": -0.1,
        "normal_first_brake": 0.05,
        "variant_first_steer": 0.2,
        "variant_first_throttle": -0.2,
        "variant_first_brake": 0.1,
    }


def _target_replay_row(
    row_id: int,
    policy: str = "proof_current",
    *,
    normal_success: bool = True,
    wrong_history_success: bool = False,
) -> dict[str, object]:
    return {
        "policy": policy,
        "checkpoint": f"{policy}.pt",
        "family_row_id": row_id,
        "normal_success": normal_success,
        "wrong_history_success": wrong_history_success,
        "success_drop": bool(normal_success and not wrong_history_success),
        "normal_margin": 0.3,
        "wrong_history_margin": -0.2,
        "margin_gap": 0.5,
        "normal_first_steer": 0.31,
        "normal_first_throttle": -0.32,
        "normal_first_brake": 0.33,
        "wrong_history_first_steer": -0.41,
        "wrong_history_first_throttle": 0.42,
        "wrong_history_first_brake": -0.43,
    }


def test_materialize_uses_target_policy_replay_fields_and_preserves_source_fields():
    intersection = pd.DataFrame([_intersection_row(0, source_label="short61049")])
    replay = pd.DataFrame([_target_replay_row(0, policy="proof_current")])

    rows = materialize_target_policy_rows(
        intersection_frame=intersection,
        replay_frame=replay,
        target_policy_label="proof_current",
    )

    assert rows["checkpoint_label"].tolist() == ["proof_current"]
    assert rows["target_policy_label"].tolist() == ["proof_current"]
    assert rows["source_checkpoint_label"].tolist() == ["short61049"]
    assert rows["source_normal_margin"].tolist() == [0.01]
    assert rows["normal_margin"].tolist() == [0.3]
    assert rows["variant_margin"].tolist() == [-0.2]
    assert rows["normal_first_steer"].tolist() == [0.31]
    assert rows["variant_first_steer"].tolist() == [-0.41]
    validate_boundary_row_frame(rows)


def test_materialize_fails_when_target_replay_missing():
    intersection = pd.DataFrame([_intersection_row(0)])
    replay = pd.DataFrame([_target_replay_row(1)])

    with pytest.raises(ValueError, match="missing replay rows"):
        materialize_target_policy_rows(
            intersection_frame=intersection,
            replay_frame=replay,
            target_policy_label="proof_current",
        )


def test_materialize_fails_when_target_wrong_history_succeeds():
    intersection = pd.DataFrame([_intersection_row(0)])
    replay = pd.DataFrame([_target_replay_row(0, wrong_history_success=True)])

    with pytest.raises(ValueError, match="wrong history succeeded"):
        materialize_target_policy_rows(
            intersection_frame=intersection,
            replay_frame=replay,
            target_policy_label="proof_current",
        )


def test_run_materialization_writes_outputs(tmp_path):
    intersection = pd.DataFrame([_intersection_row(i, source_label=f"s{i % 4}", pair_index=i) for i in range(12)])
    replay = pd.DataFrame([_target_replay_row(i, policy="proof_current") for i in range(12)])
    intersection_csv = tmp_path / "intersection.csv"
    replay_csv = tmp_path / "replay.csv"
    intersection.to_csv(intersection_csv, index=False)
    replay.to_csv(replay_csv, index=False)

    summary = run_target_policy_materialization(
        family_intersection_rows_csv=intersection_csv,
        cross_family_replay_rows_csv=replay_csv,
        target_policy_label="proof_current",
        run_dir=tmp_path / "run",
        expected_rows=12,
        min_physical_pairs=10,
        min_source_labels=4,
        min_targets=2,
        min_left_steps=10,
        max_physical_pair_fraction=0.20,
        max_source_label_fraction=0.40,
    )

    assert summary["passed"]
    assert summary["rows"] == 12
    assert summary["normal_success_count"] == 12
    assert summary["wrong_history_success_count"] == 0
    assert summary["objective_npz_written"] is False
    assert (tmp_path / "run" / "proof_current_boundary_rows.csv").exists()
    assert (tmp_path / "run" / "proof_current_materialization_summary.json").exists()


def test_run_materialization_rejects_unexpected_row_count(tmp_path):
    intersection = pd.DataFrame([_intersection_row(0)])
    replay = pd.DataFrame([_target_replay_row(0)])
    intersection_csv = tmp_path / "intersection.csv"
    replay_csv = tmp_path / "replay.csv"
    intersection.to_csv(intersection_csv, index=False)
    replay.to_csv(replay_csv, index=False)

    summary = run_target_policy_materialization(
        family_intersection_rows_csv=intersection_csv,
        cross_family_replay_rows_csv=replay_csv,
        target_policy_label="proof_current",
        run_dir=tmp_path / "run",
        expected_rows=12,
    )

    assert not summary["passed"]
    assert summary["decision"] == "target_policy_materialization_reject"
