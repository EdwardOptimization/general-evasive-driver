from __future__ import annotations

import csv
import json

import numpy as np

from autodrift.source_history_objective_evaluator import (
    evaluate_source_history_objective_rows,
    run_source_history_objective_evaluator,
)
from test_source_history_policy_gate import _history_frame, _write_checkpoint, _write_csv


def test_evaluate_source_history_objective_rows_is_finite():
    rows = evaluate_source_history_objective_rows(
        [
            {
                "history_intervention_id": "0",
                "intervention_id": "0",
                "pair_id": "0",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "0",
                "wrong_history_id": "1",
                "logp_cp": "-1.0",
                "logp_cr": "-2.0",
                "logp_wp": "-3.0",
                "logp_wr": "-1.5",
                "correct_preference_margin": "1.0",
                "wrong_history_preference_margin": "1.5",
                "preferred_hidden_margin": "2.0",
                "rejected_hidden_margin": "0.5",
                "history_action_l2": "0.2",
                "finite": "True",
            }
        ],
        correct_margin=0.05,
        wrong_margin=0.05,
    )

    assert len(rows) == 1
    assert rows[0]["finite"] is True
    assert rows[0]["correct_preference_loss"] > 0.0
    assert rows[0]["wrong_history_preference_loss"] > 0.0
    assert rows[0]["combined_loss"] > 0.0


def test_run_source_history_objective_evaluator_writes_exact_rows(tmp_path):
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

    summary = run_source_history_objective_evaluator(
        checkpoint_path=checkpoint,
        history_run_dir=history_dir,
        intervention_run_dir=intervention_dir,
        run_dir=run_dir,
        device="cpu",
    )

    assert summary["row_count"] == 1
    assert summary["finite_row_count"] == 1
    assert summary["exact_objective_finite"] is True
    assert summary["checkpoint_weights_mutated"] is False
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["result_class"] == "source_history_objective_evaluator_pass"
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "source_history_objective_rows.csv").exists()
    with (run_dir / "source_history_objective_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["combined_loss"]) > 0.0
