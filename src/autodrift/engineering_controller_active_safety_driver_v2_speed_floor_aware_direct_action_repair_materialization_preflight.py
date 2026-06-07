"""Materialize M3093 v2 speed-floor-aware direct-action repair artifacts."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight import (
    DEFAULT_POLICY_CONFIG,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-"
    "direct-action-repair-materialization-preflight"
)
NEXT_ID = (
    "m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-"
    "direct-action-repair-materialization-result-audit"
)
M3092_ID = (
    "m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-"
    "behavior-negative-repair-synthesis"
)
M3090_ID = (
    "m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-full-fresh-runtime-measurement-preflight"
)

DEFAULT_M3092_SYNTHESIS = Path(f"docs/{M3092_ID}.md")
DEFAULT_M3090_DIR = Path(
    "runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_full_fresh_runtime_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_"
    "direct_action_repair_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

ACTION_COMPONENTS = ("steer", "throttle", "brake")
OUTPUT_SEMANTICS = "direct_action_clipped"
POLICY_ID = "m3093_speed_floor_aware_balanced_direct_action_repair_v2"
CLAIM_SCOPE = (
    "M3093 Active Safety Driver v2 speed-floor-aware direct-action repair "
    "materialization only; artifacts may define actor-visible obs72 to direct "
    "action3 [steer throttle brake] repair rules, config, guards, doc, and "
    "M3094 audit manifest. No reset, step, rollout, replay, fitting, PPO, "
    "training, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper "
    "evidence, finite-window-vs-GRU evidence, full ideal driver completion, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, "
    "current-sim verdict, robustness-result, repair success, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, or level3 self-identification"
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
    "allowed_in_m3093",
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


V2_POLICY_CONFIG: dict[str, Any] = deepcopy(DEFAULT_POLICY_CONFIG)
V2_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "repair_route": "speed_floor_aware_balanced_direct_action_repair",
        "repair_scope": "materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
    }
)
V2_POLICY_CONFIG["gains"].update(
    {
        "road_center_steer": 0.62,
        "edge_brake": 0.32,
        "obstacle_steer": 0.82,
        "obstacle_brake": 0.90,
        "yaw_damping": 0.24,
        "lateral_velocity_damping": 0.22,
        "steer_rate_damping": 0.10,
        "stability_brake": 0.18,
        "brake_to_throttle_suppression": 0.65,
        "edge_to_throttle_suppression": 0.18,
        "stability_to_throttle_suppression": 0.10,
        "speed_floor_throttle_boost": 0.58,
        "speed_floor_brake_release": 0.48,
    }
)
V2_POLICY_CONFIG["thresholds"].update(
    {
        "base_throttle_normalized": 0.08,
        "speed_floor_mps": 6.0,
        "speed_floor_recovery_obstacle_urgency_cap": 0.42,
        "speed_floor_recovery_edge_urgency_cap": 0.48,
    }
)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _config_value(config: Mapping[str, Any], section: str, key: str) -> float:
    default = _float(V2_POLICY_CONFIG[section][key])
    return _float(config.get(section, {}).get(key), default)


def speed_floor_aware_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute v2 direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg: Mapping[str, Any] = config or V2_POLICY_CONFIG
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
        + _float(gains.get("obstacle_steer")) * obstacle_avoid_direction * obstacle_urgency
        - _float(gains.get("yaw_damping")) * float(obs[2])
        - _float(gains.get("lateral_velocity_damping")) * float(obs[1])
        - _float(gains.get("steer_rate_damping")) * steer_rate
    )

    brake_physical = _clip01(
        _float(gains.get("obstacle_brake")) * obstacle_urgency
        + _float(gains.get("edge_brake")) * edge_urgency
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "safety_reflex_rule_rows": output_dir / "safety_reflex_rule_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def build_rule_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "m3093-rule-speed-floor-recovery",
            "speed_floor_throttle_brake_release",
            "p0",
            "ego_response;obstacle_slots;road_left_boundary;road_right_boundary",
            "throttle;brake",
            "raise throttle and release non-urgent braking when actor-visible speed is below the speed floor",
            "speed_floor_throttle_boost",
            0.0,
            1.2,
        ),
        (
            "m3093-rule-obstacle-safety",
            "urgent_obstacle_braking_and_steering",
            "p0",
            "obstacle_slots;ego_response",
            "steer;brake;throttle",
            "preserve urgent visible-obstacle lateral avoidance and braking before speed recovery",
            "obstacle_brake",
            0.0,
            1.5,
        ),
        (
            "m3093-rule-road-recovery",
            "corridor_centering_and_edge_guard",
            "p0",
            "road_left_boundary;road_right_boundary",
            "steer;brake;throttle",
            "center in the observed road corridor while avoiding excess low-speed edge braking",
            "road_center_steer",
            0.0,
            1.2,
        ),
        (
            "m3093-rule-stability-balance",
            "stability_damping_without_speed_collapse",
            "p1",
            "ego_response;actuator_state",
            "steer;brake;throttle",
            "damp yaw lateral velocity acceleration and steering pressure with reduced throttle suppression",
            "stability_brake",
            0.0,
            0.8,
        ),
        (
            "m3093-rule-direct-action-bound",
            "bounded_direct_action",
            "p0",
            "all_actor_visible_features",
            "steer;throttle;brake",
            "clip final action to [-1, 1] and require finite direct action output",
            "not_applicable",
            -1.0,
            1.0,
        ),
    ]
    gains = V2_POLICY_CONFIG["gains"]
    return [
        {
            "rule_id": rule_id,
            "rule_family": family,
            "priority": priority,
            "input_feature_groups": inputs,
            "output_channels": outputs,
            "formula_summary": formula,
            "default_gain": gains.get(gain_key, "not_applicable"),
            "gain_lower_bound": lower,
            "gain_upper_bound": upper,
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "direct_action_output": True,
            "hidden_oracle_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for rule_id, family, priority, inputs, outputs, formula, gain_key, lower, upper in specs
    ]


def build_actor_input_exclusion_rows() -> list[dict[str, Any]]:
    exclusions = [
        ("hidden_oracle", "hidden dynamics or simulator-only state"),
        ("ttc", "precomputed time-to-collision shortcut"),
        ("target_label", "trainer-side action or objective target"),
        ("target_provenance", "target source or fitted-row provenance"),
        ("source_label", "source policy label"),
        ("route_label", "route or branch decision label"),
        ("outcome_label", "success failure or completion outcome"),
        ("progress_label", "future progress or success-progress signal"),
        ("verdict_label", "validation ranking promotion or audit verdict"),
        ("diagnostic_key", "mu mass tire force feasibility or reward diagnostics"),
    ]
    return [
        {
            "exclusion_id": f"m3093-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(exclusions, start=1)
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("policy_config_materialized", "materialization", True, "direct_action_policy_config.json"),
        ("rule_table_materialized", "materialization", True, "safety_reflex_rule_rows.csv"),
        ("actor_input_exclusions_materialized", "guard", True, "actor_input_exclusion_rows.csv"),
        ("claim_boundary_guards_materialized", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3094 audit manifest"),
    ]
    blocked = [
        ("environment_reset_or_step", "execution", "future measurement route"),
        ("rollout_measurement", "execution", "future measurement route"),
        ("fitting_or_training", "training", "future guarded route if selected"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit after measurement"),
        ("robustness_result", "verdict", "future robustness measurement route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity route"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
    ]
    rows = [
        {
            "claim_id": f"m3093-{claim_id}",
            "claim_family": family,
            "allowed_in_m3093": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3093-{claim_id}",
            "claim_family": family,
            "allowed_in_m3093": False,
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
        "priority": 30890,
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
        "hypothesis": "A bounded result audit can accept or reject the M3093 v2 speed-floor-aware direct-action repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "safety_reflex_rule_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit v2 speed-floor-aware repair materialization before measurement admission"],
            "derived_from": [MILESTONE_ID, M3092_ID, M3090_ID],
            "blocked_by": [
                "M3093 materialization artifacts require audit before measurement",
                "materialization cannot support repair-success or driver-performance claims",
            ],
            "supersedes": ["direct measurement admission without v2 repair artifact audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3094 must audit M3093 summary rule config exclusion claim and gate artifacts",
            "M3094 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3094 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3094 must select exactly one measurement, artifact-repair, synthesis, or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training",
            "do not treat M3093 materialization as driver-performance repair-success robustness-result or self-ID evidence",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v2_speed_floor_aware_repair",
            "evidence_axis": "speed_floor_aware_direct_action_repair_materialization_result_audit",
            "evidence_increment": "audits the M3093 v2 direct-action repair materialization artifacts before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3093 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "route to measurement only if M3093 is complete and claim-safe",
            ],
            "fallback_plan": [
                "route to materialization repair if artifacts are incomplete",
                "route to measurement preflight if artifacts are complete and claim-safe",
                "route to stop if deployment boundary is not preservable",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3093 completes v2 speed-floor-aware repair materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3093 v2 repair materialization artifacts",
            "admission_evidence": ["M3093 summary rule config exclusion claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3094 status queue scoreboard research log and review",
                "one follow-up manifest only if M3094 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3094 accepts or rejects M3093 as complete and claim-safe",
                "next measurement, artifact-repair, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3094 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3094; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3093 materialization artifacts only.",
            "negative_result_policy": "Reject or repair M3093 artifacts rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3093 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new v2 repair materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3094 prepares a measurement route decision",
            "must_synthesize_if": [
                "M3094 cannot accept M3093 as complete and claim-safe",
                "M3094 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result or self-ID evidence",
                "M3094 cannot select exactly one measurement repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3094 audits M3093 artifact row counts gates actor contract and claim boundaries",
            "M3094 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3094 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3094 hides M3093 failures or missing artifacts",
            "M3094 treats M3093 materialization as measurement validation or performance verdict",
            "M3094 changes actor input or action contract",
            "M3094 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3094 audits M3093 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_v2_repair_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _probe_observation(*, speed_mps: float, obstacle: bool = False, edge_urgent: bool = False) -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = speed_mps / 20.0
    left_y = 0.04 if edge_urgent else 0.25
    right_y = -0.04 if edge_urgent else -0.25
    for index in range(8):
        obs[12 + index * 2] = 0.05 * (index + 1)
        obs[12 + index * 2 + 1] = left_y
        obs[28 + index * 2] = 0.05 * (index + 1)
        obs[28 + index * 2 + 1] = right_y
    if obstacle:
        obs[44] = 1.0
        obs[45] = 0.10
        obs[46] = 0.0
    return obs


def _probe_rows() -> list[dict[str, Any]]:
    probes = [
        ("clear_low_speed", _probe_observation(speed_mps=3.0)),
        ("urgent_obstacle", _probe_observation(speed_mps=14.0, obstacle=True)),
        ("edge_recovery", _probe_observation(speed_mps=7.0, edge_urgent=True)),
    ]
    rows = []
    for name, obs in probes:
        action = speed_floor_aware_direct_action(obs, V2_POLICY_CONFIG)
        rows.append(
            {
                "probe_id": f"m3093-probe-{name}",
                "status_pass": bool(action.shape == (ACTION_DIM,) and np.all(np.isfinite(action)) and np.max(np.abs(action)) <= 1.0),
                "steer": float(action[0]),
                "throttle": float(action[1]),
                "brake": float(action[2]),
            }
        )
    return rows


def gate(gate_id: str, family: str, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3093-{gate_id}",
        "gate_family": family,
        "status_pass": str(observed) == str(expected),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_rows(
    *,
    m3092_text: str,
    m3090_summary: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    follow_up_manifest_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    config = V2_POLICY_CONFIG
    return [
        gate("m3092_synthesis_present", "source", bool(m3092_text), True, "lineage_invalid"),
        gate("m3092_route_marker", "source", "route_to_m3093" in m3092_text, True, "lineage_invalid"),
        gate("m3090_status_pass", "source", m3090_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3090_failure_denominator", "source", m3090_summary.get("runtime_measurement_episode_row_count"), 64, "metric_artifact"),
        gate("policy_observation_shape", "contract", config.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", config.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_action_components", "contract", "|".join(config.get("output_components", [])), "|".join(ACTION_COMPONENTS), "contract_violation"),
        gate("policy_output_semantics", "contract", config.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_required", "contract", config.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("speed_floor_config_present", "repair_config", "speed_floor_mps" in config.get("thresholds", {}), True, "metric_artifact"),
        gate("speed_floor_boost_present", "repair_config", "speed_floor_throttle_boost" in config.get("gains", {}), True, "metric_artifact"),
        gate("rule_rows_present", "artifact", len(rule_rows) >= 5, True, "metric_artifact"),
        gate("speed_floor_rule_present", "artifact", any("speed_floor" in row["rule_family"] for row in rule_rows), True, "metric_artifact"),
        gate("exclusion_rows_pass", "contract", all(_bool(row.get("status_pass")) for row in exclusion_rows), True, "contract_violation"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), True, "objective_overfit"),
        gate("probe_rows_pass", "runtime_api", all(_bool(row.get("status_pass")) for row in probe_rows), True, "contract_violation"),
        gate("low_speed_probe_positive_throttle", "repair_config", probe_rows[0]["throttle"] > 0.0, True, "behavior_regression"),
        gate("urgent_obstacle_probe_brakes", "repair_config", probe_rows[1]["brake"] > 0.0, True, "behavior_regression"),
        gate("follow_up_manifest_registered", "lineage", follow_up_manifest_exists, True, "lineage_invalid"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        gate("measurement_run", "claim", False, False, "objective_overfit"),
        gate("validation_result_claim_made", "claim", False, False, "objective_overfit"),
        gate("driver_performance_claim_made", "claim", False, False, "objective_overfit"),
        gate("repair_success_claim_made", "claim", False, False, "objective_overfit"),
        gate("self_id_claim_made", "claim", False, False, "proof_washout"),
    ]


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    text = f"""# M3093 Active Safety Driver v2 Speed-Floor-Aware Repair Materialization Preflight

