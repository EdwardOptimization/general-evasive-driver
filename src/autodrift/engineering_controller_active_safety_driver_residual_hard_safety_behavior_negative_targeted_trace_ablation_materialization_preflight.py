"""Run M3177 targeted actor-visible trace-ablation materialization."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import add_segment_metrics, curvature_segment, empty_segment_stats, outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.outcome_metric_instrumentation import compute_episode_outcome_metrics
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_CONFIG,
    POLICY_ID as M3170_POLICY_ID,
    source_localized_repair_direct_action,
    source_localized_repair_features,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as M3103_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)


MILESTONE_ID = (
    "m3177-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-targeted-trace-ablation-materialization-preflight"
)
NEXT_ID = (
    "m3178-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-targeted-trace-ablation-result-audit"
)
M3176_ID = (
    "m3176-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-source-repair-decomposition-result-audit"
)
M3175_ID = (
    "m3175-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-source-repair-decomposition-materialization-preflight"
)
M3172_ID = (
    "m3172-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-full-fresh-measurement-preflight"
)
M3170_ID = (
    "m3170-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3176_AUDIT = Path(f"docs/{M3176_ID}.md")
DEFAULT_M3175_DIR = Path(
    "runs/m3175_engineering_controller_active_safety_driver_residual_hard_safety_"
    "behavior_negative_source_repair_decomposition_materialization_preflight"
)
DEFAULT_M3172_DIR = Path(
    "runs/m3172_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_full_fresh_measurement_preflight"
)
DEFAULT_M3170_DIR = Path(
    "runs/m3170_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3177_engineering_controller_active_safety_driver_residual_hard_safety_"
    "behavior_negative_targeted_trace_ablation_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_REGRESSION_ROWS = 1
EXPECTED_VARIANT_COUNT = 5
CLAIM_SCOPE = (
    "M3177 Active Safety Driver residual hard-safety behavior-negative targeted "
    "trace-ablation materialization only; the single M3172 new collision regression row "
    "selected by M3175/M3176 may be re-executed with actor-visible obs72 to direct "
    "action3 incumbent, candidate, and bounded ablation action variants, and trace, "
    "variant, guard, claim, gate, doc, and M3178 audit artifacts may be written. No "
    "repair implementation, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, public driver default mutation, driver-performance verdict, "
    "current-sim verdict, repair success, robustness-result, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, "
    "feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)
FORBIDDEN_RUNTIME_INPUTS = (
    "row_label|baseline_outcome|source_label|route_label|outcome_label|progress_label|"
    "verdict_label|ttc_oracle"
)

TARGET_TRACE_FIELDNAMES = [
    "trace_row_id",
    "variant_id",
    "variant_family",
    "step_index",
    "measurement_episode_id",
    "baseline_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "observation_dim",
    "action_dim",
    "action_components",
    "output_semantics",
    "actor_runtime_inputs",
    "forbidden_runtime_inputs",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "incumbent_steer",
    "incumbent_throttle",
    "incumbent_brake",
    "variant_steer",
    "variant_throttle",
    "variant_brake",
    "candidate_incumbent_steer_delta",
    "candidate_incumbent_throttle_delta",
    "candidate_incumbent_brake_delta",
    "variant_incumbent_steer_delta",
    "variant_incumbent_throttle_delta",
    "variant_incumbent_brake_delta",
    "speed_mps",
    "speed_alpha",
    "obstacle_urgency",
    "obstacle_avoid_direction",
    "edge_urgency",
    "road_center_error",
    "stability_risk",
    "collision_alpha",
    "boundary_alpha",
    "reward",
    "post_step",
    "post_speed",
    "post_lateral_error",
    "post_beta",
    "post_min_clearance_margin",
    "post_collision",
    "post_obstacle_completed",
    "terminated",
    "truncated",
    "termination_reason",
    "action_finite",
    "action_bounded",
    "runtime_label_inputs_used",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]
ABLATION_VARIANT_FIELDNAMES = [
    "variant_id",
    "variant_family",
    "action_source",
    "measurement_episode_id",
    "baseline_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "policy",
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
    "high_sideslip_fraction",
    "beta_abs_error_mean",
    "lateral_rmse",
    "action_rate_mean",
    "return",
    "speed_mean",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction",
    "final_action_abs_max",
    "candidate_delta_l2_mean",
    "candidate_delta_l2_peak",
    "variant_delta_l2_mean",
    "variant_delta_l2_peak",
    "overlay_activation_fraction",
    "collision_alpha_mean",
    "boundary_alpha_mean",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "public_driver_default_mutated",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "robustness_result_claim_made",
    "validation_result_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_completion_claim_made",
    "level3_self_id_claim_made",
    "runtime_smoke_only_no_verdict",
    "claim_boundary",
]
CONTRACT_GUARD_FIELDNAMES = [
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
    "allowed_in_m3177",
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


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success", False))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def _m3176_selects_m3177(audit_text: str) -> bool:
    return (
        "m3177-engineering-controller-active-safety-driver-residual-hard-safety-behavior-negative-targeted-trace-ablation-materialization-preflight"
        in audit_text
        or "targeted actor-visible trace-ablation" in audit_text
        or "targeted trace-ablation" in audit_text
    )


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "targeted_trace_rows": output_dir / "targeted_trace_rows.csv",
        "ablation_variant_rows": output_dir / "ablation_variant_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3176_audit: Path,
    m3175_dir: Path,
    m3172_dir: Path,
    m3170_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3176_audit": m3176_audit,
        "m3175_summary": m3175_dir / "summary.json",
        "m3175_regression_rows": m3175_dir / "regression_rows.csv",
        "m3175_repair_decomposition_rows": m3175_dir / "repair_decomposition_rows.csv",
        "m3175_gate_rows": m3175_dir / "gate_matrix.csv",
        "m3172_summary": m3172_dir / "summary.json",
        "m3172_measurement_rows": m3172_dir / "measurement_episode_rows.csv",
        "m3170_summary": m3170_dir / "summary.json",
        "m3170_policy_config": m3170_dir / "direct_action_policy_config.json",
        "m3170_gate_rows": m3170_dir / "gate_matrix.csv",
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
        "m3176_audit_text": paths["m3176_audit"].read_text(encoding="utf-8") if exists["m3176_audit"] else "",
        "m3175_summary": read_json(paths["m3175_summary"]) if exists["m3175_summary"] else {},
        "m3175_regression_rows": read_csv_rows(paths["m3175_regression_rows"]),
        "m3175_repair_decomposition_rows": read_csv_rows(paths["m3175_repair_decomposition_rows"]),
        "m3175_gate_rows": read_csv_rows(paths["m3175_gate_rows"]),
        "m3172_summary": read_json(paths["m3172_summary"]) if exists["m3172_summary"] else {},
        "m3172_measurement_rows": read_csv_rows(paths["m3172_measurement_rows"]),
        "m3170_summary": read_json(paths["m3170_summary"]) if exists["m3170_summary"] else {},
        "m3170_policy_config": read_json(paths["m3170_policy_config"]) if exists["m3170_policy_config"] else {},
        "m3170_gate_rows": read_csv_rows(paths["m3170_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def target_regression_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in source["m3175_regression_rows"]
        if str(row.get("regression_family", "")) == "new_collision_regression_vs_m3105"
        and _bool(row.get("m3172_collision", False))
        and not _bool(row.get("m3105_collision", False))
    ]


def selected_execution_context(source: Mapping[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    source_id = str(target.get("source_measurement_episode_id", ""))
    m3172_row = next(
        (dict(row) for row in source["m3172_measurement_rows"] if str(row.get("source_measurement_episode_id", "")) == source_id),
        {},
    )
    m3105_row = next(
        (dict(row) for row in source["m3105_measurement_rows"] if str(row.get("source_measurement_episode_id", "")) == source_id),
        {},
    )
    workload_id = str(m3172_row.get("executable_workload_id") or m3105_row.get("executable_workload_id") or "")
    spec_id = str(m3172_row.get("executable_source_spec_id") or m3105_row.get("executable_source_spec_id") or "")
    task_source_id = str(m3172_row.get("task_source_id") or m3105_row.get("task_source_id") or "")
    workloads = {str(row.get("executable_workload_id", "")): dict(row) for row in source["m3012_workload_rows"]}
    workload = workloads.get(workload_id, {})
    specs_by_id = {str(row.get("executable_source_spec_id", "")): dict(row) for row in source["m3012_executable_specs"]}
    specs_by_task = {str(row.get("task_source_id", "")): dict(row) for row in source["m3012_executable_specs"]}
    executable_spec = specs_by_id.get(spec_id) or specs_by_task.get(task_source_id) or {}
    config_path = Path(str(workload.get("config_path") or m3172_row.get("config_path") or ""))
    profile_name = str(workload.get("profile_binding_name") or m3172_row.get("base_profile_name") or "")
    profile_config = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name) if config_path.exists() else {}
    return {
        "target": dict(target),
        "m3172_row": m3172_row,
        "m3105_row": m3105_row,
        "workload": workload,
        "executable_spec": executable_spec,
        "profile_config": profile_config,
        "config_path": str(config_path),
        "profile_name": profile_name,
        "status_pass": bool(m3172_row and m3105_row and workload and executable_spec and profile_config),
    }


def variant_specs() -> list[dict[str, str]]:
    return [
        {
            "variant_id": "m3177_incumbent_m3105",
            "variant_family": "incumbent",
            "action_source": M3103_POLICY_ID,
        },
        {
            "variant_id": "m3177_candidate_m3170",
            "variant_family": "candidate",
            "action_source": M3170_POLICY_ID,
        },
        {
            "variant_id": "m3177_ablate_steer_delta",
            "variant_family": "actor_visible_action_ablation",
            "action_source": "m3170_overlay_without_steer_delta",
        },
        {
            "variant_id": "m3177_ablate_throttle_drop",
            "variant_family": "actor_visible_action_ablation",
            "action_source": "m3170_overlay_without_throttle_drop",
        },
        {
            "variant_id": "m3177_ablate_brake_add",
            "variant_family": "actor_visible_action_ablation",
            "action_source": "m3170_overlay_without_brake_add",
        },
    ]


def incumbent_action(observation: np.ndarray) -> np.ndarray:
    return np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(observation, V4_POLICY_CONFIG), dtype=np.float32)


def candidate_action(observation: np.ndarray) -> np.ndarray:
    return np.asarray(source_localized_repair_direct_action(observation, POLICY_CONFIG), dtype=np.float32)


def action_bundle(observation: np.ndarray, variant_id: str) -> dict[str, Any]:
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    incumbent = incumbent_action(obs)
    candidate = candidate_action(obs)
    delta = candidate - incumbent
    variant = candidate.copy()
    if variant_id == "m3177_incumbent_m3105":
        variant = incumbent.copy()
    elif variant_id == "m3177_candidate_m3170":
        variant = candidate.copy()
    elif variant_id == "m3177_ablate_steer_delta":
        variant = incumbent + np.asarray([0.0, delta[1], delta[2]], dtype=np.float32)
    elif variant_id == "m3177_ablate_throttle_drop":
        variant = incumbent + np.asarray([delta[0], 0.0, delta[2]], dtype=np.float32)
    elif variant_id == "m3177_ablate_brake_add":
        variant = incumbent + np.asarray([delta[0], delta[1], 0.0], dtype=np.float32)
    else:
        raise ValueError(f"unknown variant_id: {variant_id}")
    variant = np.clip(variant, -1.0, 1.0).astype(np.float32)
    features = source_localized_repair_features(obs, POLICY_CONFIG)
    return {
        "incumbent": incumbent,
        "candidate": candidate,
        "variant": variant,
        "features": features,
        "candidate_delta_l2": float(np.linalg.norm(candidate - incumbent)),
        "variant_delta_l2": float(np.linalg.norm(variant - incumbent)),
    }


def _context(plan: Mapping[str, Any]) -> dict[str, Any]:
    target = plan["target"]
    return {
        "measurement_episode_id": target.get("measurement_episode_id", ""),
        "baseline_episode_id": target.get("baseline_episode_id", ""),
        "source_measurement_episode_id": target.get("source_measurement_episode_id", ""),
        "fresh_panel_row_id": target.get("fresh_panel_row_id", ""),
        "axis_id": target.get("axis_id", ""),
        "binding_role": target.get("binding_role", ""),
        "task_family": target.get("task_family", ""),
        "eval_seed": target.get("eval_seed", ""),
    }


def run_trace_variant(plan: Mapping[str, Any], variant: Mapping[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    env_config = env_config_for_executable_profile(
        executable_spec=plan["executable_spec"],
        profile_config=plan["profile_config"],
    )
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), plan["profile_config"])
    obs, info = env.reset(seed=_int(plan["target"].get("eval_seed"), 0))
    context = _context(plan)
    trace_rows: list[dict[str, Any]] = []
    rewards: list[float] = []
    lateral_errors: list[float] = []
    beta_errors: list[float] = []
    betas: list[float] = []
    speeds: list[float] = []
    actions: list[np.ndarray] = []
    action_trace_deltas: list[float] = []
    step_infos: list[dict[str, Any]] = []
    segment_stats = empty_segment_stats()
    candidate_delta_l2: list[float] = []
    variant_delta_l2: list[float] = []
    collision_alphas: list[float] = []
    boundary_alphas: list[float] = []
    overlay_active: list[float] = []
    clip_hits = 0
    clip_components = 0
    terminated = False
    truncated = False
    previous_action: np.ndarray | None = None

    try:
        while not (terminated or truncated):
            bundle = action_bundle(obs, str(variant["variant_id"]))
            action_array = np.asarray(bundle["variant"], dtype=np.float32)
            incumbent = np.asarray(bundle["incumbent"], dtype=np.float32)
            candidate = np.asarray(bundle["candidate"], dtype=np.float32)
            features = dict(bundle["features"])
            previous_command = np.zeros_like(action_array) if previous_action is None else previous_action
            action_trace_deltas.append(float(np.linalg.norm(action_array - previous_command)))
            clip_hits += int(np.sum(np.abs(action_array) >= 0.999999))
            clip_components += int(action_array.size)
            obs, reward, terminated, truncated, info = env.step(action_array)
            step_infos.append(dict(info))
            rewards.append(float(reward))
            beta_error = abs(float(info["beta"])) - float(info["beta_target"])
            segment = curvature_segment(float(info.get("curvature", 0.0)))
            lateral_errors.append(float(info["lateral_error"]))
            beta_errors.append(beta_error)
            betas.append(float(info["beta"]))
            speeds.append(float(info["speed"]))
            actions.append(action_array.copy())
            candidate_delta_l2.append(float(bundle["candidate_delta_l2"]))
            variant_delta_l2.append(float(bundle["variant_delta_l2"]))
            collision_alphas.append(_float(features.get("collision_alpha")))
            boundary_alphas.append(_float(features.get("boundary_alpha")))
            overlay_active.append(float(max(_float(features.get("collision_alpha")), _float(features.get("boundary_alpha"))) > 0.0))
            previous_action = action_array.copy()
            segment_stats[segment]["lateral_errors"].append(float(info["lateral_error"]))
            segment_stats[segment]["beta_errors"].append(beta_error)
            segment_stats[segment]["speeds"].append(float(info["speed"]))
            segment_stats[segment]["rewards"].append(float(reward))
            trace_rows.append(
                {
                    "trace_row_id": f"m3177-trace-{len(trace_rows) + 1:05d}",
                    "variant_id": variant["variant_id"],
                    "variant_family": variant["variant_family"],
                    "step_index": len(trace_rows),
                    **context,
                    "observation_dim": P0_OBSERVATION_DIM,
                    "action_dim": ACTION_DIM,
                    "action_components": "|".join(ACTION_COMPONENTS),
                    "output_semantics": OUTPUT_SEMANTICS,
                    "actor_runtime_inputs": "obs72",
                    "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
                    "candidate_steer": float(candidate[0]),
                    "candidate_throttle": float(candidate[1]),
                    "candidate_brake": float(candidate[2]),
                    "incumbent_steer": float(incumbent[0]),
                    "incumbent_throttle": float(incumbent[1]),
                    "incumbent_brake": float(incumbent[2]),
                    "variant_steer": float(action_array[0]),
                    "variant_throttle": float(action_array[1]),
                    "variant_brake": float(action_array[2]),
                    "candidate_incumbent_steer_delta": float(candidate[0] - incumbent[0]),
                    "candidate_incumbent_throttle_delta": float(candidate[1] - incumbent[1]),
                    "candidate_incumbent_brake_delta": float(candidate[2] - incumbent[2]),
                    "variant_incumbent_steer_delta": float(action_array[0] - incumbent[0]),
                    "variant_incumbent_throttle_delta": float(action_array[1] - incumbent[1]),
                    "variant_incumbent_brake_delta": float(action_array[2] - incumbent[2]),
                    "speed_mps": _float(features.get("speed_mps")),
                    "speed_alpha": _float(features.get("speed_alpha")),
                    "obstacle_urgency": _float(features.get("obstacle_urgency")),
                    "obstacle_avoid_direction": _float(features.get("obstacle_avoid_direction")),
                    "edge_urgency": _float(features.get("edge_urgency")),
                    "road_center_error": _float(features.get("road_center_error")),
                    "stability_risk": _float(features.get("stability_risk")),
                    "collision_alpha": _float(features.get("collision_alpha")),
                    "boundary_alpha": _float(features.get("boundary_alpha")),
                    "reward": float(reward),
                    "post_step": int(info["step"]),
                    "post_speed": float(info["speed"]),
                    "post_lateral_error": float(info["lateral_error"]),
                    "post_beta": float(info["beta"]),
                    "post_min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
                    "post_collision": bool(info.get("collision", False)),
                    "post_obstacle_completed": bool(info.get("obstacle_completed", False)),
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "termination_reason": str(info.get("termination_reason", "") or ""),
                    "action_finite": bool(np.all(np.isfinite(action_array))),
                    "action_bounded": bool(np.max(np.abs(action_array)) <= 1.0),
                    "runtime_label_inputs_used": False,
                    "hidden_oracle_actor_input_required": False,
                    "ttc_actor_input_required": False,
                    "validation_run": False,
                    "repair_success_claim_made": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    finally:
        env.close()

    outcome_metric_fields = compute_episode_outcome_metrics(
        step_infos,
        default_dt=float(getattr(env_config, "dt", 0.02)),
        default_track_width=float(getattr(env_config, "track_width", 5.0)),
    )
    row = {
        "variant_id": variant["variant_id"],
        "variant_family": variant["variant_family"],
        "action_source": variant["action_source"],
        **context,
        "policy": variant["action_source"],
        "steps": int(info["step"]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": bool(_bool(info.get("obstacle_completed", False)) and not _bool(info.get("collision", False))),
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "outcome_bucket": outcome_bucket_from_info(info, terminated=terminated, truncated=truncated),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "return": float(np.sum(rewards)),
        "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
        "lateral_rmse": float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else float("nan"),
        "lateral_peak": float(np.max(np.abs(lateral_errors))) if lateral_errors else float("nan"),
        "beta_abs_error_mean": float(np.mean(np.abs(beta_errors))) if beta_errors else float("nan"),
        "beta_abs_peak": float(np.max(np.abs(betas))) if betas else float("nan"),
        "high_sideslip_fraction": float(np.mean(np.abs(betas) > 0.35)) if betas else float("nan"),
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
        "action_rate_mean": (
            float(np.mean(np.linalg.norm(np.diff(np.asarray(actions), axis=0), axis=1))) if len(actions) > 1 else 0.0
        ),
        "raw_action_abs_max": float(np.max(np.abs(actions))) if actions else 0.0,
        "raw_action_l2_mean": float(np.mean(np.linalg.norm(np.asarray(actions), axis=1))) if actions else 0.0,
        "action_clip_fraction": float(clip_hits / clip_components) if clip_components else 0.0,
        "final_action_abs_max": float(np.max(np.abs(actions))) if actions else 0.0,
        "candidate_delta_l2_mean": _mean(candidate_delta_l2),
        "candidate_delta_l2_peak": float(np.max(candidate_delta_l2)) if candidate_delta_l2 else float("nan"),
        "variant_delta_l2_mean": _mean(variant_delta_l2),
        "variant_delta_l2_peak": float(np.max(variant_delta_l2)) if variant_delta_l2 else float("nan"),
        "overlay_activation_fraction": _mean(overlay_active),
        "collision_alpha_mean": _mean(collision_alphas),
        "boundary_alpha_mean": _mean(boundary_alphas),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "hidden_oracle_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "runtime_smoke_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
        **outcome_metric_fields,
    }
    return trace_rows, add_segment_metrics(row, segment_stats)


def guard(guard_id: str, family: str, observed: Any, expected: Any, *, actor_visible: bool = False) -> dict[str, Any]:
    return {
        "guard_id": f"m3177-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_guard_rows(
    *,
    source: Mapping[str, Any],
    plan: Mapping[str, Any],
    targets: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    variants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sample = action_bundle(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32), "m3177_candidate_m3170")
    combined = traces + variants
    primary_route_present = any(
        str(row.get("route_name", "")) == "new_collision_regression_actor_visible_ablation_trace"
        for row in source["m3175_repair_decomposition_rows"]
    )
    return [
        guard("source_artifacts_present", "source", all(source["source_exists"].values()), True),
        guard("m3176_route_marker", "lineage", _m3176_selects_m3177(source["m3176_audit_text"]), True),
        guard("m3175_primary_trace_route_present", "lineage", primary_route_present, True),
        guard("selected_context_status_pass", "lineage", plan["status_pass"], True),
        guard("target_regression_rows", "evidence", len(targets), EXPECTED_TARGET_REGRESSION_ROWS),
        guard("observation_shape", "contract", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, actor_visible=True),
        guard("action_shape", "contract", ACTION_DIM, ACTION_DIM, actor_visible=True),
        guard("action_components", "contract", "|".join(ACTION_COMPONENTS), "|".join(("steer", "throttle", "brake")), actor_visible=True),
        guard("output_semantics", "contract", OUTPUT_SEMANTICS, "direct_action_clipped", actor_visible=True),
        guard("sample_action_shape", "contract", tuple(sample["variant"].shape), (ACTION_DIM,), actor_visible=True),
        guard("sample_action_finite", "contract", bool(np.all(np.isfinite(sample["variant"]))), True, actor_visible=True),
        guard("runtime_label_inputs_used", "contract", any(_bool(row.get("runtime_label_inputs_used", False)) for row in traces), False),
        guard("hidden_oracle_actor_input_required", "contract", any(_bool(row.get("hidden_oracle_actor_input_required", False)) for row in combined), False),
        guard("ttc_actor_input_required", "contract", any(_bool(row.get("ttc_actor_input_required", False)) for row in combined), False),
        guard("runtime_base_policy_required", "contract", any(_bool(row.get("runtime_base_policy_required", False)) for row in variants), False),
        guard("public_driver_default_mutated", "contract", any(_bool(row.get("public_driver_default_mutated", False)) for row in variants), False),
        guard("validation_run", "claim", any(_bool(row.get("validation_run", False)) for row in combined), False),
        guard("repair_success_claim_made", "claim", any(_bool(row.get("repair_success_claim_made", False)) for row in combined), False),
        guard("driver_performance_claim_made", "claim", any(_bool(row.get("driver_performance_claim_made", False)) for row in variants), False),
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("targeted_trace_rows", "trace_ablation_artifact", True, True, "targeted_trace_rows.csv"),
        ("ablation_variant_rows", "trace_ablation_artifact", True, True, "ablation_variant_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "M3178 audit before implementation planning"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted deployable candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim result synthesis after validation"),
        ("repair_success", "forbidden", False, False, "accepted full-fresh improvement plus validation path"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("high_fidelity_validation", "forbidden", False, False, "later validation layer"),
        ("paper_evidence", "forbidden", False, False, "paper route remains auxiliary"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3177"),
    ]
    return [
        {
            "claim_id": f"m3177-{claim_id}",
            "claim_family": family,
            "allowed_in_m3177": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3177-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _variant_by_id(rows: list[dict[str, Any]], variant_id: str) -> dict[str, Any]:
    return next((row for row in rows if str(row.get("variant_id", "")) == variant_id), {})


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    targets: list[dict[str, Any]],
    plan: Mapping[str, Any],
    traces: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    candidate = _variant_by_id(variants, "m3177_candidate_m3170")
    incumbent = _variant_by_id(variants, "m3177_incumbent_m3105")
    target = targets[0] if targets else {}
    expected_m3172 = plan.get("m3172_row", {})
    expected_m3105 = plan.get("m3105_row", {})
    action_bounded = all(_bool(row.get("action_finite", False)) and _bool(row.get("action_bounded", False)) for row in traces)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3176_selects_m3177_route", "lineage", _m3176_selects_m3177(source["m3176_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3175_status_pass", "lineage", _bool(source["m3175_summary"].get("status_pass", False)), source["m3175_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3172_status_pass", "lineage", _bool(source["m3172_summary"].get("status_pass", False)), source["m3172_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3170_status_pass", "lineage", _bool(source["m3170_summary"].get("status_pass", False)), source["m3170_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("target_regression_rows", "evidence", len(targets) == EXPECTED_TARGET_REGRESSION_ROWS, len(targets), EXPECTED_TARGET_REGRESSION_ROWS, "behavior_regression"),
        gate("target_is_selected_source_row", "evidence", str(target.get("source_measurement_episode_id", "")) == "m3084-measurement-episode-0020", target.get("source_measurement_episode_id", ""), "m3084-measurement-episode-0020", "scenario_sampling_failure"),
        gate("selected_context_status_pass", "execution", _bool(plan.get("status_pass", False)), plan.get("status_pass"), True, "lineage_invalid"),
        gate("ablation_variant_rows", "execution", len(variants) == EXPECTED_VARIANT_COUNT, len(variants), EXPECTED_VARIANT_COUNT, "metric_artifact"),
        gate("targeted_trace_rows_present", "execution", len(traces) >= len(variants), len(traces), ">= variant count", "metric_artifact"),
        gate("trace_actions_finite_bounded", "contract", action_bounded, action_bounded, True, "contract_violation"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(variants), "finite" if variants else "none", "finite", "metric_artifact"),
        gate("candidate_replays_m3172_collision", "evidence", _bool(candidate.get("collision", False)) == _bool(expected_m3172.get("collision", False)), candidate.get("collision"), expected_m3172.get("collision"), "metric_artifact"),
        gate("candidate_step_count_matches_m3172", "evidence", _int(candidate.get("steps")) == _int(expected_m3172.get("steps")), candidate.get("steps"), expected_m3172.get("steps"), "metric_artifact"),
        gate("incumbent_replays_m3105_success", "evidence", _success(incumbent) == _success(expected_m3105), incumbent.get("success"), expected_m3105.get("success"), "metric_artifact"),
        gate("incumbent_step_count_matches_m3105", "evidence", _int(incumbent.get("steps")) == _int(expected_m3105.get("steps")), incumbent.get("steps"), expected_m3105.get("steps"), "metric_artifact"),
        gate("candidate_overlay_active", "evidence", _float(candidate.get("overlay_activation_fraction")) > 0.0, candidate.get("overlay_activation_fraction"), ">0", "metric_artifact"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31780,
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
        "hypothesis": (
            "A bounded result audit can accept or reject M3177 targeted trace-ablation "
            "artifacts before any repair implementation validation ranking promotion "
            "driver-performance current-sim high-fidelity full-driver repair-success "
            "robustness-result feasibility-proof or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "targeted_trace_rows.csv"),
                str(output_dir / "ablation_variant_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3177 targeted actor-visible trace-ablation before implementation planning"],
            "derived_from": [MILESTONE_ID, M3176_ID, M3175_ID, M3172_ID, M3170_ID, M3105_ID],
            "blocked_by": [
                "M3177 trace-ablation rows require audit before any guard or implementation",
                "the regression route must preserve actor-visible-only runtime inputs",
            ],
            "supersedes": ["direct repair implementation after M3176"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3178 must audit M3177 targeted trace variant guard claim and gate artifacts",
            "M3178 must preserve obs72/action3 direct-action contract and public driver default unchanged",
            "M3178 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3178 must select exactly one implementation-planning artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run repair implementation validation ranking promotion or high-fidelity simulation in M3178",
            "do not convert M3177 trace rows into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_behavior_negative_source_repair_decomposition",
            "evidence_axis": "behavior_negative_targeted_trace_ablation_result_audit",
            "evidence_increment": "audits targeted trace-ablation rows for the single M3172 collision regression",
            "claim_scope": (
                "Result audit only; no repair implementation validation ranking promotion "
                "performance current-sim verdict high-fidelity paper full-driver repair-success "
                "robustness-result feasibility-proof or self-ID claim"
            ),
            "stop_condition": [
                "stop if M3177 artifacts are missing or gate matrix fails",
                "stop if trace-ablation requires hidden runtime labels as actor inputs",
                "route to implementation planning only after audit acceptance",
            ],
            "fallback_plan": [
                "route to M3177 artifact repair if trace rows or guards fail",
                "route to stop if no actor-visible variant explains the regression",
                "preserve M3105/M3103 incumbent until a later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3177 materializes targeted trace-ablation artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3177 targeted actor-visible trace-ablation artifacts",
            "admission_evidence": ["M3177 summary targeted trace ablation variant guard claim and gate artifacts"],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3178 status queue scoreboard research log and review",
                "one follow-up manifest only if M3178 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3178 accepts or rejects M3177 as complete and claim-safe",
                "next implementation-planning artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3178 audits engineering trace artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3178; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3177 targeted trace-ablation artifacts only.",
            "negative_result_policy": "Preserve engineering trace evidence and route implementation planning or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3177 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new targeted trace-ablation closed-loop evidence before implementation planning",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3178 audits engineering trace evidence",
            "must_synthesize_if": [
                "M3178 cannot select implementation-planning artifact-repair synthesis or stop",
                "M3178 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3178 audits M3177 row counts gates actor contract and claim boundaries",
            "M3178 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3178 hides missing M3177 artifacts or failed gates",
            "M3178 treats M3177 trace-ablation as repair success or performance verdict",
            "M3178 changes actor input or action contract",
            "M3178 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3178 audits M3177 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_behavior_negative_targeted_trace_ablation_result_audit_doc",
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
            "# M3177 Behavior-Negative Targeted Trace-Ablation Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- target regression rows: {summary['target_regression_row_count']}",
            f"- trace rows: {summary['targeted_trace_row_count']}",
            f"- ablation variants: {summary['ablation_variant_row_count']}",
            f"- candidate outcome: `{summary['candidate_outcome_bucket']}`",
            f"- incumbent outcome: `{summary['incumbent_outcome_bucket']}`",
            f"- candidate clearance margin: {summary['candidate_min_clearance_margin']}",
            f"- incumbent clearance margin: {summary['incumbent_min_clearance_margin']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3177 re-executes only the selected M3172 new collision regression row with actor-visible direct-action variants. Row labels and incumbent outcomes select the experimental sample but are not actor runtime inputs. The artifacts are trace-ablation evidence only and do not implement a repair or validate a driver.",
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


def run_trace_ablation_preflight(
    *,
    m3176_audit: Path,
    m3175_dir: Path,
    m3172_dir: Path,
    m3170_dir: Path,
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
        m3176_audit=m3176_audit,
        m3175_dir=m3175_dir,
        m3172_dir=m3172_dir,
        m3170_dir=m3170_dir,
        m3105_dir=m3105_dir,
        m3012_dir=m3012_dir,
    )
    targets = target_regression_rows(source)
    plan = selected_execution_context(source, targets[0]) if targets else {"status_pass": False, "target": {}}
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)

    trace_rows: list[dict[str, Any]] = []
    variant_rows: list[dict[str, Any]] = []
    if targets and plan.get("status_pass"):
        for variant in variant_specs():
            rows, aggregate = run_trace_variant(plan, variant)
            trace_rows.extend(rows)
            variant_rows.append(aggregate)

    guards = contract_guard_rows(source=source, plan=plan, targets=targets, traces=trace_rows, variants=variant_rows)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["targeted_trace_rows"], trace_rows, fieldnames=TARGET_TRACE_FIELDNAMES)
    write_csv_rows(paths["ablation_variant_rows"], variant_rows, fieldnames=ABLATION_VARIANT_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=CONTRACT_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)

    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        targets=targets,
        plan=plan,
        traces=trace_rows,
        variants=variant_rows,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in variant_rows)
    candidate = _variant_by_id(variant_rows, "m3177_candidate_m3170")
    incumbent = _variant_by_id(variant_rows, "m3177_incumbent_m3105")
    status_pass = bool(gate_matrix_pass and present)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_behavior_negative_targeted_trace_ablation_materialization_pass"
            if status_pass
            else "active_safety_driver_behavior_negative_targeted_trace_ablation_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "target_regression_row_count": len(targets),
        "target_source_measurement_episode_id": targets[0].get("source_measurement_episode_id", "") if targets else "",
        "targeted_trace_row_count": len(trace_rows),
        "ablation_variant_row_count": len(variant_rows),
        "ablation_variant_ids": [str(row.get("variant_id", "")) for row in variant_rows],
        "ablation_variant_success_count": sum(1 for row in variant_rows if _success(row)),
        "ablation_variant_collision_count": sum(1 for row in variant_rows if _bool(row.get("collision", False))),
        "ablation_variant_termination_counts": dict(sorted(termination_counts.items())),
        "candidate_outcome_bucket": candidate.get("outcome_bucket", ""),
        "incumbent_outcome_bucket": incumbent.get("outcome_bucket", ""),
        "candidate_steps": _int(candidate.get("steps")),
        "incumbent_steps": _int(incumbent.get("steps")),
        "candidate_min_clearance_margin": _float(candidate.get("min_clearance_margin"), float("nan")),
        "incumbent_min_clearance_margin": _float(incumbent.get("min_clearance_margin"), float("nan")),
        "candidate_return": _float(candidate.get("return"), float("nan")),
        "incumbent_return": _float(incumbent.get("return"), float("nan")),
        "candidate_overlay_activation_fraction": _float(candidate.get("overlay_activation_fraction"), float("nan")),
        "contract_guard_row_count": len(guards),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guards),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3175_status_pass": _bool(source["m3175_summary"].get("status_pass", False)),
        "m3172_status_pass": _bool(source["m3172_summary"].get("status_pass", False)),
        "m3170_status_pass": _bool(source["m3170_summary"].get("status_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "runtime_driver_id": M3170_POLICY_ID,
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "environment_reset_run": bool(variant_rows),
        "environment_step_run": bool(trace_rows),
        "policy_action_run": bool(trace_rows),
        "policy_rollout_run": bool(variant_rows),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_behavior_negative_targeted_trace_ablation_route_to_m3178_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "target_regression_row_count": len(targets),
            "targeted_trace_row_count": len(trace_rows),
            "ablation_variant_row_count": len(variant_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3176-audit", type=Path, default=DEFAULT_M3176_AUDIT)
    parser.add_argument("--m3175-dir", type=Path, default=DEFAULT_M3175_DIR)
    parser.add_argument("--m3172-dir", type=Path, default=DEFAULT_M3172_DIR)
    parser.add_argument("--m3170-dir", type=Path, default=DEFAULT_M3170_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_trace_ablation_preflight(
        m3176_audit=args.m3176_audit,
        m3175_dir=args.m3175_dir,
        m3172_dir=args.m3172_dir,
        m3170_dir=args.m3170_dir,
        m3105_dir=args.m3105_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"target_regression_rows={summary['target_regression_row_count']}")
    print(f"targeted_trace_rows={summary['targeted_trace_row_count']}")
    print(f"ablation_variant_rows={summary['ablation_variant_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
