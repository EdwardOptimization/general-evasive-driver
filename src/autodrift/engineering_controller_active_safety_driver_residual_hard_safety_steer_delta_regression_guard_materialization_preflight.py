"""Materialize M3179 steer-delta regression guard candidate artifacts."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_CONFIG as M3170_POLICY_CONFIG,
    POLICY_ID as M3170_POLICY_ID,
    source_localized_repair_direct_action,
    source_localized_repair_features,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as M3103_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3179-engineering-controller-active-safety-driver-residual-hard-safety-"
    "steer-delta-regression-guard-materialization-preflight"
)
NEXT_ID = (
    "m3180-engineering-controller-active-safety-driver-residual-hard-safety-"
    "steer-delta-regression-guard-materialization-result-audit"
)
M3178_ID = (
    "m3178-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-targeted-trace-ablation-result-audit"
)
M3177_ID = (
    "m3177-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-targeted-trace-ablation-materialization-preflight"
)
M3170_ID = (
    "m3170-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

POLICY_ID = "m3179_steer_delta_regression_guard_overlay"
DEFAULT_M3178_AUDIT = Path(f"docs/{M3178_ID}.md")
DEFAULT_M3177_DIR = Path(
    "runs/m3177_engineering_controller_active_safety_driver_residual_hard_safety_"
    "behavior_negative_targeted_trace_ablation_materialization_preflight"
)
DEFAULT_M3170_DIR = Path(
    "runs/m3170_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3179_engineering_controller_active_safety_driver_residual_hard_safety_"
    "steer_delta_regression_guard_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3179 Active Safety Driver residual hard-safety steer-delta regression guard "
    "materialization only; artifacts may define a deterministic actor-visible obs72 to "
    "direct action3 candidate that preserves the M3170 throttle and brake overlay while "
    "zeroing the M3170 steer delta relative to M3105/M3103 fallback, plus rule, contract, "
    "probe, claim, gate, doc, and M3180 audit manifest artifacts. No reset, step, rollout, "
    "replay, validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, public driver default mutation, driver-performance verdict, current-sim "
    "verdict, repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "measurement result, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

POLICY_CONFIG: dict[str, Any] = deepcopy(M3170_POLICY_CONFIG)
POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "derived_from_policy_id": M3170_POLICY_ID,
        "repair_route": "steer_delta_regression_guard_after_targeted_trace_ablation",
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
POLICY_CONFIG["steer_delta_regression_guard"] = {
    "enabled": True,
    "guard_mode": "zero_candidate_steer_delta_preserve_throttle_brake_delta",
    "max_abs_guarded_steer_delta": 0.0,
    "evidence_source": "m3177_ablate_steer_delta_success_candidate_collision",
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
    "derived_from_policy_id",
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
    "m3170_steer",
    "m3170_throttle",
    "m3170_brake",
    "m3179_steer",
    "m3179_throttle",
    "m3179_brake",
    "m3170_steer_delta",
    "m3170_throttle_delta",
    "m3170_brake_delta",
    "m3179_steer_delta",
    "m3179_throttle_delta",
    "m3179_brake_delta",
    "steer_delta_guarded_to_zero",
    "throttle_delta_preserved",
    "brake_delta_preserved",
    "collision_alpha",
    "boundary_alpha",
    "obstacle_urgency",
    "edge_urgency",
    "speed_mps",
    "action_finite",
    "action_bounded",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3179",
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


def _close(left: float, right: float, tol: float = 1.0e-6) -> bool:
    return abs(left - right) <= tol


def _m3178_selects_m3179(audit_text: str) -> bool:
    return (
        "m3179-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-materialization-preflight"
        in audit_text
        or "steer-delta regression guard materialization" in audit_text
        or "steer_delta_regression_guard" in audit_text
    )


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "direct_action_policy_config": output_dir / "direct_action_policy_config.json",
        "steer_delta_guard_rule_rows": output_dir / "steer_delta_guard_rule_rows.csv",
        "runtime_contract_rows": output_dir / "runtime_contract_rows.csv",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3178_audit: Path,
    m3177_dir: Path,
    m3170_dir: Path,
    m3105_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3178_audit": m3178_audit,
        "m3177_summary": m3177_dir / "summary.json",
        "m3177_ablation_variant_rows": m3177_dir / "ablation_variant_rows.csv",
        "m3177_gate_rows": m3177_dir / "gate_matrix.csv",
        "m3170_summary": m3170_dir / "summary.json",
        "m3170_policy_config": m3170_dir / "direct_action_policy_config.json",
        "m3170_gate_rows": m3170_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3178_audit_text": paths["m3178_audit"].read_text(encoding="utf-8") if exists["m3178_audit"] else "",
        "m3177_summary": read_json(paths["m3177_summary"]) if exists["m3177_summary"] else {},
        "m3177_ablation_variant_rows": read_csv_rows(paths["m3177_ablation_variant_rows"]),
        "m3177_gate_rows": read_csv_rows(paths["m3177_gate_rows"]),
        "m3170_summary": read_json(paths["m3170_summary"]) if exists["m3170_summary"] else {},
        "m3170_policy_config": read_json(paths["m3170_policy_config"]) if exists["m3170_policy_config"] else {},
        "m3170_gate_rows": read_csv_rows(paths["m3170_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
    }


def fallback_action(observation: np.ndarray) -> np.ndarray:
    return np.asarray(v4_v2_fallback_no_regression_hard_safety_direct_action(observation, V4_POLICY_CONFIG), dtype=np.float32)


def m3170_action(observation: np.ndarray) -> np.ndarray:
    return np.asarray(source_localized_repair_direct_action(observation, M3170_POLICY_CONFIG), dtype=np.float32)


def steer_delta_regression_guard_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute M3179 candidate direct [steer, throttle, brake] from obs72 only."""

    del config
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")
    fallback = fallback_action(obs)
    source = m3170_action(obs)
    delta = source - fallback
    guarded = fallback + np.asarray([0.0, delta[1], delta[2]], dtype=np.float32)
    return np.clip(guarded, -1.0, 1.0).astype(np.float32)


def rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "m3179-steer-delta-guard-rule-0001",
            "rule_family": "steer_delta_regression_guard",
            "priority": 1,
            "input_feature_groups": "actor_visible_obs72|m3170_actor_visible_overlay_features|m3103_fallback_action",
            "output_channels": "steer|throttle|brake",
            "formula_summary": "fallback=m3103(obs72); candidate=m3170(obs72); delta=candidate-fallback; action=clip(fallback+[0,delta_throttle,delta_brake],-1,1)",
            "enabled_by_default": True,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def runtime_contract_rows() -> list[dict[str, Any]]:
    sample = steer_delta_regression_guard_direct_action(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32), POLICY_CONFIG)
    return [
        {
            "contract_id": "m3179-runtime-contract-0001",
            "contract_family": "direct_action_runtime",
            "runtime_symbol": "steer_delta_regression_guard_direct_action",
            "input_contract": "actor_visible_obs72_only",
            "output_contract": "direct_action3_clipped",
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "action_components": "|".join(ACTION_COMPONENTS),
            "output_semantics": OUTPUT_SEMANTICS,
            "fallback_policy_id": M3103_POLICY_ID,
            "derived_from_policy_id": M3170_POLICY_ID,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "public_driver_default_mutated": False,
            "status_pass": bool(sample.shape == (ACTION_DIM,) and np.all(np.isfinite(sample)) and np.max(np.abs(sample)) <= 1.0),
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def _active_observation() -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.7
    obs[12:28].reshape(8, 2)[:, 1] = 0.3
    obs[28:44].reshape(8, 2)[:, 1] = -0.3
    obs[44] = 1.0
    obs[45] = 0.1
    obs[46] = 0.0
    return obs


def action_probe_rows() -> list[dict[str, Any]]:
    probes = [
        ("zero_obs_fallback_probe", np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)),
        ("actor_visible_collision_overlay_probe", _active_observation()),
    ]
    rows: list[dict[str, Any]] = []
    for probe_family, obs in probes:
        fallback = fallback_action(obs)
        source = m3170_action(obs)
        guarded = steer_delta_regression_guard_direct_action(obs, POLICY_CONFIG)
        source_delta = source - fallback
        guarded_delta = guarded - fallback
        features = source_localized_repair_features(obs, M3170_POLICY_CONFIG)
        rows.append(
            {
                "probe_id": f"m3179-action-probe-{len(rows) + 1:04d}",
                "probe_family": probe_family,
                "fallback_steer": float(fallback[0]),
                "fallback_throttle": float(fallback[1]),
                "fallback_brake": float(fallback[2]),
                "m3170_steer": float(source[0]),
                "m3170_throttle": float(source[1]),
                "m3170_brake": float(source[2]),
                "m3179_steer": float(guarded[0]),
                "m3179_throttle": float(guarded[1]),
                "m3179_brake": float(guarded[2]),
                "m3170_steer_delta": float(source_delta[0]),
                "m3170_throttle_delta": float(source_delta[1]),
                "m3170_brake_delta": float(source_delta[2]),
                "m3179_steer_delta": float(guarded_delta[0]),
                "m3179_throttle_delta": float(guarded_delta[1]),
                "m3179_brake_delta": float(guarded_delta[2]),
                "steer_delta_guarded_to_zero": _close(float(guarded_delta[0]), 0.0),
                "throttle_delta_preserved": _close(float(guarded_delta[1]), float(source_delta[1])),
                "brake_delta_preserved": _close(float(guarded_delta[2]), float(source_delta[2])),
                "collision_alpha": _float(features.get("collision_alpha")),
                "boundary_alpha": _float(features.get("boundary_alpha")),
                "obstacle_urgency": _float(features.get("obstacle_urgency")),
                "edge_urgency": _float(features.get("edge_urgency")),
                "speed_mps": _float(features.get("speed_mps")),
                "action_finite": bool(np.all(np.isfinite(guarded))),
                "action_bounded": bool(np.max(np.abs(guarded)) <= 1.0),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _variant(source: Mapping[str, Any], variant_id: str) -> dict[str, Any]:
    return next((dict(row) for row in source["m3177_ablation_variant_rows"] if str(row.get("variant_id", "")) == variant_id), {})


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("policy_config", "materialization_artifact", True, True, "direct_action_policy_config.json"),
        ("rule_rows", "materialization_artifact", True, True, "steer_delta_guard_rule_rows.csv"),
        ("runtime_contract_rows", "materialization_artifact", True, True, "runtime_contract_rows.csv"),
        ("action_probe_rows", "materialization_artifact", True, True, "action_probe_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("measurement_result", "forbidden", False, False, "M3180 audit before measurement planning"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted deployable candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim result synthesis after measurement"),
        ("repair_success", "forbidden", False, False, "accepted full-fresh improvement plus validation path"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3179"),
    ]
    return [
        {
            "claim_id": f"m3179-{claim_id}",
            "claim_family": family,
            "allowed_in_m3179": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3179-{gate_id}",
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
    probes: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    candidate = _variant(source, "m3177_candidate_m3170")
    incumbent = _variant(source, "m3177_incumbent_m3105")
    steer_ablation = _variant(source, "m3177_ablate_steer_delta")
    throttle_ablation = _variant(source, "m3177_ablate_throttle_drop")
    brake_ablation = _variant(source, "m3177_ablate_brake_add")
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3178_selects_m3179_route", "lineage", _m3178_selects_m3179(source["m3178_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3177_status_pass", "lineage", _bool(source["m3177_summary"].get("status_pass", False)), source["m3177_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3177_gate_matrix_pass", "lineage", _bool(source["m3177_summary"].get("gate_matrix_pass", False)), source["m3177_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3170_status_pass", "lineage", _bool(source["m3170_summary"].get("status_pass", False)), source["m3170_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3177_candidate_collision", "evidence", _bool(candidate.get("collision", False)), candidate.get("collision"), True, "behavior_regression"),
        gate("m3177_incumbent_success", "evidence", _bool(incumbent.get("success", False)), incumbent.get("success"), True, "metric_artifact"),
        gate("m3177_steer_ablation_success", "evidence", _bool(steer_ablation.get("success", False)), steer_ablation.get("success"), True, "metric_artifact"),
        gate("m3177_throttle_ablation_still_collision", "evidence", _bool(throttle_ablation.get("collision", False)), throttle_ablation.get("collision"), True, "metric_artifact"),
        gate("m3177_brake_ablation_still_collision", "evidence", _bool(brake_ablation.get("collision", False)), brake_ablation.get("collision"), True, "metric_artifact"),
        gate("rule_rows", "materialization", len(rules) == 1, len(rules), 1, "metric_artifact"),
        gate("runtime_contract_rows_pass", "contract", all(_bool(row.get("status_pass", False)) for row in contracts), "all", "pass", "contract_violation"),
        gate("probe_actions_finite_bounded", "contract", all(_bool(row.get("action_finite", False)) and _bool(row.get("action_bounded", False)) for row in probes), "all", "finite_bounded", "contract_violation"),
        gate("probe_steer_delta_guarded", "contract", all(_bool(row.get("steer_delta_guarded_to_zero", False)) for row in probes), "all", "zero", "contract_violation"),
        gate("probe_throttle_brake_preserved", "contract", all(_bool(row.get("throttle_delta_preserved", False)) and _bool(row.get("brake_delta_preserved", False)) for row in probes), "all", "preserved", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31800,
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
        "hypothesis": "A bounded result audit can accept or reject M3179 steer-delta regression guard materialization before any measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_policy_config.json"),
                str(output_dir / "steer_delta_guard_rule_rows.csv"),
                str(output_dir / "runtime_contract_rows.csv"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3179 steer-delta guard materialization before measurement planning"],
            "derived_from": [MILESTONE_ID, M3178_ID, M3177_ID, M3170_ID, M3105_ID],
            "blocked_by": [
                "M3179 materialization requires audit before any measurement",
                "the candidate must preserve actor-visible-only runtime inputs",
            ],
            "supersedes": ["direct full-fresh measurement after M3178 without materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3180 must audit M3179 rule contract probe claim and gate artifacts",
            "M3180 must preserve obs72/action3 direct-action contract and public driver default unchanged",
            "M3180 must reject measurement validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3180 must select exactly one measurement artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run measurement validation ranking promotion or high-fidelity simulation in M3180",
            "do not convert M3179 materialization rows into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_behavior_negative_source_repair_decomposition",
            "evidence_axis": "behavior_negative_steer_delta_guard_result_audit",
            "evidence_increment": "audits steer-delta regression guard materialization artifacts before any measurement",
            "claim_scope": "Result audit only; no measurement validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3179 artifacts are missing or gate matrix fails",
                "stop if the guard requires hidden runtime labels as actor inputs",
                "route to measurement only after audit acceptance",
            ],
            "fallback_plan": [
                "route to M3179 artifact repair if rules or contracts fail",
                "route to stop if no actor-visible guard can be materialized",
                "preserve M3105/M3103 incumbent until a later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3179 materializes steer-delta regression guard artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3179 steer-delta regression guard materialization artifacts",
            "admission_evidence": ["M3179 summary rule contract probe claim and gate artifacts"],
            "blocked_shortcuts": [
                "no measurement validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver default mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3180 status queue scoreboard research log and review",
                "one follow-up manifest only if M3180 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3180 accepts or rejects M3179 as complete and claim-safe",
                "next measurement artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3180 audits engineering materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3180; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3179 materialization artifacts only.",
            "negative_result_policy": "Preserve engineering guard evidence and route measurement or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3179 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits steer-delta guard materialization before measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3180 audits engineering materialization evidence",
            "must_synthesize_if": [
                "M3180 cannot select measurement artifact-repair synthesis or stop",
                "M3180 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3180 audits M3179 row counts gates actor contract and claim boundaries",
            "M3180 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3180 hides missing M3179 artifacts or failed gates",
            "M3180 treats M3179 materialization as repair success or performance verdict",
            "M3180 changes actor input or action contract",
            "M3180 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3180 audits M3179 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_steer_delta_regression_guard_result_audit_doc",
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
            "# M3179 Steer-Delta Regression Guard Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- rule rows: {summary['rule_row_count']}",
            f"- runtime contract rows: {summary['runtime_contract_row_count']}",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3179 materializes the M3177-successful steer-delta ablation as a deterministic direct-action candidate. The candidate computes M3105/M3103 fallback and M3170 overlay from obs72 only, preserves M3170 throttle and brake deltas, and zeroes the M3170 steer delta. This is materialization only, not measurement or validation.",
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
    m3178_audit: Path,
    m3177_dir: Path,
    m3170_dir: Path,
    m3105_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str = "cpu",
) -> dict[str, Any]:
    del device
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3178_audit=m3178_audit, m3177_dir=m3177_dir, m3170_dir=m3170_dir, m3105_dir=m3105_dir)
    rules = rule_rows()
    contracts = runtime_contract_rows()
    probes = action_probe_rows()
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["direct_action_policy_config"], POLICY_CONFIG)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["steer_delta_guard_rule_rows"], rules, fieldnames=RULE_FIELDNAMES)
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
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_steer_delta_regression_guard_materialization_pass"
            if status_pass
            else "active_safety_driver_steer_delta_regression_guard_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": POLICY_ID,
        "fallback_policy_id": M3103_POLICY_ID,
        "derived_from_policy_id": M3170_POLICY_ID,
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "rule_row_count": len(rules),
        "runtime_contract_row_count": len(contracts),
        "runtime_contract_rows_pass": all(_bool(row.get("status_pass", False)) for row in contracts),
        "action_probe_row_count": len(probes),
        "action_probe_rows_pass": all(
            _bool(row.get("action_finite", False))
            and _bool(row.get("action_bounded", False))
            and _bool(row.get("steer_delta_guarded_to_zero", False))
            for row in probes
        ),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3177_status_pass": _bool(source["m3177_summary"].get("status_pass", False)),
        "m3177_gate_matrix_pass": _bool(source["m3177_summary"].get("gate_matrix_pass", False)),
        "m3170_status_pass": _bool(source["m3170_summary"].get("status_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_steer_delta_regression_guard_materialization_route_to_m3180_result_audit",
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
            "rule_row_count": len(rules),
            "runtime_contract_row_count": len(contracts),
            "action_probe_row_count": len(probes),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3178-audit", type=Path, default=DEFAULT_M3178_AUDIT)
    parser.add_argument("--m3177-dir", type=Path, default=DEFAULT_M3177_DIR)
    parser.add_argument("--m3170-dir", type=Path, default=DEFAULT_M3170_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3178_audit=args.m3178_audit,
        m3177_dir=args.m3177_dir,
        m3170_dir=args.m3170_dir,
        m3105_dir=args.m3105_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"rule_rows={summary['rule_row_count']}")
    print(f"action_probe_rows={summary['action_probe_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
