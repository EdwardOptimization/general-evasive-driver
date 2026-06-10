"""Materialize M3166 residual hard-safety source-localization diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3166-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3167-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-result-audit"
)
M3165_ID = (
    "m3165-engineering-controller-active-safety-driver-residual-hard-safety-"
    "failure-source-branch-result-audit"
)
M3164_ID = (
    "m3164-engineering-controller-active-safety-driver-residual-hard-safety-"
    "failure-source-branch-materialization-preflight"
)
M3115_ID = "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-influence-trace-materialization-preflight"
M3147_ID = (
    "m3147-engineering-controller-active-safety-driver-residual-trajectory-"
    "timing-speed-envelope-action-delta-coverage-diagnostic-materialization-preflight"
)

DEFAULT_M3165_AUDIT = Path(f"docs/{M3165_ID}.md")
DEFAULT_M3164_DIR = Path(
    "runs/m3164_engineering_controller_active_safety_driver_residual_hard_safety_"
    "failure_source_branch_materialization_preflight"
)
DEFAULT_M3115_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_influence_"
    "trace_materialization_preflight"
)
DEFAULT_M3147_DIR = Path(
    "runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_"
    "envelope_action_delta_coverage_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3166_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localization_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_M3115_STEP_ROWS = 256
EXPECTED_M3147_STEP_ROWS = 256
EXPECTED_M3115_ACTION_INFLUENCE_ROWS = 7
EXPECTED_M3147_COVERAGE_ROWS = 7

CLAIM_SCOPE = (
    "M3166 Active Safety Driver residual hard-safety source-localization diagnostic materialization only; "
    "M3165 audit, M3164 branch-pack rows, M3115 residual step/action influence traces, and M3147 "
    "action-delta coverage traces may be joined into row-preserving source-localization diagnostic, "
    "repair-admission guard, claim-boundary, gate, doc, and M3167 audit artifacts. No reset, step, "
    "rollout, replay, policy action, fitting, PPO, training, repair implementation, validation execution, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, driver-performance verdict, "
    "current-sim verdict, repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
)

SOURCE_LOCALIZATION_FIELDNAMES = [
    "source_localization_row_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "blocker_family",
    "failure_source_label",
    "next_evidence_axis",
    "m3115_trace_step_count",
    "m3115_step_trace_count",
    "m3115_primary_diagnostic_label",
    "m3115_hard_safety_signal_present",
    "m3115_max_obstacle_urgency_actor_visible",
    "m3115_step_of_max_obstacle_urgency",
    "m3115_first_obstacle_urgency_ge_0_5_step",
    "m3115_max_edge_urgency_actor_visible",
    "m3115_step_of_max_edge_urgency",
    "m3115_first_edge_urgency_ge_0_9_step",
    "m3115_terminal_min_clearance_margin_m",
    "m3115_min_clearance_margin_m_min",
    "m3115_first_negative_clearance_step",
    "m3115_high_sideslip_fraction",
    "m3115_final_10_mean_abs_steer",
    "m3115_final_10_mean_brake_physical",
    "m3115_action_saturation_fraction",
    "m3147_delta_step_trace_count",
    "m3147_overlay_active_fraction",
    "m3147_max_delta_abs",
    "m3147_candidate_saturation_fraction",
    "m3147_final_10_mean_delta_l1",
    "m3147_final_10_mean_delta_brake",
    "m3147_coverage_diagnostic_label",
    "source_localization_label",
    "repair_admission_label",
    "actor_contract",
    "repair_success_claim_made",
    "claim_boundary",
]
REPAIR_ADMISSION_FIELDNAMES = [
    "repair_admission_row_id",
    "route_name",
    "route_role",
    "source_localization_row_count",
    "residual_blocker_families",
    "required_before_repair",
    "admission_decision",
    "blocked_route",
    "evidence_basis",
    "actor_contract",
    "repair_success_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3166",
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


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _maybe_step(value: int | None) -> int | str:
    return "" if value is None else value


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_localization_rows": output_dir / "source_localization_rows.csv",
        "repair_admission_rows": output_dir / "repair_admission_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3165_audit: Path, m3164_dir: Path, m3115_dir: Path, m3147_dir: Path) -> dict[str, Any]:
    paths = {
        "m3165_audit": m3165_audit,
        "m3164_summary": m3164_dir / "summary.json",
        "m3164_failure_source_rows": m3164_dir / "failure_source_rows.csv",
        "m3164_branch_route_rows": m3164_dir / "branch_route_rows.csv",
        "m3164_gate_rows": m3164_dir / "gate_matrix.csv",
        "m3115_summary": m3115_dir / "summary.json",
        "m3115_residual_action_influence_rows": m3115_dir / "residual_action_influence_rows.csv",
        "m3115_residual_step_trace_rows": m3115_dir / "residual_step_trace_rows.csv",
        "m3115_gate_rows": m3115_dir / "gate_matrix.csv",
        "m3147_summary": m3147_dir / "summary.json",
        "m3147_action_delta_coverage_rows": m3147_dir / "action_delta_coverage_rows.csv",
        "m3147_action_delta_step_trace_rows": m3147_dir / "action_delta_step_trace_rows.csv",
        "m3147_gate_rows": m3147_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3165_audit_text": paths["m3165_audit"].read_text(encoding="utf-8") if exists["m3165_audit"] else "",
        "m3164_summary": read_json(paths["m3164_summary"]) if exists["m3164_summary"] else {},
        "m3164_failure_source_rows": read_csv_rows(paths["m3164_failure_source_rows"]),
        "m3164_branch_route_rows": read_csv_rows(paths["m3164_branch_route_rows"]),
        "m3164_gate_rows": read_csv_rows(paths["m3164_gate_rows"]),
        "m3115_summary": read_json(paths["m3115_summary"]) if exists["m3115_summary"] else {},
        "m3115_residual_action_influence_rows": read_csv_rows(paths["m3115_residual_action_influence_rows"]),
        "m3115_residual_step_trace_rows": read_csv_rows(paths["m3115_residual_step_trace_rows"]),
        "m3115_gate_rows": read_csv_rows(paths["m3115_gate_rows"]),
        "m3147_summary": read_json(paths["m3147_summary"]) if exists["m3147_summary"] else {},
        "m3147_action_delta_coverage_rows": read_csv_rows(paths["m3147_action_delta_coverage_rows"]),
        "m3147_action_delta_step_trace_rows": read_csv_rows(paths["m3147_action_delta_step_trace_rows"]),
        "m3147_gate_rows": read_csv_rows(paths["m3147_gate_rows"]),
    }


def _one_by_measurement(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("source_measurement_episode_id", "")): row for row in rows}


def _group_by_measurement(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_measurement_episode_id", ""))].append(row)
    return grouped


def _first_step(rows: list[dict[str, str]], predicate: Any) -> int | None:
    steps: list[int] = []
    for row in rows:
        if predicate(row):
            steps.append(_int(row.get("step_index"), 0))
    return min(steps) if steps else None


def _m3115_step_aggregate(rows: list[dict[str, str]]) -> dict[str, Any]:
    first_obstacle = _first_step(rows, lambda row: _float(row.get("obstacle_urgency_actor_visible")) >= 0.5)
    first_edge = _first_step(rows, lambda row: _float(row.get("edge_urgency_actor_visible")) >= 0.9)
    first_negative_clearance = _first_step(rows, lambda row: _float(row.get("min_clearance_margin_m_after_step"), 1.0) < 0.0)
    return {
        "m3115_step_trace_count": len(rows),
        "m3115_first_obstacle_urgency_ge_0_5_step": _maybe_step(first_obstacle),
        "m3115_first_edge_urgency_ge_0_9_step": _maybe_step(first_edge),
        "m3115_first_negative_clearance_step": _maybe_step(first_negative_clearance),
    }


def _m3147_step_aggregate(rows: list[dict[str, str]]) -> dict[str, Any]:
    count = len(rows)
    active_count = sum(1 for row in rows if _bool(row.get("overlay_active", False)))
    saturated_count = sum(1 for row in rows if _bool(row.get("candidate_action_saturated", False)))
    return {
        "m3147_delta_step_trace_count": count,
        "m3147_overlay_active_fraction_step_derived": active_count / count if count else 0.0,
        "m3147_candidate_saturation_fraction_step_derived": saturated_count / count if count else 0.0,
        "m3147_max_delta_abs_step_derived": max((_float(row.get("delta_max_abs")) for row in rows), default=0.0),
    }


def _source_localization_label(blocker_family: str, influence: Mapping[str, str], coverage: Mapping[str, str]) -> str:
    max_obstacle = _float(influence.get("max_obstacle_urgency_actor_visible"))
    max_edge = _float(influence.get("max_edge_urgency_actor_visible"))
    min_clearance = _float(influence.get("min_clearance_margin_m_min"), _float(influence.get("terminal_min_clearance_margin_m")))
    high_sideslip = _float(influence.get("high_sideslip_fraction"))
    coverage_label = str(coverage.get("coverage_diagnostic_label", ""))
    if blocker_family == "collision" and min_clearance < 0.0 and max_obstacle >= 0.5:
        if coverage_label == "collision_terminal_window_delta_low":
            return "collision_clearance_unresolved_with_late_or_low_terminal_action_delta"
        return "collision_clearance_unresolved_despite_visible_obstacle_and_action_response"
    if blocker_family == "offtrack" and (max_edge >= 0.9 or high_sideslip >= 0.2):
        return "boundary_recovery_unresolved_despite_visible_edge_and_stability_stress"
    if blocker_family == "collision":
        return "collision_source_localization_requires_observation_timeline_diagnostic"
    if blocker_family == "offtrack":
        return "offtrack_source_localization_requires_boundary_recovery_diagnostic"
    return "residual_hard_safety_source_localization_requires_follow_up"


def _repair_admission_label(blocker_family: str) -> str:
    if blocker_family == "collision":
        return "diagnostic_admitted_repair_not_admitted_collision_observation_timeline"
    if blocker_family == "offtrack":
        return "diagnostic_admitted_repair_not_admitted_boundary_recovery_stability"
    return "diagnostic_admitted_repair_not_admitted_residual_hard_safety"


def source_localization_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    influence_by_measurement = _one_by_measurement(list(source.get("m3115_residual_action_influence_rows", [])))
    coverage_by_measurement = _one_by_measurement(list(source.get("m3147_action_delta_coverage_rows", [])))
    m3115_steps_by_measurement = _group_by_measurement(list(source.get("m3115_residual_step_trace_rows", [])))
    m3147_steps_by_measurement = _group_by_measurement(list(source.get("m3147_action_delta_step_trace_rows", [])))
    rows: list[dict[str, Any]] = []
    for index, failure in enumerate(source.get("m3164_failure_source_rows", []), start=1):
        measurement_id = str(failure.get("source_measurement_episode_id", ""))
        blocker_family = str(failure.get("blocker_family", ""))
        influence = influence_by_measurement.get(measurement_id, {})
        coverage = coverage_by_measurement.get(measurement_id, {})
        m3115_steps = _m3115_step_aggregate(m3115_steps_by_measurement.get(measurement_id, []))
        m3147_steps = _m3147_step_aggregate(m3147_steps_by_measurement.get(measurement_id, []))
        rows.append(
            {
                "source_localization_row_id": f"m3166-source-localization-{index:04d}",
                "source_measurement_episode_id": measurement_id,
                "fresh_panel_row_id": failure.get("fresh_panel_row_id", ""),
                "axis_id": failure.get("axis_id", ""),
                "binding_role": failure.get("binding_role", ""),
                "blocker_family": blocker_family,
                "failure_source_label": failure.get("failure_source_label", ""),
                "next_evidence_axis": failure.get("next_evidence_axis", ""),
                "m3115_trace_step_count": _int(influence.get("trace_step_count")),
                "m3115_step_trace_count": m3115_steps["m3115_step_trace_count"],
                "m3115_primary_diagnostic_label": influence.get("primary_diagnostic_label", ""),
                "m3115_hard_safety_signal_present": _bool(influence.get("hard_safety_signal_present")),
                "m3115_max_obstacle_urgency_actor_visible": _float(influence.get("max_obstacle_urgency_actor_visible")),
                "m3115_step_of_max_obstacle_urgency": _maybe_step(_int(influence.get("step_of_max_obstacle_urgency")) if influence.get("step_of_max_obstacle_urgency", "") != "" else None),
                "m3115_first_obstacle_urgency_ge_0_5_step": m3115_steps["m3115_first_obstacle_urgency_ge_0_5_step"],
                "m3115_max_edge_urgency_actor_visible": _float(influence.get("max_edge_urgency_actor_visible")),
                "m3115_step_of_max_edge_urgency": _maybe_step(_int(influence.get("step_of_max_edge_urgency")) if influence.get("step_of_max_edge_urgency", "") != "" else None),
                "m3115_first_edge_urgency_ge_0_9_step": m3115_steps["m3115_first_edge_urgency_ge_0_9_step"],
                "m3115_terminal_min_clearance_margin_m": _float(influence.get("terminal_min_clearance_margin_m")),
                "m3115_min_clearance_margin_m_min": _float(influence.get("min_clearance_margin_m_min")),
                "m3115_first_negative_clearance_step": m3115_steps["m3115_first_negative_clearance_step"],
                "m3115_high_sideslip_fraction": _float(influence.get("high_sideslip_fraction")),
                "m3115_final_10_mean_abs_steer": _float(influence.get("final_10_mean_abs_steer")),
                "m3115_final_10_mean_brake_physical": _float(influence.get("final_10_mean_brake_physical")),
                "m3115_action_saturation_fraction": _float(influence.get("action_saturation_fraction")),
                "m3147_delta_step_trace_count": m3147_steps["m3147_delta_step_trace_count"],
                "m3147_overlay_active_fraction": _float(
                    coverage.get("overlay_active_fraction"),
                    m3147_steps["m3147_overlay_active_fraction_step_derived"],
                ),
                "m3147_max_delta_abs": _float(coverage.get("max_delta_abs"), m3147_steps["m3147_max_delta_abs_step_derived"]),
                "m3147_candidate_saturation_fraction": _float(
                    coverage.get("candidate_saturation_fraction"),
                    m3147_steps["m3147_candidate_saturation_fraction_step_derived"],
                ),
                "m3147_final_10_mean_delta_l1": _float(coverage.get("final_10_mean_delta_l1")),
                "m3147_final_10_mean_delta_brake": _float(coverage.get("final_10_mean_delta_brake")),
                "m3147_coverage_diagnostic_label": coverage.get("coverage_diagnostic_label", ""),
                "source_localization_label": _source_localization_label(blocker_family, influence, coverage),
                "repair_admission_label": _repair_admission_label(blocker_family),
                "actor_contract": "actor_visible_obs72_to_direct_action3",
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def repair_admission_rows(localization_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("blocker_family", "")) for row in localization_rows)
    return [
        {
            "repair_admission_row_id": "m3166-repair-admission-0001",
            "route_name": "collision_observation_timeline_source_localization",
            "route_role": "diagnostic_admission_before_repair",
            "source_localization_row_count": counts.get("collision", 0),
            "residual_blocker_families": "collision",
            "required_before_repair": True,
            "admission_decision": "diagnostic_admitted_repair_not_admitted",
            "blocked_route": "",
            "evidence_basis": "collision rows preserve negative-clearance terminal blockers with M3115 visible obstacle/action response and M3147 action-delta coverage",
            "actor_contract": "actor_visible_obs72_to_direct_action3",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_admission_row_id": "m3166-repair-admission-0002",
            "route_name": "boundary_recovery_stability_source_localization",
            "route_role": "diagnostic_admission_before_repair",
            "source_localization_row_count": counts.get("offtrack", 0),
            "residual_blocker_families": "offtrack",
            "required_before_repair": True,
            "admission_decision": "diagnostic_admitted_repair_not_admitted",
            "blocked_route": "",
            "evidence_basis": "offtrack rows preserve boundary-recovery instability with M3115 edge urgency/sideslip evidence and M3147 action-delta coverage",
            "actor_contract": "actor_visible_obs72_to_direct_action3",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_admission_row_id": "m3166-repair-admission-0003",
            "route_name": "local_action_delta_tuning",
            "route_role": "blocked_route",
            "source_localization_row_count": len(localization_rows),
            "residual_blocker_families": "collision|offtrack",
            "required_before_repair": False,
            "admission_decision": "blocked_until_source_localization_changes_repair_hypothesis",
            "blocked_route": "unbounded_local_action_delta_tuning",
            "evidence_basis": "M3153 reports 0 of 21 action-channel-sensitive comparisons and M3147 shows action deltas are present but outcomes remain unresolved",
            "actor_contract": "actor_visible_obs72_to_direct_action3",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("source_localization_rows", "diagnostic_artifact", True, "source_localization_rows.csv"),
        ("repair_admission_guard_rows", "diagnostic_artifact", True, "repair_admission_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3167 audit manifest"),
    ]
    blocked = [
        ("environment_reset", "execution", "future pre-registered execution route"),
        ("environment_step", "execution", "future pre-registered execution route"),
        ("policy_action", "execution", "future pre-registered execution route"),
        ("policy_rollout", "execution", "future pre-registered execution route"),
        ("replay_run", "execution", "future pre-registered replay route"),
        ("driver_mutation", "repair", "future pre-registered repair materialization"),
        ("repair_admitted", "repair", "future audit after source-localization result"),
        ("validation_result", "validation", "future validation execution plus audit"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("checkpoint_ranking", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("high_fidelity_validation", "validation", "future Route C HF validation"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "public deployable reflex forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3166-{claim_id}",
            "claim_family": family,
            "allowed_in_m3166": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3166-{claim_id}",
            "claim_family": family,
            "allowed_in_m3166": False,
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
        "baseline_checkpoints": [str(output_dir / "summary.json"), str(doc_path)],
        "commands": [
            {
                "command": "true",
                "name": "active_safety_driver_residual_hard_safety_source_localization_diagnostic_result_audit_doc",
            }
        ],
        "decision_rule": "Pass only if M3167 audits M3166 source-localization diagnostics and selects one repair-admission synthesis artifact-repair or stop route without overclaiming.",
        "failure_criteria": [
            "M3167 hides missing M3166 rows or failed gates",
            "M3167 treats M3166 diagnostics as repair success or performance verdict",
            "M3167 leaves the next route ambiguous",
        ],
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
        "forbidden_shortcuts": [
            "do not rerun tune rank promote validate or mutate checkpoints",
            "do not convert M3166 source-localization rows into validation performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "gate_tier": "process",
        "hypothesis": "A bounded result audit can accept or reject M3166 residual hard-safety source-localization diagnostics before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "id": NEXT_ID,
        "lineage": {
            "blocked_by": [
                "M3166 source-localization diagnostics require audit before repair admission or synthesis",
                "M3166 is diagnostic materialization not repair evidence",
            ],
            "derived_from": [MILESTONE_ID, M3165_ID, M3164_ID, M3115_ID, M3147_ID],
            "invalidates": [],
            "parent_checkpoint": [str(doc_path)],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "source_localization_rows.csv"),
                str(output_dir / "repair_admission_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_objective": ["audit residual hard-safety source-localization diagnostics"],
            "supersedes": ["direct repair admission from M3165 without M3166 source-localization audit"],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "evidence_expansion": "audits source-localization diagnostics before repair admission",
            "local_search_risk": "medium",
            "must_synthesize_if": [
                "M3167 cannot accept M3166 as complete and claim-safe",
                "M3167 cannot select one repair-admission diagnostic continuation artifact-repair synthesis or stop route",
            ],
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3167 audits engineering source-localization evidence",
            "process_overhead": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
        },
        "next_blocker": NEXT_ID,
        "priority": 31670,
        "private_holdout_policy": "not_used",
        "promotion_decision": "not_applicable",
        "public_gates": [
            "M3167 must audit M3166 summary source-localization repair-admission claim and gate artifacts",
            "M3167 must preserve obs72/action3 direct [steer throttle brake] contract and residual blocker disclosure",
            "M3167 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3167 must select exactly one next route or stop state",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "self_id_evidence_discipline": {
            "allowed_claims": [
                "M3166 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3167 audits engineering diagnostics and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3167; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "negative_result_policy": "Preserve residual blocker evidence and route to engineering repair-admission or synthesis rather than returning self-ID to the mainline objective.",
            "temporal_evidence_window": "M3166 source-localization artifacts only.",
        },
        "status": "pending",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3167 audits M3166 source-localization diagnostic artifacts and claim boundaries",
            "M3167 selects exactly one next route or stop state",
        ],
        "training_stage": {
            "admission_evidence": ["M3166 summary source-localization repair-admission claim and gate artifacts"],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3167 status queue scoreboard research log and review",
                "one follow-up manifest only if M3167 selects exactly one next route",
            ],
            "blocked_shortcuts": [
                "no validation execution ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "next_stage_criteria": [
                "M3167 accepts or rejects M3166 as complete and claim-safe",
                "M3167 selects repair-admission diagnostic continuation artifact-repair synthesis or stop explicitly",
            ],
            "stage": "process",
            "stage_objective": "Audit M3166 residual hard-safety source-localization diagnostics",
        },
        "type": "gate",
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_failure_source_resolution",
            "claim_scope": "Result audit only; no repair validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "evidence_axis": "residual_hard_safety_source_localization_diagnostic_result_audit",
            "evidence_increment": "audits M3166 residual source-localization diagnostics before repair admission",
            "fallback_plan": [
                "route to M3166 artifact repair if diagnostics are incomplete",
                "route to repair-admission planning if M3166 is complete and claim-safe",
                "synthesize if M3167 cannot select one next route",
            ],
            "stop_condition": [
                "stop if M3166 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "stop if next route would require hidden or oracle actor inputs",
            ],
            "synthesis_cadence": 10,
            "synthesis_decision": "not_applicable",
            "synthesis_trigger": "M3166 completes residual hard-safety source-localization diagnostic materialization",
        },
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3166-{gate_id}",
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
    localization_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    m3165_text = str(source.get("m3165_audit_text", ""))
    m3164_summary = source.get("m3164_summary", {})
    m3115_summary = source.get("m3115_summary", {})
    m3147_summary = source.get("m3147_summary", {})
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in localization_rows)
    repair_names = {str(row.get("route_name", "")) for row in repair_rows}
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3165_accepts_m3164_and_routes_m3166", "lineage", "accept_m3164_branch_pack_route_to_m3166_source_localization_diagnostic_materialization" in m3165_text, "M3165 route marker", "present", "lineage_invalid"),
        gate("m3164_status_pass", "lineage", _bool(m3164_summary.get("status_pass", False)), m3164_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3164_gate_matrix_pass", "lineage", _bool(m3164_summary.get("gate_matrix_pass", False)), m3164_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3115_status_pass", "lineage", _bool(m3115_summary.get("status_pass", False)), m3115_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3115_gate_matrix_pass", "lineage", _bool(m3115_summary.get("gate_matrix_pass", False)), m3115_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3147_status_pass", "lineage", _bool(m3147_summary.get("status_pass", False)), m3147_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3147_gate_matrix_pass", "lineage", _bool(m3147_summary.get("gate_matrix_pass", False)), m3147_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3164_failure_source_rows", "known_failures", int(m3164_summary.get("failure_source_row_count", 0)) == EXPECTED_RESIDUAL_ROWS, m3164_summary.get("failure_source_row_count"), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("m3115_step_trace_rows", "trace", int(m3115_summary.get("residual_step_trace_row_count", 0)) == EXPECTED_M3115_STEP_ROWS, m3115_summary.get("residual_step_trace_row_count"), EXPECTED_M3115_STEP_ROWS, "metric_artifact"),
        gate("m3115_action_influence_rows", "trace", int(m3115_summary.get("residual_action_influence_row_count", 0)) == EXPECTED_M3115_ACTION_INFLUENCE_ROWS, m3115_summary.get("residual_action_influence_row_count"), EXPECTED_M3115_ACTION_INFLUENCE_ROWS, "metric_artifact"),
        gate("m3147_step_trace_rows", "trace", int(m3147_summary.get("action_delta_step_trace_row_count", 0)) == EXPECTED_M3147_STEP_ROWS, m3147_summary.get("action_delta_step_trace_row_count"), EXPECTED_M3147_STEP_ROWS, "metric_artifact"),
        gate("m3147_coverage_rows", "trace", int(m3147_summary.get("action_delta_coverage_row_count", 0)) == EXPECTED_M3147_COVERAGE_ROWS, m3147_summary.get("action_delta_coverage_row_count"), EXPECTED_M3147_COVERAGE_ROWS, "metric_artifact"),
        gate("source_localization_rows", "known_failures", len(localization_rows) == EXPECTED_RESIDUAL_ROWS, len(localization_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("collision_rows", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_rows", "known_failures", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("all_rows_join_m3115_steps", "trace_join", all(int(row.get("m3115_step_trace_count", 0)) > 0 for row in localization_rows), "all localization rows", "m3115 step count > 0", "lineage_invalid"),
        gate("all_rows_join_m3147_steps", "trace_join", all(int(row.get("m3147_delta_step_trace_count", 0)) > 0 for row in localization_rows), "all localization rows", "m3147 step count > 0", "lineage_invalid"),
        gate("uses_step_trace_denominators", "trace_join", sum(int(row.get("m3115_step_trace_count", 0)) for row in localization_rows) == EXPECTED_M3115_STEP_ROWS and sum(int(row.get("m3147_delta_step_trace_count", 0)) for row in localization_rows) == EXPECTED_M3147_STEP_ROWS, (sum(int(row.get("m3115_step_trace_count", 0)) for row in localization_rows), sum(int(row.get("m3147_delta_step_trace_count", 0)) for row in localization_rows)), (EXPECTED_M3115_STEP_ROWS, EXPECTED_M3147_STEP_ROWS), "metric_artifact"),
        gate("source_localization_labels_present", "diagnostic", all(str(row.get("source_localization_label", "")) for row in localization_rows), "all rows", "label present", "metric_artifact"),
        gate("repair_diagnostic_admission_present", "route", {"collision_observation_timeline_source_localization", "boundary_recovery_stability_source_localization"}.issubset(repair_names), sorted(repair_names), "diagnostic admission rows present", "objective_overfit"),
        gate("local_action_delta_blocked", "route", any(row.get("route_name") == "local_action_delta_tuning" and not _bool(row.get("required_before_repair", True)) for row in repair_rows), "blocked route row", "present", "objective_overfit"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_repair_success_claim", "claim", not any(_bool(row.get("repair_success_claim_made", False)) for row in localization_rows + repair_rows), "all rows", False, "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3166 Residual Hard-Safety Source-Localization Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source-localization rows: {summary['source_localization_row_count']}",
            f"- repair-admission guard rows: {summary['repair_admission_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- collision blockers: {summary['collision_blocker_count']}",
            f"- offtrack blockers: {summary['offtrack_blocker_count']}",
            f"- M3115 step-trace rows joined: {summary['m3115_joined_step_trace_row_count']}",
            f"- M3147 action-delta step-trace rows joined: {summary['m3147_joined_step_trace_row_count']}",
            "",
            "## Interpretation",
            "",
            "M3166 converts the M3165-selected route into a row-preserving diagnostic pack. Each M3164 residual blocker row is joined to M3115 action-influence and step-trace evidence plus M3147 action-delta coverage and step-trace evidence.",
            "",
            "The resulting diagnostic rows separate collision-clearance localization from boundary-recovery/stability localization while keeping repair not admitted. Local action-delta tuning remains blocked because prior counterfactual replay found 0 of 21 action-channel-sensitive comparisons and M3147 shows action deltas can be present while hard-safety outcomes remain unresolved.",
            "",
            "M3166 does not reset or step the environment, replay rollouts, run a policy action, train, tune, rank, promote, validate, implement repair, select a winner, mutate a checkpoint, or make validation, repair-success, robustness, driver-performance, current-sim, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claims.",
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


def run_source_localization_diagnostic_materialization_preflight(
    *,
    m3165_audit: Path,
    m3164_dir: Path,
    m3115_dir: Path,
    m3147_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3165_audit=m3165_audit, m3164_dir=m3164_dir, m3115_dir=m3115_dir, m3147_dir=m3147_dir)
    localization_rows = source_localization_rows(source)
    repair_rows = repair_admission_rows(localization_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["source_localization_rows"], localization_rows, fieldnames=SOURCE_LOCALIZATION_FIELDNAMES)
    write_csv_rows(paths["repair_admission_rows"], repair_rows, fieldnames=REPAIR_ADMISSION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        localization_rows=localization_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in localization_rows)
    m3115_summary = source.get("m3115_summary", {})
    m3147_summary = source.get("m3147_summary", {})
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_source_localization_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_source_localization_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_localization_row_count": len(localization_rows),
        "repair_admission_row_count": len(repair_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "collision_blocker_count": blocker_counts.get("collision", 0),
        "offtrack_blocker_count": blocker_counts.get("offtrack", 0),
        "m3115_source_step_trace_row_count": int(m3115_summary.get("residual_step_trace_row_count", 0)),
        "m3115_joined_step_trace_row_count": sum(int(row.get("m3115_step_trace_count", 0)) for row in localization_rows),
        "m3115_action_influence_row_count": int(m3115_summary.get("residual_action_influence_row_count", 0)),
        "m3147_source_action_delta_step_trace_row_count": int(m3147_summary.get("action_delta_step_trace_row_count", 0)),
        "m3147_joined_step_trace_row_count": sum(int(row.get("m3147_delta_step_trace_count", 0)) for row in localization_rows),
        "m3147_action_delta_coverage_row_count": int(m3147_summary.get("action_delta_coverage_row_count", 0)),
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
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_source_localization_diagnostic_route_to_m3167_result_audit",
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
            "source_localization_row_count": len(localization_rows),
            "repair_admission_row_count": len(repair_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3165-audit", type=Path, default=DEFAULT_M3165_AUDIT)
    parser.add_argument("--m3164-dir", type=Path, default=DEFAULT_M3164_DIR)
    parser.add_argument("--m3115-dir", type=Path, default=DEFAULT_M3115_DIR)
    parser.add_argument("--m3147-dir", type=Path, default=DEFAULT_M3147_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_source_localization_diagnostic_materialization_preflight(
        m3165_audit=args.m3165_audit,
        m3164_dir=args.m3164_dir,
        m3115_dir=args.m3115_dir,
        m3147_dir=args.m3147_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"source_localization_rows={summary['source_localization_row_count']}")
    print(f"m3115_joined_step_trace_rows={summary['m3115_joined_step_trace_row_count']}")
    print(f"m3147_joined_step_trace_rows={summary['m3147_joined_step_trace_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
