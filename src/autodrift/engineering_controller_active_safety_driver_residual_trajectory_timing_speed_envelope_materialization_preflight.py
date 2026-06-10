"""Materialize M3142 residual trajectory-timing speed-envelope candidate artifacts."""

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
    "m3142-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-materialization-preflight"
)
NEXT_ID = (
    "m3143-engineering-controller-active-safety-driver-residual-trajectory-timing-"
    "speed-envelope-materialization-result-audit"
)
M3141_ID = (
    "m3141-engineering-controller-active-safety-driver-m3105-residual-collision-"
    "offtrack-trajectory-timing-speed-envelope-synthesis"
)
M3139_ID = (
    "m3139-engineering-controller-active-safety-driver-m3105-incumbent-deployable-"
    "reflex-interface-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)

POLICY_ID = "m3142_residual_trajectory_timing_speed_envelope"

DEFAULT_M3141_SYNTHESIS = Path(f"docs/{M3141_ID}.md")
DEFAULT_M3139_DIR = Path(
    "runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_"
    "reflex_interface_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3142 Active Safety Driver residual trajectory-timing speed-envelope materialization "
    "only; artifacts may define an actor-visible obs72 to action3 [steer throttle brake] "
    "candidate that defaults to M3105/M3103 and only applies bounded early speed-envelope "
    "overlay under obstacle/edge/stability risk. No reset, step, rollout, replay, fitting, "
    "PPO, training, measurement, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, feasibility proof, or "
    "level3 self-identification"
)

POLICY_CONFIG: dict[str, Any] = deepcopy(V4_POLICY_CONFIG)
POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "repair_route": "residual_trajectory_timing_speed_envelope",
        "repair_scope": "materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "actor_observation_contract": "actor_visible_obs72_only",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
    }
)
POLICY_CONFIG["speed_envelope"] = {
    "enabled": True,
    "lookahead_m": 64.0,
    "lateral_window_m": 5.5,
    "speed_start_mps": 11.0,
    "speed_full_mps": 20.0,
    "min_obstacle_risk": 0.08,
    "min_edge_risk": 0.55,
    "min_stability_risk": 0.25,
    "speed_floor_preserve_below_mps": 8.0,
    "max_brake_add": 0.28,
    "max_throttle_drop": 0.30,
    "max_abs_steer_delta": 0.12,
    "stability_steer_damping": 0.18,
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
    "overlay_alpha",
    "obstacle_risk",
    "edge_risk",
    "stability_risk",
    "speed_mps",
    "fallback_path_selected",
    "action_finite",
    "action_bounded",
    "delta_limited",
    "claim_boundary",
]
REQUIREMENT_FIELDNAMES = [
    "requirement_id",
    "source_measurement_episode_id",
    "axis_id",
    "blocker_family",
    "envelope_status",
    "route_recommendation",
    "terminal_speed_mps",
    "terminal_min_clearance_margin_m",
    "final_10_mean_brake_physical",
    "final_10_mean_abs_steer",
    "max_obstacle_urgency_actor_visible",
    "max_edge_urgency_actor_visible",
    "required_design_response",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3142",
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


def _brake_to_physical(action_brake: float) -> float:
    return _clip01((action_brake + 1.0) / 2.0)


def _brake_from_physical(physical_brake: float) -> float:
    return -1.0 + 2.0 * _clip01(physical_brake)


def _envelope_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    return config.get("speed_envelope", POLICY_CONFIG["speed_envelope"])


def _early_obstacle_risk(observation: np.ndarray, config: Mapping[str, Any]) -> tuple[float, float]:
    obs = np.asarray(observation, dtype=np.float32)
    cfg = _envelope_config(config)
    lookahead = _float(cfg.get("lookahead_m"), 64.0)
    lateral_window = _float(cfg.get("lateral_window_m"), 5.5)
    best_risk = 0.0
    best_avoid_direction = 0.0
    for slot_index in range(4):
        base = 44 + slot_index * 7
        present = float(obs[base])
        x_body = float(obs[base + 1] * 80.0)
        y_body = float(obs[base + 2] * 20.0)
        if present <= 0.5 or x_body <= 0.0:
            continue
        lead = _clip01((lookahead - x_body) / max(lookahead, 1e-6))
        lateral_overlap = _clip01(1.0 - abs(y_body) / max(lateral_window, 1e-6))
        risk = lead * lateral_overlap
        if risk > best_risk:
            best_risk = risk
            best_avoid_direction = -1.0 if y_body >= 0.0 else 1.0
    return best_risk, best_avoid_direction


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


def speed_envelope_features(observation: np.ndarray, config: Mapping[str, Any]) -> dict[str, float]:
    obs = np.asarray(observation, dtype=np.float32)
    hard = _hard_safety_features(obs, config)
    env = _envelope_config(config)
    obstacle_risk, avoid_direction = _early_obstacle_risk(obs, config)
    edge_risk = hard["edge_urgency"]
    stability = _stability_risk(obs)
    speed = hard["vx_body"]
    speed_alpha = _clip01((speed - _float(env.get("speed_start_mps"))) / max(_float(env.get("speed_full_mps")) - _float(env.get("speed_start_mps")), 1e-6))
    obstacle_alpha = _clip01((obstacle_risk - _float(env.get("min_obstacle_risk"))) / max(1.0 - _float(env.get("min_obstacle_risk")), 1e-6))
    edge_alpha = _clip01((edge_risk - _float(env.get("min_edge_risk"))) / max(1.0 - _float(env.get("min_edge_risk")), 1e-6))
    stability_alpha = _clip01((stability - _float(env.get("min_stability_risk"))) / max(1.0 - _float(env.get("min_stability_risk")), 1e-6))
    overlay_alpha = speed_alpha * max(obstacle_alpha, edge_alpha, stability_alpha)
    if speed < _float(env.get("speed_floor_preserve_below_mps")):
        overlay_alpha = 0.0
    return {
        "speed_mps": speed,
        "obstacle_risk": obstacle_risk,
        "edge_risk": edge_risk,
        "stability_risk": stability,
        "obstacle_avoid_direction": avoid_direction,
        "overlay_alpha": _clip01(overlay_alpha),
    }


def residual_trajectory_timing_speed_envelope_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3142 direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    fallback = np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG), dtype=np.float32)
    features = speed_envelope_features(obs, cfg)
    alpha = features["overlay_alpha"]
    if alpha <= 0.0:
        return fallback.astype(np.float32)

    env = _envelope_config(cfg)
    action = fallback.copy()
    brake_physical = _brake_to_physical(float(action[2]))
    brake_physical = _clip01(brake_physical + _float(env.get("max_brake_add")) * alpha)
    action[2] = _brake_from_physical(brake_physical)
    action[1] = float(action[1]) - _float(env.get("max_throttle_drop")) * alpha

    steer_delta = _float(env.get("max_abs_steer_delta")) * alpha * features["obstacle_avoid_direction"]
    action[0] = float(action[0]) + steer_delta
    damping = _float(env.get("stability_steer_damping")) * alpha * _clip01(features["stability_risk"])
    action[0] *= 1.0 - damping

    delta = np.clip(action - fallback, [-_float(env.get("max_abs_steer_delta")), -_float(env.get("max_throttle_drop")), 0.0], [_float(env.get("max_abs_steer_delta")), 0.0, 2.0 * _float(env.get("max_brake_add"))])
    return np.clip(fallback + delta, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "speed_envelope_rule_rows": output_dir / "speed_envelope_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "residual_blocker_requirement_rows": output_dir / "residual_blocker_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3141_synthesis: Path, m3139_dir: Path, m3105_dir: Path) -> dict[str, Any]:
    paths = {
        "m3141_synthesis": m3141_synthesis,
        "m3139_summary": m3139_dir / "summary.json",
        "m3139_residual_blocker_rows": m3139_dir / "residual_blocker_rows.csv",
        "m3105_summary": m3105_dir / "summary.json",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3141_synthesis_text": paths["m3141_synthesis"].read_text(encoding="utf-8") if exists["m3141_synthesis"] else "",
        "m3139_summary": read_json(paths["m3139_summary"]) if exists["m3139_summary"] else {},
        "m3139_residual_blocker_rows": read_csv_rows(paths["m3139_residual_blocker_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
    }


def rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "m3142-speed-envelope-rule-0001",
            "rule_family": "m3105_fallback_default",
            "priority": 0,
            "input_feature_groups": "obs72_current_frame",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "fallback = M3103/M3105 incumbent action",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3142-speed-envelope-rule-0002",
            "rule_family": "early_obstacle_speed_envelope",
            "priority": 10,
            "input_feature_groups": "speed|actor_visible_obstacle_slots",
            "output_channels": "throttle|brake|steer",
            "formula_summary": "bounded early throttle suppression/brake add with small avoid-direction steer when speed and obstacle risk exceed thresholds",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3142-speed-envelope-rule-0003",
            "rule_family": "edge_stability_speed_envelope",
            "priority": 20,
            "input_feature_groups": "speed|road_edge|stability_current_frame",
            "output_channels": "throttle|brake|steer",
            "formula_summary": "bounded deceleration and steer damping under edge or stability risk without row labels",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "rule_id": "m3142-speed-envelope-rule-0004",
            "rule_family": "speed_floor_no_regression_guard",
            "priority": 30,
            "input_feature_groups": "speed",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "disable overlay below configured speed floor and cap per-channel deltas",
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
            "contract_id": "m3142-runtime-contract-0001",
            "contract_family": "runtime_api",
            "runtime_symbol": "residual_trajectory_timing_speed_envelope_action",
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
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def _probe_observations() -> list[tuple[str, np.ndarray]]:
    zero = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    low_speed = zero.copy()
    low_speed[0] = 0.25
    obstacle = zero.copy()
    obstacle[0] = 0.9
    obstacle[44] = 1.0
    obstacle[45] = 0.28
    obstacle[46] = 0.03
    edge = zero.copy()
    edge[0] = 0.9
    edge[12:28] = 0.02
    edge[28:44] = 0.03
    stability = zero.copy()
    stability[0] = 0.85
    stability[1] = 0.5
    stability[2] = 0.5
    stability[4] = 0.5
    combined = obstacle.copy()
    combined[1] = 0.4
    combined[12:28] = 0.02
    combined[28:44] = 0.03
    return [
        ("zero_fallback", zero),
        ("low_speed_fallback", low_speed),
        ("early_obstacle_overlay", obstacle),
        ("edge_overlay", edge),
        ("stability_overlay", stability),
        ("combined_overlay", combined),
    ]


def action_probe_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    env = _envelope_config(POLICY_CONFIG)
    for index, (family, obs) in enumerate(_probe_observations(), start=1):
        fallback = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        candidate = residual_trajectory_timing_speed_envelope_action(obs, POLICY_CONFIG)
        features = speed_envelope_features(obs, POLICY_CONFIG)
        delta = candidate - fallback
        rows.append(
            {
                "probe_id": f"m3142-action-probe-{index:04d}",
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
                "overlay_alpha": float(features["overlay_alpha"]),
                "obstacle_risk": float(features["obstacle_risk"]),
                "edge_risk": float(features["edge_risk"]),
                "stability_risk": float(features["stability_risk"]),
                "speed_mps": float(features["speed_mps"]),
                "fallback_path_selected": bool(features["overlay_alpha"] <= 0.0 and np.allclose(candidate, fallback)),
                "action_finite": bool(np.all(np.isfinite(candidate))),
                "action_bounded": bool(np.max(np.abs(candidate)) <= 1.0),
                "delta_limited": bool(
                    abs(float(delta[0])) <= _float(env.get("max_abs_steer_delta")) + 1e-6
                    and -_float(env.get("max_throttle_drop")) - 1e-6 <= float(delta[1]) <= 1e-6
                    and -1e-6 <= float(delta[2]) <= 2.0 * _float(env.get("max_brake_add")) + 1e-6
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def requirement_rows(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for blocker in blockers:
        rows.append(
            {
                "requirement_id": f"m3142-residual-requirement-{len(rows) + 1:04d}",
                "source_measurement_episode_id": blocker.get("source_measurement_episode_id", ""),
                "axis_id": blocker.get("axis_id", ""),
                "blocker_family": blocker.get("blocker_family", ""),
                "envelope_status": "",
                "route_recommendation": "early_speed_envelope_before_terminal_authority_exhaustion",
                "terminal_speed_mps": blocker.get("speed_mean", ""),
                "terminal_min_clearance_margin_m": blocker.get("min_clearance_margin", ""),
                "final_10_mean_brake_physical": "",
                "final_10_mean_abs_steer": "",
                "max_obstacle_urgency_actor_visible": "",
                "max_edge_urgency_actor_visible": "",
                "required_design_response": "bounded early throttle suppression and brake support while preserving M3105 fallback and speed-floor guard",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("candidate_policy_config", "materialization", True, "direct_action_policy_config.json"),
        ("action_probe_rows", "runtime_api", True, "action_probe_rows.csv"),
        ("residual_requirements", "diagnostic", True, "residual_blocker_requirement_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3143 audit manifest"),
    ]
    blocked = [
        ("measurement_result", "measurement", "future M3144 full-fresh measurement"),
        ("validation_result", "validation", "future validation route"),
        ("repair_success", "verdict", "future result audit"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization audit"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("robustness_result", "verdict", "future robustness route"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_proof", "feasibility", "future feasibility audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
    ]
    rows = [
        {
            "claim_id": f"m3142-{claim_id}",
            "claim_family": family,
            "allowed_in_m3142": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3142-{claim_id}",
            "claim_family": family,
            "allowed_in_m3142": False,
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
        "priority": 31430,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": ["contract_violation", "lineage_invalid", "metric_artifact", "scenario_sampling_failure", "behavior_regression", "objective_overfit", "proof_washout", "seed_fragility"],
        "hypothesis": "A bounded result audit can accept or reject the M3142 residual trajectory-timing speed-envelope materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), "src/autodrift/engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight.py"],
            "parent_dataset": [str(output_dir / name) for name in ["summary.json", "direct_action_policy_config.json", "speed_envelope_rule_rows.csv", "runtime_contract_rows.csv", "action_probe_rows.csv", "residual_blocker_requirement_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3142 speed-envelope candidate before any full-fresh measurement"],
            "derived_from": [MILESTONE_ID, M3141_ID, M3139_ID, M3105_ID],
            "blocked_by": ["M3142 is only materialized and needs audit before measurement", "M3105 residual blockers remain unsolved until full-fresh measurement proves otherwise"],
            "supersedes": ["blind terminal direct-gain continuation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3143 must audit M3142 config rule contract probe requirement claim and gate artifacts",
            "M3143 must preserve obs72/action3 direct [steer throttle brake] runtime contract and M3105 fallback",
            "M3143 must reject measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": ["do not rerun tune expand rank promote validation or mutate checkpoints", "do not convert action probes into validation or repair-success evidence", "do not change actor input or action contract"],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_trajectory_timing_speed_envelope",
            "evidence_axis": "speed_envelope_materialization_result_audit",
            "evidence_increment": "audits the materialized speed-envelope candidate before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": ["stop if M3142 artifacts are incomplete", "stop if action probes violate bounds or fallback contract", "route to full-fresh measurement only after audit acceptance"],
            "fallback_plan": ["repair M3142 artifacts if incomplete", "return to M3105 incumbent if contract-unsafe", "require full-fresh measurement before behavior interpretation"],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3142 materializes speed-envelope candidate",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3142 materialized speed-envelope candidate artifacts",
            "admission_evidence": ["M3142 summary gate rule contract action probe and claim artifacts"],
            "blocked_shortcuts": ["no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim", "no checkpoint mutation profile tuning or promotion", "no hidden oracle target TTC source route outcome progress verdict actor input"],
            "allowed_updates": [f"docs/{NEXT_ID}.md", f"docs/reviews/{NEXT_ID}.md", f"experiments/reviews/{NEXT_ID}.json", "M3143 status queue scoreboard research log and review"],
            "next_stage_criteria": ["M3143 accepts or rejects M3142 as complete and claim-safe", "M3143 selects whether to run full-fresh measurement"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3143 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3143; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3142 materialization artifacts only.",
            "negative_result_policy": "Preserve engineering evidence and route to full-fresh measurement or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": ["M3142 artifact completeness and claim-safety audit"],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new early speed-envelope candidate rather than repeating terminal gain overlays",
            "paper_verdict_delta": "paper and self-ID remain diagnostic",
            "must_synthesize_if": ["M3143 cannot select audit acceptance or stop"],
        },
        "success_criteria": [f"docs/{NEXT_ID}.md exists", "M3143 audits M3142 without overclaiming"],
        "failure_criteria": ["M3143 hides missing artifacts", "M3143 treats materialization as measurement"],
        "decision_rule": "Pass only if M3143 audits M3142 artifacts and claim boundaries before any measurement.",
        "commands": [{"name": "active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {"gate_id": f"m3142-{gate_id}", "gate_family": family, "status_pass": bool(status), "observed": observed, "expected": expected, "failure_type": failure_type, "claim_boundary": CLAIM_SCOPE}


def gate_matrix_rows(*, source: Mapping[str, Any], rules: list[dict[str, Any]], contracts: list[dict[str, Any]], probes: list[dict[str, Any]], requirements: list[dict[str, Any]], claims: list[dict[str, Any]], required_artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    synthesis_selects = "pivot_to_m3142_residual_trajectory_timing_speed_envelope_materialization" in str(source.get("m3141_synthesis_text", ""))
    fallback_probes = [row for row in probes if "fallback" in str(row.get("probe_family", ""))]
    overlay_probes = [row for row in probes if _float(row.get("overlay_alpha")) > 0.0]
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3141_selects_m3142", "lineage", synthesis_selects, "route marker", "present", "lineage_invalid"),
        gate("m3139_status_pass", "lineage", _bool(source["m3139_summary"].get("status_pass", False)), source["m3139_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("policy_observation_shape", "contract", int(POLICY_CONFIG.get("observation_shape", P0_OBSERVATION_DIM)) == P0_OBSERVATION_DIM, POLICY_CONFIG.get("observation_shape", P0_OBSERVATION_DIM), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", int(POLICY_CONFIG.get("action_shape", ACTION_DIM)) == ACTION_DIM, POLICY_CONFIG.get("action_shape", ACTION_DIM), ACTION_DIM, "contract_violation"),
        gate("fallback_policy_id", "contract", POLICY_CONFIG.get("fallback_policy_id") == M3103_POLICY_ID, POLICY_CONFIG.get("fallback_policy_id"), M3103_POLICY_ID, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(POLICY_CONFIG.get("runtime_base_policy_required", True)), POLICY_CONFIG.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("rules_present", "materialization", len(rules) >= 4, len(rules), ">=4", "metric_artifact"),
        gate("runtime_contracts_pass", "contract", all(_bool(row.get("status_pass", False)) for row in contracts), "all", "pass", "contract_violation"),
        gate("action_probe_rows_present", "runtime_api", len(probes) >= 6, len(probes), ">=6", "metric_artifact"),
        gate("fallback_probes_preserve_m3105_action", "runtime_api", all(_bool(row.get("fallback_path_selected", False)) for row in fallback_probes), len(fallback_probes), "all fallback", "contract_violation"),
        gate("overlay_probes_present", "runtime_api", len(overlay_probes) >= 3, len(overlay_probes), ">=3", "metric_artifact"),
        gate("action_probes_finite", "runtime_api", all(_bool(row.get("action_finite", False)) for row in probes), "all", "finite", "contract_violation"),
        gate("action_probes_bounded", "runtime_api", all(_bool(row.get("action_bounded", False)) for row in probes), "all", "bounded", "contract_violation"),
        gate("action_probe_deltas_limited", "runtime_api", all(_bool(row.get("delta_limited", False)) for row in probes), "all", "limited", "contract_violation"),
        gate("residual_requirements_present", "diagnostic", len(requirements) == 7, len(requirements), 7, "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3142 Residual Trajectory-Timing Speed-Envelope Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- policy id: `{summary['policy_id']}`",
            f"- fallback policy id: `{summary['fallback_policy_id']}`",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- overlay probe rows: {summary['overlay_probe_row_count']}",
            f"- residual requirement rows: {summary['residual_requirement_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3142 materializes a candidate only. It keeps M3105/M3103 as the default action and adds a bounded early speed-envelope overlay under actor-visible obstacle, edge, and stability risk. It is not measured repair evidence; full-fresh measurement and audit are required before behavior interpretation.",
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


def run_materialization_preflight(*, m3141_synthesis: Path, m3139_dir: Path, m3105_dir: Path, output_dir: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3141_synthesis=m3141_synthesis, m3139_dir=m3139_dir, m3105_dir=m3105_dir)
    rules = rule_rows()
    contracts = runtime_contract_rows()
    probes = action_probe_rows()
    requirements = requirement_rows(source["m3139_residual_blocker_rows"])
    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_csv_rows(paths["speed_envelope_rule_rows"], rules, fieldnames=RULE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], contracts, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(paths["action_probe_rows"], probes, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_csv_rows(paths["residual_blocker_requirement_rows"], requirements, fieldnames=REQUIREMENT_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(source=source, rules=rules, contracts=contracts, probes=probes, requirements=requirements, claims=claims, required_artifacts_present=present, follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    overlay_count = sum(1 for row in probes if _float(row.get("overlay_alpha")) > 0.0)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": "active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_pass" if status_pass else "active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_fail",
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
        "direct_action_formula": "action = residual_trajectory_timing_speed_envelope_action(obs72) -> [steer, throttle, brake]",
        "rule_row_count": len(rules),
        "runtime_contract_row_count": len(contracts),
        "action_probe_row_count": len(probes),
        "overlay_probe_row_count": overlay_count,
        "fallback_probe_row_count": len(probes) - overlay_count,
        "action_probe_all_finite": all(_bool(row.get("action_finite", False)) for row in probes),
        "action_probe_all_bounded": all(_bool(row.get("action_bounded", False)) for row in probes),
        "action_probe_all_delta_limited": all(_bool(row.get("delta_limited", False)) for row in probes),
        "residual_requirement_row_count": len(requirements),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "required_artifacts_present": present,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_route_to_m3143_result_audit",
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
    parser.add_argument("--m3141-synthesis", type=Path, default=DEFAULT_M3141_SYNTHESIS)
    parser.add_argument("--m3139-dir", type=Path, default=DEFAULT_M3139_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(m3141_synthesis=args.m3141_synthesis, m3139_dir=args.m3139_dir, m3105_dir=args.m3105_dir, output_dir=args.output_dir, doc_path=args.doc_path, follow_up_manifest=args.follow_up_manifest)
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"action_probe_rows={summary['action_probe_row_count']}")
    print(f"overlay_probe_rows={summary['overlay_probe_row_count']}")
    print(f"residual_requirements={summary['residual_requirement_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
