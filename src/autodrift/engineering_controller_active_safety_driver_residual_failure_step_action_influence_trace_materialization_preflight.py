"""Materialize M3115 residual failure step/action influence traces."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.evaluate import outcome_bucket_from_info
import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight as m3112
import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight as m3110
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-"
    "influence-trace-materialization-preflight"
)
NEXT_ID = (
    "m3116-engineering-controller-active-safety-driver-residual-failure-step-action-"
    "influence-trace-materialization-result-audit"
)
M3114_ID = (
    "m3114-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-plateau-synthesis"
)
M3112_ID = (
    "m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-full-fresh-measurement-preflight"
)
M3108_ID = (
    "m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "failure-decomposition-materialization-preflight"
)

DEFAULT_M3114_SYNTHESIS = Path(f"docs/{M3114_ID}.md")
DEFAULT_M3112_DIR = Path(
    "runs/m3112_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3108_DIR = Path(
    "runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "failure_decomposition_materialization_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_"
    "influence_trace_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
POLICY_NAME = "active_safety_driver_residual_failure_step_action_influence_trace"
CLAIM_SCOPE = (
    "M3115 Active Safety Driver residual failure step/action influence trace "
    "materialization only; the seven M3112 residual collision/offtrack failures may be "
    "replayed through the already materialized M3110 obs72-to-action3 direct-action "
    "function to write diagnostic step traces, action influence summaries, claim, gate, "
    "doc, and M3116 audit artifacts. No repair materialization, validation, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity "
    "validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair materialization, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

CONTEXT_FIELDNAMES = [
    "trace_episode_id",
    "residual_failure_id",
    "measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "executable_workload_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "eval_seed",
]
STEP_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "trace_step_id",
    "step_index",
    "terminal_step",
    "terminated",
    "truncated",
    "success_after_step",
    "collision_after_step",
    "offtrack_after_step",
    "termination_reason_after_step",
    "outcome_bucket_after_step",
    "reward",
    "steer_action",
    "throttle_action",
    "brake_action",
    "throttle_physical",
    "brake_physical",
    "action_abs_max",
    "action_l2",
    "vx_body_mps_actor_visible",
    "vy_body_mps_actor_visible",
    "yaw_rate_rad_s_actor_visible",
    "ay_body_mps2_actor_visible",
    "steer_rate_signal_actor_visible",
    "obstacle_urgency_actor_visible",
    "edge_urgency_actor_visible",
    "road_center_error_actor_visible",
    "obstacle_avoid_direction_actor_visible",
    "nearest_obstacle_x_m_actor_visible",
    "nearest_obstacle_y_m_actor_visible",
    "nearest_obstacle_half_width_m_actor_visible",
    "visible_obstacle_slot_count",
    "min_actor_edge_margin_m",
    "speed_mps_after_step",
    "beta_after_step",
    "high_sideslip_after_step",
    "lateral_error_m_after_step",
    "heading_error_rad_after_step",
    "curvature_after_step",
    "progress_after_step",
    "obstacle_perception_visible_after_step",
    "obstacle_distance_m_after_step",
    "obstacle_lateral_offset_m_after_step",
    "active_obstacle_body_x_m_after_step",
    "active_obstacle_body_y_m_after_step",
    "active_obstacle_half_width_m_after_step",
    "min_obstacle_clearance_m_after_step",
    "obstacle_collision_radius_m_after_step",
    "min_clearance_margin_m_after_step",
    "track_width_m_after_step",
    "max_off_track_overshoot_m_after_step",
    "hard_offtrack_failure_after_step",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
INFLUENCE_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "trace_step_count",
    "terminal_termination_reason",
    "terminal_outcome_bucket",
    "terminal_collision",
    "terminal_offtrack",
    "terminal_success",
    "terminal_speed_mps",
    "terminal_beta_abs",
    "terminal_lateral_error_m",
    "terminal_min_clearance_margin_m",
    "min_clearance_margin_m_min",
    "high_sideslip_fraction",
    "steer_action_mean",
    "steer_action_abs_mean",
    "steer_action_abs_max",
    "throttle_action_mean",
    "brake_action_mean",
    "brake_physical_mean",
    "brake_physical_max",
    "final_10_mean_throttle_action",
    "final_10_mean_brake_physical",
    "final_10_mean_abs_steer",
    "action_saturation_fraction",
    "max_obstacle_urgency_actor_visible",
    "step_of_max_obstacle_urgency",
    "max_edge_urgency_actor_visible",
    "step_of_max_edge_urgency",
    "max_abs_road_center_error_actor_visible",
    "min_actor_edge_margin_m_min",
    "visible_obstacle_fraction",
    "terminal_obstacle_x_m_actor_visible",
    "terminal_obstacle_y_m_actor_visible",
    "terminal_edge_urgency_actor_visible",
    "terminal_obstacle_urgency_actor_visible",
    "hard_safety_signal_present",
    "primary_diagnostic_label",
    "action_influence_interpretation",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3115",
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


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _min(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.min(finite)) if finite else ""


def _max(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.max(finite)) if finite else ""


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success", False))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "") or "") == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "") or "") == "speed_too_low"


def _physical_throttle(action_value: float) -> float:
    return float(np.clip(0.5 * (action_value + 1.0), 0.0, 1.0))


def _physical_brake(action_value: float) -> float:
    return float(np.clip(0.5 * (action_value + 1.0), 0.0, 1.0))


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "residual_step_trace_rows": output_dir / "residual_step_trace_rows.csv",
        "residual_action_influence_rows": output_dir / "residual_action_influence_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3114_synthesis: Path, m3112_dir: Path, m3108_dir: Path, m3012_dir: Path) -> dict[str, Any]:
    paths = {
        "m3114_synthesis": m3114_synthesis,
        "m3112_summary": m3112_dir / "summary.json",
        "m3112_measurement_rows": m3112_dir / "measurement_episode_rows.csv",
        "m3112_comparison_rows": m3112_dir / "same_row_comparison_rows.csv",
        "m3112_gate_rows": m3112_dir / "gate_matrix.csv",
        "m3108_summary": m3108_dir / "summary.json",
        "m3108_residual_rows": m3108_dir / "residual_failure_rows.csv",
        "m3108_gate_rows": m3108_dir / "gate_matrix.csv",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3114_synthesis_text": paths["m3114_synthesis"].read_text(encoding="utf-8") if exists["m3114_synthesis"] else "",
        "m3112_summary": read_json(paths["m3112_summary"]) if exists["m3112_summary"] else {},
        "m3112_measurement_rows": read_csv_rows(paths["m3112_measurement_rows"]),
        "m3112_comparison_rows": read_csv_rows(paths["m3112_comparison_rows"]),
        "m3112_gate_rows": read_csv_rows(paths["m3112_gate_rows"]),
        "m3108_summary": read_json(paths["m3108_summary"]) if exists["m3108_summary"] else {},
        "m3108_residual_rows": read_csv_rows(paths["m3108_residual_rows"]),
        "m3108_gate_rows": read_csv_rows(paths["m3108_gate_rows"]),
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def _base_plan_context(row: Mapping[str, Any], residual: Mapping[str, Any], index: int) -> dict[str, Any]:
    return {
        "trace_episode_id": f"m3115-residual-trace-episode-{index:04d}",
        "residual_failure_id": residual.get("residual_failure_id", ""),
        "measurement_episode_id": row.get("runtime_smoke_episode_id", ""),
        "source_measurement_episode_id": row.get("source_measurement_episode_id", ""),
        "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
        "axis_id": row.get("axis_id", ""),
        "binding_role": row.get("binding_role", ""),
        "task_family": row.get("task_family", ""),
        "executable_workload_id": row.get("executable_workload_id", ""),
        "executable_source_spec_id": row.get("executable_source_spec_id", ""),
        "task_source_id": row.get("task_source_id", ""),
        "base_profile_name": row.get("base_profile_name", ""),
        "eval_seed": row.get("eval_seed", ""),
    }


def residual_trace_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build a row-preserving trace plan from M3108 residual IDs and M3112 rows."""

    residual_by_source = {
        str(row.get("source_measurement_episode_id", "")): row for row in source.get("m3108_residual_rows", [])
    }
    m3112_by_source = {
        str(row.get("source_measurement_episode_id", "")): row for row in source.get("m3112_measurement_rows", [])
    }
    workload_by_id = {
        str(row.get("executable_workload_id", "")): row for row in source.get("m3012_workload_rows", [])
    }
    plan: list[dict[str, Any]] = []
    for index, residual in enumerate(source.get("m3108_residual_rows", []), start=1):
        source_id = str(residual.get("source_measurement_episode_id", ""))
        measurement = m3112_by_source.get(source_id, {})
        context = _base_plan_context(measurement, residual, index)
        workload = workload_by_id.get(str(context.get("executable_workload_id", "")), {})
        row = {
            **context,
            "config_path": workload.get("config_path", ""),
            "source_residual_measurement_episode_id": residual.get("measurement_episode_id", ""),
            "source_residual_termination_reason": residual.get("termination_reason", ""),
            "source_residual_outcome_bucket": residual.get("outcome_bucket", ""),
            "m3112_termination_reason": measurement.get("termination_reason", ""),
            "m3112_outcome_bucket": measurement.get("outcome_bucket", ""),
            "m3112_collision": _bool(measurement.get("collision", False)),
            "m3112_offtrack": _offtrack(measurement),
            "m3112_speed_too_low": _speed_too_low(measurement),
            "m3112_success": _success(measurement),
            "status_pass": bool(
                source_id
                and source_id in residual_by_source
                and bool(measurement)
                and not _success(measurement)
                and (
                    _bool(measurement.get("collision", False))
                    or _offtrack(measurement)
                    or _speed_too_low(measurement)
                )
                and bool(workload.get("config_path", ""))
            ),
            "claim_boundary": CLAIM_SCOPE,
        }
        plan.append(row)
    return plan


