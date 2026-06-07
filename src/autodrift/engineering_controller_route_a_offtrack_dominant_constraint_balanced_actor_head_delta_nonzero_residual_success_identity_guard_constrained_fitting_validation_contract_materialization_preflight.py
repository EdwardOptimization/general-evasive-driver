"""Materialize M2996 validation-contract rows for the M2993 residual head.

M2996 consumes the M2994-accepted M2993 guard-constrained fitting artifact and
the M2995 admission design. It writes machine-checkable wrapper, comparison,
success-retention, stale-exclusion, actor-input, side-effect, claim, and gate
rows before any closed-loop validation can be considered. It does not run
environment reset/step/rollout, validation, ranking, winner selection,
checkpoint mutation, checkpoint promotion, private holdout, or performance
measurement.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight import (  # noqa: E501
    bool_value,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-preflight"
)
NEXT_ID = (
    "m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-result-audit"
)
DEFAULT_M2993_DIR = Path(
    "runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_success_identity_guard_constrained_fitting_preflight"
)
DEFAULT_M2994_AUDIT = Path(
    "docs/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-result-audit.md"
)
DEFAULT_M2995_DESIGN = Path(
    "docs/m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-"
    "materialization-result-audit.json"
)

EXPECTED_VALIDATION_CONTRACT_COUNT = 43
EXPECTED_SUCCESS_RETENTION_COUNT = 13
EXPECTED_STALE_EXCLUSION_COUNT = 11
EXPECTED_ACTOR_EXCLUSION_COUNT = 14
EXPECTED_SIDE_EFFECT_COUNT = 12
EXPECTED_RESIDUAL_LIMIT = 0.07999999821186066
EXPECTED_SUCCESS_ABS_MAX = 1.0e-3
PARENT_CHECKPOINTS = [
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
    "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
]

CLAIM_SCOPE = (
    "M2996 Route A actor-head delta nonzero residual validation-contract materialization preflight only; "
    "the M2994-accepted M2993 guard-constrained residual-head artifact may be bound to read-only wrapper, "
    "parent-comparison, candidate-validation-denominator, success-behavior-retention, stale-exclusion, "
    "actor-input, side-effect, claim, and gate contracts for a later result audit. No environment reset, "
    "step, rollout, validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "private holdout, performance measurement, repair-success, driver-performance, paper, current-sim, "
    "high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality validation, closed-loop validation result, repair success, driver performance, "
    "controller/source/task/profile/checkpoint/candidate ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification"
)

VALIDATION_CONTRACT_FIELDNAMES = [
    "validation_contract_id",
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "raw_trace_path",
    "target_tensor_path",
    "validation_denominator_planned",
    "parent_comparison_planned",
    "candidate_wrapper_planned",
    "target_quality_validated",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "validation_run",
    "ranking_run",
    "winner_selection_run",
    "checkpoint_mutation_planned",
    "status_pass",
    "claim_boundary",
]
RESIDUAL_HEAD_WRAPPER_FIELDNAMES = [
    "wrapper_contract_id",
    "contract_family",
    "artifact_path",
    "artifact_exists",
    "linear_weight_shape",
    "linear_bias_shape",
    "observation_dim",
    "action_dim",
    "residual_limit",
    "success_guard_required_abs_max",
    "read_only_candidate_artifact",
    "parent_checkpoint_read_only",
    "actor_input_shape_preserved",
    "action_shape_preserved",
    "residual_clipping_bound",
    "wrapper_execution_planned",
    "status_pass",
    "claim_boundary",
]
PARENT_COMPARISON_FIELDNAMES = [
    "comparison_plan_id",
    "comparison_family",
    "parent_checkpoint_path",
    "candidate_artifact_path",
    "denominator_family",
    "row_count",
    "comparison_planned",
    "ranking_planned",
    "winner_selection_planned",
    "promotion_planned",
    "performance_claim_allowed",
    "status_pass",
    "claim_boundary",
]
SUCCESS_RETENTION_FIELDNAMES = [
    "success_retention_guard_id",
    "success_guard_loss_id",
    "raw_trace_path",
    "target_tensor_path",
    "predicted_residual_abs_max",
    "required_abs_max",
    "zero_residual_guard_satisfied",
    "validation_denominator_allowed",
    "retention_guard_planned",
    "status_pass",
    "claim_boundary",
]
STALE_EXCLUSION_FIELDNAMES = [
    "stale_exclusion_guard_id",
    "stale_exclusion_audit_id",
    "stale_guardrail_exclusion_binding_id",
    "stale_guardrail_exclusion_row_id",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_denominator_allowed",
    "stale_guardrail_excluded",
    "status_pass",
    "claim_boundary",
]
ACTOR_INPUT_EXCLUSION_FIELDNAMES = [
    "actor_input_exclusion_id",
    "forbidden_metadata_key",
    "actor_visible",
    "status_pass",
    "claim_boundary",
]
SIDE_EFFECT_FIELDNAMES = [
    "side_effect_guard_id",
    "side_effect",
    "scheduled_or_run",
    "expected",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2996",
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
    "validation_contract_rows",
    "residual_head_wrapper_contract_rows",
    "parent_comparison_plan_rows",
    "success_behavior_retention_guard_rows",
    "stale_exclusion_guard_rows",
    "actor_input_exclusion_rows",
    "checkpoint_side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_validation_contract_materialization_preflight(
    *,
    m2993_dir: Path | str = DEFAULT_M2993_DIR,
    m2994_audit: Path | str = DEFAULT_M2994_AUDIT,
    m2995_design: Path | str = DEFAULT_M2995_DESIGN,
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
        m2993_dir=Path(m2993_dir),
        m2994_audit=Path(m2994_audit),
        m2995_design=Path(m2995_design),
    )

    validation_rows = build_validation_contract_rows(source)
    wrapper_rows = build_residual_head_wrapper_contract_rows(source)
    comparison_rows = build_parent_comparison_plan_rows(source, validation_rows)
    success_rows = build_success_behavior_retention_guard_rows(source)
    stale_rows = build_stale_exclusion_guard_rows(source)
    actor_rows = build_actor_input_exclusion_rows(source)
    side_effect_rows = build_checkpoint_side_effect_guard_rows(source)

    write_csv_rows(paths["validation_contract_rows"], validation_rows, fieldnames=VALIDATION_CONTRACT_FIELDNAMES)
    write_csv_rows(
        paths["residual_head_wrapper_contract_rows"],
        wrapper_rows,
        fieldnames=RESIDUAL_HEAD_WRAPPER_FIELDNAMES,
    )
    write_csv_rows(paths["parent_comparison_plan_rows"], comparison_rows, fieldnames=PARENT_COMPARISON_FIELDNAMES)
    write_csv_rows(
        paths["success_behavior_retention_guard_rows"],
        success_rows,
        fieldnames=SUCCESS_RETENTION_FIELDNAMES,
    )
    write_csv_rows(paths["stale_exclusion_guard_rows"], stale_rows, fieldnames=STALE_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], actor_rows, fieldnames=ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_effect_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)

    write_follow_up_manifest(
        Path(follow_up_manifest),
        summary_path=paths["summary"],
        doc_path=paths["doc"],
        output_dir=output,
    )
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        validation_rows=validation_rows,
        wrapper_rows=wrapper_rows,
        comparison_rows=comparison_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=False,
    )
    write_run_state(
        paths["run_state"],
        {
            "validation_contract_row_count": len(validation_rows),
            "residual_head_wrapper_contract_row_count": len(wrapper_rows),
            "parent_comparison_plan_row_count": len(comparison_rows),
            "success_behavior_retention_guard_row_count": len(success_rows),
            "stale_exclusion_guard_row_count": len(stale_rows),
            "actor_input_exclusion_row_count": len(actor_rows),
            "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
            "validation_contract_materialization_run": True,
            "validation_run": False,
            "ranking_run": False,
            "checkpoint_mutated": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        validation_rows=validation_rows,
        wrapper_rows=wrapper_rows,
        comparison_rows=comparison_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS),
    )
    return summary


def _write_summary_doc_and_gates(
    *,
    paths: dict[str, Path],
    output_dir: Path,
    source: dict[str, Any],
    validation_rows: list[dict[str, Any]],
    wrapper_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    claim_rows = build_claim_boundary_rows(
        artifacts_present=required_artifacts_present,
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        validation_rows=validation_rows,
        wrapper_rows=wrapper_rows,
        comparison_rows=comparison_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        validation_rows=validation_rows,
        wrapper_rows=wrapper_rows,
        comparison_rows=comparison_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_manifest,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "validation_contract_rows": output_dir / "validation_contract_rows.csv",
        "residual_head_wrapper_contract_rows": output_dir / "residual_head_wrapper_contract_rows.csv",
        "parent_comparison_plan_rows": output_dir / "parent_comparison_plan_rows.csv",
        "success_behavior_retention_guard_rows": output_dir / "success_behavior_retention_guard_rows.csv",
        "stale_exclusion_guard_rows": output_dir / "stale_exclusion_guard_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2993_dir: Path, m2994_audit: Path, m2995_design: Path) -> dict[str, Any]:
    paths = {
        "m2993_summary": m2993_dir / "summary.json",
        "candidate_residual_head_artifact": m2993_dir / "candidate_residual_head_artifact.npz",
        "fitting_dataset_rows": m2993_dir / "fitting_dataset_rows.csv",
        "success_guard_loss_rows": m2993_dir / "success_guard_loss_rows.csv",
        "stale_exclusion_audit_rows": m2993_dir / "stale_exclusion_audit_rows.csv",
        "actor_input_exclusion_rows": m2993_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": m2993_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": m2993_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2993_dir / "gate_matrix.csv",
        "m2994_audit": m2994_audit,
        "m2995_design": m2995_design,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m2993_summary": read_json(paths["m2993_summary"]) if exists["m2993_summary"] else {},
        "artifact_metadata": load_residual_head_artifact_metadata(paths["candidate_residual_head_artifact"]),
        "fitting_dataset_rows": read_csv_rows(paths["fitting_dataset_rows"]),
        "success_guard_loss_rows": read_csv_rows(paths["success_guard_loss_rows"]),
        "stale_exclusion_audit_rows": read_csv_rows(paths["stale_exclusion_audit_rows"]),
        "actor_input_exclusion_rows": read_csv_rows(paths["actor_input_exclusion_rows"]),
        "checkpoint_side_effect_guard_rows": read_csv_rows(paths["checkpoint_side_effect_guard_rows"]),
        "m2993_claim_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "m2993_gate_rows": read_csv_rows(paths["gate_matrix"]),
        "m2994_audit_text": m2994_audit.read_text(encoding="utf-8") if exists["m2994_audit"] else "",
        "m2995_design_text": m2995_design.read_text(encoding="utf-8") if exists["m2995_design"] else "",
        "follow_up_manifest_exists": False,
    }


def load_residual_head_artifact_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "required_keys_present": False,
        "linear_weight_shape": "",
        "linear_bias_shape": "",
        "observation_dim": 0,
        "action_dim": 0,
        "residual_limit": 0.0,
        "success_guard_required_abs_max": 0.0,
        "finite": False,
        "status_pass": False,
    }
    if not path.exists():
        return metadata
    try:
        with np.load(path, allow_pickle=False) as data:
            required = {
                "linear_weight",
                "linear_bias",
                "residual_limit",
                "success_guard_required_abs_max",
                "observation_dim",
                "action_dim",
            }
            metadata["required_keys_present"] = required.issubset(data.files)
            if not metadata["required_keys_present"]:
                return metadata
            weight = np.asarray(data["linear_weight"], dtype=np.float32)
            bias = np.asarray(data["linear_bias"], dtype=np.float32)
            residual_limit = float(np.asarray(data["residual_limit"]).reshape(-1)[0])
            success_abs = float(np.asarray(data["success_guard_required_abs_max"]).reshape(-1)[0])
            observation_dim = int(np.asarray(data["observation_dim"]).reshape(-1)[0])
            action_dim = int(np.asarray(data["action_dim"]).reshape(-1)[0])
    except Exception:
        return metadata

    metadata.update(
        {
            "linear_weight_shape": shape_text(weight.shape),
            "linear_bias_shape": shape_text(bias.shape),
            "observation_dim": observation_dim,
            "action_dim": action_dim,
            "residual_limit": residual_limit,
            "success_guard_required_abs_max": success_abs,
            "finite": bool(np.all(np.isfinite(weight)) and np.all(np.isfinite(bias))),
        }
    )
    metadata["status_pass"] = (
        weight.shape == (P0_OBSERVATION_DIM, ACTION_DIM)
        and bias.shape == (ACTION_DIM,)
        and observation_dim == P0_OBSERVATION_DIM
        and action_dim == ACTION_DIM
        and 0.0 < residual_limit <= EXPECTED_RESIDUAL_LIMIT + 1.0e-6
        and 0.0 < success_abs <= EXPECTED_SUCCESS_ABS_MAX + 1.0e-6
        and bool(metadata["finite"])
    )
    return metadata


def shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(part) for part in shape)


def source_preconditions_pass(source: dict[str, Any]) -> bool:
    summary = source["m2993_summary"]
    return (
        all(source["source_exists"].values())
        and bool_value(summary.get("status_pass"))
        and bool_value(summary.get("gate_matrix_pass"))
        and bool_value(summary.get("required_artifacts_present"))
        and bool(source["artifact_metadata"]["status_pass"])
        and "accept_m2993_artifact_claim_safe_route_to_m2995_validation_admission_design"
        in source["m2994_audit_text"]
        and "admit_m2996_validation_contract_materialization_preflight_without_validation_or_promotion"
        in source["m2995_design_text"]
    )


def build_validation_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["fitting_dataset_rows"], start=1):
        raw_trace_path = row.get("raw_trace_path", "")
        target_tensor_path = row.get("target_tensor_path", "")
        quality_validated = bool_value(row.get("target_quality_validated", False))
        labels_visible = bool_value(row.get("target_labels_actor_visible", False))
        provenance_visible = bool_value(row.get("target_provenance_actor_visible", False))
        status_pass = (
            bool_value(row.get("status_pass", False))
            and bool_value(row.get("fitting_denominator_used", False))
            and not quality_validated
            and not labels_visible
            and not provenance_visible
            and Path(raw_trace_path).exists()
            and Path(target_tensor_path).exists()
        )
        rows.append(
            {
                "validation_contract_id": f"m2996-validation-contract-{index:04d}",
                "fitting_dataset_row_id": row.get("fitting_dataset_row_id", ""),
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "raw_trace_path": raw_trace_path,
                "target_tensor_path": target_tensor_path,
                "validation_denominator_planned": True,
                "parent_comparison_planned": True,
                "candidate_wrapper_planned": True,
                "target_quality_validated": quality_validated,
                "target_labels_actor_visible": labels_visible,
                "target_provenance_actor_visible": provenance_visible,
                "validation_run": False,
                "ranking_run": False,
                "winner_selection_run": False,
                "checkpoint_mutation_planned": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_residual_head_wrapper_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    meta = source["artifact_metadata"]
    artifact_status = bool(meta["status_pass"])
    specs = [
        ("artifact-metadata", artifact_status),
        ("read-only-parent-and-candidate", artifact_status),
        ("action-boundary-residual-clipping", artifact_status),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, status_pass) in enumerate(specs, start=1):
        rows.append(
            {
                "wrapper_contract_id": f"m2996-wrapper-contract-{index:04d}",
                "contract_family": family,
                "artifact_path": meta["artifact_path"],
                "artifact_exists": bool(meta["artifact_exists"]),
                "linear_weight_shape": meta["linear_weight_shape"],
                "linear_bias_shape": meta["linear_bias_shape"],
                "observation_dim": meta["observation_dim"],
                "action_dim": meta["action_dim"],
                "residual_limit": meta["residual_limit"],
                "success_guard_required_abs_max": meta["success_guard_required_abs_max"],
                "read_only_candidate_artifact": True,
                "parent_checkpoint_read_only": True,
                "actor_input_shape_preserved": int(meta["observation_dim"]) == P0_OBSERVATION_DIM,
                "action_shape_preserved": int(meta["action_dim"]) == ACTION_DIM,
                "residual_clipping_bound": 0.0 < float(meta["residual_limit"]) <= EXPECTED_RESIDUAL_LIMIT + 1.0e-6,
                "wrapper_execution_planned": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_parent_comparison_plan_rows(
    source: dict[str, Any], validation_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    artifact_path = source["artifact_metadata"]["artifact_path"]
    specs = [
        (
            "candidate-validation-denominator-parent-comparison",
            "accepted_m2993_fitting_rows",
            len(validation_rows),
            len(validation_rows) == EXPECTED_VALIDATION_CONTRACT_COUNT,
        ),
        (
            "success-behavior-retention-parent-comparison",
            "m2993_success_identity_rows",
            len(source["success_guard_loss_rows"]),
            len(source["success_guard_loss_rows"]) == EXPECTED_SUCCESS_RETENTION_COUNT,
        ),
        ("report-only-no-ranking-no-promotion", "comparison_report_only", 2, True),
    ]
    rows: list[dict[str, Any]] = []
    parent_path = ";".join(PARENT_CHECKPOINTS)
    for index, (family, denominator, count, status_pass) in enumerate(specs, start=1):
        rows.append(
            {
                "comparison_plan_id": f"m2996-parent-comparison-{index:04d}",
                "comparison_family": family,
                "parent_checkpoint_path": parent_path,
                "candidate_artifact_path": artifact_path,
                "denominator_family": denominator,
                "row_count": count,
                "comparison_planned": True,
                "ranking_planned": False,
                "winner_selection_planned": False,
                "promotion_planned": False,
                "performance_claim_allowed": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_behavior_retention_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["success_guard_loss_rows"], start=1):
        predicted_abs = _float(row.get("predicted_residual_abs_max"))
        required_abs = max(_float(row.get("target_action_delta_abs_max")), EXPECTED_SUCCESS_ABS_MAX)
        zero_satisfied = bool_value(row.get("zero_residual_guard_satisfied", False))
        status_pass = (
            bool_value(row.get("status_pass", False))
            and bool_value(row.get("guard_penalty_or_constraint_used", False))
            and zero_satisfied
            and predicted_abs <= required_abs + 1.0e-9
            and not bool_value(row.get("fitting_denominator_used", True))
        )
        rows.append(
            {
                "success_retention_guard_id": f"m2996-success-retention-{index:04d}",
                "success_guard_loss_id": row.get("success_guard_loss_id", ""),
                "raw_trace_path": row.get("raw_trace_path", ""),
                "target_tensor_path": row.get("target_tensor_path", ""),
                "predicted_residual_abs_max": predicted_abs,
                "required_abs_max": required_abs,
                "zero_residual_guard_satisfied": zero_satisfied,
                "validation_denominator_allowed": True,
                "retention_guard_planned": True,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_exclusion_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["stale_exclusion_audit_rows"], start=1):
        stale_excluded = bool_value(row.get("stale_guardrail_excluded", False))
        status_pass = (
            bool_value(row.get("status_pass", False))
            and not bool_value(row.get("validation_denominator_used", True))
            and not bool_value(row.get("paper_denominator_used", True))
            and stale_excluded
        )
        rows.append(
            {
                "stale_exclusion_guard_id": f"m2996-stale-exclusion-{index:04d}",
                "stale_exclusion_audit_id": row.get("stale_exclusion_audit_id", ""),
                "stale_guardrail_exclusion_binding_id": row.get("stale_guardrail_exclusion_binding_id", ""),
                "stale_guardrail_exclusion_row_id": row.get("stale_guardrail_exclusion_row_id", ""),
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_denominator_allowed": False,
                "stale_guardrail_excluded": stale_excluded,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_input_exclusion_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = source["actor_input_exclusion_rows"]
    if not source_rows:
        source_rows = [
            {"forbidden_metadata_key": key, "actor_visible": False, "status_pass": True}
            for key in [
                "target_action",
                "target_action_delta",
                "target_valid_mask",
                "target_loss_weight",
                "target_source_provenance",
                "target_quality_validated",
                "objective_family",
                "outcome_bucket",
                "training_admission_candidate_id",
                "source_raw_trace_index_row_id",
                "audit_verdict",
                "route_decision",
                "paper_label",
                "validation_label",
            ]
        ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        actor_visible = bool_value(row.get("actor_visible", False))
        rows.append(
            {
                "actor_input_exclusion_id": f"m2996-actor-input-exclusion-{index:04d}",
                "forbidden_metadata_key": row.get("forbidden_metadata_key", ""),
                "actor_visible": actor_visible,
                "status_pass": bool_value(row.get("status_pass", False)) and not actor_visible,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_checkpoint_side_effect_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = source["checkpoint_side_effect_guard_rows"]
    if not source_rows:
        source_rows = [
            {"side_effect": effect, "scheduled_or_run": False, "expected": False, "status_pass": True}
            for effect in [
                "parent_checkpoint_load",
                "parent_checkpoint_save",
                "parent_checkpoint_modify",
                "parent_checkpoint_rank",
                "parent_checkpoint_promote",
                "environment_reset",
                "environment_step",
                "policy_rollout",
                "policy_validation",
                "ranking_or_winner_selection",
                "private_holdout",
                "performance_measurement",
            ]
        ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        scheduled_or_run = bool_value(row.get("scheduled_or_run", False))
        expected = bool_value(row.get("expected", False))
        rows.append(
            {
                "side_effect_guard_id": f"m2996-side-effect-guard-{index:04d}",
                "side_effect": row.get("side_effect", ""),
                "scheduled_or_run": scheduled_or_run,
                "expected": expected,
                "status_pass": bool_value(row.get("status_pass", False)) and not scheduled_or_run and not expected,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_boundary_rows(*, artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("validation_contract_materialized", "artifact", artifacts_present, "M2996 contract rows and gate matrix"),
        ("residual_head_wrapper_contract", "wrapper", artifacts_present, "M2996 wrapper contract rows"),
        ("parent_comparison_plan", "comparison", artifacts_present, "M2996 parent comparison plan rows"),
        ("success_behavior_retention_guard", "guardrail", artifacts_present, "M2996 success-retention rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2997 audit manifest"),
    ]
    blocked = [
        ("target_quality_validated", "target_quality", "future target-quality audit"),
        ("validation_result", "validation", "future bounded validation preflight and audit"),
        ("ranking_or_winner", "ranking", "future audited comparison route"),
        ("checkpoint_mutation", "implementation", "future audited implementation admission"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future validation and result audit"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_evidence", "paper", "future audited evidence matrix"),
        ("current_sim_verdict", "validation", "future current-sim verdict route"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation route"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [
        _claim_row(claim_id, family, True, bool(made), evidence)
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(_claim_row(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def _claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2996-{claim_id}",
        "claim_family": family,
        "allowed_in_m2996": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    validation_rows: list[dict[str, Any]],
    wrapper_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    summary = source["m2993_summary"]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        ("m2993_status_pass", "lineage", bool_value(summary.get("status_pass")), True, "lineage_invalid"),
        ("m2993_gate_matrix_pass", "lineage", bool_value(summary.get("gate_matrix_pass")), True, "lineage_invalid"),
        (
            "m2993_required_artifacts_present",
            "lineage",
            bool_value(summary.get("required_artifacts_present")),
            True,
            "lineage_invalid",
        ),
        (
            "m2994_accepts_m2993",
            "lineage",
            "accept_m2993_artifact_claim_safe_route_to_m2995_validation_admission_design"
            in source["m2994_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2995_admits_m2996",
            "lineage",
            "admit_m2996_validation_contract_materialization_preflight_without_validation_or_promotion"
            in source["m2995_design_text"],
            True,
            "lineage_invalid",
        ),
        ("source_preconditions_pass", "lineage", source_preconditions_pass(source), True, "lineage_invalid"),
        ("artifact_metadata_pass", "artifact", source["artifact_metadata"]["status_pass"], True, "metric_artifact"),
        (
            "validation_contract_row_count",
            "contract",
            len(validation_rows),
            EXPECTED_VALIDATION_CONTRACT_COUNT,
            "metric_artifact",
        ),
        (
            "validation_contract_rows_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in validation_rows),
            True,
            "contract_violation",
        ),
        (
            "wrapper_contract_rows_pass",
            "wrapper",
            all(bool_value(row["status_pass"]) for row in wrapper_rows),
            True,
            "contract_violation",
        ),
        (
            "parent_comparison_rows_pass",
            "comparison",
            all(bool_value(row["status_pass"]) for row in comparison_rows)
            and all(not bool_value(row["ranking_planned"]) for row in comparison_rows)
            and all(not bool_value(row["winner_selection_planned"]) for row in comparison_rows)
            and all(not bool_value(row["promotion_planned"]) for row in comparison_rows),
            True,
            "contract_violation",
        ),
        (
            "success_retention_row_count",
            "guardrail",
            len(success_rows),
            EXPECTED_SUCCESS_RETENTION_COUNT,
            "metric_artifact",
        ),
        (
            "success_retention_rows_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in success_rows),
            True,
            "contract_violation",
        ),
        (
            "stale_exclusion_row_count",
            "guardrail",
            len(stale_rows),
            EXPECTED_STALE_EXCLUSION_COUNT,
            "metric_artifact",
        ),
        (
            "stale_exclusion_rows_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in stale_rows),
            True,
            "contract_violation",
        ),
        (
            "actor_input_exclusion_row_count",
            "actor_contract",
            len(actor_rows),
            EXPECTED_ACTOR_EXCLUSION_COUNT,
            "metric_artifact",
        ),
        (
            "actor_input_exclusions_pass",
            "actor_contract",
            all(not bool_value(row["actor_visible"]) and bool_value(row["status_pass"]) for row in actor_rows),
            True,
            "contract_violation",
        ),
        (
            "checkpoint_side_effect_row_count",
            "side_effect_guard",
            len(side_effect_rows),
            EXPECTED_SIDE_EFFECT_COUNT,
            "metric_artifact",
        ),
        (
            "checkpoint_side_effect_guards_pass",
            "side_effect_guard",
            all(bool_value(row["status_pass"]) for row in side_effect_rows),
            True,
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(bool_value(row["status_pass"]) for row in claim_rows),
            True,
            "proof_washout",
        ),
        (
            "no_validation_ranking_promotion_or_checkpoint_mutation",
            "side_effect_guard",
            all(not bool_value(row["validation_run"]) for row in validation_rows)
            and all(not bool_value(row["ranking_run"]) for row in validation_rows)
            and all(not bool_value(row["winner_selection_run"]) for row in validation_rows)
            and all(not bool_value(row["checkpoint_mutation_planned"]) for row in validation_rows),
            True,
            "contract_violation",
        ),
        (
            "target_quality_validated_false",
            "claim_boundary",
            all(not bool_value(row["target_quality_validated"]) for row in validation_rows)
            and any(
                row["claim_id"] == "m2996-target_quality_validated" and not bool_value(row["claim_made"])
                for row in claim_rows
            ),
            True,
            "proof_washout",
        ),
        ("follow_up_audit_registered", "follow_up", source["follow_up_manifest_exists"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2996-gate-{index:04d}-{gate_id}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (gate_id, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    validation_rows: list[dict[str, Any]],
    wrapper_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool_value(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    artifact_meta = source["artifact_metadata"]
    success_abs_max = max((_float(row["predicted_residual_abs_max"]) for row in success_rows), default=0.0)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2993_status_pass": bool_value(source["m2993_summary"].get("status_pass")),
        "m2993_gate_matrix_pass": bool_value(source["m2993_summary"].get("gate_matrix_pass")),
        "m2993_required_artifacts_present": bool_value(source["m2993_summary"].get("required_artifacts_present")),
        "validation_contract_row_count": len(validation_rows),
        "residual_head_wrapper_contract_row_count": len(wrapper_rows),
        "parent_comparison_plan_row_count": len(comparison_rows),
        "success_behavior_retention_guard_row_count": len(success_rows),
        "stale_exclusion_guard_row_count": len(stale_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "candidate_validation_denominator_row_count": len(validation_rows),
        "success_retention_denominator_row_count": len(success_rows),
        "stale_guardrail_exclusion_row_count": len(stale_rows),
        "success_retention_predicted_residual_abs_max": success_abs_max,
        "artifact_metadata": artifact_meta,
        "candidate_residual_head_artifact": artifact_meta["artifact_path"],
        "candidate_residual_head_artifact_exists": bool(artifact_meta["artifact_exists"]),
        "actor_contract_shape_72_action_3": artifact_meta["observation_dim"] == P0_OBSERVATION_DIM
        and artifact_meta["action_dim"] == ACTION_DIM,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "validation_contract_materialized": True,
        "residual_head_wrapper_contract_materialized": True,
        "parent_comparison_plan_materialized": True,
        "success_behavior_retention_guard_materialized": True,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "private_holdout_run": False,
        "performance_measurement_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
        "result_class": (
            "engineering_controller_route_a_actor_head_delta_nonzero_residual_"
            "validation_contract_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_"
            "validation_contract_materialization_preflight_fail"
        ),
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2996 Engineering Controller Route A Actor-Head Delta Nonzero Residual Validation Contract Materialization Preflight

## Summary

- status pass: `{summary["status_pass"]}`
- gate matrix pass: `{summary["gate_matrix_pass"]}`
- required artifacts present: `{summary["required_artifacts_present"]}`
- validation contract rows: `{summary["validation_contract_row_count"]}`
- residual-head wrapper rows: `{summary["residual_head_wrapper_contract_row_count"]}`
- parent comparison rows: `{summary["parent_comparison_plan_row_count"]}`
- success behavior retention rows: `{summary["success_behavior_retention_guard_row_count"]}`
- stale exclusion rows: `{summary["stale_exclusion_guard_row_count"]}`
- actor input exclusions: `{summary["actor_input_exclusion_row_count"]}`
- checkpoint side-effect guards: `{summary["checkpoint_side_effect_guard_row_count"]}`
- target quality validated: `{summary["target_quality_validated"]}`
- validation run: `{summary["validation_run"]}`
- ranking run: `{summary["ranking_run"]}`
- checkpoint mutated: `{summary["checkpoint_mutated"]}`
- next blocker: `{summary["next_blocker"]}`
- follow-up manifest: `{summary["follow_up_manifest"]}`

## Artifact Binding

```text
artifact: {summary["candidate_residual_head_artifact"]}
artifact exists: {summary["candidate_residual_head_artifact_exists"]}
linear weight shape: {summary["artifact_metadata"]["linear_weight_shape"]}
linear bias shape: {summary["artifact_metadata"]["linear_bias_shape"]}
observation/action: {summary["artifact_metadata"]["observation_dim"]}/{summary["artifact_metadata"]["action_dim"]}
residual limit: {summary["artifact_metadata"]["residual_limit"]}
success guard required abs max: {summary["artifact_metadata"]["success_guard_required_abs_max"]}
success retention residual abs max: {summary["success_retention_predicted_residual_abs_max"]}
```

## Boundary

M2996 materializes validation contracts only. It preserves actor observation
`{summary["observation_shape"]}` and action `{summary["action_shape"]}`, keeps
target labels and provenance actor-invisible, keeps stale rows excluded, keeps
parent and candidate artifacts read-only, and keeps `target_quality_validated:
false`.

M2996 does not run validation, rank candidates, select a winner, mutate or
promote checkpoints, run private holdout or performance measurement, or claim
repair success, driver performance, paper evidence, current-sim verdict,
high-fidelity validation, finite-window-vs-GRU evidence, full-driver
completion, or self-ID evidence.
"""


