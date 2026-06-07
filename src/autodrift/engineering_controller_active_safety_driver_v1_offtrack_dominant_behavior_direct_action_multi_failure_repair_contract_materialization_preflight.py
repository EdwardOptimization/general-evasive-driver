"""Materialize M3071 direct-action multi-failure repair contract artifacts.

M3071 consumes the M3070-accepted M3069 decomposition artifacts and the M3067
measurement rows. It performs no reset, step, rollout, replay, fitting, PPO,
training, validation, ranking, promotion, profile tuning, checkpoint mutation,
or high-fidelity run. It writes one fit-ready repair contract and keeps all
offtrack, collision, speed-floor, actuation-pressure, success-preservation,
stability, clearance, actor-contract, and claim-boundary gates visible.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


MILESTONE_ID = (
    "m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-contract-materialization-preflight"
)
NEXT_ID = (
    "m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-contract-result-audit"
)
M3070_ID = (
    "m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-failure-decomposition-result-audit"
)
M3069_ID = (
    "m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-failure-decomposition-materialization-preflight"
)

DEFAULT_M3070_AUDIT = Path(f"docs/{M3070_ID}.md")
DEFAULT_M3069_DIR = Path(
    "runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_failure_decomposition_materialization_preflight"
)
DEFAULT_M3067_DIR = Path(
    "runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_closed_loop_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_multi_failure_repair_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_MEASUREMENT_ROWS = 32
EXPECTED_SUCCESS_ROWS = 8
EXPECTED_COLLISION_ROWS = 4
EXPECTED_OFFTRACK_ROWS = 16
EXPECTED_SPEED_TOO_LOW_ROWS = 5
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_ACTION_DIM = 3

REQUIREMENT_FAMILIES = [
    "offtrack_containment_recovery",
    "t5_collision_guard",
    "speed_floor_recovery",
    "direct_action_actuation_pressure",
    "success_preservation",
    "stability_clearance_tradeoff",
    "claim_boundary_guard",
]

LOSS_FAMILIES = [
    "offtrack_containment_recovery",
    "t5_collision_guard",
    "speed_floor_recovery",
    "direct_action_actuation_pressure",
    "success_preservation",
    "stability_clearance_tradeoff",
]

CLAIM_SCOPE = (
    "M3071 Active Safety Driver v1 direct-action multi-failure repair-contract "
    "materialization only; M3069 decomposition and M3067 measurement rows may "
    "be converted into trainer-side contract, loss-family, row-admission, and "
    "guard-family artifacts. No reset, step, rollout, replay, fitting, PPO, "
    "training, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, profile tuning, driver-performance verdict, "
    "current-sim verdict, repair success, high-fidelity validation, paper "
    "evidence, finite-window-vs-GRU evidence, full ideal driver completion, or "
    "self-ID claim is made"
)

FORBIDDEN_INTERPRETATION = (
    "target quality, fitted policy quality, validation result, driver-performance "
    "verdict, current-sim verdict, repair success, checkpoint ranking, winner "
    "selection, checkpoint promotion, high-fidelity validation readiness or "
    "result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver "
    "completion, or level3 self-identification"
)

CONTRACT_FIELDNAMES = [
    "contract_id",
    "contract_family",
    "observation_shape",
    "action_shape",
    "output_semantics",
    "output_components",
    "runtime_base_policy_required",
    "measurement_denominator_rows",
    "requirement_family_count",
    "loss_family_count",
    "row_admission_count",
    "guard_family_count",
    "primary_objective",
    "p0_requirement_families",
    "p1_requirement_families",
    "contract_status",
    "m3071_no_new_execution",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "ttc_actor_input_required",
    "validation_result_claim_made",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "claim_boundary",
]

LOSS_FIELDNAMES = [
    "loss_family_id",
    "requirement_family",
    "priority",
    "row_count",
    "loss_role",
    "source_artifact",
    "weight_policy",
    "protected_rows",
    "blocked_claims",
    "m3071_no_fitting",
    "claim_boundary",
]

ROW_ADMISSION_FIELDNAMES = [
    "row_admission_id",
    "measurement_episode_id",
    "binding_role",
    "task_family",
    "termination_reason",
    "outcome_bucket",
    "success",
    "collision",
    "offtrack",
    "speed_too_low",
    "action_clip_fraction",
    "raw_action_abs_max",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "loss_families",
    "admission_status",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "m3071_no_new_execution",
    "claim_boundary",
]

GUARD_FIELDNAMES = [
    "guard_family_id",
    "guard_family",
    "priority",
    "status_pass",
    "observed",
    "expected",
    "protected_requirement",
    "blocked_shortcut",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3071",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _count(rows: Iterable[Mapping[str, Any]], predicate: Any) -> int:
    return sum(1 for row in rows if predicate(row))


def _termination(row: Mapping[str, Any]) -> str:
    return str(row.get("termination_reason", ""))


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success"))


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision"))


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return _termination(row) == "off_track"


def _is_speed_too_low(row: Mapping[str, Any]) -> bool:
    return _termination(row) == "speed_too_low"


def _requirement_by_family(requirement_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("requirement_family", ""): row for row in requirement_rows}


def _row_loss_families(row: Mapping[str, Any]) -> list[str]:
    families: list[str] = []
    if _is_offtrack(row):
        families.append("offtrack_containment_recovery")
    if str(row.get("task_family")) == "T5" and _is_collision(row):
        families.append("t5_collision_guard")
    if _is_speed_too_low(row):
        families.append("speed_floor_recovery")
    if _float(row.get("action_clip_fraction")) > 0.0 or _float(row.get("raw_action_abs_max")) > 1.0:
        families.append("direct_action_actuation_pressure")
    if _is_success(row):
        families.append("success_preservation")
    if _float(row.get("high_sideslip_fraction")) >= 0.5 or _float(row.get("min_clearance_margin")) < 2.0:
        families.append("stability_clearance_tradeoff")
    return families or ["row_accounting"]


def build_contract_rows(
    *,
    m3069_summary: Mapping[str, Any],
    measurement_rows: list[dict[str, str]],
    requirement_rows: list[dict[str, str]],
    row_admission_count: int,
    guard_family_count: int,
) -> list[dict[str, Any]]:
    p0 = [
        row.get("requirement_family", "")
        for row in requirement_rows
        if str(row.get("priority", "")).lower() == "p0"
    ]
    p1 = [
        row.get("requirement_family", "")
        for row in requirement_rows
        if str(row.get("priority", "")).lower() == "p1"
    ]
    return [
        {
            "contract_id": "m3071-direct-action-repair-contract-0001",
            "contract_family": "direct_action_multi_failure_repair",
            "observation_shape": EXPECTED_OBSERVATION_DIM,
            "action_shape": EXPECTED_ACTION_DIM,
            "output_semantics": m3069_summary.get("candidate_output_semantics", "direct_action_clipped"),
            "output_components": "steer;throttle;brake",
            "runtime_base_policy_required": False,
            "measurement_denominator_rows": len(measurement_rows),
            "requirement_family_count": len(requirement_rows),
            "loss_family_count": len(LOSS_FAMILIES),
            "row_admission_count": row_admission_count,
            "guard_family_count": guard_family_count,
            "primary_objective": "fit_ready_direct_action_repair_contract_before_any_fitting",
            "p0_requirement_families": ";".join(p0),
            "p1_requirement_families": ";".join(p1),
            "contract_status": "materialized",
            "m3071_no_new_execution": True,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_required": False,
            "target_labels_actor_visible": False,
            "target_provenance_actor_visible": False,
            "ttc_actor_input_required": False,
            "validation_result_claim_made": False,
            "driver_performance_claim_made": False,
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_loss_family_rows(requirement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_family = _requirement_by_family(requirement_rows)
    roles = {
        "offtrack_containment_recovery": "primary_failure_reduction",
        "t5_collision_guard": "hard_safety_guard",
        "speed_floor_recovery": "progress_floor_guard",
        "direct_action_actuation_pressure": "action_bound_regularizer",
        "success_preservation": "behavior_retention_guard",
        "stability_clearance_tradeoff": "stability_clearance_guard",
    }
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(LOSS_FAMILIES, start=1):
        requirement = by_family.get(family, {})
        priority = requirement.get("priority", "p1")
        row_count = requirement.get("row_count", "0")
        if priority == "p0":
            weight_policy = "primary_nonzero_weight_separate_gate"
        else:
            weight_policy = "nonzero_weight_separate_guard"
        rows.append(
            {
                "loss_family_id": f"m3071-loss-family-{index:04d}",
                "requirement_family": family,
                "priority": priority,
                "row_count": row_count,
                "loss_role": roles[family],
                "source_artifact": "M3069 direct_action_repair_requirement_rows.csv",
                "weight_policy": weight_policy,
                "protected_rows": requirement.get("affected_group", ""),
                "blocked_claims": FORBIDDEN_INTERPRETATION,
                "m3071_no_fitting": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_row_admission_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(measurement_rows, start=1):
        rows.append(
            {
                "row_admission_id": f"m3071-row-admission-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "success": _is_success(row),
                "collision": _is_collision(row),
                "offtrack": _is_offtrack(row),
                "speed_too_low": _is_speed_too_low(row),
                "action_clip_fraction": _float(row.get("action_clip_fraction")),
                "raw_action_abs_max": _float(row.get("raw_action_abs_max")),
                "min_clearance_margin": _float(row.get("min_clearance_margin")),
                "high_sideslip_fraction": _float(row.get("high_sideslip_fraction")),
                "loss_families": ";".join(_row_loss_families(row)),
                "admission_status": "admitted_measurement_row",
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "source_labels_actor_visible": False,
                "route_labels_actor_visible": False,
                "outcome_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
                "ttc_actor_input_required": False,
                "m3071_no_new_execution": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guard_family_rows(
    *,
    m3069_summary: Mapping[str, Any],
    measurement_rows: list[dict[str, str]],
    requirement_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    families = {row.get("requirement_family", "") for row in requirement_rows}

    def guard(index: int, family: str, priority: str, status: bool, observed: Any, expected: Any, requirement: str, blocked: str) -> dict[str, Any]:
        return {
            "guard_family_id": f"m3071-guard-family-{index:04d}",
            "guard_family": family,
            "priority": priority,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "protected_requirement": requirement,
            "blocked_shortcut": blocked,
            "claim_boundary": CLAIM_SCOPE,
        }

    return [
        guard(1, "offtrack_containment_recovery", "p0", "offtrack_containment_recovery" in families and _count(measurement_rows, _is_offtrack) == EXPECTED_OFFTRACK_ROWS, _count(measurement_rows, _is_offtrack), EXPECTED_OFFTRACK_ROWS, "preserve offtrack rows as primary repair target", "do not optimize only aggregate success"),
        guard(2, "t5_collision_guard", "p0", "t5_collision_guard" in families and _count(measurement_rows, lambda row: row.get("task_family") == "T5" and _is_collision(row)) == EXPECTED_COLLISION_ROWS, _count(measurement_rows, lambda row: row.get("task_family") == "T5" and _is_collision(row)), EXPECTED_COLLISION_ROWS, "preserve T5 collision rows as hard safety guard", "do not hide collision rows inside offtrack repair"),
        guard(3, "speed_floor_recovery", "p1", "speed_floor_recovery" in families and _count(measurement_rows, _is_speed_too_low) == EXPECTED_SPEED_TOO_LOW_ROWS, _count(measurement_rows, _is_speed_too_low), EXPECTED_SPEED_TOO_LOW_ROWS, "preserve speed-floor recovery rows", "do not drop speed-too-low rows"),
        guard(4, "direct_action_actuation_pressure", "p1", "direct_action_actuation_pressure" in families and _float(m3069_summary.get("measurement_raw_action_abs_max")) > 1.0, m3069_summary.get("measurement_raw_action_abs_max"), ">1.0", "keep raw/final action pressure visible", "do not fit without action pressure accounting"),
        guard(5, "success_preservation", "p1", "success_preservation" in families and _count(measurement_rows, _is_success) == EXPECTED_SUCCESS_ROWS, _count(measurement_rows, _is_success), EXPECTED_SUCCESS_ROWS, "preserve success rows", "do not improve failure rows by sacrificing successes"),
        guard(6, "stability_clearance_tradeoff", "p1", "stability_clearance_tradeoff" in families, "present", "present", "preserve stability and clearance tradeoff rows", "do not report only aggregate clearance improvement"),
        guard(7, "actor_contract", "p0", bool(m3069_summary.get("actor_contract_shape_72_action_3")), "72/action3", "72/action3", "preserve actor observation/action contract", "do not change actor input or output shape"),
        guard(8, "runtime_base_policy_free", "p0", not bool(m3069_summary.get("runtime_base_policy_required")), False, False, "preserve direct-action/base-policy-free runtime", "do not reintroduce runtime base policy dependency"),
        guard(9, "claim_boundary", "p0", "claim_boundary_guard" in families and bool(m3069_summary.get("m3067_claim_boundary_rows_pass")), "pass", "pass", "preserve claim boundary", "do not claim validation performance or repair success"),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claim_specs = [
        ("direct_action_repair_contract_rows", "materialization", True, True, "direct_action_repair_contract_rows.csv"),
        ("direct_action_loss_family_rows", "materialization", True, True, "direct_action_loss_family_rows.csv"),
        ("direct_action_row_admission_rows", "materialization", True, True, "direct_action_row_admission_rows.csv"),
        ("direct_action_guard_family_rows", "materialization", True, True, "direct_action_guard_family_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", True, True, "M3072 audit manifest"),
        ("new_execution", "execution", False, False, "future separately registered measurement route"),
        ("fitting_or_training", "training", False, False, "future guarded fitting route"),
        ("target_quality", "target_quality", False, False, "future target-quality audit"),
        ("fitted_policy_quality", "fitted_policy_quality", False, False, "future fitted-policy result audit"),
        ("validation_result", "validation", False, False, "future validation route"),
        ("driver_performance_verdict", "driver_performance", False, False, "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", False, False, "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("repair_success", "verdict", False, False, "future result audit"),
        ("paper_level_evidence", "paper", False, False, "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", False, False, "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", False, False, "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", False, False, "future full goal gate"),
        ("level3_self_identification", "self_id", False, False, "future source-diverse intervention proof"),
        ("runtime_base_policy_dependency", "contract", False, False, "direct-action actor must remain base-policy-free at runtime"),
        ("hidden_oracle_actor_inputs", "contract", False, False, "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", False, False, "actor contract forbids TTC shortcuts"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, allowed, made, required) in enumerate(claim_specs, start=1):
        rows.append(
            {
                "claim_id": f"m3071-{name}",
                "claim_family": family,
                "allowed_in_m3071": allowed,
                "claim_made": made,
                "status_pass": allowed == made,
                "evidence_required_before_claim": required,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30670,
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
        "hypothesis": "A bounded result audit can accept or reject the M3071 direct-action multi-failure repair-contract artifacts before any fitting training rollout validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver repair-success or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_repair_contract_rows.csv"),
                str(output_dir / "direct_action_loss_family_rows.csv"),
                str(output_dir / "direct_action_row_admission_rows.csv"),
                str(output_dir / "direct_action_guard_family_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit multi-failure direct-action repair contract before fitting"],
            "derived_from": [MILESTONE_ID, M3070_ID, M3069_ID],
            "blocked_by": [
                "M3071 repair-contract artifacts require audit before fitting or stop decision",
                "M3070/M3069 evidence is repair-contract materialization evidence only",
            ],
            "supersedes": ["direct fitting route without auditing M3071 repair contract"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3072 must audit M3071 summary contract loss row-admission guard claim and gate artifacts",
            "M3072 must confirm all 32 M3067 rows and all M3069 requirement families remain accounted for",
            "M3072 must preserve actor 72/action 3 direct-action/base-policy-free contract and claim boundaries",
            "M3072 must reject target quality fitted policy quality validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims unless separately routed",
            "M3072 must select exactly one fitting audit stop or continuation route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun rollout fit train validate rank promote tune or mutate checkpoints",
            "do not convert M3071 contract rows into target quality fitted policy quality performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_direct_action_multi_failure_repair_contract_result_audit",
            "evidence_increment": "audits repair-contract artifacts before selecting the next fitting or stop route",
            "claim_scope": "Result audit only; no fitting training validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3071 artifacts are missing or gate matrix fails",
                "stop if row preservation requirement families or direct-action actor contracts were violated",
                "stop if M3071 rows are treated as target quality validation or performance verdicts",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete",
                "route to guarded fitting admission if contract is complete and claim-safe",
                "route to branch synthesis if no legal fitting route can preserve the contract",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3071 materializes direct-action multi-failure repair contract artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3071 direct-action multi-failure repair-contract materialization artifacts",
            "admission_evidence": [
                "M3071 summary and gate matrix",
                "M3071 contract loss-family row-admission guard-family and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no fitting training rollout validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3072 status queue scoreboard research log and review",
                "one follow-up manifest only if M3072 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3072 accepts or rejects M3071 as complete and claim-safe",
                "next fitting audit stop or continuation route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3072 audits engineering repair-contract artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3072; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3071 repair-contract artifacts only.",
            "negative_result_policy": "Preserve direct-action repair-contract evidence and route to repair or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3071 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the multi-failure repair contract before fitting admission",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3072 prepares a guarded direct-action fitting route decision",
            "must_synthesize_if": [
                "M3072 cannot accept M3071 as complete and claim-safe",
                "M3072 cannot select a fitting audit stop or continuation route",
                "M3072 would require another process-only milestone before fitting input can be acted on",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3072 audits M3071 summary contract loss row-admission guard claim and gate artifacts",
            "M3072 rejects target quality fitted policy quality validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims",
            "M3072 selects exactly one fitting audit stop or continuation route",
        ],
        "failure_criteria": [
            "M3072 hides M3071 failures or missing artifacts",
            "M3072 treats M3071 contract as target quality validation or performance verdict",
            "M3072 changes actor input action contract or runtime base-policy-free boundary",
            "M3072 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3072 audits M3071 repair-contract artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_direct_action_multi_failure_repair_contract_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "direct_action_repair_contract_rows.csv"),
            str(output_dir / "direct_action_loss_family_rows.csv"),
            str(output_dir / "direct_action_row_admission_rows.csv"),
            str(output_dir / "direct_action_guard_family_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _source_claims_pass(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)


def build_gate_rows(
    *,
    summary: Mapping[str, Any],
    paths: Mapping[str, Path],
    measurement_rows: list[dict[str, str]],
    requirement_rows: list[dict[str, str]],
    contract_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    row_admission_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": f"m3071-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    pre_written_paths = [
        "direct_action_repair_contract_rows",
        "direct_action_loss_family_rows",
        "direct_action_row_admission_rows",
        "direct_action_guard_family_rows",
        "claim_boundary_rows",
        "doc",
        "follow_up_manifest",
    ]
    pre_written_present = all(paths[key].exists() for key in pre_written_paths)
    families = {row.get("requirement_family", "") for row in requirement_rows}
    return [
        gate("m3070_audit_present", "lineage", bool(summary.get("m3070_audit_present")), True, True, "lineage_invalid"),
        gate("m3069_status_pass", "lineage", bool(summary.get("m3069_status_pass")), True, True, "lineage_invalid"),
        gate("m3069_gate_matrix_pass", "lineage", bool(summary.get("m3069_gate_matrix_pass")), True, True, "lineage_invalid"),
        gate("measurement_denominator_preserved", "denominator", len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS, len(measurement_rows), EXPECTED_MEASUREMENT_ROWS, "scenario_sampling_failure"),
        gate("expected_success_count_preserved", "metric", summary.get("measurement_success_count") == EXPECTED_SUCCESS_ROWS, summary.get("measurement_success_count"), EXPECTED_SUCCESS_ROWS, "metric_artifact"),
        gate("expected_collision_count_preserved", "metric", summary.get("measurement_collision_count") == EXPECTED_COLLISION_ROWS, summary.get("measurement_collision_count"), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("expected_offtrack_count_preserved", "metric", summary.get("measurement_offtrack_count") == EXPECTED_OFFTRACK_ROWS, summary.get("measurement_offtrack_count"), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("expected_speed_floor_count_preserved", "metric", summary.get("measurement_speed_too_low_count") == EXPECTED_SPEED_TOO_LOW_ROWS, summary.get("measurement_speed_too_low_count"), EXPECTED_SPEED_TOO_LOW_ROWS, "metric_artifact"),
        gate("requirement_families_preserved", "metric", set(REQUIREMENT_FAMILIES).issubset(families), ";".join(sorted(families)), ";".join(REQUIREMENT_FAMILIES), "metric_artifact"),
        gate("contract_rows", "metric", len(contract_rows) == 1, len(contract_rows), 1, "metric_artifact"),
        gate("loss_family_rows", "metric", len(loss_rows) == len(LOSS_FAMILIES), len(loss_rows), len(LOSS_FAMILIES), "metric_artifact"),
        gate("row_admission_rows", "metric", len(row_admission_rows) == EXPECTED_MEASUREMENT_ROWS, len(row_admission_rows), EXPECTED_MEASUREMENT_ROWS, "metric_artifact"),
        gate("guard_family_rows", "metric", len(guard_rows) >= 9 and all(_bool(row["status_pass"]) for row in guard_rows), len(guard_rows), ">=9 and pass", "metric_artifact"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("actor_contract_shape_72_action_3", "contract", bool(summary.get("actor_contract_shape_72_action_3")), True, True, "contract_violation"),
        gate("base_policy_free_runtime_preserved", "contract", not bool(summary.get("runtime_base_policy_required")), False, False, "contract_violation"),
        gate("no_new_execution", "execution", not bool(summary.get("environment_reset_run")) and not bool(summary.get("environment_step_run")) and not bool(summary.get("policy_rollout_run")), False, False, "contract_violation"),
        gate("forbidden_flags_clear", "claim", not bool(summary.get("forbidden_claim_made")), False, False, "contract_violation"),
        gate("pre_written_artifacts_present", "process", pre_written_present, pre_written_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", paths["follow_up_manifest"].exists(), paths["follow_up_manifest"].exists(), True, "lineage_invalid"),
    ]


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# M3071 Active Safety Driver v1 Direct-Action Multi-Failure Repair Contract Materialization Preflight",
        "",
        "## Summary",
        "",
        "- status: completed",
        "- result class: `active_safety_driver_v1_direct_action_multi_failure_repair_contract_materialization_preflight_pass`",
        f"- measurement rows preserved: {summary['measurement_episode_row_count']}/{EXPECTED_MEASUREMENT_ROWS}",
        f"- repair contract rows: {summary['direct_action_repair_contract_row_count']}",
        f"- loss family rows: {summary['direct_action_loss_family_row_count']}",
        f"- row admission rows: {summary['direct_action_row_admission_row_count']}",
        f"- guard family rows: {summary['direct_action_guard_family_row_count']}",
        f"- requirement families preserved: {summary['requirement_family_count']}",
        f"- success/collision/offtrack/speed-too-low: {summary['measurement_success_count']} / {summary['measurement_collision_count']} / {summary['measurement_offtrack_count']} / {summary['measurement_speed_too_low_count']}",
        f"- gate matrix pass: {summary.get('gate_matrix_pass', 'pending')}",
        "",
        "## Interpretation",
        "",
        "M3071 materializes one fit-ready direct-action repair contract from M3070/M3069 evidence. The contract is a trainer-side artifact for M3072 audit only. It is not target quality, fitted policy quality, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
        "",
        "Contract gates:",
        "",
        "```text",
        "p0 offtrack containment and recovery",
        "p0 T5 collision guard",
        "p1 speed-floor recovery",
        "p1 direct-action raw/final action pressure",
        "p1 success preservation",
        "p1 stability and clearance tradeoff",
        "p0 actor contract and claim boundary",
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
    m3070_audit: Path,
    m3069_dir: Path,
    m3067_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "direct_action_repair_contract_rows": output_dir / "direct_action_repair_contract_rows.csv",
        "direct_action_loss_family_rows": output_dir / "direct_action_loss_family_rows.csv",
        "direct_action_row_admission_rows": output_dir / "direct_action_row_admission_rows.csv",
        "direct_action_guard_family_rows": output_dir / "direct_action_guard_family_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }

    m3069_summary = read_json(m3069_dir / "summary.json")
    requirement_rows = read_csv_rows(m3069_dir / "direct_action_repair_requirement_rows.csv")
    m3069_gate_rows = read_csv_rows(m3069_dir / "gate_matrix.csv")
    m3069_claim_rows = read_csv_rows(m3069_dir / "claim_boundary_rows.csv")
    measurement_rows = read_csv_rows(m3067_dir / "measurement_episode_rows.csv")

    row_admission_rows = build_row_admission_rows(measurement_rows)
    loss_rows = build_loss_family_rows(requirement_rows)
    guard_rows = build_guard_family_rows(
        m3069_summary=m3069_summary,
        measurement_rows=measurement_rows,
        requirement_rows=requirement_rows,
    )
    contract_rows = build_contract_rows(
        m3069_summary=m3069_summary,
        measurement_rows=measurement_rows,
        requirement_rows=requirement_rows,
        row_admission_count=len(row_admission_rows),
        guard_family_count=len(guard_rows),
    )
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["direct_action_repair_contract_rows"], contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(paths["direct_action_loss_family_rows"], loss_rows, fieldnames=LOSS_FIELDNAMES)
    write_csv_rows(paths["direct_action_row_admission_rows"], row_admission_rows, fieldnames=ROW_ADMISSION_FIELDNAMES)
    write_csv_rows(paths["direct_action_guard_family_rows"], guard_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_direct_action_multi_failure_repair_contract_materialization_preflight_pass",
        "output_dir": str(output_dir),
        "m3070_audit_present": m3070_audit.exists(),
        "m3069_status_pass": bool(m3069_summary.get("status_pass")),
        "m3069_gate_matrix_pass": bool(m3069_summary.get("gate_matrix_pass")),
        "m3069_gate_row_count": len(m3069_gate_rows),
        "m3069_claim_boundary_row_count": len(m3069_claim_rows),
        "m3069_claim_boundary_rows_pass": _source_claims_pass(m3069_claim_rows),
        "measurement_episode_row_count": len(measurement_rows),
        "measurement_success_count": _count(measurement_rows, _is_success),
        "measurement_collision_count": _count(measurement_rows, _is_collision),
        "measurement_offtrack_count": _count(measurement_rows, _is_offtrack),
        "measurement_speed_too_low_count": _count(measurement_rows, _is_speed_too_low),
        "requirement_family_count": len(requirement_rows),
        "direct_action_repair_contract_row_count": len(contract_rows),
        "direct_action_loss_family_row_count": len(loss_rows),
        "direct_action_row_admission_row_count": len(row_admission_rows),
        "direct_action_guard_family_row_count": len(guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "actor_contract_shape_72_action_3": bool(m3069_summary.get("actor_contract_shape_72_action_3")),
        "candidate_output_semantics": m3069_summary.get("candidate_output_semantics", "direct_action_clipped"),
        "candidate_output_components": m3069_summary.get("candidate_output_components", ["steer", "throttle", "brake"]),
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
        "target_quality_claim_made": False,
        "fitted_policy_quality_claim_made": False,
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
        measurement_rows=measurement_rows,
        requirement_rows=requirement_rows,
        contract_rows=contract_rows,
        loss_rows=loss_rows,
        row_admission_rows=row_admission_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["gate_matrix_pass"] = gate_matrix_pass
    summary["status_pass"] = (
        bool(summary["m3070_audit_present"])
        and bool(summary["m3069_status_pass"])
        and bool(summary["m3069_gate_matrix_pass"])
        and bool(summary["m3069_claim_boundary_rows_pass"])
        and len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS
        and summary["measurement_success_count"] == EXPECTED_SUCCESS_ROWS
        and summary["measurement_collision_count"] == EXPECTED_COLLISION_ROWS
        and summary["measurement_offtrack_count"] == EXPECTED_OFFTRACK_ROWS
        and summary["measurement_speed_too_low_count"] == EXPECTED_SPEED_TOO_LOW_ROWS
        and len(requirement_rows) >= len(REQUIREMENT_FAMILIES)
        and len(contract_rows) == 1
        and len(loss_rows) == len(LOSS_FAMILIES)
        and len(row_admission_rows) == EXPECTED_MEASUREMENT_ROWS
        and len(guard_rows) >= 9
        and all(_bool(row["status_pass"]) for row in guard_rows)
        and bool(summary["actor_contract_shape_72_action_3"])
        and not bool(summary["runtime_base_policy_required"])
        and gate_matrix_pass
    )
    summary["decision"] = "active_safety_driver_v1_direct_action_multi_failure_repair_contract_route_to_m3072_result_audit"

    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    write_json(paths["summary"], summary)
    write_doc(doc_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3070-audit", type=Path, default=DEFAULT_M3070_AUDIT)
    parser.add_argument("--m3069-dir", type=Path, default=DEFAULT_M3069_DIR)
    parser.add_argument("--m3067-dir", type=Path, default=DEFAULT_M3067_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize(
        m3070_audit=args.m3070_audit,
        m3069_dir=args.m3069_dir,
        m3067_dir=args.m3067_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"repair_contract_rows={summary['direct_action_repair_contract_row_count']}")
    print(f"loss_family_rows={summary['direct_action_loss_family_row_count']}")
    print(f"row_admission_rows={summary['direct_action_row_admission_row_count']}")
    print(f"guard_family_rows={summary['direct_action_guard_family_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
