"""Execute M3189 residual blocker-axis trace telemetry collection."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import (
    ACTION_COMPONENTS,
    DRIVER_ID,
    OUTPUT_SEMANTICS,
    ActiveSafetyReflexDriver,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075


MILESTONE_ID = (
    "m3189-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-materialization-preflight"
)
NEXT_ID = (
    "m3190-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-result-audit"
)
M3188_ID = (
    "m3188-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-result-audit"
)
M3187_ID = (
    "m3187-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)
M3012_ID = "m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-preflight"

DEFAULT_M3188_AUDIT = Path(f"docs/{M3188_ID}.md")
DEFAULT_M3187_DIR = Path(
    "runs/m3187_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_spec_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3189_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_execution_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TRACE_BINDINGS = 7
EXPECTED_TRACE_AXES = {
    "clearance_timing_axis",
    "boundary_recovery_collision_axis",
    "boundary_recovery_stability_axis",
}
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3189 Active Safety Driver residual hard-safety blocker-axis trace execution "
    "materialization only; the seven accepted M3187 trace source bindings may be "
    "executed through ActiveSafetyReflexDriver.act(obs72) as the incumbent direct "
    "[steer throttle brake] action source, and obs72/public action telemetry, "
    "offline terminal-status accounting, guard, claim, gate, doc, and M3190 audit "
    "manifest artifacts may be written. No repair implementation, validation, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, public "
    "driver default mutation, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

TRACE_EXECUTION_FIELDNAMES = [
    "trace_execution_id",
    "trace_source_binding_id",
    "evidence_axis",
    "fresh_panel_row_id",
    "source_measurement_episode_id",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "executable_workload_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "runtime_driver_id",
    "actor_runtime_inputs",
    "actor_runtime_input_contract",
    "action_components",
    "output_semantics",
    "scheduled_status_pass",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "return",
    "speed_mean",
    "lateral_rmse",
    "beta_abs_error_mean",
    "high_sideslip_fraction",
    "action_rate_mean",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction",
    "final_action_abs_max",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "trace_execution_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "public_driver_default_mutated",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "terminal_status_offline_only",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "robustness_result_claim_made",
    "validation_result_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "full_ideal_driver_completion_claim_made",
    "feasibility_proof_claim_made",
    "level3_self_id_claim_made",
    "claim_boundary",
]
TRACE_STEP_FIELDNAMES = [
    "trace_step_id",
    "trace_execution_id",
    "trace_source_binding_id",
    "step_index",
    "evidence_axis",
    "fresh_panel_row_id",
    "source_measurement_episode_id",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "obs72_dim",
    "obs72_sha256",
    "obs72_snapshot",
    "obs72_l2",
    "obs72_mean",
    "obs72_std",
    "previous_steer",
    "previous_throttle",
    "previous_brake",
    "final_steer",
    "final_throttle",
    "final_brake",
    "action_delta_l2",
    "action_delta_steer_abs",
    "action_delta_throttle_abs",
    "action_delta_brake_abs",
    "raw_action_abs_max",
    "raw_action_l2",
    "final_action_abs_max",
    "action_clip_hit",
    "action_clip_fraction_step",
    "actor_runtime_inputs",
    "actor_runtime_input_contract",
    "public_telemetry_fields",
    "offline_trace_fields",
    "terminal_status_offline_only",
    "reward",
    "post_speed",
    "post_lateral_error",
    "post_beta",
    "heading_alignment_proxy",
    "sideslip_proxy",
    "lane_boundary_geometry_proxy",
    "obstacle_geometry_proxy",
    "relative_clearance_proxy",
    "post_collision",
    "post_obstacle_completed",
    "terminated",
    "truncated",
    "termination_reason",
    "runtime_label_inputs_used",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]
TRACE_FAILURE_FIELDNAMES = [
    "trace_failure_id",
    "trace_execution_id",
    "trace_source_binding_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "evidence_axis",
    "error_type",
    "error_message",
    "actor_runtime_inputs",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]
GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_runtime_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3189",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return float(np.mean(items)) if items else 0.0


def _success_from_info(info: Mapping[str, Any]) -> bool:
    return _bool(info.get("obstacle_completed", False)) and not _bool(info.get("collision", False))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _obs_snapshot(observation: np.ndarray) -> str:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    return "|".join(f"{float(value):.8g}" for value in obs)


def _obs_hash(observation: np.ndarray) -> str:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    return hashlib.sha256(obs.tobytes()).hexdigest()


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "trace_execution_rows": output_dir / "trace_execution_rows.csv",
        "trace_step_rows": output_dir / "trace_step_rows.csv",
        "trace_failure_rows": output_dir / "trace_failure_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3188_audit: Path,
    m3187_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3188_audit": m3188_audit,
        "m3187_summary": m3187_dir / "summary.json",
        "m3187_trace_specs": m3187_dir / "trace_spec_rows.csv",
        "m3187_trace_source_bindings": m3187_dir / "trace_source_binding_rows.csv",
        "m3187_boundary_rows": m3187_dir / "obs72_public_telemetry_boundary_rows.csv",
        "m3187_forbidden_label_guard_rows": m3187_dir / "forbidden_label_guard_rows.csv",
        "m3187_gate_rows": m3187_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3188_audit_text": paths["m3188_audit"].read_text(encoding="utf-8") if exists["m3188_audit"] else "",
        "m3187_summary": read_json(paths["m3187_summary"]) if exists["m3187_summary"] else {},
        "m3187_trace_specs": read_csv_rows(paths["m3187_trace_specs"]),
        "m3187_trace_source_bindings": read_csv_rows(paths["m3187_trace_source_bindings"]),
        "m3187_boundary_rows": read_csv_rows(paths["m3187_boundary_rows"]),
        "m3187_forbidden_label_guard_rows": read_csv_rows(paths["m3187_forbidden_label_guard_rows"]),
        "m3187_gate_rows": read_csv_rows(paths["m3187_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def _hidden_label_violation(*rows: Mapping[str, Any]) -> bool:
    fields = (
        "hidden_oracle_actor_input_required",
        "target_labels_actor_visible",
        "target_provenance_actor_visible",
        "source_labels_actor_visible",
        "route_labels_actor_visible",
        "outcome_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
        "ttc_actor_input_required",
        "runtime_actor_input_allowed",
    )
    return any(_bool(row.get(field, False)) for row in rows for field in fields)


def trace_execution_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    incumbent_by_source = {
        str(row.get("source_measurement_episode_id", "")): dict(row)
        for row in source["m3105_measurement_rows"]
    }
    workloads = {
        str(row.get("executable_workload_id", "")): dict(row)
        for row in source["m3012_workload_rows"]
    }
    rows = sorted(
        (dict(row) for row in source["m3187_trace_source_bindings"]),
        key=lambda item: str(item.get("trace_source_binding_id", "")),
    )
    plan: list[dict[str, Any]] = []
    for index, binding in enumerate(rows, start=1):
        source_id = str(binding.get("source_measurement_episode_id", ""))
        incumbent = incumbent_by_source.get(source_id, {})
        workload = workloads.get(str(incumbent.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        eval_seed = _int(binding.get("eval_seed") or incumbent.get("eval_seed"), 0)
        hidden_label_violation = _hidden_label_violation(binding, incumbent, workload)
        status_pass = bool(
            incumbent
            and workload
            and _bool(workload.get("status_pass", False))
            and Path(config_path).exists()
            and eval_seed > 0
            and str(incumbent.get("candidate_output_semantics", "")) == OUTPUT_SEMANTICS
            and not _bool(incumbent.get("runtime_base_policy_required", True))
            and not hidden_label_violation
        )
        plan.append(
            {
                **binding,
                **incumbent,
                **workload,
                "trace_execution_id": f"m3189-trace-execution-{index:04d}",
                "trace_source_binding_id": binding.get("trace_source_binding_id", ""),
                "evidence_axis": binding.get("evidence_axis", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": binding.get("fresh_panel_row_id", incumbent.get("fresh_panel_row_id", "")),
                "blocker_family": binding.get("blocker_family", ""),
                "axis_id": binding.get("axis_id", incumbent.get("axis_id", "")),
                "binding_role": binding.get("binding_role", incumbent.get("binding_role", "")),
                "task_family": binding.get("task_family", incumbent.get("task_family", "")),
                "base_profile_name": workload.get("profile_binding_name", incumbent.get("base_profile_name", "")),
                "config_path": config_path,
                "eval_seed": eval_seed,
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan


def _context(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "trace_execution_id": plan.get("trace_execution_id", ""),
        "trace_source_binding_id": plan.get("trace_source_binding_id", ""),
        "evidence_axis": plan.get("evidence_axis", ""),
        "fresh_panel_row_id": plan.get("fresh_panel_row_id", ""),
        "source_measurement_episode_id": plan.get("source_measurement_episode_id", ""),
        "blocker_family": plan.get("blocker_family", ""),
        "axis_id": plan.get("axis_id", ""),
        "binding_role": plan.get("binding_role", ""),
        "task_family": plan.get("task_family", ""),
        "eval_seed": plan.get("eval_seed", ""),
    }


def run_trace_execution(
    *,
    plan: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    driver: ActiveSafetyReflexDriver,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    env_config = env_config_for_executable_profile(
        executable_spec=executable_spec,
        profile_config=profile_config,
    )
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    context = _context(plan)
    trace_rows: list[dict[str, Any]] = []
    rewards: list[float] = []
    speeds: list[float] = []
    lateral_errors: list[float] = []
    beta_errors: list[float] = []
    betas: list[float] = []
    actions: list[np.ndarray] = []
    action_deltas: list[float] = []
    clip_hits = 0
    clip_components = 0
    previous_action = np.zeros(ACTION_DIM, dtype=np.float32)
    last_info: dict[str, Any] = {}
    terminated = False
    truncated = False

    try:
        if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
            raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
        if int(env.action_space.shape[0]) != ACTION_DIM:
            raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
        obs, _info = env.reset(seed=_int(plan.get("eval_seed"), 0))
        while not (terminated or truncated):
            obs_array = np.asarray(obs, dtype=np.float32)
            if obs_array.shape != (P0_OBSERVATION_DIM,):
                raise ValueError(f"expected obs72 shape {(P0_OBSERVATION_DIM,)}, got {obs_array.shape}")
            action = np.asarray(driver.act(obs_array), dtype=np.float32)
            delta = action - previous_action
            action_delta_l2 = float(np.linalg.norm(delta))
            clip_hits += int(np.sum(np.abs(action) >= 0.999999))
            clip_components += int(action.size)
            obs, reward, terminated, truncated, info = env.step(action)
            last_info = dict(info)
            rewards.append(float(reward))
            speeds.append(_float(info.get("speed")))
            lateral_errors.append(_float(info.get("lateral_error")))
            beta = _float(info.get("beta"))
            beta_target = _float(info.get("beta_target"))
            betas.append(beta)
            beta_errors.append(abs(beta) - beta_target)
            actions.append(action.copy())
            action_deltas.append(action_delta_l2)
            trace_rows.append(
                {
                    "trace_step_id": f"{plan.get('trace_execution_id')}-step-{len(trace_rows) + 1:04d}",
                    **context,
                    "step_index": len(trace_rows),
                    "obs72_dim": int(obs_array.shape[0]),
                    "obs72_sha256": _obs_hash(obs_array),
                    "obs72_snapshot": _obs_snapshot(obs_array),
                    "obs72_l2": float(np.linalg.norm(obs_array)),
                    "obs72_mean": float(np.mean(obs_array)),
                    "obs72_std": float(np.std(obs_array)),
                    "previous_steer": float(previous_action[0]),
                    "previous_throttle": float(previous_action[1]),
                    "previous_brake": float(previous_action[2]),
                    "final_steer": float(action[0]),
                    "final_throttle": float(action[1]),
                    "final_brake": float(action[2]),
                    "action_delta_l2": action_delta_l2,
                    "action_delta_steer_abs": float(abs(delta[0])),
                    "action_delta_throttle_abs": float(abs(delta[1])),
                    "action_delta_brake_abs": float(abs(delta[2])),
                    "raw_action_abs_max": float(np.max(np.abs(action))),
                    "raw_action_l2": float(np.linalg.norm(action)),
                    "final_action_abs_max": float(np.max(np.abs(action))),
                    "action_clip_hit": bool(np.any(np.abs(action) >= 0.999999)),
                    "action_clip_fraction_step": float(np.mean(np.abs(action) >= 0.999999)),
                    "actor_runtime_inputs": "obs72",
                    "actor_runtime_input_contract": "obs72_only_direct_action3",
                    "public_telemetry_fields": "previous_action|final_action|action_delta|action_rate|clip_fraction",
                    "offline_trace_fields": "terminal_status_offline|source_binding_ids_for_accounting",
                    "terminal_status_offline_only": True,
                    "reward": float(reward),
                    "post_speed": _float(info.get("speed")),
                    "post_lateral_error": _float(info.get("lateral_error")),
                    "post_beta": beta,
                    "heading_alignment_proxy": _float(
                        info.get("heading_alignment", info.get("heading_error", info.get("yaw_error", 0.0)))
                    ),
                    "sideslip_proxy": beta,
                    "lane_boundary_geometry_proxy": _float(info.get("lateral_error")),
                    "obstacle_geometry_proxy": _float(info.get("min_obstacle_clearance")),
                    "relative_clearance_proxy": _float(info.get("min_clearance_margin")),
                    "post_collision": _bool(info.get("collision", False)),
                    "post_obstacle_completed": _bool(info.get("obstacle_completed", False)),
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "termination_reason": str(info.get("termination_reason", "") or ""),
                    "runtime_label_inputs_used": False,
                    "hidden_oracle_actor_input_required": False,
                    "source_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "outcome_labels_actor_visible": False,
                    "success_progress_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "ttc_actor_input_required": False,
                    "validation_run": False,
                    "repair_success_claim_made": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            previous_action = action.copy()
    finally:
        env.close()

    action_array = np.asarray(actions, dtype=np.float32) if actions else np.zeros((0, ACTION_DIM), dtype=np.float32)
    execution_row = {
        **context,
        "executable_workload_id": plan.get("executable_workload_id", ""),
        "executable_source_spec_id": plan.get("executable_source_spec_id", ""),
        "task_source_id": plan.get("task_source_id", ""),
        "base_profile_name": plan.get("base_profile_name", ""),
        "runtime_driver_id": DRIVER_ID,
        "actor_runtime_inputs": "obs72",
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "action_components": "|".join(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "scheduled_status_pass": True,
        "steps": len(actions),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": _success_from_info(last_info),
        "collision": _bool(last_info.get("collision", False)),
        "obstacle_completed": _bool(last_info.get("obstacle_completed", False)),
        "termination_reason": str(last_info.get("termination_reason", "") or ""),
        "outcome_bucket": outcome_bucket_from_info(last_info, terminated=terminated, truncated=truncated) if last_info else "",
        "min_obstacle_clearance": _float(last_info.get("min_obstacle_clearance")),
        "obstacle_collision_radius": _float(last_info.get("obstacle_collision_radius")),
        "min_clearance_margin": _float(last_info.get("min_clearance_margin")),
        "return": float(np.sum(rewards)) if rewards else 0.0,
        "speed_mean": _mean(speeds),
        "lateral_rmse": float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else 0.0,
        "beta_abs_error_mean": _mean(abs(value) for value in beta_errors),
        "high_sideslip_fraction": _mean(float(abs(value) > 0.35) for value in betas),
        "action_rate_mean": _mean(action_deltas),
        "raw_action_abs_max": float(np.max(np.abs(action_array))) if len(action_array) else 0.0,
        "raw_action_l2_mean": _mean(float(np.linalg.norm(action)) for action in action_array),
        "action_clip_fraction": float(clip_hits / clip_components) if clip_components else 0.0,
        "final_action_abs_max": float(np.max(np.abs(action_array))) if len(action_array) else 0.0,
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "trace_execution_run": True,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "terminal_status_offline_only": True,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }
    return execution_row, trace_rows


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    return {
        "trace_failure_id": f"m3189-trace-failure-{plan.get('trace_execution_id', '')}",
        "trace_execution_id": plan.get("trace_execution_id", ""),
        "trace_source_binding_id": plan.get("trace_source_binding_id", ""),
        "source_measurement_episode_id": plan.get("source_measurement_episode_id", ""),
        "fresh_panel_row_id": plan.get("fresh_panel_row_id", ""),
        "evidence_axis": plan.get("evidence_axis", ""),
        "error_type": error_type,
        "error_message": error_message,
        "actor_runtime_inputs": "obs72",
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "validation_run": False,
        "repair_success_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def run_trace_execution_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): dict(row)
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    driver = ActiveSafetyReflexDriver()
    executions: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3189 trace execution plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            execution, trace_rows = run_trace_execution(
                plan=plan,
                executable_spec=executable_spec,
                profile_config=profile_cache[cache_key],
                driver=driver,
            )
            executions.append(execution)
            steps.extend(trace_rows)
        except Exception as exc:  # noqa: BLE001 - each scheduled trace binding is accounted.
            failures.append(failure_row(plan, error_type=type(exc).__name__, error_message=str(exc)))
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_trace_execution_row_count": len(plan_rows),
                "trace_execution_row_count": len(executions),
                "trace_step_row_count": len(steps),
                "trace_failure_row_count": len(failures),
                "latest_trace_execution_id": plan.get("trace_execution_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"executions": executions, "steps": steps, "failures": failures}


def guard(
    guard_id: str,
    family: str,
    observed: Any,
    expected: Any,
    *,
    actor_runtime_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "guard_id": f"m3189-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_runtime_allowed": actor_runtime_allowed,
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_guard_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sample_action = ActiveSafetyReflexDriver().act(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32))
    hidden_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    return [
        guard("source_artifacts_present", "source", all(source["source_exists"].values()), True),
        guard("trace_binding_plan_rows", "source", len(plan_rows), EXPECTED_TRACE_BINDINGS),
        guard("observation_shape", "contract", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, actor_runtime_allowed=True),
        guard("action_shape", "contract", ACTION_DIM, ACTION_DIM, actor_runtime_allowed=True),
        guard("action_components", "contract", "|".join(ACTION_COMPONENTS), "steer|throttle|brake", actor_runtime_allowed=True),
        guard("output_semantics", "contract", OUTPUT_SEMANTICS, "direct_action_clipped", actor_runtime_allowed=True),
        guard("sample_action_shape", "runtime_api", tuple(sample_action.shape), (ACTION_DIM,), actor_runtime_allowed=True),
        guard("sample_action_finite", "runtime_api", bool(np.all(np.isfinite(sample_action))), True, actor_runtime_allowed=True),
        guard("sample_action_bounded", "runtime_api", bool(np.max(np.abs(sample_action)) <= 1.0), True, actor_runtime_allowed=True),
        guard("actor_runtime_inputs", "contract", {row.get("actor_runtime_inputs") for row in steps} if steps else set(), {"obs72"}),
        guard("hidden_runtime_inputs_used", "contract", hidden_inputs_used, False),
        guard("terminal_status_offline_only", "contract", all(_bool(row.get("terminal_status_offline_only", False)) for row in executions + steps), True),
        guard("trace_failures", "execution", len(failures), 0),
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("trace_execution_rows", "trace_execution_artifact", True, True, "trace_execution_rows.csv"),
        ("trace_step_rows", "trace_execution_artifact", True, True, "trace_step_rows.csv"),
        ("contract_guard_rows", "contract", True, True, "contract_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "later implementation admission after audit and synthesis"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("ranking_or_winner_selection", "forbidden", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("public_driver_default_mutation", "forbidden", False, False, "future admitted implementation route"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3189"),
    ]
    return [
        {
            "claim_id": f"m3189-{claim_id}",
            "claim_family": family,
            "allowed_in_m3189": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3189-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3188_selects_m3189(audit_text: str) -> bool:
    return (
        "m3189-engineering-controller-active-safety-driver-residual-hard-safety-blocker-axis-trace-execution-materialization-preflight"
        in audit_text
        or "trace execution materialization" in audit_text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    binding_ids = {str(row.get("trace_source_binding_id", "")) for row in plan_rows}
    executed_binding_ids = {str(row.get("trace_source_binding_id", "")) for row in executions}
    axis_counts = Counter(str(row.get("evidence_axis", "")) for row in executions)
    hidden_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    overclaim_made = any(
        _bool(row.get(key, False))
        for row in executions + steps + failures
        for key in (
            "driver_performance_claim_made",
            "repair_success_claim_made",
            "robustness_result_claim_made",
            "validation_result_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "full_ideal_driver_completion_claim_made",
            "feasibility_proof_claim_made",
            "level3_self_id_claim_made",
        )
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3188_selects_m3189_route", "lineage", _m3188_selects_m3189(source["m3188_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3187_status_pass", "lineage", _bool(source["m3187_summary"].get("status_pass")), source["m3187_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3187_gate_matrix_pass", "lineage", _bool(source["m3187_summary"].get("gate_matrix_pass")), source["m3187_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass")), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("scheduled_trace_bindings", "execution", len(plan_rows) == EXPECTED_TRACE_BINDINGS, len(plan_rows), EXPECTED_TRACE_BINDINGS, "scenario_sampling_failure"),
        gate("trace_execution_rows", "execution", len(executions) == EXPECTED_TRACE_BINDINGS, len(executions), EXPECTED_TRACE_BINDINGS, "metric_artifact"),
        gate("trace_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("trace_step_rows", "execution", len(steps) > 0, len(steps), ">0", "metric_artifact"),
        gate("binding_ids_preserved", "execution", binding_ids == executed_binding_ids, sorted(executed_binding_ids), sorted(binding_ids), "metric_artifact"),
        gate("trace_axes_present", "evidence", EXPECTED_TRACE_AXES.issubset(set(axis_counts)), dict(axis_counts), sorted(EXPECTED_TRACE_AXES), "metric_artifact"),
        gate("actor_runtime_obs72_only", "contract", all(str(row.get("actor_runtime_inputs", "")) == "obs72" for row in steps), "all", "obs72", "contract_violation"),
        gate("action3_direct_components", "contract", all(str(row.get("action_components", "")) == "steer|throttle|brake" for row in executions), "all", "steer|throttle|brake", "contract_violation"),
        gate("hidden_inputs_not_used", "contract", not hidden_inputs_used, hidden_inputs_used, False, "contract_violation"),
        gate("runtime_base_policy_not_required", "contract", not any(_bool(row.get("runtime_base_policy_required", False)) for row in executions + failures), "none", "required", "contract_violation"),
        gate("public_driver_not_mutated", "contract", not any(_bool(row.get("public_driver_default_mutated", False)) for row in executions), "none", "mutated", "contract_violation"),
        gate("terminal_status_offline_only", "contract", all(_bool(row.get("terminal_status_offline_only", False)) for row in executions + steps), "all", "offline_only", "contract_violation"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claims) and not overclaim_made, "all", "pass", "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31900,
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
        "hypothesis": "A bounded result audit can accept or reject M3189 trace execution artifacts before repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "trace_execution_rows.csv"),
                str(output_dir / "trace_step_rows.csv"),
                str(output_dir / "trace_failure_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit residual blocker-axis trace execution before implementation admission"],
            "derived_from": [MILESTONE_ID, M3188_ID, M3187_ID, M3105_ID, M3012_ID],
            "blocked_by": [
                "M3189 trace execution rows require audit before implementation admission",
                "executed telemetry is diagnostic only and not a validation result or repair-success verdict",
            ],
            "supersedes": ["direct repair implementation without audited residual blocker-axis trace execution"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3190 must audit M3189 trace execution step rows guards claims and gates",
            "M3190 must preserve obs72-only actor runtime and direct [steer throttle brake] action contract",
            "M3190 must reject repair implementation validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3190 must select implementation-admission synthesis artifact-repair or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune rank promote or mutate checkpoints in M3190",
            "do not convert M3189 trace rows into validation repair-success performance current-sim robustness-result high-fidelity paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_blocker_axis_expansion",
            "evidence_axis": "residual_blocker_axis_trace_execution_result_audit",
            "evidence_increment": "audits executed obs72/public telemetry for the seven residual blocker trace bindings",
            "claim_scope": "Result audit only; no repair implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3189 artifacts are missing or gate matrix fails",
                "stop if any trace execution used hidden runtime labels",
                "synthesize if trace telemetry does not identify an implementation-admissible axis",
            ],
            "fallback_plan": [
                "route to M3189 artifact repair if rows or guards fail",
                "route to synthesis if executed traces do not justify implementation admission",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3189 materializes blocker-axis trace execution artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3189 blocker-axis trace execution artifacts",
            "admission_evidence": [
                "M3189 summary trace execution rows step rows contract guards claim rows and gate matrix",
            ],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3190 status queue scoreboard research log and review",
                "one follow-up manifest only if M3190 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3190 accepts or rejects M3189 as complete and claim-safe",
                "next implementation-admission synthesis artifact-repair or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3190 audits engineering trace execution artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3190; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3189 trace execution artifacts only.",
            "negative_result_policy": "Preserve engineering trace evidence and route implementation admission synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3189 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits executed trace telemetry before implementation admission or synthesis",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3190 audits engineering trace execution evidence",
            "must_synthesize_if": [
                "M3190 cannot select implementation-admission synthesis artifact-repair or stop",
                "M3190 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3190 audits M3189 row counts gates actor contract and claim boundaries",
            "M3190 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3190 hides missing M3189 artifacts or failed gates",
            "M3190 treats M3189 traces as repair success or performance verdict",
            "M3190 changes actor input action contract or public driver default",
            "M3190 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3190 audits M3189 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_blocker_axis_trace_execution_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3189 Residual Hard-Safety Blocker Axis Trace Execution Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- trace source bindings scheduled: {summary['scheduled_trace_execution_row_count']}",
            f"- trace execution rows: {summary['trace_execution_row_count']}",
            f"- trace step rows: {summary['trace_step_row_count']}",
            f"- trace failure rows: {summary['trace_failure_row_count']}",
            f"- actor runtime input contract: `{summary['actor_runtime_input_contract']}`",
            f"- hidden actor inputs used: {summary['hidden_actor_inputs_used']}",
            f"- validation run: {summary['validation_run']}",
            f"- repair implementation admitted: {summary['repair_implementation_admitted']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3189 executes the seven M3187 residual blocker trace bindings through the incumbent public ActiveSafetyReflexDriver.act(obs72) runtime and records obs72/public action telemetry plus offline terminal-status accounting. It is trace telemetry for later audit and possible implementation admission, not validation or repair success.",
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


def run_trace_execution_materialization_preflight(
    *,
    m3188_audit: Path,
    m3187_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str = "cpu",
) -> dict[str, Any]:
    del device
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3188_audit=m3188_audit,
        m3187_dir=m3187_dir,
        m3105_dir=m3105_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = trace_execution_plan(source)
    result = run_trace_execution_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    executions = result["executions"]
    steps = result["steps"]
    failures = result["failures"]
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
    )
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["trace_execution_rows"], executions, fieldnames=TRACE_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["trace_step_rows"], steps, fieldnames=TRACE_STEP_FIELDNAMES)
    write_csv_rows(paths["trace_failure_rows"], failures, fieldnames=TRACE_FAILURE_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    hidden_actor_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    status_pass = bool(gate_matrix_pass and len(executions) == EXPECTED_TRACE_BINDINGS and len(failures) == 0)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "trace_execution_materialized" if status_pass else "trace_execution_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "trace_source_binding_count": len(source["m3187_trace_source_bindings"]),
        "scheduled_trace_execution_row_count": len(plan_rows),
        "trace_execution_row_count": len(executions),
        "trace_step_row_count": len(steps),
        "trace_failure_row_count": len(failures),
        "success_count": sum(_bool(row.get("success", False)) for row in executions),
        "collision_count": sum(_bool(row.get("collision", False)) for row in executions),
        "offtrack_count": sum(_offtrack(row) for row in executions),
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "runtime_driver_id": DRIVER_ID,
        "output_semantics": OUTPUT_SEMANTICS,
        "action_components": list(ACTION_COMPONENTS),
        "hidden_actor_inputs_used": hidden_actor_inputs_used,
        "runtime_base_policy_required": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ranking_run": False,
        "repair_implementation_admitted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "public_driver_default_mutated": False,
        "self_id_claim_made": False,
        "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
        "claim_scope": CLAIM_SCOPE,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "next_blocker": NEXT_ID,
    }
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "scheduled_trace_execution_row_count": len(plan_rows),
            "trace_execution_row_count": len(executions),
            "trace_step_row_count": len(steps),
            "trace_failure_row_count": len(failures),
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3188-audit", type=Path, default=DEFAULT_M3188_AUDIT)
    parser.add_argument("--m3187-dir", type=Path, default=DEFAULT_M3187_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_trace_execution_materialization_preflight(
        m3188_audit=args.m3188_audit,
        m3187_dir=args.m3187_dir,
        m3105_dir=args.m3105_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(summary)


if __name__ == "__main__":
    main()
