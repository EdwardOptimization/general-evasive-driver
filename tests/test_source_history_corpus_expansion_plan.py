from __future__ import annotations

import csv
import json

from autodrift.source_history_corpus_expansion_plan import run_corpus_expansion_plan


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


def test_corpus_expansion_plan_reports_gaps_without_training(tmp_path):
    source_dir = tmp_path / "source"
    history_dir = tmp_path / "history"
    run_dir = tmp_path / "run"
    source_dir.mkdir()
    history_dir.mkdir()

    _write_csv(
        source_dir / "all_accepted_source_rows.csv",
        [
            {
                "pair_id": "2",
                "scenario_id": "seed2",
                "seed": "2",
                "condition_A_fault": "rear_left_grip_collapse",
                "condition_B_fault": "rear_right_grip_collapse",
                "fault_family_pair": "single_wheel_grip_collapse->single_wheel_grip_collapse",
                "source_family": "single_wheel_grip_collapse->single_wheel_grip_collapse",
                "severity_pair": "severe->severe",
                "speed": "14.0",
                "obstacle_body_x": "12.0",
                "min_own_margin": "0.04",
                "min_cross_regret": "0.1",
            },
            {
                "pair_id": "5",
                "scenario_id": "seed5",
                "seed": "5",
                "condition_A_fault": "front_left_brake_pull",
                "condition_B_fault": "front_right_brake_pull",
                "fault_family_pair": "single_wheel_brake_pull->single_wheel_brake_pull",
                "source_family": "single_wheel_brake_pull->single_wheel_brake_pull",
                "severity_pair": "severe->severe",
                "speed": "20.0",
                "obstacle_body_x": "18.0",
                "min_own_margin": "0.3",
                "min_cross_regret": "0.04",
            },
        ],
    )
    _write_csv(
        history_dir / "history_intervention_rows.csv",
        [
            {"history_intervention_id": "0", "pair_id": "2"},
            {"history_intervention_id": "1", "pair_id": "5"},
        ],
    )

    summary = run_corpus_expansion_plan(
        source_corpus_run_dir=source_dir,
        history_run_dir=history_dir,
        run_dir=run_dir,
        target_source_pairs=8,
        fold_count=2,
    )

    assert summary["planned_source_pairs"] == 2
    assert summary["planned_pair_probe_groups"] == 4
    assert summary["pair_disjoint"] is True
    assert summary["pair_specific_weight_used"] is False
    assert summary["coverage_gap_reported"] is True
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert (run_dir / "planned_source_pairs.csv").exists()
    assert (run_dir / "planned_pair_probe_groups.csv").exists()
    assert (run_dir / "fold_balance_summary.csv").exists()
    assert (run_dir / "family_coverage_summary.csv").exists()
    assert (run_dir / "requires_source_generator_update.csv").exists()
    saved = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["result_class"] == "source_history_corpus_expansion_plan_gap_reported"
