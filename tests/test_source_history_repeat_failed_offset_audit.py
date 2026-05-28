from __future__ import annotations

import csv
import json

from autodrift.source_history_repeat_failed_offset_audit import run_failed_offset_audit


def _write_csv(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_failed_offset_audit_writes_composition_artifacts(tmp_path):
    repeat_dir = tmp_path / "repeat"
    history_dir = tmp_path / "history"
    run_dir = tmp_path / "audit"
    repeat_dir.mkdir()
    history_dir.mkdir()

    _write_csv(
        repeat_dir / "scope_summaries.csv",
        [
            {
                "scope": "fusion_head",
                "split_offset": "0",
                "forbidden_parameter_mutation_detected": "False",
                "eval_group_all_rows_both_positive_fraction": "0.25",
                "eval_both_directional_fraction": "0.25",
                "full_group_all_rows_both_positive_count": "20",
                "full_both_positive_count": "40",
            },
            {
                "scope": "fusion_head",
                "split_offset": "1",
                "forbidden_parameter_mutation_detected": "False",
                "eval_group_all_rows_both_positive_fraction": "0.0",
                "eval_both_directional_fraction": "0.0",
                "full_group_all_rows_both_positive_count": "10",
                "full_both_positive_count": "20",
            },
        ],
    )
    _write_csv(
        repeat_dir / "directional_rows.csv",
        [
            {
                "history_intervention_id": "0",
                "intervention_id": "0",
                "pair_id": "10",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "0",
                "init_name": "fusion_head",
                "correct_preference_margin": "0.1",
                "wrong_history_preference_margin": "0.2",
                "min_preference_margin": "0.1",
                "correct_positive": "True",
                "wrong_history_positive": "True",
                "both_positive": "True",
                "mutually_exclusive": "False",
                "split": "eval",
                "split_offset": "0",
            },
            {
                "history_intervention_id": "1",
                "intervention_id": "1",
                "pair_id": "20",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "2",
                "init_name": "fusion_head",
                "correct_preference_margin": "-0.1",
                "wrong_history_preference_margin": "-0.2",
                "min_preference_margin": "-0.2",
                "correct_positive": "False",
                "wrong_history_positive": "False",
                "both_positive": "False",
                "mutually_exclusive": "False",
                "split": "eval",
                "split_offset": "1",
            },
        ],
    )
    _write_csv(
        repeat_dir / "group_rows.csv",
        [
            {
                "pair_id": "10",
                "probe_template": "left_brake_probe",
                "row_count": "1",
                "both_positive_count": "1",
                "all_rows_both_positive": "True",
                "any_row_both_positive": "True",
                "group_min_margin": "0.1",
                "group_balance_loss": "0.0",
                "scope": "fusion_head",
                "split": "eval",
                "split_offset": "0",
            },
            {
                "pair_id": "20",
                "probe_template": "left_brake_probe",
                "row_count": "1",
                "both_positive_count": "0",
                "all_rows_both_positive": "False",
                "any_row_both_positive": "False",
                "group_min_margin": "-0.2",
                "group_balance_loss": "0.0",
                "scope": "fusion_head",
                "split": "eval",
                "split_offset": "1",
            },
        ],
    )
    _write_csv(
        history_dir / "history_frame_rows.csv",
        [
            {
                "history_id": "0",
                "pair_id": "10",
                "condition": "A",
                "fault_name": "rear_left",
                "fault_family": "single_wheel",
            },
            {
                "history_id": "1",
                "pair_id": "10",
                "condition": "B",
                "fault_name": "rear_right",
                "fault_family": "single_wheel",
            },
            {
                "history_id": "2",
                "pair_id": "20",
                "condition": "A",
                "fault_name": "front_left",
                "fault_family": "front_failure",
            },
            {
                "history_id": "3",
                "pair_id": "20",
                "condition": "B",
                "fault_name": "front_right",
                "fault_family": "front_failure",
            },
        ],
    )
    _write_csv(
        history_dir / "history_intervention_rows.csv",
        [
            {
                "history_intervention_id": "0",
                "intervention_id": "0",
                "pair_id": "10",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "0",
            },
            {
                "history_intervention_id": "1",
                "intervention_id": "1",
                "pair_id": "20",
                "condition": "A",
                "probe_template": "left_brake_probe",
                "correct_history_id": "2",
            },
        ],
    )
    _write_csv(
        history_dir / "wrong_history_pair_rows.csv",
        [
            {"history_intervention_id": "0", "correct_history_id": "0", "wrong_history_id": "1"},
            {"history_intervention_id": "1", "correct_history_id": "2", "wrong_history_id": "3"},
        ],
    )

    summary = run_failed_offset_audit(repeat_run_dir=repeat_dir, history_run_dir=history_dir, run_dir=run_dir)

    assert summary["passing_offsets"] == "0"
    assert summary["failing_offsets"] == "1"
    assert summary["failed_eval_group_count"] == 1
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert (run_dir / "offset_summary.csv").exists()
    assert (run_dir / "composition_summary.csv").exists()
    assert (run_dir / "failed_eval_groups.csv").exists()
    saved = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["top_failed_probe_template"] == "left_brake_probe"
