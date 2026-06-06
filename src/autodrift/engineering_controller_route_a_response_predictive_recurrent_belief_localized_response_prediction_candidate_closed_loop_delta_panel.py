"""Run M2868 localized response-prediction candidate closed-loop delta panel."""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

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
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    _file_sha256,
    model_state_sha256,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2868-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-candidate-closed-loop-delta-panel-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2869-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-candidate-closed-loop-delta-panel-result-audit"
)
DEFAULT_M2867_AUDIT = Path(
    "docs/m2867-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-implementation-result-audit.md"
)
DEFAULT_M2866_SUMMARY = Path(
    "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_"
    "response_prediction_training_implementation_preflight/summary.json"
)
DEFAULT_M2857_SURFACE_ROWS = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_per_step_"
    "telemetry_panel_materialization/telemetry_surface_rows.csv"
)
DEFAULT_BASELINE_CHECKPOINT = Path(
    "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_"
    "response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_"
    "response_prediction_candidate_closed_loop_delta_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2868-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-candidate-closed-loop-delta-panel-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2869-engineering-controller-route-a-response-predictive-recurrent-"
    "belief-localized-response-prediction-candidate-closed-loop-delta-panel-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 286800
DEFAULT_ROW_COUNT = 24
DEFAULT_HORIZON_STEPS = 96
CANONICAL_PROFILE = "L3_online_gru"
CHECKPOINT_SUBJECTS = ("baseline", "candidate")

CLAIM_SCOPE = (
    "M2868 bounded Route A paired closed-loop diagnostic delta panel only. It compares "
    "the M2848 source checkpoint and the M2866 localized response-prediction candidate "
    "over fixed M2857 M2850-explanatory and fresh/disjoint surfaces for audit. It does "
    "not validate, rank, select a winner, promote, compute a success-rate verdict, or "
    "claim repair success, driver performance, paper evidence, finite-window-vs-GRU "
    "evidence, current-sim verdict, high-fidelity validation, full ideal driver "
    "completion, or level3 self-identification."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, "
    "source-family ranking, task-family ranking, scenario-role ranking, winner "
    "selection, checkpoint promotion, success-rate verdict, repair success, driver "
    "performance, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation, full ideal driver completion, or level3 "
    "self-identification"
)

FALSE_CLAIM_FLAGS = {
    "training_started": False,
    "replay_started": False,
    "ppo_used": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
    "active_config_overwritten": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_verdict_computed": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
}

SURFACE_FIELDNAMES = [
    "surface_row_id",
    "surface_id",
    "surface_role",
    "source_from",
    "public_diagnostic_row",
    "fresh_or_disjoint",
    "overlap_guard_required",
    "overlap_reason",
]
PAIRED_EXECUTION_FIELDNAMES = [
    "pair_id",
    *SURFACE_FIELDNAMES,
    "execution_row_id",
    "checkpoint_subject",
    "checkpoint_path",
    "checkpoint_hash",
    "model_state_hash",
    "actor_encoder",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "source_family_tag",
    "scenario_role_primary",
    "diagnostic_tags",
    "profile_config_path",
    "pair_index",
    "eval_seed",
    "eval_seed_base",
    "horizon_steps",
    "env_max_steps_applied",
    "execution_status",
    "error_type",
    "error_message",
    "reset_run",
    "environment_step_run",
    "policy_action_run",
    "closed_loop_rollout_run",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "min_obstacle_clearance",
    "return",
    "speed_mean",
    "high_sideslip_fraction",
    "action_rate_mean",
    "previous_command_norm_mean",
    "current_action_norm_mean",
    "action_trace_delta_mean",
    "plan_horizon",
    "observation_shape",
    "action_shape",
    "finite_selected_metrics",
    "actor_contract_shape_72_action_3",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "actor_visible_label",
    "source_labels_actor_visible",
    "stress_axis_labels_actor_visible",
    "scenario_role_labels_actor_visible",
    "outcome_labels_actor_visible",
    "route_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ordinary_success_denominator_allowed",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_verdict_computed",
    "driver_performance_claim_made",
    "validation_readiness_claim_made",
    "validation_result_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_gate_passed",
    "level3_self_id_claim_made",
    "claim_scope",
    "forbidden_interpretation",
]
PAIRED_DELTA_FIELDNAMES = [
    "pair_id",
    *SURFACE_FIELDNAMES,
    "pair_index",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "source_family_tag",
    "scenario_role_primary",
    "diagnostic_tags",
    "eval_seed",
    "baseline_execution_row_id",
    "candidate_execution_row_id",
    "baseline_checkpoint",
    "candidate_checkpoint",
    "baseline_checkpoint_hash",
    "candidate_checkpoint_hash",
    "baseline_execution_status",
    "candidate_execution_status",
    "baseline_steps",
    "candidate_steps",
    "baseline_success_diagnostic",
    "candidate_success_diagnostic",
    "baseline_collision_diagnostic",
    "candidate_collision_diagnostic",
    "termination_pair_changed",
    "collision_pair_changed",
    "candidate_minus_baseline_min_clearance_margin",
    "candidate_minus_baseline_return",
    "candidate_minus_baseline_speed_mean",
    "candidate_minus_baseline_high_sideslip_fraction",
    "candidate_minus_baseline_action_rate_mean",
    "candidate_minus_baseline_previous_command_norm_mean",
    "candidate_minus_baseline_current_action_norm_mean",
    "candidate_minus_baseline_action_trace_delta_mean",
    "candidate_minus_baseline_steps",
    "paired_execution_complete",
    "finite_delta",
    "ordinary_success_denominator_allowed",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "success_rate_verdict_computed",
    "claim_scope",
    "forbidden_interpretation",
]
SURFACE_DELTA_FIELDNAMES = [
    "surface_id",
    "surface_role",
    "source_from",
    "public_diagnostic_row",
    "fresh_or_disjoint",
    "paired_delta_row_count",
    "complete_pair_count",
    "finite_delta_count",
    "termination_pair_changed_count",
    "collision_pair_changed_count",
    "mean_candidate_minus_baseline_min_clearance_margin",
    "mean_candidate_minus_baseline_return",
    "mean_candidate_minus_baseline_speed_mean",
    "mean_candidate_minus_baseline_high_sideslip_fraction",
    "mean_candidate_minus_baseline_action_rate_mean",
    "mean_candidate_minus_baseline_previous_command_norm_mean",
    "mean_candidate_minus_baseline_current_action_norm_mean",
    "mean_candidate_minus_baseline_action_trace_delta_mean",
    "mean_candidate_minus_baseline_steps",
    "ordinary_success_denominator_allowed",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "success_rate_verdict_computed",
    "claim_scope",
    "forbidden_interpretation",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "row_count",
    "failure_type",
    "claim_boundary",
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
    "allowed_in_m2868",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "paired_execution_rows",
    "paired_delta_rows",
    "surface_delta_rows",
    "proof_retention_gate_rows",
    "generalization_delta_gate_rows",
    "promotion_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]
DELTA_METRIC_KEYS = [
    "candidate_minus_baseline_min_clearance_margin",
    "candidate_minus_baseline_return",
    "candidate_minus_baseline_speed_mean",
    "candidate_minus_baseline_high_sideslip_fraction",
    "candidate_minus_baseline_action_rate_mean",
    "candidate_minus_baseline_previous_command_norm_mean",
    "candidate_minus_baseline_current_action_norm_mean",
    "candidate_minus_baseline_action_trace_delta_mean",
    "candidate_minus_baseline_steps",
]


def run_localized_response_prediction_candidate_closed_loop_delta_panel(
    *,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    m2867_audit: Path | str = DEFAULT_M2867_AUDIT,
    m2866_summary: Path | str = DEFAULT_M2866_SUMMARY,
    m2857_surface_rows: Path | str = DEFAULT_M2857_SURFACE_ROWS,
    baseline_checkpoint: Path | str = DEFAULT_BASELINE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    row_count: int = DEFAULT_ROW_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
        m2867_audit=Path(m2867_audit),
        m2866_summary=Path(m2866_summary),
        m2857_surface_rows=Path(m2857_surface_rows),
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
    )
    subject_registry = load_subject_registry(
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
        device=device,
    )
    selected_rows = resolve_selected_surface_rows(source, row_count=int(row_count))
    execution_rows = collect_paired_execution_rows(
        selected_rows=selected_rows,
        source=source,
        subject_registry=subject_registry,
        output_dir=output,
        eval_seed_base=int(eval_seed_base),
        horizon_steps=int(horizon_steps),
        device=device,
        next_blocker=next_blocker,
    )
    write_csv_rows(paths["paired_execution_rows"], execution_rows, fieldnames=PAIRED_EXECUTION_FIELDNAMES)
    delta_rows = build_paired_delta_rows(execution_rows, subject_registry)
    surface_delta_rows = build_surface_delta_rows(delta_rows)
    write_csv_rows(paths["paired_delta_rows"], delta_rows, fieldnames=PAIRED_DELTA_FIELDNAMES)
    write_csv_rows(paths["surface_delta_rows"], surface_delta_rows, fieldnames=SURFACE_DELTA_FIELDNAMES)

    summary: dict[str, Any] = {}
    for _pass_index in range(2):
        required_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
        actor_guard_rows = build_actor_contract_guard_rows(execution_rows, subject_registry)
        claim_rows = build_claim_boundary_rows(
            paired_execution_rows=execution_rows,
            paired_delta_rows=delta_rows,
            surface_delta_rows=surface_delta_rows,
            required_artifacts_present=required_present,
            follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
        )
        proof_rows = build_proof_retention_gate_rows(
            source=source,
            subject_registry=subject_registry,
            selected_rows=selected_rows,
            execution_rows=execution_rows,
            delta_rows=delta_rows,
            surface_delta_rows=surface_delta_rows,
            actor_guard_rows=actor_guard_rows,
            claim_rows=claim_rows,
            required_artifacts_present=required_present,
        )
        generalization_rows = build_generalization_delta_gate_rows(
            selected_rows=selected_rows,
            execution_rows=execution_rows,
            delta_rows=delta_rows,
            surface_delta_rows=surface_delta_rows,
            row_count=int(row_count),
            horizon_steps=int(horizon_steps),
        )
        promotion_rows = build_promotion_guard_rows(execution_rows, delta_rows, surface_delta_rows)
        gate_rows = proof_rows + generalization_rows + promotion_rows
        write_csv_rows(paths["proof_retention_gate_rows"], proof_rows, fieldnames=GATE_FIELDNAMES)
        write_csv_rows(paths["generalization_delta_gate_rows"], generalization_rows, fieldnames=GATE_FIELDNAMES)
        write_csv_rows(paths["promotion_guard_rows"], promotion_rows, fieldnames=GATE_FIELDNAMES)
        write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
        write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
        write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
        summary = build_summary(
            output_dir=output,
            paths=paths,
            source=source,
            subject_registry=subject_registry,
            selected_rows=selected_rows,
            execution_rows=execution_rows,
            delta_rows=delta_rows,
            surface_delta_rows=surface_delta_rows,
            proof_gate_rows=proof_rows,
            generalization_gate_rows=generalization_rows,
            promotion_guard_rows=promotion_rows,
            actor_guard_rows=actor_guard_rows,
            claim_rows=claim_rows,
            gate_rows=gate_rows,
            required_artifacts_present=required_present,
            eval_seed_base=int(eval_seed_base),
            row_count=int(row_count),
            horizon_steps=int(horizon_steps),
            device=device,
            milestone=milestone,
            next_blocker=next_blocker,
        )
        write_json(paths["summary"], summary)
        write_follow_up_manifest(paths["follow_up_manifest"], build_m2869_follow_up_manifest(summary))
        paths["doc"].parent.mkdir(parents=True, exist_ok=True)
        paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    write_run_state(paths["run_state"], build_run_state(summary))
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "paired_execution_rows": output_dir / "paired_execution_rows.csv",
        "paired_delta_rows": output_dir / "paired_delta_rows.csv",
        "surface_delta_rows": output_dir / "surface_delta_rows.csv",
        "proof_retention_gate_rows": output_dir / "proof_retention_gate_rows.csv",
        "generalization_delta_gate_rows": output_dir / "generalization_delta_gate_rows.csv",
        "promotion_guard_rows": output_dir / "promotion_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m1690_workload: Path,
    executable_specs: Path,
    m2867_audit: Path,
    m2866_summary: Path,
    m2857_surface_rows: Path,
    baseline_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Any]:
    paths = {
        "m1690_workload": m1690_workload,
        "executable_specs": executable_specs,
        "m2867_audit": m2867_audit,
        "m2866_summary": m2866_summary,
        "m2857_surface_rows": m2857_surface_rows,
        "baseline_checkpoint": baseline_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m1690_rows = read_csv_rows(m1690_workload) if m1690_workload.exists() else []
    specs = load_executable_specs(executable_specs) if executable_specs.exists() else []
    m2866_summary_payload = read_json(m2866_summary) if m2866_summary.exists() else {}
    m2866_checkpoint_manifest = _read_optional_json(m2866_summary_payload.get("checkpoint_manifest", ""))
    m2866_actor_guard_rows = _read_optional_csv(m2866_summary_payload.get("actor_contract_guard_rows", ""))
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m1690_rows": m1690_rows,
        "m1690_l3_by_task_source": {
            str(row.get("task_source_id", "")): row
            for row in m1690_rows
            if str(row.get("profile_name", "")) == CANONICAL_PROFILE
        },
        "executable_specs": specs,
        "executable_spec_by_task_source": {str(spec["task_source_id"]): spec for spec in specs},
        "m2867_audit_text": m2867_audit.read_text(encoding="utf-8") if m2867_audit.exists() else "",
        "m2866_summary": m2866_summary_payload,
        "m2866_checkpoint_manifest": m2866_checkpoint_manifest,
        "m2866_actor_guard_rows": m2866_actor_guard_rows,
        "m2857_surface_rows": read_csv_rows(m2857_surface_rows) if m2857_surface_rows.exists() else [],
    }


def load_subject_registry(
    *,
    baseline_checkpoint: Path,
    candidate_checkpoint: Path,
    device: str,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for subject, path in (("baseline", baseline_checkpoint), ("candidate", candidate_checkpoint)):
        model, checkpoint = load_actor_critic_checkpoint(path, device=device)
        if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
            raise RuntimeError(f"{subject} checkpoint does not preserve P0 72/action 3")
        registry[subject] = {
            "subject": subject,
            "checkpoint_path": Path(path),
            "checkpoint_hash": _file_sha256(path),
            "model_state_hash": model_state_sha256(checkpoint["model_state"]),
            "actor_encoder": getattr(model, "actor_encoder", ""),
            "model": model,
        }
    return registry


def resolve_selected_surface_rows(source: dict[str, Any], row_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, surface in enumerate(source["m2857_surface_rows"][: int(row_count)], start=1):
        task_source_id = str(surface.get("task_source_id", ""))
        source_row = source["m1690_l3_by_task_source"].get(task_source_id)
        failure_reason = ""
        if not task_source_id:
            failure_reason = "surface_task_source_missing"
        elif source_row is None:
            failure_reason = "surface_task_source_missing_from_m1690_l3_rows"
        elif str(source_row.get("profile_name", "")) != CANONICAL_PROFILE:
            failure_reason = "profile_not_l3_online_gru"
        elif str(source_row.get("config_exists", "")) != "True":
            failure_reason = "profile_config_missing"
        elif _bool(source_row.get("profile_specific_tuning", False)):
            failure_reason = "profile_specific_tuning_detected"
        elif task_source_id not in source["executable_spec_by_task_source"]:
            failure_reason = "executable_spec_missing"
        elif _bool(surface.get("ranking_admissible", False)):
            failure_reason = "surface_ranking_admissible"
        elif _bool(surface.get("ordinary_success_denominator_allowed", False)):
            failure_reason = "surface_ordinary_denominator_allowed"
        admitted = source_row is not None and not failure_reason
        source_edge = str((source_row or {}).get("source_edge") or surface.get("source_edge", ""))
        rows.append(
            {
                "pair_index": index,
                "pair_id": str(surface.get("pair_id") or f"m2868-pair-{index:04d}-{task_source_id}"),
                "surface_row_id": str(surface.get("surface_row_id", f"m2868-surface-{index:04d}")),
                "surface_id": str(surface.get("surface_id", "")),
                "task_source_id": task_source_id,
                "workload_id": (source_row or {}).get("workload_id", f"{task_source_id}::{CANONICAL_PROFILE}"),
                "profile_name": (source_row or {}).get("profile_name", CANONICAL_PROFILE),
                "task_family": (source_row or {}).get("task_family", surface.get("task_family", "")),
                "source_edge": source_edge,
                "window_tag": (source_row or {}).get("window_tag", surface.get("window_tag", "")),
                "strata": (source_row or {}).get("strata", ""),
                "executable_source_family": (source_row or {}).get("executable_source_family", ""),
                "env_template_family": (source_row or {}).get("env_template_family", ""),
                "source_family_tag": str(surface.get("source_family_tag") or source_edge.split("|")[0]),
                "scenario_role_primary": str(
                    surface.get("scenario_role_primary") or (source_edge.split("|")[-1] if source_edge else "")
                ),
                "surface_role": str(surface.get("surface_role", "")),
                "source_from": str(surface.get("source_from", "")),
                "public_diagnostic_row": _bool(surface.get("public_diagnostic_row", False)),
                "fresh_or_disjoint": _bool(surface.get("fresh_or_disjoint", False)),
                "overlap_guard_required": _bool(surface.get("overlap_guard_required", False)),
                "overlap_reason": str(surface.get("overlap_reason", "")),
                "diagnostic_tags": f"{surface.get('surface_id', '')};{surface.get('surface_role', '')}",
                "profile_config_path": (source_row or {}).get("profile_config_path", ""),
                "source_row": source_row,
                "admitted": admitted,
                "failure_reason": failure_reason,
            }
        )
    return rows


def collect_paired_execution_rows(
    *,
    selected_rows: list[dict[str, Any]],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    output_dir: Path,
    eval_seed_base: int,
    horizon_steps: int,
    device: str,
    next_blocker: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, panel_row in enumerate(selected_rows):
        eval_seed = int(eval_seed_base) + index
        for subject in CHECKPOINT_SUBJECTS:
            try:
                row = run_single_subject_execution(
                    panel_row=panel_row,
                    source=source,
                    subject_entry=subject_registry[subject],
                    eval_seed=eval_seed,
                    eval_seed_base=int(eval_seed_base),
                    horizon_steps=int(horizon_steps),
                    device=device,
                )
            except Exception as exc:  # noqa: BLE001 - failed execution is durable audit evidence.
                row = failed_execution_row(
                    panel_row=panel_row,
                    subject_entry=subject_registry[subject],
                    eval_seed=eval_seed,
                    eval_seed_base=int(eval_seed_base),
                    horizon_steps=int(horizon_steps),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            rows.append(row)
        write_run_state(
            output_dir / "run_state.json",
            {
                "paired_panel_count": len(selected_rows),
                "paired_execution_row_count": len(rows),
                "latest_pair_id": panel_row["pair_id"],
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return rows


def run_single_subject_execution(
    *,
    panel_row: Mapping[str, Any],
    source: dict[str, Any],
    subject_entry: dict[str, Any],
    eval_seed: int,
    eval_seed_base: int,
    horizon_steps: int,
    device: str,
) -> dict[str, Any]:
    del device
    if not _bool(panel_row.get("admitted", False)):
        raise ValueError(str(panel_row.get("failure_reason", "panel row not admitted")))
    task_source_id = str(panel_row["task_source_id"])
    source_row = dict(panel_row["source_row"])
    spec = copy.deepcopy(source["executable_spec_by_task_source"][task_source_id])
    spec.setdefault("env_config", {})
    spec["env_config"] = dict(spec["env_config"])
    spec["env_config"]["max_steps"] = int(horizon_steps)
    profile_config = read_json(source_row["profile_config_path"])
    profile_row = {
        "profile_name": str(source_row["profile_name"]),
        "config_path": str(source_row["profile_config_path"]),
        "checkpoint_path": str(subject_entry["checkpoint_path"]),
    }
    row = run_workload_cell(
        workload_row=source_row,
        executable_spec=spec,
        profile_config=profile_config,
        model=subject_entry["model"],
        profile_row=profile_row,
        eval_seed=int(eval_seed),
    )
    row.update(
        execution_metadata(
            panel_row=panel_row,
            subject_entry=subject_entry,
            eval_seed=eval_seed,
            eval_seed_base=eval_seed_base,
            horizon_steps=horizon_steps,
            execution_status="completed",
            error_type="",
            error_message="",
        )
    )
    row["steps"] = int(row.get("steps", 0))
    row["finite_selected_metrics"] = selected_metrics_are_finite([row])
    return row


def failed_execution_row(
    *,
    panel_row: Mapping[str, Any],
    subject_entry: dict[str, Any],
    eval_seed: int,
    eval_seed_base: int,
    horizon_steps: int,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    row = {
        "steps": 0,
        "terminated": False,
        "truncated": False,
        "success": False,
        "collision": False,
        "obstacle_completed": False,
        "termination_reason": "",
        "outcome_bucket": "execution_failure",
        "min_clearance_margin": "",
        "min_obstacle_clearance": "",
        "return": "",
        "speed_mean": "",
        "high_sideslip_fraction": "",
        "action_rate_mean": "",
        "previous_command_norm_mean": "",
        "current_action_norm_mean": "",
        "action_trace_delta_mean": "",
        "plan_horizon": "",
        "finite_selected_metrics": False,
    }
    row.update(
        execution_metadata(
            panel_row=panel_row,
            subject_entry=subject_entry,
            eval_seed=eval_seed,
            eval_seed_base=eval_seed_base,
            horizon_steps=horizon_steps,
            execution_status="failed",
            error_type=error_type,
            error_message=error_message,
        )
    )
    return row


def execution_metadata(
    *,
    panel_row: Mapping[str, Any],
    subject_entry: dict[str, Any],
    eval_seed: int,
    eval_seed_base: int,
    horizon_steps: int,
    execution_status: str,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    return {
        "pair_id": panel_row["pair_id"],
        "surface_row_id": panel_row["surface_row_id"],
        "surface_id": panel_row["surface_id"],
        "surface_role": panel_row["surface_role"],
        "source_from": panel_row["source_from"],
        "public_diagnostic_row": panel_row["public_diagnostic_row"],
        "fresh_or_disjoint": panel_row["fresh_or_disjoint"],
        "overlap_guard_required": panel_row["overlap_guard_required"],
        "overlap_reason": panel_row["overlap_reason"],
        "execution_row_id": f"{panel_row['pair_id']}-{subject_entry['subject']}",
        "checkpoint_subject": subject_entry["subject"],
        "checkpoint_path": str(subject_entry["checkpoint_path"]),
        "checkpoint_hash": subject_entry["checkpoint_hash"],
        "model_state_hash": subject_entry["model_state_hash"],
        "actor_encoder": subject_entry["actor_encoder"],
        "workload_id": panel_row["workload_id"],
        "task_source_id": panel_row["task_source_id"],
        "profile_name": panel_row["profile_name"],
        "task_family": panel_row["task_family"],
        "source_edge": panel_row["source_edge"],
        "window_tag": panel_row["window_tag"],
        "strata": panel_row["strata"],
        "executable_source_family": panel_row["executable_source_family"],
        "env_template_family": panel_row["env_template_family"],
        "source_family_tag": panel_row["source_family_tag"],
        "scenario_role_primary": panel_row["scenario_role_primary"],
        "diagnostic_tags": panel_row["diagnostic_tags"],
        "profile_config_path": panel_row["profile_config_path"],
        "pair_index": panel_row["pair_index"],
        "eval_seed": int(eval_seed),
        "eval_seed_base": int(eval_seed_base),
        "horizon_steps": int(horizon_steps),
        "env_max_steps_applied": int(horizon_steps),
        "execution_status": execution_status,
        "error_type": error_type,
        "error_message": error_message,
        "reset_run": execution_status == "completed",
        "environment_step_run": execution_status == "completed",
        "policy_action_run": execution_status == "completed",
        "closed_loop_rollout_run": execution_status == "completed",
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": True,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "actor_visible_label": False,
        "source_labels_actor_visible": False,
        "stress_axis_labels_actor_visible": False,
        "scenario_role_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ordinary_success_denominator_allowed": False,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_paired_delta_rows(
    execution_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in execution_rows:
        by_pair.setdefault(str(row["pair_id"]), {})[str(row["checkpoint_subject"])] = row
    rows: list[dict[str, Any]] = []
    for pair_id in sorted(by_pair):
        pair = by_pair[pair_id]
        baseline = pair.get("baseline")
        candidate = pair.get("candidate")
        if baseline is None or candidate is None:
            continue
        delta_values = {key: _delta(candidate, baseline, key.replace("candidate_minus_baseline_", "")) for key in DELTA_METRIC_KEYS}
        rows.append(
            {
                "pair_id": pair_id,
                **{key: baseline.get(key, "") for key in SURFACE_FIELDNAMES},
                "pair_index": baseline.get("pair_index", ""),
                "task_source_id": baseline.get("task_source_id", ""),
                "workload_id": baseline.get("workload_id", ""),
                "profile_name": baseline.get("profile_name", ""),
                "task_family": baseline.get("task_family", ""),
                "source_edge": baseline.get("source_edge", ""),
                "window_tag": baseline.get("window_tag", ""),
                "source_family_tag": baseline.get("source_family_tag", ""),
                "scenario_role_primary": baseline.get("scenario_role_primary", ""),
                "diagnostic_tags": baseline.get("diagnostic_tags", ""),
                "eval_seed": baseline.get("eval_seed", ""),
                "baseline_execution_row_id": baseline["execution_row_id"],
                "candidate_execution_row_id": candidate["execution_row_id"],
                "baseline_checkpoint": str(subject_registry["baseline"]["checkpoint_path"]),
                "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
                "baseline_checkpoint_hash": subject_registry["baseline"]["checkpoint_hash"],
                "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
                "baseline_execution_status": baseline.get("execution_status", ""),
                "candidate_execution_status": candidate.get("execution_status", ""),
                "baseline_steps": baseline.get("steps", ""),
                "candidate_steps": candidate.get("steps", ""),
                "baseline_success_diagnostic": _bool(baseline.get("success", False)),
                "candidate_success_diagnostic": _bool(candidate.get("success", False)),
                "baseline_collision_diagnostic": _bool(baseline.get("collision", False)),
                "candidate_collision_diagnostic": _bool(candidate.get("collision", False)),
                "termination_pair_changed": str(baseline.get("termination_reason", "")) != str(
                    candidate.get("termination_reason", "")
                ),
                "collision_pair_changed": _bool(baseline.get("collision", False))
                != _bool(candidate.get("collision", False)),
                **delta_values,
                "paired_execution_complete": bool(
                    baseline.get("execution_status") == "completed"
                    and candidate.get("execution_status") == "completed"
                ),
                "finite_delta": bool(all(np.isfinite(float(value)) for value in delta_values.values())),
                "ordinary_success_denominator_allowed": False,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "success_rate_verdict_computed": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_surface_delta_rows(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in delta_rows:
        by_surface[str(row.get("surface_id", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for surface_id in sorted(by_surface):
        group = by_surface[surface_id]
        first = group[0]
        metric_means = {f"mean_{key}": _mean_finite(row.get(key, "") for row in group) for key in DELTA_METRIC_KEYS}
        rows.append(
            {
                "surface_id": surface_id,
                "surface_role": first.get("surface_role", ""),
                "source_from": first.get("source_from", ""),
                "public_diagnostic_row": first.get("public_diagnostic_row", False),
                "fresh_or_disjoint": first.get("fresh_or_disjoint", False),
                "paired_delta_row_count": len(group),
                "complete_pair_count": sum(1 for row in group if _bool(row.get("paired_execution_complete", False))),
                "finite_delta_count": sum(1 for row in group if _bool(row.get("finite_delta", False))),
                "termination_pair_changed_count": sum(1 for row in group if _bool(row.get("termination_pair_changed", False))),
                "collision_pair_changed_count": sum(1 for row in group if _bool(row.get("collision_pair_changed", False))),
                **metric_means,
                "ordinary_success_denominator_allowed": False,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "success_rate_verdict_computed": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    execution_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        ("p0_observation_dim", P0_OBSERVATION_DIM, 72),
        ("action_dim", ACTION_DIM, 3),
        ("baseline_model_obs_dim", getattr(subject_registry["baseline"]["model"], "obs_dim", -1), 72),
        ("candidate_model_obs_dim", getattr(subject_registry["candidate"]["model"], "obs_dim", -1), 72),
        ("baseline_model_action_dim", getattr(subject_registry["baseline"]["model"], "act_dim", -1), 3),
        ("candidate_model_action_dim", getattr(subject_registry["candidate"]["model"], "act_dim", -1), 3),
        ("execution_observation_shape", {int(row.get("observation_shape", -1)) for row in execution_rows}, {P0_OBSERVATION_DIM}),
        ("execution_action_shape", {int(row.get("action_shape", -1)) for row in execution_rows}, {ACTION_DIM}),
        ("actor_input_contract_changed", any_flag(execution_rows, "actor_input_contract_changed"), False),
        ("hidden_oracle_actor_input_required", any_flag(execution_rows, "hidden_oracle_actor_input_required"), False),
        ("actor_visible_label", any_flag(execution_rows, "actor_visible_label"), False),
        ("source_labels_actor_visible", any_flag(execution_rows, "source_labels_actor_visible"), False),
        ("stress_axis_labels_actor_visible", any_flag(execution_rows, "stress_axis_labels_actor_visible"), False),
        ("scenario_role_labels_actor_visible", any_flag(execution_rows, "scenario_role_labels_actor_visible"), False),
        ("outcome_labels_actor_visible", any_flag(execution_rows, "outcome_labels_actor_visible"), False),
        ("route_labels_actor_visible", any_flag(execution_rows, "route_labels_actor_visible"), False),
        ("verdict_labels_actor_visible", any_flag(execution_rows, "verdict_labels_actor_visible"), False),
    ]
    return [
        {
            "guard_id": f"m2868-actor-guard-{name}",
            "guard_family": name,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, observed, expected in checks
    ]


def build_claim_boundary_rows(
    *,
    paired_execution_rows: list[dict[str, Any]],
    paired_delta_rows: list[dict[str, Any]],
    surface_delta_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    specs = [
        ("paired_closed_loop_diagnostic_artifacts", "artifact", True, bool(paired_execution_rows and paired_delta_rows), "paired execution and delta rows"),
        ("surface_delta_artifacts", "artifact", True, bool(surface_delta_rows), "surface-separated delta rows"),
        ("required_artifact_completeness", "artifact", True, required_artifacts_present, "M2868 required artifact set"),
        ("follow_up_result_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2869 result-audit manifest"),
        ("validation_result", "validation", False, False, "future validation gate"),
        ("ranking_result", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("repair_success", "repair", False, False, "future audited repair route"),
        ("driver_performance", "performance", False, False, "future validation route"),
        ("paper_result", "paper", False, False, "Route B proof/generalization gates"),
        ("finite_window_vs_gru_conclusion", "paper", False, False, "Route B controller-family comparison"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C validation route"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim_row(*spec) for spec in specs]


def claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2868-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2868": allowed,
        "claim_made": made,
        "status_pass": made == allowed if allowed else not made,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_proof_retention_gate_rows(
    *,
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    surface_delta_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    expected_execution_rows = len(selected_rows) * len(CHECKPOINT_SUBJECTS)
    m2866_summary = source["m2866_summary"]
    m2866_manifest = source["m2866_checkpoint_manifest"]
    m2866_actor_guard_rows = source["m2866_actor_guard_rows"]
    m2866_actor_contract_observed = m2866_actor_contract_evidence(
        m2866_summary=m2866_summary,
        m2866_manifest=m2866_manifest,
        m2866_actor_guard_rows=m2866_actor_guard_rows,
    )
    return [
        gate("proof_source_artifacts_present", "proof", "lineage", all(source["source_exists"].values()), source["source_exists"], "M1690 specs M2867 M2866 M2857 and checkpoint artifacts present", len(source["source_exists"]), "lineage_invalid"),
        gate("proof_m2867_accepts_m2866_route", "proof", "lineage", "accept_m2866_route_to_m2868_closed_loop_delta_panel" in source["m2867_audit_text"], "M2867 route acceptance text", "accept_m2866_route_to_m2868_closed_loop_delta_panel", 1, "lineage_invalid"),
        gate("proof_m2866_status_pass", "proof", "lineage", bool(m2866_summary.get("status_pass", False)) and bool(m2866_summary.get("gate_matrix_pass", False)), {"status_pass": m2866_summary.get("status_pass", False), "gate_matrix_pass": m2866_summary.get("gate_matrix_pass", False)}, "M2866 status and gate matrix pass", 1, "lineage_invalid"),
        gate("proof_m2866_candidate_checkpoint_written", "proof", "lineage", bool(m2866_summary.get("candidate_checkpoint_written", False)), m2866_summary.get("candidate_checkpoint_written", False), True, 1, "lineage_invalid"),
        gate("proof_m2866_actor_contract", "proof", "contract", bool(m2866_actor_contract_observed["status_pass"]), m2866_actor_contract_observed, "actor 72/action 3 with no hidden/oracle input", len(m2866_actor_guard_rows) or 1, "contract_violation"),
        gate("proof_checkpoint_lineage_hashes", "proof", "lineage", bool(subject_registry["baseline"]["checkpoint_hash"]) and bool(subject_registry["candidate"]["checkpoint_hash"]) and subject_registry["baseline"]["checkpoint_hash"] != subject_registry["candidate"]["checkpoint_hash"], "baseline and candidate hashes", "non-empty distinct hashes", 2, "lineage_invalid"),
        gate("proof_m2857_surface_rows_present", "proof", "artifact", len(source["m2857_surface_rows"]) >= len(selected_rows) and len(selected_rows) > 0, len(source["m2857_surface_rows"]), f">={len(selected_rows)}", len(source["m2857_surface_rows"]), "metric_artifact"),
        gate("proof_paired_execution_row_count", "proof", "artifact", len(execution_rows) == expected_execution_rows, len(execution_rows), expected_execution_rows, len(execution_rows), "metric_artifact"),
        gate("proof_paired_delta_row_count", "proof", "artifact", len(delta_rows) == len(selected_rows), len(delta_rows), len(selected_rows), len(delta_rows), "metric_artifact"),
        gate("proof_surface_delta_rows_present", "proof", "artifact", bool(surface_delta_rows) and {row["surface_id"] for row in surface_delta_rows} == {"fresh_disjoint", "m2850_explanatory"}, sorted(row["surface_id"] for row in surface_delta_rows), "fresh_disjoint and m2850_explanatory", len(surface_delta_rows), "metric_artifact"),
        gate("proof_all_executions_completed", "proof", "execution", bool(execution_rows) and all(str(row.get("execution_status", "")) == "completed" for row in execution_rows), Counter(str(row.get("execution_status", "")) for row in execution_rows), "all completed", len(execution_rows), "metric_artifact"),
        gate("proof_pair_completeness", "proof", "artifact", bool(delta_rows) and all(_bool(row["paired_execution_complete"]) for row in delta_rows), "all pairs complete", "all pairs complete", len(delta_rows), "metric_artifact"),
        gate("proof_actor_contract_guards_pass", "proof", "contract", bool(actor_guard_rows) and all(_bool(row["status_pass"]) for row in actor_guard_rows), "all actor guards pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all actor guards pass", len(actor_guard_rows), "contract_violation"),
        gate("proof_no_actor_visible_labels", "proof", "contract", not any_actor_visible_label(execution_rows), False, False, len(execution_rows), "contract_violation"),
        gate("proof_no_hidden_or_oracle_actor_input", "proof", "contract", not any_flag(execution_rows, "hidden_oracle_actor_input_required"), False, False, len(execution_rows), "contract_violation"),
        gate("proof_no_ordinary_denominator", "proof", "proof_washout", not any_flag(execution_rows + delta_rows + surface_delta_rows, "ordinary_success_denominator_allowed"), False, False, len(execution_rows) + len(delta_rows) + len(surface_delta_rows), "proof_washout"),
        gate("proof_claim_boundary_rows_pass", "proof", "claim", bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all claim rows pass", len(claim_rows), "proof_washout"),
        gate("proof_no_ranking_winner_success_verdict", "proof", "claim", not any_flag(execution_rows + delta_rows + surface_delta_rows, "ranking_admissible") and not any_flag(execution_rows + delta_rows + surface_delta_rows, "winner_selected") and not any_flag(execution_rows + delta_rows + surface_delta_rows, "success_rate_verdict_computed"), False, False, len(execution_rows) + len(delta_rows) + len(surface_delta_rows), "objective_overfit"),
        gate("proof_required_artifacts_present", "proof", "artifact", required_artifacts_present, required_artifacts_present, True, len(REQUIRED_ARTIFACT_KEYS), "lineage_invalid"),
    ]


def build_generalization_delta_gate_rows(
    *,
    selected_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    surface_delta_rows: list[dict[str, Any]],
    row_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    surface_counts = Counter(str(row.get("surface_id", "")) for row in selected_rows)
    return [
        gate("generalization_requested_row_count", "generalization", "scenario_sampling", len(selected_rows) == int(row_count), len(selected_rows), int(row_count), len(selected_rows), "scenario_sampling_failure"),
        gate("generalization_not_single_row_panel", "generalization", "seed_split", int(row_count) >= 2, int(row_count), ">=2", int(row_count), "seed_fragility"),
        gate("generalization_unique_task_sources", "generalization", "scenario_sampling", len({row["task_source_id"] for row in selected_rows}) == len(selected_rows), len({row["task_source_id"] for row in selected_rows}), len(selected_rows), len(selected_rows), "scenario_sampling_failure"),
        gate("generalization_l3_profile_only", "generalization", "contract", {row["profile_name"] for row in selected_rows} == {CANONICAL_PROFILE}, sorted({row["profile_name"] for row in selected_rows}), CANONICAL_PROFILE, len(selected_rows), "contract_violation"),
        gate("generalization_surface_separation", "generalization", "surface_accounting", set(surface_counts) == {"fresh_disjoint", "m2850_explanatory"}, dict(sorted(surface_counts.items())), "fresh_disjoint and m2850_explanatory", len(selected_rows), "proof_washout"),
        gate("generalization_subject_coverage", "generalization", "artifact", {row["checkpoint_subject"] for row in execution_rows} == set(CHECKPOINT_SUBJECTS), sorted({row["checkpoint_subject"] for row in execution_rows}), sorted(CHECKPOINT_SUBJECTS), len(execution_rows), "metric_artifact"),
        gate("generalization_eval_seed_pairing", "generalization", "seed_split", paired_eval_seed_consistency(execution_rows), "same seed per baseline/candidate pair", "same seed per baseline/candidate pair", len(execution_rows), "seed_fragility"),
        gate("generalization_horizon_applied", "generalization", "execution", {int(row.get("horizon_steps", -1)) for row in execution_rows} == {int(horizon_steps)} and {int(row.get("env_max_steps_applied", -1)) for row in execution_rows} == {int(horizon_steps)}, sorted({row.get("horizon_steps", "") for row in execution_rows}), int(horizon_steps), len(execution_rows), "metric_artifact"),
        gate("generalization_finite_delta_rows", "generalization", "metric", bool(delta_rows) and all(_bool(row["finite_delta"]) for row in delta_rows), "finite", "finite", len(delta_rows), "metric_artifact"),
        gate("generalization_surface_delta_counts_match_pairs", "generalization", "surface_accounting", sum(int(row.get("paired_delta_row_count", 0)) for row in surface_delta_rows) == len(delta_rows), sum(int(row.get("paired_delta_row_count", 0)) for row in surface_delta_rows), len(delta_rows), len(surface_delta_rows), "metric_artifact"),
        gate("generalization_no_surface_ranking_or_denominator", "generalization", "proof_washout", not any_flag(delta_rows + surface_delta_rows, "ranking_admissible") and not any_flag(delta_rows + surface_delta_rows, "ordinary_success_denominator_allowed"), False, False, len(delta_rows) + len(surface_delta_rows), "proof_washout"),
    ]


def build_promotion_guard_rows(
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    surface_delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = execution_rows + delta_rows + surface_delta_rows
    return [
        gate("promotion_checkpoint_not_promoted", "promotion", "promotion_guard", not any_flag(execution_rows, "checkpoint_promoted"), False, False, len(execution_rows), "promotion_gate_failure"),
        gate("promotion_no_winner_selected", "promotion", "promotion_guard", not any_flag(rows, "winner_selected"), False, False, len(rows), "promotion_gate_failure"),
        gate("promotion_no_success_rate_verdict", "promotion", "promotion_guard", not any_flag(rows, "success_rate_verdict_computed"), False, False, len(rows), "metric_artifact"),
        gate("promotion_no_active_config_overwrite", "promotion", "promotion_guard", not any_flag(execution_rows, "active_config_overwritten"), False, False, len(execution_rows), "contract_violation"),
    ]


def gate(
    gate_id: str,
    tier: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2868-gate-{gate_id}",
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "row_count": int(row_count),
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    surface_delta_rows: list[dict[str, Any]],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    eval_seed_base: int,
    row_count: int,
    horizon_steps: int,
    device: str,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_contract_pass = bool(actor_guard_rows) and all(_bool(row["status_pass"]) for row in actor_guard_rows)
    claim_boundary_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    paired_rows_complete = bool(delta_rows) and all(_bool(row["paired_execution_complete"]) for row in delta_rows)
    surface_counts = Counter(str(row.get("surface_id", "")) for row in selected_rows)
    forbidden_claims_made = any_forbidden_claim(execution_rows + delta_rows + surface_delta_rows)
    execution_status_counts = Counter(str(row.get("execution_status", "")) for row in execution_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_pass
        and claim_boundary_pass
        and paired_rows_complete
        and required_artifacts_present
        and not forbidden_claims_made
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel_pass"
            if status_pass
            else "engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel_fail"
        ),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "m1690_workload": str(source["paths"]["m1690_workload"]),
        "executable_specs": str(source["paths"]["executable_specs"]),
        "m2867_audit": str(source["paths"]["m2867_audit"]),
        "m2866_summary": str(source["paths"]["m2866_summary"]),
        "m2866_checkpoint_manifest": str(source["m2866_summary"].get("checkpoint_manifest", "")),
        "m2866_actor_contract_guard_rows": str(source["m2866_summary"].get("actor_contract_guard_rows", "")),
        "m2857_surface_rows": str(source["paths"]["m2857_surface_rows"]),
        "m2866_status_pass": bool(source["m2866_summary"].get("status_pass", False)),
        "m2866_gate_matrix_pass": bool(source["m2866_summary"].get("gate_matrix_pass", False)),
        "m2866_actor_contract_evidence": m2866_actor_contract_evidence(
            m2866_summary=source["m2866_summary"],
            m2866_manifest=source["m2866_checkpoint_manifest"],
            m2866_actor_guard_rows=source["m2866_actor_guard_rows"],
        ),
        "m2866_response_prediction_loss_mean": source["m2866_summary"].get("response_prediction_loss_mean", ""),
        "m2866_candidate_checkpoint_written": bool(source["m2866_summary"].get("candidate_checkpoint_written", False)),
        "baseline_checkpoint": str(subject_registry["baseline"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "baseline_checkpoint_hash": subject_registry["baseline"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "baseline_model_state_hash": subject_registry["baseline"]["model_state_hash"],
        "candidate_model_state_hash": subject_registry["candidate"]["model_state_hash"],
        "paired_execution_rows": str(paths["paired_execution_rows"]),
        "paired_delta_rows": str(paths["paired_delta_rows"]),
        "surface_delta_rows": str(paths["surface_delta_rows"]),
        "proof_retention_gate_rows": str(paths["proof_retention_gate_rows"]),
        "generalization_delta_gate_rows": str(paths["generalization_delta_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "required_artifacts_present": required_artifacts_present,
        "selected_pair_count": len(selected_rows),
        "requested_row_count": int(row_count),
        "surface_counts": dict(sorted(surface_counts.items())),
        "selected_task_source_ids": [row["task_source_id"] for row in selected_rows],
        "paired_execution_row_count": len(execution_rows),
        "paired_delta_row_count": len(delta_rows),
        "surface_delta_row_count": len(surface_delta_rows),
        "execution_status_counts": dict(sorted(execution_status_counts.items())),
        "diagnostic_success_count": sum(1 for row in execution_rows if _bool(row.get("success", False))),
        "diagnostic_collision_count": sum(1 for row in execution_rows if _bool(row.get("collision", False))),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not _bool(row["status_pass"])],
        "actor_contract_guard_rows_pass": actor_contract_pass,
        "claim_boundary_rows_pass": claim_boundary_pass,
        "actor_contract_shape_72_action_3": actor_contract_pass,
        "hidden_oracle_actor_input_required": any_flag(execution_rows, "hidden_oracle_actor_input_required"),
        "actor_visible_labels_detected": any_actor_visible_label(execution_rows),
        "paired_rows_complete": paired_rows_complete,
        "finite_delta_rows": bool(delta_rows) and all(_bool(row["finite_delta"]) for row in delta_rows),
        "ordinary_success_denominator_allowed": any_flag(execution_rows + delta_rows + surface_delta_rows, "ordinary_success_denominator_allowed"),
        "forbidden_claims_made": forbidden_claims_made,
        "source_exists": source["source_exists"],
        "eval_seed_base": int(eval_seed_base),
        "horizon_steps": int(horizon_steps),
        "device": device,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_run_state(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "paired_panel_count": summary["selected_pair_count"],
        "paired_execution_row_count": summary["paired_execution_row_count"],
        "paired_delta_row_count": summary["paired_delta_row_count"],
        "surface_delta_row_count": summary["surface_delta_row_count"],
        "complete": summary["paired_rows_complete"],
        "next_blocker": summary["next_blocker"],
    }


def build_m2869_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    doc_path = f"docs/{task_id}.md"
    return {
        "id": task_id,
        "type": "gate",
        "gate_tier": "proof",
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
            "parent_checkpoint": [summary["baseline_checkpoint"], summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["paired_execution_rows"],
                summary["paired_delta_rows"],
                summary["surface_delta_rows"],
                summary["proof_retention_gate_rows"],
                summary["generalization_delta_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
                summary["m2867_audit"],
                summary["m2866_summary"],
                summary["m2857_surface_rows"],
            ],
            "parent_config": [
                "experiments/manifests/m2868-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-candidate-closed-loop-delta-panel-preflight.json",
                "experiments/manifests/m2867-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-result-audit.json",
            ],
            "parent_objective": [
                "audit M2868 paired M2848-source versus M2866-candidate closed-loop delta artifacts before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2869 must audit paired execution/delta completeness before any interpretation",
                "M2869 must preserve M2850 explanatory and fresh/disjoint surface separation",
                "M2869 must reject ranking winner promotion success-rate verdict validation performance paper current-sim high-fidelity full-driver and self-ID claims",
            ],
            "supersedes": ["unaudited M2868 localized response-prediction candidate closed-loop delta interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2869 must audit whether M2868 wrote complete paired baseline/candidate execution rows and paired delta rows",
            "M2869 must verify surface delta rows keep M2850 explanatory and fresh/disjoint rows separate",
            "M2869 must verify actor 72/action 3 no hidden/oracle actor input and no actor-visible labels",
            "M2869 must verify proof generalization promotion actor claim and gate rows pass",
            "M2869 must not validate rank promote select a winner compute success-rate verdict or claim performance paper current-sim high-fidelity full-driver or self-ID result",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not run validation",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not collapse M2850 explanatory and fresh/disjoint surfaces",
            "do not change actor inputs or inject hidden/oracle actor features",
            "do not claim repair success driver performance validation readiness/result paper finite-window-vs-GRU current-sim high-fidelity full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "localized_response_prediction_candidate_closed_loop_delta_panel_result_audit",
            "evidence_increment": "audits M2868 paired source-vs-candidate diagnostic deltas with surface separation",
            "claim_scope": "Result audit only; no validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity validation self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2868 paired rows are incomplete",
                "stop if actor-visible label exclusion failed",
                "stop if M2868 collapsed M2850 explanatory and fresh/disjoint surfaces",
                "stop if M2868 deltas are used as a ranking or winner verdict",
            ],
            "fallback_plan": [
                "route to artifact repair only for narrow lineage or schema failure",
                "route to branch synthesis if paired deltas are negative or claim boundaries fail",
                "route to bounded follow-up training design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2868 has produced paired closed-loop diagnostic delta artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2868 paired M2848-source versus M2866-candidate diagnostic delta artifacts",
            "admission_evidence": [
                "M2868 summary and gate rows are expected before M2869 runs",
                "M2868 paired execution delta and surface delta rows require audit before interpretation",
            ],
            "blocked_shortcuts": [
                "no new training or validation in result audit",
                "no ranking winner selection promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                doc_path,
                "M2869 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2868 paired row completeness surface separation and gate rows are accepted or rejected",
                "failure types are classified if any gate failed",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2869 audits diagnostic deltas only and does not run finite-window-vs-GRU or self-ID tests.",
            "history_necessity_tests": [
                "M2868 paired recurrent-belief deltas are not level3 self-identification evidence."
            ],
            "temporal_evidence_window": "M2866-M2868 localized response-prediction branch.",
            "negative_result_policy": "If M2868 deltas are negative or gates fail, preserve the result and route to synthesis rather than weakening gates.",
            "allowed_claims": [
                "M2868 paired closed-loop delta panel accepted or rejected",
                "bounded follow-up route registration",
                "no driver-performance verdict paper result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new M2868 paired closed-loop diagnostic data",
            "paper_verdict_delta": "no paper verdict; audit governs Route A engineering controller evidence interpretation",
            "must_synthesize_if": [
                "M2868 cannot produce complete paired source/candidate closed-loop artifacts",
                "M2868 exposes labels or hidden/oracle inputs to actor input",
                "M2868 collapses public and fresh/disjoint surfaces",
                "M2868 results are used as validation performance self-ID or paper evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2868 paired closed-loop delta artifacts before any interpretation.",
        "success_criteria": [
            f"{doc_path} exists",
            "audit checks M2868 summary paired execution rows paired delta rows surface delta rows proof generalization promotion actor claim and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels surface separation and claim boundary",
            "audit registers one bounded follow-up route if continuing",
        ],
        "failure_criteria": [
            "M2869 runs new training validation ranking promotion or success-rate verdict computation",
            "M2869 hides M2868 gate failures or weakens actor surface or claim boundaries",
            "M2869 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2869 audits M2868 artifacts under unchanged actor surface and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": doc_path, "type": "md"}],
        "baseline_checkpoints": [summary["baseline_checkpoint"], summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["paired_execution_rows"], summary["paired_delta_rows"], summary["surface_delta_rows"]],
        "scoreboard_checkpoint": doc_path,
        "next_blocker": "",
    }


def write_follow_up_manifest(path: Path, manifest: dict[str, Any]) -> None:
    write_json(path, manifest)


def m2866_actor_contract_evidence(
    *,
    m2866_summary: Mapping[str, Any],
    m2866_manifest: Mapping[str, Any],
    m2866_actor_guard_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    summary_contract = _bool(m2866_summary.get("actor_contract_shape_72_action_3", False))
    manifest_contract = _bool(m2866_manifest.get("actor_contract_shape_72_action_3", False))
    guard_rows_pass = bool(m2866_actor_guard_rows) and all(
        _bool(row.get("status_pass", False)) for row in m2866_actor_guard_rows
    )
    hidden_or_oracle = _bool(m2866_summary.get("hidden_oracle_actor_input_required", False)) or _bool(
        m2866_manifest.get("hidden_or_oracle_actor_inputs_required", False)
    )
    actor_visible_labels = _bool(m2866_summary.get("actor_visible_labels", False)) or _bool(
        m2866_manifest.get("actor_visible_labels", False)
    )
    return {
        "status_pass": (summary_contract or manifest_contract or guard_rows_pass)
        and not hidden_or_oracle
        and not actor_visible_labels,
        "summary_actor_contract_shape_72_action_3": m2866_summary.get("actor_contract_shape_72_action_3", ""),
        "manifest_actor_contract_shape_72_action_3": m2866_manifest.get("actor_contract_shape_72_action_3", ""),
        "actor_guard_rows_pass": guard_rows_pass,
        "actor_guard_row_count": len(m2866_actor_guard_rows),
        "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
        "actor_visible_labels": actor_visible_labels,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2868 Engineering Controller Route A Localized Response-Prediction Candidate Closed-Loop Delta Panel Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- paired panel rows: {summary['selected_pair_count']}",
            f"- surface counts: {summary['surface_counts']}",
            f"- paired execution rows: {summary['paired_execution_row_count']}",
            f"- paired delta rows: {summary['paired_delta_row_count']}",
            f"- surface delta rows: {summary['surface_delta_row_count']}",
            f"- execution status counts: {summary['execution_status_counts']}",
            f"- diagnostic outcomes across subjects: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']}",
            f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- failed gates: {summary['failed_gate_ids'] or 'none'}",
            f"- actor contract guards pass: {summary['actor_contract_guard_rows_pass']}",
            f"- claim boundary rows pass: {summary['claim_boundary_rows_pass']}",
            f"- required artifacts present: {summary['required_artifacts_present']}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next blocker: `{summary['next_blocker']}`",
            "",
            "## Route Boundary",
            "",
            "M2868 follows the post-M2470 Route A split: it produces bounded engineering-controller",
            "diagnostic closed-loop data without turning row or surface deltas into validation,",
            "ranking, promotion, paper, current-sim, high-fidelity, full-driver, or self-ID claims.",
            "",
            "## M2866 Lineage",
            "",
            "```text",
            f"M2866 status pass: {summary['m2866_status_pass']}",
            f"M2866 gate matrix pass: {summary['m2866_gate_matrix_pass']}",
            f"M2866 candidate checkpoint written: {summary['m2866_candidate_checkpoint_written']}",
            f"M2866 response prediction loss mean: {summary['m2866_response_prediction_loss_mean']}",
            "```",
            "",
            "## Surface Separation",
            "",
            "```text",
            f"surface counts: {summary['surface_counts']}",
            f"ordinary denominator allowed: {summary['ordinary_success_denominator_allowed']}",
            "```",
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


def _delta(left: Mapping[str, Any], right: Mapping[str, Any], key: str) -> float:
    return _float(left.get(key, float("nan"))) - _float(right.get(key, float("nan")))


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _read_optional_json(path_value: Any) -> dict[str, Any]:
    path = Path(str(path_value)) if path_value else Path()
    if not path_value or not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _read_optional_csv(path_value: Any) -> list[dict[str, str]]:
    path = Path(str(path_value)) if path_value else Path()
    if not path_value or not path.exists():
        return []
    return read_csv_rows(path)


def _mean_finite(values: Any) -> float | str:
    finite = [_float(value) for value in values if np.isfinite(_float(value))]
    return float(np.mean(finite)) if finite else ""


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def any_actor_visible_label(rows: list[Mapping[str, Any]]) -> bool:
    keys = (
        "actor_visible_label",
        "source_labels_actor_visible",
        "stress_axis_labels_actor_visible",
        "scenario_role_labels_actor_visible",
        "outcome_labels_actor_visible",
        "route_labels_actor_visible",
        "verdict_labels_actor_visible",
    )
    return any(any(_bool(row.get(key, False)) for key in keys) for row in rows)


def any_forbidden_claim(rows: list[Mapping[str, Any]]) -> bool:
    keys = (
        "ranking_admissible",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_computed",
        "driver_performance_claim_made",
        "validation_readiness_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
    )
    return any(any(_bool(row.get(key, False)) for key in keys) for row in rows)


def paired_eval_seed_consistency(rows: list[Mapping[str, Any]]) -> bool:
    by_pair: dict[str, set[int]] = {}
    subjects_by_pair: dict[str, set[str]] = {}
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        by_pair.setdefault(pair_id, set()).add(int(row.get("eval_seed", -1)))
        subjects_by_pair.setdefault(pair_id, set()).add(str(row.get("checkpoint_subject", "")))
    return bool(by_pair) and all(len(seeds) == 1 for seeds in by_pair.values()) and all(
        subjects == set(CHECKPOINT_SUBJECTS) for subjects in subjects_by_pair.values()
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--m2867-audit", type=Path, default=DEFAULT_M2867_AUDIT)
    parser.add_argument("--m2866-summary", type=Path, default=DEFAULT_M2866_SUMMARY)
    parser.add_argument("--m2857-surface-rows", type=Path, default=DEFAULT_M2857_SURFACE_ROWS)
    parser.add_argument("--baseline-checkpoint", type=Path, default=DEFAULT_BASELINE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_localized_response_prediction_candidate_closed_loop_delta_panel(
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        m2867_audit=args.m2867_audit,
        m2866_summary=args.m2866_summary,
        m2857_surface_rows=args.m2857_surface_rows,
        baseline_checkpoint=args.baseline_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        row_count=args.row_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
    )
    print(
        "M2868 localized response-prediction candidate closed-loop delta panel: "
        f"status={summary['status_pass']} "
        f"pairs={summary['selected_pair_count']} "
        f"executions={summary['paired_execution_row_count']} "
        f"deltas={summary['paired_delta_row_count']} "
        f"surfaces={summary['surface_delta_row_count']} "
        f"next={summary['next_blocker']}"
    )


if __name__ == "__main__":
    main()
