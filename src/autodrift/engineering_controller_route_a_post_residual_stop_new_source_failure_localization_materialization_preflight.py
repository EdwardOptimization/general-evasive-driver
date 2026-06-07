"""Materialize M3018 failure-localization rows from M3015 diagnostics.

M3018 consumes the accepted M3015/M3016/M3017 new-source diagnostic artifacts.
It performs no reset, step, rollout, replay, validation, training, ranking,
promotion, profile tuning, checkpoint mutation, or source build. It preserves
the fixed 32-row M3015 denominator and writes machine-checkable localization,
aggregate, claim-boundary, gate, run-state, doc, and M3019 audit artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3018-engineering-controller-route-a-post-residual-stop-new-source-"
    "failure-localization-materialization-preflight"
)
NEXT_ID = (
    "m3019-engineering-controller-route-a-post-residual-stop-new-source-"
    "failure-localization-materialization-result-audit"
)
M3015_ID = (
    "m3015-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-preflight"
)
M3016_ID = (
    "m3016-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-result-audit"
)
M3017_ID = (
    "m3017-engineering-controller-route-a-post-residual-stop-new-source-"
    "bounded-execution-result-synthesis"
)

DEFAULT_M3015_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_"
    "bounded_execution_preflight"
)
DEFAULT_M3016_AUDIT = Path(f"docs/{M3016_ID}.md")
DEFAULT_M3017_SYNTHESIS = Path(f"docs/{M3017_ID}.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_"
    "failure_localization_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_SOURCE_SPEC_COUNT = 16
EXPECTED_WORKLOAD_ROW_COUNT = 32
EXPECTED_EPISODE_ROW_COUNT = 32
EXPECTED_FAILURE_ROW_COUNT = 0
EXPECTED_PROFILE_BINDING_COUNT = 2
EXPECTED_PROFILE_SOURCE_AGGREGATE_COUNT = 32
EXPECTED_DIAGNOSTIC_COUNTS = {
    "success": 3,
    "collision": 5,
    "off_track": 23,
    "speed_too_low": 2,
}
EXPECTED_TERMINATION_COUNTS = {
    "": 3,
    "obstacle_collision": 4,
    "off_track": 23,
    "speed_too_low": 2,
}

CLAIM_SCOPE = (
    "M3018 Route A post-residual-stop new-source failure-localization "
    "materialization only; existing M3015 diagnostic episode rows may be "
    "grouped by profile, task source, task family, source family, termination, "
    "collision, and success flags. No reset, step, rollout, replay, validation, "
    "training, PPO, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, profile tuning, repair target selection, validation result, "
    "repair success, driver performance, paper, current-sim verdict, "
    "high-fidelity validation, finite-window-vs-GRU, full ideal driver, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair target selection, validation result, repair success, driver "
    "performance, current-sim verdict, paper evidence, high-fidelity "
    "validation readiness or result, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, level3 self-identification, controller/profile "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "profile tuning, training, replay, or PPO"
)

PATH_KEYS = [
    "summary",
    "failure_localization_rows",
    "profile_source_aggregate_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

LOCALIZATION_FIELDNAMES = [
    "localization_row_id",
    "source_episode_row_index",
    "seed",
    "eval_seed",
    "m3015_eval_seed",
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
    "profile_config_path",
    "checkpoint_path",
    "profile_env_history_length",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "completion_reason",
    "outcome_bucket",
    "outcome_family",
    "failure_family",
    "primary_failure_mode",
    "diagnostic_success",
    "diagnostic_collision",
    "diagnostic_obstacle_collision_termination",
    "diagnostic_offtrack",
    "diagnostic_speed_too_low",
    "diagnostic_blank_termination",
    "diagnostic_non_success",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
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
    "recoverability_window_success_available",
    "recoverability_window_success",
    "source_m3015_environment_reset_run",
    "source_m3015_environment_step_run",
    "source_m3015_policy_action_run",
    "source_m3015_policy_rollout_run",
    "m3018_no_execution_reanalysis",
    "m3018_environment_reset_run",
    "m3018_environment_step_run",
    "m3018_policy_action_run",
    "m3018_policy_rollout_run",
    "m3018_validation_run",
    "m3018_training_run",
    "m3018_replay_run",
    "m3018_ppo_run",
    "m3018_source_build_run",
    "m3018_ranking_run",
    "m3018_winner_selected",
    "m3018_checkpoint_mutated",
    "m3018_checkpoint_promoted",
    "m3018_profile_specific_tuning",
    "repair_target_selected",
    "future_route_selection_requires_m3019_audit",
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

PROFILE_SOURCE_AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "executable_source_family",
    "env_template_family",
    "scheduled_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_count",
    "collision_count",
    "obstacle_collision_termination_count",
    "offtrack_count",
    "speed_too_low_count",
    "blank_termination_count",
    "non_success_count",
    "primary_failure_mode_counts",
    "dominant_outcome_family",
    "dominant_failure_family",
    "min_clearance_margin_mean",
    "return_mean",
    "lateral_rmse_mean",
    "beta_abs_error_mean",
    "high_sideslip_fraction_mean",
    "off_track_severity_proxy_mean",
    "recoverability_window_success_count",
    "all_selected_metrics_finite",
    "m3018_no_execution_reanalysis",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "repair_target_selected",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3018",
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


def run_new_source_failure_localization_materialization_preflight(
    *,
    m3015_dir: Path | str = DEFAULT_M3015_DIR,
    m3016_audit: Path | str = DEFAULT_M3016_AUDIT,
    m3017_synthesis: Path | str = DEFAULT_M3017_SYNTHESIS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3015_dir=Path(m3015_dir),
        m3016_audit=Path(m3016_audit),
        m3017_synthesis=Path(m3017_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )

    localization_rows = build_failure_localization_rows(source["episode_rows"])
    aggregate_rows = build_profile_source_aggregate_rows(
        workload_rows=source["execution_workload_rows"],
        episode_rows=source["episode_rows"],
        failure_rows=source["failure_rows"],
    )
    write_csv_rows(paths["failure_localization_rows"], localization_rows, fieldnames=LOCALIZATION_FIELDNAMES)
    write_csv_rows(
        paths["profile_source_aggregate_rows"],
        aggregate_rows,
        fieldnames=PROFILE_SOURCE_AGGREGATE_FIELDNAMES,
    )
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]))
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()
    write_run_state(
        paths["run_state"],
        {
            "episode_row_count": len(source["episode_rows"]),
            "failure_row_count": len(source["failure_rows"]),
            "localization_row_count": len(localization_rows),
            "profile_source_aggregate_row_count": len(aggregate_rows),
            "execution_performed_by_m3018": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_without_summary_doc = all(
        paths[key].exists() for key in PATH_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        localization_rows_present=bool(localization_rows),
        aggregate_rows_present=bool(aggregate_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        aggregate_rows=aggregate_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        localization_rows=localization_rows,
        aggregate_rows=aggregate_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        localization_rows_present=bool(localization_rows),
        aggregate_rows_present=bool(aggregate_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        aggregate_rows=aggregate_rows,
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
        aggregate_rows=aggregate_rows,
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
            "episode_row_count": len(source["episode_rows"]),
            "failure_row_count": len(source["failure_rows"]),
            "localization_row_count": len(localization_rows),
            "profile_source_aggregate_row_count": len(aggregate_rows),
            "execution_performed_by_m3018": False,
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
        "failure_localization_rows": output_dir / "failure_localization_rows.csv",
        "profile_source_aggregate_rows": output_dir / "profile_source_aggregate_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3015_dir: Path,
    m3016_audit: Path,
    m3017_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3016_audit": m3016_audit,
        "m3017_synthesis": m3017_synthesis,
        "m3015_summary": m3015_dir / "summary.json",
        "execution_workload_rows": m3015_dir / "execution_workload_rows.csv",
        "episode_rows": m3015_dir / "episode_rows.csv",
        "failure_rows": m3015_dir / "failure_rows.csv",
        "profile_aggregate_rows": m3015_dir / "profile_aggregate_rows.csv",
        "source_aggregate_rows": m3015_dir / "source_aggregate_rows.csv",
        "claim_boundary_rows": m3015_dir / "claim_boundary_rows.csv",
        "gate_matrix": m3015_dir / "gate_matrix.csv",
        "run_state": m3015_dir / "run_state.json",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3016_audit_text": paths["m3016_audit"].read_text(encoding="utf-8")
        if source_exists["m3016_audit"]
        else "",
        "m3017_synthesis_text": paths["m3017_synthesis"].read_text(encoding="utf-8")
        if source_exists["m3017_synthesis"]
        else "",
        "m3015_summary": read_json(paths["m3015_summary"]) if source_exists["m3015_summary"] else {},
        "execution_workload_rows": read_csv_rows(paths["execution_workload_rows"]),
        "episode_rows": read_csv_rows(paths["episode_rows"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
        "profile_aggregate_rows": read_csv_rows(paths["profile_aggregate_rows"]),
        "source_aggregate_rows": read_csv_rows(paths["source_aggregate_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
        "run_state": read_json(paths["run_state"]) if source_exists["run_state"] else {},
    }


def build_failure_localization_rows(episode_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(episode_rows, start=1):
        outcome = outcome_family(row)
        termination = str(row.get("termination_reason", "")).strip()
        rows.append(
            {
                "localization_row_id": f"m3018-failure-localization-{index:04d}",
                "source_episode_row_index": index,
                "seed": row.get("seed", ""),
                "eval_seed": row.get("eval_seed", ""),
                "m3015_eval_seed": row.get("m3015_eval_seed", ""),
                "execution_workload_id": row.get("execution_workload_id", ""),
                "executable_workload_id": row.get("executable_workload_id", ""),
                "workload_id": row.get("workload_id", ""),
                "workload_contract_id": row.get("workload_contract_id", ""),
                "source_resolution_id": row.get("source_resolution_id", ""),
                "profile_binding_id": row.get("profile_binding_id", ""),
                "executable_source_spec_id": row.get("executable_source_spec_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "profile_binding_name": row.get("profile_binding_name", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "strata": row.get("strata", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "profile_config_path": row.get("profile_config_path", ""),
                "checkpoint_path": row.get("checkpoint_path", ""),
                "profile_env_history_length": row.get("profile_env_history_length", ""),
                "steps": row.get("steps", ""),
                "terminated": _bool(row.get("terminated", False)),
                "truncated": _bool(row.get("truncated", False)),
                "success": _bool(row.get("success", False)),
                "collision": _bool(row.get("collision", False)),
                "obstacle_completed": _bool(row.get("obstacle_completed", False)),
                "termination_reason": termination,
                "completion_reason": row.get("completion_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "outcome_family": outcome,
                "failure_family": failure_family(row),
                "primary_failure_mode": primary_failure_mode(row),
                "diagnostic_success": outcome == "success_obstacle_pass",
                "diagnostic_collision": _bool(row.get("collision", False)),
                "diagnostic_obstacle_collision_termination": termination == "obstacle_collision",
                "diagnostic_offtrack": termination == "off_track",
                "diagnostic_speed_too_low": termination == "speed_too_low",
                "diagnostic_blank_termination": termination == "",
                "diagnostic_non_success": outcome != "success_obstacle_pass",
                "min_obstacle_clearance": row.get("min_obstacle_clearance", ""),
                "obstacle_collision_radius": row.get("obstacle_collision_radius", ""),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "return": row.get("return", ""),
                "mean_reward": row.get("mean_reward", ""),
                "lateral_rmse": row.get("lateral_rmse", ""),
                "beta_abs_error_mean": row.get("beta_abs_error_mean", ""),
                "high_sideslip_fraction": row.get("high_sideslip_fraction", ""),
                "speed_mean": row.get("speed_mean", ""),
                "action_rate_mean": row.get("action_rate_mean", ""),
                "max_off_track_overshoot": row.get("max_off_track_overshoot", ""),
                "time_to_first_off_track_s": row.get("time_to_first_off_track_s", ""),
                "off_track_severity_proxy": row.get("off_track_severity_proxy", ""),
                "recoverability_window_success_available": _bool(
                    row.get("recoverability_window_success_available", False)
                ),
                "recoverability_window_success": _bool(row.get("recoverability_window_success", False)),
                "source_m3015_environment_reset_run": _bool(row.get("environment_reset_run", False)),
                "source_m3015_environment_step_run": _bool(row.get("environment_step_run", False)),
                "source_m3015_policy_action_run": _bool(row.get("policy_action_run", False)),
                "source_m3015_policy_rollout_run": _bool(row.get("policy_rollout_run", False)),
                "m3018_no_execution_reanalysis": True,
                "m3018_environment_reset_run": False,
                "m3018_environment_step_run": False,
                "m3018_policy_action_run": False,
                "m3018_policy_rollout_run": False,
                "m3018_validation_run": False,
                "m3018_training_run": False,
                "m3018_replay_run": False,
                "m3018_ppo_run": False,
                "m3018_source_build_run": False,
                "m3018_ranking_run": False,
                "m3018_winner_selected": False,
                "m3018_checkpoint_mutated": False,
                "m3018_checkpoint_promoted": False,
                "m3018_profile_specific_tuning": False,
                "repair_target_selected": False,
                "future_route_selection_requires_m3019_audit": True,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": _bool(row.get("hidden_oracle_actor_input_required", False)),
                "future_target_actor_input_required": _bool(row.get("future_target_actor_input_required", False)),
                "source_labels_actor_visible": _bool(row.get("source_labels_actor_visible", False)),
                "route_labels_actor_visible": _bool(row.get("route_labels_actor_visible", False)),
                "outcome_labels_actor_visible": _bool(row.get("outcome_labels_actor_visible", False)),
                "success_progress_labels_actor_visible": _bool(row.get("success_progress_labels_actor_visible", False)),
                "verdict_labels_actor_visible": _bool(row.get("verdict_labels_actor_visible", False)),
                "ttc_actor_input_required": _bool(row.get("ttc_actor_input_required", False)),
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
        )
    return rows


def build_profile_source_aggregate_rows(
    *,
    workload_rows: list[dict[str, str]],
    episode_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    scheduled_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    episodes_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    failures_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in workload_rows:
        scheduled_by_key[profile_source_key(row)].append(row)
    for row in episode_rows:
        episodes_by_key[profile_source_key(row)].append(row)
    for row in failure_rows:
        failures_by_key[profile_source_key(row)].append(row)

    rows: list[dict[str, Any]] = []
    for index, key in enumerate(sorted(scheduled_by_key), start=1):
        scheduled = scheduled_by_key[key]
        episodes = episodes_by_key.get(key, [])
        failures = failures_by_key.get(key, [])
        first = scheduled[0] if scheduled else (episodes[0] if episodes else {})
        outcome_counts = Counter(outcome_family(row) for row in episodes)
        failure_counts = Counter(failure_family(row) for row in episodes)
        termination_counts = Counter(str(row.get("termination_reason", "")).strip() for row in episodes)
        success_count = outcome_counts.get("success_obstacle_pass", 0)
        rows.append(
            {
                "aggregate_id": f"m3018-profile-source-aggregate-{index:04d}",
                "profile_name": first.get("profile_name", ""),
                "profile_binding_name": first.get("profile_binding_name", first.get("profile_name", "")),
                "binding_role": first.get("binding_role", ""),
                "task_source_id": first.get("task_source_id", ""),
                "task_family": first.get("task_family", ""),
                "source_edge": first.get("source_edge", ""),
                "window_tag": first.get("window_tag", ""),
                "strata": first.get("strata", ""),
                "executable_source_family": first.get("executable_source_family", ""),
                "env_template_family": first.get("env_template_family", ""),
                "scheduled_count": len(scheduled),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_count": success_count,
                "collision_count": sum(_bool(row.get("collision", False)) for row in episodes),
                "obstacle_collision_termination_count": int(termination_counts.get("obstacle_collision", 0)),
                "offtrack_count": int(termination_counts.get("off_track", 0)),
                "speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
                "blank_termination_count": int(termination_counts.get("", 0)),
                "non_success_count": len(episodes) - success_count + len(failures),
                "primary_failure_mode_counts": counts_text(Counter(primary_failure_mode(row) for row in episodes)),
                "dominant_outcome_family": dominant_counter_key(outcome_counts),
                "dominant_failure_family": dominant_counter_key(failure_counts),
                "min_clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "lateral_rmse_mean": mean_float(episodes, "lateral_rmse"),
                "beta_abs_error_mean": mean_float(episodes, "beta_abs_error_mean"),
                "high_sideslip_fraction_mean": mean_float(episodes, "high_sideslip_fraction"),
                "off_track_severity_proxy_mean": mean_float(episodes, "off_track_severity_proxy"),
                "recoverability_window_success_count": sum(
                    _bool(row.get("recoverability_window_success", False)) for row in episodes
                ),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else True,
                "m3018_no_execution_reanalysis": True,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "repair_target_selected": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def outcome_family(row: Mapping[str, Any]) -> str:
    termination = str(row.get("termination_reason", "")).strip()
    if _bool(row.get("success", False)):
        return "success_obstacle_pass"
    if _bool(row.get("collision", False)) or termination == "obstacle_collision":
        return "collision"
    if termination == "off_track":
        return "off_track"
    if termination == "speed_too_low":
        return "speed_too_low"
    if termination == "":
        return "blank_termination_non_success"
    return "other_non_success"


def failure_family(row: Mapping[str, Any]) -> str:
    family = outcome_family(row)
    if family == "success_obstacle_pass":
        return "success_context"
    if family == "collision":
        return "collision_clearance_failure"
    if family == "off_track":
        severity = max(
            _to_float(row.get("off_track_severity_proxy")),
            _to_float(row.get("max_off_track_overshoot")),
        )
        if np.isfinite(severity) and severity >= 0.075:
            return "offtrack_high_severity_recovery_failure"
        return "offtrack_recovery_failure"
    if family == "speed_too_low":
        return "speed_floor_context"
    if family == "blank_termination_non_success":
        return "unlabeled_non_success_context"
    return "other_non_success_context"


def primary_failure_mode(row: Mapping[str, Any]) -> str:
    family = outcome_family(row)
    if family == "success_obstacle_pass":
        return "diagnostic_success"
    if family == "collision":
        return "collision_or_obstacle_collision_termination"
    if family == "off_track":
        severity = max(
            _to_float(row.get("off_track_severity_proxy")),
            _to_float(row.get("max_off_track_overshoot")),
        )
        if np.isfinite(severity) and severity >= 0.075:
            return "off_track_high_severity"
        return "off_track"
    if family == "speed_too_low":
        return "speed_too_low"
    if family == "blank_termination_non_success":
        return "blank_termination_non_success"
    return "other_non_success"


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    localization_rows_present: bool,
    aggregate_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("failure_localization_materialized", "artifact", localization_rows_present, "failure_localization_rows.csv"),
        (
            "profile_source_aggregate_materialized",
            "artifact",
            aggregate_rows_present,
            "profile_source_aggregate_rows.csv",
        ),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_materialized", "artifact", artifacts_present, "summary.json"),
        ("doc_materialized", "artifact", artifacts_present, f"docs/{MILESTONE_ID}.md"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3019 audit manifest"),
        ("denominator_preserved", "diagnostic_accounting", localization_rows_present, "32 M3015 diagnostic rows"),
        ("failure_modes_classified", "diagnostic_accounting", localization_rows_present, "profile/source failure labels"),
    ]
    blocked = [
        ("reset_step_rollout_replay_execution", "execution", "M3015 artifacts only; no M3018 execution"),
        ("source_build", "execution", "future source-build manifest"),
        ("training_or_ppo", "execution", "future audited training manifest"),
        ("profile_specific_tuning", "execution", "future audited tuning route"),
        ("repair_target_selection", "repair", "M3019 audit before any repair target"),
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
        "claim_id": f"m3018_{claim_id}",
        "claim_family": family,
        "allowed_in_m3018": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    summary = source["m3015_summary"]
    episode_rows = source["episode_rows"]
    failure_rows = source["failure_rows"]
    workload_rows = source["execution_workload_rows"]
    source_ids = {str(row.get("task_source_id", "")) for row in episode_rows if row.get("task_source_id")}
    profile_names = {str(row.get("profile_name", "")) for row in episode_rows if row.get("profile_name")}
    workload_ids = {str(row.get("execution_workload_id", "")) for row in workload_rows if row.get("execution_workload_id")}
    episode_ids = {str(row.get("execution_workload_id", "")) for row in episode_rows if row.get("execution_workload_id")}
    outcome_counts = diagnostic_counts(episode_rows)
    termination_counts = dict(Counter(str(row.get("termination_reason", "")).strip() for row in episode_rows))
    aggregate_accounted_count = sum(int(row.get("accounted_count", 0)) for row in aggregate_rows)
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M3015/M3016/M3017/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m3016_accepts_m3015",
            "lineage",
            "accepts M3015" in source["m3016_audit_text"],
            "accepts M3015" in source["m3016_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3017_admits_m3018",
            "lineage",
            MILESTONE_ID in source["m3017_synthesis_text"],
            MILESTONE_ID in source["m3017_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3015_status_pass",
            "lineage",
            _bool(summary.get("status_pass", False))
            and _bool(summary.get("gate_matrix_pass", False))
            and _bool(summary.get("required_artifacts_present", False)),
            {
                "status_pass": summary.get("status_pass"),
                "gate_matrix_pass": summary.get("gate_matrix_pass"),
                "required_artifacts_present": summary.get("required_artifacts_present"),
            },
            "all true",
            "lineage_invalid",
        ),
        (
            "episode_denominator_preserved",
            "denominator",
            len(episode_rows) == EXPECTED_EPISODE_ROW_COUNT,
            len(episode_rows),
            EXPECTED_EPISODE_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "failure_rows_preserved",
            "denominator",
            len(failure_rows) == EXPECTED_FAILURE_ROW_COUNT,
            len(failure_rows),
            EXPECTED_FAILURE_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "workload_denominator_preserved",
            "denominator",
            len(workload_rows) == EXPECTED_WORKLOAD_ROW_COUNT and workload_ids == episode_ids,
            {"workload_rows": len(workload_rows), "episode_ids": len(episode_ids), "same_ids": workload_ids == episode_ids},
            EXPECTED_WORKLOAD_ROW_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "task_source_denominator_preserved",
            "denominator",
            len(source_ids) == EXPECTED_SOURCE_SPEC_COUNT,
            len(source_ids),
            EXPECTED_SOURCE_SPEC_COUNT,
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
            "localization_rows_account_all",
            "localization",
            len(localization_rows) == len(episode_rows),
            len(localization_rows),
            len(episode_rows),
            "metric_artifact",
        ),
        (
            "profile_source_aggregate_accounts_all",
            "localization",
            len(aggregate_rows) == EXPECTED_PROFILE_SOURCE_AGGREGATE_COUNT
            and aggregate_accounted_count == len(episode_rows) + len(failure_rows),
            {"rows": len(aggregate_rows), "accounted": aggregate_accounted_count},
            {"rows": EXPECTED_PROFILE_SOURCE_AGGREGATE_COUNT, "accounted": len(episode_rows) + len(failure_rows)},
            "metric_artifact",
        ),
        (
            "diagnostic_counts_match_summary",
            "metric",
            outcome_counts == EXPECTED_DIAGNOSTIC_COUNTS
            and outcome_counts["success"] == int(summary.get("diagnostic_success_count", -1))
            and outcome_counts["collision"] == int(summary.get("diagnostic_collision_count", -1))
            and outcome_counts["off_track"] == int(summary.get("diagnostic_offtrack_count", -1))
            and outcome_counts["speed_too_low"] == int(summary.get("diagnostic_speed_too_low_count", -1)),
            outcome_counts,
            EXPECTED_DIAGNOSTIC_COUNTS,
            "metric_artifact",
        ),
        (
            "termination_counts_match_summary",
            "metric",
            termination_counts == EXPECTED_TERMINATION_COUNTS
            and termination_counts == dict(summary.get("diagnostic_termination_counts", {})),
            termination_counts,
            EXPECTED_TERMINATION_COUNTS,
            "metric_artifact",
        ),
        (
            "selected_metrics_finite",
            "metric",
            selected_metrics_are_finite(episode_rows),
            selected_metrics_are_finite(episode_rows),
            True,
            "metric_artifact",
        ),
        (
            "actor_contract_preserved",
            "contract",
            int(summary.get("observation_shape", -1)) == P0_OBSERVATION_DIM
            and int(summary.get("action_shape", -1)) == ACTION_DIM
            and not any_hidden_actor_flag(localization_rows),
            {
                "observation_shape": summary.get("observation_shape"),
                "action_shape": summary.get("action_shape"),
                "hidden_actor_flags": any_hidden_actor_flag(localization_rows),
            },
            "observation 72 action 3 and no hidden actor labels",
            "contract_violation",
        ),
        (
            "no_m3018_execution_training_ranking_or_mutation",
            "contract",
            not any(forbidden_m3018_flag(row) for row in localization_rows + aggregate_rows),
            "all M3018 execution/training/ranking/mutation flags false",
            "all false",
            "contract_violation",
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
        "gate_id": f"m3018_{gate_id}",
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
    localization_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    episode_rows = source["episode_rows"]
    failure_rows = source["failure_rows"]
    workload_rows = source["execution_workload_rows"]
    outcome_counts = diagnostic_counts(episode_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")).strip() for row in episode_rows)
    profile_counts = Counter(str(row.get("profile_name", "")) for row in episode_rows)
    task_family_counts = Counter(str(row.get("task_family", "")) for row in episode_rows)
    source_family_counts = Counter(str(row.get("executable_source_family", "")) for row in episode_rows)
    failure_family_counts = Counter(str(row.get("failure_family", "")) for row in localization_rows)
    primary_failure_mode_counts = Counter(str(row.get("primary_failure_mode", "")) for row in localization_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    claim_boundary_rows_pass = all(_bool(row.get("status_pass", False)) for row in claim_rows)
    status_pass = bool(gate_matrix_pass and claim_boundary_rows_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "new_source_failure_localization_materialization_preflight_complete"
            if status_pass
            else "new_source_failure_localization_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3015_status_pass": _bool(source["m3015_summary"].get("status_pass", False)),
        "m3015_gate_matrix_pass": _bool(source["m3015_summary"].get("gate_matrix_pass", False)),
        "m3015_required_artifacts_present": _bool(
            source["m3015_summary"].get("required_artifacts_present", False)
        ),
        "source_spec_count": int(source["m3015_summary"].get("source_spec_count", 0)),
        "unique_task_source_count": len({row.get("task_source_id", "") for row in episode_rows}),
        "target_source_spec_count": EXPECTED_SOURCE_SPEC_COUNT,
        "scheduled_workload_row_count": len(workload_rows),
        "target_workload_row_count": EXPECTED_WORKLOAD_ROW_COUNT,
        "episode_row_count": len(episode_rows),
        "target_episode_row_count": EXPECTED_EPISODE_ROW_COUNT,
        "failure_row_count": len(failure_rows),
        "target_failure_row_count": EXPECTED_FAILURE_ROW_COUNT,
        "recorded_row_count": len(episode_rows) + len(failure_rows),
        "profile_binding_count": len({row.get("profile_name", "") for row in episode_rows}),
        "target_profile_binding_count": EXPECTED_PROFILE_BINDING_COUNT,
        "profile_counts": dict(sorted(profile_counts.items())),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "executable_source_family_counts": dict(sorted(source_family_counts.items())),
        "diagnostic_counts": outcome_counts,
        "diagnostic_success_count": outcome_counts["success"],
        "diagnostic_collision_count": outcome_counts["collision"],
        "diagnostic_offtrack_count": outcome_counts["off_track"],
        "diagnostic_speed_too_low_count": outcome_counts["speed_too_low"],
        "diagnostic_blank_termination_count": int(termination_counts.get("", 0)),
        "diagnostic_obstacle_collision_termination_count": int(termination_counts.get("obstacle_collision", 0)),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "failure_family_counts": dict(sorted(failure_family_counts.items())),
        "primary_failure_mode_counts": dict(sorted(primary_failure_mode_counts.items())),
        "failure_localization_row_count": len(localization_rows),
        "profile_source_aggregate_row_count": len(aggregate_rows),
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else True,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_boundary_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "ranking_run": False,
        "winner_selected": False,
        "repair_target_selected": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any_hidden_actor_flag(localization_rows),
        "future_target_actor_input_required": any_flag(localization_rows, "future_target_actor_input_required"),
        "source_labels_actor_visible": any_flag(localization_rows, "source_labels_actor_visible"),
        "route_labels_actor_visible": any_flag(localization_rows, "route_labels_actor_visible"),
        "outcome_labels_actor_visible": any_flag(localization_rows, "outcome_labels_actor_visible"),
        "success_progress_labels_actor_visible": any_flag(localization_rows, "success_progress_labels_actor_visible"),
        "verdict_labels_actor_visible": any_flag(localization_rows, "verdict_labels_actor_visible"),
        "ttc_actor_input_required": any_flag(localization_rows, "ttc_actor_input_required"),
        "success_rate_metric_recorded": False,
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
            "# M3018 Engineering Controller Route A Post-Residual-Stop New Source Failure Localization Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source specs: {summary['source_spec_count']}/{summary['target_source_spec_count']}",
            f"- scheduled workload rows: {summary['scheduled_workload_row_count']}/{summary['target_workload_row_count']}",
            f"- episode rows localized: {summary['episode_row_count']}/{summary['target_episode_row_count']}",
            f"- failure rows preserved: {summary['failure_row_count']}/{summary['target_failure_row_count']}",
            f"- failure localization rows: {summary['failure_localization_row_count']}",
            f"- profile/source aggregate rows: {summary['profile_source_aggregate_row_count']}",
            f"- diagnostic counts: {summary['diagnostic_counts']}",
            f"- termination counts: {summary['diagnostic_termination_counts']}",
            f"- failure families: {summary['failure_family_counts']}",
            f"- primary failure modes: {summary['primary_failure_mode_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- required artifacts present: {summary['required_artifacts_present']}",
            "",
            "## Boundary",
            "",
            "M3018 reanalyzes existing M3015 diagnostic rows only. It does not rerun environments, train, rank, promote, mutate checkpoints, tune profiles, validate, select a repair target, or claim performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Interpretation",
            "",
            "The materialized rows preserve the 32-row denominator and expose profile/source-localized failure families for M3019 audit. These rows remain diagnostic accounting artifacts only, not repair-success, validation, current-sim verdict, paper, high-fidelity, full-driver, finite-window-vs-GRU, ranking, promotion, or self-ID evidence.",
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
        "hypothesis": "A bounded result audit can accept or reject the M3018 failure-localization materialization before any repair training ranking validation performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "failure_localization_rows.csv"),
                str(output_dir / "profile_source_aggregate_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/summary.json",
                "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/episode_rows.csv",
                f"docs/{M3017_ID}.md",
                f"docs/{M3016_ID}.md",
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3017_ID}.json",
                f"experiments/manifests/{M3016_ID}.json",
                f"experiments/manifests/{M3015_ID}.json",
            ],
            "parent_objective": [
                "audit M3018 denominator-preserving failure-localization artifacts before any repair or continuation decision"
            ],
            "derived_from": [MILESTONE_ID, M3017_ID, M3016_ID, M3015_ID],
            "blocked_by": [
                "M3018 localization artifacts require M3019 result audit before route interpretation",
                "M3015 diagnostics are strongly negative and cannot be used for validation or performance claims",
            ],
            "supersedes": ["direct repair target selection from M3018 localization rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3019 must audit M3018 summary gate matrix row counts and claim boundaries",
            "M3019 must preserve the 32-row M3015 denominator and 16 task_source ids",
            "M3019 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M3019 must select exactly one next route or stop/synthesis state after audit",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote select a winner mutate checkpoints or tune profiles",
            "do not choose a repair target before auditing denominator and claim safety",
            "do not change actor input or action contract",
            "do not convert M3018 localization rows into performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_failure_localization_materialization_result_audit",
            "evidence_increment": "audits denominator-preserving M3018 failure-localization artifacts",
            "claim_scope": "Result audit only; no validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3018 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if M3018 dropped any M3015 diagnostic row",
                "stop if localization is insufficient to justify a bounded next route",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if localization is complete but next route remains ambiguous",
                "route to a bounded design only after M3019 accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3018 completes failure-localization materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3018 failure-localization materialization artifacts",
            "admission_evidence": [
                "M3018 summary and gate matrix",
                "M3018 failure localization profile/source aggregate claim and run-state artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO checkpoint mutation profile tuning or promotion",
                "no hidden/oracle/future-target/source/route/outcome/progress/verdict/TTC actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3019 status queue scoreboard and review",
                "one follow-up manifest only if M3019 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3019 audit accepts or rejects M3018 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3019 audits Route A engineering localization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3019; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3015 Route A new-source diagnostic execution only.",
            "negative_result_policy": "Preserve negative diagnostics and audit localization before any engineering continuation.",
            "allowed_claims": [
                "M3018 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized M3018 failure-localization artifacts",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M3019 cannot accept M3018 as complete and claim-safe",
                "M3019 would claim validation readiness driver performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID",
                "M3019 cannot choose exactly one bounded next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3019 audits M3018 artifacts row counts gates actor and claim boundaries",
            "M3019 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3019 hides M3018 missing artifacts or gate failures",
            "M3019 treats M3018 localization as validation readiness or performance verdict",
            "M3019 changes actor input or action contract",
            "M3019 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3019 audits M3018 artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "failure_localization_rows.csv"),
            str(output_dir / "profile_source_aggregate_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def diagnostic_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    row_list = list(rows) if not isinstance(rows, list) else rows
    termination_counts = Counter(str(row.get("termination_reason", "")).strip() for row in row_list)
    return {
        "success": sum(_bool(row.get("success", False)) for row in row_list),
        "collision": sum(_bool(row.get("collision", False)) for row in row_list),
        "off_track": int(termination_counts.get("off_track", 0)),
        "speed_too_low": int(termination_counts.get("speed_too_low", 0)),
    }


def profile_source_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row.get("profile_name", "")), str(row.get("task_source_id", "")))


def dominant_counter_key(counts: Counter[str]) -> str:
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def counts_text(counts: Counter[str]) -> str:
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts) if key)


def forbidden_m3018_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "m3018_environment_reset_run",
            "m3018_environment_step_run",
            "m3018_policy_action_run",
            "m3018_policy_rollout_run",
            "m3018_validation_run",
            "m3018_training_run",
            "m3018_replay_run",
            "m3018_ppo_run",
            "m3018_source_build_run",
            "m3018_ranking_run",
            "m3018_winner_selected",
            "m3018_checkpoint_mutated",
            "m3018_checkpoint_promoted",
            "m3018_profile_specific_tuning",
            "repair_target_selected",
            "ranking_claim_made",
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


def any_hidden_actor_flag(rows: Iterable[Mapping[str, Any]]) -> bool:
    return any(
        any(_bool(row.get(field, False)) for field in HIDDEN_ACTOR_FIELDS)
        for row in rows
    )


HIDDEN_ACTOR_FIELDS = (
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
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
    parser.add_argument("--m3015-dir", type=Path, default=DEFAULT_M3015_DIR)
    parser.add_argument("--m3016-audit", type=Path, default=DEFAULT_M3016_AUDIT)
    parser.add_argument("--m3017-synthesis", type=Path, default=DEFAULT_M3017_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_new_source_failure_localization_materialization_preflight(
        m3015_dir=args.m3015_dir,
        m3016_audit=args.m3016_audit,
        m3017_synthesis=args.m3017_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_rows={summary['episode_row_count']}")
    print(f"failure_localization_rows={summary['failure_localization_row_count']}")
    print(f"profile_source_aggregate_rows={summary['profile_source_aggregate_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
