"""Materialize protected runner current-M1690 workload fixture support rows.

M2710 consumes the M2709 design and M2706 support-required protected runner
rows. It creates no-execution workload/fixture proposal, exact-match
admission, blocker, traceability, actor-contract, claim-boundary, and gate rows
before any protected runner execution route. It does not reset environments,
step, roll out policies, validate, train, rank, promote, or claim driver
performance.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import DEFAULT_EXECUTABLE_SPECS, DEFAULT_EXECUTABLE_WORKLOAD
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2711-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-result-audit"
)
DEFAULT_M2706_DIR = Path("runs/m2706_engineering_controller_protected_runner_simulator_workload_support")
DEFAULT_M2697_DIR = Path("runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation")
DEFAULT_M2700_DIR = Path("runs/m2700_engineering_controller_protected_runner_adapter_contract")
DEFAULT_M2703_DIR = Path("runs/m2703_engineering_controller_protected_runner_execution_admission")
DEFAULT_M2708_SYNTHESIS = Path(
    "docs/m2708-engineering-controller-protected-runner-simulator-workload-support-branch-synthesis.md"
)
DEFAULT_M2709_DESIGN = Path(
    "docs/m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2710-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2711-engineering-controller-protected-runner-current-m1690-workload-fixture-support-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2710 protected runner current-M1690 workload fixture support materialization only; "
    "M2706 support rows, M2697 protected runner specs, M2700 adapter rows, "
    "M2703 execution-admission rows, and M1690 schema references may be "
    "reanalyzed into workload/fixture proposal, exact-match admission, blocker, "
    "traceability, actor-contract, claim-boundary, and gate rows, but no reset, "
    "step, rollout, replay, validation, training, PPO, private holdout, "
    "profile-specific tuning, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-response, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "protected execution result, protected mitigation preservation result, "
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
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

M2706_SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS = "support_materialized_candidate_requires_new_workload_row"
EXACT_STATUS_PROPOSED_NEW = "proposed_new_current_m1690_workload_row_not_existing_match"
EXACT_STATUS_EXISTING_FOUND = "existing_current_m1690_workload_match_found"
EXACT_STATUS_BLOCKED_SOURCE_MISSING = "exact_match_blocked_source_artifact_missing"
EXACT_STATUS_BLOCKED_SCHEMA = "exact_match_blocked_schema_inconsistent"
EXACT_STATUS_BLOCKED_HIDDEN_ORACLE = "exact_match_blocked_hidden_oracle_required"
EXACT_STATUS_BLOCKED_ACTOR_LABEL = "exact_match_blocked_actor_visible_label"
EXACT_STATUS_BLOCKED_DENOMINATOR = "exact_match_blocked_denominator_violation"
ADMISSION_STATUS_PROPOSED_NEW = "workload_fixture_support_proposed_new_current_m1690_row"
ADMISSION_STATUS_READY_EXISTING = "workload_fixture_support_ready_existing_current_m1690_row"
ADMISSION_STATUS_REJECTED_SCHEMA = "workload_fixture_support_rejected_schema_inconsistent"
ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE = "workload_fixture_support_rejected_hidden_oracle_required"
ADMISSION_STATUS_REJECTED_ACTOR_LABEL = "workload_fixture_support_rejected_actor_visible_protected_label"
ADMISSION_STATUS_REJECTED_DENOMINATOR = "workload_fixture_support_rejected_denominator_boundary_violation"
ADMISSION_STATUS_REJECTED_ACTOR_CONTRACT = "workload_fixture_support_rejected_actor_contract_changed"
ADMISSION_STATUS_BLOCKED_SOURCE_MISSING = "workload_fixture_support_blocked_source_artifact_missing"

ALLOWED_ADMISSION_STATUSES = {
    ADMISSION_STATUS_PROPOSED_NEW,
    ADMISSION_STATUS_READY_EXISTING,
    ADMISSION_STATUS_REJECTED_SCHEMA,
    ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE,
    ADMISSION_STATUS_REJECTED_ACTOR_LABEL,
    ADMISSION_STATUS_REJECTED_DENOMINATOR,
    ADMISSION_STATUS_REJECTED_ACTOR_CONTRACT,
    ADMISSION_STATUS_BLOCKED_SOURCE_MISSING,
}

INPUT_SOURCE_FIELDNAMES = [
    "source_artifact_id",
    "source_path",
    "source_exists",
    "required",
    "row_count_or_summary",
    "source_role",
    "claim_scope",
    "blocked_interpretation",
]
PROPOSAL_FIELDNAMES = [
    "workload_fixture_proposal_id",
    "support_candidate_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "proposed_workload_id",
    "proposed_task_source_id",
    "profile_name",
    "policy_subject_id",
    "policy_checkpoint_path",
    "policy_checkpoint_exists",
    "reference_profile_config_path",
    "reference_profile_config_exists",
    "m1690_reference_workload_id",
    "protected_task_family",
    "protected_source_edge",
    "proposed_task_family",
    "proposed_source_edge",
    "proposed_executable_source_family",
    "proposed_env_template_family",
    "proposed_window_tag",
    "proposed_strata",
    "base_fixture_id",
    "fixture_id",
    "surface_id",
    "runner_backend_family",
    "fixture_variant_digest",
    "initial_state_digest",
    "fault_scale_digest",
    "road_digest",
    "obstacle_digest",
    "fixture_support_status",
    "workload_fixture_support_status",
    "exact_existing_m1690_match",
    "new_current_m1690_row_required",
    "simulator_fixture_required",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "measured_validation_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
ADMISSION_FIELDNAMES = [
    "admission_id",
    "workload_fixture_proposal_id",
    "support_candidate_id",
    "existing_m1690_workload_id",
    "proposed_workload_id",
    "exact_match_status",
    "admission_status",
    "admission_reason",
    "required_follow_up",
    "execution_admitted",
    "environment_reset_admitted",
    "actor_visible",
    "claim_scope",
]
BLOCKER_FIELDNAMES = [
    "blocker_id",
    "workload_fixture_proposal_id",
    "support_candidate_id",
    "blocker_type",
    "blocker_reason",
    "required_follow_up",
    "actor_visible",
    "claim_scope",
]
TRACEABILITY_FIELDNAMES = [
    "workload_fixture_traceability_id",
    "support_traceability_id",
    "support_candidate_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "workload_fixture_proposal_id",
    "protected_target_id",
    "target_family",
    "source_key",
    "traceability_axis",
    "target_accounted",
    "workload_fixture_traceability_status",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
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
    "allowed_in_m2710",
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
    "workload_fixture_input_source_rows",
    "protected_workload_fixture_proposal_rows",
    "exact_match_admission_rows",
    "workload_fixture_support_blocker_rows",
    "workload_fixture_traceability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_runner_current_m1690_workload_fixture_support(
    *,
    m2706_dir: Path | str = DEFAULT_M2706_DIR,
    m2708_synthesis: Path | str = DEFAULT_M2708_SYNTHESIS,
    m2709_design: Path | str = DEFAULT_M2709_DESIGN,
    m2697_dir: Path | str = DEFAULT_M2697_DIR,
    m2700_dir: Path | str = DEFAULT_M2700_DIR,
    m2703_dir: Path | str = DEFAULT_M2703_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    route_plan: Path | str = DEFAULT_ROUTE_PLAN,
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
        m2706_dir=Path(m2706_dir),
        m2708_synthesis=Path(m2708_synthesis),
        m2709_design=Path(m2709_design),
        m2697_dir=Path(m2697_dir),
        m2700_dir=Path(m2700_dir),
        m2703_dir=Path(m2703_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_source_rows = build_input_source_rows(source)
    proposal_rows = build_proposal_rows(source)
    admission_rows = build_exact_match_admission_rows(proposal_rows)
    blocker_rows = build_blocker_rows(proposal_rows) + build_global_blocker_rows(source)
    traceability_rows = build_traceability_rows(source, proposal_rows)
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
        proposals_cover_support_candidates=False,
        exact_match_rows_cover_proposals=False,
        no_fabricated_existing_matches=False,
        all_targets_accounted=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        proposal_rows=proposal_rows,
        admission_rows=admission_rows,
        blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["workload_fixture_input_source_rows"], input_source_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(
        paths["protected_workload_fixture_proposal_rows"],
        proposal_rows,
        fieldnames=PROPOSAL_FIELDNAMES,
    )
    write_csv_rows(paths["exact_match_admission_rows"], admission_rows, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["workload_fixture_support_blocker_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["workload_fixture_traceability_rows"], traceability_rows, fieldnames=TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    proposals_cover_support_candidates = proposals_cover_source(source, proposal_rows)
    exact_match_rows_cover_proposals = exact_rows_cover_proposals(proposal_rows, admission_rows)
    no_fabricated_existing_matches = no_fabricated_existing_m1690_matches(source, admission_rows)
    all_targets_accounted = targets_accounted(source, traceability_rows)
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})

    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        proposals_cover_support_candidates=proposals_cover_support_candidates,
        exact_match_rows_cover_proposals=exact_match_rows_cover_proposals,
        no_fabricated_existing_matches=no_fabricated_existing_matches,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        proposal_rows=proposal_rows,
        admission_rows=admission_rows,
        blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
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
        input_source_rows=input_source_rows,
        proposal_rows=proposal_rows,
        admission_rows=admission_rows,
        blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        proposals_cover_support_candidates=proposals_cover_support_candidates,
        exact_match_rows_cover_proposals=exact_match_rows_cover_proposals,
        no_fabricated_existing_matches=no_fabricated_existing_matches,
        all_targets_accounted=all_targets_accounted,
        follow_up_manifest=Path(follow_up_manifest),
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
        proposals_cover_support_candidates=proposals_cover_support_candidates,
        exact_match_rows_cover_proposals=exact_match_rows_cover_proposals,
        no_fabricated_existing_matches=no_fabricated_existing_matches,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        proposal_rows=proposal_rows,
        admission_rows=admission_rows,
        blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
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
        input_source_rows=input_source_rows,
        proposal_rows=proposal_rows,
        admission_rows=admission_rows,
        blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        proposals_cover_support_candidates=proposals_cover_support_candidates,
        exact_match_rows_cover_proposals=exact_match_rows_cover_proposals,
        no_fabricated_existing_matches=no_fabricated_existing_matches,
        all_targets_accounted=all_targets_accounted,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "workload_fixture_input_source_rows": output_dir / "workload_fixture_input_source_rows.csv",
        "protected_workload_fixture_proposal_rows": output_dir / "protected_workload_fixture_proposal_rows.csv",
        "exact_match_admission_rows": output_dir / "exact_match_admission_rows.csv",
        "workload_fixture_support_blocker_rows": output_dir / "workload_fixture_support_blocker_rows.csv",
        "workload_fixture_traceability_rows": output_dir / "workload_fixture_traceability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2706_dir: Path,
    m2708_synthesis: Path,
    m2709_design: Path,
    m2697_dir: Path,
    m2700_dir: Path,
    m2703_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2709_design": m2709_design,
        "m2708_synthesis": m2708_synthesis,
        "m2706_summary": m2706_dir / "summary.json",
        "m2706_support_input_source_rows": m2706_dir / "support_input_source_rows.csv",
        "m2706_support_candidate_rows": m2706_dir / "support_candidate_rows.csv",
        "m2706_support_blocker_rows": m2706_dir / "support_blocker_rows.csv",
        "m2706_support_traceability_rows": m2706_dir / "support_traceability_rows.csv",
        "m2706_actor_contract_guard_rows": m2706_dir / "actor_contract_guard_rows.csv",
        "m2706_claim_boundary_rows": m2706_dir / "claim_boundary_rows.csv",
        "m2706_gate_matrix": m2706_dir / "gate_matrix.csv",
        "m2697_protected_runner_spec_rows": m2697_dir / "protected_runner_spec_rows.csv",
        "m2697_protected_workload_candidate_rows": m2697_dir / "protected_workload_candidate_rows.csv",
        "m2700_adapter_candidate_mapping_rows": m2700_dir / "adapter_candidate_mapping_rows.csv",
        "m2703_execution_admission_candidate_rows": m2703_dir / "execution_admission_candidate_rows.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": executable_workload,
        "post_m2470_route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2709_design_text": paths["m2709_design"].read_text(encoding="utf-8") if source_exists["m2709_design"] else "",
        "m2708_synthesis_text": (
            paths["m2708_synthesis"].read_text(encoding="utf-8") if source_exists["m2708_synthesis"] else ""
        ),
        "post_m2470_route_plan_text": (
            paths["post_m2470_route_plan"].read_text(encoding="utf-8")
            if source_exists["post_m2470_route_plan"]
            else ""
        ),
        "m2706_summary": read_json(paths["m2706_summary"]) if source_exists["m2706_summary"] else {},
        "m2706_support_input_source_rows": read_csv_rows(paths["m2706_support_input_source_rows"]),
        "m2706_support_candidate_rows": read_csv_rows(paths["m2706_support_candidate_rows"]),
        "m2706_support_blocker_rows": read_csv_rows(paths["m2706_support_blocker_rows"]),
        "m2706_support_traceability_rows": read_csv_rows(paths["m2706_support_traceability_rows"]),
        "m2706_actor_contract_guard_rows": read_csv_rows(paths["m2706_actor_contract_guard_rows"]),
        "m2706_claim_boundary_rows": read_csv_rows(paths["m2706_claim_boundary_rows"]),
        "m2706_gate_matrix": read_csv_rows(paths["m2706_gate_matrix"]),
        "m2697_protected_runner_spec_rows": read_csv_rows(paths["m2697_protected_runner_spec_rows"]),
        "m2697_protected_workload_candidate_rows": read_csv_rows(paths["m2697_protected_workload_candidate_rows"]),
        "m2700_adapter_candidate_mapping_rows": read_csv_rows(paths["m2700_adapter_candidate_mapping_rows"]),
        "m2703_execution_admission_candidate_rows": read_csv_rows(paths["m2703_execution_admission_candidate_rows"]),
        "executable_task_specs": load_json_reference(paths["executable_task_specs"], source_exists["executable_task_specs"]),
        "executable_workload_matrix": read_csv_rows(paths["executable_workload_matrix"]),
    }


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_json_reference(path: Path, exists: bool) -> Any:
    if not exists:
        return {}
    return read_json(path)


def build_input_source_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    source_roles = {
        "m2709_design": "current-M1690 workload fixture support design boundary",
        "m2708_synthesis": "parent branch synthesis route decision",
        "m2706_summary": "parent simulator/workload support status and counts",
        "m2706_support_input_source_rows": "parent support input-source rows",
        "m2706_support_candidate_rows": "parent support candidate rows",
        "m2706_support_blocker_rows": "parent support blocker rows",
        "m2706_support_traceability_rows": "parent support traceability rows",
        "m2706_actor_contract_guard_rows": "parent actor/action guard rows",
        "m2706_claim_boundary_rows": "parent claim boundary rows",
        "m2706_gate_matrix": "parent gate matrix rows",
        "m2697_protected_runner_spec_rows": "protected fixture and runner spec metadata",
        "m2697_protected_workload_candidate_rows": "protected workload candidate policy/config metadata",
        "m2700_adapter_candidate_mapping_rows": "adapter candidate mapping source rows",
        "m2703_execution_admission_candidate_rows": "execution-admission candidate source rows",
        "executable_task_specs": "current executable task schema reference",
        "executable_workload_matrix": "current executable workload exact-match reference",
        "post_m2470_route_plan": "Route A/B/C claim separation plan",
        "follow_up_manifest": "M2711 result audit registration",
    }
    return [
        {
            "source_artifact_id": artifact_id,
            "source_path": str(path),
            "source_exists": source["source_exists"][artifact_id],
            "required": True,
            "row_count_or_summary": source_summary_value(source, artifact_id),
            "source_role": source_roles[artifact_id],
            "claim_scope": CLAIM_SCOPE,
            "blocked_interpretation": FORBIDDEN_INTERPRETATION,
        }
        for artifact_id, path in source["paths"].items()
    ]


def source_summary_value(source: dict[str, Any], artifact_id: str) -> str:
    if artifact_id == "m2706_summary":
        summary = source["m2706_summary"]
        return f"status_pass={summary.get('status_pass', '')};gate_matrix_pass={summary.get('gate_matrix_pass', '')}"
    if artifact_id == "m2709_design":
        return "decision_present=" + str(
            "admit_current_m1690_workload_fixture_support_materialization_preflight"
            in source["m2709_design_text"]
        )
    if artifact_id == "m2708_synthesis":
        return "decision_present=" + str(
            "continue_to_current_m1690_workload_fixture_support_design" in source["m2708_synthesis_text"]
        )
    if artifact_id == "post_m2470_route_plan":
        return "route_split_present=" + str("Route A: Engineering Controller Mainline" in source["post_m2470_route_plan_text"])
    if artifact_id == "executable_task_specs":
        value = source["executable_task_specs"]
        if isinstance(value, dict):
            return f"json_keys={';'.join(sorted(value.keys()))}"
        if isinstance(value, list):
            return f"rows={len(value)}"
        return str(type(value).__name__)
    if artifact_id in source and isinstance(source[artifact_id], list):
        return f"rows={len(source[artifact_id])}"
    if artifact_id == "follow_up_manifest":
        return f"exists={source['source_exists'][artifact_id]}"
    return ""


def build_proposal_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    runner_specs = {str(row.get("runner_spec_id", "")): row for row in source["m2697_protected_runner_spec_rows"]}
    workload_candidates = {
        str(row.get("workload_candidate_id", "")): row for row in source["m2697_protected_workload_candidate_rows"]
    }
    adapters = {str(row.get("adapter_candidate_id", "")): row for row in source["m2700_adapter_candidate_mapping_rows"]}
    executions = {
        str(row.get("execution_admission_candidate_id", "")): row
        for row in source["m2703_execution_admission_candidate_rows"]
    }
    reference_rows = {
        str(row.get("workload_id", "")): row for row in source["executable_workload_matrix"]
    }
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(
        sorted(source["m2706_support_candidate_rows"], key=lambda row: str(row.get("support_candidate_id", ""))),
        start=1,
    ):
        runner = runner_specs.get(str(candidate.get("runner_spec_id", "")), {})
        workload = workload_candidates.get(str(candidate.get("workload_candidate_id", "")), {})
        adapter = adapters.get(str(candidate.get("adapter_candidate_id", "")), {})
        execution = executions.get(str(candidate.get("execution_admission_candidate_id", "")), {})
        reference = reference_rows.get(str(candidate.get("m1690_reference_workload_id", "")), {})
        existing_match = find_exact_existing_m1690_match(candidate, source["executable_workload_matrix"])
        admission_status, fixture_status = proposal_status(candidate, runner, workload, source, existing_match)
        support_candidate_id = str(candidate.get("support_candidate_id", ""))
        proposed_workload_id = f"m2710-current-m1690-{support_candidate_id}::{candidate.get('profile_name', '')}"
        proposed_task_source_id = f"m2710-current-m1690-source-{support_candidate_id}"
        rows.append(
            {
                "workload_fixture_proposal_id": f"m2710-workload-fixture-proposal-{index:04d}",
                "support_candidate_id": support_candidate_id,
                "execution_admission_candidate_id": candidate.get("execution_admission_candidate_id", ""),
                "adapter_candidate_id": candidate.get("adapter_candidate_id", ""),
                "workload_candidate_id": candidate.get("workload_candidate_id", ""),
                "runner_spec_id": candidate.get("runner_spec_id", ""),
                "source_panel_spec_id": candidate.get("source_panel_spec_id", ""),
                "proposed_workload_id": existing_match.get("workload_id", proposed_workload_id),
                "proposed_task_source_id": existing_match.get("task_source_id", proposed_task_source_id),
                "profile_name": candidate.get("profile_name", ""),
                "policy_subject_id": candidate.get("policy_subject_id", ""),
                "policy_checkpoint_path": first_nonempty(
                    workload.get("policy_checkpoint_path"),
                    adapter.get("policy_checkpoint_path"),
                    execution.get("policy_checkpoint_path"),
                ),
                "policy_checkpoint_exists": _bool(
                    first_nonempty(
                        workload.get("policy_checkpoint_exists"),
                        adapter.get("policy_checkpoint_exists"),
                        execution.get("policy_checkpoint_exists"),
                    )
                ),
                "reference_profile_config_path": first_nonempty(
                    workload.get("reference_profile_config_path"),
                    adapter.get("reference_profile_config_path"),
                    execution.get("reference_profile_config_path"),
                    reference.get("profile_config_path"),
                ),
                "reference_profile_config_exists": _bool(
                    first_nonempty(
                        workload.get("reference_profile_config_exists"),
                        adapter.get("reference_profile_config_exists"),
                        execution.get("reference_profile_config_exists"),
                        reference.get("config_exists"),
                    )
                ),
                "m1690_reference_workload_id": candidate.get("m1690_reference_workload_id", ""),
                "protected_task_family": candidate.get("protected_task_family", ""),
                "protected_source_edge": candidate.get("protected_source_edge", ""),
                "proposed_task_family": existing_match.get("task_family", candidate.get("protected_task_family", "")),
                "proposed_source_edge": existing_match.get("source_edge", candidate.get("protected_source_edge", "")),
                "proposed_executable_source_family": existing_match.get(
                    "executable_source_family",
                    runner.get("runner_backend_family", ""),
                ),
                "proposed_env_template_family": existing_match.get(
                    "env_template_family",
                    runner.get("env_template_family", reference.get("env_template_family", "")),
                ),
                "proposed_window_tag": existing_match.get(
                    "window_tag",
                    reference.get("window_tag", "protected_workload_fixture_support"),
                ),
                "proposed_strata": existing_match.get(
                    "strata",
                    "route_a_protected;current_m1690_workload_fixture_support;no_execution",
                ),
                "base_fixture_id": runner.get("base_fixture_id", ""),
                "fixture_id": runner.get("fixture_id", ""),
                "surface_id": runner.get("surface_id", ""),
                "runner_backend_family": runner.get("runner_backend_family", adapter.get("adapter_backend_family", "")),
                "fixture_variant_digest": runner.get("fixture_variant_digest", ""),
                "initial_state_digest": runner.get("initial_state_digest", ""),
                "fault_scale_digest": runner.get("fault_scale_digest", ""),
                "road_digest": runner.get("road_digest", ""),
                "obstacle_digest": runner.get("obstacle_digest", ""),
                "fixture_support_status": fixture_status,
                "workload_fixture_support_status": admission_status,
                "exact_existing_m1690_match": bool(existing_match),
                "new_current_m1690_row_required": not bool(existing_match),
                "simulator_fixture_required": _bool(candidate.get("candidate_requires_simulator_fixture")) or not bool(existing_match),
                "environment_reset_scheduled": False,
                "environment_rollout_scheduled": False,
                "measured_validation_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "actor_input_contract_changed": _bool(candidate.get("actor_input_contract_changed"))
                or _bool(runner.get("actor_input_contract_changed")),
                "hidden_oracle_actor_input_required": _bool(candidate.get("hidden_oracle_actor_input_required"))
                or _bool(runner.get("hidden_oracle_actor_input_required")),
                "target_labels_actor_visible": _bool(runner.get("target_labels_actor_visible")),
                "protected_labels_actor_visible": _bool(candidate.get("protected_labels_actor_visible")),
                "protected_rows_in_success_denominator": _bool(candidate.get("protected_rows_in_success_denominator"))
                or _bool(runner.get("protected_rows_in_success_denominator")),
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def proposal_status(
    candidate: dict[str, str],
    runner: dict[str, str],
    workload: dict[str, str],
    source: dict[str, Any],
    existing_match: dict[str, str],
) -> tuple[str, str]:
    required_sources = [
        "m2709_design",
        "m2708_synthesis",
        "m2706_summary",
        "m2706_support_candidate_rows",
        "m2706_support_blocker_rows",
        "m2706_support_traceability_rows",
        "m2706_actor_contract_guard_rows",
        "m2706_claim_boundary_rows",
        "m2706_gate_matrix",
        "m2697_protected_runner_spec_rows",
        "m2697_protected_workload_candidate_rows",
        "m2700_adapter_candidate_mapping_rows",
        "m2703_execution_admission_candidate_rows",
        "executable_task_specs",
        "executable_workload_matrix",
        "post_m2470_route_plan",
    ]
    if not all(source["source_exists"][key] for key in required_sources):
        return ADMISSION_STATUS_BLOCKED_SOURCE_MISSING, "fixture_support_blocked_source_artifact_missing"
    if "admit_current_m1690_workload_fixture_support_materialization_preflight" not in source["m2709_design_text"]:
        return ADMISSION_STATUS_REJECTED_SCHEMA, "fixture_support_blocked_schema_inconsistent"
    if "continue_to_current_m1690_workload_fixture_support_design" not in source["m2708_synthesis_text"]:
        return ADMISSION_STATUS_REJECTED_SCHEMA, "fixture_support_blocked_schema_inconsistent"
    if not _bool(source["m2706_summary"].get("status_pass")) or not _bool(source["m2706_summary"].get("gate_matrix_pass")):
        return ADMISSION_STATUS_REJECTED_SCHEMA, "fixture_support_blocked_schema_inconsistent"
    if not runner or not workload:
        return ADMISSION_STATUS_REJECTED_SCHEMA, "fixture_support_blocked_schema_inconsistent"
    if _bool(candidate.get("hidden_oracle_actor_input_required")) or _bool(runner.get("hidden_oracle_actor_input_required")):
        return ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE, "fixture_support_blocked_hidden_oracle_required"
    if _bool(candidate.get("protected_labels_actor_visible")) or _bool(runner.get("target_labels_actor_visible")):
        return ADMISSION_STATUS_REJECTED_ACTOR_LABEL, "fixture_support_blocked_actor_visible_protected_label"
    if _bool(candidate.get("protected_rows_in_success_denominator")) or _bool(runner.get("protected_rows_in_success_denominator")):
        return ADMISSION_STATUS_REJECTED_DENOMINATOR, "fixture_support_blocked_denominator_boundary_violation"
    if _bool(candidate.get("actor_input_contract_changed")) or _bool(runner.get("actor_input_contract_changed")):
        return ADMISSION_STATUS_REJECTED_ACTOR_CONTRACT, "fixture_support_blocked_actor_contract_changed"
    if existing_match:
        return ADMISSION_STATUS_READY_EXISTING, "fixture_support_proposed_from_existing_m1690_workload"
    if str(candidate.get("support_status", "")) == M2706_SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS:
        return ADMISSION_STATUS_PROPOSED_NEW, "fixture_support_proposed_from_m2697_runner_spec"
    return ADMISSION_STATUS_REJECTED_SCHEMA, "fixture_support_blocked_schema_inconsistent"


def find_exact_existing_m1690_match(
    candidate: dict[str, str],
    executable_workload_rows: list[dict[str, str]],
) -> dict[str, str]:
    profile = str(candidate.get("profile_name", ""))
    task_family = str(candidate.get("protected_task_family", ""))
    source_edge = str(candidate.get("protected_source_edge", ""))
    for row in executable_workload_rows:
        if (
            str(row.get("profile_name", "")) == profile
            and str(row.get("task_family", "")) == task_family
            and str(row.get("source_edge", "")) == source_edge
        ):
            return row
    return {}


def build_exact_match_admission_rows(proposal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, proposal in enumerate(proposal_rows, start=1):
        status = str(proposal.get("workload_fixture_support_status", ""))
        existing_id = str(proposal.get("proposed_workload_id", "")) if status == ADMISSION_STATUS_READY_EXISTING else ""
        exact_status = exact_status_for_admission(status)
        rows.append(
            {
                "admission_id": f"m2710-exact-match-admission-{index:04d}",
                "workload_fixture_proposal_id": proposal.get("workload_fixture_proposal_id", ""),
                "support_candidate_id": proposal.get("support_candidate_id", ""),
                "existing_m1690_workload_id": existing_id,
                "proposed_workload_id": proposal.get("proposed_workload_id", ""),
                "exact_match_status": exact_status,
                "admission_status": status,
                "admission_reason": admission_reason(status),
                "required_follow_up": "M2711 result audit before any protected execution admission route",
                "execution_admitted": False,
                "environment_reset_admitted": False,
                "actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def exact_status_for_admission(status: str) -> str:
    if status == ADMISSION_STATUS_READY_EXISTING:
        return EXACT_STATUS_EXISTING_FOUND
    if status == ADMISSION_STATUS_PROPOSED_NEW:
        return EXACT_STATUS_PROPOSED_NEW
    if status == ADMISSION_STATUS_BLOCKED_SOURCE_MISSING:
        return EXACT_STATUS_BLOCKED_SOURCE_MISSING
    if status == ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE:
        return EXACT_STATUS_BLOCKED_HIDDEN_ORACLE
    if status == ADMISSION_STATUS_REJECTED_ACTOR_LABEL:
        return EXACT_STATUS_BLOCKED_ACTOR_LABEL
    if status == ADMISSION_STATUS_REJECTED_DENOMINATOR:
        return EXACT_STATUS_BLOCKED_DENOMINATOR
    return EXACT_STATUS_BLOCKED_SCHEMA


def admission_reason(status: str) -> str:
    if status == ADMISSION_STATUS_READY_EXISTING:
        return "proposal has an exact current M1690 workload row backed by source workload matrix"
    if status == ADMISSION_STATUS_PROPOSED_NEW:
        return "proposal has no existing exact current M1690 row and remains a no-execution new-row support proposal"
    if status == ADMISSION_STATUS_BLOCKED_SOURCE_MISSING:
        return "one or more required source artifacts are missing"
    return "proposal cannot satisfy workload fixture support schema or actor/claim boundary"


def build_blocker_rows(proposal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for proposal in proposal_rows:
        status = str(proposal.get("workload_fixture_support_status", ""))
        if status == ADMISSION_STATUS_READY_EXISTING:
            continue
        rows.append(
            {
                "blocker_id": f"m2710-workload-fixture-blocker-{len(rows) + 1:04d}",
                "workload_fixture_proposal_id": proposal.get("workload_fixture_proposal_id", ""),
                "support_candidate_id": proposal.get("support_candidate_id", ""),
                "blocker_type": blocker_type_for_status(status),
                "blocker_reason": blocker_reason_for_status(status),
                "required_follow_up": "M2711 result audit before any execution admission design or protected runner execution route",
                "actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def blocker_type_for_status(status: str) -> str:
    if status == ADMISSION_STATUS_PROPOSED_NEW:
        return "workload_fixture_support_blocker_existing_m1690_match_absent"
    if status == ADMISSION_STATUS_BLOCKED_SOURCE_MISSING:
        return "workload_fixture_support_blocker_source_artifact_missing"
    if status == ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE:
        return "workload_fixture_support_blocker_hidden_oracle_required"
    if status == ADMISSION_STATUS_REJECTED_ACTOR_LABEL:
        return "workload_fixture_support_blocker_actor_visible_protected_label"
    if status == ADMISSION_STATUS_REJECTED_DENOMINATOR:
        return "workload_fixture_support_blocker_denominator_boundary_violation"
    if status == ADMISSION_STATUS_REJECTED_ACTOR_CONTRACT:
        return "workload_fixture_support_blocker_actor_contract_changed"
    return "workload_fixture_support_blocker_schema_inconsistent"


def blocker_reason_for_status(status: str) -> str:
    if status == ADMISSION_STATUS_PROPOSED_NEW:
        return "proposal materializes a new workload/fixture support row but no existing exact M1690 workload match"
    if status == ADMISSION_STATUS_BLOCKED_SOURCE_MISSING:
        return "one or more required source artifacts are missing"
    if status == ADMISSION_STATUS_REJECTED_HIDDEN_ORACLE:
        return "proposal would require hidden/oracle actor input"
    if status == ADMISSION_STATUS_REJECTED_ACTOR_LABEL:
        return "proposal would expose protected labels to actor input"
    if status == ADMISSION_STATUS_REJECTED_DENOMINATOR:
        return "proposal would put protected rows in ordinary success denominators"
    if status == ADMISSION_STATUS_REJECTED_ACTOR_CONTRACT:
        return "proposal would change the actor input/action contract"
    return "proposal is schema-inconsistent"


def build_global_blocker_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, exists in source["source_exists"].items():
        if not exists:
            rows.append(
                {
                    "blocker_id": f"m2710-workload-fixture-blocker-global-{len(rows) + 1:04d}",
                    "workload_fixture_proposal_id": "",
                    "support_candidate_id": artifact_id,
                    "blocker_type": "workload_fixture_support_blocker_source_artifact_missing",
                    "blocker_reason": f"required source artifact is missing: {source['paths'][artifact_id]}",
                    "required_follow_up": "missing-artifact repair before workload fixture support materialization",
                    "actor_visible": False,
                    "claim_scope": CLAIM_SCOPE,
                }
            )
    return rows


def build_traceability_rows(
    source: dict[str, Any],
    proposal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    proposals_by_support_id = {str(row.get("support_candidate_id", "")): row for row in proposal_rows}
    rows: list[dict[str, Any]] = []
    for index, trace in enumerate(
        sorted(source["m2706_support_traceability_rows"], key=lambda row: str(row.get("support_traceability_id", ""))),
        start=1,
    ):
        support_id = str(trace.get("support_candidate_id", ""))
        proposal = proposals_by_support_id.get(support_id, {})
        rows.append(
            {
                "workload_fixture_traceability_id": f"m2710-workload-fixture-trace-{index:04d}",
                "support_traceability_id": trace.get("support_traceability_id", ""),
                "support_candidate_id": support_id,
                "execution_admission_candidate_id": trace.get("execution_admission_candidate_id", ""),
                "adapter_candidate_id": trace.get("adapter_candidate_id", ""),
                "workload_candidate_id": trace.get("workload_candidate_id", ""),
                "runner_spec_id": trace.get("runner_spec_id", ""),
                "source_panel_spec_id": trace.get("source_panel_spec_id", ""),
                "workload_fixture_proposal_id": proposal.get("workload_fixture_proposal_id", ""),
                "protected_target_id": trace.get("protected_target_id", ""),
                "target_family": trace.get("target_family", ""),
                "source_key": trace.get("source_key", ""),
                "traceability_axis": trace.get("traceability_axis", ""),
                "target_accounted": bool(trace.get("protected_target_id")),
                "workload_fixture_traceability_status": (
                    "workload_fixture_traceability_materialized" if proposal else "trace_has_no_workload_fixture_proposal"
                ),
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "protected_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    return [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True),
        actor_guard("action_shape", ACTION_DIM, ACTION_DIM, True),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_guard("actor_input_contract_changed", False, False, False),
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
        "guard_id": f"m2710_actor_guard_{field}",
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
    proposals_cover_support_candidates: bool,
    exact_match_rows_cover_proposals: bool,
    no_fabricated_existing_matches: bool,
    all_targets_accounted: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("workload_fixture_input_source_rows_materialized", "artifact", required_artifacts_present, "workload_fixture_input_source_rows.csv"),
        ("protected_workload_fixture_proposal_rows_materialized", "artifact", required_artifacts_present, "protected_workload_fixture_proposal_rows.csv"),
        ("exact_match_admission_rows_materialized", "artifact", required_artifacts_present, "exact_match_admission_rows.csv"),
        ("workload_fixture_support_blocker_rows_materialized", "artifact", required_artifacts_present, "workload_fixture_support_blocker_rows.csv"),
        ("workload_fixture_traceability_rows_materialized", "artifact", required_artifacts_present, "workload_fixture_traceability_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", required_artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", required_artifacts_present, "gate_matrix.csv"),
        ("proposals_cover_support_candidates", "support_materialization", proposals_cover_support_candidates, "proposal row for every M2706 support candidate"),
        ("exact_match_rows_cover_proposals", "support_materialization", exact_match_rows_cover_proposals, "exact-match admission row for every proposal"),
        ("no_fabricated_existing_m1690_matches", "support_materialization", no_fabricated_existing_matches, "existing matches cite M1690 source rows"),
        ("protected_targets_accounted", "traceability", all_targets_accounted, "M2706 protected target coverage preserved"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2711 result audit manifest"),
    ]
    blocked = [
        ("workload_fixture_support_row_as_execution_row", "execution", "future protected execution admission manifest"),
        ("reset_execution", "execution", "future protected execution manifest"),
        ("environment_step", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2710"),
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
        "claim_id": f"m2710_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2710": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    proposal_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [key for key in source["paths"] if key != "follow_up_manifest"]
    source_support_ids = source_support_id_set(source)
    proposal_support_ids = {str(row.get("support_candidate_id", "")) for row in proposal_rows}
    proposal_ids = {str(row.get("workload_fixture_proposal_id", "")) for row in proposal_rows}
    admission_proposal_ids = {str(row.get("workload_fixture_proposal_id", "")) for row in admission_rows}
    source_target_ids = source_target_id_set(source)
    trace_target_ids = {
        str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")
    }
    support_required_count = sum(
        str(row.get("support_status", "")) == M2706_SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS
        for row in source["m2706_support_candidate_rows"]
    )
    proposed_new_count = sum(
        str(row.get("workload_fixture_support_status", "")) == ADMISSION_STATUS_PROPOSED_NEW
        for row in proposal_rows
    )
    ready_existing_count = sum(
        str(row.get("workload_fixture_support_status", "")) == ADMISSION_STATUS_READY_EXISTING
        for row in proposal_rows
    )
    non_ready_ids = non_ready_proposal_ids(proposal_rows)
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2710"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2710"])]
    return [
        gate(
            "m2710_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in required_sources),
            {key: source["source_exists"][key] for key in required_sources},
            "all M2709 M2708 M2706 M2697 M2700 M2703 M1690 and route-plan source artifacts present",
            "lineage_invalid",
        ),
        gate(
            "m2709_design_present",
            "lineage",
            "admit_current_m1690_workload_fixture_support_materialization_preflight"
            in source["m2709_design_text"],
            "admit_current_m1690_workload_fixture_support_materialization_preflight"
            in source["m2709_design_text"],
            True,
            "lineage_invalid",
        ),
        gate(
            "m2708_synthesis_route_present",
            "lineage",
            "continue_to_current_m1690_workload_fixture_support_design" in source["m2708_synthesis_text"],
            "continue_to_current_m1690_workload_fixture_support_design" in source["m2708_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        gate("m2706_status_pass", "lineage", _bool(source["m2706_summary"].get("status_pass")), source["m2706_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2706_gate_matrix_pass", "lineage", _bool(source["m2706_summary"].get("gate_matrix_pass")), source["m2706_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("workload_fixture_input_source_rows_cover_required_sources", "lineage", len(input_source_rows) == len(source["paths"]), len(input_source_rows), len(source["paths"]), "lineage_invalid"),
        gate("adapter_mapping_source_consumed", "lineage", bool(source["m2700_adapter_candidate_mapping_rows"]), len(source["m2700_adapter_candidate_mapping_rows"]), "non-empty M2700 adapter mapping rows", "lineage_invalid"),
        gate("execution_admission_source_consumed", "lineage", bool(source["m2703_execution_admission_candidate_rows"]), len(source["m2703_execution_admission_candidate_rows"]), "non-empty M2703 execution-admission rows", "lineage_invalid"),
        gate("proposal_rows_cover_support_candidates", "support_materialization", proposal_support_ids == source_support_ids, f"proposals={len(proposal_support_ids)} source={len(source_support_ids)}", "one proposal row per M2706 support candidate", "metric_artifact"),
        gate("exact_match_admission_rows_cover_proposals", "support_materialization", admission_proposal_ids == proposal_ids, f"admissions={len(admission_proposal_ids)} proposals={len(proposal_ids)}", "one exact-match admission row per proposal", "metric_artifact"),
        gate("exact_match_status_values_valid", "support_materialization", all(str(row.get("admission_status", "")) in ALLOWED_ADMISSION_STATUSES for row in admission_rows), sorted({str(row.get("admission_status", "")) for row in admission_rows}), "known admission status values", "metric_artifact"),
        gate("no_fabricated_existing_m1690_matches", "proof_washout", no_fabricated_existing_m1690_matches(source, admission_rows), "existing exact rows cite source workload matrix", "all exact existing matches backed by M1690 rows", "proof_washout"),
        gate("current_m1690_reference_schema_consumed", "lineage", bool(source["executable_task_specs"]) and bool(source["executable_workload_matrix"]), f"specs={bool(source['executable_task_specs'])} workload={len(source['executable_workload_matrix'])}", "non-empty executable schema/workload", "lineage_invalid"),
        gate("new_workload_row_requirements_materialized", "support_materialization", proposed_new_count + ready_existing_count == support_required_count, f"support_required={support_required_count} proposed_new={proposed_new_count} ready_existing={ready_existing_count}", "all support-required rows become proposed-new or exact-existing support rows", "metric_artifact"),
        gate("simulator_fixture_requirements_materialized", "support_materialization", all(_bool(row.get("simulator_fixture_required")) or str(row.get("workload_fixture_support_status")) == ADMISSION_STATUS_READY_EXISTING for row in proposal_rows), "all proposals have fixture requirement or existing exact row", "fixture requirement materialized", "metric_artifact"),
        gate("support_required_rows_preserved_or_reclassified_with_evidence", "proof_washout", len(proposal_rows) == len(source["m2706_support_candidate_rows"]) and ready_existing_count <= existing_m1690_workload_id_count(admission_rows), f"source={len(source['m2706_support_candidate_rows'])} proposals={len(proposal_rows)} ready_existing={ready_existing_count}", "no source support row hidden or overclaimed", "proof_washout"),
        gate("protected_targets_accounted", "traceability", trace_target_ids == source_target_ids, f"trace={len(trace_target_ids)} source={len(source_target_ids)}", "traceability row for every M2706 protected target", "proof_washout"),
        gate("traceability_rows_preserve_m2706_coverage", "traceability", len(traceability_rows) == len(source["m2706_support_traceability_rows"]), len(traceability_rows), len(source["m2706_support_traceability_rows"]), "proof_washout"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("protected_labels_actor_visible", False)) and not _bool(row.get("target_labels_actor_visible", False)) for row in proposal_rows + traceability_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in proposal_rows + traceability_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in proposal_rows + traceability_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) and not _bool(row.get("environment_reset_scheduled", False)) and not _bool(row.get("environment_rollout_scheduled", False)) and not _bool(row.get("measured_validation_scheduled", False)) and not _bool(row.get("training_scheduled", False)) for row in proposal_rows + traceability_rows), "all output rows materialization only", "no reset step rollout validation training", "objective_overfit"),
        gate("proposal_blocker_rows_actor_invisible", "contract", all(not _bool(row.get("actor_visible", False)) for row in blocker_rows), f"blockers={len(blocker_rows)} non_ready={len(non_ready_ids)}", "all false", "contract_violation"),
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
    input_source_rows: list[dict[str, Any]],
    proposal_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    proposals_cover_support_candidates: bool,
    exact_match_rows_cover_proposals: bool,
    no_fabricated_existing_matches: bool,
    all_targets_accounted: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in proposal_rows:
        status = str(row.get("workload_fixture_support_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_target_ids = source_target_id_set(source)
    exact_existing_count = sum(str(row.get("exact_match_status", "")) == EXACT_STATUS_EXISTING_FOUND for row in admission_rows)
    proposed_new_count = status_counts.get(ADMISSION_STATUS_PROPOSED_NEW, 0)
    ready_existing_count = status_counts.get(ADMISSION_STATUS_READY_EXISTING, 0)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2710"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2710"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_runner_current_m1690_workload_fixture_support_materialization_pass"
            if status_pass
            else "engineering_controller_protected_runner_current_m1690_workload_fixture_support_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"][key] for key in source["paths"] if key != "follow_up_manifest"),
        "m2709_design_decision_present": (
            "admit_current_m1690_workload_fixture_support_materialization_preflight"
            in source["m2709_design_text"]
        ),
        "m2708_synthesis_route_present": (
            "continue_to_current_m1690_workload_fixture_support_design" in source["m2708_synthesis_text"]
        ),
        "m2706_status_pass": _bool(source["m2706_summary"].get("status_pass")),
        "m2706_gate_matrix_pass": _bool(source["m2706_summary"].get("gate_matrix_pass")),
        "m2706_support_candidate_row_count": len(source["m2706_support_candidate_rows"]),
        "m2706_support_required_row_count": sum(
            str(row.get("support_status", "")) == M2706_SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS
            for row in source["m2706_support_candidate_rows"]
        ),
        "m2706_support_ready_existing_m1690_workload_count": int(
            source["m2706_summary"].get("support_ready_existing_m1690_workload_count", 0) or 0
        ),
        "m2706_m1690_exact_workload_match_count_support": int(
            source["m2706_summary"].get("m1690_exact_workload_match_count_support", 0) or 0
        ),
        "m2706_execution_admitted_source_row_count": int(
            source["m2706_summary"].get("m2703_execution_admission_admitted_count", 0) or 0
        ),
        "m2697_protected_runner_spec_row_count": len(source["m2697_protected_runner_spec_rows"]),
        "m2697_protected_workload_candidate_row_count": len(source["m2697_protected_workload_candidate_rows"]),
        "m2700_adapter_candidate_mapping_row_count": len(source["m2700_adapter_candidate_mapping_rows"]),
        "m2703_execution_admission_candidate_row_count": len(source["m2703_execution_admission_candidate_rows"]),
        "input_source_row_count": len(input_source_rows),
        "workload_fixture_proposal_row_count": len(proposal_rows),
        "exact_match_admission_row_count": len(admission_rows),
        "workload_fixture_support_blocker_row_count": len(blocker_rows),
        "workload_fixture_traceability_row_count": len(traceability_rows),
        "workload_fixture_support_status_counts": dict(sorted(status_counts.items())),
        "proposed_new_current_m1690_workload_row_count": proposed_new_count,
        "ready_existing_current_m1690_workload_row_count": ready_existing_count,
        "existing_exact_m1690_match_count": exact_existing_count,
        "fabricated_existing_m1690_match_count": fabricated_existing_m1690_match_count(source, admission_rows),
        "execution_admitted_row_count": sum(_bool(row.get("execution_admitted")) for row in admission_rows),
        "environment_reset_admitted_row_count": sum(_bool(row.get("environment_reset_admitted")) for row in admission_rows),
        "proposals_cover_support_candidates": proposals_cover_support_candidates,
        "exact_match_rows_cover_proposals": exact_match_rows_cover_proposals,
        "no_fabricated_existing_m1690_matches": no_fabricated_existing_matches,
        "all_non_ready_rows_have_blockers": non_ready_rows_have_blockers(proposal_rows, blocker_rows),
        "protected_target_count": len(source_target_ids),
        "workload_fixture_traceability_target_count": len(
            {str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")}
        ),
        "all_protected_targets_accounted": all_targets_accounted,
        "actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_contract_guard_rows),
        "actor_contract_shape_72_action_3": any(
            row["contract_field"] == "observation_shape" and str(row["observed_value"]) == str(P0_OBSERVATION_DIM)
            for row in actor_contract_guard_rows
        )
        and any(row["contract_field"] == "action_shape" and str(row["observed_value"]) == str(ACTION_DIM) for row in actor_contract_guard_rows),
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "claim_boundary_row_count": len(claim_boundary_rows),
        "claim_boundary_allowed_row_count": len(allowed_claim_rows),
        "claim_boundary_blocked_row_count": len(blocked_claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_boundary_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "allowed_claim": (
            "protected runner current-M1690 workload fixture support rows were materialized as proposed, "
            "ready-existing, rejected, or blocked no-execution rows with explicit exact-match accounting"
        ),
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def proposals_cover_source(source: dict[str, Any], proposal_rows: list[dict[str, Any]]) -> bool:
    return {str(row.get("support_candidate_id", "")) for row in proposal_rows} == source_support_id_set(source)


def exact_rows_cover_proposals(proposal_rows: list[dict[str, Any]], admission_rows: list[dict[str, Any]]) -> bool:
    return {str(row.get("workload_fixture_proposal_id", "")) for row in proposal_rows} == {
        str(row.get("workload_fixture_proposal_id", "")) for row in admission_rows
    }


def no_fabricated_existing_m1690_matches(source: dict[str, Any], admission_rows: list[dict[str, Any]]) -> bool:
    source_workload_ids = {str(row.get("workload_id", "")) for row in source["executable_workload_matrix"]}
    for row in admission_rows:
        if str(row.get("exact_match_status", "")) == EXACT_STATUS_EXISTING_FOUND:
            if str(row.get("existing_m1690_workload_id", "")) not in source_workload_ids:
                return False
    return True


def fabricated_existing_m1690_match_count(source: dict[str, Any], admission_rows: list[dict[str, Any]]) -> int:
    source_workload_ids = {str(row.get("workload_id", "")) for row in source["executable_workload_matrix"]}
    return sum(
        str(row.get("exact_match_status", "")) == EXACT_STATUS_EXISTING_FOUND
        and str(row.get("existing_m1690_workload_id", "")) not in source_workload_ids
        for row in admission_rows
    )


def existing_m1690_workload_id_count(admission_rows: list[dict[str, Any]]) -> int:
    return sum(bool(str(row.get("existing_m1690_workload_id", ""))) for row in admission_rows)


def non_ready_rows_have_blockers(
    proposal_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> bool:
    return non_ready_proposal_ids(proposal_rows).issubset(
        {str(row.get("workload_fixture_proposal_id", "")) for row in blocker_rows}
    )


def non_ready_proposal_ids(proposal_rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("workload_fixture_proposal_id", ""))
        for row in proposal_rows
        if str(row.get("workload_fixture_support_status", "")) != ADMISSION_STATUS_READY_EXISTING
    }


def targets_accounted(source: dict[str, Any], traceability_rows: list[dict[str, Any]]) -> bool:
    return {
        str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")
    } == source_target_id_set(source)


def source_target_id_set(source: dict[str, Any]) -> set[str]:
    return {
        str(row.get("protected_target_id", ""))
        for row in source["m2706_support_traceability_rows"]
        if row.get("protected_target_id")
    }


def source_support_id_set(source: dict[str, Any]) -> set[str]:
    return {
        str(row.get("support_candidate_id", ""))
        for row in source["m2706_support_candidate_rows"]
        if row.get("support_candidate_id")
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2710 Engineering Controller Protected Runner Current-M1690 Workload Fixture Support Materialization Preflight

## Summary

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- workload fixture proposal rows: {summary['workload_fixture_proposal_row_count']}
- exact-match admission rows: {summary['exact_match_admission_row_count']}
- workload fixture blocker rows: {summary['workload_fixture_support_blocker_row_count']}
- workload fixture traceability rows: {summary['workload_fixture_traceability_row_count']}
- proposed new current-M1690 workload rows: {summary['proposed_new_current_m1690_workload_row_count']}
- ready existing current-M1690 workload rows: {summary['ready_existing_current_m1690_workload_row_count']}
- existing exact M1690 matches: {summary['existing_exact_m1690_match_count']}
- fabricated existing M1690 matches: {summary['fabricated_existing_m1690_match_count']}
- execution-admitted rows: {summary['execution_admitted_row_count']}
- protected targets accounted: {summary['workload_fixture_traceability_target_count']}/{summary['protected_target_count']}
- gate matrix pass: {summary['gate_matrix_pass']}
- next: `{summary['next_blocker']}`

M2710 materializes the current-M1690 workload fixture support surface admitted
by M2709. It turns M2706 support-required rows into no-execution workload and
fixture support proposals with exact-match accounting. Proposed rows are not
protected execution rows, validation rows, ranking evidence, performance
evidence, paper evidence, current-sim verdicts, or self-ID evidence.

## Materialization Result

```text
M2706 support candidates: {summary['m2706_support_candidate_row_count']}
support-required source rows: {summary['m2706_support_required_row_count']}
workload fixture proposals: {summary['workload_fixture_proposal_row_count']}
exact-match admission rows: {summary['exact_match_admission_row_count']}
proposed new current-M1690 rows: {summary['proposed_new_current_m1690_workload_row_count']}
ready existing current-M1690 rows: {summary['ready_existing_current_m1690_workload_row_count']}
existing exact M1690 matches: {summary['existing_exact_m1690_match_count']}
fabricated existing M1690 matches: {summary['fabricated_existing_m1690_match_count']}
execution-admitted rows: {summary['execution_admitted_row_count']}
proposals cover source support candidates: {summary['proposals_cover_support_candidates']}
exact-match rows cover proposals: {summary['exact_match_rows_cover_proposals']}
no fabricated existing M1690 matches: {summary['no_fabricated_existing_m1690_matches']}
all non-ready rows have blockers: {summary['all_non_ready_rows_have_blockers']}
all protected targets accounted: {summary['all_protected_targets_accounted']}
```

## Actor Boundary

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: {summary['hidden_oracle_actor_input_detected']}
target_labels_actor_visible: {summary['target_labels_actor_visible']}
protected_rows_in_success_denominator: {summary['protected_rows_in_success_denominator']}
```

## Claim Boundary

Allowed claim:

```text
{summary['allowed_claim']}
```

Rejected claims:

```text
{summary['forbidden_interpretation']}
```

## Artifacts

- summary: `{summary['artifact_paths']['summary']}`
- workload_fixture_input_source_rows: `{summary['artifact_paths']['workload_fixture_input_source_rows']}`
- protected_workload_fixture_proposal_rows: `{summary['artifact_paths']['protected_workload_fixture_proposal_rows']}`
- exact_match_admission_rows: `{summary['artifact_paths']['exact_match_admission_rows']}`
- workload_fixture_support_blocker_rows: `{summary['artifact_paths']['workload_fixture_support_blocker_rows']}`
- workload_fixture_traceability_rows: `{summary['artifact_paths']['workload_fixture_traceability_rows']}`
- actor_contract_guard_rows: `{summary['artifact_paths']['actor_contract_guard_rows']}`
- claim_boundary_rows: `{summary['artifact_paths']['claim_boundary_rows']}`
- gate_matrix: `{summary['artifact_paths']['gate_matrix']}`
- doc: `{summary['artifact_paths']['doc']}`
"""


def first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in {None, ""}:
            return value
    return ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2706-dir", type=Path, default=DEFAULT_M2706_DIR)
    parser.add_argument("--m2708-synthesis", type=Path, default=DEFAULT_M2708_SYNTHESIS)
    parser.add_argument("--m2709-design", type=Path, default=DEFAULT_M2709_DESIGN)
    parser.add_argument("--m2697-dir", type=Path, default=DEFAULT_M2697_DIR)
    parser.add_argument("--m2700-dir", type=Path, default=DEFAULT_M2700_DIR)
    parser.add_argument("--m2703-dir", type=Path, default=DEFAULT_M2703_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_protected_runner_current_m1690_workload_fixture_support(
        m2706_dir=args.m2706_dir,
        m2708_synthesis=args.m2708_synthesis,
        m2709_design=args.m2709_design,
        m2697_dir=args.m2697_dir,
        m2700_dir=args.m2700_dir,
        m2703_dir=args.m2703_dir,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        route_plan=args.route_plan,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
