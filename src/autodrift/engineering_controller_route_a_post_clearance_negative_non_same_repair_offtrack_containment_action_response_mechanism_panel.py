"""Materialize Route A offtrack-containment action-response mechanism context.

This runner reanalyzes existing M2807/M2810/M2812 artifacts only. It writes
row-level action-response mechanism context for the already-localized
offtrack-containment rows and success obstacle-pass contrast rows. It does not
execute environments, policies, replay, validation, training, ranking,
promotion, source builds, adapter probes, or high-fidelity simulation.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2813-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-action-response-mechanism-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2814-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-action-response-mechanism-panel-materialization-result-audit"
)
DEFAULT_M2807_DIR = Path(
    "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "cross_axis_bounded_execution_preflight"
)
DEFAULT_M2810_DIR = Path(
    "runs/m2810_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "offtrack_containment_localization_panel"
)
DEFAULT_M2812_SYNTHESIS = Path(
    "docs/m2812-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-localization-branch-synthesis.md"
)
DEFAULT_M2811_AUDIT = Path(
    "docs/m2811-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-localization-panel-materialization-result-audit.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "offtrack_containment_action_response_mechanism_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2813-engineering-controller-route-a-post-clearance-negative-non-same-repair-"
    "cross-axis-offtrack-containment-action-response-mechanism-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2814-engineering-controller-route-a-post-clearance-negative-"
    "non-same-repair-cross-axis-offtrack-containment-action-response-mechanism-panel-"
    "materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2813 Route A post-clearance negative non-same-repair offtrack-containment "
    "action-response mechanism panel materialization only; existing M2807/M2810/M2812 "
    "artifacts are reanalyzed into diagnostic row-level mechanism context while no "
    "reset, step, rollout, replay, validation, training, PPO, source build, adapter "
    "probe, external simulation, ranking, winner selection, promotion, success-rate "
    "verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, "
    "controller ranking, action-response ranking, stress-axis ranking, source-edge "
    "ranking, task-family ranking, profile ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation result, full ideal driver "
    "completion, or self-ID evidence"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "source_only_backend_reset_run": False,
    "source_only_backend_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "action_response_ranking_run": False,
    "stress_axis_ranking_run": False,
    "source_edge_ranking_run": False,
    "task_family_ranking_run": False,
    "profile_ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_completion_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "private_holdout_used": False,
}

ACTION_RESPONSE_FIELDNAMES = [
    "mechanism_id",
    "localization_id",
    "candidate_id",
    "resolution_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "outcome_family",
    "success",
    "collision",
    "offtrack_noncollision",
    "min_clearance_margin",
    "speed_mean",
    "action_rate_mean",
    "previous_command_norm_mean",
    "previous_command_norm_peak",
    "current_action_norm_mean",
    "current_action_norm_peak",
    "action_trace_delta_mean",
    "action_trace_delta_peak",
    "previous_command_bootstrap_count",
    "previous_command_source",
    "action_trace_delta_source",
    "plan_action_rate_mean",
    "plan_first_action_error_mean",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "max_off_track_overshoot",
    "recoverability_window_success",
    "recoverability_window_success_available",
    "mechanism_context_family",
    "metric_context_available",
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
    "actor_visible_allowed",
    "claim_scope",
]
CONTRAST_FIELDNAMES = [
    "contrast_id",
    "outcome_family",
    "row_count",
    "success_count",
    "offtrack_count",
    "min_clearance_margin_mean",
    "speed_mean",
    "action_rate_mean",
    "previous_command_norm_mean",
    "current_action_norm_mean",
    "action_trace_delta_mean",
    "time_to_first_off_track_mean_s",
    "off_track_severity_mean",
    "recoverability_available_count",
    "recoverability_success_count",
    "ranking_claim_made",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_context_id",
    "guardrail_source",
    "guardrail_source_id",
    "task_source_id",
    "blocker_id",
    "route",
    "evidence_family",
    "row_count",
    "blocking_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_success_denominator_allowed",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "guardrail_role",
    "claim_scope",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2813",
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

REQUIRED_ACTION_FIELDS = (
    "speed_mean",
    "action_rate_mean",
    "previous_command_norm_mean",
    "previous_command_norm_peak",
    "current_action_norm_mean",
    "current_action_norm_peak",
    "action_trace_delta_mean",
    "action_trace_delta_peak",
    "previous_command_bootstrap_count",
)
CLAIM_CHECKS = (
    ("action_response_mechanism_panel_materialized", True, True, "M2813 mechanism rows"),
    ("success_offtrack_contrast_materialized", True, True, "M2813 contrast rows"),
    ("guardrail_context_preserved", True, True, "M2813 guardrail context rows"),
    ("actor_contract_preserved", True, True, "M2813 actor guard rows"),
    ("follow_up_result_audit_registered", True, True, "M2814 result-audit manifest"),
    ("existing_artifacts_reanalyzed_only", True, True, "M2807/M2810/M2812 source artifacts"),
    ("repair_success", False, False, "future repair result plus claim audit"),
    ("driver_performance", False, False, "future validation and claim audit"),
    ("validation_readiness", False, False, "future validation-readiness route decision"),
    ("validation_result", False, False, "future validation result"),
    ("controller_ranking", False, False, "future explicit ranking gate"),
    ("action_response_ranking", False, False, "future explicit ranking gate"),
    ("stress_axis_ranking", False, False, "future explicit ranking gate"),
    ("source_edge_ranking", False, False, "future explicit ranking gate"),
    ("task_family_ranking", False, False, "future explicit ranking gate"),
    ("profile_ranking", False, False, "future explicit ranking gate"),
    ("winner_selection", False, False, "future promotion gate"),
    ("checkpoint_promotion", False, False, "future promotion gate"),
    ("success_rate_verdict", False, False, "future verdict milestone"),
    ("paper_level_evidence", False, False, "future paper evidence matrix"),
    ("finite_window_vs_gru", False, False, "future controller-family comparison"),
    ("current_sim_verdict", False, False, "future current-sim synthesis"),
    ("high_fidelity_validation_result", False, False, "future high-fidelity validation"),
    ("full_ideal_driver_completion", False, False, "future full ideal driver gate"),
    ("level3_self_identification", False, False, "future self-ID proof gate"),
)


def materialize_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel(
    output_dir: Path | str,
    *,
    m2807_dir: Path | str = DEFAULT_M2807_DIR,
    m2810_dir: Path | str = DEFAULT_M2810_DIR,
    m2812_synthesis: Path | str = DEFAULT_M2812_SYNTHESIS,
    m2811_audit: Path | str = DEFAULT_M2811_AUDIT,
    route_plan: Path | str = DEFAULT_ROUTE_PLAN,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_path, Path(doc_path))
    source = load_source_artifacts(
        Path(m2807_dir),
        Path(m2810_dir),
        m2812_synthesis=Path(m2812_synthesis),
        m2811_audit=Path(m2811_audit),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )

    mechanism_rows = build_action_response_mechanism_rows(source)
    contrast_rows = build_success_offtrack_contrast_rows(mechanism_rows)
    guardrail_rows = build_guardrail_context_rows(source)
    actor_rows = build_actor_contract_guard_rows(source, mechanism_rows, guardrail_rows)
    claim_rows = build_claim_boundary_rows()

    gate_rows = build_gate_matrix_rows(
        source,
        mechanism_rows,
        contrast_rows,
        guardrail_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_outputs(paths, mechanism_rows, contrast_rows, guardrail_rows, actor_rows, claim_rows, gate_rows)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        mechanism_rows=mechanism_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_matrix_rows(
        source,
        mechanism_rows,
        contrast_rows,
        guardrail_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        mechanism_rows=mechanism_rows,
        contrast_rows=contrast_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "action_response_mechanism_rows": output_dir / "action_response_mechanism_rows.csv",
        "success_offtrack_contrast_rows": output_dir / "success_offtrack_contrast_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def write_outputs(
    paths: dict[str, Path],
    mechanism_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["action_response_mechanism_rows"], mechanism_rows, fieldnames=ACTION_RESPONSE_FIELDNAMES)
    write_csv_rows(paths["success_offtrack_contrast_rows"], contrast_rows, fieldnames=CONTRAST_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def load_source_artifacts(
    m2807_dir: Path,
    m2810_dir: Path,
    *,
    m2812_synthesis: Path,
    m2811_audit: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2812_synthesis": m2812_synthesis,
        "m2811_audit": m2811_audit,
        "m2810_summary": m2810_dir / "summary.json",
        "m2810_failure_localization_rows": m2810_dir / "failure_localization_rows.csv",
        "m2810_offtrack_containment_rows": m2810_dir / "offtrack_containment_rows.csv",
        "m2810_guardrail_context_rows": m2810_dir / "guardrail_context_rows.csv",
        "m2810_actor_contract_guard_rows": m2810_dir / "actor_contract_guard_rows.csv",
        "m2810_gate_matrix": m2810_dir / "gate_matrix.csv",
        "m2807_candidate_execution_rows": m2807_dir / "candidate_execution_rows.csv",
        "m2807_gate_matrix": m2807_dir / "gate_matrix.csv",
        "route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2810_summary": read_json(paths["m2810_summary"]),
        "m2810_failure_localization_rows": _read_csv_rows(paths["m2810_failure_localization_rows"]),
        "m2810_offtrack_containment_rows": _read_csv_rows(paths["m2810_offtrack_containment_rows"]),
        "m2810_guardrail_context_rows": _read_csv_rows(paths["m2810_guardrail_context_rows"]),
        "m2810_actor_contract_guard_rows": _read_csv_rows(paths["m2810_actor_contract_guard_rows"]),
        "m2810_gate_matrix": _read_csv_rows(paths["m2810_gate_matrix"]),
        "m2807_candidate_execution_rows": _read_csv_rows(paths["m2807_candidate_execution_rows"]),
        "m2807_gate_matrix": _read_csv_rows(paths["m2807_gate_matrix"]),
    }


def build_action_response_mechanism_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    executions = {row["candidate_id"]: row for row in source["m2807_candidate_execution_rows"]}
    rows = []
    for idx, localization in enumerate(source["m2810_failure_localization_rows"], start=1):
        execution = executions.get(localization.get("candidate_id", ""), {})
        row = {
            "mechanism_id": f"m2813-action-response-mechanism-{idx:04d}",
            "localization_id": localization.get("localization_id", ""),
            "candidate_id": localization.get("candidate_id", ""),
            "resolution_id": localization.get("resolution_id", execution.get("resolution_id", "")),
            "task_source_id": localization.get("task_source_id", execution.get("task_source_id", "")),
            "task_family": localization.get("task_family", execution.get("task_family", "")),
            "source_edge": localization.get("source_edge", execution.get("source_edge", "")),
            "stress_axis_primary": localization.get("stress_axis_primary", execution.get("stress_axis_primary", "")),
            "outcome_family": localization.get("failure_family", ""),
            "success": _bool(localization.get("success")),
            "collision": _bool(localization.get("collision")),
            "offtrack_noncollision": localization.get("failure_family") == "offtrack_positive_clearance",
            "min_clearance_margin": _float(localization.get("min_clearance_margin")),
            "speed_mean": _float(execution.get("speed_mean")),
            "action_rate_mean": _float(execution.get("action_rate_mean")),
            "previous_command_norm_mean": _float(execution.get("previous_command_norm_mean")),
            "previous_command_norm_peak": _float(execution.get("previous_command_norm_peak")),
            "current_action_norm_mean": _float(execution.get("current_action_norm_mean")),
            "current_action_norm_peak": _float(execution.get("current_action_norm_peak")),
            "action_trace_delta_mean": _float(execution.get("action_trace_delta_mean")),
            "action_trace_delta_peak": _float(execution.get("action_trace_delta_peak")),
            "previous_command_bootstrap_count": _int(execution.get("previous_command_bootstrap_count")),
            "previous_command_source": execution.get("previous_command_source", ""),
            "action_trace_delta_source": execution.get("action_trace_delta_source", ""),
            "plan_action_rate_mean": _float(execution.get("plan_action_rate_mean")),
            "plan_first_action_error_mean": _float(execution.get("plan_first_action_error_mean")),
            "time_to_first_off_track_s": _float(execution.get("time_to_first_off_track_s")),
            "off_track_severity_proxy": _float(execution.get("off_track_severity_proxy")),
            "max_off_track_overshoot": _float(execution.get("max_off_track_overshoot")),
            "recoverability_window_success": _bool(execution.get("recoverability_window_success")),
            "recoverability_window_success_available": _bool(execution.get("recoverability_window_success_available")),
            "diagnostic_only_no_verdict": True,
            "ranking_claim_made": False,
            "actor_visible_allowed": False,
            "claim_scope": CLAIM_SCOPE,
        }
        row["metric_context_available"] = action_response_metrics_available(row)
        row["mechanism_context_family"] = classify_mechanism_context(row)
        rows.append(row)
    return rows


def classify_mechanism_context(row: dict[str, Any]) -> str:
    if _bool(row.get("success")):
        return "success_obstacle_pass_action_response_context"
    if not _bool(row.get("offtrack_noncollision")):
        return "non_offtrack_action_response_context"
    time_to_offtrack = _float(row.get("time_to_first_off_track_s"))
    delta_peak = _float(row.get("action_trace_delta_peak"))
    if time_to_offtrack is not None and time_to_offtrack <= 1.5:
        return "early_offtrack_action_response_context"
    if delta_peak is not None and delta_peak >= 0.16:
        return "action_trace_delta_context"
    return "positive_clearance_offtrack_action_response_context"


def action_response_metrics_available(row: dict[str, Any]) -> bool:
    return all(_finite(_float(row.get(field))) for field in REQUIRED_ACTION_FIELDS)


def build_success_offtrack_contrast_rows(mechanism_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mechanism_rows:
        grouped[str(row["outcome_family"])].append(row)
    rows = []
    for idx, (outcome_family, group) in enumerate(sorted(grouped.items()), start=1):
        rows.append(
            {
                "contrast_id": f"m2813-success-offtrack-contrast-{idx:04d}",
                "outcome_family": outcome_family,
                "row_count": len(group),
                "success_count": sum(1 for row in group if _bool(row["success"])),
                "offtrack_count": sum(1 for row in group if _bool(row["offtrack_noncollision"])),
                "min_clearance_margin_mean": _mean([_float(row.get("min_clearance_margin")) for row in group]),
                "speed_mean": _mean([_float(row.get("speed_mean")) for row in group]),
                "action_rate_mean": _mean([_float(row.get("action_rate_mean")) for row in group]),
                "previous_command_norm_mean": _mean([_float(row.get("previous_command_norm_mean")) for row in group]),
                "current_action_norm_mean": _mean([_float(row.get("current_action_norm_mean")) for row in group]),
                "action_trace_delta_mean": _mean([_float(row.get("action_trace_delta_mean")) for row in group]),
                "time_to_first_off_track_mean_s": _mean([_float(row.get("time_to_first_off_track_s")) for row in group]),
                "off_track_severity_mean": _mean([_float(row.get("off_track_severity_proxy")) for row in group]),
                "recoverability_available_count": sum(
                    1 for row in group if _bool(row["recoverability_window_success_available"])
                ),
                "recoverability_success_count": sum(1 for row in group if _bool(row["recoverability_window_success"])),
                "ranking_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(source["m2810_guardrail_context_rows"], start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2813-guardrail-context-{idx:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_source_id": row.get("guardrail_source_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "route": row.get("route", ""),
                "evidence_family": row.get("evidence_family", ""),
                "row_count": _int(row.get("row_count")),
                "blocking_count": _int(row.get("blocking_count")),
                "execution_candidate": _bool(row.get("execution_candidate")),
                "execution_admitted": _bool(row.get("execution_admitted")),
                "execution_run": _bool(row.get("execution_run")),
                "ordinary_success_denominator_allowed": _bool(row.get("ordinary_success_denominator_allowed")),
                "protected_rows_in_success_denominator": _bool(row.get("protected_rows_in_success_denominator")),
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "diagnostic_only_no_verdict": True,
                "guardrail_role": row.get("guardrail_role", ""),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("m2813-actor-guard-observation-shape", "p0_observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("m2813-actor-guard-action-shape", "action_dim", ACTION_DIM, 3),
        actor_guard("m2813-actor-guard-m2810-rows-pass", "m2810_actor_guard_rows_pass", m2810_actor_rows_pass(source), True),
        actor_guard(
            "m2813-actor-guard-hidden-oracle",
            "hidden_oracle_actor_input_required",
            hidden_oracle_actor_input_detected(source),
            False,
        ),
        actor_guard(
            "m2813-actor-guard-actor-contract-changed",
            "actor_input_contract_changed",
            any(_bool(row.get("actor_input_contract_changed")) for row in source["m2807_candidate_execution_rows"]),
            False,
        ),
        actor_guard("m2813-actor-guard-mechanism-labels", "action_response_labels_actor_visible", False, False),
        actor_guard(
            "m2813-actor-guard-stress-axis-labels",
            "stress_axis_labels_actor_visible",
            any(_bool(row.get("stress_axis_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]),
            False,
        ),
        actor_guard("m2813-actor-guard-source-edge-labels", "source_edge_labels_actor_visible", False, False),
        actor_guard(
            "m2813-actor-guard-success-progress-labels",
            "success_progress_labels_actor_visible",
            any(_bool(row.get("success_progress_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]),
            False,
        ),
        actor_guard(
            "m2813-actor-guard-verdict-labels",
            "verdict_labels_actor_visible",
            any(_bool(row.get("verdict_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]),
            False,
        ),
        actor_guard(
            "m2813-actor-guard-protected-denominator",
            "protected_rows_in_success_denominator",
            any(_bool(row["protected_rows_in_success_denominator"]) for row in guardrail_rows),
            False,
        ),
        actor_guard(
            "m2813-actor-guard-guardrail-actor-visible",
            "guardrail_actor_visible_allowed",
            any(_bool(row["actor_visible_allowed"]) for row in guardrail_rows),
            False,
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2813-claim-{claim_family}",
            "claim_family": claim_family,
            "allowed_in_m2813": allowed,
            "claim_made": claim_made,
            "status_pass": allowed == claim_made,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_family, allowed, claim_made, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    counts = count_mechanism_outcomes(mechanism_rows)
    guardrails_executed = any(_bool(row["execution_run"]) for row in guardrail_rows)
    guardrails_in_denominator = any(
        _bool(row["ordinary_success_denominator_allowed"]) or _bool(row["protected_rows_in_success_denominator"])
        for row in guardrail_rows
    )
    return [
        gate_row("m2813-gate-source-artifacts-present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2813-gate-required-artifacts-present", "artifact", required_artifacts_present, True),
        gate_row("m2813-gate-m2810-status-pass", "lineage", _bool(source["m2810_summary"].get("status_pass")), True),
        gate_row("m2813-gate-m2810-gate-matrix-pass", "lineage", m2810_gate_rows_pass(source), True),
        gate_row("m2813-gate-m2807-gate-matrix-pass", "lineage", m2807_gate_rows_pass(source), True),
        gate_row("m2813-gate-mechanism-row-count", "diagnostic_accounting", len(mechanism_rows), 12),
        gate_row("m2813-gate-offtrack-mechanism-row-count", "diagnostic_accounting", counts["offtrack_count"], 10),
        gate_row("m2813-gate-success-mechanism-row-count", "diagnostic_accounting", counts["success_count"], 2),
        gate_row("m2813-gate-collision-mechanism-row-count", "diagnostic_accounting", counts["collision_count"], 0),
        gate_row("m2813-gate-contrast-row-count", "artifact", len(contrast_rows), 2),
        gate_row("m2813-gate-action-response-metrics-available", "artifact", all_action_metrics_available(mechanism_rows), True),
        gate_row("m2813-gate-offtrack-timing-rows", "artifact", offtrack_timing_available_count(mechanism_rows), 10),
        gate_row("m2813-gate-guardrail-context-rows", "guardrail", len(guardrail_rows), 44),
        gate_row("m2813-gate-guardrails-not-executed", "guardrail", guardrails_executed, False),
        gate_row("m2813-gate-guardrails-outside-denominator", "guardrail", guardrails_in_denominator, False),
        gate_row("m2813-gate-actor-contract-72-action-3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2813-gate-hidden-oracle-actor-input-absent", "actor_contract", hidden_oracle_actor_input_detected(source), False),
        gate_row("m2813-gate-actor-guard-rows-pass", "actor_contract", all(_bool(row["status_pass"]) for row in actor_rows), True),
        gate_row("m2813-gate-follow-up-result-audit-registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row("m2813-gate-claim-boundary-pass", "claim_boundary", claim_boundary_pass(claim_rows), True),
        gate_row("m2813-gate-no-reset-rollout-training-validation", "claim_boundary", False, False),
        gate_row("m2813-gate-no-ranking-promotion-performance", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    mechanism_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    counts = count_mechanism_outcomes(mechanism_rows)
    guardrails_executed = any(_bool(row["execution_run"]) for row in guardrail_rows)
    guardrails_in_denominator = any(
        _bool(row["ordinary_success_denominator_allowed"]) or _bool(row["protected_rows_in_success_denominator"])
        for row in guardrail_rows
    )
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2810_summary"].get("status_pass"))
        and m2810_gate_rows_pass(source)
        and m2807_gate_rows_pass(source)
        and len(mechanism_rows) == 12
        and counts["offtrack_count"] == 10
        and counts["success_count"] == 2
        and counts["collision_count"] == 0
        and len(contrast_rows) == 2
        and all_action_metrics_available(mechanism_rows)
        and offtrack_timing_available_count(mechanism_rows) == 10
        and len(guardrail_rows) == 44
        and not guardrails_executed
        and not guardrails_in_denominator
        and actor_ok
        and not hidden
        and all(_bool(row["status_pass"]) for row in actor_rows)
        and claim_boundary_pass(claim_rows)
        and gate_matrix_pass
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_clearance_non_same_repair_offtrack_action_response_v0",
        "result_class": "engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "action_response_mechanism_rows": str(paths["action_response_mechanism_rows"]),
        "success_offtrack_contrast_rows": str(paths["success_offtrack_contrast_rows"]),
        "guardrail_context_rows": str(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "source_artifacts_reanalyzed_only": True,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "mechanism_row_count": len(mechanism_rows),
        "offtrack_mechanism_row_count": counts["offtrack_count"],
        "success_mechanism_row_count": counts["success_count"],
        "collision_mechanism_row_count": counts["collision_count"],
        "contrast_row_count": len(contrast_rows),
        "action_response_metrics_available": all_action_metrics_available(mechanism_rows),
        "offtrack_timing_available_count": offtrack_timing_available_count(mechanism_rows),
        "recoverability_available_count": sum(
            1 for row in mechanism_rows if _bool(row["recoverability_window_success_available"])
        ),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "guardrails_not_executed": not guardrails_executed,
        "protected_rows_in_success_denominator": guardrails_in_denominator,
        "actor_contract_shape_72_action_3": actor_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden,
        "action_response_labels_actor_visible": False,
        "stress_axis_labels_actor_visible": any(
            _bool(row.get("stress_axis_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]
        ),
        "source_edge_labels_actor_visible": False,
        "success_progress_labels_actor_visible": any(
            _bool(row.get("success_progress_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]
        ),
        "verdict_labels_actor_visible": any(
            _bool(row.get("verdict_labels_actor_visible")) for row in source["m2807_candidate_execution_rows"]
        ),
        "selected_next_action": "m2814_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2813 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Offtrack-Containment Action-Response Mechanism Panel Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- action-response mechanism rows: `{summary['action_response_mechanism_rows']}`",
            f"- success/offtrack contrast rows: `{summary['success_offtrack_contrast_rows']}`",
            f"- guardrail context rows: `{summary['guardrail_context_rows']}`",
            f"- actor contract guard rows: `{summary['actor_contract_guard_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Mechanism Rows",
            "",
            f"- action-response mechanism rows: {summary['mechanism_row_count']}",
            f"- offtrack mechanism rows: {summary['offtrack_mechanism_row_count']}",
            f"- success obstacle-pass mechanism rows: {summary['success_mechanism_row_count']}",
            f"- collision mechanism rows: {summary['collision_mechanism_row_count']}",
            f"- success/offtrack contrast rows: {summary['contrast_row_count']}",
            f"- action-response metrics available: `{str(summary['action_response_metrics_available']).lower()}`",
            f"- offtrack timing rows: {summary['offtrack_timing_available_count']}",
            f"- recoverability available rows: {summary['recoverability_available_count']}",
            "",
            "## Guardrails",
            "",
            f"- guardrail context rows: {summary['guardrail_context_row_count']}",
            f"- guardrails not executed: `{str(summary['guardrails_not_executed']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- action-response, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2813 is no-rollout action-response mechanism materialization from existing artifacts only. It performs no reset, step, policy action, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
            "",
        ]
    )


def actor_guard(guard_id: str, guard_family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": guard_family,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_row(gate_id: str, gate_family: str, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": gate_family,
        "status_pass": observed == expected,
        "observed": observed,
        "expected": expected,
        "failure_type": "" if observed == expected else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def count_mechanism_outcomes(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "success_count": sum(1 for row in rows if row.get("outcome_family") == "success_obstacle_pass"),
        "offtrack_count": sum(1 for row in rows if _bool(row.get("offtrack_noncollision"))),
        "collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
    }


def all_action_metrics_available(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_bool(row.get("metric_context_available")) for row in rows)


def offtrack_timing_available_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if _bool(row.get("offtrack_noncollision")) and _finite(row.get("time_to_first_off_track_s")))


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    return (
        P0_OBSERVATION_DIM == 72
        and ACTION_DIM == 3
        and m2810_actor_rows_pass(source)
        and not hidden_oracle_actor_input_detected(source)
        and not any(_bool(row.get("actor_input_contract_changed")) for row in source["m2807_candidate_execution_rows"])
    )


def m2810_actor_rows_pass(source: dict[str, Any]) -> bool:
    return bool(source["m2810_actor_contract_guard_rows"]) and all(
        _bool(row.get("status_pass")) for row in source["m2810_actor_contract_guard_rows"]
    )


def m2810_gate_rows_pass(source: dict[str, Any]) -> bool:
    return bool(source["m2810_gate_matrix"]) and all(_bool(row.get("status_pass")) for row in source["m2810_gate_matrix"])


def m2807_gate_rows_pass(source: dict[str, Any]) -> bool:
    return bool(source["m2807_gate_matrix"]) and all(_bool(row.get("status_pass")) for row in source["m2807_gate_matrix"])


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    summary_hidden = any(
        _bool(source["m2810_summary"].get(key))
        for key in ("hidden_oracle_actor_input_detected", "hidden_oracle_actor_input_required")
    )
    row_hidden = any(_bool(row.get("hidden_oracle_actor_input_required")) for row in source["m2807_candidate_execution_rows"])
    return summary_hidden or row_hidden


def claim_boundary_pass(claim_rows: list[dict[str, Any]]) -> bool:
    return all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values())


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _mean(values: list[float | None]) -> float | None:
    finite = [value for value in values if _finite(value)]
    if not finite:
        return None
    return sum(finite) / len(finite)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A offtrack-containment action-response mechanism panel."
    )
    parser.add_argument("--m2807-dir", type=Path, default=DEFAULT_M2807_DIR)
    parser.add_argument("--m2810-dir", type=Path, default=DEFAULT_M2810_DIR)
    parser.add_argument("--m2812-synthesis", type=Path, default=DEFAULT_M2812_SYNTHESIS)
    parser.add_argument("--m2811-audit", type=Path, default=DEFAULT_M2811_AUDIT)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel(
        args.output_dir,
        m2807_dir=args.m2807_dir,
        m2810_dir=args.m2810_dir,
        m2812_synthesis=args.m2812_synthesis,
        m2811_audit=args.m2811_audit,
        route_plan=args.route_plan,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
