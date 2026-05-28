from __future__ import annotations

import csv
import json

from autodrift.source_history_weighted_repeat_tradeoff_audit import run_tradeoff_audit


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


def _write_summary(path, **kwargs):
    path.write_text(json.dumps(kwargs, indent=2), encoding="utf-8")


def test_weighted_repeat_tradeoff_audit_writes_classification_artifacts(tmp_path):
    baseline_dir = tmp_path / "baseline"
    weighted_dir = tmp_path / "weighted"
    failed_dir = tmp_path / "failed"
    plan_dir = tmp_path / "plan"
    run_dir = tmp_path / "audit"
    for path in (baseline_dir, weighted_dir, failed_dir, plan_dir):
        path.mkdir()

    _write_summary(
        baseline_dir / "summary.json",
        best_repeat_mean_eval_both_directional_fraction=0.25,
        best_repeat_mean_full_both_positive_count=40.0,
    )
    _write_summary(
        weighted_dir / "summary.json",
        best_repeat_mean_eval_both_directional_fraction=0.20,
        best_repeat_mean_full_both_positive_count=36.0,
    )
    _write_summary(
        failed_dir / "summary.json",
        top_failed_source_family_pair="single_wheel->single_wheel",
        top_failed_probe_template="left_brake_probe",
    )
    _write_summary(plan_dir / "summary.json", max_group_weight=2.0)

    base_scope = [
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
    ]
    weighted_scope = [
        {
            "scope": "fusion_head",
            "split_offset": "0",
            "forbidden_parameter_mutation_detected": "False",
            "eval_group_all_rows_both_positive_fraction": "0.0",
            "eval_both_directional_fraction": "0.0",
            "full_group_all_rows_both_positive_count": "10",
            "full_both_positive_count": "20",
        },
        {
            "scope": "fusion_head",
            "split_offset": "1",
            "forbidden_parameter_mutation_detected": "False",
            "eval_group_all_rows_both_positive_fraction": "0.5",
            "eval_both_directional_fraction": "0.5",
            "full_group_all_rows_both_positive_count": "30",
            "full_both_positive_count": "60",
        },
    ]
    _write_csv(baseline_dir / "scope_summaries.csv", base_scope)
    _write_csv(weighted_dir / "scope_summaries.csv", weighted_scope)

    base_groups = [
        {
            "pair_id": "10",
            "probe_template": "left_brake_probe",
            "all_rows_both_positive": "False",
            "group_min_margin": "-0.1",
            "scope": "fusion_head",
            "split": "full",
            "split_offset": "0",
        },
        {
            "pair_id": "20",
            "probe_template": "right_brake_probe",
            "all_rows_both_positive": "True",
            "group_min_margin": "0.2",
            "scope": "fusion_head",
            "split": "full",
            "split_offset": "0",
        },
    ]
    weighted_groups = [
        {
            "pair_id": "10",
            "probe_template": "left_brake_probe",
            "all_rows_both_positive": "True",
            "group_min_margin": "0.2",
            "scope": "fusion_head",
            "split": "full",
            "split_offset": "0",
        },
        {
            "pair_id": "20",
            "probe_template": "right_brake_probe",
            "all_rows_both_positive": "False",
            "group_min_margin": "-0.2",
            "scope": "fusion_head",
            "split": "full",
            "split_offset": "0",
        },
    ]
    _write_csv(baseline_dir / "group_rows.csv", base_groups)
    _write_csv(weighted_dir / "group_rows.csv", weighted_groups)
    _write_csv(
        plan_dir / "group_weight_rows.csv",
        [
            {
                "pair_id": "10",
                "probe_template": "left_brake_probe",
                "source_family_pair": "single_wheel->single_wheel",
                "source_fault_pair": "rear_left->rear_right",
                "margin_bucket": "near_boundary",
                "group_weight": "2.0",
                "failed_combo_boost": "0.5",
                "pair_specific_weight_used": "False",
            },
            {
                "pair_id": "20",
                "probe_template": "right_brake_probe",
                "source_family_pair": "split_mu->split_mu",
                "source_fault_pair": "left_low->right_low",
                "margin_bucket": "positive",
                "group_weight": "1.0",
                "failed_combo_boost": "0.0",
                "pair_specific_weight_used": "False",
            },
        ],
    )

    summary = run_tradeoff_audit(
        weighted_run_dir=weighted_dir,
        baseline_run_dir=baseline_dir,
        failed_offset_run_dir=failed_dir,
        plan_run_dir=plan_dir,
        run_dir=run_dir,
    )

    assert summary["baseline_repeat_offset_pass_count"] == 1
    assert summary["weighted_repeat_offset_pass_count"] == 1
    assert summary["new_pass_offsets"] == "1"
    assert summary["lost_pass_offsets"] == "0"
    assert summary["top_failed_combo_positive_delta"] == 1
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert (run_dir / "offset_comparison.csv").exists()
    assert (run_dir / "full_group_comparison.csv").exists()
    assert (run_dir / "source_probe_summary.csv").exists()
    assert (run_dir / "weight_gain_summary.csv").exists()
    saved = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["result_class"] == "weighted_repeat_mixed_tradeoff"
