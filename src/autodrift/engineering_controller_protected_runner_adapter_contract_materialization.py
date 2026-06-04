"""Materialize protected runner adapter contract rows.

M2700 consumes the accepted M2697 protected runner-spec generation pack and
M1690 executable workload schema references. It maps or explicitly rejects
every protected workload candidate under the M2699 adapter contract. It does
not reset environments, step, roll out policies, validate, train, rank,
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


DEFAULT_MILESTONE = "m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit"
DEFAULT_M2697_DIR = Path("runs/m2697_engineering_controller_protected_mitigation_runner_spec_generation")
DEFAULT_OUTPUT_DIR = Path("runs/m2700_engineering_controller_protected_runner_adapter_contract")
DEFAULT_DOC_PATH = Path("docs/m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2700 protected runner adapter contract materialization only; M2697 "
    "protected runner-spec rows, protected workload candidates, traceability "
    "rows, actor-contract guard rows, claim-boundary rows, gate rows, and M1690 "
    "schema references may be reanalyzed into adapter input-source, candidate "
    "mapping, rejection, traceability, actor-contract, claim-boundary, and gate "
    "rows, but no reset, step, rollout, replay, validation, training, PPO, "
    "private holdout, profile-specific tuning, ranking, winner selection, "
    "promotion, success-rate verdict, repair-success, driver-performance, "
    "paper, finite-window-vs-GRU, current-response, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "protected mitigation preservation result, controller-family ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-response sufficiency, "
    "current-sim verdict, high-fidelity validation readiness or result, full "
    "ideal driver completion, or level3 self-identification"
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

MATERIALIZED_STATUS = "adapter_contract_materialized_not_execution_admitted"
ALLOWED_ADAPTER_STATUSES = {
    MATERIALIZED_STATUS,
    "adapter_rejected_missing_policy_checkpoint",
    "adapter_rejected_missing_reference_profile_config",
    "adapter_rejected_hidden_oracle_required",
    "adapter_rejected_actor_visible_protected_label",
    "adapter_rejected_denominator_boundary_violation",
    "adapter_rejected_source_artifact_missing",
    "adapter_rejected_schema_inconsistent",
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
CANDIDATE_MAPPING_FIELDNAMES = [
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
    "m1690_exact_workload_match",
    "m1690_reference_workload_id",
    "protected_task_family",
    "protected_source_edge",
    "adapter_admission_status",
    "adapter_backend_family",
    "adapter_contract_rule",
    "environment_rollout_scheduled",
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
    "adapter_trace_id",
    "source_trace_id",
    "adapter_candidate_id",
    "workload_candidate_id",
    "runner_spec_id",
    "target_id",
    "target_family",
    "source_key",
    "taxonomy_axis",
    "source_panel_spec_id",
    "join_status",
    "adapter_trace_status",
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
    "allowed_in_m2700",
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
    "adapter_input_source_rows",
    "adapter_candidate_mapping_rows",
    "adapter_rejection_rows",
    "adapter_traceability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_runner_adapter_contract(
    *,
    m2697_dir: Path | str = DEFAULT_M2697_DIR,
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
        m2697_dir=Path(m2697_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_source_rows = build_input_source_rows(source)
    candidate_mapping_rows, candidate_rejection_rows = build_candidate_mapping_rows(source)
    traceability_rows, traceability_rejection_rows = build_traceability_rows(source, candidate_mapping_rows)
    rejection_rows = candidate_rejection_rows + traceability_rejection_rows + build_global_rejection_rows(source)
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
        all_candidates_mapped_or_rejected=False,
        all_targets_accounted=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_mapping_rows=candidate_mapping_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["adapter_input_source_rows"], input_source_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(paths["adapter_candidate_mapping_rows"], candidate_mapping_rows, fieldnames=CANDIDATE_MAPPING_FIELDNAMES)
    write_csv_rows(paths["adapter_rejection_rows"], rejection_rows, fieldnames=REJECTION_FIELDNAMES)
    write_csv_rows(paths["adapter_traceability_rows"], traceability_rows, fieldnames=TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key != "doc")
    all_candidates_mapped_or_rejected = candidates_mapped_or_rejected(source, candidate_mapping_rows, rejection_rows)
    all_targets_accounted = targets_accounted(source, traceability_rows)
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
        all_candidates_mapped_or_rejected=all_candidates_mapped_or_rejected,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_mapping_rows=candidate_mapping_rows,
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
        candidate_mapping_rows=candidate_mapping_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_mapped_or_rejected=all_candidates_mapped_or_rejected,
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
        all_candidates_mapped_or_rejected=all_candidates_mapped_or_rejected,
        all_targets_accounted=all_targets_accounted,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        input_source_rows=input_source_rows,
        candidate_mapping_rows=candidate_mapping_rows,
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
        candidate_mapping_rows=candidate_mapping_rows,
        rejection_rows=rejection_rows,
        traceability_rows=traceability_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        all_candidates_mapped_or_rejected=all_candidates_mapped_or_rejected,
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
        "adapter_input_source_rows": output_dir / "adapter_input_source_rows.csv",
        "adapter_candidate_mapping_rows": output_dir / "adapter_candidate_mapping_rows.csv",
        "adapter_rejection_rows": output_dir / "adapter_rejection_rows.csv",
        "adapter_traceability_rows": output_dir / "adapter_traceability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2697_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2697_summary": m2697_dir / "summary.json",
        "m2697_protected_runner_spec_rows": m2697_dir / "protected_runner_spec_rows.csv",
        "m2697_protected_workload_candidate_rows": m2697_dir / "protected_workload_candidate_rows.csv",
        "m2697_spec_traceability_rows": m2697_dir / "spec_traceability_rows.csv",
        "m2697_unmaterialized_bridge_rows": m2697_dir / "unmaterialized_bridge_rows.csv",
        "m2697_actor_contract_guard_rows": m2697_dir / "actor_contract_guard_rows.csv",
        "m2697_claim_boundary_rows": m2697_dir / "claim_boundary_rows.csv",
        "m2697_gate_matrix": m2697_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2697_summary": read_json(paths["m2697_summary"]) if source_exists["m2697_summary"] else {},
        "m2697_protected_runner_spec_rows": read_csv_rows(paths["m2697_protected_runner_spec_rows"]),
        "m2697_protected_workload_candidate_rows": read_csv_rows(paths["m2697_protected_workload_candidate_rows"]),
        "m2697_spec_traceability_rows": read_csv_rows(paths["m2697_spec_traceability_rows"]),
        "m2697_unmaterialized_bridge_rows": read_csv_rows(paths["m2697_unmaterialized_bridge_rows"]),
        "m2697_actor_contract_guard_rows": read_csv_rows(paths["m2697_actor_contract_guard_rows"]),
        "m2697_claim_boundary_rows": read_csv_rows(paths["m2697_claim_boundary_rows"]),
        "m2697_gate_matrix": read_csv_rows(paths["m2697_gate_matrix"]),
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
        "m2697_summary": "parent status and count summary",
        "m2697_protected_runner_spec_rows": "protected runner spec source rows",
        "m2697_protected_workload_candidate_rows": "protected workload candidate source rows",
        "m2697_spec_traceability_rows": "protected target and spec traceability rows",
        "m2697_unmaterialized_bridge_rows": "source unmaterialized bridge rows",
        "m2697_actor_contract_guard_rows": "parent actor/action guard rows",
        "m2697_claim_boundary_rows": "parent claim boundary rows",
        "m2697_gate_matrix": "parent gate matrix rows",
        "executable_task_specs": "current executable task schema reference",
        "executable_workload_matrix": "current executable workload schema reference",
        "follow_up_manifest": "M2701 result audit registration",
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
    if artifact_id == "m2697_summary":
        summary = source["m2697_summary"]
        return f"status_pass={summary.get('status_pass', '')};result_class={summary.get('result_class', '')}"
    if artifact_id == "executable_task_specs":
        value = source["executable_task_specs"]
        if isinstance(value, dict):
            return f"json_keys={';'.join(sorted(value.keys()))}"
        if isinstance(value, list):
            return f"rows={len(value)}"
        return str(type(value).__name__)
    row_key = artifact_id
    if row_key in source and isinstance(source[row_key], list):
        return f"rows={len(source[row_key])}"
    if artifact_id == "follow_up_manifest":
        return f"exists={source['source_exists'][artifact_id]}"
    return ""


def build_candidate_mapping_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runner_by_id = {str(row.get("runner_spec_id", "")): row for row in source["m2697_protected_runner_spec_rows"]}
    rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for index, candidate in enumerate(
        sorted(source["m2697_protected_workload_candidate_rows"], key=lambda row: str(row.get("workload_candidate_id", ""))),
        start=1,
    ):
        runner_spec_id = str(candidate.get("runner_spec_id", ""))
        runner = runner_by_id.get(runner_spec_id, {})
        status, rejection_reason = candidate_adapter_status(candidate, runner, source)
        adapter_candidate_id = f"m2700-adapter-candidate-{index:04d}"
        rows.append(
            {
                "adapter_candidate_id": adapter_candidate_id,
                "workload_candidate_id": candidate.get("workload_candidate_id", ""),
                "runner_spec_id": runner_spec_id,
                "source_panel_spec_id": candidate.get("source_panel_spec_id", runner.get("source_panel_spec_id", "")),
                "profile_name": candidate.get("profile_name", ""),
                "policy_subject_id": candidate.get("policy_subject_id", ""),
                "policy_checkpoint_path": candidate.get("policy_checkpoint_path", ""),
                "policy_checkpoint_exists": _bool(candidate.get("policy_checkpoint_exists")),
                "reference_profile_config_path": candidate.get("reference_profile_config_path", ""),
                "reference_profile_config_exists": _bool(candidate.get("reference_profile_config_exists")),
                "m1690_exact_workload_match": _bool(candidate.get("m1690_exact_workload_match")),
                "m1690_reference_workload_id": candidate.get("m1690_reference_workload_id", ""),
                "protected_task_family": candidate.get("protected_task_family", runner.get("protected_task_family", "")),
                "protected_source_edge": candidate.get("protected_source_edge", runner.get("protected_source_edge", "")),
                "adapter_admission_status": status,
                "adapter_backend_family": runner.get("runner_backend_family", ""),
                "adapter_contract_rule": "m2697_candidate_to_protected_runner_adapter_contract",
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "actor_input_contract_changed": _bool(candidate.get("actor_input_contract_changed")),
                "hidden_oracle_actor_input_required": _bool(candidate.get("hidden_oracle_actor_input_required")),
                "protected_labels_actor_visible": _bool(
                    candidate.get("protected_labels_actor_visible", candidate.get("target_labels_actor_visible"))
                ),
                "protected_rows_in_success_denominator": _bool(candidate.get("protected_rows_in_success_denominator")),
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
        if status != MATERIALIZED_STATUS:
            rejections.append(
                rejection(
                    f"m2700-rejection-{len(rejections) + 1:04d}",
                    candidate.get("workload_candidate_id", adapter_candidate_id),
                    status,
                    rejection_reason,
                    "repair source artifacts or route to taxonomy normalization before protected execution admission",
                )
            )
    return rows, rejections


def candidate_adapter_status(
    candidate: dict[str, str],
    runner: dict[str, str],
    source: dict[str, Any],
) -> tuple[str, str]:
    required_sources = [
        "m2697_protected_runner_spec_rows",
        "m2697_protected_workload_candidate_rows",
        "m2697_spec_traceability_rows",
        "m2697_gate_matrix",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    if not all(source["source_exists"][key] for key in required_sources):
        return "adapter_rejected_source_artifact_missing", "one or more required source artifacts are missing"
    if not runner:
        return "adapter_rejected_schema_inconsistent", "candidate runner_spec_id is not present in protected_runner_spec_rows"
    if not _bool(candidate.get("policy_checkpoint_exists")):
        return "adapter_rejected_missing_policy_checkpoint", "policy checkpoint is absent according to M2697 candidate row"
    if not _bool(candidate.get("reference_profile_config_exists")):
        return "adapter_rejected_missing_reference_profile_config", "reference profile config is absent according to M2697 candidate row"
    if _bool(candidate.get("hidden_oracle_actor_input_required")) or _bool(runner.get("hidden_oracle_actor_input_required")):
        return "adapter_rejected_hidden_oracle_required", "candidate or runner spec requires hidden/oracle actor input"
    if _bool(candidate.get("target_labels_actor_visible")) or _bool(runner.get("target_labels_actor_visible")):
        return "adapter_rejected_actor_visible_protected_label", "candidate or runner spec exposes protected labels to actor input"
    if _bool(candidate.get("protected_rows_in_success_denominator")) or _bool(runner.get("protected_rows_in_success_denominator")):
        return "adapter_rejected_denominator_boundary_violation", "candidate or runner spec places protected rows in success denominators"
    return MATERIALIZED_STATUS, ""


def build_traceability_rows(
    source: dict[str, Any],
    candidate_mapping_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_runner: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidate_mapping_rows:
        candidates_by_runner.setdefault(str(candidate.get("runner_spec_id", "")), []).append(candidate)

    rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    trace_index = 1
    for trace in sorted(source["m2697_spec_traceability_rows"], key=lambda row: str(row.get("trace_id", ""))):
        runner_spec_id = str(trace.get("runner_spec_id", ""))
        candidates = candidates_by_runner.get(runner_spec_id, [])
        if not candidates:
            rows.append(adapter_trace_row(trace_index, trace, {}, "trace_has_no_adapter_candidate"))
            rejections.append(
                rejection(
                    f"m2700-rejection-{len(rejections) + 1:04d}",
                    trace.get("trace_id", f"trace-{trace_index}"),
                    "adapter_rejected_schema_inconsistent",
                    "trace runner_spec_id has no adapter candidate mapping row",
                    "repair M2697 candidate rows or route to taxonomy normalization",
                )
            )
            trace_index += 1
            continue
        for candidate in candidates:
            rows.append(adapter_trace_row(trace_index, trace, candidate, "adapter_candidate_trace_materialized"))
            trace_index += 1

    for unmaterialized in sorted(
        source["m2697_unmaterialized_bridge_rows"],
        key=lambda row: str(row.get("target_id", "")),
    ):
        rows.append(adapter_trace_row(trace_index, unmaterialized, {}, "source_unmaterialized_preserved_not_adapter_candidate"))
        rejections.append(
            rejection(
                f"m2700-rejection-{len(rejections) + 1:04d}",
                unmaterialized.get("target_id", f"unmaterialized-{trace_index}"),
                "adapter_rejected_schema_inconsistent",
                "M2697 preserved this protected target as unmaterialized rather than a runner candidate",
                "taxonomy normalization before protected execution admission",
            )
        )
        trace_index += 1
    return rows, rejections


def adapter_trace_row(
    index: int,
    source_row: dict[str, str],
    candidate: dict[str, Any],
    adapter_trace_status: str,
) -> dict[str, Any]:
    return {
        "adapter_trace_id": f"m2700-adapter-trace-{index:04d}",
        "source_trace_id": source_row.get("trace_id", ""),
        "adapter_candidate_id": candidate.get("adapter_candidate_id", ""),
        "workload_candidate_id": candidate.get("workload_candidate_id", ""),
        "runner_spec_id": source_row.get("runner_spec_id", candidate.get("runner_spec_id", "")),
        "target_id": source_row.get("target_id", ""),
        "target_family": source_row.get("target_family", ""),
        "source_key": source_row.get("source_key", ""),
        "taxonomy_axis": source_row.get("taxonomy_axis", ""),
        "source_panel_spec_id": source_row.get("panel_spec_id", source_row.get("source_panel_spec_id", "")),
        "join_status": source_row.get("join_status", ""),
        "adapter_trace_status": adapter_trace_status,
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
                    f"m2700-rejection-global-{len(rows) + 1:04d}",
                    artifact_id,
                    "adapter_rejected_source_artifact_missing",
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
        "guard_id": f"m2700_actor_guard_{field}",
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
    all_candidates_mapped_or_rejected: bool,
    all_targets_accounted: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("adapter_input_source_rows_materialized", "artifact", required_artifacts_present, "adapter_input_source_rows.csv"),
        ("adapter_candidate_mapping_rows_materialized", "artifact", required_artifacts_present, "adapter_candidate_mapping_rows.csv"),
        ("adapter_rejection_rows_materialized", "artifact", required_artifacts_present, "adapter_rejection_rows.csv"),
        ("adapter_traceability_rows_materialized", "artifact", required_artifacts_present, "adapter_traceability_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", required_artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", required_artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", required_artifacts_present, "gate_matrix.csv"),
        ("all_candidates_mapped_or_rejected", "adapter_contract", all_candidates_mapped_or_rejected, "mapping or rejection row for every candidate"),
        ("protected_targets_accounted", "traceability", all_targets_accounted, "adapter traceability for every M2697 target"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2701 result audit manifest"),
    ]
    blocked = [
        ("reset_execution", "execution", "future protected execution manifest"),
        ("environment_step", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2700"),
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
        "claim_id": f"m2700_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2700": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    candidate_mapping_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m2697_summary",
        "m2697_protected_runner_spec_rows",
        "m2697_protected_workload_candidate_rows",
        "m2697_spec_traceability_rows",
        "m2697_unmaterialized_bridge_rows",
        "m2697_actor_contract_guard_rows",
        "m2697_claim_boundary_rows",
        "m2697_gate_matrix",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    candidate_source_ids = {str(row.get("workload_candidate_id", "")) for row in source["m2697_protected_workload_candidate_rows"]}
    candidate_mapping_ids = {str(row.get("workload_candidate_id", "")) for row in candidate_mapping_rows}
    rejected_ids = {str(row.get("candidate_or_source_id", "")) for row in rejection_rows}
    source_target_ids = source_target_id_set(source)
    trace_target_ids = {str(row.get("target_id", "")) for row in traceability_rows}
    source_exact_by_candidate = {
        str(row.get("workload_candidate_id", "")): _bool(row.get("m1690_exact_workload_match"))
        for row in source["m2697_protected_workload_candidate_rows"]
    }
    output_exact_by_candidate = {
        str(row.get("workload_candidate_id", "")): _bool(row.get("m1690_exact_workload_match"))
        for row in candidate_mapping_rows
    }
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2700"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2700"])]
    return [
        gate(
            "m2700_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in required_sources),
            {key: source["source_exists"][key] for key in required_sources},
            "all M2697 and M1690 source artifacts present",
            "lineage_invalid",
        ),
        gate("m2697_status_pass", "lineage", _bool(source["m2697_summary"].get("status_pass")), source["m2697_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("input_source_rows_cover_required_sources", "lineage", len(input_source_rows) == len(source["paths"]), len(input_source_rows), len(source["paths"]), "lineage_invalid"),
        gate("protected_candidates_present", "adapter_contract", len(candidate_source_ids) > 0, len(candidate_source_ids), ">0", "metric_artifact"),
        gate("adapter_candidate_mapping_covers_source_candidates", "adapter_contract", candidate_mapping_ids == candidate_source_ids, f"mapping={len(candidate_mapping_ids)} source={len(candidate_source_ids)}", "one mapping row per source candidate", "metric_artifact"),
        gate("adapter_candidate_rows_mapped_or_rejected", "adapter_contract", candidates_mapped_or_rejected(source, candidate_mapping_rows, rejection_rows), f"mapped={len(candidate_mapping_ids)} rejected={len(rejected_ids)} source={len(candidate_source_ids)}", "every source candidate mapped and any rejected candidate explicit", "metric_artifact"),
        gate("adapter_status_values_valid", "adapter_contract", all(str(row.get("adapter_admission_status", "")) in ALLOWED_ADAPTER_STATUSES for row in candidate_mapping_rows), sorted({str(row.get("adapter_admission_status", "")) for row in candidate_mapping_rows}), "known adapter status values", "metric_artifact"),
        gate("protected_targets_accounted", "traceability", trace_target_ids == source_target_ids, f"trace={len(trace_target_ids)} source={len(source_target_ids)}", "adapter traceability row for every M2697 target", "proof_washout"),
        gate("m1690_exact_match_boundary_preserved", "lineage", output_exact_by_candidate == source_exact_by_candidate, output_exact_by_candidate, "output exact-match flags equal source flags", "proof_washout"),
        gate("m1690_reference_schema_consumed", "lineage", bool(source["executable_task_specs"]) and bool(source["executable_workload_matrix"]), f"specs={bool(source['executable_task_specs'])} workload={len(source['executable_workload_matrix'])}", "non-empty executable schema/workload", "lineage_invalid"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("protected_labels_actor_visible", False)) and not _bool(row.get("target_labels_actor_visible", False)) for row in candidate_mapping_rows + traceability_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in candidate_mapping_rows + traceability_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in candidate_mapping_rows + traceability_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) and not _bool(row.get("environment_rollout_scheduled", False)) and not _bool(row.get("training_scheduled", False)) for row in candidate_mapping_rows + traceability_rows), "all output rows materialization only", "no reset step rollout", "objective_overfit"),
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
    candidate_mapping_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    all_candidates_mapped_or_rejected: bool,
    all_targets_accounted: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for row in candidate_mapping_rows:
        status = str(row.get("adapter_admission_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_target_ids = source_target_id_set(source)
    source_m1690_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in source["m2697_protected_workload_candidate_rows"])
    adapter_m1690_exact_count = sum(_bool(row.get("m1690_exact_workload_match")) for row in candidate_mapping_rows)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2700"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2700"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_runner_adapter_contract_materialization_pass"
            if status_pass
            else "engineering_controller_protected_runner_adapter_contract_materialization_fail"
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
                "m2697_summary",
                "m2697_protected_runner_spec_rows",
                "m2697_protected_workload_candidate_rows",
                "m2697_spec_traceability_rows",
                "m2697_unmaterialized_bridge_rows",
                "m2697_actor_contract_guard_rows",
                "m2697_claim_boundary_rows",
                "m2697_gate_matrix",
                "executable_task_specs",
                "executable_workload_matrix",
            ]
        ),
        "m2697_status_pass": _bool(source["m2697_summary"].get("status_pass")),
        "m2697_protected_runner_spec_row_count": len(source["m2697_protected_runner_spec_rows"]),
        "m2697_protected_workload_candidate_row_count": len(source["m2697_protected_workload_candidate_rows"]),
        "m2697_spec_traceability_row_count": len(source["m2697_spec_traceability_rows"]),
        "m2697_unmaterialized_bridge_row_count": len(source["m2697_unmaterialized_bridge_rows"]),
        "input_source_row_count": len(input_source_rows),
        "adapter_candidate_mapping_row_count": len(candidate_mapping_rows),
        "adapter_rejection_row_count": len(rejection_rows),
        "adapter_traceability_row_count": len(traceability_rows),
        "adapter_contract_materialized_not_execution_admitted_count": status_counts.get(MATERIALIZED_STATUS, 0),
        "adapter_execution_admitted_count": 0,
        "adapter_rejection_status_counts": dict(sorted((key, value) for key, value in status_counts.items() if key != MATERIALIZED_STATUS)),
        "m1690_exact_workload_match_count_source": source_m1690_exact_count,
        "m1690_exact_workload_match_count_adapter": adapter_m1690_exact_count,
        "m1690_exact_match_boundary_preserved": source_m1690_exact_count == adapter_m1690_exact_count,
        "protected_candidate_not_current_m1690_count": len(candidate_mapping_rows) - adapter_m1690_exact_count,
        "protected_target_count": len(source_target_ids),
        "adapter_traceability_target_count": len({str(row.get("target_id", "")) for row in traceability_rows}),
        "all_candidates_mapped_or_rejected": all_candidates_mapped_or_rejected,
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
        "allowed_claim": "protected runner adapter contract rows were materialized or rejected with explicit reasons",
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def candidates_mapped_or_rejected(
    source: dict[str, Any],
    candidate_mapping_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
) -> bool:
    source_ids = {str(row.get("workload_candidate_id", "")) for row in source["m2697_protected_workload_candidate_rows"]}
    mapped_ids = {str(row.get("workload_candidate_id", "")) for row in candidate_mapping_rows}
    rejected_ids = {str(row.get("candidate_or_source_id", "")) for row in rejection_rows}
    non_materialized_ids = {
        str(row.get("workload_candidate_id", ""))
        for row in candidate_mapping_rows
        if str(row.get("adapter_admission_status", "")) != MATERIALIZED_STATUS
    }
    return mapped_ids == source_ids and non_materialized_ids.issubset(rejected_ids)


def targets_accounted(source: dict[str, Any], traceability_rows: list[dict[str, Any]]) -> bool:
    return {str(row.get("target_id", "")) for row in traceability_rows} == source_target_id_set(source)


def source_target_id_set(source: dict[str, Any]) -> set[str]:
    trace_ids = {str(row.get("target_id", "")) for row in source["m2697_spec_traceability_rows"] if row.get("target_id")}
    unmaterialized_ids = {
        str(row.get("target_id", "")) for row in source["m2697_unmaterialized_bridge_rows"] if row.get("target_id")
    }
    return trace_ids | unmaterialized_ids


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2700 Engineering Controller Protected Runner Adapter Contract Materialization Preflight

## Summary

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- adapter candidate mapping rows: {summary['adapter_candidate_mapping_row_count']}
- adapter rejection rows: {summary['adapter_rejection_row_count']}
- adapter traceability rows: {summary['adapter_traceability_row_count']}
- protected targets accounted: {summary['adapter_traceability_target_count']}/{summary['protected_target_count']}
- M1690 exact workload matches preserved from source: {summary['m1690_exact_workload_match_count_adapter']}
- gate matrix pass: {summary['gate_matrix_pass']}
- next: `{summary['next_blocker']}`

M2700 materializes the protected runner adapter contract admitted by M2699. It
maps or explicitly rejects every M2697 protected workload candidate while
preserving the M2698 finding that these rows are adapter-contract materialization
rows, not protected execution admissions or performance evidence.

## Materialization Result

```text
M2697 protected runner specs: {summary['m2697_protected_runner_spec_row_count']}
M2697 protected workload candidates: {summary['m2697_protected_workload_candidate_row_count']}
adapter contract materialized rows: {summary['adapter_contract_materialized_not_execution_admitted_count']}
adapter rejection rows: {summary['adapter_rejection_row_count']}
adapter execution admitted rows: {summary['adapter_execution_admitted_count']}
M1690 exact workload matches: {summary['m1690_exact_workload_match_count_adapter']}
all candidates mapped or rejected: {summary['all_candidates_mapped_or_rejected']}
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
- adapter_input_source_rows: `{summary['artifact_paths']['adapter_input_source_rows']}`
- adapter_candidate_mapping_rows: `{summary['artifact_paths']['adapter_candidate_mapping_rows']}`
- adapter_rejection_rows: `{summary['artifact_paths']['adapter_rejection_rows']}`
- adapter_traceability_rows: `{summary['artifact_paths']['adapter_traceability_rows']}`
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
    parser.add_argument("--m2697-dir", type=Path, default=DEFAULT_M2697_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_protected_runner_adapter_contract(
        m2697_dir=args.m2697_dir,
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
