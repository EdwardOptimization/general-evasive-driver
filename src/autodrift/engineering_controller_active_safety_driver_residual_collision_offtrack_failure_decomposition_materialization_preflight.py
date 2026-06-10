"""Materialize M3108 residual collision/offtrack failure decomposition artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight import (
    COMPARISON_FIELDNAMES,
    EXPECTED_FULL_ROWS,
    POLICY_ID,
)


MILESTONE_ID = (
    "m3108-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "failure-decomposition-materialization-preflight"
)
NEXT_ID = (
    "m3109-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "failure-decomposition-result-audit"
)
M3107_ID = "m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis"
M3106_ID = (
    "m3106-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-result-audit"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3107_SYNTHESIS = Path(f"docs/{M3107_ID}.md")
DEFAULT_M3106_AUDIT = Path(f"docs/{M3106_ID}.md")
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3108_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "failure_decomposition_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_RESIDUAL_AXES = {"collision_lateral_intrusion", "offtrack_boundary_recovery"}
EXPECTED_BASELINES = {"m3095", "m3100", "m3090"}

CLAIM_SCOPE = (
    "M3108 residual collision/offtrack failure-decomposition materialization only; "
    "existing M3105 measurement and same-row comparison rows may be transformed into "
    "row-preserving residual failure, axis summary, comparison, repair-requirement, "
    "claim, gate, doc, and M3109 audit artifacts. No reset, step, rollout, replay, "
    "fitting, PPO, training, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, driver-performance verdict, current-sim verdict, repair "
    "success, robustness-result, high-fidelity validation, paper evidence, finite-window-"
    "vs-GRU evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

RESIDUAL_FAILURE_FIELDNAMES = [
    "residual_failure_id",
    "measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "termination_reason",
    "outcome_bucket",
    "collision",
    "offtrack",
    "speed_too_low",
    "min_clearance_margin",
    "return",
    "speed_mean",
    "lateral_rmse",
    "high_sideslip_fraction",
    "action_rate_mean",
    "raw_action_abs_max",
    "final_action_abs_max",
    "recoverability_window_success_available",
    "recoverability_window_success",
    "same_row_baseline_count",
    "same_row_baselines",
    "all_baseline_outcomes_match",
    "m3108_no_new_execution",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "claim_boundary",
]
AXIS_SUMMARY_FIELDNAMES = [
    "axis_summary_id",
    "group_key",
    "group_value",
    "residual_row_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "candidate_rows",
    "parent_rows",
    "clearance_margin_mean",
    "return_mean",
    "speed_mean",
    "lateral_rmse_mean",
    "high_sideslip_fraction_mean",
    "action_rate_mean",
    "raw_action_abs_max",
    "dominant_termination_reason",
    "measurement_episode_ids",
    "m3108_no_new_execution",
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
    "m3108_no_new_execution",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3108",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows if str(row.get(key, "")).strip() != ""]
    return sum(values) / len(values) if values else 0.0


def _max(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows if str(row.get(key, "")).strip() != ""]
    return max(values) if values else 0.0


def _success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success"))


def _collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision"))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def _dominant(values: Iterable[str]) -> str:
    counter = Counter(str(value) if str(value) else "<blank>" for value in values)
    if not counter:
        return ""
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "residual_failure_rows": output_dir / "residual_failure_rows.csv",
        "residual_axis_summary_rows": output_dir / "residual_axis_summary_rows.csv",
        "residual_comparison_rows": output_dir / "residual_comparison_rows.csv",
        "residual_repair_requirement_rows": output_dir / "residual_repair_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3107_synthesis: Path, m3106_audit: Path, m3105_dir: Path) -> dict[str, Any]:
    paths = {
        "m3107_synthesis": m3107_synthesis,
        "m3106_audit": m3106_audit,
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_episode_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3105_comparison_rows": m3105_dir / "same_row_comparison_rows.csv",
        "m3105_contract_guard_rows": m3105_dir / "measurement_contract_guard_rows.csv",
        "m3105_claim_boundary_rows": m3105_dir / "claim_boundary_rows.csv",
        "m3105_gate_rows": m3105_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3107_synthesis_text": paths["m3107_synthesis"].read_text(encoding="utf-8") if exists["m3107_synthesis"] else "",
        "m3106_audit_text": paths["m3106_audit"].read_text(encoding="utf-8") if exists["m3106_audit"] else "",
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_episode_rows": read_csv_rows(paths["m3105_episode_rows"]),
        "m3105_comparison_rows": read_csv_rows(paths["m3105_comparison_rows"]),
        "m3105_contract_guard_rows": read_csv_rows(paths["m3105_contract_guard_rows"]),
        "m3105_claim_boundary_rows": read_csv_rows(paths["m3105_claim_boundary_rows"]),
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_rows"]),
    }


def _baseline_rows_by_source(comparison_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    rows_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in comparison_rows:
        rows_by_source[str(row.get("source_measurement_episode_id", ""))].append(row)
    return rows_by_source


def residual_failure_rows(
    episode_rows: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows_by_source = _baseline_rows_by_source(comparison_rows)
    residual = [row for row in episode_rows if not _success(row)]
    output: list[dict[str, Any]] = []
    for index, row in enumerate(residual, start=1):
        source_id = str(row.get("source_measurement_episode_id", ""))
        baseline_rows = rows_by_source.get(source_id, [])
        baseline_ids = sorted(str(item.get("baseline_id", "")) for item in baseline_rows)
        m3105_termination = str(row.get("termination_reason", ""))
        output.append(
            {
                "residual_failure_id": f"m3108-residual-failure-{index:04d}",
                "measurement_episode_id": row.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "termination_reason": m3105_termination,
                "outcome_bucket": row.get("outcome_bucket", ""),
                "collision": _collision(row),
                "offtrack": _offtrack(row),
                "speed_too_low": _speed_too_low(row),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "return": row.get("return", ""),
                "speed_mean": row.get("speed_mean", ""),
                "lateral_rmse": row.get("lateral_rmse", ""),
                "high_sideslip_fraction": row.get("high_sideslip_fraction", ""),
                "action_rate_mean": row.get("action_rate_mean", ""),
                "raw_action_abs_max": row.get("raw_action_abs_max", ""),
                "final_action_abs_max": row.get("final_action_abs_max", ""),
                "recoverability_window_success_available": row.get("recoverability_window_success_available", ""),
                "recoverability_window_success": row.get("recoverability_window_success", ""),
                "same_row_baseline_count": len(baseline_rows),
                "same_row_baselines": ";".join(baseline_ids),
                "all_baseline_outcomes_match": all(
                    str(item.get("baseline_termination_reason", "")) == m3105_termination for item in baseline_rows
                ),
                "m3108_no_new_execution": True,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def residual_comparison_rows(
    residual_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    residual_sources = {str(row["source_measurement_episode_id"]) for row in residual_rows}
    output = []
    for row in comparison_rows:
        if str(row.get("source_measurement_episode_id", "")) not in residual_sources:
            continue
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        output.append(item)
    return output


def _axis_groups(rows: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    specs = [("all", "all", rows)]
    for key in ("axis_id", "binding_role", "termination_reason"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(key, ""))].append(row)
        for value in sorted(grouped):
            specs.append((key, value, grouped[value]))
    combo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        combo[f"{row.get('axis_id', '')}:{row.get('termination_reason', '')}"].append(row)
    for value in sorted(combo):
        specs.append(("axis_termination", value, combo[value]))
    return specs


def residual_axis_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for index, (group_key, group_value, grouped) in enumerate(_axis_groups(rows), start=1):
        output.append(
            {
                "axis_summary_id": f"m3108-axis-summary-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "residual_row_count": len(grouped),
                "collision_count": sum(1 for row in grouped if _bool(row.get("collision"))),
                "offtrack_count": sum(1 for row in grouped if _bool(row.get("offtrack"))),
                "speed_too_low_count": sum(1 for row in grouped if _bool(row.get("speed_too_low"))),
                "candidate_rows": sum(1 for row in grouped if row.get("binding_role") == "candidate"),
                "parent_rows": sum(1 for row in grouped if row.get("binding_role") == "parent"),
                "clearance_margin_mean": _mean(grouped, "min_clearance_margin"),
                "return_mean": _mean(grouped, "return"),
                "speed_mean": _mean(grouped, "speed_mean"),
                "lateral_rmse_mean": _mean(grouped, "lateral_rmse"),
                "high_sideslip_fraction_mean": _mean(grouped, "high_sideslip_fraction"),
                "action_rate_mean": _mean(grouped, "action_rate_mean"),
                "raw_action_abs_max": _max(grouped, "raw_action_abs_max"),
                "dominant_termination_reason": _dominant(str(row.get("termination_reason", "")) for row in grouped),
                "measurement_episode_ids": ";".join(str(row.get("measurement_episode_id", "")) for row in grouped),
                "m3108_no_new_execution": True,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def build_repair_requirement_rows(residual_rows: list[dict[str, Any]], axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    del axis_rows
    axis_counts = Counter(str(row.get("axis_id", "")) for row in residual_rows)
    collision_count = sum(1 for row in residual_rows if _bool(row.get("collision")))
    offtrack_count = sum(1 for row in residual_rows if _bool(row.get("offtrack")))
    speed_count = sum(1 for row in residual_rows if _bool(row.get("speed_too_low")))
    specs = [
        (
            "m3108-requirement-0001",
            "collision_lateral_intrusion_guard",
            "p0",
            "axis:collision_lateral_intrusion",
            axis_counts.get("collision_lateral_intrusion", 0),
            "M3105 leaves residual collision_lateral_intrusion failures after M3095 plateau",
            "next repair route must isolate obstacle/lateral intrusion collision avoidance without reopening speed-floor failures",
            "same-denominator collision_lateral_intrusion residual rows must be reduced or classified before any broader claim",
        ),
        (
            "m3108-requirement-0002",
            "offtrack_boundary_recovery_guard",
            "p0",
            "axis:offtrack_boundary_recovery",
            axis_counts.get("offtrack_boundary_recovery", 0),
            "M3105 leaves residual offtrack_boundary_recovery failures including both collision and off_track terminations",
            "next repair route must separate boundary recovery steering/stability pressure from obstacle collision pressure",
            "offtrack_boundary_recovery collision/offtrack rows must remain separately measured",
        ),
        (
            "m3108-requirement-0003",
            "speed_floor_preservation",
            "p0",
            "termination:speed_too_low",
            speed_count,
            "M3105 preserves 0 speed_too_low rows after M3095 and removes the M3100 speed-floor regression",
            "next repair route must preserve the speed-floor gain as a hard guard",
            "speed_too_low count must remain 0 on the same denominator before any repair-success interpretation",
        ),
        (
            "m3108-requirement-0004",
            "residual_collision_reduction",
            "p0",
            "termination:obstacle_collision",
            collision_count,
            "5 residual obstacle_collision rows remain",
            "next repair route must target collision count directly rather than optimizing aggregate clearance alone",
            "obstacle_collision count is separately audited against M3105/M3095 baseline",
        ),
        (
            "m3108-requirement-0005",
            "residual_offtrack_recovery",
            "p0",
            "termination:off_track",
            offtrack_count,
            "2 residual off_track rows remain",
            "next repair route must preserve boundary recovery and stability metrics separately from collision avoidance",
            "off_track count, lateral_rmse, sideslip, and recovery-window fields remain explicit",
        ),
        (
            "m3108-requirement-0006",
            "deployable_actor_boundary",
            "p0",
            "contract:obs72_action3",
            len(residual_rows),
            "the final driver objective requires direct [steer throttle brake] from actor-visible obs72",
            "next repair route must use no hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor inputs",
            "contract guards must pass before repair materialization or measurement",
        ),
        (
            "m3108-requirement-0007",
            "claim_boundary_audit",
            "p0",
            "claim:repair_success_forbidden",
            len(residual_rows),
            "M3108 is no-new-execution decomposition only",
            "M3109 must audit decomposition artifacts before any new repair or measurement route",
            "M3109 result audit exists and rejects validation/performance/repair-success claims",
        ),
    ]
    return [
        {
            "requirement_id": requirement_id,
            "requirement_family": family,
            "priority": priority,
            "affected_group": group,
            "row_count": row_count,
            "trigger_evidence": trigger,
            "requirement": requirement,
            "measurable_next_gate": gate,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3108_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for requirement_id, family, priority, group, row_count, trigger, requirement, gate in specs
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("residual_failure_rows", "materialization", True, "residual_failure_rows.csv"),
        ("residual_axis_summary_rows", "materialization", True, "residual_axis_summary_rows.csv"),
        ("residual_comparison_rows", "materialization", True, "residual_comparison_rows.csv"),
        ("residual_repair_requirement_rows", "materialization", True, "residual_repair_requirement_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3109 audit manifest"),
    ]
    blocked = [
        ("new_execution", "execution", "future separately registered measurement route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit after measurement"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action repair forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3108-{claim_id}",
            "claim_family": family,
            "allowed_in_m3108": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3108-{claim_id}",
            "claim_family": family,
            "allowed_in_m3108": False,
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
        "priority": 31040,
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
        "hypothesis": "A bounded result audit can accept or reject the M3108 residual collision/offtrack decomposition artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3107_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "residual_failure_rows.csv"),
                str(output_dir / "residual_axis_summary_rows.csv"),
                str(output_dir / "residual_comparison_rows.csv"),
                str(output_dir / "residual_repair_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit residual collision/offtrack decomposition before repair routing"],
            "derived_from": [MILESTONE_ID, M3107_ID, M3106_ID, M3105_ID],
            "blocked_by": [
                "M3108 decomposition artifacts require audit before repair materialization or measurement",
                "M3108 is no-new-execution decomposition and cannot support repair-success claims",
            ],
            "supersedes": ["direct repair materialization without auditing residual decomposition"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3109 must audit M3108 summary residual failure comparison axis requirement claim and gate artifacts",
            "M3109 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3109 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3109 must select exactly one repair materialization artifact-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3108 decomposition into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_collision_offtrack_decomposition",
            "evidence_axis": "residual_collision_offtrack_decomposition_result_audit",
            "evidence_increment": "audits residual hard-safety decomposition artifacts before selecting a repair route",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3108 artifacts are missing or gate matrix fails",
                "stop if row preservation or actor contracts were violated",
                "route to repair only if M3108 is complete and claim-safe",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to repair materialization if decomposition is complete and claim-safe",
                "route to synthesis or stop if no deployable repair requirement remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3108 completes residual collision/offtrack decomposition materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3108 residual collision/offtrack decomposition artifacts",
            "admission_evidence": ["M3108 summary gate matrix residual failure comparison axis requirement and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3109 status queue scoreboard research log and review",
                "one follow-up manifest only if M3109 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3109 accepts or rejects M3108 as complete and claim-safe",
                "next repair materialization, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3109 audits engineering decomposition artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3109; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3108 residual decomposition artifacts only.",
            "negative_result_policy": "Preserve residual hard-safety decomposition evidence and route to engineering repair or stop rather than self-ID.",
            "allowed_claims": [
                "M3108 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new residual decomposition evidence before repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3109 prepares engineering repair route decision",
            "must_synthesize_if": [
                "M3109 cannot accept M3108 as complete and claim-safe",
                "M3109 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result or self-ID evidence",
                "M3109 cannot select exactly one repair materialization synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3109 audits M3108 artifact row counts gates actor contract and claim boundaries",
            "M3109 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3109 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3109 hides M3108 failures or missing artifacts",
            "M3109 treats M3108 decomposition as validation repair-success or performance verdict",
            "M3109 changes actor input or action contract",
            "M3109 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3109 audits M3108 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_residual_collision_offtrack_decomposition_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3108-{gate_id}",
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


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    episode_rows: list[dict[str, str]],
    residual_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    summary = source["m3105_summary"]
    residual_axes = {str(row.get("axis_id", "")) for row in residual_rows}
    baseline_counts = Counter(str(row.get("baseline_id", "")) for row in comparison_rows)
    synthesis_text = str(source.get("m3107_synthesis_text", ""))
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3107_route_marker", "lineage", "pivot_to_m3108_residual_collision_offtrack_failure_decomposition" in synthesis_text, "route marker", "present", "lineage_invalid"),
        gate("m3106_audit_present", "lineage", bool(source.get("m3106_audit_text", "")), "audit text", "present", "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(summary.get("status_pass")), summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass")), summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_full_denominator", "denominator", len(episode_rows) == EXPECTED_FULL_ROWS, len(episode_rows), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("residual_failure_rows", "metric", len(residual_rows) == EXPECTED_RESIDUAL_ROWS, len(residual_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("residual_collision_rows", "metric", sum(1 for row in residual_rows if _bool(row.get("collision"))) == EXPECTED_COLLISION_ROWS, sum(1 for row in residual_rows if _bool(row.get("collision"))), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("residual_offtrack_rows", "metric", sum(1 for row in residual_rows if _bool(row.get("offtrack"))) == EXPECTED_OFFTRACK_ROWS, sum(1 for row in residual_rows if _bool(row.get("offtrack"))), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("speed_floor_preserved", "metric", sum(1 for row in residual_rows if _bool(row.get("speed_too_low"))) == EXPECTED_SPEED_TOO_LOW_ROWS, sum(1 for row in residual_rows if _bool(row.get("speed_too_low"))), EXPECTED_SPEED_TOO_LOW_ROWS, "behavior_regression"),
        gate("residual_axes_expected", "metric", residual_axes == EXPECTED_RESIDUAL_AXES, sorted(residual_axes), sorted(EXPECTED_RESIDUAL_AXES), "metric_artifact"),
        gate("residual_comparison_rows", "comparison", len(comparison_rows) == EXPECTED_RESIDUAL_ROWS * len(EXPECTED_BASELINES), len(comparison_rows), EXPECTED_RESIDUAL_ROWS * len(EXPECTED_BASELINES), "metric_artifact"),
        gate("baseline_counts", "comparison", all(baseline_counts.get(item, 0) == EXPECTED_RESIDUAL_ROWS for item in EXPECTED_BASELINES), dict(sorted(baseline_counts.items())), "7 rows per baseline", "metric_artifact"),
        gate("axis_summary_rows", "metric", bool(axis_rows), len(axis_rows), ">0", "metric_artifact"),
        gate("repair_requirement_rows", "metric", len(repair_rows) >= 7, len(repair_rows), ">=7", "metric_artifact"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in source.get("m3105_contract_guard_rows", [])), "all", "pass", "contract_violation"),
        gate("source_claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in source.get("m3105_claim_boundary_rows", [])), "all", "pass", "contract_violation"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(summary.get("runtime_base_policy_required")), summary.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("no_new_execution", "execution", True, "no reset step rollout replay fitting training validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3108 Residual Collision/Offtrack Failure Decomposition Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source denominator rows: {summary['source_measurement_row_count']}",
            f"- residual failure rows: {summary['residual_failure_row_count']}",
            f"- residual collision rows: {summary['residual_collision_count']}",
            f"- residual offtrack rows: {summary['residual_offtrack_count']}",
            f"- residual speed-too-low rows: {summary['residual_speed_too_low_count']}",
            f"- residual axes: {', '.join(summary['residual_axes'])}",
            f"- residual comparison rows: {summary['residual_comparison_row_count']}",
            f"- repair requirement rows: {summary['residual_repair_requirement_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3108 materializes row-preserving residual failure decomposition artifacts from M3105. It does not run a reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.",
            "",
            "Residual hard-safety pressure:",
            "",
            "```text",
            f"collision_lateral_intrusion rows: {summary['collision_lateral_intrusion_residual_count']}",
            f"offtrack_boundary_recovery rows: {summary['offtrack_boundary_recovery_residual_count']}",
            f"obstacle_collision rows: {summary['residual_collision_count']}",
            f"off_track rows: {summary['residual_offtrack_count']}",
            f"speed_too_low rows: {summary['residual_speed_too_low_count']}",
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


def run_materialization(
    *,
    m3107_synthesis: Path,
    m3106_audit: Path,
    m3105_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3107_synthesis=m3107_synthesis, m3106_audit=m3106_audit, m3105_dir=m3105_dir)
    episode_rows = source["m3105_episode_rows"]
    residual_rows = residual_failure_rows(episode_rows, source["m3105_comparison_rows"])
    comparison = residual_comparison_rows(residual_rows, source["m3105_comparison_rows"])
    axis_rows = residual_axis_summary_rows(residual_rows)
    repair_rows = build_repair_requirement_rows(residual_rows, axis_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["residual_failure_rows"], residual_rows, RESIDUAL_FAILURE_FIELDNAMES),
        (paths["residual_axis_summary_rows"], axis_rows, AXIS_SUMMARY_FIELDNAMES),
        (paths["residual_comparison_rows"], comparison, COMPARISON_FIELDNAMES),
        (paths["residual_repair_requirement_rows"], repair_rows, REPAIR_REQUIREMENT_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        episode_rows=episode_rows,
        residual_rows=residual_rows,
        comparison_rows=comparison,
        axis_rows=axis_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    axis_counter = Counter(str(row.get("axis_id", "")) for row in residual_rows)
    status_pass = gate_matrix_pass and present
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight_pass"
            if status_pass
            else "active_safety_driver_residual_collision_offtrack_failure_decomposition_materialization_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_measurement_row_count": len(episode_rows),
        "residual_failure_row_count": len(residual_rows),
        "residual_collision_count": sum(1 for row in residual_rows if _bool(row.get("collision"))),
        "residual_offtrack_count": sum(1 for row in residual_rows if _bool(row.get("offtrack"))),
        "residual_speed_too_low_count": sum(1 for row in residual_rows if _bool(row.get("speed_too_low"))),
        "residual_axes": sorted(axis_counter),
        "collision_lateral_intrusion_residual_count": axis_counter.get("collision_lateral_intrusion", 0),
        "offtrack_boundary_recovery_residual_count": axis_counter.get("offtrack_boundary_recovery", 0),
        "residual_comparison_row_count": len(comparison),
        "residual_axis_summary_row_count": len(axis_rows),
        "residual_repair_requirement_row_count": len(repair_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "runtime_driver_id": POLICY_ID,
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
        "driver_performance_claim_made": False,
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
        "decision": "active_safety_driver_residual_collision_offtrack_decomposition_route_to_m3109_result_audit",
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
    parser.add_argument("--m3107-synthesis", type=Path, default=DEFAULT_M3107_SYNTHESIS)
    parser.add_argument("--m3106-audit", type=Path, default=DEFAULT_M3106_AUDIT)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3107_synthesis=args.m3107_synthesis,
        m3106_audit=args.m3106_audit,
        m3105_dir=args.m3105_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"residual_failure_rows={summary['residual_failure_row_count']}")
    print(f"residual_collision_count={summary['residual_collision_count']}")
    print(f"residual_offtrack_count={summary['residual_offtrack_count']}")
    print(f"residual_speed_too_low_count={summary['residual_speed_too_low_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
