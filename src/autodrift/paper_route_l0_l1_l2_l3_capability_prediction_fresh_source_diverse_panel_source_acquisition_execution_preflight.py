"""Run M2908 source-acquisition execution preflight.

M2908 consumes the fixed M2905 acquisition-required rows and executes one
bounded diagnostic rollout for each row resolved through the existing M1690
`L3_online_gru` workload. The result is source-acquisition accounting only:
candidate/source-family evidence, explicit execution failures, projections for
M2909 audit, and boundary rows. It is not validation, ranking, model-quality,
paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or
self-ID evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-acquisition-execution-preflight"
)
NEXT_ID = (
    "m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-acquisition-execution-result-audit"
)
DEFAULT_M2907_SYNTHESIS = Path(
    "docs/m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-execution-or-pivot-synthesis.md"
)
DEFAULT_M2905_DIR = Path(
    "runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_repair_source_acquisition_materialization_preflight"
)
DEFAULT_M2906_AUDIT = Path(
    "docs/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-materialization-result-audit.md"
)
DEFAULT_M1690_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/"
    "executable_workload_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2908_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_source_acquisition_execution_preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2909-paper-route-l0-l1-l2-l3-capability-prediction-"
    "fresh-source-diverse-panel-source-acquisition-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 290800
EXPECTED_ACQUISITION_ROW_COUNT = 34
CANONICAL_PROFILE = "L3_online_gru"
CLAIM_SCOPE = (
    "source_acquisition_execution_preflight_only_no_validation_no_model_quality_"
    "no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_validation_not_paper_proof_not_model_quality_not_driver_performance_"
    "not_current_sim_not_high_fidelity_not_full_driver_not_finite_window_vs_gru_"
    "not_self_id"
)
DESIGN_TARGETS = {
    "fresh_candidate_task_count": 24,
    "fresh_candidate_profile_task_count": 288,
    "source_family_count": 3,
    "task_family_count": 2,
    "max_single_source_family_share": 0.40,
    "max_single_task_family_share": 0.70,
    "target_family_coverage_count": 6,
}
REQUIRED_OUTPUTS = {
    "summary": "summary.json",
    "source_acquisition_input_rows": "source_acquisition_input_rows.csv",
    "execution_resolution_rows": "execution_resolution_rows.csv",
    "source_acquisition_execution_rows": "source_acquisition_execution_rows.csv",
    "acquisition_failure_rows": "acquisition_failure_rows.csv",
    "candidate_support_evidence_rows": "candidate_support_evidence_rows.csv",
    "source_family_evidence_rows": "source_family_evidence_rows.csv",
    "repaired_candidate_projection_rows": "repaired_candidate_projection_rows.csv",
    "split_boundary_rows": "split_boundary_rows.csv",
    "target_boundary_rows": "target_boundary_rows.csv",
    "actor_contract_rows": "actor_contract_rows.csv",
    "claim_rows": "claim_rows.csv",
    "gate_rows": "gate_rows.csv",
    "run_state": "run_state.json",
}

SOURCE_INPUT_FIELDNAMES = (
    "source_acquisition_input_id",
    "fixed_row_set_position",
    "acquisition_required_id",
    "seed_gap_row_id",
    "repair_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "env_template_family",
    "existing_executable_source_family",
    "profile_count",
    "missing_requirement",
    "required_acquisition",
    "candidate_support_acquisition_required",
    "source_family_acquisition_required",
    "observed_candidate_artifact_count",
    "observed_source_family_tag_count",
    "observed_diagnostic_artifact_count",
    "may_seed_future_panel",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "fixed_m2905_row_set",
    "claim_boundary",
)
RESOLUTION_FIELDNAMES = (
    "resolution_id",
    "source_acquisition_input_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "profile_name",
    "workload_id",
    "workload_resolved",
    "execution_admitted",
    "failure_reason",
    "workload_task_family",
    "workload_source_edge",
    "workload_window_tag",
    "workload_executable_source_family",
    "workload_env_template_family",
    "profile_config_path",
    "checkpoint_path",
    "config_path_exists",
    "checkpoint_path_exists",
    "profile_specific_tuning",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "evaluator_targets_actor_visible",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "ranking_run",
    "claim_boundary",
)
EXECUTION_FIELDNAMES = (
    "source_acquisition_execution_id",
    "resolution_id",
    "source_acquisition_input_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "profile_name",
    "workload_id",
    "eval_seed",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "steps",
    "return",
    "min_clearance_margin",
    "source_acquisition_execution_preflight",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "evaluator_targets_actor_visible",
    "ranking_run",
    "model_quality_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "driver_performance_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_gate_passed",
    "claim_boundary",
)
FAILURE_FIELDNAMES = (
    "failure_id",
    "resolution_id",
    "source_acquisition_input_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "profile_name",
    "workload_id",
    "eval_seed",
    "failure_stage",
    "error_type",
    "error_message",
    "execution_accounted",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "evaluator_targets_actor_visible",
    "ranking_run",
    "model_quality_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "driver_performance_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_gate_passed",
    "claim_boundary",
)
CANDIDATE_EVIDENCE_FIELDNAMES = (
    "candidate_support_evidence_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "source_acquisition_execution_id",
    "candidate_support_acquisition_required",
    "execution_artifact_materialized",
    "observed_candidate_artifact_count_before",
    "added_candidate_artifact_count",
    "projected_candidate_artifact_count",
    "candidate_support_satisfied_after_acquisition",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "status_pass",
    "claim_boundary",
)
SOURCE_FAMILY_EVIDENCE_FIELDNAMES = (
    "source_family_evidence_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "source_acquisition_execution_id",
    "source_family_acquisition_required",
    "execution_artifact_materialized",
    "existing_executable_source_family",
    "acquired_executable_source_family",
    "independent_source_family_evidence_added",
    "source_family_evidence_rejection_reason",
    "observed_source_family_tag_count_before",
    "added_source_family_tag_count",
    "projected_source_family_tag_count",
    "source_family_satisfied_after_acquisition",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "status_pass",
    "claim_boundary",
)
PROJECTION_FIELDNAMES = (
    "projection_id",
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "env_template_family",
    "executable_source_family",
    "profile_count",
    "projected_candidate_artifact_count",
    "projected_source_family_tag_count",
    "projected_fresh_candidate_after_source_acquisition",
    "projection_basis",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
SPLIT_FIELDNAMES = (
    "split_boundary_id",
    "split_name",
    "row_count",
    "paper_holdout_admitted",
    "validation_denominator_allowed",
    "model_quality_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "allowed_usage",
    "status_pass",
    "claim_boundary",
)
TARGET_FIELDNAMES = (
    "target_boundary_id",
    "target_family",
    "source_acquisition_input_count",
    "projected_fresh_candidate_available_count",
    "actor_visible_allowed",
    "target_scope",
    "status_pass",
    "claim_boundary",
)
ACTOR_FIELDNAMES = (
    "actor_contract_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
)
CLAIM_FIELDNAMES = (
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
)
GATE_FIELDNAMES = (
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(str(value))
    except ValueError:
        return default


def _paths(output_dir: Path) -> dict[str, Path]:
    return {key: output_dir / filename for key, filename in REQUIRED_OUTPUTS.items()}


def _write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: Iterable[str]) -> None:
    write_csv_rows(path, rows, fieldnames=list(fieldnames) if not rows else None)


def _counter_share(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return max(counter.values()) / total


def build_source_acquisition_input_rows(
    acquisition_rows: list[dict[str, str]],
    repair_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    repair_by_seed = {row.get("seed_gap_row_id", ""): row for row in repair_rows}
    rows: list[dict[str, Any]] = []
    for index, acquisition in enumerate(acquisition_rows, start=1):
        repair = repair_by_seed.get(acquisition.get("seed_gap_row_id", ""), {})
        rows.append(
            {
                "source_acquisition_input_id": f"source-acquisition-input-{index:03d}",
                "fixed_row_set_position": index,
                "acquisition_required_id": acquisition.get("acquisition_required_id", ""),
                "seed_gap_row_id": acquisition.get("seed_gap_row_id", ""),
                "repair_row_id": repair.get("repair_row_id", ""),
                "candidate_id": acquisition.get("candidate_id", ""),
                "task_source_id": acquisition.get("task_source_id", ""),
                "task_family": acquisition.get("task_family", ""),
                "source_edge": repair.get("source_edge", ""),
                "env_template_family": acquisition.get("env_template_family", ""),
                "existing_executable_source_family": repair.get("executable_source_family", ""),
                "profile_count": _int(repair.get("profile_count"), 12),
                "missing_requirement": acquisition.get("missing_requirement", ""),
                "required_acquisition": acquisition.get("required_acquisition", ""),
                "candidate_support_acquisition_required": _bool(
                    acquisition.get("candidate_support_acquisition_required")
                ),
                "source_family_acquisition_required": _bool(
                    acquisition.get("source_family_acquisition_required")
                ),
                "observed_candidate_artifact_count": _int(
                    repair.get("observed_candidate_artifact_count")
                ),
                "observed_source_family_tag_count": _int(
                    repair.get("observed_source_family_tag_count")
                ),
                "observed_diagnostic_artifact_count": _int(
                    repair.get("observed_diagnostic_artifact_count")
                ),
                "may_seed_future_panel": _bool(acquisition.get("may_seed_future_panel")),
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "fixed_m2905_row_set": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def resolve_execution_rows(
    input_rows: list[dict[str, Any]],
    workload_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    workload_by_task_profile = {
        (row.get("task_source_id", ""), row.get("profile_name", "")): row for row in workload_rows
    }
    resolution_rows: list[dict[str, Any]] = []
    resolved_sources: dict[str, dict[str, str]] = {}
    for index, input_row in enumerate(input_rows, start=1):
        task_source_id = str(input_row.get("task_source_id", ""))
        source_row = workload_by_task_profile.get((task_source_id, CANONICAL_PROFILE))
        resolution_id = f"source-acquisition-resolution-{index:03d}"
        if source_row is None:
            reason = "missing_m1690_l3_online_gru_workload_row"
            config_path = ""
            checkpoint_path = ""
            config_exists = False
            checkpoint_exists = False
            profile_specific_tuning = False
        else:
            config_path = source_row.get("profile_config_path", "")
            checkpoint_path = source_row.get("checkpoint_path", "")
            config_exists = Path(config_path).exists()
            checkpoint_exists = Path(checkpoint_path).exists()
            profile_specific_tuning = _bool(source_row.get("profile_specific_tuning"))
            missing_reasons = []
            if not config_exists:
                missing_reasons.append("profile_config_path_missing")
            if not checkpoint_exists:
                missing_reasons.append("checkpoint_path_missing")
            if profile_specific_tuning:
                missing_reasons.append("profile_specific_tuning_forbidden")
            reason = ";".join(missing_reasons)
        admitted = source_row is not None and not reason
        row = {
            "resolution_id": resolution_id,
            "source_acquisition_input_id": input_row.get("source_acquisition_input_id", ""),
            "acquisition_required_id": input_row.get("acquisition_required_id", ""),
            "seed_gap_row_id": input_row.get("seed_gap_row_id", ""),
            "candidate_id": input_row.get("candidate_id", ""),
            "task_source_id": task_source_id,
            "profile_name": CANONICAL_PROFILE,
            "workload_id": source_row.get("workload_id", "") if source_row else "",
            "workload_resolved": source_row is not None,
            "execution_admitted": admitted,
            "failure_reason": reason,
            "workload_task_family": source_row.get("task_family", "") if source_row else "",
            "workload_source_edge": source_row.get("source_edge", "") if source_row else "",
            "workload_window_tag": source_row.get("window_tag", "") if source_row else "",
            "workload_executable_source_family": source_row.get("executable_source_family", "")
            if source_row
            else "",
            "workload_env_template_family": source_row.get("env_template_family", "") if source_row else "",
            "profile_config_path": config_path,
            "checkpoint_path": checkpoint_path,
            "config_path_exists": config_exists,
            "checkpoint_path_exists": checkpoint_exists,
            "profile_specific_tuning": profile_specific_tuning,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
            "evaluator_targets_actor_visible": False,
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
            "ranking_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        resolution_rows.append(row)
        if admitted and source_row is not None:
            resolved_sources[resolution_id] = source_row
    return resolution_rows, resolved_sources


def source_acquisition_execution_metadata(
    resolution: Mapping[str, Any],
    *,
    eval_seed: int,
    execution_index: int,
) -> dict[str, Any]:
    return {
        "source_acquisition_execution_id": f"source-acquisition-execution-{execution_index:03d}",
        "resolution_id": resolution.get("resolution_id", ""),
        "source_acquisition_input_id": resolution.get("source_acquisition_input_id", ""),
        "acquisition_required_id": resolution.get("acquisition_required_id", ""),
        "seed_gap_row_id": resolution.get("seed_gap_row_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "eval_seed": int(eval_seed),
        "source_acquisition_execution_preflight": True,
        "fixed_m2905_acquisition_surface": True,
        "paper_proof_allowed": False,
        "validation_denominator_allowed": False,
        "ordinary_success_denominator_allowed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "source_labels_actor_visible": False,
        "stress_axis_labels_actor_visible": False,
        "scenario_role_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def failure_row(
    resolution: Mapping[str, Any],
    *,
    eval_seed: int,
    failure_index: int,
    error_type: str,
    error_message: str,
    failure_stage: str,
) -> dict[str, Any]:
    return {
        "failure_id": f"source-acquisition-failure-{failure_index:03d}",
        "resolution_id": resolution.get("resolution_id", ""),
        "source_acquisition_input_id": resolution.get("source_acquisition_input_id", ""),
        "acquisition_required_id": resolution.get("acquisition_required_id", ""),
        "seed_gap_row_id": resolution.get("seed_gap_row_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "task_source_id": resolution.get("task_source_id", ""),
        "profile_name": resolution.get("profile_name", CANONICAL_PROFILE),
        "workload_id": resolution.get("workload_id", ""),
        "eval_seed": int(eval_seed),
        "failure_stage": failure_stage,
        "error_type": error_type,
        "error_message": error_message,
        "execution_accounted": True,
        "paper_proof_allowed": False,
        "validation_denominator_allowed": False,
        "ordinary_success_denominator_allowed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "ranking_run": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def run_source_acquisition_execution(
    *,
    resolution_rows: list[dict[str, Any]],
    resolved_sources: dict[str, dict[str, str]],
    output_dir: Path,
    executable_specs_path: Path,
    eval_seed_base: int,
    device: str,
    resume: bool,
    next_blocker: str,
) -> dict[str, Any]:
    if not resume:
        for name in (
            "source_acquisition_execution_rows.csv",
            "acquisition_failure_rows.csv",
            "run_state.json",
        ):
            path = output_dir / name
            if path.exists():
                path.unlink()

    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    execution_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for index, resolution in enumerate(resolution_rows, start=1):
        eval_seed = int(eval_seed_base) + index - 1
        resolution_id = str(resolution["resolution_id"])
        try:
            if not _bool(resolution.get("execution_admitted", False)):
                raise ValueError(str(resolution.get("failure_reason", "resolution not admitted")))
            source_row = resolved_sources[resolution_id]
            task_source_id = str(source_row["task_source_id"])
            if task_source_id not in spec_by_id:
                raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
            profile_name = str(source_row["profile_name"])
            config_path = str(source_row["profile_config_path"])
            checkpoint_path = str(source_row["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in profile_cache:
                profile_config = read_json(config_path)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                profile_cache[cache_key] = (
                    profile_config,
                    model,
                    {
                        "profile_name": profile_name,
                        "config_path": config_path,
                        "checkpoint_path": checkpoint_path,
                    },
                )
            profile_config, model, profile_row = profile_cache[cache_key]
            row = run_workload_cell(
                workload_row=source_row,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(
                source_acquisition_execution_metadata(
                    resolution,
                    eval_seed=eval_seed,
                    execution_index=index,
                )
            )
            execution_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every failed row becomes an artifact.
            failure_rows.append(
                failure_row(
                    resolution,
                    eval_seed=eval_seed,
                    failure_index=len(failure_rows) + 1,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    failure_stage="source_acquisition_execution",
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "milestone": MILESTONE_ID,
                "target_acquisition_row_count": len(resolution_rows),
                "completed_execution_count": len(execution_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(execution_rows) + len(failure_rows),
                "latest_resolution_id": resolution_id,
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    _write_rows(
        output_dir / "source_acquisition_execution_rows.csv",
        execution_rows,
        EXECUTION_FIELDNAMES,
    )
    _write_rows(output_dir / "acquisition_failure_rows.csv", failure_rows, FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(execution_rows) if execution_rows else False
    accounted = len(execution_rows) + len(failure_rows)
    summary = {
        "result_class": (
            "source_acquisition_execution_rows_materialized"
            if execution_rows
            else "source_acquisition_execution_rows_absent"
        ),
        "execution_row_count": len(execution_rows),
        "failure_row_count": len(failure_rows),
        "accounted_row_count": accounted,
        "target_acquisition_row_count": len(resolution_rows),
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(execution_rows),
        "environment_step_run": bool(execution_rows),
        "policy_action_run": bool(execution_rows),
        "policy_rollout_run": bool(execution_rows),
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "next_blocker": next_blocker,
    }
    write_run_state(
        output_dir / "run_state.json",
        {
            "milestone": MILESTONE_ID,
            "target_acquisition_row_count": len(resolution_rows),
            "completed_execution_count": len(execution_rows),
            "failure_count": len(failure_rows),
            "accounted_count": accounted,
            "complete": accounted == len(resolution_rows),
            "all_selected_metrics_finite": bool(all_metrics_finite),
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_candidate_support_evidence_rows(
    input_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    execution_by_acquisition = {row.get("acquisition_required_id", ""): row for row in execution_rows}
    rows: list[dict[str, Any]] = []
    for index, input_row in enumerate(
        [row for row in input_rows if _bool(row.get("candidate_support_acquisition_required"))],
        start=1,
    ):
        acquisition_id = str(input_row.get("acquisition_required_id", ""))
        execution = execution_by_acquisition.get(acquisition_id)
        observed = _int(input_row.get("observed_candidate_artifact_count"))
        added = 1 if execution is not None else 0
        projected = observed + added
        rows.append(
            {
                "candidate_support_evidence_id": f"candidate-support-evidence-{index:03d}",
                "acquisition_required_id": acquisition_id,
                "seed_gap_row_id": input_row.get("seed_gap_row_id", ""),
                "candidate_id": input_row.get("candidate_id", ""),
                "task_source_id": input_row.get("task_source_id", ""),
                "source_acquisition_execution_id": execution.get(
                    "source_acquisition_execution_id", ""
                )
                if execution
                else "",
                "candidate_support_acquisition_required": True,
                "execution_artifact_materialized": execution is not None,
                "observed_candidate_artifact_count_before": observed,
                "added_candidate_artifact_count": added,
                "projected_candidate_artifact_count": projected,
                "candidate_support_satisfied_after_acquisition": projected >= 2,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_source_family_evidence_rows(
    input_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    execution_by_acquisition = {row.get("acquisition_required_id", ""): row for row in execution_rows}
    rows: list[dict[str, Any]] = []
    for index, input_row in enumerate(
        [row for row in input_rows if _bool(row.get("source_family_acquisition_required"))],
        start=1,
    ):
        acquisition_id = str(input_row.get("acquisition_required_id", ""))
        execution = execution_by_acquisition.get(acquisition_id)
        existing_family = str(input_row.get("existing_executable_source_family", ""))
        acquired_family = str(execution.get("executable_source_family", "")) if execution else ""
        independent = bool(execution and acquired_family and acquired_family != existing_family)
        observed = _int(input_row.get("observed_source_family_tag_count"))
        added = 1 if independent else 0
        projected = observed + added
        if execution is None:
            rejection = "no_execution_artifact_materialized"
        elif not acquired_family:
            rejection = "acquired_source_family_missing"
        elif acquired_family == existing_family:
            rejection = "same_executable_source_family_not_independent"
        else:
            rejection = ""
        rows.append(
            {
                "source_family_evidence_id": f"source-family-evidence-{index:03d}",
                "acquisition_required_id": acquisition_id,
                "seed_gap_row_id": input_row.get("seed_gap_row_id", ""),
                "candidate_id": input_row.get("candidate_id", ""),
                "task_source_id": input_row.get("task_source_id", ""),
                "source_acquisition_execution_id": execution.get(
                    "source_acquisition_execution_id", ""
                )
                if execution
                else "",
                "source_family_acquisition_required": True,
                "execution_artifact_materialized": execution is not None,
                "existing_executable_source_family": existing_family,
                "acquired_executable_source_family": acquired_family,
                "independent_source_family_evidence_added": independent,
                "source_family_evidence_rejection_reason": rejection,
                "observed_source_family_tag_count_before": observed,
                "added_source_family_tag_count": added,
                "projected_source_family_tag_count": projected,
                "source_family_satisfied_after_acquisition": projected >= 2,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_repaired_candidate_projection_rows(
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_by_acquisition = {row["acquisition_required_id"]: row for row in candidate_rows}
    source_by_acquisition = {row["acquisition_required_id"]: row for row in source_rows}
    rows: list[dict[str, Any]] = []
    for input_row in input_rows:
        acquisition_id = str(input_row.get("acquisition_required_id", ""))
        candidate_required = _bool(input_row.get("candidate_support_acquisition_required"))
        source_required = _bool(input_row.get("source_family_acquisition_required"))
        candidate_projected = (
            _int(candidate_by_acquisition[acquisition_id]["projected_candidate_artifact_count"])
            if candidate_required and acquisition_id in candidate_by_acquisition
            else _int(input_row.get("observed_candidate_artifact_count"))
        )
        source_projected = (
            _int(source_by_acquisition[acquisition_id]["projected_source_family_tag_count"])
            if source_required and acquisition_id in source_by_acquisition
            else _int(input_row.get("observed_source_family_tag_count"))
        )
        if candidate_projected < 2 or source_projected < 2:
            continue
        basis = []
        if candidate_required:
            basis.append("source_acquisition_execution_added_candidate_support_artifact")
        if source_required:
            basis.append("source_acquisition_execution_added_independent_source_family")
        if not basis:
            basis.append("existing_support_already_sufficient")
        rows.append(
            {
                "projection_id": f"projection-{len(rows) + 1:03d}",
                "acquisition_required_id": acquisition_id,
                "seed_gap_row_id": input_row.get("seed_gap_row_id", ""),
                "candidate_id": input_row.get("candidate_id", ""),
                "task_source_id": input_row.get("task_source_id", ""),
                "task_family": input_row.get("task_family", ""),
                "env_template_family": input_row.get("env_template_family", ""),
                "executable_source_family": input_row.get("existing_executable_source_family", ""),
                "profile_count": _int(input_row.get("profile_count"), 12),
                "projected_candidate_artifact_count": candidate_projected,
                "projected_source_family_tag_count": source_projected,
                "projected_fresh_candidate_after_source_acquisition": True,
                "projection_basis": ";".join(basis),
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_split_boundary_rows(
    *,
    input_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
    projection_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = (
        (
            "fixed_m2905_acquisition_required_surface",
            len(input_rows),
            "source_acquisition_execution_input_only_no_validation",
        ),
        (
            "source_acquisition_execution_rows",
            len(execution_rows),
            "closed_loop_diagnostic_artifact_only_no_denominator",
        ),
        (
            "source_acquisition_failure_rows",
            len(failure_rows),
            "explicit_failure_accounting_only_no_denominator",
        ),
        (
            "repaired_candidate_projection_rows",
            len(projection_rows),
            "projection_for_m2909_audit_only_no_validation",
        ),
        ("paper_holdout", 0, "not_admitted_in_m2908"),
    )
    return [
        {
            "split_boundary_id": f"split-{index:03d}",
            "split_name": name,
            "row_count": count,
            "paper_holdout_admitted": False,
            "validation_denominator_allowed": False,
            "model_quality_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
            "allowed_usage": usage,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, count, usage) in enumerate(specs, start=1)
    ]


def build_target_boundary_rows(
    input_rows: list[dict[str, Any]],
    projection_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    input_counts = Counter(str(row.get("env_template_family", "")) for row in input_rows)
    projection_counts = Counter(str(row.get("env_template_family", "")) for row in projection_rows)
    target_families = sorted(set(input_counts) | set(projection_counts))
    return [
        {
            "target_boundary_id": f"target-{index:03d}",
            "target_family": family,
            "source_acquisition_input_count": input_counts[family],
            "projected_fresh_candidate_available_count": projection_counts[family],
            "actor_visible_allowed": False,
            "target_scope": "evaluator_only_route_b_panel_target",
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, family in enumerate(target_families, start=1)
    ]


def build_actor_contract_rows(
    *,
    input_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows = input_rows + resolution_rows + execution_rows + failure_rows
    guards = (
        ("p0_observation_dim", P0_OBSERVATION_DIM, 72),
        ("action_dim", ACTION_DIM, 3),
        ("hidden_oracle_actor_input_required", any_flag(rows, "hidden_oracle_actor_input_required"), False),
        ("future_target_actor_input_required", any_flag(rows, "future_target_actor_input_required"), False),
        ("evaluator_targets_actor_visible", any_flag(rows, "evaluator_targets_actor_visible"), False),
        ("source_labels_actor_visible", any_flag(rows, "source_labels_actor_visible"), False),
        ("route_labels_actor_visible", any_flag(rows, "route_labels_actor_visible"), False),
        ("verdict_labels_actor_visible", any_flag(rows, "verdict_labels_actor_visible"), False),
        ("actor_contract_shape_72_action_3", True, True),
    )
    return [
        {
            "actor_contract_id": f"actor-contract-{index:03d}",
            "guard_family": guard,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (guard, observed, expected) in enumerate(guards, start=1)
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    specs = (
        ("model_quality", "accepted_fresh_panel_plus_later_holdout_validation"),
        ("paper_claim", "paper_holdout_validation_and_claim_table_audit"),
        ("finite_window_vs_gru", "paired_same_case_model_quality_evidence"),
        ("level3_self_identification", "history_necessity_and_self_id_gate"),
        ("driver_performance", "closed_loop_driver_validation_gate"),
        ("current_sim_verdict", "current_sim_validation_gate"),
        ("high_fidelity_validation", "high_fidelity_validation_gate"),
        ("full_ideal_driver_gate", "full_ideal_driver_gate_sequence"),
        ("controller_ranking", "later_same_case_ranking_gate"),
        ("checkpoint_promotion", "later_promotion_gate"),
    )
    return [
        {
            "claim_id": f"claim-{index:03d}",
            "claim_family": family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, evidence) in enumerate(specs, start=1)
    ]


def _projection_metrics(projection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_counter = Counter(
        str(row.get("executable_source_family") or "unknown") for row in projection_rows
    )
    task_counter = Counter(str(row.get("task_family") or "unknown") for row in projection_rows)
    target_counter = Counter(str(row.get("env_template_family") or "unknown") for row in projection_rows)
    task_count = len(projection_rows)
    profile_task_count = sum(_int(row.get("profile_count"), 12) for row in projection_rows)
    source_family_count = len(source_counter)
    task_family_count = len(task_counter)
    target_family_coverage_count = len(target_counter)
    max_source_share = _counter_share(source_counter)
    max_task_share = _counter_share(task_counter)
    targets_satisfied = (
        task_count >= DESIGN_TARGETS["fresh_candidate_task_count"]
        and profile_task_count >= DESIGN_TARGETS["fresh_candidate_profile_task_count"]
        and source_family_count >= DESIGN_TARGETS["source_family_count"]
        and task_family_count >= DESIGN_TARGETS["task_family_count"]
        and max_source_share <= DESIGN_TARGETS["max_single_source_family_share"]
        and max_task_share <= DESIGN_TARGETS["max_single_task_family_share"]
        and target_family_coverage_count >= DESIGN_TARGETS["target_family_coverage_count"]
    )
    return {
        "projected_fresh_candidate_task_count": task_count,
        "projected_fresh_candidate_profile_task_count": profile_task_count,
        "projected_source_family_count": source_family_count,
        "projected_task_family_count": task_family_count,
        "projected_target_family_coverage_count": target_family_coverage_count,
        "projected_max_single_source_family_share": max_source_share,
        "projected_max_single_task_family_share": max_task_share,
        "projected_design_targets_satisfied": targets_satisfied,
        "projected_source_family_counts": dict(sorted(source_counter.items())),
        "projected_task_family_counts": dict(sorted(task_counter.items())),
        "projected_target_family_counts": dict(sorted(target_counter.items())),
    }


def build_gate_rows(
    *,
    input_paths_present: dict[str, bool],
    input_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    projection_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
    execution_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    accounted_count = len(execution_rows) + len(failure_rows)
    input_task_sources = [str(row.get("task_source_id", "")) for row in input_rows]
    resolved_task_sources = [str(row.get("task_source_id", "")) for row in resolution_rows]
    checks = (
        (
            "input_paths_present",
            "lineage",
            all(input_paths_present.values()),
            input_paths_present,
            "all M2907/M2905/M2906/M1690 inputs present",
            "lineage_invalid",
        ),
        (
            "fixed_m2905_acquisition_row_count",
            "lineage",
            len(input_rows) == EXPECTED_ACQUISITION_ROW_COUNT,
            len(input_rows),
            EXPECTED_ACQUISITION_ROW_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "no_row_substitution",
            "lineage",
            input_task_sources == resolved_task_sources,
            resolved_task_sources,
            input_task_sources,
            "lineage_invalid",
        ),
        (
            "all_rows_accounted",
            "execution",
            accounted_count == len(input_rows),
            accounted_count,
            len(input_rows),
            "metric_artifact",
        ),
        (
            "any_closed_loop_execution_rows",
            "execution",
            bool(execution_rows),
            len(execution_rows),
            ">0",
            "metric_artifact",
        ),
        (
            "all_selected_metrics_finite_for_execution_rows",
            "metric",
            bool(execution_summary.get("all_selected_metrics_finite", False)),
            execution_summary.get("all_selected_metrics_finite"),
            True,
            "metric_artifact",
        ),
        (
            "candidate_support_evidence_accounted",
            "evidence",
            len(candidate_rows)
            == sum(_bool(row.get("candidate_support_acquisition_required")) for row in input_rows),
            len(candidate_rows),
            sum(_bool(row.get("candidate_support_acquisition_required")) for row in input_rows),
            "metric_artifact",
        ),
        (
            "source_family_evidence_accounted",
            "evidence",
            len(source_rows)
            == sum(_bool(row.get("source_family_acquisition_required")) for row in input_rows),
            len(source_rows),
            sum(_bool(row.get("source_family_acquisition_required")) for row in input_rows),
            "metric_artifact",
        ),
        (
            "split_boundary_rows_pass",
            "boundary",
            all(_bool(row.get("status_pass")) for row in split_rows),
            "all_pass" if all(_bool(row.get("status_pass")) for row in split_rows) else split_rows,
            "all_pass",
            "contract_violation",
        ),
        (
            "target_boundary_rows_pass",
            "boundary",
            all(_bool(row.get("status_pass")) for row in target_rows),
            "all_pass" if all(_bool(row.get("status_pass")) for row in target_rows) else target_rows,
            "all_pass",
            "contract_violation",
        ),
        (
            "actor_contract_rows_pass",
            "contract",
            all(_bool(row.get("status_pass")) for row in actor_rows),
            "all_pass" if all(_bool(row.get("status_pass")) for row in actor_rows) else actor_rows,
            "all_pass",
            "contract_violation",
        ),
        (
            "claim_rows_suppressed",
            "claim",
            all(not _bool(row.get("claim_made")) for row in claim_rows),
            "all_false" if all(not _bool(row.get("claim_made")) for row in claim_rows) else claim_rows,
            "all_false",
            "proof_washout",
        ),
        (
            "denominator_flags_suppressed",
            "boundary",
            not any_denominator_flag(input_rows + execution_rows + failure_rows + projection_rows + split_rows),
            any_denominator_flag(input_rows + execution_rows + failure_rows + projection_rows + split_rows),
            False,
            "proof_washout",
        ),
        (
            "forbidden_execution_flags_suppressed",
            "claim",
            not any(forbidden_execution_flag(row) for row in execution_rows + failure_rows),
            any(forbidden_execution_flag(row) for row in execution_rows + failure_rows),
            False,
            "proof_washout",
        ),
        (
            "follow_up_manifest_registered",
            "follow_up_route",
            follow_up_manifest.exists(),
            str(follow_up_manifest),
            "exists",
            "lineage_invalid",
        ),
    )
    return [
        {
            "gate_id": f"gate-{index:03d}-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (gate_id, family, status, observed, expected, failure_type) in enumerate(
            checks,
            start=1,
        )
    ]


def build_follow_up_manifest(
    *,
    summary_path: Path,
    output_dir: Path,
    decision: str,
) -> dict[str, Any]:
    command = (
        "PYTHONPATH=src python -m autodrift.paper_route_l0_l1_l2_l3_capability_prediction_"
        "fresh_source_diverse_panel_source_acquisition_execution_result_audit "
        f"--m2908-summary {summary_path} --m2908-dir {output_dir} "
        "--output-doc docs/m2909-paper-route-l0-l1-l2-l3-capability-prediction-"
        "fresh-source-diverse-panel-source-acquisition-execution-result-audit.md"
    )
    return {
        "id": NEXT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_milestone": MILESTONE_ID,
        "type": "gate",
        "gate_tier": "process",
        "status": "pending",
        "risk": "medium",
        "promotion_decision": "not_applicable",
        "hypothesis": (
            "A bounded result audit can accept, reject, or pivot after M2908 "
            "source-acquisition execution without validation ranking model-quality "
            "paper current-sim high-fidelity full-driver finite-window-vs-GRU or "
            "self-ID claims."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "source_acquisition_input_rows.csv"),
                str(output_dir / "source_acquisition_execution_rows.csv"),
                str(output_dir / "acquisition_failure_rows.csv"),
                str(output_dir / "repaired_candidate_projection_rows.csv"),
            ],
            "parent_config": [
                "experiments/manifests/m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight.json",
                "experiments/manifests/m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis.json",
                "experiments/manifests/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.json",
            ],
            "parent_objective": [
                "audit M2908 bounded source-acquisition execution and preserve positive or negative acquisition result"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis",
                "m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit",
            ],
            "blocked_by": [
                "M2908 is execution preflight only",
                "source-family acquisitions may remain unresolved because same-family rollouts are not independent source-family evidence",
                "acquisition-required rows must remain out of validation paper proof and ordinary denominators",
            ],
            "supersedes": [
                "interpreting M2908 rollout success as driver performance",
                "treating same source-family execution as independent source-family repair evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2909 must audit all M2908 source-acquisition input execution failure evidence projection split target actor claim gate and run-state artifacts",
            "M2909 must preserve the fixed M2905 row set and no-substitution boundary",
            "M2909 must preserve candidate-support and source-family evidence exactly without threshold weakening",
            "M2909 must keep source-acquisition rows out of validation paper proof and ordinary success denominators",
            "M2909 must choose continuation pivot synthesis or stop without model-quality driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not train replay run PPO rank promote select winners or publish packages",
            "do not change actor input or action contract",
            "do not expose hidden dynamics oracle labels future targets route labels success labels diagnostics or verdict labels to actor input",
            "do not substitute rows outside the M2905 acquisition-required surface",
            "do not treat same-family execution as independent source-family evidence",
            "do not treat M2908 rows as validation paper proof model-quality or ordinary success denominators",
            "do not claim driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
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
        "workflow_synthesis": {
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_fresh_panel_expansion",
            "evidence_axis": "fresh_source_diverse_panel_source_acquisition_execution_result_audit",
            "evidence_increment": "audits bounded source-acquisition execution output before any Route B interpretation",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if M2908 artifacts are incomplete",
                "stop if fixed-row no-substitution or actor boundaries fail",
                "stop if source acquisition yields no claim-safe continuation path",
                "stop if M2909 would claim model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            ],
            "fallback_plan": [
                "route to another source-acquisition continuation only if M2909 accepts a concrete missing source-family path",
                "route to Route A engineering-controller evidence if Route B remains source-insufficient",
                "route to Route C dependency work only if source availability changes",
                "write stop synthesis if no claim-safe evidence-producing route remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2908 registered source-acquisition execution rows for audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B source-acquisition execution result audit",
            "admission_evidence": [
                "M2908 wrote source-acquisition execution and failure artifacts",
                "M2907 admitted exactly one bounded source-acquisition execution attempt",
                "M2905/M2906 preserved fixed acquisition-required rows and claim boundaries",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion",
                "no training replay PPO or promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no source-acquisition rows as paper proof or ordinary denominators",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2909 status queue scoreboard research log and review",
                "one bounded follow-up source acquisition Route A Route C synthesis or stop manifest",
            ],
            "next_stage_criteria": [
                "M2908 summary and row artifacts are audited",
                "candidate-support and source-family acquisition result is preserved exactly",
                "one next continuation pivot synthesis or stop route is selected",
                "target actor split holdout and denominator boundaries remain preserved",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": (
                "M2909 audits source-acquisition execution only and cannot substitute "
                "new closed-loop rows for history-necessity or self-ID evidence."
            ),
            "history_necessity_tests": [
                "None in M2909; later evidence requires accepted source-diverse panel data and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": (
                "M2884-M2908 Route B capability-prediction panel inventory materialization "
                "repair audit synthesis and source-acquisition execution chain."
            ),
            "negative_result_policy": (
                "If source-family or projected-design criteria remain insufficient, preserve "
                "the negative result and route to pivot/stop or concrete acquisition work "
                "rather than weakening self-ID gates."
            ),
            "allowed_claims": [
                "bounded source-acquisition execution result-audit outcome",
                "candidate/source-family acquisition evidence or explicit failure rows as reported by M2908",
                "bounded follow-up source execution pivot synthesis or stop decision",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized closed-loop source-acquisition rows",
            "paper_verdict_delta": "no verdict; preserves whether Route B has enough claim-safe acquisition evidence to continue",
            "must_synthesize_if": [
                "M2909 cannot choose between source-acquisition continuation Route A pivot Route C pivot synthesis or stop",
                "M2909 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2909 would let acquisition-required rows enter paper proof or validation",
                "M2909 would expose evaluator-only future targets to actor input",
                "another same-family source-family repair loop is proposed without independent source evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2908 summary and row artifacts are audited",
            "candidate-support and source-family evidence is preserved without threshold weakening",
            "one bounded continuation pivot synthesis or stop decision is selected",
            "no validation ranking promotion performance paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2909 changes M2908 row classifications or thresholds to force a pass",
            "M2909 admits source-acquisition rows into validation paper proof or ordinary denominators",
            "M2909 treats same-family execution as independent source-family evidence",
            "M2909 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2909 fails to select a bounded continuation pivot synthesis or stop route after auditing M2908",
        ],
        "decision_rule": (
            "Accept M2908 only if all source-acquisition execution artifacts are complete, "
            "internally consistent, fixed-row, and claim-safe."
        ),
        "commands": [{"name": "result_audit", "command": command}],
        "command": command,
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "expected_artifacts": [f"docs/{NEXT_ID}.md"],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [str(summary_path), str(output_dir)],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "m2908_result": {"summary": str(summary_path), "decision": decision},
    }


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def any_denominator_flag(rows: Iterable[Mapping[str, Any]]) -> bool:
    return any(
        any(
            _bool(row.get(field, False))
            for field in (
                "paper_proof_allowed",
                "validation_denominator_allowed",
                "model_quality_denominator_allowed",
                "ordinary_success_denominator_allowed",
                "paper_holdout_admitted",
            )
        )
        for row in rows
    )


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "paper_proof_allowed",
            "validation_denominator_allowed",
            "model_quality_denominator_allowed",
            "ordinary_success_denominator_allowed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "evaluator_targets_actor_visible",
            "source_labels_actor_visible",
            "stress_axis_labels_actor_visible",
            "scenario_role_labels_actor_visible",
            "route_labels_actor_visible",
            "verdict_labels_actor_visible",
            "training_started",
            "replay_started",
            "ppo_used",
            "source_build_run",
            "adapter_probe_run",
            "external_simulation_run",
            "private_holdout_used",
            "profile_specific_tuning",
            "ranking_run",
            "winner_selected",
            "checkpoint_promoted",
            "model_quality_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "level3_self_id_claim_made",
            "driver_performance_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
        )
    )


def write_preflight_artifacts(
    *,
    m2907_synthesis: Path = DEFAULT_M2907_SYNTHESIS,
    m2905_dir: Path = DEFAULT_M2905_DIR,
    m2906_audit: Path = DEFAULT_M2906_AUDIT,
    m1690_workload: Path = DEFAULT_M1690_WORKLOAD,
    executable_specs: Path = DEFAULT_EXECUTABLE_SPECS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(output_dir)
    acquisition_path = m2905_dir / "acquisition_required_rows.csv"
    repair_path = m2905_dir / "seed_gap_repair_rows.csv"
    m2905_summary_path = m2905_dir / "summary.json"
    input_paths_present = {
        "m2907_synthesis": m2907_synthesis.exists(),
        "m2905_acquisition_required_rows": acquisition_path.exists(),
        "m2905_seed_gap_repair_rows": repair_path.exists(),
        "m2905_summary": m2905_summary_path.exists(),
        "m2906_audit": m2906_audit.exists(),
        "m1690_workload": m1690_workload.exists(),
        "executable_specs": executable_specs.exists(),
    }
    acquisition_rows = read_csv_rows(acquisition_path) if acquisition_path.exists() else []
    repair_rows = read_csv_rows(repair_path) if repair_path.exists() else []
    workload_rows = read_csv_rows(m1690_workload) if m1690_workload.exists() else []

    input_rows = build_source_acquisition_input_rows(acquisition_rows, repair_rows)
    resolution_rows, resolved_sources = resolve_execution_rows(input_rows, workload_rows)
    execution_summary = run_source_acquisition_execution(
        resolution_rows=resolution_rows,
        resolved_sources=resolved_sources,
        output_dir=output_dir,
        executable_specs_path=executable_specs,
        eval_seed_base=eval_seed_base,
        device=device,
        resume=resume,
        next_blocker=NEXT_ID,
    )
    execution_rows = (
        read_csv_rows(paths["source_acquisition_execution_rows"])
        if paths["source_acquisition_execution_rows"].exists()
        else []
    )
    failure_rows = (
        read_csv_rows(paths["acquisition_failure_rows"])
        if paths["acquisition_failure_rows"].exists()
        else []
    )
    candidate_rows = build_candidate_support_evidence_rows(input_rows, execution_rows)
    source_rows = build_source_family_evidence_rows(input_rows, execution_rows)
    projection_rows = build_repaired_candidate_projection_rows(input_rows, candidate_rows, source_rows)
    split_rows = build_split_boundary_rows(
        input_rows=input_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        projection_rows=projection_rows,
    )
    target_rows = build_target_boundary_rows(input_rows, projection_rows)
    actor_rows = build_actor_contract_rows(
        input_rows=input_rows,
        resolution_rows=resolution_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
    )
    claim_rows = build_claim_rows()

    projection_metrics = _projection_metrics(projection_rows)
    decision = (
        "source_acquisition_execution_preflight_complete_projected_design_targets_satisfied_route_to_m2909_result_audit"
        if projection_metrics["projected_design_targets_satisfied"]
        else "source_acquisition_execution_preflight_complete_projected_design_targets_unsatisfied_route_to_m2909_result_audit"
    )
    follow_up = build_follow_up_manifest(
        summary_path=paths["summary"],
        output_dir=output_dir,
        decision=decision,
    )
    write_json(follow_up_manifest, follow_up)
    gate_rows = build_gate_rows(
        input_paths_present=input_paths_present,
        input_rows=input_rows,
        resolution_rows=resolution_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        candidate_rows=candidate_rows,
        source_rows=source_rows,
        projection_rows=projection_rows,
        split_rows=split_rows,
        target_rows=target_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up_manifest,
        execution_summary=execution_summary,
    )
    status_pass = all(_bool(row.get("status_pass")) for row in gate_rows)
    if not status_pass:
        decision = "source_acquisition_execution_preflight_incomplete"

    row_counts = {
        "source_acquisition_input_rows": len(input_rows),
        "execution_resolution_rows": len(resolution_rows),
        "source_acquisition_execution_rows": len(execution_rows),
        "acquisition_failure_rows": len(failure_rows),
        "candidate_support_evidence_rows": len(candidate_rows),
        "source_family_evidence_rows": len(source_rows),
        "repaired_candidate_projection_rows": len(projection_rows),
        "split_boundary_rows": len(split_rows),
        "target_boundary_rows": len(target_rows),
        "actor_contract_rows": len(actor_rows),
        "claim_rows": len(claim_rows),
        "gate_rows": len(gate_rows),
    }
    candidate_evidence_added_count = sum(
        _int(row.get("added_candidate_artifact_count")) for row in candidate_rows
    )
    independent_source_family_evidence_added_count = sum(
        _int(row.get("added_source_family_tag_count")) for row in source_rows
    )
    missing_requirement_counts = Counter(
        str(row.get("missing_requirement", "")) for row in input_rows
    )
    source_family_rejection_counts = Counter(
        str(row.get("source_family_evidence_rejection_reason", "")) for row in source_rows
    )
    source_family_rejection_counts.pop("", None)
    summary = {
        "milestone": MILESTONE_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status_pass": status_pass,
        "gate_matrix_pass": status_pass,
        "decision": decision,
        "result_class": (
            "source_acquisition_execution_preflight_pass"
            if status_pass
            else "source_acquisition_execution_preflight_fail"
        ),
        "artifacts": {key: str(path) for key, path in paths.items()} | {
            "follow_up_manifest": str(follow_up_manifest)
        },
        "row_counts": row_counts,
        "input_paths_present": input_paths_present,
        "m2907_synthesis": str(m2907_synthesis),
        "m2905_dir": str(m2905_dir),
        "m2906_audit": str(m2906_audit),
        "m1690_workload": str(m1690_workload),
        "executable_specs": str(executable_specs),
        "fixed_m2905_acquisition_required_row_count": len(input_rows),
        "resolved_execution_row_count": sum(
            _bool(row.get("execution_admitted")) for row in resolution_rows
        ),
        "source_acquisition_execution_row_count": len(execution_rows),
        "acquisition_failure_row_count": len(failure_rows),
        "accounted_acquisition_row_count": len(execution_rows) + len(failure_rows),
        "candidate_support_required_count": len(candidate_rows),
        "candidate_support_evidence_added_count": candidate_evidence_added_count,
        "source_family_required_count": len(source_rows),
        "independent_source_family_evidence_added_count": independent_source_family_evidence_added_count,
        "source_family_evidence_rejection_counts": dict(sorted(source_family_rejection_counts.items())),
        "repaired_candidate_projection_count": len(projection_rows),
        "missing_requirement_counts": dict(sorted(missing_requirement_counts.items())),
        "all_selected_metrics_finite": bool(execution_summary.get("all_selected_metrics_finite", False)),
        **projection_metrics,
        "design_targets": DESIGN_TARGETS,
        "actor_contract_shape_72_action_3": True,
        "observation_dim": P0_OBSERVATION_DIM,
        "action_dim": ACTION_DIM,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "source_acquisition_rows_paper_proof_allowed": False,
        "source_acquisition_rows_validation_denominator_allowed": False,
        "source_acquisition_rows_ordinary_success_denominator_allowed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(follow_up_manifest),
    }
    run_state = {
        "milestone": MILESTONE_ID,
        "status": "complete" if status_pass else "incomplete",
        "decision": decision,
        "summary_path": str(paths["summary"]),
        "follow_up_manifest": str(follow_up_manifest),
        "claim_boundary": CLAIM_SCOPE,
        "updated_at_utc": utc_timestamp(),
    }

    _write_rows(paths["source_acquisition_input_rows"], input_rows, SOURCE_INPUT_FIELDNAMES)
    _write_rows(paths["execution_resolution_rows"], resolution_rows, RESOLUTION_FIELDNAMES)
    _write_rows(paths["candidate_support_evidence_rows"], candidate_rows, CANDIDATE_EVIDENCE_FIELDNAMES)
    _write_rows(paths["source_family_evidence_rows"], source_rows, SOURCE_FAMILY_EVIDENCE_FIELDNAMES)
    _write_rows(paths["repaired_candidate_projection_rows"], projection_rows, PROJECTION_FIELDNAMES)
    _write_rows(paths["split_boundary_rows"], split_rows, SPLIT_FIELDNAMES)
    _write_rows(paths["target_boundary_rows"], target_rows, TARGET_FIELDNAMES)
    _write_rows(paths["actor_contract_rows"], actor_rows, ACTOR_FIELDNAMES)
    _write_rows(paths["claim_rows"], claim_rows, CLAIM_FIELDNAMES)
    _write_rows(paths["gate_rows"], gate_rows, GATE_FIELDNAMES)
    write_json(paths["run_state"], run_state)
    write_json(paths["summary"], summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2907-synthesis", type=Path, default=DEFAULT_M2907_SYNTHESIS)
    parser.add_argument("--m2905-dir", type=Path, default=DEFAULT_M2905_DIR)
    parser.add_argument("--m2906-audit", type=Path, default=DEFAULT_M2906_AUDIT)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_M1690_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    summary = write_preflight_artifacts(
        m2907_synthesis=args.m2907_synthesis,
        m2905_dir=args.m2905_dir,
        m2906_audit=args.m2906_audit,
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(
        "M2908 source-acquisition execution preflight: "
        f"status={summary['status_pass']} "
        f"inputs={summary['fixed_m2905_acquisition_required_row_count']} "
        f"executions={summary['source_acquisition_execution_row_count']} "
        f"failures={summary['acquisition_failure_row_count']} "
        f"projections={summary['repaired_candidate_projection_count']} "
        f"next={summary['next_blocker']}"
    )
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
