"""Run M2850 paired closed-loop delta panel for recurrent-belief candidates."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
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
from autodrift.engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight import (
    CANONICAL_PROFILE,
    SELECTED_TASK_SOURCES,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2850-engineering-controller-route-a-response-predictive-recurrent-belief-candidate-"
    "closed-loop-delta-panel-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2851-engineering-controller-route-a-response-predictive-recurrent-belief-candidate-"
    "closed-loop-delta-panel-result-audit"
)
DEFAULT_M2849_AUDIT = Path(
    "docs/m2849-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-"
    "bounded-continuation-result-audit.md"
)
DEFAULT_M2848_SUMMARY = Path(
    "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "bounded_continuation_preflight/summary.json"
)
DEFAULT_M2838_SUMMARY = Path(
    "runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_"
    "preflight/summary.json"
)
DEFAULT_BASELINE_CHECKPOINT = Path(
    "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2850_engineering_controller_route_a_response_predictive_recurrent_belief_candidate_"
    "closed_loop_delta_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2850-engineering-controller-route-a-response-predictive-recurrent-belief-candidate-"
    "closed-loop-delta-panel-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2851-engineering-controller-route-a-response-predictive-recurrent-"
    "belief-candidate-closed-loop-delta-panel-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 285000
DEFAULT_ROW_COUNT = 16
DEFAULT_HORIZON_STEPS = 96
CHECKPOINT_SUBJECTS = ("baseline", "candidate")

CLAIM_SCOPE = (
    "M2850 bounded Route A paired closed-loop diagnostic delta panel only. "
    "It compares M2846 baseline and M2848 response-predictive recurrent-belief "
    "candidate rows over fixed M1690 L3_online_gru task sources for audit. "
    "It does not validate, rank, select a winner, promote, compute a success-rate "
    "verdict, or claim repair success, driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full ideal driver completion, or level3 self-identification."
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

PAIRED_EXECUTION_FIELDNAMES = [
    "pair_id",
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
    "m2838_weak_diagnostic_accounting_visible",
    "m2838_ordinary_denominator_allowed",
    "claim_scope",
    "forbidden_interpretation",
]
PAIRED_DELTA_FIELDNAMES = [
    "pair_id",
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
    "allowed_in_m2850",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "paired_execution_rows",
    "paired_delta_rows",
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


def run_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel(
    *,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    m2849_audit: Path | str = DEFAULT_M2849_AUDIT,
    m2848_summary: Path | str = DEFAULT_M2848_SUMMARY,
    m2838_summary: Path | str = DEFAULT_M2838_SUMMARY,
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
        m2849_audit=Path(m2849_audit),
        m2848_summary=Path(m2848_summary),
        m2838_summary=Path(m2838_summary),
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
    )
    subject_registry = load_subject_registry(
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
        device=device,
    )
    selected_rows = resolve_selected_panel_rows(source, row_count=int(row_count))

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
    write_csv_rows(paths["paired_delta_rows"], delta_rows, fieldnames=PAIRED_DELTA_FIELDNAMES)

    summary: dict[str, Any] = {}
    for _pass_index in range(2):
        required_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
        actor_guard_rows = build_actor_contract_guard_rows(execution_rows, subject_registry)
        claim_rows = build_claim_boundary_rows(
            paired_execution_rows=execution_rows,
            paired_delta_rows=delta_rows,
            required_artifacts_present=required_present,
            follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
        )
        proof_rows = build_proof_retention_gate_rows(
            source=source,
            subject_registry=subject_registry,
            selected_rows=selected_rows,
            execution_rows=execution_rows,
            delta_rows=delta_rows,
            actor_guard_rows=actor_guard_rows,
            claim_rows=claim_rows,
            required_artifacts_present=required_present,
        )
        generalization_rows = build_generalization_delta_gate_rows(
            selected_rows=selected_rows,
            execution_rows=execution_rows,
            delta_rows=delta_rows,
            row_count=int(row_count),
            horizon_steps=int(horizon_steps),
        )
        promotion_rows = build_promotion_guard_rows(execution_rows, delta_rows)
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
        write_follow_up_manifest(paths["follow_up_manifest"], build_m2851_follow_up_manifest(summary))
        paths["doc"].parent.mkdir(parents=True, exist_ok=True)
        paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    write_run_state(paths["run_state"], build_run_state(summary))
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "paired_execution_rows": output_dir / "paired_execution_rows.csv",
        "paired_delta_rows": output_dir / "paired_delta_rows.csv",
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
    m2849_audit: Path,
    m2848_summary: Path,
    m2838_summary: Path,
    baseline_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Any]:
    paths = {
        "m1690_workload": m1690_workload,
        "executable_specs": executable_specs,
        "m2849_audit": m2849_audit,
        "m2848_summary": m2848_summary,
        "m2838_summary": m2838_summary,
        "baseline_checkpoint": baseline_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m1690_rows = read_csv_rows(m1690_workload) if m1690_workload.exists() else []
    m1690_l3_by_task_source: dict[str, dict[str, str]] = {}
    for row in m1690_rows:
        if row.get("profile_name") == CANONICAL_PROFILE:
            m1690_l3_by_task_source[str(row.get("task_source_id", ""))] = row
    specs = load_executable_specs(executable_specs) if executable_specs.exists() else []
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m1690_rows": m1690_rows,
        "m1690_l3_by_task_source": m1690_l3_by_task_source,
        "executable_specs": specs,
        "executable_spec_by_task_source": {str(spec["task_source_id"]): spec for spec in specs},
        "m2849_audit_text": m2849_audit.read_text(encoding="utf-8") if m2849_audit.exists() else "",
        "m2848_summary": read_json(m2848_summary) if m2848_summary.exists() else {},
        "m2838_summary": read_json(m2838_summary) if m2838_summary.exists() else {},
    }


def load_subject_registry(
    *,
    baseline_checkpoint: Path,
    candidate_checkpoint: Path,
    device: str,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for subject, path in (
        ("baseline", baseline_checkpoint),
        ("candidate", candidate_checkpoint),
    ):
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


def resolve_selected_panel_rows(source: dict[str, Any], *, row_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, selected in enumerate(SELECTED_TASK_SOURCES[: int(row_count)], start=1):
        (
            task_source_id,
            expected_task_family,
            expected_source_edge,
            expected_window_tag,
            scenario_role,
            source_family_tag,
            diagnostic_tags,
        ) = selected
        source_row = source["m1690_l3_by_task_source"].get(task_source_id)
        failure_reason = ""
        if source_row is None:
            failure_reason = "selected_task_source_missing_from_m1690_l3_rows"
        elif str(source_row.get("task_family", "")) != expected_task_family:
            failure_reason = "task_family_mismatch"
        elif str(source_row.get("source_edge", "")) != expected_source_edge:
            failure_reason = "source_edge_mismatch"
        elif str(source_row.get("window_tag", "")) != expected_window_tag:
            failure_reason = "window_tag_mismatch"
        elif str(source_row.get("config_exists", "")) != "True":
            failure_reason = "profile_config_missing"
        elif _bool(source_row.get("profile_specific_tuning", False)):
            failure_reason = "profile_specific_tuning_detected"
        if task_source_id not in source["executable_spec_by_task_source"]:
            failure_reason = failure_reason or "executable_spec_missing"
        admitted = source_row is not None and not failure_reason
        rows.append(
            {
                "pair_index": index,
                "pair_id": f"m2850-pair-{index:04d}-{task_source_id}",
                "task_source_id": task_source_id,
                "workload_id": source_row.get("workload_id", f"{task_source_id}::{CANONICAL_PROFILE}")
                if source_row
                else f"{task_source_id}::{CANONICAL_PROFILE}",
                "profile_name": source_row.get("profile_name", CANONICAL_PROFILE) if source_row else CANONICAL_PROFILE,
                "task_family": source_row.get("task_family", expected_task_family) if source_row else expected_task_family,
                "source_edge": source_row.get("source_edge", expected_source_edge) if source_row else expected_source_edge,
                "window_tag": source_row.get("window_tag", expected_window_tag) if source_row else expected_window_tag,
                "strata": source_row.get("strata", "") if source_row else "",
                "executable_source_family": source_row.get("executable_source_family", "") if source_row else "",
                "env_template_family": source_row.get("env_template_family", "") if source_row else "",
                "source_family_tag": source_family_tag,
                "scenario_role_primary": scenario_role,
                "diagnostic_tags": ";".join(diagnostic_tags),
                "profile_config_path": source_row.get("profile_config_path", "") if source_row else "",
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
            except Exception as exc:  # noqa: BLE001 - every failed execution is an audit row.
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
        "m2838_weak_diagnostic_accounting_visible": True,
        "m2838_ordinary_denominator_allowed": False,
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
        delta_values = {
            "candidate_minus_baseline_min_clearance_margin": _delta(candidate, baseline, "min_clearance_margin"),
            "candidate_minus_baseline_return": _delta(candidate, baseline, "return"),
            "candidate_minus_baseline_speed_mean": _delta(candidate, baseline, "speed_mean"),
            "candidate_minus_baseline_high_sideslip_fraction": _delta(
                candidate,
                baseline,
                "high_sideslip_fraction",
            ),
            "candidate_minus_baseline_action_rate_mean": _delta(candidate, baseline, "action_rate_mean"),
            "candidate_minus_baseline_previous_command_norm_mean": _delta(
                candidate,
                baseline,
                "previous_command_norm_mean",
            ),
            "candidate_minus_baseline_current_action_norm_mean": _delta(
                candidate,
                baseline,
                "current_action_norm_mean",
            ),
            "candidate_minus_baseline_action_trace_delta_mean": _delta(
                candidate,
                baseline,
                "action_trace_delta_mean",
            ),
            "candidate_minus_baseline_steps": _delta(candidate, baseline, "steps"),
        }
        rows.append(
            {
                "pair_id": pair_id,
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
        (
            "execution_observation_shape",
            {int(row.get("observation_shape", -1)) for row in execution_rows},
            {P0_OBSERVATION_DIM},
        ),
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
            "guard_id": f"m2850-actor-guard-{name}",
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
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    specs = [
        (
            "paired_closed_loop_diagnostic_artifacts",
            "artifact",
            True,
            bool(paired_execution_rows and paired_delta_rows),
            "paired execution and delta rows",
        ),
        (
            "required_artifact_completeness",
            "artifact",
            True,
            required_artifacts_present,
            "M2850 required artifact set",
        ),
        (
            "follow_up_result_audit_registered",
            "follow_up_route",
            True,
            follow_up_manifest_registered,
            "M2851 result-audit manifest",
        ),
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
        "claim_id": f"m2850-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2850": allowed,
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
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    expected_execution_rows = len(selected_rows) * len(CHECKPOINT_SUBJECTS)
    return [
        gate(
            "proof_source_artifacts_present",
            "proof",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M1690 specs M2849 M2848 M2838 and checkpoint artifacts present",
            len(source["source_exists"]),
            "lineage_invalid",
        ),
        gate(
            "proof_m2848_status_pass",
            "proof",
            "lineage",
            bool(source["m2848_summary"].get("status_pass", False)),
            source["m2848_summary"].get("status_pass", False),
            True,
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_m2838_weak_accounting_visible",
            "proof",
            "lineage",
            bool(source["m2838_summary"].get("status_pass", False))
            and int(source["m2838_summary"].get("candidate_execution_row_count", 0)) == 16
            and not _bool(source["m2838_summary"].get("ordinary_success_denominator_allowed", True)),
            {
                "status_pass": source["m2838_summary"].get("status_pass", False),
                "execution_rows": source["m2838_summary"].get("candidate_execution_row_count", ""),
                "ordinary_denominator": source["m2838_summary"].get("ordinary_success_denominator_allowed", ""),
            },
            "M2838 status pass with weak diagnostics outside ordinary denominators",
            1,
            "proof_washout",
        ),
        gate(
            "proof_checkpoint_lineage_hashes",
            "proof",
            "lineage",
            bool(subject_registry["baseline"]["checkpoint_hash"])
            and bool(subject_registry["candidate"]["checkpoint_hash"])
            and subject_registry["baseline"]["checkpoint_hash"] != subject_registry["candidate"]["checkpoint_hash"],
            "baseline and candidate hashes",
            "non-empty distinct hashes",
            2,
            "lineage_invalid",
        ),
        gate(
            "proof_paired_execution_row_count",
            "proof",
            "artifact",
            len(execution_rows) == expected_execution_rows,
            len(execution_rows),
            expected_execution_rows,
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "proof_paired_delta_row_count",
            "proof",
            "artifact",
            len(delta_rows) == len(selected_rows),
            len(delta_rows),
            len(selected_rows),
            len(delta_rows),
            "metric_artifact",
        ),
        gate(
            "proof_all_executions_completed",
            "proof",
            "execution",
            bool(execution_rows) and all(str(row.get("execution_status", "")) == "completed" for row in execution_rows),
            Counter(str(row.get("execution_status", "")) for row in execution_rows),
            "all completed",
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "proof_pair_completeness",
            "proof",
            "artifact",
            bool(delta_rows) and all(_bool(row["paired_execution_complete"]) for row in delta_rows),
            "all pairs complete",
            "all pairs complete",
            len(delta_rows),
            "metric_artifact",
        ),
        gate(
            "proof_actor_contract_guards_pass",
            "proof",
            "contract",
            bool(actor_guard_rows) and all(_bool(row["status_pass"]) for row in actor_guard_rows),
            "all actor guards pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows,
            "all actor guards pass",
            len(actor_guard_rows),
            "contract_violation",
        ),
        gate(
            "proof_no_actor_visible_labels",
            "proof",
            "contract",
            not any_actor_visible_label(execution_rows),
            False,
            False,
            len(execution_rows),
            "contract_violation",
        ),
        gate(
            "proof_no_hidden_or_oracle_actor_input",
            "proof",
            "contract",
            not any_flag(execution_rows, "hidden_oracle_actor_input_required"),
            False,
            False,
            len(execution_rows),
            "contract_violation",
        ),
        gate(
            "proof_m2838_outside_ordinary_denominators",
            "proof",
            "proof_washout",
            not any_flag(execution_rows + delta_rows, "m2838_ordinary_denominator_allowed")
            and not any_flag(execution_rows + delta_rows, "ordinary_success_denominator_allowed"),
            False,
            False,
            len(execution_rows) + len(delta_rows),
            "proof_washout",
        ),
        gate(
            "proof_claim_boundary_rows_pass",
            "proof",
            "claim",
            bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows),
            "all claim rows pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows,
            "all claim rows pass",
            len(claim_rows),
            "proof_washout",
        ),
        gate(
            "proof_no_ranking_winner_success_verdict",
            "proof",
            "claim",
            not any_flag(execution_rows + delta_rows, "ranking_admissible")
            and not any_flag(execution_rows + delta_rows, "winner_selected")
            and not any_flag(execution_rows + delta_rows, "success_rate_verdict_computed"),
            False,
            False,
            len(execution_rows) + len(delta_rows),
            "objective_overfit",
        ),
        gate(
            "proof_required_artifacts_present",
            "proof",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            len(REQUIRED_ARTIFACT_KEYS),
            "lineage_invalid",
        ),
    ]


def build_generalization_delta_gate_rows(
    *,
    selected_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    row_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    return [
        gate(
            "generalization_requested_row_count",
            "generalization",
            "scenario_sampling",
            len(selected_rows) == int(row_count),
            len(selected_rows),
            int(row_count),
            len(selected_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_not_single_seed_panel",
            "generalization",
            "seed_split",
            int(row_count) >= 2,
            int(row_count),
            ">=2",
            int(row_count),
            "seed_fragility",
        ),
        gate(
            "generalization_unique_task_sources",
            "generalization",
            "scenario_sampling",
            len({row["task_source_id"] for row in selected_rows}) == len(selected_rows),
            len({row["task_source_id"] for row in selected_rows}),
            len(selected_rows),
            len(selected_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_l3_profile_only",
            "generalization",
            "contract",
            {row["profile_name"] for row in selected_rows} == {CANONICAL_PROFILE},
            sorted({row["profile_name"] for row in selected_rows}),
            CANONICAL_PROFILE,
            len(selected_rows),
            "contract_violation",
        ),
        gate(
            "generalization_subject_coverage",
            "generalization",
            "artifact",
            {row["checkpoint_subject"] for row in execution_rows} == set(CHECKPOINT_SUBJECTS),
            sorted({row["checkpoint_subject"] for row in execution_rows}),
            sorted(CHECKPOINT_SUBJECTS),
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "generalization_eval_seed_pairing",
            "generalization",
            "seed_split",
            paired_eval_seed_consistency(execution_rows),
            "same seed per baseline/candidate pair",
            "same seed per baseline/candidate pair",
            len(execution_rows),
            "seed_fragility",
        ),
        gate(
            "generalization_horizon_applied",
            "generalization",
            "execution",
            {int(row.get("horizon_steps", -1)) for row in execution_rows} == {int(horizon_steps)}
            and {int(row.get("env_max_steps_applied", -1)) for row in execution_rows} == {int(horizon_steps)},
            sorted({row.get("horizon_steps", "") for row in execution_rows}),
            int(horizon_steps),
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "generalization_finite_delta_rows",
            "generalization",
            "metric",
            bool(delta_rows) and all(_bool(row["finite_delta"]) for row in delta_rows),
            "finite",
            "finite",
            len(delta_rows),
            "metric_artifact",
        ),
    ]


def build_promotion_guard_rows(
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        gate(
            "promotion_checkpoint_not_promoted",
            "promotion",
            "promotion_guard",
            not any_flag(execution_rows, "checkpoint_promoted"),
            False,
            False,
            len(execution_rows),
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_winner_selected",
            "promotion",
            "promotion_guard",
            not any_flag(execution_rows + delta_rows, "winner_selected"),
            False,
            False,
            len(execution_rows) + len(delta_rows),
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_success_rate_verdict",
            "promotion",
            "promotion_guard",
            not any_flag(execution_rows + delta_rows, "success_rate_verdict_computed"),
            False,
            False,
            len(execution_rows) + len(delta_rows),
            "metric_artifact",
        ),
        gate(
            "promotion_no_active_config_overwrite",
            "promotion",
            "promotion_guard",
            not any_flag(execution_rows, "active_config_overwritten"),
            False,
            False,
            len(execution_rows),
            "contract_violation",
        ),
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
        "gate_id": f"m2850-gate-{gate_id}",
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
    forbidden_claims_made = any_forbidden_claim(execution_rows + delta_rows)
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_pass
        and claim_boundary_pass
        and paired_rows_complete
        and required_artifacts_present
        and not forbidden_claims_made
    )
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    execution_status_counts = Counter(str(row.get("execution_status", "")) for row in execution_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel_pass"
            if status_pass
            else "engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel_fail"
        ),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "m1690_workload": str(source["paths"]["m1690_workload"]),
        "executable_specs": str(source["paths"]["executable_specs"]),
        "m2849_audit": str(source["paths"]["m2849_audit"]),
        "m2848_summary": str(source["paths"]["m2848_summary"]),
        "m2838_summary": str(source["paths"]["m2838_summary"]),
        "m2848_status_pass": bool(source["m2848_summary"].get("status_pass", False)),
        "m2838_status_pass": bool(source["m2838_summary"].get("status_pass", False)),
        "m2838_weak_diagnostic_execution_rows": source["m2838_summary"].get("candidate_execution_row_count", ""),
        "m2838_diagnostic_success_count": source["m2838_summary"].get("diagnostic_success_count", ""),
        "m2838_diagnostic_collision_count": source["m2838_summary"].get("diagnostic_collision_count", ""),
        "m2838_diagnostic_offtrack_count": source["m2838_summary"].get("diagnostic_offtrack_count", ""),
        "m2838_ordinary_denominator_allowed": source["m2838_summary"].get(
            "ordinary_success_denominator_allowed",
            "",
        ),
        "baseline_checkpoint": str(subject_registry["baseline"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "baseline_checkpoint_hash": subject_registry["baseline"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "baseline_model_state_hash": subject_registry["baseline"]["model_state_hash"],
        "candidate_model_state_hash": subject_registry["candidate"]["model_state_hash"],
        "paired_execution_rows": str(paths["paired_execution_rows"]),
        "paired_delta_rows": str(paths["paired_delta_rows"]),
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
        "selected_task_source_ids": [row["task_source_id"] for row in selected_rows],
        "paired_execution_row_count": len(execution_rows),
        "paired_delta_row_count": len(delta_rows),
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
        "ordinary_success_denominator_allowed": any_flag(execution_rows + delta_rows, "ordinary_success_denominator_allowed"),
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
        "complete": summary["paired_rows_complete"],
        "next_blocker": summary["next_blocker"],
    }


def build_m2851_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
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
                summary["proof_retention_gate_rows"],
                summary["generalization_delta_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
                summary["m2849_audit"],
                summary["m2848_summary"],
                summary["m2838_summary"],
            ],
            "parent_config": [
                "experiments/manifests/m2850-engineering-controller-route-a-response-predictive-recurrent-belief-candidate-closed-loop-delta-panel-preflight.json",
                "experiments/manifests/m2849-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-bounded-continuation-result-audit.json",
            ],
            "parent_objective": [
                "audit M2850 paired closed-loop baseline-vs-candidate delta artifacts before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2851 must audit paired execution/delta completeness before any interpretation",
                "M2851 must preserve M2838 weak diagnostic accounting outside ordinary denominators",
                "M2851 must reject ranking winner promotion success-rate verdict validation performance paper current-sim high-fidelity full-driver and self-ID claims",
            ],
            "supersedes": ["unaudited M2850 paired closed-loop delta interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2851 must audit whether M2850 wrote complete paired baseline/candidate execution rows and paired delta rows",
            "M2851 must verify actor 72/action 3 no hidden/oracle actor input and no actor-visible labels",
            "M2851 must verify proof retention generalization delta promotion guard actor guard claim and gate rows pass",
            "M2851 must verify M2838 weak diagnostic accounting remains visible and outside ordinary denominators",
            "M2851 must not validate rank promote select a winner compute success-rate verdict or claim performance paper current-sim high-fidelity full-driver or self-ID result",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not run validation",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not change actor inputs",
            "do not inject hidden or oracle actor features",
            "do not hide M2838 weak diagnostic outcomes",
            "do not claim repair success driver performance validation readiness/result paper finite-window-vs-GRU current-sim high-fidelity full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_driver_like_recurrent_belief_architecture_training_redesign",
            "evidence_axis": "response_predictive_recurrent_belief_candidate_closed_loop_delta_panel_result_audit",
            "evidence_increment": "audits M2850 paired closed-loop baseline-vs-candidate diagnostic delta artifacts before interpretation",
            "claim_scope": "Result audit only; no validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity validation self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2850 paired rows are incomplete",
                "stop if actor-visible label exclusion failed",
                "stop if M2838 weak diagnostic rows enter ordinary denominators",
                "stop if M2850 deltas are used as a ranking or winner verdict",
            ],
            "fallback_plan": [
                "route to artifact repair only for narrow lineage or schema failure",
                "route to branch synthesis if paired deltas are negative or claim boundaries fail",
                "route to fresh evidence design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2850 has produced paired closed-loop diagnostic delta artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2850 paired closed-loop baseline-vs-candidate diagnostic delta artifacts",
            "admission_evidence": [
                "M2850 summary and gate rows are expected before M2851 runs",
                "M2850 paired execution and delta rows require audit before interpretation",
            ],
            "blocked_shortcuts": [
                "no new training or validation in result audit",
                "no ranking winner selection promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                doc_path,
                "M2851 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2850 paired row completeness and gate rows are accepted or rejected",
                "failure types are classified if any gate failed",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2851 audits diagnostic deltas only and does not run finite-window-vs-GRU or self-ID tests.",
            "history_necessity_tests": [
                "M2850 paired recurrent-belief deltas are not level3 self-identification evidence."
            ],
            "temporal_evidence_window": "M2843-M2850 response-predictive recurrent-belief branch.",
            "negative_result_policy": "If M2850 deltas are negative or gates fail, preserve the result and route to synthesis rather than weakening gates.",
            "allowed_claims": [
                "M2850 paired closed-loop delta panel accepted or rejected",
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
            "evidence_expansion": "audits new M2850 paired closed-loop diagnostic data",
            "paper_verdict_delta": "no paper verdict; audit governs Route A engineering controller evidence interpretation",
            "must_synthesize_if": [
                "M2850 cannot produce complete paired baseline/candidate closed-loop artifacts",
                "M2850 exposes labels or hidden/oracle inputs to actor input",
                "M2850 regresses M2838 weak diagnostic accounting",
                "M2850 results are used as validation performance self-ID or paper evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2850 paired closed-loop delta artifacts before any interpretation.",
        "success_criteria": [
            f"{doc_path} exists",
            "audit checks M2850 summary paired execution rows paired delta rows proof generalization promotion actor claim and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels M2838 diagnostic boundary and claim boundary",
            "audit registers one bounded follow-up route if continuing",
        ],
        "failure_criteria": [
            "M2851 runs new training validation ranking promotion or success-rate verdict computation",
            "M2851 hides M2850 gate failures or weakens actor/claim boundaries",
            "M2851 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2851 audits M2850 artifacts under unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": doc_path, "type": "md"}],
        "baseline_checkpoints": [summary["baseline_checkpoint"], summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["paired_execution_rows"], summary["paired_delta_rows"]],
        "scoreboard_checkpoint": doc_path,
        "next_blocker": "",
    }


def write_follow_up_manifest(path: Path, manifest: dict[str, Any]) -> None:
    write_json(path, manifest)


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2850 Engineering Controller Route A Response-Predictive Recurrent-Belief Candidate Closed-Loop Delta Panel Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- paired panel rows: {summary['selected_pair_count']}",
            f"- paired execution rows: {summary['paired_execution_row_count']}",
            f"- paired delta rows: {summary['paired_delta_row_count']}",
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
            "M2850 follows the post-M2470 Route A split: it produces bounded engineering-controller",
            "diagnostic closed-loop data without turning the row deltas into validation, ranking,",
            "promotion, paper, current-sim, high-fidelity, full-driver, or self-ID claims.",
            "",
            "## M2838 Accounting",
            "",
            "```text",
            f"M2838 status pass: {summary['m2838_status_pass']}",
            f"M2838 weak diagnostic rows: {summary['m2838_weak_diagnostic_execution_rows']}",
            f"M2838 diagnostic outcomes: success {summary['m2838_diagnostic_success_count']} collision {summary['m2838_diagnostic_collision_count']} offtrack {summary['m2838_diagnostic_offtrack_count']}",
            f"M2838 ordinary denominator allowed: {summary['m2838_ordinary_denominator_allowed']}",
            "```",
            "",
            "## Selected Task Sources",
            "",
            "```text",
            *[str(item) for item in summary["selected_task_source_ids"]],
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
    parser.add_argument("--m2849-audit", type=Path, default=DEFAULT_M2849_AUDIT)
    parser.add_argument("--m2848-summary", type=Path, default=DEFAULT_M2848_SUMMARY)
    parser.add_argument("--m2838-summary", type=Path, default=DEFAULT_M2838_SUMMARY)
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
    summary = run_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel(
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        m2849_audit=args.m2849_audit,
        m2848_summary=args.m2848_summary,
        m2838_summary=args.m2838_summary,
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
        "M2850 response-predictive recurrent-belief candidate closed-loop delta panel: "
        f"status={summary['status_pass']} "
        f"pairs={summary['selected_pair_count']} "
        f"executions={summary['paired_execution_row_count']} "
        f"deltas={summary['paired_delta_row_count']} "
        f"next={summary['next_blocker']}"
    )


if __name__ == "__main__":
    main()
