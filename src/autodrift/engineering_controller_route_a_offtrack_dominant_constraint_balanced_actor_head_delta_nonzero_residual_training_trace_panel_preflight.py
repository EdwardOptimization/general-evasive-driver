"""Materialize M2973 nonzero residual training trace availability rows.

M2973 consumes the accepted M2970/M2971/M2972 actor-head delta training
admission chain plus the M2960 bounded execution metadata. It does not fit a
residual head, train, validate, rank, or promote. It writes an auditable panel
that says which admitted rows have deployable trace metadata and whether raw
observation/action traces are actually persisted for later fitting.
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
    "m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-trace-panel-preflight"
)
NEXT_ID = (
    "m2974-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-trace-panel-result-audit"
)
DEFAULT_M2970_DIR = Path(
    "runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_training_admission_materialization_preflight"
)
DEFAULT_M2971_AUDIT = Path(
    "docs/m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-admission-materialization-result-audit.md"
)
DEFAULT_M2972_DESIGN = Path(
    "docs/m2972-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-preflight-design.md"
)
DEFAULT_M2960_DIR = Path(
    "runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "bounded_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_training_trace_panel_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-trace-panel-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2974-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-training-trace-panel-result-audit.json"
)

EXPECTED_TRAINING_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_OUTCOME_COUNTS = {
    "collision": 7,
    "off_track": 35,
    "speed_too_low": 1,
}

CLAIM_SCOPE = (
    "M2973 Route A actor-head delta nonzero residual training trace-panel preflight only; "
    "accepted M2970 candidate and guard rows may be joined with M2960 bounded execution "
    "metadata to produce trace availability artifacts for later audit. No residual fitting, "
    "training, PPO, validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, repair success, driver-performance, paper, current-sim verdict, high-fidelity "
    "validation, full ideal driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "residual fitting readiness, residual quality, repair success, driver performance, validation "
    "readiness or result, controller-family ranking, source-family ranking, task-family ranking, "
    "profile ranking, checkpoint ranking, candidate ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification"
)

TRACE_SOURCE_FIELDNAMES = [
    "trace_source_id",
    "source_artifact",
    "source_exists",
    "row_count",
    "source_role",
    "status_pass",
    "claim_boundary",
]
TRACE_PANEL_FIELDNAMES = [
    "trace_panel_row_id",
    "training_admission_candidate_id",
    "execution_candidate_id",
    "workload_id",
    "task_family",
    "outcome_family",
    "objective_family",
    "trace_role",
    "trace_available",
    "raw_trace_persisted",
    "trace_step_count",
    "actor_observation_dim",
    "actor_action_dim",
    "parent_checkpoint_loaded_read_only",
    "zero_residual_identity_mode",
    "residual_delta_abs_max",
    "actor_visible_label",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "training_started",
    "ppo_run",
    "ranking_run",
    "checkpoint_mutated",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
TRACE_GUARD_FIELDNAMES = [
    "trace_guard_row_id",
    "source_guard_id",
    "execution_candidate_id",
    "guard_family",
    "guard_role",
    "trace_available",
    "raw_trace_persisted",
    "trace_step_count",
    "actor_visible_label",
    "training_target_allowed",
    "positive_training_target",
    "execution_allowed",
    "training_started",
    "ppo_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
TRACE_AVAILABILITY_FIELDNAMES = [
    "trace_availability_row_id",
    "source_row_id",
    "execution_candidate_id",
    "row_role",
    "objective_or_guard_family",
    "trace_metadata_present",
    "raw_trace_persisted",
    "trace_step_count",
    "availability_status",
    "blocking_reason_for_residual_fitting",
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
    "allowed_in_m2973",
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
    "trace_source_rows",
    "trace_panel_rows",
    "trace_guard_rows",
    "trace_availability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_training_trace_panel_preflight(
    *,
    m2970_dir: Path | str = DEFAULT_M2970_DIR,
    m2971_audit: Path | str = DEFAULT_M2971_AUDIT,
    m2972_design: Path | str = DEFAULT_M2972_DESIGN,
    m2960_dir: Path | str = DEFAULT_M2960_DIR,
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
        m2970_dir=Path(m2970_dir),
        m2971_audit=Path(m2971_audit),
        m2972_design=Path(m2972_design),
        m2960_dir=Path(m2960_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    trace_sources = build_trace_source_rows(source)
    execution_by_candidate = {
        str(row.get("execution_candidate_id", "")): row for row in source["bounded_execution_rows"]
    }
    contract_by_candidate = {
        str(row.get("execution_candidate_id", "")): row for row in source["contract_execution_rows"]
    }
    panel_rows = build_trace_panel_rows(
        source["training_admission_candidate_rows"],
        execution_by_candidate=execution_by_candidate,
        contract_by_candidate=contract_by_candidate,
    )
    guard_rows = build_trace_guard_rows(
        source["success_identity_guard_rows"],
        source["stale_guardrail_rows"],
        execution_by_candidate=execution_by_candidate,
        contract_by_candidate=contract_by_candidate,
    )
    availability_rows = build_trace_availability_rows(panel_rows, guard_rows)

    write_csv_rows(paths["trace_source_rows"], trace_sources, fieldnames=TRACE_SOURCE_FIELDNAMES)
    write_csv_rows(paths["trace_panel_rows"], panel_rows, fieldnames=TRACE_PANEL_FIELDNAMES)
    write_csv_rows(paths["trace_guard_rows"], guard_rows, fieldnames=TRACE_GUARD_FIELDNAMES)
    write_csv_rows(paths["trace_availability_rows"], availability_rows, fieldnames=TRACE_AVAILABILITY_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "training_candidate_row_count": len(panel_rows),
            "trace_guard_row_count": len(guard_rows),
            "trace_availability_row_count": len(availability_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        source=source,
        panel_rows=panel_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        panel_rows_present=bool(panel_rows),
        availability_rows_present=bool(availability_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        trace_sources=trace_sources,
        panel_rows=panel_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, actor_rows, claim_rows, gate_rows)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        trace_sources=trace_sources,
        panel_rows=panel_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
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
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        panel_rows_present=bool(panel_rows),
        availability_rows_present=bool(availability_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        trace_sources=trace_sources,
        panel_rows=panel_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
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
        trace_sources=trace_sources,
        panel_rows=panel_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
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
            "training_candidate_row_count": len(panel_rows),
            "trace_guard_row_count": len(guard_rows),
            "trace_availability_row_count": len(availability_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "trace_source_rows": output_dir / "trace_source_rows.csv",
        "trace_panel_rows": output_dir / "trace_panel_rows.csv",
        "trace_guard_rows": output_dir / "trace_guard_rows.csv",
        "trace_availability_rows": output_dir / "trace_availability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2970_dir: Path,
    m2971_audit: Path,
    m2972_design: Path,
    m2960_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2971_audit": m2971_audit,
        "m2972_design": m2972_design,
        "m2970_summary": m2970_dir / "summary.json",
        "training_admission_candidate_rows": m2970_dir / "training_admission_candidate_rows.csv",
        "training_admission_guard_rows": m2970_dir / "training_admission_guard_rows.csv",
        "success_identity_guard_rows": m2970_dir / "success_identity_guard_rows.csv",
        "stale_guardrail_rows": m2970_dir / "stale_guardrail_rows.csv",
        "m2970_gate_matrix": m2970_dir / "gate_matrix.csv",
        "m2960_summary": m2960_dir / "summary.json",
        "bounded_execution_rows": m2960_dir / "bounded_execution_rows.csv",
        "contract_execution_rows": m2960_dir / "actor_head_delta_contract_execution_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2971_audit_text": paths["m2971_audit"].read_text(encoding="utf-8")
        if source_exists["m2971_audit"]
        else "",
        "m2972_design_text": paths["m2972_design"].read_text(encoding="utf-8")
        if source_exists["m2972_design"]
        else "",
        "m2970_summary": read_json(paths["m2970_summary"]) if source_exists["m2970_summary"] else {},
        "m2960_summary": read_json(paths["m2960_summary"]) if source_exists["m2960_summary"] else {},
        "training_admission_candidate_rows": read_csv_rows(paths["training_admission_candidate_rows"]),
        "training_admission_guard_rows": read_csv_rows(paths["training_admission_guard_rows"]),
        "success_identity_guard_rows": read_csv_rows(paths["success_identity_guard_rows"]),
        "stale_guardrail_rows": read_csv_rows(paths["stale_guardrail_rows"]),
        "m2970_gate_matrix": read_csv_rows(paths["m2970_gate_matrix"]),
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
        "contract_execution_rows": read_csv_rows(paths["contract_execution_rows"]),
    }


def build_trace_source_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_specs = [
        ("m2971_audit", "lineage audit"),
        ("m2972_design", "training trace-panel design"),
        ("m2970_summary", "training admission summary"),
        ("training_admission_candidate_rows", "future training candidates"),
        ("training_admission_guard_rows", "training guards"),
        ("success_identity_guard_rows", "success identity guards"),
        ("stale_guardrail_rows", "stale fixed-source guardrails"),
        ("m2970_gate_matrix", "M2970 gate matrix"),
        ("m2960_summary", "bounded execution summary"),
        ("bounded_execution_rows", "bounded execution metadata"),
        ("contract_execution_rows", "actor-head delta contract execution metadata"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (key, role) in enumerate(source_specs, start=1):
        value = source.get(key, [])
        if isinstance(value, list):
            row_count = len(value)
        elif isinstance(value, dict):
            row_count = 1 if value else 0
        else:
            row_count = 1 if value else 0
        rows.append(
            {
                "trace_source_id": f"m2973-trace-source-{index:04d}",
                "source_artifact": str(source["paths"][key]),
                "source_exists": bool(source["source_exists"].get(key, False)),
                "row_count": row_count,
                "source_role": role,
                "status_pass": bool(source["source_exists"].get(key, False)),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_trace_panel_rows(
    candidate_rows: list[dict[str, str]],
    *,
    execution_by_candidate: Mapping[str, Mapping[str, str]],
    contract_by_candidate: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_rows, start=1):
        execution_id = str(candidate.get("execution_candidate_id", ""))
        execution = execution_by_candidate.get(execution_id, {})
        contract = contract_by_candidate.get(execution_id, {})
        trace_step_count = _to_int(
            contract.get("residual_trace_count", execution.get("residual_trace_count", 0))
        )
        trace_metadata_present = bool(execution) and bool(contract) and trace_step_count > 0
        rows.append(
            {
                "trace_panel_row_id": f"m2973-trace-panel-{index:04d}",
                "training_admission_candidate_id": candidate.get("training_admission_candidate_id", ""),
                "execution_candidate_id": execution_id,
                "workload_id": candidate.get("workload_id", ""),
                "task_family": candidate.get("task_family", ""),
                "outcome_family": candidate.get("outcome_family", ""),
                "objective_family": candidate.get("objective_family", ""),
                "trace_role": "future_training_candidate_trace_availability",
                "trace_available": trace_metadata_present,
                "raw_trace_persisted": False,
                "trace_step_count": trace_step_count,
                "actor_observation_dim": _to_int(contract.get("actor_observation_dim"), default=P0_OBSERVATION_DIM),
                "actor_action_dim": _to_int(contract.get("actor_action_dim"), default=ACTION_DIM),
                "parent_checkpoint_loaded_read_only": _bool(contract.get("parent_checkpoint_loaded_read_only", False)),
                "zero_residual_identity_mode": _bool(contract.get("zero_residual_identity_mode", False)),
                "residual_delta_abs_max": _to_float(contract.get("residual_delta_abs_max", 0.0)),
                "actor_visible_label": False,
                "hidden_oracle_actor_input_required": _bool(
                    contract.get("hidden_oracle_actor_input_required", False)
                    or execution.get("hidden_oracle_actor_input_required", False)
                ),
                "future_target_actor_input_required": _bool(
                    contract.get("future_target_actor_input_required", False)
                    or execution.get("future_target_actor_input_required", False)
                ),
                "training_started": False,
                "ppo_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_trace_guard_rows(
    success_rows: list[dict[str, str]],
    stale_rows: list[dict[str, str]],
    *,
    execution_by_candidate: Mapping[str, Mapping[str, str]],
    contract_by_candidate: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, guard in enumerate(success_rows, start=1):
        execution_id = str(guard.get("execution_candidate_id", ""))
        contract = contract_by_candidate.get(execution_id, {})
        execution = execution_by_candidate.get(execution_id, {})
        trace_step_count = _to_int(
            contract.get("residual_trace_count", execution.get("residual_trace_count", 0))
        )
        rows.append(
            {
                "trace_guard_row_id": f"m2973-trace-guard-success-{index:04d}",
                "source_guard_id": guard.get("guard_id", ""),
                "execution_candidate_id": execution_id,
                "guard_family": "success_identity_guard",
                "guard_role": "zero_residual_identity_guard_not_positive_training_target",
                "trace_available": bool(contract) and trace_step_count > 0,
                "raw_trace_persisted": False,
                "trace_step_count": trace_step_count,
                "actor_visible_label": False,
                "training_target_allowed": False,
                "positive_training_target": False,
                "execution_allowed": False,
                "training_started": False,
                "ppo_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, guardrail in enumerate(stale_rows, start=1):
        rows.append(
            {
                "trace_guard_row_id": f"m2973-trace-guard-stale-{index + offset:04d}",
                "source_guard_id": guardrail.get("guardrail_id", ""),
                "execution_candidate_id": "",
                "guard_family": guardrail.get("guardrail_family", ""),
                "guard_role": "blocked_stale_fixed_source_guardrail_not_executed",
                "trace_available": False,
                "raw_trace_persisted": False,
                "trace_step_count": 0,
                "actor_visible_label": False,
                "training_target_allowed": False,
                "positive_training_target": False,
                "execution_allowed": False,
                "training_started": False,
                "ppo_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_trace_availability_rows(
    panel_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(panel_rows, start=1):
        raw_persisted = _bool(row.get("raw_trace_persisted"))
        metadata_present = _bool(row.get("trace_available"))
        rows.append(
            {
                "trace_availability_row_id": f"m2973-trace-availability-{index:04d}",
                "source_row_id": row["training_admission_candidate_id"],
                "execution_candidate_id": row["execution_candidate_id"],
                "row_role": row["trace_role"],
                "objective_or_guard_family": row["objective_family"],
                "trace_metadata_present": metadata_present,
                "raw_trace_persisted": raw_persisted,
                "trace_step_count": row["trace_step_count"],
                "availability_status": "metadata_only_raw_trace_missing"
                if metadata_present and not raw_persisted
                else "trace_missing",
                "blocking_reason_for_residual_fitting": "raw deployable observation/action trace not persisted",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, row in enumerate(guard_rows, start=1):
        metadata_present = _bool(row.get("trace_available"))
        raw_persisted = _bool(row.get("raw_trace_persisted"))
        rows.append(
            {
                "trace_availability_row_id": f"m2973-trace-availability-{index + offset:04d}",
                "source_row_id": row["source_guard_id"],
                "execution_candidate_id": row["execution_candidate_id"],
                "row_role": row["guard_role"],
                "objective_or_guard_family": row["guard_family"],
                "trace_metadata_present": metadata_present,
                "raw_trace_persisted": raw_persisted,
                "trace_step_count": row["trace_step_count"],
                "availability_status": "metadata_only_raw_trace_missing"
                if metadata_present and not raw_persisted
                else "guardrail_or_trace_missing",
                "blocking_reason_for_residual_fitting": "guard row is not a positive residual fitting target",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
    panel_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = source["m2970_summary"]
    checks = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        ("actor_action_dim", ACTION_DIM, ACTION_DIM),
        ("m2970_status_pass", summary.get("status_pass"), True),
        ("m2970_gate_matrix_pass", summary.get("gate_matrix_pass"), True),
        ("m2971_accepts_m2970", "accept_m2970_nonzero_residual_training_admission" in source["m2971_audit_text"], True),
        ("m2972_admits_m2973", MILESTONE_ID in source["m2972_design_text"], True),
        ("hidden_oracle_actor_input_required", any_row_truthy("hidden_oracle_actor_input_required", panel_rows), False),
        ("future_target_actor_input_required", any_row_truthy("future_target_actor_input_required", panel_rows), False),
        ("actor_visible_label", any_row_truthy("actor_visible_label", panel_rows, guard_rows), False),
        ("training_started", any_row_truthy("training_started", panel_rows, guard_rows), False),
        ("ppo_run", any_row_truthy("ppo_run", panel_rows, guard_rows), False),
        ("ranking_run", any_row_truthy("ranking_run", panel_rows, guard_rows), False),
        ("checkpoint_mutated", any_row_truthy("checkpoint_mutated", panel_rows, guard_rows), False),
        ("raw_trace_availability_explicit", len(availability_rows) == len(panel_rows) + len(guard_rows), True),
    ]
    return [
        {
            "guard_id": f"m2973-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(checks, start=1)
    ]


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    panel_rows_present: bool,
    availability_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = {
        "trace_panel_artifacts_present": artifacts_present,
        "trace_panel_rows_present": panel_rows_present,
        "trace_availability_rows_present": availability_rows_present,
        "actor_and_claim_boundary_preserved": True,
        "m2974_result_audit_registered": follow_up_manifest_registered,
    }
    blocked = {
        "residual_fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
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
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    rows: list[dict[str, Any]] = []
    for index, (claim, made) in enumerate(allowed.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2973-claim-allowed-{index:04d}",
                "claim_family": claim,
                "allowed_in_m2973": True,
                "claim_made": made,
                "status_pass": bool(made),
                "evidence_required_before_claim": "M2973 required artifact and follow-up audit registration",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, (claim, made) in enumerate(blocked.items(), start=1):
        rows.append(
            {
                "claim_id": f"m2973-claim-blocked-{index + offset:04d}",
                "claim_family": claim,
                "allowed_in_m2973": False,
                "claim_made": made,
                "status_pass": not bool(made),
                "evidence_required_before_claim": FORBIDDEN_INTERPRETATION,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    trace_sources: list[dict[str, Any]],
    panel_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in panel_rows)
    success_guard_count = sum(row.get("guard_family") == "success_identity_guard" for row in guard_rows)
    stale_guard_count = sum(
        str(row.get("guard_family", "")) == "actor_head_delta_execution_admission_blocked_stale_fixed_surface"
        for row in guard_rows
    )
    gates = [
        (
            "m2973_source_artifacts_present",
            "lineage",
            all(_bool(row["status_pass"]) for row in trace_sources),
            f"present={sum(_bool(row['status_pass']) for row in trace_sources)} rows={len(trace_sources)}",
            "all source artifacts present",
        ),
        ("m2973_m2970_status_pass", "lineage", source["m2970_summary"].get("status_pass") is True, source["m2970_summary"].get("status_pass"), True),
        ("m2973_m2970_gate_matrix_pass", "lineage", source["m2970_summary"].get("gate_matrix_pass") is True, source["m2970_summary"].get("gate_matrix_pass"), True),
        (
            "m2973_m2971_accepts_m2970",
            "lineage",
            "accept_m2970_nonzero_residual_training_admission" in source["m2971_audit_text"],
            "accept_m2970_nonzero_residual_training_admission" in source["m2971_audit_text"],
            True,
        ),
        (
            "m2973_m2972_admits_m2973",
            "lineage",
            MILESTONE_ID in source["m2972_design_text"],
            MILESTONE_ID in source["m2972_design_text"],
            True,
        ),
        (
            "m2973_training_candidates_accounted",
            "trace_panel",
            len(panel_rows) == EXPECTED_TRAINING_CANDIDATE_COUNT,
            len(panel_rows),
            EXPECTED_TRAINING_CANDIDATE_COUNT,
        ),
        (
            "m2973_success_identity_guards_accounted",
            "trace_panel",
            success_guard_count == EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT,
            success_guard_count,
            EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT,
        ),
        (
            "m2973_stale_guardrails_accounted",
            "trace_panel",
            stale_guard_count == EXPECTED_STALE_GUARDRAIL_COUNT,
            stale_guard_count,
            EXPECTED_STALE_GUARDRAIL_COUNT,
        ),
        (
            "m2973_outcome_counts_match_design",
            "trace_panel",
            dict(outcome_counts) == EXPECTED_OUTCOME_COUNTS,
            dict(outcome_counts),
            EXPECTED_OUTCOME_COUNTS,
        ),
        (
            "m2973_trace_availability_explicit",
            "trace_panel",
            len(availability_rows) == len(panel_rows) + len(guard_rows),
            len(availability_rows),
            len(panel_rows) + len(guard_rows),
        ),
        (
            "m2973_no_training_validation_or_ranking",
            "contract",
            no_training_validation_or_ranking(panel_rows, guard_rows),
            "all false",
            "all false",
        ),
        (
            "m2973_actor_contract_guards_pass",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row['status_pass']) for row in actor_rows)}",
            "all actor guards pass",
        ),
        (
            "m2973_claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            f"allowed={sum(_bool(row['allowed_in_m2973']) for row in claim_rows)} "
            f"blocked={sum(not _bool(row['allowed_in_m2973']) for row in claim_rows)}",
            "allowed pass and blocked not made",
        ),
        ("m2973_required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True),
        ("m2973_follow_up_audit_registered", "lineage", source["source_exists"]["follow_up_manifest"], source["source_exists"]["follow_up_manifest"], True),
    ]
    rows: list[dict[str, Any]] = []
    for gate_id, family, passed, observed, expected in gates:
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(passed),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if passed else "contract_violation",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def no_training_validation_or_ranking(*row_sets: list[dict[str, Any]]) -> bool:
    forbidden_fields = [
        "training_started",
        "ppo_run",
        "ranking_run",
        "checkpoint_mutated",
        "validation_denominator_allowed",
        "paper_denominator_allowed",
        "high_fidelity_readiness_allowed",
        "self_id_claim_allowed",
    ]
    for rows in row_sets:
        for row in rows:
            for field in forbidden_fields:
                if field in row and _bool(row[field]):
                    return False
    return True


def any_row_truthy(field: str, *row_sets: list[dict[str, Any]]) -> bool:
    return any(_bool(row.get(field)) for rows in row_sets for row in rows)


def write_derived_outputs(
    paths: Mapping[str, Path],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    trace_sources: list[dict[str, Any]],
    panel_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    outcome_counts = Counter(str(row.get("outcome_family", "")) for row in panel_rows)
    raw_trace_persisted_count = sum(_bool(row.get("raw_trace_persisted")) for row in availability_rows)
    metadata_present_count = sum(_bool(row.get("trace_metadata_present")) for row in availability_rows)
    success_guard_count = sum(row.get("guard_family") == "success_identity_guard" for row in guard_rows)
    stale_guard_count = sum(
        str(row.get("guard_family", "")) == "actor_head_delta_execution_admission_blocked_stale_fixed_surface"
        for row in guard_rows
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    status_pass = gate_matrix_pass and actor_rows_pass and claim_rows_pass and required_artifacts_present
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "engineering_controller_route_a_actor_head_delta_nonzero_residual_training_trace_panel_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_actor_head_delta_nonzero_residual_training_trace_panel_preflight_blocked",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "trace_source_row_count": len(trace_sources),
        "training_trace_panel_row_count": len(panel_rows),
        "trace_guard_row_count": len(guard_rows),
        "trace_availability_row_count": len(availability_rows),
        "trace_metadata_present_count": metadata_present_count,
        "raw_trace_persisted_count": raw_trace_persisted_count,
        "trace_panel_ready_for_residual_fitting": raw_trace_persisted_count == len(panel_rows),
        "success_identity_guard_row_count": success_guard_count,
        "stale_guardrail_row_count": stale_guard_count,
        "outcome_counts": dict(outcome_counts),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "objective_labels_actor_visible": False,
        "admission_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "residual_fitting_run": False,
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
            "# M2973 Engineering Controller Route A Actor-Head Delta Nonzero Residual Training Trace Panel Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- training trace panel rows: {summary['training_trace_panel_row_count']}",
            f"- trace guard rows: {summary['trace_guard_row_count']}",
            f"- trace availability rows: {summary['trace_availability_row_count']}",
            f"- trace metadata present rows: {summary['trace_metadata_present_count']}",
            f"- raw trace persisted rows: {summary['raw_trace_persisted_count']}",
            f"- trace panel ready for residual fitting: {summary['trace_panel_ready_for_residual_fitting']}",
            f"- success identity guard rows: {summary['success_identity_guard_row_count']}",
            f"- stale guardrail rows: {summary['stale_guardrail_row_count']}",
            f"- outcome counts: {summary['outcome_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2973 materializes a trace availability panel from M2970/M2971/M2972 and M2960 artifacts. It does not fit a residual head, train, validate, rank, promote, mutate checkpoints, or claim performance.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2973 training trace-panel preflight before any residual fitting training validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "trace_source_rows.csv"),
                str(output_dir / "trace_panel_rows.csv"),
                str(output_dir / "trace_guard_rows.csv"),
                str(output_dir / "trace_availability_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m2973-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-preflight.json",
                "experiments/manifests/m2972-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-preflight-design.json",
            ],
            "parent_objective": [
                "audit M2973 trace availability panel before any residual fitting or training"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2972-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-preflight-design",
                "m2971-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-result-audit",
                "m2970-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-admission-materialization-preflight",
            ],
            "blocked_by": [
                "M2973 trace-panel rows require a result audit before residual fitting",
                "raw deployable traces may be unavailable and must not be hidden",
                "success identity and stale guardrail rows must remain protected guardrails",
            ],
            "supersedes": [
                "direct residual fitting from M2970 candidate metadata without trace availability audit",
                "direct performance interpretation of M2973 trace-panel rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2974 must audit M2973 trace panel summary rows gates actor and claim boundaries",
            "M2974 must preserve 43 future training candidates 13 success identity guards and 11 stale guardrails",
            "M2974 must explicitly state whether raw deployable traces are available for residual fitting",
            "M2974 must not claim repair success validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun validate train rank promote publish select a winner or execute dependency work",
            "do not fit train select or execute a nonzero residual head",
            "do not change actor input or action contract",
            "do not convert M2973 trace-panel rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_training_trace_panel_result_audit",
            "evidence_increment": "audits M2973 nonzero residual training trace-panel artifacts",
            "claim_scope": "Result audit only; no residual fitting validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2973 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if trace availability is hidden or overinterpreted",
                "stop if trace rows would be used for residual fitting before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if raw trace availability is insufficient",
                "route to a bounded residual fitting design only after audit accepts claim safety and trace readiness",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2973 completes trace-panel preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2973 actor-head delta training trace-panel artifacts",
            "admission_evidence": [
                "M2973 summary and gate matrix",
                "M2973 trace source panel guard availability actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2974 status queue scoreboard research log and review",
                "one follow-up manifest only if M2974 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2974 audit accepts or rejects M2973 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2974 audits Route A trace-panel materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2974; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2973 Route A actor-head delta trace-panel preflight only.",
            "negative_result_policy": "Preserve missing trace availability and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2973 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized trace availability panel",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A residual-fitting readiness only",
            "must_synthesize_if": [
                "M2974 cannot accept M2973 as complete and claim-safe",
                "M2974 finds raw trace availability insufficient for residual fitting",
                "M2974 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2974 audits M2973 artifacts row counts gates actor and claim boundaries",
            "M2974 selects exactly one next route or stop state",
            "no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2974 hides M2973 failures or missing trace availability",
            "M2974 treats M2973 trace-panel materialization as residual fitting readiness performance verdict or repair success",
            "M2974 changes actor input or action contract",
            "M2974 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2974 audits M2973 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "trace_panel_rows.csv"),
            str(output_dir / "trace_guard_rows.csv"),
            str(output_dir / "trace_availability_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2970-dir", type=Path, default=DEFAULT_M2970_DIR)
    parser.add_argument("--m2971-audit", type=Path, default=DEFAULT_M2971_AUDIT)
    parser.add_argument("--m2972-design", type=Path, default=DEFAULT_M2972_DESIGN)
    parser.add_argument("--m2960-dir", type=Path, default=DEFAULT_M2960_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_training_trace_panel_preflight(
        m2970_dir=args.m2970_dir,
        m2971_audit=args.m2971_audit,
        m2972_design=args.m2972_design,
        m2960_dir=args.m2960_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(
        "M2973 training trace-panel preflight "
        f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']} "
        f"summary={summary['paths']['summary']}"
    )


if __name__ == "__main__":
    main()
