"""Materialize M2943 residual actor-head delta implementation contracts.

M2944 consumes the accepted M2941/M2942 candidate materialization and the
M2943 implementation design. It performs no implementation, checkpoint
mutation, environment execution, replay, validation, training, ranking, or
promotion work. Its only job is to convert the design into machine-checkable
implementation surface, delta contract, objective binding, traceability,
shortcut, actor, claim, gate, summary, doc, and follow-up audit artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2944-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-implementation-contract-materialization-preflight"
)
NEXT_ID = (
    "m2945-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-implementation-contract-materialization-result-audit"
)
DEFAULT_M2941_DIR = Path(
    "runs/m2941_engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight"
)
DEFAULT_M2942_AUDIT = Path(
    "docs/m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-result-audit.md"
)
DEFAULT_M2943_DESIGN = Path(
    "docs/m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2944_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_implementation_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2944-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2945-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-result-audit.json"
)

EXPECTED_CARRYFORWARD_CONSTRAINT_COUNT = 56
EXPECTED_OBJECTIVE_BALANCE_COUNT = 5
EXPECTED_PERSISTENT_OFFTRACK_COUNT = 24
EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT = 10
EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT = 9
EXPECTED_POSITIVE_REFERENCE_COUNT = 4
EXPECTED_FULL_PANEL_COUNT = 56
EXPECTED_IMPLEMENTATION_SURFACE_COUNT = 1
EXPECTED_DELTA_CONTRACT_COUNT = 7
EXPECTED_BLOCKED_SHORTCUT_COUNT = 8

IMPLEMENTATION_DESIGN = "frozen_trunk_bounded_residual_actor_head_delta_design"
CLAIM_SCOPE = (
    "M2944 Route A residual actor-head delta implementation-contract "
    "materialization only; M2941/M2943 rows may be converted into "
    "implementation-surface, delta-contract, objective-binding, traceability, "
    "shortcut, actor-guard, claim-boundary, gate, summary, doc, and follow-up "
    "audit artifacts. No residual-head code implementation, checkpoint "
    "mutation, reset, step, rollout, replay, validation, training, PPO, "
    "dependency work, ranking, winner selection, promotion, success-rate "
    "verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "implementation readiness or result, source/task/checkpoint/environment/"
    "window/severity/time-band ranking, candidate ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

IMPLEMENTATION_SURFACE_FIELDNAMES = [
    "implementation_surface_id",
    "design_family",
    "source_design",
    "admitted_for_materialization",
    "parent_actor_policy",
    "mutable_surface",
    "frozen_surface",
    "residual_combination",
    "zero_delta_fallback_required",
    "implementation_scheduled",
    "checkpoint_modification_scheduled",
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
    "required_follow_up",
    "claim_boundary",
]
DELTA_CONTRACT_FIELDNAMES = [
    "delta_contract_id",
    "contract_family",
    "required_property",
    "observed_or_declared_value",
    "expected_value",
    "status_pass",
    "implementation_scheduled",
    "checkpoint_modification_scheduled",
    "execution_scheduled",
    "training_scheduled",
    "validation_scheduled",
    "ranking_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
OBJECTIVE_BINDING_FIELDNAMES = [
    "objective_binding_id",
    "source_objective_balance_id",
    "objective_family",
    "source_constraint_family",
    "source_row_count",
    "expected_source_row_count",
    "status_pass",
    "implementation_contract_property",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CONSTRAINT_TRACEABILITY_FIELDNAMES = [
    "traceability_id",
    "source_carryforward_constraint_id",
    "source_transition_constraint_id",
    "source_panel_row_id",
    "source_constraint_family",
    "transition_bucket",
    "objective_family",
    "implementation_surface_id",
    "actor_visible",
    "evaluator_side_only",
    "future_candidate_must_account",
    "implementation_scheduled",
    "checkpoint_modification_scheduled",
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
    "implementation_scheduled",
    "checkpoint_modification_scheduled",
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
    "allowed_in_m2944",
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
    "implementation_surface_rows",
    "delta_contract_rows",
    "objective_binding_rows",
    "constraint_traceability_rows",
    "blocked_shortcut_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_actor_head_delta_implementation_contract_materialization_preflight(
    *,
    m2941_dir: Path | str = DEFAULT_M2941_DIR,
    m2942_audit: Path | str = DEFAULT_M2942_AUDIT,
    m2943_design: Path | str = DEFAULT_M2943_DESIGN,
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
        m2941_dir=Path(m2941_dir),
        m2942_audit=Path(m2942_audit),
        m2943_design=Path(m2943_design),
    )

    surface_rows = build_implementation_surface_rows()
    delta_rows = build_delta_contract_rows()
    objective_rows = build_objective_binding_rows(source["objective_balance_rows"])
    traceability_rows = build_constraint_traceability_rows(source["constraint_carryforward_rows"])
    shortcut_rows = build_blocked_shortcut_rows()

    write_csv_rows(
        paths["implementation_surface_rows"],
        surface_rows,
        fieldnames=IMPLEMENTATION_SURFACE_FIELDNAMES,
    )
    write_csv_rows(paths["delta_contract_rows"], delta_rows, fieldnames=DELTA_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["objective_binding_rows"], objective_rows, fieldnames=OBJECTIVE_BINDING_FIELDNAMES)
    write_csv_rows(
        paths["constraint_traceability_rows"],
        traceability_rows,
        fieldnames=CONSTRAINT_TRACEABILITY_FIELDNAMES,
    )
    write_csv_rows(paths["blocked_shortcut_rows"], shortcut_rows, fieldnames=BLOCKED_SHORTCUT_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "implementation_surface_row_count": len(surface_rows),
            "delta_contract_row_count": len(delta_rows),
            "objective_binding_row_count": len(objective_rows),
            "constraint_traceability_row_count": len(traceability_rows),
            "blocked_shortcut_row_count": len(shortcut_rows),
            "implementation_performed": False,
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        surface_rows=surface_rows,
        delta_rows=delta_rows,
        objective_rows=objective_rows,
        traceability_rows=traceability_rows,
        shortcut_rows=shortcut_rows,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_without_summary_doc,
        surface_rows_present=bool(surface_rows),
        delta_rows_present=bool(delta_rows),
        objective_rows_present=bool(objective_rows),
        traceability_rows_present=bool(traceability_rows),
        shortcut_rows_present=bool(shortcut_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        surface_rows=surface_rows,
        delta_rows=delta_rows,
        objective_rows=objective_rows,
        traceability_rows=traceability_rows,
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
        surface_rows=surface_rows,
        delta_rows=delta_rows,
        objective_rows=objective_rows,
        traceability_rows=traceability_rows,
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
        surface_rows_present=bool(surface_rows),
        delta_rows_present=bool(delta_rows),
        objective_rows_present=bool(objective_rows),
        traceability_rows_present=bool(traceability_rows),
        shortcut_rows_present=bool(shortcut_rows),
        actor_guards_present=bool(actor_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        surface_rows=surface_rows,
        delta_rows=delta_rows,
        objective_rows=objective_rows,
        traceability_rows=traceability_rows,
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
        surface_rows=surface_rows,
        delta_rows=delta_rows,
        objective_rows=objective_rows,
        traceability_rows=traceability_rows,
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
            "implementation_surface_row_count": len(surface_rows),
            "delta_contract_row_count": len(delta_rows),
            "objective_binding_row_count": len(objective_rows),
            "constraint_traceability_row_count": len(traceability_rows),
            "blocked_shortcut_row_count": len(shortcut_rows),
            "actor_contract_guard_row_count": len(actor_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "implementation_performed": False,
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
        "implementation_surface_rows": output_dir / "implementation_surface_rows.csv",
        "delta_contract_rows": output_dir / "delta_contract_rows.csv",
        "objective_binding_rows": output_dir / "objective_binding_rows.csv",
        "constraint_traceability_rows": output_dir / "constraint_traceability_rows.csv",
        "blocked_shortcut_rows": output_dir / "blocked_shortcut_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2941_dir: Path, m2942_audit: Path, m2943_design: Path) -> dict[str, Any]:
    paths = {
        "m2941_summary": m2941_dir / "summary.json",
        "candidate_route_rows": m2941_dir / "candidate_route_rows.csv",
        "objective_balance_rows": m2941_dir / "objective_balance_rows.csv",
        "constraint_carryforward_rows": m2941_dir / "constraint_carryforward_rows.csv",
        "blocked_shortcut_rows": m2941_dir / "blocked_shortcut_rows.csv",
        "m2941_actor_contract_guard_rows": m2941_dir / "actor_contract_guard_rows.csv",
        "m2941_claim_boundary_rows": m2941_dir / "claim_boundary_rows.csv",
        "m2941_gate_matrix": m2941_dir / "gate_matrix.csv",
        "m2942_audit": m2942_audit,
        "m2943_design": m2943_design,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2941_summary": read_json(paths["m2941_summary"]) if source_exists["m2941_summary"] else {},
        "candidate_route_rows": read_csv_rows(paths["candidate_route_rows"]),
        "objective_balance_rows": read_csv_rows(paths["objective_balance_rows"]),
        "constraint_carryforward_rows": read_csv_rows(paths["constraint_carryforward_rows"]),
        "blocked_shortcut_rows": read_csv_rows(paths["blocked_shortcut_rows"]),
        "m2941_actor_contract_guard_rows": read_csv_rows(paths["m2941_actor_contract_guard_rows"]),
        "m2941_claim_boundary_rows": read_csv_rows(paths["m2941_claim_boundary_rows"]),
        "m2941_gate_matrix": read_csv_rows(paths["m2941_gate_matrix"]),
        "m2942_audit_text": paths["m2942_audit"].read_text(encoding="utf-8")
        if source_exists["m2942_audit"]
        else "",
        "m2943_design_text": paths["m2943_design"].read_text(encoding="utf-8")
        if source_exists["m2943_design"]
        else "",
        "follow_up_manifest_exists": False,
    }


def build_implementation_surface_rows() -> list[dict[str, Any]]:
    row = {
        "implementation_surface_id": "m2944-implementation-surface-0001",
        "design_family": IMPLEMENTATION_DESIGN,
        "source_design": "m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design",
        "admitted_for_materialization": True,
        "parent_actor_policy": "existing_parent_actor_path",
        "mutable_surface": "bounded_residual_actor_head_delta_contract_only",
        "frozen_surface": "observation_contract_parent_actor_trunk_and_non_delta_action_mapping",
        "residual_combination": "parent_action_plus_bounded_delta_contract",
        "zero_delta_fallback_required": True,
        "required_follow_up": NEXT_ID,
        "claim_boundary": CLAIM_SCOPE,
    }
    row.update(no_implementation_execution_flags())
    return [row]


def build_delta_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("residual_head_only_surface", True, True, "future implementation must only materialize residual actor-head delta"),
        ("bounded_output_required", True, True, "future residual output must be bounded before action combination"),
        ("zero_delta_parent_fallback", True, True, "zero residual must reproduce parent actor action path"),
        ("parent_trunk_frozen", True, True, "parent trunk and observation preprocessing remain unchanged"),
        ("deployed_action_mapping_preserved", "[steer, throttle, brake]", "[steer, throttle, brake]", "action mapping unchanged"),
        ("evaluator_labels_actor_invisible", False, False, "objective constraint diagnostic and verdict labels remain actor-invisible"),
        ("numeric_bounds_deferred_to_contract_rows", True, True, "M2944 records bound requirement but does not implement numeric tensors"),
    ]
    rows = []
    for index, (family, observed, expected, required) in enumerate(specs, start=1):
        rows.append(
            {
                "delta_contract_id": f"m2944-delta-contract-{index:04d}",
                "contract_family": family,
                "required_property": required,
                "observed_or_declared_value": observed,
                "expected_value": expected,
                "status_pass": str(observed) == str(expected),
                "implementation_scheduled": False,
                "checkpoint_modification_scheduled": False,
                "execution_scheduled": False,
                "training_scheduled": False,
                "validation_scheduled": False,
                "ranking_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_objective_binding_rows(objective_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    expected_counts = {
        "persistent_offtrack_reduction": EXPECTED_PERSISTENT_OFFTRACK_COUNT,
        "collision_speed_anti_substitution": EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT,
        "success_context_retention": EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT,
        "positive_reference_preservation": EXPECTED_POSITIVE_REFERENCE_COUNT,
        "full_panel_accounting": EXPECTED_FULL_PANEL_COUNT,
    }
    rows = []
    for index, row in enumerate(objective_rows, start=1):
        family = str(row.get("objective_family", ""))
        observed_count = _int(row.get("source_row_count", 0))
        expected_count = expected_counts.get(family, observed_count)
        rows.append(
            {
                "objective_binding_id": f"m2944-objective-binding-{index:04d}",
                "source_objective_balance_id": row.get("objective_balance_id", ""),
                "objective_family": family,
                "source_constraint_family": row.get("source_constraint_family", ""),
                "source_row_count": observed_count,
                "expected_source_row_count": expected_count,
                "status_pass": observed_count == expected_count,
                "implementation_contract_property": implementation_property_for_objective(family),
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def implementation_property_for_objective(family: str) -> str:
    return {
        "persistent_offtrack_reduction": "residual-head contract must not ignore persistent offtrack pressure",
        "collision_speed_anti_substitution": "residual-head contract must block offtrack-to-collision/speed substitution hiding",
        "success_context_retention": "residual-head contract must preserve success-context regression accounting",
        "positive_reference_preservation": "positive references remain diagnostics only and cannot rank a candidate",
        "full_panel_accounting": "all carryforward constraints remain linked to implementation contract rows",
    }.get(family, "unknown objective family must not be treated as success evidence")


def build_constraint_traceability_rows(carryforward_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(carryforward_rows, start=1):
        rows.append(
            {
                "traceability_id": f"m2944-traceability-{index:04d}",
                "source_carryforward_constraint_id": row.get("carryforward_constraint_id", ""),
                "source_transition_constraint_id": row.get("source_transition_constraint_id", ""),
                "source_panel_row_id": row.get("source_panel_row_id", ""),
                "source_constraint_family": row.get("source_constraint_family", ""),
                "transition_bucket": row.get("transition_bucket", ""),
                "objective_family": row.get("objective_family", ""),
                "implementation_surface_id": "m2944-implementation-surface-0001",
                "actor_visible": False,
                "evaluator_side_only": True,
                "future_candidate_must_account": True,
                "implementation_scheduled": False,
                "checkpoint_modification_scheduled": False,
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


def build_blocked_shortcut_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "direct_residual_code_implementation",
            "residual-head code implementation or tensor creation",
            "M2944 materializes contracts only; implementation requires later audited admission.",
        ),
        (
            "checkpoint_modification",
            "parent checkpoint mutation or promotion",
            "No checkpoint can be modified or promoted during contract materialization.",
        ),
        (
            "full_policy_or_trunk_rewrite",
            "full actor retrain trunk rewrite observation-preprocess rewrite",
            "The admitted surface is residual actor-head delta only.",
        ),
        (
            "evaluator_label_conditioning",
            "route objective constraint diagnostic success progress verdict labels as actor input",
            "Evaluator-side labels cannot become deployable actor observations.",
        ),
        (
            "target_only_offtrack_loss",
            "aggregate offtrack-only implementation objective",
            "Objective binding must preserve collision/speed substitution and context-retention constraints.",
        ),
        (
            "fixed_replay_as_proof",
            "fixed replay validation readiness or success-rate proof",
            "M2944 is no-execution materialization and must route to audit before interpretation.",
        ),
        (
            "candidate_ranking",
            "candidate row ranking or winner selection",
            "No implemented or validated candidate exists in M2944.",
        ),
        (
            "repair_success_or_performance_claim",
            "repair-success driver-performance paper high-fidelity or self-ID claim",
            "Implementation contracts are not driver evidence.",
        ),
    ]
    rows = []
    for index, (family, excluded, reason) in enumerate(specs, start=1):
        row = {
            "shortcut_id": f"m2944-blocked-shortcut-{index:04d}",
            "shortcut_family": family,
            "excluded_signal_or_claim": excluded,
            "exclusion_reason": reason,
            "claim_made": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        row.update(no_implementation_execution_flags())
        rows.append(row)
    return rows


def build_actor_contract_guard_rows(
    *,
    surface_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = surface_rows + delta_rows + objective_rows + traceability_rows + shortcut_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("implementation_scheduled", any_flag(rows, "implementation_scheduled"), False),
        actor_guard("checkpoint_modification_scheduled", any_flag(rows, "checkpoint_modification_scheduled"), False),
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
        "guard_id": f"m2944-actor-guard-{field}",
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
    surface_rows_present: bool,
    delta_rows_present: bool,
    objective_rows_present: bool,
    traceability_rows_present: bool,
    shortcut_rows_present: bool,
    actor_guards_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("implementation_surface_materialized", "artifact", surface_rows_present, "implementation_surface_rows.csv"),
        ("delta_contract_materialized", "artifact", delta_rows_present, "delta_contract_rows.csv"),
        ("objective_binding_materialized", "artifact", objective_rows_present, "objective_binding_rows.csv"),
        ("constraint_traceability_materialized", "artifact", traceability_rows_present, "constraint_traceability_rows.csv"),
        ("blocked_shortcuts_materialized", "artifact", shortcut_rows_present, "blocked_shortcut_rows.csv"),
        ("actor_guard_materialized", "artifact", actor_guards_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_doc_materialized", "artifact", artifacts_present, "summary.json and milestone doc"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2945 audit manifest"),
    ]
    blocked = [
        ("residual_code_implementation", "implementation", "future implementation admission"),
        ("checkpoint_mutation", "implementation", "future implementation admission"),
        ("reset_step_rollout_replay", "execution", "future bounded execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("dependency_execution", "execution", "future dependency route"),
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
        "claim_id": f"m2944_{claim_id}",
        "claim_family": family,
        "allowed_in_m2944": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    surface_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2944"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2944"])]
    objective_counts = {str(row["objective_family"]): int(row["source_row_count"]) for row in objective_rows}
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2941 artifacts and M2942/M2943 docs present",
            "lineage_invalid",
        ),
        (
            "m2941_status_pass",
            "lineage",
            _bool(source["m2941_summary"].get("status_pass", False))
            and _bool(source["m2941_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2941_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2941_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2942_accepts_m2941",
            "lineage",
            "accepts M2941" in source["m2942_audit_text"],
            "accepts M2941" in source["m2942_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2943_admits_m2944",
            "lineage",
            "admit_m2944_actor_head_delta_implementation_contract_materialization_preflight"
            in source["m2943_design_text"]
            and MILESTONE_ID in source["m2943_design_text"],
            {
                "decision_present": "admit_m2944_actor_head_delta_implementation_contract_materialization_preflight"
                in source["m2943_design_text"],
                "m2944_id_present": MILESTONE_ID in source["m2943_design_text"],
            },
            "M2943 names M2944 materialization",
            "lineage_invalid",
        ),
        (
            "implementation_surface_materialized",
            "materialization",
            len(surface_rows) == EXPECTED_IMPLEMENTATION_SURFACE_COUNT
            and surface_rows[0]["design_family"] == IMPLEMENTATION_DESIGN,
            {"rows": len(surface_rows), "design": surface_rows[0]["design_family"] if surface_rows else ""},
            IMPLEMENTATION_DESIGN,
            "metric_artifact",
        ),
        (
            "delta_contract_rows_materialized",
            "materialization",
            len(delta_rows) == EXPECTED_DELTA_CONTRACT_COUNT
            and all(_bool(row.get("status_pass", False)) for row in delta_rows),
            f"rows={len(delta_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in delta_rows)}",
            f"{EXPECTED_DELTA_CONTRACT_COUNT} passing rows",
            "contract_violation",
        ),
        (
            "objective_binding_rows_materialized",
            "materialization",
            len(objective_rows) == EXPECTED_OBJECTIVE_BALANCE_COUNT
            and objective_counts.get("persistent_offtrack_reduction") == EXPECTED_PERSISTENT_OFFTRACK_COUNT
            and objective_counts.get("collision_speed_anti_substitution")
            == EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT
            and objective_counts.get("success_context_retention") == EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT
            and objective_counts.get("positive_reference_preservation") == EXPECTED_POSITIVE_REFERENCE_COUNT
            and objective_counts.get("full_panel_accounting") == EXPECTED_FULL_PANEL_COUNT
            and all(_bool(row.get("status_pass", False)) for row in objective_rows),
            objective_counts,
            "5 objective rows with preserved M2941 counts",
            "metric_artifact",
        ),
        (
            "traceability_rows_carried_forward",
            "materialization",
            len(traceability_rows) == EXPECTED_CARRYFORWARD_CONSTRAINT_COUNT
            and len(source["constraint_carryforward_rows"]) == EXPECTED_CARRYFORWARD_CONSTRAINT_COUNT
            and not any_flag(traceability_rows, "actor_visible"),
            {"traceability": len(traceability_rows), "source": len(source["constraint_carryforward_rows"])},
            f"{EXPECTED_CARRYFORWARD_CONSTRAINT_COUNT} actor-invisible traceability rows",
            "metric_artifact",
        ),
        (
            "blocked_shortcuts_pass",
            "execution_guardrail",
            len(shortcut_rows) == EXPECTED_BLOCKED_SHORTCUT_COUNT
            and all(_bool(row["status_pass"]) for row in shortcut_rows)
            and not any_flag(shortcut_rows, "claim_made"),
            f"rows={len(shortcut_rows)}",
            f"{EXPECTED_BLOCKED_SHORTCUT_COUNT} shortcuts blocked",
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
            "no_forbidden_implementation_execution_or_overclaim",
            "execution_guardrail",
            not any(
                forbidden_execution_flag(row)
                for row in surface_rows + delta_rows + objective_rows + traceability_rows + shortcut_rows
            ),
            "no implementation/execution/ranking/promotion/overclaim flags",
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
        "gate_id": f"m2944_{gate_id}",
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
    surface_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
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
            "engineering_controller_route_a_offtrack_dominant_actor_head_delta_implementation_contract_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_actor_head_delta_implementation_contract_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2941_status_pass": _bool(source["m2941_summary"].get("status_pass", False)),
        "m2941_gate_matrix_pass": _bool(source["m2941_summary"].get("gate_matrix_pass", False)),
        "implementation_surface_row_count": len(surface_rows),
        "selected_implementation_design": surface_rows[0]["design_family"] if surface_rows else "",
        "delta_contract_row_count": len(delta_rows),
        "delta_contract_rows_pass": all(_bool(row.get("status_pass", False)) for row in delta_rows),
        "objective_binding_row_count": len(objective_rows),
        "objective_source_counts": objective_counts,
        "constraint_traceability_row_count": len(traceability_rows),
        "source_carryforward_constraint_row_count": len(source["constraint_carryforward_rows"]),
        "blocked_shortcut_row_count": len(shortcut_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "implementation_run": False,
        "checkpoint_modification_run": False,
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
            "# M2944 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Implementation Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- selected implementation design: `{summary['selected_implementation_design']}`",
            f"- implementation surface rows: {summary['implementation_surface_row_count']}",
            f"- delta contract rows: {summary['delta_contract_row_count']}",
            f"- objective binding rows: {summary['objective_binding_row_count']}",
            f"- constraint traceability rows: {summary['constraint_traceability_row_count']}",
            f"- blocked shortcut rows: {summary['blocked_shortcut_row_count']}",
            f"- actor contract guards: {summary['actor_contract_guard_row_count']}",
            f"- claim boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2944 materializes implementation contracts only. It does not implement code, mutate checkpoints, execute, train, validate, rank, promote, or claim repair success.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2944 residual actor-head delta implementation-contract materialization before any implementation execution training validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "implementation_surface_rows.csv"),
                str(output_dir / "delta_contract_rows.csv"),
                str(output_dir / "objective_binding_rows.csv"),
                str(output_dir / "constraint_traceability_rows.csv"),
                str(output_dir / "blocked_shortcut_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design.md",
                "docs/m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2944-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-preflight.json",
                "experiments/manifests/m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design.json",
            ],
            "parent_objective": [
                "audit M2944 residual actor-head delta implementation-contract materialization before interpretation"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design",
                "m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-result-audit",
                "m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-preflight",
            ],
            "blocked_by": [
                "M2944 materialization requires a result audit before interpretation",
                "implementation contract rows must not become implementation readiness validation or performance evidence",
            ],
            "supersedes": ["direct residual actor-head implementation without contract audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2945 must audit M2944 summary gate matrix actor and claim boundaries",
            "M2945 must preserve implementation surface delta objective traceability shortcut actor and claim row counts",
            "M2945 must not claim implementation readiness repair success validation ranking performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2945 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not implement residual-head code modify checkpoints rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert materialized implementation contracts into repair-success performance validation paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_implementation_contract_materialization_result_audit",
            "evidence_increment": "audits M2944 residual actor-head delta implementation-contract materialization artifacts",
            "claim_scope": "Result audit only; no implementation execution validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2944 artifacts are missing or gate matrix fails",
                "stop if traceability or objective binding rows are incomplete",
                "stop if actor or claim boundaries were violated",
                "stop if the audit cannot choose a bounded next route or stop state without overclaiming",
            ],
            "fallback_plan": [
                "route to artifact repair if materialization failed",
                "route to branch stop or pivot if no bounded implementation route remains",
                "route to a bounded implementation admission only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2944 completes residual actor-head delta contract materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2944 residual actor-head delta implementation-contract materialization artifacts",
            "admission_evidence": [
                "M2944 summary and gate matrix",
                "M2944 implementation surface delta objective traceability shortcut actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no implementation execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2945 status queue scoreboard research log and review",
                "one follow-up manifest only if M2945 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2945 audit accepts or rejects M2944 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2945 audits Route A implementation-contract materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2945; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2941-to-M2944 Route A actor-head delta implementation-contract chain.",
            "negative_result_policy": "Preserve negative or insufficient constraints and route to pivot or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2944 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized residual actor-head delta implementation contracts",
            "paper_verdict_delta": "no paper verdict; audit may admit bounded implementation admission or stop/pivot Route A repair",
            "must_synthesize_if": [
                "M2945 cannot accept M2944 as complete and claim-safe",
                "M2945 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2945 would continue to implementation without preserving actor and claim boundaries",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2945 audits M2944 artifacts row counts gates actor and claim boundaries",
            "M2945 selects exactly one next route or stop state",
            "no implementation validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2945 hides M2944 failures or missing artifacts",
            "M2945 treats M2944 contracts as implementation readiness repair success validation readiness or performance verdict",
            "M2945 selects implementation without preserving actor and claim boundaries",
        ],
        "decision_rule": "Pass only if M2945 preserves M2944 implementation-contract materialization evidence and chooses one bounded next route or stop state without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "implementation_surface_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def no_implementation_execution_flags() -> dict[str, Any]:
    return {
        "implementation_scheduled": False,
        "checkpoint_modification_scheduled": False,
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
        "implementation_scheduled",
        "checkpoint_modification_scheduled",
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


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2941-dir", type=Path, default=DEFAULT_M2941_DIR)
    parser.add_argument("--m2942-audit", type=Path, default=DEFAULT_M2942_AUDIT)
    parser.add_argument("--m2943-design", type=Path, default=DEFAULT_M2943_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_actor_head_delta_implementation_contract_materialization_preflight(
        m2941_dir=args.m2941_dir,
        m2942_audit=args.m2942_audit,
        m2943_design=args.m2943_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"implementation_surface_row_count={summary['implementation_surface_row_count']}")
    print(f"delta_contract_row_count={summary['delta_contract_row_count']}")
    print(f"objective_binding_row_count={summary['objective_binding_row_count']}")
    print(f"constraint_traceability_row_count={summary['constraint_traceability_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
