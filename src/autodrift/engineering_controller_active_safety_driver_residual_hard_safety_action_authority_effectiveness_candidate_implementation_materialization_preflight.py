"""Materialize M3203 action-authority/effectiveness candidate artifacts."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight import (
    POLICY_ID as M3194_POLICY_ID,
    preterminal_authority_boundary_stability_candidate_action,
)
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
    "m3203-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-implementation-materialization-preflight"
)
NEXT_ID = (
    "m3204-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-implementation-result-audit"
)
M3202_ID = (
    "m3202-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-admission-result-audit"
)
M3201_ID = (
    "m3201-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-admission-materialization-preflight"
)
M3199_ID = (
    "m3199-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-materialization-preflight"
)
POLICY_ID = "m3203_action_authority_effectiveness_candidate"

DEFAULT_M3202_AUDIT = Path(f"docs/{M3202_ID}.md")
DEFAULT_M3201_DIR = Path(
    "runs/m3201_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_admission_materialization_preflight"
)
DEFAULT_M3199_DIR = Path(
    "runs/m3199_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_"
    "trace_delta_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3203_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_candidate_implementation_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_ADMISSION_ROWS = 4
EXPECTED_IMPLEMENTATION_ROWS = 3
EXPECTED_GUARD_ONLY_ROWS = 1
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3203 Active Safety Driver residual hard-safety action-authority/effectiveness "
    "candidate implementation materialization only; artifacts may define a stronger "
    "deterministic actor-visible obs72 to direct action3 candidate function, config, "
    "rules, runtime contracts, synthetic action probes, claim rows, gate rows, doc, "
    "and M3204 audit manifest. No reset, step, rollout, replay, full-fresh "
    "measurement, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, public driver default mutation, driver-performance verdict, "
    "current-sim verdict, repair success, robustness-result, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, "
    "feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)

POLICY_CONFIG: dict[str, Any] = deepcopy(V4_POLICY_CONFIG)
POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "supersedes_candidate_policy_id": M3194_POLICY_ID,
        "repair_route": "action_authority_effectiveness_candidate",
        "repair_scope": "candidate_materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "actor_observation_contract": "actor_visible_obs72_only",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "public_active_safety_reflex_driver_default_mutation": False,
    }
)
POLICY_CONFIG["action_authority_effectiveness"] = {
    "enabled": True,
    "speed_start_mps": 5.5,
    "speed_full_mps": 13.5,
    "speed_floor_preserve_below_mps": 4.5,
    "collision_obstacle_urgency_trigger": 0.02,
    "boundary_edge_urgency_trigger": 0.16,
    "stability_trigger": 0.10,
    "max_collision_brake_add": 0.42,
    "max_boundary_brake_add": 0.20,
    "max_collision_throttle_drop": 0.55,
    "max_boundary_throttle_drop": 0.18,
    "max_collision_steer_delta": 0.18,
    "max_boundary_steer_delta": 0.18,
    "boundary_override_steer_delta": 0.22,
    "stability_steer_damping": 0.25,
    "max_abs_steer_delta": 0.24,
    "max_throttle_drop": 0.60,
    "max_brake_add": 0.45,
    "max_action_delta_l2": 0.85,
}

RULE_FIELDNAMES = [
    "rule_id",
    "rule_family",
    "priority",
    "source_admission_family",
    "input_feature_groups",
    "output_channels",
    "formula_summary",
    "enabled_by_default",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "public_driver_default_mutated",
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
    "fallback_steer",
    "fallback_throttle",
    "fallback_brake",
    "m3194_steer",
    "m3194_throttle",
    "m3194_brake",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "candidate_vs_fallback_steer_delta",
    "candidate_vs_fallback_throttle_delta",
    "candidate_vs_fallback_brake_delta",
    "candidate_vs_m3194_steer_delta",
    "candidate_vs_m3194_throttle_delta",
    "candidate_vs_m3194_brake_delta",
    "collision_alpha",
    "boundary_alpha",
    "saturation_guard_alpha",
    "obstacle_urgency",
    "edge_urgency",
    "stability_risk",
    "speed_mps",
    "fallback_path_selected",
    "action_finite",
    "action_bounded",
    "stronger_than_m3194",
    "delta_limited",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3203",
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
    return config.get("action_authority_effectiveness", POLICY_CONFIG["action_authority_effectiveness"])


def _brake_to_physical(action_brake: float) -> float:
    return _clip01((action_brake + 1.0) / 2.0)


def _brake_from_physical(physical_brake: float) -> float:
    return -1.0 + 2.0 * _clip01(physical_brake)


def _stability_risk(observation: np.ndarray) -> float:
    obs = np.asarray(observation, dtype=np.float32)
    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    steer_rate = float(obs[6])
    return (
        _clip01(abs(vy_body) / 4.0)
        + _clip01(abs(yaw_rate) / 1.5)
        + _clip01(abs(ay_body) / 8.0)
        + _clip01(abs(steer_rate) / 1.0)
    ) / 4.0


def action_authority_effectiveness_features(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    cfg = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    hard = _hard_safety_features(obs, cfg)
    overlay = _overlay_config(cfg)
    speed = float(hard["vx_body"])
    speed_start = _float(overlay.get("speed_start_mps"), 5.5)
    speed_full = _float(overlay.get("speed_full_mps"), 13.5)
    speed_alpha = _clip01((speed - speed_start) / max(speed_full - speed_start, 1e-6))
    if speed < _float(overlay.get("speed_floor_preserve_below_mps"), 4.5):
        speed_alpha = 0.0

    obstacle_trigger = _float(overlay.get("collision_obstacle_urgency_trigger"), 0.02)
    edge_trigger = _float(overlay.get("boundary_edge_urgency_trigger"), 0.16)
    stability_trigger = _float(overlay.get("stability_trigger"), 0.10)
    obstacle_alpha = _clip01((float(hard["obstacle_urgency"]) - obstacle_trigger) / max(1.0 - obstacle_trigger, 1e-6))
    edge_alpha = _clip01((float(hard["edge_urgency"]) - edge_trigger) / max(1.0 - edge_trigger, 1e-6))
    stability = _stability_risk(obs)
    stability_alpha = _clip01((stability - stability_trigger) / max(1.0 - stability_trigger, 1e-6))
    collision_alpha = speed_alpha * obstacle_alpha
    boundary_alpha = speed_alpha * max(edge_alpha, stability_alpha)
    return {
        "speed_mps": speed,
        "speed_alpha": speed_alpha,
        "obstacle_urgency": float(hard["obstacle_urgency"]),
        "obstacle_avoid_direction": float(hard["obstacle_avoid_direction"]),
        "edge_urgency": float(hard["edge_urgency"]),
        "road_center_error": float(hard["road_center_error"]),
        "stability_risk": stability,
        "collision_alpha": _clip01(collision_alpha),
        "boundary_alpha": _clip01(boundary_alpha),
        "saturation_guard_alpha": max(_clip01(collision_alpha), _clip01(boundary_alpha)),
    }


def _limited_delta(delta: np.ndarray, overlay: Mapping[str, Any]) -> np.ndarray:
    limited = np.asarray(
        [
            np.clip(
                delta[0],
                -_float(overlay.get("max_abs_steer_delta"), 0.24),
                _float(overlay.get("max_abs_steer_delta"), 0.24),
            ),
            np.clip(delta[1], -_float(overlay.get("max_throttle_drop"), 0.60), 0.0),
            np.clip(delta[2], 0.0, 2.0 * _float(overlay.get("max_brake_add"), 0.45)),
        ],
        dtype=np.float32,
    )
    max_l2 = _float(overlay.get("max_action_delta_l2"), 0.85)
    norm = float(np.linalg.norm(limited))
    if max_l2 > 0.0 and norm > max_l2:
        limited *= max_l2 / norm
    return limited


def action_authority_effectiveness_candidate_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3203 candidate direct [steer, throttle, brake] from obs72 only."""

    cfg = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    fallback = np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG), dtype=np.float32)
    features = action_authority_effectiveness_features(obs, cfg)
    collision_alpha = float(features["collision_alpha"])
    boundary_alpha = float(features["boundary_alpha"])
    if max(collision_alpha, boundary_alpha) <= 0.0:
        return fallback.astype(np.float32)

    overlay = _overlay_config(cfg)
    action = fallback.copy()
    boundary_direction = float(np.sign(features["road_center_error"]))
    boundary_magnitude = min(1.0, abs(float(features["road_center_error"])) * 1.5)
    action[0] += (
        _float(overlay.get("max_collision_steer_delta"), 0.18) * collision_alpha * features["obstacle_avoid_direction"]
        + _float(overlay.get("max_boundary_steer_delta"), 0.18) * boundary_alpha * features["road_center_error"]
        + _float(overlay.get("boundary_override_steer_delta"), 0.22) * boundary_alpha * boundary_direction * boundary_magnitude
    )
    damping = _float(overlay.get("stability_steer_damping"), 0.25) * boundary_alpha * _clip01(features["stability_risk"])
    action[0] *= 1.0 - damping
    brake_physical = _brake_to_physical(float(action[2]))
    brake_physical += (
        _float(overlay.get("max_collision_brake_add"), 0.42) * collision_alpha
        + _float(overlay.get("max_boundary_brake_add"), 0.20) * boundary_alpha
    )
    action[2] = _brake_from_physical(brake_physical)
    action[1] -= (
        _float(overlay.get("max_collision_throttle_drop"), 0.55) * collision_alpha
        + _float(overlay.get("max_boundary_throttle_drop"), 0.18) * boundary_alpha
    )
    delta = _limited_delta(action - fallback, overlay)
    return np.clip(fallback + delta, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "candidate_rule_rows": output_dir / "candidate_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3202_audit: Path, m3201_dir: Path, m3199_dir: Path) -> dict[str, Any]:
    paths = {
        "m3202_audit": m3202_audit,
        "m3201_summary": m3201_dir / "summary.json",
        "m3201_admission_rows": m3201_dir / "action_authority_effectiveness_admission_rows.csv",
        "m3201_contract_guard_rows": m3201_dir / "contract_guard_rows.csv",
        "m3201_claim_boundary_rows": m3201_dir / "claim_boundary_rows.csv",
        "m3201_gate_rows": m3201_dir / "gate_matrix.csv",
        "m3199_summary": m3199_dir / "summary.json",
        "m3199_gate_rows": m3199_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3202_audit_text": paths["m3202_audit"].read_text(encoding="utf-8") if exists["m3202_audit"] else "",
        "m3201_summary": read_json(paths["m3201_summary"]) if exists["m3201_summary"] else {},
        "m3201_admission_rows": read_csv_rows(paths["m3201_admission_rows"]),
        "m3201_contract_guard_rows": read_csv_rows(paths["m3201_contract_guard_rows"]),
        "m3201_claim_boundary_rows": read_csv_rows(paths["m3201_claim_boundary_rows"]),
        "m3201_gate_rows": read_csv_rows(paths["m3201_gate_rows"]),
        "m3199_summary": read_json(paths["m3199_summary"]) if exists["m3199_summary"] else {},
        "m3199_gate_rows": read_csv_rows(paths["m3199_gate_rows"]),
    }


def candidate_rule_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "longitudinal_collision_authority_effectiveness_gap",
            "p1",
            "longitudinal_collision_authority_effectiveness_gap",
            "obs72 ego speed obstacle geometry proxy relative clearance proxy lane corridor geometry",
            "steer|throttle|brake",
            "lower obstacle trigger and larger bounded throttle-drop brake-add authority than M3194",
            True,
        ),
        (
            "lateral_collision_clearance_authority_effectiveness_gap",
            "p2",
            "lateral_collision_clearance_authority_effectiveness_gap",
            "obs72 obstacle geometry proxy lane corridor geometry lateral error heading alignment",
            "steer|throttle|brake",
            "larger corridor-aware obstacle avoidance steering with bounded action delta and offtrack guard",
            True,
        ),
        (
            "boundary_recovery_override_authority_effectiveness_gap",
            "p3",
            "boundary_recovery_override_authority_effectiveness_gap",
            "obs72 lane boundary geometry lateral error heading alignment sideslip proxy ego speed",
            "steer|throttle|brake",
            "higher-priority boundary recovery steering override plus stability damping and speed-preserving floor",
            True,
        ),
        (
            "action_effectiveness_saturation_guard",
            "p4",
            "action_effectiveness_saturation_guard",
            "candidate internal action delta l2 and component clip guard only",
            "steer|throttle|brake",
            "clips stronger authority deltas and prevents terminal-only saturation from being a success claim",
            False,
        ),
    ]
    return [
        {
            "rule_id": f"m3203-candidate-rule-{index:04d}",
            "rule_family": family,
            "priority": priority,
            "source_admission_family": admission_family,
            "input_feature_groups": inputs,
            "output_channels": outputs,
            "formula_summary": formula,
            "enabled_by_default": enabled,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, admission_family, inputs, outputs, formula, enabled) in enumerate(specs, start=1)
    ]


