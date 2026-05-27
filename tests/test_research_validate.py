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


def _process_v3_manifest(task_id, artifact="docs/m690.md"):
    manifest = _process_v2_manifest(task_id, artifact=artifact)
    manifest["workflow_synthesis"] = {
        "branch": "response_amplification_actor_coupling",
        "evidence_axis": "G_action",
        "evidence_increment": "audits whether the latest exact gate changes branch admissibility",
        "claim_scope": "diagnostic exact gate, not promotion",
        "stop_condition": [
            "stop before PPO unless the next manifest adds proof, behavior, and generalization gates"
        ],
        "fallback_plan": [
            "if the branch fails closed-loop replay, return to source-diverse terminal-boundary target mining"
        ],
        "synthesis_cadence": 10,
        "synthesis_trigger": "before any post-diagnostic actor-update continuation",
        "synthesis_decision": "not_applicable",
    }
    return manifest


def _process_v3_synthesis_manifest(task_id, artifact="docs/m690-synthesis.md", decision="continue"):
    manifest = _process_v3_manifest(task_id, artifact=artifact)
    manifest["gate_tier"] = "process"
    manifest["workflow_synthesis"]["synthesis_decision"] = decision
    manifest["workflow_synthesis"]["evidence_increment"] = (
        "synthesizes the branch evidence and selects whether to continue, pivot, stop, or promote"
    )
    manifest["workflow_synthesis"]["synthesis_artifact"] = artifact
    manifest["workflow_synthesis"]["synthesis_questions"] = [
        "evidence_summary",
        "supported_claims",
        "falsified_claims",
        "failure_taxonomy_summary",
        "public_gate_overfit_risk",
        "next_branch_decision",
    ]
    return manifest


def _process_v4_manifest(task_id, artifact="docs/m1087.md", stage="infrastructure"):
    manifest = _process_v3_manifest(task_id, artifact=artifact)
    manifest["commands"] = [{"name": "process_update", "command": "true"}]
    manifest["training_stage"] = {
        "stage": stage,
        "stage_objective": "keep this milestone within the staged training discipline",
        "admission_evidence": [
            "pretrain/posttrain/RL discipline is documented",
            "no guarded RL is admitted by this infrastructure milestone",
        ],
        "blocked_shortcuts": [
            "do not run PPO before pretrain, posttrain, exact proof gates, and rollback protections are named",
        ],
        "allowed_updates": [
            "process documentation",
            "harness validation",
        ],
        "next_stage_criteria": [
            "future guarded_rl manifests must cite pre/posttrain capability evidence, exact/proof gates, and rollback protections",
        ],
    }
    return manifest


def _process_v5_manifest(task_id, artifact="docs/m1090.md", stage="infrastructure"):
    manifest = _process_v4_manifest(task_id, artifact=artifact, stage=stage)
    manifest["self_id_evidence_discipline"] = {
        "claim_level": "not_applicable",
        "current_frame_substitution_risk": "infrastructure milestone; no self-identification claim",
        "history_necessity_tests": [
            "normal vs reset/zero/delayed/wrong history gates remain required before self-ID claims",
        ],
        "temporal_evidence_window": "not applicable for this infrastructure milestone",
        "negative_result_policy": "record negative self-ID evidence instead of weakening gates",
        "allowed_claims": [
            "process or infrastructure claim only",
        ],
    }
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


