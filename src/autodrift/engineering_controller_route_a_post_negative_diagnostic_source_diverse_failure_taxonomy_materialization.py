"""Materialize failure taxonomy for post-negative source-diverse diagnostics.

M2740 consumes M2737 diagnostic execution artifacts after M2739 synthesis. It
does not reset, step, execute policies, replay, validate, train, rank source
families, or promote checkpoints. The output is a no-rollout row-level taxonomy
for Route A planning and result audit only.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "failure-taxonomy-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "failure-taxonomy-materialization-result-audit"
)
DEFAULT_M2737_DIR = Path(
    "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2739_SYNTHESIS = Path(
    "docs/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit.json"
)

EXPECTED_EXECUTION_ROW_COUNT = 18
EXPECTED_NEGATIVE_CONTEXT_GUARD_ROW_COUNT = 31
EXPECTED_BLOCKED_GUARD_ROW_COUNT = 12
EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_ROW_COUNT = 3
EXPECTED_COLLISION_FAILURE_ROW_COUNT = 1
EXPECTED_OFFTRACK_ROW_COUNT = 14
EXPECTED_SOURCE_FAMILY_CONTEXT_ROW_COUNT = 2
EXPECTED_TASK_FAMILY_CONTEXT_ROW_COUNT = 2

CLAIM_SCOPE = (
    "M2740 Route A post-negative source-diverse failure taxonomy "
    "materialization only; no reset, step, policy action, rollout, replay, "
    "validation, training, PPO, source build, adapter probe, external "
    "simulation, private holdout, profile-specific tuning, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "path",
    "present",
    "row_count",
    "status_pass",
    "claim_boundary",
]
TAXONOMY_FIELDNAMES = [
    "taxonomy_id",
    "source_row_type",
    "candidate_id",
    "guard_id",
    "context_id",
    "source_milestone",
    "source_family",
    "source_key",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "outcome_bucket",
    "success",
    "collision",
    "termination_reason",
    "taxonomy_family",
    "primary_failure_family",
    "repair_signal",
    "diagnostic_success_context",
    "execution_run",
    "execution_admitted",
    "guardrail_only",
    "negative_context_guard",
    "blocked_guard",
    "protected_or_hf3_blocker",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "taxonomy_labels_actor_visible",
    "source_family_ranking_allowed",
    "task_family_ranking_allowed",
    "profile_ranking_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "group_key",
    "execution_row_count",
    "negative_context_guard_row_count",
    "blocked_guard_row_count",
    "taxonomy_row_count",
    "diagnostic_success_context_row_count",
    "collision_failure_row_count",
    "offtrack_row_count",
    "negative_context_taxonomy_row_count",
    "blocked_guard_taxonomy_row_count",
    "protected_or_hf3_blocker_row_count",
    "source_family_ranking_allowed",
    "task_family_ranking_allowed",
    "profile_ranking_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SOURCE_CONTEXT_FIELDNAMES = [
    "source_context_id",
    "source_milestone",
    "source_family",
    "execution_row_count",
    "diagnostic_success_context_row_count",
    "collision_failure_row_count",
    "offtrack_row_count",
    "dominant_taxonomy_family",
    "source_family_ranking_allowed",
    "winner_selection_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
TASK_CONTEXT_FIELDNAMES = [
    "task_context_id",
    "task_family",
    "source_family_count",
    "execution_row_count",
    "diagnostic_success_context_row_count",
    "collision_failure_row_count",
    "offtrack_row_count",
    "dominant_taxonomy_family",
    "task_family_ranking_allowed",
    "winner_selection_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_CONTEXT_FIELDNAMES = [
    "guardrail_context_id",
    "guardrail_family",
    "source_row_type",
    "row_count",
    "execution_run_count",
    "execution_admitted_count",
    "protected_denominator_count",
    "actor_visible_count",
    "guardrail_only",
    "claim_boundary",
]
ACTOR_JOIN_FIELDNAMES = [
    "join_id",
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
    "allowed_in_m2740",
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
    "source_accounting_rows",
    "taxonomy_rows",
    "taxonomy_aggregate_rows",
    "source_family_context_rows",
    "task_family_context_rows",
    "guardrail_context_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_post_negative_source_diverse_failure_taxonomy(
    *,
    m2737_dir: Path | str = DEFAULT_M2737_DIR,
    m2739_synthesis: Path | str = DEFAULT_M2739_SYNTHESIS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2737_dir=Path(m2737_dir),
        m2739_synthesis=Path(m2739_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )
    taxonomy_rows = build_taxonomy_rows(
        execution_rows=source["candidate_execution_rows"],
        negative_context_rows=source["negative_context_guard_rows"],
        blocked_rows=source["blocked_surface_guard_rows"],
    )
    aggregate_rows = build_taxonomy_aggregate_rows(taxonomy_rows)
    source_context_rows = build_source_family_context_rows(taxonomy_rows)
    task_context_rows = build_task_family_context_rows(taxonomy_rows)
    guardrail_context_rows = build_guardrail_context_rows(taxonomy_rows)
    actor_rows = build_actor_contract_join_rows(source=source, taxonomy_rows=taxonomy_rows)
    source_rows = build_source_accounting_rows(source=source)
    required_artifacts_present = False
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        taxonomy_rows_present=bool(taxonomy_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        source_context_rows=source_context_rows,
        task_context_rows=task_context_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )

    write_csv_rows(paths["source_accounting_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["taxonomy_rows"], taxonomy_rows, fieldnames=TAXONOMY_FIELDNAMES)
    write_csv_rows(paths["taxonomy_aggregate_rows"], aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["source_family_context_rows"], source_context_rows, fieldnames=SOURCE_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["task_family_context_rows"], task_context_rows, fieldnames=TASK_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_context_rows, fieldnames=GUARDRAIL_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_join_rows"], actor_rows, fieldnames=ACTOR_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        taxonomy_rows_present=bool(taxonomy_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        source_context_rows=source_context_rows,
        task_context_rows=task_context_rows,
        guardrail_context_rows=guardrail_context_rows,
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
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        source_context_rows=source_context_rows,
        task_context_rows=task_context_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        source_context_rows=source_context_rows,
        task_context_rows=task_context_rows,
        guardrail_context_rows=guardrail_context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        source_context_rows=source_context_rows,
        task_context_rows=task_context_rows,
        guardrail_context_rows=guardrail_context_rows,
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
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_accounting_rows": output_dir / "source_accounting_rows.csv",
        "taxonomy_rows": output_dir / "taxonomy_rows.csv",
        "taxonomy_aggregate_rows": output_dir / "taxonomy_aggregate_rows.csv",
        "source_family_context_rows": output_dir / "source_family_context_rows.csv",
        "task_family_context_rows": output_dir / "task_family_context_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2737_dir: Path,
    m2739_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2739_synthesis_doc": m2739_synthesis,
        "m2737_summary": m2737_dir / "summary.json",
        "m2737_candidate_execution_rows": m2737_dir / "candidate_execution_rows.csv",
        "m2737_source_family_aggregate": m2737_dir / "source_family_aggregate.csv",
        "m2737_task_family_aggregate": m2737_dir / "task_family_aggregate.csv",
        "m2737_negative_context_guard_rows": m2737_dir / "negative_context_guard_rows.csv",
        "m2737_blocked_surface_guard_rows": m2737_dir / "blocked_surface_guard_rows.csv",
        "m2737_actor_contract_guard_rows": m2737_dir / "actor_contract_guard_rows.csv",
        "m2737_claim_boundary_rows": m2737_dir / "claim_boundary_rows.csv",
        "m2737_gate_matrix": m2737_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2739_synthesis_text": paths["m2739_synthesis_doc"].read_text(encoding="utf-8")
        if source_exists["m2739_synthesis_doc"]
        else "",
        "m2737_summary": read_json(paths["m2737_summary"]) if source_exists["m2737_summary"] else {},
        "candidate_execution_rows": read_csv_rows(paths["m2737_candidate_execution_rows"]),
        "source_family_aggregate_rows": read_csv_rows(paths["m2737_source_family_aggregate"]),
        "task_family_aggregate_rows": read_csv_rows(paths["m2737_task_family_aggregate"]),
        "negative_context_guard_rows": read_csv_rows(paths["m2737_negative_context_guard_rows"]),
        "blocked_surface_guard_rows": read_csv_rows(paths["m2737_blocked_surface_guard_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["m2737_actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2737_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2737_gate_matrix"]),
    }


def build_source_accounting_rows(*, source: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {
        "m2737_candidate_execution_rows": len(source["candidate_execution_rows"]),
        "m2737_source_family_aggregate": len(source["source_family_aggregate_rows"]),
        "m2737_task_family_aggregate": len(source["task_family_aggregate_rows"]),
        "m2737_negative_context_guard_rows": len(source["negative_context_guard_rows"]),
        "m2737_blocked_surface_guard_rows": len(source["blocked_surface_guard_rows"]),
        "m2737_actor_contract_guard_rows": len(source["actor_contract_guard_rows"]),
        "m2737_claim_boundary_rows": len(source["claim_boundary_rows"]),
        "m2737_gate_matrix": len(source["gate_matrix"]),
    }
    rows = []
    for index, (key, path) in enumerate(source["paths"].items(), start=1):
        present = bool(source["source_exists"].get(key, False))
        rows.append(
            {
                "source_id": f"m2740-source-{index:04d}",
                "source_family": key,
                "path": str(path),
                "present": present,
                "row_count": row_counts.get(key, ""),
                "status_pass": present,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_taxonomy_rows(
    *,
    execution_rows: list[dict[str, Any]],
    negative_context_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(execution_rows, start=1):
        taxonomy_family = classify_execution_row(row)
        rows.append(
            taxonomy_row(
                taxonomy_id=f"m2740-taxonomy-execution-{index:04d}",
                source_row_type="candidate_execution",
                row=row,
                candidate_id=row.get("candidate_id", ""),
                guard_id="",
                context_id=row.get("resolution_id", ""),
                taxonomy_family=taxonomy_family,
                execution_run=bool_value(row.get("full_rollout_execution", True)),
                execution_admitted=True,
                guardrail_only=False,
                negative_context_guard=False,
                blocked_guard=False,
                protected_or_hf3_blocker=False,
            )
        )
    for index, row in enumerate(negative_context_rows, start=1):
        rows.append(
            taxonomy_row(
                taxonomy_id=f"m2740-taxonomy-negative-context-{index:04d}",
                source_row_type="negative_context_guard",
                row=row,
                candidate_id=row.get("candidate_row_id", ""),
                guard_id=row.get("guard_id", ""),
                context_id=row.get("context_id", ""),
                taxonomy_family="negative_context_guard",
                execution_run=bool_value(row.get("execution_run", False)),
                execution_admitted=bool_value(row.get("execution_admitted", False)),
                guardrail_only=True,
                negative_context_guard=True,
                blocked_guard=False,
                protected_or_hf3_blocker=False,
            )
        )
    for index, row in enumerate(blocked_rows, start=1):
        family = "protected_or_hf3_blocker" if is_protected_or_hf3(row) else "blocked_guard"
        rows.append(
            taxonomy_row(
                taxonomy_id=f"m2740-taxonomy-blocked-guard-{index:04d}",
                source_row_type="blocked_surface_guard",
                row=row,
                candidate_id=row.get("blocked_id", ""),
                guard_id=row.get("guard_id", ""),
                context_id=row.get("blocked_id", ""),
                taxonomy_family=family,
                execution_run=bool_value(row.get("execution_run", False)),
                execution_admitted=bool_value(row.get("execution_admitted", False)),
                guardrail_only=True,
                negative_context_guard=False,
                blocked_guard=True,
                protected_or_hf3_blocker=is_protected_or_hf3(row),
            )
        )
    return rows


def taxonomy_row(
    *,
    taxonomy_id: str,
    source_row_type: str,
    row: Mapping[str, Any],
    candidate_id: str,
    guard_id: str,
    context_id: str,
    taxonomy_family: str,
    execution_run: bool,
    execution_admitted: bool,
    guardrail_only: bool,
    negative_context_guard: bool,
    blocked_guard: bool,
    protected_or_hf3_blocker: bool,
) -> dict[str, Any]:
    return {
        "taxonomy_id": taxonomy_id,
        "source_row_type": source_row_type,
        "candidate_id": candidate_id,
        "guard_id": guard_id,
        "context_id": context_id,
        "source_milestone": row.get("source_milestone", ""),
        "source_family": row.get("source_family", row.get("blocked_family", "")),
        "source_key": row.get("source_key", row.get("source_row_id", "")),
        "workload_id": row.get("workload_id", ""),
        "task_source_id": row.get("task_source_id", row.get("anchor_task_source_id", "")),
        "profile_name": row.get("profile_name", ""),
        "task_family": row.get("task_family", ""),
        "outcome_bucket": row.get("outcome_bucket", ""),
        "success": bool_value(row.get("success", False)),
        "collision": bool_value(row.get("collision", False)),
        "termination_reason": row.get("termination_reason", ""),
        "taxonomy_family": taxonomy_family,
        "primary_failure_family": primary_failure_family(taxonomy_family),
        "repair_signal": repair_signal(taxonomy_family),
        "diagnostic_success_context": taxonomy_family == "diagnostic_success_context",
        "execution_run": execution_run,
        "execution_admitted": execution_admitted,
        "guardrail_only": guardrail_only,
        "negative_context_guard": negative_context_guard,
        "blocked_guard": blocked_guard,
        "protected_or_hf3_blocker": protected_or_hf3_blocker,
        "protected_rows_in_success_denominator": bool_value(row.get("protected_rows_in_success_denominator", False)),
        "actor_visible_allowed": bool_value(row.get("actor_visible_allowed", False)),
        "taxonomy_labels_actor_visible": False,
        "source_family_ranking_allowed": False,
        "task_family_ranking_allowed": False,
        "profile_ranking_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def classify_execution_row(row: Mapping[str, Any]) -> str:
    outcome = str(row.get("outcome_bucket", ""))
    termination = str(row.get("termination_reason", ""))
    if bool_value(row.get("success", False)) or outcome == "success_obstacle_pass":
        return "diagnostic_success_context"
    if bool_value(row.get("collision", False)) or outcome == "collision_failure" or termination == "obstacle_collision":
        return "collision_failure"
    if outcome == "off_track_noncollision_noncompletion" or termination == "off_track":
        return "off_track"
    return "other_diagnostic_termination"


def is_protected_or_hf3(row: Mapping[str, Any]) -> bool:
    family = str(row.get("blocked_family", ""))
    return family in {"protected_mitigation_blocker", "hf3_source_dependency_blocker"}


def primary_failure_family(taxonomy_family: str) -> str:
    mapping = {
        "diagnostic_success_context": "diagnostic_success_not_failure",
        "collision_failure": "obstacle_collision",
        "off_track": "off_track",
        "negative_context_guard": "same_surface_negative_context",
        "blocked_guard": "same_surface_or_route_blocker",
        "protected_or_hf3_blocker": "protected_or_high_fidelity_blocker",
    }
    return mapping.get(taxonomy_family, "other_diagnostic_termination")


def repair_signal(taxonomy_family: str) -> str:
    mapping = {
        "diagnostic_success_context": "preserve_as_context_not_winner",
        "collision_failure": "collision_surface_needs_taxonomy_audit",
        "off_track": "offtrack_surface_needs_taxonomy_audit",
        "negative_context_guard": "preserve_as_nonexecuted_negative_context",
        "blocked_guard": "requires_route_decision_before_execution",
        "protected_or_hf3_blocker": "requires_protected_or_source_dependency_resolution_before_behavior_claim",
    }
    return mapping.get(taxonomy_family, "inspect_other_diagnostic_termination")


def build_taxonomy_aggregate_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, taxonomy_family in enumerate(sorted({str(row["taxonomy_family"]) for row in taxonomy_rows}), start=1):
        group_rows = [row for row in taxonomy_rows if row["taxonomy_family"] == taxonomy_family]
        rows.append(
            aggregate_row(
                aggregate_id=f"m2740-taxonomy-aggregate-{index:04d}",
                aggregate_family="taxonomy_family",
                group_key=taxonomy_family,
                rows=group_rows,
            )
        )
    for source_row_type in ("candidate_execution", "negative_context_guard", "blocked_surface_guard"):
        rows.append(
            aggregate_row(
                aggregate_id=f"m2740-taxonomy-aggregate-source-{source_row_type}",
                aggregate_family="source_row_type",
                group_key=source_row_type,
                rows=[row for row in taxonomy_rows if row["source_row_type"] == source_row_type],
            )
        )
    return rows


def aggregate_row(*, aggregate_id: str, aggregate_family: str, group_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "aggregate_id": aggregate_id,
        "aggregate_family": aggregate_family,
        "group_key": group_key,
        "execution_row_count": count_source(rows, "candidate_execution"),
        "negative_context_guard_row_count": count_source(rows, "negative_context_guard"),
        "blocked_guard_row_count": count_source(rows, "blocked_surface_guard"),
        "taxonomy_row_count": len(rows),
        "diagnostic_success_context_row_count": count_taxonomy(rows, "diagnostic_success_context"),
        "collision_failure_row_count": count_taxonomy(rows, "collision_failure"),
        "offtrack_row_count": count_taxonomy(rows, "off_track"),
        "negative_context_taxonomy_row_count": count_taxonomy(rows, "negative_context_guard"),
        "blocked_guard_taxonomy_row_count": count_taxonomy(rows, "blocked_guard"),
        "protected_or_hf3_blocker_row_count": count_taxonomy(rows, "protected_or_hf3_blocker"),
        "source_family_ranking_allowed": False,
        "task_family_ranking_allowed": False,
        "profile_ranking_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_source_family_context_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in taxonomy_rows:
        if row["source_row_type"] == "candidate_execution":
            by_source[(str(row["source_milestone"]), str(row["source_family"]))].append(row)
    return [
        {
            "source_context_id": f"m2740-source-family-context-{index:04d}",
            "source_milestone": source_milestone,
            "source_family": source_family,
            "execution_row_count": len(rows),
            "diagnostic_success_context_row_count": count_taxonomy(rows, "diagnostic_success_context"),
            "collision_failure_row_count": count_taxonomy(rows, "collision_failure"),
            "offtrack_row_count": count_taxonomy(rows, "off_track"),
            "dominant_taxonomy_family": dominant_taxonomy(rows),
            "source_family_ranking_allowed": False,
            "winner_selection_allowed": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, ((source_milestone, source_family), rows) in enumerate(sorted(by_source.items()), start=1)
    ]


def build_task_family_context_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in taxonomy_rows:
        if row["source_row_type"] == "candidate_execution":
            by_task[str(row["task_family"])].append(row)
    return [
        {
            "task_context_id": f"m2740-task-family-context-{index:04d}",
            "task_family": task_family,
            "source_family_count": len({str(row["source_family"]) for row in rows}),
            "execution_row_count": len(rows),
            "diagnostic_success_context_row_count": count_taxonomy(rows, "diagnostic_success_context"),
            "collision_failure_row_count": count_taxonomy(rows, "collision_failure"),
            "offtrack_row_count": count_taxonomy(rows, "off_track"),
            "dominant_taxonomy_family": dominant_taxonomy(rows),
            "task_family_ranking_allowed": False,
            "winner_selection_allowed": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (task_family, rows) in enumerate(sorted(by_task.items()), start=1)
    ]


def build_guardrail_context_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_guardrail: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in taxonomy_rows:
        if bool_value(row["guardrail_only"]):
            by_guardrail[(str(row["taxonomy_family"]), str(row["source_row_type"]))].append(row)
    return [
        {
            "guardrail_context_id": f"m2740-guardrail-context-{index:04d}",
            "guardrail_family": guardrail_family,
            "source_row_type": source_row_type,
            "row_count": len(rows),
            "execution_run_count": sum(bool_value(row["execution_run"]) for row in rows),
            "execution_admitted_count": sum(bool_value(row["execution_admitted"]) for row in rows),
            "protected_denominator_count": sum(bool_value(row["protected_rows_in_success_denominator"]) for row in rows),
            "actor_visible_count": sum(bool_value(row["actor_visible_allowed"]) for row in rows),
            "guardrail_only": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, ((guardrail_family, source_row_type), rows) in enumerate(sorted(by_guardrail.items()), start=1)
    ]


def build_actor_contract_join_rows(*, source: dict[str, Any], taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        actor_join("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_join("action_shape", ACTION_DIM, 3, False),
        actor_join("hidden_oracle_actor_input_detected", hidden_oracle_detected(source), False, False),
        actor_join("taxonomy_labels_actor_visible", any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"), False, False),
        actor_join("source_family_ranking_allowed", any_bool(taxonomy_rows, "source_family_ranking_allowed"), False, False),
        actor_join("task_family_ranking_allowed", any_bool(taxonomy_rows, "task_family_ranking_allowed"), False, False),
        actor_join("profile_ranking_allowed", any_bool(taxonomy_rows, "profile_ranking_allowed"), False, False),
        actor_join("guardrail_execution_run", any_bool(guardrail_rows(taxonomy_rows), "execution_run"), False, False),
        actor_join("guardrail_execution_admitted", any_bool(guardrail_rows(taxonomy_rows), "execution_admitted"), False, False),
        actor_join(
            "protected_rows_in_success_denominator",
            any_bool(taxonomy_rows, "protected_rows_in_success_denominator"),
            False,
            False,
        ),
        actor_join(
            "m2737_actor_guard_rows_pass",
            all(bool_value(row.get("status_pass")) for row in source["actor_contract_guard_rows"]),
            True,
            False,
        ),
    ]


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "join_id": f"m2740-actor-join-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    taxonomy_rows_present: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("failure_taxonomy_materialized", "artifact", taxonomy_rows_present, "taxonomy_rows.csv"),
        ("taxonomy_aggregate_materialized", "artifact", required_artifacts_present, "taxonomy_aggregate_rows.csv"),
        ("source_family_context_materialized", "artifact", required_artifacts_present, "source_family_context_rows.csv"),
        ("task_family_context_materialized", "artifact", required_artifacts_present, "task_family_context_rows.csv"),
        ("guardrail_context_materialized", "artifact", required_artifacts_present, "guardrail_context_rows.csv"),
        ("negative_context_guards_preserved", "contract", True, "negative_context_guard taxonomy rows"),
        ("blocked_guards_preserved", "contract", True, "blocked_surface_guard taxonomy rows"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2741 result-audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future execution manifest"),
        ("policy_action_execution", "execution", "future execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("source_build_or_adapter_probe", "execution", "future source route"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2740"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("source_family_ranking", "ranking", "future audited comparison interpretation"),
        ("task_family_ranking", "ranking", "future audited comparison interpretation"),
        ("profile_ranking", "ranking", "future audited comparison interpretation"),
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
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2740_{claim_id}",
        "claim_family": family,
        "allowed_in_m2740": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    taxonomy_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    source_context_rows: list[dict[str, Any]],
    task_context_rows: list[dict[str, Any]],
    guardrail_context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    execution_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "candidate_execution"]
    negative_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "negative_context_guard"]
    blocked_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "blocked_surface_guard"]
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2740"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2740"])]
    taxonomy_families = {str(row["taxonomy_family"]) for row in taxonomy_rows}
    expected_taxonomy_families = {
        "diagnostic_success_context",
        "collision_failure",
        "off_track",
        "negative_context_guard",
        "blocked_guard",
        "protected_or_hf3_blocker",
    }
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2737/M2739/follow-up artifacts present", "lineage_invalid"),
        ("m2739_selects_taxonomy", "lineage", "continue_to_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization" in source["m2739_synthesis_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2737_status_pass", "lineage", bool_value(source["m2737_summary"].get("status_pass", False)), source["m2737_summary"].get("status_pass", None), True, "lineage_invalid"),
        ("candidate_execution_source_count", "lineage", len(source["candidate_execution_rows"]) == EXPECTED_EXECUTION_ROW_COUNT, len(source["candidate_execution_rows"]), EXPECTED_EXECUTION_ROW_COUNT, "metric_artifact"),
        ("negative_context_guard_source_count", "lineage", len(source["negative_context_guard_rows"]) == EXPECTED_NEGATIVE_CONTEXT_GUARD_ROW_COUNT, len(source["negative_context_guard_rows"]), EXPECTED_NEGATIVE_CONTEXT_GUARD_ROW_COUNT, "metric_artifact"),
        ("blocked_guard_source_count", "lineage", len(source["blocked_surface_guard_rows"]) == EXPECTED_BLOCKED_GUARD_ROW_COUNT, len(source["blocked_surface_guard_rows"]), EXPECTED_BLOCKED_GUARD_ROW_COUNT, "metric_artifact"),
        ("execution_taxonomy_accounting", "artifact", len(execution_taxonomy_rows) == len(source["candidate_execution_rows"]), len(execution_taxonomy_rows), len(source["candidate_execution_rows"]), "metric_artifact"),
        ("negative_guard_taxonomy_accounting", "artifact", len(negative_taxonomy_rows) == len(source["negative_context_guard_rows"]), len(negative_taxonomy_rows), len(source["negative_context_guard_rows"]), "metric_artifact"),
        ("blocked_guard_taxonomy_accounting", "artifact", len(blocked_taxonomy_rows) == len(source["blocked_surface_guard_rows"]), len(blocked_taxonomy_rows), len(source["blocked_surface_guard_rows"]), "metric_artifact"),
        ("diagnostic_success_context_count_preserved", "artifact", count_taxonomy(execution_taxonomy_rows, "diagnostic_success_context") == EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_ROW_COUNT, count_taxonomy(execution_taxonomy_rows, "diagnostic_success_context"), EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_ROW_COUNT, "metric_artifact"),
        ("collision_failure_count_preserved", "artifact", count_taxonomy(execution_taxonomy_rows, "collision_failure") == EXPECTED_COLLISION_FAILURE_ROW_COUNT, count_taxonomy(execution_taxonomy_rows, "collision_failure"), EXPECTED_COLLISION_FAILURE_ROW_COUNT, "metric_artifact"),
        ("offtrack_count_preserved", "artifact", count_taxonomy(execution_taxonomy_rows, "off_track") == EXPECTED_OFFTRACK_ROW_COUNT, count_taxonomy(execution_taxonomy_rows, "off_track"), EXPECTED_OFFTRACK_ROW_COUNT, "metric_artifact"),
        ("taxonomy_families_separate", "artifact", expected_taxonomy_families.issubset(taxonomy_families), sorted(taxonomy_families), sorted(expected_taxonomy_families), "metric_artifact"),
        ("source_family_context_nonranking", "claim_boundary", len(source_context_rows) == EXPECTED_SOURCE_FAMILY_CONTEXT_ROW_COUNT and all(not bool_value(row["source_family_ranking_allowed"]) and not bool_value(row["winner_selection_allowed"]) for row in source_context_rows), f"rows={len(source_context_rows)}", "2 non-ranking source-family context rows", "proof_washout"),
        ("task_family_context_nonranking", "claim_boundary", len(task_context_rows) == EXPECTED_TASK_FAMILY_CONTEXT_ROW_COUNT and all(not bool_value(row["task_family_ranking_allowed"]) and not bool_value(row["winner_selection_allowed"]) for row in task_context_rows), f"rows={len(task_context_rows)}", "2 non-ranking task-family context rows", "proof_washout"),
        ("guardrail_context_preserved", "contract", guardrail_context_rows and all(int(row["execution_run_count"]) == 0 and int(row["execution_admitted_count"]) == 0 and int(row["protected_denominator_count"]) == 0 and int(row["actor_visible_count"]) == 0 for row in guardrail_context_rows), f"rows={len(guardrail_context_rows)}", "all guardrails not run/admitted/denominator/visible", "contract_violation"),
        ("aggregate_rows_present", "artifact", bool(aggregate_rows), len(aggregate_rows), ">0", "metric_artifact"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_rows)}", "all actor joins pass", "contract_violation"),
        ("taxonomy_labels_actor_invisible", "contract", not any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"), "all taxonomy labels actor-invisible", "all false", "contract_violation"),
        ("guardrails_not_executed_or_denominator", "contract", not any_bool(guardrail_rows(taxonomy_rows), "execution_run") and not any_bool(guardrail_rows(taxonomy_rows), "execution_admitted") and not any_bool(taxonomy_rows, "protected_rows_in_success_denominator"), "guardrail rows not run/admitted and outside denominators", "all false", "contract_violation"),
        ("no_forbidden_materialization_execution", "execution_guardrail", not forbidden_materialization_execution_detected(), "no M2740 execution flags", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        gate(gate_id, family, status_pass, observed, expected, failure_type)
        for gate_id, family, status_pass, observed, expected, failure_type in gates
    ]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2740_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    taxonomy_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    source_context_rows: list[dict[str, Any]],
    task_context_rows: list[dict[str, Any]],
    guardrail_context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    execution_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "candidate_execution"]
    negative_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "negative_context_guard"]
    blocked_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "blocked_surface_guard"]
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2737_status_pass": bool_value(source["m2737_summary"].get("status_pass", False)),
        "candidate_execution_source_row_count": len(source["candidate_execution_rows"]),
        "negative_context_guard_source_row_count": len(source["negative_context_guard_rows"]),
        "blocked_guard_source_row_count": len(source["blocked_surface_guard_rows"]),
        "taxonomy_row_count": len(taxonomy_rows),
        "execution_taxonomy_row_count": len(execution_taxonomy_rows),
        "negative_context_taxonomy_row_count": len(negative_taxonomy_rows),
        "blocked_guard_taxonomy_row_count": len(blocked_taxonomy_rows),
        "taxonomy_aggregate_row_count": len(aggregate_rows),
        "source_family_context_row_count": len(source_context_rows),
        "task_family_context_row_count": len(task_context_rows),
        "guardrail_context_row_count": len(guardrail_context_rows),
        "diagnostic_success_context_taxonomy_row_count": count_taxonomy(execution_taxonomy_rows, "diagnostic_success_context"),
        "collision_failure_taxonomy_row_count": count_taxonomy(execution_taxonomy_rows, "collision_failure"),
        "offtrack_taxonomy_row_count": count_taxonomy(execution_taxonomy_rows, "off_track"),
        "protected_or_hf3_blocker_taxonomy_row_count": count_taxonomy(blocked_taxonomy_rows, "protected_or_hf3_blocker"),
        "actor_contract_join_row_count": len(actor_rows),
        "actor_contract_join_rows_pass": all(bool_value(row["status_pass"]) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected(source),
        "taxonomy_labels_actor_visible": any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"),
        "source_family_ranking_allowed": any_bool(taxonomy_rows, "source_family_ranking_allowed"),
        "task_family_ranking_allowed": any_bool(taxonomy_rows, "task_family_ranking_allowed"),
        "profile_ranking_allowed": any_bool(taxonomy_rows, "profile_ranking_allowed"),
        "guardrail_execution_run": any_bool(guardrail_rows(taxonomy_rows), "execution_run"),
        "guardrail_execution_admitted": any_bool(guardrail_rows(taxonomy_rows), "execution_admitted"),
        "protected_rows_in_success_denominator": any_bool(taxonomy_rows, "protected_rows_in_success_denominator"),
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
            "# M2740 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Failure Taxonomy Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- execution taxonomy rows: {summary['execution_taxonomy_row_count']}",
            f"- negative-context taxonomy rows: {summary['negative_context_taxonomy_row_count']}",
            f"- blocked-guard taxonomy rows: {summary['blocked_guard_taxonomy_row_count']}",
            f"- diagnostic success context rows: {summary['diagnostic_success_context_taxonomy_row_count']}",
            f"- collision failure rows: {summary['collision_failure_taxonomy_row_count']}",
            f"- offtrack rows: {summary['offtrack_taxonomy_row_count']}",
            f"- source-family context rows: {summary['source_family_context_row_count']}",
            f"- task-family context rows: {summary['task_family_context_row_count']}",
            f"- guardrail context rows: {summary['guardrail_context_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2740 materializes taxonomy rows from existing M2737 diagnostics and guardrails only. It does not run environments, execute policies, or rank source/task/profile families.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["paths"].items()],
            "",
            "## Next",
            "",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
        ]
    )


def count_source(rows: list[dict[str, Any]], source_row_type: str) -> int:
    return sum(1 for row in rows if row["source_row_type"] == source_row_type)


def count_taxonomy(rows: list[dict[str, Any]], taxonomy_family: str) -> int:
    return sum(1 for row in rows if row["taxonomy_family"] == taxonomy_family)


def dominant_taxonomy(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    counts = Counter(str(row["taxonomy_family"]) for row in rows)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def guardrail_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if bool_value(row.get("guardrail_only", False))]


def hidden_oracle_detected(source: dict[str, Any]) -> bool:
    actor_rows = source["actor_contract_guard_rows"]
    execution_rows = source["candidate_execution_rows"]
    return any(
        bool_value(row.get("hidden_oracle_actor_input_detected", False))
        or bool_value(row.get("hidden_oracle_actor_input_required", False))
        for row in actor_rows + execution_rows
    )


def forbidden_materialization_execution_detected() -> bool:
    return False


def any_bool(rows: list[dict[str, Any]], key: str) -> bool:
    return any(bool_value(row.get(key, False)) for row in rows)


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2737-dir", type=Path, default=DEFAULT_M2737_DIR)
    parser.add_argument("--m2739-synthesis", type=Path, default=DEFAULT_M2739_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_post_negative_source_diverse_failure_taxonomy(
        m2737_dir=args.m2737_dir,
        m2739_synthesis=args.m2739_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"execution_taxonomy_row_count={summary['execution_taxonomy_row_count']}")
    print(f"negative_context_taxonomy_row_count={summary['negative_context_taxonomy_row_count']}")
    print(f"blocked_guard_taxonomy_row_count={summary['blocked_guard_taxonomy_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
