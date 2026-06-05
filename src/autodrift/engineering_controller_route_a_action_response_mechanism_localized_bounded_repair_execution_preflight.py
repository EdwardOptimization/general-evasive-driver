"""M2769 bounded mechanism-localized actor-head repair execution preflight."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

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
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    model_state_sha256,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2769-engineering-controller-route-a-action-response-mechanism-localized-"
    "bounded-repair-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2770-engineering-controller-route-a-action-response-mechanism-localized-"
    "bounded-repair-execution-result-audit"
)
DEFAULT_M2766_DIR = Path(
    "runs/m2766_engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization"
)
DEFAULT_M2768_DESIGN = Path(
    "docs/m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design.md"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
    "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2770-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 276900
CANONICAL_PROFILE = "L3_online_gru"
EXPECTED_REPAIR_ROW_COUNT = 8
EXPECTED_CONTEXT_ONLY_ROW_COUNT = 4
EXPECTED_GUARDRAIL_ROW_COUNT = 31

CLAIM_SCOPE = (
    "M2769 Route A action-response mechanism-localized bounded repair execution preflight only; "
    "reset, step, policy action, and rollout are allowed only for the 8 M2766 admitted repair-design "
    "rows under fixed actor-head bias candidates while no replay, validation, training, PPO, source build, "
    "adapter probe, external simulation, private holdout, environment relaxation, active config overwrite, "
    "profile-specific tuning, ranking, winner selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller-family ranking, "
    "repair-candidate ranking, source-edge ranking, mechanism-tag ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight_failed"
)

FALSE_CLAIM_FLAGS = {
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "external_simulation_run": False,
    "private_holdout_used": False,
    "environment_difficulty_relaxed": False,
    "active_config_overwritten": False,
    "profile_specific_tuning": False,
    "per_row_tuning": False,
    "ranking_run": False,
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

DEFAULT_REPAIR_SPECS: tuple[dict[str, str | float], ...] = (
    {
        "repair_candidate_id": "m2769_containment_brake_bias_candidate",
        "repair_lever_family": "actor_head_bias_candidate_sweep",
        "target_class_focus": "track_containment_stability_target",
        "steer_bias_delta": 0.0,
        "throttle_bias_delta": -1.5,
        "brake_bias_delta": 1.5,
    },
    {
        "repair_candidate_id": "m2769_soft_containment_bias_candidate",
        "repair_lever_family": "actor_head_bias_candidate_sweep",
        "target_class_focus": "track_containment_stability_target",
        "steer_bias_delta": 0.0,
        "throttle_bias_delta": -1.0,
        "brake_bias_delta": 1.0,
    },
    {
        "repair_candidate_id": "m2769_clearance_timing_brake_bias_candidate",
        "repair_lever_family": "actor_head_bias_candidate_sweep",
        "target_class_focus": "obstacle_timing_or_clearance_margin_target",
        "steer_bias_delta": 0.0,
        "throttle_bias_delta": -2.0,
        "brake_bias_delta": 2.0,
    },
)

REPAIR_CANDIDATE_FIELDNAMES = [
    "repair_candidate_row_id",
    "repair_admission_id",
    "mechanism_localization_id",
    "source_candidate_id",
    "task_source_id",
    "primary_mechanism",
    "repair_target_class",
    "repair_admitted_for_design",
    "repair_admission_status",
    "failure_family",
    "termination_reason",
    "diagnostic_outcome_bucket",
    "telemetry_join_id",
    "finite_telemetry",
    "track_containment_score",
    "obstacle_timing_score",
    "command_response_mismatch_score",
    "candidate_surface_role",
    "ordinary_success_denominator_allowed",
    "ranking_run",
    "winner_selected",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
RESOLUTION_FIELDNAMES = [
    "repair_candidate_resolution_id",
    "repair_candidate_row_id",
    "repair_candidate_id",
    "repair_admission_id",
    "source_candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "profile_config_path",
    "source_checkpoint_path",
    "repair_checkpoint_path",
    "repair_target_class",
    "primary_mechanism",
    "resolution_status",
    "failure_reason",
    "execution_admitted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "environment_difficulty_relaxed",
    "active_config_overwritten",
    "profile_specific_tuning",
    "per_row_tuning",
    "ranking_run",
    "winner_selected",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CHECKPOINT_FIELDNAMES = [
    "repair_candidate_id",
    "repair_lever_family",
    "source_checkpoint_path",
    "repair_checkpoint_path",
    "source_checkpoint_hash",
    "repair_checkpoint_hash",
    "source_model_state_hash",
    "repair_model_state_hash",
    "actor_mean_bias_before",
    "actor_mean_bias_after",
    "steer_bias_delta",
    "throttle_bias_delta",
    "brake_bias_delta",
    "target_class_focus",
    "trainable_parameter_names",
    "finite_update",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "active_config_overwritten",
    "environment_difficulty_relaxed",
    "profile_specific_tuning",
    "per_row_tuning",
    "checkpoint_promoted",
    "repair_training_started",
    "ppo_used",
    "ranking_run",
    "winner_selected",
    "claim_boundary",
]
BASELINE_JOIN_FIELDNAMES = [
    "baseline_join_id",
    "repair_candidate_row_id",
    "repair_admission_id",
    "source_candidate_id",
    "task_source_id",
    "telemetry_join_id",
    "mechanism_localization_id",
    "primary_mechanism",
    "repair_target_class",
    "baseline_termination_reason",
    "baseline_diagnostic_success",
    "baseline_collision",
    "baseline_min_clearance_margin",
    "baseline_previous_command",
    "baseline_current_action",
    "baseline_trace_delta_proxy",
    "baseline_speed_response_proxy",
    "baseline_yaw_response_proxy",
    "baseline_beta_response_proxy",
    "baseline_finite_metric",
    "m2764_telemetry_coverage_improved",
    "m2759_row_backfilled",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
EXECUTION_FIELDNAMES = [
    "repair_execution_id",
    "repair_candidate_resolution_id",
    "repair_candidate_row_id",
    "repair_candidate_id",
    "repair_admission_id",
    "source_candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "primary_mechanism",
    "repair_target_class",
    "repair_checkpoint_path",
    "eval_seed",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
    "previous_command_norm_mean",
    "current_action_norm_mean",
    "action_trace_delta_mean",
    "action_trace_delta_peak",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "replay_started",
    "training_started",
    "ppo_used",
    "source_build_run",
    "adapter_probe_run",
    "external_simulation_run",
    "private_holdout_used",
    "environment_difficulty_relaxed",
    "active_config_overwritten",
    "profile_specific_tuning",
    "per_row_tuning",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "mechanism_labels_actor_visible",
    "repair_target_labels_actor_visible",
    "context_labels_actor_visible",
    "guardrail_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "repair_execution_failure_id",
    "repair_candidate_resolution_id",
    "repair_candidate_row_id",
    "repair_candidate_id",
    "repair_admission_id",
    "source_candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "repair_target_class",
    "primary_mechanism",
    "eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "replay_started",
    "training_started",
    "ppo_used",
    "source_build_run",
    "adapter_probe_run",
    "external_simulation_run",
    "private_holdout_used",
    "environment_difficulty_relaxed",
    "active_config_overwritten",
    "profile_specific_tuning",
    "per_row_tuning",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "mechanism_labels_actor_visible",
    "repair_target_labels_actor_visible",
    "context_labels_actor_visible",
    "guardrail_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CONTEXT_FIELDNAMES = [
    "context_only_regression_id",
    "repair_admission_id",
    "mechanism_localization_id",
    "source_candidate_id",
    "task_source_id",
    "primary_mechanism",
    "repair_target_class",
    "repair_admitted_for_design",
    "context_role",
    "execution_admitted",
    "execution_run",
    "ordinary_success_denominator_allowed",
    "repair_win_interpretation_allowed",
    "ranking_run",
    "winner_selected",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "m2769_guardrail_id",
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
    "actor_guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2769",
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
    "repair_candidate_rows",
    "repair_candidate_resolution_rows",
    "repair_checkpoint_rows",
    "baseline_join_rows",
    "repair_execution_rows",
    "repair_execution_failure_rows",
    "context_only_regression_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]


def run(
    *,
    m2766_dir: Path | str = DEFAULT_M2766_DIR,
    m2768_design: Path | str = DEFAULT_M2768_DESIGN,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    follow_up = Path(follow_up_manifest)
    write_follow_up_manifest(follow_up)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=follow_up)

    source = load_source_artifacts(
        m2766_dir=Path(m2766_dir),
        m2768_design=Path(m2768_design),
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
        source_checkpoint=Path(source_checkpoint),
        follow_up_manifest=follow_up,
    )
    repair_candidate_rows = build_repair_candidate_rows(source)
    context_rows = build_context_only_regression_rows(source)
    baseline_join_rows = build_baseline_join_rows(repair_candidate_rows, source)
    guardrail_rows = build_guardrail_context_rows(source["guardrail_rows"])
    checkpoint_rows = write_repair_checkpoint_rows(
        source_checkpoint=Path(source_checkpoint),
        output_dir=output,
        device=device,
        milestone=milestone,
    )
    resolution_rows = build_repair_candidate_resolution_rows(
        repair_candidate_rows=repair_candidate_rows,
        checkpoint_rows=checkpoint_rows,
        source=source,
    )
    write_csv_rows(paths["repair_candidate_rows"], repair_candidate_rows, fieldnames=REPAIR_CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["context_only_regression_rows"], context_rows, fieldnames=CONTEXT_FIELDNAMES)
    write_csv_rows(paths["baseline_join_rows"], baseline_join_rows, fieldnames=BASELINE_JOIN_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["repair_checkpoint_rows"], checkpoint_rows, fieldnames=CHECKPOINT_FIELDNAMES)
    write_csv_rows(paths["repair_candidate_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)

    execution_rows, failure_rows = run_repair_execution(
        resolution_rows=resolution_rows,
        checkpoint_rows=checkpoint_rows,
        source=source,
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    write_csv_rows(paths["repair_execution_rows"], execution_rows, fieldnames=EXECUTION_FIELDNAMES)
    write_csv_rows(paths["repair_execution_failure_rows"], failure_rows, fieldnames=FAILURE_FIELDNAMES)
    actor_guard_rows = build_actor_contract_guard_rows(
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
    )
    claim_rows = build_claim_boundary_rows(required_artifacts_present=False)
    gate_rows = build_gate_matrix_rows(
        source=source,
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        resolution_rows=resolution_rows,
        baseline_join_rows=baseline_join_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        resolution_rows=resolution_rows,
        baseline_join_rows=baseline_join_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
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
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        resolution_rows=resolution_rows,
        baseline_join_rows=baseline_join_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up,
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        resolution_rows=resolution_rows,
        baseline_join_rows=baseline_join_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
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
        repair_candidate_rows=repair_candidate_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        checkpoint_rows=checkpoint_rows,
        resolution_rows=resolution_rows,
        baseline_join_rows=baseline_join_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up,
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "repair_candidate_rows": output_dir / "repair_candidate_rows.csv",
        "repair_candidate_resolution_rows": output_dir / "repair_candidate_resolution_rows.csv",
        "repair_checkpoint_rows": output_dir / "repair_checkpoint_rows.csv",
        "baseline_join_rows": output_dir / "baseline_join_rows.csv",
        "repair_execution_rows": output_dir / "repair_execution_rows.csv",
        "repair_execution_failure_rows": output_dir / "repair_execution_failure_rows.csv",
        "context_only_regression_rows": output_dir / "context_only_regression_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m2766_dir: Path,
    m2768_design: Path,
    m1690_workload: Path,
    executable_specs: Path,
    source_checkpoint: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    workload_rows = read_csv_rows(m1690_workload)
    workload_by_task = {
        str(row["task_source_id"]): row
        for row in workload_rows
        if str(row.get("profile_name", "")) == CANONICAL_PROFILE
    }
    specs = load_executable_specs(executable_specs)
    spec_by_task = {str(spec["task_source_id"]): spec for spec in specs}
    source_exists = {
        "m2766_summary": (m2766_dir / "summary.json").exists(),
        "m2768_design": m2768_design.exists(),
        "repair_admission_rows": (m2766_dir / "repair_admission_rows.csv").exists(),
        "mechanism_localization_rows": (m2766_dir / "mechanism_localization_rows.csv").exists(),
        "telemetry_join_rows": (m2766_dir / "telemetry_join_rows.csv").exists(),
        "guardrail_context_rows": (m2766_dir / "guardrail_context_rows.csv").exists(),
        "actor_contract_guard_rows": (m2766_dir / "actor_contract_guard_rows.csv").exists(),
        "claim_boundary_rows": (m2766_dir / "claim_boundary_rows.csv").exists(),
        "gate_matrix": (m2766_dir / "gate_matrix.csv").exists(),
        "m1690_workload": m1690_workload.exists(),
        "executable_specs": executable_specs.exists(),
        "source_checkpoint": source_checkpoint.exists(),
        "follow_up_manifest": follow_up_manifest.exists(),
    }
    return {
        "m2766_dir": str(m2766_dir),
        "m2768_design": str(m2768_design),
        "m1690_workload": str(m1690_workload),
        "executable_specs": str(executable_specs),
        "source_checkpoint": str(source_checkpoint),
        "m2766_summary": read_json(m2766_dir / "summary.json") if source_exists["m2766_summary"] else {},
        "repair_admission_rows": read_csv_rows(m2766_dir / "repair_admission_rows.csv"),
        "mechanism_rows": read_csv_rows(m2766_dir / "mechanism_localization_rows.csv"),
        "telemetry_rows": read_csv_rows(m2766_dir / "telemetry_join_rows.csv"),
        "guardrail_rows": read_csv_rows(m2766_dir / "guardrail_context_rows.csv"),
        "actor_rows": read_csv_rows(m2766_dir / "actor_contract_guard_rows.csv"),
        "claim_rows": read_csv_rows(m2766_dir / "claim_boundary_rows.csv"),
        "gate_rows": read_csv_rows(m2766_dir / "gate_matrix.csv"),
        "workload_by_task": workload_by_task,
        "spec_by_task": spec_by_task,
        "source_exists": source_exists,
    }


def build_repair_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    mechanisms = {row["mechanism_localization_id"]: row for row in source["mechanism_rows"]}
    telemetry = {row["telemetry_join_id"]: row for row in source["telemetry_rows"]}
    rows: list[dict[str, Any]] = []
    for index, admission in enumerate(source["repair_admission_rows"], start=1):
        if not _bool(admission.get("repair_admitted_for_design", False)):
            continue
        mechanism = mechanisms.get(str(admission.get("mechanism_localization_id", "")), {})
        telem = telemetry.get(str(mechanism.get("telemetry_join_id", "")), {})
        rows.append(
            {
                "repair_candidate_row_id": f"m2769-repair-candidate-row-{len(rows) + 1:04d}",
                "repair_admission_id": admission.get("repair_admission_id", ""),
                "mechanism_localization_id": admission.get("mechanism_localization_id", ""),
                "source_candidate_id": admission.get("candidate_id", ""),
                "task_source_id": admission.get("task_source_id", ""),
                "primary_mechanism": admission.get("primary_mechanism", ""),
                "repair_target_class": admission.get("repair_target_class", ""),
                "repair_admitted_for_design": True,
                "repair_admission_status": admission.get("repair_admission_status", ""),
                "failure_family": mechanism.get("failure_family", telem.get("failure_family", "")),
                "termination_reason": mechanism.get("termination_reason", telem.get("termination_reason", "")),
                "diagnostic_outcome_bucket": mechanism.get("diagnostic_outcome_bucket", ""),
                "telemetry_join_id": mechanism.get("telemetry_join_id", ""),
                "finite_telemetry": _bool(mechanism.get("finite_telemetry", telem.get("finite_metric", False))),
                "track_containment_score": mechanism.get("track_containment_score", ""),
                "obstacle_timing_score": mechanism.get("obstacle_timing_score", ""),
                "command_response_mismatch_score": mechanism.get("command_response_mismatch_score", ""),
                "candidate_surface_role": "bounded_repair_execution_candidate",
                "ordinary_success_denominator_allowed": False,
                "ranking_run": False,
                "winner_selected": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_context_only_regression_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for admission in source["repair_admission_rows"]:
        if _bool(admission.get("repair_admitted_for_design", False)):
            continue
        rows.append(
            {
                "context_only_regression_id": f"m2769-context-only-regression-{len(rows) + 1:04d}",
                "repair_admission_id": admission.get("repair_admission_id", ""),
                "mechanism_localization_id": admission.get("mechanism_localization_id", ""),
                "source_candidate_id": admission.get("candidate_id", ""),
                "task_source_id": admission.get("task_source_id", ""),
                "primary_mechanism": admission.get("primary_mechanism", ""),
                "repair_target_class": admission.get("repair_target_class", ""),
                "repair_admitted_for_design": False,
                "context_role": "diagnostic_success_context_only_no_repair_regression_context",
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "repair_win_interpretation_allowed": False,
                "ranking_run": False,
                "winner_selected": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_baseline_join_rows(candidate_rows: list[dict[str, Any]], source: dict[str, Any]) -> list[dict[str, Any]]:
    telemetry = {row["telemetry_join_id"]: row for row in source["telemetry_rows"]}
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_rows, start=1):
        telem = telemetry.get(str(candidate.get("telemetry_join_id", "")), {})
        rows.append(
            {
                "baseline_join_id": f"m2769-baseline-join-{index:04d}",
                "repair_candidate_row_id": candidate.get("repair_candidate_row_id", ""),
                "repair_admission_id": candidate.get("repair_admission_id", ""),
                "source_candidate_id": candidate.get("source_candidate_id", ""),
                "task_source_id": candidate.get("task_source_id", ""),
                "telemetry_join_id": candidate.get("telemetry_join_id", ""),
                "mechanism_localization_id": candidate.get("mechanism_localization_id", ""),
                "primary_mechanism": candidate.get("primary_mechanism", ""),
                "repair_target_class": candidate.get("repair_target_class", ""),
                "baseline_termination_reason": telem.get("termination_reason", ""),
                "baseline_diagnostic_success": _bool(telem.get("diagnostic_success", False)),
                "baseline_collision": _bool(telem.get("collision", False)),
                "baseline_min_clearance_margin": telem.get("min_clearance_margin", ""),
                "baseline_previous_command": telem.get("previous_command", ""),
                "baseline_current_action": telem.get("current_action", ""),
                "baseline_trace_delta_proxy": telem.get("trace_delta_proxy", ""),
                "baseline_speed_response_proxy": telem.get("speed_response_proxy", ""),
                "baseline_yaw_response_proxy": telem.get("yaw_response_proxy", ""),
                "baseline_beta_response_proxy": telem.get("beta_response_proxy", ""),
                "baseline_finite_metric": _bool(telem.get("finite_metric", False)),
                "m2764_telemetry_coverage_improved": _bool(telem.get("m2764_telemetry_coverage_improved", False)),
                "m2759_row_backfilled": _bool(telem.get("m2759_row_backfilled", False)),
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(parent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, parent in enumerate(parent_rows, start=1):
        rows.append(
            {
                "m2769_guardrail_id": f"m2769-guardrail-context-{index:04d}",
                "m2766_guardrail_id": parent.get("m2766_guardrail_id", ""),
                "guardrail_context_id": parent.get("guardrail_context_id", ""),
                "guardrail_source": parent.get("guardrail_source", ""),
                "guardrail_source_id": parent.get("guardrail_source_id", ""),
                "task_source_id": parent.get("task_source_id", ""),
                "blocker_id": parent.get("blocker_id", ""),
                "route": parent.get("route", "Route A"),
                "evidence_family": parent.get("evidence_family", ""),
                "row_count": parent.get("row_count", ""),
                "blocking_count": parent.get("blocking_count", ""),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": parent.get("guardrail_role", "m2769_nonexecuted_guardrail_outside_denominator"),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def write_repair_checkpoint_rows(
    *,
    source_checkpoint: Path,
    output_dir: Path,
    device: str,
    milestone: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in DEFAULT_REPAIR_SPECS:
        rows.append(
            write_single_repair_checkpoint(
                source_checkpoint=source_checkpoint,
                repaired_checkpoint=output_dir / "checkpoints" / f"{spec['repair_candidate_id']}.pt",
                spec=spec,
                output_dir=output_dir,
                device=device,
                milestone=milestone,
            )
        )
    return rows


def write_single_repair_checkpoint(
    *,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    spec: Mapping[str, str | float],
    output_dir: Path,
    device: str,
    milestone: str,
) -> dict[str, Any]:
    model, checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
        raise RuntimeError("source checkpoint does not preserve actor observation 72/action 3 contract")
    source_state_hash = model_state_sha256(checkpoint["model_state"])
    with torch.no_grad():
        before_bias = [float(value) for value in model.actor_mean.bias.detach().cpu().tolist()]
        model.actor_mean.bias[0].add_(float(spec["steer_bias_delta"]))
        model.actor_mean.bias[1].add_(float(spec["throttle_bias_delta"]))
        model.actor_mean.bias[2].add_(float(spec["brake_bias_delta"]))
        after_bias = [float(value) for value in model.actor_mean.bias.detach().cpu().tolist()]
    repaired_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    repaired_state_hash = model_state_sha256(repaired_state)
    checkpoint_output = copy.deepcopy(checkpoint)
    checkpoint_output["model_state"] = repaired_state
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2769_mechanism_localized_bounded_repair_execution": {
            "milestone": milestone,
            "repair_candidate_id": str(spec["repair_candidate_id"]),
            "repair_lever_family": str(spec["repair_lever_family"]),
            "source_checkpoint": str(source_checkpoint),
            "output_dir": str(output_dir),
            "trainable_parameter_names": ["actor_mean.bias[0]", "actor_mean.bias[1]", "actor_mean.bias[2]"],
            "steer_bias_delta": float(spec["steer_bias_delta"]),
            "throttle_bias_delta": float(spec["throttle_bias_delta"]),
            "brake_bias_delta": float(spec["brake_bias_delta"]),
            "target_class_focus": str(spec["target_class_focus"]),
            "checkpoint_promoted": False,
            "repair_training_started": False,
            "ppo_used": False,
            "hidden_oracle_actor_input_required": False,
            "active_config_overwritten": False,
            "environment_difficulty_relaxed": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    repaired_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, repaired_checkpoint)
    finite_update = bool(np.all(np.isfinite(np.asarray(after_bias, dtype=float))))
    return {
        "repair_candidate_id": str(spec["repair_candidate_id"]),
        "repair_lever_family": str(spec["repair_lever_family"]),
        "source_checkpoint_path": str(source_checkpoint),
        "repair_checkpoint_path": str(repaired_checkpoint),
        "source_checkpoint_hash": _file_sha256(source_checkpoint),
        "repair_checkpoint_hash": _file_sha256(repaired_checkpoint),
        "source_model_state_hash": source_state_hash,
        "repair_model_state_hash": repaired_state_hash,
        "actor_mean_bias_before": _json_list(before_bias),
        "actor_mean_bias_after": _json_list(after_bias),
        "steer_bias_delta": float(spec["steer_bias_delta"]),
        "throttle_bias_delta": float(spec["throttle_bias_delta"]),
        "brake_bias_delta": float(spec["brake_bias_delta"]),
        "target_class_focus": str(spec["target_class_focus"]),
        "trainable_parameter_names": "actor_mean.bias[0];actor_mean.bias[1];actor_mean.bias[2]",
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "active_config_overwritten": False,
        "environment_difficulty_relaxed": False,
        "profile_specific_tuning": False,
        "per_row_tuning": False,
        "checkpoint_promoted": False,
        "repair_training_started": False,
        "ppo_used": False,
        "ranking_run": False,
        "winner_selected": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_repair_candidate_resolution_rows(
    *,
    repair_candidate_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for repair_row in repair_candidate_rows:
        task_source_id = str(repair_row["task_source_id"])
        workload = source["workload_by_task"].get(task_source_id, {})
        spec_exists = task_source_id in source["spec_by_task"]
        for checkpoint in checkpoint_rows:
            failure_reason = ""
            if not workload:
                failure_reason = "missing_l3_online_gru_workload_row"
            elif not spec_exists:
                failure_reason = "missing_executable_task_spec"
            elif not Path(str(checkpoint.get("repair_checkpoint_path", ""))).exists():
                failure_reason = "repair_checkpoint_missing"
            rows.append(
                {
                    "repair_candidate_resolution_id": f"m2769-repair-resolution-{len(rows) + 1:04d}",
                    "repair_candidate_row_id": repair_row.get("repair_candidate_row_id", ""),
                    "repair_candidate_id": checkpoint.get("repair_candidate_id", ""),
                    "repair_admission_id": repair_row.get("repair_admission_id", ""),
                    "source_candidate_id": repair_row.get("source_candidate_id", ""),
                    "task_source_id": task_source_id,
                    "workload_id": workload.get("workload_id", ""),
                    "profile_name": workload.get("profile_name", CANONICAL_PROFILE),
                    "task_family": workload.get("task_family", ""),
                    "source_edge": workload.get("source_edge", ""),
                    "profile_config_path": workload.get("profile_config_path", ""),
                    "source_checkpoint_path": checkpoint.get("source_checkpoint_path", ""),
                    "repair_checkpoint_path": checkpoint.get("repair_checkpoint_path", ""),
                    "repair_target_class": repair_row.get("repair_target_class", ""),
                    "primary_mechanism": repair_row.get("primary_mechanism", ""),
                    "resolution_status": (
                        "resolved_to_bounded_actor_head_repair_execution"
                        if not failure_reason
                        else "unresolved_or_not_admitted"
                    ),
                    "failure_reason": failure_reason,
                    "execution_admitted": not bool(failure_reason),
                    "actor_input_contract_changed": False,
                    "hidden_oracle_actor_input_required": False,
                    "environment_difficulty_relaxed": False,
                    "active_config_overwritten": False,
                    "profile_specific_tuning": False,
                    "per_row_tuning": False,
                    "ranking_run": False,
                    "winner_selected": False,
                    "diagnostic_only_no_verdict": True,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def run_repair_execution(
    *,
    resolution_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    source: dict[str, Any],
    output_dir: Path,
    executable_specs_path: Path,
    eval_seed_base: int,
    device: str,
    resume: bool,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not resume:
        for name in ("repair_execution_rows.csv", "repair_execution_failure_rows.csv", "run_state.json"):
            path = output_dir / name
            if path.exists():
                path.unlink()
    specs = load_executable_specs(executable_specs_path)
    spec_by_task = {str(spec["task_source_id"]): spec for spec in specs}
    checkpoint_by_id = {str(row["repair_candidate_id"]): row for row in checkpoint_rows}
    model_cache: dict[str, tuple[dict[str, Any], Any, dict[str, str]]] = {}
    execution_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for index, resolution in enumerate(resolution_rows):
        eval_seed = int(eval_seed_base) + index
        try:
            if not _bool(resolution.get("execution_admitted", False)):
                raise ValueError(str(resolution.get("failure_reason", "resolution_not_admitted")))
            task_source_id = str(resolution["task_source_id"])
            if task_source_id not in spec_by_task:
                raise KeyError(f"missing executable task spec for {task_source_id}")
            repair_candidate_id = str(resolution["repair_candidate_id"])
            checkpoint = checkpoint_by_id[repair_candidate_id]
            checkpoint_path = str(checkpoint["repair_checkpoint_path"])
            profile_config_path = str(resolution["profile_config_path"])
            cache_key = f"{repair_candidate_id}:{profile_config_path}:{checkpoint_path}"
            if cache_key not in model_cache:
                profile_config = read_json(profile_config_path)
                model, _checkpoint_payload = load_actor_critic_checkpoint(checkpoint_path, device=device)
                profile_row = {
                    "profile_name": CANONICAL_PROFILE,
                    "config_path": profile_config_path,
                    "checkpoint_path": checkpoint_path,
                }
                model_cache[cache_key] = (profile_config, model, profile_row)
            profile_config, model, profile_row = model_cache[cache_key]
            workload_row = dict(source["workload_by_task"][task_source_id])
            row = run_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_task[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(execution_metadata(resolution, eval_seed=eval_seed, index=len(execution_rows) + 1))
            execution_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every candidate pair must be accounted.
            failure_rows.append(
                failure_row(
                    resolution,
                    eval_seed=eval_seed,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    index=len(failure_rows) + 1,
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "expected_resolution_count": len(resolution_rows),
                "completed_execution_count": len(execution_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(execution_rows) + len(failure_rows),
                "latest_resolution_id": resolution.get("repair_candidate_resolution_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    write_run_state(
        output_dir / "run_state.json",
        {
            "expected_resolution_count": len(resolution_rows),
            "completed_execution_count": len(execution_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(execution_rows) + len(failure_rows),
            "complete": len(execution_rows) + len(failure_rows) == len(resolution_rows),
            "next_blocker": next_blocker,
        },
    )
    return execution_rows, failure_rows


def execution_metadata(resolution: Mapping[str, Any], *, eval_seed: int, index: int) -> dict[str, Any]:
    return {
        "repair_execution_id": f"m2769-repair-execution-{index:04d}",
        "repair_candidate_resolution_id": resolution.get("repair_candidate_resolution_id", ""),
        "repair_candidate_row_id": resolution.get("repair_candidate_row_id", ""),
        "repair_candidate_id": resolution.get("repair_candidate_id", ""),
        "repair_admission_id": resolution.get("repair_admission_id", ""),
        "source_candidate_id": resolution.get("source_candidate_id", ""),
        "task_source_id": resolution.get("task_source_id", ""),
        "workload_id": resolution.get("workload_id", ""),
        "profile_name": resolution.get("profile_name", CANONICAL_PROFILE),
        "task_family": resolution.get("task_family", ""),
        "source_edge": resolution.get("source_edge", ""),
        "primary_mechanism": resolution.get("primary_mechanism", ""),
        "repair_target_class": resolution.get("repair_target_class", ""),
        "repair_checkpoint_path": resolution.get("repair_checkpoint_path", ""),
        "eval_seed": int(eval_seed),
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "replay_started": False,
        "training_started": False,
        "ppo_used": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "environment_difficulty_relaxed": False,
        "active_config_overwritten": False,
        "profile_specific_tuning": False,
        "per_row_tuning": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "mechanism_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "context_labels_actor_visible": False,
        "guardrail_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def failure_row(
    resolution: Mapping[str, Any],
    *,
    eval_seed: int,
    error_type: str,
    error_message: str,
    index: int,
) -> dict[str, Any]:
    row = {
        "repair_execution_failure_id": f"m2769-repair-execution-failure-{index:04d}",
        "eval_seed": int(eval_seed),
        "error_type": error_type,
        "error_message": error_message,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
    }
    for key in (
        "repair_candidate_resolution_id",
        "repair_candidate_row_id",
        "repair_candidate_id",
        "repair_admission_id",
        "source_candidate_id",
        "task_source_id",
        "workload_id",
        "profile_name",
        "repair_target_class",
        "primary_mechanism",
    ):
        row[key] = resolution.get(key, "")
    row.update(
        {
            "replay_started": False,
            "training_started": False,
            "ppo_used": False,
            "source_build_run": False,
            "adapter_probe_run": False,
            "external_simulation_run": False,
            "private_holdout_used": False,
            "environment_difficulty_relaxed": False,
            "active_config_overwritten": False,
            "profile_specific_tuning": False,
            "per_row_tuning": False,
            "ranking_run": False,
            "winner_selected": False,
            "checkpoint_promoted": False,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_required": False,
            "mechanism_labels_actor_visible": False,
            "repair_target_labels_actor_visible": False,
            "context_labels_actor_visible": False,
            "guardrail_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "protected_rows_in_success_denominator": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def build_actor_contract_guard_rows(
    *,
    repair_candidate_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_exec = execution_rows + failure_rows
    rows = [
        ("p0_observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True, False),
        ("action_dim", ACTION_DIM, ACTION_DIM, True, False),
        ("repair_candidate_row_count", len(repair_candidate_rows), EXPECTED_REPAIR_ROW_COUNT, len(repair_candidate_rows) == EXPECTED_REPAIR_ROW_COUNT, False),
        ("context_only_row_count", len(context_rows), EXPECTED_CONTEXT_ONLY_ROW_COUNT, len(context_rows) == EXPECTED_CONTEXT_ONLY_ROW_COUNT, False),
        ("guardrail_row_count", len(guardrail_rows), EXPECTED_GUARDRAIL_ROW_COUNT, len(guardrail_rows) == EXPECTED_GUARDRAIL_ROW_COUNT, False),
        (
            "hidden_oracle_actor_input_required",
            any(_bool(row.get("hidden_oracle_actor_input_required", False)) for row in checkpoint_rows + all_exec),
            False,
            not any(_bool(row.get("hidden_oracle_actor_input_required", False)) for row in checkpoint_rows + all_exec),
            False,
        ),
        (
            "actor_input_contract_changed",
            any(_bool(row.get("actor_input_contract_changed", False)) for row in all_exec),
            False,
            not any(_bool(row.get("actor_input_contract_changed", False)) for row in all_exec),
            False,
        ),
        (
            "actor_visible_labels",
            any_label_visible(repair_candidate_rows, context_rows, guardrail_rows, all_exec),
            False,
            not any_label_visible(repair_candidate_rows, context_rows, guardrail_rows, all_exec),
            False,
        ),
        (
            "environment_difficulty_relaxed",
            any(_bool(row.get("environment_difficulty_relaxed", False)) for row in checkpoint_rows + all_exec),
            False,
            not any(_bool(row.get("environment_difficulty_relaxed", False)) for row in checkpoint_rows + all_exec),
            False,
        ),
        (
            "active_config_overwritten",
            any(_bool(row.get("active_config_overwritten", False)) for row in checkpoint_rows + all_exec),
            False,
            not any(_bool(row.get("active_config_overwritten", False)) for row in checkpoint_rows + all_exec),
            False,
        ),
    ]
    return [
        {
            "actor_guard_id": f"m2769-actor-guard-{index:04d}",
            "guard_family": guard,
            "observed": observed,
            "expected": expected,
            "status_pass": status,
            "actor_visible": actor_visible,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (guard, observed, expected, status, actor_visible) in enumerate(rows, start=1)
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool) -> list[dict[str, Any]]:
    claim_specs = [
        ("artifact_completeness", True, required_artifacts_present, "M2769 required artifact set exists"),
        ("repair_success", False, False, "M2770 result audit plus later proof/generalization gates required"),
        ("driver_performance", False, False, "same-case benchmark and promotion gates required"),
        ("validation_readiness", False, False, "separate validation readiness audit required"),
        ("ranking_or_winner", False, False, "ranking and winner selection are forbidden in M2769"),
        ("checkpoint_promotion", False, False, "promotion gates required"),
        ("paper_evidence", False, False, "Route B paper proof matrix required"),
        ("current_sim_verdict", False, False, "separate current-sim verdict gate required"),
        ("high_fidelity_validation", False, False, "Route C high-fidelity validation required"),
        ("full_ideal_driver", False, False, "full ideal driver gate required"),
        ("level3_self_identification", False, False, "history/self-ID proof gates required"),
    ]
    return [
        {
            "claim_id": f"m2769-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2769": allowed,
            "claim_made": made,
            "status_pass": (made is True) if allowed else (made is False),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claim_specs, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    repair_candidate_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    baseline_join_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    expected_resolution_count = len(repair_candidate_rows) * len(checkpoint_rows)
    all_exec = execution_rows + failure_rows
    gates = [
        ("source_artifacts_present", all(source["source_exists"].values()), source["source_exists"], "all source artifacts", "lineage_invalid"),
        ("m2766_status_pass", _bool(source["m2766_summary"].get("status_pass", False)), source["m2766_summary"].get("status_pass", ""), True, "lineage_invalid"),
        ("repair_candidate_count", len(repair_candidate_rows) == EXPECTED_REPAIR_ROW_COUNT, len(repair_candidate_rows), EXPECTED_REPAIR_ROW_COUNT, "scenario_sampling_failure"),
        ("context_only_count", len(context_rows) == EXPECTED_CONTEXT_ONLY_ROW_COUNT, len(context_rows), EXPECTED_CONTEXT_ONLY_ROW_COUNT, "scenario_sampling_failure"),
        ("guardrail_count", len(guardrail_rows) == EXPECTED_GUARDRAIL_ROW_COUNT, len(guardrail_rows), EXPECTED_GUARDRAIL_ROW_COUNT, "scenario_sampling_failure"),
        ("checkpoint_count", len(checkpoint_rows) == len(DEFAULT_REPAIR_SPECS), len(checkpoint_rows), len(DEFAULT_REPAIR_SPECS), "metric_artifact"),
        ("resolution_count", len(resolution_rows) == expected_resolution_count, len(resolution_rows), expected_resolution_count, "metric_artifact"),
        ("resolution_all_admitted", all(_bool(row.get("execution_admitted", False)) for row in resolution_rows), count_true(resolution_rows, "execution_admitted"), len(resolution_rows), "lineage_invalid"),
        ("baseline_join_count", len(baseline_join_rows) == EXPECTED_REPAIR_ROW_COUNT, len(baseline_join_rows), EXPECTED_REPAIR_ROW_COUNT, "metric_artifact"),
        ("baseline_finite_telemetry", all(_bool(row.get("baseline_finite_metric", False)) for row in baseline_join_rows), count_true(baseline_join_rows, "baseline_finite_metric"), len(baseline_join_rows), "metric_artifact"),
        ("m2759_no_backfill", not any(_bool(row.get("m2759_row_backfilled", False)) for row in baseline_join_rows), count_true(baseline_join_rows, "m2759_row_backfilled"), 0, "contract_violation"),
        ("execution_accounting", len(all_exec) == len(resolution_rows), len(all_exec), len(resolution_rows), "metric_artifact"),
        ("execution_failures_absent", len(failure_rows) == 0, len(failure_rows), 0, "behavior_regression"),
        ("execution_rows_finite", selected_metrics_are_finite(execution_rows) if execution_rows else False, len(execution_rows), "finite selected metrics", "metric_artifact"),
        ("context_not_executed", not any(_bool(row.get("execution_run", False)) for row in context_rows), count_true(context_rows, "execution_run"), 0, "contract_violation"),
        ("guardrails_not_executed", not any(_bool(row.get("execution_run", False)) for row in guardrail_rows), count_true(guardrail_rows, "execution_run"), 0, "contract_violation"),
        ("actor_guards_pass", all(_bool(row.get("status_pass", False)) for row in actor_guard_rows), count_true(actor_guard_rows, "status_pass"), len(actor_guard_rows), "contract_violation"),
        ("claim_boundaries_pass", all(_bool(row.get("status_pass", False)) for row in claim_rows), count_true(claim_rows, "status_pass"), len(claim_rows), "proof_washout"),
        ("forbidden_flags_false", not any(forbidden_flag(row) for row in checkpoint_rows + all_exec), "all false", "all false", "contract_violation"),
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2769-gate-{index:04d}",
            "gate_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, status, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    repair_candidate_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    baseline_join_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    actor_guards_pass = all(_bool(row.get("status_pass", False)) for row in actor_guard_rows)
    claim_rows_pass = all(_bool(row.get("status_pass", False)) for row in claim_rows)
    status_pass = bool(required_artifacts_present and gate_matrix_pass and actor_guards_pass and claim_rows_pass)
    margins = finite_floats(execution_rows, "min_clearance_margin")
    returns = finite_floats(execution_rows, "return")
    success_values = [_bool(row.get("success", False)) for row in execution_rows]
    collision_values = [_bool(row.get("collision", False)) for row in execution_rows]
    return {
        "milestone": milestone,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "artifacts": {key: str(value) for key, value in paths.items()},
        "required_artifacts_present": required_artifacts_present,
        "source_exists": source["source_exists"],
        "m2766_status_pass": _bool(source["m2766_summary"].get("status_pass", False)),
        "repair_candidate_row_count": len(repair_candidate_rows),
        "context_only_regression_row_count": len(context_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "repair_checkpoint_row_count": len(checkpoint_rows),
        "repair_candidate_resolution_row_count": len(resolution_rows),
        "baseline_join_row_count": len(baseline_join_rows),
        "repair_execution_row_count": len(execution_rows),
        "repair_execution_failure_row_count": len(failure_rows),
        "execution_accounted_count": len(execution_rows) + len(failure_rows),
        "expected_execution_pair_count": len(resolution_rows),
        "track_containment_target_count": sum(row.get("repair_target_class") == "track_containment_stability_target" for row in repair_candidate_rows),
        "obstacle_timing_target_count": sum(row.get("repair_target_class") == "obstacle_timing_or_clearance_margin_target" for row in repair_candidate_rows),
        "baseline_finite_metric_count": count_true(baseline_join_rows, "baseline_finite_metric"),
        "m2764_telemetry_coverage_improved_count": count_true(baseline_join_rows, "m2764_telemetry_coverage_improved"),
        "m2759_rows_backfilled": any(_bool(row.get("m2759_row_backfilled", False)) for row in baseline_join_rows),
        "success_rate_diagnostic": float(np.mean(success_values)) if success_values else None,
        "collision_rate_diagnostic": float(np.mean(collision_values)) if collision_values else None,
        "clearance_margin_mean_diagnostic": float(np.mean(margins)) if margins else None,
        "return_mean_diagnostic": float(np.mean(returns)) if returns else None,
        "all_selected_metrics_finite": selected_metrics_are_finite(execution_rows) if execution_rows else False,
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": actor_guards_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_row_count": len(gate_rows),
        "guardrail_execution": any(_bool(row.get("execution_run", False)) for row in guardrail_rows),
        "context_only_execution": any(_bool(row.get("execution_run", False)) for row in context_rows),
        "protected_rows_in_success_denominator": any(
            _bool(row.get("protected_rows_in_success_denominator", False)) for row in guardrail_rows + execution_rows
        ),
        "diagnostic_labels_actor_visible": any_label_visible(repair_candidate_rows, context_rows, guardrail_rows, execution_rows + failure_rows),
        "actor_input_contract_changed": any(_bool(row.get("actor_input_contract_changed", False)) for row in execution_rows + failure_rows),
        "hidden_oracle_actor_input_required": any(
            _bool(row.get("hidden_oracle_actor_input_required", False)) for row in checkpoint_rows + execution_rows + failure_rows
        ),
        **FALSE_CLAIM_FLAGS,
        "environment_reset_run": bool(execution_rows),
        "environment_step_run": bool(execution_rows),
        "policy_action_run": bool(execution_rows),
        "policy_rollout_run": bool(execution_rows),
        "follow_up_manifest": str(follow_up_manifest),
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }


def write_follow_up_manifest(path: Path) -> None:
    manifest_id = DEFAULT_NEXT_BLOCKER
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": manifest_id,
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
            "parent_checkpoint": [str(DEFAULT_SOURCE_CHECKPOINT)],
            "parent_dataset": [
                "docs/m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight.md",
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "repair_candidate_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "repair_candidate_resolution_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "repair_checkpoint_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "baseline_join_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "repair_execution_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "repair_execution_failure_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "context_only_regression_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "guardrail_context_rows.csv"),
                "docs/m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight.json",
                "experiments/manifests/m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design.json",
            ],
            "parent_objective": [
                "audit M2769 bounded mechanism-localized repair execution artifacts before any repair interpretation"
            ],
            "derived_from": [
                "m2769-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-preflight",
                "m2768-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-design",
                "m2767-engineering-controller-route-a-action-response-telemetry-mechanism-localization-panel-materialization-result-audit",
            ],
            "blocked_by": [
                "M2769 repair execution artifacts require result audit before repair-success validation ranking or performance claim"
            ],
            "supersedes": [
                "repair success interpretation before auditing M2769",
                "another repair execution before auditing M2769",
                "checkpoint promotion or winner selection from M2769 preflight rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{manifest_id}.md",
        "public_gates": [
            "M2770 must consume M2769 summary candidate resolution checkpoint baseline execution failure context guard actor claim and gate artifacts",
            "M2770 must accept or reject artifact completeness and claim safety",
            "M2770 must preserve the 8 repair rows 4 context-only rows and 31 guardrails with actor-invisible labels",
            "M2770 must reject repair success driver performance validation ranking paper current-sim high-fidelity full ideal driver and self-ID claims",
            "M2770 must route to bounded synthesis artifact repair or next design without executing replay validation training ranking or promotion",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute replay validation training PPO source build adapter probe or external simulation",
            "do not rank candidates repair target classes controllers source edges profiles task families or mechanism tags",
            "do not select a winner promote a checkpoint or compute success-rate verdict",
            "do not claim repair success driver performance validation readiness paper current-sim high-fidelity full ideal driver or self-ID",
            "do not hide M2769 failures context-only rows or guardrail rows",
            "do not change actor inputs or expose repair labels to actor input",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_action_response_mechanism_localized_repair",
            "evidence_axis": "action_response_mechanism_localized_bounded_repair_execution_result_audit",
            "evidence_increment": "audits whether M2769 produced complete bounded repair candidate execution artifacts before interpretation",
            "claim_scope": "Route A repair execution result audit only; no replay validation training ranking promotion repair-success driver-performance paper current-sim high-fidelity self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2769 artifacts are incomplete",
                "stop if actor or claim boundaries were violated",
                "stop if repair rows context-only rows or guardrails cannot be separated",
            ],
            "fallback_plan": [
                "route to artifact repair if M2769 joins or artifact accounting are incomplete",
                "route to branch synthesis if bounded repair execution adds negative or ambiguous evidence",
                "route to a bounded next design only if the audit accepts complete non-ranking evidence",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2769 bounded repair execution artifacts require result audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "mechanism-localized bounded repair execution result audit",
            "admission_evidence": [
                "M2769 artifacts exist",
                "M2769 registers this result-audit follow-up before interpretation",
            ],
            "blocked_shortcuts": [
                "no replay validation training ranking promotion or performance claim",
                "no actor input change or hidden oracle input",
            ],
            "allowed_updates": [
                f"docs/{manifest_id}.md",
                "M2770 status queue scoreboard research log and review",
                "one bounded follow-up manifest if audit accepts artifacts",
            ],
            "next_stage_criteria": [
                "M2770 accepts or rejects M2769 artifacts and claim boundaries",
                "M2770 registers one bounded next step or synthesis route",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2770 audits Route A engineering repair artifacts and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "None in M2770; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2764-M2770 Route A action-response mechanism-localized repair artifacts only.",
            "negative_result_policy": "If M2769 artifacts are incomplete or negative preserve the result and route to synthesis or artifact repair rather than weakening gates or claiming self-ID evidence.",
            "allowed_claims": [
                "M2769 bounded repair execution artifacts are complete and claim-safe or explicitly rejected",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new M2769 repair execution artifacts before another repair loop",
            "paper_verdict_delta": "no paper verdict; can decide whether Route A should synthesize, repair artifacts, or admit another bounded evidence step",
            "must_synthesize_if": [
                "M2770 cannot decide a bounded next step after complete M2769 artifacts",
                "M2770 proposes another same-surface repair execution without a new evidence axis",
                "M2770 would make validation performance paper current-sim high-fidelity full-driver or self-ID claims",
            ],
        },
        "hypothesis": "M2769 bounded repair execution artifacts can be audited as complete and claim-safe before interpretation.",
        "success_criteria": [
            f"docs/{manifest_id}.md exists",
            "M2770 accepts or rejects M2769 bounded repair execution evidence",
            "actor and claim boundaries are preserved",
            "one bounded follow-up or synthesis route is registered",
        ],
        "failure_criteria": [
            "M2770 overclaims M2769 as repair success validation performance paper current-sim high-fidelity full-driver or self-ID evidence",
            "M2770 hides M2769 failures context-only rows or guardrail violations",
            "M2770 fails to register a bounded next step or synthesis route",
        ],
        "decision_rule": "Pass only if M2770 provides a bounded result audit of M2769 artifacts and preserves all actor guardrail and claim boundaries.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "md"}],
        "baseline_checkpoints": [str(DEFAULT_SOURCE_CHECKPOINT)],
        "baseline_artifacts": [
            str(DEFAULT_OUTPUT_DIR / "summary.json"),
            str(DEFAULT_OUTPUT_DIR / "repair_execution_rows.csv"),
            str(DEFAULT_OUTPUT_DIR / "repair_execution_failure_rows.csv"),
            str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
        ],
    }
    write_json(path, payload)


def render_doc(summary: Mapping[str, Any]) -> str:
    return f"""# M2769 Engineering Controller Route A Action-Response Mechanism-Localized Bounded Repair Execution Preflight

