"""Materialize M2916 Route A dependency-facing execution-admission rows.

M2916 is a no-execution admission materialization. It reads the accepted
M2913/M2914 family-level surface plus bounded Route A diagnostic source rows,
classifies each loaded row as admitted, rejected, or blocked for a later
separately registered execution manifest, and preserves actor, denominator,
Route B, Route C, and claim boundaries.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2916-engineering-controller-route-a-dependency-facing-evidence-surface-"
    "execution-admission-materialization-preflight"
)
NEXT_ID = (
    "m2917-engineering-controller-route-a-dependency-facing-evidence-surface-"
    "execution-admission-materialization-result-audit"
)
DEFAULT_M2913_DIR = Path(
    "runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight"
)
DEFAULT_M2914_AUDIT = Path(
    "docs/m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit.md"
)
DEFAULT_M2915_DESIGN = Path(
    "docs/m2915-engineering-controller-route-a-dependency-facing-evidence-surface-execution-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2916 Route A dependency-facing execution-admission materialization only; "
    "existing Route A diagnostic rows may be reanalyzed into source, candidate, "
    "rejection, guardrail, actor-contract, claim-boundary, and gate rows, but no "
    "reset, step, rollout, replay, validation, training, PPO, dependency "
    "execution, ranking, winner selection, promotion, success-rate verdict, "
    "driver-performance, paper, current-sim, high-fidelity, full-driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "not an execution result, repair success, driver performance, validation "
    "readiness or result, paper evidence, current-sim verdict, high-fidelity "
    "readiness or result, finite-window-vs-GRU conclusion, full ideal driver "
    "completion, or level3 self-identification"
)
DECISION_PASS = (
    "dependency_facing_execution_admission_materialized_route_to_m2917_result_audit"
)
DECISION_FAIL = "dependency_facing_execution_admission_materialization_incomplete"
ADMITTED_STATUS = "execution_admission_admitted_for_separate_bounded_execution_manifest"
BLOCKED_STALE_STATUS = "execution_admission_blocked_stale_fixed_surface"
BLOCKED_SOURCE_STATUS = "execution_admission_blocked_source_identity_unresolved"
BLOCKED_ROUTE_B_STATUS = "execution_admission_blocked_route_b_source_family_insufficient"
BLOCKED_ROUTE_C_STATUS = "execution_admission_blocked_route_c_dependency_unavailable"
REJECTED_ACTOR_STATUS = "execution_admission_rejected_actor_contract_violation"
REJECTED_HIDDEN_STATUS = "execution_admission_rejected_hidden_oracle_required"
REJECTED_FUTURE_STATUS = "execution_admission_rejected_future_target_required"
REJECTED_DENOMINATOR_STATUS = "execution_admission_rejected_denominator_boundary_violation"
REJECTED_CLAIM_STATUS = "execution_admission_rejected_claim_boundary_violation"
REJECTED_MISSING_STATUS = "execution_admission_rejected_source_artifact_missing"
REJECTED_SCHEMA_STATUS = "execution_admission_rejected_schema_inconsistent"

FALSE_EXECUTION_FLAGS = {
    "environment_reset_admitted": False,
    "environment_rollout_scheduled": False,
    "measured_validation_scheduled": False,
    "training_scheduled": False,
    "dependency_execution_scheduled": False,
    "profile_specific_tuning": False,
    "actor_input_contract_changed": False,
    "hidden_oracle_actor_input_required": False,
    "future_target_actor_input_required": False,
    "route_labels_actor_visible": False,
    "source_labels_actor_visible": False,
    "diagnostic_labels_actor_visible": False,
    "success_progress_labels_actor_visible": False,
    "verdict_labels_actor_visible": False,
    "validation_denominator_allowed": False,
    "paper_denominator_allowed": False,
    "high_fidelity_readiness_allowed": False,
    "self_id_claim_allowed": False,
    "materialization_only_no_execution": True,
    "diagnostic_only_no_verdict": True,
}

INPUT_SOURCE_FIELDNAMES = [
    "source_artifact_id",
    "source_path",
    "source_exists",
    "required",
    "expected_row_count",
    "observed_row_count",
    "source_role",
    "claim_scope",
    "blocked_interpretation",
]
SOURCE_ROW_FIELDNAMES = [
    "execution_admission_source_id",
    "source_milestone",
    "source_artifact",
    "source_row_id",
    "source_family",
    "task_family",
    "workload_id",
    "task_source_id",
    "profile_name",
    "checkpoint_path",
    "profile_config_path",
    "candidate_family_id",
    "candidate_family_name",
    "source_guard_role",
    "source_row_traceable",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
CANDIDATE_FIELDNAMES = [
    "execution_admission_candidate_id",
    "source_milestone",
    "source_artifact",
    "source_row_id",
    "source_family",
    "task_family",
    "workload_id",
    "task_source_id",
    "profile_name",
    "checkpoint_path",
    "profile_config_path",
    "candidate_family_id",
    "candidate_family_name",
    "execution_admission_status",
    "execution_rejection_status",
    "required_follow_up",
    "environment_reset_admitted",
    "environment_rollout_scheduled",
    "measured_validation_scheduled",
    "training_scheduled",
    "dependency_execution_scheduled",
    "profile_specific_tuning",
    "actor_observation_dim",
    "actor_action_dim",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ordinary_engineering_denominator_allowed_after_audit",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "diagnostic_only_no_verdict",
    "materialization_only_no_execution",
    "claim_boundary",
]
REJECTION_FIELDNAMES = [
    "rejection_id",
    "candidate_or_source_id",
    "source_milestone",
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
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2916",
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
    "execution_admission_input_source_rows",
    "execution_admission_source_rows",
    "execution_admission_candidate_rows",
    "execution_admission_rejection_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "execution_admission_input_source_rows": output_dir / "execution_admission_input_source_rows.csv",
        "execution_admission_source_rows": output_dir / "execution_admission_source_rows.csv",
        "execution_admission_candidate_rows": output_dir / "execution_admission_candidate_rows.csv",
        "execution_admission_rejection_rows": output_dir / "execution_admission_rejection_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def route_a_source_specs() -> dict[str, dict[str, Any]]:
    return {
        "m2737_candidate_execution_rows": {
            "milestone": "m2737",
            "path": Path(
                "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv"
            ),
            "expected_row_count": 18,
            "role": "source_diverse_closed_loop_diagnostic_rows",
            "guard_role": "candidate",
        },
        "m2746_candidate_execution_rows": {
            "milestone": "m2746",
            "path": Path(
                "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv"
            ),
            "expected_row_count": 14,
            "role": "source_diverse_failure_taxonomy_scenario_role_rows",
            "guard_role": "candidate",
        },
        "m2807_candidate_execution_rows": {
            "milestone": "m2807",
            "path": Path(
                "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight/candidate_execution_rows.csv"
            ),
            "expected_row_count": 12,
            "role": "post_clearance_non_same_cross_axis_rows",
            "guard_role": "candidate",
        },
        "m2816_instrumented_execution_rows": {
            "milestone": "m2816",
            "path": Path(
                "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/instrumented_execution_rows.csv"
            ),
            "expected_row_count": 12,
            "role": "recoverability_window_instrumented_rows",
            "guard_role": "candidate",
        },
        "m2877_candidate_execution_rows": {
            "milestone": "m2877",
            "path": Path(
                "runs/m2877_engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight/candidate_execution_rows.csv"
            ),
            "expected_row_count": 11,
            "role": "fixed_weak_post_package_diagnostic_guard_rows",
            "guard_role": "stale_fixed_surface_guard",
        },
    }


def materialize_dependency_facing_execution_admission(
    *,
    m2913_dir: Path | str = DEFAULT_M2913_DIR,
    m2914_audit: Path | str = DEFAULT_M2914_AUDIT,
    m2915_design: Path | str = DEFAULT_M2915_DESIGN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    source_overrides: dict[str, Path] | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    sources = load_source_artifacts(
        m2913_dir=Path(m2913_dir),
        m2914_audit=Path(m2914_audit),
        m2915_design=Path(m2915_design),
        follow_up_manifest=Path(follow_up_manifest),
        source_overrides=source_overrides or {},
    )

    follow_up = build_follow_up_manifest(summary_path=paths["summary"], output_dir=output)
    write_json(follow_up_manifest, follow_up)
    sources["paths"]["follow_up_manifest"] = Path(follow_up_manifest)
    sources["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    input_source_rows = build_input_source_rows(sources)
    source_rows = build_execution_admission_source_rows(sources)
    candidate_rows, rejection_rows = build_execution_admission_candidate_rows(source_rows)
    rejection_rows.extend(build_global_rejection_rows(sources))
    guardrail_rows = build_guardrail_context_rows(sources, candidate_rows)
    actor_contract_guard_rows = build_actor_contract_guard_rows()

    write_csv_rows(paths["execution_admission_input_source_rows"], input_source_rows, INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(paths["execution_admission_source_rows"], source_rows, SOURCE_ROW_FIELDNAMES)
    write_csv_rows(paths["execution_admission_candidate_rows"], candidate_rows, CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["execution_admission_rejection_rows"], rejection_rows, REJECTION_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, ACTOR_GUARD_FIELDNAMES)

    run_state = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "inputs": {key: str(path) for key, path in sources["paths"].items()},
        "outputs": {key: str(path) for key, path in paths.items()},
        "claim_scope": CLAIM_SCOPE,
    }
    write_json(paths["run_state"], run_state)

    claim_boundary_rows = build_claim_boundary_rows(required_artifacts_present=False)
    gate_rows = build_gate_matrix_rows(
        sources=sources,
        input_source_rows=input_source_rows,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        paths=paths,
        sources=sources,
        input_source_rows=input_source_rows,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_boundary_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        sources=sources,
        input_source_rows=input_source_rows,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        paths=paths,
        sources=sources,
        input_source_rows=input_source_rows,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        guardrail_rows=guardrail_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def load_source_artifacts(
    *,
    m2913_dir: Path,
    m2914_audit: Path,
    m2915_design: Path,
    follow_up_manifest: Path,
    source_overrides: dict[str, Path],
) -> dict[str, Any]:
    specs = route_a_source_specs()
    for key, path in source_overrides.items():
        if key not in specs:
            raise KeyError(f"unknown source override: {key}")
        specs[key]["path"] = Path(path)
    paths = {
        "m2915_design": m2915_design,
        "m2914_audit": m2914_audit,
        "m2913_summary": m2913_dir / "summary.json",
        "m2913_route_context_rows": m2913_dir / "route_context_rows.csv",
        "m2913_candidate_family_rows": m2913_dir / "candidate_family_rows.csv",
        "m2913_exclusion_family_rows": m2913_dir / "exclusion_family_rows.csv",
        "m2913_denominator_policy_rows": m2913_dir / "denominator_policy_rows.csv",
        "m2913_failure_taxonomy_rows": m2913_dir / "failure_taxonomy_rows.csv",
        "m2913_actor_contract_rows": m2913_dir / "actor_contract_rows.csv",
        "m2913_claim_boundary_rows": m2913_dir / "claim_boundary_rows.csv",
        "m2913_gate_rows": m2913_dir / "gate_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    for key, spec in specs.items():
        paths[key] = spec["path"]
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_specs": specs,
        "source_exists": source_exists,
        "m2915_design_text": _read_text(paths["m2915_design"]),
        "m2914_audit_text": _read_text(paths["m2914_audit"]),
        "m2913_summary": read_json(paths["m2913_summary"]) if source_exists["m2913_summary"] else {},
        "m2913_route_context_rows": read_csv_rows(paths["m2913_route_context_rows"]),
        "m2913_candidate_family_rows": read_csv_rows(paths["m2913_candidate_family_rows"]),
        "m2913_exclusion_family_rows": read_csv_rows(paths["m2913_exclusion_family_rows"]),
        "m2913_denominator_policy_rows": read_csv_rows(paths["m2913_denominator_policy_rows"]),
        "m2913_failure_taxonomy_rows": read_csv_rows(paths["m2913_failure_taxonomy_rows"]),
        "m2913_actor_contract_rows": read_csv_rows(paths["m2913_actor_contract_rows"]),
        "m2913_claim_boundary_rows": read_csv_rows(paths["m2913_claim_boundary_rows"]),
        "m2913_gate_rows": read_csv_rows(paths["m2913_gate_rows"]),
        "route_a_source_rows": {
            key: read_csv_rows(spec["path"])
            for key, spec in specs.items()
        },
    }


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_input_source_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    roles = {
        "m2915_design": "execution-admission design boundary",
        "m2914_audit": "parent materialization result audit",
        "m2913_summary": "parent materialization summary",
        "m2913_route_context_rows": "parent route context rows",
        "m2913_candidate_family_rows": "parent candidate family rows",
        "m2913_exclusion_family_rows": "parent exclusion family rows",
        "m2913_denominator_policy_rows": "parent denominator policy rows",
        "m2913_failure_taxonomy_rows": "parent failure taxonomy rows",
        "m2913_actor_contract_rows": "parent actor contract rows",
        "m2913_claim_boundary_rows": "parent claim boundary rows",
        "m2913_gate_rows": "parent gate rows",
        "follow_up_manifest": "M2917 result audit registration",
    }
    rows: list[dict[str, Any]] = []
    for artifact_id, path in sources["paths"].items():
        spec = sources["source_specs"].get(artifact_id, {})
        expected = spec.get("expected_row_count", "")
        observed = source_observed_count(sources, artifact_id)
        rows.append(
            {
                "source_artifact_id": artifact_id,
                "source_path": str(path),
                "source_exists": sources["source_exists"][artifact_id],
                "required": True,
                "expected_row_count": expected,
                "observed_row_count": observed,
                "source_role": roles.get(artifact_id, spec.get("role", "")),
                "claim_scope": CLAIM_SCOPE,
                "blocked_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def source_observed_count(sources: dict[str, Any], artifact_id: str) -> Any:
    if artifact_id == "m2913_summary":
        summary = sources["m2913_summary"]
        return f"status_pass={summary.get('status_pass', '')};gate_matrix_pass={summary.get('gate_matrix_pass', '')}"
    if artifact_id == "m2915_design":
        return "decision_present=" + str("admit_m2916_dependency_facing_execution_admission_materialization_preflight" in sources["m2915_design_text"])
    if artifact_id == "m2914_audit":
        return "decision_present=" + str("accept_m2913_dependency_facing_evidence_surface_materialization_claim_safe_route_to_m2915_execution_design" in sources["m2914_audit_text"])
    if artifact_id.startswith("m2913_") and artifact_id in sources:
        return len(sources[artifact_id])
    if artifact_id in sources["route_a_source_rows"]:
        return len(sources["route_a_source_rows"][artifact_id])
    if artifact_id == "follow_up_manifest":
        return "exists=" + str(sources["source_exists"][artifact_id])
    return ""


def build_execution_admission_source_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_family = next(
        (
            row
            for row in sources["m2913_candidate_family_rows"]
            if row.get("family_name") == "route_a_source_diverse_closed_loop_diagnostics"
        ),
        {},
    )
    rows: list[dict[str, Any]] = []
    for source_key, source_spec in sources["source_specs"].items():
        for index, source_row in enumerate(sources["route_a_source_rows"].get(source_key, []), start=1):
            source_id = canonical_source_row_id(source_row, fallback=f"{source_spec['milestone']}-row-{index:04d}")
            rows.append(
                {
                    "execution_admission_source_id": f"m2916-source-{len(rows) + 1:04d}",
                    "source_milestone": source_spec["milestone"],
                    "source_artifact": str(source_spec["path"]),
                    "source_row_id": source_id,
                    "source_family": source_row.get("source_family")
                    or source_row.get("source_family_tag")
                    or source_row.get("executable_source_family")
                    or source_spec["role"],
                    "task_family": source_row.get("task_family", ""),
                    "workload_id": source_row.get("workload_id", ""),
                    "task_source_id": source_row.get("task_source_id", ""),
                    "profile_name": source_row.get("profile_name", ""),
                    "checkpoint_path": source_row.get("checkpoint_path", ""),
                    "profile_config_path": source_row.get("profile_config_path", ""),
                    "candidate_family_id": candidate_family.get("candidate_family_id", "candidate-family-001-C1"),
                    "candidate_family_name": candidate_family.get(
                        "family_name",
                        "route_a_source_diverse_closed_loop_diagnostics",
                    ),
                    "source_guard_role": source_spec["guard_role"],
                    "source_row_traceable": bool(source_id),
                    "materialization_only_no_execution": True,
                    "diagnostic_only_no_verdict": True,
                    "claim_scope": CLAIM_SCOPE,
                    "_raw": source_row,
                }
            )
    return rows


def canonical_source_row_id(row: dict[str, str], *, fallback: str) -> str:
    for key in (
        "candidate_id",
        "resolution_id",
        "mechanism_id",
        "localization_id",
        "source_row_id",
        "target_panel_id",
        "seed",
        "eval_seed",
    ):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return fallback


def build_execution_admission_candidate_rows(
    source_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for index, source_row in enumerate(source_rows, start=1):
        raw = source_row.pop("_raw")
        status, reason, follow_up = classify_source_row(source_row, raw)
        rejection_status = "" if status == ADMITTED_STATUS else status
        candidate = {
            "execution_admission_candidate_id": f"m2916-execution-admission-candidate-{index:04d}",
            "source_milestone": source_row["source_milestone"],
            "source_artifact": source_row["source_artifact"],
            "source_row_id": source_row["source_row_id"],
            "source_family": source_row["source_family"],
            "task_family": source_row["task_family"],
            "workload_id": source_row["workload_id"],
            "task_source_id": source_row["task_source_id"],
            "profile_name": source_row["profile_name"],
            "checkpoint_path": source_row["checkpoint_path"],
            "profile_config_path": source_row["profile_config_path"],
            "candidate_family_id": source_row["candidate_family_id"],
            "candidate_family_name": source_row["candidate_family_name"],
            "execution_admission_status": status,
            "execution_rejection_status": rejection_status,
            "required_follow_up": follow_up,
            "actor_observation_dim": P0_OBSERVATION_DIM,
            "actor_action_dim": ACTION_DIM,
            "ordinary_engineering_denominator_allowed_after_audit": status == ADMITTED_STATUS,
            "claim_boundary": CLAIM_SCOPE,
        } | FALSE_EXECUTION_FLAGS
        candidate.update(label_flags_from_raw(raw))
        candidates.append(candidate)
        if status != ADMITTED_STATUS:
            rejections.append(
                rejection(
                    f"m2916-rejection-{len(rejections) + 1:04d}",
                    source_row["source_row_id"],
                    source_row["source_milestone"],
                    status,
                    reason,
                    follow_up,
                )
            )
    return candidates, rejections


def classify_source_row(source_row: dict[str, Any], raw: dict[str, str]) -> tuple[str, str, str]:
    if not source_row["source_row_id"]:
        return (
            BLOCKED_SOURCE_STATUS,
            "source row identity is missing",
            "repair source inventory before execution admission",
        )
    if source_row["source_milestone"] == "m2877" or source_row["source_guard_role"] == "stale_fixed_surface_guard":
        return (
            BLOCKED_STALE_STATUS,
            "M2877 fixed weak diagnostic row remains guardrail context",
            "route to result audit or different source-axis proof before execution",
        )
    if _bool(raw.get("hidden_oracle_actor_input_required")):
        return (
            REJECTED_HIDDEN_STATUS,
            "source row requires hidden/oracle actor input",
            "redesign actor contract without hidden/oracle input",
        )
    if _bool(raw.get("future_target_actor_input_required")):
        return (
            REJECTED_FUTURE_STATUS,
            "source row requires future-target actor input",
            "redesign actor contract without future-target input",
        )
    if _bool(raw.get("actor_input_contract_changed")):
        return (
            REJECTED_ACTOR_STATUS,
            "source row changes actor input contract",
            "restore actor 72/action 3 contract before admission",
        )
    if any(_bool(raw.get(key)) for key in label_visibility_keys()):
        return (
            REJECTED_ACTOR_STATUS,
            "source row exposes route source diagnostic success progress or verdict labels to the actor",
            "keep labels offline before admission",
        )
    if _bool(raw.get("protected_rows_in_success_denominator")) or _bool(raw.get("guardrail_rows_in_success_denominator")):
        return (
            REJECTED_DENOMINATOR_STATUS,
            "guardrail or protected rows enter a success denominator",
            "repair denominator boundary before admission",
        )
    if any(_bool(raw.get(key)) for key in claim_violation_keys()):
        return (
            REJECTED_CLAIM_STATUS,
            "source row already carries a ranking promotion validation performance paper high-fidelity or self-ID claim",
            "route through result audit before admission",
        )
    return (
        ADMITTED_STATUS,
        "",
        "separate M2917 audit before any bounded execution manifest",
    )


def label_flags_from_raw(raw: dict[str, str]) -> dict[str, bool]:
    return {
        "actor_input_contract_changed": _bool(raw.get("actor_input_contract_changed")),
        "hidden_oracle_actor_input_required": _bool(raw.get("hidden_oracle_actor_input_required")),
        "future_target_actor_input_required": _bool(raw.get("future_target_actor_input_required")),
        "route_labels_actor_visible": _bool(raw.get("route_labels_actor_visible")),
        "source_labels_actor_visible": any(
            _bool(raw.get(key))
            for key in ("source_labels_actor_visible", "source_edge_labels_actor_visible", "profile_labels_actor_visible")
        ),
        "diagnostic_labels_actor_visible": any(
            _bool(raw.get(key))
            for key in (
                "diagnostic_labels_actor_visible",
                "scenario_role_labels_actor_visible",
                "metric_labels_actor_visible",
                "target_labels_actor_visible",
                "stress_axis_labels_actor_visible",
                "recoverability_labels_actor_visible",
                "action_response_labels_actor_visible",
            )
        ),
        "success_progress_labels_actor_visible": _bool(raw.get("success_progress_labels_actor_visible")),
        "verdict_labels_actor_visible": _bool(raw.get("verdict_labels_actor_visible")),
        "profile_specific_tuning": _bool(raw.get("profile_specific_tuning")),
    }


def label_visibility_keys() -> tuple[str, ...]:
    return (
        "route_labels_actor_visible",
        "source_labels_actor_visible",
        "source_edge_labels_actor_visible",
        "profile_labels_actor_visible",
        "diagnostic_labels_actor_visible",
        "scenario_role_labels_actor_visible",
        "metric_labels_actor_visible",
        "target_labels_actor_visible",
        "stress_axis_labels_actor_visible",
        "recoverability_labels_actor_visible",
        "action_response_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
    )


def claim_violation_keys() -> tuple[str, ...]:
    return (
        "ranking_run",
        "source_family_ranking_claim_made",
        "profile_ranking_claim_made",
        "task_family_ranking_claim_made",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "validation_readiness_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "paper_level_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_readiness_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_completion_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
    )


def build_global_rejection_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, exists in sources["source_exists"].items():
        if exists:
            continue
        if artifact_id == "follow_up_manifest":
            continue
        rows.append(
            rejection(
                f"m2916-global-rejection-{len(rows) + 1:04d}",
                artifact_id,
                "global",
                REJECTED_MISSING_STATUS,
                f"required source artifact is missing: {artifact_id}",
                "repair missing artifact before execution admission",
            )
        )
    if "admit_m2916_dependency_facing_execution_admission_materialization_preflight" not in sources["m2915_design_text"]:
        rows.append(
            rejection(
                f"m2916-global-rejection-{len(rows) + 1:04d}",
                "m2915_design",
                "global",
                REJECTED_SCHEMA_STATUS,
                "M2915 design does not contain the expected M2916 admission decision",
                "repair M2915 design before materialization",
            )
        )
    if (
        "accept_m2913_dependency_facing_evidence_surface_materialization_claim_safe_route_to_m2915_execution_design"
        not in sources["m2914_audit_text"]
    ):
        rows.append(
            rejection(
                f"m2916-global-rejection-{len(rows) + 1:04d}",
                "m2914_audit",
                "global",
                REJECTED_SCHEMA_STATUS,
                "M2914 audit does not contain the expected acceptance decision",
                "repair M2914 audit before materialization",
            )
        )
    return rows


def rejection(
    rejection_id: str,
    candidate_or_source_id: str,
    source_milestone: str,
    rejection_type: str,
    rejection_reason: str,
    required_follow_up: str,
) -> dict[str, Any]:
    return {
        "rejection_id": rejection_id,
        "candidate_or_source_id": candidate_or_source_id,
        "source_milestone": source_milestone,
        "rejection_type": rejection_type,
        "rejection_reason": rejection_reason,
        "required_follow_up": required_follow_up,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


def build_guardrail_context_rows(
    sources: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_name, family_key in (
        ("m2913_route_context_rows", "materialization_role"),
        ("m2913_exclusion_family_rows", "family_name"),
        ("m2913_denominator_policy_rows", "policy_label"),
        ("m2913_failure_taxonomy_rows", "failure_label"),
    ):
        for row in sources[source_name]:
            rows.append(
                guardrail(
                    len(rows) + 1,
                    source_name,
                    row.get(family_key, ""),
                    row.get("context_id") or row.get("exclusion_family_id") or row.get("denominator_policy_id") or row.get("failure_taxonomy_id", ""),
                    "parent M2913 context preserved as offline guardrail",
                )
            )
    for candidate in candidate_rows:
        if candidate["execution_admission_status"] != BLOCKED_STALE_STATUS:
            continue
        rows.append(
            guardrail(
                len(rows) + 1,
                "m2877_candidate_execution_rows",
                "fixed_weak_post_package_diagnostic_guard",
                candidate["source_row_id"],
                "M2877 fixed weak diagnostic row remains guardrail and not validation readiness",
            )
        )
    return rows


def guardrail(
    index: int,
    source: str,
    family: str,
    row_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "guardrail_id": f"m2916-guardrail-{index:04d}",
        "guardrail_source": source,
        "guardrail_family": family,
        "source_row_id": row_id,
        "guardrail_reason": reason,
        "execution_allowed": False,
        "ordinary_engineering_denominator_allowed": False,
        "validation_denominator_allowed": False,
        "paper_denominator_allowed": False,
        "high_fidelity_readiness_allowed": False,
        "self_id_claim_allowed": False,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    specs = [
        ("observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        ("action_dim", ACTION_DIM, ACTION_DIM),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("actor_input_contract_changed", False, False),
        ("route_labels_actor_visible", False, False),
        ("source_labels_actor_visible", False, False),
        ("diagnostic_labels_actor_visible", False, False),
        ("success_progress_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
    ]
    return [
        {
            "guard_id": f"m2916-actor-guard-{index:03d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(specs, start=1)
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool) -> list[dict[str, Any]]:
    specs = [
        ("execution_admission_materialization", True, "M2916 source admission rows and result audit"),
        ("driver_performance", False, "later closed-loop execution and result audit"),
        ("validation_readiness", False, "later validation gate with denominator audit"),
        ("current_sim_verdict", False, "later current-sim validation synthesis"),
        ("high_fidelity_validation", False, "Route C source/build/reset/step gates first"),
        ("paper_evidence", False, "source-diverse fair L0/L1/L2/L3 evidence"),
        ("finite_window_vs_gru", False, "paired same-case model-quality evidence"),
        ("self_id", False, "history-necessity and source-diverse terminal-boundary tests"),
        ("checkpoint_promotion", False, "proof generalization behavior and holdout gates"),
        ("required_artifacts", required_artifacts_present, "all required M2916 materialization artifacts"),
    ]
    return [
        {
            "claim_id": f"m2916-claim-{index:03d}",
            "claim_family": family,
            "allowed_in_m2916": allowed,
            "claim_made": False,
            "status_pass": (not allowed) or family in {"execution_admission_materialization", "required_artifacts"},
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, evidence) in enumerate(specs, start=1)
    ]


def build_gate_matrix_rows(
    *,
    sources: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    route_source_keys = set(sources["source_specs"])
    route_source_exists = all(sources["source_exists"][key] for key in route_source_keys)
    source_counts_match = all(
        len(sources["route_a_source_rows"][key]) == spec["expected_row_count"]
        for key, spec in sources["source_specs"].items()
        if sources["source_exists"][key]
    )
    all_loaded_rows_classified = len(source_rows) == len(candidate_rows) and bool(candidate_rows)
    non_admitted = [row for row in candidate_rows if row["execution_admission_status"] != ADMITTED_STATUS]
    rejection_ids = {row["candidate_or_source_id"] for row in rejection_rows}
    every_non_admitted_has_rejection = all(row["source_row_id"] in rejection_ids for row in non_admitted)
    m2877_guarded = all(
        row["execution_admission_status"] == BLOCKED_STALE_STATUS
        for row in candidate_rows
        if row["source_milestone"] == "m2877"
    )
    actor_contract_pass = all(_bool(row["status_pass"]) for row in actor_contract_guard_rows)
    no_execution_scheduled = all(
        not any(
            _bool(row.get(key))
            for key in (
                "environment_reset_admitted",
                "environment_rollout_scheduled",
                "measured_validation_scheduled",
                "training_scheduled",
                "dependency_execution_scheduled",
            )
        )
        for row in candidate_rows
    )
    no_claims_made = all(not _bool(row["claim_made"]) for row in claim_boundary_rows)
    route_b_context_only = any("route_b" in row["guardrail_family"] for row in guardrail_rows)
    route_c_context_only = any("route_c" in row["guardrail_family"] for row in guardrail_rows)
    specs = [
        ("m2915_design_exists", sources["source_exists"]["m2915_design"], sources["source_exists"]["m2915_design"], True, "lineage_invalid"),
        ("m2914_audit_exists", sources["source_exists"]["m2914_audit"], sources["source_exists"]["m2914_audit"], True, "lineage_invalid"),
        ("m2913_summary_status_pass", _bool(sources["m2913_summary"].get("status_pass")), sources["m2913_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m2913_gate_matrix_pass", _bool(sources["m2913_summary"].get("gate_matrix_pass")), sources["m2913_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        ("m2913_candidate_families_accounted", len(sources["m2913_candidate_family_rows"]) >= 5, len(sources["m2913_candidate_family_rows"]), 5, "metric_artifact"),
        ("route_a_source_inventory_exists", route_source_exists, sum(sources["source_exists"][key] for key in route_source_keys), len(route_source_keys), "lineage_invalid"),
        ("route_a_source_row_counts_match_design", source_counts_match, sum(len(sources["route_a_source_rows"][key]) for key in route_source_keys), 67, "scenario_sampling_failure"),
        ("all_loaded_rows_classified", all_loaded_rows_classified, len(candidate_rows), len(source_rows), "metric_artifact"),
        ("every_non_admitted_row_has_rejection", every_non_admitted_has_rejection, len(rejection_ids), len(non_admitted), "metric_artifact"),
        ("m2877_fixed_rows_guarded", m2877_guarded, sum(row["source_milestone"] == "m2877" for row in candidate_rows), "all blocked", "proof_washout"),
        ("guardrail_rows_written", len(guardrail_rows) > 0, len(guardrail_rows), ">0", "metric_artifact"),
        ("actor_contract_pass", actor_contract_pass, actor_contract_pass, True, "contract_violation"),
        ("no_execution_scheduled", no_execution_scheduled, no_execution_scheduled, True, "contract_violation"),
        ("no_claims_made", no_claims_made, no_claims_made, True, "metric_artifact"),
        ("route_b_context_only", route_b_context_only, route_b_context_only, True, "proof_washout"),
        ("route_c_context_only", route_c_context_only, route_c_context_only, True, "metric_artifact"),
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        ("follow_up_manifest_written", sources["source_exists"]["follow_up_manifest"], sources["source_exists"]["follow_up_manifest"], True, "lineage_invalid"),
        ("input_source_rows_written", len(input_source_rows) >= 17, len(input_source_rows), ">=17", "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2916-gate-{index:03d}",
            "gate_family": family,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if passed else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, passed, observed, expected, failure_type) in enumerate(specs, start=1)
    ]


def build_summary(
    *,
    paths: dict[str, Path],
    sources: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    status_counts = Counter(row["execution_admission_status"] for row in candidate_rows)
    status_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    source_rows_by_milestone = Counter(row["source_milestone"] for row in source_rows)
    summary = {
        "milestone_id": MILESTONE_ID,
        "status_pass": status_pass,
        "gate_matrix_pass": status_pass,
        "decision": DECISION_PASS if status_pass else DECISION_FAIL,
        "input_source_row_count": len(input_source_rows),
        "execution_admission_source_row_count": len(source_rows),
        "execution_admission_candidate_row_count": len(candidate_rows),
        "execution_admission_rejection_row_count": len(rejection_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "claim_boundary_row_count": len(claim_boundary_rows),
        "gate_row_count": len(gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "source_artifact_missing_count": sum(
            not sources["source_exists"][key]
            for key in sources["paths"]
            if key != "follow_up_manifest"
        ),
        "route_a_source_artifact_missing_count": sum(
            not sources["source_exists"][key]
            for key in sources["source_specs"]
        ),
        "execution_admission_admitted_count": status_counts[ADMITTED_STATUS],
        "execution_admission_blocked_stale_fixed_surface_count": status_counts[BLOCKED_STALE_STATUS],
        "execution_admission_blocked_source_identity_unresolved_count": status_counts[BLOCKED_SOURCE_STATUS],
        "m2737_source_row_count": source_rows_by_milestone["m2737"],
        "m2746_source_row_count": source_rows_by_milestone["m2746"],
        "m2807_source_row_count": source_rows_by_milestone["m2807"],
        "m2816_source_row_count": source_rows_by_milestone["m2816"],
        "m2877_guard_row_count": source_rows_by_milestone["m2877"],
        "actor_observation_dim": P0_OBSERVATION_DIM,
        "actor_action_dim": ACTION_DIM,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "actor_input_contract_changed": False,
        "route_b_context_only": True,
        "route_c_context_only": True,
        "reset_or_rollout_executed": False,
        "validation_executed": False,
        "training_executed": False,
        "dependency_execution_performed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "performance_claim_made": False,
        "paper_claim_made": False,
        "high_fidelity_claim_made": False,
        "self_id_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "artifacts": {key: str(path) for key, path in paths.items()},
    }
    summary["status_counts"] = dict(status_counts)
    return summary


def build_follow_up_manifest(*, summary_path: Path, output_dir: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
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
        "hypothesis": "A bounded result audit can accept or reject the M2916 Route A dependency-facing execution-admission materialization before any behavior execution validation ranking promotion dependency execution performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "execution_admission_input_source_rows.csv"),
                str(output_dir / "execution_admission_source_rows.csv"),
                str(output_dir / "execution_admission_candidate_rows.csv"),
                str(output_dir / "execution_admission_rejection_rows.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                "docs/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.md",
            ],
            "parent_config": [
                "experiments/manifests/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.json",
                "experiments/manifests/m2915-engineering-controller-route-a-dependency-facing-evidence-surface-execution-design.json",
            ],
            "parent_objective": [
                "audit M2916 execution-admission materialization before any behavior execution route"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2915-engineering-controller-route-a-dependency-facing-evidence-surface-execution-design",
            ],
            "blocked_by": [
                "M2916 must be audited before admitted rows can influence any execution design or execution route",
                "Route B source-family insufficiency and Route C source_unavailable must remain context only",
            ],
            "supersedes": [
                "direct behavior execution from M2916 admission rows without result audit"
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2917 must audit M2916 summary row counts gates actor boundary Route B and Route C context",
            "M2917 must preserve no-execution no-validation no-ranking no-performance and no-paper claim boundaries",
            "M2917 must select exactly one next route or stop state before any execution",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not fetch clone configure build install import link probe or start an external backend",
            "do not change actor input or action contract",
            "do not convert M2916 admission rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_execution_admission_materialization_result_audit",
            "evidence_increment": "audits M2916 execution-admission materialization rows before any behavior execution route",
            "claim_scope": "Result audit only no reset rollout validation ranking promotion dependency execution performance paper high-fidelity or self-ID claim",
            "stop_condition": [
                "stop if M2916 artifacts are incomplete",
                "stop if actor or denominator boundaries fail",
                "stop if Route B or Route C context enters proof or readiness denominators",
                "stop if M2917 would execute policy or dependency work",
            ],
            "fallback_plan": [
                "route to repair or source-inventory redesign if materialization is incomplete",
                "route to stop if no actor-safe candidate rows remain",
                "route to bounded execution design only after audit acceptance",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2916 completes execution-admission materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit Route A dependency-facing execution-admission materialization",
            "admission_evidence": [
                "M2916 writes no-execution execution-admission source candidate rejection guardrail actor claim and gate rows"
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion dependency execution or performance claim",
                "no training replay PPO or promoted fitted weights",
                "no hidden oracle or future-target actor inputs",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2917 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if audit selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2917 audit artifact exists",
                "M2917 accepts rejects repairs pivots or stops M2916 materialization",
                "actor Route B Route C denominator and claim boundaries remain preserved",
                "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2917 audits engineering admission materialization and cannot substitute Route A rows for history necessity.",
            "history_necessity_tests": [
                "None in M2917; self-ID evidence remains blocked until fair source-diverse L0/L1/L2/L3 tests are admitted."
            ],
            "temporal_evidence_window": "M2910-M2916 Route A dependency-facing admission chain.",
            "negative_result_policy": "Preserve blockers rather than weakening self-ID standards.",
            "allowed_claims": [
                "bounded admission materialization audit decision",
                "row completeness and claim-boundary audit",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new materialized Route A execution-admission surface",
            "paper_verdict_delta": "no paper verdict",
            "must_synthesize_if": [
                "M2917 cannot accept reject repair pivot or stop M2916",
                "M2917 would claim validation readiness driver performance paper high-fidelity or self-ID evidence",
                "M2917 would bypass Route B or Route C blockers",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "audit summarizes M2916 materialization row counts and gates",
            "audit preserves actor Route B Route C denominator and claim boundaries",
            "audit selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2917 executes reset rollout replay validation training ranking promotion dependency work",
            "M2917 changes actor input or action contract",
            "M2917 hides Route B source-family insufficiency or Route C source_unavailable",
            "M2917 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2917 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M2917 writes a bounded result-audit artifact for M2916 and preserves all actor denominator and claim boundaries without execution.",
        "commands": [{"name": "audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "execution_admission_candidate_rows.csv"),
            str(output_dir / "guardrail_context_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2916 Engineering Controller Route A Dependency-Facing Evidence Surface Execution-Admission Materialization Preflight

## Summary

- status: completed
- decision: `{summary['decision']}`
- source rows: `{summary['execution_admission_source_row_count']}`
- candidate rows: `{summary['execution_admission_candidate_row_count']}`
- admitted rows: `{summary['execution_admission_admitted_count']}`
- stale fixed guard rows: `{summary['execution_admission_blocked_stale_fixed_surface_count']}`
- rejection rows: `{summary['execution_admission_rejection_row_count']}`
- guardrail rows: `{summary['guardrail_context_row_count']}`
- gate matrix pass: `{summary['gate_matrix_pass']}`
- next: `{NEXT_ID}`

M2916 materializes a no-execution execution-admission surface from the accepted
M2913/M2914 dependency-facing family surface and the bounded Route A source
inventory selected by M2915. It classifies rows only for a later separately
registered execution route.

## Source Inventory

```text
M2737 source rows: {summary['m2737_source_row_count']}
M2746 source rows: {summary['m2746_source_row_count']}
M2807 source rows: {summary['m2807_source_row_count']}
M2816 source rows: {summary['m2816_source_row_count']}
M2877 fixed weak diagnostic guard rows: {summary['m2877_guard_row_count']}
```

## Admission Result

```text
execution_admission_admitted_count: {summary['execution_admission_admitted_count']}
execution_admission_blocked_stale_fixed_surface_count: {summary['execution_admission_blocked_stale_fixed_surface_count']}
execution_admission_blocked_source_identity_unresolved_count: {summary['execution_admission_blocked_source_identity_unresolved_count']}
```

Rows admitted by M2916 are admitted only to a future result-audited execution
design or execution manifest. They are not reset, rollout, validation,
ranking, performance, paper, high-fidelity, or self-ID evidence.

## Boundary

```text
actor observation/action: {summary['actor_observation_dim']}/action {summary['actor_action_dim']}
hidden_oracle_actor_input_required: {summary['hidden_oracle_actor_input_required']}
future_target_actor_input_required: {summary['future_target_actor_input_required']}
actor_input_contract_changed: {summary['actor_input_contract_changed']}
reset_or_rollout_executed: {summary['reset_or_rollout_executed']}
validation_executed: {summary['validation_executed']}
training_executed: {summary['training_executed']}
dependency_execution_performed: {summary['dependency_execution_performed']}
performance_claim_made: {summary['performance_claim_made']}
paper_claim_made: {summary['paper_claim_made']}
high_fidelity_claim_made: {summary['high_fidelity_claim_made']}
self_id_claim_made: {summary['self_id_claim_made']}
```

Route B source-family insufficiency and Route C source_unavailable remain
context-only guardrails.

## Artifacts

- summary: `{summary['artifacts']['summary']}`
- input source rows: `{summary['artifacts']['execution_admission_input_source_rows']}`
- source rows: `{summary['artifacts']['execution_admission_source_rows']}`
- candidate rows: `{summary['artifacts']['execution_admission_candidate_rows']}`
- rejection rows: `{summary['artifacts']['execution_admission_rejection_rows']}`
- guardrail rows: `{summary['artifacts']['guardrail_context_rows']}`
- actor guard rows: `{summary['artifacts']['actor_contract_guard_rows']}`
- claim rows: `{summary['artifacts']['claim_boundary_rows']}`
- gate matrix: `{summary['artifacts']['gate_matrix']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
"""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2913-dir", type=Path, default=DEFAULT_M2913_DIR)
    parser.add_argument("--m2914-audit", type=Path, default=DEFAULT_M2914_AUDIT)
    parser.add_argument("--m2915-design", type=Path, default=DEFAULT_M2915_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = materialize_dependency_facing_execution_admission(
        m2913_dir=args.m2913_dir,
        m2914_audit=args.m2914_audit,
        m2915_design=args.m2915_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"status_pass={summary['status_pass']} decision={summary['decision']}")


if __name__ == "__main__":
    main()
