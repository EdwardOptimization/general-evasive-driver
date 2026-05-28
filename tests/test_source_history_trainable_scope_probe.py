from __future__ import annotations

import json

import numpy as np

from autodrift.source_history_trainable_scope_probe import run_trainable_scope_probe
from test_source_history_policy_gate import _history_frame, _write_checkpoint, _write_csv


def _frame(history_id, pair_id, condition, step, *, yaw_rate):
    row = _history_frame(history_id, condition, step, vx=14.0 - 0.1 * step, yaw_rate=yaw_rate)
    row["pair_id"] = str(pair_id)
    row["fault_name"] = f"fault_{pair_id}_{condition}"
    return row


def _history_intervention(history_intervention_id, intervention_id, pair_id, condition, correct_history_id):
    return {
        "history_intervention_id": str(history_intervention_id),
        "intervention_id": str(intervention_id),
        "pair_id": str(pair_id),
        "condition": condition,
        "probe_template": "left_brake_probe",
        "correct_history_id": str(correct_history_id),
        "preferred_candidate_id": "10",
        "rejected_candidate_id": "11",
        "margin_gap": "0.1",
    }


def _wrong_pair(history_intervention_id, correct_history_id, wrong_history_id):
    return {
        "history_intervention_id": str(history_intervention_id),
        "correct_history_id": str(correct_history_id),
        "wrong_history_id": str(wrong_history_id),
        "same_pair_swap": "True",
        "opposite_condition_swap": "True",
    }


def test_run_trainable_scope_probe_writes_split_and_parameter_artifacts(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    history_dir = tmp_path / "history"
    intervention_dir = tmp_path / "interventions"
    run_dir = tmp_path / "run"
    _write_checkpoint(checkpoint)
    history_dir.mkdir()
    intervention_dir.mkdir()

    (history_dir / "summary.json").write_text(json.dumps({"history_prefix_rows": 4}), encoding="utf-8")
    _write_csv(
        history_dir / "history_frame_rows.csv",
        [
            _frame(0, 0, "A", 0, yaw_rate=0.10),
            _frame(0, 0, "A", 1, yaw_rate=0.15),
            _frame(1, 0, "B", 0, yaw_rate=-0.10),
            _frame(1, 0, "B", 1, yaw_rate=-0.15),
            _frame(2, 1, "A", 0, yaw_rate=0.20),
            _frame(2, 1, "A", 1, yaw_rate=0.25),
            _frame(3, 1, "B", 0, yaw_rate=-0.20),
            _frame(3, 1, "B", 1, yaw_rate=-0.25),
        ],
    )
    _write_csv(
        history_dir / "history_intervention_rows.csv",
        [
            _history_intervention(0, 0, 0, "A", 0),
            _history_intervention(1, 0, 0, "B", 1),
            _history_intervention(2, 1, 1, "A", 2),
            _history_intervention(3, 1, 1, "B", 3),
        ],
    )
    _write_csv(
        history_dir / "wrong_history_pair_rows.csv",
        [
            _wrong_pair(0, 0, 1),
            _wrong_pair(1, 1, 0),
            _wrong_pair(2, 2, 3),
            _wrong_pair(3, 3, 2),
        ],
    )
    obs0 = np.zeros(72, dtype=np.float32)
    obs0[44] = 1.0
    obs1 = np.zeros(72, dtype=np.float32)
    obs1[44] = 1.0
    obs1[45] = 0.1
    _write_csv(
        intervention_dir / "intervention_observations.csv",
        [
            {"intervention_id": "0"} | {f"obs_{i}": float(value) for i, value in enumerate(obs0)},
            {"intervention_id": "1"} | {f"obs_{i}": float(value) for i, value in enumerate(obs1)},
        ],
    )
    action_rows = []
    for intervention_id in ("0", "1"):
        action_rows.extend(
            [
                {
                    "intervention_id": intervention_id,
                    "role": "preferred",
                    "candidate_id": "10",
                    "step": "0",
                    "steer": "0.5",
                    "throttle": "-1.0",
                    "brake": "1.0",
                },
                {
                    "intervention_id": intervention_id,
                    "role": "rejected",
                    "candidate_id": "11",
                    "step": "0",
                    "steer": "-0.5",
                    "throttle": "-1.0",
                    "brake": "1.0",
                },
            ]
        )
    _write_csv(intervention_dir / "intervention_action_sequences.csv", action_rows)
    split_plan = tmp_path / "split_plan.csv"
    group_weights = tmp_path / "group_weights.csv"
    _write_csv(
        split_plan,
        [
            {
                "pair_id": "0",
                "probe_template": "left_brake_probe",
                "assigned_eval_fold": "0",
            },
            {
                "pair_id": "1",
                "probe_template": "left_brake_probe",
                "assigned_eval_fold": "1",
            },
        ],
    )
    _write_csv(
        group_weights,
        [
            {
                "pair_id": "0",
                "probe_template": "left_brake_probe",
                "group_weight": "1.5",
                "pair_specific_weight_used": "False",
            },
            {
                "pair_id": "1",
                "probe_template": "left_brake_probe",
                "group_weight": "1.0",
                "pair_specific_weight_used": "False",
            },
        ],
    )

    summary = run_trainable_scope_probe(
        checkpoint_path=checkpoint,
        history_run_dir=history_dir,
        intervention_run_dir=intervention_dir,
        run_dir=run_dir,
        device="cpu",
        steps=2,
        lr=1e-3,
        scopes=("fusion_head",),
        split_offsets=(0, 1),
        split_plan_path=split_plan,
        group_weight_rows_path=group_weights,
    )

    assert summary["base_scope_count"] == 1
    assert summary["offset_count"] == 2
    assert summary["scope_count"] == 2
    assert summary["train_row_count"] > 0
    assert summary["eval_row_count"] > 0
    assert summary["pair_split_disjoint"] is True
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["split_plan_used"] is True
    assert summary["group_weights_used"] is True
    assert summary["weighted_loss_enabled"] is True
    assert summary["pair_specific_weight_used"] is False
    assert summary["max_group_weight"] == 1.5
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "scope_summaries.csv").exists()
    assert (run_dir / "repeat_summaries.csv").exists()
    assert (run_dir / "split_rows.csv").exists()
    assert (run_dir / "directional_rows.csv").exists()
    assert (run_dir / "group_rows.csv").exists()
    assert (run_dir / "parameter_group_delta.csv").exists()
    assert (run_dir / "train_trace.csv").exists()
    assert (run_dir / "weighted_group_diagnostics.csv").exists()
    assert (run_dir / "checkpoints" / "offset_0_fusion_head_candidate.pt").exists()
    assert (run_dir / "checkpoints" / "offset_1_fusion_head_candidate.pt").exists()
