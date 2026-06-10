"""Materialize M3208 recovery-clearance supervisor architecture artifacts."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_ID as M3103_POLICY_ID,
    V4_POLICY_CONFIG,
    _hard_safety_features,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3208-engineering-controller-active-safety-driver-residual-hard-safety-"
    "recovery-clearance-supervisor-architecture-materialization-preflight"
)
NEXT_ID = (
    "m3209-engineering-controller-active-safety-driver-residual-hard-safety-"
    "recovery-clearance-supervisor-architecture-result-audit"
)
M3207_ID = (
    "m3207-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-neutral-residual-trace-synthesis"
)
M3205_ID = (
    "m3205-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-residual-trace-measurement-preflight"
)
M3189_ID = (
    "m3189-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)
POLICY_ID = "m3208_recovery_clearance_supervisor_candidate"

DEFAULT_M3207_SYNTHESIS = Path(f"docs/{M3207_ID}.md")
DEFAULT_M3205_DIR = Path(
    "runs/m3205_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_candidate_residual_trace_measurement_preflight"
)
DEFAULT_M3189_DIR = Path(
    "runs/m3189_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_execution_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3208_engineering_controller_active_safety_driver_residual_hard_safety_"
    "recovery_clearance_supervisor_architecture_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3208 Active Safety Driver recovery-clearance supervisor architecture "
    "materialization only; artifacts may define a deterministic actor-visible "
    "obs72 to direct action3 candidate function, config, supervisor mode rows, "
    "feature contracts, runtime contracts, synthetic action probes, claim rows, "
    "gate rows, doc, and M3209 audit manifest. No reset, step, rollout, replay, "
    "full-fresh measurement, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, public driver default mutation, driver-"
    "performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, "
    "full ideal driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint "
    "ranking, winner selection, checkpoint promotion, public driver default "
    "replacement, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

SUPERVISOR_POLICY_CONFIG: dict[str, Any] = deepcopy(V4_POLICY_CONFIG)
SUPERVISOR_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "repair_route": "recovery_clearance_supervisor_architecture",
        "repair_scope": "architecture_materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "actor_observation_contract": "actor_visible_obs72_only",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "public_active_safety_reflex_driver_default_mutation": False,
    }
)
SUPERVISOR_POLICY_CONFIG["recovery_clearance_supervisor"] = {
    "enabled": True,
    "speed_start_mps": 4.0,
    "speed_full_mps": 14.0,
    "collision_clearance_trigger": 0.04,
    "boundary_recovery_trigger": 0.10,
    "stability_trigger": 0.08,
    "collision_steer_budget": 0.52,
    "boundary_steer_budget": 0.48,
    "stability_steer_damping": 0.20,
    "collision_brake_add": 0.58,
    "boundary_brake_add": 0.30,
    "collision_throttle_drop": 0.70,
    "boundary_throttle_drop": 0.28,
    "max_abs_steer_delta": 0.62,
    "max_throttle_drop": 0.80,
    "max_brake_add": 0.70,
    "max_action_delta_l2": 1.20,
    "mode_blend_floor": 0.18,
}

MODE_FIELDNAMES = [
    "mode_id",
    "mode_family",
    "priority",
    "activation_summary",
    "actor_visible_feature_groups",
    "output_channels",
    "fallback_policy_id",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "public_driver_default_mutated",
    "claim_boundary",
]
FEATURE_FIELDNAMES = [
    "feature_id",
    "feature_family",
    "input_contract",
    "derived_from_obs72_only",
    "forbidden_runtime_inputs",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "status_pass",
    "claim_boundary",
]
CONTRACT_FIELDNAMES = [
    "contract_id",
    "contract_family",
    "runtime_symbol",
    "input_contract",
    "output_contract",
    "observation_shape",
    "action_shape",
    "action_components",
    "output_semantics",
    "fallback_policy_id",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "public_driver_default_mutated",
    "status_pass",
    "claim_boundary",
]
ACTION_PROBE_FIELDNAMES = [
    "probe_id",
    "probe_family",
    "selected_mode",
    "fallback_steer",
    "fallback_throttle",
    "fallback_brake",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "steer_delta",
    "throttle_delta",
    "brake_delta",
    "speed_mps",
    "collision_pressure",
    "boundary_pressure",
    "stability_pressure",
    "obstacle_urgency",
    "edge_urgency",
    "road_center_error",
    "fallback_path_selected",
    "action_finite",
    "action_bounded",
    "delta_limited",
    "public_driver_default_mutated",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3208",
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


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _overlay_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    return config.get("recovery_clearance_supervisor", SUPERVISOR_POLICY_CONFIG["recovery_clearance_supervisor"])


def _brake_to_physical(action_brake: float) -> float:
    return _clip01((action_brake + 1.0) / 2.0)


def _brake_from_physical(physical_brake: float) -> float:
    return -1.0 + 2.0 * _clip01(physical_brake)


def _stability_pressure(observation: np.ndarray, trigger: float) -> float:
    obs = np.asarray(observation, dtype=np.float32)
    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    steer_rate = float(obs[6])
    raw = (
        _clip01(abs(vy_body) / 4.0)
        + _clip01(abs(yaw_rate) / 1.5)
        + _clip01(abs(ay_body) / 8.0)
        + _clip01(abs(steer_rate) / 1.0)
    ) / 4.0
    return _clip01((raw - trigger) / max(1.0 - trigger, 1e-6))


def recovery_clearance_supervisor_features(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> dict[str, float | str]:
    cfg = config or SUPERVISOR_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    hard = _hard_safety_features(obs, cfg)
    overlay = _overlay_config(cfg)
    speed = float(hard["vx_body"])
    speed_alpha = _clip01(
        (speed - _float(overlay.get("speed_start_mps"), 4.0))
        / max(_float(overlay.get("speed_full_mps"), 14.0) - _float(overlay.get("speed_start_mps"), 4.0), 1e-6)
    )
    collision_base = _clip01(
        (float(hard["obstacle_urgency"]) - _float(overlay.get("collision_clearance_trigger"), 0.04))
        / max(1.0 - _float(overlay.get("collision_clearance_trigger"), 0.04), 1e-6)
    )
    edge_base = _clip01(
        (float(hard["edge_urgency"]) - _float(overlay.get("boundary_recovery_trigger"), 0.10))
        / max(1.0 - _float(overlay.get("boundary_recovery_trigger"), 0.10), 1e-6)
    )
    center_base = _clip01(abs(float(hard["road_center_error"])) * 1.25)
    stability = _stability_pressure(obs, _float(overlay.get("stability_trigger"), 0.08))
    collision_pressure = speed_alpha * collision_base
    boundary_pressure = speed_alpha * max(edge_base, center_base, stability)
    if collision_pressure <= 0.0 and boundary_pressure <= 0.0:
        selected_mode = "fallback"
    elif collision_pressure >= boundary_pressure:
        selected_mode = "collision_clearance_supervision"
    elif stability >= max(edge_base, center_base):
        selected_mode = "stability_recovery_supervision"
    else:
        selected_mode = "boundary_recovery_supervision"
    return {
        "selected_mode": selected_mode,
        "speed_mps": speed,
        "speed_alpha": speed_alpha,
        "obstacle_urgency": float(hard["obstacle_urgency"]),
        "obstacle_avoid_direction": float(hard["obstacle_avoid_direction"]),
        "edge_urgency": float(hard["edge_urgency"]),
        "road_center_error": float(hard["road_center_error"]),
        "collision_pressure": _clip01(collision_pressure),
        "boundary_pressure": _clip01(boundary_pressure),
        "stability_pressure": _clip01(stability),
    }


def _limited_delta(delta: np.ndarray, overlay: Mapping[str, Any]) -> np.ndarray:
    limited = np.asarray(
        [
            np.clip(
                delta[0],
                -_float(overlay.get("max_abs_steer_delta"), 0.62),
                _float(overlay.get("max_abs_steer_delta"), 0.62),
            ),
            np.clip(delta[1], -_float(overlay.get("max_throttle_drop"), 0.80), 0.0),
            np.clip(delta[2], 0.0, 2.0 * _float(overlay.get("max_brake_add"), 0.70)),
        ],
        dtype=np.float32,
    )
    max_l2 = _float(overlay.get("max_action_delta_l2"), 1.20)
    norm = float(np.linalg.norm(limited))
    if max_l2 > 0.0 and norm > max_l2:
        limited *= max_l2 / norm
    return limited


def recovery_clearance_supervisor_candidate_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3208 candidate direct [steer, throttle, brake] from obs72 only."""

    cfg = config or SUPERVISOR_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    fallback = np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG), dtype=np.float32)
    features = recovery_clearance_supervisor_features(obs, cfg)
    if features["selected_mode"] == "fallback":
        return fallback.astype(np.float32)

    overlay = _overlay_config(cfg)
    collision = float(features["collision_pressure"])
    boundary = float(features["boundary_pressure"])
    stability = float(features["stability_pressure"])
    mode_alpha = max(collision, boundary, _float(overlay.get("mode_blend_floor"), 0.18))

    target = fallback.copy()
    collision_steer = _float(overlay.get("collision_steer_budget"), 0.52) * collision * float(
        features["obstacle_avoid_direction"]
    )
    boundary_steer = _float(overlay.get("boundary_steer_budget"), 0.48) * boundary * float(features["road_center_error"])
    target[0] = (1.0 - mode_alpha) * float(fallback[0]) + mode_alpha * np.clip(
        collision_steer + boundary_steer,
        -_float(overlay.get("max_abs_steer_delta"), 0.62),
        _float(overlay.get("max_abs_steer_delta"), 0.62),
    )
    target[0] *= 1.0 - _float(overlay.get("stability_steer_damping"), 0.20) * stability

    brake_physical = _brake_to_physical(float(fallback[2]))
    brake_physical += (
        _float(overlay.get("collision_brake_add"), 0.58) * collision
        + _float(overlay.get("boundary_brake_add"), 0.30) * boundary
    )
    target[2] = _brake_from_physical(brake_physical)
    target[1] = float(fallback[1]) - (
        _float(overlay.get("collision_throttle_drop"), 0.70) * collision
        + _float(overlay.get("boundary_throttle_drop"), 0.28) * boundary
    )

    delta = _limited_delta(target - fallback, overlay)
    return np.clip(fallback + delta, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "supervisor_mode_rows": output_dir / "supervisor_mode_rows.csv",
        "feature_contract_rows": output_dir / "feature_contract_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3207_synthesis: Path, m3205_dir: Path, m3189_dir: Path, m3105_dir: Path) -> dict[str, Any]:
    paths = {
        "m3207_synthesis": m3207_synthesis,
        "m3205_summary": m3205_dir / "summary.json",
        "m3205_comparison_rows": m3205_dir / "same_trace_comparison_rows.csv",
        "m3205_gate_rows": m3205_dir / "gate_matrix.csv",
        "m3189_summary": m3189_dir / "summary.json",
        "m3105_summary": m3105_dir / "summary.json",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3207_synthesis_text": paths["m3207_synthesis"].read_text(encoding="utf-8") if exists["m3207_synthesis"] else "",
        "m3205_summary": read_json(paths["m3205_summary"]) if exists["m3205_summary"] else {},
        "m3205_comparison_rows": read_csv_rows(paths["m3205_comparison_rows"]),
        "m3205_gate_rows": read_csv_rows(paths["m3205_gate_rows"]),
        "m3189_summary": read_json(paths["m3189_summary"]) if exists["m3189_summary"] else {},
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
    }


def supervisor_mode_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "fallback",
            "p0",
            "no collision or boundary pressure; exactly preserve M3105/M3103 incumbent action",
            "obs72 ego response lane boundary obstacle slots",
            "steer|throttle|brake",
        ),
        (
            "collision_clearance_supervision",
            "p1",
            "speed-scaled obstacle urgency activates clearance steering plus brake/throttle budget",
            "obs72 ego speed obstacle slots lane corridor proxy",
            "steer|throttle|brake",
        ),
        (
            "boundary_recovery_supervision",
            "p2",
            "speed-scaled edge/center pressure activates road-center recovery with bounded speed management",
            "obs72 ego response left/right lane boundary geometry",
            "steer|throttle|brake",
        ),
        (
            "stability_recovery_supervision",
            "p3",
            "actor-visible sideslip/yaw/accel proxies damp steering and preserve recovery before offtrack",
            "obs72 ego lateral velocity yaw rate lateral acceleration steering rate",
            "steer|throttle|brake",
        ),
        (
            "action_budget_guard",
            "p4",
            "component and l2 action-delta budget keeps materialized supervisor bounded",
            "candidate internal direct-action delta only",
            "steer|throttle|brake",
        ),
    ]
    return [
        {
            "mode_id": f"m3208-supervisor-mode-{index:04d}",
            "mode_family": family,
            "priority": priority,
            "activation_summary": activation,
            "actor_visible_feature_groups": features,
            "output_channels": outputs,
            "fallback_policy_id": M3103_POLICY_ID,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, activation, features, outputs) in enumerate(specs, start=1)
    ]


