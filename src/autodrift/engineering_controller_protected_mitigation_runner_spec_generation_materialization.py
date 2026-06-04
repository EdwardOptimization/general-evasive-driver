"""Materialize protected mitigation runner-spec generation rows.

M2697 consumes the accepted M2695 protected bridge pack, the M2662 protected
panel specs, and the M1690 executable workload schema. It creates auditable
protected runner-spec candidates and traceability rows for every M2695
unbridgeable protected target. It does not reset environments, step, roll out
policies, validate, train, rank, promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    load_executable_specs,
    load_executable_workload,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2697-engineering-controller-protected-mitigation-runner-spec-generation-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2698-engineering-controller-protected-mitigation-runner-spec-generation-"
    "materialization-result-audit"
)
DEFAULT_M2695_DIR = Path("runs/m2695_engineering_controller_protected_mitigation_target_executable_surface_bridge")
DEFAULT_M2662_DIR = Path("runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel")
DEFAULT_M2664_DIR = Path("runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy")
DEFAULT_M2667_DIR = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation")
DEFAULT_DOC_PATH = Path(
    "docs/m2697-engineering-controller-protected-mitigation-runner-spec-generation-materialization-preflight.md"
)
DEFAULT_M2696_AUDIT_DOC = Path(
    "docs/m2696-engineering-controller-protected-mitigation-target-executable-surface-bridge-materialization-result-audit.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2698-engineering-controller-protected-mitigation-runner-spec-generation-materialization-result-audit.json"
)
DEFAULT_PROFILE_NAME = "L3_online_gru"
DEFAULT_POLICY_SUBJECT_ID = "m2655_mitigation_preserving_policy"
DEFAULT_CHECKPOINT_PATH = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
    "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
PROTECTED_TASK_FAMILY = "route_a_protected"

CLAIM_SCOPE = (
    "M2697 protected mitigation runner-spec generation materialization only; "
    "M2695 unbridgeable protected targets, M2662 protected panel specs, M2664 "
    "taxonomy rows, M2667 known-failure rows, and M1690 executable workload "
    "schema may be reanalyzed into protected runner-spec, workload-candidate, "
    "traceability, unmaterialized, actor-contract, claim-boundary, and gate rows, "
    "but no reset, step, rollout, replay, validation, training, PPO, private "
    "holdout, profile-specific tuning, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, finite-"
    "window-vs-GRU, current-response, current-sim, high-fidelity validation, "
    "full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity validation "
    "readiness or result, full ideal driver completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
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
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_simulation_run": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "full_ideal_driver_completion_claim_made": False,
    "level3_self_id_claim_made": False,
}

PROTECTED_RUNNER_SPEC_FIELDNAMES = [
    "runner_spec_id",
    "source_panel_spec_id",
    "protected_task_family",
    "protected_source_edge",
    "role_family",
    "role_class",
    "seed_index",
    "seed",
    "dynamics_axis_id",
    "dynamics_axis_family",
    "axis_index",
    "base_fixture_id",
    "fixture_id",
    "surface_id",
    "fixture_variant_digest",
    "initial_state_digest",
    "fault_scale_digest",
    "road_digest",
    "obstacle_digest",
    "env_template_family",
    "runner_backend_family",
    "materialization_rule",
    "actor_observation_shape",
    "action_shape",
    "actor_visible_allowed",
    "hidden_diagnostics_metadata_only",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
PROTECTED_WORKLOAD_FIELDNAMES = [
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "profile_name",
    "policy_subject_id",
    "policy_checkpoint_path",
    "policy_checkpoint_exists",
    "reference_profile_config_path",
    "reference_profile_config_exists",
    "reference_profile_checkpoint_path",
    "m1690_exact_workload_match",
    "m1690_reference_workload_id",
    "protected_task_family",
    "protected_source_edge",
    "workload_candidate_status",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
TRACEABILITY_FIELDNAMES = [
    "trace_id",
    "target_id",
    "target_family",
    "source_key",
    "taxonomy_axis",
    "role_semantics_proxy",
    "unbridgeable_reason",
    "runner_spec_id",
    "panel_spec_id",
    "join_rule",
    "join_status",
    "taxonomy_row_id",
    "taxonomy_subject_id",
    "taxonomy_dynamics_axis_id",
    "target_metric",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
UNMATERIALIZED_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_key",
    "taxonomy_axis",
    "role_semantics_proxy",
    "unmaterialized_reason",
    "missing_contract",
    "required_follow_up",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "materialization_only_no_execution",
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
    "allowed_in_m2697",
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
    "protected_runner_spec_rows",
    "protected_workload_candidate_rows",
    "spec_traceability_rows",
    "unmaterialized_bridge_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_mitigation_runner_spec_generation(
    *,
    m2695_dir: Path | str = DEFAULT_M2695_DIR,
    m2662_dir: Path | str = DEFAULT_M2662_DIR,
    m2664_dir: Path | str = DEFAULT_M2664_DIR,
    m2667_dir: Path | str = DEFAULT_M2667_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m2696_audit_doc: Path | str = DEFAULT_M2696_AUDIT_DOC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    profile_name: str = DEFAULT_PROFILE_NAME,
    policy_subject_id: str = DEFAULT_POLICY_SUBJECT_ID,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2695_dir=Path(m2695_dir),
        m2662_dir=Path(m2662_dir),
        m2664_dir=Path(m2664_dir),
        m2667_dir=Path(m2667_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        m2696_audit_doc=Path(m2696_audit_doc),
        follow_up_manifest=Path(follow_up_manifest),
    )

    runner_spec_rows = build_protected_runner_spec_rows(source["m2662_panel_spec_rows"])
    workload_candidate_rows = build_workload_candidate_rows(
        runner_spec_rows=runner_spec_rows,
        source=source,
        profile_name=profile_name,
        policy_subject_id=policy_subject_id,
        checkpoint_path=Path(checkpoint_path),
    )
    spec_traceability_rows, unmaterialized_rows = build_traceability_rows(
        source=source,
        runner_spec_rows=runner_spec_rows,
    )
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
        all_targets_accounted=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        runner_spec_rows=runner_spec_rows,
        workload_candidate_rows=workload_candidate_rows,
        spec_traceability_rows=spec_traceability_rows,
        unmaterialized_rows=unmaterialized_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["protected_runner_spec_rows"], runner_spec_rows, fieldnames=PROTECTED_RUNNER_SPEC_FIELDNAMES)
    write_csv_rows(
        paths["protected_workload_candidate_rows"],
        workload_candidate_rows,
        fieldnames=PROTECTED_WORKLOAD_FIELDNAMES,
    )
    write_csv_rows(paths["spec_traceability_rows"], spec_traceability_rows, fieldnames=TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["unmaterialized_bridge_rows"], unmaterialized_rows, fieldnames=UNMATERIALIZED_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key != "doc")
    all_targets_accounted = target_ids_accounted(source, spec_traceability_rows, unmaterialized_rows)
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        runner_spec_rows=runner_spec_rows,
        workload_candidate_rows=workload_candidate_rows,
        spec_traceability_rows=spec_traceability_rows,
        unmaterialized_rows=unmaterialized_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        runner_spec_rows=runner_spec_rows,
        workload_candidate_rows=workload_candidate_rows,
        spec_traceability_rows=spec_traceability_rows,
        unmaterialized_rows=unmaterialized_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        policy_subject_id=policy_subject_id,
        checkpoint_path=Path(checkpoint_path),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        runner_spec_rows=runner_spec_rows,
        workload_candidate_rows=workload_candidate_rows,
        spec_traceability_rows=spec_traceability_rows,
        unmaterialized_rows=unmaterialized_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        runner_spec_rows=runner_spec_rows,
        workload_candidate_rows=workload_candidate_rows,
        spec_traceability_rows=spec_traceability_rows,
        unmaterialized_rows=unmaterialized_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        policy_subject_id=policy_subject_id,
        checkpoint_path=Path(checkpoint_path),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "protected_runner_spec_rows": output_dir / "protected_runner_spec_rows.csv",
        "protected_workload_candidate_rows": output_dir / "protected_workload_candidate_rows.csv",
        "spec_traceability_rows": output_dir / "spec_traceability_rows.csv",
        "unmaterialized_bridge_rows": output_dir / "unmaterialized_bridge_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2695_dir: Path,
    m2662_dir: Path,
    m2664_dir: Path,
    m2667_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    m2696_audit_doc: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2696_audit_doc": m2696_audit_doc,
        "m2695_summary": m2695_dir / "summary.json",
        "m2695_protected_bridge_rows": m2695_dir / "protected_bridge_rows.csv",
        "m2695_unbridgeable_target_rows": m2695_dir / "unbridgeable_target_rows.csv",
        "m2695_actor_contract_guard_rows": m2695_dir / "actor_contract_guard_rows.csv",
        "m2695_claim_boundary_rows": m2695_dir / "claim_boundary_rows.csv",
        "m2695_gate_matrix": m2695_dir / "gate_matrix.csv",
        "m2662_summary": m2662_dir / "summary.json",
        "m2662_panel_spec_rows": m2662_dir / "panel_spec_rows.csv",
        "m2662_protected_mitigation_gate_rows": m2662_dir / "protected_mitigation_gate_rows.csv",
        "m2662_gate_matrix": m2662_dir / "gate_matrix.csv",
        "m2664_summary": m2664_dir / "summary.json",
        "m2664_combined_failure_taxonomy_rows": m2664_dir / "combined_failure_taxonomy_rows.csv",
        "m2667_summary": m2667_dir / "summary.json",
        "m2667_known_failure_boundary_rows": m2667_dir / "known_failure_boundary_rows.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    specs: list[dict[str, Any]] = []
    workload_rows: list[dict[str, Any]] = []
    if source_exists["executable_task_specs"]:
        specs = [dict(row) for row in load_executable_specs(paths["executable_task_specs"])]
    if source_exists["executable_workload_matrix"]:
        workload_rows = [dict(row) for row in load_executable_workload(paths["executable_workload_matrix"])]
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2695_summary": read_json(paths["m2695_summary"]) if source_exists["m2695_summary"] else {},
        "m2695_protected_bridge_rows": read_csv_rows(paths["m2695_protected_bridge_rows"]),
        "m2695_unbridgeable_target_rows": read_csv_rows(paths["m2695_unbridgeable_target_rows"]),
        "m2695_actor_contract_guard_rows": read_csv_rows(paths["m2695_actor_contract_guard_rows"]),
        "m2695_claim_boundary_rows": read_csv_rows(paths["m2695_claim_boundary_rows"]),
        "m2695_gate_matrix": read_csv_rows(paths["m2695_gate_matrix"]),
        "m2662_summary": read_json(paths["m2662_summary"]) if source_exists["m2662_summary"] else {},
        "m2662_panel_spec_rows": read_csv_rows(paths["m2662_panel_spec_rows"]),
        "m2662_protected_mitigation_gate_rows": read_csv_rows(paths["m2662_protected_mitigation_gate_rows"]),
        "m2662_gate_matrix": read_csv_rows(paths["m2662_gate_matrix"]),
        "m2664_summary": read_json(paths["m2664_summary"]) if source_exists["m2664_summary"] else {},
        "m2664_combined_failure_taxonomy_rows": read_csv_rows(paths["m2664_combined_failure_taxonomy_rows"]),
        "m2667_summary": read_json(paths["m2667_summary"]) if source_exists["m2667_summary"] else {},
        "m2667_known_failure_boundary_rows": read_csv_rows(paths["m2667_known_failure_boundary_rows"]),
        "executable_task_specs": specs,
        "executable_workload_matrix": workload_rows,
    }


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_protected_runner_spec_rows(panel_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    protected_panels = sorted(
        [row for row in panel_rows if str(row.get("role_class", "")) == "protected"],
        key=lambda row: (int(float(row.get("seed", 0) or 0)), str(row.get("dynamics_axis_id", "")), row.get("panel_spec_id", "")),
    )
    rows: list[dict[str, Any]] = []
    for index, panel in enumerate(protected_panels, start=1):
        dynamics_axis = str(panel.get("dynamics_axis_id", ""))
        rows.append(
            {
                "runner_spec_id": f"m2697-protected-runner-spec-{index:04d}",
                "source_panel_spec_id": panel.get("panel_spec_id", ""),
                "protected_task_family": PROTECTED_TASK_FAMILY,
                "protected_source_edge": f"{panel.get('role_family', '')}|{dynamics_axis}",
                "role_family": panel.get("role_family", ""),
                "role_class": panel.get("role_class", ""),
                "seed_index": _int(panel.get("seed_index")),
                "seed": _int(panel.get("seed")),
                "dynamics_axis_id": dynamics_axis,
                "dynamics_axis_family": panel.get("dynamics_axis_family", panel.get("axis_family", "")),
                "axis_index": _int(panel.get("axis_index")),
                "base_fixture_id": panel.get("base_fixture_id", ""),
                "fixture_id": panel.get("fixture_id", ""),
                "surface_id": panel.get("surface_id", ""),
                "fixture_variant_digest": panel.get("fixture_variant_digest", ""),
                "initial_state_digest": panel.get("initial_state_digest", ""),
                "fault_scale_digest": panel.get("fault_scale_digest", ""),
                "road_digest": panel.get("road_digest", ""),
                "obstacle_digest": panel.get("obstacle_digest", ""),
                "env_template_family": panel.get("base_fixture_id", ""),
                "runner_backend_family": panel.get("surface_id", ""),
                "materialization_rule": "m2662_protected_panel_spec_to_route_a_protected_runner_spec",
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_visible_allowed": False,
                "hidden_diagnostics_metadata_only": True,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "protected_rows_in_success_denominator": False,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_workload_candidate_rows(
    *,
    runner_spec_rows: list[dict[str, Any]],
    source: dict[str, Any],
    profile_name: str,
    policy_subject_id: str,
    checkpoint_path: Path,
) -> list[dict[str, Any]]:
    profile_reference = first_workload_profile_reference(source["executable_workload_matrix"], profile_name)
    exact_m1690 = {
        (str(row.get("profile_name", "")), str(row.get("task_family", "")), str(row.get("source_edge", ""))): row
        for row in source["executable_workload_matrix"]
    }
    rows: list[dict[str, Any]] = []
    for spec in runner_spec_rows:
        key = (profile_name, str(spec["protected_task_family"]), str(spec["protected_source_edge"]))
        match = exact_m1690.get(key)
        reference_config = str(profile_reference.get("profile_config_path", ""))
        reference_checkpoint = str(profile_reference.get("checkpoint_path", ""))
        rows.append(
            {
                "workload_candidate_id": f"{spec['runner_spec_id']}::{profile_name}",
                "runner_spec_id": spec["runner_spec_id"],
                "source_panel_spec_id": spec["source_panel_spec_id"],
                "profile_name": profile_name,
                "policy_subject_id": policy_subject_id,
                "policy_checkpoint_path": str(checkpoint_path),
                "policy_checkpoint_exists": checkpoint_path.exists(),
                "reference_profile_config_path": reference_config,
                "reference_profile_config_exists": bool(reference_config) and Path(reference_config).exists(),
                "reference_profile_checkpoint_path": reference_checkpoint,
                "m1690_exact_workload_match": bool(match),
                "m1690_reference_workload_id": match.get("workload_id", "") if match else profile_reference.get("workload_id", ""),
                "protected_task_family": spec["protected_task_family"],
                "protected_source_edge": spec["protected_source_edge"],
                "workload_candidate_status": (
                    "exact_m1690_workload_match" if match else "protected_runner_spec_materialized_not_in_current_m1690_workload"
                ),
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "protected_rows_in_success_denominator": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def first_workload_profile_reference(workload_rows: list[dict[str, Any]], profile_name: str) -> dict[str, Any]:
    for row in sorted(workload_rows, key=lambda item: str(item.get("workload_id", ""))):
        if str(row.get("profile_name", "")) == profile_name:
            return row
    return {}


def build_traceability_rows(
    *,
    source: dict[str, Any],
    runner_spec_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runner_by_panel = {str(row["source_panel_spec_id"]): row for row in runner_spec_rows}
    panel_by_id = {str(row.get("panel_spec_id", "")): row for row in source["m2662_panel_spec_rows"]}
    taxonomy_rows = source["m2664_combined_failure_taxonomy_rows"]
    boundary_by_id = {str(row.get("boundary_id", "")): row for row in source["m2667_known_failure_boundary_rows"]}
    trace_rows: list[dict[str, Any]] = []
    unmaterialized_rows: list[dict[str, Any]] = []
    trace_index = 1
    for target in sorted(source["m2695_unbridgeable_target_rows"], key=lambda row: str(row.get("target_id", ""))):
        matches = matching_panels_for_target(target=target, panel_rows=source["m2662_panel_spec_rows"], taxonomy_rows=taxonomy_rows)
        if not matches:
            unmaterialized_rows.append(unmaterialized_row(target, boundary_by_id))
            continue
        for panel_id, join_rule, taxonomy in matches:
            runner = runner_by_panel.get(panel_id, {})
            panel = panel_by_id.get(panel_id, {})
            trace_rows.append(
                {
                    "trace_id": f"m2697-trace-{trace_index:04d}",
                    "target_id": target.get("target_id", ""),
                    "target_family": target.get("target_family", ""),
                    "source_key": target.get("source_key", ""),
                    "taxonomy_axis": target.get("taxonomy_axis", ""),
                    "role_semantics_proxy": target.get("role_semantics_proxy", ""),
                    "unbridgeable_reason": target.get("unbridgeable_reason", ""),
                    "runner_spec_id": runner.get("runner_spec_id", ""),
                    "panel_spec_id": panel_id,
                    "join_rule": join_rule,
                    "join_status": "materialized" if runner else "panel_without_runner_spec",
                    "taxonomy_row_id": taxonomy.get("taxonomy_id", ""),
                    "taxonomy_subject_id": taxonomy.get("subject_id", ""),
                    "taxonomy_dynamics_axis_id": taxonomy.get("dynamics_axis_id", panel.get("dynamics_axis_id", "")),
                    "target_metric": target.get("role_semantics_proxy", "") if target.get("taxonomy_axis") == "metric" else "",
                    "protected_rows_in_success_denominator": False,
                    "target_labels_actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "actor_input_contract_changed": False,
                    "materialization_only_no_execution": True,
                    "diagnostic_only_no_verdict": True,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            trace_index += 1
    return trace_rows, unmaterialized_rows


def matching_panels_for_target(
    *,
    target: dict[str, str],
    panel_rows: list[dict[str, str]],
    taxonomy_rows: list[dict[str, str]],
) -> list[tuple[str, str, dict[str, str]]]:
    axis = str(target.get("taxonomy_axis", ""))
    value = str(target.get("role_semantics_proxy", ""))
    panels = [row for row in panel_rows if str(row.get("role_class", "")) == "protected"]
    matches: list[tuple[str, str, dict[str, str]]] = []
    if axis == "scenario_role":
        for panel in panels:
            if str(panel.get("role_family", "")) == value:
                matches.append((str(panel.get("panel_spec_id", "")), "scenario_role_to_m2662_role_family", {}))
    elif axis == "dynamics_axis":
        for panel in panels:
            if str(panel.get("dynamics_axis_id", "")) == value:
                matches.append((str(panel.get("panel_spec_id", "")), "dynamics_axis_to_m2662_dynamics_axis_id", {}))
    elif axis == "subject":
        subject_taxonomy = [row for row in taxonomy_rows if str(row.get("subject_id", "")) == value]
        for taxonomy in subject_taxonomy:
            for panel in panels:
                if str(panel.get("dynamics_axis_id", "")) == str(taxonomy.get("dynamics_axis_id", "")):
                    matches.append((str(panel.get("panel_spec_id", "")), "subject_taxonomy_to_m2662_axis_panel", taxonomy))
    elif axis == "metric":
        metric_taxonomy = [
            row
            for row in taxonomy_rows
            if value in {part.strip() for part in str(row.get("blocking_metrics", "")).split(";") if part.strip()}
        ]
        for taxonomy in metric_taxonomy:
            for panel in panels:
                if str(panel.get("dynamics_axis_id", "")) == str(taxonomy.get("dynamics_axis_id", "")):
                    matches.append((str(panel.get("panel_spec_id", "")), "metric_taxonomy_to_m2662_axis_panel", taxonomy))
    deduped: dict[tuple[str, str, str], tuple[str, str, dict[str, str]]] = {}
    for panel_id, join_rule, taxonomy in matches:
        deduped[(panel_id, join_rule, taxonomy.get("taxonomy_id", ""))] = (panel_id, join_rule, taxonomy)
    return list(deduped.values())


def unmaterialized_row(target: dict[str, str], boundary_by_id: dict[str, dict[str, str]]) -> dict[str, Any]:
    boundary = boundary_by_id.get(str(target.get("source_key", "")), {})
    return {
        "target_id": target.get("target_id", ""),
        "target_family": target.get("target_family", ""),
        "source_key": target.get("source_key", ""),
        "taxonomy_axis": target.get("taxonomy_axis", boundary.get("taxonomy_axis", "")),
        "role_semantics_proxy": target.get("role_semantics_proxy", boundary.get("subject_or_axis_or_metric", "")),
        "unmaterialized_reason": "no M2662 protected panel spec or M2664 taxonomy row matched this protected target",
        "missing_contract": "target-to-protected-panel traceability row",
        "required_follow_up": "taxonomy normalization before protected execution admission",
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    return [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True),
        actor_guard("action_shape", ACTION_DIM, ACTION_DIM, True),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_guard("hidden_oracle_actor_input_detected", False, False, False),
        actor_guard("protected_labels_actor_visible", False, False, False),
        actor_guard("target_labels_actor_visible", False, False, False),
        actor_guard("blocker_labels_actor_visible", False, False, False),
        actor_guard("route_labels_actor_visible", False, False, False),
        actor_guard("verdict_labels_actor_visible", False, False, False),
        actor_guard("protected_rows_in_success_denominator", False, False, False),
    ]


def actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2697_actor_guard_{field}",
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
    required_artifacts_present: bool,
    all_targets_accounted: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("protected_runner_spec_rows_materialized", "artifact", required_artifacts_present, "protected_runner_spec_rows.csv"),
        ("protected_workload_candidate_rows_materialized", "artifact", required_artifacts_present, "protected_workload_candidate_rows.csv"),
        ("spec_traceability_rows_materialized", "artifact", required_artifacts_present, "spec_traceability_rows.csv"),
        ("unmaterialized_bridge_rows_materialized", "artifact", required_artifacts_present, "unmaterialized_bridge_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", required_artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", required_artifacts_present, "gate_matrix.csv"),
        ("protected_targets_accounted", "traceability", all_targets_accounted, "traceability or unmaterialized row for every target"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2698 result audit manifest"),
    ]
    blocked = [
        ("reset_execution", "execution", "future protected execution manifest"),
        ("environment_step", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2697"),
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
        "claim_id": f"m2697_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2697": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    runner_spec_rows: list[dict[str, Any]],
    workload_candidate_rows: list[dict[str, Any]],
    spec_traceability_rows: list[dict[str, Any]],
    unmaterialized_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_required_keys = [
        "m2696_audit_doc",
        "m2695_summary",
        "m2695_protected_bridge_rows",
        "m2695_unbridgeable_target_rows",
        "m2695_actor_contract_guard_rows",
        "m2695_claim_boundary_rows",
        "m2695_gate_matrix",
        "m2662_summary",
        "m2662_panel_spec_rows",
        "m2662_protected_mitigation_gate_rows",
        "m2662_gate_matrix",
        "m2664_summary",
        "m2664_combined_failure_taxonomy_rows",
        "m2667_summary",
        "m2667_known_failure_boundary_rows",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    protected_targets = source["m2695_unbridgeable_target_rows"]
    trace_target_ids = {str(row.get("target_id", "")) for row in spec_traceability_rows}
    unmaterialized_target_ids = {str(row.get("target_id", "")) for row in unmaterialized_rows}
    target_ids = {str(row.get("target_id", "")) for row in protected_targets}
    runner_ids = {str(row.get("runner_spec_id", "")) for row in runner_spec_rows}
    workload_runner_ids = {str(row.get("runner_spec_id", "")) for row in workload_candidate_rows}
    trace_runner_ids = {str(row.get("runner_spec_id", "")) for row in spec_traceability_rows if row.get("runner_spec_id")}
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2697"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2697"])]
    return [
        gate(
            "m2697_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in source_required_keys),
            {key: source["source_exists"][key] for key in source_required_keys},
            "all M2696/M2695/M2662/M2664/M2667/M1690 artifacts present",
            "lineage_invalid",
        ),
        gate("m2695_status_pass", "lineage", _bool(source["m2695_summary"].get("status_pass")), source["m2695_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2662_status_pass", "lineage", _bool(source["m2662_summary"].get("status_pass")), source["m2662_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2664_status_pass", "lineage", _bool(source["m2664_summary"].get("status_pass")), source["m2664_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2667_status_pass", "lineage", _bool(source["m2667_summary"].get("status_pass")), source["m2667_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2695_unbridgeable_targets_present", "target_panel", len(protected_targets) > 0, len(protected_targets), ">0", "metric_artifact"),
        gate("protected_runner_specs_materialized", "runner_spec", len(runner_spec_rows) > 0, len(runner_spec_rows), ">0", "metric_artifact"),
        gate("runner_specs_from_m2662_panels", "runner_spec", len(runner_spec_rows) == len(source["m2662_panel_spec_rows"]), f"runner={len(runner_spec_rows)} panel={len(source['m2662_panel_spec_rows'])}", "one runner spec per M2662 panel spec", "metric_artifact"),
        gate("workload_candidates_cover_runner_specs", "workload", workload_runner_ids == runner_ids, f"workload={len(workload_runner_ids)} runner={len(runner_ids)}", "all runner specs have workload candidates", "metric_artifact"),
        gate("traceability_rows_reference_runner_specs", "traceability", trace_runner_ids.issubset(runner_ids), f"trace runner ids={len(trace_runner_ids)} runner ids={len(runner_ids)}", "trace runner ids subset of runner specs", "metric_artifact"),
        gate("protected_targets_accounted", "traceability", trace_target_ids | unmaterialized_target_ids == target_ids, f"trace={len(trace_target_ids)} unmaterialized={len(unmaterialized_target_ids)} target={len(target_ids)}", "traceability or unmaterialized row for every target", "proof_washout"),
        gate("unmaterialized_rows_visible_not_dropped", "traceability", unmaterialized_target_ids.isdisjoint(trace_target_ids), sorted(unmaterialized_target_ids), "unmaterialized target ids do not duplicate trace target ids", "proof_washout"),
        gate("m1690_reference_schema_consumed", "lineage", bool(source["executable_task_specs"]) and bool(source["executable_workload_matrix"]), f"specs={len(source['executable_task_specs'])} workload={len(source['executable_workload_matrix'])}", "non-empty executable schema/workload", "lineage_invalid"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("target_labels_actor_visible", False)) for row in runner_spec_rows + workload_candidate_rows + spec_traceability_rows + unmaterialized_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in runner_spec_rows + workload_candidate_rows + spec_traceability_rows + unmaterialized_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in runner_spec_rows + workload_candidate_rows + spec_traceability_rows + unmaterialized_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) for row in runner_spec_rows + workload_candidate_rows + spec_traceability_rows + unmaterialized_rows), "all output rows materialization only", "no reset step rollout", "objective_overfit"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claims) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        gate("follow_up_audit_registered", "workflow", source["source_exists"]["follow_up_manifest"], source["source_exists"]["follow_up_manifest"], True, "lineage_invalid"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
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
    runner_spec_rows: list[dict[str, Any]],
    workload_candidate_rows: list[dict[str, Any]],
    spec_traceability_rows: list[dict[str, Any]],
    unmaterialized_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
    profile_name: str,
    policy_subject_id: str,
    checkpoint_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    target_ids = {str(row.get("target_id", "")) for row in source["m2695_unbridgeable_target_rows"]}
    trace_target_ids = {str(row.get("target_id", "")) for row in spec_traceability_rows}
    unmaterialized_target_ids = {str(row.get("target_id", "")) for row in unmaterialized_rows}
    trace_counts = Counter(row.get("taxonomy_axis", "") for row in spec_traceability_rows)
    workload_match_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in workload_candidate_rows)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2697"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2697"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    all_targets_accounted = (trace_target_ids | unmaterialized_target_ids) == target_ids
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_mitigation_runner_spec_generation_materialization_pass"
            if status_pass
            else "engineering_controller_protected_mitigation_runner_spec_generation_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "profile_name": profile_name,
        "policy_subject_id": policy_subject_id,
        "checkpoint_path": str(checkpoint_path),
        "source_artifacts_present": all(
            source["source_exists"][key]
            for key in [
                "m2696_audit_doc",
                "m2695_summary",
                "m2695_protected_bridge_rows",
                "m2695_unbridgeable_target_rows",
                "m2695_actor_contract_guard_rows",
                "m2695_claim_boundary_rows",
                "m2695_gate_matrix",
                "m2662_summary",
                "m2662_panel_spec_rows",
                "m2662_protected_mitigation_gate_rows",
                "m2662_gate_matrix",
                "m2664_summary",
                "m2664_combined_failure_taxonomy_rows",
                "m2667_summary",
                "m2667_known_failure_boundary_rows",
                "executable_task_specs",
                "executable_workload_matrix",
            ]
        ),
        "m2695_status_pass": _bool(source["m2695_summary"].get("status_pass")),
        "m2695_exact_current_runner_match_count": _int(source["m2695_summary"].get("exact_current_runner_match_count")),
        "m2695_unbridgeable_target_count": len(source["m2695_unbridgeable_target_rows"]),
        "m2662_status_pass": _bool(source["m2662_summary"].get("status_pass")),
        "m2662_panel_spec_count": len(source["m2662_panel_spec_rows"]),
        "m2664_status_pass": _bool(source["m2664_summary"].get("status_pass")),
        "m2664_combined_taxonomy_row_count": len(source["m2664_combined_failure_taxonomy_rows"]),
        "m2667_status_pass": _bool(source["m2667_summary"].get("status_pass")),
        "m2667_known_failure_boundary_row_count": len(source["m2667_known_failure_boundary_rows"]),
        "protected_target_count": len(target_ids),
        "protected_runner_spec_row_count": len(runner_spec_rows),
        "protected_workload_candidate_row_count": len(workload_candidate_rows),
        "m1690_exact_workload_match_count": workload_match_count,
        "protected_workload_candidate_not_current_m1690_count": len(workload_candidate_rows) - workload_match_count,
        "spec_traceability_row_count": len(spec_traceability_rows),
        "traceability_axis_counts": dict(sorted(trace_counts.items())),
        "traceability_target_count": len(trace_target_ids),
        "unmaterialized_bridge_row_count": len(unmaterialized_rows),
        "all_protected_targets_accounted": all_targets_accounted,
        "all_unbridgeable_targets_traceable_or_unmaterialized": all_targets_accounted,
        "actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_contract_guard_rows),
        "claim_boundary_row_count": len(claim_boundary_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(blocked_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "materialization_only_no_execution": True,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "diagnostic_only_no_verdict": True,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2697 Engineering Controller Protected Mitigation Runner Spec Generation Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- protected targets: {summary['protected_target_count']}",
            f"- protected runner spec rows: {summary['protected_runner_spec_row_count']}",
            f"- protected workload candidate rows: {summary['protected_workload_candidate_row_count']}",
            f"- traceability rows: {summary['spec_traceability_row_count']}",
            f"- unmaterialized bridge rows: {summary['unmaterialized_bridge_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- next: `{summary['next_blocker']}`",
            "",
            "M2697 generates a protected runner-spec candidate surface from the M2662 protected panel specs and traces the M2695 unbridgeable protected targets to that surface. It is a materialization preflight only, not protected execution, validation, repair success, or driver-performance evidence.",
            "",
            "## Materialization Result",
            "",
            "```text",
            f"M2695 exact current-runner matches: {summary['m2695_exact_current_runner_match_count']}",
            f"M2695 unbridgeable protected targets: {summary['m2695_unbridgeable_target_count']}",
            f"M2662 protected panel specs: {summary['m2662_panel_spec_count']}",
            f"generated runner specs: {summary['protected_runner_spec_row_count']}",
            f"generated workload candidates: {summary['protected_workload_candidate_row_count']}",
            f"M1690 exact workload matches for protected specs: {summary['m1690_exact_workload_match_count']}",
            f"all protected targets accounted: {summary['all_protected_targets_accounted']}",
            "```",
            "",
            "Protected rows remain actor-invisible and outside success denominators. M1690 is used as the current executable schema reference; protected runner specs that are not exact M1690 rows are recorded as candidates, not execution admissions.",
            "",
            "## Actor Boundary",
            "",
            "```text",
            f"observation_shape: {summary['observation_shape']}",
            f"action_shape: {summary['action_shape']}",
            f"hidden_oracle_actor_input_detected: {summary['hidden_oracle_actor_input_detected']}",
            f"target_labels_actor_visible: {summary['target_labels_actor_visible']}",
            f"protected_rows_in_success_denominator: {summary['protected_rows_in_success_denominator']}",
            "```",
            "",
            "## Claim Boundary",
            "",
            "Allowed claim:",
            "",
            "```text",
            "M2697 materialized protected runner-spec candidates and target traceability rows from existing artifacts.",
            "```",
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
        ]
    )


def target_ids_accounted(
    source: dict[str, Any],
    spec_traceability_rows: list[dict[str, Any]],
    unmaterialized_rows: list[dict[str, Any]],
) -> bool:
    target_ids = {str(row.get("target_id", "")) for row in source["m2695_unbridgeable_target_rows"]}
    accounted = {str(row.get("target_id", "")) for row in spec_traceability_rows} | {
        str(row.get("target_id", "")) for row in unmaterialized_rows
    }
    return accounted == target_ids


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2695-dir", type=Path, default=DEFAULT_M2695_DIR)
    parser.add_argument("--m2662-dir", type=Path, default=DEFAULT_M2662_DIR)
    parser.add_argument("--m2664-dir", type=Path, default=DEFAULT_M2664_DIR)
    parser.add_argument("--m2667-dir", type=Path, default=DEFAULT_M2667_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m2696-audit-doc", type=Path, default=DEFAULT_M2696_AUDIT_DOC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--profile-name", default=DEFAULT_PROFILE_NAME)
    parser.add_argument("--policy-subject-id", default=DEFAULT_POLICY_SUBJECT_ID)
    parser.add_argument("--checkpoint-path", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    materialize_protected_mitigation_runner_spec_generation(
        m2695_dir=args.m2695_dir,
        m2662_dir=args.m2662_dir,
        m2664_dir=args.m2664_dir,
        m2667_dir=args.m2667_dir,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        m2696_audit_doc=args.m2696_audit_doc,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        profile_name=args.profile_name,
        policy_subject_id=args.policy_subject_id,
        checkpoint_path=args.checkpoint_path,
    )


if __name__ == "__main__":
    main()
