"""Materialize M3129 trajectory-level clearance/stability corridor reflex artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "clearance-stability-corridor-reflex-materialization-preflight"
)
NEXT_ID = (
    "m3130-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "clearance-stability-corridor-reflex-materialization-result-audit"
)
M3128_ID = (
    "m3128-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "controller-architecture-diagnostic-result-audit"
)
M3127_ID = (
    "m3127-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "controller-architecture-diagnostic-materialization-preflight"
)

DEFAULT_M3128_AUDIT = Path(f"docs/{M3128_ID}.md")
DEFAULT_M3127_DIR = Path(
    "runs/m3127_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "controller_architecture_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "clearance_stability_corridor_reflex_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

POLICY_ID = "m3129_trajectory_level_clearance_stability_corridor_reflex"
OUTPUT_SEMANTICS = "direct_action_clipped"
ACTION_COMPONENTS = ("steer", "throttle", "brake")
EXPECTED_ARCHITECTURE_ROWS = 7
MIN_RULE_ROWS = 8
MIN_RUNTIME_CONTRACT_ROWS = 4
MIN_EXCLUSION_ROWS = 10

CLAIM_SCOPE = (
    "M3129 Active Safety Driver residual hard-safety trajectory-level clearance/stability "
    "corridor reflex materialization only; artifacts may define a callable actor-visible obs72 "
    "to action3 [steer throttle brake] deterministic reflex, rule rows, runtime contract rows, "
    "actor-input exclusions, claim, gate, doc, and M3130 audit manifest. No reset, step, rollout, "
    "replay, fitting, PPO, training, measurement, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, "
    "full ideal driver completion, feasibility proof, infeasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, feasibility proof, infeasibility proof, or level3 self-identification"
)

POLICY_CONFIG: dict[str, Any] = {
    "policy_id": POLICY_ID,
    "observation_shape": P0_OBSERVATION_DIM,
    "action_shape": ACTION_DIM,
    "output_components": list(ACTION_COMPONENTS),
    "output_semantics": OUTPUT_SEMANTICS,
    "runtime_base_policy_required": False,
    "checkpoint_model_required": False,
    "recurrent_hidden_state_required": False,
    "actor_observation_contract": "actor_visible_obs72_only",
    "feature_slices": {
        "ego_response": [0, 5],
        "actuator_state": [5, 9],
        "previous_action": [9, 12],
        "road_left_boundary": [12, 28],
        "road_right_boundary": [28, 44],
        "obstacle_slots": [44, 72],
    },
    "gains": {
        "road_center_steer": 0.45,
        "clearance_corridor_steer": 1.05,
        "clearance_corridor_brake": 1.20,
        "edge_corridor_steer": 0.65,
        "edge_corridor_brake": 0.55,
        "yaw_damping": 0.28,
        "lateral_velocity_damping": 0.24,
        "steer_rate_damping": 0.10,
        "sideslip_recovery_steer": 0.35,
        "stability_brake": 0.38,
        "brake_to_throttle_suppression": 1.25,
        "edge_to_throttle_suppression": 0.34,
        "stability_to_throttle_suppression": 0.30,
        "speed_floor_throttle_boost": 1.05,
        "speed_floor_brake_release": 0.55,
    },
    "thresholds": {
        "obstacle_relevance_distance_m": 42.0,
        "obstacle_lateral_window_m": 6.0,
        "road_edge_warning_margin_m": 2.2,
        "road_center_scale_m": 4.0,
        "speed_floor_mps": 8.0,
        "speed_floor_recovery_obstacle_urgency_cap": 0.30,
        "speed_floor_recovery_edge_urgency_cap": 0.35,
        "base_throttle_normalized": -0.32,
    },
}

RULE_FIELDNAMES = [
    "rule_id",
    "rule_family",
    "priority",
    "input_feature_groups",
    "output_channels",
    "formula_summary",
    "default_gain",
    "enabled_by_default",
    "runtime_base_policy_required",
    "direct_action_output",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "claim_boundary",
]
RUNTIME_CONTRACT_FIELDNAMES = [
    "contract_id",
    "contract_family",
    "runtime_symbol",
    "input_contract",
    "output_contract",
    "observation_shape",
    "action_shape",
    "action_components",
    "output_semantics",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
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
    "allowed_in_m3129",
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
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _config_value(config: Mapping[str, Any], section: str, key: str) -> float:
    default = _float(POLICY_CONFIG[section][key])
    return _float(config.get(section, {}).get(key), default)


def trajectory_level_clearance_stability_corridor_action(
    observation: np.ndarray | list[float] | tuple[float, ...],
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg: Mapping[str, Any] = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    vx_body = float(obs[0] * 20.0)
    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    steer_rate = float(obs[6])

    left = obs[12:28].reshape(8, 2).astype(np.float32)
    right = obs[28:44].reshape(8, 2).astype(np.float32)
    left_y = left[:, 1] * 20.0
    right_y = right[:, 1] * 20.0
    center_y = 0.5 * (left_y + right_y)
    margin_y = np.minimum(np.abs(left_y), np.abs(right_y))
    center_scale = _config_value(cfg, "thresholds", "road_center_scale_m")
    road_center_error = float(np.clip(np.mean(center_y[:4]) / max(center_scale, 1e-6), -1.0, 1.0))
    edge_margin = float(np.nanmin(margin_y[:4])) if margin_y.size else 0.0
    edge_warning = _config_value(cfg, "thresholds", "road_edge_warning_margin_m")
    edge_urgency = _clip01((edge_warning - edge_margin) / max(edge_warning, 1e-6))
    edge_recovery_direction = -1.0 if road_center_error > 0.0 else 1.0

    obstacle_distance = _config_value(cfg, "thresholds", "obstacle_relevance_distance_m")
    obstacle_lateral_window = _config_value(cfg, "thresholds", "obstacle_lateral_window_m")
    obstacle_urgency = 0.0
    obstacle_avoid_direction = 0.0
    for slot_index in range(4):
        base = 44 + slot_index * 7
        present = float(obs[base])
        x_body = float(obs[base + 1] * 80.0)
        y_body = float(obs[base + 2] * 20.0)
        if present <= 0.5 or x_body <= 0.0:
            continue
        approach = _clip01((obstacle_distance - x_body) / max(obstacle_distance, 1e-6))
        lateral_overlap = _clip01(1.0 - abs(y_body) / max(obstacle_lateral_window, 1e-6))
        urgency = approach * lateral_overlap
        if urgency > obstacle_urgency:
            obstacle_urgency = urgency
            obstacle_avoid_direction = -1.0 if y_body >= 0.0 else 1.0

    stability_urgency = _clip01((abs(vy_body) / 4.0 + abs(yaw_rate) / 1.5 + abs(ay_body) / 8.0) / 3.0)
    gains = cfg.get("gains", {})
    steer = (
        _float(gains.get("road_center_steer")) * road_center_error
        + _float(gains.get("clearance_corridor_steer")) * obstacle_avoid_direction * obstacle_urgency
        + _float(gains.get("edge_corridor_steer")) * edge_recovery_direction * edge_urgency
        - _float(gains.get("yaw_damping")) * float(obs[2])
        - _float(gains.get("lateral_velocity_damping")) * float(obs[1])
        - _float(gains.get("steer_rate_damping")) * steer_rate
        - _float(gains.get("sideslip_recovery_steer")) * np.sign(vy_body) * stability_urgency
    )
    brake_physical = _clip01(
        _float(gains.get("clearance_corridor_brake")) * obstacle_urgency
        + _float(gains.get("edge_corridor_brake")) * edge_urgency
        + _float(gains.get("stability_brake")) * stability_urgency
    )
    speed_floor_mps = _config_value(cfg, "thresholds", "speed_floor_mps")
    speed_deficit = _clip01((speed_floor_mps - vx_body) / max(speed_floor_mps, 1e-6))
    recovery_allowed = (
        obstacle_urgency <= _config_value(cfg, "thresholds", "speed_floor_recovery_obstacle_urgency_cap")
        and edge_urgency <= _config_value(cfg, "thresholds", "speed_floor_recovery_edge_urgency_cap")
    )
    if recovery_allowed:
        brake_physical = _clip01(brake_physical - _float(gains.get("speed_floor_brake_release")) * speed_deficit)
    throttle = (
        _config_value(cfg, "thresholds", "base_throttle_normalized")
        - _float(gains.get("brake_to_throttle_suppression")) * brake_physical
        - _float(gains.get("edge_to_throttle_suppression")) * edge_urgency
        - _float(gains.get("stability_to_throttle_suppression")) * stability_urgency
    )
    if recovery_allowed:
        throttle += _float(gains.get("speed_floor_throttle_boost")) * speed_deficit
    brake = -1.0 + 2.0 * brake_physical
    return np.clip(np.array([steer, throttle, brake], dtype=np.float32), -1.0, 1.0)


def _probe_observation(
    *,
    speed_mps: float = 14.0,
    obstacle: bool = False,
    obstacle_y_m: float = 1.0,
    edge_urgency: bool = False,
    sideslip: bool = False,
) -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = np.float32(speed_mps / 20.0)
    if sideslip:
        obs[1] = np.float32(0.35)
        obs[2] = np.float32(0.25)
        obs[4] = np.float32(0.35)
    left_y = 0.06 if edge_urgency else 0.35
    right_y = -0.06 if edge_urgency else -0.35
    for idx in range(8):
        obs[12 + idx * 2] = np.float32(idx / 8.0)
        obs[12 + idx * 2 + 1] = np.float32(left_y)
        obs[28 + idx * 2] = np.float32(idx / 8.0)
        obs[28 + idx * 2 + 1] = np.float32(right_y)
    if obstacle:
        obs[44] = 1.0
        obs[45] = np.float32(0.18)
        obs[46] = np.float32(obstacle_y_m / 20.0)
        obs[47] = np.float32(0.08)
    return obs


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "trajectory_level_corridor_rule_rows": output_dir / "trajectory_level_corridor_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3128_audit: Path, m3127_dir: Path) -> dict[str, Any]:
    paths = {
        "m3128_audit": m3128_audit,
        "m3127_summary": m3127_dir / "summary.json",
        "m3127_architecture_rows": m3127_dir / "architecture_candidate_rows.csv",
        "m3127_requirement_rows": m3127_dir / "controller_contract_requirement_rows.csv",
        "m3127_gate_rows": m3127_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3128_audit_text": paths["m3128_audit"].read_text(encoding="utf-8") if exists["m3128_audit"] else "",
        "m3127_summary": read_json(paths["m3127_summary"]) if exists["m3127_summary"] else {},
        "m3127_architecture_rows": read_csv_rows(paths["m3127_architecture_rows"]),
        "m3127_requirement_rows": read_csv_rows(paths["m3127_requirement_rows"]),
        "m3127_gate_rows": read_csv_rows(paths["m3127_gate_rows"]),
    }


def build_rule_rows() -> list[dict[str, Any]]:
    specs = [
        ("clearance_lateral_corridor", "p0", "obstacle_slots", "steer", "obstacle avoid direction times actor-visible obstacle urgency", "clearance_corridor_steer"),
        ("clearance_deceleration_corridor", "p0", "obstacle_slots;ego_response", "throttle;brake", "obstacle urgency raises physical brake and suppresses throttle", "clearance_corridor_brake"),
        ("edge_recovery_corridor", "p0", "road_left_boundary;road_right_boundary", "steer;brake", "edge urgency steers toward corridor center and adds bounded brake", "edge_corridor_steer"),
        ("sideslip_phase_recovery", "p0", "ego_response", "steer;brake", "lateral velocity yaw and acceleration damp steering and brake", "sideslip_recovery_steer"),
        ("speed_floor_guard", "p1", "ego_response", "throttle;brake", "low speed releases brake and boosts throttle only when obstacle/edge urgency is low", "speed_floor_throttle_boost"),
        ("direct_action_clipping", "p0", "all_actor_visible_obs72", "steer;throttle;brake", "output action is clipped to [-1, 1]", "not_applicable"),
        ("runtime_base_policy_absence", "p0", "none", "none", "no runtime base policy or checkpoint model is loaded", "not_applicable"),
        ("audit_before_measurement", "p0", "process", "none", "M3130 must audit materialization before measurement", "not_applicable"),
    ]
    rows = []
    gains = POLICY_CONFIG["gains"]
    for index, (family, priority, inputs, outputs, formula, gain_name) in enumerate(specs, start=1):
        rows.append(
            {
                "rule_id": f"m3129-rule-{index:04d}",
                "rule_family": family,
                "priority": priority,
                "input_feature_groups": inputs,
                "output_channels": outputs,
                "formula_summary": formula,
                "default_gain": gains.get(gain_name, "") if gain_name != "not_applicable" else "",
                "enabled_by_default": True,
                "runtime_base_policy_required": False,
                "direct_action_output": True,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_runtime_contract_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "callable_runtime",
            "autodrift.engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight.trajectory_level_clearance_stability_corridor_action",
            "np.ndarray/list/tuple shape (72,), finite actor-visible P0 observation",
            "np.ndarray shape (3,), finite bounded [steer throttle brake]",
        ),
        (
            "policy_config",
            "direct_action_policy_config.json",
            "materialized deterministic gains and thresholds",
            "same direct action3 semantics",
        ),
        (
            "actor_input_contract",
            "obs72_actor_visible_current_frame_only",
            "no hidden oracle TTC target source route outcome progress verdict baseline labels",
            "direct action3",
        ),
        (
            "audit_boundary",
            f"experiments/manifests/{NEXT_ID}.json",
            "M3130 result audit required before measurement",
            "no repair-success claim in M3129",
        ),
    ]
    return [
        {
            "contract_id": f"m3129-runtime-contract-{index:04d}",
            "contract_family": family,
            "runtime_symbol": runtime_symbol,
            "input_contract": input_contract,
            "output_contract": output_contract,
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "action_components": ";".join(ACTION_COMPONENTS),
            "output_semantics": OUTPUT_SEMANTICS,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, runtime_symbol, input_contract, output_contract) in enumerate(specs, start=1)
    ]


def build_actor_input_exclusion_rows() -> list[dict[str, Any]]:
    forbidden = [
        ("hidden_oracle_state", "privileged simulator state is not an actor input"),
        ("ttc_actor_input", "TTC is not materialized as a runtime actor input shortcut"),
        ("target_label", "target labels are not runtime inputs"),
        ("source_id", "source ids are diagnostic lineage only"),
        ("route_id", "route ids are diagnostic lineage only"),
        ("outcome_label", "outcomes are not runtime inputs"),
        ("progress_label", "progress is not a runtime shortcut input"),
        ("verdict_label", "audits/verdicts are not runtime inputs"),
        ("baseline_outcome", "baseline outcomes are not runtime inputs"),
        ("recurrent_hidden_state", "no recurrent hidden state is required"),
    ]
    return [
        {
            "exclusion_id": f"m3129-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(forbidden, start=1)
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("trajectory_level_corridor_rule_rows", "materialization", True, "trajectory_level_corridor_rule_rows.csv"),
        ("runtime_contract_rows", "runtime_contract", True, "runtime_contract_rows.csv"),
        ("actor_input_exclusion_rows", "contract_guard", True, "actor_input_exclusion_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3130 audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future separately registered measurement route"),
        ("measurement_result", "measurement", "future measurement route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("repair_success", "verdict", "future result audit after measurement"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_or_infeasibility_proof", "verdict", "future formal feasibility/validation route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action driver forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3129-{claim_id}",
            "claim_family": family,
            "allowed_in_m3129": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3129-{claim_id}",
            "claim_family": family,
            "allowed_in_m3129": False,
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
        "priority": 31250,
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
        "hypothesis": "A bounded result audit can accept or reject the M3129 trajectory-level clearance/stability corridor reflex materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3128_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "trajectory_level_corridor_rule_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit trajectory-level clearance/stability corridor reflex materialization"],
            "derived_from": [MILESTONE_ID, M3128_ID, M3127_ID],
            "blocked_by": [
                "M3129 materialization artifacts require audit before measurement",
                "M3129 is not repair-success or validation evidence",
            ],
            "supersedes": ["direct measurement after M3128 without materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3130 must audit M3129 summary rule runtime-contract actor-input exclusion claim and gate artifacts",
            "M3130 must preserve obs72/action3 direct [steer throttle brake] actor contract and runtime_base_policy_required false",
            "M3130 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof infeasibility-proof and self-ID claims",
            "M3130 must select exactly one measurement route artifact-repair route synthesis or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3129 materialization into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof infeasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_trajectory_level_controller_architecture_diagnosis",
            "evidence_axis": "trajectory_level_clearance_stability_corridor_reflex_materialization_result_audit",
            "evidence_increment": "audits materialized trajectory-level corridor reflex before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3129 artifacts are missing or gate matrix fails",
                "stop if actor input or direct action output contracts were violated",
                "route to synthesis if no safe measurement route remains",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to synthesis or stop if no deployable measurement route remains",
                "route to one constrained smoke or full-fresh measurement only after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3129 completes materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3129 trajectory-level corridor reflex materialization artifacts",
            "admission_evidence": ["M3129 summary gate matrix rule contract exclusion and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no feasibility or infeasibility proof claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3130 status queue scoreboard research log and review",
                "one follow-up manifest only if M3130 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3130 accepts or rejects M3129 as complete and claim-safe",
                "next measurement artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3130 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3130; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3129 materialization artifacts only.",
            "negative_result_policy": "Preserve materialization evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3129 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits deployable materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3130 prepares engineering measurement decision",
            "must_synthesize_if": [
                "M3130 cannot accept M3129 as complete and claim-safe",
                "M3130 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result feasibility-proof or self-ID evidence",
                "M3130 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3130 audits M3129 artifact row counts gates actor contract and claim boundaries",
            "M3130 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3130 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3130 hides M3129 failures or missing artifacts",
            "M3130 treats M3129 as validation repair-success feasibility proof or performance verdict",
            "M3130 changes actor input or action contract",
            "M3130 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3130 audits M3129 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [
            {
                "name": "active_safety_driver_residual_trajectory_level_clearance_stability_corridor_reflex_materialization_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3129-{gate_id}",
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


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    runtime_contract_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
    probe_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m3127_summary = source["m3127_summary"]
    audit_text = str(source.get("m3128_audit_text", ""))
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3128_route_marker", "lineage", "accept_m3127_architecture_diagnostics_route_to_m3129_trajectory_level_clearance_stability_corridor_reflex_materialization" in audit_text, "route marker", "present", "lineage_invalid"),
        gate("m3127_status_pass", "lineage", _bool(m3127_summary.get("status_pass")), m3127_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3127_gate_matrix_pass", "lineage", _bool(m3127_summary.get("gate_matrix_pass")), m3127_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3127_architecture_rows", "lineage", int(m3127_summary.get("architecture_candidate_row_count", 0)) == EXPECTED_ARCHITECTURE_ROWS, m3127_summary.get("architecture_candidate_row_count"), EXPECTED_ARCHITECTURE_ROWS, "lineage_invalid"),
        gate("rule_rows", "materialization", len(rule_rows) >= MIN_RULE_ROWS, len(rule_rows), f">={MIN_RULE_ROWS}", "metric_artifact"),
        gate("runtime_contract_rows", "contract", len(runtime_contract_rows) >= MIN_RUNTIME_CONTRACT_ROWS, len(runtime_contract_rows), f">={MIN_RUNTIME_CONTRACT_ROWS}", "contract_violation"),
        gate("actor_input_exclusion_rows", "contract", len(exclusion_rows) >= MIN_EXCLUSION_ROWS and all(_bool(row.get("status_pass")) for row in exclusion_rows), len(exclusion_rows), f">={MIN_EXCLUSION_ROWS} all pass", "contract_violation"),
        gate("direct_action_output", "contract", all(_bool(row.get("direct_action_output")) for row in rule_rows), "all rules", True, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", all(not _bool(row.get("runtime_base_policy_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("hidden_oracle_absent", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("ttc_actor_input_absent", "contract", all(not _bool(row.get("ttc_actor_input_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("action_probe_rows", "runtime_contract", len(probe_rows) == 4 and all(_bool(row.get("action_finite")) and _bool(row.get("action_bounded")) for row in probe_rows), len(probe_rows), "4 finite bounded", "metric_artifact"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_environment_execution", "execution", True, "no reset step rollout replay fitting training measurement validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def build_action_probe_rows() -> list[dict[str, Any]]:
    specs = [
        ("clear_low_speed", _probe_observation(speed_mps=3.0)),
        ("urgent_obstacle_left", _probe_observation(speed_mps=15.0, obstacle=True, obstacle_y_m=1.0)),
        ("urgent_edge", _probe_observation(speed_mps=14.0, edge_urgency=True)),
        ("sideslip_recovery", _probe_observation(speed_mps=14.0, sideslip=True)),
    ]
    rows = []
    for index, (family, obs) in enumerate(specs, start=1):
        action = trajectory_level_clearance_stability_corridor_action(obs)
        rows.append(
            {
                "probe_id": f"m3129-action-probe-{index:04d}",
                "probe_family": family,
                "steer": float(action[0]),
                "throttle": float(action[1]),
                "brake": float(action[2]),
                "action_finite": bool(np.all(np.isfinite(action))),
                "action_bounded": bool(np.max(np.abs(action)) <= 1.0),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3129 Residual Hard-Safety Trajectory-Level Clearance/Stability Corridor Reflex Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- rule rows: {summary['trajectory_level_corridor_rule_row_count']}",
            f"- runtime contract rows: {summary['runtime_contract_row_count']}",
            f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3129 materializes a callable actor-visible obs72-to-action3 trajectory-level clearance/stability corridor reflex and contract artifacts. It does not run the environment or make repair-success claims.",
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


def run_materialization(
    *,
    m3128_audit: Path,
    m3127_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3128_audit=m3128_audit, m3127_dir=m3127_dir)
    rule_rows = build_rule_rows()
    runtime_contract_rows = build_runtime_contract_rows()
    exclusion_rows = build_actor_input_exclusion_rows()
    probe_rows = build_action_probe_rows()
    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["trajectory_level_corridor_rule_rows"], rule_rows, fieldnames=RULE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], runtime_contract_rows, fieldnames=RUNTIME_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], exclusion_rows, fieldnames=EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = build_gate_matrix_rows(
        source=source,
        rule_rows=rule_rows,
        runtime_contract_rows=runtime_contract_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
        probe_rows=probe_rows,
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m3127_architecture_row_count": len(source["m3127_architecture_rows"]),
        "trajectory_level_corridor_rule_row_count": len(rule_rows),
        "runtime_contract_row_count": len(runtime_contract_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "action_probe_row_count": len(probe_rows),
        "required_artifacts_present": present,
        "runtime_driver_id": POLICY_ID,
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "actor_observation_contract": "obs72_actor_visible_current_frame_only",
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "measurement_run": False,
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
        "feasibility_proof_claim_made": False,
        "infeasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_route_to_m3130_result_audit",
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
    parser.add_argument("--m3128-audit", type=Path, default=DEFAULT_M3128_AUDIT)
    parser.add_argument("--m3127-dir", type=Path, default=DEFAULT_M3127_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3128_audit=args.m3128_audit,
        m3127_dir=args.m3127_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['trajectory_level_corridor_rule_row_count']}")
    print(f"runtime_contract_rows={summary['runtime_contract_row_count']}")
    print(f"actor_input_exclusion_rows={summary['actor_input_exclusion_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
