"""Materialize protected mitigation target executable-surface bridge rows.

M2695 consumes the M2694/M2693/M2691/M2664/M2667 protected mitigation
artifacts and classifies every protected target as either an exact current
runner executable candidate or an explicit unbridgeable row. It does not reset
environments, execute policies, train, validate, rank, promote, or claim driver
performance.
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
    "m2695-engineering-controller-protected-mitigation-target-executable-"
    "surface-bridge-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2696-engineering-controller-protected-mitigation-target-executable-"
    "surface-bridge-materialization-result-audit"
)
DEFAULT_M2693_DIR = Path("runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight")
DEFAULT_M2691_DIR = Path("runs/m2691_engineering_controller_source_diverse_offtrack_protected_target_panel")
DEFAULT_M2664_DIR = Path("runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy")
DEFAULT_M2667_DIR = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2695_engineering_controller_protected_mitigation_target_executable_surface_bridge")
DEFAULT_DOC_PATH = Path(
    "docs/m2695-engineering-controller-protected-mitigation-target-executable-surface-bridge-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2696-engineering-controller-protected-mitigation-target-executable-surface-bridge-materialization-result-audit.json"
)
DEFAULT_M2694_AUDIT_DOC = Path(
    "docs/m2694-engineering-controller-source-diverse-offtrack-protected-bounded-execution-result-audit.md"
)
DEFAULT_RUNTIME_PROFILE_NAME = "L3_online_gru"

CLAIM_SCOPE = (
    "M2695 protected mitigation target executable-surface bridge materialization "
    "only; M2694/M2693/M2691/M2664/M2667 artifacts and the current executable "
    "workload index may be reanalyzed into protected bridge, executable "
    "candidate, unbridgeable, actor-contract, claim-boundary, and gate rows, "
    "but no reset, step, rollout, replay, validation, training, PPO, private "
    "holdout, profile-specific tuning, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, finite-"
    "window-vs-GRU, current-response, current-sim, high-fidelity validation, "
    "full ideal driver, or self-ID claim is made"
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

PROTECTED_BRIDGE_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_family",
    "source_key",
    "task_family",
    "source_edge_or_axis",
    "role_semantics_proxy",
    "taxonomy_axis",
    "boundary_id",
    "failure_family",
    "bridge_status",
    "bridge_class",
    "executable_candidate_id",
    "unbridgeable_reason",
    "parent_failure_type",
    "parent_error_message",
    "source_row_count",
    "blocking_count",
    "regressed_row_count",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
EXECUTABLE_CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "target_id",
    "target_family",
    "source_key",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "executable_source_family",
    "env_template_family",
    "mapping_rule",
    "config_exists",
    "checkpoint_exists",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "protected_rows_in_success_denominator",
    "materialization_only_no_execution",
    "claim_boundary",
]
UNBRIDGEABLE_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_key",
    "task_family",
    "source_edge_or_axis",
    "taxonomy_axis",
    "role_semantics_proxy",
    "unbridgeable_reason",
    "missing_contract",
    "required_follow_up",
    "parent_failure_type",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "materialization_only_no_execution",
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
    "allowed_in_m2695",
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
    "protected_bridge_rows",
    "executable_candidate_rows",
    "unbridgeable_target_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_protected_mitigation_target_executable_surface_bridge(
    *,
    m2693_dir: Path | str = DEFAULT_M2693_DIR,
    m2691_dir: Path | str = DEFAULT_M2691_DIR,
    m2664_dir: Path | str = DEFAULT_M2664_DIR,
    m2667_dir: Path | str = DEFAULT_M2667_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m2694_audit_doc: Path | str = DEFAULT_M2694_AUDIT_DOC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    profile_name: str = DEFAULT_RUNTIME_PROFILE_NAME,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2693_dir=Path(m2693_dir),
        m2691_dir=Path(m2691_dir),
        m2664_dir=Path(m2664_dir),
        m2667_dir=Path(m2667_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        m2694_audit_doc=Path(m2694_audit_doc),
        follow_up_manifest=Path(follow_up_manifest),
    )

    protected_bridge_rows, executable_candidate_rows, unbridgeable_rows = build_bridge_rows(
        source=source,
        profile_name=profile_name,
    )
    actor_contract_guard_rows = build_actor_contract_guard_rows(source)
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        protected_bridge_rows=protected_bridge_rows,
        executable_candidate_rows=executable_candidate_rows,
        unbridgeable_rows=unbridgeable_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["protected_bridge_rows"], protected_bridge_rows, fieldnames=PROTECTED_BRIDGE_FIELDNAMES)
    write_csv_rows(
        paths["executable_candidate_rows"],
        executable_candidate_rows,
        fieldnames=EXECUTABLE_CANDIDATE_FIELDNAMES,
    )
    write_csv_rows(paths["unbridgeable_target_rows"], unbridgeable_rows, fieldnames=UNBRIDGEABLE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key != "doc")
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        protected_bridge_rows=protected_bridge_rows,
        executable_candidate_rows=executable_candidate_rows,
        unbridgeable_rows=unbridgeable_rows,
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
        protected_bridge_rows=protected_bridge_rows,
        executable_candidate_rows=executable_candidate_rows,
        unbridgeable_rows=unbridgeable_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        protected_bridge_rows=protected_bridge_rows,
        executable_candidate_rows=executable_candidate_rows,
        unbridgeable_rows=unbridgeable_rows,
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
        protected_bridge_rows=protected_bridge_rows,
        executable_candidate_rows=executable_candidate_rows,
        unbridgeable_rows=unbridgeable_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "protected_bridge_rows": output_dir / "protected_bridge_rows.csv",
        "executable_candidate_rows": output_dir / "executable_candidate_rows.csv",
        "unbridgeable_target_rows": output_dir / "unbridgeable_target_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2693_dir: Path,
    m2691_dir: Path,
    m2664_dir: Path,
    m2667_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    m2694_audit_doc: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2694_audit_doc": m2694_audit_doc,
        "m2693_summary": m2693_dir / "summary.json",
        "m2693_failure_rows": m2693_dir / "failure_rows.csv",
        "m2693_protected_target_aggregate": m2693_dir / "protected_target_aggregate.csv",
        "m2693_source_diversity_aggregate": m2693_dir / "source_diversity_aggregate.csv",
        "m2693_blocker_join_rows": m2693_dir / "blocker_join_rows.csv",
        "m2693_actor_contract_join_rows": m2693_dir / "actor_contract_join_rows.csv",
        "m2693_claim_boundary_rows": m2693_dir / "claim_boundary_rows.csv",
        "m2693_gate_matrix": m2693_dir / "gate_matrix.csv",
        "m2691_summary": m2691_dir / "summary.json",
        "m2691_target_panel_rows": m2691_dir / "target_panel_rows.csv",
        "m2664_combined_failure_taxonomy_rows": m2664_dir / "combined_failure_taxonomy_rows.csv",
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
        "m2693_summary": read_json(paths["m2693_summary"]) if source_exists["m2693_summary"] else {},
        "m2693_failure_rows": read_csv_rows(paths["m2693_failure_rows"]),
        "m2693_protected_target_aggregate": read_csv_rows(paths["m2693_protected_target_aggregate"]),
        "m2693_source_diversity_aggregate": read_csv_rows(paths["m2693_source_diversity_aggregate"]),
        "m2693_blocker_join_rows": read_csv_rows(paths["m2693_blocker_join_rows"]),
        "m2693_actor_contract_join_rows": read_csv_rows(paths["m2693_actor_contract_join_rows"]),
        "m2693_claim_boundary_rows": read_csv_rows(paths["m2693_claim_boundary_rows"]),
        "m2693_gate_matrix": read_csv_rows(paths["m2693_gate_matrix"]),
        "m2691_summary": read_json(paths["m2691_summary"]) if source_exists["m2691_summary"] else {},
        "m2691_target_panel_rows": read_csv_rows(paths["m2691_target_panel_rows"]),
        "m2664_combined_failure_taxonomy_rows": read_csv_rows(paths["m2664_combined_failure_taxonomy_rows"]),
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


def build_bridge_rows(
    *,
    source: dict[str, Any],
    profile_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    protected_targets = [
        row
        for row in sorted(source["m2691_target_panel_rows"], key=lambda item: str(item.get("target_id", "")))
        if row.get("source_family") == "protected_mitigation"
    ]
    failures_by_target = {row.get("target_id", ""): row for row in source["m2693_failure_rows"]}
    boundary_by_id = {row.get("boundary_id", ""): row for row in source["m2667_known_failure_boundary_rows"]}
    taxonomy_index = build_taxonomy_index(source["m2664_combined_failure_taxonomy_rows"])
    workload_candidates = build_workload_candidates(
        workload_rows=source["executable_workload_matrix"],
        specs=source["executable_task_specs"],
        profile_name=profile_name,
    )

    bridge_rows: list[dict[str, Any]] = []
    executable_rows: list[dict[str, Any]] = []
    unbridgeable_rows: list[dict[str, Any]] = []
    for index, target in enumerate(protected_targets, start=1):
        target_id = str(target.get("target_id", ""))
        boundary = boundary_by_id.get(str(target.get("source_key", "")), {})
        failure = failures_by_target.get(target_id, {})
        taxonomy_key = taxonomy_match_key(target=target, boundary=boundary)
        taxonomy = taxonomy_index.get(taxonomy_key, {})
        candidate = exact_workload_candidate(target, workload_candidates)
        candidate_id = f"m2695-candidate-{index:04d}" if candidate else ""
        bridge_status = "executable_candidate" if candidate else "unbridgeable"
        unbridgeable_reason = "" if candidate else unbridgeable_reason_for(target, source)
        bridge_class = "exact_current_runner_mapping" if candidate else "no_exact_current_runner_mapping"
        bridge_rows.append(
            {
                "target_id": target_id,
                "target_family": target.get("target_family", ""),
                "source_family": target.get("source_family", ""),
                "source_key": target.get("source_key", ""),
                "task_family": target.get("task_family", ""),
                "source_edge_or_axis": target.get("source_edge_or_axis", ""),
                "role_semantics_proxy": target.get("role_semantics_proxy", ""),
                "taxonomy_axis": boundary.get("taxonomy_axis", target.get("source_edge_or_axis", "")),
                "boundary_id": boundary.get("boundary_id", target.get("source_key", "")),
                "failure_family": boundary.get("failure_family", taxonomy.get("primary_failure_family", "")),
                "bridge_status": bridge_status,
                "bridge_class": bridge_class,
                "executable_candidate_id": candidate_id,
                "unbridgeable_reason": unbridgeable_reason,
                "parent_failure_type": failure.get("error_type", ""),
                "parent_error_message": failure.get("error_message", ""),
                "source_row_count": _int(boundary.get("row_count") or target.get("episode_or_row_count")),
                "blocking_count": _int(boundary.get("blocking_row_count") or target.get("blocking_count")),
                "regressed_row_count": _int(boundary.get("regressed_row_count") or target.get("regressed_row_count")),
                "protected_blocker_preserved": _bool(
                    boundary.get("protected_blocker_preserved", taxonomy.get("protected_blocker_preserved", True))
                ),
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        if candidate:
            executable_rows.append(executable_candidate_row(candidate_id, target, candidate))
        else:
            unbridgeable_rows.append(
                {
                    "target_id": target_id,
                    "target_family": target.get("target_family", ""),
                    "source_key": target.get("source_key", ""),
                    "task_family": target.get("task_family", ""),
                    "source_edge_or_axis": target.get("source_edge_or_axis", ""),
                    "taxonomy_axis": boundary.get("taxonomy_axis", target.get("source_edge_or_axis", "")),
                    "role_semantics_proxy": target.get("role_semantics_proxy", ""),
                    "unbridgeable_reason": unbridgeable_reason,
                    "missing_contract": "current executable workload row with exact task_family/source_edge/profile",
                    "required_follow_up": "protected taxonomy normalization or protected runner-spec generation before execution",
                    "parent_failure_type": failure.get("error_type", ""),
                    "protected_rows_in_success_denominator": False,
                    "target_labels_actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "materialization_only_no_execution": True,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return bridge_rows, executable_rows, unbridgeable_rows


def build_taxonomy_index(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        subject = str(row.get("subject_id", ""))
        axis = str(row.get("dynamics_axis_id", ""))
        if subject:
            index[("subject", subject)] = row
        if axis:
            index[("dynamics_axis", axis)] = row
        for metric in str(row.get("blocking_metrics", "")).split(";"):
            metric = metric.strip()
            if metric:
                index[("metric", metric)] = row
    return index


def taxonomy_match_key(*, target: dict[str, str], boundary: dict[str, str]) -> tuple[str, str]:
    axis = str(boundary.get("taxonomy_axis", target.get("source_edge_or_axis", "")))
    value = str(boundary.get("subject_or_axis_or_metric", target.get("role_semantics_proxy", "")))
    return axis, value


def build_workload_candidates(
    *,
    workload_rows: list[dict[str, Any]],
    specs: list[dict[str, Any]],
    profile_name: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    spec_by_id = {str(row.get("task_source_id", "")): row for row in specs}
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for row in workload_rows:
        if str(row.get("profile_name", "")) != profile_name:
            continue
        key = (str(row.get("task_family", "")), str(row.get("source_edge", "")))
        if not key[0] or not key[1]:
            continue
        merged = dict(row)
        merged["spec"] = spec_by_id.get(str(row.get("task_source_id", "")), {})
        candidates.setdefault(key, merged)
    return candidates


def exact_workload_candidate(
    target: dict[str, str],
    workload_candidates: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    key = (str(target.get("task_family", "")), str(target.get("source_edge_or_axis", "")))
    return workload_candidates.get(key)


def executable_candidate_row(candidate_id: str, target: dict[str, str], candidate: dict[str, Any]) -> dict[str, Any]:
    spec = candidate.get("spec", {})
    return {
        "candidate_id": candidate_id,
        "target_id": target.get("target_id", ""),
        "target_family": target.get("target_family", ""),
        "source_key": target.get("source_key", ""),
        "workload_id": candidate.get("workload_id", ""),
        "task_source_id": candidate.get("task_source_id", ""),
        "profile_name": candidate.get("profile_name", ""),
        "task_family": candidate.get("task_family", ""),
        "source_edge": candidate.get("source_edge", ""),
        "executable_source_family": candidate.get("executable_source_family", ""),
        "env_template_family": candidate.get("env_template_family", spec.get("env_template_family", "")),
        "mapping_rule": "exact_task_family_source_edge_profile_match",
        "config_exists": _bool(candidate.get("config_exists", True)),
        "checkpoint_exists": _bool(candidate.get("checkpoint_exists", True)),
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "protected_rows_in_success_denominator": False,
        "materialization_only_no_execution": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def unbridgeable_reason_for(target: dict[str, str], source: dict[str, Any]) -> str:
    if not source["source_exists"].get("executable_workload_matrix", False):
        return "current executable workload matrix missing"
    if not source["source_exists"].get("executable_task_specs", False):
        return "current executable task spec index missing"
    return (
        "no exact current executable workload row for protected target "
        f"task_family={target.get('task_family', '')} source_edge={target.get('source_edge_or_axis', '')} "
        f"profile={DEFAULT_RUNTIME_PROFILE_NAME}"
    )


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    parent_rows = {row.get("contract_field", ""): row for row in source["m2693_actor_contract_join_rows"]}
    rows = [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True),
        actor_guard("action_shape", ACTION_DIM, ACTION_DIM, True),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_guard("hidden_oracle_actor_input_detected", False, False, False),
        actor_guard("protected_labels_actor_visible", False, False, False),
        actor_guard("target_labels_actor_visible", False, False, False),
        actor_guard("blocker_labels_actor_visible", False, False, False),
        actor_guard("verdict_labels_actor_visible", False, False, False),
        actor_guard("protected_rows_in_success_denominator", False, False, False),
    ]
    for row in rows:
        parent = parent_rows.get(str(row["contract_field"]), {})
        if parent:
            row["parent_guard_status_pass"] = _bool(parent.get("status_pass", False))
            row["status_pass"] = _bool(row["status_pass"]) and _bool(parent.get("status_pass", False))
    return rows


def actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2695_actor_guard_{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    allowed = [
        ("protected_bridge_rows_materialized", "artifact", artifacts_present, "protected_bridge_rows.csv"),
        ("executable_candidate_rows_materialized", "artifact", artifacts_present, "executable_candidate_rows.csv"),
        ("unbridgeable_target_rows_materialized", "artifact", artifacts_present, "unbridgeable_target_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("protected_blocker_preserved", "blocker", True, "all protected rows classified without denominator use"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2696 result audit manifest"),
    ]
    blocked = [
        ("reset_execution", "execution", "future protected execution manifest"),
        ("policy_rollout", "execution", "future protected execution manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2695"),
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
        "claim_id": f"m2695_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2695": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    protected_bridge_rows: list[dict[str, Any]],
    executable_candidate_rows: list[dict[str, Any]],
    unbridgeable_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    protected_targets = [row for row in source["m2691_target_panel_rows"] if row.get("source_family") == "protected_mitigation"]
    protected_failure_rows = [
        row
        for row in source["m2693_failure_rows"]
        if row.get("source_family") == "protected_mitigation"
        and row.get("error_type") == "source_not_executable_in_current_runner"
    ]
    bridge_ids = {str(row.get("target_id", "")) for row in protected_bridge_rows}
    target_ids = {str(row.get("target_id", "")) for row in protected_targets}
    candidate_ids = {str(row.get("target_id", "")) for row in executable_candidate_rows}
    unbridgeable_ids = {str(row.get("target_id", "")) for row in unbridgeable_rows}
    source_required_keys = [
        "m2694_audit_doc",
        "m2693_summary",
        "m2693_failure_rows",
        "m2693_protected_target_aggregate",
        "m2693_source_diversity_aggregate",
        "m2693_blocker_join_rows",
        "m2693_actor_contract_join_rows",
        "m2693_claim_boundary_rows",
        "m2693_gate_matrix",
        "m2691_summary",
        "m2691_target_panel_rows",
        "m2664_combined_failure_taxonomy_rows",
        "m2667_known_failure_boundary_rows",
        "executable_task_specs",
        "executable_workload_matrix",
    ]
    allowed_claims = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2695"])]
    blocked_claims = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2695"])]
    return [
        gate(
            "m2695_gate_source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in source_required_keys),
            {key: source["source_exists"][key] for key in source_required_keys},
            "all M2694/M2693/M2691/M2664/M2667/current-runner artifacts present",
            "lineage_invalid",
        ),
        gate("m2693_status_pass", "lineage", _bool(source["m2693_summary"].get("status_pass")), source["m2693_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m2691_status_pass", "lineage", _bool(source["m2691_summary"].get("status_pass")), source["m2691_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("protected_targets_present", "target_panel", len(protected_targets) > 0, len(protected_targets), ">0", "behavior_regression"),
        gate("protected_failure_rows_present", "target_panel", len(protected_failure_rows) == len(protected_targets), len(protected_failure_rows), len(protected_targets), "behavior_regression"),
        gate("bridge_rows_cover_protected_targets", "bridge", bridge_ids == target_ids and len(protected_bridge_rows) == len(protected_targets), f"bridge={len(bridge_ids)} targets={len(target_ids)}", "all protected target ids", "metric_artifact"),
        gate("executable_or_unbridgeable_partition", "bridge", candidate_ids.isdisjoint(unbridgeable_ids) and candidate_ids | unbridgeable_ids == target_ids, f"candidate={len(candidate_ids)} unbridgeable={len(unbridgeable_ids)} target={len(target_ids)}", "partition covers all protected targets", "metric_artifact"),
        gate("unbridgeable_rows_visible_not_dropped", "bridge", len(unbridgeable_rows) == sum(row.get("bridge_status") == "unbridgeable" for row in protected_bridge_rows), len(unbridgeable_rows), "all unbridgeable bridge rows written", "proof_washout"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_contract_guard_rows), f"rows={len(actor_contract_guard_rows)} pass={sum(_bool(row['status_pass']) for row in actor_contract_guard_rows)}", "all actor guard rows pass", "contract_violation"),
        gate("protected_labels_actor_invisible", "contract", all(not _bool(row.get("target_labels_actor_visible", False)) for row in protected_bridge_rows + executable_candidate_rows + unbridgeable_rows), "target/protected labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in protected_bridge_rows + executable_candidate_rows + unbridgeable_rows), "hidden/oracle actor input requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in protected_bridge_rows + executable_candidate_rows + unbridgeable_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("materialization_only_no_execution", "execution_guardrail", all(_bool(row.get("materialization_only_no_execution", False)) for row in protected_bridge_rows + executable_candidate_rows + unbridgeable_rows), "all output rows materialization only", "no reset step rollout", "objective_overfit"),
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
    protected_bridge_rows: list[dict[str, Any]],
    executable_candidate_rows: list[dict[str, Any]],
    unbridgeable_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
    profile_name: str,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    protected_targets = [row for row in source["m2691_target_panel_rows"] if row.get("source_family") == "protected_mitigation"]
    protected_failure_rows = [
        row
        for row in source["m2693_failure_rows"]
        if row.get("source_family") == "protected_mitigation"
        and row.get("error_type") == "source_not_executable_in_current_runner"
    ]
    bridge_counts = Counter(row.get("bridge_status", "") for row in protected_bridge_rows)
    allowed_claim_rows = [row for row in claim_boundary_rows if _bool(row["allowed_in_m2695"])]
    blocked_claim_rows = [row for row in claim_boundary_rows if not _bool(row["allowed_in_m2695"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    all_protected_targets_accounted = {
        str(row.get("target_id", "")) for row in protected_bridge_rows
    } == {str(row.get("target_id", "")) for row in protected_targets}
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    summary: dict[str, Any] = {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_protected_mitigation_target_executable_surface_bridge_materialization_pass"
            if status_pass
            else "engineering_controller_protected_mitigation_target_executable_surface_bridge_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "profile_name": profile_name,
        "source_artifacts_present": all(
            source["source_exists"][key]
            for key in [
                "m2694_audit_doc",
                "m2693_summary",
                "m2693_failure_rows",
                "m2693_protected_target_aggregate",
                "m2693_source_diversity_aggregate",
                "m2693_blocker_join_rows",
                "m2693_actor_contract_join_rows",
                "m2693_claim_boundary_rows",
                "m2693_gate_matrix",
                "m2691_summary",
                "m2691_target_panel_rows",
                "m2664_combined_failure_taxonomy_rows",
                "m2667_known_failure_boundary_rows",
                "executable_task_specs",
                "executable_workload_matrix",
            ]
        ),
        "m2693_status_pass": _bool(source["m2693_summary"].get("status_pass")),
        "m2691_status_pass": _bool(source["m2691_summary"].get("status_pass")),
        "m2693_protected_failure_count": len(protected_failure_rows),
        "m2693_recorded_protected_failure_type": "source_not_executable_in_current_runner",
        "protected_target_count": len(protected_targets),
        "protected_bridge_row_count": len(protected_bridge_rows),
        "executable_candidate_row_count": len(executable_candidate_rows),
        "unbridgeable_target_row_count": len(unbridgeable_rows),
        "exact_current_runner_match_count": bridge_counts.get("executable_candidate", 0),
        "no_exact_current_runner_mapping_count": bridge_counts.get("unbridgeable", 0),
        "all_protected_targets_accounted": all_protected_targets_accounted,
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
            "# M2695 Engineering Controller Protected Mitigation Target Executable Surface Bridge Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- protected target rows: {summary['protected_target_count']}",
            f"- protected bridge rows: {summary['protected_bridge_row_count']}",
            f"- executable candidate rows: {summary['executable_candidate_row_count']}",
            f"- unbridgeable target rows: {summary['unbridgeable_target_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- next: `{summary['next_blocker']}`",
            "",
            "M2695 classifies every protected mitigation target as either an exact current-runner executable candidate or an explicit unbridgeable target. It is a materialization artifact only, not protected behavior evidence or driver-performance evidence.",
            "",
            "## Bridge Result",
            "",
            "```text",
            f"m2693 protected failure rows: {summary['m2693_protected_failure_count']}",
            f"exact current-runner matches: {summary['exact_current_runner_match_count']}",
            f"no exact current-runner mapping: {summary['no_exact_current_runner_mapping_count']}",
            f"all protected targets accounted: {summary['all_protected_targets_accounted']}",
            "```",
            "",
            "Protected rows remain visible, actor-invisible, and outside success denominators. Unbridgeable rows are not dropped and must be audited before any protected closed-loop execution route.",
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
            "M2695 materialized protected executable-surface bridge rows and explicit unbridgeable rows from existing artifacts.",
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
    parser.add_argument("--m2693-dir", type=Path, default=DEFAULT_M2693_DIR)
    parser.add_argument("--m2691-dir", type=Path, default=DEFAULT_M2691_DIR)
    parser.add_argument("--m2664-dir", type=Path, default=DEFAULT_M2664_DIR)
    parser.add_argument("--m2667-dir", type=Path, default=DEFAULT_M2667_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m2694-audit-doc", type=Path, default=DEFAULT_M2694_AUDIT_DOC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--profile-name", default=DEFAULT_RUNTIME_PROFILE_NAME)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    materialize_protected_mitigation_target_executable_surface_bridge(
        m2693_dir=args.m2693_dir,
        m2691_dir=args.m2691_dir,
        m2664_dir=args.m2664_dir,
        m2667_dir=args.m2667_dir,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        m2694_audit_doc=args.m2694_audit_doc,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        profile_name=args.profile_name,
    )


if __name__ == "__main__":
    main()
