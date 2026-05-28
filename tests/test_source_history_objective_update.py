from __future__ import annotations

import json

import numpy as np

from autodrift.source_history_objective_update import run_source_history_objective_update
from test_source_history_policy_gate import _history_frame, _write_checkpoint, _write_csv


def test_run_source_history_objective_update_writes_probe_artifacts(tmp_path):
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
            }
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
            }
        ],
    )
    obs = np.zeros(72, dtype=np.float32)
    obs[44] = 1.0
    _write_csv(
        intervention_dir / "intervention_observations.csv",
        [
            {"intervention_id": "0"} | {f"obs_{i}": float(value) for i, value in enumerate(obs)},
        ],
    )
    _write_csv(
        intervention_dir / "intervention_action_sequences.csv",
        [
            {
                "intervention_id": "0",
                "role": "preferred",
                "candidate_id": "10",
                "step": "0",
                "steer": "0.5",
                "throttle": "-1.0",
                "brake": "1.0",
            },
            {
                "intervention_id": "0",
                "role": "rejected",
                "candidate_id": "11",
                "step": "0",
                "steer": "-0.5",
                "throttle": "-1.0",
                "brake": "1.0",
            },
        ],
    )

    summary = run_source_history_objective_update(
        checkpoint_path=checkpoint,
        history_run_dir=history_dir,
        intervention_run_dir=intervention_dir,
        run_dir=run_dir,
        device="cpu",
        steps=5,
        lr=1e-3,
    )

    assert summary["finite_before"] is True
    assert summary["finite_after"] is True
    assert summary["actor_mean_changed"] is True
    assert summary["non_actor_mean_mutation_detected"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "objective_before.json").exists()
    assert (run_dir / "objective_after.json").exists()
    assert (run_dir / "source_history_objective_rows_before.csv").exists()
    assert (run_dir / "source_history_objective_rows_after.csv").exists()
    assert (run_dir / "train_trace.csv").exists()
    assert (run_dir / "parameter_delta.json").exists()
    assert (run_dir / "checkpoints" / "raw_objective_update.pt").exists()
