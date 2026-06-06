"""Run M2931 offtrack-dominant single-candidate repair execution preflight.

M2931 consumes the accepted M2925/M2928/M2929/M2930 Route A offtrack repair
admission chain. It runs at most one bounded diagnostic rollout per M2925 panel
row with the fixed M2655 repair candidate, or writes one failure row. It does
not train, validate, rank, promote, compute a repair-success verdict, or claim
driver performance.
"""

from __future__ import annotations

import argparse
from collections import Counter
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


MILESTONE_ID = (
    "m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-"
    "repair-execution-preflight"
)
NEXT_ID = (
    "m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-"
    "repair-execution-result-audit"
)
DEFAULT_M2925_DIR = Path(
    "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight"
)
DEFAULT_M2928_DIR = Path(
    "runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight"
)
DEFAULT_M2919_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2929_AUDIT = Path(
    "docs/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.md"
)
DEFAULT_M2930_DESIGN = Path(
    "docs/m2930-engineering-controller-route-a-offtrack-dominant-repair-execution-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit.json"
)
DEFAULT_REPAIR_CANDIDATE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
    "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_REPAIR_PROFILE_CONFIG = Path(
    "runs/m1674_controller_family_one_seed_public_pilot/configs/L3_online_gru_seed167400.json"
)
REPAIR_PROFILE_NAME = "L3_online_gru"
DEFAULT_EVAL_SEED_BASE = 293100

EXPECTED_TOTAL_ROW_COUNT = 56
EXPECTED_OFFTRACK_COUNT = 38
EXPECTED_NON_OFFTRACK_CONTEXT_COUNT = 18
EXPECTED_COVERAGE_CONSTRAINT_COUNT = 27
EXPECTED_SHORTCUT_EXCLUSION_COUNT = 7
EXPECTED_SOURCE_MILESTONE_COUNTS = {"m2737": 12, "m2746": 10, "m2807": 8, "m2816": 8}
EXPECTED_TASK_FAMILY_COUNTS = {"T4": 21, "T5": 17}
REQUIRED_SHORTCUT_FAMILIES = {
    "hidden_oracle_future_target_actor_input",
    "hidden_dynamics_parameters",
    "controller_route_labels",
    "map_or_oracle_progress_metrics",
    "rank_winner_shortcut",
    "overclaim_shortcut",
    "execution_training_shortcut",
}