## Metadata

- status: completed
- result class: `{summary['result_class']}`
- milestone: `{summary['milestone']}`
- summary: `{summary['artifacts']['summary']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
- next: `{summary['next_blocker']}`

## Result

M2769 executed or accounted for a bounded actor-head repair candidate sweep over
the M2766 mechanism-localized repair surface.

```text
status_pass: {summary['status_pass']}
gate_matrix_pass: {summary['gate_matrix_pass']}
repair candidate rows: {summary['repair_candidate_row_count']}
context-only regression rows: {summary['context_only_regression_row_count']}
guardrail context rows: {summary['guardrail_context_row_count']}
repair checkpoint rows: {summary['repair_checkpoint_row_count']}
candidate-resolution rows: {summary['repair_candidate_resolution_row_count']}
baseline join rows: {summary['baseline_join_row_count']}
repair execution rows: {summary['repair_execution_row_count']}
repair execution failure rows: {summary['repair_execution_failure_row_count']}
expected execution pairs: {summary['expected_execution_pair_count']}
```

The admitted repair surface remains exactly 8 M2766 rows: 7
track-containment stability targets and 1 obstacle-timing or clearance-margin
target. The 4 diagnostic-success rows are preserved as context-only regression
rows and the 31 guardrail rows remain non-executed outside ordinary success
denominators.

## Diagnostic Metrics

These metrics are diagnostic accounting only:

```text
success_rate_diagnostic: {summary['success_rate_diagnostic']}
collision_rate_diagnostic: {summary['collision_rate_diagnostic']}
clearance_margin_mean_diagnostic: {summary['clearance_margin_mean_diagnostic']}
return_mean_diagnostic: {summary['return_mean_diagnostic']}
all_selected_metrics_finite: {summary['all_selected_metrics_finite']}
```

They are not a success-rate verdict, repair-success claim, driver-performance
claim, validation result, paper result, current-sim verdict, high-fidelity
result, full-driver gate, or self-ID claim.

## Actor And Claim Boundary

```text
actor_contract_guard_rows_pass: {summary['actor_contract_guard_rows_pass']}
claim_boundary_rows_pass: {summary['claim_boundary_rows_pass']}
hidden_oracle_actor_input_required: {summary['hidden_oracle_actor_input_required']}
actor_input_contract_changed: {summary['actor_input_contract_changed']}
diagnostic_labels_actor_visible: {summary['diagnostic_labels_actor_visible']}
environment_difficulty_relaxed: {summary['environment_difficulty_relaxed']}
active_config_overwritten: {summary['active_config_overwritten']}
profile_specific_tuning: {summary['profile_specific_tuning']}
ranking_run: {summary['ranking_run']}
winner_selected: {summary['winner_selected']}
checkpoint_promoted: {summary['checkpoint_promoted']}
```

M2769 preserves actor 72/action 3, uses no hidden/oracle actor input, does not
relax environment difficulty, does not overwrite active configs, does not tune
per row, and does not rank or promote candidates.

## Route

M2769 routes to:

```text
{summary['next_blocker']}
```

M2770 must audit these artifacts before any repair interpretation, validation,
ranking, performance claim, paper claim, current-sim verdict, high-fidelity
claim, full ideal driver claim, or level3 self-identification claim.
"""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_list(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.9g}" for value in values) + "]"


def any_label_visible(
    repair_candidate_rows: list[Mapping[str, Any]],
    context_rows: list[Mapping[str, Any]],
    guardrail_rows: list[Mapping[str, Any]],
    execution_like_rows: list[Mapping[str, Any]],
) -> bool:
    for row in repair_candidate_rows:
        if _bool(row.get("actor_visible_allowed", False)):
            return True
    for row in context_rows + guardrail_rows:
        if _bool(row.get("actor_visible_allowed", False)):
            return True
    for row in execution_like_rows:
        for key in (
            "mechanism_labels_actor_visible",
            "repair_target_labels_actor_visible",
            "context_labels_actor_visible",
            "guardrail_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
        ):
            if _bool(row.get(key, False)):
                return True
    return False


def forbidden_flag(row: Mapping[str, Any]) -> bool:
    for key in (
        "replay_started",
        "replay_run",
        "validation_run",
        "training_started",
        "training_run",
        "ppo_used",
        "ppo_run",
        "source_build_run",
        "adapter_probe_run",
        "external_simulation_run",
        "private_holdout_used",
        "environment_difficulty_relaxed",
        "active_config_overwritten",
        "profile_specific_tuning",
        "per_row_tuning",
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "paper_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "level3_self_id_claim_made",
    ):
        if _bool(row.get(key, False)):
            return True
    return False


def finite_floats(rows: list[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    return values


def count_true(rows: list[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key, False)) for row in rows)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2766-dir", type=Path, default=DEFAULT_M2766_DIR)
    parser.add_argument("--m2768-design", type=Path, default=DEFAULT_M2768_DESIGN)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(
        m2766_dir=args.m2766_dir,
        m2768_design=args.m2768_design,
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        source_checkpoint=args.source_checkpoint,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=int(args.eval_seed_base),
        device=args.device,
        resume=not args.no_resume,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"repair_execution_row_count={summary['repair_execution_row_count']}")
    print(f"repair_execution_failure_row_count={summary['repair_execution_failure_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
