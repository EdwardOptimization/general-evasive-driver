"""Materialize M3118 residual trajectory-authority/stability-recovery repair artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
import autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight as m3110
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-"
    "stability-recovery-repair-materialization-preflight"
)
NEXT_ID = (
    "m3119-engineering-controller-active-safety-driver-residual-trajectory-authority-"
    "stability-recovery-repair-materialization-result-audit"
)
M3117_ID = "m3117-engineering-controller-active-safety-driver-residual-action-influence-repair-synthesis"
M3115_ID = (
    "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-"
    "influence-trace-materialization-preflight"
)
POLICY_ID = "m3118_residual_trajectory_authority_stability_recovery_repair"

DEFAULT_M3117_SYNTHESIS = Path(f"docs/{M3117_ID}.md")
DEFAULT_M3115_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_"
    "influence_trace_materialization_preflight"
)
DEFAULT_M3112_DIR = Path(
    "runs/m3112_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3110_DIR = Path(
    "runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3118_engineering_controller_active_safety_driver_residual_trajectory_authority_"
    "stability_recovery_repair_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3118 Active Safety Driver residual trajectory-authority and stability-recovery "
    "repair materialization only; artifacts may define obs72 to direct action3 "
    "[steer throttle brake] rules, config, trace-derived requirements, actor-input "
    "exclusion, claim, gate, doc, and M3119 audit manifest. No reset, step, rollout, "
    "replay, fitting, PPO, training, measurement, validation, ranking, winner selection, "
    "checkpoint mutation, checkpoint promotion, driver-performance verdict, current-sim "
    "verdict, repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

RULE_FIELDNAMES = [
    "rule_id",
    "rule_family",
    "priority",
    "input_feature_groups",
    "output_channels",
    "formula_summary",
    "default_gain",
    "gain_lower_bound",
    "gain_upper_bound",
    "enabled_by_default",
    "runtime_base_policy_required",
    "direct_action_output",
    "hidden_oracle_actor_input_required",
    "claim_boundary",
]
REQUIREMENT_FIELDNAMES = [
    "requirement_id",
    "source_trace_episode_id",
    "source_measurement_episode_id",
    "axis_id",
    "terminal_termination_reason",
    "primary_diagnostic_label",
    "trace_step_count",
    "max_obstacle_urgency_actor_visible",
    "max_edge_urgency_actor_visible",
    "final_10_mean_brake_physical",
    "final_10_mean_abs_steer",
    "action_saturation_fraction",
    "required_rule_families",
    "preserves_speed_floor",
    "actor_visible_feature_groups",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "status_pass",
    "claim_boundary",
]
EXCLUSION_FIELDNAMES = [
    "exclusion_id",
    "actor_input_family",
    "forbidden",
    "materialized_in_actor_input",
    "status_pass",
    "rationale",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3118",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]

M3118_POLICY_CONFIG: dict[str, Any] = deepcopy(m3110.M3110_POLICY_CONFIG)
M3118_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "repair_route": "residual_trajectory_authority_stability_recovery_repair",
        "repair_scope": "materialization_only_no_measurement_claim",
        "output_components": list(m3110.ACTION_COMPONENTS),
        "output_semantics": m3110.OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
    }
)
M3118_POLICY_CONFIG["gains"].update(
    {
        "early_obstacle_corridor_steer": 0.24,
        "early_obstacle_brake": 0.22,
        "early_obstacle_throttle_suppression": 0.16,
        "stability_centering_steer": 0.18,
        "stability_steer_authority_release": 0.32,
        "stability_brake_support": 0.16,
        "stability_throttle_suppression": 0.14,
    }
)
M3118_POLICY_CONFIG["thresholds"].update(
    {
        "fallback_base_policy_id": m3110.POLICY_ID,
        "m3117_selected_mechanism": "early_trajectory_authority_and_stability_recovery_allocation",
        "early_obstacle_lookahead_m": 48.0,
        "early_obstacle_lateral_window_m": 5.5,
        "early_obstacle_speed_mps": 12.0,
        "early_obstacle_min_risk": 0.04,
        "stability_beta_abs_trigger": 0.35,
        "stability_yaw_rate_trigger": 1.0,
        "stability_edge_urgency_trigger": 0.70,
        "stability_steer_limit": 0.82,
        "speed_floor_preserve_below_mps": 7.5,
        "residual_requirement_families": [
            "early_obstacle_corridor_commitment",
            "brake_throttle_timing",
            "stability_biased_steering_allocation",
            "speed_floor_preservation",
            "deployable_actor_boundary",
            "claim_boundary_audit",
        ],
    }
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _config_value(config: Mapping[str, Any], section: str, key: str) -> float:
    default = _float(M3118_POLICY_CONFIG[section][key])
    return _float(config.get(section, {}).get(key), default)


def _brake_to_physical(action_brake: float) -> float:
    return _clip01((action_brake + 1.0) / 2.0)


def _brake_from_physical(physical_brake: float) -> float:
    return -1.0 + 2.0 * _clip01(physical_brake)


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _early_obstacle_features(observation: np.ndarray, config: Mapping[str, Any]) -> dict[str, float]:
    obs = np.asarray(observation, dtype=np.float32)
    lookahead = _config_value(config, "thresholds", "early_obstacle_lookahead_m")
    lateral_window = _config_value(config, "thresholds", "early_obstacle_lateral_window_m")
    best_risk = 0.0
    best_avoid_direction = 0.0
    best_x = float("nan")
    best_y = float("nan")
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
            best_x = x_body
            best_y = y_body
    return {
        "early_obstacle_risk": best_risk,
        "early_obstacle_avoid_direction": best_avoid_direction,
        "early_obstacle_x_m": best_x,
        "early_obstacle_y_m": best_y,
    }


def residual_trajectory_authority_stability_recovery_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3118 direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg: Mapping[str, Any] = config or M3118_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    action = np.asarray(m3110.residual_collision_offtrack_actor_visible_direct_action(obs, m3110.M3110_POLICY_CONFIG), dtype=np.float32).copy()
    hard = m3110.v4_hard_safety_features(obs, cfg)
    early = _early_obstacle_features(obs, cfg)
    gains = cfg.get("gains", {})

    speed = float(hard["vx_body"])
    speed_risk = _clip01((speed - _config_value(cfg, "thresholds", "early_obstacle_speed_mps")) / 8.0)
    early_risk = speed_risk * _clip01(early["early_obstacle_risk"])
    if early_risk >= _config_value(cfg, "thresholds", "early_obstacle_min_risk"):
        action[0] += _float(gains.get("early_obstacle_corridor_steer")) * early["early_obstacle_avoid_direction"] * early_risk
        brake_physical = _brake_to_physical(float(action[2]))
        brake_physical += _float(gains.get("early_obstacle_brake")) * early_risk
        action[2] = _brake_from_physical(brake_physical)
        if speed > _config_value(cfg, "thresholds", "speed_floor_preserve_below_mps"):
            action[1] -= _float(gains.get("early_obstacle_throttle_suppression")) * early_risk

    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    steer_rate = float(obs[6])
    beta_risk = _clip01((abs(vy_body) / max(speed, 1.0) - _config_value(cfg, "thresholds", "stability_beta_abs_trigger")) / 0.45)
    yaw_risk = _clip01((abs(yaw_rate) - _config_value(cfg, "thresholds", "stability_yaw_rate_trigger")) / 2.0)
    response_risk = (beta_risk + yaw_risk + _clip01(abs(ay_body) / 10.0) + _clip01(abs(steer_rate))) / 4.0
    edge_excess = _clip01(
        (float(hard["edge_urgency"]) - _config_value(cfg, "thresholds", "stability_edge_urgency_trigger"))
        / max(1.0 - _config_value(cfg, "thresholds", "stability_edge_urgency_trigger"), 1e-6)
    )
    stability_edge_risk = edge_excess * response_risk * speed_risk
    if stability_edge_risk > 0.0:
        steer_limit = _config_value(cfg, "thresholds", "stability_steer_limit")
        release = _float(gains.get("stability_steer_authority_release")) * stability_edge_risk
        action[0] = float(action[0]) * (1.0 - release)
        action[0] += _float(gains.get("stability_centering_steer")) * float(hard["road_center_error"]) * edge_excess * (1.0 - response_risk)
        action[0] = float(np.clip(action[0], -steer_limit, steer_limit))
        brake_physical = _brake_to_physical(float(action[2]))
        brake_physical += _float(gains.get("stability_brake_support")) * stability_edge_risk
        action[2] = _brake_from_physical(brake_physical)
        if speed > _config_value(cfg, "thresholds", "speed_floor_preserve_below_mps"):
            action[1] -= _float(gains.get("stability_throttle_suppression")) * stability_edge_risk

    return np.clip(action, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "safety_reflex_rule_rows": output_dir / "safety_reflex_rule_rows.csv",
        "residual_trace_requirement_rows": output_dir / "residual_trace_requirement_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3117_synthesis: Path, m3115_dir: Path, m3112_dir: Path, m3110_dir: Path) -> dict[str, Any]:
    paths = {
        "m3117_synthesis": m3117_synthesis,
        "m3115_summary": m3115_dir / "summary.json",
        "m3115_action_influence_rows": m3115_dir / "residual_action_influence_rows.csv",
        "m3115_step_trace_rows": m3115_dir / "residual_step_trace_rows.csv",
        "m3115_gate_rows": m3115_dir / "gate_matrix.csv",
        "m3112_summary": m3112_dir / "summary.json",
        "m3112_measurement_rows": m3112_dir / "measurement_episode_rows.csv",
        "m3110_summary": m3110_dir / "summary.json",
        "m3110_policy_config": m3110_dir / "direct_action_policy_config.json",
        "m3110_gate_rows": m3110_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3117_synthesis_text": paths["m3117_synthesis"].read_text(encoding="utf-8") if exists["m3117_synthesis"] else "",
        "m3115_summary": read_json(paths["m3115_summary"]) if exists["m3115_summary"] else {},
        "m3115_action_influence_rows": read_csv_rows(paths["m3115_action_influence_rows"]),
        "m3115_step_trace_rows": read_csv_rows(paths["m3115_step_trace_rows"]),
        "m3115_gate_rows": read_csv_rows(paths["m3115_gate_rows"]),
        "m3112_summary": read_json(paths["m3112_summary"]) if exists["m3112_summary"] else {},
        "m3112_measurement_rows": read_csv_rows(paths["m3112_measurement_rows"]),
        "m3110_summary": read_json(paths["m3110_summary"]) if exists["m3110_summary"] else {},
        "m3110_policy_config": read_json(paths["m3110_policy_config"]) if exists["m3110_policy_config"] else {},
        "m3110_gate_rows": read_csv_rows(paths["m3110_gate_rows"]),
    }


def build_rule_rows() -> list[dict[str, Any]]:
    gains = M3118_POLICY_CONFIG["gains"]
    specs = [
        (
            "m3118-rule-m3110-fallback-base",
            "m3110_residual_repair_fallback_base",
            "p0",
            "ego_response;road_boundaries;obstacle_slots",
            "steer;throttle;brake",
            "start from the M3110 residual collision/offtrack actor-visible direct-action function",
            "not_applicable",
            -1.0,
            1.0,
        ),
        (
            "m3118-rule-early-obstacle-corridor-commitment",
            "early_obstacle_corridor_commitment",
            "p0",
            "obstacle_slots;ego_speed;road_boundaries",
            "steer;brake;throttle",
            "use actor-visible obstacle slot geometry before high terminal urgency to commit lateral corridor and braking",
            "early_obstacle_corridor_steer",
            0.0,
            0.4,
        ),
        (
            "m3118-rule-brake-throttle-timing",
            "brake_throttle_timing",
            "p0",
            "obstacle_slots;ego_speed",
            "brake;throttle",
            "raise physical brake and suppress throttle from early visible obstacle risk while preserving speed-floor guard",
            "early_obstacle_brake",
            0.0,
            0.35,
        ),
        (
            "m3118-rule-stability-biased-steering-allocation",
            "stability_biased_steering_allocation",
            "p0",
            "ego_response;road_boundaries",
            "steer;brake;throttle",
            "release steering saturation and add stability support when edge urgency and sideslip response risk coexist",
            "stability_steer_authority_release",
            0.0,
            0.5,
        ),
        (
            "m3118-rule-speed-floor-preservation",
            "speed_floor_preservation",
            "p0",
            "ego_speed;obstacle_slots;road_boundaries",
            "throttle;brake",
            "forbid new throttle suppression below the M3110 speed-floor preserve threshold",
            "speed_floor_preserve_below_mps",
            6.0,
            9.0,
        ),
        (
            "m3118-rule-claim-boundary",
            "claim_boundary_audit",
            "p0",
            "artifact_metadata_only",
            "none",
            "materialization is not measurement validation ranking repair-success or performance evidence",
            "not_applicable",
            0.0,
            0.0,
        ),
    ]
    return [
        {
            "rule_id": rule_id,
            "rule_family": family,
            "priority": priority,
            "input_feature_groups": inputs,
            "output_channels": outputs,
            "formula_summary": summary,
            "default_gain": gains.get(gain_key, M3118_POLICY_CONFIG["thresholds"].get(gain_key, gain_key)),
            "gain_lower_bound": low,
            "gain_upper_bound": high,
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "direct_action_output": True,
            "hidden_oracle_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for rule_id, family, priority, inputs, outputs, summary, gain_key, low, high in specs
    ]


def residual_trace_requirement_rows(influence_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(influence_rows, start=1):
        label = str(row.get("primary_diagnostic_label", ""))
        if label == "collision_action_present_but_clearance_unresolved":
            families = "early_obstacle_corridor_commitment;brake_throttle_timing;speed_floor_preservation"
        elif label == "offtrack_stability_recovery_limited":
            families = "stability_biased_steering_allocation;speed_floor_preservation"
        else:
            families = "artifact_repair_or_stop"
        rows.append(
            {
                "requirement_id": f"m3118-trace-requirement-{index:04d}",
                "source_trace_episode_id": row.get("trace_episode_id", ""),
                "source_measurement_episode_id": row.get("source_measurement_episode_id", ""),
                "axis_id": row.get("axis_id", ""),
                "terminal_termination_reason": row.get("terminal_termination_reason", ""),
                "primary_diagnostic_label": label,
                "trace_step_count": row.get("trace_step_count", ""),
                "max_obstacle_urgency_actor_visible": row.get("max_obstacle_urgency_actor_visible", ""),
                "max_edge_urgency_actor_visible": row.get("max_edge_urgency_actor_visible", ""),
                "final_10_mean_brake_physical": row.get("final_10_mean_brake_physical", ""),
                "final_10_mean_abs_steer": row.get("final_10_mean_abs_steer", ""),
                "action_saturation_fraction": row.get("action_saturation_fraction", ""),
                "required_rule_families": families,
                "preserves_speed_floor": True,
                "actor_visible_feature_groups": "ego_response;road_boundaries;obstacle_slots",
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "status_pass": bool(families != "artifact_repair_or_stop"),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def actor_input_exclusion_rows() -> list[dict[str, Any]]:
    excluded = [
        ("hidden_oracle", "hidden dynamics, hidden friction, hidden feasibility, and post-hoc labels"),
        ("ttc", "model-derived time-to-collision shortcuts"),
        ("target_labels", "target intervention labels"),
        ("source_labels", "source row identity labels"),
        ("route_labels", "route or branch labels"),
        ("outcome_labels", "future success/collision/offtrack outcome labels"),
        ("success_progress_labels", "success progress labels"),
        ("verdict_labels", "validation, ranking, or winner verdict labels"),
        ("runtime_base_policy", "runtime dependency on a base policy output"),
        ("checkpoint_model", "checkpoint model or recurrent hidden state dependency"),
    ]
    return [
        {
            "exclusion_id": f"m3118-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(excluded, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("direct_action_policy_config", "materialization", True, "direct_action_policy_config.json"),
        ("rule_rows", "materialization", True, "safety_reflex_rule_rows.csv"),
        ("trace_requirement_rows", "materialization", True, "residual_trace_requirement_rows.csv"),
        ("actor_input_exclusion_rows", "contract", True, "actor_input_exclusion_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3119 audit manifest"),
    ]
    blocked = [
        ("measurement_result", "measurement", "future measurement route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future measurement and audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
    ]
    rows = [
        {
            "claim_id": f"m3118-{claim_id}",
            "claim_family": family,
            "allowed_in_m3118": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3118-{claim_id}",
            "claim_family": family,
            "allowed_in_m3118": False,
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
        "priority": 31140,
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
        "hypothesis": "A bounded result audit can accept or reject the M3118 residual trajectory-authority and stability-recovery repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "safety_reflex_rule_rows.csv"),
                str(output_dir / "residual_trace_requirement_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3118 materialization before any measurement route"],
            "derived_from": [MILESTONE_ID, M3117_ID, M3115_ID],
            "blocked_by": [
                "M3118 materialization requires audit before execution",
                "materialized rules are not repair-success or performance evidence",
            ],
            "supersedes": ["direct execution of M3118 without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3119 must audit M3118 config rule requirement exclusion claim and gate artifacts",
            "M3119 must preserve obs72/action3 direct [steer throttle brake] runtime contract",
            "M3119 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3119 must select exactly one next measurement artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3118 materialization into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_step_action_influence_diagnosis",
            "evidence_axis": "residual_trajectory_authority_stability_recovery_repair_result_audit",
            "evidence_increment": "audits M3118 materialization artifacts before any measurement",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3118 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "route to measurement only after M3119 accepts artifacts as complete and claim-safe",
            ],
            "fallback_plan": [
                "route to M3118 artifact repair if artifacts are incomplete or contract-unsafe",
                "route to stop if the materialized mechanism is not representable within deployable obs72/action3 constraints",
                "route to full-fresh measurement only if M3119 accepts materialization",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3118 completes materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3118 materialization artifacts",
            "admission_evidence": ["M3118 summary gate matrix config rule requirement exclusion and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3119 status queue scoreboard research log and review",
                "one follow-up manifest only if M3119 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3119 accepts or rejects M3118 as complete and claim-safe",
                "M3119 selects measurement artifact-repair synthesis or stop route explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3119 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3119; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3118 materialization artifacts only.",
            "negative_result_policy": "Preserve materialization evidence and route to engineering measurement or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3118 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a mechanism-specific materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3119 audits engineering materialization evidence",
            "must_synthesize_if": [
                "M3119 cannot accept M3118 as complete and claim-safe",
                "M3119 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3119 cannot select measurement artifact-repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3119 audits M3118 row counts gates actor contract and claim boundaries",
            "M3119 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3119 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3119 hides M3118 missing artifacts",
            "M3119 treats M3118 materialization as validation repair-success or performance verdict",
            "M3119 changes actor input or action contract",
            "M3119 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3119 audits M3118 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_residual_trajectory_authority_stability_recovery_repair_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3118-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3117_synthesis_text", ""))
    sample_zero = residual_trajectory_authority_stability_recovery_direct_action(
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        M3118_POLICY_CONFIG,
    )
    obstacle_probe = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obstacle_probe[0] = 0.85
    obstacle_probe[44] = 1.0
    obstacle_probe[45] = 0.30
    obstacle_probe[46] = -0.05
    obstacle_probe[49] = 0.20
    obstacle_action = residual_trajectory_authority_stability_recovery_direct_action(obstacle_probe, M3118_POLICY_CONFIG)
    labels = Counter(str(row.get("primary_diagnostic_label", "")) for row in source.get("m3115_action_influence_rows", []))
    config = M3118_POLICY_CONFIG
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3117_selects_m3118", "lineage", "route_to_m3118_residual_trajectory_authority_stability_recovery_repair_materialization" in synthesis_text, "M3118 route marker", "present", "lineage_invalid"),
        gate("m3115_status_pass", "lineage", _bool(source["m3115_summary"].get("status_pass", False)), source["m3115_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3115_gate_matrix_pass", "lineage", _bool(source["m3115_summary"].get("gate_matrix_pass", False)), source["m3115_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3110_status_pass", "lineage", _bool(source["m3110_summary"].get("status_pass", False)), source["m3110_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3110_policy_config_status", "lineage", str(source["m3110_policy_config"].get("policy_id", "")) == m3110.POLICY_ID, source["m3110_policy_config"].get("policy_id"), m3110.POLICY_ID, "lineage_invalid"),
        gate("policy_observation_shape", "contract", int(config.get("observation_shape", -1)) == P0_OBSERVATION_DIM, config.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", int(config.get("action_shape", -1)) == ACTION_DIM, config.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_output_semantics", "contract", str(config.get("output_semantics", "")) == m3110.OUTPUT_SEMANTICS, config.get("output_semantics"), m3110.OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(config.get("runtime_base_policy_required", True)), config.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("sample_zero_action_finite_bounded", "contract", bool(np.all(np.isfinite(sample_zero)) and np.max(np.abs(sample_zero)) <= 1.0), "finite bounded", "finite bounded", "contract_violation"),
        gate("sample_obstacle_action_finite_bounded", "contract", bool(np.all(np.isfinite(obstacle_action)) and np.max(np.abs(obstacle_action)) <= 1.0), "finite bounded", "finite bounded", "contract_violation"),
        gate("rule_rows", "materialization", len(rule_rows) >= 6, len(rule_rows), ">=6", "metric_artifact"),
        gate("trace_requirement_rows", "materialization", len(requirement_rows) == 7, len(requirement_rows), 7, "metric_artifact"),
        gate("trace_requirement_labels", "materialization", labels.get("collision_action_present_but_clearance_unresolved", 0) == 5 and labels.get("offtrack_stability_recovery_limited", 0) == 2, dict(sorted(labels.items())), "5 collision-action-present and 2 offtrack-stability-limited", "metric_artifact"),
        gate("trace_requirement_rows_pass", "materialization", all(_bool(row.get("status_pass", False)) for row in requirement_rows), "all", "pass", "metric_artifact"),
        gate("actor_input_exclusions_pass", "contract", all(_bool(row.get("status_pass", False)) for row in exclusion_rows), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3118 Residual Trajectory-Authority Stability-Recovery Repair Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- policy id: `{summary['policy_id']}`",
            f"- rule rows: {summary['rule_row_count']}",
            f"- trace requirement rows: {summary['trace_requirement_row_count']}",
            f"- actor input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- claim boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3118 materializes one actor-visible obs72-to-action3 direct-action repair mechanism selected by M3117: early obstacle corridor commitment, brake/throttle timing, stability-biased steering allocation, and speed-floor preservation. It is a rule/config artifact only and is not measurement, validation, ranking, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, or self-ID evidence.",
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
    m3117_synthesis: Path,
    m3115_dir: Path,
    m3112_dir: Path,
    m3110_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3117_synthesis=m3117_synthesis, m3115_dir=m3115_dir, m3112_dir=m3112_dir, m3110_dir=m3110_dir)
    rule_rows = build_rule_rows()
    requirement_rows = residual_trace_requirement_rows(source["m3115_action_influence_rows"])
    exclusion_rows = actor_input_exclusion_rows()
    write_json(paths["direct_action_policy_config"], M3118_POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["safety_reflex_rule_rows"], rule_rows, RULE_FIELDNAMES),
        (paths["residual_trace_requirement_rows"], requirement_rows, REQUIREMENT_FIELDNAMES),
        (paths["actor_input_exclusion_rows"], exclusion_rows, EXCLUSION_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        rule_rows=rule_rows,
        requirement_rows=requirement_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    sample_zero = residual_trajectory_authority_stability_recovery_direct_action(
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        M3118_POLICY_CONFIG,
    )
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_trajectory_authority_stability_recovery_repair_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_trajectory_authority_stability_recovery_repair_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "policy_id": POLICY_ID,
        "rule_row_count": len(rule_rows),
        "trace_requirement_row_count": len(requirement_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "candidate_output_semantics": m3110.OUTPUT_SEMANTICS,
        "candidate_output_components": list(m3110.ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "sample_zero_action_abs_max": float(np.max(np.abs(sample_zero))),
        "sample_zero_action_finite": bool(np.all(np.isfinite(sample_zero))),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "measurement_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
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
        "decision": "active_safety_driver_residual_trajectory_authority_stability_recovery_repair_materialization_route_to_m3119_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
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
            "rule_row_count": len(rule_rows),
            "trace_requirement_row_count": len(requirement_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3117-synthesis", type=Path, default=DEFAULT_M3117_SYNTHESIS)
    parser.add_argument("--m3115-dir", type=Path, default=DEFAULT_M3115_DIR)
    parser.add_argument("--m3112-dir", type=Path, default=DEFAULT_M3112_DIR)
    parser.add_argument("--m3110-dir", type=Path, default=DEFAULT_M3110_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3117_synthesis=args.m3117_synthesis,
        m3115_dir=args.m3115_dir,
        m3112_dir=args.m3112_dir,
        m3110_dir=args.m3110_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['rule_row_count']}")
    print(f"trace_requirement_rows={summary['trace_requirement_row_count']}")
    print(f"actor_input_exclusion_rows={summary['actor_input_exclusion_row_count']}")


if __name__ == "__main__":
    main()
