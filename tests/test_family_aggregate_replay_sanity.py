from pathlib import Path

import pandas as pd
import pytest

import autodrift.family_aggregate_replay_sanity as replay_sanity
from autodrift.family_aggregate_replay_sanity import (
    build_aggregate_source_gate,
    build_source_policy_gate_summary,
    family_rows_to_replay_frame,
    run_family_aggregate_replay_sanity,
)
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec


def _family_row(
    *,
    family_row_id: int,
    source_label: str,
    pair_index: int,
    target: str = "future_yaw_response",
) -> dict[str, object]:
    return {
        "family_row_id": family_row_id,
        "source_row_index": family_row_id + 100,
        "source_checkpoint_label": source_label,
        "source_checkpoint_path": f"{source_label}.pt",
        "source_checkpoint_family": "family",
        "physical_pair_key": f"{1000 + pair_index}:10:{2000 + pair_index}:20",
        "boundary_geometry_key": f"geom:{pair_index}:{target}",
        "duplicate_geometry_group_id": f"g{pair_index:03d}",
        "duplicate_geometry_group_size": 1,
        "duplicate_geometry_source_labels": source_label,
        "target": target,
        "left_seed": 1000 + pair_index,
        "right_seed": 2000 + pair_index,
        "left_step": 10,
        "right_step": 20,
        "relocated_obstacle_body_x": 25.0 + pair_index,
        "relocated_obstacle_body_y": 0.1 * pair_index,
        "relocated_obstacle_half_width": 1.5,
    }


def _fake_replay_rows(*, checkpoint_spec, corpus_frame, env_config_path, max_continuation_steps, device):
    rows = []
    for _, row in corpus_frame.iterrows():
        rows.append(
            {
                "policy": checkpoint_spec.label,
                "checkpoint": str(checkpoint_spec.path),
                "row_id": int(row["row_id"]),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "normal_success": True,
                "wrong_history_success": False,
                "success_drop": True,
                "normal_margin": 0.1,
                "wrong_history_margin": -0.1,
                "margin_gap": 0.2,
                "normal_first_steer": 0.1,
                "wrong_history_first_action_distance": 0.2,
                "wrong_history_trajectory_distance_mean": 0.3,
            }
        )
    return rows


def test_family_rows_to_replay_frame_maps_family_row_id_to_row_id():
    family = pd.DataFrame([_family_row(family_row_id=7, source_label="a", pair_index=1)])

    replay = family_rows_to_replay_frame(family)

    assert replay["row_id"].tolist() == [7]
    assert "family_row_id" not in replay.columns
    assert replay["target"].tolist() == ["future_yaw_response"]


def test_source_policy_gate_summary_passes_when_source_policy_rows_all_drop():
    family_rows = []
    replay_rows = []
    labels = ("a", "b", "c")
    for row_id in range(12):
        label = labels[row_id % len(labels)]
        family_rows.append(
            _family_row(
                family_row_id=row_id,
                source_label=label,
                pair_index=row_id,
                target="future_yaw_response" if row_id % 2 else "future_braking_deceleration",
            )
        )
    family = pd.DataFrame(family_rows)
    for label in labels:
        source_family = family[family["source_checkpoint_label"] == label]
        for replay_row in _fake_replay_rows(
            checkpoint_spec=CheckpointSpec(label=label, path=Path(f"{label}.pt")),
            corpus_frame=family_rows_to_replay_frame(source_family),
            env_config_path=Path("env.json"),
            max_continuation_steps=1,
            device="cpu",
        ):
            replay_rows.append(
                {
                    **replay_row,
                    "family_row_id": int(replay_row["row_id"]),
                    "source_checkpoint_label": label,
                }
            )
    replay = pd.DataFrame(replay_rows)

    rows = build_source_policy_gate_summary(replay_frame=replay, family_frame=family, source_labels=labels)
    aggregate = build_aggregate_source_gate(replay, rows)

    assert all(row["gate_pass"] for row in rows)
    assert aggregate["gate_pass"]


def test_source_policy_gate_summary_fails_on_wrong_history_success():
    family = pd.DataFrame([_family_row(family_row_id=0, source_label="a", pair_index=0)])
    replay = pd.DataFrame(
        [
            {
                **_fake_replay_rows(
                    checkpoint_spec=CheckpointSpec(label="a", path=Path("a.pt")),
                    corpus_frame=family_rows_to_replay_frame(family),
                    env_config_path=Path("env.json"),
                    max_continuation_steps=1,
                    device="cpu",
                )[0],
                "family_row_id": 0,
                "source_checkpoint_label": "a",
                "wrong_history_success": True,
                "success_drop": False,
            }
        ]
    )

    rows = build_source_policy_gate_summary(replay_frame=replay, family_frame=family, source_labels=("a",))

    assert not rows[0]["gate_pass"]
    assert rows[0]["wrong_history_success_count"] == 1


def test_run_family_aggregate_replay_sanity_writes_outputs(monkeypatch, tmp_path):
    family = pd.DataFrame(
        [
            _family_row(family_row_id=0, source_label="a", pair_index=0, target="future_yaw_response"),
            _family_row(family_row_id=1, source_label="b", pair_index=1, target="future_braking_deceleration"),
        ]
    )
    family_csv = tmp_path / "family_rows.csv"
    family.to_csv(family_csv, index=False)
    monkeypatch.setattr(replay_sanity, "replay_boundary_rows_for_policy", _fake_replay_rows)

    summary = run_family_aggregate_replay_sanity(
        family_rows_csv=family_csv,
        checkpoint_specs=(
            CheckpointSpec(label="a", path=Path("a.pt")),
            CheckpointSpec(label="b", path=Path("b.pt")),
        ),
        env_config_path=Path("env.json"),
        run_dir=tmp_path / "run",
        max_continuation_steps=1,
        device="cpu",
    )

    assert summary["source_policy_replay_rows"] == 2
    assert summary["cross_family_summary_rows"] == 4
    assert (tmp_path / "run" / "source_policy_source_rows_replay.csv").exists()
    assert (tmp_path / "run" / "source_policy_gate_summary.csv").exists()
    assert (tmp_path / "run" / "cross_family_replay_rows.csv").exists()
    assert (tmp_path / "run" / "duplicate_geometry_replay_summary.csv").exists()
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["objective_optimization_started"] is False


def test_run_family_aggregate_replay_sanity_fails_closed_for_missing_source_policy(tmp_path):
    family = pd.DataFrame([_family_row(family_row_id=0, source_label="missing", pair_index=0)])
    family_csv = tmp_path / "family_rows.csv"
    family.to_csv(family_csv, index=False)

    with pytest.raises(ValueError, match="missing source labels"):
        run_family_aggregate_replay_sanity(
            family_rows_csv=family_csv,
            checkpoint_specs=(CheckpointSpec(label="a", path=Path("a.pt")),),
            env_config_path=Path("env.json"),
            run_dir=tmp_path / "run",
        )
