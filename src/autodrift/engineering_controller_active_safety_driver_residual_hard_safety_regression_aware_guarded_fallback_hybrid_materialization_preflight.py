"""Materialize M3135 regression-aware guarded fallback hybrid direct-action artifacts."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight import (
    POLICY_CONFIG as CORRIDOR_POLICY_CONFIG,
    _probe_observation,
    trajectory_level_clearance_stability_corridor_action,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    V4_POLICY_CONFIG,
    _hard_safety_features,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-"
    "aware-guarded-fallback-hybrid-materialization-preflight"
)
NEXT_ID = (
    "m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-"
    "aware-guarded-fallback-hybrid-materialization-result-audit"
)
M3134_ID = (
    "m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit"
)
M3133_ID = (
    "m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-regression-failure-decomposition-"
    "materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)
M3129_ID = (
    "m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-materialization-preflight"
)

DEFAULT_M3134_AUDIT = Path(f"docs/{M3134_ID}.md")
DEFAULT_M3133_DIR = Path(
    "runs/m3133_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "clearance_stability_corridor_reflex_regression_failure_decomposition_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3129_DIR = Path(
    "runs/m3129_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "clearance_stability_corridor_reflex_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3135_engineering_controller_active_safety_driver_residual_hard_safety_"
    "regression_aware_guarded_fallback_hybrid_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

POLICY_ID = "m3135_regression_aware_guarded_fallback_hybrid"
OUTPUT_SEMANTICS = "direct_action_clipped"
ACTION_COMPONENTS = ("steer", "throttle", "brake")
M3134_ROUTE_MARKER = (
    "accept_m3133_regression_decomposition_reject_standalone_corridor_route_to_m3135_"
    "guarded_fallback_hybrid_materialization"
)
EXPECTED_FULL_ROWS = 64
MIN_RULE_ROWS = 8
MIN_RUNTIME_CONTRACT_ROWS = 4
MIN_EXCLUSION_ROWS = 12
MIN_ACTION_PROBE_ROWS = 5

CLAIM_SCOPE = (
    "M3135 Active Safety Driver residual hard-safety regression-aware guarded fallback "
    "hybrid materialization only; artifacts may define a callable actor-visible obs72 to "
    "action3 [steer throttle brake] deterministic hybrid that defaults to the M3105/M3103 "
    "no-regression direct-action path and only admits bounded corridor-style adjustments "
    "behind actor-visible regression guards. No reset, step, rollout, replay, fitting, PPO, "
    "training, measurement, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner "
    "selection, checkpoint promotion, high-fidelity validation readiness or result, paper "
    "evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

POLICY_CONFIG: dict[str, Any] = {
    "policy_id": POLICY_ID,
    "observation_shape": P0_OBSERVATION_DIM,
    "action_shape": ACTION_DIM,
    "output_components": list(ACTION_COMPONENTS),
    "output_semantics": OUTPUT_SEMANTICS,
    "actor_observation_contract": "actor_visible_obs72_only",
    "fallback_policy_id": V4_POLICY_CONFIG["policy_id"],
    "corridor_policy_id": CORRIDOR_POLICY_CONFIG["policy_id"],
    "runtime_base_policy_required": False,
    "checkpoint_model_required": False,
    "recurrent_hidden_state_required": False,
    "fallback_config": deepcopy(V4_POLICY_CONFIG),
    "corridor_config": deepcopy(CORRIDOR_POLICY_CONFIG),
    "guard_thresholds": {
        "obstacle_urgency_trigger": 0.50,
        "obstacle_urgency_full_mix": 0.95,
        "edge_urgency_block": 0.45,
        "stability_urgency_block": 0.55,
        "speed_floor_block_mps": 8.0,
        "max_corridor_mix_alpha": 0.35,
        "max_abs_steer_delta": 0.28,
        "max_throttle_drop": 0.16,
        "max_brake_increase": 0.25,
    },
}

RULE_FIELDNAMES = [
    "rule_id",
    "rule_family",
    "priority",
    "input_feature_groups",
    "output_channels",
    "formula_summary",
    "default_value",
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
    "fallback_policy_id",
    "corridor_policy_id",
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
    "allowed_in_m3135",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
ACTION_PROBE_FIELDNAMES = [
    "probe_id",
    "probe_family",
    "fallback_steer",
    "fallback_throttle",
    "fallback_brake",
    "corridor_steer",
    "corridor_throttle",
    "corridor_brake",
    "hybrid_steer",
    "hybrid_throttle",
    "hybrid_brake",
    "corridor_mix_alpha",
    "obstacle_urgency",
    "edge_urgency",
    "stability_urgency",
    "speed_mps",
    "speed_floor_guard_active",
    "edge_guard_active",
    "stability_guard_active",
    "obstacle_guard_active",
    "delta_limiter_active",
    "fallback_path_selected",
    "action_finite",
    "action_bounded",
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


def _threshold(config: Mapping[str, Any], key: str) -> float:
    default = _float(POLICY_CONFIG["guard_thresholds"][key])
    return _float(config.get("guard_thresholds", {}).get(key), default)


def _stability_urgency(obs: np.ndarray) -> float:
    vy_body = float(obs[1] * 12.0)
    yaw_rate = float(obs[2] * 2.5)
    ay_body = float(obs[4] * 15.0)
    return _clip01((abs(vy_body) / 4.0 + abs(yaw_rate) / 1.5 + abs(ay_body) / 8.0) / 3.0)


def guarded_hybrid_diagnostics(
    observation: np.ndarray | list[float] | tuple[float, ...],
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the guarded hybrid action plus actor-visible guard diagnostics."""

    cfg: Mapping[str, Any] = config or POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    fallback_action = v4_v2_fallback_no_regression_hard_safety_direct_action(
        obs,
        cfg.get("fallback_config", V4_POLICY_CONFIG),
    )
    corridor_action = trajectory_level_clearance_stability_corridor_action(
        obs,
        cfg.get("corridor_config", CORRIDOR_POLICY_CONFIG),
    )
    features = _hard_safety_features(obs, cfg.get("fallback_config", V4_POLICY_CONFIG))
    speed_mps = float(features["vx_body"])
    obstacle_urgency = float(features["obstacle_urgency"])
    edge_urgency = float(features["edge_urgency"])
    stability_urgency = _stability_urgency(obs)

    obstacle_trigger = _threshold(cfg, "obstacle_urgency_trigger")
    obstacle_full_mix = max(_threshold(cfg, "obstacle_urgency_full_mix"), obstacle_trigger + 1e-6)
    speed_floor_guard_active = speed_mps < _threshold(cfg, "speed_floor_block_mps")
    edge_guard_active = edge_urgency > _threshold(cfg, "edge_urgency_block")
    stability_guard_active = stability_urgency > _threshold(cfg, "stability_urgency_block")
    obstacle_guard_active = obstacle_urgency < obstacle_trigger
    corridor_mix_alpha = 0.0
    if not (speed_floor_guard_active or edge_guard_active or stability_guard_active or obstacle_guard_active):
        corridor_mix_alpha = _threshold(cfg, "max_corridor_mix_alpha") * _clip01(
            (obstacle_urgency - obstacle_trigger) / (obstacle_full_mix - obstacle_trigger)
        )

    raw_delta = corridor_mix_alpha * (corridor_action - fallback_action)
    limited_delta = raw_delta.copy()
    limited_delta[0] = np.float32(
        np.clip(limited_delta[0], -_threshold(cfg, "max_abs_steer_delta"), _threshold(cfg, "max_abs_steer_delta"))
    )
    limited_delta[1] = np.float32(max(limited_delta[1], -_threshold(cfg, "max_throttle_drop")))
    limited_delta[2] = np.float32(min(limited_delta[2], _threshold(cfg, "max_brake_increase")))
    if speed_floor_guard_active:
        limited_delta[1] = np.float32(max(limited_delta[1], 0.0))
        limited_delta[2] = np.float32(min(limited_delta[2], 0.0))
    action = np.clip(fallback_action + limited_delta, -1.0, 1.0).astype(np.float32)

    return {
        "action": action,
        "fallback_action": fallback_action.astype(np.float32),
        "corridor_action": corridor_action.astype(np.float32),
        "corridor_mix_alpha": float(corridor_mix_alpha),
        "raw_delta": raw_delta.astype(np.float32),
        "limited_delta": limited_delta.astype(np.float32),
        "delta_limiter_active": bool(np.max(np.abs(raw_delta - limited_delta)) > 1e-6),
        "fallback_path_selected": bool(corridor_mix_alpha == 0.0),
        "speed_mps": speed_mps,
        "obstacle_urgency": obstacle_urgency,
        "edge_urgency": edge_urgency,
        "stability_urgency": stability_urgency,
        "speed_floor_guard_active": speed_floor_guard_active,
        "edge_guard_active": edge_guard_active,
        "stability_guard_active": stability_guard_active,
        "obstacle_guard_active": obstacle_guard_active,
    }


