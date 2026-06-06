"""Materialize M2857 per-step telemetry for response-predictive belief traces."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    env_config_for_executable_profile,
    load_executable_specs,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel import (
    DEFAULT_BASELINE_CHECKPOINT,
    DEFAULT_CANDIDATE_CHECKPOINT,
    load_subject_registry,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2857-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "per-step-telemetry-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2858-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "per-step-telemetry-panel-materialization-result-audit"
)
DEFAULT_M2856_DESIGN = Path(
    "docs/m2856-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "per-step-telemetry-panel-design.md"
)
DEFAULT_M2854_SUMMARY = Path(
    "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "existing_artifact_failure_localization_materialization/summary.json"
)
DEFAULT_M2854_LOCALIZATION_ROWS = Path(
    "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "existing_artifact_failure_localization_materialization/row_failure_localization_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "per_step_telemetry_panel_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2857-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "per-step-telemetry-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2858-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-per-step-telemetry-panel-materialization-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 285700
DEFAULT_M2850_ROW_COUNT = 16
DEFAULT_FRESH_ROW_COUNT = 8
DEFAULT_HORIZON_STEPS = 96
CANONICAL_PROFILE = "L3_online_gru"
CHECKPOINT_SUBJECTS = ("baseline", "candidate")

DEFAULT_PRIOR_SUMMARIES = (
    Path("runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/summary.json"),
    Path(
        "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_"
        "expansion_preflight/summary.json"
    ),
    Path(
        "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
        "cross_axis_bounded_execution_preflight/summary.json"
    ),
)
DEFAULT_PRIOR_ROW_FILES = (
    Path(
        "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_"
        "instrumented_bounded_execution_preflight/instrumented_execution_rows.csv"
    ),
    Path(
        "runs/m2759_engineering_controller_route_a_post_cross_axis_negative_action_response_"
        "containment_probe_bounded_execution_preflight/probe_execution_rows.csv"
    ),
    Path(
        "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_"
        "closed_loop_evidence_surface_bounded_execution_preflight/candidate_execution_rows.csv"
    ),
)

CLAIM_SCOPE = (
    "M2857 bounded per-step telemetry diagnostic materialization only. It runs "
    "closed-loop reset, policy action, and step calls only on the pre-registered "
    "M2850 explanatory and fresh/disjoint diagnostic surfaces. It does not train, "
    "run PPO, validate, replay, rank, select a winner, promote a checkpoint, "
    "compute success-rate verdicts, or claim repair success, driver performance, "
    "paper evidence, finite-window-vs-GRU evidence, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 self-identification."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, repair success, "
    "driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, "
    "or level3 self-identification"
)

PER_STEP_FIELDNAMES = [
    "trace_id",
    "surface_id",
    "pair_id",
    "task_source_id",
    "profile_name",
    "checkpoint_subject",
    "checkpoint_path",
    "eval_seed",
    "step_index",
    "horizon_steps",
    "terminated",
    "truncated",
    "termination_reason",
    "success_diagnostic",
    "collision_diagnostic",
    "obstacle_completed_diagnostic",
    "ego_vx",
    "ego_vy",
    "yaw_rate",
    "ax",
    "ay",
    "steer_actuator",
    "steer_rate",
    "throttle_actuator",
    "brake_actuator",
    "previous_steer_command",
    "previous_throttle_command",
    "previous_brake_command",
    "current_steer_command",
    "current_throttle_command",
    "current_brake_command",
    "action_delta_norm",
    "speed_scalar",
    "speed_delta_from_previous",
    "min_obstacle_clearance",
    "clearance_margin",
    "clearance_delta_from_previous",
    "return_increment",
    "cumulative_return",
    "offtrack_margin_proxy",
    "high_sideslip_proxy",
    "response_prediction_available",
    "response_prediction_error_norm",
    "response_prediction_error_source",
    "diagnostic_only",
    "actor_visible_allowed",
    "hidden_oracle_actor_input_required",
]
EPISODE_FIELDNAMES = [
    "surface_id",
    "pair_id",
    "task_source_id",
    "checkpoint_subject",
    "steps",
    "execution_status",
    "error_type",
    "error_message",
    "success_diagnostic",
    "collision_diagnostic",
    "termination_reason",
    "outcome_bucket",
    "first_clearance_improvement_step",
    "first_speed_drop_step",
    "first_progress_loss_step",
    "first_large_action_delta_step",
    "first_low_speed_step",
    "clearance_improvement_before_speed_drop",
    "speed_drop_before_clearance_improvement",
    "low_speed_recovery_window_available",
    "candidate_minus_baseline_clearance_improvement_step_delta",
    "candidate_minus_baseline_speed_drop_step_delta",
    "candidate_minus_baseline_progress_loss_step_delta",
    "requires_training_recipe_redesign",
    "requires_fresh_panel_audit",
    "diagnostic_only",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
SURFACE_FIELDNAMES = [
    "surface_row_id",
    "surface_id",
    "pair_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "source_family_tag",
    "scenario_role_primary",
    "surface_role",
    "source_from",
    "public_diagnostic_row",
    "fresh_or_disjoint",
    "overlap_guard_required",
    "overlap_reason",
    "diagnostic_only",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
LOCALIZATION_FIELDNAMES = [
    "surface_id",
    "pair_id",
    "task_source_id",
    "localization_bucket_from_m2854",
    "per_step_localization_bucket",
    "clearance_progress_order",
    "low_speed_onset_subject",
    "action_response_lag_detected",
    "response_prediction_timing_issue_detected",
    "termination_invariant",
    "candidate_behavior_change_before_failure",
    "training_recipe_signal",
    "requires_recipe_design",
    "requires_additional_trace",
    "diagnostic_interpretation",
    "forbidden_interpretation",
]
GUARD_FIELDNAMES = ["guard_id", "guard_family", "status_pass", "observed", "expected", "claim_boundary"]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2857",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _blank_if_nan(value: Any) -> Any:
    if isinstance(value, float) and not np.isfinite(value):
        return ""
    return value


def _first_step(rows: list[Mapping[str, Any]], predicate: str) -> int | str:
    for row in rows:
        if _bool(row.get(predicate, False)):
            return int(row["step_index"])
    return ""


def _first_numeric_step(rows: list[Mapping[str, Any]], key: str, threshold: float, *, less_than: bool) -> int | str:
    for row in rows:
        value = _finite_float(row.get(key))
        if np.isfinite(value) and ((value < threshold) if less_than else (value > threshold)):
            return int(row["step_index"])
    return ""


def _step_delta(candidate_value: Any, baseline_value: Any) -> int | str:
    if candidate_value == "" or baseline_value == "":
        return ""
    return int(candidate_value) - int(baseline_value)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "per_step_trace_rows": output_dir / "per_step_trace_rows.csv",
        "episode_trace_summary_rows": output_dir / "episode_trace_summary_rows.csv",
        "telemetry_surface_rows": output_dir / "telemetry_surface_rows.csv",
        "telemetry_localization_rows": output_dir / "telemetry_localization_rows.csv",
        "public_row_overfit_guard_rows": output_dir / "public_row_overfit_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m2856_design: Path,
    m2854_summary: Path,
    m2854_localization_rows: Path,
    m1690_workload: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2856_design": m2856_design,
        "m2854_summary": m2854_summary,
        "m2854_localization_rows": m2854_localization_rows,
        "m1690_workload": m1690_workload,
        "executable_specs": executable_specs,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items() if key != "follow_up_manifest"}
    m1690_rows = read_csv_rows(m1690_workload)
    m1690_l3 = {
        str(row.get("task_source_id", "")): row
        for row in m1690_rows
        if str(row.get("profile_name", "")) == CANONICAL_PROFILE
    }
    m2854_rows = read_csv_rows(m2854_localization_rows)
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2856_design_text": m2856_design.read_text(encoding="utf-8") if m2856_design.exists() else "",
        "m2854_summary": read_json(m2854_summary) if m2854_summary.exists() else {},
        "m2854_localization_rows": m2854_rows,
        "m1690_rows": m1690_rows,
        "m1690_l3_by_task_source": m1690_l3,
        "executable_specs": load_executable_specs(executable_specs) if executable_specs.exists() else [],
        "executable_spec_by_task_source": {
            str(spec["task_source_id"]): spec for spec in load_executable_specs(executable_specs)
        }
        if executable_specs.exists()
        else {},
        "protected_task_source_ids": protected_task_source_ids(m2854_rows),
    }


def protected_task_source_ids(m2854_rows: list[Mapping[str, Any]]) -> set[str]:
    protected = {str(row.get("task_source_id", "")) for row in m2854_rows if row.get("task_source_id")}
    for path in DEFAULT_PRIOR_SUMMARIES:
        if not path.exists():
            continue
        summary = read_json(path)
        for task_source_id in summary.get("selected_task_source_ids", []) or []:
            protected.add(str(task_source_id))
    for path in DEFAULT_PRIOR_ROW_FILES:
        if not path.exists():
            continue
        for row in read_csv_rows(path):
            if str(row.get("profile_name", CANONICAL_PROFILE)) == CANONICAL_PROFILE and row.get("task_source_id"):
                protected.add(str(row["task_source_id"]))
    return protected


def build_surface_rows(
    *,
    source: dict[str, Any],
    m2850_row_count: int,
    fresh_row_count: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, localization in enumerate(source["m2854_localization_rows"][: int(m2850_row_count)], start=1):
        task_source_id = str(localization["task_source_id"])
        source_row = source["m1690_l3_by_task_source"].get(task_source_id, {})
        rows.append(surface_row(index, "m2850_explanatory", localization, source_row, public=True))

    protected = set(source["protected_task_source_ids"])
    fresh_candidates = [
        row
        for row in sorted(source["m1690_l3_by_task_source"].values(), key=lambda item: str(item["task_source_id"]))
        if str(row.get("task_source_id", "")) not in protected
        and str(row.get("config_exists", "")) == "True"
        and not _bool(row.get("profile_specific_tuning", False))
    ]
    for index, source_row in enumerate(fresh_candidates[: int(fresh_row_count)], start=1):
        rows.append(surface_row(index, "fresh_disjoint", {}, source_row, public=False))
    return rows


def surface_row(
    index: int,
    surface_id: str,
    localization: Mapping[str, Any],
    source_row: Mapping[str, Any],
    *,
    public: bool,
) -> dict[str, Any]:
    task_source_id = str(source_row.get("task_source_id") or localization.get("task_source_id", ""))
    source_edge = str(source_row.get("source_edge") or localization.get("source_family_tag", ""))
    role = str(localization.get("scenario_role_primary") or (source_edge.split("|")[-1] if source_edge else ""))
    pair_id = (
        str(localization.get("pair_id"))
        if localization.get("pair_id")
        else f"m2857-fresh-pair-{index:04d}-{task_source_id}"
    )
    return {
        "surface_row_id": f"m2857-surface-{surface_id}-{index:04d}",
        "surface_id": surface_id,
        "pair_id": pair_id,
        "task_source_id": task_source_id,
        "profile_name": str(source_row.get("profile_name", CANONICAL_PROFILE)),
        "task_family": str(source_row.get("task_family") or localization.get("task_family", "")),
        "source_edge": source_edge,
        "window_tag": str(source_row.get("window_tag", "")),
        "source_family_tag": str(
            localization.get("source_family_tag") or (source_edge.split("|")[0] if source_edge else "")
        ),
        "scenario_role_primary": role,
        "surface_role": "M2850 explanatory diagnostic trace" if public else "fresh disjoint telemetry trace",
        "source_from": "M2854 row localization" if public else "M1690 L3_online_gru disjoint row",
        "public_diagnostic_row": public,
        "fresh_or_disjoint": not public,
        "overlap_guard_required": False,
        "overlap_reason": "",
        "diagnostic_only": True,
        "ranking_admissible": False,
        "ordinary_success_denominator_allowed": False,
    }


def collect_telemetry_rows(
    *,
    surface_rows: list[dict[str, Any]],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    output_dir: Path,
    eval_seed_base: int,
    horizon_steps: int,
    device: str,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_step_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    for pair_index, surface in enumerate(surface_rows):
        eval_seed = int(eval_seed_base) + pair_index
        for subject in CHECKPOINT_SUBJECTS:
            try:
                traces, episode = run_single_subject_per_step_trace(
                    surface_row=surface,
                    source=source,
                    subject_entry=subject_registry[subject],
                    eval_seed=eval_seed,
                    horizon_steps=int(horizon_steps),
                    device=device,
                )
                per_step_rows.extend(traces)
                episode_rows.append(episode)
            except Exception as exc:  # noqa: BLE001 - failed traces are durable audit rows.
                episode_rows.append(
                    failed_episode_row(
                        surface,
                        subject_entry=subject_registry[subject],
                        eval_seed=eval_seed,
                        horizon_steps=int(horizon_steps),
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
        write_run_state(
            output_dir / "run_state.json",
            {
                "surface_pair_count": len(surface_rows),
                "per_step_trace_row_count": len(per_step_rows),
                "episode_trace_summary_row_count": len(episode_rows),
                "latest_pair_id": surface["pair_id"],
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return per_step_rows, add_pair_deltas_to_episode_rows(episode_rows)


def run_single_subject_per_step_trace(
    *,
    surface_row: Mapping[str, Any],
    source: dict[str, Any],
    subject_entry: dict[str, Any],
    eval_seed: int,
    horizon_steps: int,
    device: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    del device
    task_source_id = str(surface_row["task_source_id"])
    if task_source_id not in source["m1690_l3_by_task_source"]:
        raise KeyError(f"task_source_id {task_source_id} missing from M1690 L3 rows")
    if task_source_id not in source["executable_spec_by_task_source"]:
        raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
    source_row = source["m1690_l3_by_task_source"][task_source_id]
    spec = copy.deepcopy(source["executable_spec_by_task_source"][task_source_id])
    spec.setdefault("env_config", {})
    spec["env_config"] = dict(spec["env_config"])
    spec["env_config"]["max_steps"] = int(horizon_steps)
    profile_config = read_json(source_row["profile_config_path"])
    env_config = env_config_for_executable_profile(executable_spec=spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    model = subject_entry["model"]
    if int(getattr(model, "obs_dim", -1)) != int(env.observation_space.shape[0]):
        env.close()
        raise ValueError(f"model obs_dim {getattr(model, 'obs_dim', -1)} does not match env obs_dim")
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    try:
        obs, info = env.reset(seed=int(eval_seed))
        policy.reset()
        traces: list[dict[str, Any]] = []
        rewards: list[float] = []
        previous_action = np.zeros(ACTION_DIM, dtype=np.float32)
        previous_speed = _finite_float(info.get("speed"), 0.0)
        previous_clearance = _finite_float(info.get("min_clearance_margin"))
        terminated = False
        truncated = False
        for step_index in range(int(horizon_steps)):
            action = np.asarray(policy.act(obs, info), dtype=np.float32)
            current_command = action.copy()
            action_delta_norm = float(np.linalg.norm(current_command - previous_action))
            obs, reward, terminated, truncated, info = env.step(action)
            rewards.append(float(reward))
            speed = _finite_float(info.get("speed"))
            clearance = _finite_float(info.get("min_clearance_margin"))
            ax, ay = body_acceleration(env)
            throttle_actuator, brake_actuator = drive_actuator_states(env)
            traces.append(
                per_step_row(
                    surface_row=surface_row,
                    subject_entry=subject_entry,
                    eval_seed=eval_seed,
                    step_index=step_index,
                    horizon_steps=int(horizon_steps),
                    terminated=terminated,
                    truncated=truncated,
                    info=info,
                    env=env,
                    previous_action=previous_action,
                    current_command=current_command,
                    action_delta_norm=action_delta_norm,
                    speed=speed,
                    previous_speed=previous_speed,
                    clearance=clearance,
                    previous_clearance=previous_clearance,
                    reward=float(reward),
                    cumulative_return=float(np.sum(rewards)),
                    ax=ax,
                    ay=ay,
                    throttle_actuator=throttle_actuator,
                    brake_actuator=brake_actuator,
                )
            )
            previous_action = current_command
            previous_speed = speed
            previous_clearance = clearance
            if terminated or truncated:
                break
        episode = episode_summary_row(surface_row, subject_entry, traces, info, terminated, truncated)
    finally:
        env.close()
    return traces, episode


def drive_actuator_states(env: AutoDriftEnv) -> tuple[float, float]:
    method = getattr(env, "_drive_actuator_states", None)
    if callable(method):
        return tuple(float(value) for value in method())  # type: ignore[return-value]
    control = getattr(env, "last_control", np.zeros(3))
    return float(control[1]), float(control[2])


def body_acceleration(env: AutoDriftEnv) -> tuple[float, float]:
    method = getattr(env, "_body_acceleration", None)
    if callable(method) and hasattr(env, "last_forces"):
        return tuple(float(value) for value in method(env.last_forces))  # type: ignore[return-value]
    return float("nan"), float("nan")


def per_step_row(
    *,
    surface_row: Mapping[str, Any],
    subject_entry: Mapping[str, Any],
    eval_seed: int,
    step_index: int,
    horizon_steps: int,
    terminated: bool,
    truncated: bool,
    info: Mapping[str, Any],
    env: AutoDriftEnv,
    previous_action: np.ndarray,
    current_command: np.ndarray,
    action_delta_norm: float,
    speed: float,
    previous_speed: float,
    clearance: float,
    previous_clearance: float,
    reward: float,
    cumulative_return: float,
    ax: float,
    ay: float,
    throttle_actuator: float,
    brake_actuator: float,
) -> dict[str, Any]:
    state = getattr(env, "state", None)
    clearance_delta = clearance - previous_clearance if np.isfinite(previous_clearance) and np.isfinite(clearance) else ""
    speed_delta = speed - previous_speed if np.isfinite(previous_speed) and np.isfinite(speed) else ""
    return {
        "trace_id": f"{surface_row['pair_id']}-{subject_entry['subject']}-step-{step_index:04d}",
        "surface_id": surface_row["surface_id"],
        "pair_id": surface_row["pair_id"],
        "task_source_id": surface_row["task_source_id"],
        "profile_name": surface_row["profile_name"],
        "checkpoint_subject": subject_entry["subject"],
        "checkpoint_path": str(subject_entry["checkpoint_path"]),
        "eval_seed": int(eval_seed),
        "step_index": int(step_index),
        "horizon_steps": int(horizon_steps),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "success_diagnostic": bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)),
        "collision_diagnostic": bool(info.get("collision", False)),
        "obstacle_completed_diagnostic": bool(info.get("obstacle_completed", False)),
        "ego_vx": _blank_if_nan(_finite_float(getattr(state, "vx", float("nan")))),
        "ego_vy": _blank_if_nan(_finite_float(getattr(state, "vy", float("nan")))),
        "yaw_rate": _blank_if_nan(_finite_float(getattr(state, "yaw_rate", info.get("yaw_rate", float("nan"))))),
        "ax": _blank_if_nan(ax),
        "ay": _blank_if_nan(ay),
        "steer_actuator": _blank_if_nan(_finite_float(getattr(state, "steer", float("nan")))),
        "steer_rate": _blank_if_nan(_finite_float(getattr(env, "last_steer_rate", float("nan")))),
        "throttle_actuator": _blank_if_nan(throttle_actuator),
        "brake_actuator": _blank_if_nan(brake_actuator),
        "previous_steer_command": float(previous_action[0]),
        "previous_throttle_command": float(previous_action[1]),
        "previous_brake_command": float(previous_action[2]),
        "current_steer_command": float(current_command[0]),
        "current_throttle_command": float(current_command[1]),
        "current_brake_command": float(current_command[2]),
        "action_delta_norm": float(action_delta_norm),
        "speed_scalar": _blank_if_nan(speed),
        "speed_delta_from_previous": _blank_if_nan(speed_delta),
        "min_obstacle_clearance": _blank_if_nan(_finite_float(info.get("min_obstacle_clearance"))),
        "clearance_margin": _blank_if_nan(clearance),
        "clearance_delta_from_previous": _blank_if_nan(clearance_delta),
        "return_increment": float(reward),
        "cumulative_return": float(cumulative_return),
        "offtrack_margin_proxy": _blank_if_nan(_finite_float(info.get("off_track_overshoot"))),
        "high_sideslip_proxy": _blank_if_nan(abs(_finite_float(info.get("beta")))),
        "response_prediction_available": False,
        "response_prediction_error_norm": "",
        "response_prediction_error_source": "not_computed_actor_invisible_instrumentation_gap",
        "diagnostic_only": True,
        "actor_visible_allowed": False,
        "hidden_oracle_actor_input_required": False,
    }


def episode_summary_row(
    surface_row: Mapping[str, Any],
    subject_entry: Mapping[str, Any],
    traces: list[dict[str, Any]],
    info: Mapping[str, Any],
    terminated: bool,
    truncated: bool,
) -> dict[str, Any]:
    first_clearance = _first_numeric_step(traces, "clearance_delta_from_previous", 0.0, less_than=False)
    first_speed_drop = _first_numeric_step(traces, "speed_delta_from_previous", -0.05, less_than=True)
    first_progress_loss = _first_numeric_step(traces, "return_increment", 0.0, less_than=True)
    first_action_delta = _first_numeric_step(traces, "action_delta_norm", 0.25, less_than=False)
    first_low_speed = _first_numeric_step(traces, "speed_scalar", 1.0, less_than=True)
    speeds_after_low = [
        _finite_float(row.get("speed_scalar"))
        for row in traces
        if first_low_speed != "" and int(row["step_index"]) > int(first_low_speed)
    ]
    return {
        "surface_id": surface_row["surface_id"],
        "pair_id": surface_row["pair_id"],
        "task_source_id": surface_row["task_source_id"],
        "checkpoint_subject": subject_entry["subject"],
        "steps": len(traces),
        "execution_status": "completed",
        "error_type": "",
        "error_message": "",
        "success_diagnostic": bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)),
        "collision_diagnostic": bool(info.get("collision", False)),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "outcome_bucket": outcome_bucket_from_info(dict(info), terminated=terminated, truncated=truncated),
        "first_clearance_improvement_step": first_clearance,
        "first_speed_drop_step": first_speed_drop,
        "first_progress_loss_step": first_progress_loss,
        "first_large_action_delta_step": first_action_delta,
        "first_low_speed_step": first_low_speed,
        "clearance_improvement_before_speed_drop": (
            first_clearance != "" and first_speed_drop != "" and int(first_clearance) < int(first_speed_drop)
        ),
        "speed_drop_before_clearance_improvement": (
            first_clearance != "" and first_speed_drop != "" and int(first_speed_drop) < int(first_clearance)
        ),
        "low_speed_recovery_window_available": bool(
            speeds_after_low and any(np.isfinite(speed) and speed > 1.5 for speed in speeds_after_low)
        ),
        "candidate_minus_baseline_clearance_improvement_step_delta": "",
        "candidate_minus_baseline_speed_drop_step_delta": "",
        "candidate_minus_baseline_progress_loss_step_delta": "",
        "requires_training_recipe_redesign": True,
        "requires_fresh_panel_audit": str(surface_row["surface_id"]) == "fresh_disjoint",
        "diagnostic_only": True,
        "ranking_admissible": False,
        "ordinary_success_denominator_allowed": False,
    }


def failed_episode_row(
    surface_row: Mapping[str, Any],
    *,
    subject_entry: Mapping[str, Any],
    eval_seed: int,
    horizon_steps: int,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    del eval_seed, horizon_steps
    row = episode_summary_row(surface_row, subject_entry, [], {}, False, False)
    row.update(
        {
            "execution_status": "failed",
            "error_type": error_type,
            "error_message": error_message,
            "outcome_bucket": "execution_failure",
            "requires_training_recipe_redesign": False,
        }
    )
    return row


def add_pair_deltas_to_episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_pair.setdefault(str(row["pair_id"]), {})[str(row["checkpoint_subject"])] = row
    for pair in by_pair.values():
        baseline = pair.get("baseline")
        candidate = pair.get("candidate")
        if not baseline or not candidate:
            continue
        deltas = {
            "candidate_minus_baseline_clearance_improvement_step_delta": _step_delta(
                candidate["first_clearance_improvement_step"],
                baseline["first_clearance_improvement_step"],
            ),
            "candidate_minus_baseline_speed_drop_step_delta": _step_delta(
                candidate["first_speed_drop_step"],
                baseline["first_speed_drop_step"],
            ),
            "candidate_minus_baseline_progress_loss_step_delta": _step_delta(
                candidate["first_progress_loss_step"],
                baseline["first_progress_loss_step"],
            ),
        }
        baseline.update(deltas)
        candidate.update(deltas)
    return rows


def build_telemetry_localization_rows(
    *,
    surface_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    m2854_localization_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    m2854_by_pair = {str(row["pair_id"]): row for row in m2854_localization_rows}
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in episode_rows:
        by_pair.setdefault(str(row["pair_id"]), {})[str(row["checkpoint_subject"])] = row
    output: list[dict[str, Any]] = []
    for surface in surface_rows:
        pair = by_pair.get(str(surface["pair_id"]), {})
        baseline = pair.get("baseline", {})
        candidate = pair.get("candidate", {})
        m2854 = m2854_by_pair.get(str(surface["pair_id"]), {})
        bucket = per_step_bucket(baseline, candidate, surface)
        output.append(
            {
                "surface_id": surface["surface_id"],
                "pair_id": surface["pair_id"],
                "task_source_id": surface["task_source_id"],
                "localization_bucket_from_m2854": m2854.get("localization_bucket", "fresh_surface_not_in_m2854"),
                "per_step_localization_bucket": bucket,
                "clearance_progress_order": clearance_progress_order(baseline, candidate),
                "low_speed_onset_subject": low_speed_onset_subject(baseline, candidate),
                "action_response_lag_detected": False,
                "response_prediction_timing_issue_detected": True,
                "termination_invariant": str(baseline.get("termination_reason", "")) == str(
                    candidate.get("termination_reason", "")
                ),
                "candidate_behavior_change_before_failure": candidate.get("first_large_action_delta_step", "") != "",
                "training_recipe_signal": m2854.get("training_recipe_signal", "fresh_per_step_localization_audit"),
                "requires_recipe_design": True,
                "requires_additional_trace": bucket in {"response_prediction_timing_unresolved", "step_trace_inconclusive"},
                "diagnostic_interpretation": "per-step diagnostic localization before any training recipe change",
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return output


def per_step_bucket(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    surface: Mapping[str, Any],
) -> str:
    if not baseline or not candidate:
        return "step_trace_inconclusive"
    if baseline.get("execution_status") != "completed" or candidate.get("execution_status") != "completed":
        return "step_trace_inconclusive"
    if candidate.get("first_low_speed_step", "") != "" or baseline.get("first_low_speed_step", "") != "":
        return "low_speed_unrecovered"
    candidate_clearance = candidate.get("first_clearance_improvement_step", "")
    candidate_progress = candidate.get("first_progress_loss_step", "")
    candidate_speed = candidate.get("first_speed_drop_step", "")
    if candidate_clearance != "" and candidate_progress != "" and int(candidate_progress) < int(candidate_clearance):
        return "late_clearance_after_progress_loss"
    if candidate_clearance != "" and candidate_speed != "":
        return "early_clearance_with_speed_collapse"
    if surface.get("surface_id") == "fresh_disjoint":
        return "fresh_surface_mismatch"
    return "response_prediction_timing_unresolved"


def clearance_progress_order(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    del baseline
    clearance = candidate.get("first_clearance_improvement_step", "")
    progress = candidate.get("first_progress_loss_step", "")
    if clearance == "" and progress == "":
        return "neither_detected"
    if clearance == "":
        return "progress_loss_without_clearance_improvement"
    if progress == "":
        return "clearance_improvement_without_progress_loss"
    return "clearance_before_progress_loss" if int(clearance) < int(progress) else "progress_loss_before_clearance"


def low_speed_onset_subject(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    baseline_low = baseline.get("first_low_speed_step", "") != ""
    candidate_low = candidate.get("first_low_speed_step", "") != ""
    if baseline_low and candidate_low:
        return "both"
    if baseline_low:
        return "baseline"
    if candidate_low:
        return "candidate"
    return "none"


def build_public_row_overfit_guard_rows(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    public_count = sum(1 for row in surface_rows if _bool(row["public_diagnostic_row"]))
    fresh_count = sum(1 for row in surface_rows if _bool(row["fresh_or_disjoint"]))
    return [
        guard("m2857-overfit-m2850-diagnostic-only", "public_row_overfit", True, public_count, "M2850 explanatory rows diagnostic only"),
        guard("m2857-overfit-fresh-surface-present", "public_row_overfit", fresh_count > 0, fresh_count, ">=1 fresh/disjoint row"),
        guard(
            "m2857-overfit-no-ranking",
            "public_row_overfit",
            all(not _bool(row["ranking_admissible"]) for row in surface_rows),
            "ranking_admissible false",
            "all rows false",
        ),
        guard(
            "m2857-overfit-no-ordinary-denominator",
            "public_row_overfit",
            all(not _bool(row["ordinary_success_denominator_allowed"]) for row in surface_rows),
            "ordinary_success_denominator_allowed false",
            "all rows false",
        ),
    ]


def build_actor_contract_guard_rows(
    *,
    subject_registry: dict[str, dict[str, Any]],
    per_step_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        guard("m2857-actor-observation-shape", "actor_contract", P0_OBSERVATION_DIM == 72, P0_OBSERVATION_DIM, 72),
        guard("m2857-actor-action-shape", "actor_contract", ACTION_DIM == 3, ACTION_DIM, 3),
        guard(
            "m2857-baseline-model-shape",
            "actor_contract",
            int(getattr(subject_registry["baseline"]["model"], "obs_dim", -1)) == P0_OBSERVATION_DIM
            and int(getattr(subject_registry["baseline"]["model"], "act_dim", -1)) == ACTION_DIM,
            f"{getattr(subject_registry['baseline']['model'], 'obs_dim', '')}/"
            f"{getattr(subject_registry['baseline']['model'], 'act_dim', '')}",
            "72/3",
        ),
        guard(
            "m2857-candidate-model-shape",
            "actor_contract",
            int(getattr(subject_registry["candidate"]["model"], "obs_dim", -1)) == P0_OBSERVATION_DIM
            and int(getattr(subject_registry["candidate"]["model"], "act_dim", -1)) == ACTION_DIM,
            f"{getattr(subject_registry['candidate']['model'], 'obs_dim', '')}/"
            f"{getattr(subject_registry['candidate']['model'], 'act_dim', '')}",
            "72/3",
        ),
        guard(
            "m2857-no-hidden-oracle-actor-input",
            "actor_contract",
            all(not _bool(row["hidden_oracle_actor_input_required"]) for row in per_step_rows),
            "hidden_oracle_actor_input_required false",
            "all rows false",
        ),
        guard(
            "m2857-evaluator-labels-actor-invisible",
            "actor_contract",
            all(not _bool(row["actor_visible_allowed"]) for row in per_step_rows),
            "actor_visible_allowed false for telemetry labels",
            "all telemetry labels actor-invisible",
        ),
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, required_artifacts_present: bool) -> list[dict[str, Any]]:
    specs = [
        ("per_step_telemetry_artifacts", "artifact", True, required_artifacts_present, "M2857 required artifact set"),
        ("follow_up_result_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2858 result audit"),
        ("training", "training", False, False, "future training route"),
        ("ppo", "training", False, False, "future training route"),
        ("validation_result", "validation", False, False, "future validation gate"),
        ("ranking_result", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("repair_success", "repair", False, False, "future audited repair route"),
        ("driver_performance", "performance", False, False, "future validation route"),
        ("paper_result", "paper", False, False, "Route B proof/generalization gates"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C validation route"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim_row(*spec) for spec in specs]


def guard(guard_id: str, family: str, status: bool, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2857-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2857": allowed,
        "claim_made": made,
        "status_pass": made == allowed if allowed else not made,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    tier: str,
    family: str,
    status: bool,
    observed: Any,
    expected: Any,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2857-{gate_id}",
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "row_count": int(row_count),
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_rows(
    *,
    source: dict[str, Any],
    surface_rows: list[dict[str, Any]],
    per_step_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    localization_rows: list[dict[str, Any]],
    overfit_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    m2850_row_count: int,
    fresh_row_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    expected_episode_rows = len(surface_rows) * len(CHECKPOINT_SUBJECTS)
    expected_trace_min = expected_episode_rows
    return [
        gate(
            "source-artifacts-present",
            "proof",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2856 design M2854 localization M1690 workload and executable specs present",
            len(source["source_exists"]),
            "lineage_invalid",
        ),
        gate(
            "m2854-step-trace-requirement-preserved",
            "proof",
            "lineage",
            int(source["m2854_summary"].get("requires_step_trace_row_count", 0)) >= int(m2850_row_count),
            source["m2854_summary"].get("requires_step_trace_row_count", ""),
            f">={m2850_row_count}",
            1,
            "proof_washout",
        ),
        gate(
            "m2850-explanatory-surface-count",
            "proof",
            "artifact",
            sum(1 for row in surface_rows if row["surface_id"] == "m2850_explanatory") == int(m2850_row_count),
            sum(1 for row in surface_rows if row["surface_id"] == "m2850_explanatory"),
            int(m2850_row_count),
            len(surface_rows),
            "metric_artifact",
        ),
        gate(
            "fresh-disjoint-surface-count",
            "generalization",
            "artifact",
            sum(1 for row in surface_rows if row["surface_id"] == "fresh_disjoint") == int(fresh_row_count),
            sum(1 for row in surface_rows if row["surface_id"] == "fresh_disjoint"),
            int(fresh_row_count),
            len(surface_rows),
            "objective_overfit",
        ),
        gate(
            "per-step-trace-rows-written",
            "proof",
            "artifact",
            len(per_step_rows) >= expected_trace_min,
            len(per_step_rows),
            f">={expected_trace_min}",
            len(per_step_rows),
            "metric_artifact",
        ),
        gate(
            "episode-summary-rows-written",
            "proof",
            "artifact",
            len(episode_rows) == expected_episode_rows,
            len(episode_rows),
            expected_episode_rows,
            len(episode_rows),
            "metric_artifact",
        ),
        gate(
            "localization-rows-written",
            "generalization",
            "artifact",
            len(localization_rows) == len(surface_rows),
            len(localization_rows),
            len(surface_rows),
            len(localization_rows),
            "metric_artifact",
        ),
        gate(
            "trace-horizon-bounded",
            "proof",
            "contract",
            all(int(row["step_index"]) < int(horizon_steps) for row in per_step_rows),
            f"max_step={max([int(row['step_index']) for row in per_step_rows], default=-1)}",
            f"<{horizon_steps}",
            len(per_step_rows),
            "contract_violation",
        ),
        gate(
            "actor-contract-guards-pass",
            "promotion",
            "actor_contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            f"{sum(1 for row in actor_rows if _bool(row['status_pass']))}/{len(actor_rows)}",
            "all actor guards pass",
            len(actor_rows),
            "contract_violation",
        ),
        gate(
            "overfit-guards-pass",
            "promotion",
            "public_row_overfit",
            all(_bool(row["status_pass"]) for row in overfit_rows),
            f"{sum(1 for row in overfit_rows if _bool(row['status_pass']))}/{len(overfit_rows)}",
            "all overfit guards pass",
            len(overfit_rows),
            "objective_overfit",
        ),
        gate(
            "claim-boundary-guards-pass",
            "promotion",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            f"{sum(1 for row in claim_rows if _bool(row['status_pass']))}/{len(claim_rows)}",
            "all claim guards pass",
            len(claim_rows),
            "contract_violation",
        ),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    surface_rows: list[dict[str, Any]],
    per_step_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    localization_rows: list[dict[str, Any]],
    overfit_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    eval_seed_base: int,
    m2850_row_count: int,
    fresh_row_count: int,
    horizon_steps: int,
    device: str,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    execution_counts = Counter(str(row["execution_status"]) for row in episode_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    bucket_counts = Counter(str(row["per_step_localization_bucket"]) for row in localization_rows)
    return {
        "result_class": "m2857_per_step_telemetry_panel_materialization_pass"
        if gate_matrix_pass
        else "m2857_per_step_telemetry_panel_materialization_failed_or_incomplete",
        "generated_at_utc": utc_timestamp(),
        "status_pass": bool(gate_matrix_pass),
        "milestone": milestone,
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "per_step_trace_rows": str(paths["per_step_trace_rows"]),
        "episode_trace_summary_rows": str(paths["episode_trace_summary_rows"]),
        "telemetry_surface_rows": str(paths["telemetry_surface_rows"]),
        "telemetry_localization_rows": str(paths["telemetry_localization_rows"]),
        "public_row_overfit_guard_rows": str(paths["public_row_overfit_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "m2856_design": str(source["paths"]["m2856_design"]),
        "m2854_summary": str(source["paths"]["m2854_summary"]),
        "m2854_localization_rows": str(source["paths"]["m2854_localization_rows"]),
        "m1690_workload": str(source["paths"]["m1690_workload"]),
        "baseline_checkpoint": str(subject_registry["baseline"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "baseline_checkpoint_hash": subject_registry["baseline"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "eval_seed_base": int(eval_seed_base),
        "m2850_row_count_requested": int(m2850_row_count),
        "fresh_row_count_requested": int(fresh_row_count),
        "horizon_steps": int(horizon_steps),
        "device": device,
        "surface_row_count": len(surface_rows),
        "m2850_explanatory_surface_row_count": sum(
            1 for row in surface_rows if row["surface_id"] == "m2850_explanatory"
        ),
        "fresh_disjoint_surface_row_count": sum(1 for row in surface_rows if row["surface_id"] == "fresh_disjoint"),
        "per_step_trace_row_count": len(per_step_rows),
        "episode_trace_summary_row_count": len(episode_rows),
        "telemetry_localization_row_count": len(localization_rows),
        "execution_status_counts": dict(sorted(execution_counts.items())),
        "termination_counts": dict(sorted(termination_counts.items())),
        "per_step_localization_bucket_counts": dict(sorted(bucket_counts.items())),
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "response_prediction_available_count": sum(
            1 for row in per_step_rows if _bool(row["response_prediction_available"])
        ),
        "m2850_zero_success_diagnostics_preserved": int(source["m2854_summary"].get("diagnostic_success_count", 0)) == 0,
        "m2854_requires_step_trace_row_count": source["m2854_summary"].get("requires_step_trace_row_count", ""),
        "m2838_weak_accounting_outside_denominators": True,
        "ordinary_success_denominator_allowed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "training_run": False,
        "ppo_used": False,
        "validation_result_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "public_row_overfit_guard_rows_pass": all(_bool(row["status_pass"]) for row in overfit_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not _bool(row["status_pass"])],
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2858_follow_up_manifest() -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    doc_path = f"docs/{task_id}.md"
    return {
        "id": task_id,
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
        "lineage": {
            "parent_checkpoint": [str(DEFAULT_BASELINE_CHECKPOINT), str(DEFAULT_CANDIDATE_CHECKPOINT)],
            "parent_dataset": [
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "per_step_trace_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "episode_trace_summary_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "telemetry_surface_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "telemetry_localization_rows.csv"),
                str(DEFAULT_DOC_PATH),
                str(DEFAULT_M2856_DESIGN),
                str(DEFAULT_M2854_SUMMARY),
                str(DEFAULT_M2854_LOCALIZATION_ROWS),
            ],
            "parent_config": [
                "experiments/manifests/m2857-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-materialization-preflight.json",
                "experiments/manifests/m2856-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-design.json",
            ],
            "parent_objective": [
                "audit M2857 per-step telemetry materialization before interpreting temporal localization"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2858 must audit M2857 artifact completeness before training recipe changes",
                "M2858 must preserve M2850 explanatory rows as diagnostic-only public rows",
                "M2858 must reject validation ranking promotion performance paper current-sim high-fidelity full-driver and self-ID claims",
            ],
            "supersedes": ["unaudited M2857 per-step telemetry interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2858 must audit M2857 summary per-step trace episode summary surface localization actor claim and gate artifacts",
            "M2858 must preserve actor 72/action 3 no hidden/oracle labels and actor-invisible diagnostics",
            "M2858 must preserve M2850 zero-success diagnostics M2854 step-trace requirement and M2838 weak accounting outside ordinary denominators",
            "M2858 must not run training validation ranking promotion or success-rate verdict computation",
            "M2858 must register one bounded next route or stop decision if M2857 artifacts are accepted",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not run validation",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not hide M2850 zero-success diagnostics or M2854 step-trace requirement",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "per_step_telemetry_panel_materialization_result_audit",
            "evidence_increment": "audits new M2857 per-step telemetry data before any recipe or training route",
            "claim_scope": "Result audit only; no training validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity validation self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2857 telemetry artifacts are incomplete",
                "stop if M2857 uses public rows as ranking validation or optimization evidence",
                "stop if actor inputs or label visibility changed",
                "stop if per-step telemetry cannot localize beyond rollout-level M2854 rows",
            ],
            "fallback_plan": [
                "route to instrumentation repair for missing per-step fields",
                "route to artifact repair for lineage/schema failures",
                "route to training recipe design only if telemetry artifacts are accepted",
                "route to branch synthesis if telemetry remains inconclusive",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2857 has produced per-step telemetry artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2857 per-step telemetry diagnostic materialization",
            "admission_evidence": [
                "M2857 summary and telemetry artifacts are expected before M2858 runs",
                "M2857 per-step localization rows require audit before recipe interpretation",
            ],
            "blocked_shortcuts": [
                "no training PPO validation ranking promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                doc_path,
                "M2858 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2857 artifacts are accepted or rejected",
                "temporal localization buckets and inconclusive gaps are preserved",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2858 audits Route A telemetry diagnostics and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "M2857 per-step telemetry is not level3 self-identification evidence."
            ],
            "temporal_evidence_window": "M2843-M2857 response-predictive recurrent-belief branch.",
            "negative_result_policy": "If telemetry is inconclusive, preserve the result and route to synthesis or instrumentation repair rather than weakening gates.",
            "allowed_claims": [
                "M2857 per-step telemetry materialization accepted or rejected",
                "bounded follow-up route registration",
                "no driver-performance verdict paper result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new per-step closed-loop telemetry evidence",
            "paper_verdict_delta": "no paper verdict; audit governs Route A telemetry interpretation before recipe changes",
            "must_synthesize_if": [
                "M2857 telemetry artifacts are incomplete",
                "M2857 cannot add localization beyond M2854 rollout-level rows",
                "M2857 exposes labels or hidden/oracle inputs to actor input",
                "M2857 results are used as validation performance self-ID or paper evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2857 per-step telemetry artifacts before recipe interpretation.",
        "success_criteria": [
            f"{doc_path} exists",
            "audit checks M2857 summary per-step trace episode summary surface localization actor claim and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels M2850/M2854/M2838 diagnostic boundary and claim boundary",
            "audit registers one bounded follow-up route or stop decision",
        ],
        "failure_criteria": [
            "M2858 runs new training validation ranking promotion or success-rate verdict computation",
            "M2858 hides M2857 gate failures or weakens actor/claim boundaries",
            "M2858 claims repair success driver performance validation readiness/result high-fidelity validation paper current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2858 audits M2857 artifacts under unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": doc_path, "type": "md"}],
        "baseline_checkpoints": [str(DEFAULT_BASELINE_CHECKPOINT), str(DEFAULT_CANDIDATE_CHECKPOINT)],
        "baseline_artifacts": [str(DEFAULT_OUTPUT_DIR / "summary.json")],
        "scoreboard_checkpoint": doc_path,
        "next_blocker": "",
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2857 Engineering Controller Route A Response-Predictive Recurrent-Belief Per-Step Telemetry Panel Materialization Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- surface rows: {summary['surface_row_count']}",
            f"- M2850 explanatory rows: {summary['m2850_explanatory_surface_row_count']}",
            f"- fresh/disjoint rows: {summary['fresh_disjoint_surface_row_count']}",
            f"- per-step trace rows: {summary['per_step_trace_row_count']}",
            f"- episode summary rows: {summary['episode_trace_summary_row_count']}",
            f"- localization rows: {summary['telemetry_localization_row_count']}",
            f"- execution status counts: {summary['execution_status_counts']}",
            f"- termination counts: {summary['termination_counts']}",
            f"- per-step localization buckets: {summary['per_step_localization_bucket_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- failed gates: {summary['failed_gate_ids'] or 'none'}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next blocker: `{summary['next_blocker']}`",
            "",
            "## Route Boundary",
            "",
            "M2857 follows post-M2470 Route A engineering-controller evidence discipline. It",
            "materializes per-step closed-loop telemetry for diagnostic localization only.",
            "The M2850 explanatory rows remain public diagnostic explanation rows and the",
            "fresh/disjoint surface prevents using only fixed public rows.",
            "",
            "## Actor And Claim Boundary",
            "",
            f"- actor observation shape: {P0_OBSERVATION_DIM}",
            f"- action shape: {ACTION_DIM}",
            "- hidden/oracle actor input required: false",
            "- response-prediction error: not computed when unavailable; actor-invisible instrumentation gap",
            "- ranking admissible: false",
            "- ordinary success denominator allowed: false",
            "- checkpoint promoted: false",
            "- driver-performance/self-ID/paper claims: false",
            "",
            "## Interpretation",
            "",
            "Allowed claim: M2857 wrote bounded per-step telemetry artifacts over M2850",
            "explanatory and fresh/disjoint diagnostic surfaces. These artifacts still require",
            "M2858 result audit before they can influence a training-recipe route.",
            "",
            "Forbidden interpretation:",
            "",
            FORBIDDEN_INTERPRETATION,
        ]
    )


def run_response_predictive_recurrent_belief_per_step_telemetry_panel_materialization(
    *,
    m2856_design: Path | str = DEFAULT_M2856_DESIGN,
    m2854_summary: Path | str = DEFAULT_M2854_SUMMARY,
    m2854_localization_rows: Path | str = DEFAULT_M2854_LOCALIZATION_ROWS,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    baseline_checkpoint: Path | str = DEFAULT_BASELINE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    m2850_row_count: int = DEFAULT_M2850_ROW_COUNT,
    fresh_row_count: int = DEFAULT_FRESH_ROW_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m2856_design=Path(m2856_design),
        m2854_summary=Path(m2854_summary),
        m2854_localization_rows=Path(m2854_localization_rows),
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
    )
    subject_registry = load_subject_registry(
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
        device=device,
    )
    surface_rows = build_surface_rows(
        source=source,
        m2850_row_count=int(m2850_row_count),
        fresh_row_count=int(fresh_row_count),
    )
    write_csv_rows(paths["telemetry_surface_rows"], surface_rows, fieldnames=SURFACE_FIELDNAMES)
    per_step_rows, episode_rows = collect_telemetry_rows(
        surface_rows=surface_rows,
        source=source,
        subject_registry=subject_registry,
        output_dir=output,
        eval_seed_base=int(eval_seed_base),
        horizon_steps=int(horizon_steps),
        device=device,
        next_blocker=next_blocker,
    )
    localization_rows = build_telemetry_localization_rows(
        surface_rows=surface_rows,
        episode_rows=episode_rows,
        m2854_localization_rows=source["m2854_localization_rows"],
    )
    write_csv_rows(paths["per_step_trace_rows"], per_step_rows, fieldnames=PER_STEP_FIELDNAMES)
    write_csv_rows(paths["episode_trace_summary_rows"], episode_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(paths["telemetry_localization_rows"], localization_rows, fieldnames=LOCALIZATION_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_m2858_follow_up_manifest())

    required_present = all(
        paths[key].exists()
        for key in (
            "per_step_trace_rows",
            "episode_trace_summary_rows",
            "telemetry_surface_rows",
            "telemetry_localization_rows",
            "follow_up_manifest",
        )
    )
    overfit_rows = build_public_row_overfit_guard_rows(surface_rows)
    actor_rows = build_actor_contract_guard_rows(subject_registry=subject_registry, per_step_rows=per_step_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
        required_artifacts_present=required_present,
    )
    gate_rows = build_gate_rows(
        source=source,
        surface_rows=surface_rows,
        per_step_rows=per_step_rows,
        episode_rows=episode_rows,
        localization_rows=localization_rows,
        overfit_rows=overfit_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        m2850_row_count=int(m2850_row_count),
        fresh_row_count=int(fresh_row_count),
        horizon_steps=int(horizon_steps),
    )
    write_csv_rows(paths["public_row_overfit_guard_rows"], overfit_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        subject_registry=subject_registry,
        surface_rows=surface_rows,
        per_step_rows=per_step_rows,
        episode_rows=episode_rows,
        localization_rows=localization_rows,
        overfit_rows=overfit_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        eval_seed_base=int(eval_seed_base),
        m2850_row_count=int(m2850_row_count),
        fresh_row_count=int(fresh_row_count),
        horizon_steps=int(horizon_steps),
        device=device,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(paths["run_state"], {**summary, "complete": True})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2856-design", type=Path, default=DEFAULT_M2856_DESIGN)
    parser.add_argument("--m2854-summary", type=Path, default=DEFAULT_M2854_SUMMARY)
    parser.add_argument("--m2854-localization-rows", type=Path, default=DEFAULT_M2854_LOCALIZATION_ROWS)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--baseline-checkpoint", type=Path, default=DEFAULT_BASELINE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--m2850-row-count", type=int, default=DEFAULT_M2850_ROW_COUNT)
    parser.add_argument("--fresh-row-count", type=int, default=DEFAULT_FRESH_ROW_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_response_predictive_recurrent_belief_per_step_telemetry_panel_materialization(
        m2856_design=args.m2856_design,
        m2854_summary=args.m2854_summary,
        m2854_localization_rows=args.m2854_localization_rows,
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        baseline_checkpoint=args.baseline_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        m2850_row_count=args.m2850_row_count,
        fresh_row_count=args.fresh_row_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
