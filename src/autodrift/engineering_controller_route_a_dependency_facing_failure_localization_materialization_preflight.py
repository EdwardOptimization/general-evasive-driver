"""Materialize M2922 dependency-facing failure-localization rows.

M2922 consumes the complete M2919 bounded diagnostic execution artifacts after
M2920/M2921 audit and synthesis. It performs no environment or policy
execution. It converts the 56 diagnostic execution rows into machine-checkable
outcome, source, task, checkpoint, and next-route candidate rows for a later
audit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight"
NEXT_ID = "m2923-engineering-controller-route-a-dependency-facing-failure-localization-materialization-result-audit"
DEFAULT_M2919_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2920_AUDIT = Path(
    "docs/m2920-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-result-audit.md"
)
DEFAULT_M2921_SYNTHESIS = Path(
    "docs/m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2923-engineering-controller-route-a-dependency-facing-failure-localization-materialization-result-audit.json"
)

EXPECTED_EXECUTION_ROW_COUNT = 56
EXPECTED_FAILURE_ROW_COUNT = 0
EXPECTED_OUTCOME_COUNTS = {
    "diagnostic_success": 11,
    "collision": 3,
    "off_track": 38,
    "speed_too_low": 4,
}
EXPECTED_SOURCE_MILESTONE_COUNTS = {
    "m2737": 18,
    "m2746": 14,
    "m2807": 12,
    "m2816": 12,
}

CLAIM_SCOPE = (
    "M2922 Route A dependency-facing failure-localization materialization only; "
    "M2919 diagnostic execution rows may be grouped into outcome, source, task, "
    "checkpoint, and next-route candidate rows, while M2877 fixed weak "
    "diagnostic rows, Route B source-family insufficiency, and Route C "
    "source_unavailable remain guardrails or context only. No reset, step, "
    "rollout, replay, validation, training, PPO, dependency work, ranking, "
    "winner selection, promotion, success-rate verdict, driver-performance, "
    "paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full "
    "ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, checkpoint ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-sim verdict, high-fidelity validation readiness or "
    "result, full ideal driver completion, or level3 self-identification"
)

OUTCOME_FIELDNAMES = [
    "outcome_family_id",
    "outcome_family",
    "row_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "source_milestone_count",
    "task_family_count",
    "checkpoint_count",
    "min_clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "execution_candidate_count",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GROUP_FIELDNAMES = [
    "localization_id",
    "group_family",
    "group_value",
    "row_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "non_success_count",
    "dominant_outcome_family",
    "min_clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
NEXT_ROUTE_FIELDNAMES = [
    "route_candidate_id",
    "route_candidate_family",
    "trigger_family",
    "trigger_value",
    "trigger_count",
    "candidate_admitted_for_audit",
    "execution_scheduled",
    "training_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "required_follow_up",
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
    "ordinary_engineering_denominator_allowed",
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
    "allowed_in_m2922",
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
    "outcome_family_rows",
    "source_milestone_outcome_rows",
    "task_family_outcome_rows",
    "checkpoint_outcome_rows",
    "next_route_candidate_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_failure_localization_materialization_preflight(
    *,
    m2919_dir: Path | str = DEFAULT_M2919_DIR,
    m2920_audit: Path | str = DEFAULT_M2920_AUDIT,
    m2921_synthesis: Path | str = DEFAULT_M2921_SYNTHESIS,
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
        m2920_audit=Path(m2920_audit),
        m2921_synthesis=Path(m2921_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]

    outcome_rows = build_outcome_family_rows(execution_rows)
    source_rows = build_group_rows(execution_rows, group_family="source_milestone", key="source_milestone")
    task_rows = build_group_rows(execution_rows, group_family="task_family", key="task_family")
    checkpoint_rows = build_group_rows(execution_rows, group_family="checkpoint_path", key="checkpoint_path")
    next_route_rows = build_next_route_candidate_rows(
        execution_rows=execution_rows,
        outcome_rows=outcome_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
    )
    guardrail_rows = build_guardrail_context_rows(source["guardrail_context_rows"])

    write_csv_rows(paths["outcome_family_rows"], outcome_rows, fieldnames=OUTCOME_FIELDNAMES)
    write_csv_rows(paths["source_milestone_outcome_rows"], source_rows, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(paths["task_family_outcome_rows"], task_rows, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(paths["checkpoint_outcome_rows"], checkpoint_rows, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(paths["next_route_candidate_rows"], next_route_rows, fieldnames=NEXT_ROUTE_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "execution_row_count": len(execution_rows),
            "failure_row_count": len(failure_rows),
            "outcome_family_row_count": len(outcome_rows),
            "source_milestone_outcome_row_count": len(source_rows),
            "task_family_outcome_row_count": len(task_rows),
            "checkpoint_outcome_row_count": len(checkpoint_rows),
            "next_route_candidate_row_count": len(next_route_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        next_route_rows=next_route_rows,
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        localization_rows_present=bool(outcome_rows and source_rows and task_rows and checkpoint_rows and next_route_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        outcome_rows=outcome_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        next_route_rows=next_route_rows,
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
        outcome_rows=outcome_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        next_route_rows=next_route_rows,
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
        localization_rows_present=bool(outcome_rows and source_rows and task_rows and checkpoint_rows and next_route_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        outcome_rows=outcome_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        next_route_rows=next_route_rows,
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
        outcome_rows=outcome_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        next_route_rows=next_route_rows,
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
            "execution_row_count": len(execution_rows),
            "failure_row_count": len(failure_rows),
            "outcome_family_row_count": len(outcome_rows),
            "source_milestone_outcome_row_count": len(source_rows),
            "task_family_outcome_row_count": len(task_rows),
            "checkpoint_outcome_row_count": len(checkpoint_rows),
            "next_route_candidate_row_count": len(next_route_rows),
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
        "outcome_family_rows": output_dir / "outcome_family_rows.csv",
        "source_milestone_outcome_rows": output_dir / "source_milestone_outcome_rows.csv",
        "task_family_outcome_rows": output_dir / "task_family_outcome_rows.csv",
        "checkpoint_outcome_rows": output_dir / "checkpoint_outcome_rows.csv",
        "next_route_candidate_rows": output_dir / "next_route_candidate_rows.csv",
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
    m2920_audit: Path,
    m2921_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2920_audit": m2920_audit,
        "m2921_synthesis": m2921_synthesis,
        "m2919_summary": m2919_dir / "summary.json",
        "execution_candidate_rows": m2919_dir / "execution_candidate_rows.csv",
        "execution_resolution_rows": m2919_dir / "execution_resolution_rows.csv",
        "bounded_execution_rows": m2919_dir / "bounded_execution_rows.csv",
        "bounded_execution_failure_rows": m2919_dir / "bounded_execution_failure_rows.csv",
        "source_milestone_aggregate": m2919_dir / "source_milestone_aggregate.csv",
        "task_family_aggregate": m2919_dir / "task_family_aggregate.csv",
        "guardrail_context_rows": m2919_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": m2919_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2919_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2919_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2920_audit_text": paths["m2920_audit"].read_text(encoding="utf-8")
        if source_exists["m2920_audit"]
        else "",
        "m2921_synthesis_text": paths["m2921_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2921_synthesis"]
        else "",
        "m2919_summary": read_json(paths["m2919_summary"]) if source_exists["m2919_summary"] else {},
        "execution_candidate_rows": read_csv_rows(paths["execution_candidate_rows"]),
        "execution_resolution_rows": read_csv_rows(paths["execution_resolution_rows"]),
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
        "bounded_execution_failure_rows": read_csv_rows(paths["bounded_execution_failure_rows"]),
        "source_milestone_aggregate": read_csv_rows(paths["source_milestone_aggregate"]),
        "task_family_aggregate": read_csv_rows(paths["task_family_aggregate"]),
        "guardrail_context_rows": read_csv_rows(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def outcome_family(row: Mapping[str, Any]) -> str:
    termination = str(row.get("termination_reason", "")).strip()
    if _bool(row.get("success", False)):
        return "diagnostic_success"
    if _bool(row.get("collision", False)) or termination == "obstacle_collision":
        return "collision"
    if termination == "off_track":
        return "off_track"
    if termination == "speed_too_low":
        return "speed_too_low"
    return "other_non_success"


def build_outcome_family_rows(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in execution_rows:
        grouped[outcome_family(row)].append(row)
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(sorted(grouped), start=1):
        group = grouped[family]
        rows.append(
            {
                "outcome_family_id": f"m2922-outcome-family-{index:04d}",
                "outcome_family": family,
                "row_count": len(group),
                "success_count": sum(_bool(row.get("success", False)) for row in group),
                "collision_count": sum(_bool(row.get("collision", False)) for row in group),
                "offtrack_count": sum(str(row.get("termination_reason", "")) == "off_track" for row in group),
                "speed_too_low_count": sum(str(row.get("termination_reason", "")) == "speed_too_low" for row in group),
                "source_milestone_count": len({str(row.get("source_milestone", "")) for row in group if row.get("source_milestone")}),
                "task_family_count": len({str(row.get("task_family", "")) for row in group if row.get("task_family")}),
                "checkpoint_count": len({str(row.get("checkpoint_path", "")) for row in group if row.get("checkpoint_path")}),
                "min_clearance_margin_mean": mean_float(group, "min_clearance_margin"),
                "return_mean": mean_float(group, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(group),
                "execution_candidate_count": len({str(row.get("execution_candidate_id", "")) for row in group}),
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_group_rows(execution_rows: list[dict[str, str]], *, group_family: str, key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in execution_rows:
        grouped[str(row.get(key, ""))].append(row)
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(sorted(value for value in grouped if value), start=1):
        group = grouped[value]
        counts = Counter(outcome_family(row) for row in group)
        rows.append(
            {
                "localization_id": f"m2922-{group_family}-localization-{index:04d}",
                "group_family": group_family,
                "group_value": value,
                "row_count": len(group),
                "success_count": counts.get("diagnostic_success", 0),
                "collision_count": counts.get("collision", 0),
                "offtrack_count": counts.get("off_track", 0),
                "speed_too_low_count": counts.get("speed_too_low", 0),
                "non_success_count": len(group) - counts.get("diagnostic_success", 0),
                "dominant_outcome_family": dominant_outcome(counts),
                "min_clearance_margin_mean": mean_float(group, "min_clearance_margin"),
                "return_mean": mean_float(group, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(group),
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_next_route_candidate_rows(
    *,
    execution_rows: list[dict[str, str]],
    outcome_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outcome_counts = {str(row["outcome_family"]): int(row["row_count"]) for row in outcome_rows}
    source_non_success = sum(1 for row in source_rows if int(row["non_success_count"]) > 0)
    task_non_success = sum(1 for row in task_rows if int(row["non_success_count"]) > 0)
    checkpoint_non_success = sum(1 for row in checkpoint_rows if int(row["non_success_count"]) > 0)
    specs = [
        (
            "offtrack_dominant_failure_localization",
            "outcome_family",
            "off_track",
            outcome_counts.get("off_track", 0),
            outcome_counts.get("off_track", 0) > outcome_counts.get("diagnostic_success", 0),
            "M2923 audit before any offtrack-specific repair or execution design",
        ),
        (
            "source_milestone_failure_spread_localization",
            "source_milestone",
            "non_success_present",
            source_non_success,
            source_non_success >= 2,
            "M2923 audit before source-slice route design",
        ),
        (
            "task_family_failure_spread_localization",
            "task_family",
            "non_success_present",
            task_non_success,
            task_non_success >= 2,
            "M2923 audit before task-family route design",
        ),
        (
            "checkpoint_context_failure_localization",
            "checkpoint_path",
            "non_success_present",
            checkpoint_non_success,
            checkpoint_non_success >= 1 and len({row.get("checkpoint_path", "") for row in execution_rows}) >= 1,
            "M2923 audit before checkpoint-context interpretation",
        ),
    ]
    rows = []
    for index, (family, trigger_family, trigger_value, trigger_count, admitted, follow_up) in enumerate(specs, start=1):
        rows.append(
            {
                "route_candidate_id": f"m2922-next-route-candidate-{index:04d}",
                "route_candidate_family": family,
                "trigger_family": trigger_family,
                "trigger_value": trigger_value,
                "trigger_count": int(trigger_count),
                "candidate_admitted_for_audit": bool(admitted),
                "execution_scheduled": False,
                "training_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "required_follow_up": follow_up,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2922-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": row.get("row_count", 1),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_engineering_denominator_allowed": False,
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
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    next_route_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = execution_rows + failure_rows + next_route_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("environment_execution_performed_by_m2922", False, False),
        actor_guard("training_scheduled", any_flag(combined, "training_scheduled"), False),
        actor_guard("ranking_allowed", any_flag(combined, "ranking_allowed"), False),
        actor_guard("winner_selection_allowed", any_flag(combined, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(combined, "promotion_allowed"), False),
        actor_guard("hidden_oracle_actor_input_required", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", any_flag(combined, "future_target_actor_input_required"), False),
        actor_guard("route_labels_actor_visible", any_flag(combined, "route_labels_actor_visible"), False),
        actor_guard("source_labels_actor_visible", any_flag(combined, "source_labels_actor_visible"), False),
        actor_guard("diagnostic_labels_actor_visible", any_flag(combined, "diagnostic_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", any_flag(combined, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(combined, "verdict_labels_actor_visible"), False),
        actor_guard("guardrail_execution", any_flag(guardrail_rows, "execution_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2922-actor-guard-{field}",
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
    localization_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("failure_localization_materialization", "artifact", localization_rows_present, "M2922 localization rows"),
        ("outcome_family_rows_materialized", "artifact", artifacts_present, "outcome_family_rows.csv"),
        ("source_milestone_rows_materialized", "artifact", artifacts_present, "source_milestone_outcome_rows.csv"),
        ("task_family_rows_materialized", "artifact", artifacts_present, "task_family_outcome_rows.csv"),
        ("checkpoint_rows_materialized", "artifact", artifacts_present, "checkpoint_outcome_rows.csv"),
        ("next_route_candidates_materialized", "artifact", artifacts_present, "next_route_candidate_rows.csv"),
        ("guardrail_context_materialized", "artifact", artifacts_present, "guardrail_context_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2923 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_execution", "execution", "no execution in M2922"),
        ("training_or_ppo", "execution", "future manifest"),
        ("dependency_execution", "execution", "future dependency route"),
        ("controller_source_task_checkpoint_ranking", "ranking", "future audited comparison route"),
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
        "claim_id": f"m2922_{claim_id}",
        "claim_family": family,
        "allowed_in_m2922": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    outcome_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    next_route_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]
    outcome_counts = Counter(outcome_family(row) for row in execution_rows)
    source_milestone_counts = Counter(str(row.get("source_milestone", "")) for row in execution_rows)
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2922"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2922"])]
    route_b_context = any("route_b" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    route_c_context = any("route_c" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2919/M2920/M2921/follow-up artifacts present", "lineage_invalid"),
        ("m2920_accepts_m2919", "lineage", "accepts M2919" in source["m2920_audit_text"], "accepts M2919" in source["m2920_audit_text"], True, "lineage_invalid"),
        ("m2921_admits_m2922", "lineage", MILESTONE_ID in source["m2921_synthesis_text"], MILESTONE_ID in source["m2921_synthesis_text"], True, "lineage_invalid"),
        ("m2919_status_pass", "lineage", _bool(source["m2919_summary"].get("status_pass", False)) and _bool(source["m2919_summary"].get("gate_matrix_pass", False)), {"status_pass": source["m2919_summary"].get("status_pass"), "gate_matrix_pass": source["m2919_summary"].get("gate_matrix_pass")}, "both true", "lineage_invalid"),
        ("execution_rows_loaded", "localization", len(execution_rows) == EXPECTED_EXECUTION_ROW_COUNT, len(execution_rows), EXPECTED_EXECUTION_ROW_COUNT, "metric_artifact"),
        ("failure_rows_preserved", "localization", len(failure_rows) == EXPECTED_FAILURE_ROW_COUNT, len(failure_rows), EXPECTED_FAILURE_ROW_COUNT, "metric_artifact"),
        ("outcome_counts_match_m2919", "localization", dict(outcome_counts) == EXPECTED_OUTCOME_COUNTS, dict(outcome_counts), EXPECTED_OUTCOME_COUNTS, "metric_artifact"),
        ("source_milestone_counts_match_m2919", "localization", dict(source_milestone_counts) == EXPECTED_SOURCE_MILESTONE_COUNTS, dict(source_milestone_counts), EXPECTED_SOURCE_MILESTONE_COUNTS, "metric_artifact"),
        ("outcome_rows_account_all", "localization", sum(int(row["row_count"]) for row in outcome_rows) == len(execution_rows), sum(int(row["row_count"]) for row in outcome_rows), len(execution_rows), "metric_artifact"),
        ("source_rows_account_all", "localization", sum(int(row["row_count"]) for row in source_rows) == len(execution_rows), sum(int(row["row_count"]) for row in source_rows), len(execution_rows), "metric_artifact"),
        ("task_rows_account_all", "localization", sum(int(row["row_count"]) for row in task_rows) == len(execution_rows), sum(int(row["row_count"]) for row in task_rows), len(execution_rows), "metric_artifact"),
        ("checkpoint_rows_account_all", "localization", sum(int(row["row_count"]) for row in checkpoint_rows) == len(execution_rows), sum(int(row["row_count"]) for row in checkpoint_rows), len(execution_rows), "metric_artifact"),
        ("next_route_candidates_present", "route", len(next_route_rows) >= 3 and any(_bool(row.get("candidate_admitted_for_audit", False)) for row in next_route_rows), len(next_route_rows), ">=3 with admitted candidates", "scenario_sampling_failure"),
        ("next_route_candidates_no_execution_or_ranking", "contract", not any(candidate_forbidden_flag(row) for row in next_route_rows), "all false", "all false", "contract_violation"),
        ("guardrails_preserved", "guardrail", route_b_context and route_c_context and not any_flag(guardrail_rows, "execution_run"), {"route_b_context": route_b_context, "route_c_context": route_c_context}, "both present and not executed", "proof_washout"),
        ("actor_contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_rows)}", "all actor guards pass", "contract_violation"),
        ("no_forbidden_execution_or_overclaim", "execution_guardrail", not any(forbidden_execution_flag(row) for row in execution_rows + failure_rows + next_route_rows + guardrail_rows), "no execution/ranking/promotion/overclaim flags", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claims) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed pass and blocked not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2922_{gate_id}",
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
    outcome_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    next_route_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    execution_rows = source["bounded_execution_rows"]
    failure_rows = source["bounded_execution_failure_rows"]
    outcome_counts = Counter(outcome_family(row) for row in execution_rows)
    source_milestone_counts = Counter(str(row.get("source_milestone", "")) for row in execution_rows)
    task_family_counts = Counter(str(row.get("task_family", "")) for row in execution_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight_fail"
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
        "execution_row_count": len(execution_rows),
        "failure_row_count": len(failure_rows),
        "bounded_execution_row_count": len(execution_rows),
        "bounded_execution_failure_row_count": len(failure_rows),
        "outcome_counts": dict(outcome_counts),
        "source_milestone_counts": dict(source_milestone_counts),
        "task_family_counts": dict(task_family_counts),
        "diagnostic_success_count": outcome_counts.get("diagnostic_success", 0),
        "diagnostic_collision_count": outcome_counts.get("collision", 0),
        "diagnostic_offtrack_count": outcome_counts.get("off_track", 0),
        "diagnostic_speed_too_low_count": outcome_counts.get("speed_too_low", 0),
        "outcome_family_row_count": len(outcome_rows),
        "source_milestone_outcome_row_count": len(source_rows),
        "task_family_outcome_row_count": len(task_rows),
        "checkpoint_outcome_row_count": len(checkpoint_rows),
        "next_route_candidate_row_count": len(next_route_rows),
        "next_route_candidate_admitted_count": sum(_bool(row.get("candidate_admitted_for_audit", False)) for row in next_route_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "all_selected_metrics_finite": selected_metrics_are_finite(execution_rows) if execution_rows else False,
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
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
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
            "# M2922 Engineering Controller Route A Dependency-Facing Failure Localization Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- execution rows localized: {summary['execution_row_count']}",
            f"- execution failure rows preserved: {summary['failure_row_count']}",
            f"- outcome counts: {summary['outcome_counts']}",
            f"- outcome family rows: {summary['outcome_family_row_count']}",
            f"- source milestone outcome rows: {summary['source_milestone_outcome_row_count']}",
            f"- task family outcome rows: {summary['task_family_outcome_row_count']}",
            f"- checkpoint outcome rows: {summary['checkpoint_outcome_row_count']}",
            f"- next route candidates: {summary['next_route_candidate_row_count']}",
            f"- admitted next route candidates for audit: {summary['next_route_candidate_admitted_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2922 materializes no-execution failure-localization rows from M2919 diagnostics. It does not rerun environments, train, rank, promote, or claim performance.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2922 dependency-facing failure-localization materialization before any repair execution validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "outcome_family_rows.csv"),
                str(output_dir / "source_milestone_outcome_rows.csv"),
                str(output_dir / "task_family_outcome_rows.csv"),
                str(output_dir / "checkpoint_outcome_rows.csv"),
                str(output_dir / "next_route_candidate_rows.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis.md",
            ],
            "parent_config": [
                "experiments/manifests/m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight.json",
                "experiments/manifests/m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis.json",
            ],
            "parent_objective": [
                "audit M2922 failure-localization materialization artifacts before any route interpretation"
            ],
            "derived_from": [MILESTONE_ID, "m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis"],
            "blocked_by": [
                "M2922 localization requires a result audit before any repair execution or route commitment",
                "M2877 Route B and Route C guardrails must remain protected context",
            ],
            "supersedes": ["direct interpretation of M2922 next-route candidate rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2923 must audit M2922 summary gate matrix actor and claim boundaries",
            "M2923 must preserve M2877 Route B Route C guardrail exclusions",
            "M2923 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2923 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert M2922 localization rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_failure_localization_result_audit",
            "evidence_increment": "audits failure-localization artifacts from M2922",
            "claim_scope": "Result audit only; no validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2922 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if guardrails entered execution or denominators",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if localization is complete but no route candidate is viable",
                "route to a bounded design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2922 completes failure-localization materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2922 dependency-facing failure-localization materialization artifacts",
            "admission_evidence": [
                "M2922 summary and gate matrix",
                "M2922 outcome source task checkpoint next-route guard actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2923 status queue scoreboard research log and review",
                "one follow-up manifest only if M2923 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2923 audit accepts or rejects M2922 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2923 audits Route A failure localization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2923; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2922 Route A dependency-facing failure localization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2922 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized Route A dependency-facing failure localization rows",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2923 cannot accept M2922 as complete and claim-safe",
                "M2923 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2923 would continue static design without new data or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2923 audits M2922 artifacts row counts gates actor and claim boundaries",
            "M2923 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2923 hides M2922 failures or missing artifacts",
            "M2923 treats M2922 localization as validation readiness or performance verdict",
            "M2923 changes actor input or action contract",
            "M2923 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2923 audits M2922 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "outcome_family_rows.csv"),
            str(output_dir / "next_route_candidate_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def dominant_outcome(counts: Counter[str]) -> str:
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def candidate_forbidden_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "execution_scheduled",
            "training_scheduled",
            "ranking_allowed",
            "winner_selection_allowed",
            "promotion_allowed",
            "validation_denominator_allowed",
            "paper_denominator_allowed",
            "high_fidelity_readiness_allowed",
            "self_id_claim_allowed",
        )
    )


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "environment_reset_run",
            "environment_step_run",
            "policy_action_run",
            "policy_rollout_run",
            "measured_validation_run",
            "training_started",
            "training_scheduled",
            "training_run",
            "replay_started",
            "replay_run",
            "ppo_used",
            "ppo_run",
            "source_build_run",
            "adapter_probe_run",
            "external_simulation_run",
            "dependency_execution_performed",
            "private_holdout_used",
            "ranking_allowed",
            "ranking_run",
            "winner_selection_allowed",
            "winner_selected",
            "promotion_allowed",
            "checkpoint_promoted",
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "guardrail_rows_in_success_denominator",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "validation_readiness_claim_made",
            "validation_result_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
            "full_ideal_driver_completion_claim_made",
            "level3_self_id_claim_made",
        )
    )


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def mean_float(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values = []
    for row in rows:
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    if not values:
        return ""
    return float(sum(values) / len(values))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2919-dir", type=Path, default=DEFAULT_M2919_DIR)
    parser.add_argument("--m2920-audit", type=Path, default=DEFAULT_M2920_AUDIT)
    parser.add_argument("--m2921-synthesis", type=Path, default=DEFAULT_M2921_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_failure_localization_materialization_preflight(
        m2919_dir=args.m2919_dir,
        m2920_audit=args.m2920_audit,
        m2921_synthesis=args.m2921_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"execution_rows={summary['execution_row_count']}")
    print(f"next_route_candidates={summary['next_route_candidate_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
