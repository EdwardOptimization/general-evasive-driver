"""Run M2990 bounded nonzero residual fitting preflight.

M2990 consumes accepted M2987 fitting-contract rows and M2983 target tensors.
It builds a trainer-side fitting dataset, fits one bounded offline linear
residual artifact, and writes audit rows. It does not run an environment,
validate a policy, rank candidates, mutate checkpoints, promote checkpoints, or
make driver-performance claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
    "m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-fitting-preflight"
)
NEXT_ID = (
    "m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-fitting-result-audit"
)
DEFAULT_M2987_DIR = Path(
    "runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_fitting_contract_materialization_preflight"
)
DEFAULT_M2988_AUDIT = Path(
    "docs/m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-contract-materialization-result-audit.md"
)
DEFAULT_M2989_DESIGN = Path(
    "docs/m2989-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-fitting-admission-design.md"
)
DEFAULT_M2983_DIR = Path(
    "runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_target_tensor_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2990_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_bounded_fitting_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-fitting-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-bounded-fitting-result-audit.json"
)

EXPECTED_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_GUARD_COUNT = 13
EXPECTED_STALE_EXCLUSION_COUNT = 11
RESIDUAL_LIMIT = 0.08
RIDGE_LAMBDA = 1.0e-3
EPS = 1.0e-12

CLAIM_SCOPE = (
    "M2990 Route A actor-head delta nonzero residual bounded fitting preflight only; accepted "
    "M2987 fitting contracts and M2983 target tensors may be consumed to produce trainer-side "
    "offline fitting artifacts and loss traces for a later M2991 audit. Target labels, provenance, "
    "objective families, source rows, route decisions, and audit verdicts remain actor-invisible. "
    "No environment reset, policy rollout, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, repair success, driver-performance, paper, current-sim verdict, "
    "high-fidelity validation, full ideal driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality validation, closed-loop repair success, driver performance, validation readiness "
    "or result, controller/source/task/profile/checkpoint/candidate ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, "
    "or level3 self-identification"
)

FITTING_DATASET_FIELDNAMES = [
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "mask_weight_binding_id",
    "training_admission_candidate_id",
    "objective_family",
    "outcome_bucket",
    "raw_trace_path",
    "target_tensor_path",
    "observation_shape",
    "target_action_delta_shape",
    "fit_sample_count",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "fitting_denominator_used",
    "target_quality_validated",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "status_pass",
    "claim_boundary",
]
FITTING_LOSS_FIELDNAMES = [
    "loss_trace_id",
    "fit_stage",
    "step",
    "sample_count",
    "weight_sum",
    "weighted_mse",
    "weighted_l1",
    "predicted_residual_abs_max",
    "status_pass",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_guard_loss_id",
    "success_identity_zero_guard_binding_id",
    "success_identity_zero_target_guard_row_id",
    "raw_trace_path",
    "target_tensor_path",
    "zero_target_guard",
    "fitting_denominator_used",
    "target_action_delta_abs_max",
    "predicted_residual_abs_max",
    "predicted_residual_mse",
    "status_pass",
    "claim_boundary",
]
STALE_EXCLUSION_FIELDNAMES = [
    "stale_exclusion_audit_id",
    "stale_guardrail_exclusion_binding_id",
    "stale_guardrail_exclusion_row_id",
    "guard_family",
    "fitting_denominator_used",
    "validation_denominator_used",
    "paper_denominator_used",
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
    "allowed_in_m2990",
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
    "fitting_dataset_rows",
    "fitting_loss_trace_rows",
    "success_guard_loss_rows",
    "stale_exclusion_audit_rows",
    "actor_input_exclusion_rows",
    "checkpoint_side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "candidate_residual_head_artifact",
    "run_state",
    "doc",
]


@dataclass(frozen=True)
class FittingBatch:
    observations: np.ndarray
    targets: np.ndarray
    weights: np.ndarray
    rows: list[dict[str, Any]]
    contracts_pass: bool


@dataclass(frozen=True)
class FittedResidual:
    weight: np.ndarray
    bias: np.ndarray
    residual_limit: float
    fitted: bool


def run_bounded_fitting_preflight(
    *,
    m2987_dir: Path | str = DEFAULT_M2987_DIR,
    m2988_audit: Path | str = DEFAULT_M2988_AUDIT,
    m2989_design: Path | str = DEFAULT_M2989_DESIGN,
    m2983_dir: Path | str = DEFAULT_M2983_DIR,
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
        m2987_dir=Path(m2987_dir),
        m2988_audit=Path(m2988_audit),
        m2989_design=Path(m2989_design),
        m2983_dir=Path(m2983_dir),
    )

    batch = build_fitting_batch(source)
    model = fit_linear_residual(batch) if batch.contracts_pass else zero_model()
    fitting_executed = bool(batch.contracts_pass and model.fitted)
    predictions_before = np.zeros_like(batch.targets, dtype=np.float32)
    predictions_after = predict_residual(model, batch.observations) if fitting_executed else predictions_before
    loss_rows = build_loss_trace_rows(batch, predictions_before, predictions_after, fitting_executed=fitting_executed)

    if fitting_executed:
        write_candidate_artifact(paths["candidate_residual_head_artifact"], model)

    success_rows = build_success_guard_loss_rows(source, model=model, fitting_executed=fitting_executed)
    stale_rows = build_stale_exclusion_audit_rows(source)
    actor_rows = build_actor_input_exclusion_rows()
    side_effect_rows = build_checkpoint_side_effect_guard_rows()

    write_csv_rows(paths["fitting_dataset_rows"], batch.rows, fieldnames=FITTING_DATASET_FIELDNAMES)
    write_csv_rows(paths["fitting_loss_trace_rows"], loss_rows, fieldnames=FITTING_LOSS_FIELDNAMES)
    write_csv_rows(paths["success_guard_loss_rows"], success_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["stale_exclusion_audit_rows"], stale_rows, fieldnames=STALE_EXCLUSION_FIELDNAMES)
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
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
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
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=required_artifacts_present,
    )
    write_run_state(
        paths["run_state"],
        {
            "fitting_dataset_row_count": len(batch.rows),
            "fitting_sample_count": int(batch.observations.shape[0]),
            "success_guard_loss_row_count": len(success_rows),
            "stale_exclusion_audit_row_count": len(stale_rows),
            "claim_boundary_row_count": summary["claim_boundary_row_count"],
            "gate_matrix_row_count": summary["gate_matrix_row_count"],
            "residual_fitting_run": fitting_executed,
            "training_run": fitting_executed,
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
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS),
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "fitting_dataset_rows": output_dir / "fitting_dataset_rows.csv",
        "fitting_loss_trace_rows": output_dir / "fitting_loss_trace_rows.csv",
        "success_guard_loss_rows": output_dir / "success_guard_loss_rows.csv",
        "stale_exclusion_audit_rows": output_dir / "stale_exclusion_audit_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_residual_head_artifact": output_dir / "candidate_residual_head_artifact.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2987_dir: Path,
    m2988_audit: Path,
    m2989_design: Path,
    m2983_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m2987_summary": m2987_dir / "summary.json",
        "mask_weight_binding_rows": m2987_dir / "mask_weight_binding_rows.csv",
        "success_identity_zero_guard_binding_rows": m2987_dir / "success_identity_zero_guard_binding_rows.csv",
        "stale_guardrail_exclusion_binding_rows": m2987_dir / "stale_guardrail_exclusion_binding_rows.csv",
        "m2987_gate_matrix": m2987_dir / "gate_matrix.csv",
        "m2988_audit": m2988_audit,
        "m2989_design": m2989_design,
        "m2983_target_tensor_rows": m2983_dir / "target_tensor_rows.csv",
        "m2983_success_identity_zero_target_guard_rows": m2983_dir / "success_identity_zero_target_guard_rows.csv",
        "m2983_stale_guardrail_exclusion_rows": m2983_dir / "stale_guardrail_exclusion_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m2987_summary": read_json(paths["m2987_summary"]) if exists["m2987_summary"] else {},
        "mask_weight_binding_rows": read_csv_rows(paths["mask_weight_binding_rows"])
        if exists["mask_weight_binding_rows"]
        else [],
        "success_identity_zero_guard_binding_rows": read_csv_rows(paths["success_identity_zero_guard_binding_rows"])
        if exists["success_identity_zero_guard_binding_rows"]
        else [],
        "stale_guardrail_exclusion_binding_rows": read_csv_rows(paths["stale_guardrail_exclusion_binding_rows"])
        if exists["stale_guardrail_exclusion_binding_rows"]
        else [],
        "m2987_gate_rows": read_csv_rows(paths["m2987_gate_matrix"]) if exists["m2987_gate_matrix"] else [],
        "m2988_audit_text": paths["m2988_audit"].read_text(encoding="utf-8") if exists["m2988_audit"] else "",
        "m2989_design_text": paths["m2989_design"].read_text(encoding="utf-8") if exists["m2989_design"] else "",
        "m2983_target_tensor_rows": read_csv_rows(paths["m2983_target_tensor_rows"])
        if exists["m2983_target_tensor_rows"]
        else [],
        "m2983_success_identity_zero_target_guard_rows": read_csv_rows(
            paths["m2983_success_identity_zero_target_guard_rows"]
        )
        if exists["m2983_success_identity_zero_target_guard_rows"]
        else [],
        "m2983_stale_guardrail_exclusion_rows": read_csv_rows(paths["m2983_stale_guardrail_exclusion_rows"])
        if exists["m2983_stale_guardrail_exclusion_rows"]
        else [],
        "follow_up_manifest_exists": False,
    }


def build_fitting_batch(source: dict[str, Any]) -> FittingBatch:
    target_rows_by_id = {row["target_tensor_row_id"]: row for row in source["m2983_target_tensor_rows"]}
    observations: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    weights: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []

    for index, binding in enumerate(source["mask_weight_binding_rows"], start=1):
        target_row = target_rows_by_id.get(binding.get("target_tensor_row_id", ""), {})
        tensor_path = Path(target_row.get("target_tensor_path") or binding.get("target_tensor_path", ""))
        raw_trace_path = Path(target_row.get("raw_trace_path", ""))
        target_quality_validated = bool_value(binding.get("target_quality_validated", False)) or bool_value(
            target_row.get("target_quality_validated", False)
        )
        labels_actor_visible = bool_value(binding.get("target_labels_actor_visible", False)) or bool_value(
            target_row.get("target_labels_actor_visible", False)
        )
        provenance_actor_visible = bool_value(binding.get("target_provenance_actor_visible", False)) or bool_value(
            target_row.get("target_provenance_actor_visible", False)
        )
        contract = _load_candidate_contract(tensor_path=tensor_path, raw_trace_path=raw_trace_path)
        denominator = contract["target_valid_mask"] & (contract["target_loss_weight"] > 0.0)
        fit_sample_count = int(np.sum(denominator))
        status_pass = (
            bool_value(binding.get("status_pass", False))
            and bool_value(binding.get("fit_candidate_after_audit", False))
            and bool(contract["status_pass"])
            and fit_sample_count > 0
            and not target_quality_validated
            and not labels_actor_visible
            and not provenance_actor_visible
        )
        if status_pass:
            observations.append(contract["observation_trace"][denominator])
            targets.append(contract["target_action_delta"][denominator])
            weights.append(contract["target_loss_weight"][denominator])
        rows.append(
            {
                "fitting_dataset_row_id": f"m2990-fitting-dataset-{index:04d}",
                "target_tensor_row_id": binding.get("target_tensor_row_id", ""),
                "mask_weight_binding_id": binding.get("mask_weight_binding_id", ""),
                "training_admission_candidate_id": binding.get("training_admission_candidate_id", ""),
                "objective_family": binding.get("objective_family", ""),
                "outcome_bucket": binding.get("outcome_bucket", ""),
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(tensor_path),
                "observation_shape": _shape_text(contract["observation_trace"].shape),
                "target_action_delta_shape": _shape_text(contract["target_action_delta"].shape),
                "fit_sample_count": fit_sample_count,
                "target_valid_mask_true_count": int(np.sum(contract["target_valid_mask"])),
                "target_loss_weight_sum": float(np.sum(contract["target_loss_weight"])),
                "fitting_denominator_used": status_pass,
                "target_quality_validated": target_quality_validated,
                "target_labels_actor_visible": labels_actor_visible,
                "target_provenance_actor_visible": provenance_actor_visible,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    if observations:
        observation_array = np.concatenate(observations, axis=0).astype(np.float32)
        target_array = np.concatenate(targets, axis=0).astype(np.float32)
        weight_array = np.concatenate(weights, axis=0).astype(np.float32)
    else:
        observation_array = np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
        target_array = np.zeros((0, ACTION_DIM), dtype=np.float32)
        weight_array = np.zeros((0,), dtype=np.float32)
    contracts_pass = (
        len(rows) == EXPECTED_CANDIDATE_COUNT
        and all(bool_value(row["status_pass"]) for row in rows)
        and observation_array.shape[0] > 0
    )
    return FittingBatch(
        observations=observation_array,
        targets=target_array,
        weights=weight_array,
        rows=rows,
        contracts_pass=contracts_pass,
    )


def _shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(int(part)) for part in shape)


def _empty_candidate_contract() -> dict[str, Any]:
    return {
        "status_pass": False,
        "observation_trace": np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        "target_action_delta": np.zeros((0, ACTION_DIM), dtype=np.float32),
        "target_valid_mask": np.zeros((0,), dtype=bool),
        "target_loss_weight": np.zeros((0,), dtype=np.float32),
    }


def _load_candidate_contract(*, tensor_path: Path, raw_trace_path: Path) -> dict[str, Any]:
    if not tensor_path.exists() or not raw_trace_path.exists():
        return _empty_candidate_contract()
    with np.load(tensor_path, allow_pickle=False) as target_data, np.load(raw_trace_path, allow_pickle=False) as trace_data:
        required_target = {"target_action_delta", "target_valid_mask", "target_loss_weight"}
        required_trace = {"observation_trace"}
        if not required_target.issubset(target_data.files) or not required_trace.issubset(trace_data.files):
            return _empty_candidate_contract()
        observation = np.asarray(trace_data["observation_trace"], dtype=np.float32)
        target_delta = np.asarray(target_data["target_action_delta"], dtype=np.float32)
        mask = np.asarray(target_data["target_valid_mask"], dtype=bool)
        weight = np.asarray(target_data["target_loss_weight"], dtype=np.float32)
    steps = observation.shape[0] if observation.ndim == 2 else -1
    status_pass = (
        observation.ndim == 2
        and observation.shape[1] == P0_OBSERVATION_DIM
        and target_delta.shape == (steps, ACTION_DIM)
        and mask.shape == (steps,)
        and weight.shape == (steps,)
        and np.all(np.isfinite(observation))
        and np.all(np.isfinite(target_delta))
        and np.all(np.isfinite(weight))
    )
    return {
        "status_pass": bool(status_pass),
        "observation_trace": observation if status_pass else np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        "target_action_delta": target_delta if status_pass else np.zeros((0, ACTION_DIM), dtype=np.float32),
        "target_valid_mask": mask if status_pass else np.zeros((0,), dtype=bool),
        "target_loss_weight": weight if status_pass else np.zeros((0,), dtype=np.float32),
    }


def zero_model() -> FittedResidual:
    return FittedResidual(
        weight=np.zeros((P0_OBSERVATION_DIM, ACTION_DIM), dtype=np.float32),
        bias=np.zeros((ACTION_DIM,), dtype=np.float32),
        residual_limit=RESIDUAL_LIMIT,
        fitted=False,
    )


def fit_linear_residual(batch: FittingBatch) -> FittedResidual:
    if batch.observations.shape[0] == 0:
        return zero_model()
    x = batch.observations.astype(np.float64)
    y = batch.targets.astype(np.float64)
    w = np.maximum(batch.weights.astype(np.float64), 0.0)
    x_aug = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float64)], axis=1)
    sqrt_w = np.sqrt(w + EPS)
    x_weighted = x_aug * sqrt_w[:, None]
    y_weighted = y * sqrt_w[:, None]
    regularizer = np.eye(x_aug.shape[1], dtype=np.float64) * RIDGE_LAMBDA
    regularizer[-1, -1] = 0.0
    lhs = x_weighted.T @ x_weighted + regularizer
    rhs = x_weighted.T @ y_weighted
    try:
        coef = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
    return FittedResidual(
        weight=coef[:-1].astype(np.float32),
        bias=coef[-1].astype(np.float32),
        residual_limit=RESIDUAL_LIMIT,
        fitted=True,
    )


def predict_residual(model: FittedResidual, observations: np.ndarray) -> np.ndarray:
    if observations.shape[0] == 0:
        return np.zeros((0, ACTION_DIM), dtype=np.float32)
    raw = observations.astype(np.float32) @ model.weight + model.bias
    return np.clip(raw, -float(model.residual_limit), float(model.residual_limit)).astype(np.float32)


def write_candidate_artifact(path: Path, model: FittedResidual) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        linear_weight=model.weight.astype(np.float32),
        linear_bias=model.bias.astype(np.float32),
        residual_limit=np.asarray([model.residual_limit], dtype=np.float32),
        observation_dim=np.asarray([P0_OBSERVATION_DIM], dtype=np.int64),
        action_dim=np.asarray([ACTION_DIM], dtype=np.int64),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


def _weighted_metrics(prediction: np.ndarray, target: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    if prediction.shape[0] == 0 or target.shape[0] == 0:
        return {"weighted_mse": float("inf"), "weighted_l1": float("inf"), "residual_abs_max": 0.0}
    denom = max(float(np.sum(weight)) * float(ACTION_DIM), EPS)
    error = prediction.astype(np.float64) - target.astype(np.float64)
    weighted = weight.astype(np.float64)[:, None]
    return {
        "weighted_mse": float(np.sum(weighted * error * error) / denom),
        "weighted_l1": float(np.sum(weighted * np.abs(error)) / denom),
        "residual_abs_max": float(np.max(np.abs(prediction))) if prediction.size else 0.0,
    }


def build_loss_trace_rows(
    batch: FittingBatch,
    predictions_before: np.ndarray,
    predictions_after: np.ndarray,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    before = _weighted_metrics(predictions_before, batch.targets, batch.weights)
    after = _weighted_metrics(predictions_after, batch.targets, batch.weights)
    after_pass = (
        fitting_executed
        and np.isfinite(after["weighted_mse"])
        and np.isfinite(after["weighted_l1"])
        and after["weighted_mse"] <= before["weighted_mse"] + 1.0e-9
        and after["residual_abs_max"] <= RESIDUAL_LIMIT + 1.0e-6
    )
    return [
        {
            "loss_trace_id": "m2990-loss-0001-zero-residual-baseline",
            "fit_stage": "zero_residual_baseline",
            "step": 0,
            "sample_count": int(batch.observations.shape[0]),
            "weight_sum": float(np.sum(batch.weights)),
            "weighted_mse": before["weighted_mse"],
            "weighted_l1": before["weighted_l1"],
            "predicted_residual_abs_max": before["residual_abs_max"],
            "status_pass": batch.observations.shape[0] > 0 and np.isfinite(before["weighted_mse"]),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m2990-loss-0002-bounded-linear-residual",
            "fit_stage": "bounded_linear_residual",
            "step": 1,
            "sample_count": int(batch.observations.shape[0]),
            "weight_sum": float(np.sum(batch.weights)),
            "weighted_mse": after["weighted_mse"],
            "weighted_l1": after["weighted_l1"],
            "predicted_residual_abs_max": after["residual_abs_max"],
            "status_pass": after_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_success_guard_loss_rows(
    source: dict[str, Any],
    *,
    model: FittedResidual,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    m2983_success_by_id = {
        row["success_identity_zero_target_guard_row_id"]: row
        for row in source["m2983_success_identity_zero_target_guard_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, binding in enumerate(source["success_identity_zero_guard_binding_rows"], start=1):
        success_id = binding.get("success_identity_zero_target_guard_row_id", "")
        source_row = m2983_success_by_id.get(success_id, {})
        raw_trace_path = Path(source_row.get("raw_trace_path", ""))
        target_tensor_path = Path(binding.get("target_tensor_path", ""))
        observation = _load_observation_trace(raw_trace_path)
        prediction = predict_residual(model, observation) if fitting_executed else np.zeros((0, ACTION_DIM), dtype=np.float32)
        target_zero = float(binding.get("target_action_delta_abs_max", 1.0)) == 0.0
        zero_guard = bool_value(binding.get("zero_target_guard", False)) and not bool_value(
            binding.get("positive_residual_target", False)
        )
        not_denominator = not bool_value(binding.get("future_fitting_denominator_allowed_after_audit", True))
        bounded_prediction = prediction.size > 0 and np.all(np.isfinite(prediction)) and (
            float(np.max(np.abs(prediction))) <= RESIDUAL_LIMIT + 1.0e-6
        )
        rows.append(
            {
                "success_guard_loss_id": f"m2990-success-guard-loss-{index:04d}",
                "success_identity_zero_guard_binding_id": binding.get("success_identity_zero_guard_binding_id", ""),
                "success_identity_zero_target_guard_row_id": success_id,
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(target_tensor_path),
                "zero_target_guard": zero_guard,
                "fitting_denominator_used": False,
                "target_action_delta_abs_max": float(binding.get("target_action_delta_abs_max", 0.0)),
                "predicted_residual_abs_max": float(np.max(np.abs(prediction))) if prediction.size else 0.0,
                "predicted_residual_mse": float(np.mean(prediction * prediction)) if prediction.size else 0.0,
                "status_pass": fitting_executed and target_zero and zero_guard and not_denominator and bounded_prediction,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _load_observation_trace(raw_trace_path: Path) -> np.ndarray:
    if not raw_trace_path.exists():
        return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
    with np.load(raw_trace_path, allow_pickle=False) as data:
        if "observation_trace" not in data.files:
            return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
        observation = np.asarray(data["observation_trace"], dtype=np.float32)
    if observation.ndim != 2 or observation.shape[1] != P0_OBSERVATION_DIM or not np.all(np.isfinite(observation)):
        return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
    return observation


def build_stale_exclusion_audit_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["stale_guardrail_exclusion_binding_rows"], start=1):
        status_pass = (
            bool_value(row.get("status_pass", False))
            and bool_value(row.get("stale_guardrail_excluded", False))
            and not bool_value(row.get("future_fitting_denominator_allowed_after_audit", False))
            and not bool_value(row.get("validation_denominator_allowed", False))
            and not bool_value(row.get("paper_denominator_allowed", False))
        )
        rows.append(
            {
                "stale_exclusion_audit_id": f"m2990-stale-exclusion-audit-{index:04d}",
                "stale_guardrail_exclusion_binding_id": row.get("stale_guardrail_exclusion_binding_id", ""),
                "stale_guardrail_exclusion_row_id": row.get("stale_guardrail_exclusion_row_id", ""),
                "guard_family": row.get("guard_family", ""),
                "fitting_denominator_used": False,
                "validation_denominator_used": False,
                "paper_denominator_used": False,
                "stale_guardrail_excluded": bool_value(row.get("stale_guardrail_excluded", False)),
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
            "actor_input_exclusion_id": f"m2990-actor-input-exclusion-{index:04d}",
            "forbidden_metadata_key": key,
            "actor_visible": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, key in enumerate(forbidden, start=1)
    ]


def build_checkpoint_side_effect_guard_rows() -> list[dict[str, Any]]:
    side_effects = [
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
    return [
        {
            "side_effect_guard_id": f"m2990-side-effect-guard-{index:04d}",
            "side_effect": effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, effect in enumerate(side_effects, start=1)
    ]


def build_claim_boundary_rows(*, fitting_executed: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("bounded_offline_fitting_artifact", "artifact", fitting_executed, "M2990 fitting artifact"),
        ("fitting_loss_trace", "artifact", fitting_executed, "M2990 loss trace rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2991 audit manifest"),
    ]
    blocked = [
        ("target_quality_validated", "target_quality", "future target-quality audit"),
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
    rows = [_claim_row(claim_id, family, True, bool(made), evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(_claim_row(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def _claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2990-{claim_id}",
        "claim_family": family,
        "allowed_in_m2990": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    fitting_executed: bool,
    candidate_artifact_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m2987_summary = source["m2987_summary"]
    final_loss = loss_rows[-1] if loss_rows else {}
    initial_loss = loss_rows[0] if loss_rows else {}
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        ("m2987_status_pass", "lineage", bool_value(m2987_summary.get("status_pass")), True, "lineage_invalid"),
        (
            "m2987_gate_matrix_pass",
            "lineage",
            bool_value(m2987_summary.get("gate_matrix_pass")),
            True,
            "lineage_invalid",
        ),
        (
            "m2988_accepts_m2987",
            "lineage",
            "accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design"
            in source["m2988_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2989_admits_m2990",
            "lineage",
            "admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion"
            in source["m2989_design_text"],
            True,
            "lineage_invalid",
        ),
        ("candidate_row_count", "artifact", len(batch.rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        (
            "fitting_dataset_rows_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in batch.rows),
            True,
            "contract_violation",
        ),
        ("fitting_sample_count_positive", "artifact", int(batch.observations.shape[0]) > 0, True, "metric_artifact"),
        ("bounded_fitting_executed", "execution", fitting_executed, True, "training_instability"),
        ("candidate_artifact_written", "artifact", candidate_artifact_exists, True, "metric_artifact"),
        (
            "fitting_loss_finite",
            "artifact",
            bool_value(final_loss.get("status_pass", False)),
            True,
            "training_instability",
        ),
        (
            "fitting_loss_not_worse_than_zero",
            "artifact",
            float(final_loss.get("weighted_mse", float("inf"))) <= float(initial_loss.get("weighted_mse", -float("inf"))) + 1.0e-9,
            True,
            "training_instability",
        ),
        (
            "success_guard_count",
            "guardrail",
            len(success_rows),
            EXPECTED_SUCCESS_GUARD_COUNT,
            "metric_artifact",
        ),
        (
            "success_guard_rows_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in success_rows),
            True,
            "contract_violation",
        ),
        ("stale_exclusion_count", "guardrail", len(stale_rows), EXPECTED_STALE_EXCLUSION_COUNT, "metric_artifact"),
        (
            "stale_exclusion_rows_pass",
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
            any(row["claim_id"] == "m2990-target_quality_validated" and not bool_value(row["claim_made"]) for row in claim_rows),
            True,
            "proof_washout",
        ),
        ("follow_up_audit_registered", "follow_up", source["follow_up_manifest_exists"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2990-gate-{index:04d}-{gate_id}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (gate_id, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def _write_summary_doc_and_gates(
    *,
    paths: dict[str, Path],
    output_dir: Path,
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    fitting_executed: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    claim_rows = build_claim_boundary_rows(
        fitting_executed=fitting_executed,
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        candidate_artifact_exists=paths["candidate_residual_head_artifact"].exists(),
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_manifest,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    fitting_executed: bool,
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool_value(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    initial_loss = loss_rows[0] if loss_rows else {}
    final_loss = loss_rows[-1] if loss_rows else {}
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2987_status_pass": bool_value(source["m2987_summary"].get("status_pass")),
        "m2987_gate_matrix_pass": bool_value(source["m2987_summary"].get("gate_matrix_pass")),
        "fitting_dataset_row_count": len(batch.rows),
        "fitting_sample_count": int(batch.observations.shape[0]),
        "fitting_weight_sum": float(np.sum(batch.weights)),
        "initial_weighted_mse": float(initial_loss.get("weighted_mse", float("inf"))),
        "final_weighted_mse": float(final_loss.get("weighted_mse", float("inf"))),
        "final_weighted_l1": float(final_loss.get("weighted_l1", float("inf"))),
        "fitting_loss_improved_or_equal": bool_value(final_loss.get("status_pass", False)),
        "candidate_residual_head_artifact": str(paths["candidate_residual_head_artifact"]),
        "candidate_residual_head_artifact_exists": paths["candidate_residual_head_artifact"].exists(),
        "success_guard_loss_row_count": len(success_rows),
        "success_guard_predicted_residual_abs_max": max(
            (float(row["predicted_residual_abs_max"]) for row in success_rows),
            default=0.0,
        ),
        "stale_exclusion_audit_row_count": len(stale_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "candidate_target_tensor_row_count": len(batch.rows),
        "success_identity_zero_target_guard_row_count": len(success_rows),
        "stale_guardrail_exclusion_row_count": len(stale_rows),
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "bounded_offline_fitting_run": fitting_executed,
        "residual_fitting_run": fitting_executed,
        "training_run": fitting_executed,
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
            "engineering_controller_route_a_actor_head_delta_nonzero_residual_bounded_fitting_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_bounded_fitting_preflight_fail"
        ),
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2990 Engineering Controller Route A Actor-Head Delta Nonzero Residual Bounded Fitting Preflight

## Summary

- status pass: `{summary["status_pass"]}`
- gate matrix pass: `{summary["gate_matrix_pass"]}`
- required artifacts present: `{summary["required_artifacts_present"]}`
- fitting dataset rows: `{summary["fitting_dataset_row_count"]}`
- fitting samples: `{summary["fitting_sample_count"]}`
- initial weighted MSE: `{summary["initial_weighted_mse"]}`
- final weighted MSE: `{summary["final_weighted_mse"]}`
- success guard rows: `{summary["success_guard_loss_row_count"]}`
- success guard predicted residual abs max: `{summary["success_guard_predicted_residual_abs_max"]}`
- stale exclusion rows: `{summary["stale_exclusion_audit_row_count"]}`
- target quality validated: `{summary["target_quality_validated"]}`
- bounded offline fitting run: `{summary["bounded_offline_fitting_run"]}`
- validation run: `{summary["validation_run"]}`
- ranking run: `{summary["ranking_run"]}`
- checkpoint mutated: `{summary["checkpoint_mutated"]}`
- next blocker: `{summary["next_blocker"]}`
- follow-up manifest: `{summary["follow_up_manifest"]}`

## Boundary

M2990 performs bounded offline fitting only. It writes a candidate linear
residual-head artifact and loss trace for M2991 audit, while preserving actor
observation/action `{summary["observation_shape"]}/action {summary["action_shape"]}`,
keeping target labels and provenance actor-invisible, keeping success rows as
zero-target guard checks, and keeping stale guardrails excluded.

M2990 does not run an environment, validate a policy, rank candidates, select a
winner, mutate or promote checkpoints, or claim repair success, driver
performance, paper evidence, current-sim verdict, high-fidelity validation,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.
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
                "A bounded result audit can accept or reject the M2990 offline fitting artifacts "
                "before any validation ranking promotion repair-success performance or self-ID claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2991 audits M2990 bounded fitting artifacts",
                "M2991 selects exactly one next route or stop state",
                "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2991 hides missing M2990 fitting artifacts",
                "M2991 treats fitting loss as target-quality validation repair success or performance evidence",
                "M2991 changes actor input or action contract",
                "M2991 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "baseline_artifacts": [
                str(summary_path),
                str(output_dir / "fitting_dataset_rows.csv"),
                str(output_dir / "fitting_loss_trace_rows.csv"),
                str(output_dir / "success_guard_loss_rows.csv"),
                str(output_dir / "stale_exclusion_audit_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "candidate_residual_head_artifact.npz"),
                str(doc_path),
            ],
            "decision_rule": (
                "Pass only if M2991 audits M2990 fitting artifacts and selects one next route or stop "
                "state while preserving actor guard stale exclusion target-quality checkpoint and claim boundaries."
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
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                ],
                "parent_dataset": [str(summary_path), str(output_dir / "gate_matrix.csv"), str(doc_path)],
                "parent_config": [
                    "experiments/manifests/m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-preflight.json"
                ],
                "parent_objective": [
                    "audit bounded offline residual fitting artifacts before any validation or promotion route"
                ],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2990 may produce fitting artifacts but cannot establish target quality repair success or performance"
                ],
                "supersedes": ["direct validation or promotion immediately after M2990 without result audit"],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "public_gates": [
                "M2991 must audit M2990 fitting dataset loss trace success guard stale exclusion artifact and gate rows",
                "M2991 must preserve target_quality_validated false unless a later target-quality audit is explicitly admitted",
                "M2991 must preserve actor 72/action 3 no target labels or provenance actor inputs",
                "M2991 must not validate rank promote mutate checkpoints or claim performance paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not run environment validation ranking winner selection private holdout or performance measurement",
                "do not mutate save replace or promote checkpoints",
                "do not change actor input or action contract",
                "do not convert fitting loss into target-quality validation repair-success performance paper high-fidelity finite-window-vs-GRU or self-ID claims",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_bounded_fitting_result_audit",
                "evidence_increment": "audits M2990 bounded offline fitting artifacts before any further route",
                "claim_scope": "Result audit only; no validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
                "stop_condition": [
                    "stop if M2990 fitting artifacts are incomplete or claim-unsafe",
                    "stop if actor target guard stale exclusion or side-effect boundaries are weakened",
                    "stop if the result would be interpreted as target-quality validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
                ],
                "fallback_plan": [
                    "route to artifact repair if fitting rows are incomplete",
                    "route to target-quality or validation design only after accepting M2990 as claim-safe",
                    "route to synthesis pivot or stop if fitting cannot preserve boundaries",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2990 produces bounded offline fitting artifacts",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit bounded fitting artifacts before validation or promotion",
                "admission_evidence": [
                    "M2990 is expected to write fitting dataset loss trace success guard stale exclusion artifact and gate rows",
                    "M2990 must preserve target_quality_validated false and no validation/ranking/promotion claims",
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
                    "M2991 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2991 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2991 accepts or rejects M2990 artifacts",
                    "M2991 chooses one next route or stop state",
                    "actor guard and claim boundaries remain unchanged",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2991 audits fitting artifacts and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2991; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2983-M2990 Route A actor-head delta target tensor fitting-contract and fitting chain.",
                "negative_result_policy": "Preserve fitting blockers rather than weakening self-ID proof gates.",
                "allowed_claims": [
                    "M2990 artifact completeness after audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits newly produced bounded fitting artifacts",
                "paper_verdict_delta": "no paper verdict; may enable later target-quality or validation design only",
                "must_synthesize_if": [
                    "M2991 cannot select exactly one next route",
                    "M2991 would claim performance validation paper current-sim high-fidelity finite-window-vs-GRU or self-ID evidence",
                ],
            },
            "next_blocker": manifest_id,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2987-dir", type=Path, default=DEFAULT_M2987_DIR)
    parser.add_argument("--m2988-audit", type=Path, default=DEFAULT_M2988_AUDIT)
    parser.add_argument("--m2989-design", type=Path, default=DEFAULT_M2989_DESIGN)
    parser.add_argument("--m2983-dir", type=Path, default=DEFAULT_M2983_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_bounded_fitting_preflight(
        m2987_dir=args.m2987_dir,
        m2988_audit=args.m2988_audit,
        m2989_design=args.m2989_design,
        m2983_dir=args.m2983_dir,
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
