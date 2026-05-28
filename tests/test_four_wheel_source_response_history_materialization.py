from __future__ import annotations

import csv
import json

from autodrift.four_wheel_source_response_history_materialization import (
    materialize_four_wheel_source_response_histories,
)


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


def _intervention(intervention_id, condition, fault_name, scenario_id="s0"):
    return {
        "intervention_id": str(intervention_id),
        "pair_id": "0",
        "source_subset": "near_high_union",
        "condition": condition,
        "fault_name": fault_name,
        "fault_family": "left_right_split_mu",
        "scenario_id": scenario_id,
        "preferred_candidate_id": "1",
        "rejected_candidate_id": "2",
        "preferred_margin": "0.2",
        "rejected_margin": "0.1",
        "margin_gap": "0.1",
    }


def test_materialize_four_wheel_source_response_histories(tmp_path):
    source = tmp_path / "source"
    interventions = tmp_path / "interventions"
    run = tmp_path / "run"
    source.mkdir()
    interventions.mkdir()
    (source / "summary.json").write_text(
        json.dumps({"scenario_profile": "viability_calibration"}),
        encoding="utf-8",
    )
    (interventions / "summary.json").write_text(json.dumps({"intervention_rows": 2}), encoding="utf-8")
    _write_csv(
        source / "scenario_summary.csv",
        [
            {
                "scenario_id": "s0",
                "vx": "14.0",
                "vy": "0.0",
                "yaw_rate": "0.0",
                "brake_force": "6000.0",
                "drive_force": "0.0",
            }
        ],
    )
    _write_csv(
        interventions / "intervention_rows.csv",
        [
            _intervention(0, "A", "split_mu_left_low"),
            _intervention(1, "B", "split_mu_right_low"),
        ],
    )

    summary = materialize_four_wheel_source_response_histories(
        source_run_dir=source,
        intervention_run_dir=interventions,
        run_dir=run,
        history_length=3,
    )

    assert summary["near_high_union_intervention_rows"] == 2
    assert summary["history_prefix_rows"] == 4
    assert summary["history_frame_rows"] == 12
    assert summary["history_intervention_rows"] == 4
    assert summary["wrong_history_pair_rows"] == 4
    assert summary["wrong_history_valid_count"] == 4
    assert summary["actor_view_history_all_finite"] is True
    assert summary["forbidden_actor_view_history_columns"] == []
    assert summary["training_started"] is False
    assert (run / "history_prefix_rows.csv").exists()
    assert (run / "history_frame_rows.csv").exists()
    assert (run / "history_intervention_rows.csv").exists()
    assert (run / "wrong_history_pair_rows.csv").exists()
