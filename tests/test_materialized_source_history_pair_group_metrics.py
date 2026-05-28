from __future__ import annotations

import csv

from autodrift.materialized_source_history_pair_group_metrics import run_pair_group_metrics
from test_materialized_source_history_objective_corpus_export import _write_csv


def _row(condition, correct_margin, wrong_margin, *, group="source:1|left_brake_probe"):
    source_identity, probe = group.split("|")
    return {
        "history_intervention_id": "0" if condition == "A" else "1",
        "source_identity": source_identity,
        "probe_template": probe,
        "source_family": "left_right_split_mu->left_right_split_mu",
        "fold": "0",
        "condition": condition,
        "correct_preference_margin": str(correct_margin),
        "wrong_history_preference_margin": str(wrong_margin),
        "correct_distance_to_preferred": "1.0",
        "correct_distance_to_rejected": "2.0" if correct_margin > 0 else "0.5",
        "wrong_distance_to_preferred": "2.0" if wrong_margin > 0 else "0.5",
        "wrong_distance_to_rejected": "1.0",
        "combined_loss": "3.0",
        "history_action_l2": "0.2",
    }


def test_pair_group_metrics_preserves_one_sided_conflict(tmp_path):
    rows_path = tmp_path / "rows.csv"
    run_dir = tmp_path / "run"
    _write_csv(
        rows_path,
        [
            _row("A", -1.0, 1.0),
            _row("B", 1.0, -1.0),
            _row("A", -1.0, -1.0, group="source:2|right_brake_probe"),
            _row("B", -1.0, -1.0, group="source:2|right_brake_probe"),
        ],
    )

    summary = run_pair_group_metrics(rows_path=rows_path, run_dir=run_dir)

    assert summary["row_count"] == 4
    assert summary["group_count"] == 2
    assert summary["valid_two_condition_group_count"] == 2
    assert summary["group_all_rows_both_directional_count"] == 0
    assert summary["group_one_sided_conflict_count"] == 1
    assert summary["group_both_negative_count"] == 1
    assert summary["checkpoint_loaded"] is False
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["actor_update_used"] is False
    assert summary["labels_enter_actor_input"] is False
    assert summary["result_class"] == "materialized_source_history_pair_group_metrics_pass"
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "group_rows.csv").exists()
    assert (run_dir / "family_group_summary.csv").exists()
    assert (run_dir / "fold_group_summary.csv").exists()

    with (run_dir / "group_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["valid_two_condition_group"] == "True"
    assert {row["group_one_sided_conflict"] for row in rows} == {"False", "True"}
