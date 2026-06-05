"""M2766 no-rollout action-response telemetry mechanism localization panel."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2766-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit"
)
DEFAULT_M2764_DIR = Path(
    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight"
)
DEFAULT_M2765_AUDIT = Path(
    "docs/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md"
)
DEFAULT_M2762_DIR = Path(
    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2766-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.json"
)

EXPECTED_LOCALIZED_ROW_COUNT = 12
EXPECTED_GUARDRAIL_ROW_COUNT = 31

CLAIM_SCOPE = (
    "M2766 Route A action-response telemetry mechanism-localization panel materialization only; existing M2764 "
    "finite evaluator telemetry and containment artifacts are reanalyzed into row-level mechanism and repair-admission "
    "context while no reset, step, policy action, rollout, replay, validation, training, PPO, source build, adapter "
    "probe, external simulation, ranking, winner selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller-family ranking, source-edge "
    "ranking, stress-axis ranking, task-family ranking, profile ranking, mechanism-tag ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "external_simulation_run": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
    "active_config_overwritten": False,
    "ranking_run": False,
    "mechanism_tag_ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_verdict_claim_made": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
}

TELEMETRY_JOIN_FIELDNAMES = [
    "telemetry_join_id",
    "probe_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "termination_reason",
    "diagnostic_success",
    "collision",
    "min_clearance_margin",
    "previous_command",
    "previous_command_source",
    "current_action",
    "current_action_source",
    "trace_delta_proxy",
    "trace_delta_source",
    "plan_first_action_error_proxy",
    "plan_first_action_error_source",
    "speed_response_proxy",
    "yaw_response_proxy",
    "beta_response_proxy",
    "finite_metric",
    "m2762_contract_satisfied",
    "m2764_telemetry_coverage_improved",
    "m2759_row_backfilled",
    "action_response_labels_actor_visible",
    "containment_labels_actor_visible",
    "mechanism_labels_actor_visible",
    "actor_visible_allowed",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
MECHANISM_LOCALIZATION_FIELDNAMES = [
    "mechanism_localization_id",
    "telemetry_join_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "termination_reason",
    "diagnostic_outcome_bucket",
    "primary_mechanism",
    "secondary_mechanisms",
    "command_response_mismatch_score",
    "track_containment_score",
    "obstacle_timing_score",
    "mixed_mechanism_score",
    "finite_telemetry",
    "containment_failure_flag",
    "collision_risk_flag",
    "repair_target_class",
    "repair_target_basis",
    "mechanism_localization_labels_actor_visible",
    "ranking_run",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
REPAIR_ADMISSION_FIELDNAMES = [
    "repair_admission_id",
    "mechanism_localization_id",
    "candidate_id",
    "task_source_id",
    "primary_mechanism",
    "repair_target_class",
    "repair_admitted_for_design",
    "repair_admission_status",
    "admission_basis",
    "ranking_run",
    "winner_selected",
    "success_rate_verdict_claim_made",
    "repair_success_claim_made",
    "driver_performance_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "m2766_guardrail_id",
    "guardrail_context_id",
    "guardrail_source",
    "guardrail_source_id",
    "task_source_id",
    "blocker_id",
    "route",
    "evidence_family",
    "row_count",
    "blocking_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_success_denominator_allowed",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "guardrail_role",
    "claim_scope",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2766",
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
    "mechanism_localization_rows",
    "telemetry_join_rows",
    "repair_admission_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
    "follow_up_manifest",
]


def run(
    *,
    m2764_dir: Path | str = DEFAULT_M2764_DIR,
    m2765_audit: Path | str = DEFAULT_M2765_AUDIT,
    m2762_dir: Path | str = DEFAULT_M2762_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    follow_up_path = Path(follow_up_manifest)
    write_follow_up_manifest(follow_up_path)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=follow_up_path)
    source = load_source_artifacts(
        m2764_dir=Path(m2764_dir),
        m2765_audit=Path(m2765_audit),
        m2762_dir=Path(m2762_dir),
        follow_up_manifest=follow_up_path,
    )
    telemetry_join_rows = build_telemetry_join_rows(source)
    mechanism_rows = build_mechanism_localization_rows(telemetry_join_rows)
    repair_rows = build_repair_admission_rows(mechanism_rows)
    guardrail_rows = build_guardrail_context_rows(source["m2764_guardrail_rows"])
    actor_guard_rows = build_actor_contract_guard_rows(
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
    )
    required_artifacts_present = False
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        telemetry_join_rows_present=bool(telemetry_join_rows),
        mechanism_rows_present=bool(mechanism_rows),
        repair_rows_present=bool(repair_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_outputs(paths, telemetry_join_rows, mechanism_rows, repair_rows, guardrail_rows, actor_guard_rows, claim_rows, gate_rows)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        telemetry_join_rows_present=bool(telemetry_join_rows),
        mechanism_rows_present=bool(mechanism_rows),
        repair_rows_present=bool(repair_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_path,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        telemetry_join_rows=telemetry_join_rows,
        mechanism_rows=mechanism_rows,
        repair_rows=repair_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_path,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "mechanism_localization_rows": output_dir / "mechanism_localization_rows.csv",
        "telemetry_join_rows": output_dir / "telemetry_join_rows.csv",
        "repair_admission_rows": output_dir / "repair_admission_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_source_artifacts(
    *,
    m2764_dir: Path,
    m2765_audit: Path,
    m2762_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    source_exists = {
        "m2764_summary": (m2764_dir / "summary.json").exists(),
        "m2764_action_response_rows": (m2764_dir / "action_response_probe_rows.csv").exists(),
        "m2764_telemetry_coverage_rows": (m2764_dir / "telemetry_coverage_rows.csv").exists(),
        "m2764_containment_rows": (m2764_dir / "containment_probe_rows.csv").exists(),
        "m2764_mechanism_rows": (m2764_dir / "mechanism_context_rows.csv").exists(),
        "m2764_guardrail_rows": (m2764_dir / "guardrail_context_rows.csv").exists(),
        "m2764_actor_rows": (m2764_dir / "actor_contract_guard_rows.csv").exists(),
        "m2764_claim_rows": (m2764_dir / "claim_boundary_rows.csv").exists(),
        "m2764_gate_rows": (m2764_dir / "gate_matrix.csv").exists(),
        "m2765_audit": m2765_audit.exists(),
        "m2762_schema_rows": (m2762_dir / "telemetry_schema_contract_rows.csv").exists(),
        "follow_up_manifest": follow_up_manifest.exists(),
    }
    return {
        "m2764_dir": str(m2764_dir),
        "m2765_audit": str(m2765_audit),
        "m2762_dir": str(m2762_dir),
        "source_exists": source_exists,
        "m2764_summary": read_json(m2764_dir / "summary.json") if source_exists["m2764_summary"] else {},
        "m2764_action_response_rows": read_csv_rows(m2764_dir / "action_response_probe_rows.csv"),
        "m2764_telemetry_coverage_rows": read_csv_rows(m2764_dir / "telemetry_coverage_rows.csv"),
        "m2764_containment_rows": read_csv_rows(m2764_dir / "containment_probe_rows.csv"),
        "m2764_mechanism_rows": read_csv_rows(m2764_dir / "mechanism_context_rows.csv"),
        "m2764_guardrail_rows": read_csv_rows(m2764_dir / "guardrail_context_rows.csv"),
        "m2764_actor_rows": read_csv_rows(m2764_dir / "actor_contract_guard_rows.csv"),
        "m2764_claim_rows": read_csv_rows(m2764_dir / "claim_boundary_rows.csv"),
        "m2764_gate_rows": read_csv_rows(m2764_dir / "gate_matrix.csv"),
        "m2765_audit_text": m2765_audit.read_text(encoding="utf-8") if m2765_audit.exists() else "",
        "m2762_schema_rows": read_csv_rows(m2762_dir / "telemetry_schema_contract_rows.csv"),
        "follow_up_manifest": str(follow_up_manifest),
    }


def build_telemetry_join_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    action_by_resolution = {
        str(row.get("probe_resolution_id", "")): row for row in source["m2764_action_response_rows"]
    }
    coverage_by_resolution = {
        str(row.get("probe_resolution_id", "")): row for row in source["m2764_telemetry_coverage_rows"]
    }
    containment_by_resolution = {
        str(row.get("probe_resolution_id", "")): row for row in source["m2764_containment_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, resolution_id in enumerate(sorted(action_by_resolution), start=1):
        action = action_by_resolution[resolution_id]
        coverage = coverage_by_resolution.get(resolution_id, {})
        containment = containment_by_resolution.get(resolution_id, {})
        rows.append(
            {
                "telemetry_join_id": f"m2766-telemetry-join-{index:04d}",
                "probe_id": action.get("probe_id", ""),
                "probe_resolution_id": resolution_id,
                "candidate_id": action.get("candidate_id", containment.get("candidate_id", "")),
                "localization_id": action.get("localization_id", containment.get("localization_id", "")),
                "task_source_id": action.get("task_source_id", containment.get("task_source_id", "")),
                "failure_family": action.get("failure_family", containment.get("failure_family", "")),
                "termination_reason": containment.get("termination_reason", ""),
                "diagnostic_success": _diagnostic_success(containment),
                "collision": _bool(containment.get("collision_risk_flag", False)),
                "min_clearance_margin": _finite_or_blank(_float(containment.get("min_clearance_margin"))),
                "previous_command": _finite_or_blank(_float(action.get("previous_command"))),
                "previous_command_source": action.get("previous_command_source", ""),
                "current_action": _finite_or_blank(_float(action.get("current_action"))),
                "current_action_source": action.get("current_action_source", ""),
                "trace_delta_proxy": _finite_or_blank(_float(action.get("trace_delta_proxy"))),
                "trace_delta_source": action.get("trace_delta_source", ""),
                "plan_first_action_error_proxy": _finite_or_blank(_float(action.get("plan_first_action_error_proxy"))),
                "plan_first_action_error_source": action.get("plan_first_action_error_source", ""),
                "speed_response_proxy": _finite_or_blank(_float(action.get("speed_response_proxy"))),
                "yaw_response_proxy": _finite_or_blank(_float(action.get("yaw_response_proxy"))),
                "beta_response_proxy": _finite_or_blank(_float(action.get("beta_response_proxy"))),
                "finite_metric": _bool(action.get("finite_metric", False)),
                "m2762_contract_satisfied": _bool(action.get("m2762_contract_satisfied", False)),
                "m2764_telemetry_coverage_improved": _bool(coverage.get("finite_metric_improved_from_m2759", False)),
                "m2759_row_backfilled": _bool(coverage.get("m2759_row_backfilled", False)),
                "action_response_labels_actor_visible": _bool(action.get("action_response_labels_actor_visible", False)),
                "containment_labels_actor_visible": _bool(containment.get("containment_labels_actor_visible", False)),
                "mechanism_labels_actor_visible": False,
                "actor_visible_allowed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_mechanism_localization_rows(telemetry_join_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(telemetry_join_rows, start=1):
        trace_delta = _finite_or_zero(_float(row.get("trace_delta_proxy")))
        action_rate = _finite_or_zero(_float(row.get("plan_first_action_error_proxy")))
        clearance = _float(row.get("min_clearance_margin"))
        termination = str(row.get("termination_reason", ""))
        diagnostic_success = _bool(row.get("diagnostic_success", False))
        collision = _bool(row.get("collision", False)) or _is_finite(clearance) and clearance < 0.0
        offtrack = termination == "off_track"
        command_score = max(trace_delta, action_rate)
        containment_score = 1.0 if offtrack else 0.0
        obstacle_score = 1.0 if collision or termination == "obstacle_collision" else 0.0
        active = []
        if command_score > 0.0:
            active.append("command_response_mismatch_context")
        if containment_score > 0.0:
            active.append("track_containment_context")
        if obstacle_score > 0.0:
            active.append("obstacle_timing_context")
        if not active:
            active.append("diagnostic_success_context")
        if len(active) > 1:
            active.append("mixed_mechanism_context")
        primary = primary_mechanism(active, termination=termination, collision=collision, diagnostic_success=diagnostic_success)
        repair_class = repair_target_class(primary)
        rows.append(
            {
                "mechanism_localization_id": f"m2766-mechanism-localization-{index:04d}",
                "telemetry_join_id": row.get("telemetry_join_id", ""),
                "probe_resolution_id": row.get("probe_resolution_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "localization_id": row.get("localization_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "failure_family": row.get("failure_family", ""),
                "termination_reason": termination,
                "diagnostic_outcome_bucket": diagnostic_outcome_bucket(row),
                "primary_mechanism": primary,
                "secondary_mechanisms": ";".join(tag for tag in active if tag != primary),
                "command_response_mismatch_score": _finite_or_blank(command_score),
                "track_containment_score": _finite_or_blank(containment_score),
                "obstacle_timing_score": _finite_or_blank(obstacle_score),
                "mixed_mechanism_score": len(active) - 1,
                "finite_telemetry": _bool(row.get("finite_metric", False)),
                "containment_failure_flag": offtrack,
                "collision_risk_flag": collision,
                "repair_target_class": repair_class,
                "repair_target_basis": "finite_telemetry_plus_containment_context",
                "mechanism_localization_labels_actor_visible": False,
                "ranking_run": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_repair_admission_rows(mechanism_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(mechanism_rows, start=1):
        admitted = _bool(row.get("finite_telemetry", False)) and str(row.get("primary_mechanism", "")) != "diagnostic_success_context"
        status = "bounded_repair_design_candidate" if admitted else "context_only_no_repair_design"
        rows.append(
            {
                "repair_admission_id": f"m2766-repair-admission-{index:04d}",
                "mechanism_localization_id": row.get("mechanism_localization_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "primary_mechanism": row.get("primary_mechanism", ""),
                "repair_target_class": row.get("repair_target_class", ""),
                "repair_admitted_for_design": admitted,
                "repair_admission_status": status,
                "admission_basis": "row_level_mechanism_localization_non_ranking",
                "ranking_run": False,
                "winner_selected": False,
                "success_rate_verdict_claim_made": False,
                "repair_success_claim_made": False,
                "driver_performance_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "m2766_guardrail_id": f"m2766-guardrail-context-{index:04d}",
                "guardrail_context_id": row.get("guardrail_context_id", ""),
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_source_id": row.get("guardrail_source_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "route": row.get("route", ""),
                "evidence_family": row.get("evidence_family", ""),
                "row_count": row.get("row_count", ""),
                "blocking_count": row.get("blocking_count", ""),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": row.get("guardrail_role", "non_executed_guardrail_context"),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: dict[str, Any],
    telemetry_join_rows: list[Mapping[str, Any]],
    mechanism_rows: list[Mapping[str, Any]],
    repair_rows: list[Mapping[str, Any]],
    guardrail_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    actor_rows = source["m2764_actor_rows"]
    obs_ok = actor_observed_expected_pass(actor_rows, "p0_observation_dim", str(P0_OBSERVATION_DIM), str(P0_OBSERVATION_DIM))
    action_ok = actor_observed_expected_pass(actor_rows, "action_dim", str(ACTION_DIM), str(ACTION_DIM))
    all_rows = telemetry_join_rows + mechanism_rows + repair_rows + guardrail_rows
    checks = [
        ("p0_observation_dim", P0_OBSERVATION_DIM if obs_ok else "missing_or_failed", P0_OBSERVATION_DIM, obs_ok),
        ("action_dim", ACTION_DIM if action_ok else "missing_or_failed", ACTION_DIM, action_ok),
        ("hidden_oracle_actor_input_detected", any_flag(all_rows, "hidden_oracle_actor_input_required"), False, not any_flag(all_rows, "hidden_oracle_actor_input_required")),
        ("actor_input_contract_changed", any_flag(all_rows, "actor_input_contract_changed"), False, not any_flag(all_rows, "actor_input_contract_changed")),
        ("diagnostic_labels_actor_visible", any_label_actor_visible(all_rows), False, not any_label_actor_visible(all_rows)),
        ("guardrails_actor_visible", any_flag(guardrail_rows, "actor_visible_allowed"), False, not any_flag(guardrail_rows, "actor_visible_allowed")),
    ]
    return [
        actor_guard(f"m2766-actor-guard-{index:04d}", family, observed, expected, status)
        for index, (family, observed, expected, status) in enumerate(checks, start=1)
    ]


def actor_observed_expected_pass(rows: list[Mapping[str, Any]], family: str, observed: str, expected: str) -> bool:
    for row in rows:
        if str(row.get("guard_family", "")) == family:
            return (
                str(row.get("observed", "")) == observed
                and str(row.get("expected", "")) == expected
                and _bool(row.get("status_pass", False))
            )
    return False


def actor_guard(guard_id: str, family: str, observed: Any, expected: Any, status: bool) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": family,
        "observed": observed,
        "expected": expected,
        "status_pass": bool(status),
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    telemetry_join_rows_present: bool,
    mechanism_rows_present: bool,
    repair_rows_present: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    claims = [
        ("telemetry_join_materialized", True, telemetry_join_rows_present, "M2766 telemetry join rows"),
        ("mechanism_localization_panel_materialized", True, mechanism_rows_present, "M2766 mechanism-localization rows"),
        ("repair_admission_rows_materialized", True, repair_rows_present, "M2766 non-ranking repair-admission rows"),
        ("required_artifacts_present", True, required_artifacts_present, "M2766 required artifacts"),
        ("result_audit_follow_up_registered", True, follow_up_manifest_registered, "M2767 result-audit manifest"),
        ("m2759_row_backfill", False, False, "M2764 fresh finite telemetry artifacts"),
        ("repair_success", False, False, "separate repair design execution and audit"),
        ("driver_performance", False, False, "separate validation and promotion gates"),
        ("validation_readiness", False, False, "separate validation-readiness gate"),
        ("validation_result", False, False, "separate validation execution"),
        ("ranking_or_winner_selection", False, False, "separate controller-family comparison and ranking protocol"),
        ("checkpoint_promotion", False, False, "separate promotion gate"),
        ("paper_evidence", False, False, "separate paper route proof/generalization matrix"),
        ("finite_window_vs_gru", False, False, "separate controlled family comparison"),
        ("current_sim_verdict", False, False, "separate current-sim benchmark verdict gate"),
        ("high_fidelity_validation", False, False, "separate high-fidelity interface and validation route"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "closed-loop self-identification proof gate"),
    ]
    return [
        {
            "claim_id": f"m2766-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2766": allowed,
            "claim_made": made,
            "status_pass": bool((allowed and made) or (not allowed and not made)),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    telemetry_join_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    schema_fields = {str(row.get("output_column", "")) for row in source["m2762_schema_rows"]}
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2764 M2765 M2762 and M2767 artifacts present", "lineage_invalid"),
        gate("m2764_summary_status_pass", "lineage", _bool(source["m2764_summary"].get("status_pass", False)), source["m2764_summary"].get("status_pass", False), True, "lineage_invalid"),
        gate("m2765_audit_routes_to_m2766", "lineage", "m2766" in source["m2765_audit_text"], "m2766" in source["m2765_audit_text"], True, "lineage_invalid"),
        gate("m2762_schema_contract_present", "telemetry", {"previous_command", "current_action", "plan_first_action_error_proxy", "finite_metric"}.issubset(schema_fields), sorted(schema_fields), "previous/current/plan-or-trace/finite contract", "metric_artifact"),
        gate("telemetry_join_rows_accounted", "metric", len(telemetry_join_rows) == EXPECTED_LOCALIZED_ROW_COUNT, len(telemetry_join_rows), EXPECTED_LOCALIZED_ROW_COUNT, "metric_artifact"),
        gate("mechanism_localization_rows_accounted", "metric", len(mechanism_rows) == len(telemetry_join_rows), len(mechanism_rows), len(telemetry_join_rows), "metric_artifact"),
        gate("repair_admission_rows_accounted", "metric", len(repair_rows) == len(mechanism_rows), len(repair_rows), len(mechanism_rows), "metric_artifact"),
        gate("finite_telemetry_join_rows", "telemetry", count_bool(telemetry_join_rows, "finite_metric") == EXPECTED_LOCALIZED_ROW_COUNT, count_bool(telemetry_join_rows, "finite_metric"), EXPECTED_LOCALIZED_ROW_COUNT, "metric_artifact"),
        gate("telemetry_improved_rows_preserved", "telemetry", count_bool(telemetry_join_rows, "m2764_telemetry_coverage_improved") == EXPECTED_LOCALIZED_ROW_COUNT, count_bool(telemetry_join_rows, "m2764_telemetry_coverage_improved"), EXPECTED_LOCALIZED_ROW_COUNT, "metric_artifact"),
        gate("m2759_rows_not_backfilled", "telemetry", not any_flag(telemetry_join_rows, "m2759_row_backfilled"), any_flag(telemetry_join_rows, "m2759_row_backfilled"), False, "proof_washout"),
        gate("mechanism_classes_present", "metric", bool({row["primary_mechanism"] for row in mechanism_rows}), sorted({row["primary_mechanism"] for row in mechanism_rows}), "non_empty", "metric_artifact"),
        gate("repair_admission_non_ranking", "claim", not any_flag(repair_rows + mechanism_rows, "ranking_run") and not any_flag(repair_rows, "winner_selected"), "ranking_or_winner_present" if (any_flag(repair_rows + mechanism_rows, "ranking_run") or any_flag(repair_rows, "winner_selected")) else False, False, "proof_washout"),
        gate("guardrail_rows_carried", "guardrail", len(guardrail_rows) == EXPECTED_GUARDRAIL_ROW_COUNT, len(guardrail_rows), EXPECTED_GUARDRAIL_ROW_COUNT, "lineage_invalid"),
        gate("guardrails_not_executed", "guardrail", not any_flag(guardrail_rows, "execution_run"), any_flag(guardrail_rows, "execution_run"), False, "proof_washout"),
        gate("guardrails_outside_denominator", "guardrail", not any_flag(guardrail_rows, "ordinary_success_denominator_allowed") and not any_flag(guardrail_rows, "protected_rows_in_success_denominator"), "ordinary_or_protected_denominator_present" if (any_flag(guardrail_rows, "ordinary_success_denominator_allowed") or any_flag(guardrail_rows, "protected_rows_in_success_denominator")) else False, False, "proof_washout"),
        gate("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        gate("hidden_oracle_actor_input_false", "contract", not any_flag(telemetry_join_rows, "hidden_oracle_actor_input_required"), any_flag(telemetry_join_rows, "hidden_oracle_actor_input_required"), False, "contract_violation"),
        gate("diagnostic_labels_actor_visible_false", "contract", not any_label_actor_visible(telemetry_join_rows + mechanism_rows + repair_rows), any_label_actor_visible(telemetry_join_rows + mechanism_rows + repair_rows), False, "contract_violation"),
        gate("forbidden_execution_false", "claim", not any(forbidden_flag(row) for row in telemetry_join_rows + mechanism_rows + repair_rows), "forbidden flag present" if any(forbidden_flag(row) for row in telemetry_join_rows + mechanism_rows + repair_rows) else False, False, "proof_washout"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2766-gate-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def write_outputs(
    paths: dict[str, Path],
    telemetry_join_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["telemetry_join_rows"], telemetry_join_rows, fieldnames=TELEMETRY_JOIN_FIELDNAMES)
    write_csv_rows(paths["mechanism_localization_rows"], mechanism_rows, fieldnames=MECHANISM_LOCALIZATION_FIELDNAMES)
    write_csv_rows(paths["repair_admission_rows"], repair_rows, fieldnames=REPAIR_ADMISSION_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    telemetry_join_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    mechanism_counts = Counter(str(row.get("primary_mechanism", "")) for row in mechanism_rows)
    repair_counts = Counter(str(row.get("repair_target_class", "")) for row in repair_rows)
    admitted_repair_rows = sum(1 for row in repair_rows if _bool(row.get("repair_admitted_for_design", False)))
    status_pass = bool(all(_bool(row["status_pass"]) for row in gate_rows))
    return {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "m2764_status_pass": _bool(source["m2764_summary"].get("status_pass", False)),
        "telemetry_join_row_count": len(telemetry_join_rows),
        "mechanism_localization_row_count": len(mechanism_rows),
        "repair_admission_row_count": len(repair_rows),
        "repair_admitted_for_design_count": admitted_repair_rows,
        "finite_telemetry_join_count": count_bool(telemetry_join_rows, "finite_metric"),
        "telemetry_coverage_improved_count": count_bool(telemetry_join_rows, "m2764_telemetry_coverage_improved"),
        "m2759_rows_backfilled": any_flag(telemetry_join_rows, "m2759_row_backfilled"),
        "primary_mechanism_counts": dict(sorted(mechanism_counts.items())),
        "repair_target_class_counts": dict(sorted(repair_counts.items())),
        "guardrail_context_row_count": len(guardrail_rows),
        "guardrail_execution": any_flag(guardrail_rows, "execution_run"),
        "protected_rows_in_success_denominator": any_flag(guardrail_rows, "protected_rows_in_success_denominator"),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": all(_bool(row["status_pass"]) for row in gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "source_exists": source["source_exists"],
        "actor_input_contract_changed": any_flag(telemetry_join_rows, "actor_input_contract_changed"),
        "hidden_oracle_actor_input_required": any_flag(telemetry_join_rows, "hidden_oracle_actor_input_required"),
        "diagnostic_labels_actor_visible": any_label_actor_visible(telemetry_join_rows + mechanism_rows + repair_rows),
        **{key: any_flag(telemetry_join_rows + mechanism_rows + repair_rows, key) for key in FALSE_CLAIM_FLAGS},
        "next_blocker": next_blocker,
        "follow_up_manifest": str(follow_up_manifest),
        "artifacts": {key: str(value) for key, value in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def render_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# M2766 Engineering Controller Route A Action-Response Telemetry Mechanism Localization Panel Materialization Preflight",
        "",
        "## Metadata",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- telemetry join rows: {summary['telemetry_join_row_count']}",
        f"- mechanism localization rows: {summary['mechanism_localization_row_count']}",
        f"- repair admission rows: {summary['repair_admission_row_count']}",
        f"- repair design admitted rows: {summary['repair_admitted_for_design_count']}",
        f"- finite telemetry joins: {summary['finite_telemetry_join_count']}",
        f"- telemetry coverage improved rows: {summary['telemetry_coverage_improved_count']}",
        f"- guardrail context rows: {summary['guardrail_context_row_count']}",
        f"- primary mechanism counts: {summary['primary_mechanism_counts']}",
        f"- repair target class counts: {summary['repair_target_class_counts']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        f"- next blocker: `{summary['next_blocker']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        "",
        "## Result",
        "",
        "M2766 materializes a no-rollout mechanism-localization panel from M2764",
        "finite evaluator-only telemetry and containment artifacts. It preserves",
        "M2759 no-backfill lineage, uses M2764 rows only as diagnostic source",
        "evidence, and does not execute or rank any candidate.",
        "",
        "## Boundary",
        "",
        summary["claim_scope"],
        "",
        "Forbidden interpretation:",
        "",
        summary["forbidden_interpretation"],
        "",
    ]
    return "\n".join(lines)


def write_follow_up_manifest(path: Path) -> None:
    write_json(
        path,
        {
            "id": DEFAULT_NEXT_BLOCKER,
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
            ],
            "lineage": {
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
                ],
                "parent_dataset": [
                    "docs/m2766-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-preflight.md",
                    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/summary.json",
                    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/mechanism_localization_rows.csv",
                    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/telemetry_join_rows.csv",
                    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/repair_admission_rows.csv",
                    "docs/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/summary.json",
                ],
                "parent_config": [
                    "experiments/manifests/m2766-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-preflight.json",
                    "experiments/manifests/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.json",
                ],
                "parent_objective": [
                    "audit M2766 mechanism-localization panel artifacts before repair design or another execution"
                ],
                "derived_from": [
                    "m2766-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-preflight",
                    "m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit",
                    "m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight",
                ],
                "blocked_by": [
                    "M2766 artifacts require result audit before repair design execution extension validation ranking or performance claim"
                ],
                "supersedes": [
                    "direct repair design before auditing M2766",
                    "same-surface execution extension before auditing M2766",
                    "repair success driver performance validation paper current-sim high-fidelity full-driver or self-ID claim from M2766",
                ],
                "invalidates": [],
            },
            "review_artifact": "docs/reviews/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.md",
            "public_gates": [
                "M2767 must consume M2766 summary mechanism-localization telemetry join repair-admission guard actor claim and gate artifacts",
                "M2767 must accept or reject M2766 artifact completeness and claim safety",
                "M2767 must preserve actor 72/action 3 no hidden oracle actor input and actor-invisible mechanism labels",
                "M2767 must reject repair success driver performance validation ranking paper current-sim high-fidelity full ideal driver and self-ID claims",
                "M2767 must route to synthesis artifact repair or bounded repair design without executing replay validation training ranking or promotion",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not execute replay validation training PPO source build adapter probe or external simulation",
                "do not rank candidates mechanism tags controllers source edges stress axes profiles or task families",
                "do not select a winner promote a checkpoint or compute success-rate verdict",
                "do not claim repair success driver performance validation readiness paper current-sim high-fidelity full ideal driver or self-ID",
                "do not backfill M2759 finite_metric rows",
                "do not change actor inputs or expose mechanism labels to actor input",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_action_response_mechanism_localization",
                "evidence_axis": "route_a_action_response_telemetry_mechanism_localization_panel_result_audit",
                "evidence_increment": "audits whether M2766 produced a complete non-ranking mechanism-localization panel from M2764 finite telemetry",
                "claim_scope": "Route A diagnostic artifact audit only; no replay validation training ranking promotion repair-success driver-performance paper current-sim high-fidelity self-ID or full ideal driver claim",
                "stop_condition": [
                    "stop if M2766 artifacts are incomplete",
                    "stop if actor or claim boundaries were violated",
                    "stop if no bounded non-ranking next route can be selected",
                ],
                "fallback_plan": [
                    "route to artifact repair if panel joins are incomplete",
                    "route to branch synthesis if localized targets remain ambiguous",
                    "route to bounded repair design only if the audit accepts a non-ranking target contract",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2766 mechanism-localization panel has produced artifacts that require result audit",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "evaluation_only",
                "stage_objective": "action-response telemetry mechanism-localization panel result audit",
                "admission_evidence": [
                    "M2766 mechanism-localization artifacts exist",
                    "M2766 registered this result-audit follow-up before interpretation",
                ],
                "blocked_shortcuts": [
                    "no replay validation training ranking promotion or performance claim",
                    "no actor input change or hidden oracle input",
                ],
                "allowed_updates": [
                    "docs/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.md",
                    "M2767 status queue scoreboard research log and review",
                    "one bounded follow-up manifest if audit accepts artifacts",
                ],
                "next_stage_criteria": [
                    "M2767 accepts or rejects M2766 artifacts and claim boundaries",
                    "M2767 registers one bounded next step or synthesis route",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2767 audits Route A engineering localization artifacts and does not test history necessity or current-frame substitution.",
                "history_necessity_tests": [
                    "None in M2767; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2759-M2767 Route A action-response containment telemetry and mechanism-localization artifacts only.",
                "negative_result_policy": "If M2766 artifacts are incomplete preserve the blocker and route to artifact repair or synthesis rather than weakening gates or claiming self-ID evidence.",
                "allowed_claims": [
                    "M2766 mechanism-localization artifacts are complete and claim-safe or explicitly rejected",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "low",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits the new M2766 mechanism-localization panel before repair design or another execution",
                "paper_verdict_delta": "no paper verdict; can decide whether Route A should admit bounded repair design or synthesize",
                "must_synthesize_if": [
                    "M2767 cannot decide a bounded next step after complete M2766 artifacts",
                    "M2767 proposes same-surface execution without a new evidence axis",
                    "M2767 would make validation performance paper current-sim high-fidelity full-driver or self-ID claims",
                ],
            },
            "hypothesis": "M2766 artifacts can be audited as complete and claim-safe before repair design or another execution.",
            "success_criteria": [
                "docs/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.md exists",
                "M2767 accepts or rejects M2766 mechanism localization and repair-admission evidence",
                "actor and claim boundaries are preserved",
                "one bounded follow-up or synthesis route is registered",
            ],
            "failure_criteria": [
                "M2767 overclaims M2766 as repair success validation performance paper current-sim high-fidelity full-driver or self-ID evidence",
                "M2767 hides M2766 finite telemetry gaps or guardrail violations",
                "M2767 fails to register a bounded next step or synthesis route",
            ],
            "decision_rule": "Pass only if M2767 provides a bounded result audit of M2766 artifacts and preserves all actor guardrail and claim boundaries.",
            "commands": [{"name": "result_audit", "command": "true"}],
            "required_artifacts": [
                {
                    "path": "docs/m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit.md",
                    "type": "md",
                }
            ],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "baseline_artifacts": [
                "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/summary.json",
                "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/mechanism_localization_rows.csv",
                "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization/repair_admission_rows.csv",
            ],
        },
    )


def primary_mechanism(active: list[str], *, termination: str, collision: bool, diagnostic_success: bool) -> str:
    if diagnostic_success and not collision and termination != "off_track":
        return "diagnostic_success_context"
    if collision or termination == "obstacle_collision":
        return "obstacle_timing_context"
    if termination == "off_track":
        return "track_containment_context"
    if "command_response_mismatch_context" in active:
        return "command_response_mismatch_context"
    return active[0]


def repair_target_class(primary: str) -> str:
    return {
        "obstacle_timing_context": "obstacle_timing_or_clearance_margin_target",
        "track_containment_context": "track_containment_stability_target",
        "command_response_mismatch_context": "command_response_smoothing_target",
        "mixed_mechanism_context": "mixed_mechanism_target",
    }.get(primary, "context_only_no_repair_target")


def diagnostic_outcome_bucket(row: Mapping[str, Any]) -> str:
    if _bool(row.get("collision", False)):
        return "obstacle_collision_context"
    if str(row.get("termination_reason", "")) == "off_track":
        return "offtrack_context"
    if _bool(row.get("diagnostic_success", False)):
        return "diagnostic_success_context"
    return "blank_or_completed_context"


def _diagnostic_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision_risk_flag", False))


def count_bool(rows: list[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if _bool(row.get(key, False)))


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def any_label_actor_visible(rows: list[Mapping[str, Any]]) -> bool:
    label_keys = [
        "action_response_labels_actor_visible",
        "containment_labels_actor_visible",
        "mechanism_labels_actor_visible",
        "mechanism_localization_labels_actor_visible",
        "stress_axis_labels_actor_visible",
        "source_edge_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
        "actor_visible_allowed",
    ]
    return any(any(_bool(row.get(key, False)) for key in label_keys) for row in rows)


def forbidden_flag(row: Mapping[str, Any]) -> bool:
    return any(_bool(row.get(key, False)) for key in FALSE_CLAIM_FLAGS)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _is_finite(value: float) -> bool:
    return math.isfinite(value)


def _finite_or_zero(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _finite_or_blank(value: float) -> float | str:
    return value if math.isfinite(value) else ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2764-dir", type=Path, default=DEFAULT_M2764_DIR)
    parser.add_argument("--m2765-audit", type=Path, default=DEFAULT_M2765_AUDIT)
    parser.add_argument("--m2762-dir", type=Path, default=DEFAULT_M2762_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(
        m2764_dir=args.m2764_dir,
        m2765_audit=args.m2765_audit,
        m2762_dir=args.m2762_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"mechanism_localization_row_count={summary['mechanism_localization_row_count']}")
    print(f"repair_admitted_for_design_count={summary['repair_admitted_for_design_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
