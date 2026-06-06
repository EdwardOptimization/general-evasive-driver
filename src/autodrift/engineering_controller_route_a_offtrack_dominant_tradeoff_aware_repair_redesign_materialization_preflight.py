"""Materialize M2936 tradeoff-aware Route A repair redesign constraints.

M2937 consumes the accepted M2934/M2935 outcome-shift localization and the
M2936 design. It performs no environment, policy, replay, training,
validation, ranking, or promotion work. Its only job is to make the
tradeoff-aware repair redesign machine-checkable before any later repair
execution design or audit.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-"
    "repair-redesign-materialization-preflight"
)
NEXT_ID = (
    "m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-"
    "repair-redesign-materialization-result-audit"
)
DEFAULT_M2934_DIR = Path(
    "runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight"
)
DEFAULT_M2935_AUDIT = Path(
    "docs/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.md"
)
DEFAULT_M2936_DESIGN = Path(
    "docs/m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2937_engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-result-audit.json"
)

EXPECTED_PANEL_ROW_COUNT = 56
EXPECTED_OFFTRACK_TARGET_COUNT = 38
EXPECTED_CONTEXT_ROW_COUNT = 18
EXPECTED_PERSISTENT_OFFTRACK_COUNT = 24
EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT = 10
EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT = 9
EXPECTED_POSITIVE_REFERENCE_COUNT = 4
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

CLAIM_SCOPE = (
    "M2937 Route A tradeoff-aware repair redesign materialization only; M2934 "
    "transition rows may be converted into constraint, candidate-surface, "
    "actor-guard, claim-boundary, gate, summary, doc, and follow-up audit "
    "artifacts. No reset, step, rollout, replay, validation, training, PPO, "
    "dependency work, ranking, winner selection, promotion, success-rate "
    "verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

TRANSITION_CONSTRAINT_FIELDNAMES = [
    "transition_constraint_id",
    "source_outcome_shift_id",
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
    "m2919_outcome_family",
    "m2931_outcome_family",
    "transition_bucket",
    "transition_family",
    "constraint_family",
    "constraint_role",
    "future_design_must_account",
    "candidate_surface_admitted",
    "execution_scheduled",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "ranking_claim_made",
    "winner_selection_allowed",
    "promotion_allowed",
    "repair_success_claim_made",
    "driver_performance_claim_made",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SPECIALIZED_CONSTRAINT_FIELDNAMES = [
    "constraint_id",
    "constraint_family",
    "source_transition_constraint_id",
    "source_outcome_shift_id",
    "panel_row_id",
    "source_milestone",
    "task_family",
    "env_template_family",
    "window_tag",
    "transition_bucket",
    "required_future_design_property",
    "blocked_shortcut",
    "ranking_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CANDIDATE_SURFACE_FIELDNAMES = [
    "candidate_surface_id",
    "surface_family",
    "constraint_family",
    "source_row_count",
    "required_future_design_property",
    "execution_scheduled",
    "training_scheduled",
    "validation_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_input_contract_changed",
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
    "allowed_in_m2937",
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
    "transition_constraint_rows",
    "offtrack_persistence_constraint_rows",
    "collision_speed_substitution_constraint_rows",
    "context_retention_constraint_rows",
    "positive_transition_reference_rows",
    "candidate_surface_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_tradeoff_aware_repair_redesign_materialization_preflight(
    *,
    m2934_dir: Path | str = DEFAULT_M2934_DIR,
    m2935_audit: Path | str = DEFAULT_M2935_AUDIT,
    m2936_design: Path | str = DEFAULT_M2936_DESIGN,
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
        m2934_dir=Path(m2934_dir),
        m2935_audit=Path(m2935_audit),
        m2936_design=Path(m2936_design),
    )

    transition_rows = build_transition_constraint_rows(source["outcome_shift_rows"])
    persistence_rows = specialized_rows(
        transition_rows,
        family="offtrack_persistence_constraint",
        required_property="future repair design must reduce persistent offtrack without using hidden/oracle actor inputs",
        blocked_shortcut="offtrack-only aggregate improvement that leaves persistent offtrack rows unaddressed",
    )
    substitution_rows = specialized_rows(
        transition_rows,
        family="collision_speed_substitution_constraint",
        required_property="future repair design must not reduce offtrack by converting rows to collision or speed_too_low",
        blocked_shortcut="offtrack reduction counted as success while collision/speed failures increase",
    )
    context_rows = specialized_rows(
        transition_rows,
        family="context_retention_constraint",
        required_property="future repair design must preserve previously successful context rows",
        blocked_shortcut="target-only optimization that regresses success-context rows",
    )
    positive_rows = specialized_rows(
        transition_rows,
        family="positive_transition_reference",
        required_property="future repair design may use positive rows as diagnostic exemplars only",
        blocked_shortcut="ranking or promotion from four positive transitions",
    )
    candidate_rows = build_candidate_surface_rows(
        transition_rows=transition_rows,
        persistence_rows=persistence_rows,
        substitution_rows=substitution_rows,
        context_rows=context_rows,
        positive_rows=positive_rows,
    )

    write_csv_rows(paths["transition_constraint_rows"], transition_rows, fieldnames=TRANSITION_CONSTRAINT_FIELDNAMES)
    write_csv_rows(
        paths["offtrack_persistence_constraint_rows"],
        persistence_rows,
        fieldnames=SPECIALIZED_CONSTRAINT_FIELDNAMES,
    )
    write_csv_rows(
        paths["collision_speed_substitution_constraint_rows"],
        substitution_rows,
        fieldnames=SPECIALIZED_CONSTRAINT_FIELDNAMES,
    )
    write_csv_rows(
        paths["context_retention_constraint_rows"],
        context_rows,
        fieldnames=SPECIALIZED_CONSTRAINT_FIELDNAMES,
    )
    write_csv_rows(
        paths["positive_transition_reference_rows"],
        positive_rows,
        fieldnames=SPECIALIZED_CONSTRAINT_FIELDNAMES,
    )
    write_csv_rows(paths["candidate_surface_rows"], candidate_rows, fieldnames=CANDIDATE_SURFACE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "transition_constraint_row_count": len(transition_rows),
            "offtrack_persistence_constraint_row_count": len(persistence_rows),
            "collision_speed_substitution_constraint_row_count": len(substitution_rows),
            "context_retention_constraint_row_count": len(context_rows),
            "positive_transition_reference_row_count": len(positive_rows),
            "candidate_surface_row_count": len(candidate_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(transition_rows, candidate_rows)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_without_summary_doc,
        transition_rows_present=bool(transition_rows),
        specialized_rows_present=bool(persistence_rows and substitution_rows and context_rows and positive_rows),
        candidate_surface_present=bool(candidate_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        transition_rows=transition_rows,
        persistence_rows=persistence_rows,
        substitution_rows=substitution_rows,
        context_rows=context_rows,
        positive_rows=positive_rows,
        candidate_rows=candidate_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        transition_rows=transition_rows,
        persistence_rows=persistence_rows,
        substitution_rows=substitution_rows,
        context_rows=context_rows,
        positive_rows=positive_rows,
        candidate_rows=candidate_rows,
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
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_artifacts_present,
        transition_rows_present=bool(transition_rows),
        specialized_rows_present=bool(persistence_rows and substitution_rows and context_rows and positive_rows),
        candidate_surface_present=bool(candidate_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        transition_rows=transition_rows,
        persistence_rows=persistence_rows,
        substitution_rows=substitution_rows,
        context_rows=context_rows,
        positive_rows=positive_rows,
        candidate_rows=candidate_rows,
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
        transition_rows=transition_rows,
        persistence_rows=persistence_rows,
        substitution_rows=substitution_rows,
        context_rows=context_rows,
        positive_rows=positive_rows,
        candidate_rows=candidate_rows,
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
            "transition_constraint_row_count": len(transition_rows),
            "offtrack_persistence_constraint_row_count": len(persistence_rows),
            "collision_speed_substitution_constraint_row_count": len(substitution_rows),
            "context_retention_constraint_row_count": len(context_rows),
            "positive_transition_reference_row_count": len(positive_rows),
            "candidate_surface_row_count": len(candidate_rows),
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
        "transition_constraint_rows": output_dir / "transition_constraint_rows.csv",
        "offtrack_persistence_constraint_rows": output_dir / "offtrack_persistence_constraint_rows.csv",
        "collision_speed_substitution_constraint_rows": output_dir
        / "collision_speed_substitution_constraint_rows.csv",
        "context_retention_constraint_rows": output_dir / "context_retention_constraint_rows.csv",
        "positive_transition_reference_rows": output_dir / "positive_transition_reference_rows.csv",
        "candidate_surface_rows": output_dir / "candidate_surface_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2934_dir: Path, m2935_audit: Path, m2936_design: Path) -> dict[str, Any]:
    paths = {
        "m2934_summary": m2934_dir / "summary.json",
        "m2934_outcome_shift_rows": m2934_dir / "outcome_shift_rows.csv",
        "m2934_offtrack_target_shift_rows": m2934_dir / "offtrack_target_shift_rows.csv",
        "m2934_context_regression_rows": m2934_dir / "context_regression_rows.csv",
        "m2934_gate_matrix": m2934_dir / "gate_matrix.csv",
        "m2935_audit": m2935_audit,
        "m2936_design": m2936_design,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2934_summary": read_json(paths["m2934_summary"]) if source_exists["m2934_summary"] else {},
        "outcome_shift_rows": read_csv_rows(paths["m2934_outcome_shift_rows"]),
        "offtrack_target_shift_rows": read_csv_rows(paths["m2934_offtrack_target_shift_rows"]),
        "context_regression_rows": read_csv_rows(paths["m2934_context_regression_rows"]),
        "m2934_gate_matrix": read_csv_rows(paths["m2934_gate_matrix"]),
        "m2935_audit_text": paths["m2935_audit"].read_text(encoding="utf-8")
        if source_exists["m2935_audit"]
        else "",
        "m2936_design_text": paths["m2936_design"].read_text(encoding="utf-8")
        if source_exists["m2936_design"]
        else "",
        "follow_up_manifest_exists": False,
    }


def build_transition_constraint_rows(outcome_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(outcome_rows, start=1):
        family = constraint_family(row)
        rows.append(
            {
                "transition_constraint_id": f"m2937-transition-constraint-{index:04d}",
                "source_outcome_shift_id": row.get("outcome_shift_id", ""),
                "panel_row_id": row.get("panel_row_id", ""),
                "panel_row_family": row.get("panel_row_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_family": row.get("source_family", ""),
                "source_edge": row.get("source_edge", ""),
                "source_row_id": row.get("source_row_id", ""),
                "task_family": row.get("task_family", ""),
                "task_source_id": row.get("task_source_id", ""),
                "workload_id": row.get("workload_id", ""),
                "profile_name": row.get("profile_name", ""),
                "env_template_family": row.get("env_template_family", ""),
                "window_tag": row.get("window_tag", ""),
                "checkpoint_context": row.get("checkpoint_context", ""),
                "m2919_outcome_family": row.get("m2919_outcome_family", ""),
                "m2931_outcome_family": row.get("m2931_outcome_family", ""),
                "transition_bucket": row.get("transition_bucket", ""),
                "transition_family": row.get("transition_family", ""),
                "constraint_family": family,
                "constraint_role": constraint_role(family),
                "future_design_must_account": True,
                "candidate_surface_admitted": True,
                "execution_scheduled": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "ranking_claim_made": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "repair_success_claim_made": False,
                "driver_performance_claim_made": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def constraint_family(row: Mapping[str, Any]) -> str:
    if _bool(row.get("offtrack_persisted", False)):
        return "offtrack_persistence_constraint"
    if _bool(row.get("offtrack_regressed_to_collision_or_speed", False)):
        return "collision_speed_substitution_constraint"
    if _bool(row.get("context_regressed_to_offtrack_or_collision", False)):
        return "context_retention_constraint"
    if _bool(row.get("offtrack_repaired_to_success", False)):
        return "positive_transition_reference"
    if _bool(row.get("context_preserved_success", False)):
        return "context_success_reference"
    return "full_panel_accounting_constraint"


def constraint_role(family: str) -> str:
    roles = {
        "offtrack_persistence_constraint": "primary_failure_pressure",
        "collision_speed_substitution_constraint": "substitution_guard",
        "context_retention_constraint": "context_regression_guard",
        "positive_transition_reference": "positive_diagnostic_reference",
        "context_success_reference": "context_success_reference",
        "full_panel_accounting_constraint": "full_panel_accounting",
    }
    return roles[family]


def specialized_rows(
    transition_rows: list[dict[str, Any]],
    *,
    family: str,
    required_property: str,
    blocked_shortcut: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate((item for item in transition_rows if item["constraint_family"] == family), start=1):
        rows.append(
            {
                "constraint_id": f"m2937-{family}-{index:04d}",
                "constraint_family": family,
                "source_transition_constraint_id": row["transition_constraint_id"],
                "source_outcome_shift_id": row["source_outcome_shift_id"],
                "panel_row_id": row["panel_row_id"],
                "source_milestone": row["source_milestone"],
                "task_family": row["task_family"],
                "env_template_family": row["env_template_family"],
                "window_tag": row["window_tag"],
                "transition_bucket": row["transition_bucket"],
                "required_future_design_property": required_property,
                "blocked_shortcut": blocked_shortcut,
                "ranking_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_candidate_surface_rows(
    *,
    transition_rows: list[dict[str, Any]],
    persistence_rows: list[dict[str, Any]],
    substitution_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    positive_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    surface_specs = [
        (
            "full_panel_accounting",
            "full_panel_accounting_constraint",
            len(transition_rows),
            "future repair designs must keep all transition rows auditable",
        ),
        (
            "persistent_offtrack_pressure",
            "offtrack_persistence_constraint",
            len(persistence_rows),
            "future repair designs must address persistent offtrack directly",
        ),
        (
            "collision_speed_substitution_guard",
            "collision_speed_substitution_constraint",
            len(substitution_rows),
            "future repair designs must block collision/speed substitution",
        ),
        (
            "context_retention_guard",
            "context_retention_constraint",
            len(context_rows),
            "future repair designs must preserve success-context rows",
        ),
        (
            "positive_reference_preservation",
            "positive_transition_reference",
            len(positive_rows),
            "future repair designs may preserve positive references without ranking them",
        ),
    ]
    rows = []
    for index, (surface_family, constraint, count, required_property) in enumerate(surface_specs, start=1):
        rows.append(
            {
                "candidate_surface_id": f"m2937-candidate-surface-{index:04d}",
                "surface_family": surface_family,
                "constraint_family": constraint,
                "source_row_count": count,
                "required_future_design_property": required_property,
                "execution_scheduled": False,
                "training_scheduled": False,
                "validation_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "actor_input_contract_changed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    transition_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    combined = transition_rows + candidate_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("execution_scheduled", any_flag(combined, "execution_scheduled"), False),
        actor_guard("validation_denominator_allowed", any_flag(combined, "validation_denominator_allowed"), False),
        actor_guard("paper_denominator_allowed", any_flag(combined, "paper_denominator_allowed"), False),
        actor_guard("ranking_claim_made", any_flag(combined, "ranking_claim_made"), False),
        actor_guard("winner_selection_allowed", any_flag(combined, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(combined, "promotion_allowed"), False),
        actor_guard("repair_success_claim_made", any_flag(combined, "repair_success_claim_made"), False),
        actor_guard("driver_performance_claim_made", any_flag(combined, "driver_performance_claim_made"), False),
        actor_guard("actor_visible_rows", any_flag(combined, "actor_visible"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2937-actor-guard-{field}",
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
    transition_rows_present: bool,
    specialized_rows_present: bool,
    candidate_surface_present: bool,
    actor_guards_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("transition_constraints_materialized", "artifact", transition_rows_present, "transition_constraint_rows.csv"),
        ("specialized_constraints_materialized", "artifact", specialized_rows_present, "four specialized constraint CSVs"),
        ("candidate_surface_materialized", "artifact", candidate_surface_present, "candidate_surface_rows.csv"),
        ("actor_guard_materialized", "artifact", actor_guards_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_doc_materialized", "artifact", artifacts_present, "summary.json and milestone doc"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2938 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_replay", "execution", "future bounded execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("dependency_execution", "execution", "future dependency route"),
        ("source_task_checkpoint_band_ranking", "ranking", "future audited comparison route"),
        ("candidate_ranking", "ranking", "future audited comparison route"),
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
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2937_{claim_id}",
        "claim_family": family,
        "allowed_in_m2937": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    transition_rows: list[dict[str, Any]],
    persistence_rows: list[dict[str, Any]],
    substitution_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    positive_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    transition_counts = Counter(str(row.get("transition_bucket", "")) for row in transition_rows)
    offtrack_count = sum(str(row.get("panel_row_family", "")) == "offtrack_repair_target" for row in transition_rows)
    context_count = sum(str(row.get("panel_row_family", "")).startswith("non_offtrack_context") for row in transition_rows)
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2937"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2937"])]
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2934 summary/rows/gates and M2935/M2936 docs present",
            "lineage_invalid",
        ),
        (
            "m2934_status_pass",
            "lineage",
            _bool(source["m2934_summary"].get("status_pass", False))
            and _bool(source["m2934_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2934_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2934_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2935_accepts_m2934",
            "lineage",
            "accepts M2934" in source["m2935_audit_text"],
            "accepts M2934" in source["m2935_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2936_admits_m2937",
            "lineage",
            "admit_m2937_tradeoff_aware_repair_redesign_materialization_preflight"
            in source["m2936_design_text"]
            and MILESTONE_ID in source["m2936_design_text"],
            {
                "decision_present": "admit_m2937_tradeoff_aware_repair_redesign_materialization_preflight"
                in source["m2936_design_text"],
                "m2937_id_present": MILESTONE_ID in source["m2936_design_text"],
            },
            "M2936 names M2937 materialization",
            "lineage_invalid",
        ),
        (
            "transition_rows_accounted",
            "materialization",
            len(transition_rows) == EXPECTED_PANEL_ROW_COUNT,
            len(transition_rows),
            EXPECTED_PANEL_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "offtrack_context_counts_preserved",
            "materialization",
            offtrack_count == EXPECTED_OFFTRACK_TARGET_COUNT and context_count == EXPECTED_CONTEXT_ROW_COUNT,
            {"offtrack": offtrack_count, "context": context_count},
            {"offtrack": EXPECTED_OFFTRACK_TARGET_COUNT, "context": EXPECTED_CONTEXT_ROW_COUNT},
            "metric_artifact",
        ),
        (
            "transition_counts_preserved",
            "materialization",
            dict(transition_counts) == EXPECTED_TRANSITION_COUNTS,
            dict(transition_counts),
            EXPECTED_TRANSITION_COUNTS,
            "metric_artifact",
        ),
        (
            "persistent_offtrack_constraints_materialized",
            "materialization",
            len(persistence_rows) == EXPECTED_PERSISTENT_OFFTRACK_COUNT,
            len(persistence_rows),
            EXPECTED_PERSISTENT_OFFTRACK_COUNT,
            "metric_artifact",
        ),
        (
            "collision_speed_substitution_constraints_materialized",
            "materialization",
            len(substitution_rows) == EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT,
            len(substitution_rows),
            EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT,
            "metric_artifact",
        ),
        (
            "context_retention_constraints_materialized",
            "materialization",
            len(context_rows) == EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT,
            len(context_rows),
            EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT,
            "metric_artifact",
        ),
        (
            "positive_reference_rows_materialized",
            "materialization",
            len(positive_rows) == EXPECTED_POSITIVE_REFERENCE_COUNT,
            len(positive_rows),
            EXPECTED_POSITIVE_REFERENCE_COUNT,
            "metric_artifact",
        ),
        (
            "candidate_surface_rows_materialized",
            "materialization",
            len(candidate_rows) == 5 and sum(int(row["source_row_count"]) for row in candidate_rows[:1]) == len(transition_rows),
            {"rows": len(candidate_rows), "full_panel_count": candidate_rows[0]["source_row_count"] if candidate_rows else ""},
            "5 rows with full panel first",
            "metric_artifact",
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
            not any(forbidden_execution_flag(row) for row in transition_rows + candidate_rows),
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
            "follow_up_audit_registered",
            "follow_up",
            source["follow_up_manifest_exists"],
            source["follow_up_manifest_exists"],
            True,
            "lineage_invalid",
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
        "gate_id": f"m2937_{gate_id}",
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
    transition_rows: list[dict[str, Any]],
    persistence_rows: list[dict[str, Any]],
    substitution_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    positive_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    transition_counts = Counter(str(row.get("transition_bucket", "")) for row in transition_rows)
    constraint_counts = Counter(str(row.get("constraint_family", "")) for row in transition_rows)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2934_status_pass": _bool(source["m2934_summary"].get("status_pass", False)),
        "m2934_gate_matrix_pass": _bool(source["m2934_summary"].get("gate_matrix_pass", False)),
        "transition_constraint_row_count": len(transition_rows),
        "offtrack_target_row_count": sum(
            str(row.get("panel_row_family", "")) == "offtrack_repair_target" for row in transition_rows
        ),
        "context_row_count": sum(
            str(row.get("panel_row_family", "")).startswith("non_offtrack_context") for row in transition_rows
        ),
        "transition_counts": dict(transition_counts),
        "constraint_family_counts": dict(constraint_counts),
        "offtrack_persistence_constraint_row_count": len(persistence_rows),
        "collision_speed_substitution_constraint_row_count": len(substitution_rows),
        "context_retention_constraint_row_count": len(context_rows),
        "positive_transition_reference_row_count": len(positive_rows),
        "candidate_surface_row_count": len(candidate_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
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
            "# M2937 Engineering Controller Route A Offtrack-Dominant Tradeoff-Aware Repair Redesign Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- transition constraint rows: {summary['transition_constraint_row_count']}",
            f"- offtrack targets: {summary['offtrack_target_row_count']}",
            f"- context rows: {summary['context_row_count']}",
            f"- transition counts: {summary['transition_counts']}",
            f"- persistent offtrack constraints: {summary['offtrack_persistence_constraint_row_count']}",
            f"- collision/speed substitution constraints: {summary['collision_speed_substitution_constraint_row_count']}",
            f"- context-retention constraints: {summary['context_retention_constraint_row_count']}",
            f"- positive reference rows: {summary['positive_transition_reference_row_count']}",
            f"- candidate surface rows: {summary['candidate_surface_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2937 materializes constraints only. Constraint counts are design accounting, not repair success, ranking, validation readiness, or performance evidence.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2937 tradeoff-aware repair redesign materialization before any execution training validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "transition_constraint_rows.csv"),
                str(output_dir / "offtrack_persistence_constraint_rows.csv"),
                str(output_dir / "collision_speed_substitution_constraint_rows.csv"),
                str(output_dir / "context_retention_constraint_rows.csv"),
                str(output_dir / "positive_transition_reference_rows.csv"),
                str(output_dir / "candidate_surface_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign.md",
                "docs/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight.json",
                "experiments/manifests/m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign.json",
            ],
            "parent_objective": [
                "audit M2937 tradeoff-aware repair redesign materialization before interpretation"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign",
                "m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit",
                "m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight",
            ],
            "blocked_by": [
                "M2937 materialization requires a result audit before interpretation",
                "constraint rows must remain design accounting and cannot become repair-success or validation evidence",
            ],
            "supersedes": ["direct next repair execution from M2936 without materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2938 must audit M2937 summary gate matrix actor and claim boundaries",
            "M2938 must preserve all transition constraint and specialized constraint row counts",
            "M2938 must not claim repair success validation ranking performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2938 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert constraint counts into repair-success performance validation paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_result_audit",
            "evidence_increment": "audits M2937 tradeoff-aware repair redesign materialization artifacts",
            "claim_scope": "Result audit only; no repair execution validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2937 artifacts are missing or gate matrix fails",
                "stop if constraint row counts are incomplete",
                "stop if actor or claim boundaries were violated",
                "stop if the audit cannot choose a bounded next design pivot stop or synthesis route without overclaiming",
            ],
            "fallback_plan": [
                "route to artifact repair if materialization failed",
                "route to branch stop or pivot if no bounded repair route remains",
                "route to a bounded next design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2937 completes tradeoff-aware repair redesign materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2937 tradeoff-aware repair redesign materialization artifacts",
            "admission_evidence": [
                "M2937 summary and gate matrix",
                "M2937 transition constraint specialized constraint candidate actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2938 status queue scoreboard research log and review",
                "one follow-up manifest only if M2938 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2938 audit accepts or rejects M2937 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2938 audits Route A repair redesign materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2938; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2919-to-M2937 Route A offtrack repair diagnostic and materialization chain.",
            "negative_result_policy": "Preserve negative or insufficient constraints and route to pivot or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2937 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits newly materialized tradeoff-aware repair redesign constraints",
            "paper_verdict_delta": "no paper verdict; audit may admit a bounded next design or stop/pivot Route A repair",
            "must_synthesize_if": [
                "M2938 cannot accept M2937 as complete and claim-safe",
                "M2938 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2938 would continue another fixed-candidate execution without a materially changed evidence question",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2938 audits M2937 artifacts row counts gates actor and claim boundaries",
            "M2938 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2938 hides M2937 failures or missing artifacts",
            "M2938 treats M2937 constraints as repair success validation readiness or performance verdict",
            "M2938 selects another fixed-candidate repair execution without a materially changed evidence question",
        ],
        "decision_rule": "Pass only if M2938 preserves M2937 constraint materialization evidence and chooses one bounded next route or stop state without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "transition_constraint_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    keys = [
        "execution_scheduled",
        "training_scheduled",
        "validation_scheduled",
        "validation_denominator_allowed",
        "paper_denominator_allowed",
        "ranking_claim_made",
        "ranking_allowed",
        "winner_selection_allowed",
        "promotion_allowed",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "actor_input_contract_changed",
        "actor_visible",
    ]
    return any(_bool(row.get(key, False)) for key in keys)


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2934-dir", type=Path, default=DEFAULT_M2934_DIR)
    parser.add_argument("--m2935-audit", type=Path, default=DEFAULT_M2935_AUDIT)
    parser.add_argument("--m2936-design", type=Path, default=DEFAULT_M2936_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_tradeoff_aware_repair_redesign_materialization_preflight(
        m2934_dir=args.m2934_dir,
        m2935_audit=args.m2935_audit,
        m2936_design=args.m2936_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"transition_constraint_row_count={summary['transition_constraint_row_count']}")
    print(f"constraint_family_counts={summary['constraint_family_counts']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
