"""Materialize M3123 residual hard-safety action-authority/feasibility diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3123-engineering-controller-active-safety-driver-residual-hard-safety-action-"
    "authority-feasibility-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3124-engineering-controller-active-safety-driver-residual-hard-safety-action-"
    "authority-feasibility-diagnostic-result-audit"
)
M3122_ID = (
    "m3122-engineering-controller-active-safety-driver-residual-trajectory-authority-"
    "stability-recovery-repair-plateau-synthesis"
)
M3120_ID = (
    "m3120-engineering-controller-active-safety-driver-residual-trajectory-authority-"
    "stability-recovery-repair-full-fresh-measurement-preflight"
)
M3115_ID = (
    "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-"
    "influence-trace-materialization-preflight"
)
M3118_ID = (
    "m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-"
    "stability-recovery-repair-materialization-preflight"
)

DEFAULT_M3122_SYNTHESIS = Path(f"docs/{M3122_ID}.md")
DEFAULT_M3120_DIR = Path(
    "runs/m3120_engineering_controller_active_safety_driver_residual_trajectory_authority_"
    "stability_recovery_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3115_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_"
    "influence_trace_materialization_preflight"
)
DEFAULT_M3118_DIR = Path(
    "runs/m3118_engineering_controller_active_safety_driver_residual_trajectory_authority_"
    "stability_recovery_repair_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3123_engineering_controller_active_safety_driver_residual_hard_safety_action_"
    "authority_feasibility_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_BASELINES = ("m3105", "m3095", "m3100", "m3090")
POLICY_ID = "m3123_residual_hard_safety_action_authority_feasibility_diagnostic"

CLAIM_SCOPE = (
    "M3123 Active Safety Driver residual hard-safety action-authority and feasibility "
    "diagnostic materialization only; existing M3120 measurement rows, M3120 same-row "
    "comparison rows, M3115 trace rows, and M3118 rule artifacts may be transformed into "
    "row-preserving diagnostic artifacts, claim, gate, doc, and M3124 audit manifest. No "
    "reset, step, rollout, replay, fitting, PPO, training, repair materialization, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal "
    "driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair materialization, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

RESIDUAL_DIAGNOSTIC_FIELDNAMES = [
    "diagnostic_id",
    "measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "termination_reason",
    "collision",
    "offtrack",
    "speed_too_low",
    "min_clearance_margin",
    "speed_mean",
    "high_sideslip_fraction",
    "lateral_rmse",
    "raw_action_abs_max",
    "final_action_abs_max",
    "same_row_baseline_count",
    "same_row_baselines",
    "plateau_vs_m3105",
    "plateau_vs_m3095",
    "trace_step_count",
    "primary_diagnostic_label",
    "terminal_speed_mps",
    "terminal_beta_abs",
    "terminal_lateral_error_m",
    "terminal_min_clearance_margin_m",
    "final_10_mean_brake_physical",
    "final_10_mean_abs_steer",
    "action_saturation_fraction",
    "max_obstacle_urgency_actor_visible",
    "step_of_max_obstacle_urgency",
    "max_edge_urgency_actor_visible",
    "step_of_max_edge_urgency",
    "terminal_obstacle_x_m_actor_visible",
    "terminal_obstacle_y_m_actor_visible",
    "authority_label",
    "feasibility_label",
    "diagnostic_interpretation",
    "recommended_next_evidence",
    "row_identity_preserved",
    "m3123_no_new_execution",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
REQUIREMENT_FIELDNAMES = [
    "requirement_id",
    "requirement_family",
    "priority",
    "affected_group",
    "row_count",
    "trigger_evidence",
    "requirement",
    "measurable_next_gate",
    "blocked_claims",
    "m3123_no_new_execution",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3123",
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


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success", False))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "residual_action_authority_feasibility_rows": output_dir / "residual_action_authority_feasibility_rows.csv",
        "diagnostic_requirement_rows": output_dir / "diagnostic_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3122_synthesis: Path, m3120_dir: Path, m3115_dir: Path, m3118_dir: Path) -> dict[str, Any]:
    paths = {
        "m3122_synthesis": m3122_synthesis,
        "m3120_summary": m3120_dir / "summary.json",
        "m3120_measurement_rows": m3120_dir / "measurement_episode_rows.csv",
        "m3120_comparison_rows": m3120_dir / "same_row_comparison_rows.csv",
        "m3120_gate_rows": m3120_dir / "gate_matrix.csv",
        "m3115_summary": m3115_dir / "summary.json",
        "m3115_step_trace_rows": m3115_dir / "residual_step_trace_rows.csv",
        "m3115_action_influence_rows": m3115_dir / "residual_action_influence_rows.csv",
        "m3118_summary": m3118_dir / "summary.json",
        "m3118_rule_rows": m3118_dir / "safety_reflex_rule_rows.csv",
        "m3118_gate_rows": m3118_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3122_synthesis_text": paths["m3122_synthesis"].read_text(encoding="utf-8") if exists["m3122_synthesis"] else "",
        "m3120_summary": read_json(paths["m3120_summary"]) if exists["m3120_summary"] else {},
        "m3120_measurement_rows": read_csv_rows(paths["m3120_measurement_rows"]),
        "m3120_comparison_rows": read_csv_rows(paths["m3120_comparison_rows"]),
        "m3120_gate_rows": read_csv_rows(paths["m3120_gate_rows"]),
        "m3115_summary": read_json(paths["m3115_summary"]) if exists["m3115_summary"] else {},
        "m3115_step_trace_rows": read_csv_rows(paths["m3115_step_trace_rows"]),
        "m3115_action_influence_rows": read_csv_rows(paths["m3115_action_influence_rows"]),
        "m3118_summary": read_json(paths["m3118_summary"]) if exists["m3118_summary"] else {},
        "m3118_rule_rows": read_csv_rows(paths["m3118_rule_rows"]),
        "m3118_gate_rows": read_csv_rows(paths["m3118_gate_rows"]),
    }


def _baseline_rows_by_source(comparison_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in comparison_rows:
        grouped.setdefault(str(row.get("source_measurement_episode_id", "")), []).append(row)
    return grouped


def _row_plateau_vs(rows: list[dict[str, str]], baseline_id: str) -> bool:
    selected = [row for row in rows if str(row.get("baseline_id", "")) == baseline_id]
    if not selected:
        return False
    row = selected[0]
    return (
        int(_float(row.get("success_delta"))) == 0
        and int(_float(row.get("collision_delta"))) == 0
        and int(_float(row.get("offtrack_delta"))) == 0
        and int(_float(row.get("speed_too_low_delta"))) == 0
    )


def classify_authority_feasibility(
    episode: Mapping[str, Any],
    influence: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    """Classify one residual row without claiming repair success or feasibility proof."""

    collision = _bool(episode.get("collision", False))
    offtrack = _offtrack(episode)
    raw_abs = _float(episode.get("raw_action_abs_max"))
    final_abs = _float(episode.get("final_action_abs_max"))
    action_saturation = _float(influence.get("action_saturation_fraction"))
    final_brake = _float(influence.get("final_10_mean_brake_physical"))
    final_steer = _float(influence.get("final_10_mean_abs_steer"))
    high_sideslip = _float(episode.get("high_sideslip_fraction"))
    max_edge = _float(influence.get("max_edge_urgency_actor_visible"))
    max_obstacle = _float(influence.get("max_obstacle_urgency_actor_visible"))
    terminal_speed = _float(influence.get("terminal_speed_mps"))
    clearance_margin = _float(episode.get("min_clearance_margin"))

    saturated = raw_abs >= 0.98 or final_abs >= 0.98 or action_saturation >= 0.10
    strong_response = final_brake >= 0.55 or final_steer >= 0.75
    high_speed = terminal_speed >= 14.0

    if collision and saturated and strong_response:
        authority = "collision_action_authority_saturated_clearance_unresolved"
        feasibility = "clearance_or_timing_feasibility_unresolved_under_direct_action"
        interpretation = (
            "collision persists despite high direct-action authority and strong final-window response; "
            "next evidence should separate action authority from geometric clearance feasibility"
        )
        next_evidence = "counterfactual authority envelope or trajectory-feasibility diagnostic before another repair"
    elif collision and high_speed and max_obstacle >= 0.5:
        authority = "collision_high_speed_obstacle_timing_authority_unresolved"
        feasibility = "brake_timing_feasibility_unresolved"
        interpretation = "collision persists at high terminal speed with visible obstacle urgency"
        next_evidence = "row-preserving brake/steer timing envelope diagnostic"
    elif offtrack and (high_sideslip >= 0.25 or max_edge >= 0.85):
        authority = "offtrack_stability_edge_authority_limited"
        feasibility = "boundary_recovery_feasibility_unresolved_under_sideslip"
        interpretation = (
            "offtrack persists under high edge urgency or sideslip; next evidence should separate steering "
            "authority from stability recovery feasibility"
        )
        next_evidence = "stability recovery authority envelope or trajectory-level controller diagnostic"
    elif clearance_margin < 0.0:
        authority = "negative_clearance_authority_unresolved"
        feasibility = "clearance_feasibility_unresolved"
        interpretation = "negative clearance remains after direct-rule repair"
        next_evidence = "clearance feasibility diagnostic"
    else:
        authority = "residual_authority_unclassified_requires_audit"
        feasibility = "feasibility_unclassified_requires_audit"
        interpretation = "residual failure could not be classified from current row-level diagnostics"
        next_evidence = "artifact audit or richer diagnostic before repair"
    return authority, feasibility, interpretation, next_evidence


def residual_action_authority_feasibility_rows(
    measurement_rows: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
    influence_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    comparison_by_source = _baseline_rows_by_source(comparison_rows)
    influence_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in influence_rows}
    residual_rows = [row for row in measurement_rows if not _success(row)]
    output: list[dict[str, Any]] = []
    for index, episode in enumerate(residual_rows, start=1):
        source_id = str(episode.get("source_measurement_episode_id", ""))
        influence = influence_by_source.get(source_id, {})
        baseline_rows = comparison_by_source.get(source_id, [])
        authority, feasibility, interpretation, next_evidence = classify_authority_feasibility(episode, influence)
        baseline_ids = sorted(str(row.get("baseline_id", "")) for row in baseline_rows)
        output.append(
            {
                "diagnostic_id": f"m3123-action-authority-feasibility-{index:04d}",
                "measurement_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "termination_reason": episode.get("termination_reason", ""),
                "collision": _bool(episode.get("collision", False)),
                "offtrack": _offtrack(episode),
                "speed_too_low": _speed_too_low(episode),
                "min_clearance_margin": episode.get("min_clearance_margin", ""),
                "speed_mean": episode.get("speed_mean", ""),
                "high_sideslip_fraction": episode.get("high_sideslip_fraction", ""),
                "lateral_rmse": episode.get("lateral_rmse", ""),
                "raw_action_abs_max": episode.get("raw_action_abs_max", ""),
                "final_action_abs_max": episode.get("final_action_abs_max", ""),
                "same_row_baseline_count": len(baseline_rows),
                "same_row_baselines": ";".join(baseline_ids),
                "plateau_vs_m3105": _row_plateau_vs(baseline_rows, "m3105"),
                "plateau_vs_m3095": _row_plateau_vs(baseline_rows, "m3095"),
                "trace_step_count": influence.get("trace_step_count", ""),
                "primary_diagnostic_label": influence.get("primary_diagnostic_label", ""),
                "terminal_speed_mps": influence.get("terminal_speed_mps", ""),
                "terminal_beta_abs": influence.get("terminal_beta_abs", ""),
                "terminal_lateral_error_m": influence.get("terminal_lateral_error_m", ""),
                "terminal_min_clearance_margin_m": influence.get("terminal_min_clearance_margin_m", ""),
                "final_10_mean_brake_physical": influence.get("final_10_mean_brake_physical", ""),
                "final_10_mean_abs_steer": influence.get("final_10_mean_abs_steer", ""),
                "action_saturation_fraction": influence.get("action_saturation_fraction", ""),
                "max_obstacle_urgency_actor_visible": influence.get("max_obstacle_urgency_actor_visible", ""),
                "step_of_max_obstacle_urgency": influence.get("step_of_max_obstacle_urgency", ""),
                "max_edge_urgency_actor_visible": influence.get("max_edge_urgency_actor_visible", ""),
                "step_of_max_edge_urgency": influence.get("step_of_max_edge_urgency", ""),
                "terminal_obstacle_x_m_actor_visible": influence.get("terminal_obstacle_x_m_actor_visible", ""),
                "terminal_obstacle_y_m_actor_visible": influence.get("terminal_obstacle_y_m_actor_visible", ""),
                "authority_label": authority,
                "feasibility_label": feasibility,
                "diagnostic_interpretation": interpretation,
                "recommended_next_evidence": next_evidence,
                "row_identity_preserved": bool(source_id and source_id in influence_by_source),
                "m3123_no_new_execution": True,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def diagnostic_requirement_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = Counter(str(row.get("authority_label", "")) for row in rows)
    collision_count = sum(1 for row in rows if _bool(row.get("collision")))
    offtrack_count = sum(1 for row in rows if _bool(row.get("offtrack")))
    saturated_count = sum(1 for row in rows if "saturated" in str(row.get("authority_label", "")))
    plateau_count = sum(1 for row in rows if _bool(row.get("plateau_vs_m3105")) and _bool(row.get("plateau_vs_m3095")))
    specs = [
        (
            "collision_action_authority_envelope",
            "p0",
            "termination:obstacle_collision",
            collision_count,
            f"{collision_count} residual collision rows remain after M3120 plateau",
            "separate insufficient action authority from geometric clearance infeasibility before another repair",
            "row-preserving counterfactual authority or trajectory feasibility artifact must exist before repair",
        ),
        (
            "offtrack_stability_authority_envelope",
            "p0",
            "termination:off_track",
            offtrack_count,
            f"{offtrack_count} residual offtrack rows remain after M3120 plateau",
            "separate steering authority from stability recovery feasibility under edge urgency and sideslip",
            "stability authority envelope or trajectory-level diagnostic must exist before repair",
        ),
        (
            "direct_rule_plateau_guard",
            "p0",
            "baseline:M3105_M3095",
            plateau_count,
            "M3120 has zero aggregate delta against both M3105 and M3095 on residual hard-safety counts",
            "forbid another blind direct-rule gain edit unless a new evidence axis is materialized",
            "M3124 must audit whether this diagnostic justifies stop pivot or one next route",
        ),
        (
            "saturation_vs_feasibility_split",
            "p0",
            "authority:saturated",
            saturated_count,
            f"{saturated_count} residual rows show saturated or near-saturated action authority",
            "diagnose whether the remaining failure is controllability/action authority or trajectory feasibility",
            "future repair must cite action-authority/feasibility rows rather than only aggregate counts",
        ),
        (
            "speed_floor_deceleration_tradeoff",
            "p1",
            "contract:speed_floor",
            sum(1 for row in rows if _float(row.get("speed_mean")) >= 14.0),
            "M3120 preserves zero speed-too-low but collision rows remain high-speed",
            "evaluate whether speed-floor preservation blocks needed deceleration without reopening speed-too-low failures",
            "next route must keep speed_too_low explicit and separately audited",
        ),
        (
            "deployable_actor_boundary",
            "p0",
            "contract:obs72_action3",
            len(rows),
            "final driver must remain direct [steer throttle brake] from actor-visible obs72",
            "preserve actor boundary and forbid hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor inputs",
            "all future diagnostics and repairs must keep actor contract gates",
        ),
        (
            "claim_boundary_audit",
            "p0",
            "claim:diagnostic_only",
            len(rows),
            "M3123 is no-new-execution diagnostic materialization",
            "M3124 must audit M3123 before any repair success or route verdict",
            "M3124 audit artifact must exist before interpretation",
        ),
    ]
    return [
        {
            "requirement_id": f"m3123-requirement-{index:04d}",
            "requirement_family": family,
            "priority": priority,
            "affected_group": group,
            "row_count": row_count,
            "trigger_evidence": trigger,
            "requirement": requirement,
            "measurable_next_gate": gate,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3123_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, group, row_count, trigger, requirement, gate) in enumerate(specs, start=1)
        if family in labels or True
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("residual_action_authority_feasibility_rows", "diagnostic", True, "residual_action_authority_feasibility_rows.csv"),
        ("diagnostic_requirement_rows", "diagnostic_requirement", True, "diagnostic_requirement_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3124 audit manifest"),
    ]
    blocked = [
        ("new_execution", "execution", "future separately registered measurement route"),
        ("repair_materialization", "repair", "future separately registered repair route"),
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
        ("runtime_base_policy_dependency", "contract", "direct-action driver forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3123-{claim_id}",
            "claim_family": family,
            "allowed_in_m3123": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3123-{claim_id}",
            "claim_family": family,
            "allowed_in_m3123": False,
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
        "priority": 31190,
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
        "hypothesis": "A bounded result audit can accept or reject the M3123 action-authority and feasibility diagnostic artifacts before any repair validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3122_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "residual_action_authority_feasibility_rows.csv"),
                str(output_dir / "diagnostic_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit residual hard-safety action-authority feasibility diagnostics before repair routing"],
            "derived_from": [MILESTONE_ID, M3122_ID, M3120_ID, M3115_ID, M3118_ID],
            "blocked_by": [
                "M3123 diagnostic artifacts require audit before repair materialization or measurement",
                "M3123 is no-new-execution diagnostic materialization and cannot support repair-success claims",
            ],
            "supersedes": ["direct repair materialization after M3120 plateau without action-authority feasibility audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3124 must audit M3123 summary diagnostic requirement claim and gate artifacts",
            "M3124 must preserve obs72/action3 direct [steer throttle brake] actor contract and runtime_base_policy_required false",
            "M3124 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3124 must select exactly one stop pivot diagnostic architecture experiment repair route or synthesis route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3123 diagnostic labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_action_authority_feasibility_diagnosis",
            "evidence_axis": "residual_hard_safety_action_authority_feasibility_diagnostic_result_audit",
            "evidence_increment": "audits a no-new-execution action-authority feasibility diagnostic artifact after the M3120 plateau",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3123 artifacts are missing or gate matrix fails",
                "stop if actor or row identity contracts were violated",
                "route to synthesis before any repair interpretation if diagnostic labels are ambiguous",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to synthesis or stop if no deployable next route remains",
                "route to one constrained next diagnostic or architecture experiment only after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3123 completes action-authority feasibility diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3123 residual hard-safety action-authority feasibility diagnostic artifacts",
            "admission_evidence": ["M3123 summary gate matrix diagnostic requirement and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3124 status queue scoreboard research log and review",
                "one follow-up manifest only if M3124 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3124 accepts or rejects M3123 as complete and claim-safe",
                "next stop pivot diagnostic architecture experiment repair or synthesis route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3124 audits engineering diagnostic artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3124; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3123 diagnostic artifacts only.",
            "negative_result_policy": "Preserve diagnostic evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3123 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the action-authority feasibility diagnostic evidence before repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3124 prepares engineering route decision",
            "must_synthesize_if": [
                "M3124 cannot accept M3123 as complete and claim-safe",
                "M3124 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result or self-ID evidence",
                "M3124 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3124 audits M3123 artifact row counts gates actor contract and claim boundaries",
            "M3124 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3124 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3124 hides M3123 failures or missing artifacts",
            "M3124 treats M3123 diagnostics as validation repair-success or performance verdict",
            "M3124 changes actor input or action contract",
            "M3124 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3124 audits M3123 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_residual_action_authority_feasibility_diagnostic_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3123-{gate_id}",
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
    diagnostic_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    summary = source["m3120_summary"]
    labels = Counter(str(row.get("authority_label", "")) for row in diagnostic_rows)
    baseline_counts = Counter()
    for row in diagnostic_rows:
        for baseline in str(row.get("same_row_baselines", "")).split(";"):
            if baseline:
                baseline_counts[baseline] += 1
    synthesis_text = str(source.get("m3122_synthesis_text", ""))
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3122_route_marker", "lineage", "pivot_to_m3123_residual_hard_safety_action_authority_feasibility_diagnostic_materialization" in synthesis_text, "route marker", "present", "lineage_invalid"),
        gate("m3120_status_pass", "lineage", _bool(summary.get("status_pass")), summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3120_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass")), summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3120_full_denominator", "denominator", int(summary.get("measurement_episode_row_count", 0)) == EXPECTED_FULL_ROWS, summary.get("measurement_episode_row_count"), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("m3115_trace_rows_present", "lineage", len(source.get("m3115_step_trace_rows", [])) > 0, len(source.get("m3115_step_trace_rows", [])), ">0", "lineage_invalid"),
        gate("m3115_influence_rows", "lineage", len(source.get("m3115_action_influence_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3115_action_influence_rows", [])), EXPECTED_RESIDUAL_ROWS, "lineage_invalid"),
        gate("m3118_rule_rows_present", "lineage", len(source.get("m3118_rule_rows", [])) >= 6, len(source.get("m3118_rule_rows", [])), ">=6", "lineage_invalid"),
        gate("diagnostic_rows", "metric", len(diagnostic_rows) == EXPECTED_RESIDUAL_ROWS, len(diagnostic_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("collision_rows", "metric", sum(1 for row in diagnostic_rows if _bool(row.get("collision"))) == EXPECTED_COLLISION_ROWS, sum(1 for row in diagnostic_rows if _bool(row.get("collision"))), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_rows", "metric", sum(1 for row in diagnostic_rows if _bool(row.get("offtrack"))) == EXPECTED_OFFTRACK_ROWS, sum(1 for row in diagnostic_rows if _bool(row.get("offtrack"))), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("speed_too_low_rows", "metric", sum(1 for row in diagnostic_rows if _bool(row.get("speed_too_low"))) == EXPECTED_SPEED_TOO_LOW_ROWS, sum(1 for row in diagnostic_rows if _bool(row.get("speed_too_low"))), EXPECTED_SPEED_TOO_LOW_ROWS, "behavior_regression"),
        gate("row_identity_preserved", "metric", all(_bool(row.get("row_identity_preserved")) for row in diagnostic_rows), "all", "preserved", "metric_artifact"),
        gate("baseline_counts", "comparison", all(baseline_counts.get(baseline, 0) == EXPECTED_RESIDUAL_ROWS for baseline in EXPECTED_BASELINES), dict(sorted(baseline_counts.items())), "7 per baseline", "metric_artifact"),
        gate("plateau_vs_m3105_m3095", "comparison", all(_bool(row.get("plateau_vs_m3105")) and _bool(row.get("plateau_vs_m3095")) for row in diagnostic_rows), "all residual rows", "plateau", "metric_artifact"),
        gate("authority_labels_present", "metric", bool(labels) and "residual_authority_unclassified_requires_audit" not in labels, dict(sorted(labels.items())), "classified", "metric_artifact"),
        gate("diagnostic_requirement_rows", "metric", len(requirement_rows) >= 7, len(requirement_rows), ">=7", "metric_artifact"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(summary.get("runtime_base_policy_required")), summary.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("no_new_execution", "execution", True, "no reset step rollout replay fitting training validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    labels = summary["authority_label_counts"]
    return "\n".join(
        [
            "# M3123 Residual Hard-Safety Action-Authority Feasibility Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source full-fresh rows: {summary['source_measurement_row_count']}",
            f"- diagnostic residual rows: {summary['diagnostic_row_count']}",
            f"- residual collision rows: {summary['residual_collision_count']}",
            f"- residual offtrack rows: {summary['residual_offtrack_count']}",
            f"- residual speed-too-low rows: {summary['residual_speed_too_low_count']}",
            f"- diagnostic requirement rows: {summary['diagnostic_requirement_row_count']}",
            f"- authority label counts: {labels}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3123 materializes row-preserving action-authority and feasibility diagnostics for the seven M3120 residual hard-safety failures. It is no-new-execution evidence reanalysis only. It does not run a reset, step, rollout, replay, fitting, PPO, training, repair materialization, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.",
            "",
            "Residual hard-safety diagnostic pressure:",
            "",
            "```text",
            f"collision rows: {summary['residual_collision_count']}",
            f"offtrack rows: {summary['residual_offtrack_count']}",
            f"saturated/authority-limited rows: {summary['authority_limited_row_count']}",
            f"plateau rows vs M3105/M3095: {summary['plateau_vs_m3105_m3095_count']}",
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
    m3122_synthesis: Path,
    m3120_dir: Path,
    m3115_dir: Path,
    m3118_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3122_synthesis=m3122_synthesis, m3120_dir=m3120_dir, m3115_dir=m3115_dir, m3118_dir=m3118_dir)
    diagnostic_rows = residual_action_authority_feasibility_rows(
        source["m3120_measurement_rows"],
        source["m3120_comparison_rows"],
        source["m3115_action_influence_rows"],
    )
    requirement_rows = diagnostic_requirement_rows(diagnostic_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["residual_action_authority_feasibility_rows"], diagnostic_rows, RESIDUAL_DIAGNOSTIC_FIELDNAMES),
        (paths["diagnostic_requirement_rows"], requirement_rows, REQUIREMENT_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        diagnostic_rows=diagnostic_rows,
        requirement_rows=requirement_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    label_counts = Counter(str(row.get("authority_label", "")) for row in diagnostic_rows)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_action_authority_feasibility_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_action_authority_feasibility_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_measurement_row_count": len(source["m3120_measurement_rows"]),
        "source_same_row_comparison_row_count": len(source["m3120_comparison_rows"]),
        "diagnostic_row_count": len(diagnostic_rows),
        "residual_collision_count": sum(1 for row in diagnostic_rows if _bool(row.get("collision"))),
        "residual_offtrack_count": sum(1 for row in diagnostic_rows if _bool(row.get("offtrack"))),
        "residual_speed_too_low_count": sum(1 for row in diagnostic_rows if _bool(row.get("speed_too_low"))),
        "authority_label_counts": dict(sorted(label_counts.items())),
        "authority_limited_row_count": sum(
            1
            for row in diagnostic_rows
            if "authority" in str(row.get("authority_label", "")) and "unclassified" not in str(row.get("authority_label", ""))
        ),
        "plateau_vs_m3105_m3095_count": sum(
            1 for row in diagnostic_rows if _bool(row.get("plateau_vs_m3105")) and _bool(row.get("plateau_vs_m3095"))
        ),
        "diagnostic_requirement_row_count": len(requirement_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "runtime_driver_id": POLICY_ID,
        "candidate_output_semantics": "direct_action_clipped",
        "candidate_output_components": ["steer", "throttle", "brake"],
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
        "decision": "active_safety_driver_residual_hard_safety_action_authority_feasibility_diagnostic_route_to_m3124_result_audit",
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
    parser.add_argument("--m3122-synthesis", type=Path, default=DEFAULT_M3122_SYNTHESIS)
    parser.add_argument("--m3120-dir", type=Path, default=DEFAULT_M3120_DIR)
    parser.add_argument("--m3115-dir", type=Path, default=DEFAULT_M3115_DIR)
    parser.add_argument("--m3118-dir", type=Path, default=DEFAULT_M3118_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3122_synthesis=args.m3122_synthesis,
        m3120_dir=args.m3120_dir,
        m3115_dir=args.m3115_dir,
        m3118_dir=args.m3118_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"diagnostic_rows={summary['diagnostic_row_count']}")
    print(f"residual_collision_count={summary['residual_collision_count']}")
    print(f"residual_offtrack_count={summary['residual_offtrack_count']}")
    print(f"residual_speed_too_low_count={summary['residual_speed_too_low_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
