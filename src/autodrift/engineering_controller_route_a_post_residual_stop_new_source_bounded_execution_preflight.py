"""Run M3015 bounded diagnostic execution over M3012 new-source workloads.

M3015 consumes the M3013/M3014 admission chain and the M3012 executable
env/workload artifacts. It records one bounded current-sim diagnostic episode
or one failure row for each M3012 workload row. The milestone does not train,
rank, promote, tune profiles, mutate checkpoints, validate, or claim driver
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
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3015-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-preflight"
)
NEXT_ID = (
    "m3016-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-result-audit"
)
M3012_ID = (
    "m3012-engineering-controller-route-a-post-residual-stop-new-source-"
    "executable-env-materialization-preflight"
)
M3013_ID = (
    "m3013-engineering-controller-route-a-post-residual-stop-new-source-"
    "executable-env-materialization-result-audit"
)
M3014_ID = (
    "m3014-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-admission-design"
)

DEFAULT_M3013_AUDIT = Path(f"docs/{M3013_ID}.md")
DEFAULT_M3014_DESIGN = Path(f"docs/{M3014_ID}.md")
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_"
    "bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")
DEFAULT_EVAL_SEED_BASE = 301500

EXPECTED_SOURCE_SPEC_COUNT = 16
EXPECTED_WORKLOAD_ROW_COUNT = 32
EXPECTED_PROFILE_BINDING_COUNT = 2

CLAIM_SCOPE = (
    "M3015 Route A post-residual-stop new-source bounded diagnostic execution "
    "preflight only; one current-sim diagnostic episode or one failure row may "
    "be recorded for each M3012 workload row. No validation result, repair "
    "success, driver performance, paper, current-sim verdict, high-fidelity "
    "validation, finite-window-vs-GRU, full ideal driver, self-ID, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, profile "
    "tuning, training, replay, or PPO claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, repair success, driver performance, current-sim "
    "verdict, paper evidence, high-fidelity validation readiness or result, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, level3 "
    "self-identification, checkpoint ranking, winner selection, or promotion"
)

PATH_KEYS = [
    "summary",
    "execution_workload_rows",
    "episode_rows",
    "failure_rows",
    "profile_aggregate_rows",
    "source_aggregate_rows",
    "claim_boundary_rows",
    "execution_guard_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

EXECUTION_WORKLOAD_FIELDNAMES = [
    "execution_workload_id",
    "executable_workload_id",
    "workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "axis_name",
    "axis_family",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "source_spec_exists",
    "m3012_status_pass",
    "execution_scheduled_in_m3015",
    "environment_reset_scheduled_by_m3015",
    "environment_step_scheduled_by_m3015",
    "policy_action_scheduled_by_m3015",
    "policy_rollout_scheduled_by_m3015",
    "validation_scheduled_by_m3015",
    "training_scheduled_by_m3015",
    "replay_scheduled_by_m3015",
    "ppo_scheduled_by_m3015",
    "ranking_scheduled_by_m3015",
    "winner_selection_scheduled_by_m3015",
    "checkpoint_mutation_scheduled",
    "checkpoint_promotion_scheduled",
    "profile_specific_tuning",
    "actor_observation_dim",
    "actor_action_dim",
    "actor_input_contract_changed",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "diagnostic_only_no_verdict",
    "status_pass",
    "claim_boundary",
]

EPISODE_FIELDNAMES = [
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
    "execution_workload_id",
    "executable_workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
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
    "m3015_eval_seed",
    "m3015_bounded_execution_preflight",
    "new_source_diagnostic_row",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "source_build_run",
    "private_holdout_used",
    "profile_specific_tuning",
    "active_config_overwritten",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "success_rate_verdict_claim_made",
    "driver_performance_claim_made",
    "repair_success_claim_made",
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
    "execution_workload_id",
    "executable_workload_id",
    "workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "config_path",
    "checkpoint_path",
    "m3015_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "source_build_run",
    "private_holdout_used",
    "profile_specific_tuning",
    "active_config_overwritten",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "success_rate_verdict_claim_made",
    "driver_performance_claim_made",
    "repair_success_claim_made",
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
    "task_family",
    "source_edge",
    "window_tag",
    "binding_role",
    "scheduled_count",
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

GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3015",
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


def run_new_source_bounded_execution_preflight(
    *,
    m3013_audit: Path | str = DEFAULT_M3013_AUDIT,
    m3014_design: Path | str = DEFAULT_M3014_DESIGN,
    m3012_dir: Path | str = DEFAULT_M3012_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3013_audit=Path(m3013_audit),
        m3014_design=Path(m3014_design),
        m3012_dir=Path(m3012_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    execution_workloads = build_execution_workload_rows(source)
    write_csv_rows(paths["execution_workload_rows"], execution_workloads, fieldnames=EXECUTION_WORKLOAD_FIELDNAMES)

    execution_summary = run_execution_rows(
        execution_workloads=execution_workloads,
        executable_specs=source["m3012_executable_source_specs"],
        output_dir=output,
        eval_seed_base=int(eval_seed_base),
        device=device,
        next_blocker=next_blocker,
    )
    artifact_rows = load_execution_artifact_rows(paths)
    profile_aggregates = build_aggregate_rows(
        aggregate_family="profile_name",
        key="profile_name",
        execution_workloads=execution_workloads,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    source_aggregates = build_aggregate_rows(
        aggregate_family="task_source_id",
        key="task_source_id",
        execution_workloads=execution_workloads,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    write_csv_rows(paths["profile_aggregate_rows"], profile_aggregates, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["source_aggregate_rows"], source_aggregates, fieldnames=AGGREGATE_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]))
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    required_without_summary_doc = all(
        paths[key].exists() for key in PATH_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        episode_rows_present=bool(artifact_rows["episode_rows"]),
        episode_or_failure_rows_present=bool(artifact_rows["episode_rows"] or artifact_rows["failure_rows"]),
    )
    guard_rows = build_execution_guard_rows(
        execution_workloads=execution_workloads,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        execution_workloads=execution_workloads,
        artifact_rows=artifact_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["execution_guard_rows"], guard_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        execution_workloads=execution_workloads,
        artifact_rows=artifact_rows,
        profile_aggregates=profile_aggregates,
        source_aggregates=source_aggregates,
        guard_rows=guard_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_rows_present=bool(artifact_rows["episode_rows"]),
        episode_or_failure_rows_present=bool(artifact_rows["episode_rows"] or artifact_rows["failure_rows"]),
    )
    guard_rows = build_execution_guard_rows(
        execution_workloads=execution_workloads,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        execution_workloads=execution_workloads,
        artifact_rows=artifact_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["execution_guard_rows"], guard_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        execution_workloads=execution_workloads,
        artifact_rows=artifact_rows,
        profile_aggregates=profile_aggregates,
        source_aggregates=source_aggregates,
        guard_rows=guard_rows,
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
            "scheduled_workload_row_count": len(execution_workloads),
            "episode_row_count": len(artifact_rows["episode_rows"]),
            "failure_row_count": len(artifact_rows["failure_rows"]),
            "recorded_row_count": len(artifact_rows["episode_rows"]) + len(artifact_rows["failure_rows"]),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "execution_workload_rows": output_dir / "execution_workload_rows.csv",
        "episode_rows": output_dir / "episode_rows.csv",
        "failure_rows": output_dir / "failure_rows.csv",
        "profile_aggregate_rows": output_dir / "profile_aggregate_rows.csv",
        "source_aggregate_rows": output_dir / "source_aggregate_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "execution_guard_rows": output_dir / "execution_guard_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3013_audit: Path,
    m3014_design: Path,
    m3012_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3013_audit": m3013_audit,
        "m3014_design": m3014_design,
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_source_specs": m3012_dir / "executable_source_specs.json",
        "m3012_executable_workload_rows": m3012_dir / "executable_workload_rows.csv",
        "m3012_actor_contract_guard_rows": m3012_dir / "actor_contract_guard_rows.csv",
        "m3012_claim_boundary_rows": m3012_dir / "claim_boundary_rows.csv",
        "m3012_gate_matrix": m3012_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_source_specs"]) if source_exists["m3012_executable_source_specs"] else {}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3013_audit_text": paths["m3013_audit"].read_text(encoding="utf-8")
        if source_exists["m3013_audit"]
        else "",
        "m3014_design_text": paths["m3014_design"].read_text(encoding="utf-8")
        if source_exists["m3014_design"]
        else "",
        "m3012_summary": read_json(paths["m3012_summary"]) if source_exists["m3012_summary"] else {},
        "m3012_executable_source_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_executable_workload_rows": read_csv_rows(paths["m3012_executable_workload_rows"]),
        "m3012_actor_contract_guard_rows": read_csv_rows(paths["m3012_actor_contract_guard_rows"]),
        "m3012_claim_boundary_rows": read_csv_rows(paths["m3012_claim_boundary_rows"]),
        "m3012_gate_matrix": read_csv_rows(paths["m3012_gate_matrix"]),
    }


def build_execution_workload_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    spec_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for spec in source["m3012_executable_source_specs"]:
        spec_by_key[(str(spec.get("task_source_id", "")), str(spec.get("executable_source_spec_id", "")))] = spec

    rows: list[dict[str, Any]] = []
    for index, workload in enumerate(
        sorted(source["m3012_executable_workload_rows"], key=lambda row: row.get("executable_workload_id", "")),
        start=1,
    ):
        task_source_id = str(workload.get("task_source_id", ""))
        executable_source_spec_id = str(workload.get("executable_source_spec_id", ""))
        spec = spec_by_key.get((task_source_id, executable_source_spec_id))
        config_path = str(workload.get("config_path", ""))
        checkpoint_path = str(workload.get("checkpoint_path", ""))
        profile_name = str(workload.get("profile_binding_name", ""))
        strata = ";".join(
            value
            for value in (
                "new_source",
                str(workload.get("task_family", "")),
                str(workload.get("binding_role", "")),
                str(workload.get("executable_source_family", "")),
                str(workload.get("env_template_family", "")),
            )
            if value
        )
        hidden_label_violation = any(
            _bool(workload.get(field, False))
            for field in (
                "hidden_oracle_actor_input_required",
                "future_target_actor_input_required",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
            )
        )
        status_pass = bool(
            _bool(workload.get("status_pass", False))
            and spec is not None
            and Path(config_path).exists()
            and Path(checkpoint_path).exists()
            and int(workload.get("actor_observation_dim", -1)) == P0_OBSERVATION_DIM
            and int(workload.get("actor_action_dim", -1)) == ACTION_DIM
            and not hidden_label_violation
        )
        rows.append(
            {
                "execution_workload_id": f"m3015-execution-workload-{index:04d}",
                "executable_workload_id": workload.get("executable_workload_id", ""),
                "workload_id": workload.get("executable_workload_id", ""),
                "workload_contract_id": workload.get("workload_contract_id", ""),
                "source_resolution_id": workload.get("source_resolution_id", ""),
                "profile_binding_id": workload.get("profile_binding_id", ""),
                "executable_source_spec_id": executable_source_spec_id,
                "task_source_id": task_source_id,
                "profile_name": profile_name,
                "profile_binding_name": profile_name,
                "binding_role": workload.get("binding_role", ""),
                "axis_name": workload.get("axis_name", ""),
                "axis_family": workload.get("axis_family", ""),
                "task_family": workload.get("task_family", ""),
                "source_edge": workload.get("source_edge", ""),
                "window_tag": workload.get("window_tag", ""),
                "strata": strata,
                "executable_source_family": workload.get("executable_source_family", ""),
                "env_template_family": workload.get("env_template_family", ""),
                "config_path": config_path,
                "checkpoint_path": checkpoint_path,
                "config_exists": Path(config_path).exists(),
                "checkpoint_exists": Path(checkpoint_path).exists(),
                "source_spec_exists": spec is not None,
                "m3012_status_pass": _bool(workload.get("status_pass", False)),
                "execution_scheduled_in_m3015": True,
                "environment_reset_scheduled_by_m3015": True,
                "environment_step_scheduled_by_m3015": True,
                "policy_action_scheduled_by_m3015": True,
                "policy_rollout_scheduled_by_m3015": True,
                "validation_scheduled_by_m3015": False,
                "training_scheduled_by_m3015": False,
                "replay_scheduled_by_m3015": False,
                "ppo_scheduled_by_m3015": False,
                "ranking_scheduled_by_m3015": False,
                "winner_selection_scheduled_by_m3015": False,
                "checkpoint_mutation_scheduled": False,
                "checkpoint_promotion_scheduled": False,
                "profile_specific_tuning": False,
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "actor_input_contract_changed": False,
                "actor_visible": False,
                "hidden_oracle_actor_input_required": _bool(workload.get("hidden_oracle_actor_input_required", False)),
                "future_target_actor_input_required": _bool(workload.get("future_target_actor_input_required", False)),
                "source_labels_actor_visible": _bool(workload.get("source_labels_actor_visible", False)),
                "route_labels_actor_visible": _bool(workload.get("route_labels_actor_visible", False)),
                "outcome_labels_actor_visible": _bool(workload.get("outcome_labels_actor_visible", False)),
                "success_progress_labels_actor_visible": _bool(workload.get("success_progress_labels_actor_visible", False)),
                "verdict_labels_actor_visible": _bool(workload.get("verdict_labels_actor_visible", False)),
                "ttc_actor_input_required": _bool(workload.get("ttc_actor_input_required", False)),
                "diagnostic_only_no_verdict": True,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def run_execution_rows(
    *,
    execution_workloads: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    eval_seed_base: int,
    device: str,
    next_blocker: str,
) -> dict[str, Any]:
    spec_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for spec in executable_specs:
        spec_by_key[(str(spec.get("task_source_id", "")), str(spec.get("executable_source_spec_id", "")))] = spec

    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    episode_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for index, workload in enumerate(execution_workloads):
        eval_seed = int(eval_seed_base) + index
        try:
            if not _bool(workload.get("status_pass", False)):
                raise ValueError("execution workload failed pre-execution status guards")
            spec_key = (str(workload["task_source_id"]), str(workload["executable_source_spec_id"]))
            executable_spec = spec_by_key[spec_key]
            profile_name = str(workload["profile_name"])
            config_path = str(workload["config_path"])
            checkpoint_path = str(workload["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in profile_cache:
                profile_config = profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                profile_cache[cache_key] = (
                    profile_config,
                    model,
                    {"profile_name": profile_name, "config_path": config_path, "checkpoint_path": checkpoint_path},
                )
            profile_config, model, profile_row = profile_cache[cache_key]
            row = run_workload_cell(
                workload_row=workload,
                executable_spec=executable_spec,
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(execution_metadata(workload, eval_seed=eval_seed))
            episode_rows.append(_normalized_episode_row(row))
        except Exception as exc:  # noqa: BLE001 - every workload row must be accounted.
            failure_rows.append(
                failure_row(
                    workload,
                    eval_seed=eval_seed,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_workload_row_count": len(execution_workloads),
                "episode_row_count": len(episode_rows),
                "failure_row_count": len(failure_rows),
                "recorded_row_count": len(episode_rows) + len(failure_rows),
                "latest_execution_workload_id": workload.get("execution_workload_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    write_csv_rows(output_dir / "episode_rows.csv", episode_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else True
    accounted_count = len(episode_rows) + len(failure_rows)
    status_pass = bool(
        len(execution_workloads) == EXPECTED_WORKLOAD_ROW_COUNT
        and accounted_count == len(execution_workloads)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    write_run_state(
        output_dir / "run_state.json",
        {
            "scheduled_workload_row_count": len(execution_workloads),
            "episode_row_count": len(episode_rows),
            "failure_row_count": len(failure_rows),
            "recorded_row_count": accounted_count,
            "complete": accounted_count == len(execution_workloads),
            "status_pass": status_pass,
            "next_blocker": next_blocker,
        },
    )
    return {
        "result_class": (
            "new_source_bounded_execution_preflight_complete"
            if status_pass
            else "new_source_bounded_execution_preflight_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "scheduled_workload_row_count": len(execution_workloads),
        "episode_row_count": len(episode_rows),
        "failure_row_count": len(failure_rows),
        "recorded_row_count": accounted_count,
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }


def execution_metadata(workload: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "execution_workload_id": workload.get("execution_workload_id", ""),
        "executable_workload_id": workload.get("executable_workload_id", ""),
        "workload_contract_id": workload.get("workload_contract_id", ""),
        "source_resolution_id": workload.get("source_resolution_id", ""),
        "profile_binding_id": workload.get("profile_binding_id", ""),
        "executable_source_spec_id": workload.get("executable_source_spec_id", ""),
        "profile_binding_name": workload.get("profile_binding_name", ""),
        "binding_role": workload.get("binding_role", ""),
        "m3015_eval_seed": int(eval_seed),
        "m3015_bounded_execution_preflight": True,
        "new_source_diagnostic_row": True,
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def failure_row(
    workload: Mapping[str, Any],
    *,
    eval_seed: int,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    row = {key: False for key in FAILURE_FIELDNAMES}
    row.update(
        {
            "execution_workload_id": workload.get("execution_workload_id", ""),
            "executable_workload_id": workload.get("executable_workload_id", ""),
            "workload_id": workload.get("workload_id", ""),
            "workload_contract_id": workload.get("workload_contract_id", ""),
            "source_resolution_id": workload.get("source_resolution_id", ""),
            "profile_binding_id": workload.get("profile_binding_id", ""),
            "executable_source_spec_id": workload.get("executable_source_spec_id", ""),
            "task_source_id": workload.get("task_source_id", ""),
            "profile_name": workload.get("profile_name", ""),
            "profile_binding_name": workload.get("profile_binding_name", ""),
            "binding_role": workload.get("binding_role", ""),
            "task_family": workload.get("task_family", ""),
            "source_edge": workload.get("source_edge", ""),
            "window_tag": workload.get("window_tag", ""),
            "strata": workload.get("strata", ""),
            "executable_source_family": workload.get("executable_source_family", ""),
            "env_template_family": workload.get("env_template_family", ""),
            "config_path": workload.get("config_path", ""),
            "checkpoint_path": workload.get("checkpoint_path", ""),
            "m3015_eval_seed": int(eval_seed),
            "error_type": error_type,
            "error_message": error_message,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "episode_rows": read_csv_rows(paths["episode_rows"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
    }


def build_aggregate_rows(
    *,
    aggregate_family: str,
    key: str,
    execution_workloads: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    values = sorted({str(row.get(key, "")) for row in execution_workloads if str(row.get(key, ""))})
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(values, start=1):
        scheduled = [row for row in execution_workloads if str(row.get(key, "")) == value]
        episodes = [row for row in episode_rows if str(row.get(key, "")) == value]
        failures = [row for row in failure_rows if str(row.get(key, "")) == value]
        termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
        first = scheduled[0] if scheduled else {}
        rows.append(
            {
                "aggregate_id": f"m3015-{aggregate_family}-aggregate-{index:04d}",
                "aggregate_family": aggregate_family,
                "aggregate_value": value,
                "task_family": first.get("task_family", ""),
                "source_edge": first.get("source_edge", ""),
                "window_tag": first.get("window_tag", ""),
                "binding_role": first.get("binding_role", ""),
                "scheduled_count": len(scheduled),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in episodes),
                "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in episodes),
                "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
                "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
                "min_clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else True,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_execution_guard_rows(
    *,
    execution_workloads: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = execution_workloads + episode_rows + failure_rows
    accounted_ids = {
        str(row.get("execution_workload_id", ""))
        for row in episode_rows + failure_rows
        if row.get("execution_workload_id")
    }
    return [
        guard("observation_dim", P0_OBSERVATION_DIM, 72),
        guard("action_dim", ACTION_DIM, 3),
        guard("scheduled_workload_rows", len(execution_workloads), EXPECTED_WORKLOAD_ROW_COUNT),
        guard("accounted_workload_rows", len(accounted_ids), len(execution_workloads)),
        guard("actor_input_contract_changed", any_flag(combined, "actor_input_contract_changed"), False),
        guard("hidden_oracle_actor_input_required", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        guard("future_target_actor_input_required", any_flag(combined, "future_target_actor_input_required"), False),
        guard("source_labels_actor_visible", any_flag(combined, "source_labels_actor_visible"), False),
        guard("route_labels_actor_visible", any_flag(combined, "route_labels_actor_visible"), False),
        guard("outcome_labels_actor_visible", any_flag(combined, "outcome_labels_actor_visible"), False),
        guard("success_progress_labels_actor_visible", any_flag(combined, "success_progress_labels_actor_visible"), False),
        guard("verdict_labels_actor_visible", any_flag(combined, "verdict_labels_actor_visible"), False),
        guard("ttc_actor_input_required", any_flag(combined, "ttc_actor_input_required"), False),
        guard("training_run", any_flag(combined, "training_run") or any_flag(combined, "training_scheduled_by_m3015"), False),
        guard("replay_run", any_flag(combined, "replay_run") or any_flag(combined, "replay_scheduled_by_m3015"), False),
        guard("ppo_run", any_flag(combined, "ppo_run") or any_flag(combined, "ppo_scheduled_by_m3015"), False),
        guard("ranking_run", any_flag(combined, "ranking_run") or any_flag(combined, "ranking_scheduled_by_m3015"), False),
        guard("winner_selected", any_flag(combined, "winner_selected") or any_flag(combined, "winner_selection_scheduled_by_m3015"), False),
        guard("checkpoint_mutated", any_flag(combined, "checkpoint_mutated") or any_flag(combined, "checkpoint_mutation_scheduled"), False),
        guard("checkpoint_promoted", any_flag(combined, "checkpoint_promoted") or any_flag(combined, "checkpoint_promotion_scheduled"), False),
        guard("profile_specific_tuning", any_flag(combined, "profile_specific_tuning"), False),
        guard("active_config_overwritten", any_flag(combined, "active_config_overwritten"), False),
        guard("validation_result_claim_made", any_flag(combined, "validation_result_claim_made"), False),
        guard("driver_performance_claim_made", any_flag(combined, "driver_performance_claim_made"), False),
        guard("paper_claim_made", any_flag(combined, "paper_claim_made"), False),
        guard("current_sim_verdict_claim_made", any_flag(combined, "current_sim_verdict_claim_made"), False),
        guard("level3_self_id_claim_made", any_flag(combined, "level3_self_id_claim_made"), False),
    ]


def guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3015_execution_guard_{field}",
        "guard_family": field,
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
        ("bounded_execution_preflight", "execution", episode_or_failure_rows_present, "episode or failure rows"),
        ("execution_workloads_materialized", "artifact", artifacts_present, "execution_workload_rows.csv"),
        ("episode_rows_materialized", "artifact", artifacts_present, "episode_rows.csv"),
        ("failure_rows_materialized", "artifact", artifacts_present, "failure_rows.csv"),
        ("profile_aggregate_materialized", "artifact", artifacts_present, "profile_aggregate_rows.csv"),
        ("source_aggregate_materialized", "artifact", artifacts_present, "source_aggregate_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("execution_guard_materialized", "artifact", artifacts_present, "execution_guard_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded_if_available", "diagnostic_metric", episode_rows_present, "diagnostic fields only"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3016 audit manifest"),
    ]
    blocked = [
        ("source_build", "execution", "future source-build manifest"),
        ("replay_training_ppo", "execution", "future training manifest"),
        ("profile_specific_tuning", "execution", "future audited tuning route"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("controller_or_profile_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcut inputs"),
    ]
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3015_{claim_id}",
        "claim_family": family,
        "allowed_in_m3015": allowed,
        "claim_made": made,
        "status_pass": bool(allowed) or not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    execution_workloads: list[dict[str, Any]],
    artifact_rows: dict[str, list[dict[str, Any]]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["episode_rows"]
    failure_rows = artifact_rows["failure_rows"]
    accounted_ids = {
        str(row.get("execution_workload_id", ""))
        for row in episode_rows + failure_rows
        if row.get("execution_workload_id")
    }
    scheduled_ids = {str(row.get("execution_workload_id", "")) for row in execution_workloads}
    profile_names = {str(row.get("profile_name", "")) for row in execution_workloads if row.get("profile_name")}
    source_spec_ids = {
        str(row.get("task_source_id", ""))
        for row in source["m3012_executable_source_specs"]
        if row.get("task_source_id")
    }
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(value for key, value in source["source_exists"].items() if key != "follow_up_manifest"),
            source["source_exists"],
            "M3013/M3014/M3012 artifacts present",
            "lineage_invalid",
        ),
        (
            "m3013_accepts_m3012",
            "lineage",
            "accepts M3012" in source["m3013_audit_text"],
            "accepts M3012" in source["m3013_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3014_admits_m3015",
            "lineage",
            MILESTONE_ID in source["m3014_design_text"],
            MILESTONE_ID in source["m3014_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3012_status_pass",
            "lineage",
            _bool(source["m3012_summary"].get("status_pass", False))
            and _bool(source["m3012_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m3012_summary"].get("status_pass"),
                "gate_matrix_pass": source["m3012_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "source_spec_denominator_preserved",
            "denominator",
            len(source["m3012_executable_source_specs"]) == EXPECTED_SOURCE_SPEC_COUNT
            and len(source_spec_ids) == EXPECTED_SOURCE_SPEC_COUNT,
            {"source_specs": len(source["m3012_executable_source_specs"]), "unique_task_sources": len(source_spec_ids)},
            EXPECTED_SOURCE_SPEC_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "workload_denominator_preserved",
            "denominator",
            len(source["m3012_executable_workload_rows"]) == EXPECTED_WORKLOAD_ROW_COUNT
            and len(execution_workloads) == EXPECTED_WORKLOAD_ROW_COUNT,
            {"m3012": len(source["m3012_executable_workload_rows"]), "m3015": len(execution_workloads)},
            EXPECTED_WORKLOAD_ROW_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "profile_binding_count_preserved",
            "denominator",
            len(profile_names) == EXPECTED_PROFILE_BINDING_COUNT,
            sorted(profile_names),
            EXPECTED_PROFILE_BINDING_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "execution_workloads_scheduled_once",
            "execution",
            len(scheduled_ids) == len(execution_workloads) == EXPECTED_WORKLOAD_ROW_COUNT,
            {"scheduled_ids": len(scheduled_ids), "scheduled_rows": len(execution_workloads)},
            EXPECTED_WORKLOAD_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "episode_or_failure_accounts_all",
            "execution",
            accounted_ids == scheduled_ids and len(episode_rows) + len(failure_rows) == len(execution_workloads),
            {"accounted_ids": len(accounted_ids), "recorded_rows": len(episode_rows) + len(failure_rows)},
            len(execution_workloads),
            "scenario_sampling_failure",
        ),
        (
            "diagnostic_metrics_finite_if_present",
            "metric",
            selected_metrics_are_finite(episode_rows) if episode_rows else True,
            execution_summary.get("all_selected_metrics_finite"),
            True,
            "metric_artifact",
        ),
        (
            "execution_guard_rows_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in guard_rows),
            f"rows={len(guard_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in guard_rows)}",
            "all execution guards pass",
            "contract_violation",
        ),
        (
            "no_forbidden_execution_or_overclaim",
            "execution_guardrail",
            not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows),
            "no train/replay/PPO/ranking/promotion/overclaim flags",
            "all false",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row.get("status_pass", False)) for row in claim_rows),
            f"rows={len(claim_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in claim_rows)}",
            "all claim rows pass",
            "proof_washout",
        ),
        (
            "follow_up_manifest_registered",
            "lineage",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
            "lineage_invalid",
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
        "gate_id": f"m3015_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    execution_workloads: list[dict[str, Any]],
    artifact_rows: dict[str, list[dict[str, Any]]],
    profile_aggregates: list[dict[str, Any]],
    source_aggregates: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    episode_rows = artifact_rows["episode_rows"]
    failure_rows = artifact_rows["failure_rows"]
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    profile_counts = Counter(str(row.get("profile_name", "")) for row in execution_workloads)
    task_family_counts = Counter(str(row.get("task_family", "")) for row in execution_workloads)
    source_family_counts = Counter(str(row.get("executable_source_family", "")) for row in execution_workloads)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "new_source_bounded_execution_preflight_complete"
            if status_pass
            else "new_source_bounded_execution_preflight_fail"
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
        "m3013_audit_present": source["source_exists"]["m3013_audit"],
        "m3014_design_present": source["source_exists"]["m3014_design"],
        "m3012_status_pass": _bool(source["m3012_summary"].get("status_pass", False)),
        "m3012_gate_matrix_pass": _bool(source["m3012_summary"].get("gate_matrix_pass", False)),
        "source_spec_count": len(source["m3012_executable_source_specs"]),
        "unique_task_source_count": len({row.get("task_source_id", "") for row in source["m3012_executable_source_specs"]}),
        "target_source_spec_count": EXPECTED_SOURCE_SPEC_COUNT,
        "scheduled_workload_row_count": len(execution_workloads),
        "target_workload_row_count": EXPECTED_WORKLOAD_ROW_COUNT,
        "profile_binding_count": len({row.get("profile_name", "") for row in execution_workloads}),
        "target_profile_binding_count": EXPECTED_PROFILE_BINDING_COUNT,
        "episode_row_count": len(episode_rows),
        "failure_row_count": len(failure_rows),
        "recorded_row_count": len(episode_rows) + len(failure_rows),
        "profile_counts": dict(sorted(profile_counts.items())),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "executable_source_family_counts": dict(sorted(source_family_counts.items())),
        "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in episode_rows),
        "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in episode_rows),
        "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
        "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else True,
        "profile_aggregate_row_count": len(profile_aggregates),
        "source_aggregate_row_count": len(source_aggregates),
        "execution_guard_row_count": len(guard_rows),
        "execution_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "execution_summary_result_class": execution_summary.get("result_class", ""),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_new_source_execution_preflight": bool(episode_rows or failure_rows),
        "source_build_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "ranking_run": False,
        "winner_selected": False,
        "actor_input_contract_changed": any_flag(episode_rows + failure_rows, "actor_input_contract_changed"),
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any_flag(episode_rows + failure_rows, "hidden_oracle_actor_input_required"),
        "future_target_actor_input_required": any_flag(episode_rows + failure_rows, "future_target_actor_input_required"),
        "source_labels_actor_visible": any_flag(episode_rows + failure_rows, "source_labels_actor_visible"),
        "route_labels_actor_visible": any_flag(episode_rows + failure_rows, "route_labels_actor_visible"),
        "outcome_labels_actor_visible": any_flag(episode_rows + failure_rows, "outcome_labels_actor_visible"),
        "success_progress_labels_actor_visible": any_flag(episode_rows + failure_rows, "success_progress_labels_actor_visible"),
        "verdict_labels_actor_visible": any_flag(episode_rows + failure_rows, "verdict_labels_actor_visible"),
        "ttc_actor_input_required": any_flag(episode_rows + failure_rows, "ttc_actor_input_required"),
        "success_rate_metric_recorded": bool(episode_rows),
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
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
            "# M3015 Engineering Controller Route A Post-Residual-Stop New Source Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source specs: {summary['source_spec_count']}/{summary['target_source_spec_count']}",
            f"- scheduled workload rows: {summary['scheduled_workload_row_count']}/{summary['target_workload_row_count']}",
            f"- episode rows: {summary['episode_row_count']}",
            f"- failure rows: {summary['failure_row_count']}",
            f"- recorded rows: {summary['recorded_row_count']}/{summary['scheduled_workload_row_count']}",
            f"- profiles: {summary['profile_counts']}",
            f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
            f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- required artifacts present: {summary['required_artifacts_present']}",
            "",
            "## Boundary",
            "",
            "M3015 records bounded diagnostic current-sim execution/failure artifacts only. The episode rows, if present, are not validation, performance, paper, finite-window-vs-GRU, high-fidelity, full-driver, or self-ID evidence before M3016 audit.",
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
        "hypothesis": "A bounded result audit can accept or reject the M3015 new-source bounded execution preflight before any validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "execution_workload_rows.csv"),
                str(output_dir / "episode_rows.csv"),
                str(output_dir / "failure_rows.csv"),
                str(output_dir / "profile_aggregate_rows.csv"),
                str(output_dir / "source_aggregate_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "execution_guard_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                f"docs/{M3014_ID}.md",
                f"docs/{M3013_ID}.md",
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3014_ID}.json",
                f"experiments/manifests/{M3013_ID}.json",
                f"experiments/manifests/{M3012_ID}.json",
            ],
            "parent_objective": [
                "audit M3015 bounded diagnostic execution/failure artifacts before interpretation"
            ],
            "derived_from": [MILESTONE_ID, M3014_ID, M3013_ID, M3012_ID],
            "blocked_by": [
                "M3015 diagnostics require M3016 result audit before any verdict or continuation decision",
                "M3015 must preserve the full 32-row denominator and actor 72/action 3 contract",
            ],
            "supersedes": ["direct interpretation of M3015 diagnostic rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3016 must audit M3015 summary gate matrix execution guards actor and claim boundaries",
            "M3016 must preserve all 32 M3012 workload rows as episode or failure rows",
            "M3016 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M3016 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner mutate checkpoints or tune profiles",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert M3015 diagnostic rows into performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_bounded_diagnostic_execution_result_audit",
            "evidence_increment": "audits bounded diagnostic execution/failure artifacts from M3015",
            "claim_scope": "Result audit only; no validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3015 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if M3015 dropped any M3012 workload row",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if diagnostics are complete but negative or insufficient",
                "route to a next evidence-producing route only after M3016 accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3015 completes bounded diagnostic execution preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3015 bounded diagnostic execution preflight artifacts",
            "admission_evidence": [
                "M3015 summary and gate matrix",
                "M3015 execution workload episode failure aggregate guard and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO checkpoint mutation profile tuning or promotion",
                "no hidden/oracle/future-target/source/route/outcome/progress/verdict/TTC actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3016 status queue scoreboard and review",
                "one follow-up manifest only if M3016 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3016 audit accepts or rejects M3015 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3016 audits Route A new-source engineering diagnostics and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3016; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3015 Route A new-source diagnostic execution only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3015 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly generated Route A new-source bounded execution/failure artifacts",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M3016 cannot accept M3015 as complete and claim-safe",
                "M3016 would claim validation readiness driver performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID",
                "M3016 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3016 audits M3015 artifacts row counts gates actor and claim boundaries",
            "M3016 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3016 hides M3015 failures or missing artifacts",
            "M3016 treats M3015 diagnostics as validation readiness or performance verdict",
            "M3016 changes actor input or action contract",
            "M3016 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3016 audits M3015 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "episode_rows.csv"),
            str(output_dir / "failure_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def profile_config_for_runtime(config: dict[str, Any], *, profile_name: str) -> dict[str, Any]:
    controller_profile = config.get("controller_profile")
    if isinstance(controller_profile, dict) and str(controller_profile.get("name", "")).strip():
        return dict(config)

    runtime = config.get("controller_profile_runtime")
    if not isinstance(runtime, dict):
        runtime = {}
    adapted = dict(config)
    adapted["controller_profile"] = {
        "name": str(runtime.get("profile_name") or profile_name),
        "observation_mask": str(runtime.get("observation_mask", "none")),
        "previous_command_mask_indices": list(runtime.get("previous_command_mask_indices", [])),
        "history_transform": str(runtime.get("history_transform", "none")),
        "reset_hidden_policy": str(runtime.get("reset_hidden_policy", "episode_persistent")),
    }
    return adapted


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
            "private_holdout_used",
            "profile_specific_tuning",
            "active_config_overwritten",
            "ranking_run",
            "winner_selected",
            "checkpoint_mutated",
            "checkpoint_mutation_scheduled",
            "checkpoint_promoted",
            "checkpoint_promotion_scheduled",
            "promoted",
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "source_labels_actor_visible",
            "route_labels_actor_visible",
            "outcome_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "ttc_actor_input_required",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "repair_success_claim_made",
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


def _normalized_episode_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in EPISODE_FIELDNAMES}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3013-audit", type=Path, default=DEFAULT_M3013_AUDIT)
    parser.add_argument("--m3014-design", type=Path, default=DEFAULT_M3014_DESIGN)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_new_source_bounded_execution_preflight(
        m3013_audit=args.m3013_audit,
        m3014_design=args.m3014_design,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_rows={summary['episode_row_count']}")
    print(f"failure_rows={summary['failure_row_count']}")
    print(f"summary={Path(args.output_dir) / 'summary.json'}")


if __name__ == "__main__":
    main()
