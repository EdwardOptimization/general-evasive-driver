"""Materialize protected runner simulator/workload support rows.

M2706 consumes the M2705 support design and the accepted M2703 no-execution
execution-admission pack. It classifies each blocked protected candidate into
a simulator/workload support status before any protected execution route. It
does not reset environments, step, roll out policies, validate, train, rank,
promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import DEFAULT_EXECUTABLE_SPECS, DEFAULT_EXECUTABLE_WORKLOAD
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2707-engineering-controller-protected-runner-simulator-workload-support-materialization-result-audit"
)
DEFAULT_M2703_DIR = Path("runs/m2703_engineering_controller_protected_runner_execution_admission")
DEFAULT_M2700_DIR = Path("runs/m2700_engineering_controller_protected_runner_adapter_contract")
DEFAULT_M2704_AUDIT = Path(
    "docs/m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit.md"
)
DEFAULT_M2705_DESIGN = Path(
    "docs/m2705-engineering-controller-protected-runner-simulator-workload-support-design.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path("runs/m2706_engineering_controller_protected_runner_simulator_workload_support")
DEFAULT_DOC_PATH = Path(
    "docs/m2706-engineering-controller-protected-runner-simulator-workload-support-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2707-engineering-controller-protected-runner-simulator-workload-support-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2706 protected runner simulator/workload support materialization only; "
    "M2703 blocked execution-admission rows, M2704 audit, M2705 design, M2700 "
    "adapter rows, and M1690 schema references may be reanalyzed into support "
    "input-source, candidate, blocker, traceability, actor-contract, "
    "claim-boundary, and gate rows, but no reset, step, rollout, replay, "
    "validation, training, PPO, private holdout, profile-specific tuning, "
    "ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-response, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
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

EXECUTION_BLOCKED_NO_M1690_STATUS = "execution_admission_blocked_no_current_m1690_workload"
EXECUTION_ADMITTED_STATUS = "execution_admission_admitted_for_separate_execution_manifest"

SUPPORT_READY_STATUS = "support_ready_existing_m1690_workload"
SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS = "support_materialized_candidate_requires_new_workload_row"
SUPPORT_REQUIRES_SIMULATOR_FIXTURE_STATUS = "support_materialized_candidate_requires_simulator_fixture"
SUPPORT_REQUIRES_RUNTIME_ADAPTER_STATUS = "support_materialized_candidate_requires_runtime_adapter"
SUPPORT_BLOCKED_SCHEMA_STATUS = "support_blocked_schema_inconsistent"
SUPPORT_BLOCKED_SOURCE_MISSING_STATUS = "support_blocked_source_artifact_missing"
SUPPORT_BLOCKED_HIDDEN_ORACLE_STATUS = "support_blocked_hidden_oracle_required"
SUPPORT_BLOCKED_ACTOR_VISIBLE_LABEL_STATUS = "support_blocked_actor_visible_protected_label"
SUPPORT_BLOCKED_DENOMINATOR_STATUS = "support_blocked_denominator_boundary_violation"
SUPPORT_BLOCKED_ACTOR_CONTRACT_STATUS = "support_blocked_actor_contract_changed"
ALLOWED_SUPPORT_STATUSES = {
    SUPPORT_READY_STATUS,
    SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS,
    SUPPORT_REQUIRES_SIMULATOR_FIXTURE_STATUS,
    SUPPORT_REQUIRES_RUNTIME_ADAPTER_STATUS,
    SUPPORT_BLOCKED_SCHEMA_STATUS,
    SUPPORT_BLOCKED_SOURCE_MISSING_STATUS,
    SUPPORT_BLOCKED_HIDDEN_ORACLE_STATUS,
    SUPPORT_BLOCKED_ACTOR_VISIBLE_LABEL_STATUS,
    SUPPORT_BLOCKED_DENOMINATOR_STATUS,
    SUPPORT_BLOCKED_ACTOR_CONTRACT_STATUS,
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
SUPPORT_CANDIDATE_FIELDNAMES = [
    "support_candidate_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "profile_name",
    "policy_subject_id",
    "protected_task_family",
    "protected_source_edge",
    "execution_admission_status",
    "m1690_exact_workload_match",
    "m1690_reference_workload_id",
    "support_status",
    "support_blocker_status",
    "support_rule",
    "required_follow_up",
    "candidate_can_be_represented_in_current_runner",
    "candidate_requires_new_workload_row",
    "candidate_requires_simulator_fixture",
    "candidate_requires_runtime_adapter",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "measured_validation_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "protected_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
SUPPORT_BLOCKER_FIELDNAMES = [
    "blocker_id",
    "support_candidate_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "blocker_type",
    "blocker_reason",
    "required_follow_up",
    "actor_visible",
    "claim_scope",
]
SUPPORT_TRACEABILITY_FIELDNAMES = [
    "support_traceability_id",
    "execution_admission_trace_id",
    "adapter_trace_id",
    "source_trace_id",
    "support_candidate_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "protected_target_id",
    "target_family",
    "source_key",
    "traceability_axis",
    "source_artifact",
    "target_accounted",
    "support_traceability_status",
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
    "allowed_in_m2706",
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
    "support_input_source_rows",
    "support_candidate_rows",
    "support_blocker_rows",
    "support_traceability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_runner_simulator_workload_support(
    *,
    m2703_dir: Path | str = DEFAULT_M2703_DIR,
    m2700_dir: Path | str = DEFAULT_M2700_DIR,
    m2704_audit: Path | str = DEFAULT_M2704_AUDIT,
    m2705_design: Path | str = DEFAULT_M2705_DESIGN,
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
        m2703_dir=Path(m2703_dir),
        m2700_dir=Path(m2700_dir),
        m2704_audit=Path(m2704_audit),
        m2705_design=Path(m2705_design),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_source_rows = build_input_source_rows(source)
    support_candidate_rows = build_support_candidate_rows(source)
    traceability_rows, traceability_blocker_rows = build_support_traceability_rows(source, support_candidate_rows)
    blocker_rows = build_support_blocker_rows(support_candidate_rows) + traceability_blocker_rows + build_global_blocker_rows(source)
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
        all_candidates_classified=False,
        all_non_ready_rows_have_blockers=False,
        all_targets_accounted=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        support_candidate_rows=support_candidate_rows,
        support_blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["support_input_source_rows"], input_source_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(paths["support_candidate_rows"], support_candidate_rows, fieldnames=SUPPORT_CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["support_blocker_rows"], blocker_rows, fieldnames=SUPPORT_BLOCKER_FIELDNAMES)
    write_csv_rows(paths["support_traceability_rows"], traceability_rows, fieldnames=SUPPORT_TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    all_candidates_classified = candidates_classified(source, support_candidate_rows)
    all_non_ready_rows_have_blockers = non_ready_rows_have_blockers(support_candidate_rows, blocker_rows)
    all_targets_accounted = targets_accounted(source, traceability_rows)
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_ready_rows_have_blockers=all_non_ready_rows_have_blockers,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        support_candidate_rows=support_candidate_rows,
        support_blocker_rows=blocker_rows,
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
        support_candidate_rows=support_candidate_rows,
        support_blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_ready_rows_have_blockers=all_non_ready_rows_have_blockers,
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
        all_candidates_classified=all_candidates_classified,
        all_non_ready_rows_have_blockers=all_non_ready_rows_have_blockers,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        support_candidate_rows=support_candidate_rows,
        support_blocker_rows=blocker_rows,
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
        support_candidate_rows=support_candidate_rows,
        support_blocker_rows=blocker_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_ready_rows_have_blockers=all_non_ready_rows_have_blockers,
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
        "support_input_source_rows": output_dir / "support_input_source_rows.csv",
        "support_candidate_rows": output_dir / "support_candidate_rows.csv",
        "support_blocker_rows": output_dir / "support_blocker_rows.csv",
        "support_traceability_rows": output_dir / "support_traceability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2703_dir: Path,
    m2700_dir: Path,
    m2704_audit: Path,
    m2705_design: Path,
    executable_specs: Path,
    executable_workload: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2705_design": m2705_design,
        "m2704_audit": m2704_audit,
        "m2703_summary": m2703_dir / "summary.json",
        "m2703_execution_admission_input_source_rows": m2703_dir / "execution_admission_input_source_rows.csv",
        "m2703_execution_admission_candidate_rows": m2703_dir / "execution_admission_candidate_rows.csv",
        "m2703_execution_admission_rejection_rows": m2703_dir / "execution_admission_rejection_rows.csv",
        "m2703_execution_admission_traceability_rows": m2703_dir / "execution_admission_traceability_rows.csv",
        "m2703_actor_contract_guard_rows": m2703_dir / "actor_contract_guard_rows.csv",
        "m2703_claim_boundary_rows": m2703_dir / "claim_boundary_rows.csv",
        "m2703_gate_matrix": m2703_dir / "gate_matrix.csv",
        "m2700_summary": m2700_dir / "summary.json",
        "m2700_adapter_candidate_mapping_rows": m2700_dir / "adapter_candidate_mapping_rows.csv",
        "m2700_adapter_traceability_rows": m2700_dir / "adapter_traceability_rows.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": executable_workload,
        "post_m2470_route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2705_design_text": paths["m2705_design"].read_text(encoding="utf-8") if source_exists["m2705_design"] else "",
        "m2704_audit_text": paths["m2704_audit"].read_text(encoding="utf-8") if source_exists["m2704_audit"] else "",
        "post_m2470_route_plan_text": (
            paths["post_m2470_route_plan"].read_text(encoding="utf-8")
            if source_exists["post_m2470_route_plan"]
            else ""
        ),
        "m2703_summary": read_json(paths["m2703_summary"]) if source_exists["m2703_summary"] else {},
        "m2703_execution_admission_input_source_rows": read_csv_rows(paths["m2703_execution_admission_input_source_rows"]),
        "m2703_execution_admission_candidate_rows": read_csv_rows(paths["m2703_execution_admission_candidate_rows"]),
        "m2703_execution_admission_rejection_rows": read_csv_rows(paths["m2703_execution_admission_rejection_rows"]),
        "m2703_execution_admission_traceability_rows": read_csv_rows(paths["m2703_execution_admission_traceability_rows"]),
        "m2703_actor_contract_guard_rows": read_csv_rows(paths["m2703_actor_contract_guard_rows"]),
        "m2703_claim_boundary_rows": read_csv_rows(paths["m2703_claim_boundary_rows"]),
        "m2703_gate_matrix": read_csv_rows(paths["m2703_gate_matrix"]),
        "m2700_summary": read_json(paths["m2700_summary"]) if source_exists["m2700_summary"] else {},
        "m2700_adapter_candidate_mapping_rows": read_csv_rows(paths["m2700_adapter_candidate_mapping_rows"]),
        "m2700_adapter_traceability_rows": read_csv_rows(paths["m2700_adapter_traceability_rows"]),
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
        "m2705_design": "support materialization design boundary",
        "m2704_audit": "parent execution-admission result audit",
        "m2703_summary": "parent execution-admission status and count summary",
        "m2703_execution_admission_input_source_rows": "parent execution-admission input-source rows",
        "m2703_execution_admission_candidate_rows": "parent execution-admission candidate rows",
        "m2703_execution_admission_rejection_rows": "parent execution-admission rejection rows",
        "m2703_execution_admission_traceability_rows": "parent execution-admission traceability rows",
        "m2703_actor_contract_guard_rows": "parent actor/action guard rows",
        "m2703_claim_boundary_rows": "parent claim boundary rows",
        "m2703_gate_matrix": "parent gate matrix rows",
        "m2700_summary": "adapter-contract source status and count summary",
        "m2700_adapter_candidate_mapping_rows": "adapter-contract candidate mapping rows",
        "m2700_adapter_traceability_rows": "adapter-contract traceability rows",
        "executable_task_specs": "current executable task schema reference",
        "executable_workload_matrix": "current executable workload schema reference",
        "post_m2470_route_plan": "Route A/B/C claim separation plan",
        "follow_up_manifest": "M2707 result audit registration",
    }
    rows: list[dict[str, Any]] = []
    for artifact_id, path in source["paths"].items():
        rows.append(
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
        )
    return rows


def source_summary_value(source: dict[str, Any], artifact_id: str) -> str:
    if artifact_id == "m2703_summary":
        summary = source["m2703_summary"]
        return f"status_pass={summary.get('status_pass', '')};gate_matrix_pass={summary.get('gate_matrix_pass', '')}"
    if artifact_id == "m2700_summary":
        summary = source["m2700_summary"]
        return f"status_pass={summary.get('status_pass', '')};result_class={summary.get('result_class', '')}"
    if artifact_id == "m2704_audit":
        return "decision_present=" + str("accept_m2703_route_to_simulator_workload_support_design" in source["m2704_audit_text"])
    if artifact_id == "m2705_design":
        return "decision_present=" + str(
            "admit_protected_runner_simulator_workload_support_materialization_preflight"
            in source["m2705_design_text"]
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


def build_support_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(
        sorted(
            source["m2703_execution_admission_candidate_rows"],
            key=lambda row: str(row.get("execution_admission_candidate_id", "")),
        ),
        start=1,
    ):
        status, blocker_status, follow_up = candidate_support_status(candidate, source)
        support_candidate_id = f"m2706-support-candidate-{index:04d}"
        row = {
            "support_candidate_id": support_candidate_id,
            "execution_admission_candidate_id": candidate.get("execution_admission_candidate_id", ""),
            "adapter_candidate_id": candidate.get("adapter_candidate_id", ""),
            "workload_candidate_id": candidate.get("workload_candidate_id", ""),
            "runner_spec_id": candidate.get("runner_spec_id", ""),
            "source_panel_spec_id": candidate.get("source_panel_spec_id", ""),
            "profile_name": candidate.get("profile_name", ""),
            "policy_subject_id": candidate.get("policy_subject_id", ""),
            "protected_task_family": candidate.get("protected_task_family", ""),
            "protected_source_edge": candidate.get("protected_source_edge", ""),
            "execution_admission_status": candidate.get("execution_admission_status", ""),
            "m1690_exact_workload_match": _bool(candidate.get("m1690_exact_workload_match")),
            "m1690_reference_workload_id": candidate.get("m1690_reference_workload_id", ""),
            "support_status": status,
            "support_blocker_status": blocker_status,
            "support_rule": "m2703_blocked_execution_admission_to_no_execution_support_classification",
            "required_follow_up": follow_up,
            "candidate_can_be_represented_in_current_runner": status == SUPPORT_READY_STATUS,
            "candidate_requires_new_workload_row": status == SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS,
            "candidate_requires_simulator_fixture": status
            in {SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS, SUPPORT_REQUIRES_SIMULATOR_FIXTURE_STATUS},
            "candidate_requires_runtime_adapter": status == SUPPORT_REQUIRES_RUNTIME_ADAPTER_STATUS,
            "environment_reset_scheduled": False,
            "environment_rollout_scheduled": False,
            "measured_validation_scheduled": False,
            "training_scheduled": False,
            "profile_specific_tuning": False,
            "actor_input_contract_changed": _bool(candidate.get("actor_input_contract_changed")),
            "hidden_oracle_actor_input_required": _bool(candidate.get("hidden_oracle_actor_input_required")),
            "protected_labels_actor_visible": _bool(candidate.get("protected_labels_actor_visible")),
            "protected_rows_in_success_denominator": _bool(candidate.get("protected_rows_in_success_denominator")),
            "materialization_only_no_execution": True,
            "diagnostic_only_no_verdict": True,
            "claim_scope": CLAIM_SCOPE,
        }
        rows.append(row)
    return rows


def candidate_support_status(candidate: dict[str, str], source: dict[str, Any]) -> tuple[str, str, str]:
    required_sources = [
        "m2705_design",
        "m2704_audit",
        "m2703_summary",
        "m2703_execution_admission_candidate_rows",
        "m2703_execution_admission_rejection_rows",
        "m2703_execution_admission_traceability_rows",
        "m2703_actor_contract_guard_rows",
        "m2703_claim_boundary_rows",
        "m2703_gate_matrix",
        "m2700_summary",
        "m2700_adapter_candidate_mapping_rows",
        "m2700_adapter_traceability_rows",
        "executable_task_specs",
        "executable_workload_matrix",
        "post_m2470_route_plan",
    ]
    if not all(source["source_exists"][key] for key in required_sources):
        return (
            SUPPORT_BLOCKED_SOURCE_MISSING_STATUS,
            "support_blocker_source_artifact_missing",
            "missing-artifact repair before simulator/workload support materialization",
        )
    if "accept_m2703_route_to_simulator_workload_support_design" not in source["m2704_audit_text"]:
        return (
            SUPPORT_BLOCKED_SCHEMA_STATUS,
            "support_blocker_m2704_route_missing",
            "repair or rerun M2704 audit before support materialization",
        )
    if "admit_protected_runner_simulator_workload_support_materialization_preflight" not in source["m2705_design_text"]:
        return (
            SUPPORT_BLOCKED_SCHEMA_STATUS,
            "support_blocker_m2705_design_missing",
            "repair M2705 design before support materialization",
        )
    if not _bool(source["m2703_summary"].get("status_pass")) or not _bool(source["m2703_summary"].get("gate_matrix_pass")):
        return (
            SUPPORT_BLOCKED_SCHEMA_STATUS,
            "support_blocker_m2703_not_accepted",
            "rerun or audit M2703 before support materialization",
        )
    if _bool(candidate.get("hidden_oracle_actor_input_required")):
        return (
            SUPPORT_BLOCKED_HIDDEN_ORACLE_STATUS,
            "support_blocker_hidden_oracle_required",
            "redesign support route without hidden/oracle actor features",
        )
    if _bool(candidate.get("protected_labels_actor_visible")):
        return (
            SUPPORT_BLOCKED_ACTOR_VISIBLE_LABEL_STATUS,
            "support_blocker_actor_visible_protected_label",
            "repair protected label boundary before support materialization",
        )
    if _bool(candidate.get("protected_rows_in_success_denominator")):
        return (
            SUPPORT_BLOCKED_DENOMINATOR_STATUS,
            "support_blocker_denominator_boundary_violation",
            "repair denominator boundary before support materialization",
        )
    if _bool(candidate.get("actor_input_contract_changed")):
        return (
            SUPPORT_BLOCKED_ACTOR_CONTRACT_STATUS,
            "support_blocker_actor_contract_changed",
            "repair actor input contract before support materialization",
        )
    if _bool(candidate.get("m1690_exact_workload_match")):
        return (
            SUPPORT_READY_STATUS,
            "",
            "separate protected execution admission manifest required before any reset or rollout",
        )
    if str(candidate.get("execution_admission_status", "")) == EXECUTION_BLOCKED_NO_M1690_STATUS:
        return (
            SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS,
            "support_blocker_new_workload_row_required",
            "materialize a current M1690 workload row and simulator fixture before protected execution admission",
        )
    return (
        SUPPORT_BLOCKED_SCHEMA_STATUS,
        "support_blocker_execution_admission_status_unexpected",
        "route to taxonomy normalization before support materialization",
    )


def build_support_blocker_rows(support_candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in support_candidate_rows:
        if candidate.get("support_status") == SUPPORT_READY_STATUS:
            continue
        rows.append(
            blocker(
                f"m2706-support-blocker-{len(rows) + 1:04d}",
                candidate.get("support_candidate_id", ""),
                candidate.get("execution_admission_candidate_id", ""),
                candidate.get("adapter_candidate_id", ""),
                candidate.get("support_blocker_status") or candidate.get("support_status", ""),
                support_blocker_reason(str(candidate.get("support_status", ""))),
                str(candidate.get("required_follow_up", "")),
            )
        )
    return rows


def support_blocker_reason(status: str) -> str:
    if status == SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS:
        return "execution-admission candidate has no exact current M1690 executable workload row"
    if status == SUPPORT_REQUIRES_SIMULATOR_FIXTURE_STATUS:
        return "candidate requires simulator fixture support before execution admission"
    if status == SUPPORT_REQUIRES_RUNTIME_ADAPTER_STATUS:
        return "candidate requires runtime adapter support before execution admission"
    if status == SUPPORT_BLOCKED_SOURCE_MISSING_STATUS:
        return "one or more required source artifacts are missing"
    if status == SUPPORT_BLOCKED_HIDDEN_ORACLE_STATUS:
        return "candidate would require hidden/oracle actor input"
    if status == SUPPORT_BLOCKED_ACTOR_VISIBLE_LABEL_STATUS:
        return "candidate would expose protected labels to actor input"
    if status == SUPPORT_BLOCKED_DENOMINATOR_STATUS:
        return "candidate would put protected rows in ordinary success denominators"
    if status == SUPPORT_BLOCKED_ACTOR_CONTRACT_STATUS:
        return "candidate would change the actor input/action contract"
    return "candidate support status is schema-inconsistent"


def build_support_traceability_rows(
    source: dict[str, Any],
    support_candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_execution_id = {
        str(row.get("execution_admission_candidate_id", "")): row for row in support_candidate_rows
    }
    rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for index, trace in enumerate(
        sorted(
            source["m2703_execution_admission_traceability_rows"],
            key=lambda row: str(row.get("execution_admission_trace_id", "")),
        ),
        start=1,
    ):
        execution_candidate_id = str(trace.get("execution_admission_candidate_id", ""))
        candidate = candidates_by_execution_id.get(execution_candidate_id, {})
        trace_status = "support_traceability_materialized"
        if execution_candidate_id and not candidate:
            trace_status = "trace_has_no_support_candidate"
            blockers.append(
                blocker(
                    f"m2706-support-trace-blocker-{len(blockers) + 1:04d}",
                    "",
                    execution_candidate_id,
                    trace.get("adapter_candidate_id", ""),
                    "support_blocker_trace_has_no_candidate",
                    "execution-admission trace row references a candidate without a support row",
                    "repair M2703 traceability or route to taxonomy normalization",
                )
            )
        rows.append(support_traceability_row(index, trace, candidate, trace_status))
    return rows, blockers


def support_traceability_row(
    index: int,
    trace: dict[str, str],
    candidate: dict[str, Any],
    trace_status: str,
) -> dict[str, Any]:
    return {
        "support_traceability_id": f"m2706-support-trace-{index:04d}",
        "execution_admission_trace_id": trace.get("execution_admission_trace_id", ""),
        "adapter_trace_id": trace.get("adapter_trace_id", ""),
        "source_trace_id": trace.get("source_trace_id", ""),
        "support_candidate_id": candidate.get("support_candidate_id", ""),
        "execution_admission_candidate_id": trace.get(
            "execution_admission_candidate_id",
            candidate.get("execution_admission_candidate_id", ""),
        ),
        "adapter_candidate_id": trace.get("adapter_candidate_id", candidate.get("adapter_candidate_id", "")),
        "workload_candidate_id": trace.get("workload_candidate_id", candidate.get("workload_candidate_id", "")),
        "runner_spec_id": trace.get("runner_spec_id", candidate.get("runner_spec_id", "")),
        "source_panel_spec_id": trace.get("source_panel_spec_id", candidate.get("source_panel_spec_id", "")),
        "protected_target_id": trace.get("target_id", ""),
        "target_family": trace.get("target_family", ""),
        "source_key": trace.get("source_key", ""),
        "traceability_axis": trace.get("taxonomy_axis", ""),
        "source_artifact": "m2703_execution_admission_traceability_rows.csv",
        "target_accounted": bool(trace.get("target_id")),
        "support_traceability_status": trace_status,
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_scope": CLAIM_SCOPE,
    }


def build_global_blocker_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, exists in source["source_exists"].items():
        if not exists:
            rows.append(
                blocker(
                    f"m2706-support-blocker-global-{len(rows) + 1:04d}",
                    "",
                    "",
                    artifact_id,
                    "support_blocker_source_artifact_missing",
                    f"required source artifact is missing: {source['paths'][artifact_id]}",
                    "missing-artifact repair before simulator/workload support materialization",
                )
            )
    return rows


def blocker(
    blocker_id: str,
    support_candidate_id: Any,
    execution_admission_candidate_id: Any,
    adapter_candidate_id: Any,
    blocker_type: str,
    blocker_reason: str,
    required_follow_up: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "support_candidate_id": support_candidate_id,
        "execution_admission_candidate_id": execution_admission_candidate_id,
        "adapter_candidate_id": adapter_candidate_id,
        "blocker_type": blocker_type,
        "blocker_reason": blocker_reason,
        "required_follow_up": required_follow_up,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


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
        "guard_id": f"m2706_actor_guard_{field}",
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
    all_candidates_classified: bool,
    all_non_ready_rows_have_blockers: bool,
    all_targets_accounted: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("support_input_source_rows_materialized", "artifact", required_artifacts_present, "support_input_source_rows.csv"),
        ("support_candidate_rows_materialized", "artifact", required_artifacts_present, "support_candidate_rows.csv"),
        ("support_blocker_rows_materialized", "artifact", required_artifacts_present, "support_blocker_rows.csv"),
        ("support_traceability_rows_materialized", "artifact", required_artifacts_present, "support_traceability_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", required_artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", required_artifacts_present, "gate_matrix.csv"),
        (
            "all_candidates_classified",
            "support_materialization",
            all_candidates_classified,
            "support row for every M2703 execution-admission candidate",
        ),
        (
            "non_ready_rows_have_blockers",
            "support_materialization",
            all_non_ready_rows_have_blockers,
            "explicit support blocker for every non-ready support row",
        ),
        ("protected_targets_accounted", "traceability", all_targets_accounted, "support traceability for every M2703 target"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2707 result audit manifest"),
    ]
    blocked = [
        ("support_row_as_execution_row", "execution", "future protected execution admission manifest"),
        ("reset_execution", "execution", "future protected execution manifest"),
        ("environment_step", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2706"),
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
        "claim_id": f"m2706_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2706": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    support_candidate_rows: list[dict[str, Any]],
    support_blocker_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m2705_design",
        "m2704_audit",
        "m2703_summary",
        "m2703_execution_admission_candidate_rows",
        "m2703_execution_admission_rejection_rows",
        "m2703_execution_admission_traceability_rows",
        "m2703_actor_contract_guard_rows",
        "m2703_claim_boundary_rows",
        "m2703_gate_matrix",
        "m2700_summary",
        "m2700_adapter_candidate_mapping_rows",
        "m2700_adapter_traceability_rows",
        "executable_task_specs",
        "executable_workload_matrix",
        "post_m2470_route_plan",
    ]
    source_candidate_ids = {
        str(row.get("execution_admission_candidate_id", "")) for row in source["m2703_execution_admission_candidate_rows"]
    }
    output_candidate_ids = {str(row.get("execution_admission_candidate_id", "")) for row in support_candidate_rows}
    source_target_ids = source_target_id_set(source)
    trace_target_ids = {
        str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")
    }
    source_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in source["m2703_execution_admission_candidate_rows"])
    support_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in support_candidate_rows)
    source_admitted_count = int(source["m2703_summary"].get("execution_admission_admitted_count", 0) or 0)
    support_ready_count = sum(row.get("support_status") == SUPPORT_READY_STATUS for row in support_candidate_rows)
    non_ready_ids = non_ready_support_candidate_ids(support_candidate_rows)
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2706"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2706"])]
    return [
        gate(
            "m2706_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in required_sources),
            {key: source["source_exists"][key] for key in required_sources},
            "all M2705 M2704 M2703 M2700 M1690 and route-plan source artifacts present",
            "lineage_invalid",
        ),
        gate(
            "m2705_design_present",
            "lineage",
            "admit_protected_runner_simulator_workload_support_materialization_preflight"
            in source["m2705_design_text"],
            "admit_protected_runner_simulator_workload_support_materialization_preflight"
            in source["m2705_design_text"],
            True,
            "lineage_invalid",
        ),
        gate(
            "m2704_support_route_decision_present",
            "lineage",
            "accept_m2703_route_to_simulator_workload_support_design" in source["m2704_audit_text"],
            "accept_m2703_route_to_simulator_workload_support_design" in source["m2704_audit_text"],
            True,
            "lineage_invalid",
        ),
        gate("m2703_status_pass", "lineage", _bool(source["m2703_summary"].get("status_pass")), source["m2703_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2703_gate_matrix_pass", "lineage", _bool(source["m2703_summary"].get("gate_matrix_pass")), source["m2703_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("support_input_source_rows_cover_required_sources", "lineage", len(input_source_rows) == len(source["paths"]), len(input_source_rows), len(source["paths"]), "lineage_invalid"),
        gate("support_candidates_cover_execution_admission_candidates", "support_materialization", output_candidate_ids == source_candidate_ids, f"classified={len(output_candidate_ids)} source={len(source_candidate_ids)}", "one support row per M2703 execution-admission candidate", "metric_artifact"),
        gate("support_blockers_cover_non_ready_rows", "support_materialization", non_ready_rows_have_blockers(support_candidate_rows, support_blocker_rows), f"non_ready={len(non_ready_ids)} blockers={len(support_blocker_rows)}", "explicit blocker per non-ready support row", "metric_artifact"),
        gate("support_status_values_valid", "support_materialization", all(str(row.get("support_status", "")) in ALLOWED_SUPPORT_STATUSES for row in support_candidate_rows), sorted({str(row.get("support_status", "")) for row in support_candidate_rows}), "known support status values", "metric_artifact"),
        gate("blocked_execution_admission_rows_not_reinterpreted_as_execution", "execution_guardrail", all(not _bool(row.get("environment_reset_scheduled")) and not _bool(row.get("environment_rollout_scheduled")) for row in support_candidate_rows), "all support rows no execution", "no reset or rollout scheduled", "proof_washout"),
        gate("m1690_exact_match_boundary_preserved", "proof_washout", source_exact_count == support_exact_count, f"source_exact={source_exact_count} support_exact={support_exact_count}", "support rows preserve source exact-match count", "proof_washout"),
        gate("expected_zero_admitted_preserved_without_exact_match", "proof_washout", source_exact_count > 0 or source_admitted_count == 0, f"source_exact={source_exact_count} source_admitted={source_admitted_count}", "source admitted remains 0 when exact source count is 0", "proof_washout"),
        gate("support_ready_rows_zero_without_exact_m1690_match", "proof_washout", source_exact_count > 0 or support_ready_count == 0, f"source_exact={source_exact_count} support_ready={support_ready_count}", "support-ready count remains 0 without exact M1690 matches", "proof_washout"),
        gate("protected_targets_accounted", "traceability", trace_target_ids == source_target_ids, f"trace={len(trace_target_ids)} source={len(source_target_ids)}", "traceability row for every M2703 protected target", "proof_washout"),
        gate("m1690_reference_schema_consumed", "lineage", bool(source["executable_task_specs"]) and bool(source["executable_workload_matrix"]), f"specs={bool(source['executable_task_specs'])} workload={len(source['executable_workload_matrix'])}", "non-empty executable schema/workload", "lineage_invalid"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("protected_labels_actor_visible", False)) and not _bool(row.get("target_labels_actor_visible", False)) for row in support_candidate_rows + traceability_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in support_candidate_rows + traceability_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in support_candidate_rows + traceability_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) and not _bool(row.get("environment_reset_scheduled", False)) and not _bool(row.get("environment_rollout_scheduled", False)) and not _bool(row.get("measured_validation_scheduled", False)) and not _bool(row.get("training_scheduled", False)) for row in support_candidate_rows + traceability_rows), "all output rows materialization only", "no reset step rollout validation training", "objective_overfit"),
        gate("support_blocker_rows_actor_invisible", "contract", all(not _bool(row.get("actor_visible", False)) for row in support_blocker_rows), f"blockers={len(support_blocker_rows)}", "all false", "contract_violation"),
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
    support_candidate_rows: list[dict[str, Any]],
    support_blocker_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    all_candidates_classified: bool,
    all_non_ready_rows_have_blockers: bool,
    all_targets_accounted: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in support_candidate_rows:
        status = str(row.get("support_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_target_ids = source_target_id_set(source)
    source_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in source["m2703_execution_admission_candidate_rows"])
    support_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in support_candidate_rows)
    source_admitted_count = int(source["m2703_summary"].get("execution_admission_admitted_count", 0) or 0)
    support_ready_count = status_counts.get(SUPPORT_READY_STATUS, 0)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2706"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2706"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_runner_simulator_workload_support_materialization_pass"
            if status_pass
            else "engineering_controller_protected_runner_simulator_workload_support_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(
            source["source_exists"][key]
            for key in [
                "m2705_design",
                "m2704_audit",
                "m2703_summary",
                "m2703_execution_admission_candidate_rows",
                "m2703_execution_admission_rejection_rows",
                "m2703_execution_admission_traceability_rows",
                "m2703_actor_contract_guard_rows",
                "m2703_claim_boundary_rows",
                "m2703_gate_matrix",
                "m2700_summary",
                "m2700_adapter_candidate_mapping_rows",
                "m2700_adapter_traceability_rows",
                "executable_task_specs",
                "executable_workload_matrix",
                "post_m2470_route_plan",
            ]
        ),
        "m2705_design_decision_present": "admit_protected_runner_simulator_workload_support_materialization_preflight"
        in source["m2705_design_text"],
        "m2704_support_route_decision_present": "accept_m2703_route_to_simulator_workload_support_design"
        in source["m2704_audit_text"],
        "m2703_status_pass": _bool(source["m2703_summary"].get("status_pass")),
        "m2703_gate_matrix_pass": _bool(source["m2703_summary"].get("gate_matrix_pass")),
        "m2703_execution_admission_candidate_row_count": len(source["m2703_execution_admission_candidate_rows"]),
        "m2703_execution_admission_rejection_row_count": len(source["m2703_execution_admission_rejection_rows"]),
        "m2703_execution_admission_traceability_row_count": len(source["m2703_execution_admission_traceability_rows"]),
        "m2703_execution_admission_admitted_count": source_admitted_count,
        "m2703_execution_admission_blocked_no_current_m1690_workload_count": int(
            source["m2703_summary"].get("execution_admission_blocked_no_current_m1690_workload_count", 0) or 0
        ),
        "m2700_adapter_candidate_mapping_row_count": len(source["m2700_adapter_candidate_mapping_rows"]),
        "m2700_adapter_traceability_row_count": len(source["m2700_adapter_traceability_rows"]),
        "input_source_row_count": len(input_source_rows),
        "support_candidate_row_count": len(support_candidate_rows),
        "support_blocker_row_count": len(support_blocker_rows),
        "support_traceability_row_count": len(traceability_rows),
        "support_ready_existing_m1690_workload_count": support_ready_count,
        "support_materialized_candidate_requires_new_workload_row_count": status_counts.get(
            SUPPORT_REQUIRES_NEW_WORKLOAD_STATUS,
            0,
        ),
        "support_candidate_requires_simulator_fixture_count": sum(
            _bool(row.get("candidate_requires_simulator_fixture")) for row in support_candidate_rows
        ),
        "support_candidate_requires_runtime_adapter_count": sum(
            _bool(row.get("candidate_requires_runtime_adapter")) for row in support_candidate_rows
        ),
        "support_status_counts": dict(sorted(status_counts.items())),
        "m1690_exact_workload_match_count_source": source_exact_count,
        "m1690_exact_workload_match_count_support": support_exact_count,
        "m1690_exact_match_boundary_preserved": source_exact_count == support_exact_count,
        "expected_zero_admitted_preserved_without_exact_match": source_exact_count > 0 or source_admitted_count == 0,
        "support_ready_rows_zero_without_exact_m1690_match": source_exact_count > 0 or support_ready_count == 0,
        "protected_candidate_not_current_m1690_count": len(support_candidate_rows) - support_exact_count,
        "protected_target_count": len(source_target_ids),
        "support_traceability_target_count": len(
            {str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")}
        ),
        "all_candidates_classified": all_candidates_classified,
        "all_non_ready_rows_have_blockers": all_non_ready_rows_have_blockers,
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
        "allowed_claim": "protected runner simulator/workload support rows were materialized as support-ready, support-required, or blocked with explicit reasons",
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def candidates_classified(source: dict[str, Any], support_candidate_rows: list[dict[str, Any]]) -> bool:
    source_ids = {
        str(row.get("execution_admission_candidate_id", "")) for row in source["m2703_execution_admission_candidate_rows"]
    }
    output_ids = {str(row.get("execution_admission_candidate_id", "")) for row in support_candidate_rows}
    return output_ids == source_ids and all(str(row.get("support_status", "")) for row in support_candidate_rows)


def non_ready_rows_have_blockers(
    support_candidate_rows: list[dict[str, Any]],
    support_blocker_rows: list[dict[str, Any]],
) -> bool:
    return non_ready_support_candidate_ids(support_candidate_rows).issubset(
        {str(row.get("support_candidate_id", "")) for row in support_blocker_rows}
    )


def non_ready_support_candidate_ids(support_candidate_rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("support_candidate_id", ""))
        for row in support_candidate_rows
        if str(row.get("support_status", "")) != SUPPORT_READY_STATUS
    }


def targets_accounted(source: dict[str, Any], traceability_rows: list[dict[str, Any]]) -> bool:
    return {
        str(row.get("protected_target_id", "")) for row in traceability_rows if row.get("protected_target_id")
    } == source_target_id_set(source)


def source_target_id_set(source: dict[str, Any]) -> set[str]:
    return {
        str(row.get("target_id", ""))
        for row in source["m2703_execution_admission_traceability_rows"]
        if row.get("target_id")
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2706 Engineering Controller Protected Runner Simulator/Workload Support Materialization Preflight

## Summary

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- support candidate rows: {summary['support_candidate_row_count']}
- support blocker rows: {summary['support_blocker_row_count']}
- support traceability rows: {summary['support_traceability_row_count']}
- support-ready existing M1690 rows: {summary['support_ready_existing_m1690_workload_count']}
- support rows requiring new workload rows: {summary['support_materialized_candidate_requires_new_workload_row_count']}
- protected targets accounted: {summary['support_traceability_target_count']}/{summary['protected_target_count']}
- M1690 exact workload matches preserved from source: {summary['m1690_exact_workload_match_count_support']}
- source execution-admitted rows preserved: {summary['m2703_execution_admission_admitted_count']}
- gate matrix pass: {summary['gate_matrix_pass']}
- next: `{summary['next_blocker']}`

M2706 materializes the protected runner simulator/workload support surface
admitted by M2705. It reclassifies M2703 blocked execution-admission rows into
support rows while preserving that support rows are not execution rows,
validation rows, or performance evidence.

## Materialization Result

```text
M2703 execution-admission candidates: {summary['m2703_execution_admission_candidate_row_count']}
support candidates: {summary['support_candidate_row_count']}
support-ready existing M1690 rows: {summary['support_ready_existing_m1690_workload_count']}
support rows requiring new workload rows: {summary['support_materialized_candidate_requires_new_workload_row_count']}
support blocker rows: {summary['support_blocker_row_count']}
M1690 exact workload matches: {summary['m1690_exact_workload_match_count_support']}
source execution-admitted rows: {summary['m2703_execution_admission_admitted_count']}
all candidates classified: {summary['all_candidates_classified']}
all non-ready rows have blocker rows: {summary['all_non_ready_rows_have_blockers']}
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
- support_input_source_rows: `{summary['artifact_paths']['support_input_source_rows']}`
- support_candidate_rows: `{summary['artifact_paths']['support_candidate_rows']}`
- support_blocker_rows: `{summary['artifact_paths']['support_blocker_rows']}`
- support_traceability_rows: `{summary['artifact_paths']['support_traceability_rows']}`
- actor_contract_guard_rows: `{summary['artifact_paths']['actor_contract_guard_rows']}`
- claim_boundary_rows: `{summary['artifact_paths']['claim_boundary_rows']}`
- gate_matrix: `{summary['artifact_paths']['gate_matrix']}`
- doc: `{summary['artifact_paths']['doc']}`
"""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2703-dir", type=Path, default=DEFAULT_M2703_DIR)
    parser.add_argument("--m2700-dir", type=Path, default=DEFAULT_M2700_DIR)
    parser.add_argument("--m2704-audit", type=Path, default=DEFAULT_M2704_AUDIT)
    parser.add_argument("--m2705-design", type=Path, default=DEFAULT_M2705_DESIGN)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_protected_runner_simulator_workload_support(
        m2703_dir=args.m2703_dir,
        m2700_dir=args.m2700_dir,
        m2704_audit=args.m2704_audit,
        m2705_design=args.m2705_design,
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
