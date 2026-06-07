"""Materialize M3004 post-residual-stop source-axis expansion rows.

M3004 is a no-execution materialization preflight. It converts the M3003
exhausted M1690 L3 source-space design into machine-checkable source
inventory, exhausted-surface, same-surface rejection, candidate-axis,
actor-contract, claim-boundary, and gate artifacts for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3004-engineering-controller-route-a-post-residual-stop-source-axis-"
    "expansion-materialization-preflight"
)
NEXT_ID = (
    "m3005-engineering-controller-route-a-post-residual-stop-source-axis-"
    "expansion-materialization-result-audit"
)
DEFAULT_M3003_DESIGN = Path(
    "docs/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-"
    "evidence-surface-design.md"
)
DEFAULT_M1690_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/"
    "executable_workload_matrix.csv"
)
DEFAULT_M2916_DIR = Path(
    "runs/m2916_engineering_controller_route_a_dependency_facing_evidence_surface_"
    "execution_admission_materialization_preflight"
)
DEFAULT_M2919_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_"
    "bounded_execution_preflight"
)
DEFAULT_M2922_DIR = Path(
    "runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_"
    "materialization_preflight"
)
DEFAULT_M2925_DIR = Path(
    "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_"
    "materialization_preflight"
)
DEFAULT_M2934_DIR = Path(
    "runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_"
    "outcome_shift_localization_preflight"
)
DEFAULT_M3000_DIR = Path(
    "runs/m3000_engineering_controller_route_a_offtrack_dominant_constraint_balanced_"
    "actor_head_delta_nonzero_residual_bounded_diagnostic_validation_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3004_engineering_controller_route_a_post_residual_stop_source_axis_"
    "expansion_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-"
    "materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m3005-engineering-controller-route-a-post-residual-stop-"
    "source-axis-expansion-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M3004 Route A post-residual-stop source-axis expansion materialization only; "
    "existing current-sim diagnostic artifacts may be inventoried into source, "
    "exhausted-surface, same-surface rejection, candidate-axis, supporting guard, "
    "actor-contract, claim-boundary, and gate rows. No reset, step, rollout, "
    "replay, validation, training, PPO, source build, adapter probe, external "
    "simulation, ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, current-sim "
    "verdict, high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "fresh M1690 L3 row selection, eval-seed-only source expansion, repair success, "
    "driver performance, validation readiness or result, source/task/checkpoint "
    "ranking, winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)
DECISION_PASS = "source_axis_expansion_materialized_route_to_m3005_result_audit"
DECISION_FAIL = "source_axis_expansion_materialization_incomplete"

TASK_SOURCE_PATTERN = re.compile(r"m1680-spec-\d{4}")

PRIOR_SURFACE_SPECS = [
    (
        "m2737",
        Path(
            "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_"
            "diverse_closed_loop_evidence_surface_bounded_execution_preflight/"
            "candidate_execution_rows.csv"
        ),
        "prior_route_a_source_diverse_closed_loop_diagnostic",
    ),
    (
        "m2746",
        Path(
            "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_"
            "scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv"
        ),
        "prior_route_a_failure_taxonomy_scenario_role_metric_panel",
    ),
    (
        "m2807",
        Path(
            "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_"
            "repair_cross_axis_bounded_execution_preflight/candidate_execution_rows.csv"
        ),
        "prior_route_a_clearance_negative_non_same_repair_cross_axis",
    ),
    (
        "m2816",
        Path(
            "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_"
            "window_instrumented_bounded_execution_preflight/instrumented_execution_rows.csv"
        ),
        "prior_route_a_action_response_recoverability_window",
    ),
    (
        "m2828",
        Path(
            "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_"
            "loop_evidence_expansion_preflight/candidate_execution_rows.csv"
        ),
        "prior_route_a_post_package_source_diverse_expansion",
    ),
    (
        "m2838",
        Path(
            "runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_"
            "loop_evidence_preflight/candidate_execution_rows.csv"
        ),
        "prior_post_route_c_hf3_stop_source_diverse_diagnostic",
    ),
    (
        "m2868",
        Path(
            "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_"
            "localized_response_prediction_candidate_closed_loop_delta_panel/paired_execution_rows.csv"
        ),
        "prior_route_a_localized_response_prediction_pair_panel",
    ),
    (
        "m2877",
        Path(
            "runs/m2877_engineering_controller_route_a_post_package_refresh_fresh_closed_"
            "loop_evidence_preflight/candidate_execution_rows.csv"
        ),
        "prior_remaining_m1690_l3_fresh_row_panel",
    ),
]

SOURCE_INVENTORY_FIELDNAMES = [
    "source_inventory_id",
    "source_milestone",
    "artifact_path",
    "artifact_exists",
    "artifact_kind",
    "source_role",
    "observed_row_count",
    "unique_task_source_id_count",
    "m1690_l3_overlap_count",
    "execution_performed_by_m3004",
    "used_for_fresh_denominator_selection",
    "claim_scope",
]
EXHAUSTED_SURFACE_FIELDNAMES = [
    "m3004_exhausted_row_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "config_exists",
    "checkpoint_exists",
    "covered_by_prior_surface",
    "coverage_source_milestones",
    "coverage_surface_count",
    "unused_for_m1690_l3_row_selection",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
PRIOR_IDENTITY_FIELDNAMES = [
    "prior_surface_identity_id",
    "source_milestone",
    "source_artifact",
    "source_family",
    "source_row_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "included_in_m1690_l3",
    "same_surface_reuse_allowed",
    "actor_visible",
    "claim_boundary",
]
SOURCE_AXIS_FIELDNAMES = [
    "source_axis_candidate_id",
    "axis_family",
    "axis_name",
    "axis_status",
    "source_identity_requirement",
    "future_materialization_required",
    "future_execution_manifest_required",
    "uses_exhausted_m1690_l3_rows_as_evidence_surface",
    "eval_seed_only",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "ordinary_engineering_candidate_axis",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "execution_scheduled_by_m3004",
    "ranking_allowed",
    "claim_boundary",
]
REJECTED_SURFACE_FIELDNAMES = [
    "rejected_same_surface_id",
    "rejected_route",
    "rejection_family",
    "source_identity_relation",
    "rejection_reason",
    "required_follow_up",
    "actor_visible",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
SUPPORTING_GUARD_FIELDNAMES = [
    "supporting_guard_axis_id",
    "guard_source",
    "guard_family",
    "guard_role",
    "row_count",
    "unique_task_source_id_count",
    "execution_allowed_by_m3004",
    "ordinary_engineering_candidate_axis",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
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
    "allowed_in_m3004",
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
    "source_inventory_rows",
    "exhausted_m1690_l3_surface_rows",
    "prior_surface_identity_rows",
    "source_axis_candidate_rows",
    "rejected_same_surface_rows",
    "supporting_guard_axis_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_inventory_rows": output_dir / "source_inventory_rows.csv",
        "exhausted_m1690_l3_surface_rows": output_dir / "exhausted_m1690_l3_surface_rows.csv",
        "prior_surface_identity_rows": output_dir / "prior_surface_identity_rows.csv",
        "source_axis_candidate_rows": output_dir / "source_axis_candidate_rows.csv",
        "rejected_same_surface_rows": output_dir / "rejected_same_surface_rows.csv",
        "supporting_guard_axis_rows": output_dir / "supporting_guard_axis_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def run_source_axis_expansion_materialization_preflight(
    *,
    m3003_design: Path | str = DEFAULT_M3003_DESIGN,
    m1690_workload: Path | str = DEFAULT_M1690_WORKLOAD,
    m2916_dir: Path | str = DEFAULT_M2916_DIR,
    m2919_dir: Path | str = DEFAULT_M2919_DIR,
    m2922_dir: Path | str = DEFAULT_M2922_DIR,
    m2925_dir: Path | str = DEFAULT_M2925_DIR,
    m2934_dir: Path | str = DEFAULT_M2934_DIR,
    m3000_dir: Path | str = DEFAULT_M3000_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3003_design=Path(m3003_design),
        m1690_workload=Path(m1690_workload),
        m2916_dir=Path(m2916_dir),
        m2919_dir=Path(m2919_dir),
        m2922_dir=Path(m2922_dir),
        m2925_dir=Path(m2925_dir),
        m2934_dir=Path(m2934_dir),
        m3000_dir=Path(m3000_dir),
    )

    m1690_l3_rows = source["m1690_l3_rows"]
    prior_identity_rows = build_prior_surface_identity_rows(source)
    l3_task_source_ids = {str(row["task_source_id"]) for row in m1690_l3_rows}
    prior_task_source_ids = {
        str(row["task_source_id"])
        for row in prior_identity_rows
        if _bool(row["included_in_m1690_l3"])
    }
    source_inventory_rows = build_source_inventory_rows(source, l3_task_source_ids=l3_task_source_ids)
    exhausted_rows = build_exhausted_surface_rows(m1690_l3_rows, prior_identity_rows)
    source_axis_rows = build_source_axis_candidate_rows()
    rejected_rows = build_rejected_same_surface_rows()
    supporting_rows = build_supporting_guard_axis_rows(source)

    write_csv_rows(paths["source_inventory_rows"], source_inventory_rows, fieldnames=SOURCE_INVENTORY_FIELDNAMES)
    write_csv_rows(
        paths["exhausted_m1690_l3_surface_rows"],
        exhausted_rows,
        fieldnames=EXHAUSTED_SURFACE_FIELDNAMES,
    )
    write_csv_rows(paths["prior_surface_identity_rows"], prior_identity_rows, fieldnames=PRIOR_IDENTITY_FIELDNAMES)
    write_csv_rows(paths["source_axis_candidate_rows"], source_axis_rows, fieldnames=SOURCE_AXIS_FIELDNAMES)
    write_csv_rows(paths["rejected_same_surface_rows"], rejected_rows, fieldnames=REJECTED_SURFACE_FIELDNAMES)
    write_csv_rows(paths["supporting_guard_axis_rows"], supporting_rows, fieldnames=SUPPORTING_GUARD_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "m1690_l3_row_count": len(m1690_l3_rows),
            "m1690_l3_unique_task_source_count": len(l3_task_source_ids),
            "prior_surface_unique_task_source_count": len(prior_task_source_ids),
            "unused_m1690_l3_task_source_count": len(l3_task_source_ids - prior_task_source_ids),
            "execution_performed": False,
            "training_performed": False,
            "validation_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)

    actor_rows = build_actor_contract_guard_rows()
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_without_summary_doc)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_inventory_rows=source_inventory_rows,
        exhausted_rows=exhausted_rows,
        prior_identity_rows=prior_identity_rows,
        source_axis_rows=source_axis_rows,
        rejected_rows=rejected_rows,
        supporting_rows=supporting_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
        follow_up_manifest_exists=Path(follow_up_manifest).exists(),
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_inventory_rows=source_inventory_rows,
        exhausted_rows=exhausted_rows,
        prior_identity_rows=prior_identity_rows,
        source_axis_rows=source_axis_rows,
        rejected_rows=rejected_rows,
        supporting_rows=supporting_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_inventory_rows=source_inventory_rows,
        exhausted_rows=exhausted_rows,
        prior_identity_rows=prior_identity_rows,
        source_axis_rows=source_axis_rows,
        rejected_rows=rejected_rows,
        supporting_rows=supporting_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=Path(follow_up_manifest).exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_inventory_rows=source_inventory_rows,
        exhausted_rows=exhausted_rows,
        prior_identity_rows=prior_identity_rows,
        source_axis_rows=source_axis_rows,
        rejected_rows=rejected_rows,
        supporting_rows=supporting_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "m1690_l3_row_count": len(m1690_l3_rows),
            "m1690_l3_unique_task_source_count": len(l3_task_source_ids),
            "prior_surface_unique_task_source_count": len(prior_task_source_ids),
            "unused_m1690_l3_task_source_count": len(l3_task_source_ids - prior_task_source_ids),
            "source_axis_candidate_row_count": len(source_axis_rows),
            "rejected_same_surface_row_count": len(rejected_rows),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "execution_performed": False,
            "training_performed": False,
            "validation_performed": False,
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def load_source_artifacts(
    *,
    m3003_design: Path,
    m1690_workload: Path,
    m2916_dir: Path,
    m2919_dir: Path,
    m2922_dir: Path,
    m2925_dir: Path,
    m2934_dir: Path,
    m3000_dir: Path,
) -> dict[str, Any]:
    m1690_rows = read_csv_rows(m1690_workload)
    m1690_l3_rows = [
        row for row in m1690_rows if str(row.get("profile_name", "")).strip() == "L3_online_gru"
    ]
    artifact_specs: list[dict[str, Any]] = []
    for milestone, path, role in PRIOR_SURFACE_SPECS:
        artifact_specs.append(
            {
                "source_milestone": milestone,
                "path": path,
                "artifact_kind": "prior_surface_identity",
                "source_role": role,
                "rows": read_csv_rows(path),
            }
        )
    dynamic_specs = [
        (
            "m2916_candidate",
            m2916_dir / "execution_admission_candidate_rows.csv",
            "prior_dependency_facing_execution_admission_candidates",
        ),
        (
            "m2916_source",
            m2916_dir / "execution_admission_source_rows.csv",
            "prior_dependency_facing_execution_admission_sources",
        ),
        (
            "m2919",
            m2919_dir / "bounded_execution_rows.csv",
            "prior_dependency_facing_bounded_execution_rows",
        ),
        (
            "m2922_source_outcome",
            m2922_dir / "source_milestone_outcome_rows.csv",
            "supporting_failure_localization_source_aggregates",
        ),
        (
            "m2922_next_route",
            m2922_dir / "next_route_candidate_rows.csv",
            "supporting_failure_localization_next_route_candidates",
        ),
        (
            "m2925_offtrack",
            m2925_dir / "offtrack_slice_rows.csv",
            "supporting_offtrack_failure_slice_rows",
        ),
        (
            "m2925_context",
            m2925_dir / "non_offtrack_context_rows.csv",
            "supporting_non_offtrack_context_rows",
        ),
        (
            "m2934_shift",
            m2934_dir / "outcome_shift_rows.csv",
            "supporting_outcome_shift_rows",
        ),
        (
            "m3000_parent",
            m3000_dir / "parent_comparison_report_rows.csv",
            "same_identity_residual_head_parent_comparison_rows",
        ),
        (
            "m3000_candidate",
            m3000_dir / "candidate_validation_execution_rows.csv",
            "same_identity_residual_head_candidate_execution_rows",
        ),
        (
            "m3000_success_retention",
            m3000_dir / "success_behavior_retention_execution_rows.csv",
            "same_identity_residual_head_success_retention_rows",
        ),
        (
            "m3000_stale_exclusion",
            m3000_dir / "stale_exclusion_guard_rows.csv",
            "supporting_stale_exclusion_guard_rows",
        ),
    ]
    for milestone, path, role in dynamic_specs:
        artifact_specs.append(
            {
                "source_milestone": milestone,
                "path": path,
                "artifact_kind": "route_context",
                "source_role": role,
                "rows": read_csv_rows(path),
            }
        )
    summary_paths = {
        "m2922_summary": m2922_dir / "summary.json",
        "m2925_summary": m2925_dir / "summary.json",
        "m2934_summary": m2934_dir / "summary.json",
        "m3000_summary": m3000_dir / "summary.json",
    }
    summaries = {key: read_json(path) if path.exists() else {} for key, path in summary_paths.items()}
    return {
        "m3003_design": m3003_design,
        "m3003_design_exists": m3003_design.exists(),
        "m1690_workload": m1690_workload,
        "m1690_rows": m1690_rows,
        "m1690_l3_rows": m1690_l3_rows,
        "artifact_specs": artifact_specs,
        "summary_paths": summary_paths,
        "summaries": summaries,
    }


def build_source_inventory_rows(
    source: Mapping[str, Any],
    *,
    l3_task_source_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "source_inventory_id": "m3004-source-inventory-0001",
            "source_milestone": "m3003_design",
            "artifact_path": str(source["m3003_design"]),
            "artifact_exists": source["m3003_design_exists"],
            "artifact_kind": "design",
            "source_role": "post_residual_stop_source_axis_expansion_design",
            "observed_row_count": 1 if source["m3003_design_exists"] else 0,
            "unique_task_source_id_count": 0,
            "m1690_l3_overlap_count": 0,
            "execution_performed_by_m3004": False,
            "used_for_fresh_denominator_selection": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "source_inventory_id": "m3004-source-inventory-0002",
            "source_milestone": "m1690_l3",
            "artifact_path": str(source["m1690_workload"]),
            "artifact_exists": source["m1690_workload"].exists(),
            "artifact_kind": "workload",
            "source_role": "exhausted_fixed_l3_online_gru_workload_space",
            "observed_row_count": len(source["m1690_l3_rows"]),
            "unique_task_source_id_count": len(l3_task_source_ids),
            "m1690_l3_overlap_count": len(l3_task_source_ids),
            "execution_performed_by_m3004": False,
            "used_for_fresh_denominator_selection": False,
            "claim_scope": CLAIM_SCOPE,
        },
    ]
    next_index = 3
    for spec in source["artifact_specs"]:
        ids = task_source_ids_from_rows(spec["rows"])
        rows.append(
            {
                "source_inventory_id": f"m3004-source-inventory-{next_index:04d}",
                "source_milestone": spec["source_milestone"],
                "artifact_path": str(spec["path"]),
                "artifact_exists": spec["path"].exists(),
                "artifact_kind": spec["artifact_kind"],
                "source_role": spec["source_role"],
                "observed_row_count": len(spec["rows"]),
                "unique_task_source_id_count": len(ids),
                "m1690_l3_overlap_count": len(ids & l3_task_source_ids),
                "execution_performed_by_m3004": False,
                "used_for_fresh_denominator_selection": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
        next_index += 1
    for name, path in source["summary_paths"].items():
        rows.append(
            {
                "source_inventory_id": f"m3004-source-inventory-{next_index:04d}",
                "source_milestone": name,
                "artifact_path": str(path),
                "artifact_exists": path.exists(),
                "artifact_kind": "summary",
                "source_role": "supporting_context_summary",
                "observed_row_count": 1 if path.exists() else 0,
                "unique_task_source_id_count": 0,
                "m1690_l3_overlap_count": 0,
                "execution_performed_by_m3004": False,
                "used_for_fresh_denominator_selection": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
        next_index += 1
    return rows


def build_prior_surface_identity_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    l3_ids = {str(row["task_source_id"]) for row in source["m1690_l3_rows"]}
    rows: list[dict[str, Any]] = []
    for spec in source["artifact_specs"]:
        for index, row in enumerate(spec["rows"], start=1):
            ids = sorted(extract_task_source_ids(row))
            for task_source_id in ids:
                rows.append(
                    {
                        "prior_surface_identity_id": f"m3004-prior-identity-{len(rows) + 1:04d}",
                        "source_milestone": spec["source_milestone"],
                        "source_artifact": str(spec["path"]),
                        "source_family": row.get("source_family") or spec["source_role"],
                        "source_row_id": row_identifier(row, fallback_index=index),
                        "task_source_id": task_source_id,
                        "workload_id": row.get("workload_id", ""),
                        "profile_name": row.get("profile_name", ""),
                        "task_family": row.get("task_family", ""),
                        "source_edge": row.get("source_edge", ""),
                        "window_tag": row.get("window_tag", ""),
                        "included_in_m1690_l3": task_source_id in l3_ids,
                        "same_surface_reuse_allowed": False,
                        "actor_visible": False,
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
    return rows


def build_exhausted_surface_rows(
    m1690_l3_rows: list[dict[str, str]],
    prior_identity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage: dict[str, set[str]] = defaultdict(set)
    for row in prior_identity_rows:
        if _bool(row["included_in_m1690_l3"]):
            coverage[str(row["task_source_id"])].add(str(row["source_milestone"]))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(m1690_l3_rows, key=lambda item: str(item.get("task_source_id", ""))), start=1):
        task_source_id = str(row.get("task_source_id", ""))
        covered_by = sorted(coverage.get(task_source_id, set()))
        rows.append(
            {
                "m3004_exhausted_row_id": f"m3004-exhausted-l3-{index:04d}",
                "task_source_id": task_source_id,
                "workload_id": row.get("workload_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "config_exists": _bool(row.get("config_exists")),
                "checkpoint_exists": _bool(row.get("checkpoint_exists")),
                "covered_by_prior_surface": bool(covered_by),
                "coverage_source_milestones": ";".join(covered_by),
                "coverage_surface_count": len(covered_by),
                "unused_for_m1690_l3_row_selection": not covered_by,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_source_axis_candidate_rows() -> list[dict[str, Any]]:
    candidates = [
        (
            "source_generator_new_task_source_identity",
            "route_a_source_generator_axis",
            "generate_or_inventory_route_a_sources_with_task_source_ids_outside_m1680_spec_0000_0071",
            "candidate_axis_admissible_after_m3005_audit",
            "future rows must use task_source identities outside the exhausted m1680-spec-0000..0071 set",
            True,
            False,
        ),
        (
            "scenario_distribution_variant_source_axis",
            "route_a_distribution_axis",
            "materialize source-level scenario variants with new source identity rather than eval-seed replay",
            "candidate_axis_admissible_after_m3005_audit",
            "variant identity must be new source identity, not only a new eval_seed on an old row",
            True,
            False,
        ),
        (
            "ood_dynamics_source_axis",
            "route_a_generalization_axis",
            "materialize unseen dynamics-range source rows while keeping hidden dynamics actor-invisible",
            "candidate_axis_admissible_after_m3005_audit",
            "new task_source identity required; hidden dynamics may be evaluator metadata only",
            True,
            False,
        ),
        (
            "sensor_noise_delay_source_axis",
            "route_a_deployability_axis",
            "materialize sensor-noise and actuator-delay source rows with new task_source identity",
            "candidate_axis_admissible_after_m3005_audit",
            "new source identity required; no TTC or oracle feasibility labels may enter actor input",
            True,
            False,
        ),
        (
            "route_c_selected_platform_source_axis",
            "route_c_dependency_axis",
            "selected-platform high-fidelity source acquisition axis",
            "candidate_axis_blocked_until_source_or_approved_dependency_route_available",
            "requires source/dependency availability before any execution or validation work",
            True,
            False,
        ),
        (
            "route_b_controller_family_source_refresh_axis",
            "route_b_paper_context_axis",
            "controller-family fair-comparison source refresh context",
            "candidate_axis_context_only_not_route_a_execution",
            "may inform paper-route source acquisition but cannot become Route A performance evidence here",
            True,
            False,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (
        axis_name,
        axis_family,
        status_name,
        axis_status,
        requirement,
        future_materialization_required,
        high_fidelity_allowed,
    ) in enumerate(candidates, start=1):
        rows.append(
            {
                "source_axis_candidate_id": f"m3004-source-axis-candidate-{index:04d}",
                "axis_family": axis_family,
                "axis_name": axis_name,
                "axis_status": axis_status,
                "source_identity_requirement": requirement,
                "future_materialization_required": future_materialization_required,
                "future_execution_manifest_required": True,
                "uses_exhausted_m1690_l3_rows_as_evidence_surface": False,
                "eval_seed_only": False,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "source_labels_actor_visible": False,
                "ordinary_engineering_candidate_axis": axis_status.startswith("candidate_axis_admissible"),
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": high_fidelity_allowed,
                "self_id_claim_allowed": False,
                "execution_scheduled_by_m3004": False,
                "ranking_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_rejected_same_surface_rows() -> list[dict[str, Any]]:
    rejected = [
        (
            "reuse_m1690_l3_task_source_rows",
            "exhausted_fixed_source_identity",
            "same m1680-spec-0000..0071 identity set",
            "all 72 M1690 L3 task_source ids are already covered by prior audited surfaces",
            "source-axis expansion with new source identity or explicit stop",
        ),
        (
            "reuse_m2919_dependency_facing_rows",
            "same_task_source_identity",
            "same task_source identity as M3000 at audited granularity",
            "M2919 rows are diagnostic parent surface, not a fresh denominator",
            "M3005 audit before any new source materialization",
        ),
        (
            "reuse_m2996_m3000_residual_head_denominator",
            "behavior_neutral_residual_head_same_surface",
            "same M2919 task_source identity plus residual-head wrapper",
            "M3000 was behavior-neutral and cannot become the next optimization target",
            "source-axis expansion outside the fixed denominator",
        ),
        (
            "eval_seed_only_rerun",
            "seed_only_relabeling",
            "same task_source identity with a new eval_seed",
            "new eval seeds may support repeatability but do not create source-diverse freshness",
            "new task_source identity or explicit stop",
        ),
        (
            "label_only_or_doc_only_reclassification",
            "label_only_reuse",
            "same rows with new tags",
            "diagnostic labels cannot create a fresh evidence surface and must not be actor-visible",
            "machine-checkable source-axis materialization",
        ),
        (
            "wrapper_only_residual_head_variant",
            "wrapper_only_reuse",
            "same rows with another residual wrapper",
            "M3002 stops actor-head-delta residual-head local repair after behavior-neutral result",
            "new source-axis materialization or synthesis",
        ),
        (
            "stale_fixed_source_guardrails_as_candidates",
            "protected_guardrail_reuse",
            "prior stale/protected rows counted as ordinary candidates",
            "stale and protected rows remain guardrails outside validation paper and self-ID denominators",
            "keep as supporting guards only",
        ),
        (
            "route_or_outcome_labels_actor_visible",
            "actor_contract_violation",
            "source route outcome success or verdict labels exposed to actor",
            "actor input contract forbids hidden/oracle/evaluator labels",
            "preserve actor 72/action 3 and evaluator-only labels",
        ),
    ]
    return [
        {
            "rejected_same_surface_id": f"m3004-rejected-same-surface-{index:04d}",
            "rejected_route": route,
            "rejection_family": family,
            "source_identity_relation": relation,
            "rejection_reason": reason,
            "required_follow_up": follow_up,
            "actor_visible": False,
            "ordinary_engineering_denominator_allowed": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "self_id_claim_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (route, family, relation, reason, follow_up) in enumerate(rejected, start=1)
    ]


def build_supporting_guard_axis_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = {spec["source_milestone"]: spec for spec in source["artifact_specs"]}
    rows = [
        guard_row(
            1,
            "m2919",
            "dependency_facing_diagnostic_context",
            "M2919 rows remain prior diagnostic context and same-identity guard for M3000",
            specs.get("m2919", {}).get("rows", []),
        ),
        guard_row(
            2,
            "m3000_parent",
            "behavior_neutral_residual_head_context",
            "M3000 parent comparison is report-only and not a fresh denominator",
            specs.get("m3000_parent", {}).get("rows", []),
        ),
        guard_row(
            3,
            "m2925_offtrack",
            "offtrack_dominant_failure_slice_context",
            "M2925 offtrack rows preserve failure-slice context only",
            specs.get("m2925_offtrack", {}).get("rows", []),
        ),
        guard_row(
            4,
            "m2934_shift",
            "outcome_shift_tradeoff_context",
            "M2934 outcome shifts preserve tradeoff accounting only",
            specs.get("m2934_shift", {}).get("rows", []),
        ),
        guard_row(
            5,
            "m3000_stale_exclusion",
            "stale_fixed_source_exclusion",
            "stale fixed-source rows remain excluded from validation paper and self-ID denominators",
            specs.get("m3000_stale_exclusion", {}).get("rows", []),
        ),
        {
            "supporting_guard_axis_id": "m3004-supporting-guard-0006",
            "guard_source": "route_c_hf3_source_dependency",
            "guard_family": "route_c_dependency_blocker",
            "guard_role": "Route C remains blocked until source or approved dependency route is supplied",
            "row_count": 1,
            "unique_task_source_id_count": 0,
            "execution_allowed_by_m3004": False,
            "ordinary_engineering_candidate_axis": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]
    return rows


def guard_row(
    index: int,
    guard_source: str,
    guard_family: str,
    guard_role: str,
    source_rows: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "supporting_guard_axis_id": f"m3004-supporting-guard-{index:04d}",
        "guard_source": guard_source,
        "guard_family": guard_family,
        "guard_role": guard_role,
        "row_count": len(source_rows),
        "unique_task_source_id_count": len(task_source_ids_from_rows(source_rows)),
        "execution_allowed_by_m3004": False,
        "ordinary_engineering_candidate_axis": False,
        "validation_denominator_allowed": False,
        "paper_denominator_allowed": False,
        "high_fidelity_readiness_allowed": False,
        "self_id_claim_allowed": False,
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    guards = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, 72),
        ("actor_action_dim", ACTION_DIM, 3),
        ("actor_input_contract_changed", False, False),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("source_labels_actor_visible", False, False),
        ("route_labels_actor_visible", False, False),
        ("outcome_success_progress_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
        ("profile_specific_tuning_scheduled", False, False),
        ("source_build_or_dependency_probe_scheduled", False, False),
        ("materialization_only_no_execution", True, True),
    ]
    return [
        {
            "guard_id": f"m3004-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(guards, start=1)
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool) -> list[dict[str, Any]]:
    claims = [
        ("source_axis_materialization", True, True, "M3005 result audit before interpretation"),
        ("exhausted_m1690_l3_accounting", True, True, "M3005 result audit before next route"),
        ("same_surface_rejection_accounting", True, True, "M3005 result audit before next route"),
        ("execution_result", False, False, "separate execution manifest and audit"),
        ("repair_success", False, False, "closed-loop same-case and fresh-surface execution evidence"),
        ("validation_result", False, False, "separate validation manifest and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("current_sim_verdict", False, False, "distribution-level validation and synthesis"),
        ("paper_evidence", False, False, "Route B fair controller-family proof gates"),
        ("finite_window_vs_gru_result", False, False, "separately pre-registered comparison"),
        ("high_fidelity_validation", False, False, "Route C source/dependency and validation manifest"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "history-necessity/self-ID proof gates"),
        ("checkpoint_ranking_or_promotion", False, False, "promotion gates after proof and generalization"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (claim, allowed, made, evidence) in enumerate(claims, start=1):
        rows.append(
            {
                "claim_id": f"m3004-claim-{index:04d}",
                "claim_family": claim,
                "allowed_in_m3004": allowed,
                "claim_made": made,
                "status_pass": required_artifacts_present and (made is allowed),
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    source_inventory_rows: list[dict[str, Any]],
    exhausted_rows: list[dict[str, Any]],
    prior_identity_rows: list[dict[str, Any]],
    source_axis_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    supporting_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    l3_ids = {str(row["task_source_id"]) for row in source["m1690_l3_rows"]}
    prior_ids = {
        str(row["task_source_id"])
        for row in prior_identity_rows
        if _bool(row["included_in_m1690_l3"])
    }
    m2919_ids = ids_for_source(source, "m2919")
    m3000_parent_ids = ids_for_source(source, "m3000_parent")
    m3000_candidate_ids = ids_for_source(source, "m3000_candidate")
    unused_ids = l3_ids - prior_ids
    admissible_axes = [
        row
        for row in source_axis_rows
        if str(row["axis_status"]).startswith("candidate_axis_admissible")
    ]
    rejected_routes = {str(row["rejected_route"]) for row in rejected_rows}
    gates = [
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
        ("m3003_design_present", source["m3003_design_exists"], source["m3003_design_exists"], True, "lineage_invalid"),
        ("m1690_l3_row_count", len(source["m1690_l3_rows"]) == 72, len(source["m1690_l3_rows"]), 72, "lineage_invalid"),
        ("m1690_l3_unique_task_source_count", len(l3_ids) == 72, len(l3_ids), 72, "lineage_invalid"),
        ("prior_surface_l3_coverage_count", len(prior_ids) == 72, len(prior_ids), 72, "lineage_invalid"),
        ("unused_m1690_l3_task_source_count", len(unused_ids) == 0, len(unused_ids), 0, "lineage_invalid"),
        (
            "exhausted_surface_rows_present",
            len(exhausted_rows) == 72 and all(not _bool(row["unused_for_m1690_l3_row_selection"]) for row in exhausted_rows),
            len(exhausted_rows),
            72,
            "lineage_invalid",
        ),
        ("source_inventory_rows_present", bool(source_inventory_rows), len(source_inventory_rows), ">=1", "lineage_invalid"),
        ("prior_identity_rows_present", bool(prior_identity_rows), len(prior_identity_rows), ">=1", "lineage_invalid"),
        ("source_axis_candidate_rows_present", bool(source_axis_rows), len(source_axis_rows), ">=1", "scenario_sampling_failure"),
        (
            "admissible_source_axis_candidate_count",
            len(admissible_axes) >= 1,
            len(admissible_axes),
            ">=1",
            "scenario_sampling_failure",
        ),
        (
            "same_surface_reuse_rejected",
            {"reuse_m1690_l3_task_source_rows", "reuse_m2919_dependency_facing_rows", "reuse_m2996_m3000_residual_head_denominator", "eval_seed_only_rerun"} <= rejected_routes,
            sorted(rejected_routes),
            "required same-surface rejections present",
            "objective_overfit",
        ),
        (
            "m3000_m2919_same_task_source_identity",
            bool(m2919_ids) and m2919_ids == m3000_parent_ids == m3000_candidate_ids,
            f"m2919={len(m2919_ids)} m3000_parent={len(m3000_parent_ids)} m3000_candidate={len(m3000_candidate_ids)}",
            "same non-empty task_source identity set",
            "objective_overfit",
        ),
        ("supporting_guard_rows_present", bool(supporting_rows), len(supporting_rows), ">=1", "lineage_invalid"),
        ("actor_contract_rows_pass", all(_bool(row["status_pass"]) for row in actor_rows), "all actor rows pass", True, "contract_violation"),
        ("claim_boundary_rows_pass", all(_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass", True, "proof_washout"),
        ("follow_up_manifest_written", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
        ("environment_execution_performed", True, False, False, "contract_violation"),
        ("training_performed", True, False, False, "contract_violation"),
        ("validation_claim_made", True, False, False, "proof_washout"),
        ("performance_claim_made", True, False, False, "proof_washout"),
        ("paper_claim_made", True, False, False, "proof_washout"),
        ("high_fidelity_claim_made", True, False, False, "proof_washout"),
        ("self_id_claim_made", True, False, False, "proof_washout"),
    ]
    return [
        {
            "gate_id": f"m3004-gate-{index:04d}",
            "gate_family": name,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, passed, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    source_inventory_rows: list[dict[str, Any]],
    exhausted_rows: list[dict[str, Any]],
    prior_identity_rows: list[dict[str, Any]],
    source_axis_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    supporting_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    l3_ids = {str(row["task_source_id"]) for row in source["m1690_l3_rows"]}
    prior_ids = {
        str(row["task_source_id"])
        for row in prior_identity_rows
        if _bool(row["included_in_m1690_l3"])
    }
    m2919_ids = ids_for_source(source, "m2919")
    m3000_parent_ids = ids_for_source(source, "m3000_parent")
    m3000_candidate_ids = ids_for_source(source, "m3000_candidate")
    source_milestone_counts = Counter(str(row["source_milestone"]) for row in prior_identity_rows)
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    status_pass = gate_matrix_pass and actor_rows_pass and claim_rows_pass and required_artifacts_present
    admissible_axis_count = sum(
        1 for row in source_axis_rows if str(row["axis_status"]).startswith("candidate_axis_admissible")
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": DECISION_PASS if status_pass else DECISION_FAIL,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "m3003_design_present": source["m3003_design_exists"],
        "m1690_workload_present": source["m1690_workload"].exists(),
        "m1690_l3_row_count": len(source["m1690_l3_rows"]),
        "m1690_l3_unique_task_source_count": len(l3_ids),
        "prior_surface_l3_unique_task_source_count": len(prior_ids),
        "unused_m1690_l3_task_source_count": len(l3_ids - prior_ids),
        "surface_ids_not_in_l3_count": len(prior_ids - l3_ids),
        "exhausted_m1690_l3_confirmed": len(source["m1690_l3_rows"]) == 72 and len(l3_ids - prior_ids) == 0,
        "m3000_m2919_same_identity_confirmed": bool(m2919_ids)
        and m2919_ids == m3000_parent_ids == m3000_candidate_ids,
        "m2919_unique_task_source_count": len(m2919_ids),
        "m3000_parent_unique_task_source_count": len(m3000_parent_ids),
        "m3000_candidate_unique_task_source_count": len(m3000_candidate_ids),
        "source_inventory_row_count": len(source_inventory_rows),
        "exhausted_surface_row_count": len(exhausted_rows),
        "prior_surface_identity_row_count": len(prior_identity_rows),
        "source_axis_candidate_row_count": len(source_axis_rows),
        "admissible_source_axis_candidate_count": admissible_axis_count,
        "rejected_same_surface_row_count": len(rejected_rows),
        "supporting_guard_axis_row_count": len(supporting_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "prior_surface_identity_counts": dict(source_milestone_counts),
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "dependency_probe_run": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "private_holdout_used": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3004 Engineering Controller Route A Post-Residual-Stop Source-Axis Expansion Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- M1690 L3 rows: {summary['m1690_l3_row_count']}",
            f"- M1690 L3 unique task_source ids: {summary['m1690_l3_unique_task_source_count']}",
            f"- prior surface L3 unique task_source ids: {summary['prior_surface_l3_unique_task_source_count']}",
            f"- unused M1690 L3 task_source ids: {summary['unused_m1690_l3_task_source_count']}",
            f"- source inventory rows: {summary['source_inventory_row_count']}",
            f"- exhausted surface rows: {summary['exhausted_surface_row_count']}",
            f"- prior surface identity rows: {summary['prior_surface_identity_row_count']}",
            f"- source-axis candidate rows: {summary['source_axis_candidate_row_count']}",
            f"- admissible source-axis candidates after audit: {summary['admissible_source_axis_candidate_count']}",
            f"- rejected same-surface rows: {summary['rejected_same_surface_row_count']}",
            f"- supporting guard rows: {summary['supporting_guard_axis_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3004 materializes source-axis inventory and guard artifacts only. It does not execute environments, train, validate, rank, promote, mutate checkpoints, or claim repair success or performance.",
            "",
            "Rejected interpretations:",
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
        "hypothesis": "A bounded result audit can accept or reject the M3004 source-axis expansion materialization before any execution validation ranking promotion repair-success performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "source_inventory_rows.csv"),
                str(output_dir / "exhausted_m1690_l3_surface_rows.csv"),
                str(output_dir / "prior_surface_identity_rows.csv"),
                str(output_dir / "source_axis_candidate_rows.csv"),
                str(output_dir / "rejected_same_surface_rows.csv"),
                str(output_dir / "supporting_guard_axis_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m3004-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-preflight.json",
                "experiments/manifests/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design.json",
            ],
            "parent_objective": [
                "audit M3004 source-axis expansion materialization before selecting implementation, stop, or synthesis"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design",
            ],
            "blocked_by": [
                "M3004 materialization requires audit before any source-generation implementation or execution",
                "M1690 L3 row selection remains exhausted and cannot be treated as a fresh denominator",
                "same-surface residual-head and eval-seed-only routes remain rejected",
            ],
            "supersedes": [
                "direct execution from M3004 source-axis inventory without result audit",
                "direct performance interpretation of M3004 candidate-axis rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3005 must audit M3004 summary source inventory exhausted-surface same-surface rejection actor and claim boundaries",
            "M3005 must preserve the 72/72 exhausted M1690 L3 task_source-id accounting",
            "M3005 must not convert candidate-axis rows into execution validation performance paper high-fidelity or self-ID evidence",
            "M3005 must select exactly one next route or explicit stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote select a winner or execute dependency work",
            "do not implement source generation or execution inside the audit",
            "do not change actor input or action contract",
            "do not convert M3004 source inventory rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "source_axis_expansion_materialization_result_audit",
            "evidence_increment": "audits M3004 source-axis expansion inventory and same-surface rejection artifacts",
            "claim_scope": "Result audit only; no execution validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3004 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if M3004 leaves no admissible source-axis candidate or explicit stop route",
                "stop if candidate-axis rows would be used as execution instructions before a separate manifest",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if materialization is complete but no source-axis route is viable",
                "route to bounded source-generation implementation design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3004 completes source-axis expansion materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3004 post-residual-stop source-axis expansion materialization artifacts",
            "admission_evidence": [
                "M3004 summary and gate matrix",
                "M3004 source inventory exhausted-surface same-surface rejection candidate-axis actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3005 status queue scoreboard research log and review",
                "one follow-up manifest only if M3005 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3005 audit accepts or rejects M3004 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3005 audits Route A source-axis materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3005; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3004 Route A post-residual-stop source-axis materialization only.",
            "negative_result_policy": "Preserve exhausted-source and same-surface rejection findings and route to synthesis or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3004 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized source-axis inventory and same-surface rejection panel",
            "paper_verdict_delta": "no paper verdict; audit may authorize a later source-generation route only",
            "must_synthesize_if": [
                "M3005 cannot accept M3004 as complete and claim-safe",
                "M3005 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M3005 cannot select an implementation, synthesis, or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3005 audits M3004 artifacts row counts gates actor and claim boundaries",
            "M3005 selects exactly one next route or stop state",
            "no execution training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3005 hides M3004 failures or missing artifacts",
            "M3005 treats M3004 source-axis candidates as execution readiness performance verdict or repair success",
            "M3005 changes actor input or action contract",
            "M3005 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3005 audits M3004 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "source_inventory_rows.csv"),
            str(output_dir / "exhausted_m1690_l3_surface_rows.csv"),
            str(output_dir / "prior_surface_identity_rows.csv"),
            str(output_dir / "source_axis_candidate_rows.csv"),
            str(output_dir / "rejected_same_surface_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def extract_task_source_ids(row: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key, value in row.items():
        value_text = str(value or "")
        key_text = str(key or "").lower()
        if key_text == "task_source_id" or key_text.endswith("_task_source_id"):
            ids.update(TASK_SOURCE_PATTERN.findall(value_text))
            if value_text.startswith("m1680-spec-"):
                ids.add(value_text)
        ids.update(TASK_SOURCE_PATTERN.findall(value_text))
    return ids


def task_source_ids_from_rows(rows: list[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        ids.update(extract_task_source_ids(row))
    return ids


def ids_for_source(source: Mapping[str, Any], source_milestone: str) -> set[str]:
    for spec in source["artifact_specs"]:
        if spec["source_milestone"] == source_milestone:
            return task_source_ids_from_rows(spec["rows"])
    return set()


def row_identifier(row: Mapping[str, Any], *, fallback_index: int) -> str:
    for key in (
        "execution_candidate_id",
        "execution_admission_candidate_id",
        "source_row_id",
        "offtrack_slice_id",
        "outcome_shift_id",
        "m3000_execution_id",
        "parent_comparison_report_id",
        "resolution_id",
        "workload_id",
    ):
        value = row.get(key)
        if value:
            return str(value)
    return f"source-row-{fallback_index:04d}"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3003-design", type=Path, default=DEFAULT_M3003_DESIGN)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_M1690_WORKLOAD)
    parser.add_argument("--m2916-dir", type=Path, default=DEFAULT_M2916_DIR)
    parser.add_argument("--m2919-dir", type=Path, default=DEFAULT_M2919_DIR)
    parser.add_argument("--m2922-dir", type=Path, default=DEFAULT_M2922_DIR)
    parser.add_argument("--m2925-dir", type=Path, default=DEFAULT_M2925_DIR)
    parser.add_argument("--m2934-dir", type=Path, default=DEFAULT_M2934_DIR)
    parser.add_argument("--m3000-dir", type=Path, default=DEFAULT_M3000_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_source_axis_expansion_materialization_preflight(
        m3003_design=args.m3003_design,
        m1690_workload=args.m1690_workload,
        m2916_dir=args.m2916_dir,
        m2919_dir=args.m2919_dir,
        m2922_dir=args.m2922_dir,
        m2925_dir=args.m2925_dir,
        m2934_dir=args.m2934_dir,
        m3000_dir=args.m3000_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
