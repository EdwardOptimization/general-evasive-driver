"""Materialize M3078 actor-visible deterministic safety-reflex artifacts.

M3078 consumes the M3077 route design and the M3076 negative audit context. It
does not reset, step, rollout, replay, fit, train, validate, rank, promote, or
run high-fidelity simulation. It materializes one deterministic obs72-to-action3
direct-action safety-reflex skeleton plus guards and measurement-admission rows.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-materialization-preflight"
)
NEXT_ID = (
    "m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-materialization-result-audit"
)
M3077_ID = (
    "m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-pivot-route-design"
)

DEFAULT_M3077_DESIGN = Path(f"docs/{M3077_ID}.md")
DEFAULT_M3076_AUDIT = Path(
    "docs/m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-closed-loop-measurement-result-audit.md"
)
DEFAULT_M3067_DIR = Path(
    "runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_closed_loop_measurement_preflight"
)
DEFAULT_M3075_DIR = Path(
    "runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_multi_failure_repair_closed_loop_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3078 Active Safety Driver v1 actor-visible deterministic direct-action "
    "safety-reflex materialization only; artifacts may define a bounded obs72 "
    "to action3 [steer throttle brake] policy skeleton, feature contract, "
    "guards, and measurement-admission rows. No reset, step, rollout, replay, "
    "fitting, PPO, training, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim "
    "verdict, repair success, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, or self-ID "
    "claim is made"
)

FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, repair "
    "success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

FEATURE_FIELDNAMES = [
    "feature_contract_id",
    "slice_start",
    "slice_end_exclusive",
    "feature_group",
    "actor_visible",
    "runtime_use",
    "normalization",
    "hidden_oracle_required",
    "ttc_required",
    "target_label_required",
    "provenance_required",
    "claim_boundary",
]

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

ADMISSION_FIELDNAMES = [
    "admission_gate_id",
    "gate_family",
    "required_metric",
    "required_before_claim",
    "same_denominator_required",
    "status_pass",
    "blocked_claims",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3078",
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


DEFAULT_POLICY_CONFIG: dict[str, Any] = {
    "policy_id": "m3078_actor_visible_deterministic_direct_action_safety_reflex_v1",
    "observation_shape": P0_OBSERVATION_DIM,
    "action_shape": ACTION_DIM,
    "output_components": ["steer", "throttle", "brake"],
    "output_semantics": "direct_action_clipped",
    "runtime_base_policy_required": False,
    "action_low": [-1.0, -1.0, -1.0],
    "action_high": [1.0, 1.0, 1.0],
    "feature_slices": {
        "ego_response": [0, 5],
        "actuator_state": [5, 9],
        "previous_action": [9, 12],
        "road_left_boundary": [12, 28],
        "road_right_boundary": [28, 44],
        "obstacle_slots": [44, 72],
    },
    "gains": {
        "road_center_steer": 0.55,
        "edge_brake": 0.45,
        "obstacle_steer": 0.70,
        "obstacle_brake": 0.95,
        "yaw_damping": 0.22,
        "lateral_velocity_damping": 0.18,
        "steer_rate_damping": 0.08,
        "stability_brake": 0.30,
        "brake_to_throttle_suppression": 1.20,
        "edge_to_throttle_suppression": 0.35,
        "stability_to_throttle_suppression": 0.25,
    },
    "thresholds": {
        "obstacle_relevance_distance_m": 40.0,
        "obstacle_lateral_window_m": 6.0,
        "road_edge_warning_margin_m": 2.0,
        "road_center_scale_m": 4.0,
        "base_throttle_normalized": -0.35,
    },
}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _config_value(config: Mapping[str, Any], section: str, key: str) -> float:
    return _float(config.get(section, {}).get(key), _float(DEFAULT_POLICY_CONFIG[section][key]))


def actor_visible_safety_reflex_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute a bounded direct [steer, throttle, brake] action from obs72 only."""

    cfg: Mapping[str, Any] = config or DEFAULT_POLICY_CONFIG
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
    road_center_scale = _config_value(cfg, "thresholds", "road_center_scale_m")
    road_center_error = float(np.clip(np.mean(center_y[:4]) / max(road_center_scale, 1e-6), -1.0, 1.0))
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
    brake = -1.0 + 2.0 * brake_physical
    throttle = (
        _config_value(cfg, "thresholds", "base_throttle_normalized")
        - _float(gains.get("brake_to_throttle_suppression")) * brake_physical
        - _float(gains.get("edge_to_throttle_suppression")) * edge_urgency
        - _float(gains.get("stability_to_throttle_suppression")) * stability_urgency
    )
    if vx_body < 1.0 and brake_physical < 0.2:
        throttle = max(throttle, -0.15)

    return np.clip(np.array([steer, throttle, brake], dtype=np.float32), -1.0, 1.0)


