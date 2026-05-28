from __future__ import annotations

import csv
import json

import numpy as np
import torch

from autodrift.source_history_policy_gate import project_history_frame, run_source_history_policy_gate
from autodrift.train_ppo import ActorCritic


def _write_csv(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_checkpoint(path):
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        actor_history_length=1,
        action_sequence_horizon=1,
        response_prediction_dim=0,
        log_std_init=-0.5,
        log_std_min=-2.0,
        log_std_max=1.0,
    )
    checkpoint = {
        "model_state": model.state_dict(),
        "config": {
            "actor_encoder": "human_view_online_gru",
            "actor_history_length": 1,
            "action_sequence_horizon": 1,
            "response_prediction_dim": 0,
            "response_prediction_horizon": 1,
            "log_std_init": -0.5,
            "log_std_min": -2.0,
            "log_std_max": 1.0,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, path)


def _history_frame(history_id, condition, step, *, vx=14.0, yaw_rate=0.1, brake=6000.0):
    return {
        "history_id": str(history_id),
        "pair_id": "0",
        "condition": condition,
        "fault_name": f"fault_{condition}",
        "fault_family": "test_family",
        "probe_template": "left_brake_probe",
        "step": str(step),
        "cmd_steer": "0.25",
        "cmd_throttle": "-1.0",
        "cmd_brake": "1.0",
        "vx": str(vx),
        "vy": "0.2",
        "yaw_rate": str(yaw_rate),
        "ax": "-4.0",
        "ay": "2.0",
        "steer_state": "0.31",
        "steer_rate": "1.75",
        "drive_state": "8200.0",
        "brake_state": str(brake),
        "prev_cmd_steer": "0.25",
        "prev_cmd_throttle": "-1.0",
        "prev_cmd_brake": "1.0",
    }


def test_project_history_frame_uses_canonical_actor_mapping():
    frame = project_history_frame(_history_frame(0, "A", 0))

    assert frame.shape == (72,)
    assert np.isclose(frame[0], 14.0 / 20.0)
    assert np.isclose(frame[2], 0.1 / 2.5)
    assert np.isclose(frame[5], 0.31 / 0.62)
    assert np.isclose(frame[6], 1.75 / 3.5)
    assert frame[7] == 1.0
    assert frame[8] == 1.0
    assert frame[9] == 0.25
    assert frame[10] == 0.0
    assert frame[11] == 1.0
    assert np.all(frame[12:] == 0.0)


def test_run_source_history_policy_gate_writes_finite_artifacts(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    history_dir = tmp_path / "history"
    intervention_dir = tmp_path / "interventions"
    run_dir = tmp_path / "run"
    _write_checkpoint(checkpoint)
    history_dir.mkdir()
    intervention_dir.mkdir()

    (history_dir / "summary.json").write_text(
        json.dumps({"history_prefix_rows": 2}),
        encoding="utf-8",
    )
    _write_csv(
        history_dir / "history_frame_rows.csv",
        [
            _history_frame(0, "A", 0, vx=14.0, yaw_rate=0.10),
            _history_frame(0, "A", 1, vx=13.9, yaw_rate=0.15),
            _history_frame(1, "B", 0, vx=14.0, yaw_rate=-0.10),
            _history_frame(1, "B", 1, vx=13.8, yaw_rate=-0.15),
        ],
    )
    _write_csv(
        history_dir / "history_intervention_rows.csv",
        [
            {
                "history_intervention_id": "0",
                "intervention_id": "0",
                "pair_id": "0",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "0",
                "preferred_candidate_id": "10",
                "rejected_candidate_id": "11",
                "margin_gap": "0.1",
            },
            {
                "history_intervention_id": "1",
                "intervention_id": "1",
                "pair_id": "0",
                "condition": "B",
                "probe_template": "left_brake_probe",
                "correct_history_id": "1",
                "preferred_candidate_id": "11",
                "rejected_candidate_id": "10",
                "margin_gap": "0.1",
            },
        ],
    )
    _write_csv(
        history_dir / "wrong_history_pair_rows.csv",
        [
            {
                "history_intervention_id": "0",
                "correct_history_id": "0",
                "wrong_history_id": "1",
                "same_pair_swap": "True",
                "opposite_condition_swap": "True",
            },
            {
                "history_intervention_id": "1",
                "correct_history_id": "1",
                "wrong_history_id": "0",
                "same_pair_swap": "True",
                "opposite_condition_swap": "True",
            },
        ],
    )
    obs = np.zeros(72, dtype=np.float32)
    obs[44] = 1.0
    _write_csv(
        intervention_dir / "intervention_observations.csv",
        [
            {"intervention_id": "0"} | {f"obs_{i}": float(value) for i, value in enumerate(obs)},
            {"intervention_id": "1"} | {f"obs_{i}": float(value) for i, value in enumerate(obs)},
        ],
    )
    _write_csv(
        intervention_dir / "intervention_action_sequences.csv",
        [
            {"intervention_id": "0", "role": "preferred", "candidate_id": "10", "step": "0", "steer": "0.5", "throttle": "-1.0", "brake": "1.0"},
            {"intervention_id": "0", "role": "rejected", "candidate_id": "11", "step": "0", "steer": "-0.5", "throttle": "-1.0", "brake": "1.0"},
            {"intervention_id": "1", "role": "preferred", "candidate_id": "11", "step": "0", "steer": "-0.5", "throttle": "-1.0", "brake": "1.0"},
            {"intervention_id": "1", "role": "rejected", "candidate_id": "10", "step": "0", "steer": "0.5", "throttle": "-1.0", "brake": "1.0"},
        ],
    )

    summary = run_source_history_policy_gate(
        checkpoint_path=checkpoint,
        history_run_dir=history_dir,
        intervention_run_dir=intervention_dir,
        run_dir=run_dir,
        device="cpu",
    )

    assert summary["row_count"] == 2
    assert summary["finite_row_count"] == 2
    assert summary["projection_rows"] == 2
    assert summary["projection_valid_count"] == 2
    assert summary["wrong_history_valid_count"] == 2
    assert summary["checkpoint_contract"] == "canonical_72_human_view_online_recurrent"
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["labels_enter_actor_input"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "policy_gate_rows.csv").exists()
    assert (run_dir / "history_projection_audit.csv").exists()
