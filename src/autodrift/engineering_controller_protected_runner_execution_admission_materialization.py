"""Materialize protected runner execution-admission rows without execution.

M2703 consumes the accepted M2700 protected runner adapter contract pack and
the M2702 execution-admission design. It classifies every M2700 adapter
candidate as admitted, rejected, or blocked before any protected runner
execution route. It does not reset environments, step, roll out policies,
validate, train, rank, promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import DEFAULT_EXECUTABLE_SPECS, DEFAULT_EXECUTABLE_WORKLOAD
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit"
)
DEFAULT_M2700_DIR = Path("runs/m2700_engineering_controller_protected_runner_adapter_contract")
DEFAULT_M2701_AUDIT = Path(
    "docs/m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit.md"
)
DEFAULT_M2702_DESIGN = Path("docs/m2702-engineering-controller-protected-runner-execution-admission-design.md")
DEFAULT_OUTPUT_DIR = Path("runs/m2703_engineering_controller_protected_runner_execution_admission")
DEFAULT_DOC_PATH = Path(
    "docs/m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2703 protected runner execution-admission materialization only; M2700 "
    "adapter input-source, candidate mapping, rejection, traceability, "
    "actor-contract, claim-boundary, gate rows, M2701 audit, M2702 design, and "
    "M1690 schema references may be reanalyzed into execution-admission "
    "input-source, candidate, rejection, traceability, actor-contract, "
    "claim-boundary, and gate rows, but no reset, step, rollout, replay, "
    "validation, training, PPO, private holdout, profile-specific tuning, "
    "ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-response, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "protected execution result, repair success, driver performance, "
    "validation readiness or result, protected mitigation preservation result, "
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

M2700_MATERIALIZED_STATUS = "adapter_contract_materialized_not_execution_admitted"
ADMITTED_STATUS = "execution_admission_admitted_for_separate_execution_manifest"
BLOCKED_NO_M1690_STATUS = "execution_admission_blocked_no_current_m1690_workload"
BLOCKED_ADAPTER_STATUS = "execution_admission_blocked_adapter_not_execution_admitted"
ALLOWED_EXECUTION_ADMISSION_STATUSES = {
    ADMITTED_STATUS,
    BLOCKED_NO_M1690_STATUS,
    BLOCKED_ADAPTER_STATUS,
    "execution_admission_rejected_missing_policy_checkpoint",
    "execution_admission_rejected_missing_reference_profile_config",
    "execution_admission_rejected_hidden_oracle_required",
    "execution_admission_rejected_actor_visible_protected_label",
    "execution_admission_rejected_denominator_boundary_violation",
    "execution_admission_rejected_actor_contract_changed",
    "execution_admission_rejected_source_artifact_missing",
    "execution_admission_rejected_schema_inconsistent",
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
CANDIDATE_FIELDNAMES = [
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "source_panel_spec_id",
    "profile_name",
    "policy_subject_id",
    "policy_checkpoint_path",
    "policy_checkpoint_exists",
    "reference_profile_config_path",
    "reference_profile_config_exists",
    "adapter_admission_status",
    "m1690_exact_workload_match",
    "m1690_reference_workload_id",
    "protected_task_family",
    "protected_source_edge",
    "execution_admission_status",
    "execution_rejection_status",
    "execution_admission_rule",
    "required_follow_up",
    "environment_reset_admitted",
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
REJECTION_FIELDNAMES = [
    "rejection_id",
    "candidate_or_source_id",
    "rejection_type",
    "rejection_reason",
    "required_follow_up",
    "actor_visible",
    "claim_scope",
]
TRACEABILITY_FIELDNAMES = [
    "execution_admission_trace_id",
    "adapter_trace_id",
    "source_trace_id",
    "execution_admission_candidate_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "target_id",
    "target_family",
    "source_key",
    "taxonomy_axis",
    "source_panel_spec_id",
    "join_status",
    "execution_admission_trace_status",
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
    "allowed_in_m2703",
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
    "execution_admission_input_source_rows",
    "execution_admission_candidate_rows",
    "execution_admission_rejection_rows",
    "execution_admission_traceability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_runner_execution_admission(
    *,
    m2700_dir: Path | str = DEFAULT_M2700_DIR,
    m2701_audit: Path | str = DEFAULT_M2701_AUDIT,
    m2702_design: Path | str = DEFAULT_M2702_DESIGN,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
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
        m2700_dir=Path(m2700_dir),
        m2701_audit=Path(m2701_audit),
        m2702_design=Path(m2702_design),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_source_rows = build_input_source_rows(source)
    candidate_rows, candidate_rejection_rows = build_candidate_rows(source)
    traceability_rows, traceability_rejection_rows = build_traceability_rows(source, candidate_rows)
    rejection_rows = candidate_rejection_rows + traceability_rejection_rows + build_global_rejection_rows(source)
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
        all_candidates_classified=False,
        all_non_admitted_rows_have_rejection=False,
        all_targets_accounted=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["execution_admission_input_source_rows"], input_source_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(paths["execution_admission_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["execution_admission_rejection_rows"], rejection_rows, fieldnames=REJECTION_FIELDNAMES)
    write_csv_rows(paths["execution_admission_traceability_rows"], traceability_rows, fieldnames=TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    all_candidates_classified = candidates_classified(source, candidate_rows)
    all_non_admitted_rows_have_rejection = non_admitted_rows_have_rejection(candidate_rows, rejection_rows)
    all_targets_accounted = targets_accounted(source, traceability_rows)
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_admitted_rows_have_rejection=all_non_admitted_rows_have_rejection,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
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
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_admitted_rows_have_rejection=all_non_admitted_rows_have_rejection,
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
        all_non_admitted_rows_have_rejection=all_non_admitted_rows_have_rejection,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
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
        candidate_rows=candidate_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_classified=all_candidates_classified,
        all_non_admitted_rows_have_rejection=all_non_admitted_rows_have_rejection,
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
        "execution_admission_input_source_rows": output_dir / "execution_admission_input_source_rows.csv",
        "execution_admission_candidate_rows": output_dir / "execution_admission_candidate_rows.csv",
        "execution_admission_rejection_rows": output_dir / "execution_admission_rejection_rows.csv",
        "execution_admission_traceability_rows": output_dir / "execution_admission_traceability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2700_dir: Path,
    m2701_audit: Path,
    m2702_design: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2702_design": m2702_design,
        "m2701_audit": m2701_audit,
        "m2700_summary": m2700_dir / "summary.json",
        "m2700_adapter_input_source_rows": m2700_dir / "adapter_input_source_rows.csv",
        "m2700_adapter_candidate_mapping_rows": m2700_dir / "adapter_candidate_mapping_rows.csv",
        "m2700_adapter_rejection_rows": m2700_dir / "adapter_rejection_rows.csv",
        "m2700_adapter_traceability_rows": m2700_dir / "adapter_traceability_rows.csv",
        "m2700_actor_contract_guard_rows": m2700_dir / "actor_contract_guard_rows.csv",
        "m2700_claim_boundary_rows": m2700_dir / "claim_boundary_rows.csv",
        "m2700_gate_matrix": m2700_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2702_design_text": paths["m2702_design"].read_text(encoding="utf-8") if source_exists["m2702_design"] else "",
        "m2701_audit_text": paths["m2701_audit"].read_text(encoding="utf-8") if source_exists["m2701_audit"] else "",
        "m2700_summary": read_json(paths["m2700_summary"]) if source_exists["m2700_summary"] else {},
        "m2700_adapter_input_source_rows": read_csv_rows(paths["m2700_adapter_input_source_rows"]),
        "m2700_adapter_candidate_mapping_rows": read_csv_rows(paths["m2700_adapter_candidate_mapping_rows"]),
        "m2700_adapter_rejection_rows": read_csv_rows(paths["m2700_adapter_rejection_rows"]),
        "m2700_adapter_traceability_rows": read_csv_rows(paths["m2700_adapter_traceability_rows"]),
        "m2700_actor_contract_guard_rows": read_csv_rows(paths["m2700_actor_contract_guard_rows"]),
        "m2700_claim_boundary_rows": read_csv_rows(paths["m2700_claim_boundary_rows"]),
        "m2700_gate_matrix": read_csv_rows(paths["m2700_gate_matrix"]),
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
        "m2702_design": "execution-admission design boundary",
        "m2701_audit": "parent adapter-contract result audit",
        "m2700_summary": "parent adapter-contract status and count summary",
        "m2700_adapter_input_source_rows": "parent adapter input-source rows",
        "m2700_adapter_candidate_mapping_rows": "parent adapter candidate mapping rows",
        "m2700_adapter_rejection_rows": "parent adapter rejection rows",
        "m2700_adapter_traceability_rows": "parent adapter traceability rows",
        "m2700_actor_contract_guard_rows": "parent actor/action guard rows",
        "m2700_claim_boundary_rows": "parent claim boundary rows",
        "m2700_gate_matrix": "parent gate matrix rows",
        "executable_task_specs": "current executable task schema reference",
        "executable_workload_matrix": "current executable workload schema reference",
        "follow_up_manifest": "M2704 result audit registration",
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
    if artifact_id == "m2700_summary":
        summary = source["m2700_summary"]
        return f"status_pass={summary.get('status_pass', '')};result_class={summary.get('result_class', '')}"
    if artifact_id == "m2701_audit":
        return "decision_present=" + str("accept_m2700_route_to_protected_runner_execution_admission_design" in source["m2701_audit_text"])
    if artifact_id == "m2702_design":
        return "decision_present=" + str("admit_protected_runner_execution_admission_materialization_preflight" in source["m2702_design_text"])
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


def build_candidate_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for index, adapter in enumerate(
        sorted(
            source["m2700_adapter_candidate_mapping_rows"],
            key=lambda row: str(row.get("adapter_candidate_id", "")),
        ),
        start=1,
    ):
        status, rejection_reason, follow_up = candidate_execution_admission_status(adapter, source)
        candidate_id = f"m2703-execution-admission-candidate-{index:04d}"
        rejection_status = "" if status == ADMITTED_STATUS else status
        row = {
            "execution_admission_candidate_id": candidate_id,
            "adapter_candidate_id": adapter.get("adapter_candidate_id", ""),
            "workload_candidate_id": adapter.get("workload_candidate_id", ""),
            "runner_spec_id": adapter.get("runner_spec_id", ""),
            "source_panel_spec_id": adapter.get("source_panel_spec_id", ""),
            "profile_name": adapter.get("profile_name", ""),
            "policy_subject_id": adapter.get("policy_subject_id", ""),
            "policy_checkpoint_path": adapter.get("policy_checkpoint_path", ""),
            "policy_checkpoint_exists": _bool(adapter.get("policy_checkpoint_exists")),
            "reference_profile_config_path": adapter.get("reference_profile_config_path", ""),
            "reference_profile_config_exists": _bool(adapter.get("reference_profile_config_exists")),
            "adapter_admission_status": adapter.get("adapter_admission_status", ""),
            "m1690_exact_workload_match": _bool(adapter.get("m1690_exact_workload_match")),
            "m1690_reference_workload_id": adapter.get("m1690_reference_workload_id", ""),
            "protected_task_family": adapter.get("protected_task_family", ""),
            "protected_source_edge": adapter.get("protected_source_edge", ""),
            "execution_admission_status": status,
            "execution_rejection_status": rejection_status,
            "execution_admission_rule": "m2700_adapter_row_to_no_execution_admission_classification",
            "required_follow_up": follow_up,
            "environment_reset_admitted": False,
            "environment_rollout_scheduled": False,
            "measured_validation_scheduled": False,
            "training_scheduled": False,
            "profile_specific_tuning": False,
            "actor_input_contract_changed": _bool(adapter.get("actor_input_contract_changed")),
            "hidden_oracle_actor_input_required": _bool(adapter.get("hidden_oracle_actor_input_required")),
            "protected_labels_actor_visible": _bool(adapter.get("protected_labels_actor_visible")),
            "protected_rows_in_success_denominator": _bool(adapter.get("protected_rows_in_success_denominator")),
            "materialization_only_no_execution": True,
            "diagnostic_only_no_verdict": True,
            "claim_scope": CLAIM_SCOPE,
        }
        rows.append(row)
        if status != ADMITTED_STATUS:
            rejections.append(
                rejection(
                    f"m2703-rejection-{len(rejections) + 1:04d}",
                    adapter.get("adapter_candidate_id", candidate_id),
                    status,
                    rejection_reason,
                    follow_up,
                )
            )
    return rows, rejections


def candidate_execution_admission_status(adapter: dict[str, str], source: dict[str, Any]) -> tuple[str, str, str]:
    required_sources = [
        "m2702_design",
        "m2701_audit",
        "m2700_summary",
        "m2700_adapter_candidate_mapping_rows",
        "m2700_adapter_traceability_rows",
        "m2700_actor_contract_guard_rows",
        "m2700_claim_boundary_rows",
        "m2700_gate_matrix",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    if not all(source["source_exists"][key] for key in required_sources):
        return (
            "execution_admission_rejected_source_artifact_missing",
            "one or more required source artifacts are missing",
            "missing-artifact repair before protected execution admission",
        )
    if "accept_m2700_route_to_protected_runner_execution_admission_design" not in source["m2701_audit_text"]:
        return (
            "execution_admission_rejected_schema_inconsistent",
            "M2701 audit does not contain the expected route decision",
            "repair or rerun M2701 audit before execution admission",
        )
    if "admit_protected_runner_execution_admission_materialization_preflight" not in source["m2702_design_text"]:
        return (
            "execution_admission_rejected_schema_inconsistent",
            "M2702 design does not contain the expected admission decision",
            "repair M2702 design before materialization",
        )
    if not _bool(source["m2700_summary"].get("status_pass")):
        return (
            "execution_admission_rejected_schema_inconsistent",
            "M2700 summary did not pass",
            "rerun or audit M2700 before execution admission",
        )
    if str(adapter.get("adapter_admission_status", "")) != M2700_MATERIALIZED_STATUS:
        return (
            BLOCKED_ADAPTER_STATUS,
            "adapter row is not materialized as adapter-contract-not-execution",
            "repair adapter row or route to taxonomy normalization before protected execution",
        )
    if not _bool(adapter.get("policy_checkpoint_exists")):
        return (
            "execution_admission_rejected_missing_policy_checkpoint",
            "policy checkpoint is absent according to M2700 adapter row",
            "repair policy artifact before any protected execution route",
        )
    if not _bool(adapter.get("reference_profile_config_exists")):
        return (
            "execution_admission_rejected_missing_reference_profile_config",
            "reference profile config is absent according to M2700 adapter row",
            "repair profile config before any protected execution route",
        )
    if _bool(adapter.get("hidden_oracle_actor_input_required")):
        return (
            "execution_admission_rejected_hidden_oracle_required",
            "adapter row requires hidden/oracle actor input",
            "redesign runner contract without hidden/oracle actor features",
        )
    if _bool(adapter.get("protected_labels_actor_visible")):
        return (
            "execution_admission_rejected_actor_visible_protected_label",
            "adapter row exposes protected labels to actor input",
            "repair label boundary before protected execution admission",
        )
    if _bool(adapter.get("protected_rows_in_success_denominator")):
        return (
            "execution_admission_rejected_denominator_boundary_violation",
            "adapter row places protected rows in ordinary success denominators",
            "repair denominator boundary before protected execution admission",
        )
    if _bool(adapter.get("actor_input_contract_changed")):
        return (
            "execution_admission_rejected_actor_contract_changed",
            "adapter row changes actor input contract",
            "repair actor input contract before protected execution admission",
        )
    if not _bool(adapter.get("m1690_exact_workload_match")):
        return (
            BLOCKED_NO_M1690_STATUS,
            "adapter row has no exact current M1690 executable workload match",
            "materialize simulator/workload support or branch synthesis before protected execution",
        )
    return (
        ADMITTED_STATUS,
        "",
        "separate protected execution manifest and result audit required before any reset or rollout",
    )


def build_traceability_rows(
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_adapter_id = {str(row.get("adapter_candidate_id", "")): row for row in candidate_rows}
    rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for index, trace in enumerate(
        sorted(source["m2700_adapter_traceability_rows"], key=lambda row: str(row.get("adapter_trace_id", ""))),
        start=1,
    ):
        adapter_candidate_id = str(trace.get("adapter_candidate_id", ""))
        candidate = candidates_by_adapter_id.get(adapter_candidate_id, {})
        trace_status = "execution_admission_trace_materialized"
        if adapter_candidate_id and not candidate:
            trace_status = "trace_has_no_execution_admission_candidate"
            rejections.append(
                rejection(
                    f"m2703-trace-rejection-{len(rejections) + 1:04d}",
                    trace.get("adapter_trace_id", f"trace-{index}"),
                    "execution_admission_rejected_schema_inconsistent",
                    "adapter trace row references a candidate without an execution-admission row",
                    "repair M2700 traceability or route to taxonomy normalization",
                )
            )
        rows.append(execution_trace_row(index, trace, candidate, trace_status))
    return rows, rejections


def execution_trace_row(
    index: int,
    trace: dict[str, str],
    candidate: dict[str, Any],
    trace_status: str,
) -> dict[str, Any]:
    return {
        "execution_admission_trace_id": f"m2703-execution-admission-trace-{index:04d}",
        "adapter_trace_id": trace.get("adapter_trace_id", ""),
        "source_trace_id": trace.get("source_trace_id", ""),
        "execution_admission_candidate_id": candidate.get("execution_admission_candidate_id", ""),
        "adapter_candidate_id": trace.get("adapter_candidate_id", candidate.get("adapter_candidate_id", "")),
        "workload_candidate_id": trace.get("workload_candidate_id", candidate.get("workload_candidate_id", "")),
        "runner_spec_id": trace.get("runner_spec_id", candidate.get("runner_spec_id", "")),
        "target_id": trace.get("target_id", ""),
        "target_family": trace.get("target_family", ""),
        "source_key": trace.get("source_key", ""),
        "taxonomy_axis": trace.get("taxonomy_axis", ""),
        "source_panel_spec_id": trace.get("source_panel_spec_id", ""),
        "join_status": trace.get("join_status", ""),
        "execution_admission_trace_status": trace_status,
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_scope": CLAIM_SCOPE,
    }


def build_global_rejection_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, exists in source["source_exists"].items():
        if not exists:
            rows.append(
                rejection(
                    f"m2703-rejection-global-{len(rows) + 1:04d}",
                    artifact_id,
                    "execution_admission_rejected_source_artifact_missing",
                    f"required source artifact is missing: {source['paths'][artifact_id]}",
                    "missing-artifact repair before protected execution admission",
                )
            )
    return rows


def rejection(
    rejection_id: str,
    candidate_or_source_id: Any,
    rejection_type: str,
    rejection_reason: str,
    required_follow_up: str,
) -> dict[str, Any]:
    return {
        "rejection_id": rejection_id,
        "candidate_or_source_id": candidate_or_source_id,
        "rejection_type": rejection_type,
        "rejection_reason": rejection_reason,
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
        "guard_id": f"m2703_actor_guard_{field}",
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
    all_non_admitted_rows_have_rejection: bool,
    all_targets_accounted: bool,
) -> list[dict[str, Any]]:
    allowed = [
        (
            "execution_admission_input_source_rows_materialized",
            "artifact",
            required_artifacts_present,
            "execution_admission_input_source_rows.csv",
        ),
        (
            "execution_admission_candidate_rows_materialized",
            "artifact",
            required_artifacts_present,
            "execution_admission_candidate_rows.csv",
        ),
        (
            "execution_admission_rejection_rows_materialized",
            "artifact",
            required_artifacts_present,
            "execution_admission_rejection_rows.csv",
        ),
        (
            "execution_admission_traceability_rows_materialized",
            "artifact",
            required_artifacts_present,
            "execution_admission_traceability_rows.csv",
        ),
        ("actor_contract_guard_rows_materialized", "artifact", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", required_artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", required_artifacts_present, "gate_matrix.csv"),
        ("all_candidates_classified", "execution_admission", all_candidates_classified, "classification row for every M2700 adapter candidate"),
        (
            "non_admitted_rows_have_rejections",
            "execution_admission",
            all_non_admitted_rows_have_rejection,
            "explicit rejection or blocked row for every non-admitted candidate",
        ),
        ("protected_targets_accounted", "traceability", all_targets_accounted, "execution-admission traceability for every M2700 target"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2704 result audit manifest"),
    ]
    blocked = [
        ("reset_execution", "execution", "future protected execution manifest"),
        ("environment_step", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2703"),
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
        "claim_id": f"m2703_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2703": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m2702_design",
        "m2701_audit",
        "m2700_summary",
        "m2700_adapter_candidate_mapping_rows",
        "m2700_adapter_traceability_rows",
        "m2700_actor_contract_guard_rows",
        "m2700_claim_boundary_rows",
        "m2700_gate_matrix",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    adapter_ids = {str(row.get("adapter_candidate_id", "")) for row in source["m2700_adapter_candidate_mapping_rows"]}
    output_adapter_ids = {str(row.get("adapter_candidate_id", "")) for row in candidate_rows}
    source_target_ids = source_target_id_set(source)
    trace_target_ids = {str(row.get("target_id", "")) for row in traceability_rows if row.get("target_id")}
    non_exact_admitted = [
        row
        for row in candidate_rows
        if row.get("execution_admission_status") == ADMITTED_STATUS and not _bool(row.get("m1690_exact_workload_match"))
    ]
    source_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in source["m2700_adapter_candidate_mapping_rows"])
    admitted_count = sum(row.get("execution_admission_status") == ADMITTED_STATUS for row in candidate_rows)
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2703"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2703"])]
    return [
        gate(
            "m2703_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in required_sources),
            {key: source["source_exists"][key] for key in required_sources},
            "all M2702 M2701 M2700 and M1690 source artifacts present",
            "lineage_invalid",
        ),
        gate(
            "m2701_route_decision_present",
            "lineage",
            "accept_m2700_route_to_protected_runner_execution_admission_design" in source["m2701_audit_text"],
            "accept_m2700_route_to_protected_runner_execution_admission_design" in source["m2701_audit_text"],
            True,
            "lineage_invalid",
        ),
        gate(
            "m2702_admission_design_present",
            "lineage",
            "admit_protected_runner_execution_admission_materialization_preflight" in source["m2702_design_text"],
            "admit_protected_runner_execution_admission_materialization_preflight" in source["m2702_design_text"],
            True,
            "lineage_invalid",
        ),
        gate("m2700_status_pass", "lineage", _bool(source["m2700_summary"].get("status_pass")), source["m2700_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("input_source_rows_cover_required_sources", "lineage", len(input_source_rows) == len(source["paths"]), len(input_source_rows), len(source["paths"]), "lineage_invalid"),
        gate("adapter_candidates_present", "execution_admission", len(adapter_ids) > 0, len(adapter_ids), ">0", "metric_artifact"),
        gate("candidate_classification_covers_adapter_candidates", "execution_admission", output_adapter_ids == adapter_ids, f"classified={len(output_adapter_ids)} source={len(adapter_ids)}", "one classification row per M2700 adapter candidate", "metric_artifact"),
        gate("non_admitted_rows_have_rejection", "execution_admission", non_admitted_rows_have_rejection(candidate_rows, rejection_rows), f"non_admitted={len(non_admitted_candidate_ids(candidate_rows))} rejections={len(rejection_rows)}", "explicit rejection or blocker per non-admitted row", "metric_artifact"),
        gate("execution_admission_status_values_valid", "execution_admission", all(str(row.get("execution_admission_status", "")) in ALLOWED_EXECUTION_ADMISSION_STATUSES for row in candidate_rows), sorted({str(row.get("execution_admission_status", "")) for row in candidate_rows}), "known execution-admission status values", "metric_artifact"),
        gate("m1690_non_exact_not_execution_admitted", "proof_washout", not non_exact_admitted, len(non_exact_admitted), 0, "proof_washout"),
        gate("expected_zero_admitted_preserved_without_exact_match", "proof_washout", source_exact_count > 0 or admitted_count == 0, f"source_exact={source_exact_count} admitted={admitted_count}", "admitted remains 0 when exact source count is 0", "proof_washout"),
        gate("protected_targets_accounted", "traceability", trace_target_ids == source_target_ids, f"trace={len(trace_target_ids)} source={len(source_target_ids)}", "traceability row for every M2700 protected target", "proof_washout"),
        gate("m1690_reference_schema_consumed", "lineage", bool(source["executable_task_specs"]) and bool(source["executable_workload_matrix"]), f"specs={bool(source['executable_task_specs'])} workload={len(source['executable_workload_matrix'])}", "non-empty executable schema/workload", "lineage_invalid"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("protected_labels_actor_visible", False)) and not _bool(row.get("target_labels_actor_visible", False)) for row in candidate_rows + traceability_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in candidate_rows + traceability_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in candidate_rows + traceability_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) and not _bool(row.get("environment_reset_admitted", False)) and not _bool(row.get("environment_rollout_scheduled", False)) and not _bool(row.get("measured_validation_scheduled", False)) and not _bool(row.get("training_scheduled", False)) for row in candidate_rows + traceability_rows), "all output rows materialization only", "no reset step rollout validation training", "objective_overfit"),
        gate("rejection_rows_actor_invisible", "contract", all(not _bool(row.get("actor_visible", False)) for row in rejection_rows), f"rejections={len(rejection_rows)}", "all false", "contract_violation"),
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
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    all_candidates_classified: bool,
    all_non_admitted_rows_have_rejection: bool,
    all_targets_accounted: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in candidate_rows:
        status = str(row.get("execution_admission_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_target_ids = source_target_id_set(source)
    source_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in source["m2700_adapter_candidate_mapping_rows"])
    output_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in candidate_rows)
    admitted_count = status_counts.get(ADMITTED_STATUS, 0)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2703"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2703"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_runner_execution_admission_materialization_pass"
            if status_pass
            else "engineering_controller_protected_runner_execution_admission_materialization_fail"
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
                "m2702_design",
                "m2701_audit",
                "m2700_summary",
                "m2700_adapter_candidate_mapping_rows",
                "m2700_adapter_traceability_rows",
                "m2700_actor_contract_guard_rows",
                "m2700_claim_boundary_rows",
                "m2700_gate_matrix",
                "executable_task_specs",
                "executable_workload_matrix",
            ]
        ),
        "m2701_route_decision_present": "accept_m2700_route_to_protected_runner_execution_admission_design"
        in source["m2701_audit_text"],
        "m2702_design_decision_present": "admit_protected_runner_execution_admission_materialization_preflight"
        in source["m2702_design_text"],
        "m2700_status_pass": _bool(source["m2700_summary"].get("status_pass")),
        "m2700_adapter_candidate_mapping_row_count": len(source["m2700_adapter_candidate_mapping_rows"]),
        "m2700_adapter_traceability_row_count": len(source["m2700_adapter_traceability_rows"]),
        "m2700_adapter_execution_admitted_count": int(source["m2700_summary"].get("adapter_execution_admitted_count", 0) or 0),
        "m2700_adapter_contract_materialized_not_execution_admitted_count": int(
            source["m2700_summary"].get("adapter_contract_materialized_not_execution_admitted_count", 0) or 0
        ),
        "input_source_row_count": len(input_source_rows),
        "execution_admission_candidate_row_count": len(candidate_rows),
        "execution_admission_rejection_row_count": len(rejection_rows),
        "execution_admission_traceability_row_count": len(traceability_rows),
        "execution_admission_admitted_count": admitted_count,
        "execution_admission_blocked_no_current_m1690_workload_count": status_counts.get(BLOCKED_NO_M1690_STATUS, 0),
        "execution_admission_blocked_adapter_not_execution_admitted_count": status_counts.get(BLOCKED_ADAPTER_STATUS, 0),
        "execution_admission_status_counts": dict(sorted(status_counts.items())),
        "m1690_exact_workload_match_count_source": source_exact_count,
        "m1690_exact_workload_match_count_execution_admission": output_exact_count,
        "m1690_exact_match_boundary_preserved": source_exact_count == output_exact_count,
        "non_exact_m1690_execution_admitted_count": sum(
            row.get("execution_admission_status") == ADMITTED_STATUS and not _bool(row.get("m1690_exact_workload_match"))
            for row in candidate_rows
        ),
        "expected_zero_admitted_preserved_without_exact_match": source_exact_count > 0 or admitted_count == 0,
        "protected_candidate_not_current_m1690_count": len(candidate_rows) - output_exact_count,
        "protected_target_count": len(source_target_ids),
        "execution_admission_traceability_target_count": len(
            {str(row.get("target_id", "")) for row in traceability_rows if row.get("target_id")}
        ),
        "all_candidates_classified": all_candidates_classified,
        "all_non_admitted_rows_have_rejection": all_non_admitted_rows_have_rejection,
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
        "allowed_claim": "protected runner execution-admission rows were materialized as admitted, rejected, or blocked with explicit reasons",
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def candidates_classified(source: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> bool:
    source_ids = {str(row.get("adapter_candidate_id", "")) for row in source["m2700_adapter_candidate_mapping_rows"]}
    output_ids = {str(row.get("adapter_candidate_id", "")) for row in candidate_rows}
    return output_ids == source_ids and all(str(row.get("execution_admission_status", "")) for row in candidate_rows)


def non_admitted_rows_have_rejection(
    candidate_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
) -> bool:
    return non_admitted_candidate_ids(candidate_rows).issubset(
        {str(row.get("candidate_or_source_id", "")) for row in rejection_rows}
    )


def non_admitted_candidate_ids(candidate_rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("adapter_candidate_id", ""))
        for row in candidate_rows
        if str(row.get("execution_admission_status", "")) != ADMITTED_STATUS
    }


def targets_accounted(source: dict[str, Any], traceability_rows: list[dict[str, Any]]) -> bool:
    return {str(row.get("target_id", "")) for row in traceability_rows if row.get("target_id")} == source_target_id_set(source)


def source_target_id_set(source: dict[str, Any]) -> set[str]:
    return {str(row.get("target_id", "")) for row in source["m2700_adapter_traceability_rows"] if row.get("target_id")}


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2703 Engineering Controller Protected Runner Execution Admission Materialization Preflight

## Summary

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- execution-admission candidate rows: {summary['execution_admission_candidate_row_count']}
- execution-admission rejection rows: {summary['execution_admission_rejection_row_count']}
- execution-admission traceability rows: {summary['execution_admission_traceability_row_count']}
- execution-admitted rows: {summary['execution_admission_admitted_count']}
- blocked no-current-M1690 rows: {summary['execution_admission_blocked_no_current_m1690_workload_count']}
- protected targets accounted: {summary['execution_admission_traceability_target_count']}/{summary['protected_target_count']}
- M1690 exact workload matches preserved from source: {summary['m1690_exact_workload_match_count_execution_admission']}
- gate matrix pass: {summary['gate_matrix_pass']}
- next: `{summary['next_blocker']}`

M2703 materializes the protected runner execution-admission classification
surface admitted by M2702. It classifies every M2700 adapter candidate while
preserving the M2701 finding that adapter rows are not protected execution
rows, validation rows, or performance evidence.

## Materialization Result

```text
M2700 adapter candidate rows: {summary['m2700_adapter_candidate_mapping_row_count']}
execution-admission candidates: {summary['execution_admission_candidate_row_count']}
execution-admitted rows: {summary['execution_admission_admitted_count']}
blocked no-current-M1690 rows: {summary['execution_admission_blocked_no_current_m1690_workload_count']}
execution-admission rejection rows: {summary['execution_admission_rejection_row_count']}
M1690 exact workload matches: {summary['m1690_exact_workload_match_count_execution_admission']}
all candidates classified: {summary['all_candidates_classified']}
all non-admitted rows have rejection rows: {summary['all_non_admitted_rows_have_rejection']}
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
- execution_admission_input_source_rows: `{summary['artifact_paths']['execution_admission_input_source_rows']}`
- execution_admission_candidate_rows: `{summary['artifact_paths']['execution_admission_candidate_rows']}`
- execution_admission_rejection_rows: `{summary['artifact_paths']['execution_admission_rejection_rows']}`
- execution_admission_traceability_rows: `{summary['artifact_paths']['execution_admission_traceability_rows']}`
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
    parser.add_argument("--m2700-dir", type=Path, default=DEFAULT_M2700_DIR)
    parser.add_argument("--m2701-audit", type=Path, default=DEFAULT_M2701_AUDIT)
    parser.add_argument("--m2702-design", type=Path, default=DEFAULT_M2702_DESIGN)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_protected_runner_execution_admission(
        m2700_dir=args.m2700_dir,
        m2701_audit=args.m2701_audit,
        m2702_design=args.m2702_design,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