CLAIM_SCOPE = (
    "M2931 Route A offtrack-dominant single-candidate repair diagnostic "
    "execution only; reset, step, policy action, and rollout may be recorded "
    "for resolved rows from the 56-row M2925 panel with the fixed M2655 repair "
    "candidate. No replay, measured validation, training, PPO, dependency "
    "work, ranking, winner selection, checkpoint promotion, repair-success "
    "verdict, driver-performance, paper, finite-window-vs-GRU, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

CANDIDATE_FIELDNAMES = [
    "repair_execution_candidate_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "source_family",
    "source_edge",
    "source_row_id",
    "task_family",
    "task_source_id",
    "workload_id",
    "profile_name",
    "m2919_execution_candidate_id",
    "m2919_resolution_id",
    "original_checkpoint_context",
    "original_checkpoint_path",
    "repair_candidate_checkpoint_path",
    "repair_candidate_profile_config_path",
    "repair_candidate_profile_name",
    "env_template_family",
    "window_tag",
    "profile_env_history_length",
    "outcome_family",
    "previous_termination_reason",
    "offtrack_severity_band",
    "time_to_offtrack_band",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "measured_validation_scheduled",
    "training_scheduled",
    "replay_scheduled",
    "ppo_scheduled",
    "dependency_execution_scheduled",
    "profile_specific_tuning",
    "repair_overlay_used",
    "ranking_run",
    "winner_selection_allowed",
    "promotion_allowed",
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
    "repair_execution_resolution_id",
    "repair_execution_candidate_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "source_row_id",
    "task_family",
    "task_source_id",
    "workload_id",
    "profile_name",
    "repair_candidate_checkpoint_path",
    "repair_candidate_profile_config_path",
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
    "m2931_eval_seed",
    "repair_execution_resolution_id",
    "repair_execution_candidate_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "source_family",
    "source_row_id",
    "offtrack_dominant_single_candidate_repair_execution_preflight",
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
    "repair_overlay_used",
    "dependency_execution_performed",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_verdict_claim_made",
    "repair_success_claim_made",
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
FAILURE_FIELDNAMES = [
    "repair_execution_resolution_id",
    "repair_execution_candidate_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "source_row_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "m2931_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "dependency_execution_performed",
    "private_holdout_used",
    "profile_specific_tuning",
    "active_config_overwritten",
    "repair_overlay_used",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "m2877_guard_execution",
    "route_b_context_execution",
    "route_c_context_execution",
    "guardrail_rows_in_success_denominator",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "route_labels_actor_visible",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "success_rate_verdict_claim_made",
    "repair_success_claim_made",
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
TARGET_CONTEXT_FIELDNAMES = [
    "target_context_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "task_family",
    "workload_id",
    "task_source_id",
    "profile_name",
    "checkpoint_context",
    "env_template_family",
    "window_tag",
    "outcome_family",
    "coverage_preserved",
    "execution_candidate",
    "execution_admitted",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "ranking_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
COVERAGE_AUDIT_FIELDNAMES = [
    "coverage_audit_id",
    "coverage_constraint_id",
    "coverage_family",
    "coverage_value",
    "observed_row_count",
    "expected_row_count",
    "source_scope",
    "coverage_constraint_status_pass",
    "ranking_claim_made",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "m2931_audit_status_pass",
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
    "allowed_in_m2931",
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
    "repair_execution_candidate_rows",
    "repair_execution_resolution_rows",
    "repair_execution_rows",
    "repair_execution_failure_rows",
    "repair_target_context_rows",
    "coverage_constraint_audit_rows",
    "source_milestone_aggregate",
    "task_family_aggregate",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_offtrack_dominant_repair_execution_preflight(
    *,
    m2925_dir: Path | str = DEFAULT_M2925_DIR,
    m2928_dir: Path | str = DEFAULT_M2928_DIR,
    m2919_dir: Path | str = DEFAULT_M2919_DIR,
    m2929_audit: Path | str = DEFAULT_M2929_AUDIT,
    m2930_design: Path | str = DEFAULT_M2930_DESIGN,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    repair_candidate_checkpoint: Path | str = DEFAULT_REPAIR_CANDIDATE_CHECKPOINT,
    repair_profile_config: Path | str = DEFAULT_REPAIR_PROFILE_CONFIG,
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
        m2925_dir=Path(m2925_dir),
        m2928_dir=Path(m2928_dir),
        m2919_dir=Path(m2919_dir),
        m2929_audit=Path(m2929_audit),
        m2930_design=Path(m2930_design),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        repair_candidate_checkpoint=Path(repair_candidate_checkpoint),
        repair_profile_config=Path(repair_profile_config),
        follow_up_manifest=Path(follow_up_manifest),
    )

    candidate_rows = build_repair_execution_candidate_rows(source)
    write_csv_rows(paths["repair_execution_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    resolution_rows, resolved_workloads = build_resolution_rows(source, candidate_rows)
    write_csv_rows(paths["repair_execution_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)

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
    target_rows = build_repair_target_context_rows(candidate_rows, resolution_rows)
    coverage_rows = build_coverage_constraint_audit_rows(source["m2928_coverage_constraint_rows"])
    guardrail_rows = build_guardrail_context_rows(source["m2925_guardrail_context_rows"])
    source_aggregate_rows = build_aggregate_rows(
        aggregate_family="source_milestone",
        key="source_milestone",
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["repair_execution_rows"],
        failure_rows=artifact_rows["repair_execution_failure_rows"],
    )
    task_aggregate_rows = build_aggregate_rows(
        aggregate_family="task_family",
        key="task_family",
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["repair_execution_rows"],
        failure_rows=artifact_rows["repair_execution_failure_rows"],
    )

    write_csv_rows(paths["repair_target_context_rows"], target_rows, fieldnames=TARGET_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["coverage_constraint_audit_rows"], coverage_rows, fieldnames=COVERAGE_AUDIT_FIELDNAMES)
    write_csv_rows(paths["source_milestone_aggregate"], source_aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["task_family_aggregate"], task_aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        source=source,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["repair_execution_rows"],
        failure_rows=artifact_rows["repair_execution_failure_rows"],
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        episode_rows_present=bool(artifact_rows["repair_execution_rows"]),
        episode_or_failure_rows_present=bool(
            artifact_rows["repair_execution_rows"] or artifact_rows["repair_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        target_rows=target_rows,
        coverage_rows=coverage_rows,
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
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        target_rows=target_rows,
        coverage_rows=coverage_rows,
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
        episode_rows_present=bool(artifact_rows["repair_execution_rows"]),
        episode_or_failure_rows_present=bool(
            artifact_rows["repair_execution_rows"] or artifact_rows["repair_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        target_rows=target_rows,
        coverage_rows=coverage_rows,
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
        target_rows=target_rows,
        coverage_rows=coverage_rows,
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
    write_run_state(
        paths["run_state"],
        {
            "candidate_count": len(candidate_rows),
            "resolved_candidate_count": summary["resolved_candidate_count"],
            "completed_execution_count": summary["repair_execution_row_count"],
            "failure_count": summary["repair_execution_failure_row_count"],
            "accounted_count": summary["accounted_candidate_count"],
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "repair_execution_candidate_rows": output_dir / "repair_execution_candidate_rows.csv",
        "repair_execution_resolution_rows": output_dir / "repair_execution_resolution_rows.csv",
        "repair_execution_rows": output_dir / "repair_execution_rows.csv",
        "repair_execution_failure_rows": output_dir / "repair_execution_failure_rows.csv",
        "repair_target_context_rows": output_dir / "repair_target_context_rows.csv",
        "coverage_constraint_audit_rows": output_dir / "coverage_constraint_audit_rows.csv",
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
    m2925_dir: Path,
    m2928_dir: Path,
    m2919_dir: Path,
    m2929_audit: Path,
    m2930_design: Path,
    executable_specs: Path,
    executable_workload: Path,
    repair_candidate_checkpoint: Path,
    repair_profile_config: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2929_audit": m2929_audit,
        "m2930_design": m2930_design,
        "m2925_summary": m2925_dir / "summary.json",
        "m2925_offtrack_slice_rows": m2925_dir / "offtrack_slice_rows.csv",
        "m2925_non_offtrack_context_rows": m2925_dir / "non_offtrack_context_rows.csv",
        "m2925_guardrail_context_rows": m2925_dir / "guardrail_context_rows.csv",
        "m2928_summary": m2928_dir / "summary.json",
        "m2928_repair_hypothesis_rows": m2928_dir / "repair_hypothesis_rows.csv",
        "m2928_coverage_constraint_rows": m2928_dir / "coverage_constraint_rows.csv",
        "m2928_shortcut_exclusion_rows": m2928_dir / "shortcut_exclusion_rows.csv",
        "m2928_actor_contract_guard_rows": m2928_dir / "actor_contract_guard_rows.csv",
        "m2928_claim_boundary_rows": m2928_dir / "claim_boundary_rows.csv",
        "m2928_gate_matrix": m2928_dir / "gate_matrix.csv",
        "m2919_bounded_execution_rows": m2919_dir / "bounded_execution_rows.csv",
        "executable_task_specs": executable_specs,
        "executable_workload": executable_workload,
        "repair_candidate_checkpoint": repair_candidate_checkpoint,
        "repair_profile_config": repair_profile_config,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m2919_rows = read_csv_rows(paths["m2919_bounded_execution_rows"])
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2929_audit_text": paths["m2929_audit"].read_text(encoding="utf-8")
        if source_exists["m2929_audit"]
        else "",
        "m2930_design_text": paths["m2930_design"].read_text(encoding="utf-8")
        if source_exists["m2930_design"]
        else "",
        "m2925_summary": read_json(paths["m2925_summary"]) if source_exists["m2925_summary"] else {},
        "m2925_offtrack_slice_rows": read_csv_rows(paths["m2925_offtrack_slice_rows"]),
        "m2925_non_offtrack_context_rows": read_csv_rows(paths["m2925_non_offtrack_context_rows"]),
        "m2925_guardrail_context_rows": read_csv_rows(paths["m2925_guardrail_context_rows"]),
        "m2928_summary": read_json(paths["m2928_summary"]) if source_exists["m2928_summary"] else {},
        "m2928_repair_hypothesis_rows": read_csv_rows(paths["m2928_repair_hypothesis_rows"]),
        "m2928_coverage_constraint_rows": read_csv_rows(paths["m2928_coverage_constraint_rows"]),
        "m2928_shortcut_exclusion_rows": read_csv_rows(paths["m2928_shortcut_exclusion_rows"]),
        "m2928_actor_contract_guard_rows": read_csv_rows(paths["m2928_actor_contract_guard_rows"]),
        "m2928_claim_boundary_rows": read_csv_rows(paths["m2928_claim_boundary_rows"]),
        "m2928_gate_matrix": read_csv_rows(paths["m2928_gate_matrix"]),
        "m2919_bounded_execution_rows": m2919_rows,
        "m2919_by_execution_candidate_id": {
            str(row.get("execution_candidate_id", "")): row for row in m2919_rows if row.get("execution_candidate_id")
        },
        "m2919_by_resolution_id": {str(row.get("resolution_id", "")): row for row in m2919_rows if row.get("resolution_id")},
        "m2919_by_source_row_id": {str(row.get("source_row_id", "")): row for row in m2919_rows if row.get("source_row_id")},
        "executable_workload_rows": read_csv_rows(paths["executable_workload"]),
        "repair_candidate_checkpoint": str(repair_candidate_checkpoint),
        "repair_profile_config": str(repair_profile_config),
    }


def build_repair_execution_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source["m2925_offtrack_slice_rows"]:
        rows.append(candidate_row(len(rows) + 1, row, panel_family="offtrack_repair_target", lineage={}))
    for row in source["m2925_non_offtrack_context_rows"]:
        lineage = (
            source["m2919_by_execution_candidate_id"].get(str(row.get("execution_candidate_id", "")))
            or source["m2919_by_resolution_id"].get(str(row.get("resolution_id", "")))
            or source["m2919_by_source_row_id"].get(str(row.get("source_row_id", "")))
            or {}
        )
        rows.append(candidate_row(len(rows) + 1, row, panel_family="non_offtrack_context_regression", lineage=lineage))
    return rows


def candidate_row(index: int, row: Mapping[str, Any], *, panel_family: str, lineage: Mapping[str, Any]) -> dict[str, Any]:
    panel_row_id = str(row.get("offtrack_slice_id") or row.get("context_row_id") or row.get("panel_row_id") or "")
    task_source_id = str(row.get("task_source_id") or lineage.get("task_source_id") or "")
    workload_id = str(row.get("workload_id") or lineage.get("workload_id") or "")
    profile_name = str(row.get("profile_name") or lineage.get("profile_name") or REPAIR_PROFILE_NAME)
    source_family = str(row.get("source_family") or lineage.get("source_family") or "")
    return {
        "repair_execution_candidate_id": f"m2931-repair-execution-candidate-{index:04d}",
        "panel_row_id": panel_row_id,
        "panel_row_family": panel_family,
        "source_milestone": row.get("source_milestone", ""),
        "source_family": source_family,
        "source_edge": row.get("source_edge") or lineage.get("source_edge", ""),
        "source_row_id": row.get("source_row_id", ""),
        "task_family": row.get("task_family") or lineage.get("task_family", ""),
        "task_source_id": task_source_id,
        "workload_id": workload_id,
        "profile_name": profile_name,
        "m2919_execution_candidate_id": row.get("execution_candidate_id") or lineage.get("execution_candidate_id", ""),
        "m2919_resolution_id": row.get("resolution_id") or lineage.get("resolution_id", ""),
        "original_checkpoint_context": row.get("checkpoint_context") or checkpoint_context(lineage),
        "original_checkpoint_path": row.get("checkpoint_path") or lineage.get("checkpoint_path", ""),
        "repair_candidate_checkpoint_path": str(DEFAULT_REPAIR_CANDIDATE_CHECKPOINT),
        "repair_candidate_profile_config_path": str(DEFAULT_REPAIR_PROFILE_CONFIG),
        "repair_candidate_profile_name": REPAIR_PROFILE_NAME,
        "env_template_family": row.get("env_template_family") or lineage.get("env_template_family", ""),
        "window_tag": row.get("window_tag") or lineage.get("window_tag", ""),
        "profile_env_history_length": row.get("profile_env_history_length") or lineage.get("profile_env_history_length", ""),
        "outcome_family": row.get("outcome_family") or "off_track",
        "previous_termination_reason": row.get("termination_reason") or lineage.get("termination_reason", ""),
        "offtrack_severity_band": row.get("offtrack_severity_band", ""),
        "time_to_offtrack_band": row.get("time_to_offtrack_band", ""),
        "environment_reset_scheduled": True,
        "environment_rollout_scheduled": True,
        "measured_validation_scheduled": False,
        "training_scheduled": False,
        "replay_scheduled": False,
        "ppo_scheduled": False,
        "dependency_execution_scheduled": False,
        "profile_specific_tuning": False,
        "repair_overlay_used": False,
        "ranking_run": False,
        "winner_selection_allowed": False,
        "promotion_allowed": False,
        "actor_observation_dim": P0_OBSERVATION_DIM,
        "actor_action_dim": ACTION_DIM,
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
        "diagnostic_only_no_verdict": True,
        "checkpoint_exists": DEFAULT_REPAIR_CANDIDATE_CHECKPOINT.exists(),
        "profile_config_exists": DEFAULT_REPAIR_PROFILE_CONFIG.exists(),
        "claim_boundary": CLAIM_SCOPE,
    }


def build_resolution_rows(
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    workload_by_id = {str(row.get("workload_id", "")): row for row in source["executable_workload_rows"]}
    rows: list[dict[str, Any]] = []
    resolved_workloads: dict[str, dict[str, Any]] = {}
    source_failure = source_prerequisite_failure(source)
    for index, candidate in enumerate(candidate_rows, start=1):
        workload = workload_by_id.get(str(candidate.get("workload_id", "")))
        failure_reason = source_failure
        if not failure_reason:
            failure_reason = candidate_failure_reason(candidate, workload)
        execution_admitted = not failure_reason
        resolution_id = f"m2931-repair-execution-resolution-{index:04d}"
        resolved_workload = dict(workload or {})
        if execution_admitted:
            resolved_workload.update(
                {
                    "checkpoint_path": source["repair_candidate_checkpoint"],
                    "profile_config_path": source["repair_profile_config"],
                    "profile_name": REPAIR_PROFILE_NAME,
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "profile_specific_tuning": False,
                    "environment_rollout_scheduled": True,
                    "training_scheduled": False,
                }
            )
            resolved_workloads[resolution_id] = resolved_workload
        row = {
            "repair_execution_resolution_id": resolution_id,
            "repair_execution_candidate_id": candidate.get("repair_execution_candidate_id", ""),
            "panel_row_id": candidate.get("panel_row_id", ""),
            "panel_row_family": candidate.get("panel_row_family", ""),
            "source_milestone": candidate.get("source_milestone", ""),
            "source_row_id": candidate.get("source_row_id", ""),
            "task_family": candidate.get("task_family", ""),
            "task_source_id": candidate.get("task_source_id", ""),
            "workload_id": candidate.get("workload_id", ""),
            "profile_name": REPAIR_PROFILE_NAME,
            "repair_candidate_checkpoint_path": source["repair_candidate_checkpoint"],
            "repair_candidate_profile_config_path": source["repair_profile_config"],
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


def source_prerequisite_failure(source: Mapping[str, Any]) -> str:
    if not _bool(source["m2925_summary"].get("status_pass", False)) or not _bool(
        source["m2925_summary"].get("gate_matrix_pass", False)
    ):
        return "m2925_status_or_gate_not_pass"
    if not _bool(source["m2928_summary"].get("status_pass", False)) or not _bool(
        source["m2928_summary"].get("gate_matrix_pass", False)
    ):
        return "m2928_status_or_gate_not_pass"
    if "accepts M2928" not in source["m2929_audit_text"]:
        return "m2929_does_not_accept_m2928"
    if MILESTONE_ID not in source["m2930_design_text"]:
        return "m2930_design_does_not_admit_m2931"
    if not Path(str(source["repair_candidate_checkpoint"])).exists():
        return "repair_candidate_checkpoint_missing"
    if not Path(str(source["repair_profile_config"])).exists():
        return "repair_profile_config_missing"
    return ""


def candidate_failure_reason(candidate: Mapping[str, Any], workload: Mapping[str, Any] | None) -> str:
    if not str(candidate.get("workload_id", "")):
        return "workload_id_missing"
    if not str(candidate.get("task_source_id", "")):
        return "task_source_id_missing"
    if workload is None:
        return "workload_id_missing_from_m1690_matrix"
    if str(workload.get("task_source_id", "")) != str(candidate.get("task_source_id", "")):
        return "workload_task_source_mismatch"
    if str(workload.get("profile_name", "")) != REPAIR_PROFILE_NAME:
        return "workload_profile_mismatch"
    if int(candidate.get("actor_observation_dim", -1)) != P0_OBSERVATION_DIM:
        return "actor_observation_dim_mismatch"
    if int(candidate.get("actor_action_dim", -1)) != ACTION_DIM:
        return "actor_action_dim_mismatch"
    if any(
        _bool(candidate.get(field, False))
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
    ):
        return "actor_or_protected_denominator_violation"
    return ""


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
        for name in ("repair_execution_rows.csv", "repair_execution_failure_rows.csv", "run_state.json"):
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
        resolution_id = str(resolution.get("repair_execution_resolution_id", ""))
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
            row = execute_repair_candidate_row(
                workload=workload,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(execution_metadata(resolution, eval_seed=eval_seed))
            episode_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every panel row must be accounted.
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
        output_dir / "repair_execution_rows.csv",
        [_normalized_execution_row(row) for row in episode_rows],
        fieldnames=EXECUTION_FIELDNAMES,
    )
    write_csv_rows(output_dir / "repair_execution_failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(resolution_rows) == EXPECTED_TOTAL_ROW_COUNT
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
            "engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight_incomplete_or_fail"
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
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }


def execute_repair_candidate_row(
    *,
    workload: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    profile_row: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    return run_workload_cell(
        workload_row=workload,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=model,
        profile_row=profile_row,
        eval_seed=eval_seed,
    )


def execution_metadata(resolution: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "m2931_eval_seed": int(eval_seed),
        "repair_execution_resolution_id": resolution.get("repair_execution_resolution_id", ""),
        "repair_execution_candidate_id": resolution.get("repair_execution_candidate_id", ""),
        "panel_row_id": resolution.get("panel_row_id", ""),
        "panel_row_family": resolution.get("panel_row_family", ""),
        "source_milestone": resolution.get("source_milestone", ""),
        "source_row_id": resolution.get("source_row_id", ""),
        "offtrack_dominant_single_candidate_repair_execution_preflight": True,
        "candidate_surface_count": EXPECTED_TOTAL_ROW_COUNT,
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
        "repair_overlay_used": False,
        "dependency_execution_performed": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "repair_success_claim_made": False,
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
            "repair_execution_resolution_id": resolution.get("repair_execution_resolution_id", ""),
            "repair_execution_candidate_id": resolution.get("repair_execution_candidate_id", ""),
            "panel_row_id": resolution.get("panel_row_id", ""),
            "panel_row_family": resolution.get("panel_row_family", ""),
            "source_milestone": resolution.get("source_milestone", ""),
            "source_row_id": resolution.get("source_row_id", ""),
            "workload_id": resolution.get("workload_id", ""),
            "task_source_id": resolution.get("task_source_id", ""),
            "profile_name": resolution.get("profile_name", ""),
            "task_family": resolution.get("task_family", ""),
            "m2931_eval_seed": int(eval_seed),
            "error_type": error_type,
            "error_message": error_message,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "repair_execution_rows": read_csv_rows(paths["repair_execution_rows"]),
        "repair_execution_failure_rows": read_csv_rows(paths["repair_execution_failure_rows"]),
    }


def build_repair_target_context_rows(
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    resolution_by_candidate = {str(row["repair_execution_candidate_id"]): row for row in resolution_rows}
    rows = []
    for index, candidate in enumerate(candidate_rows, start=1):
        resolution = resolution_by_candidate.get(str(candidate["repair_execution_candidate_id"]), {})
        rows.append(
            {
                "target_context_id": f"m2931-repair-target-context-{index:04d}",
                "panel_row_id": candidate.get("panel_row_id", ""),
                "panel_row_family": candidate.get("panel_row_family", ""),
                "source_milestone": candidate.get("source_milestone", ""),
                "task_family": candidate.get("task_family", ""),
                "workload_id": candidate.get("workload_id", ""),
                "task_source_id": candidate.get("task_source_id", ""),
                "profile_name": candidate.get("profile_name", ""),
                "checkpoint_context": candidate.get("original_checkpoint_context", ""),
                "env_template_family": candidate.get("env_template_family", ""),
                "window_tag": candidate.get("window_tag", ""),
                "outcome_family": candidate.get("outcome_family", ""),
                "coverage_preserved": True,
                "execution_candidate": True,
                "execution_admitted": _bool(resolution.get("execution_admitted", False)),
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "ranking_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_coverage_constraint_audit_rows(coverage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(coverage_rows, start=1):
        status = (
            _bool(row.get("coverage_constraint_status_pass", False))
            and not _bool(row.get("ranking_claim_made", False))
            and not _bool(row.get("validation_denominator_allowed", False))
            and not _bool(row.get("paper_denominator_allowed", False))
            and not _bool(row.get("high_fidelity_readiness_allowed", False))
            and not _bool(row.get("self_id_claim_allowed", False))
            and not _bool(row.get("actor_visible", False))
        )
        rows.append(
            {
                "coverage_audit_id": f"m2931-coverage-audit-{index:04d}",
                "coverage_constraint_id": row.get("coverage_constraint_id", ""),
                "coverage_family": row.get("coverage_family", ""),
                "coverage_value": row.get("coverage_value", ""),
                "observed_row_count": row.get("observed_row_count", ""),
                "expected_row_count": row.get("expected_row_count", ""),
                "source_scope": row.get("source_scope", ""),
                "coverage_constraint_status_pass": _bool(row.get("coverage_constraint_status_pass", False)),
                "ranking_claim_made": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "m2931_audit_status_pass": status,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2931-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": row.get("row_count", 1),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
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
                "aggregate_id": f"m2931-{aggregate_family}-aggregate-{index:04d}",
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


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
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
        actor_guard("repair_candidate_checkpoint", source["repair_candidate_checkpoint"], str(DEFAULT_REPAIR_CANDIDATE_CHECKPOINT)),
        actor_guard("repair_profile_config", source["repair_profile_config"], str(DEFAULT_REPAIR_PROFILE_CONFIG)),
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
        actor_guard("profile_specific_tuning", any_flag(combined, "profile_specific_tuning"), False),
        actor_guard("active_config_overwritten", any_flag(combined, "active_config_overwritten"), False),
        actor_guard("repair_overlay_used", any_flag(combined, "repair_overlay_used"), False),
        actor_guard("dependency_execution_performed", any_flag(combined, "dependency_execution_performed"), False),
        actor_guard("ranking_run", any_flag(combined, "ranking_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2931-actor-guard-{field}",
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
        ("single_candidate_repair_execution_preflight", "execution", episode_or_failure_rows_present, "diagnostic execution/failure rows"),
        ("repair_execution_candidates_materialized", "artifact", artifacts_present, "repair_execution_candidate_rows.csv"),
        ("repair_execution_resolution_materialized", "artifact", artifacts_present, "repair_execution_resolution_rows.csv"),
        ("repair_execution_rows_materialized", "artifact", artifacts_present, "repair_execution_rows.csv"),
        ("repair_execution_failure_rows_materialized", "artifact", artifacts_present, "repair_execution_failure_rows.csv"),
        ("repair_target_context_materialized", "artifact", artifacts_present, "repair_target_context_rows.csv"),
        ("coverage_constraint_audit_materialized", "artifact", artifacts_present, "coverage_constraint_audit_rows.csv"),
        ("source_aggregate_materialized", "artifact", artifacts_present, "source_milestone_aggregate.csv"),
        ("task_family_aggregate_materialized", "artifact", artifacts_present, "task_family_aggregate.csv"),
        ("guardrail_context_materialized", "artifact", artifacts_present, "guardrail_context_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", episode_rows_present, "diagnostic fields only"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2932 audit manifest"),
    ]
    blocked = [
        ("m2877_guard_execution", "execution", "M2877 rows remain guardrail only"),
        ("route_b_context_execution", "execution", "Route B remains source-family-insufficient context"),
        ("route_c_context_execution", "execution", "Route C remains source_unavailable context"),
        ("replay_validation_training_ppo", "execution", "future manifest"),
        ("dependency_or_external_execution", "execution", "future dependency route"),
        ("source_task_environment_ranking", "ranking", "future audited comparison route"),
        ("checkpoint_or_candidate_ranking", "ranking", "future audited comparison route"),
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
    rows = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2931_{claim_id}",
        "claim_family": family,
        "allowed_in_m2931": allowed,
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
    target_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["repair_execution_rows"]
    failure_rows = artifact_rows["repair_execution_failure_rows"]
    panel_counts = Counter(str(row.get("panel_row_family", "")) for row in candidate_rows)
    offtrack_candidates = [
        row for row in candidate_rows if str(row.get("panel_row_family", "")) == "offtrack_repair_target"
    ]
    source_counts = Counter(str(row.get("source_milestone", "")) for row in offtrack_candidates)
    task_counts = Counter(str(row.get("task_family", "")) for row in offtrack_candidates)
    accounted_ids = {
        str(row.get("repair_execution_candidate_id", ""))
        for row in episode_rows + failure_rows
        if row.get("repair_execution_candidate_id")
    }
    shortcut_families = {str(row.get("shortcut_family", "")) for row in source["m2928_shortcut_exclusion_rows"]}
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2931"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2931"])]
    route_b_context = any("route_b" in str(row.get("guardrail_family", "")).lower() for row in guardrail_rows)
    route_c_context = any("route_c" in str(row.get("guardrail_family", "")).lower() for row in guardrail_rows)
    m2877_context = any("m2877" in str(row.get("guardrail_family", "")).lower() for row in guardrail_rows)
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2925/M2928/M2929/M2930/M1690/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m2929_accepts_m2928",
            "lineage",
            "accepts M2928" in source["m2929_audit_text"],
            "accepts M2928" in source["m2929_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2930_admits_m2931",
            "lineage",
            MILESTONE_ID in source["m2930_design_text"],
            MILESTONE_ID in source["m2930_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2925_status_pass",
            "lineage",
            _bool(source["m2925_summary"].get("status_pass", False))
            and _bool(source["m2925_summary"].get("gate_matrix_pass", False)),
            {"status_pass": source["m2925_summary"].get("status_pass"), "gate_matrix_pass": source["m2925_summary"].get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        (
            "m2928_status_pass",
            "lineage",
            _bool(source["m2928_summary"].get("status_pass", False))
            and _bool(source["m2928_summary"].get("gate_matrix_pass", False)),
            {"status_pass": source["m2928_summary"].get("status_pass"), "gate_matrix_pass": source["m2928_summary"].get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        (
            "panel_row_count",
            "candidate_resolution",
            len(candidate_rows) == EXPECTED_TOTAL_ROW_COUNT,
            len(candidate_rows),
            EXPECTED_TOTAL_ROW_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "panel_family_counts",
            "candidate_resolution",
            panel_counts.get("offtrack_repair_target", 0) == EXPECTED_OFFTRACK_COUNT
            and panel_counts.get("non_offtrack_context_regression", 0) == EXPECTED_NON_OFFTRACK_CONTEXT_COUNT,
            dict(panel_counts),
            {"offtrack": EXPECTED_OFFTRACK_COUNT, "context": EXPECTED_NON_OFFTRACK_CONTEXT_COUNT},
            "scenario_sampling_failure",
        ),
        (
            "source_milestone_distribution",
            "candidate_resolution",
            dict(source_counts) == EXPECTED_SOURCE_MILESTONE_COUNTS,
            dict(source_counts),
            EXPECTED_SOURCE_MILESTONE_COUNTS,
            "scenario_sampling_failure",
        ),
        (
            "task_family_distribution",
            "candidate_resolution",
            dict(task_counts) == EXPECTED_TASK_FAMILY_COUNTS,
            dict(task_counts),
            EXPECTED_TASK_FAMILY_COUNTS,
            "scenario_sampling_failure",
        ),
        (
            "fixed_repair_candidate_paths_exist",
            "lineage",
            Path(str(source["repair_candidate_checkpoint"])).exists() and Path(str(source["repair_profile_config"])).exists(),
            {"checkpoint": Path(str(source["repair_candidate_checkpoint"])).exists(), "profile_config": Path(str(source["repair_profile_config"])).exists()},
            "both true",
            "lineage_invalid",
        ),
        (
            "coverage_constraints_preserved",
            "coverage",
            len(coverage_rows) == EXPECTED_COVERAGE_CONSTRAINT_COUNT
            and all(_bool(row.get("m2931_audit_status_pass", False)) for row in coverage_rows),
            {"rows": len(coverage_rows), "pass": sum(_bool(row.get("m2931_audit_status_pass", False)) for row in coverage_rows)},
            EXPECTED_COVERAGE_CONSTRAINT_COUNT,
            "proof_washout",
        ),
        (
            "shortcut_exclusion_families_preserved",
            "shortcut",
            len(source["m2928_shortcut_exclusion_rows"]) == EXPECTED_SHORTCUT_EXCLUSION_COUNT
            and REQUIRED_SHORTCUT_FAMILIES.issubset(shortcut_families)
            and all(_bool(row.get("status_pass", False)) for row in source["m2928_shortcut_exclusion_rows"]),
            {"rows": len(source["m2928_shortcut_exclusion_rows"]), "families": sorted(shortcut_families)},
            sorted(REQUIRED_SHORTCUT_FAMILIES),
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
            "diagnostic_execution_rows_present",
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
            "target_context_rows_account_panel",
            "coverage",
            len(target_rows) == len(candidate_rows),
            len(target_rows),
            len(candidate_rows),
            "metric_artifact",
        ),
        (
            "guardrails_preserved_not_executed",
            "guardrail",
            m2877_context
            and route_b_context
            and route_c_context
            and not any_flag(guardrail_rows, "execution_run")
            and not any_flag(episode_rows + failure_rows, "m2877_guard_execution")
            and not any_flag(episode_rows + failure_rows, "route_b_context_execution")
            and not any_flag(episode_rows + failure_rows, "route_c_context_execution"),
            {"m2877": m2877_context, "route_b": route_b_context, "route_c": route_c_context},
            "all present and execution false",
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
            "no validation/training/replay/PPO/ranking/promotion/overclaim flags",
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
        "gate_id": f"m2931_{gate_id}",
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
    target_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
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
    episode_rows = artifact_rows["repair_execution_rows"]
    failure_rows = artifact_rows["repair_execution_failure_rows"]
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    panel_counts = Counter(str(row.get("panel_row_family", "")) for row in candidate_rows)
    offtrack_candidates = [
        row for row in candidate_rows if str(row.get("panel_row_family", "")) == "offtrack_repair_target"
    ]
    source_counts = Counter(str(row.get("source_milestone", "")) for row in offtrack_candidates)
    task_counts = Counter(str(row.get("task_family", "")) for row in offtrack_candidates)
    panel_source_counts = Counter(str(row.get("source_milestone", "")) for row in candidate_rows)
    panel_task_counts = Counter(str(row.get("task_family", "")) for row in candidate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight_fail"
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
        "m2925_status_pass": _bool(source["m2925_summary"].get("status_pass", False)),
        "m2925_gate_matrix_pass": _bool(source["m2925_summary"].get("gate_matrix_pass", False)),
        "m2928_status_pass": _bool(source["m2928_summary"].get("status_pass", False)),
        "m2928_gate_matrix_pass": _bool(source["m2928_summary"].get("gate_matrix_pass", False)),
        "candidate_count": len(candidate_rows),
        "expected_candidate_count": EXPECTED_TOTAL_ROW_COUNT,
        "offtrack_candidate_count": panel_counts.get("offtrack_repair_target", 0),
        "non_offtrack_context_candidate_count": panel_counts.get("non_offtrack_context_regression", 0),
        "source_milestone_counts": dict(source_counts),
        "task_family_counts": dict(task_counts),
        "panel_source_milestone_counts": dict(panel_source_counts),
        "panel_task_family_counts": dict(panel_task_counts),
        "resolved_candidate_count": sum(_bool(row.get("execution_admitted", False)) for row in resolution_rows),
        "repair_execution_row_count": len(episode_rows),
        "repair_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": len(
            {
                str(row.get("repair_execution_candidate_id", ""))
                for row in episode_rows + failure_rows
                if row.get("repair_execution_candidate_id")
            }
        ),
        "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in episode_rows),
        "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in episode_rows),
        "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
        "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "repair_target_context_row_count": len(target_rows),
        "coverage_constraint_audit_row_count": len(coverage_rows),
        "coverage_constraint_rows_pass": all(_bool(row.get("m2931_audit_status_pass", False)) for row in coverage_rows),
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
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "repair_overlay_used": False,
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
        "repair_candidate_checkpoint": source["repair_candidate_checkpoint"],
        "repair_profile_config": source["repair_profile_config"],
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2931 Engineering Controller Route A Offtrack-Dominant Single-Candidate Repair Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rows: {summary['candidate_count']}",
            f"- offtrack/context rows: {summary['offtrack_candidate_count']}/{summary['non_offtrack_context_candidate_count']}",
            f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['candidate_count']}",
            f"- repair execution rows: {summary['repair_execution_row_count']}",
            f"- failure rows: {summary['repair_execution_failure_row_count']}",
            f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
            f"- source split: {summary['source_milestone_counts']}",
            f"- task split: {summary['task_family_counts']}",
            f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
            f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
            f"- fixed checkpoint: `{summary['repair_candidate_checkpoint']}`",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2931 records bounded closed-loop diagnostic data only for the fixed M2655 repair candidate over the M2925 panel. M2877, Route B, and Route C rows remain guardrails. The rows are not validation, ranking, or repair-success evidence.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2931 single-candidate repair execution preflight before any validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                str(DEFAULT_REPAIR_CANDIDATE_CHECKPOINT),
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "repair_execution_candidate_rows.csv"),
                str(output_dir / "repair_execution_resolution_rows.csv"),
                str(output_dir / "repair_execution_rows.csv"),
                str(output_dir / "repair_execution_failure_rows.csv"),
                str(output_dir / "repair_target_context_rows.csv"),
                str(output_dir / "coverage_constraint_audit_rows.csv"),
                str(output_dir / "source_milestone_aggregate.csv"),
                str(output_dir / "task_family_aggregate.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2930-engineering-controller-route-a-offtrack-dominant-repair-execution-design.md",
                "docs/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight.json",
                "experiments/manifests/m2930-engineering-controller-route-a-offtrack-dominant-repair-execution-design.json",
            ],
            "parent_objective": ["audit M2931 repair diagnostic execution artifacts before any interpretation"],
            "derived_from": [
                MILESTONE_ID,
                "m2930-engineering-controller-route-a-offtrack-dominant-repair-execution-design",
                "m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit",
            ],
            "blocked_by": [
                "M2931 diagnostics require a result audit before any verdict or continuation decision",
                "M2928 coverage constraints and shortcut exclusions must remain protected",
            ],
            "supersedes": ["direct interpretation of M2931 diagnostic rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2932 must audit M2931 summary gate matrix actor and claim boundaries",
            "M2932 must preserve M2928 coverage constraints shortcut exclusions and M2877 Route B Route C guardrails",
            "M2932 must not claim validation repair-success performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2932 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert M2931 diagnostic rows into repair-success performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_single_candidate_repair_execution_result_audit",
            "evidence_increment": "audits bounded diagnostic repair execution artifacts from M2931",
            "claim_scope": "Result audit only; no validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2931 artifacts are missing or gate matrix fails",
                "stop if actor coverage shortcut guardrail or claim boundaries were violated",
                "stop if M2931 diagnostic rows cannot be interpreted without overclaiming",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if diagnostics are complete but negative or insufficient",
                "route to a new bounded evidence surface only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2931 completes bounded single-candidate repair execution preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2931 bounded single-candidate repair execution artifacts",
            "admission_evidence": [
                "M2931 summary and gate matrix",
                "M2931 repair execution candidate resolution execution failure aggregate coverage guard actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion repair-success performance verdict paper high-fidelity full ideal driver or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2932 status queue scoreboard research log and review",
                "one follow-up manifest only if M2932 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2932 audit accepts or rejects M2931 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2932 audits Route A engineering diagnostics and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2932; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2931 Route A offtrack-dominant repair diagnostic execution only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2931 artifact completeness and claim-safety audit",
                "no repair-success driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly generated Route A offtrack-dominant repair diagnostics",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2932 cannot accept M2931 as complete and claim-safe",
                "M2932 would claim validation readiness repair success driver performance paper current-sim high-fidelity or self-ID",
                "M2932 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2932 audits M2931 artifacts row counts gates actor and claim boundaries",
            "M2932 selects exactly one next route or stop state",
            "no validation ranking promotion repair-success performance paper high-fidelity or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2932 hides M2931 failures or missing artifacts",
            "M2932 treats M2931 diagnostics as validation readiness repair success or performance verdict",
            "M2932 changes actor input or action contract",
            "M2932 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2932 audits M2931 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            str(DEFAULT_REPAIR_CANDIDATE_CHECKPOINT),
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "repair_execution_rows.csv"),
            str(output_dir / "repair_execution_failure_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _normalized_execution_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in EXECUTION_FIELDNAMES}


def checkpoint_context(row: Mapping[str, Any]) -> str:
    path = str(row.get("checkpoint_path", ""))
    if "m2655" in path:
        return "m2655_mitigation_preserving_checkpoint"
    if "m1674" in path or "profile_runs/L3_online_gru" in path:
        return "public_pilot_l3_checkpoint"
    if not path:
        return ""
    return Path(path).name


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "measured_validation_run",
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
            "repair_overlay_used",
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
            "repair_success_claim_made",
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
    parser.add_argument("--m2925-dir", type=Path, default=DEFAULT_M2925_DIR)
    parser.add_argument("--m2928-dir", type=Path, default=DEFAULT_M2928_DIR)
    parser.add_argument("--m2919-dir", type=Path, default=DEFAULT_M2919_DIR)
    parser.add_argument("--m2929-audit", type=Path, default=DEFAULT_M2929_AUDIT)
    parser.add_argument("--m2930-design", type=Path, default=DEFAULT_M2930_DESIGN)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--repair-candidate-checkpoint", type=Path, default=DEFAULT_REPAIR_CANDIDATE_CHECKPOINT)
    parser.add_argument("--repair-profile-config", type=Path, default=DEFAULT_REPAIR_PROFILE_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_offtrack_dominant_repair_execution_preflight(
        m2925_dir=args.m2925_dir,
        m2928_dir=args.m2928_dir,
        m2919_dir=args.m2919_dir,
        m2929_audit=args.m2929_audit,
        m2930_design=args.m2930_design,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        repair_candidate_checkpoint=args.repair_candidate_checkpoint,
        repair_profile_config=args.repair_profile_config,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"repair_execution_rows={summary['repair_execution_row_count']}")
    print(f"failure_rows={summary['repair_execution_failure_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
