"""Materialize M3139 M3105-incumbent deployable reflex interface artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import (
    DRIVER_ID,
    INCUMBENT_MEASUREMENT_ID,
    ActiveSafetyReflexDriver,
    active_safety_reflex_action,
    policy_config_fingerprint,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as INCUMBENT_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3139-engineering-controller-active-safety-driver-m3105-incumbent-deployable-"
    "reflex-interface-materialization-preflight"
)
NEXT_ID = (
    "m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-"
    "reflex-interface-result-audit"
)
M3138_ID = (
    "m3138-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-"
    "guarded-fallback-hybrid-full-fresh-measurement-result-audit"
)
M3105_ID = INCUMBENT_MEASUREMENT_ID
M3103_ID = (
    "m3103-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-materialization-preflight"
)

DEFAULT_M3138_AUDIT = Path(f"docs/{M3138_ID}.md")
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3103_DIR = Path(
    "runs/m3103_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_"
    "reflex_interface_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

CLAIM_SCOPE = (
    "M3139 Active Safety Driver M3105-incumbent deployable reflex interface "
    "materialization only; artifacts may bind the public runtime API to the M3103/M3105 "
    "incumbent obs72-to-action3 [steer throttle brake] direct-action function, record "
    "contract probes, preserve M3105 measurement evidence, list residual blockers, write "
    "doc and M3140 audit manifest. No reset, step, rollout, replay, fitting, PPO, "
    "training, measurement, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, driver-performance verdict, current-sim verdict, repair "
    "success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, feasibility proof, or level3 "
    "self-identification"
)

ACTION_PROBE_FIELDNAMES = [
    "probe_id",
    "probe_family",
    "driver_id",
    "incumbent_policy_id",
    "active_steer",
    "active_throttle",
    "active_brake",
    "incumbent_steer",
    "incumbent_throttle",
    "incumbent_brake",
    "max_abs_delta_vs_incumbent",
    "action_finite",
    "action_bounded",
    "action_equivalent_to_incumbent",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "claim_boundary",
]
INCUMBENT_EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "source_milestone",
    "status_pass",
    "gate_matrix_pass",
    "measurement_episode_row_count",
    "measurement_failure_row_count",
    "measurement_success_count",
    "measurement_collision_count",
    "measurement_offtrack_count",
    "measurement_speed_too_low_count",
    "runtime_driver_id",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "claim_boundary",
]
RESIDUAL_BLOCKER_FIELDNAMES = [
    "blocker_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "blocker_family",
    "collision",
    "offtrack",
    "speed_too_low",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "lateral_rmse",
    "return",
    "speed_mean",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3139",
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


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "deployable_contract": output_dir / "deployable_contract.json",
        "action_probe_rows": output_dir / "action_probe_rows.csv",
        "incumbent_evidence_rows": output_dir / "incumbent_evidence_rows.csv",
        "residual_blocker_rows": output_dir / "residual_blocker_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3138_audit: Path, m3105_dir: Path, m3103_dir: Path) -> dict[str, Any]:
    paths = {
        "m3138_audit": m3138_audit,
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_episode_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3105_gate_matrix": m3105_dir / "gate_matrix.csv",
        "m3103_summary": m3103_dir / "summary.json",
        "m3103_policy_config": m3103_dir / "direct_action_policy_config.json",
        "m3103_gate_matrix": m3103_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3138_audit_text": paths["m3138_audit"].read_text(encoding="utf-8") if exists["m3138_audit"] else "",
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_episode_rows": read_csv_rows(paths["m3105_episode_rows"]),
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_matrix"]),
        "m3103_summary": read_json(paths["m3103_summary"]) if exists["m3103_summary"] else {},
        "m3103_policy_config": read_json(paths["m3103_policy_config"]) if exists["m3103_policy_config"] else {},
        "m3103_gate_rows": read_csv_rows(paths["m3103_gate_matrix"]),
    }


def _probe_observations() -> list[tuple[str, np.ndarray]]:
    probes: list[tuple[str, np.ndarray]] = []
    zero = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    probes.append(("zero_observation", zero))

    low_speed = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    low_speed[0] = 0.25
    probes.append(("low_speed_floor", low_speed))

    obstacle = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obstacle[0] = 0.85
    obstacle[44] = 1.0
    obstacle[45] = 0.12
    obstacle[46] = 0.02
    probes.append(("high_speed_obstacle", obstacle))

    edge = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    edge[0] = 0.85
    edge[12:28] = 0.02
    edge[28:44] = 0.03
    probes.append(("high_speed_edge", edge))

    combined = obstacle.copy()
    combined[12:28] = 0.02
    combined[28:44] = 0.03
    probes.append(("combined_obstacle_edge", combined))
    return probes


def action_probe_rows() -> list[dict[str, Any]]:
    driver = ActiveSafetyReflexDriver()
    contract = driver.contract_dict()
    rows: list[dict[str, Any]] = []
    for index, (family, obs) in enumerate(_probe_observations(), start=1):
        active_action = active_safety_reflex_action(obs)
        incumbent_action = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, V4_POLICY_CONFIG)
        delta = np.asarray(active_action, dtype=np.float32) - np.asarray(incumbent_action, dtype=np.float32)
        rows.append(
            {
                "probe_id": f"m3139-action-probe-{index:04d}",
                "probe_family": family,
                "driver_id": contract["driver_id"],
                "incumbent_policy_id": contract["incumbent_policy_id"],
                "active_steer": float(active_action[0]),
                "active_throttle": float(active_action[1]),
                "active_brake": float(active_action[2]),
                "incumbent_steer": float(incumbent_action[0]),
                "incumbent_throttle": float(incumbent_action[1]),
                "incumbent_brake": float(incumbent_action[2]),
                "max_abs_delta_vs_incumbent": float(np.max(np.abs(delta))),
                "action_finite": bool(np.all(np.isfinite(active_action))),
                "action_bounded": bool(np.max(np.abs(active_action)) <= 1.0),
                "action_equivalent_to_incumbent": bool(np.allclose(active_action, incumbent_action, rtol=0.0, atol=1e-7)),
                "runtime_base_policy_required": bool(contract["runtime_base_policy_required"]),
                "checkpoint_model_required": bool(contract["checkpoint_model_required"]),
                "recurrent_hidden_state_required": bool(contract["recurrent_hidden_state_required"]),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def incumbent_evidence_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source.get("m3105_summary", {})
    contract = ActiveSafetyReflexDriver().contract_dict()
    return [
        {
            "evidence_id": "m3139-incumbent-evidence-0001",
            "source_milestone": M3105_ID,
            "status_pass": _bool(summary.get("status_pass", False)),
            "gate_matrix_pass": _bool(summary.get("gate_matrix_pass", False)),
            "measurement_episode_row_count": int(summary.get("measurement_episode_row_count", 0) or 0),
            "measurement_failure_row_count": int(summary.get("measurement_failure_row_count", 0) or 0),
            "measurement_success_count": int(summary.get("measurement_success_count", 0) or 0),
            "measurement_collision_count": int(summary.get("measurement_collision_count", 0) or 0),
            "measurement_offtrack_count": int(summary.get("measurement_offtrack_count", 0) or 0),
            "measurement_speed_too_low_count": int(summary.get("measurement_speed_too_low_count", 0) or 0),
            "runtime_driver_id": contract["incumbent_policy_id"],
            "runtime_base_policy_required": bool(contract["runtime_base_policy_required"]),
            "checkpoint_model_required": bool(contract["checkpoint_model_required"]),
            "recurrent_hidden_state_required": bool(contract["recurrent_hidden_state_required"]),
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def residual_blocker_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        collision = _bool(episode.get("collision", False))
        offtrack = _offtrack(episode)
        speed_too_low = _speed_too_low(episode)
        if not (collision or offtrack or speed_too_low):
            continue
        if collision:
            blocker_family = "collision"
        elif offtrack:
            blocker_family = "offtrack"
        elif speed_too_low:
            blocker_family = "speed_too_low"
        else:
            blocker_family = "other_unsuccessful"
        rows.append(
            {
                "blocker_id": f"m3139-residual-blocker-{len(rows) + 1:04d}",
                "source_measurement_episode_id": episode.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "blocker_family": blocker_family,
                "collision": collision,
                "offtrack": offtrack,
                "speed_too_low": speed_too_low,
                "termination_reason": episode.get("termination_reason", ""),
                "outcome_bucket": episode.get("outcome_bucket", ""),
                "min_clearance_margin": episode.get("min_clearance_margin", ""),
                "high_sideslip_fraction": episode.get("high_sideslip_fraction", ""),
                "lateral_rmse": episode.get("lateral_rmse", ""),
                "return": episode.get("return", ""),
                "speed_mean": episode.get("speed_mean", ""),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("deployable_api_contract", "deployment_contract", True, "deployable_contract.json"),
        ("incumbent_lineage", "lineage", True, "M3103/M3105 incumbent contract"),
        ("action_equivalence_probes", "runtime_api", True, "action_probe_rows.csv"),
        ("residual_blocker_rows", "diagnostic", True, "residual_blocker_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3140 audit manifest"),
    ]
    blocked = [
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action deployable API forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3139-{claim_id}",
            "claim_family": family,
            "allowed_in_m3139": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3139-{claim_id}",
            "claim_family": family,
            "allowed_in_m3139": False,
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
        "priority": 31400,
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
        "hypothesis": "A bounded result audit can accept or reject the M3139 M3105-incumbent deployable reflex interface artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), "src/autodrift/active_safety_reflex_driver.py"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "deployable_contract.json"),
                str(output_dir / "action_probe_rows.csv"),
                str(output_dir / "incumbent_evidence_rows.csv"),
                str(output_dir / "residual_blocker_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit deployable API binding to the current M3105/M3103 incumbent reflex"],
            "derived_from": [MILESTONE_ID, M3138_ID, M3105_ID, M3103_ID],
            "blocked_by": [
                "M3139 must be audited before the public API is treated as deployment-ready evidence",
                "M3105 residual 5 collision and 2 offtrack blockers remain unsolved",
            ],
            "supersedes": ["using the older M3078 active_safety_reflex_driver binding as the current deployment interface"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3140 must audit M3139 contract action-probe evidence and residual blocker rows",
            "M3140 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3140 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3140 must state that residual M3105 blockers remain unsolved",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3139 deployable API binding into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_m3105_incumbent_deployable_interface",
            "evidence_axis": "deployable_reflex_interface_binding",
            "evidence_increment": "audits that the public runtime API is bound to the M3105/M3103 incumbent and preserves residual blocker evidence",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3139 artifacts are missing or gate matrix fails",
                "stop if public API action probes diverge from M3103 incumbent action",
                "stop if residual M3105 blockers are hidden or reinterpreted as solved",
            ],
            "fallback_plan": [
                "route to deployable API repair if the public API binding is incomplete",
                "route to residual blocker branch only after M3140 accepts the deployable interface artifact",
                "retain M3105/M3103 incumbent until a stronger measured candidate passes same-row no-regression gates",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3138 stops the guarded fallback hybrid branch and retains M3105/M3103 as incumbent",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3139 deployable public API binding to M3105/M3103 incumbent",
            "admission_evidence": ["M3139 summary contract action probe incumbent evidence residual blocker and gate artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3140 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M3140 accepts or rejects M3139 as complete and claim-safe",
                "M3140 preserves residual blocker limitations explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3140 audits a deployable current-frame engineering API and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3140; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3139 deployable API materialization artifacts only.",
            "negative_result_policy": "Preserve deployable interface evidence and residual blockers rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3139 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "new_tool_or_infra",
            "process_overhead": "low",
            "local_search_risk": "low",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "aligns the public deployable API with the measured incumbent and preserves residual blocker evidence",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3140 audits engineering deployment interface evidence",
            "must_synthesize_if": [
                "M3140 cannot accept M3139 as complete and claim-safe",
                "M3140 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3140 hides the M3105 residual collision/offtrack blockers",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3140 audits M3139 public API contract action equivalence and residual blockers",
            "M3140 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
        ],
        "failure_criteria": [
            "M3140 hides M3139 failures or missing artifacts",
            "M3140 treats the deployable API binding as validation repair-success or performance verdict",
            "M3140 changes actor input or action contract",
        ],
        "decision_rule": "Pass only if M3140 audits M3139 artifacts while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_m3105_incumbent_deployable_reflex_interface_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3139-{gate_id}",
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
    contract: Mapping[str, Any],
    probes: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blocker_rows)
    route_marker = "retain M3105/M3103 no-regression direct-action path" in str(source.get("m3138_audit_text", ""))
    config_match = policy_config_fingerprint(V4_POLICY_CONFIG) == contract.get("policy_config_sha256")
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3138_retains_m3105_incumbent", "lineage", route_marker, "route marker", "present", "lineage_invalid"),
        gate("m3103_status_pass", "lineage", _bool(source["m3103_summary"].get("status_pass", False)), source["m3103_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3103_gate_matrix_pass", "lineage", _bool(source["m3103_summary"].get("gate_matrix_pass", False)), source["m3103_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(source["m3105_summary"].get("gate_matrix_pass", False)), source["m3105_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("driver_id_current", "contract", contract.get("driver_id") == DRIVER_ID, contract.get("driver_id"), DRIVER_ID, "contract_violation"),
        gate("incumbent_policy_id_current", "contract", contract.get("incumbent_policy_id") == INCUMBENT_POLICY_ID, contract.get("incumbent_policy_id"), INCUMBENT_POLICY_ID, "contract_violation"),
        gate("incumbent_measurement_id_current", "contract", contract.get("incumbent_measurement_id") == M3105_ID, contract.get("incumbent_measurement_id"), M3105_ID, "contract_violation"),
        gate("policy_config_fingerprint_current", "contract", config_match, contract.get("policy_config_sha256"), policy_config_fingerprint(V4_POLICY_CONFIG), "contract_violation"),
        gate("observation_shape", "contract", int(contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM, contract.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("action_shape", "contract", int(contract.get("action_shape", -1)) == ACTION_DIM, contract.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(contract.get("runtime_base_policy_required", True)), contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("checkpoint_model_absent", "contract", not _bool(contract.get("checkpoint_model_required", True)), contract.get("checkpoint_model_required"), False, "contract_violation"),
        gate("recurrent_hidden_absent", "contract", not _bool(contract.get("recurrent_hidden_state_required", True)), contract.get("recurrent_hidden_state_required"), False, "contract_violation"),
        gate("action_probe_rows_present", "runtime_api", len(probes) >= 5, len(probes), ">=5", "metric_artifact"),
        gate("action_probes_finite", "runtime_api", all(_bool(row.get("action_finite", False)) for row in probes), "all", "finite", "contract_violation"),
        gate("action_probes_bounded", "runtime_api", all(_bool(row.get("action_bounded", False)) for row in probes), "all", "bounded", "contract_violation"),
        gate("action_probes_equivalent_to_incumbent", "runtime_api", all(_bool(row.get("action_equivalent_to_incumbent", False)) for row in probes), "all", "equivalent", "contract_violation"),
        gate("m3105_full_fresh_rows", "incumbent_evidence", int(source["m3105_summary"].get("measurement_episode_row_count", 0) or 0) == 64, source["m3105_summary"].get("measurement_episode_row_count"), 64, "metric_artifact"),
        gate("m3105_measurement_failures_zero", "incumbent_evidence", int(source["m3105_summary"].get("measurement_failure_row_count", 0) or 0) == 0, source["m3105_summary"].get("measurement_failure_row_count"), 0, "metric_artifact"),
        gate("m3105_success_count_preserved", "incumbent_evidence", int(source["m3105_summary"].get("measurement_success_count", 0) or 0) == 57, source["m3105_summary"].get("measurement_success_count"), 57, "metric_artifact"),
        gate("m3105_collision_count_preserved", "incumbent_evidence", int(source["m3105_summary"].get("measurement_collision_count", 0) or 0) == 5, source["m3105_summary"].get("measurement_collision_count"), 5, "metric_artifact"),
        gate("m3105_offtrack_count_preserved", "incumbent_evidence", int(source["m3105_summary"].get("measurement_offtrack_count", 0) or 0) == 2, source["m3105_summary"].get("measurement_offtrack_count"), 2, "metric_artifact"),
        gate("m3105_speed_too_low_count_preserved", "incumbent_evidence", int(source["m3105_summary"].get("measurement_speed_too_low_count", 0) or 0) == 0, source["m3105_summary"].get("measurement_speed_too_low_count"), 0, "metric_artifact"),
        gate("incumbent_evidence_rows_present", "incumbent_evidence", len(evidence_rows) == 1, len(evidence_rows), 1, "metric_artifact"),
        gate("residual_blocker_rows_present", "residual_blocker", len(blocker_rows) == 7, len(blocker_rows), 7, "metric_artifact"),
        gate("residual_blocker_collision_count", "residual_blocker", blocker_counts.get("collision", 0) == 5, dict(sorted(blocker_counts.items())), "collision=5", "metric_artifact"),
        gate("residual_blocker_offtrack_count", "residual_blocker", blocker_counts.get("offtrack", 0) == 2, dict(sorted(blocker_counts.items())), "offtrack=2", "metric_artifact"),
        gate("residual_blocker_speed_too_low_count", "residual_blocker", blocker_counts.get("speed_too_low", 0) == 0, dict(sorted(blocker_counts.items())), "speed_too_low=0", "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3139 M3105-Incumbent Deployable Reflex Interface Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- driver id: `{summary['driver_id']}`",
            f"- incumbent policy id: `{summary['incumbent_policy_id']}`",
            f"- incumbent measurement: `{summary['incumbent_measurement_id']}`",
            f"- action probe rows: {summary['action_probe_row_count']}",
            f"- residual blocker rows: {summary['residual_blocker_row_count']}",
            f"- M3105 success/collision/offtrack/speed-too-low: {summary['m3105_success_count']}/{summary['m3105_collision_count']}/{summary['m3105_offtrack_count']}/{summary['m3105_speed_too_low_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3139 binds the public `autodrift.active_safety_reflex_driver` runtime API to the current M3105/M3103 no-regression direct-action incumbent. The runtime remains actor-visible obs72 input to direct `[steer, throttle, brake]` output with no runtime base policy, checkpoint model, recurrent hidden state, hidden oracle input, target/source/route/outcome labels, TTC shortcut, validation, ranking, or promotion dependency.",
            "",
            "This is a deployable interface artifact, not a repair-success or final-driver verdict. The M3105 residual blockers remain explicit: 5 collision rows and 2 offtrack rows on the 64-row fresh current-sim denominator.",
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
    m3138_audit: Path,
    m3105_dir: Path,
    m3103_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3138_audit=m3138_audit, m3105_dir=m3105_dir, m3103_dir=m3103_dir)
    contract = ActiveSafetyReflexDriver().contract_dict()
    probes = action_probe_rows()
    evidence = incumbent_evidence_rows(source)
    blockers = residual_blocker_rows(source["m3105_episode_rows"])
    write_json(paths["deployable_contract"], contract)
    write_csv_rows(paths["action_probe_rows"], probes, fieldnames=ACTION_PROBE_FIELDNAMES)
    write_csv_rows(paths["incumbent_evidence_rows"], evidence, fieldnames=INCUMBENT_EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["residual_blocker_rows"], blockers, fieldnames=RESIDUAL_BLOCKER_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        contract=contract,
        probes=probes,
        evidence_rows=evidence,
        blocker_rows=blockers,
        claim_rows=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_pass"
            if status_pass
            else "active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "driver_id": DRIVER_ID,
        "incumbent_policy_id": INCUMBENT_POLICY_ID,
        "incumbent_measurement_id": M3105_ID,
        "policy_config_sha256": contract["policy_config_sha256"],
        "public_api": "autodrift.active_safety_reflex_driver.ActiveSafetyReflexDriver.act(obs72)",
        "direct_action_formula": "action = active_safety_reflex_action(obs72) == v4_v2_fallback_no_regression_hard_safety_direct_action(obs72, V4_POLICY_CONFIG) -> [steer, throttle, brake]",
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "action_components": ["steer", "throttle", "brake"],
        "output_semantics": "direct_action_clipped",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "action_probe_row_count": len(probes),
        "action_probe_all_finite": all(_bool(row.get("action_finite", False)) for row in probes),
        "action_probe_all_bounded": all(_bool(row.get("action_bounded", False)) for row in probes),
        "action_probe_all_equivalent_to_incumbent": all(_bool(row.get("action_equivalent_to_incumbent", False)) for row in probes),
        "incumbent_evidence_row_count": len(evidence),
        "residual_blocker_row_count": len(blockers),
        "residual_blocker_counts": dict(sorted(blocker_counts.items())),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "m3105_gate_matrix_pass": _bool(source["m3105_summary"].get("gate_matrix_pass", False)),
        "m3105_measurement_rows": int(source["m3105_summary"].get("measurement_episode_row_count", 0) or 0),
        "m3105_measurement_failures": int(source["m3105_summary"].get("measurement_failure_row_count", 0) or 0),
        "m3105_success_count": int(source["m3105_summary"].get("measurement_success_count", 0) or 0),
        "m3105_collision_count": int(source["m3105_summary"].get("measurement_collision_count", 0) or 0),
        "m3105_offtrack_count": int(source["m3105_summary"].get("measurement_offtrack_count", 0) or 0),
        "m3105_speed_too_low_count": int(source["m3105_summary"].get("measurement_speed_too_low_count", 0) or 0),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
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
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_route_to_m3140_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "required_artifacts_present": present,
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
            "action_probe_row_count": len(probes),
            "residual_blocker_row_count": len(blockers),
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3138-audit", type=Path, default=DEFAULT_M3138_AUDIT)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3103-dir", type=Path, default=DEFAULT_M3103_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization_preflight(
        m3138_audit=args.m3138_audit,
        m3105_dir=args.m3105_dir,
        m3103_dir=args.m3103_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"action_probe_rows={summary['action_probe_row_count']}")
    print(f"residual_blocker_rows={summary['residual_blocker_row_count']}")
    print(f"m3105_success_count={summary['m3105_success_count']}")
    print(f"m3105_collision_count={summary['m3105_collision_count']}")
    print(f"m3105_offtrack_count={summary['m3105_offtrack_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