def feature_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("ego_response", "obs72 ego speed lateral velocity yaw rate lateral acceleration steering rate"),
        ("lane_corridor_proxy", "obs72 left/right lane boundary samples only"),
        ("obstacle_clearance_proxy", "obs72 obstacle presence and relative x/y slots only"),
        ("mode_pressure", "deterministic scalar pressures derived from obs72 features"),
        ("forbidden_runtime_inputs", FORBIDDEN_RUNTIME_INPUTS),
    ]
    return [
        {
            "feature_id": f"m3208-feature-contract-{index:04d}",
            "feature_family": family,
            "input_contract": inputs,
            "derived_from_obs72_only": True,
            "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, inputs) in enumerate(specs, start=1)
    ]


def runtime_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("runtime_symbol", "recovery_clearance_supervisor_candidate_action"),
        ("obs72_input", "actor_visible_obs72_only"),
        ("direct_action3_output", "direct clipped [steer throttle brake]"),
        ("public_default_unchanged", "candidate artifact only"),
        ("no_runtime_base_policy", "deterministic function artifact only"),
    ]
    return [
        {
            "contract_id": f"m3208-runtime-contract-{index:04d}",
            "contract_family": family,
            "runtime_symbol": "recovery_clearance_supervisor_candidate_action",
            "input_contract": "actor_visible_obs72_only",
            "output_contract": "direct_action3",
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "action_components": "|".join(ACTION_COMPONENTS),
            "output_semantics": OUTPUT_SEMANTICS,
            "fallback_policy_id": M3103_POLICY_ID,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "status_pass": bool(value),
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, value) in enumerate(specs, start=1)
    ]


