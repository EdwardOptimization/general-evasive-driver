from __future__ import annotations

import csv
import json

from autodrift.materialized_source_history_objective_corpus_export import (
    export_materialized_source_history_objective_corpus,
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


def _source(pair_id, family, fold=0):
    return {
        "pair_id": str(pair_id),
        "source_run_id": "source_run",
        "source_row_id": str(pair_id + 10),
        "original_pair_id": str(pair_id + 10),
        "source_identity": f"source_run:{pair_id + 10}",
        "source_family": family,
        "fold": str(fold),
    }


def _history_rows(pair_id, family, *, prefix_count=4, frame_count=8, response_l2=0.25):
    prefixes = []
    frames = []
    interventions = []
    wrong = []
    for idx in range(prefix_count):
        history_id = pair_id * 10 + idx
        common = {
            "history_id": str(history_id),
            "pair_id": str(pair_id),
            "source_run_id": "source_run",
            "source_row_id": str(pair_id + 10),
            "original_pair_id": str(pair_id + 10),
            "source_identity": f"source_run:{pair_id + 10}",
            "source_family": family,
            "fold": str(pair_id % 2),
            "response_l2_from_opposite_branch": str(response_l2),
        }
        prefixes.append(common)
        interventions.append(
            {
                "history_intervention_id": str(history_id),
                "pair_id": str(pair_id),
                "source_run_id": "source_run",
                "source_row_id": str(pair_id + 10),
                "original_pair_id": str(pair_id + 10),
                "source_identity": f"source_run:{pair_id + 10}",
            }
        )
        wrong.append(
            {
                "history_intervention_id": str(history_id),
                "pair_id": str(pair_id),
                "source_run_id": "source_run",
                "source_row_id": str(pair_id + 10),
                "original_pair_id": str(pair_id + 10),
                "source_identity": f"source_run:{pair_id + 10}",
                "same_pair_swap": "True",
            }
        )
    for idx in range(frame_count):
        frames.append(
            {
                "history_id": str(pair_id * 10),
                "pair_id": str(pair_id),
                "source_run_id": "source_run",
                "source_row_id": str(pair_id + 10),
                "original_pair_id": str(pair_id + 10),
                "source_identity": f"source_run:{pair_id + 10}",
                "step": str(idx),
            }
        )
    return prefixes, frames, interventions, wrong


def test_export_materialized_source_history_objective_corpus(tmp_path):
    materialized = tmp_path / "materialized"
    run = tmp_path / "run"
    materialized.mkdir()
    (materialized / "summary.json").write_text(
        json.dumps({"global_friction_missing": True}),
        encoding="utf-8",
    )
    source_rows = [
        _source(0, "left_right_split_mu->left_right_split_mu", fold=0),
        _source(1, "single_wheel_brake_pull->single_wheel_brake_pull", fold=1),
        _source(2, "halfshaft_torque_loss->halfshaft_torque_loss", fold=0),
    ]
    prefixes = []
    frames = []
    interventions = []
    wrong = []
    for row in source_rows:
        pair_id = int(row["pair_id"])
        family = row["source_family"]
        response_l2 = 0.0 if family == "halfshaft_torque_loss->halfshaft_torque_loss" else 0.2
        p, f, i, w = _history_rows(pair_id, family, response_l2=response_l2)
        prefixes.extend(p)
        frames.extend(f)
        interventions.extend(i)
        wrong.extend(w)

    _write_csv(materialized / "source_pair_rows.csv", source_rows)
    _write_csv(materialized / "history_prefix_rows.csv", prefixes)
    _write_csv(materialized / "history_frame_rows.csv", frames)
    _write_csv(materialized / "history_intervention_rows.csv", interventions)
    _write_csv(materialized / "wrong_history_pair_rows.csv", wrong)
    _write_csv(materialized / "source_lineage_rows.csv", [{"source_run_id": "source_run"}])

    summary = export_materialized_source_history_objective_corpus(
        materialized_run_dir=materialized,
        run_dir=run,
        min_response_l2=0.01,
    )

    assert summary["active_source_pair_rows"] == 2
    assert summary["active_history_prefix_rows"] == 8
    assert summary["active_history_frame_rows"] == 16
    assert summary["active_history_intervention_rows"] == 8
    assert summary["active_wrong_history_pair_rows"] == 8
    assert summary["active_source_family_count"] == 2
    assert summary["active_zero_response_l2_prefix_count"] == 0
    assert summary["active_response_l2_ge_0_01_count"] == 8
    assert summary["quarantine_source_pair_rows"] == 1
    assert summary["quarantine_history_prefix_rows"] == 4
    assert summary["quarantine_history_frame_rows"] == 8
    assert "halfshaft_probe_silent" in summary["quarantine_reasons"]
    assert "global_friction_missing" in summary["quarantine_reasons"]
    assert summary["source_identity_duplicate_count"] == 0
    assert summary["source_identity_metadata_preserved"] is True
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False

    with (run / "active_source_pair_rows.csv").open(newline="", encoding="utf-8") as handle:
        active_pairs = list(csv.DictReader(handle))
    assert {row["pair_id"] for row in active_pairs} == {"0", "1"}

    with (run / "quarantine_family_rows.csv").open(newline="", encoding="utf-8") as handle:
        reasons = {row["quarantine_reason"] for row in csv.DictReader(handle)}
    assert reasons == {"halfshaft_probe_silent", "global_friction_missing"}
