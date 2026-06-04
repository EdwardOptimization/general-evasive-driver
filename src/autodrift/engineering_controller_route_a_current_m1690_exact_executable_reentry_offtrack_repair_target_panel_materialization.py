"""Materialize an offtrack repair target panel from M2719 taxonomy artifacts.

M2721 is a no-rollout materialization step. It converts accepted taxonomy rows
into target, caution, context, and protected-exclusion slices before any repair
design or execution extension.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-target-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2722-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-target-panel-materialization-result-audit"
)
DEFAULT_M2719_DIR = Path(
    "runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy"
)
DEFAULT_M2720_AUDIT = Path(
    "docs/m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2721_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2722-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-result-audit.json"
)

EXPECTED_OFFTRACK_TARGET_COUNT = 31
EXPECTED_COLLISION_CAUTION_COUNT = 2
EXPECTED_SUCCESS_CONTEXT_COUNT = 3
EXPECTED_PROTECTED_EXCLUSION_COUNT = 12

CLAIM_SCOPE = (
    "M2721 Route A current-M1690 exact-executable reentry offtrack repair target "
    "panel materialization only; no reset, step, rollout, replay, validation, "
    "training, PPO, private holdout, profile-specific tuning, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-performance, "
    "paper, finite-window-vs-GRU, current-response, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity validation "
    "readiness or result, full ideal driver completion, or level3 self-identification"
)

SLICE_FIELDNAMES = [
    "panel_row_id",
    "source_taxonomy_id",
    "candidate_id",
    "anchor_task_source_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "taxonomy_family",
    "panel_slice",
    "repair_priority",
    "target_panel_admitted",
    "execution_scheduled",
    "profile_ranking_allowed",
    "winner_selection_allowed",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "target_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "path",
    "present",
    "row_count",
    "status_pass",
    "claim_boundary",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "group_key",
    "row_count",
    "offtrack_target_row_count",
    "collision_caution_row_count",
    "diagnostic_success_context_row_count",
    "protected_exclusion_row_count",
    "execution_scheduled",
    "profile_ranking_allowed",
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
    "allowed_in_m2721",
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
    "offtrack_target_rows",
    "collision_caution_rows",
    "diagnostic_success_context_rows",
    "protected_exclusion_rows",
    "target_panel_aggregate_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_offtrack_repair_target_panel(
    *,
    m2719_dir: Path | str = DEFAULT_M2719_DIR,
    m2720_audit: Path | str = DEFAULT_M2720_AUDIT,
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
        m2719_dir=Path(m2719_dir),
        m2720_audit=Path(m2720_audit),
        follow_up_manifest=Path(follow_up_manifest),
    )
    slice_rows = build_slice_rows(source["taxonomy_rows"])
    offtrack_rows = [row for row in slice_rows if row["panel_slice"] == "offtrack_target"]
    collision_rows = [row for row in slice_rows if row["panel_slice"] == "collision_caution"]
    success_rows = [row for row in slice_rows if row["panel_slice"] == "diagnostic_success_context"]
    protected_rows = [row for row in slice_rows if row["panel_slice"] == "protected_exclusion"]
    aggregate_rows = build_aggregate_rows(slice_rows)
    actor_rows = build_actor_contract_join_rows(source=source, slice_rows=slice_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        panel_rows_present=bool(slice_rows),
        required_artifacts_present=False,
    )
    source_rows = build_source_accounting_rows(source=source)
    gate_rows = build_gate_matrix_rows(
        source=source,
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        protected_rows=protected_rows,
        aggregate_rows=aggregate_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["source_accounting_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["offtrack_target_rows"], offtrack_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(paths["collision_caution_rows"], collision_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(paths["diagnostic_success_context_rows"], success_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(paths["protected_exclusion_rows"], protected_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(paths["target_panel_aggregate_rows"], aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_join_rows"], actor_rows, fieldnames=ACTOR_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        panel_rows_present=bool(slice_rows),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        protected_rows=protected_rows,
        aggregate_rows=aggregate_rows,
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
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        protected_rows=protected_rows,
        aggregate_rows=aggregate_rows,
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
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        protected_rows=protected_rows,
        aggregate_rows=aggregate_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        protected_rows=protected_rows,
        aggregate_rows=aggregate_rows,
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
        "offtrack_target_rows": output_dir / "offtrack_target_rows.csv",
        "collision_caution_rows": output_dir / "collision_caution_rows.csv",
        "diagnostic_success_context_rows": output_dir / "diagnostic_success_context_rows.csv",
        "protected_exclusion_rows": output_dir / "protected_exclusion_rows.csv",
        "target_panel_aggregate_rows": output_dir / "target_panel_aggregate_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2719_dir: Path, m2720_audit: Path, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "m2720_audit_doc": m2720_audit,
        "m2719_summary": m2719_dir / "summary.json",
        "m2719_taxonomy_rows": m2719_dir / "taxonomy_rows.csv",
        "m2719_taxonomy_aggregate": m2719_dir / "taxonomy_aggregate_rows.csv",
        "m2719_profile_context": m2719_dir / "profile_taxonomy_context_rows.csv",
        "m2719_anchor_context": m2719_dir / "anchor_taxonomy_context_rows.csv",
        "m2719_actor_contract_join_rows": m2719_dir / "actor_contract_join_rows.csv",
        "m2719_claim_boundary_rows": m2719_dir / "claim_boundary_rows.csv",
        "m2719_gate_matrix": m2719_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2720_audit_text": paths["m2720_audit_doc"].read_text(encoding="utf-8")
        if source_exists["m2720_audit_doc"]
        else "",
        "m2719_summary": read_json(paths["m2719_summary"]) if source_exists["m2719_summary"] else {},
        "taxonomy_rows": read_csv_rows(paths["m2719_taxonomy_rows"]),
        "taxonomy_aggregate_rows": read_csv_rows(paths["m2719_taxonomy_aggregate"]),
        "profile_context_rows": read_csv_rows(paths["m2719_profile_context"]),
        "anchor_context_rows": read_csv_rows(paths["m2719_anchor_context"]),
        "actor_contract_join_rows": read_csv_rows(paths["m2719_actor_contract_join_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2719_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2719_gate_matrix"]),
    }


def build_source_accounting_rows(*, source: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {
        "m2719_taxonomy_rows": len(source["taxonomy_rows"]),
        "m2719_taxonomy_aggregate": len(source["taxonomy_aggregate_rows"]),
        "m2719_profile_context": len(source["profile_context_rows"]),
        "m2719_anchor_context": len(source["anchor_context_rows"]),
        "m2719_actor_contract_join_rows": len(source["actor_contract_join_rows"]),
        "m2719_claim_boundary_rows": len(source["claim_boundary_rows"]),
        "m2719_gate_matrix": len(source["gate_matrix"]),
    }
    return [
        {
            "source_id": f"m2721-source-{index:04d}",
            "source_family": key,
            "path": str(path),
            "present": bool(source["source_exists"].get(key, False)),
            "row_count": row_counts.get(key, ""),
            "status_pass": bool(source["source_exists"].get(key, False)),
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (key, path) in enumerate(source["paths"].items(), start=1)
    ]


def build_slice_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(taxonomy_rows, start=1):
        taxonomy_family = str(row.get("taxonomy_family", ""))
        if taxonomy_family == "off_track":
            panel_slice = "offtrack_target"
            priority = 1
            admitted = True
        elif taxonomy_family == "obstacle_collision":
            panel_slice = "collision_caution"
            priority = 2
            admitted = False
        elif taxonomy_family == "diagnostic_success":
            panel_slice = "diagnostic_success_context"
            priority = 3
            admitted = False
        elif taxonomy_family == "protected_excluded":
            panel_slice = "protected_exclusion"
            priority = 4
            admitted = False
        else:
            panel_slice = "other_context"
            priority = 5
            admitted = False
        rows.append(
            {
                "panel_row_id": f"m2721-{panel_slice}-{index:04d}",
                "source_taxonomy_id": row.get("taxonomy_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "anchor_task_source_id": row.get("anchor_task_source_id", ""),
                "workload_id": row.get("workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "taxonomy_family": taxonomy_family,
                "panel_slice": panel_slice,
                "repair_priority": priority,
                "target_panel_admitted": admitted,
                "execution_scheduled": False,
                "profile_ranking_allowed": False,
                "winner_selection_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "target_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_aggregate_rows(slice_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, panel_slice in enumerate(sorted({str(row["panel_slice"]) for row in slice_rows}), start=1):
        group_rows = [row for row in slice_rows if row["panel_slice"] == panel_slice]
        rows.append(aggregate_row(f"m2721-target-panel-aggregate-{index:04d}", "panel_slice", panel_slice, group_rows))
    rows.append(aggregate_row("m2721-target-panel-aggregate-all", "panel", "all", slice_rows))
    return rows


def aggregate_row(aggregate_id: str, aggregate_family: str, group_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["panel_slice"] for row in rows)
    return {
        "aggregate_id": aggregate_id,
        "aggregate_family": aggregate_family,
        "group_key": group_key,
        "row_count": len(rows),
        "offtrack_target_row_count": counts.get("offtrack_target", 0),
        "collision_caution_row_count": counts.get("collision_caution", 0),
        "diagnostic_success_context_row_count": counts.get("diagnostic_success_context", 0),
        "protected_exclusion_row_count": counts.get("protected_exclusion", 0),
        "execution_scheduled": False,
        "profile_ranking_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_join_rows(*, source: dict[str, Any], slice_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        actor_join("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_join("action_shape", ACTION_DIM, 3, False),
        actor_join("hidden_oracle_actor_input_detected", False, False, False),
        actor_join("target_labels_actor_visible", any_bool(slice_rows, "target_labels_actor_visible"), False, False),
        actor_join("profile_ranking_allowed", any_bool(slice_rows, "profile_ranking_allowed"), False, False),
        actor_join("execution_scheduled", any_bool(slice_rows, "execution_scheduled"), False, False),
        actor_join(
            "protected_rows_in_success_denominator",
            any_bool(slice_rows, "protected_rows_in_success_denominator"),
            False,
            False,
        ),
        actor_join("m2719_actor_join_rows_pass", all(bool_value(row.get("status_pass")) for row in source["actor_contract_join_rows"]), True, False),
    ]


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "join_id": f"m2721-actor-join-{field}",
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
    panel_rows_present: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("offtrack_target_panel_materialized", "artifact", panel_rows_present, "offtrack_target_rows.csv"),
        ("caution_and_context_rows_materialized", "artifact", required_artifacts_present, "collision and success context rows"),
        ("protected_exclusions_preserved", "contract", True, "protected_exclusion_rows.csv"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2722 result-audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future execution manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2721_{claim_id}",
        "claim_family": family,
        "allowed_in_m2721": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    offtrack_rows: list[dict[str, Any]],
    collision_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2721"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2721"])]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2719/M2720/follow-up artifacts present", "lineage_invalid"),
        ("m2720_accepts_target_panel_route", "lineage", "accept_m2719_route_to_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization" in source["m2720_audit_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2719_status_pass", "lineage", bool_value(source["m2719_summary"].get("status_pass", False)), source["m2719_summary"].get("status_pass"), True, "lineage_invalid"),
        ("offtrack_target_count", "artifact", len(offtrack_rows) == EXPECTED_OFFTRACK_TARGET_COUNT, len(offtrack_rows), EXPECTED_OFFTRACK_TARGET_COUNT, "metric_artifact"),
        ("collision_caution_count", "artifact", len(collision_rows) == EXPECTED_COLLISION_CAUTION_COUNT, len(collision_rows), EXPECTED_COLLISION_CAUTION_COUNT, "metric_artifact"),
        ("success_context_count", "artifact", len(success_rows) == EXPECTED_SUCCESS_CONTEXT_COUNT, len(success_rows), EXPECTED_SUCCESS_CONTEXT_COUNT, "metric_artifact"),
        ("protected_exclusion_count", "artifact", len(protected_rows) == EXPECTED_PROTECTED_EXCLUSION_COUNT, len(protected_rows), EXPECTED_PROTECTED_EXCLUSION_COUNT, "metric_artifact"),
        ("offtrack_rows_admitted_only", "contract", all(bool_value(row["target_panel_admitted"]) for row in offtrack_rows) and not any(bool_value(row["target_panel_admitted"]) for row in collision_rows + success_rows + protected_rows), "only offtrack admitted", "all non-offtrack false", "contract_violation"),
        ("no_execution_scheduled", "execution_guardrail", not any_bool(offtrack_rows + collision_rows + success_rows + protected_rows, "execution_scheduled"), "no execution scheduled", "all false", "objective_overfit"),
        ("profile_context_nonranking", "claim_boundary", not any_bool(offtrack_rows + collision_rows + success_rows + protected_rows, "profile_ranking_allowed"), "all profile rows non-ranking", "all false", "proof_washout"),
        ("protected_not_denominator", "contract", not any_bool(protected_rows, "protected_rows_in_success_denominator"), "protected exclusions outside denominator", "all false", "contract_violation"),
        ("target_labels_actor_invisible", "contract", not any_bool(offtrack_rows + collision_rows + success_rows + protected_rows, "target_labels_actor_visible"), "target labels actor-invisible", "all false", "contract_violation"),
        ("aggregate_rows_present", "artifact", bool(aggregate_rows), len(aggregate_rows), ">0", "metric_artifact"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_rows)}", "all actor joins pass", "contract_violation"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status, observed, expected, failure_type) for gate_id, family, status, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2721_{gate_id}",
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
    offtrack_rows: list[dict[str, Any]],
    collision_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2719_status_pass": bool_value(source["m2719_summary"].get("status_pass", False)),
        "offtrack_target_row_count": len(offtrack_rows),
        "collision_caution_row_count": len(collision_rows),
        "diagnostic_success_context_row_count": len(success_rows),
        "protected_exclusion_row_count": len(protected_rows),
        "target_panel_aggregate_row_count": len(aggregate_rows),
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
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": any_bool(offtrack_rows + collision_rows + success_rows + protected_rows, "target_labels_actor_visible"),
        "profile_ranking_allowed": any_bool(offtrack_rows + collision_rows + success_rows + protected_rows, "profile_ranking_allowed"),
        "winner_selected": False,
        "checkpoint_promoted": False,
        "protected_rows_in_success_denominator": any_bool(protected_rows, "protected_rows_in_success_denominator"),
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2721 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Target Panel Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- offtrack target rows: {summary['offtrack_target_row_count']}",
            f"- collision caution rows: {summary['collision_caution_row_count']}",
            f"- diagnostic success context rows: {summary['diagnostic_success_context_row_count']}",
            f"- protected exclusion rows: {summary['protected_exclusion_row_count']}",
            f"- aggregate rows: {summary['target_panel_aggregate_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2721 materializes a no-rollout target panel. It does not execute environments or rank profiles.",
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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def any_bool(rows: list[dict[str, Any]], key: str) -> bool:
    return any(bool_value(row.get(key, False)) for row in rows)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2719-dir", type=Path, default=DEFAULT_M2719_DIR)
    parser.add_argument("--m2720-audit", type=Path, default=DEFAULT_M2720_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_offtrack_repair_target_panel(
        m2719_dir=args.m2719_dir,
        m2720_audit=args.m2720_audit,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"offtrack_target_row_count={summary['offtrack_target_row_count']}")
    print(f"protected_exclusion_row_count={summary['protected_exclusion_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
