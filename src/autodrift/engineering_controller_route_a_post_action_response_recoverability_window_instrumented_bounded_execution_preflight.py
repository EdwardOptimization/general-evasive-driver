"""Run M2816 recoverability-window instrumented bounded execution preflight.

M2816 consumes the fixed M2813 action-response mechanism rows and reruns the
resolved M2807 workload cells with soft offtrack metric instrumentation. The
run is evaluation-only and diagnostic-only: it does not train, repair, rank,
promote, validate, or claim driver performance.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    load_executable_specs,
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy, run_episode_with_policy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2816-engineering-controller-route-a-post-action-response-recoverability-window-"
    "instrumented-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2817-engineering-controller-route-a-post-action-response-recoverability-window-"
    "instrumented-bounded-execution-result-audit"
)
DEFAULT_M2815_SYNTHESIS = Path(
    "docs/m2815-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-action-response-mechanism-branch-synthesis.md"
)
DEFAULT_M2813_DIR = Path(
    "runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "offtrack_containment_action_response_mechanism_panel"
)
DEFAULT_M2807_DIR = Path(
    "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "cross_axis_bounded_execution_preflight"
)
DEFAULT_M2810_DIR = Path(
    "runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "offtrack_containment_localization_panel"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_"
    "preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_"
    "instrumented_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2816-engineering-controller-route-a-post-action-response-recoverability-window-"
    "instrumented-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2817-engineering-controller-route-a-post-action-response-"
    "recoverability-window-instrumented-bounded-execution-result-audit.json"
)
DEFAULT_SEED_START_INDEX = 281600
DEFAULT_HORIZON_STEPS = 180
DEFAULT_RECOVERABILITY_WINDOW_STEPS = 40
DEFAULT_SOFT_OFFTRACK_TOLERANCE_M = 1.0
EXPECTED_MECHANISM_ROWS = 12
EXPECTED_SOURCE_OFFTRACK_ROWS = 10
EXPECTED_SOURCE_SUCCESS_ROWS = 2
EXPECTED_GUARDRAIL_ROWS = 44

CLAIM_SCOPE = (
    "M2816 Route A post-action-response recoverability-window instrumented bounded "
    "execution preflight only; fixed M2813/M2807 rows may be rerun with evaluator-only "
    "soft-offtrack metric instrumentation to materialize recoverability-window and "
    "post-offtrack action-response diagnostics. No replay, validation, training, PPO, "
    "repair, source build, adapter probe, external simulation, ranking, winner selection, "
    "promotion, success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller "
    "ranking, action-response ranking, recoverability ranking, source-family ranking, "
    "task-family ranking, stress-axis ranking, profile ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-sim verdict, high-fidelity validation readiness or result, "
    "full ideal driver completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "repair_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "external_simulation_run": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
    "active_config_overwritten": False,
    "ranking_run": False,
    "recoverability_ranking_run": False,
    "action_response_ranking_run": False,
    "stress_axis_ranking_run": False,
    "source_edge_ranking_run": False,
    "task_family_ranking_run": False,
    "profile_ranking_run": False,
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
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_completion_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
}

RECOVERABILITY_FIELDNAMES = [
    "recoverability_id",
    "mechanism_id",
    "localization_id",
    "candidate_id",
    "resolution_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "stress_axis_tags",
    "source_outcome_family",
    "outcome_family",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "steps",
    "return",
    "min_clearance_margin",
    "speed_mean",
    "action_rate_mean",
    "previous_command_norm_mean",
    "current_action_norm_mean",
    "action_trace_delta_mean",
    "time_to_first_off_track_s",
    "max_off_track_overshoot",
    "off_track_severity_proxy",
    "post_event_speed_mps",
    "post_event_speed_mps_available",
    "post_event_yaw_rate_abs",
    "post_event_yaw_rate_abs_available",
    "post_event_offtrack_overshoot",
    "post_event_offtrack_overshoot_available",
    "recoverability_window_success",
    "recoverability_window_success_available",
    "recoverability_window_steps",
    "m2816_eval_seed",
    "horizon_steps",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "bounded_execution_admitted",
    "execution_failure",
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
    "actor_visible_allowed",
    "claim_scope",
]
POST_ACTION_RESPONSE_FIELDNAMES = [
    "post_action_response_id",
    "mechanism_id",
    "candidate_id",
    "resolution_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "source_outcome_family",
    "outcome_family",
    "metric_context_available",
    "previous_command_norm_mean",
    "previous_command_norm_peak",
    "current_action_norm_mean",
    "current_action_norm_peak",
    "action_trace_delta_mean",
    "action_trace_delta_peak",
    "action_rate_mean",
    "speed_mean",
    "time_to_first_off_track_s",
    "post_event_speed_mps",
    "post_event_speed_mps_available",
    "post_event_yaw_rate_abs",
    "post_event_yaw_rate_abs_available",
    "post_event_offtrack_overshoot",
    "post_event_offtrack_overshoot_available",
    "recoverability_window_success",
    "recoverability_window_success_available",
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
    "actor_visible_allowed",
    "claim_scope",
]
CONTRAST_FIELDNAMES = [
    "contrast_id",
    "source_outcome_family",
    "row_count",
    "episode_count",
    "failure_count",
    "success_count_diagnostic",
    "collision_count_diagnostic",
    "offtrack_termination_count_diagnostic",
    "post_event_available_count",
    "recoverability_available_count",
    "recoverability_success_count",
    "min_clearance_margin_mean",
    "speed_mean",
    "action_rate_mean",
    "previous_command_norm_mean",
    "current_action_norm_mean",
    "action_trace_delta_mean",
    "ranking_claim_made",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
GUARDRAIL_FIELDNAMES = [
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
    "allowed_in_m2816",
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
FAILURE_FIELDNAMES = [
    "failure_id",
    "mechanism_id",
    "candidate_id",
    "resolution_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "m2816_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "repair_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "recoverability_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
REQUIRED_ARTIFACT_KEYS = [
    "recoverability_window_rows",
    "post_offtrack_action_response_rows",
    "success_offtrack_contrast_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "instrumented_execution_rows",
    "instrumented_execution_failure_rows",
    "run_state",
    "doc",
]


def run_post_action_response_recoverability_window_instrumented_bounded_execution_preflight(
    *,
    m2815_synthesis: Path | str = DEFAULT_M2815_SYNTHESIS,
    m2813_dir: Path | str = DEFAULT_M2813_DIR,
    m2807_dir: Path | str = DEFAULT_M2807_DIR,
    m2810_dir: Path | str = DEFAULT_M2810_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    route_plan: Path | str = DEFAULT_ROUTE_PLAN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    device: str = "cpu",
    seed_start_index: int = DEFAULT_SEED_START_INDEX,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    recoverability_window_steps: int = DEFAULT_RECOVERABILITY_WINDOW_STEPS,
    soft_offtrack_tolerance_m: float = DEFAULT_SOFT_OFFTRACK_TOLERANCE_M,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2815_synthesis=Path(m2815_synthesis),
        m2813_dir=Path(m2813_dir),
        m2807_dir=Path(m2807_dir),
        m2810_dir=Path(m2810_dir),
        source_checkpoint=Path(source_checkpoint),
        executable_specs=Path(executable_specs),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )
    mechanism_rows = build_fixed_mechanism_rows(source)
    guardrail_rows = build_guardrail_context_rows(source)

    execution_rows, failure_rows, execution_summary = run_recoverability_panel_execution(
        mechanism_rows=mechanism_rows,
        source=source,
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        device=device,
        seed_start_index=int(seed_start_index),
        horizon_steps=int(horizon_steps),
        recoverability_window_steps=int(recoverability_window_steps),
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        next_blocker=next_blocker,
    )
    write_csv_rows(paths["instrumented_execution_rows"], execution_rows)
    write_csv_rows(paths["instrumented_execution_failure_rows"], failure_rows, fieldnames=FAILURE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "fixed_mechanism_row_count": len(mechanism_rows),
            "completed_execution_count": len(execution_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(execution_rows) + len(failure_rows),
            "complete": len(execution_rows) + len(failure_rows) == len(mechanism_rows),
            "status_pass": bool(execution_summary.get("status_pass")),
            "next_blocker": next_blocker,
        },
    )

    recoverability_rows = build_recoverability_window_rows(
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        recoverability_window_steps=int(recoverability_window_steps),
        horizon_steps=int(horizon_steps),
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
    )
    post_rows = build_post_offtrack_action_response_rows(mechanism_rows=mechanism_rows, execution_rows=execution_rows)
    contrast_rows = build_success_offtrack_contrast_rows(
        mechanism_rows=mechanism_rows, execution_rows=execution_rows, failure_rows=failure_rows
    )
    actor_rows = build_actor_contract_guard_rows(
        source=source,
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        guardrail_rows=guardrail_rows,
    )
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        execution_rows_present=bool(execution_rows or failure_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        recoverability_rows=recoverability_rows,
        post_rows=post_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_outputs(paths, recoverability_rows, post_rows, contrast_rows, guardrail_rows, actor_rows, claim_rows, gate_rows)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key != "doc")
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        execution_rows_present=bool(execution_rows or failure_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        recoverability_rows=recoverability_rows,
        post_rows=post_rows,
        contrast_rows=contrast_rows,
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
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        execution_summary=execution_summary,
        recoverability_rows=recoverability_rows,
        post_rows=post_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        seed_start_index=int(seed_start_index),
        horizon_steps=int(horizon_steps),
        recoverability_window_steps=int(recoverability_window_steps),
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        recoverability_rows=recoverability_rows,
        post_rows=post_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        mechanism_rows=mechanism_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        execution_summary=execution_summary,
        recoverability_rows=recoverability_rows,
        post_rows=post_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        seed_start_index=int(seed_start_index),
        horizon_steps=int(horizon_steps),
        recoverability_window_steps=int(recoverability_window_steps),
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "recoverability_window_rows": output_dir / "recoverability_window_rows.csv",
        "post_offtrack_action_response_rows": output_dir / "post_offtrack_action_response_rows.csv",
        "success_offtrack_contrast_rows": output_dir / "success_offtrack_contrast_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "instrumented_execution_rows": output_dir / "instrumented_execution_rows.csv",
        "instrumented_execution_failure_rows": output_dir / "instrumented_execution_failure_rows.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2815_synthesis: Path,
    m2813_dir: Path,
    m2807_dir: Path,
    m2810_dir: Path,
    source_checkpoint: Path,
    executable_specs: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2815_synthesis": m2815_synthesis,
        "m2813_summary": m2813_dir / "summary.json",
        "m2813_action_response_mechanism_rows": m2813_dir / "action_response_mechanism_rows.csv",
        "m2813_success_offtrack_contrast_rows": m2813_dir / "success_offtrack_contrast_rows.csv",
        "m2813_guardrail_context_rows": m2813_dir / "guardrail_context_rows.csv",
        "m2813_actor_contract_guard_rows": m2813_dir / "actor_contract_guard_rows.csv",
        "m2813_claim_boundary_rows": m2813_dir / "claim_boundary_rows.csv",
        "m2813_gate_matrix": m2813_dir / "gate_matrix.csv",
        "m2807_candidate_execution_rows": m2807_dir / "candidate_execution_rows.csv",
        "m2807_candidate_execution_failure_rows": m2807_dir / "candidate_execution_failure_rows.csv",
        "m2807_execution_candidate_resolution_rows": m2807_dir / "execution_candidate_resolution_rows.csv",
        "m2807_gate_matrix": m2807_dir / "gate_matrix.csv",
        "m2810_summary": m2810_dir / "summary.json",
        "m2810_failure_localization_rows": m2810_dir / "failure_localization_rows.csv",
        "m2810_guardrail_context_rows": m2810_dir / "guardrail_context_rows.csv",
        "m2810_actor_contract_guard_rows": m2810_dir / "actor_contract_guard_rows.csv",
        "m2810_gate_matrix": m2810_dir / "gate_matrix.csv",
        "source_checkpoint": source_checkpoint,
        "executable_task_specs": executable_specs,
        "route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2815_synthesis_text": paths["m2815_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2815_synthesis"]
        else "",
        "route_plan_text": paths["route_plan"].read_text(encoding="utf-8") if source_exists["route_plan"] else "",
        "m2813_summary": read_json(paths["m2813_summary"]) if source_exists["m2813_summary"] else {},
        "m2813_action_response_mechanism_rows": read_csv_rows(paths["m2813_action_response_mechanism_rows"]),
        "m2813_success_offtrack_contrast_rows": read_csv_rows(paths["m2813_success_offtrack_contrast_rows"]),
        "m2813_guardrail_context_rows": read_csv_rows(paths["m2813_guardrail_context_rows"]),
        "m2813_actor_contract_guard_rows": read_csv_rows(paths["m2813_actor_contract_guard_rows"]),
        "m2813_claim_boundary_rows": read_csv_rows(paths["m2813_claim_boundary_rows"]),
        "m2813_gate_matrix": read_csv_rows(paths["m2813_gate_matrix"]),
        "m2807_candidate_execution_rows": read_csv_rows(paths["m2807_candidate_execution_rows"]),
        "m2807_candidate_execution_failure_rows": read_csv_rows(paths["m2807_candidate_execution_failure_rows"]),
        "m2807_execution_candidate_resolution_rows": read_csv_rows(paths["m2807_execution_candidate_resolution_rows"]),
        "m2807_gate_matrix": read_csv_rows(paths["m2807_gate_matrix"]),
        "m2810_summary": read_json(paths["m2810_summary"]) if source_exists["m2810_summary"] else {},
        "m2810_failure_localization_rows": read_csv_rows(paths["m2810_failure_localization_rows"]),
        "m2810_guardrail_context_rows": read_csv_rows(paths["m2810_guardrail_context_rows"]),
        "m2810_actor_contract_guard_rows": read_csv_rows(paths["m2810_actor_contract_guard_rows"]),
        "m2810_gate_matrix": read_csv_rows(paths["m2810_gate_matrix"]),
    }


def build_fixed_mechanism_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2807_by_candidate = {
        str(row.get("candidate_id", "")): row for row in source["m2807_candidate_execution_rows"]
    }
    localization_by_id = {
        str(row.get("localization_id", "")): row for row in source["m2810_failure_localization_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, mechanism in enumerate(source["m2813_action_response_mechanism_rows"], start=1):
        candidate_id = str(mechanism.get("candidate_id", ""))
        localization_id = str(mechanism.get("localization_id", ""))
        m2807_row = m2807_by_candidate.get(candidate_id, {})
        localization_row = localization_by_id.get(localization_id, {})
        row = dict(mechanism)
        row.update(
            {
                "m2816_fixed_row_id": f"m2816-fixed-mechanism-row-{index:04d}",
                "workload_id": m2807_row.get("workload_id", localization_row.get("workload_id", "")),
                "profile_name": m2807_row.get("profile_name", localization_row.get("profile_name", "")),
                "window_tag": m2807_row.get("window_tag", ""),
                "strata": m2807_row.get("strata", ""),
                "executable_source_family": m2807_row.get("executable_source_family", ""),
                "env_template_family": m2807_row.get("env_template_family", ""),
                "profile_config_path": m2807_row.get("profile_config_path", ""),
                "checkpoint_path": m2807_row.get("checkpoint_path", ""),
                "source_eval_seed": m2807_row.get("eval_seed", ""),
                "source_m2807_outcome_bucket": m2807_row.get("outcome_bucket", ""),
                "source_m2807_termination_reason": m2807_row.get("termination_reason", ""),
                "source_m2807_row_present": bool(m2807_row),
                "source_m2810_row_present": bool(localization_row),
                "bounded_execution_admitted": bool(m2807_row),
                "claim_scope": CLAIM_SCOPE,
            }
        )
        rows.append(row)
    return rows


def build_guardrail_context_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m2813_guardrail_context_rows"], start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2816-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_source_id": row.get("guardrail_source_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "route": row.get("route", ""),
                "evidence_family": row.get("evidence_family", ""),
                "row_count": _int(row.get("row_count")),
                "blocking_count": _int(row.get("blocking_count")),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": row.get("guardrail_role", ""),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def run_recoverability_panel_execution(
    *,
    mechanism_rows: list[dict[str, Any]],
    source: dict[str, Any],
    output_dir: Path,
    executable_specs_path: Path,
    device: str,
    seed_start_index: int,
    horizon_steps: int,
    recoverability_window_steps: int,
    soft_offtrack_tolerance_m: float,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    episode_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for index, mechanism in enumerate(mechanism_rows):
        eval_seed = int(seed_start_index) + index
        try:
            if not _bool(mechanism.get("bounded_execution_admitted")):
                raise ValueError("mechanism row did not resolve to M2807 execution row")
            task_source_id = str(mechanism["task_source_id"])
            if task_source_id not in spec_by_id:
                raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
            config_path = str(mechanism.get("profile_config_path", ""))
            checkpoint_path = str(mechanism.get("checkpoint_path", ""))
            profile_name = str(mechanism.get("profile_name", ""))
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
            row = run_recoverability_workload_cell(
                workload_row=mechanism,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
                horizon_steps=horizon_steps,
                soft_offtrack_tolerance_m=soft_offtrack_tolerance_m,
            )
            row.update(execution_metadata(mechanism, eval_seed=eval_seed, recoverability_window_steps=recoverability_window_steps))
            episode_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every fixed row must be accounted.
            failure_rows.append(
                failure_row(
                    mechanism,
                    index=len(failure_rows) + 1,
                    eval_seed=eval_seed,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "fixed_mechanism_row_count": len(mechanism_rows),
                "completed_execution_count": len(episode_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(episode_rows) + len(failure_rows),
                "latest_mechanism_id": mechanism.get("mechanism_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(mechanism_rows) == EXPECTED_MECHANISM_ROWS
        and len(episode_rows) + len(failure_rows) == len(mechanism_rows)
        and len(failure_rows) == 0
        and bool(episode_rows)
        and all_metrics_finite
        and not any_forbidden_flag(episode_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_post_action_response_recoverability_window_execution_pass"
            if status_pass
            else "engineering_controller_route_a_post_action_response_recoverability_window_execution_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "fixed_mechanism_row_count": len(mechanism_rows),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "accounted_count": len(episode_rows) + len(failure_rows),
        "all_selected_metrics_finite": all_metrics_finite,
        "horizon_steps": int(horizon_steps),
        "recoverability_window_steps": int(recoverability_window_steps),
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
        "status_pass": status_pass,
        "next_blocker": next_blocker,
    }
    write_run_state(
        output_dir / "run_state.json",
        {
            "fixed_mechanism_row_count": len(mechanism_rows),
            "completed_execution_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(episode_rows) + len(failure_rows),
            "complete": len(episode_rows) + len(failure_rows) == len(mechanism_rows),
            "status_pass": status_pass,
            "next_blocker": next_blocker,
        },
    )
    return episode_rows, failure_rows, summary


def run_recoverability_workload_cell(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    profile_row: Mapping[str, Any],
    eval_seed: int,
    horizon_steps: int,
    soft_offtrack_tolerance_m: float,
) -> dict[str, Any]:
    env_config = env_config_for_recoverability_profile(
        executable_spec=executable_spec,
        profile_config=profile_config,
        horizon_steps=horizon_steps,
        soft_offtrack_tolerance_m=soft_offtrack_tolerance_m,
    )
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    target_obs_dim = int(env.observation_space.shape[0])
    model_obs_dim = int(getattr(model, "obs_dim", -1))
    if model_obs_dim != target_obs_dim:
        env.close()
        raise ValueError(
            f"profile {workload_row.get('profile_name', '')} checkpoint obs_dim {model_obs_dim} "
            f"does not match task env obs_dim {target_obs_dim}"
        )
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    try:
        row = run_episode_with_policy(env, policy, "checkpoint", int(eval_seed))
    finally:
        env.close()

    row.update(
        {
            "workload_id": str(workload_row.get("workload_id", "")),
            "task_source_id": str(workload_row.get("task_source_id", "")),
            "profile_name": str(workload_row.get("profile_name", "")),
            "task_family": str(workload_row.get("task_family", "")),
            "source_edge": str(workload_row.get("source_edge", "")),
            "window_tag": str(workload_row.get("window_tag", "")),
            "strata": str(workload_row.get("strata", "")),
            "executable_source_family": str(workload_row.get("executable_source_family", "")),
            "env_template_family": str(workload_row.get("env_template_family", "")),
            "profile_config_path": str(profile_row["config_path"]),
            "checkpoint_path": str(profile_row["checkpoint_path"]),
            "profile_env_history_length": int(env_config.history_length),
            "eval_seed": int(eval_seed),
            "routing_smoke_only": False,
            "full_rollout_execution": True,
            "recoverability_window_instrumented_execution": True,
            "private_holdout_used": False,
            "promoted": False,
            "training_started": False,
            "training_run": False,
            "replay_started": False,
            "replay_run": False,
            "ppo_used": False,
            "ppo_run": False,
            "repair_run": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "success": bool(row.get("obstacle_completed", False)) and not bool(row.get("collision", False)),
            "horizon_steps": int(horizon_steps),
            "soft_offtrack_metric_enabled": True,
            "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
        }
    )
    return row


def env_config_for_recoverability_profile(
    *,
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    horizon_steps: int,
    soft_offtrack_tolerance_m: float,
) -> DriftEnvConfig:
    env_data = dict(executable_spec["env_config"])
    profile_env = dict(profile_config.get("env") or {})
    env_data["history_length"] = int(profile_env.get("history_length", env_data["history_length"]))
    env_data["action_history_mode"] = "full"
    env_data["include_privileged_params"] = False
    env_data["obstacle_relative_velocity_mode"] = "zero"
    env_data["wheel_observation_mode"] = "none"
    env_data["max_steps"] = int(horizon_steps)
    env_data["soft_offtrack_metric_enabled"] = True
    env_data["soft_offtrack_tolerance_m"] = float(soft_offtrack_tolerance_m)
    env_config = build_env_config(env_data)
    assert_human_view_env_contract(env_config)
    return env_config


def execution_metadata(
    mechanism: Mapping[str, Any], *, eval_seed: int, recoverability_window_steps: int
) -> dict[str, Any]:
    return {
        "m2816_eval_seed": int(eval_seed),
        "mechanism_id": mechanism.get("mechanism_id", ""),
        "localization_id": mechanism.get("localization_id", ""),
        "candidate_id": mechanism.get("candidate_id", ""),
        "resolution_id": mechanism.get("resolution_id", ""),
        "source_outcome_family": mechanism.get("outcome_family", ""),
        "source_m2807_outcome_bucket": mechanism.get("source_m2807_outcome_bucket", ""),
        "source_m2807_termination_reason": mechanism.get("source_m2807_termination_reason", ""),
        "bounded_post_action_response_recoverability_window_execution_preflight": True,
        "recoverability_window_steps": int(recoverability_window_steps),
        "prior_surface_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
        "protected_rows_in_success_denominator": False,
        "hidden_oracle_actor_input_required": False,
        "recoverability_labels_actor_visible": False,
        "action_response_labels_actor_visible": False,
        "stress_axis_labels_actor_visible": False,
        "source_edge_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        **FALSE_CLAIM_FLAGS,
        "diagnostic_only_no_verdict": True,
        "claim_scope": CLAIM_SCOPE,
        "claim_boundary": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def failure_row(
    mechanism: Mapping[str, Any], *, index: int, eval_seed: int, error_type: str, error_message: str
) -> dict[str, Any]:
    return {
        "failure_id": f"m2816-execution-failure-{index:04d}",
        "mechanism_id": mechanism.get("mechanism_id", ""),
        "candidate_id": mechanism.get("candidate_id", ""),
        "resolution_id": mechanism.get("resolution_id", ""),
        "task_source_id": mechanism.get("task_source_id", ""),
        "workload_id": mechanism.get("workload_id", ""),
        "profile_name": mechanism.get("profile_name", ""),
        "m2816_eval_seed": int(eval_seed),
        "error_type": error_type,
        "error_message": error_message,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "repair_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "recoverability_labels_actor_visible": False,
        "diagnostic_only_no_verdict": True,
        "claim_scope": CLAIM_SCOPE,
    }


def build_recoverability_window_rows(
    *,
    mechanism_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    recoverability_window_steps: int,
    horizon_steps: int,
    soft_offtrack_tolerance_m: float,
) -> list[dict[str, Any]]:
    execution_by_mechanism = {str(row.get("mechanism_id", "")): row for row in execution_rows}
    failure_by_mechanism = {str(row.get("mechanism_id", "")): row for row in failure_rows}
    rows: list[dict[str, Any]] = []
    for index, mechanism in enumerate(mechanism_rows, start=1):
        mechanism_id = str(mechanism.get("mechanism_id", ""))
        execution = execution_by_mechanism.get(mechanism_id, {})
        failure = failure_by_mechanism.get(mechanism_id, {})
        row = {
            "recoverability_id": f"m2816-recoverability-window-{index:04d}",
            "mechanism_id": mechanism_id,
            "localization_id": mechanism.get("localization_id", ""),
            "candidate_id": mechanism.get("candidate_id", ""),
            "resolution_id": mechanism.get("resolution_id", ""),
            "task_source_id": mechanism.get("task_source_id", ""),
            "workload_id": mechanism.get("workload_id", ""),
            "profile_name": mechanism.get("profile_name", ""),
            "task_family": mechanism.get("task_family", ""),
            "source_edge": mechanism.get("source_edge", ""),
            "stress_axis_primary": mechanism.get("stress_axis_primary", ""),
            "stress_axis_tags": mechanism.get("stress_axis_tags", ""),
            "source_outcome_family": mechanism.get("outcome_family", ""),
            "outcome_family": diagnostic_outcome_family(execution),
            "success": _bool(execution.get("success")),
            "collision": _bool(execution.get("collision")),
            "obstacle_completed": _bool(execution.get("obstacle_completed")),
            "termination_reason": execution.get("termination_reason", ""),
            "outcome_bucket": execution.get("outcome_bucket", ""),
            "steps": _int(execution.get("steps")),
            "return": _float_or_blank(execution.get("return")),
            "min_clearance_margin": _float_or_blank(execution.get("min_clearance_margin")),
            "speed_mean": _float_or_blank(execution.get("speed_mean")),
            "action_rate_mean": _float_or_blank(execution.get("action_rate_mean")),
            "previous_command_norm_mean": _float_or_blank(execution.get("previous_command_norm_mean")),
            "current_action_norm_mean": _float_or_blank(execution.get("current_action_norm_mean")),
            "action_trace_delta_mean": _float_or_blank(execution.get("action_trace_delta_mean")),
            "time_to_first_off_track_s": _float_or_blank(execution.get("time_to_first_off_track_s")),
            "max_off_track_overshoot": _float_or_blank(execution.get("max_off_track_overshoot")),
            "off_track_severity_proxy": _float_or_blank(execution.get("off_track_severity_proxy")),
            "post_event_speed_mps": _float_or_blank(execution.get("post_event_speed_mps")),
            "post_event_speed_mps_available": _bool(execution.get("post_event_speed_mps_available")),
            "post_event_yaw_rate_abs": _float_or_blank(execution.get("post_event_yaw_rate_abs")),
            "post_event_yaw_rate_abs_available": _bool(execution.get("post_event_yaw_rate_abs_available")),
            "post_event_offtrack_overshoot": _float_or_blank(execution.get("post_event_offtrack_overshoot")),
            "post_event_offtrack_overshoot_available": _bool(
                execution.get("post_event_offtrack_overshoot_available")
            ),
            "recoverability_window_success": _bool(execution.get("recoverability_window_success")),
            "recoverability_window_success_available": _bool(
                execution.get("recoverability_window_success_available")
            ),
            "recoverability_window_steps": int(recoverability_window_steps),
            "m2816_eval_seed": execution.get("m2816_eval_seed", failure.get("m2816_eval_seed", "")),
            "horizon_steps": int(horizon_steps),
            "soft_offtrack_metric_enabled": bool(execution) and _bool(execution.get("soft_offtrack_metric_enabled")),
            "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
            "bounded_execution_admitted": _bool(mechanism.get("bounded_execution_admitted")),
            "execution_failure": bool(failure),
            "diagnostic_only_no_verdict": True,
            "ranking_claim_made": False,
            "actor_visible_allowed": False,
            "claim_scope": CLAIM_SCOPE,
        }
        rows.append(row)
    return rows


def build_post_offtrack_action_response_rows(
    *, mechanism_rows: list[dict[str, Any]], execution_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    execution_by_mechanism = {str(row.get("mechanism_id", "")): row for row in execution_rows}
    rows: list[dict[str, Any]] = []
    for index, mechanism in enumerate(mechanism_rows, start=1):
        execution = execution_by_mechanism.get(str(mechanism.get("mechanism_id", "")), {})
        rows.append(
            {
                "post_action_response_id": f"m2816-post-offtrack-action-response-{index:04d}",
                "mechanism_id": mechanism.get("mechanism_id", ""),
                "candidate_id": mechanism.get("candidate_id", ""),
                "resolution_id": mechanism.get("resolution_id", ""),
                "task_source_id": mechanism.get("task_source_id", ""),
                "task_family": mechanism.get("task_family", ""),
                "source_edge": mechanism.get("source_edge", ""),
                "stress_axis_primary": mechanism.get("stress_axis_primary", ""),
                "source_outcome_family": mechanism.get("outcome_family", ""),
                "outcome_family": diagnostic_outcome_family(execution),
                "metric_context_available": bool(execution),
                "previous_command_norm_mean": _float_or_blank(execution.get("previous_command_norm_mean")),
                "previous_command_norm_peak": _float_or_blank(execution.get("previous_command_norm_peak")),
                "current_action_norm_mean": _float_or_blank(execution.get("current_action_norm_mean")),
                "current_action_norm_peak": _float_or_blank(execution.get("current_action_norm_peak")),
                "action_trace_delta_mean": _float_or_blank(execution.get("action_trace_delta_mean")),
                "action_trace_delta_peak": _float_or_blank(execution.get("action_trace_delta_peak")),
                "action_rate_mean": _float_or_blank(execution.get("action_rate_mean")),
                "speed_mean": _float_or_blank(execution.get("speed_mean")),
                "time_to_first_off_track_s": _float_or_blank(execution.get("time_to_first_off_track_s")),
                "post_event_speed_mps": _float_or_blank(execution.get("post_event_speed_mps")),
                "post_event_speed_mps_available": _bool(execution.get("post_event_speed_mps_available")),
                "post_event_yaw_rate_abs": _float_or_blank(execution.get("post_event_yaw_rate_abs")),
                "post_event_yaw_rate_abs_available": _bool(execution.get("post_event_yaw_rate_abs_available")),
                "post_event_offtrack_overshoot": _float_or_blank(execution.get("post_event_offtrack_overshoot")),
                "post_event_offtrack_overshoot_available": _bool(
                    execution.get("post_event_offtrack_overshoot_available")
                ),
                "recoverability_window_success": _bool(execution.get("recoverability_window_success")),
                "recoverability_window_success_available": _bool(
                    execution.get("recoverability_window_success_available")
                ),
                "diagnostic_only_no_verdict": True,
                "ranking_claim_made": False,
                "actor_visible_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_offtrack_contrast_rows(
    *,
    mechanism_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    execution_by_mechanism = {str(row.get("mechanism_id", "")): row for row in execution_rows}
    failure_by_mechanism = {str(row.get("mechanism_id", "")): row for row in failure_rows}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mechanism in mechanism_rows:
        source_family = str(mechanism.get("outcome_family", ""))
        item = {
            "mechanism": mechanism,
            "execution": execution_by_mechanism.get(str(mechanism.get("mechanism_id", "")), {}),
            "failure": failure_by_mechanism.get(str(mechanism.get("mechanism_id", "")), {}),
        }
        groups[source_family].append(item)

    rows: list[dict[str, Any]] = []
    for index, source_family in enumerate(sorted(groups), start=1):
        items = groups[source_family]
        executions = [item["execution"] for item in items if item["execution"]]
        failures = [item["failure"] for item in items if item["failure"]]
        rows.append(
            {
                "contrast_id": f"m2816-success-offtrack-contrast-{index:04d}",
                "source_outcome_family": source_family,
                "row_count": len(items),
                "episode_count": len(executions),
                "failure_count": len(failures),
                "success_count_diagnostic": sum(1 for row in executions if _bool(row.get("success"))),
                "collision_count_diagnostic": sum(1 for row in executions if _bool(row.get("collision"))),
                "offtrack_termination_count_diagnostic": sum(
                    1 for row in executions if str(row.get("termination_reason", "")) == "off_track"
                ),
                "post_event_available_count": sum(
                    1 for row in executions if _bool(row.get("post_event_speed_mps_available"))
                ),
                "recoverability_available_count": sum(
                    1 for row in executions if _bool(row.get("recoverability_window_success_available"))
                ),
                "recoverability_success_count": sum(
                    1 for row in executions if _bool(row.get("recoverability_window_success"))
                ),
                "min_clearance_margin_mean": mean_float(executions, "min_clearance_margin"),
                "speed_mean": mean_float(executions, "speed_mean"),
                "action_rate_mean": mean_float(executions, "action_rate_mean"),
                "previous_command_norm_mean": mean_float(executions, "previous_command_norm_mean"),
                "current_action_norm_mean": mean_float(executions, "current_action_norm_mean"),
                "action_trace_delta_mean": mean_float(executions, "action_trace_delta_mean"),
                "ranking_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("observation_shape", "p0_observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_shape", "action_dim", ACTION_DIM, 3),
        actor_guard("m2813_actor_guards_pass", "m2813_actor_guard_rows_pass", m2813_actor_rows_pass(source), True),
        actor_guard("m2810_actor_guards_pass", "m2810_actor_guard_rows_pass", m2810_actor_rows_pass(source), True),
        actor_guard(
            "hidden_oracle_actor_input_absent",
            "hidden_oracle_actor_input_required",
            hidden_oracle_actor_input_detected(source, execution_rows, failure_rows),
            False,
        ),
        actor_guard(
            "actor_contract_changed_absent",
            "actor_input_contract_changed",
            any_flag(execution_rows + failure_rows, "actor_input_contract_changed"),
            False,
        ),
        actor_guard("recoverability_labels_actor_visible", "recoverability_labels_actor_visible", False, False),
        actor_guard("action_response_labels_actor_visible", "action_response_labels_actor_visible", False, False),
        actor_guard(
            "stress_axis_labels_actor_visible",
            "stress_axis_labels_actor_visible",
            any_flag(mechanism_rows + execution_rows + failure_rows, "stress_axis_labels_actor_visible"),
            False,
        ),
        actor_guard("source_edge_labels_actor_visible", "source_edge_labels_actor_visible", False, False),
        actor_guard(
            "success_progress_labels_actor_visible",
            "success_progress_labels_actor_visible",
            any_flag(execution_rows + failure_rows, "success_progress_labels_actor_visible"),
            False,
        ),
        actor_guard(
            "verdict_labels_actor_visible",
            "verdict_labels_actor_visible",
            any_flag(execution_rows + failure_rows, "verdict_labels_actor_visible"),
            False,
        ),
        actor_guard(
            "guardrail_rows_actor_visible",
            "guardrail_actor_visible_allowed",
            any_flag(guardrail_rows, "actor_visible_allowed"),
            False,
        ),
        actor_guard(
            "protected_denominator_absent",
            "protected_rows_in_success_denominator",
            any_flag(guardrail_rows + execution_rows + failure_rows, "protected_rows_in_success_denominator"),
            False,
        ),
    ]


def build_claim_boundary_rows(
    *, follow_up_manifest_registered: bool, artifacts_present: bool, execution_rows_present: bool
) -> list[dict[str, Any]]:
    specs = [
        (
            "bounded_recoverability_execution_artifact_completeness",
            "artifact",
            True,
            artifacts_present and execution_rows_present,
            "M2816 recoverability-window execution artifacts",
        ),
        (
            "follow_up_result_audit_registered",
            "follow_up_route",
            True,
            follow_up_manifest_registered,
            "M2817 result-audit manifest",
        ),
        ("driver_performance", "performance", False, False, "future validation gate"),
        ("repair_success", "repair", False, False, "future repair audit"),
        ("validation_readiness", "validation", False, False, "future validation-readiness manifest"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("controller_ranking", "ranking", False, False, "future comparison gate"),
        ("action_response_ranking", "ranking", False, False, "future comparison gate"),
        ("recoverability_ranking", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("paper_evidence", "paper", False, False, "Route B proof/generalization gates"),
        ("finite_window_vs_gru_conclusion", "paper", False, False, "Route B comparison gates"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C source dependency and validation gates"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim(*spec) for spec in specs]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    recoverability_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    counts = count_source_mechanism_outcomes(mechanism_rows)
    post_event_count = sum(1 for row in recoverability_rows if _bool(row.get("post_event_speed_mps_available")))
    recoverability_available_count = sum(
        1 for row in recoverability_rows if _bool(row.get("recoverability_window_success_available"))
    )
    guardrails_executed = any_flag(guardrail_rows, "execution_run")
    guardrails_in_denominator = any_flag(guardrail_rows, "ordinary_success_denominator_allowed") or any_flag(
        guardrail_rows, "protected_rows_in_success_denominator"
    )
    m2813_gates_pass = gate_rows_pass(source["m2813_gate_matrix"])
    m2807_gates_pass = gate_rows_pass(source["m2807_gate_matrix"])
    m2810_gates_pass = gate_rows_pass(source["m2810_gate_matrix"])
    all_fixed_rows_resolved = all(_bool(row.get("bounded_execution_admitted")) for row in mechanism_rows)
    selected_metrics_ok = selected_metrics_are_finite(execution_rows) if execution_rows else False
    soft_offtrack_enabled = bool(execution_rows) and all(
        _bool(row.get("soft_offtrack_metric_enabled")) for row in execution_rows
    )
    actor_rows_pass = all(_bool(row.get("status_pass")) for row in actor_rows)
    claim_rows_pass = all(_bool(row.get("status_pass")) for row in claim_rows)
    checks = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all source artifacts plus follow-up manifest", "lineage_invalid"),
        ("m2813_status_pass", "lineage", _bool(source["m2813_summary"].get("status_pass")), source["m2813_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m2813_gate_matrix_pass", "lineage", m2813_gates_pass, "all_pass" if m2813_gates_pass else "not_all_pass", "all_pass", "lineage_invalid"),
        ("m2807_gate_matrix_pass", "lineage", m2807_gates_pass, "all_pass" if m2807_gates_pass else "not_all_pass", "all_pass", "lineage_invalid"),
        ("m2810_gate_matrix_pass", "lineage", m2810_gates_pass, "all_pass" if m2810_gates_pass else "not_all_pass", "all_pass", "lineage_invalid"),
        ("mechanism_row_count", "diagnostic_accounting", len(mechanism_rows) == EXPECTED_MECHANISM_ROWS, len(mechanism_rows), EXPECTED_MECHANISM_ROWS, "scenario_sampling_failure"),
        ("source_offtrack_row_count", "diagnostic_accounting", counts["offtrack_count"] == EXPECTED_SOURCE_OFFTRACK_ROWS, counts["offtrack_count"], EXPECTED_SOURCE_OFFTRACK_ROWS, "lineage_invalid"),
        ("source_success_row_count", "diagnostic_accounting", counts["success_count"] == EXPECTED_SOURCE_SUCCESS_ROWS, counts["success_count"], EXPECTED_SOURCE_SUCCESS_ROWS, "lineage_invalid"),
        ("source_collision_row_count", "diagnostic_accounting", counts["collision_count"] == 0, counts["collision_count"], 0, "lineage_invalid"),
        ("all_fixed_rows_resolved", "execution", all_fixed_rows_resolved, "all_resolved" if all_fixed_rows_resolved else "missing_resolution", "all_resolved", "lineage_invalid"),
        ("all_rows_accounted", "execution", len(execution_rows) + len(failure_rows) == len(mechanism_rows), len(execution_rows) + len(failure_rows), len(mechanism_rows), "lineage_invalid"),
        ("execution_failure_count_zero", "execution", len(failure_rows) == 0, len(failure_rows), 0, "behavior_regression"),
        ("instrumented_execution_count", "execution", len(execution_rows) == EXPECTED_MECHANISM_ROWS, len(execution_rows), EXPECTED_MECHANISM_ROWS, "metric_artifact"),
        ("selected_metrics_finite", "metric", selected_metrics_ok, selected_metrics_ok, True, "metric_artifact"),
        ("soft_offtrack_metric_enabled", "metric", soft_offtrack_enabled, "all_enabled" if soft_offtrack_enabled else "not_all_enabled", "all_enabled", "metric_artifact"),
        ("recoverability_window_rows", "artifact", len(recoverability_rows) == EXPECTED_MECHANISM_ROWS, len(recoverability_rows), EXPECTED_MECHANISM_ROWS, "metric_artifact"),
        ("post_offtrack_action_response_rows", "artifact", len(post_rows) == EXPECTED_MECHANISM_ROWS, len(post_rows), EXPECTED_MECHANISM_ROWS, "metric_artifact"),
        ("success_offtrack_contrast_rows", "artifact", len(contrast_rows) == 2, len(contrast_rows), 2, "metric_artifact"),
        ("post_event_available_count_positive", "metric", post_event_count > 0, post_event_count, ">0", "metric_artifact"),
        ("recoverability_available_count_recorded", "metric", recoverability_available_count >= 0, recoverability_available_count, "recorded", "metric_artifact"),
        ("guardrail_context_rows", "guardrail", len(guardrail_rows) == EXPECTED_GUARDRAIL_ROWS, len(guardrail_rows), EXPECTED_GUARDRAIL_ROWS, "lineage_invalid"),
        ("guardrails_not_executed", "guardrail", not guardrails_executed, guardrails_executed, False, "proof_washout"),
        ("guardrails_outside_denominator", "guardrail", not guardrails_in_denominator, guardrails_in_denominator, False, "proof_washout"),
        ("actor_contract_guards_pass", "contract", actor_rows_pass, "all_pass" if actor_rows_pass else "not_all_pass", "all_pass", "contract_violation"),
        ("claim_boundary_rows_pass", "claim", claim_rows_pass, "all_pass" if claim_rows_pass else "not_all_pass", "all_pass", "proof_washout"),
        ("training_false", "claim", not any_flag(execution_rows + failure_rows, "training_run"), any_flag(execution_rows + failure_rows, "training_run"), False, "objective_overfit"),
        ("ranking_false", "claim", not any_flag(execution_rows + failure_rows, "ranking_run"), any_flag(execution_rows + failure_rows, "ranking_run"), False, "objective_overfit"),
        ("driver_performance_claim_false", "claim", not any_flag(execution_rows + failure_rows, "driver_performance_claim_made"), any_flag(execution_rows + failure_rows, "driver_performance_claim_made"), False, "proof_washout"),
        ("paper_claim_false", "claim", not any_flag(execution_rows + failure_rows, "paper_claim_made"), any_flag(execution_rows + failure_rows, "paper_claim_made"), False, "proof_washout"),
        ("current_sim_verdict_false", "claim", not any_flag(execution_rows + failure_rows, "current_sim_verdict_claim_made"), any_flag(execution_rows + failure_rows, "current_sim_verdict_claim_made"), False, "proof_washout"),
        ("level3_self_id_claim_false", "claim", not any_flag(execution_rows + failure_rows, "level3_self_id_claim_made"), any_flag(execution_rows + failure_rows, "level3_self_id_claim_made"), False, "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]
    return [gate(*check) for check in checks]


def write_outputs(
    paths: dict[str, Path],
    recoverability_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["recoverability_window_rows"], recoverability_rows, fieldnames=RECOVERABILITY_FIELDNAMES)
    write_csv_rows(paths["post_offtrack_action_response_rows"], post_rows, fieldnames=POST_ACTION_RESPONSE_FIELDNAMES)
    write_csv_rows(paths["success_offtrack_contrast_rows"], contrast_rows, fieldnames=CONTRAST_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    execution_summary: dict[str, Any],
    recoverability_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    seed_start_index: int,
    horizon_steps: int,
    recoverability_window_steps: int,
    soft_offtrack_tolerance_m: float,
    device: str,
) -> dict[str, Any]:
    source_counts = count_source_mechanism_outcomes(mechanism_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gate_rows)
    post_event_available_count = sum(1 for row in recoverability_rows if _bool(row.get("post_event_speed_mps_available")))
    recoverability_available_count = sum(
        1 for row in recoverability_rows if _bool(row.get("recoverability_window_success_available"))
    )
    recoverability_success_count = sum(
        1 for row in recoverability_rows if _bool(row.get("recoverability_window_success"))
    )
    status_pass = bool(
        required_artifacts_present
        and all(source["source_exists"].values())
        and gate_matrix_pass
        and bool(execution_summary.get("status_pass"))
        and post_event_available_count > 0
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_action_response_recoverability_window_v0",
        "result_class": (
            "engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight_fail"
        ),
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "recoverability_window_rows": str(paths["recoverability_window_rows"]),
        "post_offtrack_action_response_rows": str(paths["post_offtrack_action_response_rows"]),
        "success_offtrack_contrast_rows": str(paths["success_offtrack_contrast_rows"]),
        "guardrail_context_rows": str(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "instrumented_execution_rows": str(paths["instrumented_execution_rows"]),
        "instrumented_execution_failure_rows": str(paths["instrumented_execution_failure_rows"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(follow_up_manifest),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_exists": source["source_exists"],
        "mechanism_row_count": len(mechanism_rows),
        "source_offtrack_mechanism_row_count": source_counts["offtrack_count"],
        "source_success_mechanism_row_count": source_counts["success_count"],
        "source_collision_mechanism_row_count": source_counts["collision_count"],
        "episode_count": len(execution_rows),
        "failure_count": len(failure_rows),
        "accounted_count": len(execution_rows) + len(failure_rows),
        "diagnostic_success_count": sum(1 for row in execution_rows if _bool(row.get("success"))),
        "diagnostic_collision_count": sum(1 for row in execution_rows if _bool(row.get("collision"))),
        "diagnostic_offtrack_termination_count": sum(
            1 for row in execution_rows if str(row.get("termination_reason", "")) == "off_track"
        ),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "recoverability_window_row_count": len(recoverability_rows),
        "post_offtrack_action_response_row_count": len(post_rows),
        "success_offtrack_contrast_row_count": len(contrast_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "post_event_available_count": post_event_available_count,
        "recoverability_available_count": recoverability_available_count,
        "recoverability_success_count": recoverability_success_count,
        "all_selected_metrics_finite": selected_metrics_are_finite(execution_rows) if execution_rows else False,
        "seed_start_index": int(seed_start_index),
        "horizon_steps": int(horizon_steps),
        "recoverability_window_steps": int(recoverability_window_steps),
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
        "device": device,
        "guardrails_not_executed": not any_flag(guardrail_rows, "execution_run"),
        "protected_rows_in_success_denominator": any_flag(guardrail_rows + execution_rows + failure_rows, "protected_rows_in_success_denominator"),
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(source, execution_rows, failure_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass")) for row in actor_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass")) for row in claim_rows),
        "execution_summary": execution_summary,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2816 Engineering Controller Route A Post-Action-Response Recoverability-Window Instrumented Bounded Execution Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- recoverability rows: `{summary['recoverability_window_rows']}`",
            f"- post-offtrack action-response rows: `{summary['post_offtrack_action_response_rows']}`",
            f"- success/offtrack contrast rows: `{summary['success_offtrack_contrast_rows']}`",
            f"- guardrail context rows: `{summary['guardrail_context_rows']}`",
            f"- actor contract guard rows: `{summary['actor_contract_guard_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Fixed Row Accounting",
            "",
            f"- fixed mechanism rows: {summary['mechanism_row_count']}",
            f"- source offtrack rows: {summary['source_offtrack_mechanism_row_count']}",
            f"- source success rows: {summary['source_success_mechanism_row_count']}",
            f"- source collision rows: {summary['source_collision_mechanism_row_count']}",
            f"- instrumented execution rows: {summary['episode_count']}",
            f"- execution failures: {summary['failure_count']}",
            f"- diagnostic terminations: {summary['diagnostic_termination_counts']}",
            "",
            "## Recoverability Diagnostics",
            "",
            f"- horizon steps: {summary['horizon_steps']}",
            f"- recoverability window steps: {summary['recoverability_window_steps']}",
            f"- soft-offtrack metric enabled: `{str(summary['soft_offtrack_metric_enabled']).lower()}`",
            f"- soft-offtrack tolerance m: {summary['soft_offtrack_tolerance_m']}",
            f"- post-event available rows: {summary['post_event_available_count']}",
            f"- recoverability available rows: {summary['recoverability_available_count']}",
            f"- recoverability success rows: {summary['recoverability_success_count']}",
            "",
            "## Guardrails",
            "",
            f"- guardrail context rows: {summary['guardrail_context_row_count']}",
            f"- guardrails not executed: `{str(summary['guardrails_not_executed']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- action-response, recoverability, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            summary["claim_scope"],
            "",
            "Forbidden interpretation:",
            "",
            summary["forbidden_interpretation"],
            "",
        ]
    )


def diagnostic_outcome_family(row: Mapping[str, Any]) -> str:
    if not row:
        return "execution_missing"
    if _bool(row.get("success")):
        return "success_obstacle_pass"
    if _bool(row.get("collision")):
        return "collision_failure"
    if str(row.get("termination_reason", "")) == "off_track":
        return "offtrack_hard_termination"
    if _finite(row.get("max_off_track_overshoot")) and float(row.get("max_off_track_overshoot")) > 0.0:
        return "offtrack_soft_event_continued"
    return str(row.get("outcome_bucket", "") or "other_diagnostic")


def count_source_mechanism_outcomes(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "success_count": sum(1 for row in rows if row.get("outcome_family") == "success_obstacle_pass"),
        "offtrack_count": sum(1 for row in rows if _bool(row.get("offtrack_noncollision"))),
        "collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
    }


def actor_guard(guard_id: str, guard_family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2816-actor-guard-{guard_id}",
        "guard_family": guard_family,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2816-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2816": allowed,
        "claim_made": made,
        "status_pass": made == allowed if allowed else not made,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2816-gate-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)


def m2813_actor_rows_pass(source: dict[str, Any]) -> bool:
    rows = source["m2813_actor_contract_guard_rows"]
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)


def m2810_actor_rows_pass(source: dict[str, Any]) -> bool:
    rows = source["m2810_actor_contract_guard_rows"]
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)


def hidden_oracle_actor_input_detected(
    source: dict[str, Any], execution_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]
) -> bool:
    summary_hidden = any(
        _bool(source["m2813_summary"].get(key))
        for key in ("hidden_oracle_actor_input_detected", "hidden_oracle_actor_input_required")
    )
    row_hidden = any_flag(source["m2813_action_response_mechanism_rows"], "hidden_oracle_actor_input_required")
    execution_hidden = any_flag(execution_rows + failure_rows, "hidden_oracle_actor_input_required")
    return summary_hidden or row_hidden or execution_hidden


def any_forbidden_flag(rows: list[Mapping[str, Any]]) -> bool:
    return any(any_flag(rows, key) for key in FALSE_CLAIM_FLAGS) or any_flag(rows, "actor_input_contract_changed")


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key)) for row in rows)


def mean_float(rows: list[Mapping[str, Any]], key: str) -> float | str:
    values = [_float(row.get(key)) for row in rows]
    finite = [value for value in values if value is not None]
    if not finite:
        return ""
    return float(np.mean(finite))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _finite(value: Any) -> bool:
    return _float(value) is not None


def _float_or_blank(value: Any) -> float | str:
    numeric = _float(value)
    return "" if numeric is None else float(numeric)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run M2816 recoverability-window instrumented bounded execution preflight."
    )
    parser.add_argument("--m2815-synthesis", type=Path, default=DEFAULT_M2815_SYNTHESIS)
    parser.add_argument("--m2813-dir", type=Path, default=DEFAULT_M2813_DIR)
    parser.add_argument("--m2807-dir", type=Path, default=DEFAULT_M2807_DIR)
    parser.add_argument("--m2810-dir", type=Path, default=DEFAULT_M2810_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed-start-index", type=int, default=DEFAULT_SEED_START_INDEX)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--recoverability-window-steps", type=int, default=DEFAULT_RECOVERABILITY_WINDOW_STEPS)
    parser.add_argument("--soft-offtrack-tolerance-m", type=float, default=DEFAULT_SOFT_OFFTRACK_TOLERANCE_M)
    args = parser.parse_args(argv)
    summary = run_post_action_response_recoverability_window_instrumented_bounded_execution_preflight(
        m2815_synthesis=args.m2815_synthesis,
        m2813_dir=args.m2813_dir,
        m2807_dir=args.m2807_dir,
        m2810_dir=args.m2810_dir,
        source_checkpoint=args.source_checkpoint,
        executable_specs=args.executable_specs,
        route_plan=args.route_plan,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
        seed_start_index=args.seed_start_index,
        horizon_steps=args.horizon_steps,
        recoverability_window_steps=args.recoverability_window_steps,
        soft_offtrack_tolerance_m=args.soft_offtrack_tolerance_m,
    )
    print(
        f"{summary['milestone']} status_pass={summary['status_pass']} "
        f"recoverability_available={summary['recoverability_available_count']} "
        f"post_event_available={summary['post_event_available_count']}"
    )
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
