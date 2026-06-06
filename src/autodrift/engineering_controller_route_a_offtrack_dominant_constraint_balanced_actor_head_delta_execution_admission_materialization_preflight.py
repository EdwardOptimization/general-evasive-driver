"""Materialize M2956 actor-head delta execution-admission rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


MILESTONE_ID = (
    "m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-execution-admission-materialization-preflight"
)
NEXT_ID = (
    "m2957-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-execution-admission-materialization-result-audit"
)
DEFAULT_M2953_DIR = Path(
    "runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "source_diverse_evidence_surface_materialization_preflight"
)
DEFAULT_M2954_AUDIT = Path(
    "docs/m2954-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "source-diverse-evidence-surface-materialization-result-audit.md"
)
DEFAULT_M2955_DESIGN = Path(
    "docs/m2955-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "candidate-execution-admission-design.md"
)
DEFAULT_M2916_DIR = Path(
    "runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight"
)
DEFAULT_M2917_AUDIT = Path(
    "docs/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2956_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "execution_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "execution-admission-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2957-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-execution-admission-materialization-result-audit.json"
)

ACTION_DIM = 3
M2916_ADMITTED_STATUS = "execution_admission_admitted_for_separate_bounded_execution_manifest"
M2916_STALE_STATUS = "execution_admission_blocked_stale_fixed_surface"
ADMITTED_STATUS = "actor_head_delta_execution_admission_materialized_for_separate_bounded_execution_design"
BLOCKED_STALE_STATUS = "actor_head_delta_execution_admission_blocked_stale_fixed_surface"
BLOCKED_SOURCE_STATUS = "actor_head_delta_execution_admission_blocked_source_identity_unresolved"
REJECTED_ACTOR_STATUS = "actor_head_delta_execution_admission_rejected_actor_contract_violation"
REJECTED_HIDDEN_STATUS = "actor_head_delta_execution_admission_rejected_hidden_oracle_required"
REJECTED_FUTURE_STATUS = "actor_head_delta_execution_admission_rejected_future_target_required"
REJECTED_DENOMINATOR_STATUS = "actor_head_delta_execution_admission_rejected_denominator_boundary_violation"
REJECTED_CHECKPOINT_STATUS = "actor_head_delta_execution_admission_rejected_checkpoint_or_config_missing"
REJECTED_TRACE_STATUS = "actor_head_delta_execution_admission_rejected_delta_contract_trace_missing"
DECISION_PASS = "actor_head_delta_execution_admission_materialized_route_to_m2957_result_audit"
DECISION_FAIL = "actor_head_delta_execution_admission_materialization_incomplete"

CLAIM_SCOPE = (
    "M2956 actor-head delta execution-admission materialization only; accepted "
    "M2953 actor-head delta panel rows and accepted M2916 Route A execution-admission "
    "rows may be bound into candidate, rejection, guardrail, actor-delta contract, "
    "claim-boundary, and gate rows, but no reset, step, rollout, replay, validation, "
    "training, PPO, dependency execution, adapter probe, checkpoint mutation, ranking, "
    "winner selection, promotion, success-rate verdict, implementation-readiness, "
    "repair-success, driver-performance, paper, current-sim, high-fidelity, full-driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)

INPUT_SURFACE_FIELDNAMES = [
    "input_surface_id",
    "source_family",
    "source_artifact",
    "source_exists",
    "row_count",
    "status_pass_or_present",
    "surface_role",
    "claim_scope",
]
CANDIDATE_FIELDNAMES = [
    "actor_head_delta_candidate_id",
    "source_execution_admission_candidate_id",
    "source_milestone",
    "source_artifact",
    "source_row_id",
    "source_family",
    "task_family",
    "workload_id",
    "task_source_id",
    "profile_name",
    "parent_checkpoint_path",
    "parent_profile_config_path",
    "actor_head_delta_panel_spec_ids",
    "actor_head_delta_traceability_count",
    "execution_admission_status",
    "required_follow_up",
    "environment_reset_admitted",
    "environment_rollout_scheduled",
    "measured_validation_scheduled",
    "training_scheduled",
    "dependency_execution_scheduled",
    "checkpoint_load_scheduled",
    "checkpoint_save_scheduled",
    "checkpoint_mutation_scheduled",
    "profile_specific_tuning",
    "actor_observation_dim",
    "actor_action_dim",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "evaluator_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ordinary_engineering_denominator_allowed_after_audit",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "materialization_only_no_execution",
    "claim_boundary",
]
REJECTION_FIELDNAMES = [
    "rejection_id",
    "source_execution_admission_candidate_id",
    "source_milestone",
    "source_artifact",
    "source_row_id",
    "rejection_type",
    "rejection_reason",
    "required_follow_up",
    "actor_visible",
    "claim_scope",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_source",
    "guardrail_family",
    "source_row_id",
    "guardrail_reason",
    "execution_allowed",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "claim_scope",
]
ACTOR_DELTA_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible_allowed",
    "execution_scheduled",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2956",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "input_surface_rows",
    "candidate_rows",
    "rejection_rows",
    "source_guardrail_rows",
    "actor_delta_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def materialize_actor_head_delta_execution_admission(
    *,
    m2953_dir: Path | str = DEFAULT_M2953_DIR,
    m2954_audit: Path | str = DEFAULT_M2954_AUDIT,
    m2955_design: Path | str = DEFAULT_M2955_DESIGN,
    m2916_dir: Path | str = DEFAULT_M2916_DIR,
    m2917_audit: Path | str = DEFAULT_M2917_AUDIT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2953_dir=Path(m2953_dir),
        m2954_audit=Path(m2954_audit),
        m2955_design=Path(m2955_design),
        m2916_dir=Path(m2916_dir),
        m2917_audit=Path(m2917_audit),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_rows = build_input_surface_rows(source)
    candidate_rows = build_candidate_rows(source)
    rejection_rows = build_rejection_rows(source)
    guardrail_rows = build_source_guardrail_rows(source, rejection_rows)
    actor_delta_rows = build_actor_delta_contract_guard_rows(source)

    write_csv_rows(paths["input_surface_rows"], input_rows, fieldnames=INPUT_SURFACE_FIELDNAMES)
    write_csv_rows(paths["candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["rejection_rows"], rejection_rows, fieldnames=REJECTION_FIELDNAMES)
    write_csv_rows(paths["source_guardrail_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(
        paths["actor_delta_contract_guard_rows"],
        actor_delta_rows,
        fieldnames=ACTOR_DELTA_GUARD_FIELDNAMES,
    )

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=False,
        required_artifacts_present=required_without_summary_doc,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_delta_rows=actor_delta_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    follow_up = build_follow_up_manifest(summary_path=paths["summary"], output_dir=output, doc_path=paths["doc"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=Path(follow_up_manifest).exists(),
        required_artifacts_present=required_without_summary_doc,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_delta_rows=actor_delta_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_delta_rows=actor_delta_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone_id": milestone,
            "candidate_row_count": len(candidate_rows),
            "rejection_row_count": len(rejection_rows),
            "source_guardrail_row_count": len(guardrail_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=Path(follow_up_manifest).exists(),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_delta_rows=actor_delta_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_delta_rows=actor_delta_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone_id": milestone,
            "candidate_row_count": len(candidate_rows),
            "rejection_row_count": len(rejection_rows),
            "source_guardrail_row_count": len(guardrail_rows),
            "actor_delta_contract_guard_row_count": len(actor_delta_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "input_surface_rows": output_dir / "input_surface_rows.csv",
        "candidate_rows": output_dir / "actor_head_delta_execution_admission_candidate_rows.csv",
        "rejection_rows": output_dir / "actor_head_delta_execution_admission_rejection_rows.csv",
        "source_guardrail_rows": output_dir / "source_guardrail_rows.csv",
        "actor_delta_contract_guard_rows": output_dir / "actor_delta_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_source_artifacts(
    *,
    m2953_dir: Path,
    m2954_audit: Path,
    m2955_design: Path,
    m2916_dir: Path,
    m2917_audit: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2953_summary": m2953_dir / "summary.json",
        "m2953_panel_spec_rows": m2953_dir / "panel_spec_rows.csv",
        "m2953_traceability_rows": m2953_dir / "contract_traceability_rows.csv",
        "m2953_actor_guard_rows": m2953_dir / "actor_contract_guard_rows.csv",
        "m2953_side_effect_guard_rows": m2953_dir / "side_effect_guard_rows.csv",
        "m2953_claim_boundary_rows": m2953_dir / "claim_boundary_rows.csv",
        "m2953_gate_matrix": m2953_dir / "gate_matrix.csv",
        "m2954_audit": m2954_audit,
        "m2955_design": m2955_design,
        "m2916_summary": m2916_dir / "summary.json",
        "m2916_candidate_rows": m2916_dir / "execution_admission_candidate_rows.csv",
        "m2916_rejection_rows": m2916_dir / "execution_admission_rejection_rows.csv",
        "m2916_guardrail_rows": m2916_dir / "guardrail_context_rows.csv",
        "m2916_actor_guard_rows": m2916_dir / "actor_contract_guard_rows.csv",
        "m2916_claim_boundary_rows": m2916_dir / "claim_boundary_rows.csv",
        "m2916_gate_matrix": m2916_dir / "gate_matrix.csv",
        "m2917_audit": m2917_audit,
        "follow_up_manifest": follow_up_manifest,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m2953_summary": read_json(paths["m2953_summary"]) if exists["m2953_summary"] else {},
        "m2953_panel_spec_rows": read_csv_rows(paths["m2953_panel_spec_rows"]),
        "m2953_traceability_rows": read_csv_rows(paths["m2953_traceability_rows"]),
        "m2953_actor_guard_rows": read_csv_rows(paths["m2953_actor_guard_rows"]),
        "m2953_side_effect_guard_rows": read_csv_rows(paths["m2953_side_effect_guard_rows"]),
        "m2953_claim_boundary_rows": read_csv_rows(paths["m2953_claim_boundary_rows"]),
        "m2953_gate_matrix": read_csv_rows(paths["m2953_gate_matrix"]),
        "m2954_audit_text": m2954_audit.read_text(encoding="utf-8") if exists["m2954_audit"] else "",
        "m2955_design_text": m2955_design.read_text(encoding="utf-8") if exists["m2955_design"] else "",
        "m2916_summary": read_json(paths["m2916_summary"]) if exists["m2916_summary"] else {},
        "m2916_candidate_rows": read_csv_rows(paths["m2916_candidate_rows"]),
        "m2916_rejection_rows": read_csv_rows(paths["m2916_rejection_rows"]),
        "m2916_guardrail_rows": read_csv_rows(paths["m2916_guardrail_rows"]),
        "m2916_actor_guard_rows": read_csv_rows(paths["m2916_actor_guard_rows"]),
        "m2916_claim_boundary_rows": read_csv_rows(paths["m2916_claim_boundary_rows"]),
        "m2916_gate_matrix": read_csv_rows(paths["m2916_gate_matrix"]),
        "m2917_audit_text": m2917_audit.read_text(encoding="utf-8") if exists["m2917_audit"] else "",
    }


def build_input_surface_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2953_summary", "actor_head_delta_surface_summary", "M2953 status and false-claim flags"),
        ("m2953_panel_spec_rows", "actor_head_delta_panel_specs", "actor-head delta panel/spec rows"),
        ("m2953_traceability_rows", "actor_head_delta_traceability", "M2951 contract to M2953 panel traceability"),
        ("m2953_actor_guard_rows", "actor_head_delta_actor_guards", "actor 72/action 3 and label visibility guards"),
        ("m2953_side_effect_guard_rows", "actor_head_delta_side_effect_guards", "checkpoint/environment side-effect guards"),
        ("m2953_claim_boundary_rows", "actor_head_delta_claim_boundary", "M2953 claim boundary rows"),
        ("m2953_gate_matrix", "actor_head_delta_gate_matrix", "M2953 gates"),
        ("m2954_audit", "actor_head_delta_result_audit", "M2954 acceptance audit"),
        ("m2955_design", "actor_head_delta_admission_design", "M2955 design authority"),
        ("m2916_summary", "route_a_execution_admission_summary", "M2916 admitted-row summary"),
        ("m2916_candidate_rows", "route_a_execution_admission_candidates", "M2916 row-level candidates"),
        ("m2916_rejection_rows", "route_a_execution_admission_rejections", "M2916 rejected or blocked candidates"),
        ("m2916_guardrail_rows", "route_a_execution_admission_guardrails", "M2916 guardrail rows"),
        ("m2916_actor_guard_rows", "route_a_execution_actor_guards", "M2916 actor guards"),
        ("m2916_claim_boundary_rows", "route_a_execution_claim_boundary", "M2916 claim boundary rows"),
        ("m2916_gate_matrix", "route_a_execution_gate_matrix", "M2916 gates"),
        ("m2917_audit", "route_a_execution_admission_result_audit", "M2917 acceptance audit"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (key, family, role) in enumerate(specs, 1):
        rows.append(
            {
                "input_surface_id": f"m2956-input-surface-{index:04d}",
                "source_family": family,
                "source_artifact": str(source["paths"][key]),
                "source_exists": source["source_exists"][key],
                "row_count": source_row_count(source, key),
                "status_pass_or_present": source_status_pass(source, key),
                "surface_role": role,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def source_row_count(source: dict[str, Any], key: str) -> int:
    if key in {"m2953_summary", "m2954_audit", "m2955_design", "m2916_summary", "m2917_audit"}:
        return 1 if source["source_exists"][key] else 0
    return len(source[key])


def source_status_pass(source: dict[str, Any], key: str) -> bool:
    if key == "m2953_summary":
        return bool(source["m2953_summary"].get("status_pass")) and bool(source["m2953_summary"].get("gate_matrix_pass"))
    if key == "m2954_audit":
        return "accept_m2953_source_diverse_surface_claim_safe_route_to_m2955" in source["m2954_audit_text"]
    if key == "m2955_design":
        return "admit_m2956_actor_head_delta_execution_admission_materialization_preflight" in source["m2955_design_text"]
    if key == "m2916_summary":
        return bool(source["m2916_summary"].get("status_pass")) and bool(source["m2916_summary"].get("gate_matrix_pass"))
    if key == "m2917_audit":
        return "accept_m2916_execution_admission_materialization_claim_safe_route" in source["m2917_audit_text"]
    rows = source[key]
    if key in {
        "m2953_actor_guard_rows",
        "m2953_side_effect_guard_rows",
        "m2953_claim_boundary_rows",
        "m2953_gate_matrix",
        "m2916_actor_guard_rows",
        "m2916_claim_boundary_rows",
        "m2916_gate_matrix",
    }:
        return bool(rows) and all(_bool(row.get("status_pass", True)) for row in rows)
    if key in {
        "m2953_panel_spec_rows",
        "m2953_traceability_rows",
        "m2916_candidate_rows",
        "m2916_rejection_rows",
        "m2916_guardrail_rows",
    }:
        return bool(rows)
    return source["source_exists"].get(key, False)


def build_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    panel_spec_ids = ";".join(row["panel_spec_id"] for row in source["m2953_panel_spec_rows"])
    traceability_count = len(source["m2953_traceability_rows"])
    rows: list[dict[str, Any]] = []
    for source_row in source["m2916_candidate_rows"]:
        if source_row.get("execution_admission_status") != M2916_ADMITTED_STATUS:
            continue
        rows.append(
            {
                "actor_head_delta_candidate_id": f"m2956-actor-head-delta-candidate-{len(rows) + 1:04d}",
                "source_execution_admission_candidate_id": source_row.get("execution_admission_candidate_id", ""),
                "source_milestone": source_row.get("source_milestone", ""),
                "source_artifact": source_row.get("source_artifact", ""),
                "source_row_id": source_row.get("source_row_id", ""),
                "source_family": source_row.get("source_family", ""),
                "task_family": source_row.get("task_family", ""),
                "workload_id": source_row.get("workload_id", ""),
                "task_source_id": source_row.get("task_source_id", ""),
                "profile_name": source_row.get("profile_name", ""),
                "parent_checkpoint_path": source_row.get("checkpoint_path", ""),
                "parent_profile_config_path": source_row.get("profile_config_path", ""),
                "actor_head_delta_panel_spec_ids": panel_spec_ids,
                "actor_head_delta_traceability_count": traceability_count,
                "execution_admission_status": ADMITTED_STATUS,
                "required_follow_up": "M2957 result audit before bounded execution design",
                "environment_reset_admitted": False,
                "environment_rollout_scheduled": False,
                "measured_validation_scheduled": False,
                "training_scheduled": False,
                "dependency_execution_scheduled": False,
                "checkpoint_load_scheduled": False,
                "checkpoint_save_scheduled": False,
                "checkpoint_mutation_scheduled": False,
                "profile_specific_tuning": _bool(source_row.get("profile_specific_tuning")),
                "actor_observation_dim": _int(source_row.get("actor_observation_dim")),
                "actor_action_dim": _int(source_row.get("actor_action_dim")),
                "actor_input_contract_changed": _bool(source_row.get("actor_input_contract_changed")),
                "hidden_oracle_actor_input_required": _bool(source_row.get("hidden_oracle_actor_input_required")),
                "future_target_actor_input_required": _bool(source_row.get("future_target_actor_input_required")),
                "route_labels_actor_visible": _bool(source_row.get("route_labels_actor_visible")),
                "source_labels_actor_visible": _bool(source_row.get("source_labels_actor_visible")),
                "evaluator_labels_actor_visible": False,
                "diagnostic_labels_actor_visible": _bool(source_row.get("diagnostic_labels_actor_visible")),
                "success_progress_labels_actor_visible": _bool(source_row.get("success_progress_labels_actor_visible")),
                "verdict_labels_actor_visible": _bool(source_row.get("verdict_labels_actor_visible")),
                "ordinary_engineering_denominator_allowed_after_audit": _bool(
                    source_row.get("ordinary_engineering_denominator_allowed_after_audit")
                ),
                "validation_denominator_allowed": _bool(source_row.get("validation_denominator_allowed")),
                "paper_denominator_allowed": _bool(source_row.get("paper_denominator_allowed")),
                "high_fidelity_readiness_allowed": _bool(source_row.get("high_fidelity_readiness_allowed")),
                "self_id_claim_allowed": _bool(source_row.get("self_id_claim_allowed")),
                "materialization_only_no_execution": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_rejection_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in source["m2916_candidate_rows"]:
        status = source_row.get("execution_admission_status", "")
        if status == M2916_ADMITTED_STATUS:
            continue
        rejection_type = map_rejection_status(status)
        rows.append(
            {
                "rejection_id": f"m2956-rejection-{len(rows) + 1:04d}",
                "source_execution_admission_candidate_id": source_row.get("execution_admission_candidate_id", ""),
                "source_milestone": source_row.get("source_milestone", ""),
                "source_artifact": source_row.get("source_artifact", ""),
                "source_row_id": source_row.get("source_row_id", ""),
                "rejection_type": rejection_type,
                "rejection_reason": f"source M2916 status {status} is not admitted for actor-head delta materialization",
                "required_follow_up": "repair or stop before any execution if this row is needed",
                "actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def map_rejection_status(status: str) -> str:
    if status == M2916_STALE_STATUS:
        return BLOCKED_STALE_STATUS
    if "source_identity" in status:
        return BLOCKED_SOURCE_STATUS
    if "hidden_oracle" in status:
        return REJECTED_HIDDEN_STATUS
    if "future_target" in status:
        return REJECTED_FUTURE_STATUS
    if "denominator" in status:
        return REJECTED_DENOMINATOR_STATUS
    if "actor_contract" in status:
        return REJECTED_ACTOR_STATUS
    if "checkpoint" in status or "config" in status:
        return REJECTED_CHECKPOINT_STATUS
    if "trace" in status:
        return REJECTED_TRACE_STATUS
    return status.replace("execution_admission_", "actor_head_delta_execution_admission_")


def build_source_guardrail_rows(source: dict[str, Any], rejection_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for guard in source["m2916_guardrail_rows"]:
        rows.append(
            {
                "guardrail_id": f"m2956-source-guardrail-{len(rows) + 1:04d}",
                "guardrail_source": "m2916_guardrail_context_rows",
                "guardrail_family": guard.get("guardrail_family", guard.get("guardrail_type", "m2916_guardrail_context")),
                "source_row_id": guard.get("source_row_id", guard.get("guardrail_id", "")),
                "guardrail_reason": guard.get("guardrail_reason", guard.get("blocked_interpretation", "M2916 guardrail context")),
                "execution_allowed": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    for rejection in rejection_rows:
        rows.append(
            {
                "guardrail_id": f"m2956-source-guardrail-{len(rows) + 1:04d}",
                "guardrail_source": "m2956_rejection_rows",
                "guardrail_family": rejection["rejection_type"],
                "source_row_id": rejection["source_row_id"],
                "guardrail_reason": rejection["rejection_reason"],
                "execution_allowed": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_delta_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel in source["m2953_panel_spec_rows"]:
        rows.append(
            actor_guard(
                "panel_spec",
                panel.get("source_family", ""),
                panel.get("materialization_admitted", ""),
                True,
                _bool(panel.get("evaluator_label_actor_visible")) or _bool(panel.get("verdict_label_actor_visible")),
            )
        )
    for guard in source["m2953_actor_guard_rows"]:
        rows.append(
            actor_guard(
                "m2953_actor_guard",
                guard.get("contract_field", ""),
                guard.get("observed_value", ""),
                guard.get("expected_value", ""),
                _bool(guard.get("actor_visible_allowed")),
                status_pass=_bool(guard.get("status_pass")),
            )
        )
    for guard in source["m2953_side_effect_guard_rows"]:
        rows.append(
            actor_guard(
                "m2953_side_effect_guard",
                guard.get("side_effect", ""),
                guard.get("scheduled_or_run", ""),
                False,
                False,
                status_pass=_bool(guard.get("status_pass")),
            )
        )
    return [
        {
            "guard_id": f"m2956-actor-delta-guard-{index:04d}",
            **row,
        }
        for index, row in enumerate(rows, 1)
    ]


def actor_guard(
    family: str,
    field: str,
    observed: Any,
    expected: Any,
    actor_visible_allowed: bool,
    *,
    status_pass: bool | None = None,
) -> dict[str, Any]:
    if status_pass is None:
        status_pass = str(observed) == str(expected)
    return {
        "guard_family": family,
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": bool(status_pass),
        "actor_visible_allowed": actor_visible_allowed,
        "execution_scheduled": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("actor_head_delta_execution_admission_materialized", "M2956 candidate and rejection rows", required_artifacts_present),
        ("source_guardrails_carried", "M2956 source guardrail rows", required_artifacts_present),
        ("actor_delta_contract_guards_materialized", "M2956 actor delta guard rows", required_artifacts_present),
        ("follow_up_result_audit_registered", "M2957 result-audit manifest", follow_up_manifest_registered),
    ]
    blocked = [
        "candidate_execution",
        "implementation_readiness",
        "checkpoint_mutation",
        "training_or_ppo",
        "validation_result",
        "ranking_or_winner",
        "checkpoint_promotion",
        "repair_success",
        "driver_performance",
        "paper_evidence",
        "current_sim_verdict",
        "finite_window_vs_gru",
        "high_fidelity_validation",
        "full_ideal_driver_completion",
        "level3_self_identification",
    ]
    rows = [
        claim(claim_family, True, made, evidence)
        for claim_family, evidence, made in allowed
    ]
    rows.extend(
        claim(claim_family, False, False, f"future audited evidence before any {claim_family} claim")
        for claim_family in blocked
    )
    return rows


def claim(claim_family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2956_claim_{'allowed' if allowed else 'blocked'}_{claim_family}",
        "claim_family": claim_family,
        "allowed_in_m2956": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_delta_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2956"])]
    source_candidate_count = len(source["m2916_candidate_rows"])
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in source["source_exists"] if key != "follow_up_manifest"),
            "all required inputs present",
            "present",
            "lineage_invalid",
        ),
        ("m2953_status_pass", "lineage", bool(source["m2953_summary"].get("status_pass")), source["m2953_summary"].get("status_pass"), True, "lineage_invalid"),
        (
            "m2954_accepts_m2953",
            "lineage",
            "accept_m2953_source_diverse_surface_claim_safe_route_to_m2955" in source["m2954_audit_text"],
            "M2954 acceptance token",
            "present",
            "lineage_invalid",
        ),
        (
            "m2955_admits_m2956",
            "lineage",
            "admit_m2956_actor_head_delta_execution_admission_materialization_preflight" in source["m2955_design_text"],
            "M2955 admission token",
            "present",
            "lineage_invalid",
        ),
        ("m2916_status_pass", "lineage", bool(source["m2916_summary"].get("status_pass")), source["m2916_summary"].get("status_pass"), True, "lineage_invalid"),
        (
            "m2917_accepts_m2916",
            "lineage",
            "accept_m2916_execution_admission_materialization_claim_safe_route" in source["m2917_audit_text"],
            "M2917 acceptance token",
            "present",
            "lineage_invalid",
        ),
        (
            "input_surfaces_pass",
            "artifact",
            len(input_rows) == 17 and all(_bool(row["status_pass_or_present"]) for row in input_rows),
            len(input_rows),
            "17 passing input rows",
            "metric_artifact",
        ),
        (
            "m2916_rows_accounted",
            "traceability",
            len(candidate_rows) + len(rejection_rows) == source_candidate_count,
            len(candidate_rows) + len(rejection_rows),
            source_candidate_count,
            "metric_artifact",
        ),
        (
            "admitted_rows_materialized",
            "traceability",
            len(candidate_rows) == _int(source["m2916_summary"].get("execution_admission_admitted_count")),
            len(candidate_rows),
            source["m2916_summary"].get("execution_admission_admitted_count"),
            "metric_artifact",
        ),
        (
            "stale_rows_rejected",
            "traceability",
            len(rejection_rows) == _int(source["m2916_summary"].get("execution_admission_blocked_stale_fixed_surface_count")),
            len(rejection_rows),
            source["m2916_summary"].get("execution_admission_blocked_stale_fixed_surface_count"),
            "proof_washout",
        ),
        (
            "guardrails_carried",
            "guardrail",
            len(guardrail_rows) >= len(source["m2916_guardrail_rows"]) + len(rejection_rows),
            len(guardrail_rows),
            f">={len(source['m2916_guardrail_rows']) + len(rejection_rows)}",
            "proof_washout",
        ),
        (
            "actor_delta_contract_pass",
            "contract",
            all(_bool(row["status_pass"]) and not _bool(row["execution_scheduled"]) for row in actor_delta_rows),
            "all actor delta guards pass",
            "all pass and no execution",
            "contract_violation",
        ),
        (
            "candidate_actor_contract_preserved",
            "contract",
            all(candidate_row_actor_safe(row) for row in candidate_rows),
            "all candidate rows actor-safe",
            "all true",
            "contract_violation",
        ),
        (
            "no_execution_scheduled",
            "execution_guardrail",
            all(candidate_row_no_execution(row) for row in candidate_rows),
            "no execution fields true",
            "all false",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims),
            f"blocked={len(blocked_claims)}",
            "blocked claims not made",
            "proof_washout",
        ),
        (
            "follow_up_audit_registered",
            "follow_up",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status, observed, expected, failure) for gate_id, family, status, observed, expected, failure in gates]


def candidate_row_actor_safe(row: dict[str, Any]) -> bool:
    return (
        _int(row["actor_observation_dim"]) == HUMAN_VIEW_OBS_DIM
        and _int(row["actor_action_dim"]) == ACTION_DIM
        and not _bool(row["actor_input_contract_changed"])
        and not _bool(row["hidden_oracle_actor_input_required"])
        and not _bool(row["future_target_actor_input_required"])
        and not _bool(row["route_labels_actor_visible"])
        and not _bool(row["source_labels_actor_visible"])
        and not _bool(row["evaluator_labels_actor_visible"])
        and not _bool(row["diagnostic_labels_actor_visible"])
        and not _bool(row["success_progress_labels_actor_visible"])
        and not _bool(row["verdict_labels_actor_visible"])
    )


def candidate_row_no_execution(row: dict[str, Any]) -> bool:
    execution_fields = [
        "environment_reset_admitted",
        "environment_rollout_scheduled",
        "measured_validation_scheduled",
        "training_scheduled",
        "dependency_execution_scheduled",
        "checkpoint_load_scheduled",
        "checkpoint_save_scheduled",
        "checkpoint_mutation_scheduled",
        "validation_denominator_allowed",
        "paper_denominator_allowed",
        "high_fidelity_readiness_allowed",
        "self_id_claim_allowed",
    ]
    return all(not _bool(row[field]) for field in execution_fields)


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2956_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_delta_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = gate_matrix_pass and required_artifacts_present
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_actor_head_delta_execution_admission_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_actor_head_delta_execution_admission_materialization_preflight_fail"
        ),
        "decision": DECISION_PASS if status_pass else DECISION_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(
            source["source_exists"][key] for key in source["source_exists"] if key != "follow_up_manifest"
        ),
        "m2953_status_pass": bool(source["m2953_summary"].get("status_pass")),
        "m2916_status_pass": bool(source["m2916_summary"].get("status_pass")),
        "input_surface_row_count": len(input_rows),
        "actor_head_delta_execution_admission_candidate_row_count": len(candidate_rows),
        "actor_head_delta_execution_admission_rejection_row_count": len(rejection_rows),
        "source_guardrail_row_count": len(guardrail_rows),
        "m2916_source_guardrail_row_count": len(source["m2916_guardrail_rows"]),
        "m2956_rejection_guardrail_row_count": len(
            [row for row in guardrail_rows if row.get("guardrail_source") == "m2956_rejection_rows"]
        ),
        "actor_delta_contract_guard_row_count": len(actor_delta_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "m2916_source_candidate_row_count": len(source["m2916_candidate_rows"]),
        "m2916_admitted_source_row_count": _int(source["m2916_summary"].get("execution_admission_admitted_count")),
        "m2916_blocked_stale_source_row_count": _int(
            source["m2916_summary"].get("execution_admission_blocked_stale_fixed_surface_count")
        ),
        "actor_head_delta_traceability_row_count": len(source["m2953_traceability_rows"]),
        "actor_head_delta_panel_spec_row_count": len(source["m2953_panel_spec_rows"]),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "future_target_actor_inputs_required": False,
        "evaluator_label_actor_visible": False,
        "verdict_label_actor_visible": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "dependency_build_run": False,
        "adapter_probe_run": False,
        "checkpoint_load_scheduled": False,
        "checkpoint_modification_run": False,
        "checkpoint_save_scheduled": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "implementation_readiness_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_driver_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }


def build_follow_up_manifest(*, summary_path: Path, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
        "status": "pending",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "actor_head_delta_execution_admission_candidate_rows.csv"),
                str(output_dir / "actor_head_delta_execution_admission_rejection_rows.csv"),
                str(output_dir / "source_guardrail_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m2956-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-execution-admission-materialization-preflight.json",
                "experiments/manifests/m2955-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-candidate-execution-admission-design.json",
            ],
            "parent_objective": ["audit M2956 actor-head delta execution-admission materialization"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": ["M2956 materialization must be audited before any bounded execution design"],
            "supersedes": ["direct bounded execution design from unaudited M2956 rows"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2957 must audit M2956 row counts and gates",
            "M2957 must preserve actor 72/action 3 and no hidden/oracle/future-target/evaluator-label actor input",
            "M2957 must not execute reset rollout validation training ranking promotion dependency work adapter probe or external simulation",
            "M2957 must not claim implementation readiness repair success driver performance validation paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run environment reset step rollout replay validation training PPO or private holdout",
            "do not load modify save rank or promote checkpoints",
            "do not treat M2956 materialization rows as repair success or performance evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_execution_admission_materialization_result_audit",
            "evidence_increment": "audits newly materialized actor-head delta execution-admission rows",
            "claim_scope": "Result audit only; no candidate execution validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2956 rows are incomplete",
                "stop if actor or claim boundaries are violated",
            ],
            "fallback_plan": [
                "route to artifact repair if row accounting is incomplete",
                "route to stop or pivot if rows require privileged actor input",
                "admit one bounded execution-design route only after audit acceptance",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2956 materialization completed",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit actor-head delta execution-admission materialization",
            "admission_evidence": ["M2956 materialization preflight completed"],
            "blocked_shortcuts": [
                "no environment execution validation ranking promotion repair-success or performance verdict",
                "no training replay PPO or checkpoint promotion",
                "no hidden oracle future-target evaluator-label progress or verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2957 status queue scoreboard research log and review",
                "one follow-up manifest only if audit selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2957 audit artifact exists",
                "M2957 accepts rejects repairs pivots or stops M2956 materialization",
                "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2957 audits materialized rows only and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2957; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2956 materialization.",
            "negative_result_policy": "If row accounting fails route to repair or stop rather than weakening interpretation standards.",
            "allowed_claims": [
                "M2956 materialization audit",
                "actor and claim boundary preserved",
                "no implementation readiness repair-success driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized actor-head delta execution-admission rows",
            "paper_verdict_delta": "no paper verdict; may admit one bounded execution design or force repair/stop",
            "must_synthesize_if": [
                "M2957 cannot accept reject repair pivot or stop M2956 artifacts",
                "M2957 would claim implementation readiness repair success driver performance paper high-fidelity or self-ID evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2956 actor-head delta execution-admission materialization before any candidate execution validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "audit summarizes M2956 row counts and gates",
            "audit preserves actor and claim boundaries",
            "audit selects exactly one next route or stop state",
            "no execution training ranking validation repair-success performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2957 executes reset rollout replay validation training ranking promotion dependency work",
            "M2957 changes actor input or action contract",
            "M2957 claims implementation readiness driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2957 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M2957 writes a bounded result-audit artifact for M2956 and preserves all actor execution and claim boundaries without execution.",
        "commands": [{"name": "actor_head_delta_execution_admission_result_audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "actor_head_delta_execution_admission_candidate_rows.csv"),
            str(output_dir / "actor_head_delta_execution_admission_rejection_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2956 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Execution-Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status_pass: `{summary['status_pass']}`",
            f"- decision: `{summary['decision']}`",
            f"- input surface rows: `{summary['input_surface_row_count']}`",
            f"- candidate rows: `{summary['actor_head_delta_execution_admission_candidate_row_count']}`",
            f"- rejection rows: `{summary['actor_head_delta_execution_admission_rejection_row_count']}`",
            f"- source guardrail rows: `{summary['source_guardrail_row_count']}`",
            f"- M2916 source guardrail rows: `{summary['m2916_source_guardrail_row_count']}`",
            f"- M2956 rejection guardrail rows: `{summary['m2956_rejection_guardrail_row_count']}`",
            f"- actor delta contract guard rows: `{summary['actor_delta_contract_guard_row_count']}`",
            f"- claim boundary rows: `{summary['claim_boundary_row_count']}`",
            f"- gate matrix rows: `{summary['gate_matrix_row_count']}`",
            f"- gate_matrix_pass: `{summary['gate_matrix_pass']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "M2956 materializes actor-head delta execution-admission rows by binding the accepted M2953 actor-head delta surface to accepted M2916 Route A execution-admission rows. It does not execute a candidate, mutate checkpoints, train, validate, rank, promote, or claim implementation readiness, repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.",
            "",
            "## Boundary",
            "",
            CLAIM_SCOPE,
        ]
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2953-dir", type=Path, default=DEFAULT_M2953_DIR)
    parser.add_argument("--m2954-audit", type=Path, default=DEFAULT_M2954_AUDIT)
    parser.add_argument("--m2955-design", type=Path, default=DEFAULT_M2955_DESIGN)
    parser.add_argument("--m2916-dir", type=Path, default=DEFAULT_M2916_DIR)
    parser.add_argument("--m2917-audit", type=Path, default=DEFAULT_M2917_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = materialize_actor_head_delta_execution_admission(
        m2953_dir=args.m2953_dir,
        m2954_audit=args.m2954_audit,
        m2955_design=args.m2955_design,
        m2916_dir=args.m2916_dir,
        m2917_audit=args.m2917_audit,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={summary['artifacts']['summary']}")


if __name__ == "__main__":
    main()
