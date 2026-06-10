"""Materialize M3125 residual hard-safety counterfactual action-authority envelope diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3125-engineering-controller-active-safety-driver-residual-hard-safety-counterfactual-"
    "action-authority-envelope-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3126-engineering-controller-active-safety-driver-residual-hard-safety-counterfactual-"
    "action-authority-envelope-diagnostic-result-audit"
)
M3124_ID = (
    "m3124-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-"
    "feasibility-diagnostic-result-audit"
)
M3123_ID = (
    "m3123-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-"
    "feasibility-diagnostic-materialization-preflight"
)
M3115_ID = (
    "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-influence-"
    "trace-materialization-preflight"
)

DEFAULT_M3124_AUDIT = Path(f"docs/{M3124_ID}.md")
DEFAULT_M3123_DIR = Path(
    "runs/m3123_engineering_controller_active_safety_driver_residual_hard_safety_action_"
    "authority_feasibility_diagnostic_materialization_preflight"
)
DEFAULT_M3115_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_"
    "influence_trace_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3125_engineering_controller_active_safety_driver_residual_hard_safety_counterfactual_"
    "action_authority_envelope_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
POLICY_ID = "m3125_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic"

CLAIM_SCOPE = (
    "M3125 Active Safety Driver residual hard-safety counterfactual action-authority "
    "envelope diagnostic materialization only; existing M3124 audit text, M3123 row-level "
    "diagnostics, and M3115 trace/action-influence rows may be transformed into row-preserving "
    "envelope, requirement, claim, gate, doc, and M3126 audit manifest artifacts. No reset, "
    "step, rollout, replay, fitting, PPO, training, repair materialization, validation, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, driver-performance verdict, "
    "current-sim verdict, repair success, robustness-result, high-fidelity validation, paper "
    "evidence, finite-window-vs-GRU evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair materialization, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, infeasibility proof, feasibility proof, or level3 self-identification"
)

ENVELOPE_FIELDNAMES = [
    "envelope_id",
    "diagnostic_id",
    "trace_episode_id",
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
    "authority_label",
    "feasibility_label",
    "primary_diagnostic_label",
    "trace_step_count",
    "terminal_speed_mps",
    "terminal_beta_abs",
    "terminal_lateral_error_m",
    "terminal_min_clearance_margin_m",
    "high_sideslip_fraction",
    "final_10_mean_throttle_action",
    "final_10_mean_brake_physical",
    "final_10_brake_margin_to_full",
    "final_10_mean_abs_steer",
    "final_10_steer_margin_to_saturation",
    "negative_throttle_margin_to_full_decel",
    "action_saturation_fraction",
    "max_obstacle_urgency_actor_visible",
    "max_edge_urgency_actor_visible",
    "terminal_obstacle_x_m_actor_visible",
    "terminal_obstacle_y_m_actor_visible",
    "counterfactual_brake_target",
    "counterfactual_brake_delta_to_full",
    "counterfactual_steer_target",
    "counterfactual_steer_delta_to_saturation",
    "throttle_deceleration_tradeoff_label",
    "envelope_status",
    "route_recommendation",
    "diagnostic_interpretation",
    "row_identity_preserved",
    "m3125_no_new_execution",
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
    "m3125_no_new_execution",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3125",
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


def _margin_to_upper(value: Any, upper: float = 1.0) -> float:
    return max(0.0, upper - _float(value))


def _mean(values: list[float]) -> float | str:
    return sum(values) / len(values) if values else ""


def _min(values: list[float]) -> float | str:
    return min(values) if values else ""


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "counterfactual_action_authority_envelope_rows": output_dir / "counterfactual_action_authority_envelope_rows.csv",
        "envelope_requirement_rows": output_dir / "envelope_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3124_audit: Path, m3123_dir: Path, m3115_dir: Path) -> dict[str, Any]:
    paths = {
        "m3124_audit": m3124_audit,
        "m3123_summary": m3123_dir / "summary.json",
        "m3123_envelope_source_rows": m3123_dir / "residual_action_authority_feasibility_rows.csv",
        "m3123_requirement_rows": m3123_dir / "diagnostic_requirement_rows.csv",
        "m3123_gate_rows": m3123_dir / "gate_matrix.csv",
        "m3115_summary": m3115_dir / "summary.json",
        "m3115_action_influence_rows": m3115_dir / "residual_action_influence_rows.csv",
        "m3115_step_trace_rows": m3115_dir / "residual_step_trace_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3124_audit_text": paths["m3124_audit"].read_text(encoding="utf-8") if exists["m3124_audit"] else "",
        "m3123_summary": read_json(paths["m3123_summary"]) if exists["m3123_summary"] else {},
        "m3123_envelope_source_rows": read_csv_rows(paths["m3123_envelope_source_rows"]),
        "m3123_requirement_rows": read_csv_rows(paths["m3123_requirement_rows"]),
        "m3123_gate_rows": read_csv_rows(paths["m3123_gate_rows"]),
        "m3115_summary": read_json(paths["m3115_summary"]) if exists["m3115_summary"] else {},
        "m3115_action_influence_rows": read_csv_rows(paths["m3115_action_influence_rows"]),
        "m3115_step_trace_rows": read_csv_rows(paths["m3115_step_trace_rows"]),
    }


def _step_rows_by_source(step_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in step_rows:
        grouped.setdefault(str(row.get("source_measurement_episode_id", "")), []).append(row)
    return grouped


def _final_window_stats(step_rows: list[dict[str, str]], window: int = 10) -> dict[str, Any]:
    rows = sorted(step_rows, key=lambda row: int(_float(row.get("step_index"))))
    final_rows = rows[-window:]
    throttle_values = [_float(row.get("throttle_action")) for row in final_rows]
    brake_values = [_float(row.get("brake_physical")) for row in final_rows]
    steer_values = [abs(_float(row.get("steer_action"))) for row in final_rows]
    return {
        "final_10_min_throttle_action": _min(throttle_values),
        "final_10_max_brake_physical": max(brake_values) if brake_values else "",
        "final_10_max_abs_steer": max(steer_values) if steer_values else "",
    }


def classify_throttle_tradeoff(*, final_throttle: float, final_brake: float, speed_too_low: bool) -> str:
    if speed_too_low:
        return "speed_floor_already_failed_no_deceleration_tradeoff_claim"
    if final_throttle <= -0.65 and final_brake >= 0.80:
        return "negative_throttle_and_physical_brake_near_full_under_speed_floor_preservation"
    if final_throttle <= -0.40 and final_brake >= 0.55:
        return "strong_deceleration_action_with_speed_floor_preserved"
    if final_throttle > -0.20 and final_brake < 0.55:
        return "additional_deceleration_authority_nominally_available_timing_unresolved"
    return "mixed_deceleration_margin_requires_audit"


def classify_envelope(row: Mapping[str, Any], influence: Mapping[str, Any]) -> tuple[str, str, str]:
    collision = _bool(row.get("collision"))
    offtrack = _bool(row.get("offtrack"))
    final_brake = _float(row.get("final_10_mean_brake_physical", influence.get("final_10_mean_brake_physical")))
    final_steer = _float(row.get("final_10_mean_abs_steer", influence.get("final_10_mean_abs_steer")))
    final_throttle = _float(influence.get("final_10_mean_throttle_action"))
    action_saturation = _float(row.get("action_saturation_fraction", influence.get("action_saturation_fraction")))
    terminal_clearance = _float(row.get("terminal_min_clearance_margin_m"))
    high_sideslip = _float(row.get("high_sideslip_fraction"))
    max_edge = _float(row.get("max_edge_urgency_actor_visible", influence.get("max_edge_urgency_actor_visible")))
    speed_too_low = _bool(row.get("speed_too_low"))
    tradeoff = classify_throttle_tradeoff(
        final_throttle=final_throttle,
        final_brake=final_brake,
        speed_too_low=speed_too_low,
    )

    if collision and (
        (final_brake >= 0.85 and final_steer >= 0.90)
        or (action_saturation >= 0.30 and final_steer >= 0.90)
        or (terminal_clearance < 0.0 and final_brake >= 0.90)
    ):
        status = "joint_brake_steer_envelope_exhausted_clearance_unresolved"
        route = "trajectory_level_controller_architecture_or_feasibility_diagnostic_before_more_direct_gain"
        interpretation = (
            "collision row is already using near-full brake or steer authority; M3125 can only route "
            "to trajectory-level/feasibility evidence, not repair success"
        )
    elif collision and final_brake >= 0.55 and final_steer >= 0.70 and terminal_clearance < 0.0:
        status = "joint_brake_steer_envelope_near_exhausted_clearance_unresolved"
        route = "trajectory_level_controller_architecture_or_feasibility_diagnostic_before_more_direct_gain"
        interpretation = (
            "collision row has strong final-window brake/steer response with negative clearance; "
            "another direct gain edit needs a stronger trajectory-timing hypothesis first"
        )
    elif offtrack and (final_steer >= 0.95 or (action_saturation >= 0.15 and max_edge >= 0.95)):
        status = "stability_steer_envelope_near_exhausted"
        route = "trajectory_level_stability_recovery_architecture_diagnostic_before_more_direct_gain"
        interpretation = (
            "offtrack row is near steer saturation under high edge urgency; direct steer gain evidence is nearly exhausted"
        )
    elif offtrack and final_steer >= 0.70 and (high_sideslip >= 0.25 or max_edge >= 0.85):
        status = "stability_recovery_envelope_timing_limited"
        route = "stability_recovery_timing_or_trajectory_level_controller_diagnostic"
        interpretation = (
            "offtrack row still has some physical margin but sustained sideslip/edge pressure makes timing and recovery "
            "dynamics the next evidence axis"
        )
    elif tradeoff == "additional_deceleration_authority_nominally_available_timing_unresolved":
        status = "direct_action_margin_available_but_timing_unresolved"
        route = "row_preserving_timing_counterfactual_before_direct_gain"
        interpretation = "residual row has nominal action margin; M3125 does not prove that using it would repair the row"
    else:
        status = "authority_envelope_mixed_requires_result_audit"
        route = "m3126_result_audit_before_any_repair_route"
        interpretation = "current envelope fields do not support a stronger route than audit"
    return status, route, interpretation


def counterfactual_action_authority_envelope_rows(
    m3123_rows: list[dict[str, str]],
    influence_rows: list[dict[str, str]],
    step_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    influence_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in influence_rows}
    step_by_source = _step_rows_by_source(step_rows)
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(m3123_rows, start=1):
        source_id = str(row.get("source_measurement_episode_id", ""))
        influence = influence_by_source.get(source_id, {})
        final_stats = _final_window_stats(step_by_source.get(source_id, []))
        final_brake = _float(row.get("final_10_mean_brake_physical", influence.get("final_10_mean_brake_physical")))
        final_steer = _float(row.get("final_10_mean_abs_steer", influence.get("final_10_mean_abs_steer")))
        final_throttle = _float(influence.get("final_10_mean_throttle_action"))
        brake_margin = _margin_to_upper(final_brake)
        steer_margin = _margin_to_upper(final_steer)
        negative_throttle_margin = max(0.0, final_throttle + 1.0)
        status, route, interpretation = classify_envelope(row, influence)
        tradeoff = classify_throttle_tradeoff(
            final_throttle=final_throttle,
            final_brake=final_brake,
            speed_too_low=_bool(row.get("speed_too_low")),
        )
        rows.append(
            {
                "envelope_id": f"m3125-counterfactual-action-authority-envelope-{index:04d}",
                "diagnostic_id": row.get("diagnostic_id", ""),
                "trace_episode_id": influence.get("trace_episode_id", ""),
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "termination_reason": row.get("termination_reason", ""),
                "collision": _bool(row.get("collision")),
                "offtrack": _bool(row.get("offtrack")),
                "speed_too_low": _bool(row.get("speed_too_low")),
                "authority_label": row.get("authority_label", ""),
                "feasibility_label": row.get("feasibility_label", ""),
                "primary_diagnostic_label": row.get("primary_diagnostic_label", influence.get("primary_diagnostic_label", "")),
                "trace_step_count": row.get("trace_step_count", influence.get("trace_step_count", "")),
                "terminal_speed_mps": row.get("terminal_speed_mps", influence.get("terminal_speed_mps", "")),
                "terminal_beta_abs": row.get("terminal_beta_abs", influence.get("terminal_beta_abs", "")),
                "terminal_lateral_error_m": row.get("terminal_lateral_error_m", influence.get("terminal_lateral_error_m", "")),
                "terminal_min_clearance_margin_m": row.get(
                    "terminal_min_clearance_margin_m",
                    influence.get("terminal_min_clearance_margin_m", ""),
                ),
                "high_sideslip_fraction": row.get("high_sideslip_fraction", ""),
                "final_10_mean_throttle_action": influence.get("final_10_mean_throttle_action", ""),
                "final_10_mean_brake_physical": final_brake,
                "final_10_brake_margin_to_full": brake_margin,
                "final_10_mean_abs_steer": final_steer,
                "final_10_steer_margin_to_saturation": steer_margin,
                "negative_throttle_margin_to_full_decel": negative_throttle_margin,
                "action_saturation_fraction": row.get(
                    "action_saturation_fraction",
                    influence.get("action_saturation_fraction", ""),
                ),
                "max_obstacle_urgency_actor_visible": row.get(
                    "max_obstacle_urgency_actor_visible",
                    influence.get("max_obstacle_urgency_actor_visible", ""),
                ),
                "max_edge_urgency_actor_visible": row.get(
                    "max_edge_urgency_actor_visible",
                    influence.get("max_edge_urgency_actor_visible", ""),
                ),
                "terminal_obstacle_x_m_actor_visible": row.get(
                    "terminal_obstacle_x_m_actor_visible",
                    influence.get("terminal_obstacle_x_m_actor_visible", ""),
                ),
                "terminal_obstacle_y_m_actor_visible": row.get(
                    "terminal_obstacle_y_m_actor_visible",
                    influence.get("terminal_obstacle_y_m_actor_visible", ""),
                ),
                "counterfactual_brake_target": 1.0,
                "counterfactual_brake_delta_to_full": brake_margin,
                "counterfactual_steer_target": 1.0,
                "counterfactual_steer_delta_to_saturation": steer_margin,
                "throttle_deceleration_tradeoff_label": tradeoff,
                "envelope_status": status,
                "route_recommendation": route,
                "diagnostic_interpretation": interpretation,
                "row_identity_preserved": bool(source_id and source_id in influence_by_source and source_id in step_by_source),
                "m3125_no_new_execution": True,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
                **final_stats,
            }
        )
    return rows


def envelope_requirement_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status_counts = Counter(str(row.get("envelope_status", "")) for row in rows)
    route_counts = Counter(str(row.get("route_recommendation", "")) for row in rows)
    collision_count = sum(1 for row in rows if _bool(row.get("collision")))
    offtrack_count = sum(1 for row in rows if _bool(row.get("offtrack")))
    near_exhausted_count = sum(1 for row in rows if "exhausted" in str(row.get("envelope_status", "")))
    timing_limited_count = sum(1 for row in rows if "timing" in str(row.get("envelope_status", "")))
    specs = [
        (
            "counterfactual_brake_steer_margin_audit",
            "p0",
            "all_residual_hard_safety_rows",
            len(rows),
            f"envelope statuses {dict(sorted(status_counts.items()))}",
            "audit brake/steer envelope margins before treating another direct-gain edit as justified",
            "M3126 must accept or reject envelope rows before any repair materialization",
        ),
        (
            "collision_clearance_envelope_split",
            "p0",
            "termination:obstacle_collision",
            collision_count,
            f"{collision_count} collision rows retain negative or unresolved terminal clearance",
            "separate direct action saturation from trajectory geometry/timing feasibility",
            "future route must cite collision envelope rows and cannot claim feasibility or repair success",
        ),
        (
            "offtrack_stability_envelope_split",
            "p0",
            "termination:off_track",
            offtrack_count,
            f"{offtrack_count} offtrack rows retain stability/edge recovery pressure",
            "separate steer saturation from stability recovery timing",
            "future route must cite stability envelope rows and cannot claim performance verdict",
        ),
        (
            "near_exhausted_authority_guard",
            "p0",
            "envelope:near_or_full_exhaustion",
            near_exhausted_count,
            f"{near_exhausted_count} residual rows are near or fully exhausted by envelope labels",
            "forbid another blind local gain edit when direct-action authority is already near practical bounds",
            "M3126 must decide stop synthesis architecture diagnostic or one constrained repair route",
        ),
        (
            "timing_limited_margin_guard",
            "p1",
            "envelope:timing_limited_or_mixed",
            timing_limited_count,
            f"{timing_limited_count} residual rows retain timing-limited or mixed envelope labels",
            "preserve a timing/trajectory evidence route instead of claiming counterfactual action repair",
            "future action changes must be audited as hypotheses, not as proven repairs",
        ),
        (
            "speed_floor_deceleration_tradeoff_guard",
            "p1",
            "contract:speed_floor",
            sum(1 for row in rows if "speed_floor" in str(row.get("throttle_deceleration_tradeoff_label", ""))),
            "M3125 derives throttle/brake tradeoff labels while preserving zero speed-too-low interpretation",
            "keep speed-floor preservation explicit before increasing braking/deceleration",
            "next route must track speed-too-low separately from collision/offtrack",
        ),
        (
            "claim_boundary_audit",
            "p0",
            "claim:diagnostic_only",
            len(rows),
            "M3125 is no-new-execution envelope diagnostic materialization only",
            "M3126 must audit M3125 before any repair validation or verdict",
            "M3126 audit artifact must exist before interpretation",
        ),
        (
            "route_consolidation_guard",
            "p0",
            "route_recommendation",
            len(route_counts),
            f"route recommendations {dict(sorted(route_counts.items()))}",
            "consolidate route decision in M3126 rather than continuing local search from row labels alone",
            "M3126 must choose exactly one next route or synthesis/stop state",
        ),
    ]
    return [
        {
            "requirement_id": f"m3125-requirement-{index:04d}",
            "requirement_family": family,
            "priority": priority,
            "affected_group": group,
            "row_count": row_count,
            "trigger_evidence": trigger,
            "requirement": requirement,
            "measurable_next_gate": gate,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3125_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, group, row_count, trigger, requirement, gate) in enumerate(specs, start=1)
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("counterfactual_action_authority_envelope_rows", "diagnostic", True, "counterfactual_action_authority_envelope_rows.csv"),
        ("envelope_requirement_rows", "diagnostic_requirement", True, "envelope_requirement_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3126 audit manifest"),
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
        ("feasibility_or_infeasibility_proof", "verdict", "future formal feasibility/validation route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action driver forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3125-{claim_id}",
            "claim_family": family,
            "allowed_in_m3125": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3125-{claim_id}",
            "claim_family": family,
            "allowed_in_m3125": False,
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
        "priority": 31210,
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
        "hypothesis": "A bounded result audit can accept or reject the M3125 counterfactual action-authority envelope diagnostic artifacts before any repair validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3124_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "counterfactual_action_authority_envelope_rows.csv"),
                str(output_dir / "envelope_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit residual hard-safety counterfactual action-authority envelope diagnostics before repair routing"],
            "derived_from": [MILESTONE_ID, M3124_ID, M3123_ID, M3115_ID],
            "blocked_by": [
                "M3125 envelope diagnostic artifacts require audit before repair materialization or measurement",
                "M3125 is no-new-execution diagnostic materialization and cannot support repair-success claims",
            ],
            "supersedes": ["direct repair materialization after M3124 audit without counterfactual envelope audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3126 must audit M3125 summary envelope requirement claim and gate artifacts",
            "M3126 must preserve obs72/action3 direct [steer throttle brake] actor contract and runtime_base_policy_required false",
            "M3126 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof infeasibility-proof and self-ID claims",
            "M3126 must select exactly one stop synthesis architecture diagnostic repair route or artifact-repair route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3125 envelope labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof infeasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_action_authority_feasibility_diagnosis",
            "evidence_axis": "residual_counterfactual_action_authority_envelope_diagnostic_result_audit",
            "evidence_increment": "audits a no-new-execution counterfactual action-authority envelope diagnostic artifact after M3124",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3125 artifacts are missing or gate matrix fails",
                "stop if actor or row identity contracts were violated",
                "route to synthesis before repair if envelope labels imply direct-action authority is exhausted",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to synthesis or stop if no deployable next route remains",
                "route to one constrained architecture diagnostic or repair route only after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3125 completes counterfactual action-authority envelope diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3125 residual hard-safety counterfactual action-authority envelope diagnostic artifacts",
            "admission_evidence": ["M3125 summary gate matrix envelope requirement and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no feasibility or infeasibility proof claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3126 status queue scoreboard research log and review",
                "one follow-up manifest only if M3126 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3126 accepts or rejects M3125 as complete and claim-safe",
                "next stop synthesis architecture diagnostic repair or artifact-repair route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3126 audits engineering diagnostic artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3126; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3125 diagnostic artifacts only.",
            "negative_result_policy": "Preserve envelope evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3125 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits counterfactual action-authority envelope evidence before repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3126 prepares engineering route decision",
            "must_synthesize_if": [
                "M3126 cannot accept M3125 as complete and claim-safe",
                "M3126 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result feasibility-proof or self-ID evidence",
                "M3126 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3126 audits M3125 artifact row counts gates actor contract and claim boundaries",
            "M3126 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3126 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3126 hides M3125 failures or missing artifacts",
            "M3126 treats M3125 diagnostics as validation repair-success feasibility proof or performance verdict",
            "M3126 changes actor input or action contract",
            "M3126 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3126 audits M3125 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [{"name": "active_safety_driver_residual_counterfactual_action_authority_envelope_diagnostic_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3125-{gate_id}",
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
    envelope_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    m3123_summary = source["m3123_summary"]
    m3115_summary = source["m3115_summary"]
    audit_text = str(source.get("m3124_audit_text", ""))
    status_counts = Counter(str(row.get("envelope_status", "")) for row in envelope_rows)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate(
            "m3124_route_marker",
            "lineage",
            "accept_m3123_diagnostics_route_to_m3125_counterfactual_action_authority_envelope_diagnostic_materialization" in audit_text,
            "route marker",
            "present",
            "lineage_invalid",
        ),
        gate("m3123_status_pass", "lineage", _bool(m3123_summary.get("status_pass")), m3123_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3123_gate_matrix_pass", "lineage", _bool(m3123_summary.get("gate_matrix_pass")), m3123_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3123_diagnostic_rows", "lineage", int(m3123_summary.get("diagnostic_row_count", 0)) == EXPECTED_RESIDUAL_ROWS, m3123_summary.get("diagnostic_row_count"), EXPECTED_RESIDUAL_ROWS, "lineage_invalid"),
        gate("m3115_status_pass", "lineage", _bool(m3115_summary.get("status_pass")), m3115_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3115_influence_rows", "lineage", len(source.get("m3115_action_influence_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3115_action_influence_rows", [])), EXPECTED_RESIDUAL_ROWS, "lineage_invalid"),
        gate("m3115_step_trace_rows_present", "lineage", len(source.get("m3115_step_trace_rows", [])) > 0, len(source.get("m3115_step_trace_rows", [])), ">0", "lineage_invalid"),
        gate("envelope_rows", "metric", len(envelope_rows) == EXPECTED_RESIDUAL_ROWS, len(envelope_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("collision_rows", "metric", sum(1 for row in envelope_rows if _bool(row.get("collision"))) == EXPECTED_COLLISION_ROWS, sum(1 for row in envelope_rows if _bool(row.get("collision"))), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_rows", "metric", sum(1 for row in envelope_rows if _bool(row.get("offtrack"))) == EXPECTED_OFFTRACK_ROWS, sum(1 for row in envelope_rows if _bool(row.get("offtrack"))), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("speed_too_low_rows", "metric", sum(1 for row in envelope_rows if _bool(row.get("speed_too_low"))) == EXPECTED_SPEED_TOO_LOW_ROWS, sum(1 for row in envelope_rows if _bool(row.get("speed_too_low"))), EXPECTED_SPEED_TOO_LOW_ROWS, "behavior_regression"),
        gate("row_identity_preserved", "metric", all(_bool(row.get("row_identity_preserved")) for row in envelope_rows), "all", "preserved", "metric_artifact"),
        gate("envelope_statuses_present", "metric", bool(status_counts) and "authority_envelope_mixed_requires_result_audit" not in status_counts, dict(sorted(status_counts.items())), "classified", "metric_artifact"),
        gate("brake_margin_materialized", "metric", all(row.get("final_10_brake_margin_to_full") != "" for row in envelope_rows), "all rows", "margin present", "metric_artifact"),
        gate("steer_margin_materialized", "metric", all(row.get("final_10_steer_margin_to_saturation") != "" for row in envelope_rows), "all rows", "margin present", "metric_artifact"),
        gate("throttle_tradeoff_materialized", "metric", all(row.get("throttle_deceleration_tradeoff_label") for row in envelope_rows), "all rows", "tradeoff label present", "metric_artifact"),
        gate("requirement_rows", "metric", len(requirement_rows) >= 8, len(requirement_rows), ">=8", "metric_artifact"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(m3123_summary.get("runtime_base_policy_required")), m3123_summary.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("no_new_execution", "execution", True, "no reset step rollout replay fitting training validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3125 Residual Hard-Safety Counterfactual Action-Authority Envelope Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- envelope residual rows: {summary['envelope_row_count']}",
            f"- residual collision rows: {summary['residual_collision_count']}",
            f"- residual offtrack rows: {summary['residual_offtrack_count']}",
            f"- residual speed-too-low rows: {summary['residual_speed_too_low_count']}",
            f"- envelope status counts: {summary['envelope_status_counts']}",
            f"- route recommendation counts: {summary['route_recommendation_counts']}",
            f"- mean final brake margin to full: {summary['final_10_brake_margin_to_full_mean']}",
            f"- mean final steer margin to saturation: {summary['final_10_steer_margin_to_saturation_mean']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3125 is a row-preserving no-new-execution diagnostic. It quantifies direct-action envelope pressure from existing M3123/M3115 artifacts: physical brake margin to full brake, steer margin to saturation, throttle/deceleration tradeoff labels, saturation fraction, and route recommendations for the seven residual hard-safety rows.",
            "",
            "M3125 does not prove that a row is feasible or infeasible, and it does not claim repair success. Its main result is that any next route must be audited as a trajectory-level/controller-architecture or timing hypothesis before another local direct-gain edit is treated as justified.",
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
    m3124_audit: Path,
    m3123_dir: Path,
    m3115_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3124_audit=m3124_audit, m3123_dir=m3123_dir, m3115_dir=m3115_dir)
    envelope_rows = counterfactual_action_authority_envelope_rows(
        source["m3123_envelope_source_rows"],
        source["m3115_action_influence_rows"],
        source["m3115_step_trace_rows"],
    )
    requirement_rows = envelope_requirement_rows(envelope_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["counterfactual_action_authority_envelope_rows"], envelope_rows, ENVELOPE_FIELDNAMES),
        (paths["envelope_requirement_rows"], requirement_rows, REQUIREMENT_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        envelope_rows=envelope_rows,
        requirement_rows=requirement_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_counts = Counter(str(row.get("envelope_status", "")) for row in envelope_rows)
    route_counts = Counter(str(row.get("route_recommendation", "")) for row in envelope_rows)
    brake_margins = [_float(row.get("final_10_brake_margin_to_full")) for row in envelope_rows]
    steer_margins = [_float(row.get("final_10_steer_margin_to_saturation")) for row in envelope_rows]
    negative_throttle_margins = [_float(row.get("negative_throttle_margin_to_full_decel")) for row in envelope_rows]
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m3123_diagnostic_row_count": len(source["m3123_envelope_source_rows"]),
        "source_m3115_action_influence_row_count": len(source["m3115_action_influence_rows"]),
        "source_m3115_step_trace_row_count": len(source["m3115_step_trace_rows"]),
        "envelope_row_count": len(envelope_rows),
        "residual_collision_count": sum(1 for row in envelope_rows if _bool(row.get("collision"))),
        "residual_offtrack_count": sum(1 for row in envelope_rows if _bool(row.get("offtrack"))),
        "residual_speed_too_low_count": sum(1 for row in envelope_rows if _bool(row.get("speed_too_low"))),
        "envelope_status_counts": dict(sorted(status_counts.items())),
        "route_recommendation_counts": dict(sorted(route_counts.items())),
        "near_or_full_exhausted_envelope_row_count": sum(
            1 for row in envelope_rows if "exhausted" in str(row.get("envelope_status", ""))
        ),
        "timing_limited_envelope_row_count": sum(
            1 for row in envelope_rows if "timing" in str(row.get("envelope_status", ""))
        ),
        "final_10_brake_margin_to_full_mean": _mean(brake_margins),
        "final_10_steer_margin_to_saturation_mean": _mean(steer_margins),
        "negative_throttle_margin_to_full_decel_mean": _mean(negative_throttle_margins),
        "envelope_requirement_row_count": len(requirement_rows),
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
        "feasibility_proof_claim_made": False,
        "infeasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic_route_to_m3126_result_audit",
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
    parser.add_argument("--m3124-audit", type=Path, default=DEFAULT_M3124_AUDIT)
    parser.add_argument("--m3123-dir", type=Path, default=DEFAULT_M3123_DIR)
    parser.add_argument("--m3115-dir", type=Path, default=DEFAULT_M3115_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3124_audit=args.m3124_audit,
        m3123_dir=args.m3123_dir,
        m3115_dir=args.m3115_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"envelope_rows={summary['envelope_row_count']}")
    print(f"residual_collision_count={summary['residual_collision_count']}")
    print(f"residual_offtrack_count={summary['residual_offtrack_count']}")
    print(f"residual_speed_too_low_count={summary['residual_speed_too_low_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