def write_follow_up_manifest(path: Path, *, summary_path: Path, doc_path: Path, output_dir: Path) -> None:
    if path.exists():
        return
    manifest_id = NEXT_ID
    write_json(
        path,
        {
            "id": manifest_id,
            "type": "gate",
            "status": "pending",
            "hypothesis": (
                "A bounded result audit can accept or reject the M2996 validation-contract "
                "materialization artifacts before any closed-loop validation ranking promotion "
                "repair-success performance paper high-fidelity or self-ID claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2997 audits M2996 wrapper comparison success-retention stale-exclusion actor side-effect claim and gate artifacts",
                "M2997 selects exactly one validation-preflight, artifact-repair, synthesis, pivot, or stop route",
                "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2997 hides missing M2996 contract artifacts",
                "M2997 treats validation-contract materialization as validation result repair-success performance or paper evidence",
                "M2997 changes actor input action checkpoint side-effect stale-exclusion or claim boundaries",
                "M2997 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": PARENT_CHECKPOINTS,
            "baseline_artifacts": [
                str(summary_path),
                str(output_dir / "validation_contract_rows.csv"),
                str(output_dir / "residual_head_wrapper_contract_rows.csv"),
                str(output_dir / "parent_comparison_plan_rows.csv"),
                str(output_dir / "success_behavior_retention_guard_rows.csv"),
                str(output_dir / "stale_exclusion_guard_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "checkpoint_side_effect_guard_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "decision_rule": (
                "Pass only if M2997 audits M2996 artifacts and selects one next route or stop state "
                "while preserving actor guard stale-exclusion target-quality checkpoint side-effect and claim boundaries."
            ),
            "gate_tier": "process",
            "promotion_decision": "pending",
            "failure_types": [
                "contract_violation",
                "lineage_invalid",
                "metric_artifact",
                "training_instability",
                "scenario_sampling_failure",
                "behavior_regression",
                "objective_overfit",
                "proof_washout",
                "seed_fragility",
            ],
            "lineage": {
                "parent_checkpoint": PARENT_CHECKPOINTS,
                "parent_dataset": [str(summary_path), str(output_dir / "gate_matrix.csv"), str(doc_path)],
                "parent_config": [
                    "experiments/manifests/"
                    "m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
                    "nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-"
                    "materialization-preflight.json"
                ],
                "parent_objective": [
                    "audit validation-contract materialization before any residual-head validation can be admitted"
                ],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2996 materializes contracts but does not itself establish validation result or repair success"
                ],
                "supersedes": ["direct validation immediately after M2996 without result audit"],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "public_gates": [
                "M2997 must audit M2996 validation-contract rows and gate matrix",
                "M2997 must preserve target_quality_validated false unless a later target-quality audit is explicitly admitted",
                "M2997 must preserve actor 72/action 3 no target labels provenance objective source route verdict or paper actor inputs",
                "M2997 must not validate rank promote mutate checkpoints or claim performance paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not run environment validation ranking winner selection private holdout or performance measurement",
                "do not mutate save replace or promote checkpoints",
                "do not change actor input or action contract",
                "do not convert materialization rows into validation repair-success performance paper high-fidelity finite-window-vs-GRU or self-ID claims",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": (
                    "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_"
                    "validation_contract_materialization_result_audit"
                ),
                "evidence_increment": (
                    "audits M2996 validation-contract materialization before any bounded validation-preflight decision"
                ),
                "claim_scope": (
                    "Result audit only; no validation ranking promotion repair-success driver-performance paper "
                    "current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim"
                ),
                "stop_condition": [
                    "stop if M2996 contract artifacts are incomplete or claim-unsafe",
                    "stop if actor target guard stale-exclusion side-effect or checkpoint boundaries are weakened",
                    "stop if the result would be interpreted as validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
                ],
                "fallback_plan": [
                    "route to artifact repair if contract rows are incomplete",
                    "route to validation-admission design only if the audit accepts M2996 as complete and claim-safe",
                    "route to synthesis pivot or stop if materialization cannot preserve boundaries",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2996 materializes validation-contract artifacts",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit validation-contract materialization before residual-head validation admission",
                "admission_evidence": [
                    "M2996 is expected to write wrapper comparison success-retention stale-exclusion actor side-effect claim and gate rows",
                    "M2996 must preserve target_quality_validated false and no validation/ranking/promotion claims",
                ],
                "blocked_shortcuts": [
                    "no environment validation ranking promotion or success-rate verdict",
                    "no checkpoint mutation save selection or promotion",
                    "no target labels target provenance objective admission source route verdict or paper actor inputs",
                    "no driver-performance current-sim high-fidelity full ideal driver finite-window-vs-GRU paper or self-ID claim",
                ],
                "allowed_updates": [
                    f"docs/{manifest_id}.md",
                    f"docs/reviews/{manifest_id}.md",
                    "M2997 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2997 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2997 accepts or rejects M2996 artifacts",
                    "M2997 chooses one next route or stop state",
                    "actor guard checkpoint side-effect and claim boundaries remain unchanged",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2997 audits validation contracts and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2997; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2983-M2996 Route A actor-head delta target tensor fitting-contract validation-contract chain.",
                "negative_result_policy": "Preserve validation blockers rather than weakening self-ID proof gates.",
                "allowed_claims": [
                    "M2996 artifact completeness after audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits newly materialized validation-contract artifacts",
                "paper_verdict_delta": "no paper verdict; may enable later validation-admission design only",
                "must_synthesize_if": [
                    "M2997 cannot select exactly one next route",
                    "M2997 would claim performance validation paper current-sim high-fidelity finite-window-vs-GRU or self-ID evidence",
                ],
            },
            "next_blocker": manifest_id,
        },
    )


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2993-dir", type=Path, default=DEFAULT_M2993_DIR)
    parser.add_argument("--m2994-audit", type=Path, default=DEFAULT_M2994_AUDIT)
    parser.add_argument("--m2995-design", type=Path, default=DEFAULT_M2995_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_validation_contract_materialization_preflight(
        m2993_dir=args.m2993_dir,
        m2994_audit=args.m2994_audit,
        m2995_design=args.m2995_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"validation_contract_rows={summary['validation_contract_row_count']}")
    print(f"success_behavior_retention_rows={summary['success_behavior_retention_guard_row_count']}")
    print(f"stale_exclusion_rows={summary['stale_exclusion_guard_row_count']}")
    print(f"follow_up_manifest={summary['follow_up_manifest']}")


if __name__ == "__main__":
    main()
