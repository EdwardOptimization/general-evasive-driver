from __future__ import annotations

import csv
import json

from autodrift.source_history_concentration_refresh_plan import run_concentration_refresh_plan


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


def _group(pair_id, offset, probe, family, margin, both):
    return {
        "split_offset": str(offset),
        "split": "eval",
        "offset_status": "fail" if offset == 1 else "pass",
        "offset_pass": "False" if offset == 1 else "True",
        "pair_id": str(pair_id),
        "probe_template": probe,
        "row_count": "2",
        "both_positive_count": "2" if both else "0",
        "all_rows_both_positive": "True" if both else "False",
        "any_row_both_positive": "True" if both else "False",
        "group_min_margin": str(margin),
        "group_balance_loss": "0.0",
        "source_family_pair": family,
        "source_fault_pair": f"{family}_fault",
    }


def test_concentration_refresh_plan_writes_balanced_weights(tmp_path):
    failed_dir = tmp_path / "failed"
    run_dir = tmp_path / "plan"
    failed_dir.mkdir()

    group_rows = [
        _group(1, 0, "left_brake_probe", "family_a", -0.01, False),
        _group(1, 0, "right_brake_probe", "family_a", 0.2, True),
        _group(2, 1, "left_brake_probe", "family_a", -1.2, False),
        _group(2, 1, "right_brake_probe", "family_a", -0.2, False),
        _group(3, 2, "left_brake_probe", "family_b", 0.1, True),
        _group(3, 2, "right_brake_probe", "family_b", -0.03, False),
        _group(4, 3, "left_brake_probe", "family_c", 0.2, True),
        _group(4, 3, "right_brake_probe", "family_c", 0.3, True),
    ]
    _write_csv(failed_dir / "eval_group_rows.csv", group_rows)
    _write_csv(
        failed_dir / "failed_eval_groups.csv",
        [row for row in group_rows if row["all_rows_both_positive"] == "False"],
    )

    summary = run_concentration_refresh_plan(
        failed_offset_run_dir=failed_dir,
        run_dir=run_dir,
        fold_count=2,
    )

    assert summary["pair_count"] == 4
    assert summary["pair_disjoint"] is True
    assert summary["all_folds_nonempty"] is True
    assert summary["all_folds_have_both_probe_templates"] is True
    assert summary["pair_specific_weight_used"] is False
    assert summary["max_group_weight"] <= 2.0
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert (run_dir / "balanced_split_rows.csv").exists()
    assert (run_dir / "group_weight_rows.csv").exists()
    assert (run_dir / "fold_composition_summary.csv").exists()
    saved = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["result_class"] == "source_history_concentration_refresh_plan_admissible"
