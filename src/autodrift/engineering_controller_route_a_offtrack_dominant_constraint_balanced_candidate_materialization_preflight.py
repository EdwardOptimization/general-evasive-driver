"""Materialize the M2940 constraint-balanced Route A candidate surface.

M2941 consumes the accepted M2937/M2938 tradeoff materialization chain, the
M2939 continuation synthesis, and the M2940 candidate design. It performs no
environment, policy, replay, validation, training, ranking, or promotion work.
Its only job is to convert the selected candidate route into machine-checkable
route, objective-balance, carryforward-constraint, shortcut, actor, claim,
gate, summary, doc, and follow-up audit artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "candidate-materialization-preflight"
)
NEXT_ID = (
    "m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "candidate-materialization-result-audit"
)
DEFAULT_M2937_DIR = Path(
    "runs/m2937_engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight"
)
DEFAULT_M2938_AUDIT = Path(
    "docs/m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-result-audit.md"
)
DEFAULT_M2939_SYNTHESIS = Path(
    "docs/m2939-engineering-controller-route-a-offtrack-dominant-post-materialization-continuation-or-stop-synthesis.md"
)
DEFAULT_M2940_DESIGN = Path(
    "docs/m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2941_engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-result-audit.json"
)

EXPECTED_TRANSITION_CONSTRAINT_COUNT = 56
EXPECTED_PERSISTENT_OFFTRACK_COUNT = 24
EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT = 10
EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT = 9
EXPECTED_POSITIVE_REFERENCE_COUNT = 4
EXPECTED_CANDIDATE_SURFACE_COUNT = 5
EXPECTED_OBJECTIVE_BALANCE_COUNT = 5

ROUTE_FAMILY = "constraint_balanced_actor_head_delta_candidate"
CLAIM_SCOPE = (
    "M2941 Route A constraint-balanced candidate materialization only; M2937 "
    "transition constraints may be converted into candidate-route, objective-"
    "balance, constraint-carryforward, shortcut, actor-guard, claim-boundary, "
    "gate, summary, doc, and follow-up audit artifacts. No reset, step, "
    "rollout, replay, validation, training, PPO, dependency work, ranking, "
    "winner selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, high-"
    "fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "candidate ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

CANDIDATE_ROUTE_FIELDNAMES = [
    "candidate_route_id",
    "route_family",
    "source_design",
    "admitted_for_materialization",
    "actor_surface",
    "source_transition_constraint_count",
    "objective_balance_row_count",
    "constraint_carryforward_row_count",
    "required_follow_up",
    "execution_scheduled",
    "training_scheduled",
    "validation_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
OBJECTIVE_BALANCE_FIELDNAMES = [
    "objective_balance_id",
    "objective_family",
    "source_constraint_family",
    "source_row_count",
    "balance_role",
    "required_future_candidate_property",
    "blocked_substitution",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "ranking_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CONSTRAINT_CARRYFORWARD_FIELDNAMES = [
    "carryforward_constraint_id",
    "source_transition_constraint_id",
    "source_panel_row_id",
    "source_constraint_family",
    "transition_bucket",
    "source_milestone",
    "task_family",
    "env_template_family",
    "window_tag",
    "candidate_route_id",
    "objective_family",
    "actor_visible",
    "evaluator_side_only",
    "future_candidate_must_account",
    "execution_scheduled",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "repair_success_claim_made",
    "driver_performance_claim_made",
    "claim_boundary",
]
BLOCKED_SHORTCUT_FIELDNAMES = [
    "shortcut_id",
    "shortcut_family",
    "excluded_signal_or_claim",
    "exclusion_reason",
    "actor_visible",
    "execution_scheduled",
    "training_scheduled",
    "validation_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "claim_made",
    "status_pass",
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
    "allowed_in_m2941",
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
    "candidate_route_rows",
    "objective_balance_rows",
    "constraint_carryforward_rows",
    "blocked_shortcut_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_constraint_balanced_candidate_materialization_preflight(
    *,
    m2937_dir: Path | str = DEFAULT_M2937_DIR,
    m2938_audit: Path | str = DEFAULT_M2938_AUDIT,
    m2939_synthesis: Path | str = DEFAULT_M2939_SYNTHESIS,
    m2940_design: Path | str = DEFAULT_M2940_DESIGN,
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
        m2937_dir=Path(m2937_dir),
        m2938_audit=Path(m2938_audit),
        m2939_synthesis=Path(m2939_synthesis),
        m2940_design=Path(m2940_design),
    )

    transition_rows = source["transition_constraint_rows"]
    objective_rows = build_objective_balance_rows(source)
    route_rows = build_candidate_route_rows(
        transition_count=len(transition_rows),
        objective_count=len(objective_rows),
        carryforward_count=len(transition_rows),
    )
    carryforward_rows = build_constraint_carryforward_rows(transition_rows)
    shortcut_rows = build_blocked_shortcut_rows()

    write_csv_rows(paths["candidate_route_rows"], route_rows, fieldnames=CANDIDATE_ROUTE_FIELDNAMES)
    write_csv_rows(paths["objective_balance_rows"], objective_rows, fieldnames=OBJECTIVE_BALANCE_FIELDNAMES)
    write_csv_rows(
        paths["constraint_carryforward_rows"],
        carryforward_rows,
        fieldnames=CONSTRAINT_CARRYFORWARD_FIELDNAMES,
    )
    write_csv_rows(paths["blocked_shortcut_rows"], shortcut_rows, fieldnames=BLOCKED_SHORTCUT_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "candidate_route_row_count": len(route_rows),
            "objective_balance_row_count": len(objective_rows),
            "constraint_carryforward_row_count": len(carryforward_rows),
            "blocked_shortcut_row_count": len(shortcut_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        route_rows=route_rows,
        objective_rows=objective_rows,
        carryforward_rows=carryforward_rows,
        shortcut_rows=shortcut_rows,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_without_summary_doc,
        route_rows_present=bool(route_rows),
        objective_rows_present=bool(objective_rows),
        carryforward_rows_present=bool(carryforward_rows),
        shortcut_rows_present=bool(shortcut_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        route_rows=route_rows,
        objective_rows=objective_rows,
        carryforward_rows=carryforward_rows,
        shortcut_rows=shortcut_rows,
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
        route_rows=route_rows,
        objective_rows=objective_rows,
        carryforward_rows=carryforward_rows,
        shortcut_rows=shortcut_rows,
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
        route_rows_present=bool(route_rows),
        objective_rows_present=bool(objective_rows),
        carryforward_rows_present=bool(carryforward_rows),
        shortcut_rows_present=bool(shortcut_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        route_rows=route_rows,
        objective_rows=objective_rows,
        carryforward_rows=carryforward_rows,
        shortcut_rows=shortcut_rows,
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
        route_rows=route_rows,
        objective_rows=objective_rows,
        carryforward_rows=carryforward_rows,
        shortcut_rows=shortcut_rows,
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
            "candidate_route_row_count": len(route_rows),
            "objective_balance_row_count": len(objective_rows),
            "constraint_carryforward_row_count": len(carryforward_rows),
            "blocked_shortcut_row_count": len(shortcut_rows),
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
        "candidate_route_rows": output_dir / "candidate_route_rows.csv",
        "objective_balance_rows": output_dir / "objective_balance_rows.csv",
        "constraint_carryforward_rows": output_dir / "constraint_carryforward_rows.csv",
        "blocked_shortcut_rows": output_dir / "blocked_shortcut_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2937_dir: Path,
    m2938_audit: Path,
    m2939_synthesis: Path,
    m2940_design: Path,
) -> dict[str, Any]:
    paths = {
        "m2937_summary": m2937_dir / "summary.json",
        "transition_constraint_rows": m2937_dir / "transition_constraint_rows.csv",
        "offtrack_persistence_constraint_rows": m2937_dir / "offtrack_persistence_constraint_rows.csv",
        "collision_speed_substitution_constraint_rows": m2937_dir
        / "collision_speed_substitution_constraint_rows.csv",
        "context_retention_constraint_rows": m2937_dir / "context_retention_constraint_rows.csv",
        "positive_transition_reference_rows": m2937_dir / "positive_transition_reference_rows.csv",
        "candidate_surface_rows": m2937_dir / "candidate_surface_rows.csv",
        "m2937_actor_contract_guard_rows": m2937_dir / "actor_contract_guard_rows.csv",
        "m2937_claim_boundary_rows": m2937_dir / "claim_boundary_rows.csv",
        "m2937_gate_matrix": m2937_dir / "gate_matrix.csv",
        "m2938_audit": m2938_audit,
        "m2939_synthesis": m2939_synthesis,
        "m2940_design": m2940_design,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2937_summary": read_json(paths["m2937_summary"]) if source_exists["m2937_summary"] else {},
        "transition_constraint_rows": read_csv_rows(paths["transition_constraint_rows"]),
        "offtrack_persistence_constraint_rows": read_csv_rows(paths["offtrack_persistence_constraint_rows"]),
        "collision_speed_substitution_constraint_rows": read_csv_rows(
            paths["collision_speed_substitution_constraint_rows"]
        ),
        "context_retention_constraint_rows": read_csv_rows(paths["context_retention_constraint_rows"]),
        "positive_transition_reference_rows": read_csv_rows(paths["positive_transition_reference_rows"]),
        "candidate_surface_rows": read_csv_rows(paths["candidate_surface_rows"]),
        "m2937_actor_contract_guard_rows": read_csv_rows(paths["m2937_actor_contract_guard_rows"]),
        "m2937_claim_boundary_rows": read_csv_rows(paths["m2937_claim_boundary_rows"]),
        "m2937_gate_matrix": read_csv_rows(paths["m2937_gate_matrix"]),
        "m2938_audit_text": paths["m2938_audit"].read_text(encoding="utf-8")
        if source_exists["m2938_audit"]
        else "",
        "m2939_synthesis_text": paths["m2939_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2939_synthesis"]
        else "",
        "m2940_design_text": paths["m2940_design"].read_text(encoding="utf-8")
        if source_exists["m2940_design"]
        else "",
        "follow_up_manifest_exists": False,
    }


def build_candidate_route_rows(
    *, transition_count: int, objective_count: int, carryforward_count: int
) -> list[dict[str, Any]]:
    row = {
        "candidate_route_id": "m2941-candidate-route-0001",
        "route_family": ROUTE_FAMILY,
        "source_design": "m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design",
        "admitted_for_materialization": True,
        "actor_surface": "bounded_actor_head_delta_only",
        "source_transition_constraint_count": transition_count,
        "objective_balance_row_count": objective_count,
        "constraint_carryforward_row_count": carryforward_count,
        "required_follow_up": NEXT_ID,
        "claim_boundary": CLAIM_SCOPE,
    }
    row.update(no_execution_contract_flags())
    return [row]


def build_objective_balance_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = [
        (
            "persistent_offtrack_reduction",
            "offtrack_persistence_constraint",
            len(source["offtrack_persistence_constraint_rows"]),
            "primary_failure_pressure",
            "future candidate must directly reduce persistent offtrack pressure",
            "aggregate offtrack-only improvement that leaves offtrack->offtrack rows unresolved",
        ),
        (
            "collision_speed_anti_substitution",
            "collision_speed_substitution_constraint",
            len(source["collision_speed_substitution_constraint_rows"]),
            "substitution_guard",
            "future candidate must not exchange offtrack failures for collision or speed_too_low",
            "counting offtrack reduction while collision/speed failures rise",
        ),
        (
            "success_context_retention",
            "context_retention_constraint",
            len(source["context_retention_constraint_rows"]),
            "context_regression_guard",
            "future candidate must preserve success-context rows",
            "target-only objective that regresses prior success contexts",
        ),
        (
            "positive_reference_preservation",
            "positive_transition_reference",
            len(source["positive_transition_reference_rows"]),
            "positive_diagnostic_reference",
            "future candidate may preserve positive references as diagnostics only",
            "ranking or promotion from positive references",
        ),
        (
            "full_panel_accounting",
            "all_transition_constraints",
            len(source["transition_constraint_rows"]),
            "denominator_guard",
            "future candidate must keep every M2937 transition constraint auditable",
            "hiding rows outside the preferred objective family",
        ),
    ]
    rows = []
    for index, (family, source_family, count, role, required, blocked) in enumerate(specs, start=1):
        rows.append(
            {
                "objective_balance_id": f"m2941-objective-balance-{index:04d}",
                "objective_family": family,
                "source_constraint_family": source_family,
                "source_row_count": count,
                "balance_role": role,
                "required_future_candidate_property": required,
                "blocked_substitution": blocked,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "ranking_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_constraint_carryforward_rows(transition_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(transition_rows, start=1):
        rows.append(
            {
                "carryforward_constraint_id": f"m2941-carryforward-constraint-{index:04d}",
                "source_transition_constraint_id": row.get("transition_constraint_id", ""),
                "source_panel_row_id": row.get("panel_row_id", ""),
                "source_constraint_family": row.get("constraint_family", ""),
                "transition_bucket": row.get("transition_bucket", ""),
                "source_milestone": row.get("source_milestone", ""),
                "task_family": row.get("task_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "window_tag": row.get("window_tag", ""),
                "candidate_route_id": "m2941-candidate-route-0001",
                "objective_family": objective_family_for_constraint(row.get("constraint_family", "")),
                "actor_visible": False,
                "evaluator_side_only": True,
                "future_candidate_must_account": True,
                "execution_scheduled": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "repair_success_claim_made": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def objective_family_for_constraint(constraint_family: str) -> str:
    return {
        "offtrack_persistence_constraint": "persistent_offtrack_reduction",
        "collision_speed_substitution_constraint": "collision_speed_anti_substitution",
        "context_retention_constraint": "success_context_retention",
        "positive_transition_reference": "positive_reference_preservation",
    }.get(constraint_family, "full_panel_accounting")


def build_blocked_shortcut_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "target_only_offtrack_objective",
            "aggregate offtrack-only objective",
            "Offtrack reduction must be balanced against collision speed and context constraints.",
        ),
        (
            "collision_speed_substitution_hidden",
            "offtrack-to-collision or offtrack-to-speed_too_low substitution",
            "Candidate materialization must keep substitution rows visible to evaluator gates.",
        ),
        (
            "success_context_regression_hidden",
            "success-to-offtrack or success-to-collision context regression",
            "Context-retention rows remain carryforward constraints, not ignorable side effects.",
        ),
        (
            "positive_reference_as_ranking",
            "ranking promotion or winner selection from positive references",
            "Positive rows are diagnostic references only.",
        ),
        (
            "constraint_label_actor_input",
            "transition constraint route source diagnostic success or verdict labels as actor input",
            "Evaluator-side labels cannot become deployable actor observations.",
        ),
        (
            "fixed_candidate_replay_as_proof",
            "fixed-candidate replay validation or success-rate verdict",
            "M2941 is no-execution materialization and must route to audit before interpretation.",
        ),
        (
            "winner_selection_or_promotion",
            "candidate ranking winner selection checkpoint promotion",
            "No validated candidate exists in M2941.",
        ),
    ]
    rows = []
    for index, (family, excluded, reason) in enumerate(specs, start=1):
        rows.append(
            {
                "shortcut_id": f"m2941-blocked-shortcut-{index:04d}",
                "shortcut_family": family,
                "excluded_signal_or_claim": excluded,
                "exclusion_reason": reason,
                "actor_visible": False,
                "execution_scheduled": False,
                "training_scheduled": False,
                "validation_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "claim_made": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    route_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    carryforward_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = route_rows + objective_rows + carryforward_rows + shortcut_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("execution_scheduled", any_flag(rows, "execution_scheduled"), False),
        actor_guard("training_scheduled", any_flag(rows, "training_scheduled"), False),
        actor_guard("validation_scheduled", any_flag(rows, "validation_scheduled"), False),
        actor_guard("validation_denominator_allowed", any_flag(rows, "validation_denominator_allowed"), False),
        actor_guard("paper_denominator_allowed", any_flag(rows, "paper_denominator_allowed"), False),
        actor_guard("ranking_allowed", any_flag(rows, "ranking_allowed"), False),
        actor_guard("winner_selection_allowed", any_flag(rows, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(rows, "promotion_allowed"), False),
        actor_guard("actor_input_contract_changed", any_flag(rows, "actor_input_contract_changed"), False),
        actor_guard("hidden_oracle_actor_input_required", any_flag(rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", any_flag(rows, "future_target_actor_input_required"), False),
        actor_guard("actor_visible_rows", any_flag(rows, "actor_visible"), False),
        actor_guard("repair_success_claim_made", any_flag(rows, "repair_success_claim_made"), False),
        actor_guard("driver_performance_claim_made", any_flag(rows, "driver_performance_claim_made"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2941-actor-guard-{field}",
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
    route_rows_present: bool,
    objective_rows_present: bool,
    carryforward_rows_present: bool,
    shortcut_rows_present: bool,
    actor_guards_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("candidate_route_materialized", "artifact", route_rows_present, "candidate_route_rows.csv"),
        ("objective_balance_materialized", "artifact", objective_rows_present, "objective_balance_rows.csv"),
        ("constraint_carryforward_materialized", "artifact", carryforward_rows_present, "constraint_carryforward_rows.csv"),
        ("blocked_shortcuts_materialized", "artifact", shortcut_rows_present, "blocked_shortcut_rows.csv"),
        ("actor_guard_materialized", "artifact", actor_guards_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_doc_materialized", "artifact", artifacts_present, "summary.json and milestone doc"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2942 audit manifest"),
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
        "claim_id": f"m2941_{claim_id}",
        "claim_family": family,
        "allowed_in_m2941": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    route_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    carryforward_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2941"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2941"])]
    objective_counts = {str(row["objective_family"]): int(row["source_row_count"]) for row in objective_rows}
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2937 artifacts and M2938/M2939/M2940 docs present",
            "lineage_invalid",
        ),
        (
            "m2937_status_pass",
            "lineage",
            _bool(source["m2937_summary"].get("status_pass", False))
            and _bool(source["m2937_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2937_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2937_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2938_accepts_m2937",
            "lineage",
            "accepts M2937" in source["m2938_audit_text"],
            "accepts M2937" in source["m2938_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2939_routes_to_m2940",
            "lineage",
            "continue_to_m2940_tradeoff_aware_candidate_design" in source["m2939_synthesis_text"],
            "continue_to_m2940_tradeoff_aware_candidate_design" in source["m2939_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2940_admits_m2941",
            "lineage",
            "admit_m2941_constraint_balanced_candidate_materialization_preflight"
            in source["m2940_design_text"]
            and MILESTONE_ID in source["m2940_design_text"],
            {
                "decision_present": "admit_m2941_constraint_balanced_candidate_materialization_preflight"
                in source["m2940_design_text"],
                "m2941_id_present": MILESTONE_ID in source["m2940_design_text"],
            },
            "M2940 names M2941 materialization",
            "lineage_invalid",
        ),
        (
            "transition_constraints_carried_forward",
            "materialization",
            len(carryforward_rows) == EXPECTED_TRANSITION_CONSTRAINT_COUNT,
            len(carryforward_rows),
            EXPECTED_TRANSITION_CONSTRAINT_COUNT,
            "metric_artifact",
        ),
        (
            "source_specialized_counts_preserved",
            "materialization",
            len(source["offtrack_persistence_constraint_rows"]) == EXPECTED_PERSISTENT_OFFTRACK_COUNT
            and len(source["collision_speed_substitution_constraint_rows"]) == EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT
            and len(source["context_retention_constraint_rows"]) == EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT
            and len(source["positive_transition_reference_rows"]) == EXPECTED_POSITIVE_REFERENCE_COUNT,
            {
                "persistent_offtrack": len(source["offtrack_persistence_constraint_rows"]),
                "collision_speed_substitution": len(source["collision_speed_substitution_constraint_rows"]),
                "context_retention": len(source["context_retention_constraint_rows"]),
                "positive_reference": len(source["positive_transition_reference_rows"]),
            },
            {
                "persistent_offtrack": EXPECTED_PERSISTENT_OFFTRACK_COUNT,
                "collision_speed_substitution": EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT,
                "context_retention": EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT,
                "positive_reference": EXPECTED_POSITIVE_REFERENCE_COUNT,
            },
            "metric_artifact",
        ),
        (
            "candidate_surface_count_preserved",
            "materialization",
            len(source["candidate_surface_rows"]) == EXPECTED_CANDIDATE_SURFACE_COUNT,
            len(source["candidate_surface_rows"]),
            EXPECTED_CANDIDATE_SURFACE_COUNT,
            "metric_artifact",
        ),
        (
            "candidate_route_selected_once",
            "materialization",
            len(route_rows) == 1 and route_rows[0]["route_family"] == ROUTE_FAMILY,
            {"rows": len(route_rows), "route": route_rows[0]["route_family"] if route_rows else ""},
            ROUTE_FAMILY,
            "metric_artifact",
        ),
        (
            "objective_balance_rows_materialized",
            "materialization",
            len(objective_rows) == EXPECTED_OBJECTIVE_BALANCE_COUNT
            and objective_counts.get("persistent_offtrack_reduction") == EXPECTED_PERSISTENT_OFFTRACK_COUNT
            and objective_counts.get("collision_speed_anti_substitution")
            == EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT
            and objective_counts.get("success_context_retention") == EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT
            and objective_counts.get("positive_reference_preservation") == EXPECTED_POSITIVE_REFERENCE_COUNT
            and objective_counts.get("full_panel_accounting") == EXPECTED_TRANSITION_CONSTRAINT_COUNT,
            objective_counts,
            "5 objective rows with preserved M2937 counts",
            "metric_artifact",
        ),
        (
            "carryforward_rows_actor_invisible",
            "contract",
            len(carryforward_rows) == len(source["transition_constraint_rows"])
            and not any_flag(carryforward_rows, "actor_visible"),
            {"carryforward": len(carryforward_rows), "source": len(source["transition_constraint_rows"])},
            "one actor-invisible carryforward row per source transition",
            "contract_violation",
        ),
        (
            "blocked_shortcuts_pass",
            "execution_guardrail",
            bool(shortcut_rows)
            and all(_bool(row["status_pass"]) for row in shortcut_rows)
            and not any_flag(shortcut_rows, "claim_made"),
            f"rows={len(shortcut_rows)}",
            "all shortcuts blocked",
            "objective_overfit",
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
            not any(forbidden_execution_flag(row) for row in route_rows + objective_rows + carryforward_rows + shortcut_rows),
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
        "gate_id": f"m2941_{gate_id}",
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
    route_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    carryforward_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    objective_counts = {str(row["objective_family"]): int(row["source_row_count"]) for row in objective_rows}
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2937_status_pass": _bool(source["m2937_summary"].get("status_pass", False)),
        "m2937_gate_matrix_pass": _bool(source["m2937_summary"].get("gate_matrix_pass", False)),
        "candidate_route_row_count": len(route_rows),
        "selected_candidate_route": route_rows[0]["route_family"] if route_rows else "",
        "objective_balance_row_count": len(objective_rows),
        "objective_source_counts": objective_counts,
        "constraint_carryforward_row_count": len(carryforward_rows),
        "source_transition_constraint_row_count": len(source["transition_constraint_rows"]),
        "offtrack_persistence_constraint_row_count": len(source["offtrack_persistence_constraint_rows"]),
        "collision_speed_substitution_constraint_row_count": len(
            source["collision_speed_substitution_constraint_rows"]
        ),
        "context_retention_constraint_row_count": len(source["context_retention_constraint_rows"]),
        "positive_transition_reference_row_count": len(source["positive_transition_reference_rows"]),
        "candidate_surface_row_count": len(source["candidate_surface_rows"]),
        "blocked_shortcut_row_count": len(shortcut_rows),
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
            "# M2941 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Candidate Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- selected candidate route: `{summary['selected_candidate_route']}`",
            f"- candidate route rows: {summary['candidate_route_row_count']}",
            f"- objective balance rows: {summary['objective_balance_row_count']}",
            f"- constraint carryforward rows: {summary['constraint_carryforward_row_count']}",
            f"- persistent offtrack constraints: {summary['offtrack_persistence_constraint_row_count']}",
            f"- collision/speed substitution constraints: {summary['collision_speed_substitution_constraint_row_count']}",
            f"- context-retention constraints: {summary['context_retention_constraint_row_count']}",
            f"- positive reference rows: {summary['positive_transition_reference_row_count']}",
            f"- blocked shortcut rows: {summary['blocked_shortcut_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2941 materializes candidate design rows only. It does not implement, execute, rank, validate, promote, or claim repair success for a candidate.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2941 constraint-balanced candidate materialization before any execution training validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "candidate_route_rows.csv"),
                str(output_dir / "objective_balance_rows.csv"),
                str(output_dir / "constraint_carryforward_rows.csv"),
                str(output_dir / "blocked_shortcut_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design.md",
                "docs/m2939-engineering-controller-route-a-offtrack-dominant-post-materialization-continuation-or-stop-synthesis.md",
                "docs/m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-result-audit.md",
                "runs/m2937_engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight/summary.json",
            ],
            "parent_config": [
                "experiments/manifests/m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-preflight.json",
                "experiments/manifests/m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design.json",
                "experiments/manifests/m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight.json",
            ],
            "parent_objective": [
                "audit M2941 constraint-balanced candidate materialization before interpretation"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design",
                "m2939-engineering-controller-route-a-offtrack-dominant-post-materialization-continuation-or-stop-synthesis",
                "m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-result-audit",
                "m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight",
            ],
            "blocked_by": [
                "M2941 materialization requires a result audit before interpretation",
                "candidate rows must remain design accounting and cannot become repair-success or validation evidence",
            ],
            "supersedes": ["direct candidate implementation or execution from M2940 without materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2942 must audit M2941 summary gate matrix actor and claim boundaries",
            "M2942 must preserve candidate route objective carryforward shortcut actor and claim row counts",
            "M2942 must not claim repair success validation ranking performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2942 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert materialized candidate rows into repair-success performance validation paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_constraint_balanced_candidate_materialization_result_audit",
            "evidence_increment": "audits M2941 constraint-balanced candidate materialization artifacts",
            "claim_scope": "Result audit only; no repair execution validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2941 artifacts are missing or gate matrix fails",
                "stop if candidate route objective or carryforward rows are incomplete",
                "stop if actor or claim boundaries were violated",
                "stop if the audit cannot choose a bounded next design pivot stop or synthesis route without overclaiming",
            ],
            "fallback_plan": [
                "route to artifact repair if materialization failed",
                "route to branch stop or pivot if no bounded candidate implementation route remains",
                "route to a bounded next design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2941 completes constraint-balanced candidate materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2941 constraint-balanced candidate materialization artifacts",
            "admission_evidence": [
                "M2941 summary and gate matrix",
                "M2941 candidate route objective carryforward shortcut actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2942 status queue scoreboard research log and review",
                "one follow-up manifest only if M2942 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2942 audit accepts or rejects M2941 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2942 audits Route A candidate materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2942; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2937-to-M2941 Route A tradeoff-aware candidate design chain.",
            "negative_result_policy": "Preserve negative or insufficient constraints and route to pivot or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2941 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized constraint-balanced candidate rows",
            "paper_verdict_delta": "no paper verdict; audit may admit a bounded candidate implementation design or stop/pivot Route A repair",
            "must_synthesize_if": [
                "M2942 cannot accept M2941 as complete and claim-safe",
                "M2942 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2942 would continue another fixed-candidate execution without a materially changed evidence question",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2942 audits M2941 artifacts row counts gates actor and claim boundaries",
            "M2942 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2942 hides M2941 failures or missing artifacts",
            "M2942 treats M2941 constraints as repair success validation readiness or performance verdict",
            "M2942 selects candidate execution without preserving actor and claim boundaries",
        ],
        "decision_rule": "Pass only if M2942 preserves M2941 candidate materialization evidence and chooses one bounded next route or stop state without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "candidate_route_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def no_execution_contract_flags() -> dict[str, Any]:
    return {
        "execution_scheduled": False,
        "training_scheduled": False,
        "validation_scheduled": False,
        "ranking_allowed": False,
        "winner_selection_allowed": False,
        "promotion_allowed": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "actor_visible": False,
        "diagnostic_only_no_verdict": True,
    }


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    keys = [
        "execution_scheduled",
        "training_scheduled",
        "validation_scheduled",
        "validation_denominator_allowed",
        "paper_denominator_allowed",
        "ranking_allowed",
        "ranking_run",
        "ranking_claim_made",
        "winner_selection_allowed",
        "winner_selected",
        "promotion_allowed",
        "checkpoint_promoted",
        "actor_input_contract_changed",
        "hidden_oracle_actor_input_required",
        "future_target_actor_input_required",
        "actor_visible",
        "repair_success_claim_made",
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
        "claim_made",
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
    parser.add_argument("--m2937-dir", type=Path, default=DEFAULT_M2937_DIR)
    parser.add_argument("--m2938-audit", type=Path, default=DEFAULT_M2938_AUDIT)
    parser.add_argument("--m2939-synthesis", type=Path, default=DEFAULT_M2939_SYNTHESIS)
    parser.add_argument("--m2940-design", type=Path, default=DEFAULT_M2940_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_constraint_balanced_candidate_materialization_preflight(
        m2937_dir=args.m2937_dir,
        m2938_audit=args.m2938_audit,
        m2939_synthesis=args.m2939_synthesis,
        m2940_design=args.m2940_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"candidate_route_row_count={summary['candidate_route_row_count']}")
    print(f"objective_balance_row_count={summary['objective_balance_row_count']}")
    print(f"constraint_carryforward_row_count={summary['constraint_carryforward_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
