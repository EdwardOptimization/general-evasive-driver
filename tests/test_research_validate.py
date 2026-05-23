import csv
import json

import pytest

from autodrift.research_validate import (
    SCOREBOARD_FIELDS,
    load_scoreboard,
    normalize_next_task,
    validate_research_state,
)


def _write_queue(path, rows):
    fields = ["id", "priority", "status", "kind", "hypothesis", "command", "success_artifact", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_scoreboard(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCOREBOARD_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _manifest(task_id, artifact="docs/m90.md"):
    return {
        "id": task_id,
        "type": "driver_candidate",
        "hypothesis": "guarded PPO can preserve the wheel objective signal",
        "success_criteria": ["success >= 0.85"],
        "failure_criteria": ["zero-wheel gap < 0.10"],
        "commands": [{"name": "train", "command": "python -m autodrift.train_ppo"}],
        "required_artifacts": [{"path": artifact}],
        "baseline_checkpoints": ["runs/m89/checkpoint.pt"],
        "decision_rule": "promote only if retention and zero-wheel gates pass",
    }


def _process_v2_manifest(task_id, artifact="docs/m227.md"):
    manifest = _manifest(task_id, artifact=artifact)
    manifest.update(
        {
            "gate_tier": "process",
            "promotion_decision": "pending",
            "failure_types": ["proof_washout"],
            "lineage": {
                "parent_checkpoint": ["runs/m226/checkpoint.pt"],
                "parent_dataset": ["runs/m223/boundary_outcome_corpus.npz"],
                "parent_config": ["configs/ppo_m226_guarded_from_m224_smoke.json"],
                "parent_objective": ["M223 outcome objective"],
                "derived_from": ["m226"],
                "blocked_by": ["m226"],
                "supersedes": [],
                "invalidates": [],
            },
            "review_artifact": "docs/reviews/m227.md",
            "public_gates": ["M183 replay", "protected key"],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": ["do not promote broad behavior alone"],
        }
    )
    return manifest


def test_normalize_next_task_supports_string_and_object():
    assert normalize_next_task("m90") == "m90"
    assert normalize_next_task({"id": "m91"}) == "m91"
    assert normalize_next_task(None) is None
    with pytest.raises(ValueError):
        normalize_next_task(["m90"])


def test_load_scoreboard_requires_exact_fields(tmp_path):
    scoreboard = tmp_path / "scoreboard.csv"
    scoreboard.write_text("milestone,type\nm89,objective_sanity\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_scoreboard(scoreboard)


def test_load_scoreboard_rejects_unescaped_extra_columns(tmp_path):
    scoreboard = tmp_path / "scoreboard.csv"
    _write_scoreboard(scoreboard, [])
    scoreboard.write_text(
        scoreboard.read_text(encoding="utf-8") + "m90,gate,,,,,,,,,reject,reason with comma,extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="extra fields"):
        load_scoreboard(scoreboard)


def test_validate_research_state_requires_manifest_for_enforced_task(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m90",
                "priority": 870,
                "status": "planned",
                "kind": "training",
                "hypothesis": "run m90",
                "command": "",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 1, "completed": 0, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": "m90"}),
        encoding="utf-8",
    )
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("missing manifest" in issue.message for issue in issues)


def test_validate_research_state_requires_scoreboard_for_completed_enforced_task(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    docs = tmp_path / "docs"
    manifest_dir.mkdir()
    docs.mkdir()
    (docs / "m90.md").write_text("done\n", encoding="utf-8")
    _write_queue(
        queue,
        [
            {
                "id": "m90",
                "priority": 870,
                "status": "completed",
                "kind": "training",
                "hypothesis": "run m90",
                "command": "python -m autodrift.train_ppo",
                "success_artifact": "docs/m90.md",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 1, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": None}),
        encoding="utf-8",
    )
    (manifest_dir / "m90.json").write_text(json.dumps(_manifest("m90")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("missing scoreboard row" in issue.message for issue in issues)


def test_validate_research_state_accepts_current_enforced_planned_shape(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m89",
                "priority": 860,
                "status": "completed",
                "kind": "gate",
                "hypothesis": "legacy completed",
                "command": "python -m autodrift.wheel_masked_friction_optimize",
                "success_artifact": "",
                "notes": "",
            },
            {
                "id": "m90",
                "priority": 870,
                "status": "planned",
                "kind": "training",
                "hypothesis": "run m90",
                "command": "",
                "success_artifact": "",
                "notes": "",
            },
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 1, "completed": 1, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": "m90"}),
        encoding="utf-8",
    )
    (manifest_dir / "m90.json").write_text(json.dumps(_manifest("m90")), encoding="utf-8")
    _write_scoreboard(
        scoreboard,
        [
            {
                "milestone": "m89",
                "type": "objective_sanity",
                "checkpoint": "runs/m89/optimized_checkpoint.pt",
                "success_rate": "0.90",
                "termination_rate": "0.10",
                "clearance_margin_mean": "2.11",
                "reset_success": "0.80",
                "zero_wheel_success": "0.85",
                "zero_all_success": "0.90",
                "wheel_gain_mu": "0.137",
                "decision": "warm_start_candidate",
                "reason": "legacy reference row",
            }
        ],
    )

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_validate_research_state_recomputes_completed_structured_gate_decision(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    docs = tmp_path / "docs"
    manifest_dir.mkdir()
    docs.mkdir()
    (docs / "m90.md").write_text("done\n", encoding="utf-8")
    with (tmp_path / "policy_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["policy", "success_rate"], lineterminator="\n")
        writer.writeheader()
        writer.writerow({"policy": "m90", "success_rate": "0.90"})
    _write_queue(
        queue,
        [
            {
                "id": "m90",
                "priority": 870,
                "status": "completed",
                "kind": "training",
                "hypothesis": "run m90",
                "command": "python -m autodrift.train_ppo",
                "success_artifact": "docs/m90.md",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 1, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": None}),
        encoding="utf-8",
    )
    manifest = _manifest("m90")
    manifest["metric_extractors"] = [
        {
            "type": "csv",
            "metric": "success_rate",
            "path": "policy_summary.csv",
            "match": {"policy": "m90"},
            "column": "success_rate",
        }
    ]
    manifest["gates"] = [{"name": "retention", "metric": "success_rate", "op": ">=", "threshold": 0.85}]
    manifest["decision_labels"] = {"pass": "accepted", "fail": "rejected"}
    (manifest_dir / "m90.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(
        scoreboard,
        [
            {
                "milestone": "m90",
                "type": "driver_candidate",
                "checkpoint": "runs/m90/checkpoint.pt",
                "success_rate": "0.90",
                "termination_rate": "",
                "clearance_margin_mean": "",
                "reset_success": "",
                "zero_wheel_success": "",
                "zero_all_success": "",
                "wheel_gain_mu": "",
                "decision": "rejected",
                "reason": "wrong manual decision",
            }
        ],
    )

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("does not match structured gate decision" in issue.message for issue in issues)


def test_process_v2_requires_governance_fields_from_m227(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m227",
                "priority": 2220,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "audit PPO retention",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m227"}),
        encoding="utf-8",
    )
    (manifest_dir / "m227.json").write_text(json.dumps(_manifest("m227")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("process-v2 manifest missing fields" in issue.message for issue in issues)


def test_process_v2_accepts_pending_governance_manifest(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m227",
                "priority": 2220,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "audit PPO retention",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m227"}),
        encoding="utf-8",
    )
    (manifest_dir / "m227.json").write_text(json.dumps(_process_v2_manifest("m227")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v2_completed_reject_requires_failure_taxonomy_and_review(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    docs = tmp_path / "docs"
    manifest_dir.mkdir()
    docs.mkdir()
    (docs / "m227.md").write_text("done\n", encoding="utf-8")
    _write_queue(
        queue,
        [
            {
                "id": "m227",
                "priority": 2220,
                "status": "completed",
                "kind": "gate",
                "hypothesis": "audit PPO retention",
                "command": "see manifest",
                "success_artifact": "docs/m227.md",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 1, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": None}),
        encoding="utf-8",
    )
    manifest = _process_v2_manifest("m227")
    manifest["promotion_decision"] = "reject"
    manifest["failure_types"] = []
    (manifest_dir / "m227.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(
        scoreboard,
        [
            {
                "milestone": "m227",
                "type": "gate",
                "checkpoint": "",
                "success_rate": "",
                "termination_rate": "",
                "clearance_margin_mean": "",
                "reset_success": "",
                "zero_wheel_success": "",
                "zero_all_success": "",
                "wheel_gain_mu": "",
                "decision": "reject",
                "reason": "audit failed",
            }
        ],
    )

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("must classify failure_types" in issue.message for issue in issues)
    assert any("review_artifact is missing" in issue.message for issue in issues)


def test_process_v2_accepts_scenario_sampling_failure_taxonomy(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    docs = tmp_path / "docs"
    manifest_dir.mkdir()
    docs.mkdir(parents=True)
    (docs / "m227.md").write_text("done\n", encoding="utf-8")
    (docs / "review.md").write_text("review\n", encoding="utf-8")
    _write_queue(
        queue,
        [
            {
                "id": "m227",
                "priority": 2220,
                "status": "completed",
                "kind": "gate",
                "hypothesis": "challenge sampling audit",
                "command": "see manifest",
                "success_artifact": "docs/m227.md",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 1, "failed": 0, "blocked": 0, "pending": 0, "running": 0}, "next_task": None}),
        encoding="utf-8",
    )
    manifest = _process_v2_manifest("m227", artifact="docs/m227.md")
    manifest["promotion_decision"] = "reject"
    manifest["failure_types"] = ["scenario_sampling_failure"]
    manifest["review_artifact"] = "docs/review.md"
    (manifest_dir / "m227.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(
        scoreboard,
        [
            {
                "milestone": "m227",
                "type": "gate",
                "checkpoint": "",
                "success_rate": "",
                "termination_rate": "",
                "clearance_margin_mean": "",
                "reset_success": "",
                "zero_wheel_success": "",
                "zero_all_success": "",
                "wheel_gain_mu": "",
                "decision": "reject",
                "reason": "scenario sampling failed",
            }
        ],
    )

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []
