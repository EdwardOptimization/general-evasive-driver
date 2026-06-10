"""Materialize M3103 v4 v2-fallback no-regression hard-safety direct-action repair."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    V2_POLICY_CONFIG,
    speed_floor_aware_direct_action,
)


MILESTONE_ID = (
    "m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-materialization-preflight"
)
NEXT_ID = (
    "m3104-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-materialization-result-audit"
)
M3102_ID = "m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis"
M3100_ID = (
    "m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)
M3095_ID = (
    "m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-"
    "repair-full-fresh-measurement-preflight"
)
M3093_ID = (
    "m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-"
    "repair-materialization-preflight"
)
POLICY_ID = "m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair"

DEFAULT_M3102_SYNTHESIS = Path(f"docs/{M3102_ID}.md")
DEFAULT_M3100_DIR = Path(
    "runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3095_DIR = Path(
    "runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_"
    "direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3093_DIR = Path(
    "runs/m3093_engineering_controller_active_safety_driver_v2_speed_floor_aware_"
    "direct_action_repair_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3103 Active Safety Driver v4 v2-fallback no-regression hard-safety direct-action "
    "repair materialization only; artifacts may define actor-visible obs72 to direct "
    "action3 [steer throttle brake] repair rules, config, no-regression guards, doc, "
    "and M3104 audit manifest. No reset, step, rollout, replay, fitting, PPO, training, "
    "measurement, validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-"
    "identification"
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
NO_REGRESSION_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "source_row",
    "guard_expression",
    "status_pass",
    "expected_preservation",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3103",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


V4_POLICY_CONFIG: dict[str, Any] = deepcopy(V2_POLICY_CONFIG)
V4_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "repair_route": "v2_fallback_no_regression_hard_safety_direct_action_repair",
        "repair_scope": "materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
    }
)
V4_POLICY_CONFIG["gains"].update(
    {
        "local_obstacle_steer": 0.22,
        "local_obstacle_brake": 0.18,
        "local_edge_steer": 0.14,
        "local_edge_brake": 0.10,
        "local_throttle_suppression": 0.12,
    }
)
V4_POLICY_CONFIG["thresholds"].update(
    {
        "fallback_base_policy_id": "m3093_speed_floor_aware_balanced_direct_action_repair_v2",
        "global_high_speed_throttle_suppression_enabled": False,
        "local_hard_safety_speed_mps": 14.0,
        "local_obstacle_urgency_trigger": 0.50,
        "local_edge_urgency_trigger": 0.72,
        "speed_floor_preserve_below_mps": 7.0,
        "m3100_regression_rows_guarded": ["m3100-same-row-comparison-0014", "m3100-same-row-comparison-0048"],
    }
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _config_value(config: Mapping[str, Any], section: str, key: str) -> float:
    default = _float(V4_POLICY_CONFIG[section][key])
    return _float(config.get(section, {}).get(key), default)


def _hard_safety_features(observation: np.ndarray, config: Mapping[str, Any]) -> dict[str, float]:
    obs = np.asarray(observation, dtype=np.float32)
    vx_body = float(obs[0] * 20.0)
    left = obs[12:28].reshape(8, 2).astype(np.float32)
    right = obs[28:44].reshape(8, 2).astype(np.float32)
    left_y = left[:, 1] * 20.0
    right_y = right[:, 1] * 20.0
    center_y = 0.5 * (left_y + right_y)
    margin_y = np.minimum(np.abs(left_y), np.abs(right_y))
    edge_warning = _config_value(config, "thresholds", "road_edge_warning_margin_m")
    edge_margin = float(np.nanmin(margin_y[:4])) if margin_y.size else 0.0
    edge_urgency = _clip01((edge_warning - edge_margin) / max(edge_warning, 1e-6))
    road_center_error = float(np.clip(np.mean(center_y[:4]) / max(_config_value(config, "thresholds", "road_center_scale_m"), 1e-6), -1.0, 1.0))

    obstacle_distance = _config_value(config, "thresholds", "obstacle_relevance_distance_m")
    obstacle_lateral_window = _config_value(config, "thresholds", "obstacle_lateral_window_m")
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

    return {
        "vx_body": vx_body,
        "edge_urgency": edge_urgency,
        "road_center_error": road_center_error,
        "obstacle_urgency": obstacle_urgency,
        "obstacle_avoid_direction": obstacle_avoid_direction,
    }


def v4_v2_fallback_no_regression_hard_safety_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute v4 direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg: Mapping[str, Any] = config or V4_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    action = np.asarray(speed_floor_aware_direct_action(obs, V2_POLICY_CONFIG), dtype=np.float32).copy()
    features = _hard_safety_features(obs, cfg)
    gains = cfg.get("gains", {})
    thresholds = cfg.get("thresholds", {})
    speed = features["vx_body"]
    local_speed_risk = _clip01((speed - _float(thresholds.get("local_hard_safety_speed_mps"))) / 6.0)
    obstacle_excess = _clip01(
        (features["obstacle_urgency"] - _float(thresholds.get("local_obstacle_urgency_trigger"))) / 0.5
    )
    edge_excess = _clip01((features["edge_urgency"] - _float(thresholds.get("local_edge_urgency_trigger"))) / 0.28)
    local_risk = local_speed_risk * max(obstacle_excess, edge_excess)

    if local_risk > 0.0:
        action[0] += (
            _float(gains.get("local_obstacle_steer")) * features["obstacle_avoid_direction"] * obstacle_excess
            + _float(gains.get("local_edge_steer")) * features["road_center_error"] * edge_excess
        )
        brake_physical = _clip01((float(action[2]) + 1.0) / 2.0)
        brake_physical = _clip01(
            brake_physical
            + local_speed_risk
            * (_float(gains.get("local_obstacle_brake")) * obstacle_excess + _float(gains.get("local_edge_brake")) * edge_excess)
        )
        action[2] = -1.0 + 2.0 * brake_physical
        if speed > _float(thresholds.get("speed_floor_preserve_below_mps")):
            action[1] -= _float(gains.get("local_throttle_suppression")) * local_risk

    return np.clip(action, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "safety_reflex_rule_rows": output_dir / "safety_reflex_rule_rows.csv",
        "no_regression_guard_rows": output_dir / "no_regression_guard_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3102_synthesis: Path, m3100_dir: Path, m3095_dir: Path, m3093_dir: Path) -> dict[str, Any]:
    paths = {
        "m3102_synthesis": m3102_synthesis,
        "m3100_summary": m3100_dir / "summary.json",
        "m3100_comparison_rows": m3100_dir / "same_row_comparison_rows.csv",
        "m3095_summary": m3095_dir / "summary.json",
        "m3095_episode_rows": m3095_dir / "measurement_episode_rows.csv",
        "m3093_summary": m3093_dir / "summary.json",
        "m3093_policy_config": m3093_dir / "direct_action_policy_config.json",
        "m3093_gate_rows": m3093_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    comparison_rows = read_csv_rows(paths["m3100_comparison_rows"])
    return {
        "paths": paths,
        "source_exists": exists,
        "m3102_synthesis_text": paths["m3102_synthesis"].read_text(encoding="utf-8") if exists["m3102_synthesis"] else "",
        "m3100_summary": read_json(paths["m3100_summary"]) if exists["m3100_summary"] else {},
        "m3100_comparison_rows": comparison_rows,
        "m3100_regression_rows": [row for row in comparison_rows if int(row.get("success_delta_vs_m3095", "0")) < 0],
        "m3095_summary": read_json(paths["m3095_summary"]) if exists["m3095_summary"] else {},
        "m3095_episode_rows": read_csv_rows(paths["m3095_episode_rows"]),
        "m3093_summary": read_json(paths["m3093_summary"]) if exists["m3093_summary"] else {},
        "m3093_policy_config": read_json(paths["m3093_policy_config"]) if exists["m3093_policy_config"] else {},
        "m3093_gate_rows": read_csv_rows(paths["m3093_gate_rows"]),
    }


def build_rule_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "m3103-rule-v2-fallback-base",
            "v2_speed_floor_fallback_base",
            "p0",
            "ego_response;road_boundaries;obstacle_slots",
            "steer;throttle;brake",
            "start from the M3093 v2 speed-floor-aware direct-action function",
            "not_applicable",
            -1.0,
            1.0,
        ),
        (
            "m3103-rule-no-global-throttle-suppression",
            "no_global_high_speed_throttle_suppression",
            "p0",
            "ego_response",
            "throttle",
            "forbid the M3100-style global high-speed throttle suppression pattern",
            "local_throttle_suppression",
            0.0,
            0.25,
        ),
        (
            "m3103-rule-local-obstacle-arbitration",
            "local_obstacle_hard_safety_arbitration",
            "p1",
            "ego_response;obstacle_slots",
            "steer;brake;throttle",
            "apply small obstacle avoidance and braking only above local actor-visible urgency thresholds",
            "local_obstacle_brake",
            0.0,
            0.4,
        ),
        (
            "m3103-rule-local-edge-arbitration",
            "local_edge_hard_safety_arbitration",
            "p1",
            "ego_response;road_left_boundary;road_right_boundary",
            "steer;brake;throttle",
            "apply small road-centering and braking only above local actor-visible edge urgency thresholds",
            "local_edge_brake",
            0.0,
            0.3,
        ),
        (
            "m3103-rule-direct-action-bound",
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
    gains = V4_POLICY_CONFIG["gains"]
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
            "exclusion_id": f"m3103-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(exclusions, start=1)
    ]


def build_no_regression_guard_rows(regression_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "guard_id": "m3103-no-regression-speed-floor-stress",
            "guard_family": "speed_floor_preservation",
            "source_row": "M3095 speed_floor_stress 16/16 success",
            "guard_expression": "preserve v2 fallback speed_floor recovery; no global throttle suppression below preserve threshold",
            "status_pass": not _bool(V4_POLICY_CONFIG["thresholds"].get("global_high_speed_throttle_suppression_enabled")),
            "expected_preservation": "speed_floor_stress should not reopen M3100 speed_too_low pattern before measurement",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m3103-no-regression-row-0014",
            "guard_family": "m3100_regression_row",
            "source_row": "m3100-same-row-comparison-0014",
            "guard_expression": "do not apply broad high-speed edge throttle suppression to M3095-success collision_lateral_intrusion parent row",
            "status_pass": any(row.get("comparison_id") == "m3100-same-row-comparison-0014" for row in regression_rows),
            "expected_preservation": "M3095 success row must be explicitly audited before any v4 measurement",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m3103-no-regression-row-0048",
            "guard_family": "m3100_regression_row",
            "source_row": "m3100-same-row-comparison-0048",
            "guard_expression": "do not suppress low-speed speed-floor recovery on M3095-success speed_floor_stress parent row",
            "status_pass": any(row.get("comparison_id") == "m3100-same-row-comparison-0048" for row in regression_rows),
            "expected_preservation": "M3095 speed-floor success row must be explicitly audited before any v4 measurement",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m3103-no-regression-comparison-complete",
            "guard_family": "comparison_artifact",
            "source_row": "M3100 same-row comparison",
            "guard_expression": "all known M3100 regressions are represented as materialization guards",
            "status_pass": len(regression_rows) == 2,
            "expected_preservation": "two regression guards from M3102",
            "claim_boundary": CLAIM_SCOPE,
        },
    ]
    return rows


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("policy_config_materialized", "materialization", True, "direct_action_policy_config.json"),
        ("rule_table_materialized", "materialization", True, "safety_reflex_rule_rows.csv"),
        ("no_regression_guards_materialized", "guard", True, "no_regression_guard_rows.csv"),
        ("actor_input_exclusions_materialized", "guard", True, "actor_input_exclusion_rows.csv"),
        ("claim_boundary_guards_materialized", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3104 audit manifest"),
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
            "claim_id": f"m3103-{claim_id}",
            "claim_family": family,
            "allowed_in_m3103": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3103-{claim_id}",
            "claim_family": family,
            "allowed_in_m3103": False,
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
        "priority": 30990,
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
        "hypothesis": "A bounded result audit can accept or reject the M3103 v4 v2-fallback no-regression hard-safety repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "safety_reflex_rule_rows.csv"),
                str(output_dir / "no_regression_guard_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit v4 v2-fallback no-regression materialization before measurement admission"],
            "derived_from": [MILESTONE_ID, M3102_ID, M3100_ID, M3095_ID, M3093_ID],
            "blocked_by": [
                "M3103 materialization artifacts require audit before measurement",
                "materialization cannot support repair-success or driver-performance claims",
            ],
            "supersedes": ["direct measurement admission without v4 materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3104 must audit M3103 summary rule config no-regression exclusion claim and gate artifacts",
            "M3104 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3104 must reject measurement validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3104 must select exactly one measurement artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training",
            "do not treat M3103 materialization as driver-performance repair-success robustness-result or self-ID evidence",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair",
            "evidence_axis": "v4_no_regression_materialization_result_audit",
            "evidence_increment": "audits the M3103 v4 no-regression repair materialization artifacts before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3103 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "route to measurement only if M3103 is complete and claim-safe",
            ],
            "fallback_plan": [
                "route to materialization repair if artifacts are incomplete",
                "route to measurement preflight if artifacts are complete and claim-safe",
                "route to stop if deployment boundary is not preservable",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3103 completes v4 no-regression materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3103 v4 no-regression repair materialization artifacts",
            "admission_evidence": ["M3103 summary rule config no-regression exclusion claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3104 status queue scoreboard research log and review",
                "one follow-up manifest only if M3104 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3104 accepts or rejects M3103 as complete and claim-safe",
                "next measurement, artifact-repair, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3104 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3104; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3103 materialization artifacts only.",
            "negative_result_policy": "Reject or repair M3103 artifacts rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3103 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 3,
            "same_public_gate_repair_count": 2,
            "evidence_expansion": "audits the new v4 materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3104 prepares a measurement route decision",
            "must_synthesize_if": [
                "M3104 cannot accept M3103 as complete and claim-safe",
                "M3104 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result or self-ID evidence",
                "M3104 cannot select exactly one measurement repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3104 audits M3103 artifact row counts gates actor contract and claim boundaries",
            "M3104 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3104 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3104 hides M3103 failures or missing artifacts",
            "M3104 treats M3103 materialization as measurement validation or performance verdict",
            "M3104 changes actor input or action contract",
            "M3104 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3104 audits M3103 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_v4_no_regression_repair_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _probe_observation(*, speed_mps: float, obstacle: bool = False, edge_urgent: bool = False) -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = speed_mps / 20.0
    left_y = 0.02 if edge_urgent else 0.25
    right_y = -0.02 if edge_urgent else -0.25
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
        ("low_speed_floor_preservation", _probe_observation(speed_mps=3.0)),
        ("local_high_speed_obstacle", _probe_observation(speed_mps=17.0, obstacle=True)),
        ("local_high_speed_edge", _probe_observation(speed_mps=16.0, edge_urgent=True)),
    ]
    rows = []
    for name, obs in probes:
        v2_action = speed_floor_aware_direct_action(obs, V2_POLICY_CONFIG)
        v4_action = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        rows.append(
            {
                "probe_id": f"m3103-probe-{name}",
                "status_pass": bool(v4_action.shape == (ACTION_DIM,) and np.all(np.isfinite(v4_action)) and np.max(np.abs(v4_action)) <= 1.0),
                "v2_steer": float(v2_action[0]),
                "v2_throttle": float(v2_action[1]),
                "v2_brake": float(v2_action[2]),
                "v4_steer": float(v4_action[0]),
                "v4_throttle": float(v4_action[1]),
                "v4_brake": float(v4_action[2]),
            }
        )
    return rows


def gate(gate_id: str, family: str, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3103-{gate_id}",
        "gate_family": family,
        "status_pass": str(observed) == str(expected),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    no_regression_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    follow_up_manifest_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    config = V4_POLICY_CONFIG
    synthesis_text = str(source.get("m3102_synthesis_text", ""))
    comparison_rows = source.get("m3100_comparison_rows", [])
    regression_rows = source.get("m3100_regression_rows", [])
    residual_counts = Counter(str(row.get("m3100_termination_reason", "")) for row in comparison_rows if not _bool(row.get("m3100_success")))
    return [
        gate("m3102_synthesis_present", "source", bool(synthesis_text), True, "lineage_invalid"),
        gate("m3102_route_marker", "source", "route_to_m3103_v4_v2_fallback_no_regression_hard_safety_repair_materialization" in synthesis_text, True, "lineage_invalid"),
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), True, "lineage_invalid"),
        gate("m3100_status_pass", "source", source["m3100_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3100_gate_matrix_pass", "source", source["m3100_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3095_status_pass", "source", source["m3095_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3095_gate_matrix_pass", "source", source["m3095_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3093_status_pass", "source", source["m3093_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3093_gate_matrix_pass", "source", source["m3093_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3100_comparison_rows", "source", len(comparison_rows), 64, "metric_artifact"),
        gate("m3100_regression_rows", "source", len(regression_rows), 2, "metric_artifact"),
        gate("m3100_collision_residual_count", "source", residual_counts.get("obstacle_collision", 0), 5, "behavior_regression"),
        gate("policy_observation_shape", "contract", config.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", config.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_action_components", "contract", "|".join(config.get("output_components", [])), "|".join(ACTION_COMPONENTS), "contract_violation"),
        gate("policy_output_semantics", "contract", config.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_required", "contract", config.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("global_high_speed_throttle_suppression_disabled", "repair_config", config["thresholds"].get("global_high_speed_throttle_suppression_enabled"), False, "behavior_regression"),
        gate("fallback_base_policy_id", "repair_config", config["thresholds"].get("fallback_base_policy_id"), "m3093_speed_floor_aware_balanced_direct_action_repair_v2", "lineage_invalid"),
        gate("rule_rows_present", "artifact", len(rule_rows) >= 5, True, "metric_artifact"),
        gate("no_regression_rows_present", "artifact", len(no_regression_rows) >= 4, True, "metric_artifact"),
        gate("no_regression_rows_pass", "artifact", all(_bool(row.get("status_pass")) for row in no_regression_rows), True, "behavior_regression"),
        gate("exclusion_rows_pass", "contract", all(_bool(row.get("status_pass")) for row in exclusion_rows), True, "contract_violation"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), True, "objective_overfit"),
        gate("probe_rows_pass", "runtime_api", all(_bool(row.get("status_pass")) for row in probe_rows), True, "contract_violation"),
        gate("low_speed_probe_preserves_positive_throttle", "repair_config", probe_rows[0]["v4_throttle"] > 0.0, True, "behavior_regression"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
        gate("required_artifacts_present", "process", required_artifacts_present, True, "metric_artifact"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3103 Active Safety Driver v4 v2-Fallback No-Regression Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- policy id: `{summary['policy_id']}`",
            f"- rule rows: {summary['rule_row_count']}",
            f"- no-regression guard rows: {summary['no_regression_guard_row_count']}",
            f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- low-speed probe throttle: {summary['low_speed_probe_throttle']}",
            f"- local obstacle probe brake: {summary['local_high_speed_obstacle_probe_brake']}",
            f"- local edge probe brake: {summary['local_high_speed_edge_probe_brake']}",
            "",
            "## Interpretation",
            "",
            "M3103 materializes a v4 v2-fallback no-regression direct-action repair package. It does not run an environment reset, step, rollout, replay, fitting, PPO, training, measurement, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.",
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
    m3102_synthesis: Path,
    m3100_dir: Path,
    m3095_dir: Path,
    m3093_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3102_synthesis=m3102_synthesis,
        m3100_dir=m3100_dir,
        m3095_dir=m3095_dir,
        m3093_dir=m3093_dir,
    )
    rule_rows = build_rule_rows()
    no_regression_rows = build_no_regression_guard_rows(source["m3100_regression_rows"])
    exclusion_rows = build_actor_input_exclusion_rows()
    write_json(paths["direct_action_policy_config"], V4_POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    probe_rows = _probe_rows()
    for path, rows, fieldnames in (
        (paths["safety_reflex_rule_rows"], rule_rows, RULE_FIELDNAMES),
        (paths["no_regression_guard_rows"], no_regression_rows, NO_REGRESSION_FIELDNAMES),
        (paths["actor_input_exclusion_rows"], exclusion_rows, EXCLUSION_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = build_gate_rows(
        source=source,
        rule_rows=rule_rows,
        no_regression_rows=no_regression_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        probe_rows=probe_rows,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
        required_artifacts_present=present,
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    probe_by_id = {row["probe_id"]: row for row in probe_rows}
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_preflight_pass"
            if status_pass
            else "active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": present,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "policy_id": POLICY_ID,
        "rule_row_count": len(rule_rows),
        "no_regression_guard_row_count": len(no_regression_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "m3100_status_pass": _bool(source["m3100_summary"].get("status_pass", False)),
        "m3095_status_pass": _bool(source["m3095_summary"].get("status_pass", False)),
        "m3093_status_pass": _bool(source["m3093_summary"].get("status_pass", False)),
        "m3100_regression_row_count": len(source["m3100_regression_rows"]),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "action = v4_v2_fallback_no_regression_hard_safety_direct_action(obs72) -> [steer, throttle, brake]",
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "measurement_run": False,
        "validation_run": False,
        "training_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "low_speed_probe_throttle": probe_by_id["m3103-probe-low_speed_floor_preservation"]["v4_throttle"],
        "local_high_speed_obstacle_probe_brake": probe_by_id["m3103-probe-local_high_speed_obstacle"]["v4_brake"],
        "local_high_speed_edge_probe_brake": probe_by_id["m3103-probe-local_high_speed_edge"]["v4_brake"],
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_v4_v2_fallback_no_regression_hard_safety_repair_materialization_route_to_m3104_result_audit",
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
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3102-synthesis", type=Path, default=DEFAULT_M3102_SYNTHESIS)
    parser.add_argument("--m3100-dir", type=Path, default=DEFAULT_M3100_DIR)
    parser.add_argument("--m3095-dir", type=Path, default=DEFAULT_M3095_DIR)
    parser.add_argument("--m3093-dir", type=Path, default=DEFAULT_M3093_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3102_synthesis=args.m3102_synthesis,
        m3100_dir=args.m3100_dir,
        m3095_dir=args.m3095_dir,
        m3093_dir=args.m3093_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['rule_row_count']}")
    print(f"no_regression_guard_rows={summary['no_regression_guard_row_count']}")
    print(f"claim_boundary_rows={summary['claim_boundary_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
