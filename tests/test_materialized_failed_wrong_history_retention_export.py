from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.artifacts import write_json
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.materialized_failed_wrong_history_retention_export import (
    build_combined_target_base_rejected_anchor,
    collect_failed_events,
    failed_events_from_replay_dir,
    save_anchor_arrays,
    validate_failed_event_registry,
)


BASE_CHECKPOINT = "runs/base/checkpoint.pt"
CANDIDATE_CHECKPOINT = "runs/candidate/checkpoint.pt"


def _policy_row(
    *,
    policy: str,
    checkpoint: str,
    row_id: int,
    normal_success: bool,
    wrong_history_success: bool,
    normal_margin: float,
    wrong_history_margin: float,
) -> dict[str, object]:
    return {
        "policy": policy,
        "checkpoint": checkpoint,
        "row_id": row_id,
        "target": "future_braking_deceleration",
        "physical_pair_key": "9530:9:9550:12",
        "left_seed": 9530,
        "right_seed": 9550,
        "left_step": 9,
        "right_step": 12,
        "relocated_obstacle_body_x": 13.0,
        "relocated_obstacle_body_y": -0.1,
        "relocated_obstacle_half_width": 0.72,
        "normal_success": normal_success,
        "wrong_history_success": wrong_history_success,
        "success_drop": bool(normal_success and not wrong_history_success),
        "normal_margin": normal_margin,
        "wrong_history_margin": wrong_history_margin,
        "margin_gap": normal_margin - wrong_history_margin,
    }


def _write_replay_gate(
    run_dir,
    *,
    baseline_policy: str = "m399_base",
    baseline_checkpoint: str = BASE_CHECKPOINT,
    row_id: int = 6,
) -> None:
    run_dir.mkdir(parents=True)
    write_json(
        run_dir / "summary.json",
        {
            "baseline_policy": baseline_policy,
            "candidate_policy": "candidate",
            "corpus_csv": "runs/corpus/boundary_outcome_corpus.csv",
        },
    )
    rows = [
        _policy_row(
            policy=baseline_policy,
            checkpoint=baseline_checkpoint,
            row_id=row_id,
            normal_success=True,
            wrong_history_success=False,
            normal_margin=0.01,
            wrong_history_margin=-0.003,
        ),
        _policy_row(
            policy="candidate",
            checkpoint=CANDIDATE_CHECKPOINT,
            row_id=row_id,
            normal_success=True,
            wrong_history_success=True,
            normal_margin=0.012,
            wrong_history_margin=0.001,
        ),
    ]
    pd.DataFrame(rows).to_csv(run_dir / "boundary_replay_rows.csv", index=False)


def test_failed_events_from_replay_dir_classifies_wrong_history_safe_target_base(tmp_path):
    replay_dir = tmp_path / "full_gates" / "m267_m264_replay"
    _write_replay_gate(replay_dir)

    events = failed_events_from_replay_dir(
        replay_dir=replay_dir,
        surface_label="m267_m264",
        surface_tier="old_public",
        base_checkpoint=tmp_path / "other.pt",
    )

    assert len(events) == 1
    event = events[0]
    assert event["target_class"] == "target_base"
    assert event["normal_lost"] is False
    assert event["wrong_history_safe"] is True
    assert event["base_wrong_history_margin"] == pytest.approx(-0.003)
    assert event["candidate_wrong_history_margin"] == pytest.approx(0.001)


def test_collect_failed_events_splits_short_family_rows(tmp_path):
    _write_replay_gate(tmp_path / "full_gates" / "m183_m168_replay", row_id=10)
    _write_replay_gate(
        tmp_path / "family_intersection_public_gate" / "replay_gates" / "short61049_to_candidate",
        baseline_policy="short61049",
        baseline_checkpoint="runs/short61049/checkpoint.pt",
        row_id=12,
    )
    _write_replay_gate(
        tmp_path / "source_diverse_protected_diagnostic" / "replay_gates" / "current_m333_surface",
        row_id=15,
    )

    events = collect_failed_events(full_gate_run_dir=tmp_path, base_checkpoint=tmp_path / "base.pt")

    assert [event["surface_tier"] for event in events] == ["old_public", "family_intersection", "source_diverse"]
    assert [event["target_class"] for event in events] == ["target_base", "family_source", "target_base"]
    assert [event["event_index"] for event in events] == [0, 1, 2]
    counts = validate_failed_event_registry(events, expected_event_count=3)
    assert counts["failed_event_count"] == 3
    assert counts["normal_lost_events"] == 0
    assert counts["wrong_history_safe_events"] == 3


def test_validate_failed_event_registry_fails_closed_on_normal_lost():
    events = [
        {
            "normal_lost": True,
            "wrong_history_safe": False,
        }
    ]

    with pytest.raises(ValueError, match="normal_lost"):
        validate_failed_event_registry(events, expected_event_count=1)


def _anchor(rows: int, *, source_index, weight) -> dict[str, np.ndarray]:
    return {
        "observation": np.zeros((rows, 72), dtype=np.float32),
        "hidden": np.zeros((rows, 128), dtype=np.float32),
        "reference_action": np.zeros((rows, 3), dtype=np.float32),
        "source_index": np.asarray(source_index, dtype=np.int64),
        "step_index": np.arange(rows, dtype=np.int64),
        "weight": np.asarray(weight, dtype=np.float32),
    }


def test_build_combined_target_base_rejected_anchor_namespaces_and_normalizes(tmp_path):
    base = _anchor(2, source_index=[0, 1], weight=[0.25, 0.75])
    base["family_id"] = np.asarray([0, 1], dtype=np.int64)
    base["family_weight_total"] = np.asarray([1.0, 4.0], dtype=np.float32)
    target = _anchor(3, source_index=[0, 0, 1], weight=[50.0, 50.0, 50.0])
    base_npz = tmp_path / "base.npz"
    target_npz = tmp_path / "target.npz"
    combined_npz = tmp_path / "combined.npz"
    save_anchor_arrays(base_npz, base)
    save_anchor_arrays(target_npz, target)

    summary = build_combined_target_base_rejected_anchor(
        base_combined_anchor_npz=base_npz,
        target_anchor_npz=target_npz,
        output_npz=combined_npz,
        target_source_index_offset=2_000_000,
        target_family_id=2,
        target_family_total=4.0,
    )

    assert summary["combined_rows"] == 5
    assert summary["source_collision"] is False
    assert summary["target_family_weight_match"] is True
    anchor = load_trajectory_action_anchor(
        combined_npz,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )
    assert anchor.size == 5
    data = np.load(combined_npz)
    assert data["source_index"].tolist() == [0, 1, 2_000_000, 2_000_000, 2_000_001]
    assert data["family_id"].tolist() == [0, 1, 2, 2, 2]
    assert data["family_weight_total"].tolist() == pytest.approx([1.0, 4.0, 4.0, 4.0, 4.0])
    assert float(data["weight"][2:].sum()) == pytest.approx(4.0)
