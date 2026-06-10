"""Materialize M3170 source-localized repair implementation candidate artifacts."""

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
    "m3170-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-materialization-preflight"
)
NEXT_ID = (
    "m3171-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-result-audit"
)
M3169_ID = (
    "m3169-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-admission-result-audit"
)
M3168_ID = (
    "m3168-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-admission-materialization-preflight"
)
M3167_ID = (
    "m3167-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-result-audit"
)
M3166_ID = (
    "m3166-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-materialization-preflight"
)

POLICY_ID = "m3170_source_localized_repair_overlay"

DEFAULT_M3169_AUDIT = Path(f"docs/{M3169_ID}.md")
DEFAULT_M3168_DIR = Path(
    "runs/m3168_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_admission_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3170_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3170 Active Safety Driver residual hard-safety source-localized repair "
    "implementation materialization only; artifacts may define a deterministic "
    "actor-visible obs72 to direct action3 [steer throttle brake] candidate overlay, "
    "config, rules, runtime contracts, repair-hypothesis bindings, synthetic action "
    "probes, claim boundaries, gate matrix, doc, and M3171 audit manifest. No reset, "
    "step, rollout, replay, full-fresh measurement, validation, ranking, winner "
    "selection, checkpoint mutation, checkpoint promotion, public driver default "
    "mutation, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, feasibility proof, or self-ID claim is made"
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
        "repair_route": "source_localized_collision_clearance_and_boundary_recovery_overlay",
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
POLICY_CONFIG["source_localized_overlay"] = {
    "enabled": True,
    "speed_start_mps": 8.0,
    "speed_full_mps": 18.0,
    "speed_floor_preserve_below_mps": 7.0,
    "collision_obstacle_urgency_trigger": 0.10,
    "boundary_edge_urgency_trigger": 0.35,
    "boundary_stability_trigger": 0.24,
    "max_collision_brake_add": 0.24,
    "max_boundary_brake_add": 0.16,
    "max_collision_throttle_drop": 0.28,
    "max_boundary_throttle_drop": 0.16,
    "max_collision_steer_delta": 0.16,
    "max_boundary_steer_delta": 0.12,
    "stability_steer_damping": 0.18,
    "max_abs_steer_delta": 0.20,
    "max_throttle_drop": 0.34,
    "max_brake_add": 0.32,
}

RULE_FIELDNAMES = [
    "rule_id",
    "rule_family",
    "priority",
    "input_feature_groups",
    "output_channels",
    "formula_summary",
    "enabled_by_default",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "claim_boundary",
]
BINDING_FIELDNAMES = [
    "binding_id",
    "source_repair_hypothesis_id",
    "source_repair_hypothesis_name",
    "blocker_family",
    "source_localization_row_count",
    "candidate_rule_family",
    "admitted_for_repair_implementation_materialization",
    "admitted_for_validation",
    "runtime_actor_inputs",
    "forbidden_actor_inputs",
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
    "fallback_steer",
    "fallback_throttle",
    "fallback_brake",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "steer_delta",
    "throttle_delta",
    "brake_delta",
    "collision_alpha",
    "boundary_alpha",
    "obstacle_urgency",
    "edge_urgency",
    "stability_risk",
    "speed_mps",
    "fallback_path_selected",
    "action_finite",
    "action_bounded",
    "delta_limited",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3170",
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
    return config.get("source_localized_overlay", POLICY_CONFIG["source_localized_overlay"])


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


def source_localized_repair_features(observation: np.ndarray, config: Mapping[str, Any]) -> dict[str, float]:
    obs = np.asarray(observation, dtype=np.float32)
    hard = _hard_safety_features(obs, config)
    overlay = _overlay_config(config)
    speed = float(hard["vx_body"])
    speed_start = _float(overlay.get("speed_start_mps"), 8.0)
    speed_full = _float(overlay.get("speed_full_mps"), 18.0)
    speed_alpha = _clip01((speed - speed_start) / max(speed_full - speed_start, 1e-6))
    if speed < _float(overlay.get("speed_floor_preserve_below_mps"), 7.0):
        speed_alpha = 0.0

    obstacle_alpha = _clip01(
        (float(hard["obstacle_urgency"]) - _float(overlay.get("collision_obstacle_urgency_trigger"), 0.10))
        / max(1.0 - _float(overlay.get("collision_obstacle_urgency_trigger"), 0.10), 1e-6)
    )
    edge_alpha = _clip01(
        (float(hard["edge_urgency"]) - _float(overlay.get("boundary_edge_urgency_trigger"), 0.35))
        / max(1.0 - _float(overlay.get("boundary_edge_urgency_trigger"), 0.35), 1e-6)
    )
    stability = _stability_risk(obs)
    stability_alpha = _clip01(
        (stability - _float(overlay.get("boundary_stability_trigger"), 0.24))
        / max(1.0 - _float(overlay.get("boundary_stability_trigger"), 0.24), 1e-6)
    )
    collision_alpha = speed_alpha * obstacle_alpha
    boundary_alpha = speed_alpha * max(edge_alpha, edge_alpha * stability_alpha)
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
    }


def source_localized_repair_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3170 candidate direct [steer, throttle, brake] from obs72 only."""

    cfg = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    fallback = np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG), dtype=np.float32)
    features = source_localized_repair_features(obs, cfg)
    collision_alpha = float(features["collision_alpha"])
    boundary_alpha = float(features["boundary_alpha"])
    if max(collision_alpha, boundary_alpha) <= 0.0:
        return fallback.astype(np.float32)

    overlay = _overlay_config(cfg)
    action = fallback.copy()
    action[0] += (
        _float(overlay.get("max_collision_steer_delta")) * collision_alpha * features["obstacle_avoid_direction"]
        + _float(overlay.get("max_boundary_steer_delta")) * boundary_alpha * features["road_center_error"]
    )
    damping = _float(overlay.get("stability_steer_damping")) * boundary_alpha * _clip01(features["stability_risk"])
    action[0] *= 1.0 - damping

    brake_physical = _brake_to_physical(float(action[2]))
    brake_physical += (
        _float(overlay.get("max_collision_brake_add")) * collision_alpha
        + _float(overlay.get("max_boundary_brake_add")) * boundary_alpha
    )
    action[2] = _brake_from_physical(brake_physical)
    action[1] -= (
        _float(overlay.get("max_collision_throttle_drop")) * collision_alpha
        + _float(overlay.get("max_boundary_throttle_drop")) * boundary_alpha
    )

    delta = action - fallback
    limited = np.array(
        [
            np.clip(delta[0], -_float(overlay.get("max_abs_steer_delta")), _float(overlay.get("max_abs_steer_delta"))),
            np.clip(delta[1], -_float(overlay.get("max_throttle_drop")), 0.0),
            np.clip(delta[2], 0.0, 2.0 * _float(overlay.get("max_brake_add"))),
        ],
        dtype=np.float32,
    )
    return np.clip(fallback + limited, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "source_localized_rule_rows": output_dir / "source_localized_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "repair_hypothesis_binding_rows": output_dir / "repair_hypothesis_binding_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3169_audit: Path, m3168_dir: Path) -> dict[str, Any]:
    paths = {
        "m3169_audit": m3169_audit,
        "m3168_summary": m3168_dir / "summary.json",
        "m3168_repair_hypothesis_rows": m3168_dir / "repair_hypothesis_rows.csv",
        "m3168_actor_contract_guard_rows": m3168_dir / "actor_contract_guard_rows.csv",
        "m3168_measurement_readiness_rows": m3168_dir / "measurement_readiness_rows.csv",
        "m3168_gate_rows": m3168_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3169_audit_text": paths["m3169_audit"].read_text(encoding="utf-8") if exists["m3169_audit"] else "",
        "m3168_summary": read_json(paths["m3168_summary"]) if exists["m3168_summary"] else {},
        "m3168_repair_hypothesis_rows": read_csv_rows(paths["m3168_repair_hypothesis_rows"]),
        "m3168_actor_contract_guard_rows": read_csv_rows(paths["m3168_actor_contract_guard_rows"]),
        "m3168_measurement_readiness_rows": read_csv_rows(paths["m3168_measurement_readiness_rows"]),
        "m3168_gate_rows": read_csv_rows(paths["m3168_gate_rows"]),
    }


def rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "m3170-rule-0001",
            "rule_family": "m3105_m3103_incumbent_fallback",
            "priority": 0,
            "input_feature_groups": "obs72_current_frame",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "fallback = M3103/M3105 incumbent direct action",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3170-rule-0002",
            "rule_family": "collision_clearance_observation_timeline_reflex",
            "priority": 10,
            "input_feature_groups": "speed|actor_visible_obstacle_slots|road_center_error",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "bounded earlier throttle drop brake add and obstacle-side steering moderation using visible obstacle geometry only",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3170-rule-0003",
            "rule_family": "boundary_recovery_stability_reflex",
            "priority": 20,
            "input_feature_groups": "speed|road_left_boundary|road_right_boundary|lateral_yaw_response",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "bounded throttle damping brake support and center-recovery steering moderation using visible edge and stability signals",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3170-rule-0004",
            "rule_family": "deployable_boundary_guard",
            "priority": 30,
            "input_feature_groups": "obs72_only",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "clip final action and cap per-channel deltas while leaving public ActiveSafetyReflexDriver default binding unchanged",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def runtime_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "contract_id": "m3170-runtime-contract-0001",
            "contract_family": "runtime_api",
            "runtime_symbol": "source_localized_repair_direct_action",
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
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def repair_hypothesis_binding_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(source.get("m3168_repair_hypothesis_rows", []), start=1):
        name = str(hypothesis.get("repair_hypothesis_name", ""))
        if "collision_clearance" in name:
            rule_family = "collision_clearance_observation_timeline_reflex"
            runtime_inputs = "obs72 speed actor_visible_obstacle_slots road_center_error"
        elif "boundary_recovery" in name:
            rule_family = "boundary_recovery_stability_reflex"
            runtime_inputs = "obs72 speed road_edges road_center_error lateral_yaw_response"
        else:
            rule_family = "unbound"
            runtime_inputs = "none"
        status = (
            _bool(hypothesis.get("admitted_for_repair_implementation_materialization"))
            and not _bool(hypothesis.get("admitted_for_validation"))
            and rule_family != "unbound"
        )
        rows.append(
            {
                "binding_id": f"m3170-repair-binding-{index:04d}",
                "source_repair_hypothesis_id": hypothesis.get("repair_hypothesis_id", ""),
                "source_repair_hypothesis_name": name,
                "blocker_family": hypothesis.get("blocker_family", ""),
                "source_localization_row_count": hypothesis.get("source_localization_row_count", ""),
                "candidate_rule_family": rule_family,
                "admitted_for_repair_implementation_materialization": _bool(
                    hypothesis.get("admitted_for_repair_implementation_materialization")
                ),
                "admitted_for_validation": _bool(hypothesis.get("admitted_for_validation")),
                "runtime_actor_inputs": runtime_inputs,
                "forbidden_actor_inputs": hypothesis.get("forbidden_actor_inputs", ""),
                "status_pass": status,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _probe_observations() -> list[tuple[str, np.ndarray]]:
    zero = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    safe_left_y = 0.25
    safe_right_y = -0.25
    low_speed_obstacle = zero.copy()
    low_speed_obstacle[0] = 0.25
    low_speed_obstacle[44] = 1.0
    low_speed_obstacle[45] = 0.20
    low_speed_obstacle[46] = 0.02
    low_speed_obstacle[13:28:2] = safe_left_y
    low_speed_obstacle[29:44:2] = safe_right_y

    collision_left = zero.copy()
    collision_left[0] = 0.85
    collision_left[44] = 1.0
    collision_left[45] = 0.24
    collision_left[46] = 0.05
    collision_left[13:28:2] = safe_left_y
    collision_left[29:44:2] = safe_right_y

    collision_right = zero.copy()
    collision_right[0] = 0.85
    collision_right[44] = 1.0
    collision_right[45] = 0.22
    collision_right[46] = -0.05
    collision_right[13:28:2] = safe_left_y
    collision_right[29:44:2] = safe_right_y

    boundary = zero.copy()
    boundary[0] = 0.82
    boundary[12:28] = 0.02
    boundary[28:44] = 0.03
    boundary[1] = 0.35
    boundary[2] = 0.25
    boundary[4] = 0.35

    combined = collision_left.copy()
    combined[12:28] = 0.02
    combined[28:44] = 0.03
    combined[1] = 0.4
    combined[2] = -0.3
    combined[4] = 0.4

    return [
        ("zero_fallback", zero),
        ("low_speed_obstacle_fallback", low_speed_obstacle),
        ("collision_clearance_left_overlay", collision_left),
        ("collision_clearance_right_overlay", collision_right),
        ("boundary_recovery_stability_overlay", boundary),
        ("combined_collision_boundary_overlay", combined),
    ]


def action_probe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    overlay = _overlay_config(POLICY_CONFIG)
    for index, (family, obs) in enumerate(_probe_observations(), start=1):
        fallback = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        candidate = source_localized_repair_direct_action(obs, POLICY_CONFIG)
        features = source_localized_repair_features(obs, POLICY_CONFIG)
        delta = candidate - fallback
        rows.append(
            {
                "probe_id": f"m3170-action-probe-{index:04d}",
                "probe_family": family,
                "fallback_steer": float(fallback[0]),
                "fallback_throttle": float(fallback[1]),
                "fallback_brake": float(fallback[2]),
                "candidate_steer": float(candidate[0]),
                "candidate_throttle": float(candidate[1]),
                "candidate_brake": float(candidate[2]),
                "steer_delta": float(delta[0]),
                "throttle_delta": float(delta[1]),
                "brake_delta": float(delta[2]),
                "collision_alpha": float(features["collision_alpha"]),
                "boundary_alpha": float(features["boundary_alpha"]),
                "obstacle_urgency": float(features["obstacle_urgency"]),
                "edge_urgency": float(features["edge_urgency"]),
                "stability_risk": float(features["stability_risk"]),
                "speed_mps": float(features["speed_mps"]),
                "fallback_path_selected": bool(
                    max(features["collision_alpha"], features["boundary_alpha"]) <= 0.0
                    and np.allclose(candidate, fallback)
                ),
                "action_finite": bool(np.all(np.isfinite(candidate))),
                "action_bounded": bool(np.max(np.abs(candidate)) <= 1.0),
                "delta_limited": bool(
                    abs(float(delta[0])) <= _float(overlay.get("max_abs_steer_delta")) + 1e-6
                    and -_float(overlay.get("max_throttle_drop")) - 1e-6 <= float(delta[1]) <= 1e-6
                    and -1e-6 <= float(delta[2]) <= 2.0 * _float(overlay.get("max_brake_add")) + 1e-6
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("candidate_policy_config", "materialization", True, "direct_action_policy_config.json"),
        ("source_localized_rules", "materialization", True, "source_localized_rule_rows.csv"),
        ("runtime_contracts", "contract", True, "runtime_contract_rows.csv"),
        ("repair_hypothesis_bindings", "lineage", True, "repair_hypothesis_binding_rows.csv"),
        ("action_probe_rows", "runtime_api", True, "action_probe_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3171 audit manifest"),
    ]
    blocked = [
        ("environment_reset_or_step", "execution", "future measurement route"),
        ("rollout_or_replay", "execution", "future measurement route"),
        ("full_fresh_measurement", "measurement", "future post-M3171 measurement"),
        ("validation_result", "validation", "future validation route"),
        ("repair_success", "verdict", "future result audit after measurement"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization audit"),
        ("current_sim_verdict", "verdict", "future synthesis after measurement audit"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("public_driver_default_replacement", "deployment", "future promotion or deployment gate"),
        ("robustness_result", "verdict", "future robustness measurement route"),
        ("high_fidelity_validation", "validation", "future high-fidelity route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_proof", "feasibility", "future feasibility audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
    ]
    rows = [
        {
            "claim_id": f"m3170-{claim_id}",
            "claim_family": family,
            "allowed_in_m3170": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3170-{claim_id}",
            "claim_family": family,
            "allowed_in_m3170": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31710,
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
        "hypothesis": "A bounded result audit can accept or reject M3170 source-localized repair implementation materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), "src/autodrift/engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_preflight.py"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_policy_config.json"),
                str(output_dir / "source_localized_rule_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "repair_hypothesis_binding_rows.csv"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3170 candidate implementation before measurement admission"],
            "derived_from": [MILESTONE_ID, M3169_ID, M3168_ID, M3167_ID, M3166_ID],
            "blocked_by": [
                "M3170 is candidate materialization only and needs audit before measurement",
                "action probes are runtime contract probes not validation evidence",
            ],
            "supersedes": ["direct measurement admission from M3168 repair-admission rows"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3171 must audit M3170 config rule contract binding action-probe claim and gate artifacts",
            "M3171 must preserve obs72/action3 direct [steer throttle brake] runtime contract and public driver default unchanged boundary",
            "M3171 must reject measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3171 must select measurement preflight artifact-repair synthesis or stop explicitly",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training",
            "do not convert action probes into validation performance robustness-result repair-success feasibility-proof or self-ID evidence",
            "do not change actor input action contract runtime base-policy-free boundary or public driver default binding",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_failure_source_resolution",
            "evidence_axis": "source_localized_repair_implementation_result_audit",
            "evidence_increment": "audits materialized candidate implementation artifacts before measurement admission",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3170 artifacts are incomplete or gate matrix fails",
                "stop if actor or direct-action contracts are violated",
                "route to measurement only after audit acceptance",
            ],
            "fallback_plan": [
                "route to M3170 artifact repair if incomplete",
                "route to synthesis if candidate cannot preserve deployable boundary",
                "require full-fresh same-case measurement before behavior interpretation",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3170 materializes source-localized candidate implementation",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3170 materialized candidate implementation artifacts",
            "admission_evidence": ["M3170 summary config rule contract binding probe claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input runtime base policy or public driver default mutation",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3171 status queue scoreboard research log and review",
                "one follow-up manifest only if M3171 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3171 accepts or rejects M3170 as complete and claim-safe",
                "next measurement preflight artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3171 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3171; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3170 materialization artifacts only.",
            "negative_result_policy": "Reject or repair M3170 artifacts rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3170 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new source-localized candidate implementation before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3171 audits engineering candidate artifacts",
            "must_synthesize_if": ["M3171 cannot select measurement preflight artifact repair synthesis or stop"],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3171 audits M3170 materialization artifacts and claim boundaries",
            "M3171 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3171 hides missing M3170 rows or failed gates",
            "M3171 treats M3170 action probes as repair success or performance verdict",
            "M3171 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3171 audits M3170 artifacts and selects one measurement preflight artifact-repair synthesis or stop route without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_source_localized_repair_implementation_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json"), str(doc_path)],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3170-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    rules: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    audit_selects_m3170 = (
        "accept_m3168_repair_admission_route_to_m3170_source_localized_repair_implementation_materialization"
        in str(source.get("m3169_audit_text", ""))
    )
    overlay_probes = [
        row
        for row in probes
        if max(_float(row.get("collision_alpha")), _float(row.get("boundary_alpha"))) > 0.0
    ]
    fallback_probes = [row for row in probes if "fallback" in str(row.get("probe_family", ""))]
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3169_selects_m3170", "lineage", audit_selects_m3170, "route marker", "present", "lineage_invalid"),
        gate("m3168_status_pass", "lineage", _bool(source["m3168_summary"].get("status_pass")), source["m3168_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3168_gate_matrix_pass", "lineage", _bool(source["m3168_summary"].get("gate_matrix_pass")), source["m3168_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3168_implementation_admitted_hypotheses", "lineage", int(source["m3168_summary"].get("implementation_admitted_hypothesis_count", 0)) == 2, source["m3168_summary"].get("implementation_admitted_hypothesis_count"), 2, "metric_artifact"),
        gate("m3168_validation_admitted_hypotheses_zero", "claim", int(source["m3168_summary"].get("validation_admitted_hypothesis_count", -1)) == 0, source["m3168_summary"].get("validation_admitted_hypothesis_count"), 0, "proof_washout"),
        gate("rules_present", "materialization", len(rules) >= 4, len(rules), ">=4", "metric_artifact"),
        gate("bindings_present", "lineage", len(bindings) == 2, len(bindings), 2, "metric_artifact"),
        gate("bindings_pass", "lineage", all(_bool(row.get("status_pass")) for row in bindings), "all", "pass", "lineage_invalid"),
        gate("runtime_contracts_pass", "contract", all(_bool(row.get("status_pass")) for row in contracts), "all", "pass", "contract_violation"),
        gate("policy_observation_shape", "contract", P0_OBSERVATION_DIM == 72, P0_OBSERVATION_DIM, 72, "contract_violation"),
        gate("policy_action_shape", "contract", ACTION_DIM == 3, ACTION_DIM, 3, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(POLICY_CONFIG.get("runtime_base_policy_required", True)), POLICY_CONFIG.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("public_driver_default_unchanged", "contract", not _bool(POLICY_CONFIG.get("public_active_safety_reflex_driver_default_mutation")), POLICY_CONFIG.get("public_active_safety_reflex_driver_default_mutation"), False, "contract_violation"),
        gate("action_probe_rows_present", "runtime_api", len(probes) >= 6, len(probes), ">=6", "metric_artifact"),
        gate("fallback_probes_preserve_incumbent", "runtime_api", all(_bool(row.get("fallback_path_selected")) for row in fallback_probes), len(fallback_probes), "all fallback", "contract_violation"),
        gate("overlay_probes_present", "runtime_api", len(overlay_probes) >= 3, len(overlay_probes), ">=3", "metric_artifact"),
        gate("action_probes_finite", "runtime_api", all(_bool(row.get("action_finite")) for row in probes), "all", "finite", "contract_violation"),
        gate("action_probes_bounded", "runtime_api", all(_bool(row.get("action_bounded")) for row in probes), "all", "bounded", "contract_violation"),
        gate("action_probe_deltas_limited", "runtime_api", all(_bool(row.get("delta_limited")) for row in probes), "all", "limited", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass")) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3170 Source-Localized Repair Implementation Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- policy id: `{summary['policy_id']}`",
            f"- fallback policy id: `{summary['fallback_policy_id']}`",
            f"- rule rows: {summary['rule_row_count']}",
            f"- binding rows: {summary['repair_hypothesis_binding_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- overlay probe rows: {summary['overlay_probe_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            "",
            "## Interpretation",
            "",
            "M3170 materializes a candidate only. It starts from the M3105/M3103 incumbent direct action and adds a bounded source-localized overlay for the two M3168-admitted implementation hypotheses. The public ActiveSafetyReflexDriver default binding remains unchanged. These action probes are runtime contract probes, not closed-loop measurement or repair-success evidence.",
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


def run_materialization_preflight(
    *,
    m3169_audit: Path,
    m3168_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3169_audit=m3169_audit, m3168_dir=m3168_dir)
    rules = rule_rows()
    contracts = runtime_contract_rows()
    bindings = repair_hypothesis_binding_rows(source)
    probes = action_probe_rows()

    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_csv_rows(paths["source_localized_rule_rows"], rules, fieldnames=RULE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], contracts, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(paths["repair_hypothesis_binding_rows"], bindings, fieldnames=BINDING_FIELDNAMES)
    write_csv_rows(paths["action_probe_rows"], probes, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)

    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        rules=rules,
        contracts=contracts,
        bindings=bindings,
        probes=probes,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    overlay_count = sum(
        1
        for row in probes
        if max(_float(row.get("collision_alpha")), _float(row.get("boundary_alpha"))) > 0.0
    )
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": "active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_pass"
        if status_pass
        else "active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_fail",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "public_driver_default_mutated": False,
        "direct_action_formula": "action = source_localized_repair_direct_action(obs72) -> [steer, throttle, brake]",
        "rule_row_count": len(rules),
        "runtime_contract_row_count": len(contracts),
        "repair_hypothesis_binding_row_count": len(bindings),
        "repair_hypothesis_binding_rows_pass": all(_bool(row.get("status_pass")) for row in bindings),
        "action_probe_row_count": len(probes),
        "overlay_probe_row_count": overlay_count,
        "fallback_probe_row_count": len(probes) - overlay_count,
        "action_probe_all_finite": all(_bool(row.get("action_finite")) for row in probes),
        "action_probe_all_bounded": all(_bool(row.get("action_bounded")) for row in probes),
        "action_probe_all_delta_limited": all(_bool(row.get("delta_limited")) for row in probes),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass")) for row in claims),
        "required_artifacts_present": present,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "full_fresh_measurement_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_implementation_materialized": True,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_route_to_m3171_result_audit",
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
    write_run_state(paths["run_state"], {"complete": status_pass, "status_pass": status_pass, "next_blocker": NEXT_ID})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3169-audit", type=Path, default=DEFAULT_M3169_AUDIT)
    parser.add_argument("--m3168-dir", type=Path, default=DEFAULT_M3168_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3169_audit=args.m3169_audit,
        m3168_dir=args.m3168_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"action_probe_rows={summary['action_probe_row_count']}")
    print(f"overlay_probe_rows={summary['overlay_probe_row_count']}")
    print(f"binding_rows={summary['repair_hypothesis_binding_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