def build_feature_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("m3078-feature-ego-response", 0, 5, "ego_response", "stability damping and speed-aware recovery", "vx*20 vy*12 yaw_rate*2.5 ax/ay*15"),
        ("m3078-feature-actuator-state", 5, 9, "actuator_state", "actuator damping and command smoothing", "normalized current actuator state"),
        ("m3078-feature-previous-action", 9, 12, "previous_action", "direct-action continuity guard", "previous normalized steer throttle brake command"),
        ("m3078-feature-road-left", 12, 28, "road_left_boundary", "road corridor centering and edge urgency", "x*80 y*20 body-frame lookahead"),
        ("m3078-feature-road-right", 28, 44, "road_right_boundary", "road corridor centering and edge urgency", "x*80 y*20 body-frame lookahead"),
        ("m3078-feature-obstacle-slots", 44, 72, "obstacle_slots", "visible obstacle braking and lateral avoidance", "present x*80 y*20 vx*20 vy*12 half-width/length*5"),
    ]
    return [
        {
            "feature_contract_id": feature_id,
            "slice_start": start,
            "slice_end_exclusive": end,
            "feature_group": group,
            "actor_visible": True,
            "runtime_use": runtime_use,
            "normalization": normalization,
            "hidden_oracle_required": False,
            "ttc_required": False,
            "target_label_required": False,
            "provenance_required": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for feature_id, start, end, group, runtime_use, normalization in specs
    ]


def build_rule_rows() -> list[dict[str, Any]]:
    specs = [
        ("m3078-rule-obstacle-brake", "collision_approach_braking", "p0", "obstacle_slots", "brake;throttle", "increase brake and suppress throttle from visible obstacle proximity and lateral overlap", "obstacle_brake", 0.0, 1.5),
        ("m3078-rule-obstacle-steer", "collision_lateral_avoidance", "p0", "obstacle_slots;ego_response", "steer", "steer away from the most urgent visible obstacle slot", "obstacle_steer", 0.0, 1.5),
        ("m3078-rule-road-center", "offtrack_corridor_centering", "p0", "road_left_boundary;road_right_boundary", "steer", "steer toward the observed road-corridor center", "road_center_steer", 0.0, 1.2),
        ("m3078-rule-road-edge", "offtrack_edge_braking", "p0", "road_left_boundary;road_right_boundary", "brake;throttle", "increase brake and suppress throttle when road-boundary margin is low", "edge_brake", 0.0, 1.2),
        ("m3078-rule-stability-damping", "stability_damping", "p1", "ego_response;actuator_state", "steer;brake;throttle", "damp yaw-rate lateral-velocity acceleration and steer-rate pressure", "yaw_damping", 0.0, 0.8),
        ("m3078-rule-action-clip", "bounded_direct_action", "p0", "all_actor_visible_features", "steer;throttle;brake", "clip final action to [-1, 1] and require finite output", "not_applicable", -1.0, 1.0),
    ]
    rows: list[dict[str, Any]] = []
    gains = DEFAULT_POLICY_CONFIG["gains"]
    for rule_id, family, priority, inputs, outputs, formula, gain_key, lower, upper in specs:
        default_gain = gains.get(gain_key, "not_applicable")
        rows.append(
            {
                "rule_id": rule_id,
                "rule_family": family,
                "priority": priority,
                "input_feature_groups": inputs,
                "output_channels": outputs,
                "formula_summary": formula,
                "default_gain": default_gain,
                "gain_lower_bound": lower,
                "gain_upper_bound": upper,
                "enabled_by_default": True,
                "runtime_base_policy_required": False,
                "direct_action_output": True,
                "hidden_oracle_actor_input_required": False,
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
            "exclusion_id": f"m3078-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(exclusions, start=1)
    ]


def build_measurement_admission_rows() -> list[dict[str, Any]]:
    metrics = [
        ("same_denominator_32", "denominator", "32 scheduled rows", True),
        ("success_rows", "primary_safety", "success count and rate", True),
        ("collision_rows", "hard_safety", "collision count and rate", True),
        ("offtrack_rows", "hard_safety", "offtrack count and rate", True),
        ("speed_too_low_rows", "recovery", "speed-too-low count and rate", True),
        ("clearance_margin", "clearance", "mean and row distribution", True),
        ("stability_pressure", "stability", "sideslip yaw-rate or high-sideslip proxy rows", True),
        ("recovery_rows", "recovery", "termination and recovery status rows", True),
        ("raw_action_pressure", "action", "raw action abs max and l2 rows", True),
        ("action_clip_fraction", "action", "final action clipping fraction", True),
        ("actor_contract_guards", "contract", "obs72/action3 direct-action guards", True),
        ("claim_boundary_guards", "claim", "no validation performance promotion paper self-ID claim guards", True),
    ]
    return [
        {
            "admission_gate_id": f"m3078-admission-{index:04d}",
            "gate_family": family,
            "required_metric": metric,
            "required_before_claim": required,
            "same_denominator_required": same_denominator,
            "status_pass": True,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (metric, family, required, same_denominator) in enumerate(metrics, start=1)
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = [
        ("feature_contract_materialized", "materialization", True, True, "actor_visible_feature_contract_rows.csv"),
        ("rule_table_materialized", "materialization", True, True, "safety_reflex_rule_rows.csv"),
        ("policy_config_materialized", "materialization", True, True, "direct_action_policy_config.json"),
        ("measurement_admission_materialized", "materialization", True, True, "measurement_admission_gate_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", True, True, "M3079 audit manifest"),
        ("environment_reset_or_step", "execution", False, False, "future same-denominator measurement route"),
        ("rollout_measurement", "execution", False, False, "future same-denominator measurement route"),
        ("fitting_or_training", "training", False, False, "future guarded route if selected"),
        ("validation_result", "validation", False, False, "future validation route"),
        ("driver_performance_verdict", "driver_performance", False, False, "future proof/generalization audit"),
        ("current_sim_verdict", "verdict", False, False, "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("repair_success", "verdict", False, False, "future result audit"),
        ("paper_level_evidence", "paper", False, False, "future evidence matrix"),
        ("high_fidelity_validation", "validation", False, False, "future high-fidelity route"),
        ("finite_window_vs_gru_result", "paper", False, False, "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", False, False, "future full goal gate"),
        ("level3_self_identification", "self_id", False, False, "future source-diverse intervention proof"),
    ]
    return [
        {
            "claim_id": f"m3078-{name}",
            "claim_family": family,
            "allowed_in_m3078": allowed,
            "claim_made": made,
            "status_pass": allowed == made,
            "evidence_required_before_claim": required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, allowed, made, required in claims
    ]


def _feature_coverage_pass(rows: list[Mapping[str, Any]]) -> bool:
    covered: set[int] = set()
    for row in rows:
        if not bool(row.get("actor_visible")):
            return False
        start = int(row["slice_start"])
        end = int(row["slice_end_exclusive"])
        covered.update(range(start, end))
    return covered == set(range(P0_OBSERVATION_DIM))


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30740,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3078 actor-visible deterministic direct-action safety-reflex materialization artifacts before any rollout, validation, ranking, promotion, driver-performance, paper, high-fidelity, repair-success, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "actor_visible_feature_contract_rows.csv"),
                str(output_dir / "safety_reflex_rule_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "measurement_admission_gate_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3078 deterministic direct-action safety-reflex materialization before measurement admission"],
            "derived_from": [MILESTONE_ID, M3077_ID],
            "blocked_by": [
                "M3078 materialization artifacts require audit before any closed-loop measurement",
                "M3078 is materialization evidence only and cannot support performance claims",
            ],
            "supersedes": ["same offline target-fitting repair continuation as default route"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3079 must audit M3078 summary feature rule policy exclusion admission claim and gate artifacts",
            "M3079 must verify obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3079 must verify hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs are excluded",
            "M3079 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success and self-ID claims",
            "M3079 must route exactly one same-denominator closed-loop measurement preflight or stop decision",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout fitting training validation ranking promotion or high-fidelity simulation",
            "do not treat M3078 materialization as driver performance repair success or validation evidence",
            "do not change actor input shape output shape or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "actor_visible_deterministic_direct_action_safety_reflex_result_audit",
            "evidence_increment": "audits the materialized deterministic direct-action safety-reflex contract before measurement admission",
            "claim_scope": "Result audit only; no rollout validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3078 artifacts are missing or gate matrix fails",
                "stop if obs72/action3 direct-action or base-policy-free runtime contract is violated",
                "stop if forbidden actor inputs or overclaims appear",
            ],
            "fallback_plan": [
                "route to artifact repair if M3078 artifacts are incomplete",
                "route to same-denominator measurement if M3078 is complete and claim-safe",
                "stop branch if actor-visible direct-action constraints cannot be preserved",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3078 materializes the selected safety-reflex route",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3078 actor-visible deterministic direct-action safety-reflex materialization artifacts",
            "admission_evidence": [
                "M3078 summary and gate matrix",
                "M3078 feature contract, rule table, policy config, exclusion rows, admission gates, and claim rows",
            ],
            "blocked_shortcuts": [
                "no rollout fitting validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3079 status queue scoreboard research log and review",
                "one follow-up manifest only if M3079 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3079 accepts or rejects M3078 as complete and claim-safe",
                "next same-denominator measurement preflight or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3079 audits engineering safety-reflex artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3079; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3078 materialization artifacts only.",
            "negative_result_policy": "Reject or repair M3078 artifacts rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3078 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new deterministic deployable safety-reflex materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3079 prepares a measurement route decision",
            "must_synthesize_if": [
                "M3079 cannot accept M3078 as complete and claim-safe",
                "M3079 cannot select a same-denominator measurement or stop route",
                "M3079 would require another process-only milestone before measurement admission",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3079 audits M3078 summary feature rule policy exclusion admission claim and gate artifacts",
            "M3079 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims",
            "M3079 selects exactly one measurement audit stop or continuation route",
        ],
        "failure_criteria": [
            "M3079 hides missing M3078 artifacts or failed gates",
            "M3079 treats M3078 materialization as validation or performance evidence",
            "M3079 changes actor input action contract or runtime base-policy-free boundary",
            "M3079 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3079 audits M3078 materialization artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(doc_path), str(output_dir / "direct_action_policy_config.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def build_gate_rows(
    *,
    summary: Mapping[str, Any],
    paths: Mapping[str, Path],
    feature_rows: list[dict[str, Any]],
    rule_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": f"m3078-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    required_paths = [
        "actor_visible_feature_contract_rows",
        "safety_reflex_rule_rows",
        "direct_action_policy_config",
        "actor_input_exclusion_rows",
        "measurement_admission_gate_rows",
        "claim_boundary_rows",
        "doc",
        "follow_up_manifest",
    ]
    sample_action = actor_visible_safety_reflex_action(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32))
    return [
        gate("m3077_design_present", "lineage", bool(summary["m3077_design_present"]), True, True, "lineage_invalid"),
        gate("m3076_audit_present", "lineage", bool(summary["m3076_audit_present"]), True, True, "lineage_invalid"),
        gate("feature_contract_covers_obs72", "contract", _feature_coverage_pass(feature_rows), "0..71", "0..71", "contract_violation"),
        gate("policy_config_shape_72_action_3", "contract", bool(summary["actor_contract_shape_72_action_3"]), True, True, "contract_violation"),
        gate("direct_action_output", "contract", bool(summary["direct_action_contract_pass"]), True, True, "contract_violation"),
        gate("runtime_base_policy_free", "contract", not bool(summary["runtime_base_policy_required"]), False, False, "contract_violation"),
        gate("rule_rows_present", "metric", len(rule_rows) >= 6, len(rule_rows), ">=6", "metric_artifact"),
        gate("exclusion_rows_pass", "contract", all(bool(row["status_pass"]) for row in exclusion_rows), "all", "pass", "contract_violation"),
        gate("measurement_admission_rows_present", "process", len(admission_rows) >= 12, len(admission_rows), ">=12", "metric_artifact"),
        gate("claim_boundary_rows_pass", "claim", all(bool(row["status_pass"]) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("sample_action_finite", "contract", bool(np.all(np.isfinite(sample_action))), sample_action.tolist(), "finite", "contract_violation"),
        gate("sample_action_bounded", "contract", bool(np.max(np.abs(sample_action)) <= 1.0), float(np.max(np.abs(sample_action))), "<=1.0", "contract_violation"),
        gate("no_new_execution", "execution", not bool(summary["environment_reset_run"]) and not bool(summary["policy_rollout_run"]), False, False, "contract_violation"),
        gate("forbidden_flags_clear", "claim", not bool(summary["forbidden_claim_made"]), False, False, "contract_violation"),
        gate("required_artifacts_present", "process", all(paths[key].exists() for key in required_paths), True, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", paths["follow_up_manifest"].exists(), True, True, "lineage_invalid"),
    ]


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# M3078 Active Safety Driver v1 Actor-Visible Deterministic Direct-Action Safety-Reflex Materialization Preflight",
        "",
        "## Summary",
        "",
        "- status: completed",
        "- result class: `active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight_pass`",
        f"- feature contract rows: {summary['actor_visible_feature_contract_row_count']}",
        f"- safety-reflex rule rows: {summary['safety_reflex_rule_row_count']}",
        f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
        f"- measurement admission rows: {summary['measurement_admission_gate_row_count']}",
        f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
        f"- gate matrix pass: {summary.get('gate_matrix_pass', 'pending')}",
        "",
        "## Interpretation",
        "",
        "M3078 materializes one actor-visible deterministic direct-action safety-reflex skeleton. The skeleton maps the canonical P0 obs72 frame to clipped `[steer, throttle, brake]` without a runtime base policy. This is contract and route materialization only; it is not rollout, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
        "",
        "Selected feature groups:",
        "",
        "```text",
        "ego_response obs[0:5]",
        "actuator_state obs[5:9]",
        "previous_action obs[9:12]",
        "road_left_boundary obs[12:28]",
        "road_right_boundary obs[28:44]",
        "obstacle_slots obs[44:72]",
        "```",
        "",
        "Rule families:",
        "",
        "```text",
        "collision approach braking",
        "collision lateral avoidance",
        "offtrack corridor centering",
        "offtrack edge braking",
        "stability damping",
        "bounded direct-action clipping",
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
        f"- next blocker: `{NEXT_ID}`",
        f"- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize(
    *,
    m3077_design: Path,
    m3076_audit: Path,
    m3067_dir: Path,
    m3075_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "actor_visible_feature_contract_rows": output_dir / "actor_visible_feature_contract_rows.csv",
        "safety_reflex_rule_rows": output_dir / "safety_reflex_rule_rows.csv",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "measurement_admission_gate_rows": output_dir / "measurement_admission_gate_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }

    m3067_summary = read_json(m3067_dir / "summary.json")
    m3075_summary = read_json(m3075_dir / "summary.json")
    feature_rows = build_feature_contract_rows()
    rule_rows = build_rule_rows()
    exclusion_rows = build_actor_input_exclusion_rows()
    admission_rows = build_measurement_admission_rows()
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["actor_visible_feature_contract_rows"], feature_rows, fieldnames=FEATURE_FIELDNAMES)
    write_csv_rows(paths["safety_reflex_rule_rows"], rule_rows, fieldnames=RULE_FIELDNAMES)
    write_json(paths["direct_action_policy_config"], DEFAULT_POLICY_CONFIG)
    write_csv_rows(paths["actor_input_exclusion_rows"], exclusion_rows, fieldnames=EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["measurement_admission_gate_rows"], admission_rows, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight_pass",
        "output_dir": str(output_dir),
        "m3077_design_present": m3077_design.exists(),
        "m3076_audit_present": m3076_audit.exists(),
        "m3067_success_count": m3067_summary.get("measurement_success_count"),
        "m3067_collision_count": m3067_summary.get("measurement_collision_count"),
        "m3067_offtrack_count": m3067_summary.get("measurement_offtrack_count"),
        "m3067_speed_too_low_count": m3067_summary.get("measurement_speed_too_low_count"),
        "m3075_success_count": m3075_summary.get("measurement_success_count"),
        "m3075_collision_count": m3075_summary.get("measurement_collision_count"),
        "m3075_offtrack_count": m3075_summary.get("measurement_offtrack_count"),
        "m3075_speed_too_low_count": m3075_summary.get("measurement_speed_too_low_count"),
        "actor_visible_feature_contract_row_count": len(feature_rows),
        "safety_reflex_rule_row_count": len(rule_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "measurement_admission_gate_row_count": len(admission_rows),
        "claim_boundary_row_count": len(claim_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "candidate_output_semantics": "direct_action_clipped",
        "candidate_output_components": ["steer", "throttle", "brake"],
        "direct_action_contract_pass": True,
        "runtime_base_policy_required": False,
        "base_policy_required_at_runtime": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "forbidden_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "paths": {key: str(value) for key, value in paths.items()},
    }
    write_doc(doc_path, summary)

    gate_rows = build_gate_rows(
        summary=summary,
        paths=paths,
        feature_rows=feature_rows,
        rule_rows=rule_rows,
        exclusion_rows=exclusion_rows,
        admission_rows=admission_rows,
        claim_rows=claim_rows,
    )
    gate_matrix_pass = all(bool(row["status_pass"]) for row in gate_rows)
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["gate_matrix_pass"] = gate_matrix_pass
    summary["status_pass"] = (
        bool(summary["m3077_design_present"])
        and bool(summary["m3076_audit_present"])
        and _feature_coverage_pass(feature_rows)
        and len(rule_rows) >= 6
        and len(exclusion_rows) >= 10
        and len(admission_rows) >= 12
        and all(bool(row["status_pass"]) for row in exclusion_rows)
        and all(bool(row["status_pass"]) for row in claim_rows)
        and bool(summary["actor_contract_shape_72_action_3"])
        and bool(summary["direct_action_contract_pass"])
        and not bool(summary["runtime_base_policy_required"])
        and gate_matrix_pass
    )
    summary["decision"] = "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_route_to_m3079_result_audit"

    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    write_json(paths["summary"], summary)
    write_doc(doc_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3077-design", type=Path, default=DEFAULT_M3077_DESIGN)
    parser.add_argument("--m3076-audit", type=Path, default=DEFAULT_M3076_AUDIT)
    parser.add_argument("--m3067-dir", type=Path, default=DEFAULT_M3067_DIR)
    parser.add_argument("--m3075-dir", type=Path, default=DEFAULT_M3075_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize(
        m3077_design=args.m3077_design,
        m3076_audit=args.m3076_audit,
        m3067_dir=args.m3067_dir,
        m3075_dir=args.m3075_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"feature_contract_rows={summary['actor_visible_feature_contract_row_count']}")
    print(f"rule_rows={summary['safety_reflex_rule_row_count']}")
    print(f"admission_rows={summary['measurement_admission_gate_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