def test_process_v3_requires_workflow_synthesis_from_m690(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "audit response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    (manifest_dir / "m690.json").write_text(json.dumps(_process_v2_manifest("m690")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("process-v3 manifest missing fields" in issue.message for issue in issues)


def test_process_v3_accepts_workflow_synthesis_manifest(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "audit response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    (manifest_dir / "m690.json").write_text(json.dumps(_process_v3_manifest("m690")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v3_rejects_out_of_range_synthesis_cadence(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "audit response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    manifest = _process_v3_manifest("m690")
    manifest["workflow_synthesis"]["synthesis_cadence"] = 21
    (manifest_dir / "m690.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("synthesis_cadence must be between 10 and 20" in issue.message for issue in issues)


def test_process_v3_rejects_synthesis_decision_on_non_process_gate(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "synthesize response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    manifest = _process_v3_manifest("m690")
    manifest["gate_tier"] = "proof"
    manifest["workflow_synthesis"]["synthesis_decision"] = "continue"
    (manifest_dir / "m690.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("requires gate_tier='process'" in issue.message for issue in issues)


def test_process_v3_rejects_branch_after_cadence_without_synthesis(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    rows = []
    for index in range(11):
        task_id = f"m69{index}"
        rows.append(
            {
                "id": task_id,
                "priority": 6850 + index * 10,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "continue response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        )
        (manifest_dir / f"{task_id}.json").write_text(json.dumps(_process_v3_manifest(task_id)), encoding="utf-8")
    _write_queue(queue, rows)
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 11, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("non-synthesis milestones since the last synthesis" in issue.message for issue in issues)


def test_process_v3_synthesis_decision_resets_branch_cadence(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    rows = []
    for index in range(12):
        task_id = f"m69{index}"
        rows.append(
            {
                "id": task_id,
                "priority": 6850 + index * 10,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "continue or synthesize response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        )
        manifest = _process_v3_manifest(task_id)
        if index == 10:
            manifest = _process_v3_synthesis_manifest(task_id)
        (manifest_dir / f"{task_id}.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_queue(queue, rows)
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 12, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v3_synthesis_decision_requires_artifact_and_questions(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "synthesize response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    manifest = _process_v3_manifest("m690")
    manifest["workflow_synthesis"]["synthesis_decision"] = "continue"
    (manifest_dir / "m690.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("synthesis_artifact must be non-empty text" in issue.message for issue in issues)
    assert any("synthesis_questions must be a non-empty list" in issue.message for issue in issues)


def test_process_v3_synthesis_decision_requires_all_synthesis_questions(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m690",
                "priority": 6850,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "synthesize response amplification branch",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m690"}),
        encoding="utf-8",
    )
    manifest = _process_v3_synthesis_manifest("m690")
    manifest["workflow_synthesis"]["synthesis_questions"] = ["evidence_summary"]
    (manifest_dir / "m690.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("synthesis_questions missing" in issue.message for issue in issues)


def test_process_v4_requires_training_stage_from_m1087(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1087",
                "priority": 10820,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "enforce staged training discipline",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1087"}),
        encoding="utf-8",
    )
    (manifest_dir / "m1087.json").write_text(json.dumps(_process_v3_manifest("m1087")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("process-v4 manifest missing fields" in issue.message for issue in issues)


def test_process_v4_accepts_training_stage_manifest(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1087",
                "priority": 10820,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "enforce staged training discipline",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1087"}),
        encoding="utf-8",
    )
    (manifest_dir / "m1087.json").write_text(json.dumps(_process_v4_manifest("m1087")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v4_rejects_train_ppo_outside_guarded_rl(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1087",
                "priority": 10820,
                "status": "pending",
                "kind": "driver_candidate",
                "hypothesis": "bad PPO shortcut",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1087"}),
        encoding="utf-8",
    )
    manifest = _process_v4_manifest("m1087", stage="action_grounding_posttrain")
    manifest["commands"] = [{"name": "bad_ppo", "command": "PYTHONPATH=src python -m autodrift.train_ppo"}]
    (manifest_dir / "m1087.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("must use training_stage.stage='guarded_rl'" in issue.message for issue in issues)


def test_process_v4_guarded_rl_requires_admission_evidence(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1087",
                "priority": 10820,
                "status": "pending",
                "kind": "driver_candidate",
                "hypothesis": "guarded PPO missing evidence",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1087"}),
        encoding="utf-8",
    )
    manifest = _process_v4_manifest("m1087", stage="guarded_rl")
    manifest["commands"] = [{"name": "ppo", "command": "PYTHONPATH=src python -m autodrift.train_ppo"}]
    manifest["training_stage"]["admission_evidence"] = ["basic behavior exists"]
    (manifest_dir / "m1087.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("guarded_rl stage must cite" in issue.message for issue in issues)


def test_process_v5_requires_self_id_evidence_discipline_from_m1090(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1090",
                "priority": 10850,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "enforce self-ID evidence discipline",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1090"}),
        encoding="utf-8",
    )
    (manifest_dir / "m1090.json").write_text(json.dumps(_process_v4_manifest("m1090")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("process-v5 manifest missing fields" in issue.message for issue in issues)


def test_process_v5_accepts_self_id_evidence_discipline(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1090",
                "priority": 10850,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "enforce self-ID evidence discipline",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1090"}),
        encoding="utf-8",
    )
    (manifest_dir / "m1090.json").write_text(json.dumps(_process_v5_manifest("m1090")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v5_rejects_unknown_self_id_claim_level(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1090",
                "priority": 10850,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "bad self-ID claim",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps({"counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0}, "next_task": "m1090"}),
        encoding="utf-8",
    )
    manifest = _process_v5_manifest("m1090")
    manifest["self_id_evidence_discipline"]["claim_level"] = "driver_like_self_id_without_evidence"
    (manifest_dir / "m1090.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("claim_level must be one of" in issue.message for issue in issues)
