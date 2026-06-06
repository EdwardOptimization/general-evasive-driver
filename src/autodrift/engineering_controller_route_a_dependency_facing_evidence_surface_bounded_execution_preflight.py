"""Run M2919 dependency-facing bounded diagnostic execution preflight.

M2919 consumes the M2916/M2917/M2918 dependency-facing admission chain and
runs one bounded current-sim diagnostic rollout, or records one failure row, for
each M2916 admitted row. The run excludes the M2877 fixed weak diagnostic guard
rows and keeps Route B/Route C context outside execution and verdict
denominators. It does not train, rank, validate, promote, or claim driver
performance.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight"
NEXT_ID = "m2920-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-result-audit"
DEFAULT_M2916_DIR = Path(
    "runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight"
)
DEFAULT_M2917_AUDIT = Path(
    "docs/m2917-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-result-audit.md"
)
DEFAULT_M2918_DESIGN = Path(
    "docs/m2918-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2920-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 291900

ADMITTED_STATUS = "execution_admission_admitted_for_separate_bounded_execution_manifest"
BLOCKED_STALE_STATUS = "execution_admission_blocked_stale_fixed_surface"
EXPECTED_TOTAL_CANDIDATE_COUNT = 67
EXPECTED_ADMITTED_COUNT = 56
EXPECTED_M2877_GUARD_COUNT = 11
EXPECTED_SOURCE_MILESTONE_COUNTS = {
    "m2737": 18,
    "m2746": 14,
    "m2807": 12,
    "m2816": 12,
}

CLAIM_SCOPE = (
    "M2919 Route A dependency-facing bounded diagnostic execution preflight "
    "only; reset, step, rollout, and policy action may be recorded for the 56 "
    "M2916 admitted rows, while M2877 fixed weak diagnostic rows, Route B "
    "source-family insufficiency, and Route C source_unavailable rows remain "
    "guardrails or context only. No replay, validation, training, PPO, source "
    "build, adapter probe, external simulation, dependency execution, ranking, "
    "winner selection, promotion, success-rate verdict, driver-performance, "
    "paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full "
    "ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

CANDIDATE_FIELDNAMES = [
    "execution_candidate_id",
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
    "execution_scheduled_in_m2919",
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
    "checkpoint_exists",
    "profile_config_exists",
    "claim_boundary",
]
RESOLUTION_FIELDNAMES = [
    "resolution_id",
    "execution_candidate_id",
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
    "resolved_source_edge",
    "resolved_window_tag",
    "resolved_strata",
    "resolved_executable_source_family",
    "resolved_env_template_family",
    "resolution_status",
    "execution_admitted",
    "execution_planned",
    "failure_reason",
    "actor_contract_shape_72_action_3",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ranking_run",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "resolution_id",
    "execution_candidate_id",
    "execution_admission_candidate_id",
    "source_milestone",
    "source_family",
    "source_row_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "m2919_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "m2877_guard_execution",
    "route_b_context_execution",
    "route_c_context_execution",
    "training_started",
    "replay_started",
    "ppo_used",
    "source_build_run",
    "adapter_probe_run",
    "external_simulation_run",
    "dependency_execution_performed",
    "private_holdout_used",
    "profile_specific_tuning",
    "active_config_overwritten",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "guardrail_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
EXECUTION_FIELDNAMES = [
    "seed",
    "policy",
    "steps",
    "terminated",
    "truncated",
    "collision",
    "obstacle_completed",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "termination_reason",
    "completion_reason",
    "outcome_bucket",
    "return",
    "mean_reward",
    "lateral_rmse",
    "beta_abs_error_mean",
    "high_sideslip_fraction",
    "speed_mean",
    "action_rate_mean",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "recoverability_window_success",
    "recoverability_window_success_available",
    "success",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "profile_config_path",
    "checkpoint_path",
    "profile_env_history_length",
    "eval_seed",
    "m2919_eval_seed",
    "resolution_id",
    "execution_candidate_id",
    "execution_admission_candidate_id",
    "source_milestone",
    "source_family",
    "source_row_id",
    "dependency_facing_bounded_execution_preflight",
    "candidate_surface_count",
    "m2877_guard_execution",
    "route_b_context_execution",
    "route_c_context_execution",
    "guardrail_rows_in_success_denominator",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "profile_specific_tuning",
    "active_config_overwritten",
    "dependency_execution_performed",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
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
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "aggregate_value",
    "candidate_count",
    "resolved_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "diagnostic_success_count",
    "diagnostic_collision_count",
    "diagnostic_offtrack_count",
    "diagnostic_speed_too_low_count",
    "min_clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_context_id",
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
    "allowed_in_m2919",
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
    "execution_candidate_rows",
    "execution_resolution_rows",
    "bounded_execution_rows",
    "bounded_execution_failure_rows",
    "source_milestone_aggregate",
    "task_family_aggregate",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_dependency_facing_bounded_execution_preflight(
    *,
    m2916_dir: Path | str = DEFAULT_M2916_DIR,
    m2917_audit: Path | str = DEFAULT_M2917_AUDIT,
    m2918_design: Path | str = DEFAULT_M2918_DESIGN,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2916_dir=Path(m2916_dir),
        m2917_audit=Path(m2917_audit),
        m2918_design=Path(m2918_design),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )

    candidate_rows = build_execution_candidate_rows(source["m2916_candidate_rows"])
    write_csv_rows(paths["execution_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    resolution_rows, resolved_workloads = build_resolution_rows(source, candidate_rows)
    write_csv_rows(paths["execution_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)

    execution_summary = run_candidate_execution(
        resolution_rows=resolution_rows,
        resolved_workloads=resolved_workloads,
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    artifact_rows = load_execution_artifact_rows(paths)
    source_aggregate_rows = build_aggregate_rows(
        aggregate_family="source_milestone",
        key="source_milestone",
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["bounded_execution_rows"],
        failure_rows=artifact_rows["bounded_execution_failure_rows"],
    )
    task_aggregate_rows = build_aggregate_rows(
        aggregate_family="task_family",
        key="task_family",
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["bounded_execution_rows"],
        failure_rows=artifact_rows["bounded_execution_failure_rows"],
    )
    guardrail_rows = build_guardrail_context_rows(
        source["m2916_guardrail_context_rows"],
        source["m2916_rejection_rows"],
    )
    write_csv_rows(paths["source_milestone_aggregate"], source_aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["task_family_aggregate"], task_aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["bounded_execution_rows"],
        failure_rows=artifact_rows["bounded_execution_failure_rows"],
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        episode_rows_present=bool(artifact_rows["bounded_execution_rows"]),
        episode_or_failure_rows_present=bool(
            artifact_rows["bounded_execution_rows"] or artifact_rows["bounded_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, guardrail_rows, actor_rows, claim_rows, gate_rows)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        source_aggregate_rows=source_aggregate_rows,
        task_aggregate_rows=task_aggregate_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    artifact_rows = load_execution_artifact_rows(paths)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_rows_present=bool(artifact_rows["bounded_execution_rows"]),
        episode_or_failure_rows_present=bool(
            artifact_rows["bounded_execution_rows"] or artifact_rows["bounded_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
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
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        source_aggregate_rows=source_aggregate_rows,
        task_aggregate_rows=task_aggregate_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "execution_candidate_rows": output_dir / "execution_candidate_rows.csv",
        "execution_resolution_rows": output_dir / "execution_resolution_rows.csv",
        "bounded_execution_rows": output_dir / "bounded_execution_rows.csv",
        "bounded_execution_failure_rows": output_dir / "bounded_execution_failure_rows.csv",
        "source_milestone_aggregate": output_dir / "source_milestone_aggregate.csv",
        "task_family_aggregate": output_dir / "task_family_aggregate.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2916_dir: Path,
    m2917_audit: Path,
    m2918_design: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2917_audit": m2917_audit,
        "m2918_design": m2918_design,
        "m2916_summary": m2916_dir / "summary.json",
        "m2916_candidate_rows": m2916_dir / "execution_admission_candidate_rows.csv",
        "m2916_rejection_rows": m2916_dir / "execution_admission_rejection_rows.csv",
        "m2916_guardrail_context_rows": m2916_dir / "guardrail_context_rows.csv",
        "m2916_actor_contract_guard_rows": m2916_dir / "actor_contract_guard_rows.csv",
        "m2916_claim_boundary_rows": m2916_dir / "claim_boundary_rows.csv",
        "m2916_gate_matrix": m2916_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "executable_workload": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2917_audit_text": paths["m2917_audit"].read_text(encoding="utf-8")
        if source_exists["m2917_audit"]
        else "",
        "m2918_design_text": paths["m2918_design"].read_text(encoding="utf-8")
        if source_exists["m2918_design"]
        else "",
        "m2916_summary": read_json(paths["m2916_summary"]) if source_exists["m2916_summary"] else {},
        "m2916_candidate_rows": read_csv_rows(paths["m2916_candidate_rows"]),
        "m2916_rejection_rows": read_csv_rows(paths["m2916_rejection_rows"]),
        "m2916_guardrail_context_rows": read_csv_rows(paths["m2916_guardrail_context_rows"]),
        "m2916_actor_contract_guard_rows": read_csv_rows(paths["m2916_actor_contract_guard_rows"]),
        "m2916_claim_boundary_rows": read_csv_rows(paths["m2916_claim_boundary_rows"]),
        "m2916_gate_matrix": read_csv_rows(paths["m2916_gate_matrix"]),
        "executable_workload_rows": read_csv_rows(paths["executable_workload"]),
    }


def build_execution_candidate_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        [row for row in candidate_rows if str(row.get("execution_admission_status", "")) == ADMITTED_STATUS],
        start=1,
    ):
        candidate = {key: row.get(key, "") for key in CANDIDATE_FIELDNAMES}
        candidate.update(
            {
                "execution_candidate_id": f"m2919-execution-candidate-{index:04d}",
                "execution_admission_candidate_id": row.get("execution_admission_candidate_id", ""),
                "execution_scheduled_in_m2919": True,
                "environment_reset_admitted": True,
                "environment_rollout_scheduled": True,
                "measured_validation_scheduled": False,
                "training_scheduled": False,
                "dependency_execution_scheduled": False,
                "profile_specific_tuning": False,
                "actor_observation_dim": int(row.get("actor_observation_dim", P0_OBSERVATION_DIM)),
                "actor_action_dim": int(row.get("actor_action_dim", ACTION_DIM)),
                "actor_input_contract_changed": _bool(row.get("actor_input_contract_changed", False)),
                "hidden_oracle_actor_input_required": _bool(row.get("hidden_oracle_actor_input_required", False)),
                "future_target_actor_input_required": _bool(row.get("future_target_actor_input_required", False)),
                "route_labels_actor_visible": _bool(row.get("route_labels_actor_visible", False)),
                "source_labels_actor_visible": _bool(row.get("source_labels_actor_visible", False)),
                "diagnostic_labels_actor_visible": _bool(row.get("diagnostic_labels_actor_visible", False)),
                "success_progress_labels_actor_visible": _bool(row.get("success_progress_labels_actor_visible", False)),
                "verdict_labels_actor_visible": _bool(row.get("verdict_labels_actor_visible", False)),
                "ordinary_engineering_denominator_allowed_after_audit": _bool(
                    row.get("ordinary_engineering_denominator_allowed_after_audit", False)
                ),
                "validation_denominator_allowed": _bool(row.get("validation_denominator_allowed", False)),
                "paper_denominator_allowed": _bool(row.get("paper_denominator_allowed", False)),
                "high_fidelity_readiness_allowed": _bool(row.get("high_fidelity_readiness_allowed", False)),
                "self_id_claim_allowed": _bool(row.get("self_id_claim_allowed", False)),
                "diagnostic_only_no_verdict": True,
                "checkpoint_exists": Path(str(row.get("checkpoint_path", ""))).exists(),
                "profile_config_exists": Path(str(row.get("profile_config_path", ""))).exists(),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        rows.append(candidate)
    return rows


def build_resolution_rows(
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    workload_by_id = {str(row.get("workload_id", "")): row for row in source["executable_workload_rows"]}
    rows: list[dict[str, Any]] = []
    resolved_workloads: dict[str, dict[str, Any]] = {}
    for index, candidate in enumerate(candidate_rows, start=1):
        workload = workload_by_id.get(str(candidate.get("workload_id", "")))
        failure_reason = ""
        if str(candidate.get("source_milestone", "")) == "m2877":
            failure_reason = "m2877_guard_row_rejected"
        elif str(candidate.get("execution_admission_status", "")) != ADMITTED_STATUS:
            failure_reason = "m2916_candidate_not_admitted"
        elif int(candidate.get("actor_observation_dim", -1)) != P0_OBSERVATION_DIM:
            failure_reason = "actor_observation_dim_mismatch"
        elif int(candidate.get("actor_action_dim", -1)) != ACTION_DIM:
            failure_reason = "actor_action_dim_mismatch"
        elif _bool(candidate.get("actor_input_contract_changed", False)):
            failure_reason = "actor_input_contract_changed"
        elif _bool(candidate.get("hidden_oracle_actor_input_required", False)):
            failure_reason = "hidden_oracle_actor_input_required"
        elif _bool(candidate.get("future_target_actor_input_required", False)):
            failure_reason = "future_target_actor_input_required"
        elif any(
            _bool(candidate.get(field, False))
            for field in (
                "route_labels_actor_visible",
                "source_labels_actor_visible",
                "diagnostic_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
            )
        ):
            failure_reason = "actor_visible_diagnostic_or_verdict_label"
        elif not _bool(candidate.get("ordinary_engineering_denominator_allowed_after_audit", False)):
            failure_reason = "ordinary_engineering_denominator_not_admitted_after_audit"
        elif any(
            _bool(candidate.get(field, False))
            for field in (
                "validation_denominator_allowed",
                "paper_denominator_allowed",
                "high_fidelity_readiness_allowed",
                "self_id_claim_allowed",
            )
        ):
            failure_reason = "protected_denominator_or_claim_allowed"
        elif not _bool(candidate.get("checkpoint_exists", False)):
            failure_reason = "checkpoint_path_missing"
        elif not _bool(candidate.get("profile_config_exists", False)):
            failure_reason = "profile_config_path_missing"
        elif workload is None:
            failure_reason = "workload_id_missing_from_m1690_matrix"
        elif str(workload.get("task_source_id", "")) != str(candidate.get("task_source_id", "")):
            failure_reason = "workload_task_source_mismatch"
        elif str(workload.get("profile_name", "")) != str(candidate.get("profile_name", "")):
            failure_reason = "workload_profile_mismatch"

        execution_admitted = not failure_reason
        resolution_id = f"m2919-resolution-{index:04d}"
        resolved_workload = dict(workload or {})
        if execution_admitted:
            resolved_workload.update(
                {
                    "checkpoint_path": candidate.get("checkpoint_path", ""),
                    "profile_config_path": candidate.get("profile_config_path", ""),
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "profile_specific_tuning": False,
                    "environment_rollout_scheduled": True,
                    "training_scheduled": False,
                }
            )
            resolved_workloads[resolution_id] = resolved_workload

        row = {
            "resolution_id": resolution_id,
            "execution_candidate_id": candidate.get("execution_candidate_id", ""),
            "execution_admission_candidate_id": candidate.get("execution_admission_candidate_id", ""),
            "source_milestone": candidate.get("source_milestone", ""),
            "source_artifact": candidate.get("source_artifact", ""),
            "source_row_id": candidate.get("source_row_id", ""),
            "source_family": candidate.get("source_family", ""),
            "task_family": candidate.get("task_family", ""),
            "workload_id": candidate.get("workload_id", ""),
            "task_source_id": candidate.get("task_source_id", ""),
            "profile_name": candidate.get("profile_name", ""),
            "checkpoint_path": candidate.get("checkpoint_path", ""),
            "profile_config_path": candidate.get("profile_config_path", ""),
            "resolved_source_edge": resolved_workload.get("source_edge", ""),
            "resolved_window_tag": resolved_workload.get("window_tag", ""),
            "resolved_strata": resolved_workload.get("strata", ""),
            "resolved_executable_source_family": resolved_workload.get("executable_source_family", ""),
            "resolved_env_template_family": resolved_workload.get("env_template_family", ""),
            "resolution_status": "resolved_to_m1690_workload" if execution_admitted else "accounted_by_failure",
            "execution_admitted": execution_admitted,
            "execution_planned": execution_admitted,
            "failure_reason": failure_reason,
            "actor_contract_shape_72_action_3": True,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
            "route_labels_actor_visible": False,
            "source_labels_actor_visible": False,
            "diagnostic_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "ranking_run": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
    return rows, resolved_workloads


def run_candidate_execution(
    *,
    resolution_rows: list[dict[str, Any]],
    resolved_workloads: dict[str, dict[str, Any]],
    output_dir: Path,
    executable_specs_path: Path,
    eval_seed_base: int,
    device: str,
    resume: bool,
    next_blocker: str,
) -> dict[str, Any]:
    if not resume:
        for name in ("bounded_execution_rows.csv", "bounded_execution_failure_rows.csv", "run_state.json"):
            path = output_dir / name
            if path.exists():
                path.unlink()

    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    episode_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for index, resolution in enumerate(resolution_rows):
        eval_seed = int(eval_seed_base) + index
        resolution_id = str(resolution.get("resolution_id", ""))
        try:
            if not _bool(resolution.get("execution_admitted", False)):
                raise ValueError(str(resolution.get("failure_reason", "candidate resolution not admitted")))
            workload = resolved_workloads[resolution_id]
            task_source_id = str(workload["task_source_id"])
            if task_source_id not in spec_by_id:
                raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
            profile_name = str(workload["profile_name"])
            config_path = str(workload["profile_config_path"])
            checkpoint_path = str(workload["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in profile_cache:
                profile_config = read_json(config_path)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                profile_cache[cache_key] = (
                    profile_config,
                    model,
                    {"profile_name": profile_name, "config_path": config_path, "checkpoint_path": checkpoint_path},
                )
            profile_config, model, profile_row = profile_cache[cache_key]
            row = run_workload_cell(
                workload_row=workload,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(execution_metadata(resolution, eval_seed=eval_seed))
            episode_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every admitted candidate must be accounted.
            failure_rows.append(
                failure_row(
                    resolution,
                    eval_seed=eval_seed,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "candidate_count": len(resolution_rows),
                "completed_execution_count": len(episode_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(episode_rows) + len(failure_rows),
                "latest_resolution_id": resolution_id,
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    write_csv_rows(
        output_dir / "bounded_execution_rows.csv",
        [_normalized_execution_row(row) for row in episode_rows],
        fieldnames=EXECUTION_FIELDNAMES,
    )
    write_csv_rows(output_dir / "bounded_execution_failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(resolution_rows) == EXPECTED_ADMITTED_COUNT
        and len(episode_rows) + len(failure_rows) == len(resolution_rows)
        and bool(episode_rows)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    write_run_state(
        output_dir / "run_state.json",
        {
            "candidate_count": len(resolution_rows),
            "completed_execution_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(episode_rows) + len(failure_rows),
            "complete": len(episode_rows) + len(failure_rows) == len(resolution_rows),
            "status_pass": status_pass,
            "next_blocker": next_blocker,
        },
    )
    return {
        "result_class": (
            "engineering_controller_route_a_dependency_facing_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_dependency_facing_bounded_execution_preflight_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(resolution_rows),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "accounted_count": len(episode_rows) + len(failure_rows),
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }


def execution_metadata(resolution: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "m2919_eval_seed": int(eval_seed),
        "resolution_id": resolution.get("resolution_id", ""),
        "execution_candidate_id": resolution.get("execution_candidate_id", ""),
        "execution_admission_candidate_id": resolution.get("execution_admission_candidate_id", ""),
        "source_milestone": resolution.get("source_milestone", ""),
        "source_family": resolution.get("source_family", ""),
        "source_row_id": resolution.get("source_row_id", ""),
        "dependency_facing_bounded_execution_preflight": True,
        "candidate_surface_count": EXPECTED_ADMITTED_COUNT,
        "m2877_guard_execution": False,
        "route_b_context_execution": False,
        "route_c_context_execution": False,
        "guardrail_rows_in_success_denominator": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "route_labels_actor_visible": False,
        "source_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "diagnostic_only_no_verdict": True,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "dependency_execution_performed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def _normalized_execution_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in EXECUTION_FIELDNAMES}


def failure_row(
    resolution: Mapping[str, Any],
    *,
    eval_seed: int,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    row = {key: False for key in FAILURE_FIELDNAMES}
    row.update(
        {
            "resolution_id": resolution.get("resolution_id", ""),
            "execution_candidate_id": resolution.get("execution_candidate_id", ""),
            "execution_admission_candidate_id": resolution.get("execution_admission_candidate_id", ""),
            "source_milestone": resolution.get("source_milestone", ""),
            "source_family": resolution.get("source_family", ""),
            "source_row_id": resolution.get("source_row_id", ""),
            "workload_id": resolution.get("workload_id", ""),
            "task_source_id": resolution.get("task_source_id", ""),
            "profile_name": resolution.get("profile_name", ""),
            "task_family": resolution.get("task_family", ""),
            "m2919_eval_seed": int(eval_seed),
            "error_type": error_type,
            "error_message": error_message,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
        "bounded_execution_failure_rows": read_csv_rows(paths["bounded_execution_failure_rows"]),
    }


def build_aggregate_rows(
    *,
    aggregate_family: str,
    key: str,
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    values = sorted({str(row.get(key, "")) for row in candidate_rows if str(row.get(key, ""))})
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(values, start=1):
        candidates = [row for row in candidate_rows if str(row.get(key, "")) == value]
        resolutions = [row for row in resolution_rows if str(row.get(key, "")) == value]
        episodes = [row for row in episode_rows if str(row.get(key, "")) == value]
        failures = [row for row in failure_rows if str(row.get(key, "")) == value]
        termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
        rows.append(
            {
                "aggregate_id": f"m2919-{aggregate_family}-aggregate-{index:04d}",
                "aggregate_family": aggregate_family,
                "aggregate_value": value,
                "candidate_count": len(candidates),
                "resolved_count": sum(_bool(row.get("execution_admitted", False)) for row in resolutions),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in episodes),
                "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in episodes),
                "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
                "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
                "min_clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else False,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(
    guardrail_context_rows: list[dict[str, str]],
    rejection_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(guardrail_context_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2919-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": "",
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": 1,
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
    offset = len(rows)
    for index, row in enumerate(rejection_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2919-guardrail-context-{offset + index:04d}",
                "guardrail_source": "m2916_execution_admission_rejection_rows",
                "guardrail_family": row.get("rejection_type", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("candidate_or_source_id", ""),
                "guardrail_reason": row.get("rejection_reason", ""),
                "row_count": 1,
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
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = candidate_rows + resolution_rows + episode_rows + failure_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("actor_input_contract_changed", any_flag(combined, "actor_input_contract_changed"), False),
        actor_guard("hidden_oracle_actor_input_required", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", any_flag(combined, "future_target_actor_input_required"), False),
        actor_guard("route_labels_actor_visible", any_flag(combined, "route_labels_actor_visible"), False),
        actor_guard("source_labels_actor_visible", any_flag(combined, "source_labels_actor_visible"), False),
        actor_guard("diagnostic_labels_actor_visible", any_flag(combined, "diagnostic_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", any_flag(combined, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(combined, "verdict_labels_actor_visible"), False),
        actor_guard("m2877_guard_execution", any_flag(combined, "m2877_guard_execution") or any_flag(guardrail_rows, "execution_run"), False),
        actor_guard("route_b_context_execution", any_flag(combined, "route_b_context_execution"), False),
        actor_guard("route_c_context_execution", any_flag(combined, "route_c_context_execution"), False),
        actor_guard("guardrail_rows_in_success_denominator", any_flag(combined, "guardrail_rows_in_success_denominator"), False),
        actor_guard("profile_specific_tuning", any_flag(combined, "profile_specific_tuning"), False),
        actor_guard("active_config_overwritten", any_flag(combined, "active_config_overwritten"), False),
        actor_guard("dependency_execution_performed", any_flag(combined, "dependency_execution_performed"), False),
        actor_guard("ranking_run", any_flag(combined, "ranking_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2919-actor-guard-{field}",
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
    episode_rows_present: bool,
    episode_or_failure_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("bounded_execution_preflight", "execution", episode_or_failure_rows_present, "bounded execution/failure rows"),
        ("execution_candidates_materialized", "artifact", artifacts_present, "execution_candidate_rows.csv"),
        ("candidate_resolution_materialized", "artifact", artifacts_present, "execution_resolution_rows.csv"),
        ("bounded_execution_rows_materialized", "artifact", artifacts_present, "bounded_execution_rows.csv"),
        ("bounded_failure_rows_materialized", "artifact", artifacts_present, "bounded_execution_failure_rows.csv"),
        ("source_aggregate_materialized", "artifact", artifacts_present, "source_milestone_aggregate.csv"),
        ("task_family_aggregate_materialized", "artifact", artifacts_present, "task_family_aggregate.csv"),
        ("guardrail_context_materialized", "artifact", artifacts_present, "guardrail_context_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", episode_rows_present, "diagnostic fields only"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2920 audit manifest"),
    ]
    blocked = [
        ("m2877_guard_execution", "execution", "M2877 rows remain guardrail only"),
        ("route_b_context_execution", "execution", "Route B remains source-family-insufficient context"),
        ("route_c_context_execution", "execution", "Route C remains source_unavailable context"),
        ("replay_validation_training_ppo", "execution", "future manifest"),
        ("source_build_adapter_external_sim", "execution", "future dependency route"),
        ("controller_or_source_family_ranking", "ranking", "future audited comparison route"),
        ("profile_or_task_family_ranking", "ranking", "future audited comparison route"),
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
        "claim_id": f"m2919_{claim_id}",
        "claim_family": family,
        "allowed_in_m2919": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["bounded_execution_rows"]
    failure_rows = artifact_rows["bounded_execution_failure_rows"]
    source_status_counts = Counter(str(row.get("execution_admission_status", "")) for row in source["m2916_candidate_rows"])
    admitted_source_counts = Counter(str(row.get("source_milestone", "")) for row in candidate_rows)
    m2877_rejection_count = sum(
        str(row.get("source_milestone", "")) == "m2877"
        and str(row.get("rejection_type", "")) == BLOCKED_STALE_STATUS
        for row in source["m2916_rejection_rows"]
    )
    accounted_ids = {
        str(row.get("execution_candidate_id", ""))
        for row in episode_rows + failure_rows
        if row.get("execution_candidate_id")
    }
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2919"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2919"])]
    route_b_context = any("route_b" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    route_c_context = any("route_c" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2916/M2917/M2918/M1690/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m2917_accepts_m2916",
            "lineage",
            "accepts M2916" in source["m2917_audit_text"],
            "accepts M2916" in source["m2917_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2918_admits_m2919",
            "lineage",
            MILESTONE_ID in source["m2918_design_text"],
            MILESTONE_ID in source["m2918_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2916_status_pass",
            "lineage",
            _bool(source["m2916_summary"].get("status_pass", False))
            and _bool(source["m2916_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2916_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2916_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2916_candidate_rows_loaded",
            "candidate_resolution",
            len(source["m2916_candidate_rows"]) == EXPECTED_TOTAL_CANDIDATE_COUNT,
            len(source["m2916_candidate_rows"]),
            EXPECTED_TOTAL_CANDIDATE_COUNT,
            "metric_artifact",
        ),
        (
            "m2916_admitted_candidate_count",
            "candidate_resolution",
            source_status_counts.get(ADMITTED_STATUS, 0) == EXPECTED_ADMITTED_COUNT
            and len(candidate_rows) == EXPECTED_ADMITTED_COUNT,
            {"source": dict(source_status_counts), "m2919_candidates": len(candidate_rows)},
            EXPECTED_ADMITTED_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "m2916_m2877_guard_count",
            "guardrail",
            source_status_counts.get(BLOCKED_STALE_STATUS, 0) == EXPECTED_M2877_GUARD_COUNT
            and m2877_rejection_count == EXPECTED_M2877_GUARD_COUNT,
            {"blocked_status": source_status_counts.get(BLOCKED_STALE_STATUS, 0), "rejections": m2877_rejection_count},
            EXPECTED_M2877_GUARD_COUNT,
            "metric_artifact",
        ),
        (
            "source_milestone_distribution",
            "candidate_resolution",
            dict(admitted_source_counts) == EXPECTED_SOURCE_MILESTONE_COUNTS,
            dict(admitted_source_counts),
            EXPECTED_SOURCE_MILESTONE_COUNTS,
            "scenario_sampling_failure",
        ),
        (
            "candidate_actor_contract_preserved",
            "contract",
            not any(candidate_contract_violation(row) for row in candidate_rows),
            "no actor or protected denominator violation",
            "all false",
            "contract_violation",
        ),
        (
            "candidate_resolution_accounts_all",
            "candidate_resolution",
            len(resolution_rows) == len(candidate_rows),
            len(resolution_rows),
            len(candidate_rows),
            "lineage_invalid",
        ),
        (
            "execution_accounts_all_candidates",
            "execution",
            len(accounted_ids) == len(candidate_rows),
            len(accounted_ids),
            len(candidate_rows),
            "scenario_sampling_failure",
        ),
        (
            "execution_rows_present",
            "execution",
            bool(episode_rows),
            len(episode_rows),
            ">0",
            "scenario_sampling_failure",
        ),
        (
            "all_selected_metrics_finite",
            "metric",
            selected_metrics_are_finite(episode_rows) if episode_rows else False,
            execution_summary.get("all_selected_metrics_finite"),
            True,
            "metric_artifact",
        ),
        (
            "m2877_guard_rows_not_executed",
            "guardrail",
            not any(str(row.get("source_milestone", "")) == "m2877" for row in candidate_rows + episode_rows + failure_rows)
            and not any(_bool(row.get("execution_run", False)) for row in guardrail_rows if str(row.get("source_milestone", "")) == "m2877"),
            "m2877 absent from candidates/execution and guard execution false",
            "all false",
            "contract_violation",
        ),
        (
            "route_b_c_context_preserved",
            "guardrail",
            route_b_context and route_c_context and not any_flag(episode_rows + failure_rows, "route_b_context_execution")
            and not any_flag(episode_rows + failure_rows, "route_c_context_execution"),
            {"route_b_context": route_b_context, "route_c_context": route_c_context},
            "both present and not executed",
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
            not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows),
            "no train/replay/PPO/dependency/ranking/promotion/overclaim flags",
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


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2919_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def write_derived_outputs(
    paths: dict[str, Path],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    source_aggregate_rows: list[dict[str, Any]],
    task_aggregate_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    episode_rows = artifact_rows["bounded_execution_rows"]
    failure_rows = artifact_rows["bounded_execution_failure_rows"]
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    admitted_source_counts = Counter(str(row.get("source_milestone", "")) for row in candidate_rows)
    status_counts = Counter(str(row.get("execution_admission_status", "")) for row in source["m2916_candidate_rows"])
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_dependency_facing_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_dependency_facing_bounded_execution_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2916_status_pass": _bool(source["m2916_summary"].get("status_pass", False)),
        "m2916_gate_matrix_pass": _bool(source["m2916_summary"].get("gate_matrix_pass", False)),
        "m2916_candidate_row_count": len(source["m2916_candidate_rows"]),
        "m2916_status_counts": dict(status_counts),
        "candidate_count": len(candidate_rows),
        "expected_candidate_count": EXPECTED_ADMITTED_COUNT,
        "m2877_guard_row_count": status_counts.get(BLOCKED_STALE_STATUS, 0),
        "source_milestone_counts": dict(admitted_source_counts),
        "resolved_candidate_count": sum(_bool(row.get("execution_admitted", False)) for row in resolution_rows),
        "bounded_execution_row_count": len(episode_rows),
        "bounded_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": len(
            {
                str(row.get("execution_candidate_id", ""))
                for row in episode_rows + failure_rows
                if row.get("execution_candidate_id")
            }
        ),
        "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in episode_rows),
        "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in episode_rows),
        "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
        "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "source_milestone_aggregate_row_count": len(source_aggregate_rows),
        "task_family_aggregate_row_count": len(task_aggregate_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "execution_summary_result_class": execution_summary.get("result_class", ""),
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else False,
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_dependency_facing_execution_preflight": bool(episode_rows),
        "m2877_guard_execution": False,
        "route_b_context_execution": False,
        "route_c_context_execution": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any_flag(episode_rows + failure_rows, "hidden_oracle_actor_input_required"),
        "future_target_actor_input_required": any_flag(episode_rows + failure_rows, "future_target_actor_input_required"),
        "route_labels_actor_visible": any_flag(episode_rows + failure_rows, "route_labels_actor_visible"),
        "source_labels_actor_visible": any_flag(episode_rows + failure_rows, "source_labels_actor_visible"),
        "diagnostic_labels_actor_visible": any_flag(episode_rows + failure_rows, "diagnostic_labels_actor_visible"),
        "success_progress_labels_actor_visible": any_flag(episode_rows + failure_rows, "success_progress_labels_actor_visible"),
        "verdict_labels_actor_visible": any_flag(episode_rows + failure_rows, "verdict_labels_actor_visible"),
        "guardrail_rows_in_success_denominator": any_flag(episode_rows + failure_rows, "guardrail_rows_in_success_denominator"),
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_metric_recorded": bool(episode_rows),
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
            "# M2919 Engineering Controller Route A Dependency-Facing Evidence Surface Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rows: {summary['candidate_count']}",
            f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['candidate_count']}",
            f"- bounded execution rows: {summary['bounded_execution_row_count']}",
            f"- failure rows: {summary['bounded_execution_failure_row_count']}",
            f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
            f"- source split: {summary['source_milestone_counts']}",
            f"- M2877 guard rows excluded: {summary['m2877_guard_row_count']}",
            f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
            f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2919 records bounded closed-loop diagnostic data only for resolved M2916 admitted rows. M2877 fixed weak diagnostic rows remain guardrails. Route B source-family insufficiency and Route C source_unavailable remain context only.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2919 dependency-facing bounded execution preflight before any validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "execution_candidate_rows.csv"),
                str(output_dir / "execution_resolution_rows.csv"),
                str(output_dir / "bounded_execution_rows.csv"),
                str(output_dir / "bounded_execution_failure_rows.csv"),
                str(output_dir / "source_milestone_aggregate.csv"),
                str(output_dir / "task_family_aggregate.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2918-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight.json",
                "experiments/manifests/m2918-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-design.json",
            ],
            "parent_objective": [
                "audit M2919 bounded diagnostic execution artifacts before any interpretation"
            ],
            "derived_from": [MILESTONE_ID, "m2918-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-design"],
            "blocked_by": [
                "M2919 diagnostics require a result audit before any verdict or continuation decision",
                "M2877 guard rows Route B source-family insufficiency and Route C source_unavailable must remain protected context",
            ],
            "supersedes": ["direct interpretation of M2919 diagnostic rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2920 must audit M2919 summary gate matrix actor and claim boundaries",
            "M2920 must preserve M2877 Route B Route C guardrail exclusions",
            "M2920 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2920 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not fetch clone configure build install import link probe or start an external backend",
            "do not change actor input or action contract",
            "do not convert M2919 diagnostic rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_bounded_execution_result_audit",
            "evidence_increment": "audits bounded diagnostic execution artifacts from M2919",
            "claim_scope": "Result audit only; no validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2919 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if M2877 Route B or Route C guardrails entered execution or denominators",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if diagnostics are complete but negative or insufficient",
                "route to a new bounded evidence surface only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2919 completes bounded diagnostic execution preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2919 bounded diagnostic execution preflight artifacts",
            "admission_evidence": [
                "M2919 summary and gate matrix",
                "M2919 execution candidate resolution execution failure aggregate guard actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2920 status queue scoreboard research log and review",
                "one follow-up manifest only if M2920 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2920 audit accepts or rejects M2919 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2920 audits Route A engineering diagnostics and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2920; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2919 Route A dependency-facing diagnostic execution only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2919 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly generated Route A dependency-facing closed-loop diagnostics",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2920 cannot accept M2919 as complete and claim-safe",
                "M2920 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2920 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2920 audits M2919 artifacts row counts gates actor and claim boundaries",
            "M2920 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2920 hides M2919 failures or missing artifacts",
            "M2920 treats M2919 diagnostics as validation readiness or performance verdict",
            "M2920 changes actor input or action contract",
            "M2920 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2920 audits M2919 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "bounded_execution_rows.csv"),
            str(output_dir / "bounded_execution_failure_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def candidate_contract_violation(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "validation_denominator_allowed",
            "paper_denominator_allowed",
            "high_fidelity_readiness_allowed",
            "self_id_claim_allowed",
        )
    ) or int(row.get("actor_observation_dim", -1)) != P0_OBSERVATION_DIM or int(row.get("actor_action_dim", -1)) != ACTION_DIM


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "training_started",
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
            "profile_specific_tuning",
            "active_config_overwritten",
            "ranking_run",
            "winner_selected",
            "checkpoint_promoted",
            "promoted",
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "m2877_guard_execution",
            "route_b_context_execution",
            "route_c_context_execution",
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
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    if not values:
        return ""
    return float(sum(values) / len(values))


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
    parser.add_argument("--m2916-dir", type=Path, default=DEFAULT_M2916_DIR)
    parser.add_argument("--m2917-audit", type=Path, default=DEFAULT_M2917_AUDIT)
    parser.add_argument("--m2918-design", type=Path, default=DEFAULT_M2918_DESIGN)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_dependency_facing_bounded_execution_preflight(
        m2916_dir=args.m2916_dir,
        m2917_audit=args.m2917_audit,
        m2918_design=args.m2918_design,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"bounded_execution_rows={summary['bounded_execution_row_count']}")
    print(f"failure_rows={summary['bounded_execution_failure_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
