"""Materialize M3147 speed-envelope action-delta coverage diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.evaluate import outcome_bucket_from_info
import autodrift.engineering_controller_active_safety_driver_residual_failure_step_action_influence_trace_materialization_preflight as m3115
import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_full_fresh_measurement_preflight as m3144
import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight as m3142
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight as m3103
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3147-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-action-delta-coverage-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3148-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-action-delta-coverage-diagnostic-result-audit"
)
M3146_ID = (
    "m3146-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-plateau-synthesis"
)
M3144_ID = (
    "m3144-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-full-fresh-measurement-preflight"
)
M3142_ID = (
    "m3142-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3146_SYNTHESIS = Path(f"docs/{M3146_ID}.md")
DEFAULT_M3144_DIR = Path(
    "runs/m3144_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_full_fresh_measurement_preflight"
)
DEFAULT_M3142_DIR = Path(
    "runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_action_delta_coverage_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
DELTA_EPS = 1e-6
CLAIM_SCOPE = (
    "M3147 Active Safety Driver speed-envelope action-delta coverage diagnostic only; "
    "the seven M3144 residual collision/offtrack rows may be replayed through the M3142 "
    "obs72-to-action3 candidate while recording same-observation M3105/M3103 fallback "
    "versus candidate [steer throttle brake] deltas, overlay activation, action saturation, "
    "claim, gate, doc, and M3148 audit artifacts. No new repair implementation, validation, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, feasibility "
    "proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
)

CONTEXT_FIELDNAMES = [
    "trace_episode_id",
    "residual_failure_id",
    "m3144_measurement_episode_id",
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
    "m3105_same_row_comparison_id",
    "m3105_termination_reason",
    "m3105_outcome_bucket",
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
    "fallback_steer",
    "fallback_throttle",
    "fallback_brake",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "delta_steer",
    "delta_throttle",
    "delta_brake",
    "delta_l1",
    "delta_l2",
    "delta_max_abs",
    "fallback_action_abs_max",
    "candidate_action_abs_max",
    "fallback_action_saturated",
    "candidate_action_saturated",
    "candidate_throttle_physical",
    "candidate_brake_physical",
    "overlay_alpha",
    "overlay_active",
    "speed_mps_actor_visible",
    "obstacle_risk_actor_visible",
    "edge_risk_actor_visible",
    "stability_risk_actor_visible",
    "obstacle_avoid_direction_actor_visible",
    "obstacle_urgency_actor_visible",
    "edge_urgency_actor_visible",
    "road_center_error_actor_visible",
    "visible_obstacle_slot_count",
    "min_actor_edge_margin_m",
    "speed_mps_after_step",
    "beta_after_step",
    "high_sideslip_after_step",
    "lateral_error_m_after_step",
    "heading_error_rad_after_step",
    "progress_after_step",
    "min_clearance_margin_m_after_step",
    "max_off_track_overshoot_m_after_step",
    "hard_offtrack_failure_after_step",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
COVERAGE_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "source_m3144_termination_reason",
    "source_m3144_outcome_bucket",
    "target_failure_kind",
    "trace_step_count",
    "terminal_termination_reason",
    "terminal_outcome_bucket",
    "terminal_collision",
    "terminal_offtrack",
    "terminal_success",
    "terminal_speed_mps",
    "terminal_min_clearance_margin_m",
    "overlay_active_step_count",
    "overlay_active_fraction",
    "first_overlay_step_index",
    "first_overlay_lead_to_terminal_steps",
    "max_overlay_alpha",
    "mean_overlay_alpha",
    "final_10_mean_overlay_alpha",
    "max_delta_abs",
    "mean_delta_l1",
    "final_10_mean_delta_l1",
    "final_10_mean_delta_throttle",
    "final_10_mean_delta_brake",
    "candidate_saturation_fraction",
    "fallback_saturation_fraction",
    "throttle_drop_active_fraction",
    "brake_add_active_fraction",
    "steer_delta_active_fraction",
    "max_obstacle_risk_actor_visible",
    "max_edge_risk_actor_visible",
    "max_stability_risk_actor_visible",
    "min_clearance_margin_m_min",
    "coverage_diagnostic_label",
    "coverage_interpretation",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
OVERALL_FIELDNAMES = [
    "summary_id",
    "target_residual_row_count",
    "residual_action_delta_episode_row_count",
    "trace_step_row_count",
    "trace_failure_row_count",
    "collision_trace_count",
    "offtrack_trace_count",
    "speed_too_low_trace_count",
    "overlay_any_episode_count",
    "overlay_never_episode_count",
    "zero_delta_episode_count",
    "mean_overlay_active_fraction",
    "max_overlay_alpha",
    "max_delta_abs",
    "mean_candidate_saturation_fraction",
    "mean_fallback_saturation_fraction",
    "dominant_coverage_label",
    "diagnostic_boundary",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "error_type",
    "error_message",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3147",
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


def _max(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.max(finite)) if finite else ""


def _min(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.min(finite)) if finite else ""


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success", False))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "") or "") == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "") or "") == "speed_too_low"


def _target_failure_kind(row: Mapping[str, Any]) -> str:
    if _bool(row.get("collision", False)):
        return "collision"
    if _offtrack(row):
        return "offtrack"
    if _speed_too_low(row):
        return "speed_too_low"
    return "non_residual"


def _physical(action_value: float) -> float:
    return float(np.clip(0.5 * (action_value + 1.0), 0.0, 1.0))


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "action_delta_step_trace_rows": output_dir / "action_delta_step_trace_rows.csv",
        "action_delta_coverage_rows": output_dir / "action_delta_coverage_rows.csv",
        "residual_overlay_coverage_summary_rows": output_dir / "residual_overlay_coverage_summary_rows.csv",
        "action_delta_trace_failure_rows": output_dir / "action_delta_trace_failure_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3146_synthesis: Path, m3144_dir: Path, m3142_dir: Path, m3105_dir: Path, m3012_dir: Path) -> dict[str, Any]:
    paths = {
        "m3146_synthesis": m3146_synthesis,
        "m3144_summary": m3144_dir / "summary.json",
        "m3144_measurement_rows": m3144_dir / "measurement_episode_rows.csv",
        "m3144_same_row_comparison_rows": m3144_dir / "same_row_comparison_rows.csv",
        "m3144_gate_rows": m3144_dir / "gate_matrix.csv",
        "m3142_summary": m3142_dir / "summary.json",
        "m3142_policy_config": m3142_dir / "direct_action_policy_config.json",
        "m3142_gate_rows": m3142_dir / "gate_matrix.csv",
        "m3142_action_probe_rows": m3142_dir / "action_probe_rows.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3146_synthesis_text": paths["m3146_synthesis"].read_text(encoding="utf-8") if exists["m3146_synthesis"] else "",
        "m3144_summary": read_json(paths["m3144_summary"]) if exists["m3144_summary"] else {},
        "m3144_measurement_rows": read_csv_rows(paths["m3144_measurement_rows"]),
        "m3144_same_row_comparison_rows": read_csv_rows(paths["m3144_same_row_comparison_rows"]),
        "m3144_gate_rows": read_csv_rows(paths["m3144_gate_rows"]),
        "m3142_summary": read_json(paths["m3142_summary"]) if exists["m3142_summary"] else {},
        "m3142_policy_config": read_json(paths["m3142_policy_config"]) if exists["m3142_policy_config"] else {},
        "m3142_gate_rows": read_csv_rows(paths["m3142_gate_rows"]),
        "m3142_action_probe_rows": read_csv_rows(paths["m3142_action_probe_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def _context_fields(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {field: plan.get(field, "") for field in CONTEXT_FIELDNAMES}


def residual_action_delta_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build a trace plan from the seven residual M3144 rows and M3012 workload configs."""

    residual_rows = [
        row
        for row in source.get("m3144_measurement_rows", [])
        if _bool(row.get("collision", False)) or _offtrack(row) or _speed_too_low(row)
    ]
    workload_by_id = {
        str(row.get("executable_workload_id", "")): row for row in source.get("m3012_workload_rows", [])
    }
    m3105_compare_by_source = {
        str(row.get("source_measurement_episode_id", "")): row
        for row in source.get("m3144_same_row_comparison_rows", [])
        if str(row.get("baseline_id", "")) == "m3105"
    }
    plan: list[dict[str, Any]] = []
    for index, row in enumerate(residual_rows, start=1):
        workload = workload_by_id.get(str(row.get("executable_workload_id", "")), {})
        comparison = m3105_compare_by_source.get(str(row.get("source_measurement_episode_id", "")), {})
        failure_kind = _target_failure_kind(row)
        context = {
            "trace_episode_id": f"m3147-action-delta-trace-episode-{index:04d}",
            "residual_failure_id": f"m3147-residual-failure-{index:04d}",
            "m3144_measurement_episode_id": row.get("runtime_smoke_episode_id", ""),
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
            "m3105_same_row_comparison_id": comparison.get("comparison_id", ""),
            "m3105_termination_reason": comparison.get("baseline_termination_reason", ""),
            "m3105_outcome_bucket": comparison.get("baseline_outcome_bucket", ""),
        }
        context.update(
            {
                "config_path": workload.get("config_path", ""),
                "source_m3144_termination_reason": row.get("termination_reason", ""),
                "source_m3144_outcome_bucket": row.get("outcome_bucket", ""),
                "target_failure_kind": failure_kind,
                "m3144_collision": _bool(row.get("collision", False)),
                "m3144_offtrack": _offtrack(row),
                "m3144_speed_too_low": _speed_too_low(row),
                "m3144_success": _success(row),
                "m3105_exact_seed_match": _bool(comparison.get("exact_seed_match_m3105", False)),
                "status_pass": bool(
                    context["source_measurement_episode_id"]
                    and failure_kind in {"collision", "offtrack", "speed_too_low"}
                    and bool(workload.get("config_path", ""))
                    and bool(comparison)
                    and _bool(comparison.get("exact_seed_match_m3105", False))
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        plan.append(context)
    return plan


def action_delta_from_observation(observation: np.ndarray) -> dict[str, Any]:
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")
    fallback = np.asarray(
        m3103.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m3103.V4_POLICY_CONFIG),
        dtype=np.float32,
    )
    candidate = np.asarray(m3142.residual_trajectory_timing_speed_envelope_action(obs, m3142.POLICY_CONFIG), dtype=np.float32)
    if fallback.shape != (ACTION_DIM,) or candidate.shape != (ACTION_DIM,):
        raise ValueError("fallback and candidate actions must both be action3")
    delta = candidate - fallback
    features = m3142.speed_envelope_features(obs, m3142.POLICY_CONFIG)
    actor_features = m3115.actor_visible_diagnostic_features(obs)
    return {
        "fallback_action": fallback,
        "candidate_action": candidate,
        "delta": delta,
        "features": features,
        "actor_features": actor_features,
    }


def trace_episode(*, env: Any, plan: Mapping[str, Any], seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obs, info = env.reset(seed=seed)
    del info
    step_rows: list[dict[str, Any]] = []
    rewards: list[float] = []
    terminated = False
    truncated = False
    while not (terminated or truncated):
        delta_payload = action_delta_from_observation(obs)
        fallback = np.asarray(delta_payload["fallback_action"], dtype=np.float32)
        candidate = np.asarray(delta_payload["candidate_action"], dtype=np.float32)
        delta = np.asarray(delta_payload["delta"], dtype=np.float32)
        features = dict(delta_payload["features"])
        actor_features = dict(delta_payload["actor_features"])
        action = np.clip(candidate, -1.0, 1.0).astype(np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        step_index = int(info.get("step", len(step_rows) + 1))
        collision = _bool(info.get("collision", False))
        offtrack = str(info.get("termination_reason", "") or "") == "off_track" or _bool(
            info.get("hard_offtrack_failure", False)
        )
        outcome_bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
        row = {
            **_context_fields(plan),
            "trace_step_id": f"{plan.get('trace_episode_id', 'm3147-action-delta')}-step-{step_index:04d}",
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
            "fallback_steer": float(fallback[0]),
            "fallback_throttle": float(fallback[1]),
            "fallback_brake": float(fallback[2]),
            "candidate_steer": float(action[0]),
            "candidate_throttle": float(action[1]),
            "candidate_brake": float(action[2]),
            "delta_steer": float(delta[0]),
            "delta_throttle": float(delta[1]),
            "delta_brake": float(delta[2]),
            "delta_l1": float(np.sum(np.abs(delta))),
            "delta_l2": float(np.linalg.norm(delta)),
            "delta_max_abs": float(np.max(np.abs(delta))),
            "fallback_action_abs_max": float(np.max(np.abs(fallback))),
            "candidate_action_abs_max": float(np.max(np.abs(action))),
            "fallback_action_saturated": bool(np.max(np.abs(fallback)) >= 0.999),
            "candidate_action_saturated": bool(np.max(np.abs(action)) >= 0.999),
            "candidate_throttle_physical": _physical(float(action[1])),
            "candidate_brake_physical": _physical(float(action[2])),
            "overlay_alpha": float(features["overlay_alpha"]),
            "overlay_active": bool(float(features["overlay_alpha"]) > DELTA_EPS or float(np.max(np.abs(delta))) > DELTA_EPS),
            "speed_mps_actor_visible": float(features["speed_mps"]),
            "obstacle_risk_actor_visible": float(features["obstacle_risk"]),
            "edge_risk_actor_visible": float(features["edge_risk"]),
            "stability_risk_actor_visible": float(features["stability_risk"]),
            "obstacle_avoid_direction_actor_visible": float(features["obstacle_avoid_direction"]),
            "obstacle_urgency_actor_visible": actor_features["obstacle_urgency_actor_visible"],
            "edge_urgency_actor_visible": actor_features["edge_urgency_actor_visible"],
            "road_center_error_actor_visible": actor_features["road_center_error_actor_visible"],
            "visible_obstacle_slot_count": actor_features["visible_obstacle_slot_count"],
            "min_actor_edge_margin_m": actor_features["min_actor_edge_margin_m"],
            "speed_mps_after_step": _float(info.get("speed")),
            "beta_after_step": _float(info.get("beta")),
            "high_sideslip_after_step": abs(_float(info.get("beta"))) > 0.35,
            "lateral_error_m_after_step": _float(info.get("lateral_error")),
            "heading_error_rad_after_step": _float(info.get("heading_error")),
            "progress_after_step": _float(info.get("progress")),
            "min_clearance_margin_m_after_step": _float(info.get("min_clearance_margin")),
            "max_off_track_overshoot_m_after_step": _float(info.get("max_off_track_overshoot_env")),
            "hard_offtrack_failure_after_step": _bool(info.get("hard_offtrack_failure", False)),
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        step_rows.append(row)
    coverage = coverage_row_from_trace(plan=plan, step_rows=step_rows)
    coverage["return"] = float(np.sum(rewards)) if rewards else 0.0
    return step_rows, coverage


def _final_window(rows: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    return rows[-count:] if len(rows) > count else rows


def _fraction(rows: list[dict[str, Any]], predicate: Any) -> float | str:
    if not rows:
        return ""
    return float(np.mean([1.0 if predicate(row) else 0.0 for row in rows]))


def _coverage_label(rows: list[dict[str, Any]]) -> tuple[str, str]:
    terminal = rows[-1] if rows else {}
    reason = str(terminal.get("termination_reason_after_step", "") or "")
    active_rows = [row for row in rows if _bool(row.get("overlay_active", False))]
    max_delta = _float(_max(_float(row.get("delta_max_abs")) for row in rows), 0.0)
    max_overlay = _float(_max(_float(row.get("overlay_alpha")) for row in rows), 0.0)
    first_overlay = int(active_rows[0].get("step_index", 0)) if active_rows else 0
    terminal_step = int(terminal.get("step_index", 0) or 0)
    final_rows = _final_window(rows)
    final_brake_delta = _float(_mean(_float(row.get("delta_brake")) for row in final_rows), 0.0)
    final_throttle_delta = _float(_mean(_float(row.get("delta_throttle")) for row in final_rows), 0.0)
    candidate_saturation = _float(_fraction(rows, lambda row: _bool(row.get("candidate_action_saturated", False))), 0.0)

    if not active_rows:
        return (
            "overlay_never_active_on_residual_row",
            "candidate equals fallback for the whole residual trace or overlay alpha never activates",
        )
    if terminal_step and first_overlay >= max(1, terminal_step - 5):
        return (
            "overlay_active_only_near_terminal_failure",
            "first candidate-fallback delta appears only in the last five executed steps",
        )
    if max_overlay > 0.0 and max_delta < 0.03:
        return (
            "overlay_active_but_action_delta_tiny",
            "overlay alpha becomes positive but same-observation action delta remains below diagnostic threshold",
        )
    if candidate_saturation > 0.30:
        return (
            "candidate_action_saturation_may_limit_delta_effect",
            "candidate action is frequently at normalized bounds in this residual trace",
        )
    if reason == "obstacle_collision" and final_brake_delta < 0.05 and final_throttle_delta > -0.05:
        return (
            "collision_terminal_window_delta_low",
            "terminal collision occurs while final-window brake add and throttle drop remain small",
        )
    return (
        "delta_present_outcome_unresolved",
        "candidate-fallback action delta is present but residual hard-safety outcome remains unresolved",
    )


def coverage_row_from_trace(*, plan: Mapping[str, Any], step_rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal = step_rows[-1] if step_rows else {}
    final_rows = _final_window(step_rows)
    active_rows = [row for row in step_rows if _bool(row.get("overlay_active", False))]
    first_overlay_step = int(active_rows[0].get("step_index", 0)) if active_rows else ""
    terminal_step = int(terminal.get("step_index", 0) or 0)
    label, interpretation = _coverage_label(step_rows)
    return {
        **_context_fields(plan),
        "source_m3144_termination_reason": plan.get("source_m3144_termination_reason", ""),
        "source_m3144_outcome_bucket": plan.get("source_m3144_outcome_bucket", ""),
        "target_failure_kind": plan.get("target_failure_kind", ""),
        "trace_step_count": len(step_rows),
        "terminal_termination_reason": terminal.get("termination_reason_after_step", ""),
        "terminal_outcome_bucket": terminal.get("outcome_bucket_after_step", ""),
        "terminal_collision": _bool(terminal.get("collision_after_step", False)),
        "terminal_offtrack": _bool(terminal.get("offtrack_after_step", False)),
        "terminal_success": _bool(terminal.get("success_after_step", False)),
        "terminal_speed_mps": terminal.get("speed_mps_after_step", ""),
        "terminal_min_clearance_margin_m": terminal.get("min_clearance_margin_m_after_step", ""),
        "overlay_active_step_count": len(active_rows),
        "overlay_active_fraction": _fraction(step_rows, lambda row: _bool(row.get("overlay_active", False))),
        "first_overlay_step_index": first_overlay_step,
        "first_overlay_lead_to_terminal_steps": terminal_step - first_overlay_step if first_overlay_step != "" else "",
        "max_overlay_alpha": _max(_float(row.get("overlay_alpha")) for row in step_rows),
        "mean_overlay_alpha": _mean(_float(row.get("overlay_alpha")) for row in step_rows),
        "final_10_mean_overlay_alpha": _mean(_float(row.get("overlay_alpha")) for row in final_rows),
        "max_delta_abs": _max(_float(row.get("delta_max_abs")) for row in step_rows),
        "mean_delta_l1": _mean(_float(row.get("delta_l1")) for row in step_rows),
        "final_10_mean_delta_l1": _mean(_float(row.get("delta_l1")) for row in final_rows),
        "final_10_mean_delta_throttle": _mean(_float(row.get("delta_throttle")) for row in final_rows),
        "final_10_mean_delta_brake": _mean(_float(row.get("delta_brake")) for row in final_rows),
        "candidate_saturation_fraction": _fraction(step_rows, lambda row: _bool(row.get("candidate_action_saturated", False))),
        "fallback_saturation_fraction": _fraction(step_rows, lambda row: _bool(row.get("fallback_action_saturated", False))),
        "throttle_drop_active_fraction": _fraction(step_rows, lambda row: _float(row.get("delta_throttle"), 0.0) < -DELTA_EPS),
        "brake_add_active_fraction": _fraction(step_rows, lambda row: _float(row.get("delta_brake"), 0.0) > DELTA_EPS),
        "steer_delta_active_fraction": _fraction(step_rows, lambda row: abs(_float(row.get("delta_steer"), 0.0)) > DELTA_EPS),
        "max_obstacle_risk_actor_visible": _max(_float(row.get("obstacle_risk_actor_visible")) for row in step_rows),
        "max_edge_risk_actor_visible": _max(_float(row.get("edge_risk_actor_visible")) for row in step_rows),
        "max_stability_risk_actor_visible": _max(_float(row.get("stability_risk_actor_visible")) for row in step_rows),
        "min_clearance_margin_m_min": _min(_float(row.get("min_clearance_margin_m_after_step")) for row in step_rows),
        "coverage_diagnostic_label": label,
        "coverage_interpretation": interpretation,
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "repair_success_claim_made": False,
        "validation_run": False,
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def trace_action_delta_plan(
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
    coverage_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3147 residual action-delta plan row failed guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3088.m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            profile_config = profile_cache[cache_key]
            env_config = m3088.env_config_for_executable_profile(
                executable_spec=executable_spec,
                profile_config=profile_config,
            )
            env = m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                step_rows, coverage = trace_episode(env=env, plan=plan, seed=int(plan["eval_seed"]))
            finally:
                env.close()
            all_steps.extend(step_rows)
            coverage_rows.append(coverage)
        except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
            failure = _context_fields(plan)
            failure.update(
                {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "runtime_base_policy_required": False,
                    "hidden_oracle_actor_input_required": False,
                    "ttc_actor_input_required": False,
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
                "scheduled_residual_action_delta_row_count": len(plan_rows),
                "action_delta_step_trace_row_count": len(all_steps),
                "action_delta_coverage_row_count": len(coverage_rows),
                "action_delta_trace_failure_row_count": len(failures),
                "recorded_episode_count": len(coverage_rows) + len(failures),
                "latest_trace_episode_id": plan.get("trace_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"steps": all_steps, "coverage": coverage_rows, "failures": failures}


def overall_coverage_rows(coverage_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]], step_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = Counter(str(row.get("coverage_diagnostic_label", "")) for row in coverage_rows)
    dominant = labels.most_common(1)[0][0] if labels else ""
    return [
        {
            "summary_id": "m3147-residual-overlay-coverage-summary-0001",
            "target_residual_row_count": EXPECTED_RESIDUAL_ROWS,
            "residual_action_delta_episode_row_count": len(coverage_rows),
            "trace_step_row_count": len(step_rows),
            "trace_failure_row_count": len(failure_rows),
            "collision_trace_count": sum(1 for row in coverage_rows if _bool(row.get("terminal_collision", False))),
            "offtrack_trace_count": sum(1 for row in coverage_rows if _bool(row.get("terminal_offtrack", False)) and not _bool(row.get("terminal_collision", False))),
            "speed_too_low_trace_count": sum(1 for row in coverage_rows if str(row.get("terminal_termination_reason", "")) == "speed_too_low"),
            "overlay_any_episode_count": sum(1 for row in coverage_rows if int(_float(row.get("overlay_active_step_count"), 0.0)) > 0),
            "overlay_never_episode_count": sum(1 for row in coverage_rows if int(_float(row.get("overlay_active_step_count"), 0.0)) == 0),
            "zero_delta_episode_count": sum(1 for row in coverage_rows if _float(row.get("max_delta_abs"), 0.0) <= DELTA_EPS),
            "mean_overlay_active_fraction": _mean(_float(row.get("overlay_active_fraction")) for row in coverage_rows),
            "max_overlay_alpha": _max(_float(row.get("max_overlay_alpha")) for row in coverage_rows),
            "max_delta_abs": _max(_float(row.get("max_delta_abs")) for row in coverage_rows),
            "mean_candidate_saturation_fraction": _mean(_float(row.get("candidate_saturation_fraction")) for row in coverage_rows),
            "mean_fallback_saturation_fraction": _mean(_float(row.get("fallback_saturation_fraction")) for row in coverage_rows),
            "dominant_coverage_label": dominant,
            "diagnostic_boundary": "diagnostic action-delta coverage only; no repair-success or validation claim",
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31480,
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
        "hypothesis": "A bounded result audit can accept or reject the M3147 speed-envelope action-delta coverage diagnostic artifacts before any new repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "action_delta_step_trace_rows.csv"),
                str(output_dir / "action_delta_coverage_rows.csv"),
                str(output_dir / "residual_overlay_coverage_summary_rows.csv"),
                str(output_dir / "action_delta_trace_failure_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3147 residual action-delta coverage diagnostics"],
            "derived_from": [MILESTONE_ID, M3146_ID, M3144_ID, M3142_ID, M3105_ID],
            "blocked_by": [
                "M3147 diagnostics require audit before selecting a repair route",
                "action-delta coverage labels are not validation, repair-success, or performance evidence",
            ],
            "supersedes": ["direct interpretation of M3147 action-delta diagnostics without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3148 must audit M3147 row counts action-delta coverage gates actor contract and claim boundaries",
            "M3148 must preserve obs72/action3 direct [steer throttle brake] contract and runtime_base_policy_required false",
            "M3148 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3148 must choose exactly one next route: no-go, synthesis, artifact repair, or a bounded repair hypothesis",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not tune gains run full-fresh validation rank promote or mutate checkpoints",
            "do not convert M3147 action-delta labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic",
            "evidence_axis": "speed_envelope_action_delta_coverage_result_audit",
            "evidence_increment": "audits residual-row candidate-vs-fallback action-delta coverage and saturation diagnostics",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3147 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize before any repair if coverage labels are mixed or inconclusive",
            ],
            "fallback_plan": [
                "route to M3147 artifact repair if diagnostics are incomplete or contract-unsafe",
                "route to no-go if action deltas are absent or too late on residual rows",
                "route to bounded repair synthesis only if diagnostics identify an actor-visible coverage gap",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3147 completes residual action-delta coverage diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3147 action-delta coverage diagnostic artifacts",
            "admission_evidence": ["M3147 summary action-delta traces coverage rows gate matrix and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3148 status queue scoreboard research log and review",
                "one follow-up manifest only if M3148 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3148 accepts or rejects M3147 as complete and claim-safe",
                "M3148 selects no-go synthesis artifact repair or bounded repair route explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3148 audits engineering action-delta diagnostics and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3148; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3147 residual action-delta diagnostic artifacts only.",
            "negative_result_policy": "Preserve diagnostic evidence and route to engineering synthesis or no-go rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3147 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits per-step candidate-vs-fallback action deltas rather than another blind repair overlay",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3148 audits engineering hard-safety action-delta evidence",
            "must_synthesize_if": [
                "M3148 cannot accept M3147 as complete and claim-safe",
                "M3148 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3148 cannot select no-go synthesis artifact repair or bounded repair route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3148 audits M3147 row counts gates actor contract action-delta coverage and claim boundaries",
            "M3148 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3148 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3148 hides M3147 missing rows or missing artifacts",
            "M3148 treats M3147 diagnostics as validation repair-success or performance verdict",
            "M3148 changes actor input or action contract",
            "M3148 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3148 audits M3147 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("action_delta_step_trace_rows", "diagnostic_trace", True, "action_delta_step_trace_rows.csv"),
        ("action_delta_coverage_rows", "diagnostic_trace", True, "action_delta_coverage_rows.csv"),
        ("residual_overlay_coverage_summary_rows", "diagnostic_summary", True, "residual_overlay_coverage_summary_rows.csv"),
        ("trace_failure_rows", "diagnostic_accounting", True, "action_delta_trace_failure_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3148 audit manifest"),
    ]
    blocked = [
        ("repair_implementation", "repair", "future audited repair synthesis route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
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
            "claim_id": f"m3147-{claim_id}",
            "claim_family": family,
            "allowed_in_m3147": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3147-{claim_id}",
            "claim_family": family,
            "allowed_in_m3147": False,
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
        "gate_id": f"m3147-{gate_id}",
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
            "ttc_actor_input_required",
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
    coverage_rows: list[dict[str, Any]],
    overall_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3146_synthesis_text", ""))
    source_ids = {str(row.get("source_measurement_episode_id", "")) for row in plan_rows}
    step_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in step_rows}
    coverage_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in coverage_rows}
    step_counts = Counter(str(row.get("source_measurement_episode_id", "")) for row in step_rows)
    residual_counts = Counter(str(row.get("target_failure_kind", "")) for row in plan_rows)
    comparison_ids = {str(row.get("m3105_same_row_comparison_id", "")) for row in plan_rows}
    sample = action_delta_from_observation(_sample_overlay_observation())
    combined = step_rows + coverage_rows + overall_rows + failure_rows
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3146_pivots_to_m3147", "lineage", "pivot_to_m3147_speed_envelope_action_delta_coverage_diagnostic" in synthesis_text, "pivot marker", "present", "lineage_invalid"),
        gate("m3144_status_pass", "lineage", _bool(source["m3144_summary"].get("status_pass", False)), source["m3144_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3144_gate_matrix_pass", "lineage", _bool(source["m3144_summary"].get("gate_matrix_pass", False)), source["m3144_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3142_status_pass", "lineage", _bool(source["m3142_summary"].get("status_pass", False)), source["m3142_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3142_gate_matrix_pass", "lineage", _bool(source["m3142_summary"].get("gate_matrix_pass", False)), source["m3142_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3142_policy_config_id", "lineage", str(source["m3142_policy_config"].get("policy_id", "")) == m3142.POLICY_ID, source["m3142_policy_config"].get("policy_id"), m3142.POLICY_ID, "lineage_invalid"),
        gate("m3144_same_row_comparison_m3105_present", "comparison", len(comparison_ids) == EXPECTED_RESIDUAL_ROWS and "" not in comparison_ids, sorted(comparison_ids), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("policy_observation_shape", "contract", int(m3142.POLICY_CONFIG.get("observation_shape", -1)) == P0_OBSERVATION_DIM, m3142.POLICY_CONFIG.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", int(m3142.POLICY_CONFIG.get("action_shape", -1)) == ACTION_DIM, m3142.POLICY_CONFIG.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_output_semantics", "contract", str(m3142.POLICY_CONFIG.get("output_semantics", "")) == m3142.OUTPUT_SEMANTICS, m3142.POLICY_CONFIG.get("output_semantics"), m3142.OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(m3142.POLICY_CONFIG.get("runtime_base_policy_required", True)), m3142.POLICY_CONFIG.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("sample_fallback_action_shape", "contract", tuple(sample["fallback_action"].shape) == (ACTION_DIM,), tuple(sample["fallback_action"].shape), (ACTION_DIM,), "contract_violation"),
        gate("sample_candidate_action_shape", "contract", tuple(sample["candidate_action"].shape) == (ACTION_DIM,), tuple(sample["candidate_action"].shape), (ACTION_DIM,), "contract_violation"),
        gate("sample_actions_finite_bounded", "contract", bool(np.all(np.isfinite(sample["fallback_action"])) and np.all(np.isfinite(sample["candidate_action"])) and np.max(np.abs(sample["fallback_action"])) <= 1.0 and np.max(np.abs(sample["candidate_action"])) <= 1.0), "finite bounded", "finite bounded", "contract_violation"),
        gate("sample_overlay_delta_present", "contract", bool(float(sample["features"]["overlay_alpha"]) > 0.0 and float(np.max(np.abs(sample["delta"]))) > 0.0), "overlay delta", "present", "metric_artifact"),
        gate("residual_plan_row_count", "residual", len(plan_rows) == EXPECTED_RESIDUAL_ROWS, len(plan_rows), EXPECTED_RESIDUAL_ROWS, "scenario_sampling_failure"),
        gate("residual_collision_count", "residual", residual_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(residual_counts.items())), EXPECTED_COLLISION_ROWS, "scenario_sampling_failure"),
        gate("residual_offtrack_count", "residual", residual_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(residual_counts.items())), EXPECTED_OFFTRACK_ROWS, "scenario_sampling_failure"),
        gate("residual_speed_too_low_count", "residual", residual_counts.get("speed_too_low", 0) == EXPECTED_SPEED_TOO_LOW_ROWS, dict(sorted(residual_counts.items())), EXPECTED_SPEED_TOO_LOW_ROWS, "scenario_sampling_failure"),
        gate("plan_rows_pass", "residual", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("trace_execution_accounted", "execution", len(coverage_rows) + len(failure_rows) == len(plan_rows), len(coverage_rows) + len(failure_rows), len(plan_rows), "metric_artifact"),
        gate("trace_failure_rows", "execution", len(failure_rows) == 0, len(failure_rows), 0, "metric_artifact"),
        gate("step_trace_rows_nonempty", "trace", bool(step_rows), len(step_rows), "nonzero", "metric_artifact"),
        gate("step_trace_identity_complete", "trace", step_source_ids == source_ids and all(step_counts[source_id] > 0 for source_id in source_ids), dict(sorted(step_counts.items())), "all residual rows have steps", "metric_artifact"),
        gate("coverage_rows", "trace", len(coverage_rows) == EXPECTED_RESIDUAL_ROWS, len(coverage_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("coverage_identity_complete", "trace", coverage_source_ids == source_ids, sorted(coverage_source_ids), sorted(source_ids), "metric_artifact"),
        gate("overall_coverage_summary_rows", "trace", len(overall_rows) == 1, len(overall_rows), 1, "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", _all_forbidden_flags_clear(combined), "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def _sample_overlay_observation() -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.9
    obs[44] = 1.0
    obs[45] = 0.20
    obs[46] = 0.02
    obs[49] = 0.30
    return obs


def render_doc(summary: Mapping[str, Any]) -> str:
    diagnosis_counts = summary.get("coverage_diagnostic_label_counts", {})
    diagnosis_lines = [f"- {label}: {count}" for label, count in sorted(diagnosis_counts.items())]
    return "\n".join(
        [
            "# M3147 Speed-Envelope Action-Delta Coverage Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- residual action-delta plan rows: {summary['residual_action_delta_plan_row_count']}/{summary['target_residual_row_count']}",
            f"- action-delta step trace rows: {summary['action_delta_step_trace_row_count']}",
            f"- action-delta coverage rows: {summary['action_delta_coverage_row_count']}",
            f"- action-delta trace failure rows: {summary['action_delta_trace_failure_row_count']}",
            f"- overlay-any episode count: {summary['overlay_any_episode_count']}",
            f"- overlay-never episode count: {summary['overlay_never_episode_count']}",
            f"- zero-delta episode count: {summary['zero_delta_episode_count']}",
            f"- max overlay alpha: {summary['max_overlay_alpha']}",
            f"- max delta abs: {summary['max_delta_abs']}",
            f"- mean overlay active fraction: {summary['mean_overlay_active_fraction']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Diagnostic Labels",
            "",
            *(diagnosis_lines or ["- none: 0"]),
            "",
            "## Interpretation",
            "",
            "M3147 replays only the seven M3144 residual collision/offtrack rows through the M3142 direct-action candidate and records same-observation deltas against the M3105/M3103 fallback action. These artifacts diagnose overlay coverage, action saturation, and candidate-vs-fallback delta timing only. They are not a new repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.",
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


def run_action_delta_coverage_diagnostic_preflight(
    *,
    m3146_synthesis: Path,
    m3144_dir: Path,
    m3142_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3146_synthesis=m3146_synthesis,
        m3144_dir=m3144_dir,
        m3142_dir=m3142_dir,
        m3105_dir=m3105_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = residual_action_delta_plan(source)
    trace = trace_action_delta_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    step_rows = trace["steps"]
    coverage_rows = trace["coverage"]
    failure_rows = trace["failures"]
    overall_rows = overall_coverage_rows(coverage_rows, failure_rows, step_rows)

    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["action_delta_step_trace_rows"], step_rows, STEP_FIELDNAMES),
        (paths["action_delta_coverage_rows"], coverage_rows, COVERAGE_FIELDNAMES),
        (paths["residual_overlay_coverage_summary_rows"], overall_rows, OVERALL_FIELDNAMES),
        (paths["action_delta_trace_failure_rows"], failure_rows, FAILURE_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        step_rows=step_rows,
        coverage_rows=coverage_rows,
        overall_rows=overall_rows,
        failure_rows=failure_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    terminal_counts = Counter(str(row.get("terminal_termination_reason", "")) for row in coverage_rows)
    label_counts = Counter(str(row.get("coverage_diagnostic_label", "")) for row in coverage_rows)
    overall = overall_rows[0] if overall_rows else {}

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": m3142.POLICY_ID,
        "fallback_policy_id": m3103.POLICY_ID,
        "target_residual_row_count": EXPECTED_RESIDUAL_ROWS,
        "residual_action_delta_plan_row_count": len(plan_rows),
        "action_delta_step_trace_row_count": len(step_rows),
        "action_delta_coverage_row_count": len(coverage_rows),
        "action_delta_trace_failure_row_count": len(failure_rows),
        "coverage_summary_row_count": len(overall_rows),
        "terminal_collision_count": sum(1 for row in coverage_rows if _bool(row.get("terminal_collision", False))),
        "terminal_offtrack_count": sum(1 for row in coverage_rows if _bool(row.get("terminal_offtrack", False)) and not _bool(row.get("terminal_collision", False))),
        "terminal_success_count": sum(1 for row in coverage_rows if _bool(row.get("terminal_success", False))),
        "terminal_termination_counts": dict(sorted(terminal_counts.items())),
        "coverage_diagnostic_label_counts": dict(sorted(label_counts.items())),
        "overlay_any_episode_count": overall.get("overlay_any_episode_count", 0),
        "overlay_never_episode_count": overall.get("overlay_never_episode_count", 0),
        "zero_delta_episode_count": overall.get("zero_delta_episode_count", 0),
        "mean_overlay_active_fraction": overall.get("mean_overlay_active_fraction", ""),
        "max_overlay_alpha": overall.get("max_overlay_alpha", ""),
        "max_delta_abs": overall.get("max_delta_abs", ""),
        "mean_candidate_saturation_fraction": overall.get("mean_candidate_saturation_fraction", ""),
        "mean_fallback_saturation_fraction": overall.get("mean_fallback_saturation_fraction", ""),
        "dominant_coverage_label": overall.get("dominant_coverage_label", ""),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3144_status_pass": _bool(source["m3144_summary"].get("status_pass", False)),
        "m3144_gate_matrix_pass": _bool(source["m3144_summary"].get("gate_matrix_pass", False)),
        "m3142_status_pass": _bool(source["m3142_summary"].get("status_pass", False)),
        "m3142_gate_matrix_pass": _bool(source["m3142_summary"].get("gate_matrix_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "candidate_output_semantics": m3142.OUTPUT_SEMANTICS,
        "candidate_output_components": list(m3142.ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "candidate = residual_trajectory_timing_speed_envelope_action(obs72); fallback = M3105/M3103; diagnostic_delta = candidate - fallback",
        "environment_reset_run": bool(coverage_rows),
        "environment_step_run": bool(step_rows),
        "policy_action_run": bool(step_rows),
        "policy_rollout_run": bool(coverage_rows),
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
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_route_to_m3148_result_audit",
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
            "scheduled_residual_action_delta_row_count": len(plan_rows),
            "action_delta_step_trace_row_count": len(step_rows),
            "action_delta_coverage_row_count": len(coverage_rows),
            "action_delta_trace_failure_row_count": len(failure_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3146-synthesis", type=Path, default=DEFAULT_M3146_SYNTHESIS)
    parser.add_argument("--m3144-dir", type=Path, default=DEFAULT_M3144_DIR)
    parser.add_argument("--m3142-dir", type=Path, default=DEFAULT_M3142_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_action_delta_coverage_diagnostic_preflight(
        m3146_synthesis=args.m3146_synthesis,
        m3144_dir=args.m3144_dir,
        m3142_dir=args.m3142_dir,
        m3105_dir=args.m3105_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"residual_action_delta_plan_rows={summary['residual_action_delta_plan_row_count']}")
    print(f"action_delta_step_trace_rows={summary['action_delta_step_trace_row_count']}")
    print(f"action_delta_coverage_rows={summary['action_delta_coverage_row_count']}")
    print(f"action_delta_trace_failures={summary['action_delta_trace_failure_row_count']}")
    print(f"overlay_any_episode_count={summary['overlay_any_episode_count']}")
    print(f"overlay_never_episode_count={summary['overlay_never_episode_count']}")
    print(f"zero_delta_episode_count={summary['zero_delta_episode_count']}")
    print(f"max_overlay_alpha={summary['max_overlay_alpha']}")
    print(f"max_delta_abs={summary['max_delta_abs']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
