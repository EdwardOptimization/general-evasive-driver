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


def _process_v6_manifest(task_id, artifact="docs/m1896.md", stage="infrastructure", progress_type="new_tool_or_infra"):
    manifest = _process_v5_manifest(task_id, artifact=artifact, stage=stage)
    manifest["local_search_guard"] = {
        "actual_progress_type": progress_type,
        "process_overhead": "medium",
        "local_search_risk": "low",
        "same_failure_repeat_count": 0,
        "same_public_gate_repair_count": 0,
        "evidence_expansion": "adds a validator-enforced process guard but no driver-performance evidence",
        "paper_verdict_delta": "improves evidence governance only",
        "must_synthesize_if": [
            "same failure type repeats three times",
            "same public gate is repaired three times",
            "five consecutive milestones add no new data or panel evidence",
        ],
    }
    return manifest


def _process_v7_manifest(
    task_id,
    artifact="docs/m3220.md",
    evidence_axis="process_guardrail_validator_enforcement",
    milestone_intent=None,
):
    manifest = _process_v6_manifest(task_id, artifact=artifact)
    manifest["workflow_synthesis"]["evidence_axis"] = evidence_axis
    if milestone_intent is not None:
        manifest["milestone_intent"] = milestone_intent
    return manifest


def _queue_row(task_id, priority, status="pending", hypothesis="run process milestone", notes=""):
    return {
        "id": task_id,
        "priority": priority,
        "status": status,
        "kind": "infrastructure",
        "hypothesis": hypothesis,
        "command": "see manifest",
        "success_artifact": "",
        "notes": notes,
    }


