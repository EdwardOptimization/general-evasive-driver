"""Materialize M3009 no-execution new-source workload contract rows.

M3009 converts the M3008 design and M3006 source specs into a bounded
machine-checkable workload-contract panel. It does not build sources,
instantiate environments, execute policies, validate, train, rank, or promote
checkpoints.
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
    "m3009-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "workload-materialization-preflight"
)
NEXT_ID = (
    "m3010-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "workload-materialization-result-audit"
)
M3007_ID = (
    "m3007-engineering-controller-route-a-post-residual-stop-new-task-source-generation-"
    "contract-materialization-result-audit"
)
M3008_ID = (
    "m3008-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "workload-materialization-design"
)
DEFAULT_M3007_AUDIT = Path(f"docs/{M3007_ID}.md")
DEFAULT_M3008_DESIGN = Path(f"docs/{M3008_ID}.md")
DEFAULT_M3006_DIR = Path(
    "runs/m3006_engineering_controller_route_a_post_residual_stop_new_task_source_"
    "generation_contract_materialization_preflight"
)
DEFAULT_M1674_CONFIG = Path(
    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/"
    "seed_167400/config.json"
)
DEFAULT_M1674_CHECKPOINT = Path(
    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/"
    "seed_167400/checkpoint.pt"
)
DEFAULT_M2655_CONFIG = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/repair_config_snapshot.json"
)
DEFAULT_M2655_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_"
    "actor_head_repair.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_workload_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

SOURCE_SPEC_COUNT = 16
PROFILE_BINDING_COUNT = 2
WORKLOAD_CONTRACT_COUNT = SOURCE_SPEC_COUNT * PROFILE_BINDING_COUNT

CLAIM_SCOPE = (
    "M3009 Route A post-residual-stop new-source executable workload contract "
    "materialization only; source-resolution, read-only profile-binding, "
    "workload-contract, rejection, actor-contract, claim-boundary, and gate rows "
    "may be written. No source build, environment reset, step, rollout, replay, "
    "validation, training, PPO, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, repair-success, driver-performance, paper, current-sim "
    "verdict, high-fidelity validation, finite-window-vs-GRU, full ideal driver, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "source build readiness, executable environment readiness, execution result, "
    "validation result, repair success, driver performance, current-sim verdict, "
    "paper evidence, high-fidelity validation, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, level3 self-identification, checkpoint ranking, "
    "or checkpoint promotion"
)
DECISION_PASS = "new_source_workload_contract_materialized_route_to_m3010_result_audit"
DECISION_FAIL = "new_source_workload_contract_materialization_incomplete"

PATH_KEYS = [
    "summary",
    "source_spec_resolution_rows",
    "profile_binding_rows",
    "executable_workload_contract_rows",
    "rejected_workload_shortcut_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

SOURCE_RESOLUTION_FIELDNAMES = [
    "source_resolution_id",
    "new_task_source_spec_id",
    "task_source_id",
    "axis_name",
    "axis_family",
    "axis_variant_tag",
    "task_family",
    "source_edge",
    "window_tag",
    "reference_m1680_task_source_id",
    "new_identity_outside_m1680_m1690",
    "overlaps_exhausted_m1690_l3",
    "source_spec_preserved",
    "source_build_scheduled_by_m3009",
    "execution_scheduled_by_m3009",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "status_pass",
    "claim_boundary",
]
PROFILE_BINDING_FIELDNAMES = [
    "profile_binding_id",
    "profile_binding_name",
    "binding_role",
    "config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "read_only_binding",
    "profile_specific_tuning",
    "checkpoint_mutation_scheduled",
    "actor_observation_dim",
    "actor_action_dim",
    "status_pass",
    "claim_boundary",
]
WORKLOAD_FIELDNAMES = [
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "task_source_id",
    "profile_binding_name",
    "binding_role",
    "axis_name",
    "axis_family",
    "task_family",
    "source_edge",
    "window_tag",
    "config_path",
    "checkpoint_path",
    "actor_observation_dim",
    "actor_action_dim",
    "new_source_identity_preserved",
    "read_only_profile_binding",
    "future_execution_manifest_required",
    "source_build_scheduled_by_m3009",
    "environment_reset_scheduled_by_m3009",
    "environment_step_scheduled_by_m3009",
    "policy_action_scheduled_by_m3009",
    "validation_scheduled_by_m3009",
    "training_scheduled_by_m3009",
    "ranking_scheduled_by_m3009",
    "checkpoint_mutation_scheduled",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "status_pass",
    "claim_boundary",
]
REJECTED_FIELDNAMES = [
    "rejected_workload_shortcut_id",
    "rejected_route",
    "rejection_family",
    "rejection_reason",
    "required_follow_up",
    "actor_visible",
    "workload_denominator_allowed",
    "execution_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_claim_allowed",
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
    "allowed_in_m3009",
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_spec_resolution_rows": output_dir / "source_spec_resolution_rows.csv",
        "profile_binding_rows": output_dir / "profile_binding_rows.csv",
        "executable_workload_contract_rows": output_dir / "executable_workload_contract_rows.csv",
        "rejected_workload_shortcut_rows": output_dir / "rejected_workload_shortcut_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def run_new_source_executable_workload_materialization_preflight(
    *,
    m3007_audit: Path | str = DEFAULT_M3007_AUDIT,
    m3008_design: Path | str = DEFAULT_M3008_DESIGN,
    m3006_dir: Path | str = DEFAULT_M3006_DIR,
    m1674_config: Path | str = DEFAULT_M1674_CONFIG,
    m1674_checkpoint: Path | str = DEFAULT_M1674_CHECKPOINT,
    m2655_config: Path | str = DEFAULT_M2655_CONFIG,
    m2655_checkpoint: Path | str = DEFAULT_M2655_CHECKPOINT,
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
        m3007_audit=Path(m3007_audit),
        m3008_design=Path(m3008_design),
        m3006_dir=Path(m3006_dir),
        m1674_config=Path(m1674_config),
        m1674_checkpoint=Path(m1674_checkpoint),
        m2655_config=Path(m2655_config),
        m2655_checkpoint=Path(m2655_checkpoint),
    )

    source_rows = build_source_spec_resolution_rows(source["m3006_source_spec_rows"])
    profile_rows = build_profile_binding_rows(source)
    workload_rows = build_workload_contract_rows(source_rows, profile_rows)
    rejected_rows = build_rejected_workload_shortcut_rows()
    actor_rows = build_actor_contract_guard_rows()

    write_csv_rows(paths["source_spec_resolution_rows"], source_rows, fieldnames=SOURCE_RESOLUTION_FIELDNAMES)
    write_csv_rows(paths["profile_binding_rows"], profile_rows, fieldnames=PROFILE_BINDING_FIELDNAMES)
    write_csv_rows(paths["executable_workload_contract_rows"], workload_rows, fieldnames=WORKLOAD_FIELDNAMES)
    write_csv_rows(paths["rejected_workload_shortcut_rows"], rejected_rows, fieldnames=REJECTED_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "source_spec_resolution_row_count": len(source_rows),
            "profile_binding_row_count": len(profile_rows),
            "workload_contract_row_count": len(workload_rows),
            "execution_performed": False,
            "validation_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(paths["follow_up_manifest"], follow_up)

    required_without_summary_doc = all(
        paths[key].exists() for key in PATH_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_without_summary_doc)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        rejected_rows=rejected_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "source_spec_resolution_row_count": len(source_rows),
            "source_spec_unique_task_source_count": len({row["task_source_id"] for row in source_rows}),
            "old_m1690_l3_overlap_count": old_overlap_count(source_rows),
            "profile_binding_row_count": len(profile_rows),
            "workload_contract_row_count": len(workload_rows),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "execution_performed": False,
            "validation_performed": False,
            "training_performed": False,
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def load_source_artifacts(
    *,
    m3007_audit: Path,
    m3008_design: Path,
    m3006_dir: Path,
    m1674_config: Path,
    m1674_checkpoint: Path,
    m2655_config: Path,
    m2655_checkpoint: Path,
) -> dict[str, Any]:
    m3006_summary_path = m3006_dir / "summary.json"
    return {
        "m3007_audit": m3007_audit,
        "m3007_audit_exists": m3007_audit.exists(),
        "m3008_design": m3008_design,
        "m3008_design_exists": m3008_design.exists(),
        "m3006_dir": m3006_dir,
        "m3006_summary": read_json(m3006_summary_path) if m3006_summary_path.exists() else {},
        "m3006_source_spec_rows": read_csv_rows(m3006_dir / "new_task_source_spec_rows.csv"),
        "m3006_source_contract_rows": read_csv_rows(m3006_dir / "source_contract_rows.csv"),
        "m3006_gate_rows": read_csv_rows(m3006_dir / "gate_matrix.csv"),
        "m1674_config": m1674_config,
        "m1674_checkpoint": m1674_checkpoint,
        "m2655_config": m2655_config,
        "m2655_checkpoint": m2655_checkpoint,
    }


def build_source_spec_resolution_rows(source_specs: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(sorted(source_specs, key=lambda row: row.get("task_source_id", "")), start=1):
        preserved = bool(spec.get("task_source_id")) and _bool(spec.get("new_identity_outside_m1680_m1690"))
        rows.append(
            {
                "source_resolution_id": f"m3009-source-resolution-{index:04d}",
                "new_task_source_spec_id": spec.get("new_task_source_spec_id", ""),
                "task_source_id": spec.get("task_source_id", ""),
                "axis_name": spec.get("axis_name", ""),
                "axis_family": spec.get("axis_family", ""),
                "axis_variant_tag": spec.get("axis_variant_tag", ""),
                "task_family": spec.get("task_family", ""),
                "source_edge": spec.get("source_edge", ""),
                "window_tag": spec.get("window_tag", ""),
                "reference_m1680_task_source_id": spec.get("reference_m1680_task_source_id", ""),
                "new_identity_outside_m1680_m1690": _bool(spec.get("new_identity_outside_m1680_m1690")),
                "overlaps_exhausted_m1690_l3": _bool(spec.get("overlaps_exhausted_m1690_l3")),
                "source_spec_preserved": preserved,
                "source_build_scheduled_by_m3009": False,
                "execution_scheduled_by_m3009": False,
                "actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "source_labels_actor_visible": False,
                "route_labels_actor_visible": False,
                "outcome_labels_actor_visible": False,
                "status_pass": preserved and not _bool(spec.get("overlaps_exhausted_m1690_l3")),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_profile_binding_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    bindings = [
        (
            "route_a_candidate_m2655_mitigation_preserving",
            "candidate",
            source["m2655_config"],
            source["m2655_checkpoint"],
        ),
        (
            "route_a_parent_l3_online_gru",
            "parent",
            source["m1674_config"],
            source["m1674_checkpoint"],
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, role, config_path, checkpoint_path) in enumerate(bindings, start=1):
        config_exists = Path(config_path).exists()
        checkpoint_exists = Path(checkpoint_path).exists()
        rows.append(
            {
                "profile_binding_id": f"m3009-profile-binding-{index:04d}",
                "profile_binding_name": name,
                "binding_role": role,
                "config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": config_exists,
                "checkpoint_exists": checkpoint_exists,
                "read_only_binding": True,
                "profile_specific_tuning": False,
                "checkpoint_mutation_scheduled": False,
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "status_pass": config_exists and checkpoint_exists and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_workload_contract_rows(
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in source_rows:
        for profile_row in profile_rows:
            index = len(rows) + 1
            status_pass = (
                _bool(source_row["status_pass"])
                and _bool(profile_row["status_pass"])
                and _bool(source_row["source_spec_preserved"])
                and _bool(profile_row["read_only_binding"])
            )
            rows.append(
                {
                    "workload_contract_id": f"m3009-workload-contract-{index:04d}",
                    "source_resolution_id": source_row["source_resolution_id"],
                    "profile_binding_id": profile_row["profile_binding_id"],
                    "task_source_id": source_row["task_source_id"],
                    "profile_binding_name": profile_row["profile_binding_name"],
                    "binding_role": profile_row["binding_role"],
                    "axis_name": source_row["axis_name"],
                    "axis_family": source_row["axis_family"],
                    "task_family": source_row["task_family"],
                    "source_edge": source_row["source_edge"],
                    "window_tag": source_row["window_tag"],
                    "config_path": profile_row["config_path"],
                    "checkpoint_path": profile_row["checkpoint_path"],
                    "actor_observation_dim": P0_OBSERVATION_DIM,
                    "actor_action_dim": ACTION_DIM,
                    "new_source_identity_preserved": _bool(source_row["source_spec_preserved"]),
                    "read_only_profile_binding": _bool(profile_row["read_only_binding"]),
                    "future_execution_manifest_required": True,
                    "source_build_scheduled_by_m3009": False,
                    "environment_reset_scheduled_by_m3009": False,
                    "environment_step_scheduled_by_m3009": False,
                    "policy_action_scheduled_by_m3009": False,
                    "validation_scheduled_by_m3009": False,
                    "training_scheduled_by_m3009": False,
                    "ranking_scheduled_by_m3009": False,
                    "checkpoint_mutation_scheduled": False,
                    "actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "source_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "outcome_labels_actor_visible": False,
                    "status_pass": status_pass,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_rejected_workload_shortcut_rows() -> list[dict[str, Any]]:
    rejected = [
        (
            "direct_execution_from_m3008_design",
            "execution_shortcut",
            "M3008 is design-only and M3009 is materialization-only",
        ),
        (
            "drop_m3006_source_specs_for_smaller_panel",
            "source_identity_shortcut",
            "all 16 M3006 source identities must be preserved",
        ),
        (
            "reuse_m1680_spec_ids_as_new_identity",
            "same_surface_shortcut",
            "old M1690 L3 identities remain exhausted and cannot become fresh ids",
        ),
        (
            "candidate_only_without_parent_binding",
            "comparison_denominator_shortcut",
            "M3008 requires candidate and parent read-only profile bindings",
        ),
        (
            "profile_specific_tuning_for_new_sources",
            "profile_tuning_shortcut",
            "M3009 may bind configs/checkpoints but cannot tune profiles",
        ),
        (
            "source_build_inside_materialization",
            "execution_readiness_shortcut",
            "source build requires a separate post-audit route",
        ),
        (
            "hidden_source_or_outcome_labels_actor_visible",
            "actor_contract_shortcut",
            "source route outcome progress and verdict labels are evaluator metadata only",
        ),
        (
            "ranking_or_performance_interpretation",
            "claim_boundary_shortcut",
            "workload contracts are not execution results or performance evidence",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (route, family, reason) in enumerate(rejected, start=1):
        rows.append(
            {
                "rejected_workload_shortcut_id": f"m3009-rejected-workload-shortcut-{index:04d}",
                "rejected_route": route,
                "rejection_family": family,
                "rejection_reason": reason,
                "required_follow_up": "preserve rejection until a separate audited route admits the work",
                "actor_visible": False,
                "workload_denominator_allowed": False,
                "execution_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    guards = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, 72),
        ("actor_action_dim", ACTION_DIM, 3),
        ("actor_input_contract_changed", False, False),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("source_labels_actor_visible", False, False),
        ("route_labels_actor_visible", False, False),
        ("outcome_labels_actor_visible", False, False),
        ("success_progress_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
        ("profile_specific_tuning", False, False),
        ("materialization_only_no_execution", True, True),
    ]
    return [
        {
            "guard_id": f"m3009-actor-guard-{index:04d}",
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
        ("workload_contract_materialization", True, True, "M3010 result audit before execution design"),
        ("new_source_workload_identity_accounting", True, True, "M3010 result audit before interpretation"),
        ("source_build_readiness", False, False, "separate source-build route and audit"),
        ("executable_environment_readiness", False, False, "separate executable environment materialization and audit"),
        ("execution_result", False, False, "separate execution manifest and audit"),
        ("validation_result", False, False, "separate validation manifest and audit"),
        ("repair_success", False, False, "closed-loop fresh-source evidence"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_evidence", False, False, "paper-route proof gates"),
        ("high_fidelity_validation", False, False, "Route C validation layer"),
        ("finite_window_vs_gru_result", False, False, "separate controller-family comparison"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "history-necessity/self-ID proof gates"),
        ("checkpoint_ranking_or_promotion", False, False, "promotion gates after proof and generalization"),
    ]
    return [
        {
            "claim_id": f"m3009-claim-{index:04d}",
            "claim_family": claim,
            "allowed_in_m3009": allowed,
            "claim_made": made,
            "status_pass": required_artifacts_present and made is allowed,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (claim, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    workload_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    source_ids = {row["task_source_id"] for row in source_rows}
    workload_pairs = {(row["task_source_id"], row["profile_binding_id"]) for row in workload_rows}
    expected_pairs = {(source["task_source_id"], profile["profile_binding_id"]) for source in source_rows for profile in profile_rows}
    gates = [
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
        ("m3007_audit_present", source["m3007_audit_exists"], source["m3007_audit_exists"], True, "lineage_invalid"),
        ("m3008_design_present", source["m3008_design_exists"], source["m3008_design_exists"], True, "lineage_invalid"),
        ("m3006_status_pass", source["m3006_summary"].get("status_pass") is True, source["m3006_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m3006_gate_matrix_pass", source["m3006_summary"].get("gate_matrix_pass") is True, source["m3006_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        ("m3006_source_spec_row_count", len(source["m3006_source_spec_rows"]) == SOURCE_SPEC_COUNT, len(source["m3006_source_spec_rows"]), SOURCE_SPEC_COUNT, "scenario_sampling_failure"),
        ("source_spec_resolution_row_count", len(source_rows) == SOURCE_SPEC_COUNT, len(source_rows), SOURCE_SPEC_COUNT, "scenario_sampling_failure"),
        ("source_spec_unique_task_source_count", len(source_ids) == SOURCE_SPEC_COUNT, len(source_ids), SOURCE_SPEC_COUNT, "lineage_invalid"),
        ("old_m1690_l3_overlap_count", old_overlap_count(source_rows) == 0, old_overlap_count(source_rows), 0, "objective_overfit"),
        ("source_resolution_rows_pass", all(_bool(row["status_pass"]) for row in source_rows), "all source rows pass", True, "lineage_invalid"),
        ("profile_binding_row_count", len(profile_rows) == PROFILE_BINDING_COUNT, len(profile_rows), PROFILE_BINDING_COUNT, "lineage_invalid"),
        ("profile_binding_rows_pass", all(_bool(row["status_pass"]) for row in profile_rows), "all profile rows pass", True, "lineage_invalid"),
        ("profile_bindings_read_only", all(_bool(row["read_only_binding"]) for row in profile_rows), "all read only", True, "contract_violation"),
        ("profile_specific_tuning_count", sum(1 for row in profile_rows if _bool(row["profile_specific_tuning"])) == 0, sum(1 for row in profile_rows if _bool(row["profile_specific_tuning"])), 0, "contract_violation"),
        ("workload_contract_row_count", len(workload_rows) == WORKLOAD_CONTRACT_COUNT, len(workload_rows), WORKLOAD_CONTRACT_COUNT, "scenario_sampling_failure"),
        ("workload_cross_product_complete", workload_pairs == expected_pairs, len(workload_pairs), len(expected_pairs), "lineage_invalid"),
        ("workload_contract_rows_pass", all(_bool(row["status_pass"]) for row in workload_rows), "all workload rows pass", True, "lineage_invalid"),
        ("rejected_workload_shortcut_rows_present", len(rejected_rows) >= 8, len(rejected_rows), ">=8", "objective_overfit"),
        ("actor_contract_rows_pass", all(_bool(row["status_pass"]) for row in actor_rows), "all actor rows pass", True, "contract_violation"),
        ("claim_boundary_rows_pass", all(_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass", True, "proof_washout"),
        ("follow_up_manifest_written", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
        ("source_build_run", True, False, False, "contract_violation"),
        ("environment_execution_run", True, False, False, "contract_violation"),
        ("validation_run", True, False, False, "contract_violation"),
        ("training_run", True, False, False, "contract_violation"),
        ("ranking_run", True, False, False, "proof_washout"),
        ("performance_claim_made", True, False, False, "proof_washout"),
        ("paper_claim_made", True, False, False, "proof_washout"),
        ("high_fidelity_claim_made", True, False, False, "proof_washout"),
        ("self_id_claim_made", True, False, False, "proof_washout"),
    ]
    return [
        {
            "gate_id": f"m3009-gate-{index:04d}",
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
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    workload_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    profile_rows_pass = bool(profile_rows) and all(_bool(row["status_pass"]) for row in profile_rows)
    workload_rows_pass = bool(workload_rows) and all(_bool(row["status_pass"]) for row in workload_rows)
    status_pass = (
        gate_matrix_pass
        and actor_rows_pass
        and claim_rows_pass
        and profile_rows_pass
        and workload_rows_pass
        and required_artifacts_present
    )
    axis_counts = Counter(str(row["axis_name"]) for row in source_rows)
    task_family_counts = Counter(str(row["task_family"]) for row in source_rows)
    binding_counts = Counter(str(row["binding_role"]) for row in profile_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": DECISION_PASS if status_pass else DECISION_FAIL,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "m3007_audit_present": source["m3007_audit_exists"],
        "m3008_design_present": source["m3008_design_exists"],
        "m3006_status_pass": source["m3006_summary"].get("status_pass") is True,
        "m3006_gate_matrix_pass": source["m3006_summary"].get("gate_matrix_pass") is True,
        "m3006_source_spec_row_count": len(source["m3006_source_spec_rows"]),
        "source_spec_resolution_row_count": len(source_rows),
        "source_spec_unique_task_source_count": len({row["task_source_id"] for row in source_rows}),
        "old_m1690_l3_overlap_count": old_overlap_count(source_rows),
        "axis_counts": dict(sorted(axis_counts.items())),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "profile_binding_row_count": len(profile_rows),
        "profile_binding_counts": dict(sorted(binding_counts.items())),
        "profile_binding_rows_pass": profile_rows_pass,
        "workload_contract_row_count": len(workload_rows),
        "workload_contract_rows_pass": workload_rows_pass,
        "target_workload_contract_row_count": WORKLOAD_CONTRACT_COUNT,
        "rejected_workload_shortcut_row_count": len(rejected_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "profile_specific_tuning": False,
        "source_build_run": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
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
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3009 Engineering Controller Route A Post-Residual-Stop New Source Executable Workload Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- source spec resolution rows: {summary['source_spec_resolution_row_count']}",
            f"- unique source ids: {summary['source_spec_unique_task_source_count']}",
            f"- old M1690 L3 overlap count: {summary['old_m1690_l3_overlap_count']}",
            f"- profile binding rows: {summary['profile_binding_row_count']}",
            f"- workload contract rows: {summary['workload_contract_row_count']}",
            f"- axis counts: {summary['axis_counts']}",
            f"- task family counts: {summary['task_family_counts']}",
            f"- profile binding counts: {summary['profile_binding_counts']}",
            f"- rejected workload shortcut rows: {summary['rejected_workload_shortcut_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3009 materializes workload contract rows only. It does not build sources, instantiate environments, execute policies, validate, train, rank, promote, or claim repair success or performance.",
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
        "hypothesis": "A bounded result audit can accept or reject the M3009 new-source executable workload materialization before any execution validation ranking promotion repair-success performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(DEFAULT_M2655_CHECKPOINT), str(DEFAULT_M1674_CHECKPOINT)],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "source_spec_resolution_rows.csv"),
                str(output_dir / "profile_binding_rows.csv"),
                str(output_dir / "executable_workload_contract_rows.csv"),
                str(output_dir / "rejected_workload_shortcut_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3008_ID}.json",
            ],
            "parent_objective": ["audit M3009 workload materialization before any execution design or stop"],
            "derived_from": [MILESTONE_ID, M3008_ID, M3007_ID],
            "blocked_by": [
                "M3009 workload rows require audit before any execution design",
                "workload contract rows are not execution readiness or performance evidence",
            ],
            "supersedes": [
                "direct execution from M3009 without result audit",
                "direct performance interpretation of workload contract rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3010 must audit M3009 summary workload rows actor and claim boundaries",
            "M3010 must preserve 16 source identities 2 profile bindings and 32 workload contract rows",
            "M3010 must not convert contract rows into execution validation performance paper high-fidelity or self-ID evidence",
            "M3010 must select exactly one next route or explicit stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute workloads build sources validate train rank promote or select a winner",
            "do not change actor input or action contract",
            "do not convert M3009 workload rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_executable_workload_materialization_result_audit",
            "evidence_increment": "audits M3009 workload-contract materialization and decides execution design repair synthesis or stop",
            "claim_scope": "Result audit only; no execution validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3009 artifacts are missing or gate matrix fails",
                "stop if workload rows drop source specs or profile bindings",
                "stop if actor or claim boundaries were violated",
                "stop if workload-contract rows would be used as execution results",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if no execution design is viable",
                "route to bounded execution design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3009 completes workload materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3009 no-execution workload materialization artifacts",
            "admission_evidence": ["M3009 summary and gate matrix", "M3009 source profile workload actor and claim artifacts"],
            "blocked_shortcuts": [
                "no execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO checkpoint mutation",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3010 status queue scoreboard research log and review",
                "one follow-up manifest only if M3010 selects exactly one next route",
            ],
            "next_stage_criteria": ["M3010 audit accepts or rejects M3009 as complete and claim-safe", "next route or stop state is explicit"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3010 audits workload-contract materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3010; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."],
            "temporal_evidence_window": "M3009 workload materialization only.",
            "negative_result_policy": "Preserve workload materialization failures and route to synthesis or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3009 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized workload-contract panel",
            "paper_verdict_delta": "no paper verdict; audit may authorize execution design only",
            "must_synthesize_if": [
                "M3010 cannot accept M3009 as complete and claim-safe",
                "M3010 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M3010 cannot select execution design repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3010 audits M3009 artifacts row counts gates actor and claim boundaries",
            "M3010 selects exactly one next route or stop state",
            "no execution training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3010 hides M3009 failures or missing artifacts",
            "M3010 treats M3009 workload contracts as execution readiness performance verdict or repair success",
            "M3010 changes actor input or action contract",
            "M3010 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3010 audits M3009 artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(DEFAULT_M2655_CHECKPOINT), str(DEFAULT_M1674_CHECKPOINT)],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "source_spec_resolution_rows.csv"),
            str(output_dir / "profile_binding_rows.csv"),
            str(output_dir / "executable_workload_contract_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def old_overlap_count(rows: list[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _bool(row.get("overlaps_exhausted_m1690_l3")))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3007-audit", type=Path, default=DEFAULT_M3007_AUDIT)
    parser.add_argument("--m3008-design", type=Path, default=DEFAULT_M3008_DESIGN)
    parser.add_argument("--m3006-dir", type=Path, default=DEFAULT_M3006_DIR)
    parser.add_argument("--m1674-config", type=Path, default=DEFAULT_M1674_CONFIG)
    parser.add_argument("--m1674-checkpoint", type=Path, default=DEFAULT_M1674_CHECKPOINT)
    parser.add_argument("--m2655-config", type=Path, default=DEFAULT_M2655_CONFIG)
    parser.add_argument("--m2655-checkpoint", type=Path, default=DEFAULT_M2655_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_new_source_executable_workload_materialization_preflight(
        m3007_audit=args.m3007_audit,
        m3008_design=args.m3008_design,
        m3006_dir=args.m3006_dir,
        m1674_config=args.m1674_config,
        m1674_checkpoint=args.m1674_checkpoint,
        m2655_config=args.m2655_config,
        m2655_checkpoint=args.m2655_checkpoint,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