def regression_aware_guarded_fallback_hybrid_action(
    observation: np.ndarray | list[float] | tuple[float, ...],
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute deployable direct [steer, throttle, brake] from actor-visible obs72 only."""

    return np.asarray(guarded_hybrid_diagnostics(observation, config)["action"], dtype=np.float32)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "guarded_hybrid_rule_rows": output_dir / "guarded_hybrid_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3134_audit: Path, m3133_dir: Path, m3105_dir: Path, m3129_dir: Path) -> dict[str, Any]:
    paths = {
        "m3134_audit": m3134_audit,
        "m3133_summary": m3133_dir / "summary.json",
        "m3133_regression_rows": m3133_dir / "regression_failure_decomposition_rows.csv",
        "m3133_gate_rows": m3133_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_gate_rows": m3105_dir / "gate_matrix.csv",
        "m3129_summary": m3129_dir / "summary.json",
        "m3129_gate_rows": m3129_dir / "gate_matrix.csv",
        "m3129_policy_config": m3129_dir / "direct_action_policy_config.json",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3134_audit_text": paths["m3134_audit"].read_text(encoding="utf-8") if exists["m3134_audit"] else "",
        "m3133_summary": read_json(paths["m3133_summary"]) if exists["m3133_summary"] else {},
        "m3133_regression_rows": read_csv_rows(paths["m3133_regression_rows"]),
        "m3133_gate_rows": read_csv_rows(paths["m3133_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_rows"]),
        "m3129_summary": read_json(paths["m3129_summary"]) if exists["m3129_summary"] else {},
        "m3129_gate_rows": read_csv_rows(paths["m3129_gate_rows"]),
        "m3129_policy_config": read_json(paths["m3129_policy_config"]) if exists["m3129_policy_config"] else {},
    }


def build_rule_rows() -> list[dict[str, Any]]:
    thresholds = POLICY_CONFIG["guard_thresholds"]
    specs = [
        (
            "m3105_default_fallback_path",
            "p0",
            "all_actor_visible_obs72",
            "steer;throttle;brake",
            "start from the M3103/M3105 no-regression direct-action path for every observation",
            POLICY_CONFIG["fallback_policy_id"],
        ),
        (
            "corridor_candidate_path",
            "p1",
            "all_actor_visible_obs72",
            "steer;throttle;brake",
            "compute the M3129 corridor action only as a bounded candidate adjustment",
            POLICY_CONFIG["corridor_policy_id"],
        ),
        (
            "obstacle_urgency_gate",
            "p0",
            "obstacle_slots",
            "steer;brake;throttle",
            "corridor mix is zero unless actor-visible obstacle urgency exceeds the trigger",
            thresholds["obstacle_urgency_trigger"],
        ),
        (
            "speed_floor_regression_guard",
            "p0",
            "ego_response",
            "throttle;brake",
            "corridor mix is zero below the speed-floor block threshold",
            thresholds["speed_floor_block_mps"],
        ),
        (
            "edge_regression_guard",
            "p0",
            "road_left_boundary;road_right_boundary",
            "steer;brake",
            "corridor mix is zero when actor-visible edge urgency exceeds the block threshold",
            thresholds["edge_urgency_block"],
        ),
        (
            "stability_regression_guard",
            "p0",
            "ego_response",
            "steer;brake",
            "corridor mix is zero when actor-visible stability urgency exceeds the block threshold",
            thresholds["stability_urgency_block"],
        ),
        (
            "bounded_corridor_mix",
            "p0",
            "actor_visible_guard_features",
            "steer;throttle;brake",
            "corridor adjustment is mixed with a capped alpha and per-channel delta limits",
            thresholds["max_corridor_mix_alpha"],
        ),
        (
            "direct_action_clipping",
            "p0",
            "all_actor_visible_obs72",
            "steer;throttle;brake",
            "final hybrid output is clipped to [-1, 1]",
            "not_applicable",
        ),
        (
            "audit_before_measurement",
            "p0",
            "process",
            "none",
            "M3136 result audit is required before any full-fresh measurement",
            "not_applicable",
        ),
    ]
    return [
        {
            "rule_id": f"m3135-rule-{index:04d}",
            "rule_family": family,
            "priority": priority,
            "input_feature_groups": inputs,
            "output_channels": outputs,
            "formula_summary": formula,
            "default_value": value,
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "direct_action_output": True,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, inputs, outputs, formula, value) in enumerate(specs, start=1)
    ]


def build_runtime_contract_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "callable_runtime",
            "autodrift.engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight.regression_aware_guarded_fallback_hybrid_action",
            "np.ndarray/list/tuple shape (72,), finite actor-visible P0 observation",
            "np.ndarray shape (3,), finite bounded [steer throttle brake]",
        ),
        (
            "fallback_direct_action",
            "v4_v2_fallback_no_regression_hard_safety_direct_action",
            "deterministic actor-visible direct-action fallback function",
            "same direct action3 semantics",
        ),
        (
            "corridor_candidate",
            "trajectory_level_clearance_stability_corridor_action",
            "deterministic actor-visible corridor candidate function",
            "bounded candidate action before guarded mixing",
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
            "M3136 result audit required before measurement",
            "no repair-success claim in M3135",
        ),
    ]
    return [
        {
            "contract_id": f"m3135-runtime-contract-{index:04d}",
            "contract_family": family,
            "runtime_symbol": runtime_symbol,
            "input_contract": input_contract,
            "output_contract": output_contract,
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "action_components": ";".join(ACTION_COMPONENTS),
            "output_semantics": OUTPUT_SEMANTICS,
            "fallback_policy_id": POLICY_CONFIG["fallback_policy_id"],
            "corridor_policy_id": POLICY_CONFIG["corridor_policy_id"],
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
        ("baseline_outcome", "M3105/M3131 outcomes are not runtime inputs"),
        ("m3133_regression_axis_label", "M3133 row labels are offline diagnostics only"),
        ("m3105_same_row_delta", "same-row deltas are offline diagnostics only"),
        ("recurrent_hidden_state", "no recurrent hidden state is required"),
    ]
    return [
        {
            "exclusion_id": f"m3135-exclusion-{index:04d}",
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
        ("guarded_hybrid_rule_rows", "materialization", True, "guarded_hybrid_rule_rows.csv"),
        ("runtime_contract_rows", "runtime_contract", True, "runtime_contract_rows.csv"),
        ("actor_input_exclusion_rows", "contract_guard", True, "actor_input_exclusion_rows.csv"),
        ("action_probe_rows", "runtime_contract", True, "action_probe_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3136 audit manifest"),
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
        ("feasibility_proof", "verdict", "future formal feasibility/validation route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("row_label_actor_inputs", "contract", "M3133 regression labels are forbidden actor inputs"),
    ]
    rows = [
        {
            "claim_id": f"m3135-{claim_id}",
            "claim_family": family,
            "allowed_in_m3135": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3135-{claim_id}",
            "claim_family": family,
            "allowed_in_m3135": False,
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
        "priority": 31360,
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
        "hypothesis": "A bounded result audit can accept or reject the M3135 guarded fallback hybrid materialization artifacts before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3134_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "guarded_hybrid_rule_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit guarded fallback hybrid materialization before measurement routing"],
            "derived_from": [MILESTONE_ID, M3134_ID, M3133_ID, M3105_ID, M3129_ID],
            "blocked_by": [
                "M3135 materialization artifacts require audit before measurement",
                "M3135 is no-new-execution materialization and cannot support repair-success claims",
            ],
            "supersedes": ["standalone corridor reflex continuation after M3133 regression decomposition"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3136 must audit M3135 summary rule runtime contract exclusion action probe claim and gate artifacts",
            "M3136 must preserve obs72/action3 direct [steer throttle brake] actor contract",
            "M3136 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3136 must select exactly one full-fresh measurement artifact repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3135 materialization into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_regression_aware_guarded_fallback_hybrid",
            "evidence_axis": "guarded_fallback_hybrid_materialization_result_audit",
            "evidence_increment": "audits guarded fallback hybrid materialization artifacts before measurement routing",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3135 artifacts are missing or gate matrix fails",
                "stop if actor or runtime contract is violated",
                "route to one constrained measurement only if M3135 is complete and claim-safe",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to synthesis or stop if no deployable next route remains",
                "route to full-fresh measurement only after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3135 completes guarded fallback hybrid materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3135 guarded fallback hybrid materialization artifacts",
            "admission_evidence": ["M3135 summary gate matrix rule contract exclusion action probe and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime learned base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3136 status queue scoreboard research log and review",
                "one follow-up manifest only if M3136 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3136 accepts or rejects M3135 as complete and claim-safe",
                "next full-fresh measurement artifact repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3136 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3136; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3135 materialization artifacts only.",
            "negative_result_policy": "Preserve guarded fallback materialization evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3135 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the guarded fallback hybrid materialization before measurement routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3136 prepares engineering measurement route decision",
            "must_synthesize_if": [
                "M3136 cannot accept M3135 as complete and claim-safe",
                "M3136 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result feasibility-proof or self-ID evidence",
                "M3136 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3136 audits M3135 artifact row counts gates actor contract and claim boundaries",
            "M3136 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3136 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3136 hides M3135 failures or missing artifacts",
            "M3136 treats M3135 materialization as validation repair-success or performance verdict",
            "M3136 changes actor input or action contract",
            "M3136 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3136 audits M3135 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_guarded_fallback_hybrid_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3135-{gate_id}",
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


def build_action_probe_rows() -> list[dict[str, Any]]:
    specs = [
        ("clear_nominal", _probe_observation(speed_mps=12.0)),
        ("low_speed_floor", _probe_observation(speed_mps=3.0)),
        ("urgent_obstacle_left", _probe_observation(speed_mps=15.0, obstacle=True, obstacle_y_m=1.0)),
        ("urgent_edge", _probe_observation(speed_mps=14.0, edge_urgency=True)),
        ("sideslip_recovery", _probe_observation(speed_mps=14.0, sideslip=True)),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, obs) in enumerate(specs, start=1):
        diag = guarded_hybrid_diagnostics(obs)
        fallback = diag["fallback_action"]
        corridor = diag["corridor_action"]
        action = diag["action"]
        rows.append(
            {
                "probe_id": f"m3135-action-probe-{index:04d}",
                "probe_family": family,
                "fallback_steer": float(fallback[0]),
                "fallback_throttle": float(fallback[1]),
                "fallback_brake": float(fallback[2]),
                "corridor_steer": float(corridor[0]),
                "corridor_throttle": float(corridor[1]),
                "corridor_brake": float(corridor[2]),
                "hybrid_steer": float(action[0]),
                "hybrid_throttle": float(action[1]),
                "hybrid_brake": float(action[2]),
                "corridor_mix_alpha": diag["corridor_mix_alpha"],
                "obstacle_urgency": diag["obstacle_urgency"],
                "edge_urgency": diag["edge_urgency"],
                "stability_urgency": diag["stability_urgency"],
                "speed_mps": diag["speed_mps"],
                "speed_floor_guard_active": diag["speed_floor_guard_active"],
                "edge_guard_active": diag["edge_guard_active"],
                "stability_guard_active": diag["stability_guard_active"],
                "obstacle_guard_active": diag["obstacle_guard_active"],
                "delta_limiter_active": diag["delta_limiter_active"],
                "fallback_path_selected": diag["fallback_path_selected"],
                "action_finite": bool(np.all(np.isfinite(action))),
                "action_bounded": bool(np.max(np.abs(action)) <= 1.0),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    rule_rows: list[dict[str, Any]],
    runtime_contract_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    m3133_summary = source["m3133_summary"]
    m3105_summary = source["m3105_summary"]
    m3129_summary = source["m3129_summary"]
    audit_text = str(source.get("m3134_audit_text", ""))
    probe_by_family = {str(row.get("probe_family", "")): row for row in probe_rows}
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3134_route_marker", "lineage", M3134_ROUTE_MARKER in audit_text, "route marker", "present", "lineage_invalid"),
        gate("m3133_status_pass", "lineage", _bool(m3133_summary.get("status_pass")), m3133_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3133_gate_matrix_pass", "lineage", _bool(m3133_summary.get("gate_matrix_pass")), m3133_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3133_decomposition_rows", "lineage", int(m3133_summary.get("regression_decomposition_row_count", 0)) == EXPECTED_FULL_ROWS, m3133_summary.get("regression_decomposition_row_count"), EXPECTED_FULL_ROWS, "lineage_invalid"),
        gate("m3133_standalone_regression_confirmed", "lineage", int(m3133_summary.get("success_delta_sum_vs_m3105", 0)) < 0, m3133_summary.get("success_delta_sum_vs_m3105"), "<0", "behavior_regression"),
        gate("m3105_status_pass", "lineage", _bool(m3105_summary.get("status_pass")), m3105_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(m3105_summary.get("gate_matrix_pass")), m3105_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3129_status_pass", "lineage", _bool(m3129_summary.get("status_pass")), m3129_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3129_gate_matrix_pass", "lineage", _bool(m3129_summary.get("gate_matrix_pass")), m3129_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("rule_rows", "materialization", len(rule_rows) >= MIN_RULE_ROWS, len(rule_rows), f">={MIN_RULE_ROWS}", "metric_artifact"),
        gate("runtime_contract_rows", "contract", len(runtime_contract_rows) >= MIN_RUNTIME_CONTRACT_ROWS, len(runtime_contract_rows), f">={MIN_RUNTIME_CONTRACT_ROWS}", "contract_violation"),
        gate("actor_input_exclusion_rows", "contract", len(exclusion_rows) >= MIN_EXCLUSION_ROWS and all(_bool(row.get("status_pass")) for row in exclusion_rows), len(exclusion_rows), f">={MIN_EXCLUSION_ROWS} all pass", "contract_violation"),
        gate("direct_action_output", "contract", all(_bool(row.get("direct_action_output")) for row in rule_rows), "all rules", True, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", all(not _bool(row.get("runtime_base_policy_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("hidden_oracle_absent", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("ttc_actor_input_absent", "contract", all(not _bool(row.get("ttc_actor_input_required")) for row in runtime_contract_rows), "all contracts", False, "contract_violation"),
        gate("action_probe_rows", "runtime_contract", len(probe_rows) >= MIN_ACTION_PROBE_ROWS and all(_bool(row.get("action_finite")) and _bool(row.get("action_bounded")) for row in probe_rows), len(probe_rows), f">={MIN_ACTION_PROBE_ROWS} finite bounded", "metric_artifact"),
        gate("low_speed_uses_fallback", "regression_guard", _bool(probe_by_family.get("low_speed_floor", {}).get("fallback_path_selected")), probe_by_family.get("low_speed_floor", {}).get("corridor_mix_alpha"), "0 alpha", "behavior_regression"),
        gate("edge_probe_uses_fallback", "regression_guard", _bool(probe_by_family.get("urgent_edge", {}).get("fallback_path_selected")), probe_by_family.get("urgent_edge", {}).get("corridor_mix_alpha"), "0 alpha", "behavior_regression"),
        gate("sideslip_probe_uses_fallback", "regression_guard", _bool(probe_by_family.get("sideslip_recovery", {}).get("fallback_path_selected")), probe_by_family.get("sideslip_recovery", {}).get("corridor_mix_alpha"), "0 alpha", "behavior_regression"),
        gate("obstacle_probe_allows_bounded_mix", "regression_guard", _float(probe_by_family.get("urgent_obstacle_left", {}).get("corridor_mix_alpha")) > 0.0, probe_by_family.get("urgent_obstacle_left", {}).get("corridor_mix_alpha"), ">0 alpha", "metric_artifact"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_environment_execution", "execution", True, "no reset step rollout replay fitting training measurement validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3135 Regression-Aware Guarded Fallback Hybrid Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- rule rows: {summary['guarded_hybrid_rule_row_count']}",
            f"- runtime contract rows: {summary['runtime_contract_row_count']}",
            f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- fallback probe rows: {summary['fallback_path_probe_count']}",
            f"- bounded mix probe rows: {summary['bounded_mix_probe_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3135 materializes a callable actor-visible obs72-to-action3 guarded fallback hybrid. It defaults to the M3105/M3103 no-regression direct-action path and only admits bounded corridor-style adjustment when actor-visible guards permit it. It does not run the environment or make repair-success claims.",
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
    m3134_audit: Path,
    m3133_dir: Path,
    m3105_dir: Path,
    m3129_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3134_audit=m3134_audit, m3133_dir=m3133_dir, m3105_dir=m3105_dir, m3129_dir=m3129_dir)
    rule_rows = build_rule_rows()
    runtime_contract_rows = build_runtime_contract_rows()
    exclusion_rows = build_actor_input_exclusion_rows()
    probe_rows = build_action_probe_rows()
    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["guarded_hybrid_rule_rows"], rule_rows, fieldnames=RULE_FIELDNAMES)
    write_csv_rows(paths["runtime_contract_rows"], runtime_contract_rows, fieldnames=RUNTIME_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], exclusion_rows, fieldnames=EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["action_probe_rows"], probe_rows, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = build_gate_matrix_rows(
        source=source,
        rule_rows=rule_rows,
        runtime_contract_rows=runtime_contract_rows,
        exclusion_rows=exclusion_rows,
        claim_rows=claim_rows,
        probe_rows=probe_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    fallback_probe_count = sum(1 for row in probe_rows if _bool(row.get("fallback_path_selected")))
    bounded_mix_probe_count = sum(1 for row in probe_rows if _float(row.get("corridor_mix_alpha")) > 0.0)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m3133_regression_row_count": len(source["m3133_regression_rows"]),
        "guarded_hybrid_rule_row_count": len(rule_rows),
        "runtime_contract_row_count": len(runtime_contract_rows),
        "actor_input_exclusion_row_count": len(exclusion_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "action_probe_row_count": len(probe_rows),
        "fallback_path_probe_count": fallback_probe_count,
        "bounded_mix_probe_count": bounded_mix_probe_count,
        "required_artifacts_present": present,
        "runtime_driver_id": POLICY_ID,
        "fallback_policy_id": POLICY_CONFIG["fallback_policy_id"],
        "corridor_policy_id": POLICY_CONFIG["corridor_policy_id"],
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
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_route_to_m3136_result_audit",
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
    parser.add_argument("--m3134-audit", type=Path, default=DEFAULT_M3134_AUDIT)
    parser.add_argument("--m3133-dir", type=Path, default=DEFAULT_M3133_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3129-dir", type=Path, default=DEFAULT_M3129_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3134_audit=args.m3134_audit,
        m3133_dir=args.m3133_dir,
        m3105_dir=args.m3105_dir,
        m3129_dir=args.m3129_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['guarded_hybrid_rule_row_count']}")
    print(f"runtime_contract_rows={summary['runtime_contract_row_count']}")
    print(f"actor_input_exclusion_rows={summary['actor_input_exclusion_row_count']}")
    print(f"action_probe_rows={summary['action_probe_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