def context_fields(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {field: plan.get(field, "") for field in CONTEXT_FIELDNAMES}


def actor_visible_diagnostic_features(observation: np.ndarray) -> dict[str, Any]:
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    hard = m3110.v4_hard_safety_features(obs, m3110.M3110_POLICY_CONFIG)
    left = obs[12:28].reshape(8, 2).astype(np.float32)
    right = obs[28:44].reshape(8, 2).astype(np.float32)
    margin_y = np.minimum(np.abs(left[:, 1] * 20.0), np.abs(right[:, 1] * 20.0))
    min_edge_margin = float(np.nanmin(margin_y[:4])) if margin_y.size else float("nan")

    visible_slots = []
    for slot_index in range(4):
        base = 44 + slot_index * 7
        present = float(obs[base])
        x_body = float(obs[base + 1] * 80.0)
        y_body = float(obs[base + 2] * 20.0)
        half_width = float(obs[base + 5] * 5.0)
        if present > 0.5 and x_body > 0.0:
            visible_slots.append((x_body, y_body, half_width))
    if visible_slots:
        nearest = min(visible_slots, key=lambda item: item[0])
        nearest_x, nearest_y, nearest_half_width = nearest
    else:
        nearest_x = nearest_y = nearest_half_width = float("nan")

    return {
        "vx_body_mps_actor_visible": float(obs[0] * 20.0),
        "vy_body_mps_actor_visible": float(obs[1] * 12.0),
        "yaw_rate_rad_s_actor_visible": float(obs[2] * 2.5),
        "ay_body_mps2_actor_visible": float(obs[4] * 15.0),
        "steer_rate_signal_actor_visible": float(obs[6]),
        "obstacle_urgency_actor_visible": float(hard["obstacle_urgency"]),
        "edge_urgency_actor_visible": float(hard["edge_urgency"]),
        "road_center_error_actor_visible": float(hard["road_center_error"]),
        "obstacle_avoid_direction_actor_visible": float(hard["obstacle_avoid_direction"]),
        "nearest_obstacle_x_m_actor_visible": nearest_x,
        "nearest_obstacle_y_m_actor_visible": nearest_y,
        "nearest_obstacle_half_width_m_actor_visible": nearest_half_width,
        "visible_obstacle_slot_count": len(visible_slots),
        "min_actor_edge_margin_m": min_edge_margin,
    }


class M3115TracePolicy(m3112.M3112RepairMeasurementPolicy):
    """Policy adapter for the already materialized M3110 direct-action function."""

    pass


def trace_episode(
    *,
    env: Any,
    policy: M3115TracePolicy,
    plan: Mapping[str, Any],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obs, info = env.reset(seed=seed)
    policy.reset()
    step_rows: list[dict[str, Any]] = []
    terminated = False
    truncated = False
    rewards: list[float] = []
    step_infos: list[dict[str, Any]] = []
    while not (terminated or truncated):
        action = np.asarray(policy.act(obs, info), dtype=np.float32)
        if action.shape != (ACTION_DIM,):
            raise ValueError(f"expected action shape {(ACTION_DIM,)}, got {action.shape}")
        if not np.all(np.isfinite(action)):
            raise ValueError("action contains non-finite values")
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        features = actor_visible_diagnostic_features(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        step_infos.append(dict(info))
        rewards.append(float(reward))
        step_index = int(info.get("step", len(step_rows) + 1))
        collision = _bool(info.get("collision", False))
        offtrack = str(info.get("termination_reason", "") or "") == "off_track" or _bool(
            info.get("hard_offtrack_failure", False)
        )
        outcome_bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
        row = {
            **context_fields(plan),
            "trace_step_id": f"{plan.get('trace_episode_id', 'm3115-trace')}-step-{step_index:04d}",
            "step_index": step_index,
            "terminal_step": bool(terminated or truncated),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "success_after_step": _bool(info.get("obstacle_completed", False)) and not collision,
            "collision_after_step": collision,
            "offtrack_after_step": offtrack,
            "termination_reason_after_step": info.get("termination_reason", ""),
            "outcome_bucket_after_step": outcome_bucket,
            "reward": float(reward),
            "steer_action": float(action[0]),
            "throttle_action": float(action[1]),
            "brake_action": float(action[2]),
            "throttle_physical": _physical_throttle(float(action[1])),
            "brake_physical": _physical_brake(float(action[2])),
            "action_abs_max": float(np.max(np.abs(action))),
            "action_l2": float(np.linalg.norm(action)),
            **features,
            "speed_mps_after_step": _float(info.get("speed")),
            "beta_after_step": _float(info.get("beta")),
            "high_sideslip_after_step": abs(_float(info.get("beta"))) > 0.35,
            "lateral_error_m_after_step": _float(info.get("lateral_error")),
            "heading_error_rad_after_step": _float(info.get("heading_error")),
            "curvature_after_step": _float(info.get("curvature")),
            "progress_after_step": _float(info.get("progress")),
            "obstacle_perception_visible_after_step": _bool(info.get("obstacle_perception_visible", False)),
            "obstacle_distance_m_after_step": _float(info.get("obstacle_distance")),
            "obstacle_lateral_offset_m_after_step": _float(info.get("obstacle_lateral_offset")),
            "active_obstacle_body_x_m_after_step": _float(info.get("active_obstacle_body_x")),
            "active_obstacle_body_y_m_after_step": _float(info.get("active_obstacle_body_y")),
            "active_obstacle_half_width_m_after_step": _float(info.get("active_obstacle_half_width")),
            "min_obstacle_clearance_m_after_step": _float(info.get("min_obstacle_clearance")),
            "obstacle_collision_radius_m_after_step": _float(info.get("obstacle_collision_radius")),
            "min_clearance_margin_m_after_step": _float(info.get("min_clearance_margin")),
            "track_width_m_after_step": _float(info.get("track_width")),
            "max_off_track_overshoot_m_after_step": _float(info.get("max_off_track_overshoot_env")),
            "hard_offtrack_failure_after_step": _bool(info.get("hard_offtrack_failure", False)),
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        step_rows.append(row)
    aggregate = influence_row_from_trace(plan=plan, step_rows=step_rows, policy=policy)
    aggregate["return"] = float(np.sum(rewards)) if rewards else 0.0
    aggregate["episode_info_step_count"] = len(step_infos)
    return step_rows, aggregate


def _final_window(rows: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    return rows[-count:] if len(rows) > count else rows


def _step_of_max(rows: list[dict[str, Any]], key: str) -> int | str:
    finite = [(row, _float(row.get(key))) for row in rows if np.isfinite(_float(row.get(key)))]
    if not finite:
        return ""
    row, _ = max(finite, key=lambda item: item[1])
    return int(row.get("step_index", 0))


def _diagnostic_label(rows: list[dict[str, Any]]) -> tuple[str, str]:
    terminal = rows[-1] if rows else {}
    reason = str(terminal.get("termination_reason_after_step", "") or "")
    max_obstacle = _float(_max(_float(row.get("obstacle_urgency_actor_visible")) for row in rows), 0.0)
    max_edge = _float(_max(_float(row.get("edge_urgency_actor_visible")) for row in rows), 0.0)
    final_rows = _final_window(rows)
    final_brake = _float(_mean(_float(row.get("brake_physical")) for row in final_rows), 0.0)
    final_abs_steer = _float(_mean(abs(_float(row.get("steer_action"), 0.0)) for row in final_rows), 0.0)
    high_sideslip_fraction = _float(
        _mean(1.0 if _bool(row.get("high_sideslip_after_step", False)) else 0.0 for row in rows),
        0.0,
    )
    terminal_speed = _float(terminal.get("speed_mps_after_step"), 0.0)
    if reason == "obstacle_collision":
        if max_obstacle < 0.10:
            return (
                "collision_actor_visible_obstacle_signal_late_or_absent",
                "collision occurred while actor-visible obstacle urgency stayed low in the trace window",
            )
        if final_brake < 0.55 and terminal_speed > 12.0:
            return (
                "collision_brake_response_insufficient_under_visible_obstacle_urgency",
                "collision occurred after visible obstacle urgency while final-window brake demand stayed moderate",
            )
        return (
            "collision_action_present_but_clearance_unresolved",
            "collision occurred despite visible obstacle signal and nonzero action response, so trace supports diagnosis only",
        )
    if reason == "off_track":
        if max_edge < 0.20:
            return (
                "offtrack_actor_visible_edge_signal_late_or_absent",
                "offtrack occurred while actor-visible edge urgency stayed low in the trace window",
            )
        if final_abs_steer < 0.25:
            return (
                "offtrack_boundary_steer_response_insufficient",
                "offtrack occurred after edge urgency while final-window steering magnitude stayed moderate",
            )
        if high_sideslip_fraction > 0.25:
            return (
                "offtrack_stability_recovery_limited",
                "offtrack occurred with sustained high sideslip, indicating recovery authority or timing remains unresolved",
            )
        return (
            "offtrack_boundary_recovery_unresolved",
            "offtrack occurred with visible edge signal and action response, so trace supports diagnosis only",
        )
    return (
        "non_target_terminal_outcome",
        "terminal reason is outside the expected residual collision/offtrack target set",
    )


def influence_row_from_trace(
    *,
    plan: Mapping[str, Any],
    step_rows: list[dict[str, Any]],
    policy: M3115TracePolicy | None = None,
) -> dict[str, Any]:
    terminal = step_rows[-1] if step_rows else {}
    final_rows = _final_window(step_rows)
    label, interpretation = _diagnostic_label(step_rows)
    max_obstacle = _max(_float(row.get("obstacle_urgency_actor_visible")) for row in step_rows)
    max_edge = _max(_float(row.get("edge_urgency_actor_visible")) for row in step_rows)
    telemetry = policy.telemetry() if policy is not None else {}
    del telemetry
    return {
        **context_fields(plan),
        "trace_step_count": len(step_rows),
        "terminal_termination_reason": terminal.get("termination_reason_after_step", ""),
        "terminal_outcome_bucket": terminal.get("outcome_bucket_after_step", ""),
        "terminal_collision": _bool(terminal.get("collision_after_step", False)),
        "terminal_offtrack": _bool(terminal.get("offtrack_after_step", False)),
        "terminal_success": _bool(terminal.get("success_after_step", False)),
        "terminal_speed_mps": terminal.get("speed_mps_after_step", ""),
        "terminal_beta_abs": abs(_float(terminal.get("beta_after_step"))),
        "terminal_lateral_error_m": terminal.get("lateral_error_m_after_step", ""),
        "terminal_min_clearance_margin_m": terminal.get("min_clearance_margin_m_after_step", ""),
        "min_clearance_margin_m_min": _min(_float(row.get("min_clearance_margin_m_after_step")) for row in step_rows),
        "high_sideslip_fraction": _mean(
            1.0 if _bool(row.get("high_sideslip_after_step", False)) else 0.0 for row in step_rows
        ),
        "steer_action_mean": _mean(_float(row.get("steer_action")) for row in step_rows),
        "steer_action_abs_mean": _mean(abs(_float(row.get("steer_action"), 0.0)) for row in step_rows),
        "steer_action_abs_max": _max(abs(_float(row.get("steer_action"), 0.0)) for row in step_rows),
        "throttle_action_mean": _mean(_float(row.get("throttle_action")) for row in step_rows),
        "brake_action_mean": _mean(_float(row.get("brake_action")) for row in step_rows),
        "brake_physical_mean": _mean(_float(row.get("brake_physical")) for row in step_rows),
        "brake_physical_max": _max(_float(row.get("brake_physical")) for row in step_rows),
        "final_10_mean_throttle_action": _mean(_float(row.get("throttle_action")) for row in final_rows),
        "final_10_mean_brake_physical": _mean(_float(row.get("brake_physical")) for row in final_rows),
        "final_10_mean_abs_steer": _mean(abs(_float(row.get("steer_action"), 0.0)) for row in final_rows),
        "action_saturation_fraction": _mean(
            1.0 if _float(row.get("action_abs_max"), 0.0) >= 0.999 else 0.0 for row in step_rows
        ),
        "max_obstacle_urgency_actor_visible": max_obstacle,
        "step_of_max_obstacle_urgency": _step_of_max(step_rows, "obstacle_urgency_actor_visible"),
        "max_edge_urgency_actor_visible": max_edge,
        "step_of_max_edge_urgency": _step_of_max(step_rows, "edge_urgency_actor_visible"),
        "max_abs_road_center_error_actor_visible": _max(
            abs(_float(row.get("road_center_error_actor_visible"), 0.0)) for row in step_rows
        ),
        "min_actor_edge_margin_m_min": _min(_float(row.get("min_actor_edge_margin_m")) for row in step_rows),
        "visible_obstacle_fraction": _mean(
            1.0 if int(_float(row.get("visible_obstacle_slot_count"), 0.0)) > 0 else 0.0 for row in step_rows
        ),
        "terminal_obstacle_x_m_actor_visible": terminal.get("nearest_obstacle_x_m_actor_visible", ""),
        "terminal_obstacle_y_m_actor_visible": terminal.get("nearest_obstacle_y_m_actor_visible", ""),
        "terminal_edge_urgency_actor_visible": terminal.get("edge_urgency_actor_visible", ""),
        "terminal_obstacle_urgency_actor_visible": terminal.get("obstacle_urgency_actor_visible", ""),
        "hard_safety_signal_present": bool(_float(max_obstacle, 0.0) > 0.10 or _float(max_edge, 0.0) > 0.20),
        "primary_diagnostic_label": label,
        "action_influence_interpretation": interpretation,
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "repair_success_claim_made": False,
        "validation_run": False,
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def trace_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    all_steps: list[dict[str, Any]] = []
    influences: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3115 residual trace plan row failed guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3088.m3075.profile_config_for_runtime(
                    read_json(config_path), profile_name=profile_name
                )
            profile_config = profile_cache[cache_key]
            env_config = m3088.env_config_for_executable_profile(
                executable_spec=executable_spec,
                profile_config=profile_config,
            )
            env = m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)
            policy = M3115TracePolicy()
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                step_rows, influence = trace_episode(env=env, policy=policy, plan=plan, seed=int(plan["eval_seed"]))
            finally:
                env.close()
            all_steps.extend(step_rows)
            influences.append(influence)
        except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
            failure = {field: plan.get(field, "") for field in CONTEXT_FIELDNAMES}
            failure.update(
                {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "runtime_base_policy_required": False,
                    "hidden_oracle_actor_input_required": False,
                    "repair_success_claim_made": False,
                    "validation_run": False,
                    "driver_performance_claim_made": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            failures.append(failure)
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_residual_trace_row_count": len(plan_rows),
                "residual_step_trace_row_count": len(all_steps),
                "residual_action_influence_row_count": len(influences),
                "residual_trace_failure_row_count": len(failures),
                "recorded_episode_count": len(influences) + len(failures),
                "latest_trace_episode_id": plan.get("trace_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"steps": all_steps, "influences": influences, "failures": failures}


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31110,
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
        "hypothesis": "A bounded result audit can accept or reject the M3115 residual failure step/action influence trace artifacts before any repair materialization validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "residual_step_trace_rows.csv"),
                str(output_dir / "residual_action_influence_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3115 row-preserving residual step/action influence traces"],
            "derived_from": [MILESTONE_ID, M3114_ID, M3112_ID, M3108_ID],
            "blocked_by": [
                "M3115 diagnostic traces require audit before any repair materialization route",
                "diagnostic action-influence labels are not repair-success or performance evidence",
            ],
            "supersedes": ["direct interpretation of M3115 trace artifacts without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3116 must audit M3115 summary trace action-influence claim and gate artifacts",
            "M3116 must preserve seven residual row identities and obs72/action3 direct [steer throttle brake] contract",
            "M3116 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3116 must choose exactly one next route: repair synthesis, trace artifact repair, or stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3115 diagnostic labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_step_action_influence_diagnosis",
            "evidence_axis": "residual_failure_step_action_trace_result_audit",
            "evidence_increment": "audits row-preserving per-step action and actor-visible risk traces for the seven residual failures",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3115 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize before repair if trace labels are mixed or inconclusive",
            ],
            "fallback_plan": [
                "route to M3115 artifact repair if trace artifacts are incomplete or contract-unsafe",
                "route to repair synthesis if trace artifacts are complete and point to actor-visible action influence gaps",
                "route to stop if deployable actor boundary prevents a useful next repair hypothesis",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3115 completes residual step/action influence trace materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3115 residual failure step/action influence trace artifacts",
            "admission_evidence": ["M3115 summary gate matrix residual step trace action influence and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3116 status queue scoreboard research log and review",
                "one follow-up manifest only if M3116 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3116 accepts or rejects M3115 artifacts as complete and claim-safe",
                "M3116 selects trace artifact repair, repair synthesis, or stop route explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3116 audits engineering trace artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3116; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3115 residual failure step/action trace artifacts only.",
            "negative_result_policy": "Preserve trace evidence and route to engineering synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3115 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits per-step action influence traces rather than another blind overlay repair",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3116 audits engineering hard-safety trace evidence",
            "must_synthesize_if": [
                "M3116 cannot accept M3115 as complete and claim-safe",
                "M3116 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3116 cannot select trace artifact repair, repair synthesis, or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3116 audits M3115 row counts gates actor contract trace completeness and claim boundaries",
            "M3116 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3116 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3116 hides M3115 missing rows or missing artifacts",
            "M3116 treats M3115 diagnostic traces as validation repair-success or performance verdict",
            "M3116 changes actor input or action contract",
            "M3116 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3116 audits M3115 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_residual_failure_step_action_influence_trace_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("residual_step_trace_rows", "diagnostic_trace", True, "residual_step_trace_rows.csv"),
        ("residual_action_influence_rows", "diagnostic_trace", True, "residual_action_influence_rows.csv"),
        ("row_identity_preservation", "lineage", True, "M3108 residual IDs and M3112 measurement source IDs"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3116 audit manifest"),
    ]
    blocked = [
        ("repair_materialization", "repair", "future audited repair synthesis route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action repair forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3115-{claim_id}",
            "claim_family": family,
            "allowed_in_m3115": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3115-{claim_id}",
            "claim_family": family,
            "allowed_in_m3115": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3115-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _all_forbidden_flags_clear(rows: list[dict[str, Any]]) -> bool:
    return not any(
        _bool(row.get(key, False))
        for row in rows
        for key in (
            "runtime_base_policy_required",
            "hidden_oracle_actor_input_required",
            "repair_success_claim_made",
            "validation_run",
            "driver_performance_claim_made",
        )
    )


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    step_rows: list[dict[str, Any]],
    influence_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3114_synthesis_text", ""))
    source_ids = {str(row.get("source_measurement_episode_id", "")) for row in source.get("m3108_residual_rows", [])}
    plan_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in plan_rows}
    influence_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in influence_rows}
    step_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in step_rows}
    step_counts = Counter(str(row.get("source_measurement_episode_id", "")) for row in step_rows)
    sample_action = m3110.residual_collision_offtrack_actor_visible_direct_action(
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        m3110.M3110_POLICY_CONFIG,
    )
    combined = step_rows + influence_rows + failure_rows
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3114_pivots_to_m3115", "lineage", "pivot_to_m3115_residual_failure_step_action_influence_trace_materialization" in synthesis_text, "pivot marker", "present", "lineage_invalid"),
        gate("m3112_status_pass", "lineage", _bool(source["m3112_summary"].get("status_pass", False)), source["m3112_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3112_gate_matrix_pass", "lineage", _bool(source["m3112_summary"].get("gate_matrix_pass", False)), source["m3112_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3108_status_pass", "lineage", _bool(source["m3108_summary"].get("status_pass", False)), source["m3108_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3108_gate_matrix_pass", "lineage", _bool(source["m3108_summary"].get("gate_matrix_pass", False)), source["m3108_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("policy_observation_shape", "contract", int(m3110.M3110_POLICY_CONFIG.get("observation_shape", -1)) == P0_OBSERVATION_DIM, m3110.M3110_POLICY_CONFIG.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", int(m3110.M3110_POLICY_CONFIG.get("action_shape", -1)) == ACTION_DIM, m3110.M3110_POLICY_CONFIG.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_output_semantics", "contract", str(m3110.M3110_POLICY_CONFIG.get("output_semantics", "")) == m3110.OUTPUT_SEMANTICS, m3110.M3110_POLICY_CONFIG.get("output_semantics"), m3110.OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(m3110.M3110_POLICY_CONFIG.get("runtime_base_policy_required", True)), m3110.M3110_POLICY_CONFIG.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("sample_action_shape", "contract", tuple(sample_action.shape) == (ACTION_DIM,), tuple(sample_action.shape), (ACTION_DIM,), "contract_violation"),
        gate("sample_action_finite_bounded", "contract", bool(np.all(np.isfinite(sample_action)) and np.max(np.abs(sample_action)) <= 1.0), "finite bounded", "finite bounded", "contract_violation"),
        gate("residual_source_row_count", "lineage", len(source_ids) == EXPECTED_RESIDUAL_ROWS, len(source_ids), EXPECTED_RESIDUAL_ROWS, "scenario_sampling_failure"),
        gate("trace_plan_row_count", "trace", len(plan_rows) == EXPECTED_RESIDUAL_ROWS, len(plan_rows), EXPECTED_RESIDUAL_ROWS, "scenario_sampling_failure"),
        gate("trace_plan_rows_pass", "trace", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("residual_row_identity_preserved_in_plan", "lineage", plan_source_ids == source_ids, sorted(plan_source_ids), sorted(source_ids), "lineage_invalid"),
        gate("trace_execution_accounted", "execution", len(influence_rows) + len(failure_rows) == len(plan_rows), len(influence_rows) + len(failure_rows), len(plan_rows), "metric_artifact"),
        gate("trace_failure_rows", "execution", len(failure_rows) == 0, len(failure_rows), 0, "metric_artifact"),
        gate("step_trace_rows_nonempty", "trace", bool(step_rows), len(step_rows), "nonzero", "metric_artifact"),
        gate("step_trace_identity_complete", "trace", step_source_ids == source_ids and all(step_counts[source_id] > 0 for source_id in source_ids), dict(sorted(step_counts.items())), "all residual rows have steps", "metric_artifact"),
        gate("action_influence_rows", "trace", len(influence_rows) == EXPECTED_RESIDUAL_ROWS, len(influence_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("action_influence_identity_complete", "trace", influence_source_ids == source_ids, sorted(influence_source_ids), sorted(source_ids), "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", _all_forbidden_flags_clear(combined), "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    diagnosis_counts = summary.get("primary_diagnostic_label_counts", {})
    diagnosis_lines = [f"- {label}: {count}" for label, count in sorted(diagnosis_counts.items())]
    return "\n".join(
        [
            "# M3115 Residual Failure Step/Action Influence Trace Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- residual trace plan rows: {summary['residual_trace_plan_row_count']}/{summary['target_residual_row_count']}",
            f"- residual step trace rows: {summary['residual_step_trace_row_count']}",
            f"- residual action influence rows: {summary['residual_action_influence_row_count']}",
            f"- residual trace failure rows: {summary['residual_trace_failure_row_count']}",
            f"- terminal collisions: {summary['terminal_collision_count']}",
            f"- terminal offtracks: {summary['terminal_offtrack_count']}",
            f"- max obstacle urgency: {summary['max_obstacle_urgency_actor_visible']}",
            f"- max edge urgency: {summary['max_edge_urgency_actor_visible']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Diagnostic Labels",
            "",
            *(diagnosis_lines or ["- none: 0"]),
            "",
            "## Interpretation",
            "",
            "M3115 replays only the seven M3112 residual collision/offtrack rows through the already materialized M3110 direct-action function and records per-step actor-visible risk signals with direct [steer, throttle, brake] actions. These artifacts diagnose action influence only. They are not repair materialization, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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


def run_trace_materialization_preflight(
    *,
    m3114_synthesis: Path,
    m3112_dir: Path,
    m3108_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3114_synthesis=m3114_synthesis,
        m3112_dir=m3112_dir,
        m3108_dir=m3108_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = residual_trace_plan(source)
    trace = trace_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    step_rows = trace["steps"]
    influence_rows = trace["influences"]
    failure_rows = trace["failures"]

    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["residual_step_trace_rows"], step_rows, STEP_FIELDNAMES),
        (paths["residual_action_influence_rows"], influence_rows, INFLUENCE_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        step_rows=step_rows,
        influence_rows=influence_rows,
        failure_rows=failure_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    terminal_counts = Counter(str(row.get("terminal_termination_reason", "")) for row in influence_rows)
    diagnosis_counts = Counter(str(row.get("primary_diagnostic_label", "")) for row in influence_rows)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_failure_step_action_influence_trace_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_failure_step_action_influence_trace_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": m3110.POLICY_ID,
        "target_residual_row_count": EXPECTED_RESIDUAL_ROWS,
        "residual_trace_plan_row_count": len(plan_rows),
        "residual_step_trace_row_count": len(step_rows),
        "residual_action_influence_row_count": len(influence_rows),
        "residual_trace_failure_row_count": len(failure_rows),
        "terminal_collision_count": sum(1 for row in influence_rows if _bool(row.get("terminal_collision", False))),
        "terminal_offtrack_count": sum(1 for row in influence_rows if _bool(row.get("terminal_offtrack", False))),
        "terminal_success_count": sum(1 for row in influence_rows if _bool(row.get("terminal_success", False))),
        "terminal_termination_counts": dict(sorted(terminal_counts.items())),
        "primary_diagnostic_label_counts": dict(sorted(diagnosis_counts.items())),
        "max_obstacle_urgency_actor_visible": _max(
            _float(row.get("max_obstacle_urgency_actor_visible")) for row in influence_rows
        ),
        "max_edge_urgency_actor_visible": _max(_float(row.get("max_edge_urgency_actor_visible")) for row in influence_rows),
        "hard_safety_signal_present_count": sum(
            1 for row in influence_rows if _bool(row.get("hard_safety_signal_present", False))
        ),
        "mean_final_10_brake_physical": _mean(_float(row.get("final_10_mean_brake_physical")) for row in influence_rows),
        "mean_final_10_abs_steer": _mean(_float(row.get("final_10_mean_abs_steer")) for row in influence_rows),
        "mean_action_saturation_fraction": _mean(_float(row.get("action_saturation_fraction")) for row in influence_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3112_status_pass": _bool(source["m3112_summary"].get("status_pass", False)),
        "m3112_gate_matrix_pass": _bool(source["m3112_summary"].get("gate_matrix_pass", False)),
        "m3108_status_pass": _bool(source["m3108_summary"].get("status_pass", False)),
        "m3108_gate_matrix_pass": _bool(source["m3108_summary"].get("gate_matrix_pass", False)),
        "candidate_output_semantics": m3110.OUTPUT_SEMANTICS,
        "candidate_output_components": list(m3110.ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "action = residual_collision_offtrack_actor_visible_direct_action(obs72) -> [steer, throttle, brake]",
        "environment_reset_run": bool(influence_rows),
        "environment_step_run": bool(step_rows),
        "policy_action_run": bool(step_rows),
        "policy_rollout_run": bool(influence_rows),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_materialization_run": False,
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
        "decision": "active_safety_driver_residual_failure_step_action_influence_trace_route_to_m3116_result_audit",
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
            "scheduled_residual_trace_row_count": len(plan_rows),
            "residual_step_trace_row_count": len(step_rows),
            "residual_action_influence_row_count": len(influence_rows),
            "residual_trace_failure_row_count": len(failure_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3114-synthesis", type=Path, default=DEFAULT_M3114_SYNTHESIS)
    parser.add_argument("--m3112-dir", type=Path, default=DEFAULT_M3112_DIR)
    parser.add_argument("--m3108-dir", type=Path, default=DEFAULT_M3108_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_trace_materialization_preflight(
        m3114_synthesis=args.m3114_synthesis,
        m3112_dir=args.m3112_dir,
        m3108_dir=args.m3108_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"residual_trace_plan_rows={summary['residual_trace_plan_row_count']}")
    print(f"residual_step_trace_rows={summary['residual_step_trace_row_count']}")
    print(f"residual_action_influence_rows={summary['residual_action_influence_row_count']}")
    print(f"residual_trace_failures={summary['residual_trace_failure_row_count']}")
    print(f"terminal_collision_count={summary['terminal_collision_count']}")
    print(f"terminal_offtrack_count={summary['terminal_offtrack_count']}")


if __name__ == "__main__":
    main()