def _write_state(tmp_path, rows, manifests):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir(exist_ok=True)
    _write_queue(queue, rows)
    counts = {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 0, "running": 0}
    for row in rows:
        counts[row["status"]] += 1
    next_candidates = [row["id"] for row in rows if row["status"] in {"pending", "planned"}]
    status.write_text(
        json.dumps({"counts": counts, "next_task": sorted(next_candidates)[0] if next_candidates else None}),
        encoding="utf-8",
    )
    for manifest in manifests:
        (manifest_dir / f"{manifest['id']}.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])
    return queue, status, manifest_dir, scoreboard


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


def test_validate_research_state_accepts_running_next_task_shape(tmp_path):
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
                "status": "running",
                "kind": "infrastructure",
                "hypothesis": "run m90",
                "command": "python run.py",
                "success_artifact": "",
                "notes": "",
            },
        ],
    )
    status.write_text(
        json.dumps(
            {
                "counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 0, "running": 1},
                "next_task": {
                    "id": "m90",
                    "priority": 870,
                    "status": "running",
                    "kind": "infrastructure",
                    "hypothesis": "run m90",
                    "command": "python run.py",
                    "success_artifact": "",
                    "notes": "",
                },
            }
        ),
        encoding="utf-8",
    )
    (manifest_dir / "m90.json").write_text(json.dumps(_manifest("m90")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

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


def test_process_v6_requires_local_search_guard_from_m1896(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1896",
                "priority": 18910,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "enforce local search guard",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps(
            {
                "counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0},
                "next_task": "m1896",
            }
        ),
        encoding="utf-8",
    )
    (manifest_dir / "m1896.json").write_text(json.dumps(_process_v5_manifest("m1896")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("process-v6 manifest missing fields" in issue.message for issue in issues)


def test_process_v6_accepts_local_search_guard(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1896",
                "priority": 18910,
                "status": "pending",
                "kind": "infrastructure",
                "hypothesis": "enforce local search guard",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps(
            {
                "counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0},
                "next_task": "m1896",
            }
        ),
        encoding="utf-8",
    )
    (manifest_dir / "m1896.json").write_text(json.dumps(_process_v6_manifest("m1896")), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v6_repeat_counts_require_synthesis_decision(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    _write_queue(
        queue,
        [
            {
                "id": "m1896",
                "priority": 18910,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "bad repeated local search",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        ],
    )
    status.write_text(
        json.dumps(
            {
                "counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 1, "running": 0},
                "next_task": "m1896",
            }
        ),
        encoding="utf-8",
    )
    manifest = _process_v6_manifest("m1896", progress_type="repair_only")
    manifest["local_search_guard"]["same_failure_repeat_count"] = 3
    (manifest_dir / "m1896.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("requires a workflow synthesis decision" in issue.message for issue in issues)


def test_process_v6_rejects_non_evidence_streak_without_synthesis(tmp_path):
    queue = tmp_path / "queue.csv"
    status = tmp_path / "status.json"
    manifest_dir = tmp_path / "manifests"
    scoreboard = tmp_path / "scoreboard.csv"
    manifest_dir.mkdir()
    rows = []
    for index in range(6):
        task_id = f"m189{index + 6}"
        rows.append(
            {
                "id": task_id,
                "priority": 18910 + index * 10,
                "status": "pending",
                "kind": "gate",
                "hypothesis": "continue local process iteration",
                "command": "see manifest",
                "success_artifact": "",
                "notes": "",
            }
        )
        manifest = _process_v6_manifest(task_id, progress_type="design_only")
        (manifest_dir / f"{task_id}.json").write_text(json.dumps(manifest), encoding="utf-8")
    _write_queue(queue, rows)
    status.write_text(
        json.dumps(
            {
                "counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "pending": 6, "running": 0},
                "next_task": "m1896",
            }
        ),
        encoding="utf-8",
    )
    _write_scoreboard(scoreboard, [])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("consecutive non-evidence milestones" in issue.message for issue in issues)


def test_process_v7_repair_axis_requires_feasibility_pricing(tmp_path):
    rows = [_queue_row("m3220", 32200, hypothesis="close a measured controller gap")]
    manifests = [_process_v7_manifest("m3220", evidence_axis="hard_safety_repair_direct_action")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("requires a feasibility_pricing object" in issue.message for issue in issues)


def test_process_v7_milestone_intent_triggers_pricing_requirement(tmp_path):
    rows = [_queue_row("m3220", 32200, hypothesis="close a measured controller gap")]
    manifests = [
        _process_v7_manifest(
            "m3220",
            evidence_axis="boundary_measurement_axis",
            milestone_intent="training",
        )
    ]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("requires a feasibility_pricing object" in issue.message for issue in issues)


def test_process_v7_explicit_non_priced_intent_overrides_axis_inference(tmp_path):
    rows = [_queue_row("m3220", 32200, hypothesis="audit a measured surface")]
    manifests = [
        _process_v7_manifest(
            "m3220",
            evidence_axis="post_repair_surface_audit",
            milestone_intent="measurement",
        )
    ]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert not any("requires a feasibility_pricing object" in issue.message for issue in issues)


def test_process_v7_accepts_compliant_feasibility_pricing(tmp_path):
    pricing_dir = tmp_path / "experiments" / "pricing"
    pricing_dir.mkdir(parents=True)
    (pricing_dir / "new_gap_pricing.json").write_text("{}\n", encoding="utf-8")
    manifest = _process_v7_manifest("m3220", evidence_axis="structural_ceiling_repair")
    manifest["feasibility_pricing"] = {
        "pricing_artifact": "experiments/pricing/new_gap_pricing.json",
        "priced_gap": 0.21,
        "threshold": 0.15,
        "gap_meets_threshold": True,
    }
    rows = [_queue_row("m3220", 32200, hypothesis="close a priced reachable gap")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, [manifest])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v7_rejects_missing_pricing_artifact_and_bad_types(tmp_path):
    manifest = _process_v7_manifest("m3220", evidence_axis="structural_ceiling_repair")
    manifest["feasibility_pricing"] = {
        "pricing_artifact": "experiments/pricing/does_not_exist.json",
        "priced_gap": "0.21",
        "threshold": 0.15,
        "gap_meets_threshold": "yes",
    }
    rows = [_queue_row("m3220", 32200, hypothesis="close a priced reachable gap")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, [manifest])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("pricing_artifact does not exist" in issue.message for issue in issues)
    assert any("priced_gap must be a number" in issue.message for issue in issues)
    assert any("gap_meets_threshold must be a boolean" in issue.message for issue in issues)


def test_process_v7_rejects_certified_dead_end_residual_seed_repair(tmp_path):
    rows = [
        _queue_row(
            "m3220",
            32200,
            hypothesis="repair the residual hard-safety row seed 401530 with a new controller patch",
        )
    ]
    manifests = [_process_v7_manifest("m3220", evidence_axis="residual_row_hard_safety_repair")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    dead_end = [issue.message for issue in issues if "certified dead end" in issue.message]
    assert dead_end
    assert any("oracle_certification_results.json" in message for message in dead_end)
    assert any("c5_reflex_degradation.json" in message for message in dead_end)


def test_process_v7_dead_end_reopened_only_with_new_pricing_artifact(tmp_path):
    pricing_dir = tmp_path / "experiments" / "pricing"
    pricing_dir.mkdir(parents=True)
    (pricing_dir / "residual_row_repricing.json").write_text("{}\n", encoding="utf-8")
    manifest = _process_v7_manifest("m3220", evidence_axis="residual_row_hard_safety_repair")
    manifest["feasibility_pricing"] = {
        "pricing_artifact": "experiments/pricing/residual_row_repricing.json",
        "priced_gap": 0.18,
        "threshold": 0.15,
        "gap_meets_threshold": True,
    }
    rows = [
        _queue_row(
            "m3220",
            32200,
            hypothesis="repair the residual hard-safety row seed 401530 after fresh re-pricing",
        )
    ]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, [manifest])

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def test_process_v7_rejects_certification_artifact_reused_as_new_pricing(tmp_path):
    manifest = _process_v7_manifest("m3220", evidence_axis="residual_row_hard_safety_repair")
    manifest["feasibility_pricing"] = {
        "pricing_artifact": "experiments/feasibility_audit/oracle_certification_results.json",
        "priced_gap": 0.18,
        "threshold": 0.15,
        "gap_meets_threshold": True,
    }
    rows = [
        _queue_row(
            "m3220",
            32200,
            hypothesis="repair the residual hard-safety row seed 401530 again",
        )
    ]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, [manifest])
    certification = tmp_path / "experiments" / "feasibility_audit"
    certification.mkdir(parents=True)
    (certification / "oracle_certification_results.json").write_text("{}\n", encoding="utf-8")

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("certified dead end" in issue.message for issue in issues)


def test_process_v7_rejects_reflex_drift_required_repair(tmp_path):
    rows = [
        _queue_row(
            "m3220",
            32200,
            hypothesis="repair the reflex family drift_required rows with a deeper governor",
        )
    ]
    manifests = [_process_v7_manifest("m3220", evidence_axis="reflex_drift_required_repair")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any(
        "certified dead end" in issue.message and "drift_required" in issue.message for issue in issues
    )


def test_process_v7_rejects_vehicle_spread_reflex_retuning(tmp_path):
    rows = [
        _queue_row(
            "m3220",
            32200,
            hypothesis="per-instance retuning of the reflex across the vehicle spread tiers",
        )
    ]
    manifests = [_process_v7_manifest("m3220", evidence_axis="vehicle_spread_reflex_retuning")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any(
        "certified dead end" in issue.message and "vehicle-spread reflex retuning" in issue.message
        for issue in issues
    )


def test_process_v7_not_enforced_below_priority_threshold(tmp_path):
    rows = [
        _queue_row(
            "m3219x",
            32190,
            hypothesis="repair the residual hard-safety row seed 401530 with a new controller patch",
        )
    ]
    manifests = [_process_v7_manifest("m3219x", evidence_axis="residual_row_hard_safety_repair")]
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert issues == []


def _dependency_unavailable_rows_and_manifests(count, note="blocked dependency: external chrono solver unavailable"):
    rows = []
    manifests = []
    for index in range(count):
        task_id = f"m322{index}"
        rows.append(
            _queue_row(
                task_id,
                32200 + index * 10,
                status="completed",
                hypothesis="continue branch bookkeeping milestone",
                notes=note,
            )
        )
        manifests.append(_process_v7_manifest(task_id))
    return rows, manifests


def test_process_v7b_two_dependency_unavailable_completed_require_escalation(tmp_path):
    rows, manifests = _dependency_unavailable_rows_and_manifests(2)
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert any("escalate instead of bookkeeping" in issue.message for issue in issues)


def test_process_v7b_single_dependency_unavailable_completed_is_allowed(tmp_path):
    rows, manifests = _dependency_unavailable_rows_and_manifests(1)
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert not any("escalate instead of bookkeeping" in issue.message for issue in issues)


def test_process_v7b_escalation_file_allows_dependency_streak(tmp_path):
    rows, manifests = _dependency_unavailable_rows_and_manifests(2)
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)
    escalations = tmp_path / "docs" / "escalations"
    escalations.mkdir(parents=True)
    (escalations / "README.md").write_text("protocol\n", encoding="utf-8")
    (escalations / "2026-06-12-chrono-solver.md").write_text(
        "Blocked branch: response_amplification_actor_coupling\nResume condition: solver released\n",
        encoding="utf-8",
    )

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert not any("escalate instead of bookkeeping" in issue.message for issue in issues)


def test_process_v7b_streak_resets_on_normal_completed_milestone(tmp_path):
    rows, manifests = _dependency_unavailable_rows_and_manifests(3)
    rows[1]["notes"] = "completed with fresh panel evidence"
    queue, status, manifest_dir, scoreboard = _write_state(tmp_path, rows, manifests)

    issues = validate_research_state(tmp_path, queue, status, manifest_dir, scoreboard)

    assert not any("escalate instead of bookkeeping" in issue.message for issue in issues)
