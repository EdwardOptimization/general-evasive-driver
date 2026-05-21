import csv
import json
import shlex
import sys

from autodrift.research_manifest import (
    build_manifest_summary,
    run_manifest_commands,
    summarize_manifest_to_scoreboard,
)


def _write_csv(path, rows):
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _manifest(tmp_path):
    return {
        "id": "m90",
        "type": "driver_candidate",
        "scoreboard_checkpoint": "runs/m90/checkpoint.pt",
        "metric_extractors": [
            {
                "type": "csv",
                "metric": "success_rate",
                "path": "policy_summary.csv",
                "match": {"policy": "m90"},
                "column": "success_rate",
            },
            {
                "type": "csv",
                "metric": "zero_wheel_success",
                "path": "policy_summary.csv",
                "match": {"policy": "m90_zero_wheel"},
                "column": "success_rate",
            },
            {
                "type": "csv",
                "metric": "clearance_margin_mean",
                "path": "policy_summary.csv",
                "match": {"policy": "m90"},
                "column": "min_clearance_margin_mean",
            },
            {
                "type": "csv",
                "metric": "wheel_gain_mu",
                "path": "wheel_gain_summary.csv",
                "match": {"target": "mu_bucket"},
                "column": "body_plus_wheel_gain",
            },
        ],
        "gates": [
            {"name": "retention", "metric": "success_rate", "op": ">=", "threshold": 0.85},
            {
                "name": "zero_wheel_gap",
                "aggregation": "difference",
                "left_metric": "success_rate",
                "right_metric": "zero_wheel_success",
                "op": ">=",
                "threshold": 0.10,
            },
            {"name": "wheel_gain", "metric": "wheel_gain_mu", "op": ">=", "threshold": 0.10},
        ],
        "decision_labels": {"pass": "continuation_candidate", "fail": "reject"},
        "commands": [{"name": "noop", "command": "true"}],
        "required_artifacts": [{"path": "docs/m90.md"}],
        "baseline_checkpoints": ["runs/m89/checkpoint.pt"],
        "hypothesis": "test manifest",
        "success_criteria": ["pass gates"],
        "failure_criteria": ["fail gates"],
        "decision_rule": "structured gates",
    }


def test_build_manifest_summary_extracts_metrics_and_gates(tmp_path):
    _write_csv(
        tmp_path / "policy_summary.csv",
        [
            {"policy": "m90", "success_rate": "0.90", "min_clearance_margin_mean": "2.2"},
            {"policy": "m90_zero_wheel", "success_rate": "0.75", "min_clearance_margin_mean": "1.7"},
        ],
    )
    _write_csv(
        tmp_path / "wheel_gain_summary.csv",
        [{"target": "mu_bucket", "body_plus_wheel_gain": "0.12"}],
    )

    summary = build_manifest_summary(_manifest(tmp_path), root=tmp_path)

    assert summary.decision == "continuation_candidate"
    assert all(gate.passed for gate in summary.gates)
    assert summary.scoreboard_row["success_rate"] == "0.9"
    assert summary.scoreboard_row["zero_wheel_success"] == "0.75"
    assert summary.scoreboard_row["clearance_margin_mean"] == "2.2"
    assert summary.scoreboard_row["wheel_gain_mu"] == "0.12"


def test_summarize_manifest_upserts_scoreboard_row(tmp_path):
    _write_csv(
        tmp_path / "policy_summary.csv",
        [
            {"policy": "m90", "success_rate": "0.90", "min_clearance_margin_mean": "2.2"},
            {"policy": "m90_zero_wheel", "success_rate": "0.88", "min_clearance_margin_mean": "2.1"},
        ],
    )
    _write_csv(
        tmp_path / "wheel_gain_summary.csv",
        [{"target": "mu_bucket", "body_plus_wheel_gain": "0.12"}],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest(tmp_path)), encoding="utf-8")
    scoreboard = tmp_path / "scoreboard.csv"

    summary = summarize_manifest_to_scoreboard(manifest_path, scoreboard, root=tmp_path)

    assert summary.decision == "reject"
    rows = list(csv.DictReader(scoreboard.open(newline="", encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["milestone"] == "m90"
    assert rows[0]["decision"] == "reject"
    assert "zero_wheel_gap" in rows[0]["reason"]


def test_run_manifest_commands_writes_receipt_and_artifact_provenance(tmp_path):
    artifact = tmp_path / "artifact.txt"
    script = "from pathlib import Path; Path('artifact.txt').write_text('ok', encoding='utf-8')"
    command = (
        f"{shlex.quote(sys.executable)} -c "
        f"{shlex.quote(script)}"
    )
    manifest = {
        "id": "m91",
        "type": "infrastructure",
        "commands": [{"name": "emit_artifact", "command": command}],
        "required_artifacts": [{"path": "artifact.txt"}],
    }

    results = run_manifest_commands(manifest, root=tmp_path, run_dir=tmp_path / "manifest_run")

    assert artifact.read_text(encoding="utf-8") == "ok"
    assert [result.returncode for result in results] == [0]
    receipt = json.loads((tmp_path / "manifest_run" / "run_receipt.json").read_text(encoding="utf-8"))
    assert receipt["manifest_id"] == "m91"
    assert receipt["required_artifacts"][0]["exists"] is True
    assert receipt["required_artifacts"][0]["sha256"]