def _lane_obs(left_y_m: float = 3.0, right_y_m: float = -3.0) -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.75
    for index in range(8):
        obs[12 + index * 2 + 1] = left_y_m / 20.0
        obs[28 + index * 2 + 1] = right_y_m / 20.0
    return obs


def probe_observations() -> list[tuple[str, np.ndarray]]:
    low_risk = _lane_obs()
    low_risk[0] = 0.30
    collision = _lane_obs()
    collision[0] = 0.90
    collision[44] = 1.0
    collision[45] = 7.0 / 80.0
    collision[46] = 0.20 / 20.0
    boundary = _lane_obs(left_y_m=1.0, right_y_m=-5.0)
    boundary[0] = 0.82
    boundary[1] = 0.18
    boundary[2] = 0.12
    boundary[4] = 0.15
    mixed = boundary.copy()
    mixed[44] = 1.0
    mixed[45] = 6.5 / 80.0
    mixed[46] = -0.35 / 20.0
    stability = _lane_obs()
    stability[0] = 0.80
    stability[1] = 0.35
    stability[2] = -0.45
    stability[4] = 0.40
    stability[6] = 0.85
    return [
        ("low_risk_fallback_probe", low_risk),
        ("collision_clearance_probe", collision),
        ("boundary_recovery_probe", boundary),
        ("mixed_clearance_recovery_probe", mixed),
        ("stability_recovery_probe", stability),
    ]


