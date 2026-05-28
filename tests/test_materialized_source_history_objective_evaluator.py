from __future__ import annotations

import csv

from autodrift.materialized_source_history_objective_evaluator import (
    evaluate_materialized_source_history_objective,
)
from test_source_history_policy_gate import _history_frame, _write_checkpoint, _write_csv


def test_materialized_source_history_objective_evaluator_writes_finite_rows(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    corpus = tmp_path / "corpus"
    run = tmp_path / "run"
    _write_checkpoint(checkpoint)
    corpus.mkdir()

    source_common = {
        "pair_id": "0",
        "source_run_id": "source_run",
        "source_row_id": "10",
        "original_pair_id": "10",
        "source_identity": "source_run:10",
        "source_family": "left_right_split_mu->left_right_split_mu",
        "fold": "0",
    }
    _write_csv(corpus / "active_source_pair_rows.csv", [source_common])
    _write_csv(
        corpus / "active_history_frame_rows.csv",
        [
            _history_frame(0, "A", 0, vx=14.0, yaw_rate=0.10),
            _history_frame(0, "A", 1, vx=13.9, yaw_rate=0.15),
            _history_frame(1, "B", 0, vx=14.0, yaw_rate=-0.10),
            _history_frame(1, "B", 1, vx=13.8, yaw_rate=-0.15),
        ],
    )
    _write_csv(
        corpus / "active_history_intervention_rows.csv",
        [
            {
                **source_common,
                "history_intervention_id": "0",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "0",
                "preferred_candidate_id": "10",
                "rejected_candidate_id": "11",
                "preferred_steer": "0.5",
                "preferred_throttle": "-1.0",
                "preferred_brake": "1.0",
                "rejected_steer": "-0.5",
                "rejected_throttle": "-1.0",
                "rejected_brake": "1.0",
            }
        ],
    )
    _write_csv(
        corpus / "active_wrong_history_pair_rows.csv",
        [
            {
                **source_common,
                "history_intervention_id": "0",
                "correct_history_id": "0",
                "wrong_history_id": "1",
                "same_pair_swap": "True",
                "opposite_condition_swap": "True",
                "same_source_identity_swap": "True",
            }
        ],
    )

    summary = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint,
        corpus_run_dir=corpus,
        run_dir=run,
        device="cpu",
    )

    assert summary["row_count"] == 1
    assert summary["finite_row_count"] == 1
    assert summary["projection_valid_count"] == 1
    assert summary["wrong_history_valid_count"] == 1
    assert summary["active_quarantine_rows_used"] == 0
    assert summary["checkpoint_weights_mutated"] is False
    assert summary["exact_objective_finite"] is True
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["actor_update_used"] is False
    assert summary["labels_enter_actor_input"] is False
    assert summary["result_class"] == "materialized_source_history_objective_evaluator_pass"
    assert (run / "summary.json").exists()
    assert (run / "materialized_source_history_objective_rows.csv").exists()
    assert (run / "history_projection_audit.csv").exists()
    assert (run / "family_summary.csv").exists()
    assert (run / "fold_summary.csv").exists()

    with (run / "materialized_source_history_objective_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["source_identity"] == "source_run:10"
    assert float(rows[0]["combined_loss"]) > 0.0

    with (run / "history_projection_audit.csv").open(newline="", encoding="utf-8") as handle:
        projection_rows = list(csv.DictReader(handle))
    assert projection_rows[0]["source_observation_context_zero"] == "True"
