from __future__ import annotations

import csv

from autodrift.source_history_directional_conflict_audit import (
    build_directional_conflict_rows,
    run_directional_conflict_audit,
)


def _row(history_intervention_id: int, correct: float, wrong: float, loss: float) -> dict[str, str]:
    return {
        "history_intervention_id": str(history_intervention_id),
        "intervention_id": str(history_intervention_id),
        "pair_id": "1",
        "condition": "A",
        "probe_template": "left_brake_probe",
        "correct_history_id": "0",
        "wrong_history_id": "1",
        "logp_cp": "0.0",
        "logp_cr": "0.0",
        "logp_wp": "0.0",
        "logp_wr": "0.0",
        "correct_preference_margin": str(correct),
        "wrong_history_preference_margin": str(wrong),
        "preferred_hidden_margin": "0.0",
        "rejected_hidden_margin": "0.0",
        "correct_preference_loss": "1.0",
        "wrong_history_preference_loss": "1.0",
        "combined_loss": str(loss),
        "history_action_l2": "0.1",
        "finite": "True",
    }


def _write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_build_directional_conflict_rows_detects_quadrants():
    rows = build_directional_conflict_rows(
        [_row(0, 1.0, -1.0, 10.0), _row(1, -1.0, 1.0, 10.0)],
        [_row(0, 0.5, -0.5, 5.0), _row(1, -0.5, 0.5, 5.0)],
    )

    assert [row["after_quadrant"] for row in rows] == [
        "correct_positive_wrong_negative",
        "correct_negative_wrong_positive",
    ]
    assert all(row["after_mutually_exclusive"] for row in rows)
    assert all(row["combined_loss_delta"] == -5.0 for row in rows)


def test_run_directional_conflict_audit_classifies_magnitude_compression(tmp_path):
    before = tmp_path / "before.csv"
    after = tmp_path / "after.csv"
    run_dir = tmp_path / "run"
    _write_rows(before, [_row(0, 2.0, -2.0, 10.0), _row(1, -2.0, 2.0, 10.0)])
    _write_rows(after, [_row(0, 0.5, -0.5, 4.0), _row(1, -0.5, 0.5, 4.0)])

    summary = run_directional_conflict_audit(before_rows_path=before, after_rows_path=after, run_dir=run_dir)

    assert summary["row_count"] == 2
    assert summary["after_mutually_exclusive_count"] == 2
    assert summary["after_both_positive_count"] == 0
    assert summary["combined_loss_delta_mean"] == -6.0
    assert summary["result_class"] == "source_history_directional_conflict_magnitude_compression"
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "directional_conflict_rows.csv").exists()
