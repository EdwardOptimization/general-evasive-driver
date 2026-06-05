"""Materialize Route A post-cross-axis negative failure localization panel.

This runner reanalyzes existing M2753/M2755 artifacts only. It writes
row-level failure localization, outcome bucket, context, guardrail, actor,
claim, and gate artifacts. It does not execute environments, policies, replay,
validation, training, source builds, adapter probes, ranking, promotion, or
high-fidelity simulation.
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
    "m2756-engineering-controller-route-a-post-cross-axis-negative-failure-"
    "localization-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2757-engineering-controller-route-a-post-cross-axis-negative-failure-"
    "localization-panel-materialization-result-audit"
)
DEFAULT_M2753_DIR = Path("runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight")
DEFAULT_M2755_SYNTHESIS = Path(
    "docs/m2755-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-result-synthesis.md"
)
DEFAULT_M2754_AUDIT = Path(
    "docs/m2754-engineering-controller-route-a-cross-axis-stress-generalization-bounded-execution-result-audit.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2756-engineering-controller-route-a-post-cross-axis-negative-failure-"
    "localization-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2757-engineering-controller-route-a-post-cross-axis-negative-"
    "failure-localization-panel-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2756 Route A post-cross-axis negative failure-localization panel "
    "materialization only; existing M2753/M2755 artifacts are reanalyzed into "
    "row-level diagnostic context while no reset, step, rollout, replay, "
    "validation, training, PPO, source build, adapter probe, external simulation, "
    "ranking, winner selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, "
    "controller ranking, stress-axis ranking, source-edge ranking, task-family "
    "ranking, profile ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
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

LOCALIZATION_FIELDNAMES = [
    "localization_id",
    "candidate_id",
    "resolution_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "stress_axis_tags",
    "termination_reason",
    "outcome_bucket",
    "failure_family",
    "clearance_sign",
    "min_clearance_margin",
    "return",
    "success",
    "collision",
    "obstacle_completed",
    "candidate_admitted",
    "prior_panel_excluded",
    "localization_role",
    "diagnostic_only_no_verdict",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "protected_rows_in_success_denominator",
    "hidden_oracle_actor_input_required",
    "localization_labels_actor_visible",
    "stress_axis_labels_actor_visible",
    "source_edge_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "actor_visible_allowed",
    "claim_scope",
    "forbidden_interpretation",
]
OUTCOME_BUCKET_FIELDNAMES = [
    "bucket_id",
    "failure_family",
    "outcome_bucket",
    "row_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "negative_clearance_count",
    "positive_clearance_count",
    "min_clearance_margin_min",
    "min_clearance_margin_mean",
    "min_clearance_margin_max",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
STRESS_AXIS_FIELDNAMES = [
    "context_id",
    "stress_axis_tag",
    "candidate_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_rate_diagnostic",
    "collision_rate_diagnostic",
    "offtrack_rate_diagnostic",
    "clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "context_role",
    "actor_visible_allowed",
    "claim_scope",
]
SOURCE_EDGE_FIELDNAMES = [
    "context_id",
    "source_edge",
    "task_family_count",
    "stress_axis_tag_count",
    "row_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "collision_negative_clearance_count",
    "offtrack_positive_clearance_count",
    "min_clearance_margin_min",
    "min_clearance_margin_mean",
    "min_clearance_margin_max",
    "return_mean",
    "ranking_claim_made",
    "diagnostic_only_no_verdict",
    "context_role",
    "actor_visible_allowed",
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
    "allowed_in_m2756",
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

CLAIM_CHECKS = (
    ("failure_localization_panel_materialized", True, True, "M2756 localization artifacts"),
    ("outcome_bucket_context_materialized", True, True, "M2756 outcome-bucket rows"),
    ("stress_axis_context_materialized", True, True, "M2756 stress-axis context rows"),
    ("source_edge_context_materialized", True, True, "M2756 source-edge context rows"),
    ("guardrail_context_preserved", True, True, "M2756 guardrail context rows"),
    ("actor_contract_preserved", True, True, "M2756 actor guard rows"),
    ("follow_up_result_audit_registered", True, True, "M2757 result-audit manifest"),
    ("repair_success", False, False, "future repair result plus claim audit"),
    ("driver_performance", False, False, "future validation and claim audit"),
    ("validation_readiness", False, False, "future validation-readiness route decision"),
    ("validation_result", False, False, "future validation result"),
    ("controller_ranking", False, False, "future explicit ranking gate"),
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


def materialize_post_cross_axis_negative_failure_localization_panel(
    output_dir: Path | str,
    *,
    m2753_dir: Path | str = DEFAULT_M2753_DIR,
    m2755_synthesis: Path | str = DEFAULT_M2755_SYNTHESIS,
    m2754_audit: Path | str = DEFAULT_M2754_AUDIT,
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
        Path(m2753_dir),
        m2755_synthesis=Path(m2755_synthesis),
        m2754_audit=Path(m2754_audit),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )

    localization_rows = build_failure_localization_rows(source)
    outcome_rows = build_outcome_bucket_rows(localization_rows)
    stress_rows = build_stress_axis_context_rows(source)
    source_edge_rows = build_source_edge_context_rows(localization_rows)
    guardrail_rows = build_guardrail_context_rows(source)
    actor_rows = build_actor_contract_guard_rows(source, localization_rows, guardrail_rows)
    claim_rows = build_claim_boundary_rows()

    gate_rows = build_gate_matrix_rows(
        source,
        localization_rows,
        outcome_rows,
        stress_rows,
        source_edge_rows,
        guardrail_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_outputs(paths, localization_rows, outcome_rows, stress_rows, source_edge_rows, guardrail_rows, actor_rows, claim_rows, gate_rows)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        localization_rows=localization_rows,
        outcome_rows=outcome_rows,
        stress_rows=stress_rows,
        source_edge_rows=source_edge_rows,
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
        localization_rows,
        outcome_rows,
        stress_rows,
        source_edge_rows,
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
        localization_rows=localization_rows,
        outcome_rows=outcome_rows,
        stress_rows=stress_rows,
        source_edge_rows=source_edge_rows,
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
        "failure_localization_rows": output_dir / "failure_localization_rows.csv",
        "outcome_bucket_rows": output_dir / "outcome_bucket_rows.csv",
        "stress_axis_context_rows": output_dir / "stress_axis_context_rows.csv",
        "source_edge_context_rows": output_dir / "source_edge_context_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def write_outputs(
    paths: dict[str, Path],
    localization_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
    source_edge_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["failure_localization_rows"], localization_rows, fieldnames=LOCALIZATION_FIELDNAMES)
    write_csv_rows(paths["outcome_bucket_rows"], outcome_rows, fieldnames=OUTCOME_BUCKET_FIELDNAMES)
    write_csv_rows(paths["stress_axis_context_rows"], stress_rows, fieldnames=STRESS_AXIS_FIELDNAMES)
    write_csv_rows(paths["source_edge_context_rows"], source_edge_rows, fieldnames=SOURCE_EDGE_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def load_source_artifacts(
    m2753_dir: Path,
    *,
    m2755_synthesis: Path,
    m2754_audit: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2755_synthesis": m2755_synthesis,
        "m2754_audit": m2754_audit,
        "m2753_summary": m2753_dir / "summary.json",
        "m2753_cross_axis_candidate_rows": m2753_dir / "cross_axis_candidate_rows.csv",
        "m2753_candidate_execution_rows": m2753_dir / "candidate_execution_rows.csv",
        "m2753_stress_axis_aggregate_rows": m2753_dir / "stress_axis_aggregate_rows.csv",
        "m2753_prior_panel_exclusion_rows": m2753_dir / "prior_panel_exclusion_rows.csv",
        "m2753_blocker_guard_rows": m2753_dir / "blocker_guard_rows.csv",
        "m2753_actor_contract_guard_rows": m2753_dir / "actor_contract_guard_rows.csv",
        "m2753_claim_boundary_rows": m2753_dir / "claim_boundary_rows.csv",
        "m2753_gate_matrix": m2753_dir / "gate_matrix.csv",
        "route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2753_summary": read_json(paths["m2753_summary"]),
        "m2753_cross_axis_candidate_rows": _read_csv_rows(paths["m2753_cross_axis_candidate_rows"]),
        "m2753_candidate_execution_rows": _read_csv_rows(paths["m2753_candidate_execution_rows"]),
        "m2753_stress_axis_aggregate_rows": _read_csv_rows(paths["m2753_stress_axis_aggregate_rows"]),
        "m2753_prior_panel_exclusion_rows": _read_csv_rows(paths["m2753_prior_panel_exclusion_rows"]),
        "m2753_blocker_guard_rows": _read_csv_rows(paths["m2753_blocker_guard_rows"]),
        "m2753_actor_contract_guard_rows": _read_csv_rows(paths["m2753_actor_contract_guard_rows"]),
        "m2753_claim_boundary_rows": _read_csv_rows(paths["m2753_claim_boundary_rows"]),
        "m2753_gate_matrix": _read_csv_rows(paths["m2753_gate_matrix"]),
    }


def build_failure_localization_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = {row["candidate_id"]: row for row in source["m2753_cross_axis_candidate_rows"]}
    rows = []
    for idx, row in enumerate(source["m2753_candidate_execution_rows"], start=1):
        candidate = candidates.get(row.get("candidate_id", ""), {})
        margin = _float(row.get("min_clearance_margin"))
        rows.append(
            {
                "localization_id": f"m2756-localization-{idx:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "resolution_id": row.get("resolution_id", ""),
                "task_source_id": row.get("task_source_id", candidate.get("task_source_id", "")),
                "workload_id": row.get("workload_id", candidate.get("workload_id", "")),
                "profile_name": row.get("profile_name", candidate.get("profile_name", "")),
                "task_family": row.get("task_family", candidate.get("task_family", "")),
                "source_edge": row.get("source_edge", candidate.get("source_edge", "")),
                "stress_axis_primary": row.get("stress_axis_primary", candidate.get("stress_axis_primary", "")),
                "stress_axis_tags": row.get("stress_axis_tags", candidate.get("stress_axis_tags", "")),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "failure_family": classify_failure_family(row),
                "clearance_sign": classify_clearance_sign(margin),
                "min_clearance_margin": margin,
                "return": _float(row.get("return")),
                "success": _bool(row.get("success")),
                "collision": _bool(row.get("collision")),
                "obstacle_completed": _bool(row.get("obstacle_completed")),
                "candidate_admitted": _bool(candidate.get("candidate_admitted", True)),
                "prior_panel_excluded": _bool(candidate.get("prior_panel_excluded", False)),
                "localization_role": "negative_execution_row_failure_localization",
                "diagnostic_only_no_verdict": True,
                "ranking_run": False,
                "winner_selected": False,
                "checkpoint_promoted": False,
                "protected_rows_in_success_denominator": False,
                "hidden_oracle_actor_input_required": _bool(row.get("hidden_oracle_actor_input_required")),
                "localization_labels_actor_visible": False,
                "stress_axis_labels_actor_visible": _bool(row.get("stress_axis_labels_actor_visible")),
                "source_edge_labels_actor_visible": False,
                "success_progress_labels_actor_visible": _bool(row.get("success_progress_labels_actor_visible")),
                "verdict_labels_actor_visible": _bool(row.get("verdict_labels_actor_visible")),
                "actor_visible_allowed": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def classify_failure_family(row: dict[str, Any]) -> str:
    margin = _float(row.get("min_clearance_margin"))
    termination = str(row.get("termination_reason", ""))
    collision = _bool(row.get("collision")) or termination == "obstacle_collision"
    if _bool(row.get("success")):
        return "diagnostic_success_context"
    if collision:
        return "collision_negative_clearance" if margin is not None and margin < 0.0 else "collision_nonnegative_clearance"
    if termination == "off_track":
        return "offtrack_positive_clearance" if margin is not None and margin > 0.0 else "offtrack_nonpositive_clearance"
    return "unclassified_negative_context"


def classify_clearance_sign(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.0:
        return "negative"
    if value > 0.0:
        return "positive"
    return "zero"


def build_outcome_bucket_rows(localization_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in localization_rows:
        grouped[str(row["failure_family"])].append(row)
    rows = []
    for idx, (failure_family, group) in enumerate(sorted(grouped.items()), start=1):
        margins = [_float(row.get("min_clearance_margin")) for row in group]
        returns = [_float(row.get("return")) for row in group]
        rows.append(
            {
                "bucket_id": f"m2756-outcome-bucket-{idx:04d}",
                "failure_family": failure_family,
                "outcome_bucket": "|".join(sorted({str(row["outcome_bucket"]) for row in group})),
                "row_count": len(group),
                "success_count": sum(1 for row in group if _bool(row["success"])),
                "collision_count": sum(1 for row in group if _bool(row["collision"])),
                "offtrack_count": sum(1 for row in group if row["termination_reason"] == "off_track"),
                "negative_clearance_count": sum(1 for value in margins if value is not None and value < 0.0),
                "positive_clearance_count": sum(1 for value in margins if value is not None and value > 0.0),
                "min_clearance_margin_min": _min(margins),
                "min_clearance_margin_mean": _mean(margins),
                "min_clearance_margin_max": _max(margins),
                "return_mean": _mean(returns),
                "all_selected_metrics_finite": all(_finite(value) for value in [*margins, *returns]),
                "ranking_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_stress_axis_context_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(source["m2753_stress_axis_aggregate_rows"], start=1):
        rows.append(
            {
                "context_id": f"m2756-stress-axis-context-{idx:04d}",
                "stress_axis_tag": row.get("stress_axis_tag", ""),
                "candidate_count": _int(row.get("candidate_count")),
                "episode_count": _int(row.get("episode_count")),
                "failure_count": _int(row.get("failure_count")),
                "accounted_count": _int(row.get("accounted_count")),
                "success_rate_diagnostic": _float(row.get("success_rate_diagnostic")),
                "collision_rate_diagnostic": _float(row.get("collision_rate_diagnostic")),
                "offtrack_rate_diagnostic": _float(row.get("offtrack_rate_diagnostic")),
                "clearance_margin_mean": _float(row.get("clearance_margin_mean")),
                "return_mean": _float(row.get("return_mean")),
                "all_selected_metrics_finite": _bool(row.get("all_selected_metrics_finite")),
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "context_role": "stress_axis_context_only_nonranking",
                "actor_visible_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_source_edge_context_rows(localization_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in localization_rows:
        grouped[str(row["source_edge"])].append(row)
    rows = []
    for idx, (source_edge, group) in enumerate(sorted(grouped.items()), start=1):
        margins = [_float(row.get("min_clearance_margin")) for row in group]
        returns = [_float(row.get("return")) for row in group]
        rows.append(
            {
                "context_id": f"m2756-source-edge-context-{idx:04d}",
                "source_edge": source_edge,
                "task_family_count": len({row["task_family"] for row in group}),
                "stress_axis_tag_count": len({row["stress_axis_primary"] for row in group}),
                "row_count": len(group),
                "success_count": sum(1 for row in group if _bool(row["success"])),
                "collision_count": sum(1 for row in group if _bool(row["collision"])),
                "offtrack_count": sum(1 for row in group if row["termination_reason"] == "off_track"),
                "collision_negative_clearance_count": sum(
                    1 for row in group if row["failure_family"] == "collision_negative_clearance"
                ),
                "offtrack_positive_clearance_count": sum(
                    1 for row in group if row["failure_family"] == "offtrack_positive_clearance"
                ),
                "min_clearance_margin_min": _min(margins),
                "min_clearance_margin_mean": _mean(margins),
                "min_clearance_margin_max": _max(margins),
                "return_mean": _mean(returns),
                "ranking_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "context_role": "source_edge_context_only_nonranking",
                "actor_visible_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(source["m2753_prior_panel_exclusion_rows"], start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2756-guardrail-prior-panel-{idx:04d}",
                "guardrail_source": "prior_panel_exclusion",
                "guardrail_source_id": row.get("exclusion_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "blocker_id": "",
                "route": "Route A",
                "evidence_family": row.get("source_panel", "prior_panel"),
                "row_count": _int(row.get("row_count")),
                "blocking_count": 0,
                "execution_candidate": _bool(row.get("execution_candidate")),
                "execution_admitted": _bool(row.get("execution_admitted")),
                "execution_run": _bool(row.get("execution_run")),
                "ordinary_success_denominator_allowed": _bool(row.get("ordinary_success_denominator_allowed")),
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "diagnostic_only_no_verdict": True,
                "guardrail_role": "prior_panel_nonexecuted_guardrail_outside_denominator",
                "claim_scope": CLAIM_SCOPE,
            }
        )
    for idx, row in enumerate(source["m2753_blocker_guard_rows"], start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2756-guardrail-blocker-{idx:04d}",
                "guardrail_source": "blocker_guard",
                "guardrail_source_id": row.get("guard_id", ""),
                "task_source_id": "",
                "blocker_id": row.get("blocker_id", ""),
                "route": row.get("route", ""),
                "evidence_family": row.get("evidence_family", ""),
                "row_count": _int(row.get("blocking_count")),
                "blocking_count": _int(row.get("blocking_count")),
                "execution_candidate": _bool(row.get("execution_candidate")),
                "execution_admitted": _bool(row.get("execution_admitted")),
                "execution_run": _bool(row.get("execution_run")),
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": _bool(row.get("protected_rows_in_success_denominator")),
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "diagnostic_only_no_verdict": True,
                "guardrail_role": "protected_or_hf3_or_process_blocker_nonexecuted_guardrail",
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("m2756-actor-guard-observation-shape", "p0_observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("m2756-actor-guard-action-shape", "action_dim", ACTION_DIM, 3),
        actor_guard("m2756-actor-guard-m2753-rows-pass", "m2753_actor_guard_rows_pass", m2753_actor_rows_pass(source), True),
        actor_guard(
            "m2756-actor-guard-hidden-oracle",
            "hidden_oracle_actor_input_required",
            any(_bool(row["hidden_oracle_actor_input_required"]) for row in localization_rows),
            False,
        ),
        actor_guard(
            "m2756-actor-guard-actor-contract-changed",
            "actor_input_contract_changed",
            any(_bool(row.get("actor_input_contract_changed")) for row in source["m2753_candidate_execution_rows"]),
            False,
        ),
        actor_guard("m2756-actor-guard-localization-labels", "localization_labels_actor_visible", False, False),
        actor_guard(
            "m2756-actor-guard-stress-axis-labels",
            "stress_axis_labels_actor_visible",
            any(_bool(row["stress_axis_labels_actor_visible"]) for row in localization_rows),
            False,
        ),
        actor_guard("m2756-actor-guard-source-edge-labels", "source_edge_labels_actor_visible", False, False),
        actor_guard(
            "m2756-actor-guard-success-progress-labels",
            "success_progress_labels_actor_visible",
            any(_bool(row["success_progress_labels_actor_visible"]) for row in localization_rows),
            False,
        ),
        actor_guard(
            "m2756-actor-guard-verdict-labels",
            "verdict_labels_actor_visible",
            any(_bool(row["verdict_labels_actor_visible"]) for row in localization_rows),
            False,
        ),
        actor_guard(
            "m2756-actor-guard-protected-denominator",
            "protected_rows_in_success_denominator",
            any(_bool(row["protected_rows_in_success_denominator"]) for row in guardrail_rows),
            False,
        ),
        actor_guard(
            "m2756-actor-guard-guardrail-actor-visible",
            "guardrail_actor_visible_allowed",
            any(_bool(row["actor_visible_allowed"]) for row in guardrail_rows),
            False,
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2756-claim-{claim_family}",
            "claim_family": claim_family,
            "allowed_in_m2756": allowed,
            "claim_made": claim_made,
            "status_pass": allowed == claim_made,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_family, allowed, claim_made, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
    source_edge_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    counts = count_localization_outcomes(localization_rows)
    prior_guard_count = sum(1 for row in guardrail_rows if row["guardrail_source"] == "prior_panel_exclusion")
    blocker_guard_count = sum(1 for row in guardrail_rows if row["guardrail_source"] == "blocker_guard")
    guardrails_executed = any(_bool(row["execution_run"]) for row in guardrail_rows)
    guardrails_in_denominator = any(
        _bool(row["ordinary_success_denominator_allowed"]) or _bool(row["protected_rows_in_success_denominator"])
        for row in guardrail_rows
    )
    actor_visible = any(_bool(row["actor_visible_allowed"]) for row in guardrail_rows)
    return [
        gate_row("m2756-gate-source-artifacts-present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2756-gate-required-artifacts-present", "artifact", required_artifacts_present, True),
        gate_row("m2756-gate-m2753-status-pass", "lineage", _bool(source["m2753_summary"].get("status_pass")), True),
        gate_row("m2756-gate-m2753-gate-matrix-pass", "lineage", m2753_gate_rows_pass(source), True),
        gate_row("m2756-gate-execution-row-count", "diagnostic_accounting", len(localization_rows), 12),
        gate_row("m2756-gate-diagnostic-success-count", "diagnostic_accounting", counts["success_count"], 0),
        gate_row("m2756-gate-collision-negative-clearance-count", "diagnostic_accounting", counts["collision_negative_clearance_count"], 3),
        gate_row("m2756-gate-offtrack-positive-clearance-count", "diagnostic_accounting", counts["offtrack_positive_clearance_count"], 9),
        gate_row("m2756-gate-outcome-bucket-rows", "artifact", len(outcome_rows), 2),
        gate_row("m2756-gate-stress-axis-context-rows", "artifact", len(stress_rows), 4),
        gate_row("m2756-gate-source-edge-context-rows", "artifact", len(source_edge_rows) > 0, True),
        gate_row("m2756-gate-prior-panel-guardrail-rows", "guardrail", prior_guard_count, 25),
        gate_row("m2756-gate-blocker-guardrail-rows", "guardrail", blocker_guard_count, 6),
        gate_row("m2756-gate-guardrail-context-rows", "guardrail", len(guardrail_rows), 31),
        gate_row("m2756-gate-guardrails-not-executed", "guardrail", guardrails_executed, False),
        gate_row("m2756-gate-guardrails-outside-denominator", "guardrail", guardrails_in_denominator, False),
        gate_row("m2756-gate-guardrail-labels-actor-invisible", "actor_contract", actor_visible, False),
        gate_row("m2756-gate-actor-contract-72-action-3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2756-gate-hidden-oracle-actor-input-absent", "actor_contract", hidden_oracle_actor_input_detected(source), False),
        gate_row("m2756-gate-actor-guard-rows-pass", "actor_contract", all(_bool(row["status_pass"]) for row in actor_rows), True),
        gate_row("m2756-gate-follow-up-result-audit-registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row("m2756-gate-claim-boundary-pass", "claim_boundary", claim_boundary_pass(claim_rows), True),
        gate_row("m2756-gate-no-reset-rollout-training-validation", "claim_boundary", False, False),
        gate_row("m2756-gate-no-ranking-promotion-performance", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    localization_rows: list[dict[str, Any]],
    outcome_rows: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
    source_edge_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    counts = count_localization_outcomes(localization_rows)
    prior_guard_count = sum(1 for row in guardrail_rows if row["guardrail_source"] == "prior_panel_exclusion")
    blocker_guard_count = sum(1 for row in guardrail_rows if row["guardrail_source"] == "blocker_guard")
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
        and _bool(source["m2753_summary"].get("status_pass"))
        and m2753_gate_rows_pass(source)
        and len(localization_rows) == 12
        and counts["success_count"] == 0
        and counts["collision_negative_clearance_count"] == 3
        and counts["offtrack_positive_clearance_count"] == 9
        and len(outcome_rows) == 2
        and len(stress_rows) == 4
        and len(source_edge_rows) > 0
        and prior_guard_count == 25
        and blocker_guard_count == 6
        and len(guardrail_rows) == 31
        and not guardrails_executed
        and not guardrails_in_denominator
        and actor_ok
        and not hidden
        and all(_bool(row["status_pass"]) for row in actor_rows)
        and claim_boundary_pass(claim_rows)
        and gate_matrix_pass
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_cross_axis_failure_localization_v0",
        "result_class": "engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "failure_localization_rows": str(paths["failure_localization_rows"]),
        "outcome_bucket_rows": str(paths["outcome_bucket_rows"]),
        "stress_axis_context_rows": str(paths["stress_axis_context_rows"]),
        "source_edge_context_rows": str(paths["source_edge_context_rows"]),
        "guardrail_context_rows": str(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "source_artifacts_reanalyzed_only": True,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "failure_localization_row_count": len(localization_rows),
        "outcome_bucket_row_count": len(outcome_rows),
        "stress_axis_context_row_count": len(stress_rows),
        "source_edge_context_row_count": len(source_edge_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "prior_panel_guardrail_row_count": prior_guard_count,
        "blocker_guardrail_row_count": blocker_guard_count,
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "diagnostic_success_count": counts["success_count"],
        "diagnostic_collision_count": counts["collision_count"],
        "diagnostic_offtrack_count": counts["offtrack_count"],
        "collision_negative_clearance_count": counts["collision_negative_clearance_count"],
        "offtrack_positive_clearance_count": counts["offtrack_positive_clearance_count"],
        "all_localization_rows_accounted": len(localization_rows) == counts["row_count"],
        "guardrails_not_executed": not guardrails_executed,
        "protected_rows_in_success_denominator": guardrails_in_denominator,
        "actor_contract_shape_72_action_3": actor_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden,
        "localization_labels_actor_visible": False,
        "stress_axis_labels_actor_visible": any(_bool(row["stress_axis_labels_actor_visible"]) for row in localization_rows),
        "source_edge_labels_actor_visible": False,
        "success_progress_labels_actor_visible": any(
            _bool(row["success_progress_labels_actor_visible"]) for row in localization_rows
        ),
        "verdict_labels_actor_visible": any(_bool(row["verdict_labels_actor_visible"]) for row in localization_rows),
        "selected_next_action": "m2757_post_cross_axis_negative_failure_localization_panel_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2756 Engineering Controller Route A Post-Cross-Axis Negative Failure Localization Panel Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- failure localization rows: `{summary['failure_localization_rows']}`",
            f"- outcome bucket rows: `{summary['outcome_bucket_rows']}`",
            f"- stress-axis context rows: `{summary['stress_axis_context_rows']}`",
            f"- source-edge context rows: `{summary['source_edge_context_rows']}`",
            f"- guardrail context rows: `{summary['guardrail_context_rows']}`",
            f"- actor contract guard rows: `{summary['actor_contract_guard_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Localized Negative Rows",
            "",
            f"- execution rows localized: {summary['failure_localization_row_count']}",
            f"- diagnostic success rows: {summary['diagnostic_success_count']}",
            f"- collision rows: {summary['diagnostic_collision_count']}",
            f"- offtrack rows: {summary['diagnostic_offtrack_count']}",
            f"- collision negative-clearance rows: {summary['collision_negative_clearance_count']}",
            f"- offtrack positive-clearance rows: {summary['offtrack_positive_clearance_count']}",
            f"- outcome bucket rows: {summary['outcome_bucket_row_count']}",
            "",
            "## Context And Guardrails",
            "",
            f"- stress-axis context rows: {summary['stress_axis_context_row_count']}",
            f"- source-edge context rows: {summary['source_edge_context_row_count']}",
            f"- prior-panel guardrail rows: {summary['prior_panel_guardrail_row_count']}",
            f"- blocker guardrail rows: {summary['blocker_guardrail_row_count']}",
            f"- guardrails not executed: `{str(summary['guardrails_not_executed']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- localization, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2756 is no-rollout materialization from existing artifacts only. It performs no reset, step, policy action, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
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


def count_localization_outcomes(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "success_count": sum(1 for row in rows if _bool(row.get("success"))),
        "collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
        "offtrack_count": sum(1 for row in rows if row.get("termination_reason") == "off_track"),
        "collision_negative_clearance_count": sum(
            1 for row in rows if row.get("failure_family") == "collision_negative_clearance"
        ),
        "offtrack_positive_clearance_count": sum(
            1 for row in rows if row.get("failure_family") == "offtrack_positive_clearance"
        ),
    }


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    return (
        P0_OBSERVATION_DIM == 72
        and ACTION_DIM == 3
        and m2753_actor_rows_pass(source)
        and not hidden_oracle_actor_input_detected(source)
        and not any(_bool(row.get("actor_input_contract_changed")) for row in source["m2753_candidate_execution_rows"])
    )


def m2753_actor_rows_pass(source: dict[str, Any]) -> bool:
    return bool(source["m2753_actor_contract_guard_rows"]) and all(
        _bool(row.get("status_pass")) for row in source["m2753_actor_contract_guard_rows"]
    )


def m2753_gate_rows_pass(source: dict[str, Any]) -> bool:
    return bool(source["m2753_gate_matrix"]) and all(_bool(row.get("status_pass")) for row in source["m2753_gate_matrix"])


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    summary_hidden = any(
        _bool(source["m2753_summary"].get(key))
        for key in ("hidden_oracle_actor_input_detected", "hidden_oracle_actor_input_required")
    )
    row_hidden = any(_bool(row.get("hidden_oracle_actor_input_required")) for row in source["m2753_candidate_execution_rows"])
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


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _mean(values: list[float | None]) -> float | None:
    finite = [value for value in values if _finite(value)]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _min(values: list[float | None]) -> float | None:
    finite = [value for value in values if _finite(value)]
    return min(finite) if finite else None


def _max(values: list[float | None]) -> float | None:
    finite = [value for value in values if _finite(value)]
    return max(finite) if finite else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A post-cross-axis negative failure localization panel."
    )
    parser.add_argument("--m2753-dir", type=Path, default=DEFAULT_M2753_DIR)
    parser.add_argument("--m2755-synthesis", type=Path, default=DEFAULT_M2755_SYNTHESIS)
    parser.add_argument("--m2754-audit", type=Path, default=DEFAULT_M2754_AUDIT)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_post_cross_axis_negative_failure_localization_panel(
        args.output_dir,
        m2753_dir=args.m2753_dir,
        m2755_synthesis=args.m2755_synthesis,
        m2754_audit=args.m2754_audit,
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
