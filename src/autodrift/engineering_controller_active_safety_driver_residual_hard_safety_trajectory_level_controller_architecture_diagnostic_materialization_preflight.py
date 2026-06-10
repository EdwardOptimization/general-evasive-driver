"""Materialize M3127 trajectory-level controller architecture diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3127-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "controller-architecture-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3128-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-"
    "controller-architecture-diagnostic-result-audit"
)
M3126_ID = (
    "m3126-engineering-controller-active-safety-driver-residual-hard-safety-counterfactual-"
    "action-authority-envelope-diagnostic-result-audit"
)
M3125_ID = (
    "m3125-engineering-controller-active-safety-driver-residual-hard-safety-counterfactual-"
    "action-authority-envelope-diagnostic-materialization-preflight"
)
M3115_ID = (
    "m3115-engineering-controller-active-safety-driver-residual-failure-step-action-influence-"
    "trace-materialization-preflight"
)

DEFAULT_M3126_AUDIT = Path(f"docs/{M3126_ID}.md")
DEFAULT_M3125_DIR = Path(
    "runs/m3125_engineering_controller_active_safety_driver_residual_hard_safety_counterfactual_"
    "action_authority_envelope_diagnostic_materialization_preflight"
)
DEFAULT_M3115_DIR = Path(
    "runs/m3115_engineering_controller_active_safety_driver_residual_failure_step_action_"
    "influence_trace_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3127_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "controller_architecture_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
POLICY_ID = "m3127_residual_hard_safety_trajectory_level_controller_architecture_diagnostic"

CLAIM_SCOPE = (
    "M3127 Active Safety Driver residual hard-safety trajectory-level controller architecture "
    "diagnostic materialization only; existing M3126 audit text, M3125 envelope rows, and M3115 "
    "trace/action-influence rows may be transformed into row-preserving architecture candidate, "
    "controller contract requirement, claim, gate, doc, and M3128 audit manifest artifacts. No "
    "reset, step, rollout, replay, fitting, PPO, training, repair materialization, implementation, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, feasibility proof, infeasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair materialization, controller implementation, validation result, driver-performance verdict, "
    "current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, feasibility proof, "
    "infeasibility proof, or level3 self-identification"
)

ARCHITECTURE_FIELDNAMES = [
    "architecture_candidate_id",
    "envelope_id",
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
    "envelope_status",
    "route_recommendation",
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
    "action_saturation_fraction",
    "max_obstacle_urgency_actor_visible",
    "max_edge_urgency_actor_visible",
    "max_abs_road_center_error_actor_visible",
    "min_actor_edge_margin_m_min",
    "visible_obstacle_fraction",
    "terminal_obstacle_x_m_actor_visible",
    "terminal_obstacle_y_m_actor_visible",
    "architecture_family",
    "controller_mode",
    "controller_contract",
    "primary_metric_target",
    "secondary_metric_target",
    "required_evidence_before_repair",
    "why_local_gain_is_insufficient",
    "architecture_interpretation",
    "implementation_allowed_in_m3127",
    "measurement_allowed_in_m3127",
    "row_identity_preserved",
    "m3127_no_new_execution",
    "actor_observation_contract",
    "candidate_output_semantics",
    "candidate_output_components",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
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
    "m3127_no_new_execution",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3127",
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


def _mean(values: list[float]) -> float | str:
    return sum(values) / len(values) if values else ""


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "architecture_candidate_rows": output_dir / "architecture_candidate_rows.csv",
        "controller_contract_requirement_rows": output_dir / "controller_contract_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3126_audit: Path, m3125_dir: Path, m3115_dir: Path) -> dict[str, Any]:
    paths = {
        "m3126_audit": m3126_audit,
        "m3125_summary": m3125_dir / "summary.json",
        "m3125_envelope_rows": m3125_dir / "counterfactual_action_authority_envelope_rows.csv",
        "m3125_requirement_rows": m3125_dir / "envelope_requirement_rows.csv",
        "m3125_gate_rows": m3125_dir / "gate_matrix.csv",
        "m3115_summary": m3115_dir / "summary.json",
        "m3115_action_influence_rows": m3115_dir / "residual_action_influence_rows.csv",
        "m3115_step_trace_rows": m3115_dir / "residual_step_trace_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3126_audit_text": paths["m3126_audit"].read_text(encoding="utf-8") if exists["m3126_audit"] else "",
        "m3125_summary": read_json(paths["m3125_summary"]) if exists["m3125_summary"] else {},
        "m3125_envelope_rows": read_csv_rows(paths["m3125_envelope_rows"]),
        "m3125_requirement_rows": read_csv_rows(paths["m3125_requirement_rows"]),
        "m3125_gate_rows": read_csv_rows(paths["m3125_gate_rows"]),
        "m3115_summary": read_json(paths["m3115_summary"]) if exists["m3115_summary"] else {},
        "m3115_action_influence_rows": read_csv_rows(paths["m3115_action_influence_rows"]),
        "m3115_step_trace_rows": read_csv_rows(paths["m3115_step_trace_rows"]),
    }


def classify_architecture_candidate(row: Mapping[str, Any]) -> tuple[str, str, str, str, str, str]:
    """Choose an architecture diagnostic label without implementing a controller."""

    collision = _bool(row.get("collision"))
    offtrack = _bool(row.get("offtrack"))
    envelope_status = str(row.get("envelope_status", ""))
    final_steer_margin = _float(row.get("final_10_steer_margin_to_saturation"))
    final_brake_margin = _float(row.get("final_10_brake_margin_to_full"))
    high_sideslip = _float(row.get("high_sideslip_fraction"))
    max_edge = _float(row.get("max_edge_urgency_actor_visible"))

    if collision and "exhausted" in envelope_status:
        family = "actor_visible_receding_horizon_clearance_corridor_reflex"
        mode = "short_horizon_clearance_timing_and_lateral_offset_scheduler"
        contract = "obs72_current_frame_geometry_to_direct_action3_no_runtime_base_policy"
        primary = "collision_clearance_margin"
        secondary = "speed_floor_and_stability_preservation"
        reason = (
            "collision row is already near direct brake/steer saturation, so local gain does not create "
            "a new evidence axis"
        )
    elif offtrack and ("near_exhausted" in envelope_status or final_steer_margin <= 0.05):
        family = "actor_visible_stability_corridor_recovery_reflex"
        mode = "short_horizon_edge_and_sideslip_recovery_scheduler"
        contract = "obs72_current_frame_edge_stability_to_direct_action3_no_runtime_base_policy"
        primary = "offtrack_and_recovery_stability"
        secondary = "clearance_and_speed_floor_preservation"
        reason = (
            "offtrack row is near steer saturation under edge pressure, so local steer gain is not a "
            "sufficient next evidence axis"
        )
    elif offtrack and (high_sideslip >= 0.25 or max_edge >= 0.85):
        family = "actor_visible_stability_timing_reflex"
        mode = "short_horizon_sideslip_phase_and_edge_margin_scheduler"
        contract = "obs72_current_frame_stability_signals_to_direct_action3_no_runtime_base_policy"
        primary = "stability_recovery_timing"
        secondary = "offtrack_and_speed_floor_preservation"
        reason = "offtrack row retains timing margin but needs trajectory-phase evidence before implementation"
    elif collision and final_brake_margin > 0.25:
        family = "actor_visible_brake_timing_reflex"
        mode = "short_horizon_deceleration_timing_scheduler"
        contract = "obs72_current_frame_obstacle_geometry_to_direct_action3_no_runtime_base_policy"
        primary = "collision_brake_timing"
        secondary = "speed_floor_preservation"
        reason = "collision row has nominal brake margin but still needs timing evidence before implementation"
    else:
        family = "architecture_candidate_unclassified_requires_audit"
        mode = "m3128_result_audit_required"
        contract = "contract_unclassified_requires_audit"
        primary = "audit_required"
        secondary = "audit_required"
        reason = "source row does not support a stronger architecture label"
    interpretation = (
        "diagnostic only; the candidate preserves actor-visible obs72 input and direct [steer throttle brake] "
        "output semantics before any repair implementation or measurement"
    )
    return family, mode, contract, primary, secondary, f"{reason}; {interpretation}"


def architecture_candidate_rows(
    envelope_rows: list[dict[str, str]],
    influence_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    influence_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in influence_rows}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(envelope_rows, start=1):
        source_id = str(row.get("source_measurement_episode_id", ""))
        influence = influence_by_source.get(source_id, {})
        family, mode, contract, primary, secondary, interpretation = classify_architecture_candidate(row)
        rows.append(
            {
                "architecture_candidate_id": f"m3127-architecture-candidate-{index:04d}",
                "envelope_id": row.get("envelope_id", ""),
                "trace_episode_id": row.get("trace_episode_id", influence.get("trace_episode_id", "")),
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
                "envelope_status": row.get("envelope_status", ""),
                "route_recommendation": row.get("route_recommendation", ""),
                "terminal_speed_mps": row.get("terminal_speed_mps", influence.get("terminal_speed_mps", "")),
                "terminal_beta_abs": row.get("terminal_beta_abs", influence.get("terminal_beta_abs", "")),
                "terminal_lateral_error_m": row.get(
                    "terminal_lateral_error_m",
                    influence.get("terminal_lateral_error_m", ""),
                ),
                "terminal_min_clearance_margin_m": row.get(
                    "terminal_min_clearance_margin_m",
                    influence.get("terminal_min_clearance_margin_m", ""),
                ),
                "high_sideslip_fraction": row.get("high_sideslip_fraction", influence.get("high_sideslip_fraction", "")),
                "final_10_mean_throttle_action": row.get(
                    "final_10_mean_throttle_action",
                    influence.get("final_10_mean_throttle_action", ""),
                ),
                "final_10_mean_brake_physical": row.get(
                    "final_10_mean_brake_physical",
                    influence.get("final_10_mean_brake_physical", ""),
                ),
                "final_10_brake_margin_to_full": row.get("final_10_brake_margin_to_full", ""),
                "final_10_mean_abs_steer": row.get(
                    "final_10_mean_abs_steer",
                    influence.get("final_10_mean_abs_steer", ""),
                ),
                "final_10_steer_margin_to_saturation": row.get("final_10_steer_margin_to_saturation", ""),
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
                "max_abs_road_center_error_actor_visible": influence.get("max_abs_road_center_error_actor_visible", ""),
                "min_actor_edge_margin_m_min": influence.get("min_actor_edge_margin_m_min", ""),
                "visible_obstacle_fraction": influence.get("visible_obstacle_fraction", ""),
                "terminal_obstacle_x_m_actor_visible": row.get(
                    "terminal_obstacle_x_m_actor_visible",
                    influence.get("terminal_obstacle_x_m_actor_visible", ""),
                ),
                "terminal_obstacle_y_m_actor_visible": row.get(
                    "terminal_obstacle_y_m_actor_visible",
                    influence.get("terminal_obstacle_y_m_actor_visible", ""),
                ),
                "architecture_family": family,
                "controller_mode": mode,
                "controller_contract": contract,
                "primary_metric_target": primary,
                "secondary_metric_target": secondary,
                "required_evidence_before_repair": "M3128 audit then separately registered architecture materialization preflight",
                "why_local_gain_is_insufficient": interpretation.split("; ", 1)[0],
                "architecture_interpretation": interpretation,
                "implementation_allowed_in_m3127": False,
                "measurement_allowed_in_m3127": False,
                "row_identity_preserved": bool(source_id and source_id in influence_by_source),
                "m3127_no_new_execution": True,
                "actor_observation_contract": "obs72_actor_visible_current_frame_only",
                "candidate_output_semantics": "direct_action_clipped",
                "candidate_output_components": "steer;throttle;brake",
                "runtime_base_policy_required": False,
                "checkpoint_model_required": False,
                "recurrent_hidden_state_required": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def controller_contract_requirement_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_counts = Counter(str(row.get("architecture_family", "")) for row in rows)
    collision_count = sum(1 for row in rows if _bool(row.get("collision")))
    offtrack_count = sum(1 for row in rows if _bool(row.get("offtrack")))
    specs = [
        (
            "direct_action3_output_contract",
            "p0",
            "interface:output",
            len(rows),
            "all M3127 candidates must keep [steer throttle brake] output semantics",
            "preserve direct action3 with bounded clipping and no runtime base policy",
            "future implementation must expose a deployable obs72-to-action3 driver contract",
        ),
        (
            "actor_visible_input_contract",
            "p0",
            "interface:input",
            len(rows),
            "architecture candidates are derived from M3125/M3115 actor-visible rows",
            "forbid hidden oracle source route target outcome progress verdict labels or baseline outcomes as actor input",
            "future implementation must include actor-input exclusion probes",
        ),
        (
            "no_ttc_actor_shortcut",
            "p0",
            "contract:actor_input",
            len(rows),
            "M3127 may use only actor-visible geometry and urgency signals already present in obs72 diagnostics",
            "forbid TTC as actor input or privileged shortcut even when geometry can be internally transformed",
            "future audit must check feature names and runtime API inputs",
        ),
        (
            "collision_clearance_corridor_architecture",
            "p0",
            "termination:obstacle_collision",
            collision_count,
            f"{collision_count} residual collision rows route to trajectory-level clearance evidence",
            "materialize clearance corridor timing architecture before any repair implementation",
            "M3128 must accept or reject the collision architecture route",
        ),
        (
            "offtrack_stability_corridor_architecture",
            "p0",
            "termination:off_track",
            offtrack_count,
            f"{offtrack_count} residual offtrack rows route to stability/edge recovery architecture evidence",
            "materialize stability corridor timing architecture before any repair implementation",
            "M3128 must accept or reject the offtrack architecture route",
        ),
        (
            "speed_floor_deceleration_separation",
            "p1",
            "contract:speed_floor",
            sum(1 for row in rows if _float(row.get("terminal_speed_mps")) >= 14.0),
            "residual rows preserve zero speed-too-low while hard-safety failures remain high-speed",
            "track speed-floor, collision, offtrack, clearance, and stability as separate gates",
            "future implementation must not hide speed-too-low regressions behind collision fixes",
        ),
        (
            "row_preserving_architecture_traceability",
            "p0",
            "lineage:row_identity",
            len(rows),
            f"architecture families {dict(sorted(family_counts.items()))}",
            "preserve envelope row to architecture candidate traceability",
            "future artifacts must keep source_measurement_episode_id and fresh_panel_row_id",
        ),
        (
            "m3128_result_audit_required",
            "p0",
            "process:audit",
            len(rows),
            "M3127 is diagnostic materialization only",
            "route to M3128 audit before implementation measurement validation or verdict",
            "M3128 audit artifact must exist before any next route",
        ),
        (
            "no_repair_success_claim",
            "p0",
            "claim:diagnostic_only",
            len(rows),
            "architecture labels are design-route evidence, not measured behavior",
            "reject repair-success feasibility-proof performance and current-sim verdict claims",
            "future claims require separately registered measurement and audit",
        ),
        (
            "architecture_branch_synthesis_guard",
            "p1",
            "local_search_guard",
            len(family_counts),
            "new branch opens trajectory-level controller architecture diagnosis",
            "synthesize if architecture diagnostics cannot preserve the deployable action contract",
            "do not return to local direct-gain search without M3128 decision",
        ),
    ]
    return [
        {
            "requirement_id": f"m3127-requirement-{index:04d}",
            "requirement_family": family,
            "priority": priority,
            "affected_group": group,
            "row_count": row_count,
            "trigger_evidence": trigger,
            "requirement": requirement,
            "measurable_next_gate": gate,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3127_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, priority, group, row_count, trigger, requirement, gate) in enumerate(specs, start=1)
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("architecture_candidate_rows", "diagnostic", True, "architecture_candidate_rows.csv"),
        ("controller_contract_requirement_rows", "diagnostic_requirement", True, "controller_contract_requirement_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3128 audit manifest"),
    ]
    blocked = [
        ("new_execution", "execution", "future separately registered measurement route"),
        ("repair_materialization", "repair", "future separately registered repair route"),
        ("controller_implementation", "implementation", "future separately registered materialization route"),
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
            "claim_id": f"m3127-{claim_id}",
            "claim_family": family,
            "allowed_in_m3127": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3127-{claim_id}",
            "claim_family": family,
            "allowed_in_m3127": False,
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
        "priority": 31230,
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
        "hypothesis": "A bounded result audit can accept or reject the M3127 trajectory-level controller architecture diagnostic artifacts before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3126_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "architecture_candidate_rows.csv"),
                str(output_dir / "controller_contract_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": [
                "audit trajectory-level controller architecture diagnostics before implementation routing"
            ],
            "derived_from": [MILESTONE_ID, M3126_ID, M3125_ID, M3115_ID],
            "blocked_by": [
                "M3127 architecture diagnostic artifacts require audit before repair materialization or measurement",
                "M3127 is no-new-execution diagnostic materialization and cannot support repair-success claims",
            ],
            "supersedes": ["direct controller implementation after M3126 audit without architecture diagnostic audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3128 must audit M3127 summary architecture requirement claim and gate artifacts",
            "M3128 must preserve obs72/action3 direct [steer throttle brake] actor contract and runtime_base_policy_required false",
            "M3128 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof infeasibility-proof and self-ID claims",
            "M3128 must select exactly one stop synthesis implementation diagnostic repair route or artifact-repair route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3127 architecture labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof infeasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_trajectory_level_controller_architecture_diagnosis",
            "evidence_axis": "residual_trajectory_level_controller_architecture_diagnostic_result_audit",
            "evidence_increment": "audits no-new-execution architecture diagnostic artifacts after M3127",
            "claim_scope": "Result audit only; no implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3127 artifacts are missing or gate matrix fails",
                "stop if actor or row identity contracts were violated",
                "route to synthesis if no actor-contract-preserving architecture candidate remains",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to synthesis or stop if no deployable next route remains",
                "route to one constrained implementation materialization only after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3127 completes trajectory-level controller architecture diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3127 trajectory-level controller architecture diagnostic artifacts",
            "admission_evidence": ["M3127 summary gate matrix architecture requirement and claim artifacts"],
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
                "M3128 status queue scoreboard research log and review",
                "one follow-up manifest only if M3128 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3128 accepts or rejects M3127 as complete and claim-safe",
                "next stop synthesis implementation materialization diagnostic or artifact-repair route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3128 audits engineering architecture diagnostic artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3128; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3127 diagnostic artifacts only.",
            "negative_result_policy": "Preserve architecture evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3127 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits architecture diagnostic evidence before implementation routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3128 prepares engineering route decision",
            "must_synthesize_if": [
                "M3128 cannot accept M3127 as complete and claim-safe",
                "M3128 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result feasibility-proof or self-ID evidence",
                "M3128 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3128 audits M3127 artifact row counts gates actor contract and claim boundaries",
            "M3128 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3128 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3128 hides M3127 failures or missing artifacts",
            "M3128 treats M3127 diagnostics as validation repair-success feasibility proof or performance verdict",
            "M3128 changes actor input or action contract",
            "M3128 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3128 audits M3127 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [
            {
                "name": "active_safety_driver_residual_trajectory_level_controller_architecture_diagnostic_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3127-{gate_id}",
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
    architecture_rows: list[dict[str, Any]],
    requirement_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    m3125_summary = source["m3125_summary"]
    m3115_summary = source["m3115_summary"]
    audit_text = str(source.get("m3126_audit_text", ""))
    family_counts = Counter(str(row.get("architecture_family", "")) for row in architecture_rows)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate(
            "m3126_route_marker",
            "lineage",
            "accept_m3125_envelope_diagnostics_route_to_m3127_trajectory_level_controller_architecture_diagnostic_materialization" in audit_text,
            "route marker",
            "present",
            "lineage_invalid",
        ),
        gate("m3125_status_pass", "lineage", _bool(m3125_summary.get("status_pass")), m3125_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3125_gate_matrix_pass", "lineage", _bool(m3125_summary.get("gate_matrix_pass")), m3125_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3125_envelope_rows", "lineage", int(m3125_summary.get("envelope_row_count", 0)) == EXPECTED_RESIDUAL_ROWS, m3125_summary.get("envelope_row_count"), EXPECTED_RESIDUAL_ROWS, "lineage_invalid"),
        gate("m3115_status_pass", "lineage", _bool(m3115_summary.get("status_pass")), m3115_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3115_influence_rows", "lineage", len(source.get("m3115_action_influence_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3115_action_influence_rows", [])), EXPECTED_RESIDUAL_ROWS, "lineage_invalid"),
        gate("architecture_rows", "metric", len(architecture_rows) == EXPECTED_RESIDUAL_ROWS, len(architecture_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("collision_rows", "metric", sum(1 for row in architecture_rows if _bool(row.get("collision"))) == EXPECTED_COLLISION_ROWS, sum(1 for row in architecture_rows if _bool(row.get("collision"))), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_rows", "metric", sum(1 for row in architecture_rows if _bool(row.get("offtrack"))) == EXPECTED_OFFTRACK_ROWS, sum(1 for row in architecture_rows if _bool(row.get("offtrack"))), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("speed_too_low_rows", "metric", sum(1 for row in architecture_rows if _bool(row.get("speed_too_low"))) == EXPECTED_SPEED_TOO_LOW_ROWS, sum(1 for row in architecture_rows if _bool(row.get("speed_too_low"))), EXPECTED_SPEED_TOO_LOW_ROWS, "behavior_regression"),
        gate("row_identity_preserved", "metric", all(_bool(row.get("row_identity_preserved")) for row in architecture_rows), "all", "preserved", "metric_artifact"),
        gate("architecture_families_present", "metric", bool(family_counts) and "architecture_candidate_unclassified_requires_audit" not in family_counts, dict(sorted(family_counts.items())), "classified", "metric_artifact"),
        gate("controller_contract_requirement_rows", "metric", len(requirement_rows) >= 10, len(requirement_rows), ">=10", "metric_artifact"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("direct_action3_output", "contract", all(str(row.get("candidate_output_components")) == "steer;throttle;brake" for row in architecture_rows), "all", "steer;throttle;brake", "contract_violation"),
        gate("runtime_base_policy_absent", "contract", all(not _bool(row.get("runtime_base_policy_required")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("checkpoint_model_absent", "contract", all(not _bool(row.get("checkpoint_model_required")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("hidden_oracle_actor_inputs_absent", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("ttc_actor_inputs_absent", "contract", all(not _bool(row.get("ttc_actor_input_required")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("no_implementation", "execution", all(not _bool(row.get("implementation_allowed_in_m3127")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("no_measurement", "execution", all(not _bool(row.get("measurement_allowed_in_m3127")) for row in architecture_rows), "all", False, "contract_violation"),
        gate("no_new_execution", "execution", True, "no reset step rollout replay fitting training validation", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3127 Residual Hard-Safety Trajectory-Level Controller Architecture Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- architecture residual rows: {summary['architecture_candidate_row_count']}",
            f"- residual collision rows: {summary['residual_collision_count']}",
            f"- residual offtrack rows: {summary['residual_offtrack_count']}",
            f"- residual speed-too-low rows: {summary['residual_speed_too_low_count']}",
            f"- architecture family counts: {summary['architecture_family_counts']}",
            f"- controller contract requirement rows: {summary['controller_contract_requirement_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3127 is no-new-execution architecture diagnostic materialization. It converts M3125 envelope pressure into row-preserving trajectory-level controller architecture candidates while preserving obs72 actor-visible input and direct `[steer, throttle, brake]` output semantics.",
            "",
            "The result supports an audited architecture route, not a controller implementation or repair-success claim. M3128 must audit this artifact before any implementation materialization, measurement, validation, or verdict.",
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
    m3126_audit: Path,
    m3125_dir: Path,
    m3115_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3126_audit=m3126_audit, m3125_dir=m3125_dir, m3115_dir=m3115_dir)
    arch_rows = architecture_candidate_rows(
        source["m3125_envelope_rows"],
        source["m3115_action_influence_rows"],
    )
    requirement_rows = controller_contract_requirement_rows(arch_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["architecture_candidate_rows"], arch_rows, ARCHITECTURE_FIELDNAMES),
        (paths["controller_contract_requirement_rows"], requirement_rows, REQUIREMENT_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        architecture_rows=arch_rows,
        requirement_rows=requirement_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    family_counts = Counter(str(row.get("architecture_family", "")) for row in arch_rows)
    mode_counts = Counter(str(row.get("controller_mode", "")) for row in arch_rows)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_trajectory_level_controller_architecture_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_trajectory_level_controller_architecture_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m3125_envelope_row_count": len(source["m3125_envelope_rows"]),
        "source_m3115_action_influence_row_count": len(source["m3115_action_influence_rows"]),
        "source_m3115_step_trace_row_count": len(source["m3115_step_trace_rows"]),
        "architecture_candidate_row_count": len(arch_rows),
        "residual_collision_count": sum(1 for row in arch_rows if _bool(row.get("collision"))),
        "residual_offtrack_count": sum(1 for row in arch_rows if _bool(row.get("offtrack"))),
        "residual_speed_too_low_count": sum(1 for row in arch_rows if _bool(row.get("speed_too_low"))),
        "architecture_family_counts": dict(sorted(family_counts.items())),
        "controller_mode_counts": dict(sorted(mode_counts.items())),
        "controller_contract_requirement_row_count": len(requirement_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "mean_final_10_brake_margin_to_full": _mean([_float(row.get("final_10_brake_margin_to_full")) for row in arch_rows]),
        "mean_final_10_steer_margin_to_saturation": _mean(
            [_float(row.get("final_10_steer_margin_to_saturation")) for row in arch_rows]
        ),
        "runtime_driver_id": POLICY_ID,
        "candidate_output_semantics": "direct_action_clipped",
        "candidate_output_components": ["steer", "throttle", "brake"],
        "actor_observation_contract": "obs72_actor_visible_current_frame_only",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
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
        "controller_implementation_run": False,
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
        "decision": "active_safety_driver_residual_hard_safety_trajectory_level_controller_architecture_diagnostic_route_to_m3128_result_audit",
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
    parser.add_argument("--m3126-audit", type=Path, default=DEFAULT_M3126_AUDIT)
    parser.add_argument("--m3125-dir", type=Path, default=DEFAULT_M3125_DIR)
    parser.add_argument("--m3115-dir", type=Path, default=DEFAULT_M3115_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3126_audit=args.m3126_audit,
        m3125_dir=args.m3125_dir,
        m3115_dir=args.m3115_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"architecture_rows={summary['architecture_candidate_row_count']}")
    print(f"residual_collision_count={summary['residual_collision_count']}")
    print(f"residual_offtrack_count={summary['residual_offtrack_count']}")
    print(f"residual_speed_too_low_count={summary['residual_speed_too_low_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