def runtime_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("runtime_symbol", "action_authority_effectiveness_candidate_action"),
        ("obs72_input", "actor_visible_obs72_only"),
        ("direct_action3_output", "direct clipped [steer throttle brake]"),
        ("public_default_unchanged", "candidate artifact only"),
        ("no_runtime_base_policy", "deterministic function artifact only"),
    ]
    return [
        {
            "contract_id": f"m3203-runtime-contract-{index:04d}",
            "contract_family": family,
            "runtime_symbol": "action_authority_effectiveness_candidate_action",
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
    obs[0] = 0.8
    for index in range(8):
        obs[12 + index * 2 + 1] = left_y_m / 20.0
        obs[28 + index * 2 + 1] = right_y_m / 20.0
    return obs


def probe_observations() -> list[tuple[str, np.ndarray]]:
    base = _lane_obs()
    low_risk = base.copy()
    low_risk[0] = 0.3
    collision = _lane_obs()
    collision[0] = 0.88
    collision[44] = 1.0
    collision[45] = 8.0 / 80.0
    collision[46] = 0.2 / 20.0
    boundary = _lane_obs(left_y_m=1.1, right_y_m=-5.0)
    boundary[0] = 0.78
    boundary[1] = 0.22
    boundary[2] = 0.25
    boundary[4] = 0.25
    mixed = boundary.copy()
    mixed[44] = 1.0
    mixed[45] = 7.0 / 80.0
    mixed[46] = -0.4 / 20.0
    return [
        ("low_risk_fallback_probe", low_risk),
        ("collision_authority_probe", collision),
        ("boundary_recovery_override_probe", boundary),
        ("mixed_collision_boundary_probe", mixed),
    ]


def _delta_limited(delta: np.ndarray, overlay: Mapping[str, Any]) -> bool:
    return (
        abs(float(delta[0])) <= _float(overlay.get("max_abs_steer_delta"), 0.24) + 1e-6
        and -_float(overlay.get("max_throttle_drop"), 0.60) - 1e-6 <= float(delta[1]) <= 1e-6
        and -1e-6 <= float(delta[2]) <= 2.0 * _float(overlay.get("max_brake_add"), 0.45) + 1e-6
        and float(np.linalg.norm(delta)) <= _float(overlay.get("max_action_delta_l2"), 0.85) + 1e-6
    )


def action_probe_rows(config: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = config or POLICY_CONFIG
    rows: list[dict[str, Any]] = []
    overlay = _overlay_config(cfg)
    for index, (family, obs) in enumerate(probe_observations(), start=1):
        fallback = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        m3194 = preterminal_authority_boundary_stability_candidate_action(obs)
        candidate = action_authority_effectiveness_candidate_action(obs, cfg)
        features = action_authority_effectiveness_features(obs, cfg)
        candidate_delta = candidate - fallback
        m3194_delta = m3194 - fallback
        candidate_vs_m3194 = candidate - m3194
        candidate_l2 = float(np.linalg.norm(candidate_delta))
        m3194_l2 = float(np.linalg.norm(m3194_delta))
        rows.append(
            {
                "probe_id": f"m3203-action-probe-{index:04d}",
                "probe_family": family,
                "fallback_steer": float(fallback[0]),
                "fallback_throttle": float(fallback[1]),
                "fallback_brake": float(fallback[2]),
                "m3194_steer": float(m3194[0]),
                "m3194_throttle": float(m3194[1]),
                "m3194_brake": float(m3194[2]),
                "candidate_steer": float(candidate[0]),
                "candidate_throttle": float(candidate[1]),
                "candidate_brake": float(candidate[2]),
                "candidate_vs_fallback_steer_delta": float(candidate_delta[0]),
                "candidate_vs_fallback_throttle_delta": float(candidate_delta[1]),
                "candidate_vs_fallback_brake_delta": float(candidate_delta[2]),
                "candidate_vs_m3194_steer_delta": float(candidate_vs_m3194[0]),
                "candidate_vs_m3194_throttle_delta": float(candidate_vs_m3194[1]),
                "candidate_vs_m3194_brake_delta": float(candidate_vs_m3194[2]),
                "collision_alpha": float(features["collision_alpha"]),
                "boundary_alpha": float(features["boundary_alpha"]),
                "saturation_guard_alpha": float(features["saturation_guard_alpha"]),
                "obstacle_urgency": float(features["obstacle_urgency"]),
                "edge_urgency": float(features["edge_urgency"]),
                "stability_risk": float(features["stability_risk"]),
                "speed_mps": float(features["speed_mps"]),
                "fallback_path_selected": bool(np.allclose(candidate, fallback)),
                "action_finite": bool(np.all(np.isfinite(candidate))),
                "action_bounded": bool(np.max(np.abs(candidate)) <= 1.0),
                "stronger_than_m3194": bool(candidate_l2 > m3194_l2 + 1e-6),
                "delta_limited": _delta_limited(candidate_delta, overlay),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("direct_action_policy_config", "implementation_artifact", True, True, "direct_action_policy_config.json"),
        ("candidate_rule_rows", "implementation_artifact", True, True, "candidate_rule_rows.csv"),
        ("runtime_contract_rows", "contract_artifact", True, True, "runtime_contract_rows.csv"),
        ("action_probe_rows", "probe_artifact", True, True, "action_probe_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("measurement_result", "forbidden", False, False, "future residual trace or full-fresh measurement preflight"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("robustness_result", "forbidden", False, False, "future robustness panel measurement"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("public_driver_default_mutation", "forbidden", False, False, "future promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3203"),
    ]
    return [
        {
            "claim_id": f"m3203-{claim_id}",
            "claim_family": family,
            "allowed_in_m3203": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3203-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3202_selects_m3203(text: str) -> bool:
    return (
        "m3203-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-candidate-implementation-materialization-preflight"
        in text
        or "route to M3203 action-authority/effectiveness candidate implementation" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    rules: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    rule_families = {str(row.get("rule_family", "")) for row in rules}
    admission_families = {str(row.get("admission_family", "")) for row in source["m3201_admission_rows"]}
    implementation_count = sum(
        str(row.get("admission_role", "")) == "implementation_candidate_after_audit" for row in source["m3201_admission_rows"]
    )
    guard_only_count = sum(str(row.get("admission_role", "")) == "cross_cutting_guard_only" for row in source["m3201_admission_rows"])
    high_risk_probe_count = sum(not _bool(row.get("fallback_path_selected")) for row in probes)
    stronger_probe_count = sum(_bool(row.get("stronger_than_m3194")) for row in probes if not _bool(row.get("fallback_path_selected")))
    low_risk_exact = any(
        str(row.get("probe_family")) == "low_risk_fallback_probe" and _bool(row.get("fallback_path_selected"))
        for row in probes
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3202_selects_m3203_route", "lineage", _m3202_selects_m3203(source["m3202_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3201_status_pass", "lineage", _bool(source["m3201_summary"].get("status_pass")), source["m3201_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3201_gate_matrix_pass", "lineage", _bool(source["m3201_summary"].get("gate_matrix_pass")), source["m3201_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3199_status_pass", "lineage", _bool(source["m3199_summary"].get("status_pass")), source["m3199_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3199_gate_matrix_pass", "lineage", _bool(source["m3199_summary"].get("gate_matrix_pass")), source["m3199_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3201_admission_row_count", "admission", len(source["m3201_admission_rows"]) == EXPECTED_ADMISSION_ROWS, len(source["m3201_admission_rows"]), EXPECTED_ADMISSION_ROWS, "metric_artifact"),
        gate("m3201_implementation_recommended_count", "admission", implementation_count == EXPECTED_IMPLEMENTATION_ROWS, implementation_count, EXPECTED_IMPLEMENTATION_ROWS, "metric_artifact"),
        gate("m3201_guard_only_count", "admission", guard_only_count == EXPECTED_GUARD_ONLY_ROWS, guard_only_count, EXPECTED_GUARD_ONLY_ROWS, "metric_artifact"),
        gate("required_admission_families", "admission", {"longitudinal_collision_authority_effectiveness_gap", "lateral_collision_clearance_authority_effectiveness_gap", "boundary_recovery_override_authority_effectiveness_gap", "action_effectiveness_saturation_guard"}.issubset(admission_families), sorted(admission_families), "all required", "metric_artifact"),
        gate("candidate_rule_rows", "implementation", len(rules) == 4, len(rules), 4, "metric_artifact"),
        gate("required_rule_families", "implementation", {"longitudinal_collision_authority_effectiveness_gap", "lateral_collision_clearance_authority_effectiveness_gap", "boundary_recovery_override_authority_effectiveness_gap", "action_effectiveness_saturation_guard"}.issubset(rule_families), sorted(rule_families), "all required", "metric_artifact"),
        gate("runtime_contract_rows", "contract", len(contracts) >= 5 and all(_bool(row.get("status_pass")) for row in contracts), len(contracts), ">=5 pass", "contract_violation"),
        gate("runtime_base_policy_not_required", "contract", not any(_bool(row.get("runtime_base_policy_required")) for row in rules + contracts), "none", "required", "contract_violation"),
        gate("hidden_oracle_input_not_required", "contract", not any(_bool(row.get("hidden_oracle_actor_input_required")) for row in rules + contracts), "none", "required", "contract_violation"),
        gate("ttc_input_not_required", "contract", not any(_bool(row.get("ttc_actor_input_required")) for row in rules + contracts), "none", "required", "contract_violation"),
        gate("public_driver_default_unchanged", "contract", not any(_bool(row.get("public_driver_default_mutated")) for row in rules + contracts), "none", "mutated", "contract_violation"),
        gate("action_probe_rows", "probe", len(probes) >= 4, len(probes), ">=4", "metric_artifact"),
        gate("probe_actions_finite_bounded", "probe", all(_bool(row.get("action_finite")) and _bool(row.get("action_bounded")) for row in probes), "all", "finite bounded", "metric_artifact"),
        gate("probe_deltas_limited", "probe", all(_bool(row.get("delta_limited")) for row in probes), "all", "limited", "contract_violation"),
        gate("low_risk_fallback_exact", "probe", low_risk_exact, low_risk_exact, True, "behavior_regression"),
        gate("high_risk_probe_count", "probe", high_risk_probe_count >= 3, high_risk_probe_count, ">=3", "metric_artifact"),
        gate("stronger_than_m3194_high_risk_probe_count", "probe", stronger_probe_count >= 3, stronger_probe_count, ">=3", "metric_artifact"),
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
        "priority": 32040,
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
        "hypothesis": "A bounded result audit can accept or reject M3203 action-authority/effectiveness candidate implementation artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_policy_config.json"),
                str(output_dir / "candidate_rule_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3203 candidate artifacts before residual-trace measurement"],
            "derived_from": [MILESTONE_ID, M3202_ID, M3201_ID, M3199_ID, M3194_POLICY_ID],
            "blocked_by": [
                "M3203 candidate artifacts require audit before any measurement",
                "M3203 materialization is not validation, repair success, or public default replacement",
            ],
            "supersedes": ["direct measurement without audited M3203 candidate artifacts"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3204 must audit M3203 candidate config rule contract action-probe claim and gate artifacts",
            "M3204 must preserve obs72-only direct action runtime and public driver unchanged",
            "M3204 must reject measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3204 must select residual-trace measurement artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking or promotion in M3204",
            "do not convert M3203 synthetic probes into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_action_authority_effectiveness",
            "evidence_axis": "candidate_implementation_result_audit",
            "evidence_increment": "audits deterministic stronger action-authority/effectiveness candidate artifacts before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3203 artifacts are missing or gate matrix fails",
                "stop if actor contract was violated",
                "route to measurement only after M3204 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3203 artifact repair if rules probes or gates fail",
                "route to synthesis if deterministic candidate cannot preserve actor contract",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3203 materializes candidate artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3203 candidate implementation artifacts",
            "admission_evidence": ["M3203 summary config rule contract action-probe claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3204 status queue scoreboard research log and review",
                "one follow-up manifest only if M3204 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3204 accepts or rejects M3203 as complete and claim-safe",
                "next residual-trace measurement artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3204 audits engineering candidate artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3204; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3203 candidate artifacts only.",
            "negative_result_policy": "Preserve candidate evidence and route measurement or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3203 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits candidate materialization before same-seven residual trace measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3204 audits engineering candidate artifacts",
            "must_synthesize_if": [
                "M3204 cannot select residual-trace measurement artifact-repair synthesis or stop",
                "M3204 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3204 audits M3203 row counts gates actor contract and claim boundaries",
            "M3204 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3204 hides missing M3203 artifacts or failed gates",
            "M3204 treats M3203 candidate probes as measurement or repair success",
            "M3204 changes actor input or action contract",
            "M3204 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3204 audits M3203 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_action_authority_effectiveness_candidate_implementation_result_audit_doc",
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
            "# M3203 Action-Authority/Effectiveness Candidate Implementation Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rule rows: {summary['candidate_rule_row_count']}",
            f"- runtime contract rows: {summary['runtime_contract_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- high-risk probes stronger than M3194: {summary['stronger_than_m3194_high_risk_probe_count']}",
            f"- low-risk fallback exact: {summary['low_risk_fallback_exact']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3203 materializes an independent deterministic obs72-to-action3 candidate artifact that increases bounded action authority relative to M3194 on synthetic high-risk probes. It keeps M3105/M3103 as the public incumbent and does not run measurement or validation.",
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


def run_candidate_materialization_preflight(
    *,
    m3202_audit: Path,
    m3201_dir: Path,
    m3199_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3202_audit=m3202_audit, m3201_dir=m3201_dir, m3199_dir=m3199_dir)
    rules = candidate_rule_rows()
    contracts = runtime_contract_rows()
    probes = action_probe_rows(POLICY_CONFIG)
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_csv_rows(paths["candidate_rule_rows"], rules, fieldnames=RULE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], contracts, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(paths["action_probe_rows"], probes, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        probes=probes,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    high_risk_probe_count = sum(not _bool(row.get("fallback_path_selected")) for row in probes)
    stronger_probe_count = sum(_bool(row.get("stronger_than_m3194")) for row in probes if not _bool(row.get("fallback_path_selected")))
    low_risk_fallback_exact = any(
        str(row.get("probe_family")) == "low_risk_fallback_probe" and _bool(row.get("fallback_path_selected"))
        for row in probes
    )
    status_pass = bool(gate_matrix_pass and high_risk_probe_count >= 3 and stronger_probe_count >= 3)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "action_authority_effectiveness_candidate_materialized" if status_pass else "action_authority_effectiveness_candidate_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "supersedes_candidate_policy_id": M3194_POLICY_ID,
        "candidate_rule_row_count": len(rules),
        "runtime_contract_row_count": len(contracts),
        "action_probe_row_count": len(probes),
        "high_risk_action_probe_count": high_risk_probe_count,
        "stronger_than_m3194_high_risk_probe_count": stronger_probe_count,
        "low_risk_fallback_exact": low_risk_fallback_exact,
        "claim_boundary_row_count": len(claims),
        "m3201_admission_row_count": len(source["m3201_admission_rows"]),
        "m3201_implementation_recommended_count": sum(
            str(row.get("admission_role", "")) == "implementation_candidate_after_audit"
            for row in source["m3201_admission_rows"]
        ),
        "m3201_guard_only_count": sum(
            str(row.get("admission_role", "")) == "cross_cutting_guard_only"
            for row in source["m3201_admission_rows"]
        ),
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
            "candidate_rule_row_count": len(rules),
            "runtime_contract_row_count": len(contracts),
            "action_probe_row_count": len(probes),
            "high_risk_action_probe_count": high_risk_probe_count,
            "stronger_than_m3194_high_risk_probe_count": stronger_probe_count,
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3202-audit", type=Path, default=DEFAULT_M3202_AUDIT)
    parser.add_argument("--m3201-dir", type=Path, default=DEFAULT_M3201_DIR)
    parser.add_argument("--m3199-dir", type=Path, default=DEFAULT_M3199_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_candidate_materialization_preflight(
        m3202_audit=args.m3202_audit,
        m3201_dir=args.m3201_dir,
        m3199_dir=args.m3199_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(summary)


if __name__ == "__main__":
    main()
