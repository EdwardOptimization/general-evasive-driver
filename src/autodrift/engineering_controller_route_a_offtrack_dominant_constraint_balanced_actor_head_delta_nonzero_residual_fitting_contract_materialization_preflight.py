"""Materialize M2987 nonzero residual fitting-contract artifacts.

M2987 consumes accepted M2983 target tensor artifacts plus M2984-M2986
admission/synthesis documents. It writes machine-checkable contract rows for a
later fitting preflight. It does not fit, train, validate, rank, promote,
mutate checkpoints, or make performance claims.
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
    "m2987-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-contract-materialization-preflight"
)
NEXT_ID = (
    "m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-contract-materialization-result-audit"
)
DEFAULT_M2983_DIR = Path(
    "runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_target_tensor_materialization_preflight"
)
DEFAULT_M2984_AUDIT = Path(
    "docs/m2984-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-tensor-materialization-result-audit.md"
)
DEFAULT_M2985_DESIGN = Path(
    "docs/m2985-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-admission-design.md"
)
DEFAULT_M2986_SYNTHESIS = Path(
    "docs/m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-contract-branch-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_fitting_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2987-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-contract-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-fitting-contract-materialization-result-audit.json"
)

EXPECTED_TARGET_ROW_COUNT = 43
EXPECTED_SUCCESS_ZERO_GUARD_COUNT = 13
EXPECTED_STALE_EXCLUSION_COUNT = 11

CLAIM_SCOPE = (
    "M2987 Route A actor-head delta nonzero residual fitting-contract materialization preflight only; "
    "accepted M2983 target tensors may be bound to dataset, split, mask, weight, success-guard, stale-"
    "exclusion, actor-input, side-effect, claim, and gate contracts for a later audited fitting "
    "preflight. No residual fitting, training, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, repair success, driver-performance, paper, current-sim verdict, "
    "high-fidelity validation, full ideal driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality validation, fitting readiness beyond contract materialization, fitted residual "
    "quality, repair success, driver performance, validation readiness or result, controller/source/"
    "task/profile/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)

DATASET_CONTRACT_FIELDNAMES = [
    "dataset_contract_id",
    "source_artifact",
    "row_family",
    "row_count",
    "expected_count",
    "status_pass",
    "actor_visible",
    "fitting_execution_run",
    "claim_boundary",
]
SPLIT_DENOMINATOR_FIELDNAMES = [
    "split_denominator_id",
    "row_family",
    "source_row_count",
    "future_fitting_denominator_allowed_after_audit",
    "guard_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "positive_residual_target",
    "status_pass",
    "claim_boundary",
]
MASK_WEIGHT_FIELDNAMES = [
    "mask_weight_binding_id",
    "target_tensor_row_id",
    "training_admission_candidate_id",
    "objective_family",
    "outcome_bucket",
    "target_tensor_path",
    "target_action_delta_shape",
    "target_valid_mask_shape",
    "target_loss_weight_shape",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "target_action_delta_abs_max",
    "target_quality_validated",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "fit_candidate_after_audit",
    "tensor_contract_pass",
    "status_pass",
    "claim_boundary",
]
SUCCESS_BINDING_FIELDNAMES = [
    "success_identity_zero_guard_binding_id",
    "success_identity_zero_target_guard_row_id",
    "source_row_id",
    "target_tensor_path",
    "zero_target_guard",
    "positive_residual_target",
    "future_fitting_denominator_allowed_after_audit",
    "guard_denominator_allowed",
    "target_action_delta_abs_max",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "tensor_contract_pass",
    "status_pass",
    "claim_boundary",
]
STALE_BINDING_FIELDNAMES = [
    "stale_guardrail_exclusion_binding_id",
    "stale_guardrail_exclusion_row_id",
    "source_row_id",
    "guard_family",
    "target_materialized",
    "positive_residual_target",
    "future_fitting_denominator_allowed_after_audit",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
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
    "allowed_in_m2987",
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
    "dataset_contract_rows",
    "split_denominator_rows",
    "mask_weight_binding_rows",
    "success_identity_zero_guard_binding_rows",
    "stale_guardrail_exclusion_binding_rows",
    "actor_input_exclusion_rows",
    "checkpoint_side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_fitting_contract_materialization_preflight(
    *,
    m2983_dir: Path | str = DEFAULT_M2983_DIR,
    m2984_audit: Path | str = DEFAULT_M2984_AUDIT,
    m2985_design: Path | str = DEFAULT_M2985_DESIGN,
    m2986_synthesis: Path | str = DEFAULT_M2986_SYNTHESIS,
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
        m2983_dir=Path(m2983_dir),
        m2984_audit=Path(m2984_audit),
        m2985_design=Path(m2985_design),
        m2986_synthesis=Path(m2986_synthesis),
    )

    dataset_rows = build_dataset_contract_rows(source)
    split_rows = build_split_denominator_rows(source)
    mask_rows = build_mask_weight_binding_rows(source["target_tensor_rows"])
    success_rows = build_success_guard_binding_rows(source["success_identity_zero_target_guard_rows"])
    stale_rows = build_stale_exclusion_binding_rows(source["stale_guardrail_exclusion_rows"])
    actor_rows = build_actor_input_exclusion_rows()
    side_effect_rows = build_checkpoint_side_effect_guard_rows()

    write_csv_rows(paths["dataset_contract_rows"], dataset_rows, fieldnames=DATASET_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["split_denominator_rows"], split_rows, fieldnames=SPLIT_DENOMINATOR_FIELDNAMES)
    write_csv_rows(paths["mask_weight_binding_rows"], mask_rows, fieldnames=MASK_WEIGHT_FIELDNAMES)
    write_csv_rows(
        paths["success_identity_zero_guard_binding_rows"],
        success_rows,
        fieldnames=SUCCESS_BINDING_FIELDNAMES,
    )
    write_csv_rows(
        paths["stale_guardrail_exclusion_binding_rows"],
        stale_rows,
        fieldnames=STALE_BINDING_FIELDNAMES,
    )
    write_csv_rows(paths["actor_input_exclusion_rows"], actor_rows, fieldnames=ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(
        paths["checkpoint_side_effect_guard_rows"],
        side_effect_rows,
        fieldnames=SIDE_EFFECT_FIELDNAMES,
    )

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
        dataset_rows=dataset_rows,
        split_rows=split_rows,
        mask_rows=mask_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=False,
    )
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        dataset_rows=dataset_rows,
        split_rows=split_rows,
        mask_rows=mask_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=required_artifacts_present,
    )
    write_run_state(
        paths["run_state"],
        {
            "dataset_contract_row_count": len(dataset_rows),
            "split_denominator_row_count": len(split_rows),
            "mask_weight_binding_row_count": len(mask_rows),
            "success_identity_zero_guard_binding_row_count": len(success_rows),
            "stale_guardrail_exclusion_binding_row_count": len(stale_rows),
            "actor_input_exclusion_row_count": len(actor_rows),
            "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
            "claim_boundary_row_count": summary["claim_boundary_row_count"],
            "gate_matrix_row_count": summary["gate_matrix_row_count"],
            "residual_fitting_run": False,
            "training_run": False,
            "validation_run": False,
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
        dataset_rows=dataset_rows,
        split_rows=split_rows,
        mask_rows=mask_rows,
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
    dataset_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    mask_rows: list[dict[str, Any]],
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
        dataset_rows=dataset_rows,
        split_rows=split_rows,
        mask_rows=mask_rows,
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
        dataset_rows=dataset_rows,
        split_rows=split_rows,
        mask_rows=mask_rows,
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
        "dataset_contract_rows": output_dir / "dataset_contract_rows.csv",
        "split_denominator_rows": output_dir / "split_denominator_rows.csv",
        "mask_weight_binding_rows": output_dir / "mask_weight_binding_rows.csv",
        "success_identity_zero_guard_binding_rows": output_dir
        / "success_identity_zero_guard_binding_rows.csv",
        "stale_guardrail_exclusion_binding_rows": output_dir / "stale_guardrail_exclusion_binding_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2983_dir: Path,
    m2984_audit: Path,
    m2985_design: Path,
    m2986_synthesis: Path,
) -> dict[str, Any]:
    paths = {
        "m2983_summary": m2983_dir / "summary.json",
        "target_tensor_rows": m2983_dir / "target_tensor_rows.csv",
        "success_identity_zero_target_guard_rows": m2983_dir / "success_identity_zero_target_guard_rows.csv",
        "stale_guardrail_exclusion_rows": m2983_dir / "stale_guardrail_exclusion_rows.csv",
        "gate_matrix": m2983_dir / "gate_matrix.csv",
        "m2984_audit": m2984_audit,
        "m2985_design": m2985_design,
        "m2986_synthesis": m2986_synthesis,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m2983_summary": read_json(paths["m2983_summary"]) if exists["m2983_summary"] else {},
        "target_tensor_rows": read_csv_rows(paths["target_tensor_rows"]) if exists["target_tensor_rows"] else [],
        "success_identity_zero_target_guard_rows": read_csv_rows(paths["success_identity_zero_target_guard_rows"])
        if exists["success_identity_zero_target_guard_rows"]
        else [],
        "stale_guardrail_exclusion_rows": read_csv_rows(paths["stale_guardrail_exclusion_rows"])
        if exists["stale_guardrail_exclusion_rows"]
        else [],
        "m2983_gate_rows": read_csv_rows(paths["gate_matrix"]) if exists["gate_matrix"] else [],
        "m2984_audit_text": m2984_audit.read_text(encoding="utf-8") if exists["m2984_audit"] else "",
        "m2985_design_text": m2985_design.read_text(encoding="utf-8") if exists["m2985_design"] else "",
        "m2986_synthesis_text": m2986_synthesis.read_text(encoding="utf-8") if exists["m2986_synthesis"] else "",
        "follow_up_manifest_exists": False,
    }


def build_dataset_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2983_summary", "summary", 1 if source["source_exists"]["m2983_summary"] else 0, 1),
        ("target_tensor_rows", "candidate_target_tensor_rows", len(source["target_tensor_rows"]), EXPECTED_TARGET_ROW_COUNT),
        (
            "success_identity_zero_target_guard_rows",
            "success_identity_zero_guard_rows",
            len(source["success_identity_zero_target_guard_rows"]),
            EXPECTED_SUCCESS_ZERO_GUARD_COUNT,
        ),
        (
            "stale_guardrail_exclusion_rows",
            "stale_guardrail_exclusion_rows",
            len(source["stale_guardrail_exclusion_rows"]),
            EXPECTED_STALE_EXCLUSION_COUNT,
        ),
        ("m2983_gate_matrix", "source_gate_rows", len(source["m2983_gate_rows"]), 14),
        ("m2984_audit", "audit_doc", 1 if source["source_exists"]["m2984_audit"] else 0, 1),
        ("m2985_design", "admission_design_doc", 1 if source["source_exists"]["m2985_design"] else 0, 1),
        ("m2986_synthesis", "branch_synthesis_doc", 1 if source["source_exists"]["m2986_synthesis"] else 0, 1),
    ]
    return [
        {
            "dataset_contract_id": f"m2987-dataset-contract-{index:04d}",
            "source_artifact": artifact,
            "row_family": family,
            "row_count": row_count,
            "expected_count": expected,
            "status_pass": row_count == expected,
            "actor_visible": False,
            "fitting_execution_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (artifact, family, row_count, expected) in enumerate(specs, start=1)
    ]


def build_split_denominator_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_count = len(source["target_tensor_rows"])
    success_count = len(source["success_identity_zero_target_guard_rows"])
    stale_count = len(source["stale_guardrail_exclusion_rows"])
    specs = [
        (
            "candidate_target_tensor_rows",
            candidate_count,
            True,
            False,
            False,
            False,
            True,
            candidate_count == EXPECTED_TARGET_ROW_COUNT,
        ),
        (
            "success_identity_zero_target_guard_rows",
            success_count,
            False,
            True,
            False,
            False,
            False,
            success_count == EXPECTED_SUCCESS_ZERO_GUARD_COUNT,
        ),
        (
            "stale_guardrail_exclusion_rows",
            stale_count,
            False,
            False,
            False,
            False,
            False,
            stale_count == EXPECTED_STALE_EXCLUSION_COUNT,
        ),
    ]
    return [
        {
            "split_denominator_id": f"m2987-split-denominator-{index:04d}",
            "row_family": family,
            "source_row_count": count,
            "future_fitting_denominator_allowed_after_audit": fitting_allowed,
            "guard_denominator_allowed": guard_allowed,
            "validation_denominator_allowed": validation_allowed,
            "paper_denominator_allowed": paper_allowed,
            "positive_residual_target": positive_target,
            "status_pass": status_pass,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (
            family,
            count,
            fitting_allowed,
            guard_allowed,
            validation_allowed,
            paper_allowed,
            positive_target,
            status_pass,
        ) in enumerate(specs, start=1)
    ]


def _tensor_contract(path: str | Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": False,
        "required_keys_present": False,
        "shape_pass": False,
        "finite": False,
        "valid_mask_bool": False,
        "loss_weight_finite": False,
        "target_delta_abs_max": 0.0,
        "valid_mask_true_count": 0,
        "loss_weight_sum": 0.0,
    }
    tensor_path = Path(path)
    if not tensor_path.exists():
        return result
    result["exists"] = True
    data = np.load(tensor_path)
    required = {"base_action", "target_action", "target_action_delta", "target_valid_mask", "target_loss_weight"}
    if not required.issubset(data.files):
        return result
    result["required_keys_present"] = True
    base = np.asarray(data["base_action"], dtype=np.float32)
    target = np.asarray(data["target_action"], dtype=np.float32)
    delta = np.asarray(data["target_action_delta"], dtype=np.float32)
    mask = np.asarray(data["target_valid_mask"])
    weight = np.asarray(data["target_loss_weight"], dtype=np.float32)
    steps = base.shape[0] if base.ndim == 2 else -1
    result["shape_pass"] = (
        base.ndim == 2
        and target.shape == base.shape
        and delta.shape == base.shape
        and base.shape[1] == ACTION_DIM
        and mask.shape == (steps,)
        and weight.shape == (steps,)
    )
    result["finite"] = all(np.all(np.isfinite(array)) for array in (base, target, delta, weight))
    result["valid_mask_bool"] = mask.dtype == np.dtype("bool")
    result["loss_weight_finite"] = bool(np.all(np.isfinite(weight)))
    result["target_delta_abs_max"] = float(np.max(np.abs(delta))) if delta.size else 0.0
    result["valid_mask_true_count"] = int(np.sum(mask.astype(bool)))
    result["loss_weight_sum"] = float(np.sum(weight))
    return result


def build_mask_weight_binding_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(target_rows, start=1):
        contract = _tensor_contract(row["target_tensor_path"])
        quality_validated = bool_value(row.get("target_quality_validated", False))
        labels_actor_visible = bool_value(row.get("target_labels_actor_visible", False))
        provenance_actor_visible = bool_value(row.get("target_provenance_actor_visible", False))
        tensor_contract_pass = all(
            bool(contract[key])
            for key in ("exists", "required_keys_present", "shape_pass", "finite", "valid_mask_bool", "loss_weight_finite")
        )
        status_pass = (
            tensor_contract_pass
            and not quality_validated
            and not labels_actor_visible
            and not provenance_actor_visible
            and bool_value(row.get("positive_residual_target", False))
            and not bool_value(row.get("residual_fitting_run", False))
            and not bool_value(row.get("training_run", False))
            and not bool_value(row.get("validation_run", False))
            and not bool_value(row.get("ranking_run", False))
            and not bool_value(row.get("checkpoint_mutated", False))
        )
        rows.append(
            {
                "mask_weight_binding_id": f"m2987-mask-weight-binding-{index:04d}",
                "target_tensor_row_id": row["target_tensor_row_id"],
                "training_admission_candidate_id": row["training_admission_candidate_id"],
                "objective_family": row["objective_family"],
                "outcome_bucket": row.get("outcome_bucket", ""),
                "target_tensor_path": row["target_tensor_path"],
                "target_action_delta_shape": row["target_action_delta_shape"],
                "target_valid_mask_shape": row["target_valid_mask_shape"],
                "target_loss_weight_shape": row["target_loss_weight_shape"],
                "target_valid_mask_true_count": contract["valid_mask_true_count"],
                "target_loss_weight_sum": contract["loss_weight_sum"],
                "target_action_delta_abs_max": contract["target_delta_abs_max"],
                "target_quality_validated": quality_validated,
                "target_labels_actor_visible": labels_actor_visible,
                "target_provenance_actor_visible": provenance_actor_visible,
                "fit_candidate_after_audit": True,
                "tensor_contract_pass": tensor_contract_pass,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_guard_binding_rows(success_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(success_rows, start=1):
        contract = _tensor_contract(row["target_tensor_path"])
        zero_guard = bool_value(row.get("zero_target_guard", False))
        positive_target = bool_value(row.get("positive_residual_target", False))
        tensor_contract_pass = (
            all(
                bool(contract[key])
                for key in (
                    "exists",
                    "required_keys_present",
                    "shape_pass",
                    "finite",
                    "valid_mask_bool",
                    "loss_weight_finite",
                )
            )
            and contract["target_delta_abs_max"] == 0.0
            and contract["valid_mask_true_count"] == 0
            and contract["loss_weight_sum"] == 0.0
        )
        status_pass = zero_guard and not positive_target and tensor_contract_pass
        rows.append(
            {
                "success_identity_zero_guard_binding_id": f"m2987-success-zero-binding-{index:04d}",
                "success_identity_zero_target_guard_row_id": row["success_identity_zero_target_guard_row_id"],
                "source_row_id": row["source_row_id"],
                "target_tensor_path": row["target_tensor_path"],
                "zero_target_guard": zero_guard,
                "positive_residual_target": positive_target,
                "future_fitting_denominator_allowed_after_audit": False,
                "guard_denominator_allowed": True,
                "target_action_delta_abs_max": contract["target_delta_abs_max"],
                "target_valid_mask_true_count": contract["valid_mask_true_count"],
                "target_loss_weight_sum": contract["loss_weight_sum"],
                "tensor_contract_pass": tensor_contract_pass,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_exclusion_binding_rows(stale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(stale_rows, start=1):
        target_materialized = bool_value(row.get("target_materialized", False))
        positive_target = bool_value(row.get("positive_residual_target", False))
        stale_excluded = bool_value(row.get("stale_guardrail_excluded", False))
        status_pass = (
            not target_materialized
            and not positive_target
            and not bool_value(row.get("training_denominator_allowed", False))
            and not bool_value(row.get("validation_denominator_allowed", False))
            and not bool_value(row.get("paper_denominator_allowed", False))
            and stale_excluded
        )
        rows.append(
            {
                "stale_guardrail_exclusion_binding_id": f"m2987-stale-exclusion-binding-{index:04d}",
                "stale_guardrail_exclusion_row_id": row["stale_guardrail_exclusion_row_id"],
                "source_row_id": row["source_row_id"],
                "guard_family": row["guard_family"],
                "target_materialized": target_materialized,
                "positive_residual_target": positive_target,
                "future_fitting_denominator_allowed_after_audit": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "stale_guardrail_excluded": stale_excluded,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_input_exclusion_rows() -> list[dict[str, Any]]:
    forbidden = [
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
    return [
        {
            "actor_input_exclusion_id": f"m2987-actor-input-exclusion-{index:04d}",
            "forbidden_metadata_key": key,
            "actor_visible": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, key in enumerate(forbidden, start=1)
    ]


def build_checkpoint_side_effect_guard_rows() -> list[dict[str, Any]]:
    side_effects = [
        "checkpoint_load",
        "checkpoint_save",
        "checkpoint_modify",
        "checkpoint_rank",
        "checkpoint_promote",
        "residual_fitting",
        "training_or_ppo",
        "validation",
        "ranking_or_winner_selection",
        "environment_reset",
        "environment_step",
        "policy_rollout",
    ]
    return [
        {
            "side_effect_guard_id": f"m2987-side-effect-guard-{index:04d}",
            "side_effect": effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, effect in enumerate(side_effects, start=1)
    ]


def build_claim_boundary_rows(*, artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("fitting_contract_materialized", "artifact", artifacts_present, "M2987 materialization rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2988 audit manifest"),
    ]
    blocked = [
        ("target_quality_validated", "target_quality", "future target-quality audit"),
        ("residual_fitting_readiness", "readiness", "M2988 result audit plus later fitting-admission design"),
        ("residual_fitting_run", "execution", "future fitting preflight"),
        ("training_run", "execution", "future training manifest"),
        ("validation_result", "validation", "future validation route"),
        ("ranking_or_winner", "ranking", "future audited comparison route"),
        ("checkpoint_mutation", "implementation", "future audited implementation admission"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair audit and validation route"),
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
        "claim_id": f"m2987-{claim_id}",
        "claim_family": family,
        "allowed_in_m2987": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    dataset_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    mask_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m2983_summary = source["m2983_summary"]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        ("m2983_status_pass", "lineage", bool_value(m2983_summary.get("status_pass")), True, "lineage_invalid"),
        (
            "m2983_gate_matrix_pass",
            "lineage",
            bool_value(m2983_summary.get("gate_matrix_pass")),
            True,
            "lineage_invalid",
        ),
        (
            "m2984_accepts_m2983",
            "lineage",
            "accept_m2983_target_tensor_materialization_claim_safe_route_to_m2985_fitting_admission_design"
            in source["m2984_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2985_routes_to_m2986",
            "lineage",
            "route_to_m2986_fitting_contract_branch_synthesis_before_m2987_contract_materialization"
            in source["m2985_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2986_continues_to_m2987",
            "lineage",
            "continue_to_m2987_fitting_contract_materialization_preflight" in source["m2986_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        (
            "dataset_contract_rows_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in dataset_rows),
            True,
            "metric_artifact",
        ),
        ("target_row_count", "artifact", len(mask_rows), EXPECTED_TARGET_ROW_COUNT, "metric_artifact"),
        (
            "success_zero_guard_count",
            "artifact",
            len(success_rows),
            EXPECTED_SUCCESS_ZERO_GUARD_COUNT,
            "metric_artifact",
        ),
        ("stale_exclusion_count", "artifact", len(stale_rows), EXPECTED_STALE_EXCLUSION_COUNT, "metric_artifact"),
        (
            "split_denominator_rows_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in split_rows),
            True,
            "contract_violation",
        ),
        (
            "mask_weight_bindings_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in mask_rows),
            True,
            "contract_violation",
        ),
        (
            "success_guard_bindings_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in success_rows),
            True,
            "contract_violation",
        ),
        (
            "stale_exclusion_bindings_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in stale_rows),
            True,
            "contract_violation",
        ),
        (
            "actor_input_exclusions_pass",
            "actor_contract",
            all(not bool_value(row["actor_visible"]) and bool_value(row["status_pass"]) for row in actor_rows),
            True,
            "contract_violation",
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
            "target_quality_validated_false",
            "claim_boundary",
            any(row["claim_id"] == "m2987-target_quality_validated" and not bool_value(row["claim_made"]) for row in claim_rows),
            True,
            "proof_washout",
        ),
        ("follow_up_audit_registered", "follow_up", source["follow_up_manifest_exists"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2987-gate-{index:04d}-{gate_id}",
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
    dataset_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    mask_rows: list[dict[str, Any]],
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
    target_action_delta_abs_max = max((float(row["target_action_delta_abs_max"]) for row in mask_rows), default=0.0)
    target_loss_weight_sum = sum(float(row["target_loss_weight_sum"]) for row in mask_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2983_status_pass": bool_value(source["m2983_summary"].get("status_pass")),
        "m2983_gate_matrix_pass": bool_value(source["m2983_summary"].get("gate_matrix_pass")),
        "dataset_contract_row_count": len(dataset_rows),
        "split_denominator_row_count": len(split_rows),
        "mask_weight_binding_row_count": len(mask_rows),
        "success_identity_zero_guard_binding_row_count": len(success_rows),
        "stale_guardrail_exclusion_binding_row_count": len(stale_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "candidate_target_tensor_row_count": len(mask_rows),
        "success_identity_zero_target_guard_row_count": len(success_rows),
        "stale_guardrail_exclusion_row_count": len(stale_rows),
        "target_action_delta_abs_max": target_action_delta_abs_max,
        "target_loss_weight_sum": target_loss_weight_sum,
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "fitting_contract_materialized": True,
        "residual_fitting_readiness_claim_made": False,
        "residual_fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
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
            "fitting_contract_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_"
            "fitting_contract_materialization_preflight_fail"
        ),
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2987 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Contract Materialization Preflight

## Summary

- status pass: `{summary["status_pass"]}`
- gate matrix pass: `{summary["gate_matrix_pass"]}`
- required artifacts present: `{summary["required_artifacts_present"]}`
- candidate target tensor rows: `{summary["candidate_target_tensor_row_count"]}`
- success identity zero-target guards: `{summary["success_identity_zero_target_guard_row_count"]}`
- stale guardrail exclusions: `{summary["stale_guardrail_exclusion_row_count"]}`
- target quality validated: `{summary["target_quality_validated"]}`
- residual fitting run: `{summary["residual_fitting_run"]}`
- training run: `{summary["training_run"]}`
- validation run: `{summary["validation_run"]}`
- ranking run: `{summary["ranking_run"]}`
- checkpoint mutated: `{summary["checkpoint_mutated"]}`
- next blocker: `{summary["next_blocker"]}`
- follow-up manifest: `{summary["follow_up_manifest"]}`

## Contract Rows

```text
dataset contract rows: {summary["dataset_contract_row_count"]}
split denominator rows: {summary["split_denominator_row_count"]}
mask weight binding rows: {summary["mask_weight_binding_row_count"]}
success identity zero guard binding rows: {summary["success_identity_zero_guard_binding_row_count"]}
stale guardrail exclusion binding rows: {summary["stale_guardrail_exclusion_binding_row_count"]}
actor input exclusion rows: {summary["actor_input_exclusion_row_count"]}
checkpoint side-effect guard rows: {summary["checkpoint_side_effect_guard_row_count"]}
claim boundary rows: {summary["claim_boundary_row_count"]}
gate rows: {summary["gate_matrix_row_count"]}
```

## Boundary

M2987 materializes fitting-contract artifacts only. It preserves actor
observation/action `{summary["observation_shape"]}/action {summary["action_shape"]}`,
keeps target labels and provenance actor-invisible, keeps success rows as
zero-target guards, keeps stale guardrails excluded, and keeps
`target_quality_validated: false`.

M2987 does not fit, train, validate, rank, select, promote, mutate
checkpoints, or claim repair success, driver performance, paper evidence,
current-sim verdict, high-fidelity validation, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.
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
                "A bounded result audit can accept or reject the M2987 fitting-contract "
                "materialization preflight before any residual fitting training validation ranking "
                "promotion or performance claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2988 audits M2987 fitting-contract artifacts",
                "M2988 selects exactly one next route or stop state",
                "no fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2988 hides missing fitting-contract artifacts",
                "M2988 treats fitting-contract materialization as target-quality validation fitting readiness or performance evidence",
                "M2988 changes actor input or action contract",
                "M2988 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "baseline_artifacts": [
                str(summary_path),
                str(output_dir / "dataset_contract_rows.csv"),
                str(output_dir / "split_denominator_rows.csv"),
                str(output_dir / "mask_weight_binding_rows.csv"),
                str(output_dir / "success_identity_zero_guard_binding_rows.csv"),
                str(output_dir / "stale_guardrail_exclusion_binding_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "decision_rule": (
                "Pass only if M2988 audits M2987 artifacts and selects one next route or stop state "
                "while preserving actor guardrail and claim boundaries without overclaiming."
            ),
            "gate_tier": "process",
            "promotion_decision": "pending",
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
            "lineage": {
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                ],
                "parent_dataset": [str(summary_path), str(output_dir / "gate_matrix.csv"), str(doc_path)],
                "parent_config": [
                    "experiments/manifests/m2987-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-preflight.json"
                ],
                "parent_objective": [
                    "audit fitting-contract materialization before any residual fitting can be admitted"
                ],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2987 materializes contracts but does not itself establish fitting readiness or target quality"
                ],
                "supersedes": ["direct residual fitting immediately after M2987 without result audit"],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "public_gates": [
                "M2988 must audit M2987 contract artifacts and gate matrix",
                "M2988 must preserve target_quality_validated false unless a later target-quality audit is explicitly admitted",
                "M2988 must preserve actor 72/action 3 no target labels or provenance actor inputs",
                "M2988 must not fit train validate rank promote select a winner mutate checkpoints or claim performance paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not fit train validate rank promote select or execute a nonzero residual head",
                "do not mutate save replace or promote checkpoints",
                "do not change actor input or action contract",
                "do not convert contract materialization into target-quality validation fitting readiness performance paper high-fidelity finite-window-vs-GRU or self-ID claims",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_fitting_contract_materialization_result_audit",
                "evidence_increment": "audits M2987 fitting-contract materialization before any fitting-admission decision",
                "claim_scope": "Result audit only; no residual fitting training validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
                "stop_condition": [
                    "stop if M2987 contract artifacts are incomplete or claim-unsafe",
                    "stop if actor target guard stale exclusion or side-effect boundaries are weakened",
                    "stop if the result would be interpreted as fitting readiness performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
                ],
                "fallback_plan": [
                    "route to artifact repair if contract rows are incomplete",
                    "route to fitting-admission design only if the audit accepts M2987 as complete and claim-safe",
                    "route to synthesis pivot or stop if contract materialization cannot preserve boundaries",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2987 materializes fitting-contract artifacts",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit fitting-contract materialization before residual fitting admission",
                "admission_evidence": [
                    "M2987 is expected to materialize dataset split mask weight success guard stale exclusion actor side-effect claim and gate rows",
                    "M2987 must preserve target_quality_validated false and no fitting/training/validation claims",
                ],
                "blocked_shortcuts": [
                    "no residual fitting training validation ranking promotion or success-rate verdict",
                    "no checkpoint mutation save selection or promotion",
                    "no target labels target provenance objective admission source route verdict or paper actor inputs",
                    "no driver-performance current-sim high-fidelity full ideal driver finite-window-vs-GRU paper or self-ID claim",
                ],
                "allowed_updates": [
                    f"docs/{manifest_id}.md",
                    f"docs/reviews/{manifest_id}.md",
                    "M2988 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2988 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2988 accepts or rejects M2987 artifacts",
                    "M2988 chooses one next route or stop state",
                    "actor guard and claim boundaries remain unchanged",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2988 audits fitting contracts and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2988; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2983-M2987 Route A actor-head delta target tensor and fitting-contract chain.",
                "negative_result_policy": "Preserve contract blockers rather than weakening self-ID proof gates.",
                "allowed_claims": [
                    "M2987 artifact completeness after audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits newly materialized fitting-contract artifacts",
                "paper_verdict_delta": "no paper verdict; may enable later fitting-admission design only",
                "must_synthesize_if": [
                    "M2988 cannot select exactly one next route",
                    "M2988 would claim performance validation paper current-sim high-fidelity finite-window-vs-GRU or self-ID evidence",
                ],
            },
            "next_blocker": manifest_id,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2983-dir", type=Path, default=DEFAULT_M2983_DIR)
    parser.add_argument("--m2984-audit", type=Path, default=DEFAULT_M2984_AUDIT)
    parser.add_argument("--m2985-design", type=Path, default=DEFAULT_M2985_DESIGN)
    parser.add_argument("--m2986-synthesis", type=Path, default=DEFAULT_M2986_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_fitting_contract_materialization_preflight(
        m2983_dir=args.m2983_dir,
        m2984_audit=args.m2984_audit,
        m2985_design=args.m2985_design,
        m2986_synthesis=args.m2986_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
