"""Materialize failure taxonomy for the current-M1690 exact-executable reentry branch.

M2719 consumes M2716 diagnostic execution artifacts after M2718 synthesis. It
does not reset, step, roll out policies, replay, validate, train, rank profiles,
or promote checkpoints. The output is a row-level failure taxonomy for branch
planning only.
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
    "m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "failure-taxonomy-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "failure-taxonomy-materialization-result-audit"
)
DEFAULT_M2716_DIR = Path(
    "runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight"
)
DEFAULT_M2718_SYNTHESIS = Path(
    "docs/m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit.json"
)

EXPECTED_EXACT_EXECUTION_ROW_COUNT = 36
EXPECTED_PROTECTED_EXCLUSION_ROW_COUNT = 12
EXPECTED_DIAGNOSTIC_SUCCESS_ROW_COUNT = 3
EXPECTED_OBSTACLE_COLLISION_ROW_COUNT = 2
EXPECTED_OFFTRACK_ROW_COUNT = 31

CLAIM_SCOPE = (
    "M2719 Route A current-M1690 exact-executable reentry failure taxonomy "
    "materialization only; no reset, step, rollout, replay, validation, "
    "training, PPO, private holdout, profile-specific tuning, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-response, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
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
    "anchor_task_source_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "success",
    "collision",
    "termination_reason",
    "taxonomy_family",
    "primary_failure_family",
    "repair_signal",
    "diagnostic_success_context",
    "protected_excluded",
    "protected_execution_run",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "taxonomy_labels_actor_visible",
    "profile_ranking_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "group_key",
    "exact_execution_row_count",
    "protected_exclusion_row_count",
    "taxonomy_row_count",
    "diagnostic_success_row_count",
    "obstacle_collision_row_count",
    "offtrack_row_count",
    "protected_excluded_row_count",
    "profile_ranking_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
PROFILE_FIELDNAMES = [
    "profile_context_id",
    "profile_name",
    "exact_execution_row_count",
    "diagnostic_success_row_count",
    "obstacle_collision_row_count",
    "offtrack_row_count",
    "dominant_taxonomy_family",
    "profile_ranking_allowed",
    "winner_selection_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
ANCHOR_FIELDNAMES = [
    "anchor_context_id",
    "anchor_task_source_id",
    "exact_execution_row_count",
    "diagnostic_success_row_count",
    "obstacle_collision_row_count",
    "offtrack_row_count",
    "dominant_taxonomy_family",
    "repair_target_candidate",
    "diagnostic_only_no_verdict",
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
    "allowed_in_m2719",
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
    "profile_taxonomy_context_rows",
    "anchor_taxonomy_context_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_current_m1690_exact_executable_reentry_failure_taxonomy(
    *,
    m2716_dir: Path | str = DEFAULT_M2716_DIR,
    m2718_synthesis: Path | str = DEFAULT_M2718_SYNTHESIS,
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
        m2716_dir=Path(m2716_dir),
        m2718_synthesis=Path(m2718_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )
    exact_rows = source["exact_execution_rows"]
    protected_rows = source["protected_proposal_exclusion_audit_rows"]
    taxonomy_rows = build_taxonomy_rows(exact_rows=exact_rows, protected_rows=protected_rows)
    aggregate_rows = build_taxonomy_aggregate_rows(taxonomy_rows)
    profile_rows = build_profile_taxonomy_context_rows(taxonomy_rows)
    anchor_rows = build_anchor_taxonomy_context_rows(taxonomy_rows)
    actor_rows = build_actor_contract_join_rows(source=source, taxonomy_rows=taxonomy_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        taxonomy_rows_present=bool(taxonomy_rows),
        required_artifacts_present=False,
    )
    source_rows = build_source_accounting_rows(source=source)
    gate_rows = build_gate_matrix_rows(
        source=source,
        taxonomy_rows=taxonomy_rows,
        aggregate_rows=aggregate_rows,
        profile_rows=profile_rows,
        anchor_rows=anchor_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["source_accounting_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["taxonomy_rows"], taxonomy_rows, fieldnames=TAXONOMY_FIELDNAMES)
    write_csv_rows(paths["taxonomy_aggregate_rows"], aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["profile_taxonomy_context_rows"], profile_rows, fieldnames=PROFILE_FIELDNAMES)
    write_csv_rows(paths["anchor_taxonomy_context_rows"], anchor_rows, fieldnames=ANCHOR_FIELDNAMES)
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
        profile_rows=profile_rows,
        anchor_rows=anchor_rows,
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
        profile_rows=profile_rows,
        anchor_rows=anchor_rows,
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
        profile_rows=profile_rows,
        anchor_rows=anchor_rows,
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
        profile_rows=profile_rows,
        anchor_rows=anchor_rows,
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
        "profile_taxonomy_context_rows": output_dir / "profile_taxonomy_context_rows.csv",
        "anchor_taxonomy_context_rows": output_dir / "anchor_taxonomy_context_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2716_dir: Path,
    m2718_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2718_synthesis_doc": m2718_synthesis,
        "m2716_summary": m2716_dir / "summary.json",
        "m2716_exact_execution_rows": m2716_dir / "exact_execution_rows.csv",
        "m2716_profile_aggregate": m2716_dir / "profile_aggregate.csv",
        "m2716_anchor_aggregate": m2716_dir / "anchor_aggregate.csv",
        "m2716_protected_exclusion_audit_rows": m2716_dir / "protected_proposal_exclusion_audit_rows.csv",
        "m2716_actor_contract_join_rows": m2716_dir / "actor_contract_join_rows.csv",
        "m2716_claim_boundary_rows": m2716_dir / "claim_boundary_rows.csv",
        "m2716_gate_matrix": m2716_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2718_synthesis_text": paths["m2718_synthesis_doc"].read_text(encoding="utf-8")
        if source_exists["m2718_synthesis_doc"]
        else "",
        "m2716_summary": read_json(paths["m2716_summary"]) if source_exists["m2716_summary"] else {},
        "exact_execution_rows": read_csv_rows(paths["m2716_exact_execution_rows"]),
        "profile_aggregate_rows": read_csv_rows(paths["m2716_profile_aggregate"]),
        "anchor_aggregate_rows": read_csv_rows(paths["m2716_anchor_aggregate"]),
        "protected_proposal_exclusion_audit_rows": read_csv_rows(paths["m2716_protected_exclusion_audit_rows"]),
        "actor_contract_join_rows": read_csv_rows(paths["m2716_actor_contract_join_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2716_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2716_gate_matrix"]),
    }


def build_source_accounting_rows(*, source: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {
        "m2716_exact_execution_rows": len(source["exact_execution_rows"]),
        "m2716_profile_aggregate": len(source["profile_aggregate_rows"]),
        "m2716_anchor_aggregate": len(source["anchor_aggregate_rows"]),
        "m2716_protected_exclusion_audit_rows": len(source["protected_proposal_exclusion_audit_rows"]),
        "m2716_actor_contract_join_rows": len(source["actor_contract_join_rows"]),
        "m2716_claim_boundary_rows": len(source["claim_boundary_rows"]),
        "m2716_gate_matrix": len(source["gate_matrix"]),
    }
    rows = []
    for index, (key, path) in enumerate(source["paths"].items(), start=1):
        present = bool(source["source_exists"].get(key, False))
        rows.append(
            {
                "source_id": f"m2719-source-{index:04d}",
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
    exact_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(exact_rows, start=1):
        taxonomy_family = classify_exact_row(row)
        rows.append(
            {
                "taxonomy_id": f"m2719-taxonomy-exact-{index:04d}",
                "source_row_type": "exact_execution",
                "candidate_id": row.get("candidate_id", ""),
                "anchor_task_source_id": row.get("anchor_task_source_id", ""),
                "workload_id": row.get("workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "success": bool_value(row.get("success", False)),
                "collision": bool_value(row.get("collision", False)),
                "termination_reason": row.get("termination_reason", ""),
                "taxonomy_family": taxonomy_family,
                "primary_failure_family": primary_failure_family(taxonomy_family),
                "repair_signal": repair_signal(taxonomy_family),
                "diagnostic_success_context": taxonomy_family == "diagnostic_success",
                "protected_excluded": False,
                "protected_execution_run": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "taxonomy_labels_actor_visible": False,
                "profile_ranking_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for index, row in enumerate(protected_rows, start=1):
        rows.append(
            {
                "taxonomy_id": f"m2719-taxonomy-protected-excluded-{index:04d}",
                "source_row_type": "protected_proposal_exclusion",
                "candidate_id": row.get("exclusion_id", ""),
                "anchor_task_source_id": "",
                "workload_id": row.get("proposed_workload_id", ""),
                "task_source_id": row.get("support_candidate_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": "protected_proposal",
                "success": False,
                "collision": False,
                "termination_reason": "protected_proposal_not_executed",
                "taxonomy_family": "protected_excluded",
                "primary_failure_family": "protected_executable_surface_absent",
                "repair_signal": "requires_exact_executable_surface_before_behavior_claim",
                "diagnostic_success_context": False,
                "protected_excluded": True,
                "protected_execution_run": bool_value(row.get("m2716_execution_run", False)),
                "protected_rows_in_success_denominator": bool_value(
                    row.get("protected_rows_in_success_denominator", False)
                ),
                "actor_visible_allowed": False,
                "taxonomy_labels_actor_visible": False,
                "profile_ranking_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def classify_exact_row(row: Mapping[str, Any]) -> str:
    if bool_value(row.get("success", False)):
        return "diagnostic_success"
    if bool_value(row.get("collision", False)) or str(row.get("termination_reason", "")) == "obstacle_collision":
        return "obstacle_collision"
    if str(row.get("termination_reason", "")) == "off_track":
        return "off_track"
    return "other_diagnostic_termination"


def primary_failure_family(taxonomy_family: str) -> str:
    mapping = {
        "diagnostic_success": "diagnostic_success_not_failure",
        "obstacle_collision": "obstacle_collision",
        "off_track": "off_track",
        "protected_excluded": "protected_executable_surface_absent",
    }
    return mapping.get(taxonomy_family, "other_diagnostic_termination")


def repair_signal(taxonomy_family: str) -> str:
    mapping = {
        "diagnostic_success": "preserve_as_context_not_winner",
        "obstacle_collision": "collision_surface_needs_taxonomy_audit",
        "off_track": "offtrack_surface_needs_taxonomy_audit",
        "protected_excluded": "requires_exact_executable_surface_before_behavior_claim",
    }
    return mapping.get(taxonomy_family, "inspect_other_diagnostic_termination")


def build_taxonomy_aggregate_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    exact_rows = [row for row in taxonomy_rows if row["source_row_type"] == "exact_execution"]
    protected_rows = [row for row in taxonomy_rows if row["source_row_type"] == "protected_proposal_exclusion"]
    for index, taxonomy_family in enumerate(sorted({str(row["taxonomy_family"]) for row in taxonomy_rows}), start=1):
        group_rows = [row for row in taxonomy_rows if row["taxonomy_family"] == taxonomy_family]
        rows.append(
            aggregate_row(
                aggregate_id=f"m2719-taxonomy-aggregate-{index:04d}",
                aggregate_family="taxonomy_family",
                group_key=taxonomy_family,
                rows=group_rows,
            )
        )
    rows.append(
        aggregate_row(
            aggregate_id="m2719-taxonomy-aggregate-all-exact-execution",
            aggregate_family="source_row_type",
            group_key="exact_execution",
            rows=exact_rows,
        )
    )
    rows.append(
        aggregate_row(
            aggregate_id="m2719-taxonomy-aggregate-all-protected-excluded",
            aggregate_family="source_row_type",
            group_key="protected_proposal_exclusion",
            rows=protected_rows,
        )
    )
    return rows


def aggregate_row(*, aggregate_id: str, aggregate_family: str, group_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "aggregate_id": aggregate_id,
        "aggregate_family": aggregate_family,
        "group_key": group_key,
        "exact_execution_row_count": count_source(rows, "exact_execution"),
        "protected_exclusion_row_count": count_source(rows, "protected_proposal_exclusion"),
        "taxonomy_row_count": len(rows),
        "diagnostic_success_row_count": count_taxonomy(rows, "diagnostic_success"),
        "obstacle_collision_row_count": count_taxonomy(rows, "obstacle_collision"),
        "offtrack_row_count": count_taxonomy(rows, "off_track"),
        "protected_excluded_row_count": count_taxonomy(rows, "protected_excluded"),
        "profile_ranking_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_profile_taxonomy_context_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in taxonomy_rows:
        if row["source_row_type"] == "exact_execution":
            by_profile[str(row["profile_name"])].append(row)
    return [
        {
            "profile_context_id": f"m2719-profile-taxonomy-context-{index:04d}",
            "profile_name": profile,
            "exact_execution_row_count": len(rows),
            "diagnostic_success_row_count": count_taxonomy(rows, "diagnostic_success"),
            "obstacle_collision_row_count": count_taxonomy(rows, "obstacle_collision"),
            "offtrack_row_count": count_taxonomy(rows, "off_track"),
            "dominant_taxonomy_family": dominant_taxonomy(rows),
            "profile_ranking_allowed": False,
            "winner_selection_allowed": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (profile, rows) in enumerate(sorted(by_profile.items()), start=1)
    ]


def build_anchor_taxonomy_context_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in taxonomy_rows:
        if row["source_row_type"] == "exact_execution":
            by_anchor[str(row["anchor_task_source_id"])].append(row)
    return [
        {
            "anchor_context_id": f"m2719-anchor-taxonomy-context-{index:04d}",
            "anchor_task_source_id": anchor,
            "exact_execution_row_count": len(rows),
            "diagnostic_success_row_count": count_taxonomy(rows, "diagnostic_success"),
            "obstacle_collision_row_count": count_taxonomy(rows, "obstacle_collision"),
            "offtrack_row_count": count_taxonomy(rows, "off_track"),
            "dominant_taxonomy_family": dominant_taxonomy(rows),
            "repair_target_candidate": dominant_taxonomy(rows) in {"off_track", "obstacle_collision"},
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (anchor, rows) in enumerate(sorted(by_anchor.items()), start=1)
    ]


def build_actor_contract_join_rows(*, source: dict[str, Any], taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        actor_join("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_join("action_shape", ACTION_DIM, 3, False),
        actor_join("hidden_oracle_actor_input_detected", hidden_oracle_detected(source), False, False),
        actor_join("taxonomy_labels_actor_visible", any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"), False, False),
        actor_join("profile_ranking_allowed", any_bool(taxonomy_rows, "profile_ranking_allowed"), False, False),
        actor_join("protected_execution_run", any_bool(taxonomy_rows, "protected_execution_run"), False, False),
        actor_join(
            "protected_rows_in_success_denominator",
            any_bool(taxonomy_rows, "protected_rows_in_success_denominator"),
            False,
            False,
        ),
        actor_join("m2716_actor_join_rows_pass", all(bool_value(row.get("status_pass")) for row in source["actor_contract_join_rows"]), True, False),
    ]


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "join_id": f"m2719-actor-join-{field}",
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
        ("profile_context_materialized", "artifact", required_artifacts_present, "profile_taxonomy_context_rows.csv"),
        ("anchor_context_materialized", "artifact", required_artifacts_present, "anchor_taxonomy_context_rows.csv"),
        ("protected_exclusions_preserved", "contract", True, "protected_excluded taxonomy rows"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2720 result-audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2719"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_response_sufficiency_result", "paper", "future fair comparison audit"),
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
        "claim_id": f"m2719_{claim_id}",
        "claim_family": family,
        "allowed_in_m2719": allowed,
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
    profile_rows: list[dict[str, Any]],
    anchor_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    exact_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "exact_execution"]
    protected_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "protected_proposal_exclusion"]
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2719"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2719"])]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2716/M2718/follow-up artifacts present", "lineage_invalid"),
        ("m2718_selects_taxonomy", "lineage", "continue_to_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_preflight" in source["m2718_synthesis_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2716_status_pass", "lineage", bool_value(source["m2716_summary"].get("status_pass", False)), source["m2716_summary"].get("status_pass", None), True, "lineage_invalid"),
        ("exact_execution_source_count", "lineage", len(source["exact_execution_rows"]) == EXPECTED_EXACT_EXECUTION_ROW_COUNT, len(source["exact_execution_rows"]), EXPECTED_EXACT_EXECUTION_ROW_COUNT, "metric_artifact"),
        ("protected_exclusion_source_count", "lineage", len(source["protected_proposal_exclusion_audit_rows"]) == EXPECTED_PROTECTED_EXCLUSION_ROW_COUNT, len(source["protected_proposal_exclusion_audit_rows"]), EXPECTED_PROTECTED_EXCLUSION_ROW_COUNT, "metric_artifact"),
        ("exact_taxonomy_accounting", "artifact", len(exact_taxonomy_rows) == len(source["exact_execution_rows"]), len(exact_taxonomy_rows), len(source["exact_execution_rows"]), "metric_artifact"),
        ("protected_taxonomy_accounting", "artifact", len(protected_taxonomy_rows) == len(source["protected_proposal_exclusion_audit_rows"]), len(protected_taxonomy_rows), len(source["protected_proposal_exclusion_audit_rows"]), "metric_artifact"),
        ("diagnostic_success_count_preserved", "artifact", count_taxonomy(exact_taxonomy_rows, "diagnostic_success") == EXPECTED_DIAGNOSTIC_SUCCESS_ROW_COUNT, count_taxonomy(exact_taxonomy_rows, "diagnostic_success"), EXPECTED_DIAGNOSTIC_SUCCESS_ROW_COUNT, "metric_artifact"),
        ("obstacle_collision_count_preserved", "artifact", count_taxonomy(exact_taxonomy_rows, "obstacle_collision") == EXPECTED_OBSTACLE_COLLISION_ROW_COUNT, count_taxonomy(exact_taxonomy_rows, "obstacle_collision"), EXPECTED_OBSTACLE_COLLISION_ROW_COUNT, "metric_artifact"),
        ("offtrack_count_preserved", "artifact", count_taxonomy(exact_taxonomy_rows, "off_track") == EXPECTED_OFFTRACK_ROW_COUNT, count_taxonomy(exact_taxonomy_rows, "off_track"), EXPECTED_OFFTRACK_ROW_COUNT, "metric_artifact"),
        ("profile_context_nonranking", "claim_boundary", profile_rows and all(not bool_value(row["profile_ranking_allowed"]) and not bool_value(row["winner_selection_allowed"]) for row in profile_rows), f"rows={len(profile_rows)}", "all profile rows non-ranking", "proof_washout"),
        ("anchor_context_present", "artifact", bool(anchor_rows), len(anchor_rows), ">0", "metric_artifact"),
        ("aggregate_rows_present", "artifact", bool(aggregate_rows), len(aggregate_rows), ">0", "metric_artifact"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_rows)}", "all actor joins pass", "contract_violation"),
        ("taxonomy_labels_actor_invisible", "contract", not any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"), "all taxonomy labels actor-invisible", "all false", "contract_violation"),
        ("protected_not_executed_or_denominator", "contract", not any_bool(taxonomy_rows, "protected_execution_run") and not any_bool(taxonomy_rows, "protected_rows_in_success_denominator"), "protected excluded rows not run and outside denominators", "all false", "contract_violation"),
        ("no_forbidden_execution", "execution_guardrail", not forbidden_execution_detected(source), "no new execution flags", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        gate(gate_id, family, status_pass, observed, expected, failure_type)
        for gate_id, family, status_pass, observed, expected, failure_type in gates
    ]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2719_{gate_id}",
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
    profile_rows: list[dict[str, Any]],
    anchor_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    exact_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "exact_execution"]
    protected_taxonomy_rows = [row for row in taxonomy_rows if row["source_row_type"] == "protected_proposal_exclusion"]
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2716_status_pass": bool_value(source["m2716_summary"].get("status_pass", False)),
        "exact_execution_source_row_count": len(source["exact_execution_rows"]),
        "protected_exclusion_source_row_count": len(source["protected_proposal_exclusion_audit_rows"]),
        "taxonomy_row_count": len(taxonomy_rows),
        "exact_execution_taxonomy_row_count": len(exact_taxonomy_rows),
        "protected_exclusion_taxonomy_row_count": len(protected_taxonomy_rows),
        "taxonomy_aggregate_row_count": len(aggregate_rows),
        "profile_taxonomy_context_row_count": len(profile_rows),
        "anchor_taxonomy_context_row_count": len(anchor_rows),
        "diagnostic_success_taxonomy_row_count": count_taxonomy(exact_taxonomy_rows, "diagnostic_success"),
        "obstacle_collision_taxonomy_row_count": count_taxonomy(exact_taxonomy_rows, "obstacle_collision"),
        "offtrack_taxonomy_row_count": count_taxonomy(exact_taxonomy_rows, "off_track"),
        "protected_excluded_taxonomy_row_count": count_taxonomy(protected_taxonomy_rows, "protected_excluded"),
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
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected(source),
        "taxonomy_labels_actor_visible": any_bool(taxonomy_rows, "taxonomy_labels_actor_visible"),
        "profile_ranking_allowed": any_bool(taxonomy_rows, "profile_ranking_allowed"),
        "protected_execution_run": any_bool(taxonomy_rows, "protected_execution_run"),
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
        "current_response_sufficiency_claim_made": False,
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
            "# M2719 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Failure Taxonomy Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- exact execution taxonomy rows: {summary['exact_execution_taxonomy_row_count']}",
            f"- protected exclusion taxonomy rows: {summary['protected_exclusion_taxonomy_row_count']}",
            f"- diagnostic success rows: {summary['diagnostic_success_taxonomy_row_count']}",
            f"- obstacle collision rows: {summary['obstacle_collision_taxonomy_row_count']}",
            f"- offtrack rows: {summary['offtrack_taxonomy_row_count']}",
            f"- profile context rows: {summary['profile_taxonomy_context_row_count']}",
            f"- anchor context rows: {summary['anchor_taxonomy_context_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2719 materializes taxonomy rows from existing M2716 diagnostics only. It does not run environments or rank profiles.",
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


def hidden_oracle_detected(source: dict[str, Any]) -> bool:
    return any(
        bool_value(row.get("hidden_oracle_actor_input_detected", False))
        or bool_value(row.get("hidden_oracle_actor_input_required", False))
        for row in source["exact_execution_rows"] + source["actor_contract_join_rows"]
    )


def forbidden_execution_detected(source: dict[str, Any]) -> bool:
    forbidden_keys = (
        "training_started",
        "training_run",
        "replay_started",
        "replay_run",
        "ppo_used",
        "private_holdout_used",
        "profile_specific_tuning",
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "driver_performance_claim_made",
        "paper_claim_made",
        "current_sim_verdict_claim_made",
        "level3_self_id_claim_made",
    )
    return any(bool_value(row.get(key, False)) for row in source["exact_execution_rows"] for key in forbidden_keys)


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
    parser.add_argument("--m2716-dir", type=Path, default=DEFAULT_M2716_DIR)
    parser.add_argument("--m2718-synthesis", type=Path, default=DEFAULT_M2718_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_current_m1690_exact_executable_reentry_failure_taxonomy(
        m2716_dir=args.m2716_dir,
        m2718_synthesis=args.m2718_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"exact_execution_taxonomy_row_count={summary['exact_execution_taxonomy_row_count']}")
    print(f"protected_exclusion_taxonomy_row_count={summary['protected_exclusion_taxonomy_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