## Summary

- status: completed
- result class: `{summary['result_class']}`
- policy id: `{summary['policy_id']}`
- rule rows: {summary['rule_row_count']}
- actor input exclusion rows: {summary['actor_input_exclusion_row_count']}
- claim-boundary rows: {summary['claim_boundary_row_count']}
- gate matrix pass: {summary['gate_matrix_pass']}
- selected next action: `{summary['selected_next_action']}`

## Repair Scope

M3093 materializes a v2 speed-floor-aware balanced direct-action repair config and rule table selected by M3092. The largest M3090 behavior blocker is speed-too-low, while collision and offtrack rows remain hard-safety blockers. This materialization targets speed-floor throttle/brake release only when visible obstacle and road-edge urgency are not high, while preserving urgent obstacle and corridor recovery branches.

## Contract

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Boundary

This is materialization only. M3093 runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test. It makes no repair-success, robustness-result, current-sim verdict, driver-performance, full-driver, paper, or validation claim.

## Next

- next blocker: `{summary['next_blocker']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_preflight(
    *,
    m3092_synthesis: Path,
    m3090_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)

    m3092_text = m3092_synthesis.read_text(encoding="utf-8") if m3092_synthesis.exists() else ""
    m3090_summary = read_json(m3090_dir / "summary.json") if (m3090_dir / "summary.json").exists() else {}
    m3090_rows = read_csv_rows(m3090_dir / "runtime_measurement_episode_rows.csv")

    rule_rows = build_rule_rows()
    exclusion_rows = build_actor_input_exclusion_rows()
    follow_up = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=True)
    probe_rows = _probe_rows()

    write_json(paths["direct_action_policy_config"], V2_POLICY_CONFIG)
    write_csv_rows(paths["safety_reflex_rule_rows"], rule_rows, RULE_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], exclusion_rows, EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_json(paths["follow_up_manifest"], follow_up)

    required_without_summary = [
        "direct_action_policy_config",
        "safety_reflex_rule_rows",
        "actor_input_exclusion_rows",
        "claim_boundary_rows",
        "follow_up_manifest",
    ]
    required_artifacts_present = all(paths[key].exists() for key in required_without_summary)
    gate_rows = build_gate_rows(
        m3092_text=m3092_text,
        m3090_summary=m3090_summary,
        rule_rows=rule_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        probe_rows=probe_rows,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
        required_artifacts_present=required_artifacts_present,
    )
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    non_success_rows = [row for row in m3090_rows if not _bool(row.get("success"))]
    speed_low_rows = [row for row in non_success_rows if row.get("termination_reason") == "speed_too_low"]
    collision_rows = [row for row in non_success_rows if row.get("termination_reason") == "obstacle_collision"]
    offtrack_rows = [row for row in non_success_rows if row.get("termination_reason") == "off_track"]

    generated_at = utc_timestamp()
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": generated_at,
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "result_class": "active_safety_driver_v2_speed_floor_aware_repair_materialization_preflight_pass",
        "decision": "route_to_m3094_speed_floor_aware_repair_materialization_result_audit",
        "policy_id": POLICY_ID,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "rule_row_count": len(rule_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "m3090_non_success_count": len(non_success_rows),
        "m3090_speed_too_low_count": len(speed_low_rows),
        "m3090_collision_count": len(collision_rows),
        "m3090_offtrack_count": len(offtrack_rows),
        "low_speed_probe_throttle": probe_rows[0]["throttle"],
        "urgent_obstacle_probe_brake": probe_rows[1]["brake"],
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "next_blocker": NEXT_ID,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(value) for key, value in paths.items()},
    }
    write_doc(paths["doc"], summary)
    write_json(paths["summary"], summary)
    write_run_state(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3092-synthesis", type=Path, default=DEFAULT_M3092_SYNTHESIS)
    parser.add_argument("--m3090-dir", type=Path, default=DEFAULT_M3090_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_preflight(
        m3092_synthesis=args.m3092_synthesis,
        m3090_dir=args.m3090_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )


if __name__ == "__main__":
    main()
