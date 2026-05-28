from __future__ import annotations

import csv
import json

from autodrift.four_wheel_source_corpus_export import export_four_wheel_source_corpus


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


def test_export_four_wheel_source_corpus_stratifies_rows(tmp_path):
    source = tmp_path / "source"
    run = tmp_path / "export"
    source.mkdir()
    (source / "summary.json").write_text(
        json.dumps({"scenario_profile": "viability_calibration", "accepted_separable_pairs": 3}),
        encoding="utf-8",
    )
    _write_csv(
        source / "scenario_summary.csv",
        [
            {"scenario_id": "s0", "vx": "14.0"},
            {"scenario_id": "s1", "vx": "15.0"},
            {"scenario_id": "s2", "vx": "16.0"},
            {"scenario_id": "s3", "vx": "16.0"},
        ],
    )
    accepted_rows = [
        {
            "pair_id": "0",
            "scenario_id": "s0",
            "fault_family_pair": "split",
            "margin_A_best_A": "0.10",
            "margin_B_best_B": "0.12",
            "cross_regret_A": "0.06",
            "cross_regret_B": "0.07",
        },
        {
            "pair_id": "1",
            "scenario_id": "s1",
            "fault_family_pair": "split",
            "margin_A_best_A": "0.30",
            "margin_B_best_B": "0.32",
            "cross_regret_A": "0.03",
            "cross_regret_B": "0.04",
        },
        {
            "pair_id": "2",
            "scenario_id": "s2",
            "fault_family_pair": "grip",
            "margin_A_best_A": "0.03",
            "margin_B_best_B": "0.05",
            "cross_regret_A": "0.10",
            "cross_regret_B": "0.08",
        },
    ]
    _write_csv(source / "accepted_separable_pairs.csv", accepted_rows)
    _write_csv(
        source / "matched_capability_pairs.csv",
        accepted_rows
        + [
            {
                "pair_id": "3",
                "scenario_id": "s3",
                "fault_family_pair": "halfshaft",
                "margin_A_best_A": "0.50",
                "margin_B_best_B": "0.50",
                "cross_regret_A": "0.00",
                "cross_regret_B": "0.00",
                "best_action_l2": "0.00",
                "best_A_success": "True",
                "best_B_success": "True",
                "rejection_reason": "best_actions_too_close",
            }
        ],
    )

    summary = export_four_wheel_source_corpus(source_run_dir=source, run_dir=run, family_cap=1)

    assert summary["exported_accepted_rows"] == 3
    assert summary["near_boundary_rows"] == 2
    assert summary["high_regret_rows"] == 2
    assert summary["family_balanced_rows"] == 2
    assert summary["inactive_fault_families"] == ["halfshaft"]
    assert summary["training_started"] is False
    assert (run / "all_accepted_source_rows.csv").exists()
    assert (run / "near_boundary_source_rows.csv").exists()
    assert (run / "high_regret_source_rows.csv").exists()
    assert (run / "family_balanced_source_rows.csv").exists()
    assert (run / "inactive_fault_families.csv").exists()
