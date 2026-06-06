"""Materialize M2934 offtrack repair outcome-shift localization rows.

M2934 consumes the accepted M2931 fixed-candidate repair diagnostics and the
M2919 baseline panel. It performs no environment or policy execution. Its only
job is to make the M2919-to-M2931 row-level outcome shifts auditable before any
new repair design, training, validation, ranking, or promotion.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-"
    "outcome-shift-localization-preflight"
)
NEXT_ID = (
    "m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-"
    "outcome-shift-localization-result-audit"
)
DEFAULT_M2919_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2925_DIR = Path(
    "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight"
)
DEFAULT_M2928_DIR = Path(
    "runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight"
)
DEFAULT_M2931_DIR = Path(
    "runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight"
)
DEFAULT_M2932_AUDIT = Path(
    "docs/m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit.md"
)
DEFAULT_M2933_SYNTHESIS = Path(
    "docs/m2933-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.json"
)

EXPECTED_PANEL_ROW_COUNT = 56
EXPECTED_OFFTRACK_TARGET_COUNT = 38
EXPECTED_CONTEXT_ROW_COUNT = 18
EXPECTED_COVERAGE_CONSTRAINT_COUNT = 27
EXPECTED_SHORTCUT_EXCLUSION_COUNT = 7
EXPECTED_M2919_OUTCOME_COUNTS = {
    "success": 11,
    "collision": 3,
    "offtrack": 38,
    "speed_too_low": 4,
}
EXPECTED_M2931_OUTCOME_COUNTS = {
    "success": 6,
    "collision": 9,
    "offtrack": 31,
    "speed_too_low": 10,
}
EXPECTED_M2931_DIAGNOSTIC_COUNTS = {
    "success": 6,
    "collision": 9,
    "offtrack": 32,
    "speed_too_low": 10,
}
EXPECTED_TRANSITION_COUNTS = {
    "collision->collision": 1,
    "collision->offtrack": 1,
    "collision->speed_too_low": 1,
    "offtrack->collision": 4,
    "offtrack->offtrack": 24,
    "offtrack->speed_too_low": 6,
    "offtrack->success": 4,
    "speed_too_low->offtrack": 1,
    "speed_too_low->speed_too_low": 3,
    "success->collision": 4,
    "success->offtrack": 5,
    "success->success": 2,
}
EXPECTED_PANEL_SOURCE_COUNTS = {"m2737": 18, "m2746": 14, "m2807": 12, "m2816": 12}
EXPECTED_PANEL_TASK_COUNTS = {"T4": 31, "T5": 25}

CLAIM_SCOPE = (
    "M2934 Route A offtrack-dominant outcome-shift localization only; already "
    "recorded M2919 and M2931 diagnostic rows may be joined into row-level "
    "transition, offtrack-target, context, source, task, coverage, guard, actor, "
    "claim, and gate artifacts. No reset, step, rollout, replay, validation, "
    "training, PPO, dependency work, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

OUTCOME_SHIFT_FIELDNAMES = [
    "outcome_shift_id",
    "panel_row_id",
    "panel_row_family",
    "source_milestone",
    "source_family",
    "source_edge",
    "source_row_id",
    "task_family",
    "task_source_id",
    "workload_id",
    "profile_name",
    "env_template_family",
    "window_tag",
    "checkpoint_context",
    "m2919_execution_candidate_id",
    "m2931_repair_execution_candidate_id",
    "m2919_outcome_family",
    "m2931_outcome_family",
    "transition_bucket",
    "transition_family",
    "m2919_termination_reason",
    "m2931_termination_reason",
    "m2919_success",
    "m2931_success",
    "m2919_collision",
    "m2931_collision",
    "m2919_min_clearance_margin",
    "m2931_min_clearance_margin",
    "min_clearance_margin_delta",
    "m2919_return",
    "m2931_return",
    "return_delta",
    "m2919_speed_mean",
    "m2931_speed_mean",
    "speed_mean_delta",
    "offtrack_repair_target",
    "offtrack_repaired_to_success",
    "offtrack_persisted",
    "offtrack_regressed_to_collision_or_speed",
    "context_row",
    "context_preserved_success",
    "context_regressed_from_success",
    "context_regressed_to_offtrack_or_collision",
    "execution_performed_by_m2934",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "repair_success_claim_made",
    "driver_performance_claim_made",
    "diagnostic_only_no_verdict",
    "actor_visible",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "aggregate_value",
    "row_count",
    "offtrack_target_row_count",
    "context_row_count",
    "baseline_success_count",
    "baseline_collision_count",
    "baseline_offtrack_count",
    "baseline_speed_too_low_count",
    "repair_success_count",
    "repair_collision_count",
    "repair_offtrack_count",
    "repair_speed_too_low_count",
    "offtrack_to_success_count",
    "offtrack_to_offtrack_count",
    "offtrack_to_collision_count",
    "offtrack_to_speed_too_low_count",
    "success_to_success_count",
    "success_to_offtrack_count",
    "success_to_collision_count",
    "collision_to_collision_count",
    "collision_to_offtrack_count",
    "collision_to_speed_too_low_count",
    "speed_too_low_to_speed_too_low_count",
    "speed_too_low_to_offtrack_count",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
COVERAGE_AUDIT_FIELDNAMES = [
    "coverage_audit_id",
    "coverage_constraint_id",
    "coverage_family",
    "coverage_value",
    "observed_row_count",
    "expected_row_count",
    "source_scope",
    "coverage_constraint_status_pass",
    "ranking_claim_made",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "m2934_audit_status_pass",
    "transition_localization_preserved",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_context_id",
    "guardrail_source",
    "guardrail_family",
    "source_milestone",
    "source_row_id",
    "guardrail_reason",
    "row_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2934",
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
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "outcome_shift_rows",
    "offtrack_target_shift_rows",
    "context_regression_rows",
    "source_milestone_transition_aggregate",
    "task_family_transition_aggregate",
    "coverage_constraint_audit_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_outcome_shift_localization_preflight(
    *,
    m2919_dir: Path | str = DEFAULT_M2919_DIR,
    m2925_dir: Path | str = DEFAULT_M2925_DIR,
    m2928_dir: Path | str = DEFAULT_M2928_DIR,
    m2931_dir: Path | str = DEFAULT_M2931_DIR,
    m2932_audit: Path | str = DEFAULT_M2932_AUDIT,
    m2933_synthesis: Path | str = DEFAULT_M2933_SYNTHESIS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2919_dir=Path(m2919_dir),
        m2925_dir=Path(m2925_dir),
        m2928_dir=Path(m2928_dir),
        m2931_dir=Path(m2931_dir),
        m2932_audit=Path(m2932_audit),
        m2933_synthesis=Path(m2933_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )

    shift_rows = build_outcome_shift_rows(source)
    offtrack_rows = [row for row in shift_rows if _bool(row["offtrack_repair_target"])]
    context_rows = [row for row in shift_rows if _bool(row["context_row"])]
    source_rows = build_aggregate_rows(shift_rows, aggregate_family="source_milestone", key="source_milestone")
    task_rows = build_aggregate_rows(shift_rows, aggregate_family="task_family", key="task_family")
    coverage_rows = build_coverage_constraint_audit_rows(source["coverage_constraint_rows"])
    guardrail_rows = build_guardrail_context_rows(source["guardrail_context_rows"])

    write_csv_rows(paths["outcome_shift_rows"], shift_rows, fieldnames=OUTCOME_SHIFT_FIELDNAMES)
    write_csv_rows(paths["offtrack_target_shift_rows"], offtrack_rows, fieldnames=OUTCOME_SHIFT_FIELDNAMES)
    write_csv_rows(paths["context_regression_rows"], context_rows, fieldnames=OUTCOME_SHIFT_FIELDNAMES)
    write_csv_rows(paths["source_milestone_transition_aggregate"], source_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["task_family_transition_aggregate"], task_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["coverage_constraint_audit_rows"], coverage_rows, fieldnames=COVERAGE_AUDIT_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "outcome_shift_row_count": len(shift_rows),
            "offtrack_target_shift_row_count": len(offtrack_rows),
            "context_regression_row_count": len(context_rows),
            "coverage_constraint_audit_row_count": len(coverage_rows),
            "source_milestone_transition_aggregate_row_count": len(source_rows),
            "task_family_transition_aggregate_row_count": len(task_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        shift_rows=shift_rows,
        coverage_rows=coverage_rows,
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        shift_rows_present=bool(shift_rows),
        offtrack_rows_present=bool(offtrack_rows),
        context_rows_present=bool(context_rows),
        coverage_rows_present=bool(coverage_rows),
        guardrails_preserved=guardrails_preserved(guardrail_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        shift_rows=shift_rows,
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        coverage_rows=coverage_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, actor_rows, claim_rows, gate_rows)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        shift_rows=shift_rows,
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        coverage_rows=coverage_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        shift_rows_present=bool(shift_rows),
        offtrack_rows_present=bool(offtrack_rows),
        context_rows_present=bool(context_rows),
        coverage_rows_present=bool(coverage_rows),
        guardrails_preserved=guardrails_preserved(guardrail_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        shift_rows=shift_rows,
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        coverage_rows=coverage_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        shift_rows=shift_rows,
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        coverage_rows=coverage_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "outcome_shift_row_count": len(shift_rows),
            "offtrack_target_shift_row_count": len(offtrack_rows),
            "context_regression_row_count": len(context_rows),
            "source_milestone_transition_aggregate_row_count": len(source_rows),
            "task_family_transition_aggregate_row_count": len(task_rows),
            "coverage_constraint_audit_row_count": len(coverage_rows),
            "guardrail_context_row_count": len(guardrail_rows),
            "actor_contract_guard_row_count": len(actor_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "execution_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "outcome_shift_rows": output_dir / "outcome_shift_rows.csv",
        "offtrack_target_shift_rows": output_dir / "offtrack_target_shift_rows.csv",
        "context_regression_rows": output_dir / "context_regression_rows.csv",
        "source_milestone_transition_aggregate": output_dir / "source_milestone_transition_aggregate.csv",
        "task_family_transition_aggregate": output_dir / "task_family_transition_aggregate.csv",
        "coverage_constraint_audit_rows": output_dir / "coverage_constraint_audit_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2919_dir: Path,
    m2925_dir: Path,
    m2928_dir: Path,
    m2931_dir: Path,
    m2932_audit: Path,
    m2933_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2932_audit": m2932_audit,
        "m2933_synthesis": m2933_synthesis,
        "m2919_summary": m2919_dir / "summary.json",
        "m2919_bounded_execution_rows": m2919_dir / "bounded_execution_rows.csv",
        "m2925_summary": m2925_dir / "summary.json",
        "offtrack_slice_rows": m2925_dir / "offtrack_slice_rows.csv",
        "non_offtrack_context_rows": m2925_dir / "non_offtrack_context_rows.csv",
        "m2928_summary": m2928_dir / "summary.json",
        "coverage_constraint_rows": m2928_dir / "coverage_constraint_rows.csv",
        "shortcut_exclusion_rows": m2928_dir / "shortcut_exclusion_rows.csv",
        "m2931_summary": m2931_dir / "summary.json",
        "repair_execution_candidate_rows": m2931_dir / "repair_execution_candidate_rows.csv",
        "repair_execution_rows": m2931_dir / "repair_execution_rows.csv",
        "repair_execution_failure_rows": m2931_dir / "repair_execution_failure_rows.csv",
        "repair_target_context_rows": m2931_dir / "repair_target_context_rows.csv",
        "guardrail_context_rows": m2931_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": m2931_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2931_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2931_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2932_audit_text": paths["m2932_audit"].read_text(encoding="utf-8")
        if source_exists["m2932_audit"]
        else "",
        "m2933_synthesis_text": paths["m2933_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2933_synthesis"]
        else "",
        "m2919_summary": read_json(paths["m2919_summary"]) if source_exists["m2919_summary"] else {},
        "m2925_summary": read_json(paths["m2925_summary"]) if source_exists["m2925_summary"] else {},
        "m2928_summary": read_json(paths["m2928_summary"]) if source_exists["m2928_summary"] else {},
        "m2931_summary": read_json(paths["m2931_summary"]) if source_exists["m2931_summary"] else {},
        "m2919_bounded_execution_rows": read_csv_rows(paths["m2919_bounded_execution_rows"]),
        "offtrack_slice_rows": read_csv_rows(paths["offtrack_slice_rows"]),
        "non_offtrack_context_rows": read_csv_rows(paths["non_offtrack_context_rows"]),
        "coverage_constraint_rows": read_csv_rows(paths["coverage_constraint_rows"]),
        "shortcut_exclusion_rows": read_csv_rows(paths["shortcut_exclusion_rows"]),
        "repair_execution_candidate_rows": read_csv_rows(paths["repair_execution_candidate_rows"]),
        "repair_execution_rows": read_csv_rows(paths["repair_execution_rows"]),
        "repair_execution_failure_rows": read_csv_rows(paths["repair_execution_failure_rows"]),
        "repair_target_context_rows": read_csv_rows(paths["repair_target_context_rows"]),
        "guardrail_context_rows": read_csv_rows(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def build_outcome_shift_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    baseline_by_candidate = {
        str(row.get("execution_candidate_id", "")): row for row in source["m2919_bounded_execution_rows"]
    }
    repair_by_candidate = {
        str(row.get("repair_execution_candidate_id", "")): row for row in source["repair_execution_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(source["repair_execution_candidate_rows"], start=1):
        baseline = baseline_by_candidate.get(str(candidate.get("m2919_execution_candidate_id", "")), {})
        repair = repair_by_candidate.get(str(candidate.get("repair_execution_candidate_id", "")), {})
        baseline_outcome = outcome_label(baseline)
        repair_outcome = outcome_label(repair)
        transition = f"{baseline_outcome}->{repair_outcome}"
        panel_family = str(candidate.get("panel_row_family", ""))
        offtrack_target = panel_family == "offtrack_repair_target"
        context_row = not offtrack_target
        row = {
            "outcome_shift_id": f"m2934-outcome-shift-{index:04d}",
            "panel_row_id": candidate.get("panel_row_id", ""),
            "panel_row_family": panel_family,
            "source_milestone": candidate.get("source_milestone", ""),
            "source_family": candidate.get("source_family", ""),
            "source_edge": candidate.get("source_edge", ""),
            "source_row_id": candidate.get("source_row_id", ""),
            "task_family": candidate.get("task_family", ""),
            "task_source_id": candidate.get("task_source_id", ""),
            "workload_id": candidate.get("workload_id", ""),
            "profile_name": candidate.get("profile_name", ""),
            "env_template_family": candidate.get("env_template_family", ""),
            "window_tag": candidate.get("window_tag", ""),
            "checkpoint_context": candidate.get("original_checkpoint_context", ""),
            "m2919_execution_candidate_id": candidate.get("m2919_execution_candidate_id", ""),
            "m2931_repair_execution_candidate_id": candidate.get("repair_execution_candidate_id", ""),
            "m2919_outcome_family": baseline_outcome,
            "m2931_outcome_family": repair_outcome,
            "transition_bucket": transition,
            "transition_family": transition_family(
                baseline_outcome=baseline_outcome,
                repair_outcome=repair_outcome,
                offtrack_target=offtrack_target,
            ),
            "m2919_termination_reason": baseline.get("termination_reason", ""),
            "m2931_termination_reason": repair.get("termination_reason", ""),
            "m2919_success": _bool(baseline.get("success", False)),
            "m2931_success": _bool(repair.get("success", False)),
            "m2919_collision": _bool(baseline.get("collision", False)),
            "m2931_collision": _bool(repair.get("collision", False)),
            "m2919_min_clearance_margin": _float_or_blank(baseline.get("min_clearance_margin")),
            "m2931_min_clearance_margin": _float_or_blank(repair.get("min_clearance_margin")),
            "min_clearance_margin_delta": delta_float(
                repair.get("min_clearance_margin"), baseline.get("min_clearance_margin")
            ),
            "m2919_return": _float_or_blank(baseline.get("return")),
            "m2931_return": _float_or_blank(repair.get("return")),
            "return_delta": delta_float(repair.get("return"), baseline.get("return")),
            "m2919_speed_mean": _float_or_blank(baseline.get("speed_mean")),
            "m2931_speed_mean": _float_or_blank(repair.get("speed_mean")),
            "speed_mean_delta": delta_float(repair.get("speed_mean"), baseline.get("speed_mean")),
            "offtrack_repair_target": offtrack_target,
            "offtrack_repaired_to_success": offtrack_target and repair_outcome == "success",
            "offtrack_persisted": offtrack_target and repair_outcome == "offtrack",
            "offtrack_regressed_to_collision_or_speed": offtrack_target
            and repair_outcome in {"collision", "speed_too_low"},
            "context_row": context_row,
            "context_preserved_success": context_row and baseline_outcome == "success" and repair_outcome == "success",
            "context_regressed_from_success": context_row
            and baseline_outcome == "success"
            and repair_outcome != "success",
            "context_regressed_to_offtrack_or_collision": context_row
            and baseline_outcome == "success"
            and repair_outcome in {"offtrack", "collision"},
            "execution_performed_by_m2934": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "ranking_claim_made": False,
            "success_rate_verdict_claim_made": False,
            "repair_success_claim_made": False,
            "driver_performance_claim_made": False,
            "diagnostic_only_no_verdict": True,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
    return rows


def outcome_label(row: Mapping[str, Any]) -> str:
    termination = str(row.get("termination_reason", "")).strip()
    if _bool(row.get("success", False)):
        return "success"
    if _bool(row.get("collision", False)) or termination == "obstacle_collision":
        return "collision"
    if termination == "off_track":
        return "offtrack"
    if termination == "speed_too_low":
        return "speed_too_low"
    return "other"


def transition_family(*, baseline_outcome: str, repair_outcome: str, offtrack_target: bool) -> str:
    if offtrack_target and repair_outcome == "success":
        return "offtrack_target_repaired_to_success"
    if offtrack_target and repair_outcome == "offtrack":
        return "offtrack_target_persistent_offtrack"
    if offtrack_target and repair_outcome in {"collision", "speed_too_low"}:
        return "offtrack_target_shifted_to_collision_or_speed"
    if offtrack_target:
        return "offtrack_target_other_shift"
    if baseline_outcome == "success" and repair_outcome == "success":
        return "context_success_preserved"
    if baseline_outcome == "success" and repair_outcome in {"offtrack", "collision"}:
        return "context_success_regressed_to_offtrack_or_collision"
    if baseline_outcome == repair_outcome:
        return "context_non_success_preserved"
    return "context_non_success_shifted"


def build_aggregate_rows(
    shift_rows: list[dict[str, Any]], *, aggregate_family: str, key: str
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in shift_rows:
        grouped[str(row.get(key, ""))].append(row)
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(sorted(value for value in grouped if value), start=1):
        rows.append(aggregate_row(index, aggregate_family, value, grouped[value]))
    return rows


def aggregate_row(index: int, aggregate_family: str, value: str, group: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_counts = Counter(str(row.get("m2919_outcome_family", "")) for row in group)
    repair_counts = Counter(str(row.get("m2931_outcome_family", "")) for row in group)
    transition_counts = Counter(str(row.get("transition_bucket", "")) for row in group)
    return {
        "aggregate_id": f"m2934-{aggregate_family}-transition-aggregate-{index:04d}",
        "aggregate_family": aggregate_family,
        "aggregate_value": value,
        "row_count": len(group),
        "offtrack_target_row_count": sum(_bool(row.get("offtrack_repair_target", False)) for row in group),
        "context_row_count": sum(_bool(row.get("context_row", False)) for row in group),
        "baseline_success_count": baseline_counts.get("success", 0),
        "baseline_collision_count": baseline_counts.get("collision", 0),
        "baseline_offtrack_count": baseline_counts.get("offtrack", 0),
        "baseline_speed_too_low_count": baseline_counts.get("speed_too_low", 0),
        "repair_success_count": repair_counts.get("success", 0),
        "repair_collision_count": repair_counts.get("collision", 0),
        "repair_offtrack_count": repair_counts.get("offtrack", 0),
        "repair_speed_too_low_count": repair_counts.get("speed_too_low", 0),
        "offtrack_to_success_count": transition_counts.get("offtrack->success", 0),
        "offtrack_to_offtrack_count": transition_counts.get("offtrack->offtrack", 0),
        "offtrack_to_collision_count": transition_counts.get("offtrack->collision", 0),
        "offtrack_to_speed_too_low_count": transition_counts.get("offtrack->speed_too_low", 0),
        "success_to_success_count": transition_counts.get("success->success", 0),
        "success_to_offtrack_count": transition_counts.get("success->offtrack", 0),
        "success_to_collision_count": transition_counts.get("success->collision", 0),
        "collision_to_collision_count": transition_counts.get("collision->collision", 0),
        "collision_to_offtrack_count": transition_counts.get("collision->offtrack", 0),
        "collision_to_speed_too_low_count": transition_counts.get("collision->speed_too_low", 0),
        "speed_too_low_to_speed_too_low_count": transition_counts.get("speed_too_low->speed_too_low", 0),
        "speed_too_low_to_offtrack_count": transition_counts.get("speed_too_low->offtrack", 0),
        "ranking_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_coverage_constraint_audit_rows(coverage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(coverage_rows, start=1):
        status_pass = _bool(row.get("coverage_constraint_status_pass", False))
        rows.append(
            {
                "coverage_audit_id": f"m2934-coverage-audit-{index:04d}",
                "coverage_constraint_id": row.get("coverage_constraint_id", ""),
                "coverage_family": row.get("coverage_family", ""),
                "coverage_value": row.get("coverage_value", ""),
                "observed_row_count": row.get("observed_row_count", ""),
                "expected_row_count": row.get("expected_row_count", ""),
                "source_scope": row.get("source_scope", ""),
                "coverage_constraint_status_pass": status_pass,
                "ranking_claim_made": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "m2934_audit_status_pass": status_pass,
                "transition_localization_preserved": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2934-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": row.get("row_count", 1),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    shift_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = shift_rows + coverage_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("m2934_execution_performed", any_flag(shift_rows, "execution_performed_by_m2934"), False),
        actor_guard("validation_denominator_allowed", any_flag(combined, "validation_denominator_allowed"), False),
        actor_guard("paper_denominator_allowed", any_flag(combined, "paper_denominator_allowed"), False),
        actor_guard("ranking_claim_made", any_flag(combined, "ranking_claim_made"), False),
        actor_guard("repair_success_claim_made", any_flag(combined, "repair_success_claim_made"), False),
        actor_guard("driver_performance_claim_made", any_flag(combined, "driver_performance_claim_made"), False),
        actor_guard("actor_visible_rows", any_flag(combined, "actor_visible"), False),
        actor_guard("guardrail_execution", any_flag(guardrail_rows, "execution_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2934-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    shift_rows_present: bool,
    offtrack_rows_present: bool,
    context_rows_present: bool,
    coverage_rows_present: bool,
    guardrails_preserved: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("outcome_shift_rows_materialized", "artifact", shift_rows_present, "outcome_shift_rows.csv"),
        ("offtrack_target_shift_rows_materialized", "artifact", offtrack_rows_present, "offtrack_target_shift_rows.csv"),
        ("context_shift_rows_materialized", "artifact", context_rows_present, "context_regression_rows.csv"),
        ("transition_aggregates_materialized", "artifact", artifacts_present, "source/task aggregate rows"),
        ("coverage_constraint_audit_materialized", "artifact", coverage_rows_present, "coverage_constraint_audit_rows.csv"),
        ("guardrail_context_preserved", "guardrail", guardrails_preserved, "M2877 Route B Route C guardrails"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_doc_materialized", "artifact", artifacts_present, "summary.json and milestone doc"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2935 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_replay", "execution", "future bounded execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("dependency_execution", "execution", "future dependency route"),
        ("source_task_checkpoint_band_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2934_{claim_id}",
        "claim_family": family,
        "allowed_in_m2934": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    shift_rows: list[dict[str, Any]],
    offtrack_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m2919_outcomes = Counter(str(row.get("m2919_outcome_family", "")) for row in shift_rows)
    m2931_outcomes = Counter(str(row.get("m2931_outcome_family", "")) for row in shift_rows)
    transition_counts = Counter(str(row.get("transition_bucket", "")) for row in shift_rows)
    source_counts = Counter(str(row.get("source_milestone", "")) for row in shift_rows)
    task_counts = Counter(str(row.get("task_family", "")) for row in shift_rows)
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2934"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2934"])]
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2919/M2925/M2928/M2931/M2932/M2933/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m2932_accepts_m2931",
            "lineage",
            "accepts M2931" in source["m2932_audit_text"],
            "accepts M2931" in source["m2932_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2933_admits_m2934",
            "lineage",
            MILESTONE_ID in source["m2933_synthesis_text"] and "synthesis decision: `continue`" in source["m2933_synthesis_text"],
            {
                "m2934_id_present": MILESTONE_ID in source["m2933_synthesis_text"],
                "continue_decision_present": "synthesis decision: `continue`" in source["m2933_synthesis_text"],
            },
            "M2933 continue decision names M2934",
            "lineage_invalid",
        ),
        (
            "m2919_status_pass",
            "lineage",
            _bool(source["m2919_summary"].get("status_pass", False))
            and _bool(source["m2919_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2919_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2919_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2931_status_pass",
            "lineage",
            _bool(source["m2931_summary"].get("status_pass", False))
            and _bool(source["m2931_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2931_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2931_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "panel_rows_joined_one_to_one",
            "localization",
            len(shift_rows) == EXPECTED_PANEL_ROW_COUNT
            and len({str(row.get("m2919_execution_candidate_id", "")) for row in shift_rows}) == EXPECTED_PANEL_ROW_COUNT
            and len({str(row.get("m2931_repair_execution_candidate_id", "")) for row in shift_rows})
            == EXPECTED_PANEL_ROW_COUNT,
            len(shift_rows),
            EXPECTED_PANEL_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "offtrack_and_context_rows_preserved",
            "localization",
            len(offtrack_rows) == EXPECTED_OFFTRACK_TARGET_COUNT and len(context_rows) == EXPECTED_CONTEXT_ROW_COUNT,
            {"offtrack": len(offtrack_rows), "context": len(context_rows)},
            {"offtrack": EXPECTED_OFFTRACK_TARGET_COUNT, "context": EXPECTED_CONTEXT_ROW_COUNT},
            "metric_artifact",
        ),
        (
            "m2919_outcome_counts_preserved",
            "localization",
            dict(m2919_outcomes) == EXPECTED_M2919_OUTCOME_COUNTS,
            dict(m2919_outcomes),
            EXPECTED_M2919_OUTCOME_COUNTS,
            "metric_artifact",
        ),
        (
            "m2931_outcome_counts_preserved",
            "localization",
            dict(m2931_outcomes) == EXPECTED_M2931_OUTCOME_COUNTS,
            dict(m2931_outcomes),
            EXPECTED_M2931_OUTCOME_COUNTS,
            "metric_artifact",
        ),
        (
            "m2931_diagnostic_counts_preserved",
            "localization",
            m2931_diagnostic_counts(source["m2931_summary"]) == EXPECTED_M2931_DIAGNOSTIC_COUNTS,
            m2931_diagnostic_counts(source["m2931_summary"]),
            EXPECTED_M2931_DIAGNOSTIC_COUNTS,
            "metric_artifact",
        ),
        (
            "transition_counts_preserved",
            "localization",
            dict(transition_counts) == EXPECTED_TRANSITION_COUNTS,
            dict(transition_counts),
            EXPECTED_TRANSITION_COUNTS,
            "metric_artifact",
        ),
        (
            "source_panel_counts_preserved",
            "localization",
            dict(source_counts) == EXPECTED_PANEL_SOURCE_COUNTS,
            dict(source_counts),
            EXPECTED_PANEL_SOURCE_COUNTS,
            "metric_artifact",
        ),
        (
            "task_panel_counts_preserved",
            "localization",
            dict(task_counts) == EXPECTED_PANEL_TASK_COUNTS,
            dict(task_counts),
            EXPECTED_PANEL_TASK_COUNTS,
            "metric_artifact",
        ),
        (
            "aggregate_rows_account_all",
            "localization",
            sum(int(row["row_count"]) for row in source_rows) == EXPECTED_PANEL_ROW_COUNT
            and sum(int(row["row_count"]) for row in task_rows) == EXPECTED_PANEL_ROW_COUNT,
            {
                "source": sum(int(row["row_count"]) for row in source_rows),
                "task": sum(int(row["row_count"]) for row in task_rows),
            },
            EXPECTED_PANEL_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "coverage_constraints_preserved",
            "coverage",
            len(coverage_rows) == EXPECTED_COVERAGE_CONSTRAINT_COUNT
            and all(_bool(row.get("m2934_audit_status_pass", False)) for row in coverage_rows),
            f"rows={len(coverage_rows)} pass={sum(_bool(row.get('m2934_audit_status_pass', False)) for row in coverage_rows)}",
            f"{EXPECTED_COVERAGE_CONSTRAINT_COUNT} rows all pass",
            "metric_artifact",
        ),
        (
            "shortcut_exclusions_preserved",
            "shortcut",
            len(source["shortcut_exclusion_rows"]) == EXPECTED_SHORTCUT_EXCLUSION_COUNT,
            len(source["shortcut_exclusion_rows"]),
            EXPECTED_SHORTCUT_EXCLUSION_COUNT,
            "proof_washout",
        ),
        (
            "guardrails_preserved",
            "guardrail",
            guardrails_preserved(guardrail_rows),
            guardrail_presence(guardrail_rows),
            "route_b route_c m2877 present and not executed",
            "proof_washout",
        ),
        (
            "actor_contract_guards_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_rows)}",
            "all actor guards pass",
            "contract_violation",
        ),
        (
            "no_forbidden_execution_or_overclaim",
            "execution_guardrail",
            not any(forbidden_execution_flag(row) for row in shift_rows + coverage_rows + guardrail_rows),
            "no execution/ranking/promotion/overclaim flags",
            "all false",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in allowed_claims)
            and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims),
            f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}",
            "allowed pass and blocked not made",
            "proof_washout",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2934_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def write_derived_outputs(
    paths: dict[str, Path],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    shift_rows: list[dict[str, Any]],
    offtrack_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    m2919_outcomes = Counter(str(row.get("m2919_outcome_family", "")) for row in shift_rows)
    m2931_outcomes = Counter(str(row.get("m2931_outcome_family", "")) for row in shift_rows)
    transition_counts = Counter(str(row.get("transition_bucket", "")) for row in shift_rows)
    source_counts = Counter(str(row.get("source_milestone", "")) for row in shift_rows)
    task_counts = Counter(str(row.get("task_family", "")) for row in shift_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2919_status_pass": _bool(source["m2919_summary"].get("status_pass", False)),
        "m2919_gate_matrix_pass": _bool(source["m2919_summary"].get("gate_matrix_pass", False)),
        "m2931_status_pass": _bool(source["m2931_summary"].get("status_pass", False)),
        "m2931_gate_matrix_pass": _bool(source["m2931_summary"].get("gate_matrix_pass", False)),
        "outcome_shift_row_count": len(shift_rows),
        "offtrack_target_shift_row_count": len(offtrack_rows),
        "context_regression_row_count": len(context_rows),
        "m2919_outcome_counts": dict(m2919_outcomes),
        "m2931_outcome_counts": dict(m2931_outcomes),
        "m2931_diagnostic_counts": m2931_diagnostic_counts(source["m2931_summary"]),
        "transition_counts": dict(transition_counts),
        "source_milestone_counts": dict(source_counts),
        "task_family_counts": dict(task_counts),
        "offtrack_to_success_count": transition_counts.get("offtrack->success", 0),
        "offtrack_to_offtrack_count": transition_counts.get("offtrack->offtrack", 0),
        "offtrack_to_collision_count": transition_counts.get("offtrack->collision", 0),
        "offtrack_to_speed_too_low_count": transition_counts.get("offtrack->speed_too_low", 0),
        "success_to_offtrack_count": transition_counts.get("success->offtrack", 0),
        "success_to_collision_count": transition_counts.get("success->collision", 0),
        "success_to_success_count": transition_counts.get("success->success", 0),
        "offtrack_regression_or_substitution_count": sum(
            _bool(row.get("offtrack_regressed_to_collision_or_speed", False)) for row in shift_rows
        ),
        "success_context_regression_to_offtrack_or_collision_count": sum(
            _bool(row.get("context_regressed_to_offtrack_or_collision", False)) for row in shift_rows
        ),
        "source_milestone_transition_aggregate_row_count": len(source_rows),
        "task_family_transition_aggregate_row_count": len(task_rows),
        "coverage_constraint_audit_row_count": len(coverage_rows),
        "coverage_constraint_rows_pass": all(_bool(row.get("m2934_audit_status_pass", False)) for row in coverage_rows),
        "shortcut_exclusion_row_count": len(source["shortcut_exclusion_rows"]),
        "guardrail_context_row_count": len(guardrail_rows),
        "guardrails_preserved": guardrails_preserved(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "all_selected_metrics_finite": selected_metrics_are_finite(source["repair_execution_rows"])
        and selected_metrics_are_finite(source["m2919_bounded_execution_rows"]),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_simulation_run": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2934 Engineering Controller Route A Offtrack-Dominant Repair Execution Outcome-Shift Localization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- outcome shift rows: {summary['outcome_shift_row_count']}",
            f"- offtrack target rows: {summary['offtrack_target_shift_row_count']}",
            f"- context rows: {summary['context_regression_row_count']}",
            f"- M2919 outcomes: {summary['m2919_outcome_counts']}",
            f"- M2931 transition-label outcomes: {summary['m2931_outcome_counts']}",
            f"- M2931 diagnostic counts: {summary['m2931_diagnostic_counts']}",
            f"- transition counts: {summary['transition_counts']}",
            f"- offtrack to success: {summary['offtrack_to_success_count']}",
            f"- offtrack persistent: {summary['offtrack_to_offtrack_count']}",
            f"- offtrack to collision/speed: {summary['offtrack_regression_or_substitution_count']}",
            f"- success context to offtrack/collision: {summary['success_context_regression_to_offtrack_or_collision_count']}",
            f"- coverage audit rows: {summary['coverage_constraint_audit_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2934 materializes row-level outcome shifts only. Transition counts are diagnostic accounting, not repair success, ranking, validation readiness, or performance evidence.",
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


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
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
        "hypothesis": "A bounded result audit can accept or reject the M2934 outcome-shift localization before any further repair design, training, validation, ranking, promotion, performance, paper, high-fidelity, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "outcome_shift_rows.csv"),
                str(output_dir / "offtrack_target_shift_rows.csv"),
                str(output_dir / "context_regression_rows.csv"),
                str(output_dir / "source_milestone_transition_aggregate.csv"),
                str(output_dir / "task_family_transition_aggregate.csv"),
                str(output_dir / "coverage_constraint_audit_rows.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2933-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-synthesis.md",
                "docs/m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight.json",
                "experiments/manifests/m2933-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-synthesis.json",
            ],
            "parent_objective": ["audit M2934 outcome-shift localization before any next repair branch decision"],
            "derived_from": [
                MILESTONE_ID,
                "m2933-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-synthesis",
                "m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit",
                "m2931-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-preflight",
                "m2919-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-preflight",
            ],
            "blocked_by": [
                "M2934 materialization requires a result audit before interpretation",
                "transition counts include both offtrack repairs and regressions and cannot be promoted directly",
            ],
            "supersedes": ["direct next repair design from M2933 without transition audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2935 must audit M2934 summary gate matrix actor and claim boundaries",
            "M2935 must preserve all 56 transition rows and all expected M2919-to-M2931 transition counts",
            "M2935 must preserve offtrack target and context regression accounting",
            "M2935 must not claim repair success validation ranking performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2935 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert transition counts into repair-success performance validation paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_repair_execution_outcome_shift_localization_result_audit",
            "evidence_increment": "audits M2934 row-level M2919-to-M2931 outcome-shift localization artifacts",
            "claim_scope": "Result audit only; no repair design validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2934 artifacts are missing or gate matrix fails",
                "stop if row joins or transition counts are incomplete",
                "stop if actor or claim boundaries were violated",
                "stop if the audit cannot choose a bounded next design pivot stop or synthesis route without overclaiming",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch stop or pivot if transition localization shows no bounded repair route",
                "route to a bounded next design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2934 completes row-level outcome-shift localization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2934 offtrack repair outcome-shift localization artifacts",
            "admission_evidence": [
                "M2934 summary and gate matrix",
                "M2934 transition rows source/task aggregates coverage actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2935 status queue scoreboard research log and review",
                "one follow-up manifest only if M2935 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2935 audit accepts or rejects M2934 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2935 audits Route A outcome-shift localization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2935; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2919-to-M2934 Route A offtrack repair diagnostic chain.",
            "negative_result_policy": "Preserve negative or insufficient transitions and route to pivot or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2934 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized M2919-to-M2931 outcome shifts including regressions",
            "paper_verdict_delta": "no paper verdict; audit may admit a bounded next design or stop/pivot Route A repair",
            "must_synthesize_if": [
                "M2935 cannot accept M2934 as complete and claim-safe",
                "M2935 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2935 would continue another fixed-candidate execution without a materially changed evidence question",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2935 audits M2934 artifacts row counts gates actor and claim boundaries",
            "M2935 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2935 hides M2934 failures or missing artifacts",
            "M2935 treats M2934 transition localization as repair success validation readiness or performance verdict",
            "M2935 selects another fixed-candidate repair execution without a materially changed evidence question",
        ],
        "decision_rule": "Pass only if M2935 preserves M2934 transition localization evidence and chooses one bounded next route or stop state without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "outcome_shift_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def transition_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("transition_bucket", "")) for row in rows))


def m2931_diagnostic_counts(summary: Mapping[str, Any]) -> dict[str, int]:
    return {
        "success": int(summary.get("diagnostic_success_count", 0) or 0),
        "collision": int(summary.get("diagnostic_collision_count", 0) or 0),
        "offtrack": int(summary.get("diagnostic_offtrack_count", 0) or 0),
        "speed_too_low": int(summary.get("diagnostic_speed_too_low_count", 0) or 0),
    }


def guardrails_preserved(rows: list[dict[str, Any]]) -> bool:
    presence = guardrail_presence(rows)
    return bool(presence["route_b_context"] and presence["route_c_context"] and presence["m2877_context"]) and not any_flag(
        rows, "execution_run"
    )


def guardrail_presence(rows: list[dict[str, Any]]) -> dict[str, bool]:
    families = " ".join(str(row.get("guardrail_family", "")) for row in rows).lower()
    return {
        "route_b_context": "route_b" in families,
        "route_c_context": "route_c" in families,
        "m2877_context": "m2877" in families,
    }


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    keys = [
        "execution_performed_by_m2934",
        "validation_denominator_allowed",
        "paper_denominator_allowed",
        "ranking_claim_made",
        "success_rate_verdict_claim_made",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "execution_run",
        "training_run",
        "ppo_run",
        "winner_selected",
        "checkpoint_promoted",
        "actor_visible",
    ]
    return any(_bool(row.get(key, False)) for key in keys)


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def delta_float(new_value: Any, old_value: Any) -> float | str:
    new_float = _float_value(new_value)
    old_float = _float_value(old_value)
    if new_float is None or old_float is None:
        return ""
    return new_float - old_float


def _float_or_blank(value: Any) -> float | str:
    parsed = _float_value(value)
    return "" if parsed is None else parsed


def _float_value(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2919-dir", type=Path, default=DEFAULT_M2919_DIR)
    parser.add_argument("--m2925-dir", type=Path, default=DEFAULT_M2925_DIR)
    parser.add_argument("--m2928-dir", type=Path, default=DEFAULT_M2928_DIR)
    parser.add_argument("--m2931-dir", type=Path, default=DEFAULT_M2931_DIR)
    parser.add_argument("--m2932-audit", type=Path, default=DEFAULT_M2932_AUDIT)
    parser.add_argument("--m2933-synthesis", type=Path, default=DEFAULT_M2933_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_outcome_shift_localization_preflight(
        m2919_dir=args.m2919_dir,
        m2925_dir=args.m2925_dir,
        m2928_dir=args.m2928_dir,
        m2931_dir=args.m2931_dir,
        m2932_audit=args.m2932_audit,
        m2933_synthesis=args.m2933_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"outcome_shift_row_count={summary['outcome_shift_row_count']}")
    print(f"transition_counts={summary['transition_counts']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
