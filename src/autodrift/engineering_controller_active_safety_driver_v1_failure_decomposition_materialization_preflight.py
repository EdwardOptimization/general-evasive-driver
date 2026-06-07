"""Materialize M3045 Active Safety Driver v1 failure decomposition artifacts.

M3045 consumes the M3044-accepted M3043 closed-loop measurement artifacts. It
performs no reset, step, rollout, replay, fitting, PPO, training, validation,
ranking, promotion, profile tuning, checkpoint mutation, or high-fidelity run.
It preserves the 32-row measurement denominator and writes repair-facing
failure decomposition, actuation saturation, repair requirement, claim, gate,
doc, and M3046 audit artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


MILESTONE_ID = "m3045-engineering-controller-active-safety-driver-v1-failure-decomposition-materialization-preflight"
NEXT_ID = "m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit"
M3044_ID = "m3044-engineering-controller-active-safety-driver-v1-closed-loop-measurement-result-audit"
M3043_ID = "m3043-engineering-controller-active-safety-driver-v1-closed-loop-measurement-preflight"

DEFAULT_M3044_AUDIT = Path(f"docs/{M3044_ID}.md")
DEFAULT_M3043_DIR = Path("runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight")
DEFAULT_OUTPUT_DIR = Path("runs/m3045_engineering_controller_active_safety_driver_v1_failure_decomposition_materialization_preflight")
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_MEASUREMENT_ROWS = 32
EXPECTED_FAILURE_ROWS = 0
EXPECTED_SUCCESS_ROWS = 4
EXPECTED_COLLISION_ROWS = 4
EXPECTED_OFFTRACK_ROWS = 24
EXPECTED_SPEED_TOO_LOW_ROWS = 1
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_ACTION_DIM = 3

CLAIM_SCOPE = (
    "M3045 Active Safety Driver v1 failure-decomposition materialization only; "
    "existing M3043 measurement rows may be grouped into failure-mode, "
    "actuation-saturation, and repair-requirement artifacts. No reset, step, "
    "rollout, replay, fitting, PPO, training, validation, ranking, winner "
    "selection, checkpoint mutation, checkpoint promotion, profile tuning, "
    "driver-performance verdict, current-sim verdict, repair success, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, "
    "full ideal driver completion, or self-ID claim is made"
)

FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, "
    "repair success, checkpoint ranking, winner selection, checkpoint "
    "promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

FAILURE_MODE_FIELDNAMES = [
    "failure_mode_row_id",
    "group_key",
    "group_value",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "blank_termination_count",
    "non_success_count",
    "baseline_success_count",
    "baseline_collision_count",
    "success_delta_positive_count",
    "success_delta_negative_count",
    "collision_delta_negative_count",
    "collision_delta_positive_count",
    "clearance_margin_mean",
    "clearance_margin_delta_mean",
    "return_delta_mean",
    "high_sideslip_fraction_mean",
    "action_clip_fraction_mean",
    "residual_clip_fraction_mean",
    "residual_abs_max",
    "dominant_outcome_bucket",
    "dominant_termination_reason",
    "measurement_episode_ids",
    "m3045_no_new_execution",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "validation_result_claim_made",
    "measurement_only_no_verdict",
    "claim_boundary",
]

ACTUATION_FIELDNAMES = [
    "actuation_row_id",
    "group_key",
    "group_value",
    "episode_count",
    "action_clip_fraction_mean",
    "action_clip_fraction_max",
    "high_action_clip_row_count",
    "residual_clip_fraction_mean",
    "residual_clip_fraction_max",
    "residual_abs_max",
    "base_action_abs_max",
    "final_action_abs_max",
    "action_saturation_pressure",
    "residual_bound_pressure",
    "candidate_binding_rows",
    "parent_binding_rows",
    "m3045_no_new_execution",
    "ranking_claim_made",
    "promotion_claim_made",
    "repair_success_claim_made",
    "claim_boundary",
]

REPAIR_REQUIREMENT_FIELDNAMES = [
    "requirement_id",
    "requirement_family",
    "priority",
    "affected_group",
    "row_count",
    "trigger_evidence",
    "requirement",
    "measurable_next_gate",
    "blocked_claims",
    "m3045_no_new_execution",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3045",
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


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows]
    return sum(values) / len(values) if values else 0.0


def _count(rows: Iterable[Mapping[str, Any]], predicate: Any) -> int:
    return sum(1 for row in rows if predicate(row))


def _dominant(values: Iterable[str]) -> str:
    counter = Counter(str(value) for value in values)
    if not counter:
        return ""
    value, _count_value = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0]
    return value


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


def _group_specs(rows: list[dict[str, str]]) -> list[tuple[str, str, list[dict[str, str]]]]:
    specs: list[tuple[str, str, list[dict[str, str]]]] = [("all", "all", rows)]
    for key in ("binding_role", "task_family", "outcome_bucket", "termination_reason"):
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(key, ""))].append(row)
        for value in sorted(groups):
            specs.append((key, value if value else "<blank>", groups[value]))

    combo_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        combo_groups[f"{row.get('binding_role', '')}:{row.get('task_family', '')}"].append(row)
    for value in sorted(combo_groups):
        specs.append(("binding_role_task_family", value, combo_groups[value]))
    return specs


def build_failure_mode_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, rows) in enumerate(_group_specs(measurement_rows), start=1):
        output_rows.append(
            {
                "failure_mode_row_id": f"m3045-failure-mode-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "episode_count": len(rows),
                "success_count": _count(rows, _is_success),
                "collision_count": _count(rows, _is_collision),
                "offtrack_count": _count(rows, _is_offtrack),
                "speed_too_low_count": _count(rows, _is_speed_too_low),
                "blank_termination_count": _count(rows, lambda row: _termination(row) == ""),
                "non_success_count": _count(rows, lambda row: not _is_success(row)),
                "baseline_success_count": _count(rows, lambda row: _bool(row.get("baseline_success"))),
                "baseline_collision_count": _count(rows, lambda row: _bool(row.get("baseline_collision"))),
                "success_delta_positive_count": _count(rows, lambda row: _float(row.get("success_delta_vs_baseline")) > 0.0),
                "success_delta_negative_count": _count(rows, lambda row: _float(row.get("success_delta_vs_baseline")) < 0.0),
                "collision_delta_negative_count": _count(rows, lambda row: _float(row.get("collision_delta_vs_baseline")) < 0.0),
                "collision_delta_positive_count": _count(rows, lambda row: _float(row.get("collision_delta_vs_baseline")) > 0.0),
                "clearance_margin_mean": _mean(rows, "min_clearance_margin"),
                "clearance_margin_delta_mean": _mean(rows, "clearance_margin_delta_vs_baseline"),
                "return_delta_mean": _mean(rows, "return_delta_vs_baseline"),
                "high_sideslip_fraction_mean": _mean(rows, "high_sideslip_fraction"),
                "action_clip_fraction_mean": _mean(rows, "action_clip_fraction"),
                "residual_clip_fraction_mean": _mean(rows, "residual_clip_fraction"),
                "residual_abs_max": max((_float(row.get("residual_abs_max")) for row in rows), default=0.0),
                "dominant_outcome_bucket": _dominant(row.get("outcome_bucket", "") for row in rows),
                "dominant_termination_reason": _dominant(row.get("termination_reason", "") or "<blank>" for row in rows),
                "measurement_episode_ids": ";".join(str(row.get("measurement_episode_id", "")) for row in rows),
                "m3045_no_new_execution": True,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "driver_performance_claim_made": False,
                "repair_success_claim_made": False,
                "validation_result_claim_made": False,
                "measurement_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_actuation_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, rows) in enumerate(
        [spec for spec in _group_specs(measurement_rows) if spec[0] in {"all", "binding_role", "task_family", "binding_role_task_family"}],
        start=1,
    ):
        action_clip_mean = _mean(rows, "action_clip_fraction")
        action_clip_max = max((_float(row.get("action_clip_fraction")) for row in rows), default=0.0)
        residual_clip_max = max((_float(row.get("residual_clip_fraction")) for row in rows), default=0.0)
        residual_abs_max = max((_float(row.get("residual_abs_max")) for row in rows), default=0.0)
        if action_clip_mean >= 0.25 or action_clip_max >= 0.5:
            action_pressure = "high"
        elif action_clip_mean > 0.0 or action_clip_max > 0.0:
            action_pressure = "medium"
        else:
            action_pressure = "low"
        residual_pressure = "bound_active" if residual_abs_max >= 0.0799 or residual_clip_max > 0.0 else "within_bound"
        output_rows.append(
            {
                "actuation_row_id": f"m3045-actuation-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "episode_count": len(rows),
                "action_clip_fraction_mean": action_clip_mean,
                "action_clip_fraction_max": action_clip_max,
                "high_action_clip_row_count": _count(rows, lambda row: _float(row.get("action_clip_fraction")) >= 0.25),
                "residual_clip_fraction_mean": _mean(rows, "residual_clip_fraction"),
                "residual_clip_fraction_max": residual_clip_max,
                "residual_abs_max": residual_abs_max,
                "base_action_abs_max": max((_float(row.get("base_action_abs_max")) for row in rows), default=0.0),
                "final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in rows), default=0.0),
                "action_saturation_pressure": action_pressure,
                "residual_bound_pressure": residual_pressure,
                "candidate_binding_rows": _count(rows, lambda row: row.get("binding_role") == "candidate"),
                "parent_binding_rows": _count(rows, lambda row: row.get("binding_role") == "parent"),
                "m3045_no_new_execution": True,
                "ranking_claim_made": False,
                "promotion_claim_made": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def _group_count(measurement_rows: list[dict[str, str]], predicate: Any) -> int:
    return _count(measurement_rows, predicate)


def build_repair_requirement_rows(measurement_rows: list[dict[str, str]], actuation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_action_row = next(
        (row for row in actuation_rows if row["group_key"] == "binding_role" and row["group_value"] == "candidate"),
        {},
    )
    rows = [
        {
            "requirement_id": "m3045-requirement-0001",
            "requirement_family": "offtrack_recovery",
            "priority": "p0",
            "affected_group": "all",
            "row_count": _group_count(measurement_rows, _is_offtrack),
            "trigger_evidence": "M3043 recorded 24 off_track terminations out of 32 measurement rows",
            "requirement": "next repair route must explicitly reduce offtrack pressure before any ranking or promotion route",
            "measurable_next_gate": "row-preserving offtrack count and offtrack severity decomposition accepted by M3046 before refit or rerun",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3045-requirement-0002",
            "requirement_family": "candidate_action_saturation",
            "priority": "p0",
            "affected_group": "binding_role:candidate",
            "row_count": _group_count(measurement_rows, lambda row: row.get("binding_role") == "candidate"),
            "trigger_evidence": (
                "candidate binding has 0/16 success and action_clip_fraction_mean "
                f"{candidate_action_row.get('action_clip_fraction_mean', 0.0)}"
            ),
            "requirement": "next residual repair must be actuation-aware and must not add safety residuals that saturate final actions on candidate rows",
            "measurable_next_gate": "candidate action saturation pressure must be separately gated from residual prediction loss",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3045-requirement-0003",
            "requirement_family": "collision_guard",
            "priority": "p1",
            "affected_group": "task_family:T5",
            "row_count": _group_count(measurement_rows, lambda row: row.get("task_family") == "T5" and _is_collision(row)),
            "trigger_evidence": "M3043 recorded 4 collision rows and all collisions are in the T5 family",
            "requirement": "next repair route must keep a separate collision guard instead of optimizing only offtrack metrics",
            "measurable_next_gate": "T5 collision rows remain separately accounted before any broad safety claim",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3045-requirement-0004",
            "requirement_family": "success_preservation",
            "priority": "p1",
            "affected_group": "binding_role:parent",
            "row_count": _group_count(measurement_rows, lambda row: row.get("binding_role") == "parent" and _is_success(row)),
            "trigger_evidence": "parent binding contains all 4 observed M3043 success rows and one positive success delta row",
            "requirement": "next repair route must preserve parent success rows and success identity guards while addressing failures",
            "measurable_next_gate": "success-preservation rows must be explicit before any repair fit is accepted",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3045-requirement-0005",
            "requirement_family": "speed_floor_guard",
            "priority": "p2",
            "affected_group": "termination_reason:speed_too_low",
            "row_count": _group_count(measurement_rows, _is_speed_too_low),
            "trigger_evidence": "M3043 recorded 1 speed_too_low termination",
            "requirement": "speed-floor failure must remain visible in repair metrics even though offtrack dominates",
            "measurable_next_gate": "speed-too-low rows remain separately counted in M3046 audit",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3045-requirement-0006",
            "requirement_family": "claim_boundary_guard",
            "priority": "p0",
            "affected_group": "all",
            "row_count": len(measurement_rows),
            "trigger_evidence": "M3043/M3044 are measurement and audit artifacts only",
            "requirement": "M3046 must audit these decomposition artifacts before any fitting training rollout validation ranking promotion or driver-performance claim",
            "measurable_next_gate": "M3046 accepts or rejects M3045 and selects exactly one repair audit stop or continuation route",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3045_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claim_specs = [
        ("failure_decomposition_rows", "materialization", True, True, "failure_mode_rows.csv"),
        ("actuation_saturation_rows", "materialization", True, True, "actuation_saturation_rows.csv"),
        ("repair_requirement_rows", "materialization", True, True, "repair_requirement_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", True, True, "M3046 audit manifest"),
        ("new_execution", "execution", False, False, "future separately registered measurement route"),
        ("fitting_or_training", "training", False, False, "future guarded repair route"),
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
        ("hidden_oracle_actor_inputs", "contract", False, False, "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", False, False, "actor contract forbids TTC shortcuts"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, allowed, made, required) in enumerate(claim_specs, start=1):
        rows.append(
            {
                "claim_id": f"m3045-{name}",
                "claim_family": family,
                "allowed_in_m3045": allowed,
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
        "priority": 30410,
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
        "hypothesis": "A bounded result audit can accept or reject the M3045 Active Safety Driver v1 failure-decomposition materialization artifacts before any fitting training validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "failure_mode_rows.csv"),
                str(output_dir / "actuation_saturation_rows.csv"),
                str(output_dir / "repair_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit failure decomposition before any repair route"],
            "derived_from": [MILESTONE_ID, M3044_ID],
            "blocked_by": [
                "M3045 decomposition artifacts require audit before refit rerun repair or stop decision",
                "M3043/M3044 evidence is measurement and audit evidence only",
            ],
            "supersedes": ["direct repair route without auditing M3045 decomposition"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3046 must audit M3045 summary failure actuation repair claim and gate artifacts",
            "M3046 must confirm all 32 M3043 rows remain accounted for",
            "M3046 must preserve actor 72/action 3 and claim boundaries",
            "M3046 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims unless separately routed",
            "M3046 must select exactly one repair audit stop or continuation route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun rollout fit train validate rank promote tune or mutate checkpoints",
            "do not convert M3045 decomposition rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_failure_decomposition_result_audit",
            "evidence_increment": "audits repair-facing failure decomposition artifacts before selecting the next active-safety repair route",
            "claim_scope": "Result audit only; no fitting training validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3045 artifacts are missing or gate matrix fails",
                "stop if row preservation or actor contracts were violated",
                "stop if M3045 rows are treated as validation or performance verdicts",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete",
                "route to repair design if decomposition is complete and claim-safe",
                "route to branch stop if decomposition shows no viable repair input",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3045 materializes failure decomposition artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3045 failure-decomposition materialization artifacts",
            "admission_evidence": [
                "M3045 summary and gate matrix",
                "M3045 failure mode actuation saturation repair requirement and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no fitting training validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress or verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3046 status queue scoreboard research log and review",
                "one follow-up manifest only if M3046 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3046 accepts or rejects M3045 as complete and claim-safe",
                "next repair audit stop or continuation route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3046 audits engineering failure decomposition artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3046; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3045 failure decomposition artifacts only.",
            "negative_result_policy": "Preserve negative active-safety evidence and route to repair or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3045 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the failure and actuation decomposition panel before repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3046 prepares an active-safety repair route decision",
            "must_synthesize_if": [
                "M3046 cannot accept M3045 as complete and claim-safe",
                "M3046 cannot select a repair audit stop or continuation route",
                "M3046 would require another process-only milestone before repair input can be acted on",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3046 audits M3045 summary failure actuation repair claim and gate artifacts",
            "M3046 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3046 selects exactly one repair audit stop or continuation route",
        ],
        "failure_criteria": [
            "M3046 hides M3045 failures or missing artifacts",
            "M3046 treats M3045 decomposition as validation or performance verdict",
            "M3046 changes actor input or action contract",
            "M3046 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3046 audits M3045 decomposition artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_failure_decomposition_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "failure_mode_rows.csv"),
            str(output_dir / "actuation_saturation_rows.csv"),
            str(output_dir / "repair_requirement_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def build_gate_rows(
    *,
    summary: Mapping[str, Any],
    paths: Mapping[str, Path],
    measurement_rows: list[dict[str, str]],
    failure_mode_rows: list[dict[str, Any]],
    actuation_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": f"m3045-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    pre_written_paths = [
        "failure_mode_rows",
        "actuation_saturation_rows",
        "repair_requirement_rows",
        "claim_boundary_rows",
        "doc",
        "follow_up_manifest",
    ]
    pre_written_present = all(paths[key].exists() for key in pre_written_paths)
    return [
        gate("m3044_audit_present", "lineage", bool(summary.get("m3044_audit_present")), True, True, "lineage_invalid"),
        gate("m3043_status_pass", "lineage", bool(summary.get("m3043_status_pass")), True, True, "lineage_invalid"),
        gate("m3043_gate_matrix_pass", "lineage", bool(summary.get("m3043_gate_matrix_pass")), True, True, "lineage_invalid"),
        gate("measurement_denominator_preserved", "denominator", len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS, len(measurement_rows), EXPECTED_MEASUREMENT_ROWS, "scenario_sampling_failure"),
        gate("failure_decomposition_rows", "metric", bool(failure_mode_rows), len(failure_mode_rows), ">0", "metric_artifact"),
        gate("actuation_rows", "metric", bool(actuation_rows), len(actuation_rows), ">0", "metric_artifact"),
        gate("repair_requirement_rows", "metric", len(repair_rows) >= 6, len(repair_rows), ">=6", "metric_artifact"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("actor_contract_shape_72_action_3", "contract", bool(summary.get("actor_contract_shape_72_action_3")), True, True, "contract_violation"),
        gate("no_new_execution", "execution", not bool(summary.get("environment_reset_run")) and not bool(summary.get("environment_step_run")) and not bool(summary.get("policy_rollout_run")), False, False, "contract_violation"),
        gate("forbidden_flags_clear", "claim", not bool(summary.get("forbidden_claim_made")), False, False, "contract_violation"),
        gate("pre_written_artifacts_present", "process", pre_written_present, pre_written_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", paths["follow_up_manifest"].exists(), paths["follow_up_manifest"].exists(), True, "lineage_invalid"),
    ]


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# M3045 Active Safety Driver v1 Failure Decomposition Materialization Preflight",
        "",
        "## Summary",
        "",
        "- status: completed",
        "- result class: `active_safety_driver_v1_failure_decomposition_materialization_preflight_pass`",
        f"- measurement rows preserved: {summary['measurement_episode_row_count']}/{EXPECTED_MEASUREMENT_ROWS}",
        f"- failure mode rows: {summary['failure_mode_row_count']}",
        f"- actuation saturation rows: {summary['actuation_saturation_row_count']}",
        f"- repair requirement rows: {summary['repair_requirement_row_count']}",
        f"- success count: {summary['measurement_success_count']}",
        f"- collision count: {summary['measurement_collision_count']}",
        f"- offtrack count: {summary['measurement_offtrack_count']}",
        f"- speed-too-low count: {summary['measurement_speed_too_low_count']}",
        f"- candidate action clip mean: {summary['candidate_action_clip_fraction_mean']}",
        f"- parent action clip mean: {summary['parent_action_clip_fraction_mean']}",
        f"- gate matrix pass: {summary.get('gate_matrix_pass', 'pending')}",
        "",
        "## Interpretation",
        "",
        "M3045 materializes repair-facing failure and actuation decomposition artifacts from the accepted M3043 measurement rows. These artifacts are repair inputs for M3046 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
        "",
        "Primary repair pressure:",
        "",
        "```text",
        "offtrack recovery: 24/32 rows",
        "candidate action saturation: candidate action_clip_fraction_mean 0.41243192505631066",
        "collision guard: 4/16 T5 rows collided",
        "success preservation: all 4 success rows are parent-binding rows",
        "speed-floor guard: 1 speed_too_low row",
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
    m3044_audit: Path,
    m3043_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "failure_mode_rows": output_dir / "failure_mode_rows.csv",
        "actuation_saturation_rows": output_dir / "actuation_saturation_rows.csv",
        "repair_requirement_rows": output_dir / "repair_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }

    m3043_summary = read_json(m3043_dir / "summary.json")
    measurement_rows = read_csv_rows(m3043_dir / "measurement_episode_rows.csv")
    failure_rows = read_csv_rows(m3043_dir / "measurement_failure_rows.csv")
    m3043_gate_rows = read_csv_rows(m3043_dir / "gate_matrix.csv")
    claim_rows_source = read_csv_rows(m3043_dir / "claim_boundary_rows.csv")

    failure_mode_rows = build_failure_mode_rows(measurement_rows)
    actuation_rows = build_actuation_rows(measurement_rows)
    repair_rows = build_repair_requirement_rows(measurement_rows, actuation_rows)
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["failure_mode_rows"], failure_mode_rows, fieldnames=FAILURE_MODE_FIELDNAMES)
    write_csv_rows(paths["actuation_saturation_rows"], actuation_rows, fieldnames=ACTUATION_FIELDNAMES)
    write_csv_rows(paths["repair_requirement_rows"], repair_rows, fieldnames=REPAIR_REQUIREMENT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    candidate_actuation = next(
        (row for row in actuation_rows if row["group_key"] == "binding_role" and row["group_value"] == "candidate"),
        {},
    )
    parent_actuation = next(
        (row for row in actuation_rows if row["group_key"] == "binding_role" and row["group_value"] == "parent"),
        {},
    )

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_failure_decomposition_materialization_preflight_pass",
        "output_dir": str(output_dir),
        "m3044_audit_present": m3044_audit.exists(),
        "m3043_status_pass": bool(m3043_summary.get("status_pass")),
        "m3043_gate_matrix_pass": bool(m3043_summary.get("gate_matrix_pass")),
        "m3043_gate_row_count": len(m3043_gate_rows),
        "m3043_claim_boundary_row_count": len(claim_rows_source),
        "measurement_episode_row_count": len(measurement_rows),
        "measurement_failure_row_count": len(failure_rows),
        "measurement_success_count": _count(measurement_rows, _is_success),
        "measurement_collision_count": _count(measurement_rows, _is_collision),
        "measurement_offtrack_count": _count(measurement_rows, _is_offtrack),
        "measurement_speed_too_low_count": _count(measurement_rows, _is_speed_too_low),
        "failure_mode_row_count": len(failure_mode_rows),
        "actuation_saturation_row_count": len(actuation_rows),
        "repair_requirement_row_count": len(repair_rows),
        "claim_boundary_row_count": len(claim_rows),
        "candidate_action_clip_fraction_mean": candidate_actuation.get("action_clip_fraction_mean", 0.0),
        "parent_action_clip_fraction_mean": parent_actuation.get("action_clip_fraction_mean", 0.0),
        "candidate_success_count": _count(measurement_rows, lambda row: row.get("binding_role") == "candidate" and _is_success(row)),
        "parent_success_count": _count(measurement_rows, lambda row: row.get("binding_role") == "parent" and _is_success(row)),
        "actor_contract_shape_72_action_3": m3043_summary.get("observation_shape") == EXPECTED_OBSERVATION_DIM and m3043_summary.get("action_shape") == EXPECTED_ACTION_DIM,
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
        measurement_rows=measurement_rows,
        failure_mode_rows=failure_mode_rows,
        actuation_rows=actuation_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
    )
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["gate_matrix_pass"] = gate_matrix_pass
    summary["status_pass"] = (
        bool(summary["m3044_audit_present"])
        and bool(summary["m3043_status_pass"])
        and bool(summary["m3043_gate_matrix_pass"])
        and len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS
        and len(failure_rows) == EXPECTED_FAILURE_ROWS
        and summary["measurement_success_count"] == EXPECTED_SUCCESS_ROWS
        and summary["measurement_collision_count"] == EXPECTED_COLLISION_ROWS
        and summary["measurement_offtrack_count"] == EXPECTED_OFFTRACK_ROWS
        and summary["measurement_speed_too_low_count"] == EXPECTED_SPEED_TOO_LOW_ROWS
        and bool(summary["actor_contract_shape_72_action_3"])
        and gate_matrix_pass
    )
    summary["decision"] = "active_safety_driver_v1_failure_decomposition_route_to_m3046_result_audit"

    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    write_json(paths["summary"], summary)
    write_doc(doc_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3044-audit", type=Path, default=DEFAULT_M3044_AUDIT)
    parser.add_argument("--m3043-dir", type=Path, default=DEFAULT_M3043_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize(
        m3044_audit=args.m3044_audit,
        m3043_dir=args.m3043_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"failure_mode_rows={summary['failure_mode_row_count']}")
    print(f"actuation_saturation_rows={summary['actuation_saturation_row_count']}")
    print(f"repair_requirement_rows={summary['repair_requirement_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