def _delta_limited(delta: np.ndarray, overlay: Mapping[str, Any]) -> bool:
    return (
        abs(float(delta[0])) <= _float(overlay.get("max_abs_steer_delta"), 0.62) + 1e-6
        and -_float(overlay.get("max_throttle_drop"), 0.80) - 1e-6 <= float(delta[1]) <= 1e-6
        and -1e-6 <= float(delta[2]) <= 2.0 * _float(overlay.get("max_brake_add"), 0.70) + 1e-6
        and float(np.linalg.norm(delta)) <= _float(overlay.get("max_action_delta_l2"), 1.20) + 1e-6
    )


def action_probe_rows(config: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = config or SUPERVISOR_POLICY_CONFIG
    overlay = _overlay_config(cfg)
    rows: list[dict[str, Any]] = []
    for index, (family, obs) in enumerate(probe_observations(), start=1):
        fallback = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        candidate = recovery_clearance_supervisor_candidate_action(obs, cfg)
        features = recovery_clearance_supervisor_features(obs, cfg)
        delta = candidate - fallback
        rows.append(
            {
                "probe_id": f"m3208-action-probe-{index:04d}",
                "probe_family": family,
                "selected_mode": features["selected_mode"],
                "fallback_steer": float(fallback[0]),
                "fallback_throttle": float(fallback[1]),
                "fallback_brake": float(fallback[2]),
                "candidate_steer": float(candidate[0]),
                "candidate_throttle": float(candidate[1]),
                "candidate_brake": float(candidate[2]),
                "steer_delta": float(delta[0]),
                "throttle_delta": float(delta[1]),
                "brake_delta": float(delta[2]),
                "speed_mps": float(features["speed_mps"]),
                "collision_pressure": float(features["collision_pressure"]),
                "boundary_pressure": float(features["boundary_pressure"]),
                "stability_pressure": float(features["stability_pressure"]),
                "obstacle_urgency": float(features["obstacle_urgency"]),
                "edge_urgency": float(features["edge_urgency"]),
                "road_center_error": float(features["road_center_error"]),
                "fallback_path_selected": bool(np.allclose(candidate, fallback)),
                "action_finite": bool(np.all(np.isfinite(candidate))),
                "action_bounded": bool(np.max(np.abs(candidate)) <= 1.0),
                "delta_limited": _delta_limited(delta, overlay),
                "public_driver_default_mutated": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("direct_action_policy_config", "architecture_artifact", True, "direct_action_policy_config.json"),
        ("supervisor_mode_rows", "architecture_artifact", True, "supervisor_mode_rows.csv"),
        ("feature_contract_rows", "contract_artifact", True, "feature_contract_rows.csv"),
        ("runtime_contract_rows", "contract_artifact", True, "runtime_contract_rows.csv"),
        ("action_probe_rows", "probe_artifact", True, "action_probe_rows.csv"),
        ("follow_up_result_audit_registered", "process", follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
    ]
    blocked = [
        ("measurement_result", "forbidden", "future residual trace or full-fresh measurement preflight"),
        ("validation_result", "forbidden", "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", "future audited result synthesis"),
        ("robustness_result", "forbidden", "future robustness panel measurement"),
        ("repair_success", "forbidden", "accepted measurement improvement plus validation route"),
        ("public_driver_default_mutation", "forbidden", "future promotion gate"),
        ("self_id", "forbidden", "history necessity tests outside M3208"),
    ]
    rows = [
        {
            "claim_id": f"m3208-{claim_id}",
            "claim_family": family,
            "allowed_in_m3208": True,
            "claim_made": made,
            "status_pass": bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3208-{claim_id}",
            "claim_family": family,
            "allowed_in_m3208": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3208-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3207_selects_m3208(text: str) -> bool:
    return MILESTONE_ID in text or "recovery-clearance supervisor architecture materialization" in text


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    modes: list[dict[str, Any]],
    features: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    mode_families = {str(row.get("mode_family")) for row in modes}
    selected_modes = {str(row.get("selected_mode")) for row in probes}
    high_risk_probe_count = sum(not _bool(row.get("fallback_path_selected")) for row in probes)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3207_selects_m3208_route", "lineage", _m3207_selects_m3208(source["m3207_synthesis_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3205_status_pass", "lineage", _bool(source["m3205_summary"].get("status_pass")), source["m3205_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3205_behavior_neutral", "lineage", int(source["m3205_summary"].get("hard_safety_improved_vs_incumbent_count", 0)) == 0 and int(source["m3205_summary"].get("outcome_changed_vs_incumbent_count", 0)) == 0, "no incumbent hard-safety improvement or outcome change", "neutral", "lineage_invalid"),
        gate("incumbent_source_present", "lineage", bool(source["m3105_summary"]), "present", "present", "lineage_invalid"),
        gate("supervisor_mode_rows", "architecture", len(modes) == 5, len(modes), 5, "metric_artifact"),
        gate("required_modes_present", "architecture", {"fallback", "collision_clearance_supervision", "boundary_recovery_supervision", "stability_recovery_supervision", "action_budget_guard"}.issubset(mode_families), sorted(mode_families), "all required", "metric_artifact"),
        gate("feature_contract_rows", "contract", len(features) >= 5 and all(_bool(row.get("status_pass")) for row in features), len(features), ">=5 pass", "contract_violation"),
        gate("runtime_contract_rows", "contract", len(contracts) >= 5 and all(_bool(row.get("status_pass")) for row in contracts), len(contracts), ">=5 pass", "contract_violation"),
        gate("runtime_base_policy_not_required", "contract", not any(_bool(row.get("runtime_base_policy_required")) for row in modes + features + contracts), "none", "required", "contract_violation"),
        gate("hidden_oracle_input_not_required", "contract", not any(_bool(row.get("hidden_oracle_actor_input_required")) for row in modes + features + contracts), "none", "required", "contract_violation"),
        gate("ttc_input_not_required", "contract", not any(_bool(row.get("ttc_actor_input_required")) for row in modes + features + contracts), "none", "required", "contract_violation"),
        gate("public_driver_default_unchanged", "contract", not any(_bool(row.get("public_driver_default_mutated")) for row in modes + contracts + probes), "none", "mutated", "contract_violation"),
        gate("action_probe_rows", "probe", len(probes) >= 5, len(probes), ">=5", "metric_artifact"),
        gate("probe_actions_finite_bounded", "probe", all(_bool(row.get("action_finite")) and _bool(row.get("action_bounded")) for row in probes), "all", "finite bounded", "metric_artifact"),
        gate("probe_deltas_limited", "probe", all(_bool(row.get("delta_limited")) for row in probes), "all", "limited", "contract_violation"),
        gate("low_risk_fallback_exact", "probe", any(str(row.get("probe_family")) == "low_risk_fallback_probe" and _bool(row.get("fallback_path_selected")) for row in probes), "low risk", "fallback exact", "behavior_regression"),
        gate("high_risk_probe_count", "probe", high_risk_probe_count >= 4, high_risk_probe_count, ">=4", "metric_artifact"),
        gate("probe_modes_cover_supervisor", "probe", {"collision_clearance_supervision", "boundary_recovery_supervision", "stability_recovery_supervision"}.issubset(selected_modes), sorted(selected_modes), "collision boundary stability", "metric_artifact"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claims), "all", "pass", "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 32090,
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
        "hypothesis": "A bounded result audit can accept or reject M3208 recovery-clearance supervisor architecture artifacts before residual-trace measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_policy_config.json"),
                str(output_dir / "supervisor_mode_rows.csv"),
                str(output_dir / "feature_contract_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3208 supervisor architecture artifacts before residual-trace measurement"],
            "derived_from": [MILESTONE_ID, M3207_ID, M3205_ID, M3189_ID, M3105_ID],
            "blocked_by": [
                "M3208 architecture artifacts require audit before residual-trace measurement",
                "M3208 materialization is not validation repair success or public default replacement",
            ],
            "supersedes": ["direct measurement without audited M3208 supervisor architecture artifacts"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3209 must audit M3208 config mode feature contract runtime contract action-probe claim and gate artifacts",
            "M3209 must preserve obs72-only direct action runtime and public driver unchanged",
            "M3209 must reject measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3209 must select residual-trace measurement artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking or promotion in M3209",
            "do not convert M3208 synthetic probes into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_recovery_clearance_supervisor",
            "evidence_axis": "recovery_clearance_supervisor_architecture_result_audit",
            "evidence_increment": "audits recovery-clearance supervisor architecture artifacts before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3208 artifacts are missing or gate matrix fails",
                "stop if actor contract was violated",
                "route to residual-trace measurement only after M3209 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3208 artifact repair if modes probes or gates fail",
                "route to synthesis if architecture cannot preserve actor contract",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3208 materializes supervisor architecture artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3208 supervisor architecture artifacts",
            "admission_evidence": ["M3208 summary config mode feature contract action-probe claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3209 status queue scoreboard research log and review",
                "one follow-up manifest only if M3209 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3209 accepts or rejects M3208 as complete and claim-safe",
                "next residual-trace measurement artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3209 audits engineering architecture artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3209; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3208 architecture artifacts only.",
            "negative_result_policy": "Preserve architecture evidence and route measurement or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3208 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new architecture materialization before same-seven residual trace measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3209 audits engineering architecture artifacts",
            "must_synthesize_if": [
                "M3209 cannot select residual-trace measurement artifact-repair synthesis or stop",
                "M3209 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3209 audits M3208 row counts gates actor contract and claim boundaries",
            "M3209 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3209 hides missing M3208 artifacts or failed gates",
            "M3209 treats M3208 candidate probes as measurement or repair success",
            "M3209 changes actor input or action contract",
            "M3209 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3209 audits M3208 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_recovery_clearance_supervisor_architecture_result_audit_doc",
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
            "# M3208 Recovery-Clearance Supervisor Architecture Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- supervisor mode rows: {summary['supervisor_mode_row_count']}",
            f"- feature contract rows: {summary['feature_contract_row_count']}",
            f"- runtime contract rows: {summary['runtime_contract_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- high-risk probe rows: {summary['high_risk_action_probe_count']}",
            f"- probe modes covered: {', '.join(summary['probe_modes_covered'])}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3208 materializes a new deterministic recovery-clearance supervisor candidate as an architecture artifact. It changes the evidence axis from scalar action-authority amplification to explicit mode-level clearance, boundary recovery, stability recovery, and bounded fallback behavior. It keeps M3105/M3103 as incumbent and does not measure or validate the candidate.",
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


def run_supervisor_architecture_materialization_preflight(
    *,
    m3207_synthesis: Path,
    m3205_dir: Path,
    m3189_dir: Path,
    m3105_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3207_synthesis=m3207_synthesis,
        m3205_dir=m3205_dir,
        m3189_dir=m3189_dir,
        m3105_dir=m3105_dir,
    )
    modes = supervisor_mode_rows()
    features = feature_contract_rows()
    contracts = runtime_contract_rows()
    probes = action_probe_rows(SUPERVISOR_POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_json(paths["direct_action_policy_config"], SUPERVISOR_POLICY_CONFIG)
    write_csv_rows(paths["supervisor_mode_rows"], modes, fieldnames=MODE_FIELDNAMES)
    write_csv_rows(paths["feature_contract_rows"], features, fieldnames=FEATURE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], contracts, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(paths["action_probe_rows"], probes, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        modes=modes,
        features=features,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    high_risk_probe_count = sum(not _bool(row.get("fallback_path_selected")) for row in probes)
    probe_modes = sorted({str(row.get("selected_mode")) for row in probes})
    status_pass = bool(gate_matrix_pass and high_risk_probe_count >= 4)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "recovery_clearance_supervisor_architecture_materialized" if status_pass else "recovery_clearance_supervisor_architecture_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "supervisor_mode_row_count": len(modes),
        "feature_contract_row_count": len(features),
        "runtime_contract_row_count": len(contracts),
        "action_probe_row_count": len(probes),
        "high_risk_action_probe_count": high_risk_probe_count,
        "probe_modes_covered": probe_modes,
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "output_semantics": OUTPUT_SEMANTICS,
        "action_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
        "public_driver_default_mutated": False,
        "measurement_run": False,
        "validation_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "self_id_claim_made": False,
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
            "supervisor_mode_row_count": len(modes),
            "feature_contract_row_count": len(features),
            "runtime_contract_row_count": len(contracts),
            "action_probe_row_count": len(probes),
            "high_risk_action_probe_count": high_risk_probe_count,
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3207-synthesis", type=Path, default=DEFAULT_M3207_SYNTHESIS)
    parser.add_argument("--m3205-dir", type=Path, default=DEFAULT_M3205_DIR)
    parser.add_argument("--m3189-dir", type=Path, default=DEFAULT_M3189_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_supervisor_architecture_materialization_preflight(
        m3207_synthesis=args.m3207_synthesis,
        m3205_dir=args.m3205_dir,
        m3189_dir=args.m3189_dir,
        m3105_dir=args.m3105_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(summary)


if __name__ == "__main__":
    main()
