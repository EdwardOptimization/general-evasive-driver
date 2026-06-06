"""Materialize M2963 post-zero-residual failure-localization rows.

M2963 consumes the accepted M2960/M2961/M2962 actor-head delta zero-residual
diagnostic artifacts. It performs no environment, policy, validation, training,
ranking, or promotion work. It converts the 56 diagnostic execution rows into
machine-checkable failure-localization rows and residual-objective admission
rows for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2963-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-zero-residual-failure-localization-objective-admission-preflight"
)
NEXT_ID = (
    "m2964-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-zero-residual-failure-localization-objective-admission-result-audit"
)
DEFAULT_M2960_DIR = Path(
    "runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "bounded_execution_preflight"
)
DEFAULT_M2961_AUDIT = Path(
    "docs/m2961-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "bounded-execution-result-audit.md"
)
DEFAULT_M2962_SYNTHESIS = Path(
    "docs/m2962-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "bounded-execution-result-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2963_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "post_zero_residual_failure_localization_objective_admission_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2963-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-zero-residual-failure-localization-objective-admission-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2964-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-post-zero-residual-failure-localization-objective-admission-result-audit.json"
)

EXPECTED_EXECUTION_ROW_COUNT = 56
EXPECTED_FAILURE_ROW_COUNT = 0
EXPECTED_CONTRACT_ROW_COUNT = 56
EXPECTED_BLOCKED_STALE_GUARD_COUNT = 11
EXPECTED_OUTCOME_COUNTS = {
    "diagnostic_success": 13,
    "collision": 7,
    "off_track": 35,
    "speed_too_low": 1,
}
EXPECTED_SOURCE_MILESTONE_COUNTS = {
    "m2737": 18,
    "m2746": 14,
    "m2807": 12,
    "m2816": 12,
}

CLAIM_SCOPE = (
    "M2963 Route A actor-head delta post-zero-residual failure-localization and "
    "residual-objective admission materialization only; M2960 zero-residual "
    "diagnostic execution rows may be grouped into outcome, source, task, and "
    "objective-admission rows, while 11 stale fixed-source rows remain "
    "non-executed guardrails. No reset, step, rollout, replay, validation, "
    "training, PPO, dependency work, nonzero residual selection, ranking, "
    "winner selection, promotion, success-rate verdict, repair success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, nonzero residual quality, driver performance, validation "
    "readiness or result, controller-family ranking, source-family ranking, "
    "task-family ranking, profile ranking, checkpoint ranking, candidate "
    "ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

FAILURE_LOCALIZATION_FIELDNAMES = [
    "localization_row_id",
    "execution_candidate_id",
    "resolution_id",
    "actor_head_delta_candidate_id",
    "source_execution_admission_candidate_id",
    "source_milestone",
    "source_family",
    "source_row_id",
    "workload_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "checkpoint_path",
    "parent_checkpoint_path",
    "outcome_family",
    "termination_reason",
    "outcome_bucket",
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "lateral_rmse",
    "beta_abs_error_mean",
    "high_sideslip_fraction",
    "speed_mean",
    "action_rate_mean",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "recoverability_window_success_available",
    "recoverability_window_success",
    "failure_localization_family",
    "residual_objective_candidate_family",
    "candidate_admitted_for_objective_audit",
    "future_training_manifest_required",
    "future_execution_manifest_required",
    "execution_scheduled",
    "training_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_visible_label",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
OBJECTIVE_ADMISSION_FIELDNAMES = [
    "admission_row_id",
    "objective_family",
    "trigger_outcome_family",
    "trigger_count",
    "source_milestone_count",
    "task_family_count",
    "candidate_row_count",
    "non_success_count",
    "admission_action",
    "admission_reason",
    "admitted_for_m2964_audit",
    "future_training_manifest_required",
    "future_execution_manifest_required",
    "training_scheduled",
    "execution_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "residual_target_signal_actor_visible",
    "actor_input_change_required",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "aggregate_value",
    "row_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "non_success_count",
    "dominant_outcome_family",
    "residual_objective_candidate_count",
    "min_clearance_margin_mean",
    "return_mean",
    "lateral_rmse_mean",
    "beta_abs_error_mean",
    "high_sideslip_fraction_mean",
    "recoverability_window_success_count",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_context_id",
    "source_guardrail_context_id",
    "guardrail_source",
    "guardrail_family",
    "source_milestone",
    "source_row_id",
    "guardrail_reason",
    "row_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
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
    "allowed_in_m2963",
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
    "failure_localization_rows",
    "residual_objective_admission_rows",
    "source_milestone_aggregate",
    "task_family_aggregate",
    "outcome_family_aggregate",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_zero_residual_failure_localization_objective_admission_preflight(
    *,
    m2960_dir: Path | str = DEFAULT_M2960_DIR,
    m2961_audit: Path | str = DEFAULT_M2961_AUDIT,
    m2962_synthesis: Path | str = DEFAULT_M2962_SYNTHESIS,
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
        m2960_dir=Path(m2960_dir),
        m2961_audit=Path(m2961_audit),
        m2962_synthesis=Path(m2962_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]
    contract_rows = source["actor_head_delta_contract_execution_rows"]

    localization_rows = build_failure_localization_rows(execution_rows)
    objective_rows = build_residual_objective_admission_rows(localization_rows)
    source_rows = build_aggregate_rows(execution_rows, aggregate_family="source_milestone", key="source_milestone")
    task_rows = build_aggregate_rows(execution_rows, aggregate_family="task_family", key="task_family")
    outcome_rows = build_aggregate_rows(execution_rows, aggregate_family="outcome_family", key="outcome_family")
    guardrail_rows = build_guardrail_context_rows(source["guardrail_context_rows"])

    write_csv_rows(paths["failure_localization_rows"], localization_rows, fieldnames=FAILURE_LOCALIZATION_FIELDNAMES)
    write_csv_rows(
        paths["residual_objective_admission_rows"],
        objective_rows,
        fieldnames=OBJECTIVE_ADMISSION_FIELDNAMES,
    )
    write_csv_rows(paths["source_milestone_aggregate"], source_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["task_family_aggregate"], task_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["outcome_family_aggregate"], outcome_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "execution_row_count": len(execution_rows),
            "bounded_execution_failure_row_count": len(failure_rows),
            "contract_execution_row_count": len(contract_rows),
            "failure_localization_row_count": len(localization_rows),
            "residual_objective_admission_row_count": len(objective_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        source=source,
        localization_rows=localization_rows,
        objective_rows=objective_rows,
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        localization_rows_present=bool(localization_rows),
        objective_rows_present=bool(objective_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        objective_rows=objective_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        outcome_rows=outcome_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, actor_rows, claim_rows, gate_rows)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        localization_rows=localization_rows,
        objective_rows=objective_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        outcome_rows=outcome_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        localization_rows_present=bool(localization_rows),
        objective_rows_present=bool(objective_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        objective_rows=objective_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        outcome_rows=outcome_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        localization_rows=localization_rows,
        objective_rows=objective_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        outcome_rows=outcome_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
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
            "execution_row_count": len(execution_rows),
            "bounded_execution_failure_row_count": len(failure_rows),
            "contract_execution_row_count": len(contract_rows),
            "failure_localization_row_count": len(localization_rows),
            "residual_objective_admission_row_count": len(objective_rows),
            "execution_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "failure_localization_rows": output_dir / "failure_localization_rows.csv",
        "residual_objective_admission_rows": output_dir / "residual_objective_admission_rows.csv",
        "source_milestone_aggregate": output_dir / "source_milestone_aggregate.csv",
        "task_family_aggregate": output_dir / "task_family_aggregate.csv",
        "outcome_family_aggregate": output_dir / "outcome_family_aggregate.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2960_dir: Path,
    m2961_audit: Path,
    m2962_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2961_audit": m2961_audit,
        "m2962_synthesis": m2962_synthesis,
        "m2960_summary": m2960_dir / "summary.json",
        "execution_candidate_rows": m2960_dir / "execution_candidate_rows.csv",
        "execution_resolution_rows": m2960_dir / "execution_resolution_rows.csv",
        "actor_head_delta_contract_execution_rows": m2960_dir / "actor_head_delta_contract_execution_rows.csv",
        "bounded_execution_rows": m2960_dir / "bounded_execution_rows.csv",
        "bounded_execution_failure_rows": m2960_dir / "bounded_execution_failure_rows.csv",
        "source_milestone_aggregate": m2960_dir / "source_milestone_aggregate.csv",
        "task_family_aggregate": m2960_dir / "task_family_aggregate.csv",
        "guardrail_context_rows": m2960_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": m2960_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2960_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2960_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2961_audit_text": paths["m2961_audit"].read_text(encoding="utf-8")
        if source_exists["m2961_audit"]
        else "",
        "m2962_synthesis_text": paths["m2962_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2962_synthesis"]
        else "",
        "m2960_summary": read_json(paths["m2960_summary"]) if source_exists["m2960_summary"] else {},
        "execution_candidate_rows": read_csv_rows(paths["execution_candidate_rows"]),
        "execution_resolution_rows": read_csv_rows(paths["execution_resolution_rows"]),
        "actor_head_delta_contract_execution_rows": read_csv_rows(paths["actor_head_delta_contract_execution_rows"]),
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
        "bounded_execution_failure_rows": read_csv_rows(paths["bounded_execution_failure_rows"]),
        "source_milestone_aggregate": read_csv_rows(paths["source_milestone_aggregate"]),
        "task_family_aggregate": read_csv_rows(paths["task_family_aggregate"]),
        "guardrail_context_rows": read_csv_rows(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def outcome_family(row: Mapping[str, Any]) -> str:
    termination = str(row.get("termination_reason", "")).strip()
    if _bool(row.get("success", False)):
        return "diagnostic_success"
    if _bool(row.get("collision", False)) or termination == "obstacle_collision":
        return "collision"
    if termination == "off_track":
        return "off_track"
    if termination == "speed_too_low":
        return "speed_too_low"
    return "other_non_success"


def failure_localization_family(row: Mapping[str, Any]) -> str:
    family = outcome_family(row)
    if family == "diagnostic_success":
        return "success_identity_guard"
    if family == "collision":
        return "collision_clearance_failure"
    if family == "speed_too_low":
        return "speed_floor_context"
    if family == "off_track":
        severity = _to_float(row.get("off_track_severity_proxy"))
        overshoot = _to_float(row.get("max_off_track_overshoot"))
        if max(severity, overshoot) >= 0.075:
            return "offtrack_high_severity_recovery_failure"
        return "offtrack_recovery_failure"
    return "other_non_success_context"


def objective_family_for_row(row: Mapping[str, Any]) -> str:
    family = outcome_family(row)
    if family == "collision":
        return "collision_clearance_residual_objective"
    if family == "off_track":
        return "offtrack_recovery_residual_objective"
    if family == "speed_too_low":
        return "speed_floor_context_guard_objective"
    if family == "diagnostic_success":
        return "success_identity_guard"
    return "other_non_success_context_objective"


def build_failure_localization_rows(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(execution_rows, start=1):
        family = outcome_family(row)
        admitted = family != "diagnostic_success"
        rows.append(
            {
                "localization_row_id": f"m2963-failure-localization-{index:04d}",
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "resolution_id": row.get("resolution_id", ""),
                "actor_head_delta_candidate_id": row.get("actor_head_delta_candidate_id", ""),
                "source_execution_admission_candidate_id": row.get("source_execution_admission_candidate_id", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_family": row.get("source_family", ""),
                "source_row_id": row.get("source_row_id", ""),
                "workload_id": row.get("workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "checkpoint_path": row.get("checkpoint_path", ""),
                "parent_checkpoint_path": row.get("parent_checkpoint_path", ""),
                "outcome_family": family,
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "success": _bool(row.get("success", False)),
                "collision": _bool(row.get("collision", False)),
                "min_clearance_margin": _to_float(row.get("min_clearance_margin")),
                "return": _to_float(row.get("return")),
                "lateral_rmse": _to_float(row.get("lateral_rmse")),
                "beta_abs_error_mean": _to_float(row.get("beta_abs_error_mean")),
                "high_sideslip_fraction": _to_float(row.get("high_sideslip_fraction")),
                "speed_mean": _to_float(row.get("speed_mean")),
                "action_rate_mean": _to_float(row.get("action_rate_mean")),
                "max_off_track_overshoot": _to_float(row.get("max_off_track_overshoot")),
                "time_to_first_off_track_s": row.get("time_to_first_off_track_s", ""),
                "off_track_severity_proxy": _to_float(row.get("off_track_severity_proxy")),
                "recoverability_window_success_available": _bool(row.get("recoverability_window_success_available", False)),
                "recoverability_window_success": _bool(row.get("recoverability_window_success", False)),
                "failure_localization_family": failure_localization_family(row),
                "residual_objective_candidate_family": objective_family_for_row(row),
                "candidate_admitted_for_objective_audit": admitted,
                "future_training_manifest_required": admitted,
                "future_execution_manifest_required": admitted,
                "execution_scheduled": False,
                "training_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "actor_visible_label": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_residual_objective_admission_rows(localization_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in localization_rows:
        grouped[str(row["residual_objective_candidate_family"])].append(row)
    rows: list[dict[str, Any]] = []
    for index, objective_family in enumerate(sorted(grouped), start=1):
        group = grouped[objective_family]
        counts = Counter(str(row["outcome_family"]) for row in group)
        non_success_count = len(group) - counts.get("diagnostic_success", 0)
        admitted = objective_family != "success_identity_guard" and non_success_count > 0
        if admitted:
            action = "admit_for_m2964_result_audit"
            reason = "non-success zero-residual diagnostic slice requires audited objective admission before training"
        else:
            action = "guard_context_only"
            reason = "success zero-residual rows remain identity guard context and are not a training objective"
        rows.append(
            {
                "admission_row_id": f"m2963-residual-objective-admission-{index:04d}",
                "objective_family": objective_family,
                "trigger_outcome_family": dominant_outcome(counts),
                "trigger_count": max(counts.values()) if counts else 0,
                "source_milestone_count": len({str(row["source_milestone"]) for row in group if row.get("source_milestone")}),
                "task_family_count": len({str(row["task_family"]) for row in group if row.get("task_family")}),
                "candidate_row_count": len(group),
                "non_success_count": non_success_count,
                "admission_action": action,
                "admission_reason": reason,
                "admitted_for_m2964_audit": admitted,
                "future_training_manifest_required": admitted,
                "future_execution_manifest_required": admitted,
                "training_scheduled": False,
                "execution_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "residual_target_signal_actor_visible": False,
                "actor_input_change_required": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_aggregate_rows(execution_rows: list[dict[str, str]], *, aggregate_family: str, key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in execution_rows:
        value = outcome_family(row) if key == "outcome_family" else str(row.get(key, ""))
        grouped[value].append(row)
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(sorted(item for item in grouped if item), start=1):
        group = grouped[value]
        counts = Counter(outcome_family(row) for row in group)
        rows.append(
            {
                "aggregate_id": f"m2963-{aggregate_family}-aggregate-{index:04d}",
                "aggregate_family": aggregate_family,
                "aggregate_value": value,
                "row_count": len(group),
                "success_count": counts.get("diagnostic_success", 0),
                "collision_count": counts.get("collision", 0),
                "offtrack_count": counts.get("off_track", 0),
                "speed_too_low_count": counts.get("speed_too_low", 0),
                "non_success_count": len(group) - counts.get("diagnostic_success", 0),
                "dominant_outcome_family": dominant_outcome(counts),
                "residual_objective_candidate_count": sum(outcome_family(row) != "diagnostic_success" for row in group),
                "min_clearance_margin_mean": mean_float(group, "min_clearance_margin"),
                "return_mean": mean_float(group, "return"),
                "lateral_rmse_mean": mean_float(group, "lateral_rmse"),
                "beta_abs_error_mean": mean_float(group, "beta_abs_error_mean"),
                "high_sideslip_fraction_mean": mean_float(group, "high_sideslip_fraction"),
                "recoverability_window_success_count": sum(
                    _bool(row.get("recoverability_window_success", False)) for row in group
                ),
                "all_selected_metrics_finite": selected_metrics_are_finite(group),
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2963-guardrail-context-{index:04d}",
                "source_guardrail_context_id": row.get("guardrail_context_id", ""),
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": row.get("row_count", 1),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = source["m2960_summary"]
    contract_rows = source["actor_head_delta_contract_execution_rows"]
    combined = localization_rows + objective_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("environment_execution_performed_by_m2963", False, False),
        actor_guard("zero_residual_identity_boundary_preserved", _bool(summary.get("zero_residual_identity_mode", False)), True),
        actor_guard("residual_delta_abs_max", float(summary.get("residual_delta_abs_max", 0.0)), 0.0),
        actor_guard("contract_execution_rows_pass", all(_bool(row.get("status_pass", False)) for row in contract_rows), True),
        actor_guard("training_scheduled", any_flag(combined, "training_scheduled"), False),
        actor_guard("execution_scheduled", any_flag(combined, "execution_scheduled"), False),
        actor_guard("ranking_allowed", any_flag(combined, "ranking_allowed"), False),
        actor_guard("winner_selection_allowed", any_flag(combined, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(combined, "promotion_allowed"), False),
        actor_guard("actor_input_change_required", any_flag(combined, "actor_input_change_required"), False),
        actor_guard("residual_target_signal_actor_visible", any_flag(combined, "residual_target_signal_actor_visible"), False),
        actor_guard("actor_visible_label", any_flag(combined, "actor_visible_label"), False),
        actor_guard("hidden_oracle_actor_input_detected", _bool(summary.get("hidden_oracle_actor_input_detected", False)), False),
        actor_guard("future_target_actor_input_required", _bool(summary.get("future_target_actor_input_required", False)), False),
        actor_guard("route_labels_actor_visible", _bool(summary.get("route_labels_actor_visible", False)), False),
        actor_guard("source_labels_actor_visible", _bool(summary.get("source_labels_actor_visible", False)), False),
        actor_guard("evaluator_labels_actor_visible", _bool(summary.get("evaluator_labels_actor_visible", False)), False),
        actor_guard("diagnostic_labels_actor_visible", _bool(summary.get("diagnostic_labels_actor_visible", False)), False),
        actor_guard("success_progress_labels_actor_visible", _bool(summary.get("success_progress_labels_actor_visible", False)), False),
        actor_guard("verdict_labels_actor_visible", _bool(summary.get("verdict_labels_actor_visible", False)), False),
        actor_guard("guardrail_execution", any_flag(guardrail_rows, "execution_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2963-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    localization_rows_present: bool,
    objective_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("failure_localization_materialized", "artifact", localization_rows_present, "failure_localization_rows.csv"),
        (
            "residual_objective_admission_materialized",
            "artifact",
            objective_rows_present,
            "residual_objective_admission_rows.csv",
        ),
        ("source_milestone_aggregate_materialized", "artifact", artifacts_present, "source_milestone_aggregate.csv"),
        ("task_family_aggregate_materialized", "artifact", artifacts_present, "task_family_aggregate.csv"),
        ("outcome_family_aggregate_materialized", "artifact", artifacts_present, "outcome_family_aggregate.csv"),
        ("guardrail_context_materialized", "artifact", artifacts_present, "guardrail_context_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2964 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_execution", "execution", "no execution in M2963"),
        ("training_or_ppo", "execution", "future audited manifest"),
        ("nonzero_residual_head_training", "execution", "future objective-admitted manifest only"),
        ("dependency_execution", "execution", "future dependency route"),
        ("controller_source_task_checkpoint_candidate_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2963_{claim_id}",
        "claim_family": family,
        "allowed_in_m2963": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]
    contract_rows = source["actor_head_delta_contract_execution_rows"]
    summary = source["m2960_summary"]
    outcome_counts = Counter(outcome_family(row) for row in execution_rows)
    source_milestone_counts = Counter(str(row.get("source_milestone", "")) for row in execution_rows)
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2963"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2963"])]
    admitted_objectives = [row for row in objective_rows if _bool(row.get("admitted_for_m2964_audit", False))]
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2960/M2961/M2962/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m2961_accepts_m2960",
            "lineage",
            "accepts M2960" in source["m2961_audit_text"],
            "accepts M2960" in source["m2961_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2962_admits_m2963",
            "lineage",
            MILESTONE_ID in source["m2962_synthesis_text"],
            MILESTONE_ID in source["m2962_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2960_status_pass",
            "lineage",
            _bool(summary.get("status_pass", False)) and _bool(summary.get("gate_matrix_pass", False)),
            {"status_pass": summary.get("status_pass"), "gate_matrix_pass": summary.get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        (
            "execution_rows_loaded",
            "localization",
            len(execution_rows) == EXPECTED_EXECUTION_ROW_COUNT,
            len(execution_rows),
            EXPECTED_EXECUTION_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "failure_rows_preserved",
            "localization",
            len(failure_rows) == EXPECTED_FAILURE_ROW_COUNT,
            len(failure_rows),
            EXPECTED_FAILURE_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "contract_rows_loaded",
            "contract",
            len(contract_rows) == EXPECTED_CONTRACT_ROW_COUNT and all(_bool(row.get("status_pass", False)) for row in contract_rows),
            f"rows={len(contract_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in contract_rows)}",
            f"{EXPECTED_CONTRACT_ROW_COUNT} rows all pass",
            "contract_violation",
        ),
        (
            "outcome_counts_match_m2960",
            "localization",
            dict(outcome_counts) == EXPECTED_OUTCOME_COUNTS,
            dict(outcome_counts),
            EXPECTED_OUTCOME_COUNTS,
            "metric_artifact",
        ),
        (
            "source_milestone_counts_match_m2960",
            "localization",
            dict(source_milestone_counts) == EXPECTED_SOURCE_MILESTONE_COUNTS,
            dict(source_milestone_counts),
            EXPECTED_SOURCE_MILESTONE_COUNTS,
            "metric_artifact",
        ),
        (
            "localization_rows_account_all",
            "localization",
            len(localization_rows) == len(execution_rows),
            len(localization_rows),
            len(execution_rows),
            "metric_artifact",
        ),
        (
            "source_aggregate_accounts_all",
            "localization",
            sum(int(row["row_count"]) for row in source_rows) == len(execution_rows),
            sum(int(row["row_count"]) for row in source_rows),
            len(execution_rows),
            "metric_artifact",
        ),
        (
            "task_aggregate_accounts_all",
            "localization",
            sum(int(row["row_count"]) for row in task_rows) == len(execution_rows),
            sum(int(row["row_count"]) for row in task_rows),
            len(execution_rows),
            "metric_artifact",
        ),
        (
            "outcome_aggregate_accounts_all",
            "localization",
            sum(int(row["row_count"]) for row in outcome_rows) == len(execution_rows),
            sum(int(row["row_count"]) for row in outcome_rows),
            len(execution_rows),
            "metric_artifact",
        ),
        (
            "objective_admission_rows_present",
            "objective_admission",
            len(objective_rows) >= 3 and len(admitted_objectives) >= 2,
            {"rows": len(objective_rows), "admitted": len(admitted_objectives)},
            ">=3 rows with >=2 admitted for audit",
            "scenario_sampling_failure",
        ),
        (
            "objective_admission_no_execution_or_ranking",
            "contract",
            not any(candidate_forbidden_flag(row) for row in objective_rows),
            "all false",
            "all false",
            "contract_violation",
        ),
        (
            "blocked_stale_guardrails_preserved",
            "guardrail",
            int(summary.get("blocked_stale_guard_row_count", 0)) == EXPECTED_BLOCKED_STALE_GUARD_COUNT
            and not any_flag(guardrail_rows, "execution_run"),
            {"blocked_stale_guard_row_count": summary.get("blocked_stale_guard_row_count"), "guard_execution": any_flag(guardrail_rows, "execution_run")},
            f"{EXPECTED_BLOCKED_STALE_GUARD_COUNT} and no execution",
            "proof_washout",
        ),
        (
            "actor_contract_guards_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_rows)}",
            "all actor guards pass",
            "contract_violation",
        ),
        (
            "no_forbidden_execution_or_overclaim",
            "execution_guardrail",
            not any(forbidden_execution_flag(row) for row in localization_rows + objective_rows + guardrail_rows),
            "no M2963 execution/ranking/promotion/overclaim flags",
            "all false",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in allowed_claims)
            and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims),
            f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}",
            "allowed pass and blocked not made",
            "proof_washout",
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
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2963_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def write_derived_outputs(
    paths: dict[str, Path],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]
    contract_rows = source["actor_head_delta_contract_execution_rows"]
    outcome_counts = Counter(outcome_family(row) for row in execution_rows)
    source_milestone_counts = Counter(str(row.get("source_milestone", "")) for row in execution_rows)
    task_family_counts = Counter(str(row.get("task_family", "")) for row in execution_rows)
    admitted_objectives = [row for row in objective_rows if _bool(row.get("admitted_for_m2964_audit", False))]
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_actor_head_delta_post_zero_residual_"
            "failure_localization_objective_admission_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_actor_head_delta_post_zero_residual_"
            "failure_localization_objective_admission_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2960_status_pass": _bool(source["m2960_summary"].get("status_pass", False)),
        "m2960_gate_matrix_pass": _bool(source["m2960_summary"].get("gate_matrix_pass", False)),
        "m2960_zero_residual_identity_mode": _bool(source["m2960_summary"].get("zero_residual_identity_mode", False)),
        "m2960_residual_delta_abs_max": source["m2960_summary"].get("residual_delta_abs_max", 0.0),
        "execution_row_count": len(execution_rows),
        "bounded_execution_row_count": len(execution_rows),
        "bounded_execution_failure_row_count": len(failure_rows),
        "actor_head_delta_contract_execution_row_count": len(contract_rows),
        "actor_head_delta_contract_execution_rows_pass": all(_bool(row.get("status_pass", False)) for row in contract_rows),
        "outcome_counts": dict(outcome_counts),
        "source_milestone_counts": dict(source_milestone_counts),
        "task_family_counts": dict(task_family_counts),
        "diagnostic_success_count": outcome_counts.get("diagnostic_success", 0),
        "diagnostic_collision_count": outcome_counts.get("collision", 0),
        "diagnostic_offtrack_count": outcome_counts.get("off_track", 0),
        "diagnostic_speed_too_low_count": outcome_counts.get("speed_too_low", 0),
        "failure_localization_row_count": len(localization_rows),
        "residual_objective_admission_row_count": len(objective_rows),
        "residual_objective_admitted_for_audit_count": len(admitted_objectives),
        "source_milestone_aggregate_row_count": len(source_rows),
        "task_family_aggregate_row_count": len(task_rows),
        "outcome_family_aggregate_row_count": len(outcome_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "blocked_stale_guard_row_count": int(source["m2960_summary"].get("blocked_stale_guard_row_count", 0)),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "all_selected_metrics_finite": selected_metrics_are_finite(execution_rows) if execution_rows else False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "nonzero_residual_head_trained": False,
        "nonzero_residual_head_selected": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_simulation_run": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2963 Engineering Controller Route A Actor-Head Delta Post-Zero-Residual Failure Localization Objective Admission Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- execution rows localized: {summary['execution_row_count']}",
            f"- execution failure rows preserved: {summary['bounded_execution_failure_row_count']}",
            f"- outcome counts: {summary['outcome_counts']}",
            f"- failure localization rows: {summary['failure_localization_row_count']}",
            f"- residual objective admission rows: {summary['residual_objective_admission_row_count']}",
            f"- residual objectives admitted for audit: {summary['residual_objective_admitted_for_audit_count']}",
            f"- source milestone aggregate rows: {summary['source_milestone_aggregate_row_count']}",
            f"- task family aggregate rows: {summary['task_family_aggregate_row_count']}",
            f"- outcome family aggregate rows: {summary['outcome_family_aggregate_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2963 materializes no-execution post-zero-residual failure-localization and residual-objective admission rows from M2960 diagnostics. It does not rerun environments, train, select a nonzero residual, rank, promote, or claim performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
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
        "hypothesis": "A bounded result audit can accept or reject the M2963 post-zero-residual failure-localization and residual-objective admission materialization before any repair execution training validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "failure_localization_rows.csv"),
                str(output_dir / "residual_objective_admission_rows.csv"),
                str(output_dir / "source_milestone_aggregate.csv"),
                str(output_dir / "task_family_aggregate.csv"),
                str(output_dir / "outcome_family_aggregate.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2962-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-result-synthesis.md",
            ],
            "parent_config": [
                "experiments/manifests/m2963-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-zero-residual-failure-localization-objective-admission-preflight.json",
                "experiments/manifests/m2962-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-result-synthesis.json",
            ],
            "parent_objective": [
                "audit M2963 post-zero-residual failure-localization and objective-admission materialization artifacts before any route interpretation"
            ],
            "derived_from": [MILESTONE_ID, "m2962-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-bounded-execution-result-synthesis"],
            "blocked_by": [
                "M2963 objective-admission rows require a result audit before any nonzero residual training or execution design",
                "M2960 zero-residual diagnostics remain weak and cannot be interpreted as repair success",
                "11 blocked stale fixed-source rows must remain protected guardrails",
            ],
            "supersedes": [
                "direct interpretation of M2963 residual-objective admission rows without result audit",
                "direct nonzero residual training from M2960 rows without audit",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2964 must audit M2963 summary gate matrix actor and claim boundaries",
            "M2964 must preserve M2960 56 localized rows and 11 blocked stale fixed-source guardrails",
            "M2964 must audit residual-objective admission rows before any nonzero residual training or execution design",
            "M2964 must not claim repair success validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2964 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote publish select a winner or execute dependency work",
            "do not fit train select or execute a nonzero residual head",
            "do not change actor input or action contract",
            "do not convert M2963 localization or objective-admission rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_post_zero_residual_failure_localization_objective_admission_result_audit",
            "evidence_increment": "audits post-zero-residual failure-localization and objective-admission artifacts from M2963",
            "claim_scope": "Result audit only; no validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2963 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if guardrails entered execution or denominators",
                "stop if objective-admission rows would be used as training instructions before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if objective admission is complete but no route candidate is viable",
                "route to a bounded design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2963 completes post-zero-residual failure-localization objective-admission materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2963 actor-head delta post-zero-residual localization and objective-admission artifacts",
            "admission_evidence": [
                "M2963 summary and gate matrix",
                "M2963 failure-localization residual-objective guard actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2964 status queue scoreboard research log and review",
                "one follow-up manifest only if M2964 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2964 audit accepts or rejects M2963 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2964 audits Route A objective admission and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2964; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2963 Route A actor-head delta post-zero-residual materialization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2963 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized post-zero-residual localization and residual-objective admission rows",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2964 cannot accept M2963 as complete and claim-safe",
                "M2964 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2964 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2964 audits M2963 artifacts row counts gates actor and claim boundaries",
            "M2964 selects exactly one next route or stop state",
            "no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2964 hides M2963 failures or missing artifacts",
            "M2964 treats M2963 localization as validation readiness or performance verdict",
            "M2964 changes actor input or action contract",
            "M2964 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2964 audits M2963 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "failure_localization_rows.csv"),
            str(output_dir / "residual_objective_admission_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def dominant_outcome(counts: Counter[str]) -> str:
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def candidate_forbidden_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "execution_scheduled",
            "training_scheduled",
            "ranking_allowed",
            "winner_selection_allowed",
            "promotion_allowed",
            "ordinary_engineering_denominator_allowed",
            "validation_denominator_allowed",
            "paper_denominator_allowed",
            "high_fidelity_readiness_allowed",
            "self_id_claim_allowed",
            "residual_target_signal_actor_visible",
            "actor_input_change_required",
        )
    )


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "environment_reset_run",
            "environment_step_run",
            "policy_action_run",
            "policy_rollout_run",
            "measured_validation_run",
            "training_started",
            "training_scheduled",
            "training_run",
            "replay_started",
            "replay_run",
            "ppo_used",
            "ppo_run",
            "source_build_run",
            "adapter_probe_run",
            "external_simulation_run",
            "dependency_execution_performed",
            "private_holdout_used",
            "ranking_allowed",
            "ranking_run",
            "winner_selection_allowed",
            "winner_selected",
            "promotion_allowed",
            "checkpoint_promoted",
            "actor_input_contract_changed",
            "actor_visible_label",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "guardrail_rows_in_success_denominator",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "validation_readiness_claim_made",
            "validation_result_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
            "full_ideal_driver_completion_claim_made",
            "level3_self_id_claim_made",
        )
    )


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def mean_float(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values: list[float] = []
    for row in rows:
        value = _to_float(row.get(key))
        if np.isfinite(value):
            values.append(value)
    if not values:
        return ""
    return float(sum(values) / len(values))


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2960-dir", type=Path, default=DEFAULT_M2960_DIR)
    parser.add_argument("--m2961-audit", type=Path, default=DEFAULT_M2961_AUDIT)
    parser.add_argument("--m2962-synthesis", type=Path, default=DEFAULT_M2962_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_post_zero_residual_failure_localization_objective_admission_preflight(
        m2960_dir=args.m2960_dir,
        m2961_audit=args.m2961_audit,
        m2962_synthesis=args.m2962_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"execution_rows={summary['execution_row_count']}")
    print(f"residual_objective_admission_rows={summary['residual_objective_admission_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
