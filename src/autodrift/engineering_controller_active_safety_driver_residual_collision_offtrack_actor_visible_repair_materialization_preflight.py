"""Materialize M3110 actor-visible residual collision/offtrack repair artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    V4_POLICY_CONFIG,
    _hard_safety_features as v4_hard_safety_features,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-materialization-preflight"
)
NEXT_ID = (
    "m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-materialization-result-audit"
)
M3109_ID = (
    "m3109-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "failure-decomposition-result-audit"
)
M3108_ID = (
    "m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "failure-decomposition-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)
M3103_ID = (
    "m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-materialization-preflight"
)
POLICY_ID = "m3110_residual_collision_offtrack_actor_visible_repair"

DEFAULT_M3109_AUDIT = Path(f"docs/{M3109_ID}.md")
DEFAULT_M3108_DIR = Path(
    "runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "failure_decomposition_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3103_DIR = Path(
    "runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3110 Active Safety Driver residual collision/offtrack actor-visible repair "
    "materialization only; artifacts may define obs72 to direct action3 [steer "
    "throttle brake] repair rules, config, residual guards, doc, and M3111 audit "
    "manifest. No reset, step, rollout, replay, fitting, PPO, training, measurement, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal "
    "driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
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
REPAIR_GUARD_FIELDNAMES = [
    "guard_id",
    "source_requirement_id",
    "requirement_family",
    "priority",
    "affected_group",
    "source_row_count",
    "guard_expression",
    "actor_visible_feature_groups",
    "output_channels",
    "preserves_speed_floor",
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
    "allowed_in_m3110",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


M3110_POLICY_CONFIG: dict[str, Any] = deepcopy(V4_POLICY_CONFIG)
M3110_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "repair_route": "residual_collision_offtrack_actor_visible_repair",
        "repair_scope": "materialization_only_no_measurement_claim",
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
    }
)
M3110_POLICY_CONFIG["gains"].update(
    {
        "residual_obstacle_steer": 0.30,
        "residual_obstacle_brake": 0.30,
        "residual_edge_steer": 0.22,
        "residual_edge_brake": 0.18,
        "residual_stability_steer_damping": 0.12,
        "residual_throttle_suppression": 0.10,
    }
)
M3110_POLICY_CONFIG["thresholds"].update(
    {
        "fallback_base_policy_id": "m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair",
        "residual_actor_visible_overlay_enabled": True,
        "residual_repair_speed_mps": 12.0,
        "residual_obstacle_urgency_trigger": 0.42,
        "residual_edge_urgency_trigger": 0.62,
        "speed_floor_preserve_below_mps": 7.5,
        "residual_stability_trigger": 0.30,
        "residual_requirement_families": [
            "collision_lateral_intrusion_guard",
            "offtrack_boundary_recovery_guard",
            "speed_floor_preservation",
            "residual_collision_reduction",
            "residual_offtrack_recovery",
            "deployable_actor_boundary",
            "claim_boundary_audit",
        ],
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
    default = _float(M3110_POLICY_CONFIG[section][key])
    return _float(config.get(section, {}).get(key), default)


def _brake_to_physical(action_brake: float) -> float:
    return _clip01((action_brake + 1.0) / 2.0)


def _brake_from_physical(physical_brake: float) -> float:
    return -1.0 + 2.0 * _clip01(physical_brake)


def residual_collision_offtrack_actor_visible_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3110 direct [steer, throttle, brake] from actor-visible obs72 only."""

    cfg: Mapping[str, Any] = config or M3110_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    action = np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG), dtype=np.float32).copy()
    features = v4_hard_safety_features(obs, cfg)
    thresholds = cfg.get("thresholds", {})
    gains = cfg.get("gains", {})

    speed = features["vx_body"]
    speed_risk = _clip01((speed - _float(thresholds.get("residual_repair_speed_mps"))) / 8.0)
    obstacle_excess = _clip01(
        (features["obstacle_urgency"] - _float(thresholds.get("residual_obstacle_urgency_trigger")))
        / max(1.0 - _float(thresholds.get("residual_obstacle_urgency_trigger")), 1e-6)
    )
    edge_excess = _clip01(
        (features["edge_urgency"] - _float(thresholds.get("residual_edge_urgency_trigger")))
        / max(1.0 - _float(thresholds.get("residual_edge_urgency_trigger")), 1e-6)
    )

    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    steer_rate = float(obs[6])
    stability_energy = (
        _clip01(abs(vy_body) / 4.0)
        + _clip01(abs(yaw_rate) / 1.5)
        + _clip01(abs(ay_body) / 8.0)
        + _clip01(abs(steer_rate) / 1.0)
    ) / 4.0
    stability_excess = _clip01(stability_energy - _float(thresholds.get("residual_stability_trigger")))

    obstacle_risk = speed_risk * obstacle_excess
    edge_risk = speed_risk * edge_excess
    residual_risk = max(obstacle_risk, edge_risk)

    if residual_risk > 0.0:
        action[0] += (
            _float(gains.get("residual_obstacle_steer")) * features["obstacle_avoid_direction"] * obstacle_risk
            + _float(gains.get("residual_edge_steer")) * features["road_center_error"] * edge_risk
        )
        if stability_excess > 0.0:
            damping_direction = -np.sign(vy_body + 0.5 * yaw_rate)
            action[0] += _float(gains.get("residual_stability_steer_damping")) * float(damping_direction) * residual_risk * stability_excess

        brake_physical = _brake_to_physical(float(action[2]))
        brake_physical += (
            _float(gains.get("residual_obstacle_brake")) * obstacle_risk
            + _float(gains.get("residual_edge_brake")) * edge_risk
        )
        action[2] = _brake_from_physical(brake_physical)

        if speed > _float(thresholds.get("speed_floor_preserve_below_mps")):
            action[1] -= _float(gains.get("residual_throttle_suppression")) * residual_risk

    return np.clip(action, -1.0, 1.0).astype(np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "safety_reflex_rule_rows": output_dir / "safety_reflex_rule_rows.csv",
        "residual_repair_guard_rows": output_dir / "residual_repair_guard_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3109_audit: Path, m3108_dir: Path, m3105_dir: Path, m3103_dir: Path) -> dict[str, Any]:
    paths = {
        "m3109_audit": m3109_audit,
        "m3108_summary": m3108_dir / "summary.json",
        "m3108_residual_failure_rows": m3108_dir / "residual_failure_rows.csv",
        "m3108_repair_requirement_rows": m3108_dir / "residual_repair_requirement_rows.csv",
        "m3108_gate_rows": m3108_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3103_summary": m3103_dir / "summary.json",
        "m3103_policy_config": m3103_dir / "direct_action_policy_config.json",
        "m3103_gate_rows": m3103_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3109_audit_text": paths["m3109_audit"].read_text(encoding="utf-8") if exists["m3109_audit"] else "",
        "m3108_summary": read_json(paths["m3108_summary"]) if exists["m3108_summary"] else {},
        "m3108_residual_failure_rows": read_csv_rows(paths["m3108_residual_failure_rows"]),
        "m3108_repair_requirement_rows": read_csv_rows(paths["m3108_repair_requirement_rows"]),
        "m3108_gate_rows": read_csv_rows(paths["m3108_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3103_summary": read_json(paths["m3103_summary"]) if exists["m3103_summary"] else {},
        "m3103_policy_config": read_json(paths["m3103_policy_config"]) if exists["m3103_policy_config"] else {},
        "m3103_gate_rows": read_csv_rows(paths["m3103_gate_rows"]),
    }


def build_rule_rows() -> list[dict[str, Any]]:
    gains = M3110_POLICY_CONFIG["gains"]
    specs = [
        (
            "m3110-rule-v4-fallback-base",
            "v4_no_regression_fallback_base",
            "p0",
            "ego_response;road_boundaries;obstacle_slots",
            "steer;throttle;brake",
            "start from the M3103 v4 no-regression direct-action function",
            "not_applicable",
            -1.0,
            1.0,
        ),
        (
            "m3110-rule-residual-collision-lateral-intrusion",
            "residual_collision_lateral_intrusion_guard",
            "p0",
            "ego_response;obstacle_slots",
            "steer;brake;throttle",
            "increase local obstacle avoidance and braking only when actor-visible obstacle urgency and speed risk are both active",
            "residual_obstacle_brake",
            0.0,
            0.5,
        ),
        (
            "m3110-rule-residual-offtrack-boundary-recovery",
            "residual_offtrack_boundary_recovery_guard",
            "p0",
            "ego_response;road_left_boundary;road_right_boundary",
            "steer;brake;throttle",
            "increase boundary centering and braking only when actor-visible edge urgency and speed risk are both active",
            "residual_edge_brake",
            0.0,
            0.35,
        ),
        (
            "m3110-rule-speed-floor-preservation",
            "speed_floor_preservation",
            "p0",
            "ego_response;obstacle_slots;road_boundaries",
            "throttle;brake",
            "preserve M3105 zero speed-too-low guard by forbidding residual throttle suppression below the speed-floor preserve threshold",
            "residual_throttle_suppression",
            0.0,
            0.2,
        ),
        (
            "m3110-rule-stability-damping",
            "residual_boundary_stability_damping",
            "p1",
            "ego_response",
            "steer;brake",
            "apply small actor-visible lateral and yaw damping only inside residual obstacle or edge risk",
            "residual_stability_steer_damping",
            0.0,
            0.25,
        ),
        (
            "m3110-rule-direct-action-bound",
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


def build_residual_repair_guard_rows(requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings = {
        "collision_lateral_intrusion_guard": (
            "actor-visible obstacle urgency plus speed risk produces local steer and brake overlay",
            "ego_response;obstacle_slots",
            "steer;brake;throttle",
            True,
        ),
        "offtrack_boundary_recovery_guard": (
            "actor-visible edge urgency plus speed risk produces boundary centering and brake overlay",
            "ego_response;road_left_boundary;road_right_boundary",
            "steer;brake;throttle",
            True,
        ),
        "speed_floor_preservation": (
            "residual throttle suppression is disabled below speed_floor_preserve_below_mps",
            "ego_response",
            "throttle;brake",
            True,
        ),
        "residual_collision_reduction": (
            "collision count remains a named measurement gate and obstacle collision rows get a direct local overlay guard",
            "ego_response;obstacle_slots",
            "steer;brake",
            True,
        ),
        "residual_offtrack_recovery": (
            "offtrack count lateral_rmse and sideslip remain separate measurement gates with boundary recovery overlay",
            "ego_response;road_boundaries",
            "steer;brake",
            True,
        ),
        "deployable_actor_boundary": (
            "obs72 actor-visible input and direct action3 output are kept as hard materialization gates",
            "all_actor_visible_features",
            "steer;throttle;brake",
            True,
        ),
        "claim_boundary_audit": (
            "M3111 audit manifest is registered before any measurement or repair-success claim",
            "none",
            "none",
            True,
        ),
    }
    rows = []
    for index, requirement in enumerate(requirement_rows, start=1):
        family = str(requirement.get("requirement_family", ""))
        expression, inputs, outputs, preserves_speed_floor = mappings.get(
            family,
            ("requirement preserved as materialization guard", "actor_visible_features", "steer;throttle;brake", True),
        )
        rows.append(
            {
                "guard_id": f"m3110-residual-repair-guard-{index:04d}",
                "source_requirement_id": requirement.get("requirement_id", ""),
                "requirement_family": family,
                "priority": requirement.get("priority", ""),
                "affected_group": requirement.get("affected_group", ""),
                "source_row_count": requirement.get("row_count", ""),
                "guard_expression": expression,
                "actor_visible_feature_groups": inputs,
                "output_channels": outputs,
                "preserves_speed_floor": preserves_speed_floor,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "status_pass": family in mappings,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


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
            "exclusion_id": f"m3110-exclusion-{index:04d}",
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
        ("residual_repair_guards_materialized", "guard", True, "residual_repair_guard_rows.csv"),
        ("actor_input_exclusions_materialized", "guard", True, "actor_input_exclusion_rows.csv"),
        ("claim_boundary_guards_materialized", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3111 audit manifest"),
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
            "claim_id": f"m3110-{claim_id}",
            "claim_family": family,
            "allowed_in_m3110": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3110-{claim_id}",
            "claim_family": family,
            "allowed_in_m3110": False,
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
        "priority": 31060,
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
        "hypothesis": "A bounded result audit can accept or reject the M3110 residual collision/offtrack actor-visible repair materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "safety_reflex_rule_rows.csv"),
                str(output_dir / "residual_repair_guard_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit residual collision/offtrack actor-visible repair materialization before measurement admission"],
            "derived_from": [MILESTONE_ID, M3109_ID, M3108_ID, M3105_ID, M3103_ID],
            "blocked_by": [
                "M3110 materialization artifacts require audit before measurement",
                "materialization cannot support repair-success or driver-performance claims",
            ],
            "supersedes": ["direct measurement admission without residual repair materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3111 must audit M3110 summary rule config residual guard exclusion claim and gate artifacts",
            "M3111 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3111 must reject measurement validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3111 must select exactly one measurement artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking promotion high-fidelity simulation fitting PPO or training",
            "do not treat M3110 materialization as driver-performance repair-success robustness-result or self-ID evidence",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_collision_offtrack_repair",
            "evidence_axis": "residual_collision_offtrack_materialization_result_audit",
            "evidence_increment": "audits the M3110 residual repair materialization artifacts before measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3110 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "route to measurement only if M3110 is complete and claim-safe",
            ],
            "fallback_plan": [
                "route to materialization repair if artifacts are incomplete",
                "route to measurement preflight if artifacts are complete and claim-safe",
                "route to stop if deployment boundary is not preservable",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3110 completes residual collision/offtrack actor-visible repair materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3110 residual repair materialization artifacts",
            "admission_evidence": ["M3110 summary rule config residual guard exclusion claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3111 status queue scoreboard research log and review",
                "one follow-up manifest only if M3111 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3111 accepts or rejects M3110 as complete and claim-safe",
                "next measurement artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3111 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3111; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3110 materialization artifacts only.",
            "negative_result_policy": "Reject or repair M3110 artifacts rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3110 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new residual repair materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3111 prepares a measurement route decision",
            "must_synthesize_if": [
                "M3111 cannot accept M3110 as complete and claim-safe",
                "M3111 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result or self-ID evidence",
                "M3111 cannot select exactly one measurement repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3111 audits M3110 artifact row counts gates actor contract and claim boundaries",
            "M3111 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3111 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3111 hides M3110 failures or missing artifacts",
            "M3111 treats M3110 materialization as measurement validation or performance verdict",
            "M3111 changes actor input or action contract",
            "M3111 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3111 audits M3110 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_residual_repair_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3110-{gate_id}",
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


def _probe_observation(*, speed_mps: float, obstacle: bool = False, edge_urgent: bool = False) -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = speed_mps / 20.0
    left_y = 0.03 if edge_urgent else 0.25
    right_y = -0.20 if edge_urgent else -0.25
    for index in range(8):
        obs[12 + index * 2] = 0.05 * (index + 1)
        obs[12 + index * 2 + 1] = left_y
        obs[28 + index * 2] = 0.05 * (index + 1)
        obs[28 + index * 2 + 1] = right_y
    if obstacle:
        obs[44] = 1.0
        obs[45] = 0.08
        obs[46] = 0.02
    return obs


def _probe_rows() -> list[dict[str, Any]]:
    probes = [
        ("low_speed_floor_preservation", _probe_observation(speed_mps=3.0, obstacle=True)),
        ("residual_high_speed_obstacle", _probe_observation(speed_mps=18.0, obstacle=True)),
        ("residual_high_speed_edge", _probe_observation(speed_mps=17.0, edge_urgent=True)),
    ]
    rows = []
    for name, obs in probes:
        v4_action = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        m3110_action = residual_collision_offtrack_actor_visible_direct_action(obs, M3110_POLICY_CONFIG)
        rows.append(
            {
                "probe_id": f"m3110-probe-{name}",
                "status_pass": bool(
                    m3110_action.shape == (ACTION_DIM,)
                    and np.all(np.isfinite(m3110_action))
                    and np.max(np.abs(m3110_action)) <= 1.0
                ),
                "v4_steer": float(v4_action[0]),
                "v4_throttle": float(v4_action[1]),
                "v4_brake": float(v4_action[2]),
                "m3110_steer": float(m3110_action[0]),
                "m3110_throttle": float(m3110_action[1]),
                "m3110_brake": float(m3110_action[2]),
            }
        )
    return rows


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    repair_guard_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    follow_up_manifest_exists: bool,
    present: bool,
) -> list[dict[str, Any]]:
    residual_rows = source["m3108_residual_failure_rows"]
    requirement_rows = source["m3108_repair_requirement_rows"]
    requirement_families = {str(row.get("requirement_family", "")) for row in requirement_rows}
    expected_requirement_families = set(M3110_POLICY_CONFIG["thresholds"]["residual_requirement_families"])
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in residual_rows)
    axis_counts = Counter(str(row.get("axis_id", "")) for row in residual_rows)
    audit_text = str(source.get("m3109_audit_text", ""))
    probe_by_id = {row["probe_id"]: row for row in probe_rows}
    low_speed_probe = probe_by_id["m3110-probe-low_speed_floor_preservation"]
    obstacle_probe = probe_by_id["m3110-probe-residual_high_speed_obstacle"]
    edge_probe = probe_by_id["m3110-probe-residual_high_speed_edge"]
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3109_audit_present", "lineage", bool(audit_text), "audit text", "present", "lineage_invalid"),
        gate("m3109_route_marker", "lineage", "accept_m3108_decomposition_route_to_m3110_residual_collision_offtrack_actor_visible_repair_materialization" in audit_text, "route marker", "present", "lineage_invalid"),
        gate("m3108_status_pass", "lineage", _bool(source["m3108_summary"].get("status_pass")), source["m3108_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3108_gate_matrix_pass", "lineage", _bool(source["m3108_summary"].get("gate_matrix_pass")), source["m3108_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass")), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3103_status_pass", "lineage", _bool(source["m3103_summary"].get("status_pass")), source["m3103_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("residual_rows", "metric", len(residual_rows) == 7, len(residual_rows), 7, "metric_artifact"),
        gate("residual_collision_rows", "metric", termination_counts.get("obstacle_collision", 0) == 5, termination_counts.get("obstacle_collision", 0), 5, "metric_artifact"),
        gate("residual_offtrack_rows", "metric", termination_counts.get("off_track", 0) == 2, termination_counts.get("off_track", 0), 2, "metric_artifact"),
        gate("speed_too_low_rows", "metric", termination_counts.get("speed_too_low", 0) == 0, termination_counts.get("speed_too_low", 0), 0, "behavior_regression"),
        gate("collision_lateral_intrusion_rows", "metric", axis_counts.get("collision_lateral_intrusion", 0) == 3, axis_counts.get("collision_lateral_intrusion", 0), 3, "metric_artifact"),
        gate("offtrack_boundary_recovery_rows", "metric", axis_counts.get("offtrack_boundary_recovery", 0) == 4, axis_counts.get("offtrack_boundary_recovery", 0), 4, "metric_artifact"),
        gate("requirement_families_complete", "metric", expected_requirement_families.issubset(requirement_families), sorted(requirement_families), sorted(expected_requirement_families), "metric_artifact"),
        gate("policy_observation_shape", "contract", M3110_POLICY_CONFIG.get("observation_shape") == P0_OBSERVATION_DIM, M3110_POLICY_CONFIG.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", M3110_POLICY_CONFIG.get("action_shape") == ACTION_DIM, M3110_POLICY_CONFIG.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_action_components", "contract", M3110_POLICY_CONFIG.get("output_components") == list(ACTION_COMPONENTS), M3110_POLICY_CONFIG.get("output_components"), list(ACTION_COMPONENTS), "contract_violation"),
        gate("runtime_base_policy_required", "contract", M3110_POLICY_CONFIG.get("runtime_base_policy_required") is False, M3110_POLICY_CONFIG.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("checkpoint_model_required", "contract", M3110_POLICY_CONFIG.get("checkpoint_model_required") is False, M3110_POLICY_CONFIG.get("checkpoint_model_required"), False, "contract_violation"),
        gate("recurrent_hidden_state_required", "contract", M3110_POLICY_CONFIG.get("recurrent_hidden_state_required") is False, M3110_POLICY_CONFIG.get("recurrent_hidden_state_required"), False, "contract_violation"),
        gate("rule_rows_present", "artifact", len(rule_rows) >= 6, len(rule_rows), ">=6", "metric_artifact"),
        gate("repair_guard_rows_present", "artifact", len(repair_guard_rows) == len(requirement_rows), len(repair_guard_rows), len(requirement_rows), "metric_artifact"),
        gate("repair_guard_rows_pass", "artifact", all(_bool(row.get("status_pass")) for row in repair_guard_rows), "all", "pass", "metric_artifact"),
        gate("exclusion_rows_pass", "contract", all(_bool(row.get("status_pass")) for row in exclusion_rows), "all", "pass", "contract_violation"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "objective_overfit"),
        gate("probe_rows_pass", "runtime_api", all(_bool(row.get("status_pass")) for row in probe_rows), "all", "pass", "contract_violation"),
        gate("low_speed_probe_preserves_throttle", "behavior_guard", low_speed_probe["m3110_throttle"] >= low_speed_probe["v4_throttle"] - 1e-6, low_speed_probe["m3110_throttle"], f">= {low_speed_probe['v4_throttle']}", "behavior_regression"),
        gate("obstacle_probe_brake_not_lower", "behavior_guard", obstacle_probe["m3110_brake"] >= obstacle_probe["v4_brake"] - 1e-6, obstacle_probe["m3110_brake"], f">= {obstacle_probe['v4_brake']}", "behavior_regression"),
        gate("edge_probe_brake_not_lower", "behavior_guard", edge_probe["m3110_brake"] >= edge_probe["v4_brake"] - 1e-6, edge_probe["m3110_brake"], f">= {edge_probe['v4_brake']}", "behavior_regression"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3110 Residual Collision/Offtrack Actor-Visible Repair Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- policy id: `{summary['policy_id']}`",
            f"- source residual rows: {summary['source_residual_row_count']}",
            f"- residual collision rows: {summary['source_residual_collision_count']}",
            f"- residual offtrack rows: {summary['source_residual_offtrack_count']}",
            f"- residual speed-too-low rows: {summary['source_residual_speed_too_low_count']}",
            f"- rule rows: {summary['rule_row_count']}",
            f"- residual repair guard rows: {summary['residual_repair_guard_row_count']}",
            f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- low-speed probe throttle: {summary['low_speed_probe_throttle']}",
            f"- residual obstacle probe brake: {summary['residual_high_speed_obstacle_probe_brake']}",
            f"- residual edge probe brake: {summary['residual_high_speed_edge_probe_brake']}",
            "",
            "## Interpretation",
            "",
            "M3110 materializes an actor-visible residual collision/offtrack direct-action repair package. It does not run an environment reset, step, rollout, replay, fitting, PPO, training, measurement, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.",
            "",
            "The materialized function remains:",
            "",
            "```text",
            "obs72 actor-visible input -> direct action3 [steer, throttle, brake]",
            "runtime_base_policy_required: false",
            "checkpoint_model_required: false",
            "recurrent_hidden_state_required: false",
            "```",
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
    m3109_audit: Path,
    m3108_dir: Path,
    m3105_dir: Path,
    m3103_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3109_audit=m3109_audit, m3108_dir=m3108_dir, m3105_dir=m3105_dir, m3103_dir=m3103_dir)
    residual_rows = source["m3108_residual_failure_rows"]
    requirement_rows = source["m3108_repair_requirement_rows"]
    rule_rows = build_rule_rows()
    repair_guard_rows = build_residual_repair_guard_rows(requirement_rows)
    exclusion_rows = build_actor_input_exclusion_rows()
    write_json(paths["direct_action_policy_config"], M3110_POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["safety_reflex_rule_rows"], rule_rows, RULE_FIELDNAMES),
        (paths["residual_repair_guard_rows"], repair_guard_rows, REPAIR_GUARD_FIELDNAMES),
        (paths["actor_input_exclusion_rows"], exclusion_rows, EXCLUSION_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    probe_rows = _probe_rows()
    gates = build_gate_rows(
        source=source,
        rule_rows=rule_rows,
        repair_guard_rows=repair_guard_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        probe_rows=probe_rows,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
        present=present,
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in residual_rows)
    probe_by_id = {row["probe_id"]: row for row in probe_rows}
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight_pass"
            if status_pass
            else "active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": present,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "policy_id": POLICY_ID,
        "source_residual_row_count": len(residual_rows),
        "source_residual_collision_count": termination_counts.get("obstacle_collision", 0),
        "source_residual_offtrack_count": termination_counts.get("off_track", 0),
        "source_residual_speed_too_low_count": termination_counts.get("speed_too_low", 0),
        "source_repair_requirement_row_count": len(requirement_rows),
        "rule_row_count": len(rule_rows),
        "residual_repair_guard_row_count": len(repair_guard_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "candidate_observation_shape": P0_OBSERVATION_DIM,
        "candidate_action_shape": ACTION_DIM,
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "action = residual_collision_offtrack_actor_visible_direct_action(obs72) -> [steer, throttle, brake]",
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
        "low_speed_probe_throttle": probe_by_id["m3110-probe-low_speed_floor_preservation"]["m3110_throttle"],
        "residual_high_speed_obstacle_probe_brake": probe_by_id["m3110-probe-residual_high_speed_obstacle"]["m3110_brake"],
        "residual_high_speed_edge_probe_brake": probe_by_id["m3110-probe-residual_high_speed_edge"]["m3110_brake"],
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_route_to_m3111_result_audit",
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
    parser.add_argument("--m3109-audit", type=Path, default=DEFAULT_M3109_AUDIT)
    parser.add_argument("--m3108-dir", type=Path, default=DEFAULT_M3108_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3103-dir", type=Path, default=DEFAULT_M3103_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3109_audit=args.m3109_audit,
        m3108_dir=args.m3108_dir,
        m3105_dir=args.m3105_dir,
        m3103_dir=args.m3103_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['rule_row_count']}")
    print(f"residual_repair_guard_rows={summary['residual_repair_guard_row_count']}")
    print(f"claim_boundary_rows={summary['claim_boundary_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
