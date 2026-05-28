from __future__ import annotations

import csv

from autodrift.materialized_source_history_pair_group_update import (
    DEFAULT_TRAINABLE_SCOPE,
    run_materialized_source_history_pair_group_update,
)
from test_source_history_policy_gate import _history_frame, _write_checkpoint, _write_csv


def test_materialized_source_history_pair_group_update_writes_probe_artifacts(tmp_path):
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
            },
            {
                **source_common,
                "history_intervention_id": "1",
                "condition": "B",
                "probe_template": "left_brake_probe",
                "correct_history_id": "1",
                "preferred_candidate_id": "20",
                "rejected_candidate_id": "21",
                "preferred_steer": "-0.5",
                "preferred_throttle": "-1.0",
                "preferred_brake": "1.0",
                "rejected_steer": "0.5",
                "rejected_throttle": "-1.0",
                "rejected_brake": "1.0",
            },
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
            },
            {
                **source_common,
                "history_intervention_id": "1",
                "correct_history_id": "1",
                "wrong_history_id": "0",
                "same_pair_swap": "True",
                "opposite_condition_swap": "True",
                "same_source_identity_swap": "True",
            },
        ],
    )
    row_metrics = tmp_path / "row_metrics.csv"
    _write_csv(row_metrics, [{"row_id": "0"}, {"row_id": "1"}])

    summary = run_materialized_source_history_pair_group_update(
        checkpoint_path=checkpoint,
        corpus_run_dir=corpus,
        row_metrics_path=row_metrics,
        run_dir=run,
        device="cpu",
        train_folds="0",
        eval_fold=0,
        steps=2,
        lr=1e-4,
    )

    assert summary["trainable_scope"] == DEFAULT_TRAINABLE_SCOPE
    assert summary["finite_before"] is True
    assert summary["finite_after"] is True
    assert summary["log_std_l2"] == 0.0
    assert summary["forbidden_parameter_mutation_detected"] is False
    assert summary["actor_update_used"] is True
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["input_row_metrics_row_count"] == 2
    assert (run / "summary.json").exists()
    assert (run / "objective_before.json").exists()
    assert (run / "objective_after.json").exists()
    assert (run / "group_metrics_before.json").exists()
    assert (run / "group_metrics_after.json").exists()
    assert (run / "materialized_source_history_objective_rows_before.csv").exists()
    assert (run / "materialized_source_history_objective_rows_after.csv").exists()
    assert (run / "group_rows_before.csv").exists()
    assert (run / "group_rows_after.csv").exists()
    assert (run / "train_trace.csv").exists()
    assert (run / "parameter_delta.json").exists()
    assert (run / "parameter_delta_rows.csv").exists()
    assert (run / "checkpoints" / "raw_pair_group_update.pt").exists()

    with (run / "parameter_delta_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    forbidden_changed = [
        row["parameter"]
        for row in rows
        if row["allowed_trainable"] == "False" and row["changed"] == "True"
    ]
    assert forbidden_changed == []
