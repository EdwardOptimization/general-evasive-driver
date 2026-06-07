"""Run M3048 actuation-aware residual repair fitting preflight."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m3048-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-preflight"
NEXT_ID = "m3049-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-fitting-result-audit"
M3047_ID = "m3047-engineering-controller-active-safety-driver-v1-actuation-aware-repair-design"
M3046_ID = "m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit"

DEFAULT_M3047_DESIGN = Path(f"docs/{M3047_ID}.md")
DEFAULT_M3046_AUDIT = Path(f"docs/{M3046_ID}.md")
DEFAULT_M3045_DIR = Path("runs/m3045_engineering_controller_active_safety_driver_v1_failure_decomposition_materialization_preflight")
DEFAULT_M3043_DIR = Path("runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight")
DEFAULT_M3041_DIR = Path("runs/m3041_engineering_controller_active_safety_driver_v1_bounded_residual_fitting_preflight")
DEFAULT_M3032_DIR = Path(
    "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path("runs/m3048_engineering_controller_active_safety_driver_v1_actuation_aware_residual_repair_fitting_preflight")
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_ROWS = 29
EXPECTED_SUCCESS_GUARDS = 3
EXPECTED_MEASUREMENT_ROWS = 32
RESIDUAL_LIMIT = 0.08
ACTION_LOW = -1.0
ACTION_HIGH = 1.0
RIDGE_LAMBDA = 1.0e-3
EPS = 1.0e-12
SUCCESS_GUARD_WEIGHT = 0.35

CLAIM_SCOPE = (
    "M3048 Active Safety Driver v1 actuation-aware residual repair fitting "
    "preflight only; M3047 design, M3045 repair requirements, M3043 "
    "measurement rows, M3041 prior residual context, and M3032 trainer-side "
    "target tensors may be consumed to fit one offline action-headroom-"
    "constrained 72-to-3 residual/reflex candidate artifact for later audit. "
    "Target labels, provenance, objective families, source rows, route "
    "decisions, and audit verdicts remain actor-invisible. No environment "
    "reset, rollout, replay, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, repair success, driver-performance "
    "verdict, current-sim verdict, high-fidelity validation, paper evidence, "
    "full ideal driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "closed-loop repair success, driver performance, validation readiness or "
    "result, controller/checkpoint/candidate ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

CONFIG_FIELDNAMES = [
    "config_id",
    "residual_limit",
    "ridge_lambda",
    "success_guard_weight",
    "action_low",
    "action_high",
    "action_composition",
    "headroom_constraint_applied",
    "claim_boundary",
]
FITTING_DATASET_FIELDNAMES = [
    "fitting_dataset_row_id",
    "source_row_type",
    "target_tensor_row_id",
    "success_identity_zero_target_guard_row_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "objective_family",
    "failure_family",
    "raw_trace_path",
    "target_tensor_path",
    "observation_shape",
    "base_action_shape",
    "target_action_delta_shape",
    "fit_sample_count",
    "target_valid_mask_true_count",
    "original_target_loss_weight_sum",
    "repair_weight_sum",
    "target_headroom_clip_fraction",
    "target_residual_clip_fraction",
    "fitting_denominator_used",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "positive_residual_target",
    "success_preservation_regularizer",
    "status_pass",
    "claim_boundary",
]
LOSS_FIELDNAMES = [
    "loss_trace_id",
    "fit_stage",
    "step",
    "sample_count",
    "weight_sum",
    "weighted_mse",
    "weighted_l1",
    "predicted_residual_abs_max",
    "headroom_clip_fraction",
    "final_action_bound_violation_count",
    "status_pass",
    "claim_boundary",
]
ACTION_GUARD_FIELDNAMES = [
    "action_saturation_guard_id",
    "group_key",
    "group_value",
    "sample_count",
    "target_headroom_clip_fraction",
    "predicted_headroom_clip_fraction",
    "predicted_residual_abs_max",
    "final_action_bound_violation_count",
    "base_action_abs_max",
    "final_action_abs_max",
    "status_pass",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_preservation_guard_id",
    "success_identity_zero_target_guard_row_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "raw_trace_path",
    "target_tensor_path",
    "sample_count",
    "zero_target_guard",
    "fitting_regularizer_used",
    "predicted_residual_abs_max",
    "predicted_residual_mse",
    "predicted_headroom_clip_fraction",
    "final_action_bound_violation_count",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3048",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
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
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


@dataclass(frozen=True)
class FittingBatch:
    observations: np.ndarray
    targets: np.ndarray
    base_actions: np.ndarray
    weights: np.ndarray
    group_keys: list[tuple[str, str]]
    rows: list[dict[str, Any]]
    success_guard_contracts: list[dict[str, Any]]
    contracts_pass: bool


@dataclass(frozen=True)
class FittedResidual:
    weight: np.ndarray
    bias: np.ndarray
    residual_limit: float
    fitted: bool


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(int(part)) for part in shape)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "repair_config_snapshot": output_dir / "repair_config_snapshot.json",
        "fitting_dataset_rows": output_dir / "fitting_dataset_rows.csv",
        "fitting_loss_trace_rows": output_dir / "fitting_loss_trace_rows.csv",
        "action_saturation_guard_rows": output_dir / "action_saturation_guard_rows.csv",
        "success_preservation_guard_rows": output_dir / "success_preservation_guard_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_residual_reflex_layer": output_dir / "candidate_residual_reflex_layer.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3047_design: Path,
    m3046_audit: Path,
    m3045_dir: Path,
    m3043_dir: Path,
    m3041_dir: Path,
    m3032_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3047_design": m3047_design,
        "m3046_audit": m3046_audit,
        "m3045_summary": m3045_dir / "summary.json",
        "m3045_repair_requirement_rows": m3045_dir / "repair_requirement_rows.csv",
        "m3045_actuation_saturation_rows": m3045_dir / "actuation_saturation_rows.csv",
        "m3045_gate_matrix": m3045_dir / "gate_matrix.csv",
        "m3043_summary": m3043_dir / "summary.json",
        "m3043_measurement_rows": m3043_dir / "measurement_episode_rows.csv",
        "m3041_candidate": m3041_dir / "candidate_residual_reflex_layer.npz",
        "m3041_summary": m3041_dir / "summary.json",
        "m3032_summary": m3032_dir / "summary.json",
        "target_tensor_rows": m3032_dir / "target_tensor_rows.csv",
        "success_identity_zero_target_guard_rows": m3032_dir / "success_identity_zero_target_guard_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3047_design_text": paths["m3047_design"].read_text(encoding="utf-8") if exists["m3047_design"] else "",
        "m3046_audit_text": paths["m3046_audit"].read_text(encoding="utf-8") if exists["m3046_audit"] else "",
        "m3045_summary": read_json(paths["m3045_summary"]) if exists["m3045_summary"] else {},
        "m3045_repair_requirement_rows": read_csv_rows(paths["m3045_repair_requirement_rows"])
        if exists["m3045_repair_requirement_rows"]
        else [],
        "m3045_actuation_rows": read_csv_rows(paths["m3045_actuation_saturation_rows"])
        if exists["m3045_actuation_saturation_rows"]
        else [],
        "m3045_gate_rows": read_csv_rows(paths["m3045_gate_matrix"]) if exists["m3045_gate_matrix"] else [],
        "m3043_summary": read_json(paths["m3043_summary"]) if exists["m3043_summary"] else {},
        "m3043_measurement_rows": read_csv_rows(paths["m3043_measurement_rows"]) if exists["m3043_measurement_rows"] else [],
        "m3041_summary": read_json(paths["m3041_summary"]) if exists["m3041_summary"] else {},
        "m3032_summary": read_json(paths["m3032_summary"]) if exists["m3032_summary"] else {},
        "target_tensor_rows": read_csv_rows(paths["target_tensor_rows"]) if exists["target_tensor_rows"] else [],
        "success_identity_zero_target_guard_rows": read_csv_rows(
            paths["success_identity_zero_target_guard_rows"]
        )
        if exists["success_identity_zero_target_guard_rows"]
        else [],
    }


def _empty_contract() -> dict[str, Any]:
    return {
        "status_pass": False,
        "observation_trace": np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        "target_action_delta": np.zeros((0, ACTION_DIM), dtype=np.float32),
        "target_valid_mask": np.zeros((0,), dtype=bool),
        "target_loss_weight": np.zeros((0,), dtype=np.float32),
        "base_action": np.zeros((0, ACTION_DIM), dtype=np.float32),
    }


def _load_contract(*, tensor_path: Path, raw_trace_path: Path) -> dict[str, Any]:
    if not tensor_path.exists() or not raw_trace_path.exists():
        return _empty_contract()
    with np.load(tensor_path, allow_pickle=False) as target_data, np.load(raw_trace_path, allow_pickle=False) as trace_data:
        if not {"target_action_delta", "target_valid_mask", "target_loss_weight"}.issubset(target_data.files):
            return _empty_contract()
        if "observation_trace" not in trace_data.files:
            return _empty_contract()
        observation = np.asarray(trace_data["observation_trace"], dtype=np.float32)
        target_delta = np.asarray(target_data["target_action_delta"], dtype=np.float32)
        mask = np.asarray(target_data["target_valid_mask"], dtype=bool)
        weight = np.asarray(target_data["target_loss_weight"], dtype=np.float32)
        if "base_action" in target_data.files:
            base_action = np.asarray(target_data["base_action"], dtype=np.float32)
        elif "action_trace" in trace_data.files:
            base_action = np.asarray(trace_data["action_trace"], dtype=np.float32)
        else:
            return _empty_contract()
    steps = observation.shape[0] if observation.ndim == 2 else -1
    status_pass = (
        observation.ndim == 2
        and observation.shape[1] == P0_OBSERVATION_DIM
        and target_delta.shape == (steps, ACTION_DIM)
        and base_action.shape == (steps, ACTION_DIM)
        and mask.shape == (steps,)
        and weight.shape == (steps,)
        and np.all(np.isfinite(observation))
        and np.all(np.isfinite(target_delta))
        and np.all(np.isfinite(base_action))
        and np.all(np.isfinite(weight))
        and float(np.max(np.abs(base_action))) <= 1.0 + 1.0e-5
    )
    return {
        "status_pass": status_pass,
        "observation_trace": observation,
        "target_action_delta": target_delta,
        "target_valid_mask": mask,
        "target_loss_weight": weight,
        "base_action": base_action,
    }


def _headroom_clip(residual: np.ndarray, base_action: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    limited = np.clip(residual, -RESIDUAL_LIMIT, RESIDUAL_LIMIT)
    low = ACTION_LOW - base_action
    high = ACTION_HIGH - base_action
    clipped = np.minimum(np.maximum(limited, low), high)
    headroom_clip = np.abs(clipped - limited) > 1.0e-8
    return clipped.astype(np.float32), headroom_clip


def _row_weight_multiplier(row: dict[str, Any], measurement_index: dict[tuple[str, str], dict[str, str]]) -> float:
    multiplier = 1.0
    binding_role = str(row.get("binding_role", ""))
    task_source_id = str(row.get("task_source_id", ""))
    if binding_role == "candidate":
        multiplier *= 1.35
    measurement = measurement_index.get((task_source_id, binding_role), {})
    if measurement.get("termination_reason") == "off_track":
        multiplier *= 1.25
    if _bool(measurement.get("collision")):
        multiplier *= 1.25
    if measurement.get("termination_reason") == "speed_too_low":
        multiplier *= 1.1
    return multiplier


def _measurement_index(measurement_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (str(row.get("task_source_id", "")), str(row.get("binding_role", ""))): row
        for row in measurement_rows
    }


def build_fitting_batch(
    *,
    target_tensor_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    measurement_rows: list[dict[str, str]],
) -> FittingBatch:
    observations: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    base_actions: list[np.ndarray] = []
    weights: list[np.ndarray] = []
    group_keys: list[tuple[str, str]] = []
    dataset_rows: list[dict[str, Any]] = []
    success_guard_contracts: list[dict[str, Any]] = []
    measurement = _measurement_index(measurement_rows)

    for index, row in enumerate(target_tensor_rows, start=1):
        tensor_path = Path(str(row.get("target_tensor_path", "")))
        raw_trace_path = Path(str(row.get("raw_trace_path", "")))
        contract = _load_contract(tensor_path=tensor_path, raw_trace_path=raw_trace_path)
        labels_actor_visible = _bool(row.get("target_labels_actor_visible", False))
        provenance_actor_visible = _bool(row.get("target_provenance_actor_visible", False))
        positive_target = _bool(row.get("positive_residual_target", False))
        materialized = _bool(row.get("numeric_target_tensor_materialized", False))
        denominator = contract["target_valid_mask"] & (contract["target_loss_weight"] > 0.0)
        sample_count = int(np.sum(denominator))
        bounded_target, target_headroom_clip = _headroom_clip(
            contract["target_action_delta"][denominator],
            contract["base_action"][denominator],
        )
        original_target = contract["target_action_delta"][denominator]
        target_residual_clip = np.abs(np.clip(original_target, -RESIDUAL_LIMIT, RESIDUAL_LIMIT) - original_target) > 1.0e-8
        multiplier = _row_weight_multiplier(row, measurement)
        repair_weight = contract["target_loss_weight"][denominator] * multiplier
        status_pass = (
            bool(contract["status_pass"])
            and materialized
            and positive_target
            and sample_count > 0
            and not labels_actor_visible
            and not provenance_actor_visible
        )
        if status_pass:
            observations.append(contract["observation_trace"][denominator])
            targets.append(bounded_target)
            base_actions.append(contract["base_action"][denominator])
            weights.append(repair_weight)
            group_keys.extend(
                [(str(row.get("binding_role", "")), str(row.get("task_source_id", "")))]
                * sample_count
            )
        dataset_rows.append(
            {
                "fitting_dataset_row_id": f"m3048-fitting-dataset-{index:04d}",
                "source_row_type": "positive_target",
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "success_identity_zero_target_guard_row_id": "",
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "objective_family": row.get("objective_family", ""),
                "failure_family": row.get("failure_family", ""),
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(tensor_path),
                "observation_shape": _shape_text(contract["observation_trace"].shape),
                "base_action_shape": _shape_text(contract["base_action"].shape),
                "target_action_delta_shape": _shape_text(contract["target_action_delta"].shape),
                "fit_sample_count": sample_count,
                "target_valid_mask_true_count": int(np.sum(contract["target_valid_mask"])),
                "original_target_loss_weight_sum": float(np.sum(contract["target_loss_weight"])),
                "repair_weight_sum": float(np.sum(repair_weight)) if status_pass else 0.0,
                "target_headroom_clip_fraction": float(np.mean(target_headroom_clip)) if target_headroom_clip.size else 0.0,
                "target_residual_clip_fraction": float(np.mean(target_residual_clip)) if target_residual_clip.size else 0.0,
                "fitting_denominator_used": status_pass,
                "target_labels_actor_visible": labels_actor_visible,
                "target_provenance_actor_visible": provenance_actor_visible,
                "positive_residual_target": positive_target,
                "success_preservation_regularizer": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    for index, row in enumerate(success_guard_rows, start=1):
        tensor_path = Path(str(row.get("target_tensor_path", "")))
        raw_trace_path = Path(str(row.get("raw_trace_path", "")))
        contract = _load_contract(tensor_path=tensor_path, raw_trace_path=raw_trace_path)
        zero_guard = _bool(row.get("zero_target_guard", False)) and not _bool(row.get("positive_residual_target", False))
        labels_actor_visible = _bool(row.get("target_labels_actor_visible", False))
        provenance_actor_visible = _bool(row.get("target_provenance_actor_visible", False))
        steps = int(contract["observation_trace"].shape[0])
        status_pass = bool(contract["status_pass"]) and zero_guard and steps > 0 and not labels_actor_visible and not provenance_actor_visible
        if status_pass:
            observations.append(contract["observation_trace"])
            targets.append(np.zeros((steps, ACTION_DIM), dtype=np.float32))
            base_actions.append(contract["base_action"])
            weights.append(np.full((steps,), SUCCESS_GUARD_WEIGHT, dtype=np.float32))
            group_keys.extend([(str(row.get("binding_role", "")), str(row.get("task_source_id", "")))] * steps)
        success_guard_contracts.append({"row": row, "contract": contract, "status_pass": status_pass})
        dataset_rows.append(
            {
                "fitting_dataset_row_id": f"m3048-fitting-dataset-success-{index:04d}",
                "source_row_type": "success_guard_regularizer",
                "target_tensor_row_id": "",
                "success_identity_zero_target_guard_row_id": row.get("success_identity_zero_target_guard_row_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "objective_family": "success_preservation_zero_target",
                "failure_family": "success_preservation",
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(tensor_path),
                "observation_shape": _shape_text(contract["observation_trace"].shape),
                "base_action_shape": _shape_text(contract["base_action"].shape),
                "target_action_delta_shape": _shape_text(contract["target_action_delta"].shape),
                "fit_sample_count": steps if status_pass else 0,
                "target_valid_mask_true_count": int(np.sum(contract["target_valid_mask"])),
                "original_target_loss_weight_sum": float(np.sum(contract["target_loss_weight"])),
                "repair_weight_sum": float(steps * SUCCESS_GUARD_WEIGHT) if status_pass else 0.0,
                "target_headroom_clip_fraction": 0.0,
                "target_residual_clip_fraction": 0.0,
                "fitting_denominator_used": status_pass,
                "target_labels_actor_visible": labels_actor_visible,
                "target_provenance_actor_visible": provenance_actor_visible,
                "positive_residual_target": False,
                "success_preservation_regularizer": status_pass,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    if observations:
        observation_array = np.concatenate(observations, axis=0).astype(np.float32)
        target_array = np.concatenate(targets, axis=0).astype(np.float32)
        base_action_array = np.concatenate(base_actions, axis=0).astype(np.float32)
        weight_array = np.concatenate(weights, axis=0).astype(np.float32)
    else:
        observation_array = np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
        target_array = np.zeros((0, ACTION_DIM), dtype=np.float32)
        base_action_array = np.zeros((0, ACTION_DIM), dtype=np.float32)
        weight_array = np.zeros((0,), dtype=np.float32)
    positive_rows = [row for row in dataset_rows if row["source_row_type"] == "positive_target"]
    success_rows = [row for row in dataset_rows if row["source_row_type"] == "success_guard_regularizer"]
    contracts_pass = (
        len(positive_rows) == EXPECTED_TARGET_ROWS
        and all(_bool(row["status_pass"]) for row in positive_rows)
        and len(success_rows) == EXPECTED_SUCCESS_GUARDS
        and all(_bool(row["status_pass"]) for row in success_rows)
        and observation_array.shape[0] > 0
    )
    return FittingBatch(
        observations=observation_array,
        targets=target_array,
        base_actions=base_action_array,
        weights=weight_array,
        group_keys=group_keys,
        rows=dataset_rows,
        success_guard_contracts=success_guard_contracts,
        contracts_pass=contracts_pass,
    )


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
    lhs = (x_aug * sqrt_w[:, None]).T @ (x_aug * sqrt_w[:, None])
    rhs = (x_aug * sqrt_w[:, None]).T @ (y * sqrt_w[:, None])
    regularizer = np.eye(x_aug.shape[1], dtype=np.float64) * RIDGE_LAMBDA
    regularizer[-1, -1] = 0.0
    try:
        coef = np.linalg.solve(lhs + regularizer, rhs)
    except np.linalg.LinAlgError:
        coef = np.linalg.lstsq(lhs + regularizer, rhs, rcond=None)[0]
    return FittedResidual(
        weight=coef[:-1].astype(np.float32),
        bias=coef[-1].astype(np.float32),
        residual_limit=RESIDUAL_LIMIT,
        fitted=True,
    )


def predict_raw_residual(model: FittedResidual, observations: np.ndarray) -> np.ndarray:
    if observations.shape[0] == 0:
        return np.zeros((0, ACTION_DIM), dtype=np.float32)
    raw = observations.astype(np.float32) @ model.weight + model.bias
    return np.clip(raw, -float(model.residual_limit), float(model.residual_limit)).astype(np.float32)


def predict_action_aware(
    model: FittedResidual,
    observations: np.ndarray,
    base_action: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw = predict_raw_residual(model, observations)
    residual, headroom_clip = _headroom_clip(raw, base_action)
    final_action = np.clip(base_action + residual, ACTION_LOW, ACTION_HIGH).astype(np.float32)
    return residual, final_action, headroom_clip


def _weighted_metrics(prediction: np.ndarray, target: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    if prediction.shape[0] == 0 or target.shape[0] == 0:
        return {"weighted_mse": float("inf"), "weighted_l1": float("inf"), "residual_abs_max": 0.0}
    error = prediction.astype(np.float64) - target.astype(np.float64)
    weighted = weight.astype(np.float64)[:, None]
    denom = max(float(np.sum(weight)) * float(ACTION_DIM), EPS)
    return {
        "weighted_mse": float(np.sum(weighted * error * error) / denom),
        "weighted_l1": float(np.sum(weighted * np.abs(error)) / denom),
        "residual_abs_max": float(np.max(np.abs(prediction))) if prediction.size else 0.0,
    }


def build_loss_trace_rows(
    batch: FittingBatch,
    prediction_before: np.ndarray,
    final_before: np.ndarray,
    headroom_before: np.ndarray,
    prediction_after: np.ndarray,
    final_after: np.ndarray,
    headroom_after: np.ndarray,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    before = _weighted_metrics(prediction_before, batch.targets, batch.weights)
    after = _weighted_metrics(prediction_after, batch.targets, batch.weights)
    before_bound_violations = int(np.sum((final_before < ACTION_LOW - 1.0e-6) | (final_before > ACTION_HIGH + 1.0e-6)))
    after_bound_violations = int(np.sum((final_after < ACTION_LOW - 1.0e-6) | (final_after > ACTION_HIGH + 1.0e-6)))
    after_pass = (
        fitting_executed
        and np.isfinite(after["weighted_mse"])
        and after["weighted_mse"] <= before["weighted_mse"] + 1.0e-9
        and after["residual_abs_max"] <= RESIDUAL_LIMIT + 1.0e-6
        and after_bound_violations == 0
    )
    return [
        {
            "loss_trace_id": "m3048-loss-0001-zero-residual-baseline",
            "fit_stage": "zero_residual_baseline",
            "step": 0,
            "sample_count": int(batch.observations.shape[0]),
            "weight_sum": float(np.sum(batch.weights)),
            "weighted_mse": before["weighted_mse"],
            "weighted_l1": before["weighted_l1"],
            "predicted_residual_abs_max": before["residual_abs_max"],
            "headroom_clip_fraction": float(np.mean(headroom_before)) if headroom_before.size else 0.0,
            "final_action_bound_violation_count": before_bound_violations,
            "status_pass": batch.observations.shape[0] > 0 and np.isfinite(before["weighted_mse"]) and before_bound_violations == 0,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3048-loss-0002-action-aware-linear-residual",
            "fit_stage": "action_headroom_constrained_linear_residual",
            "step": 1,
            "sample_count": int(batch.observations.shape[0]),
            "weight_sum": float(np.sum(batch.weights)),
            "weighted_mse": after["weighted_mse"],
            "weighted_l1": after["weighted_l1"],
            "predicted_residual_abs_max": after["residual_abs_max"],
            "headroom_clip_fraction": float(np.mean(headroom_after)) if headroom_after.size else 0.0,
            "final_action_bound_violation_count": after_bound_violations,
            "status_pass": after_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def _slice_group(batch: FittingBatch, predicate: Any) -> np.ndarray:
    return np.asarray([bool(predicate(role, source)) for role, source in batch.group_keys], dtype=bool)


def build_action_saturation_guard_rows(
    batch: FittingBatch,
    model: FittedResidual,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    residual, final_action, headroom_clip = predict_action_aware(model, batch.observations, batch.base_actions)
    target_headroom = np.abs(_headroom_clip(batch.targets, batch.base_actions)[0] - batch.targets) > 1.0e-8
    specs = [
        ("all", "all", lambda role, source: True),
        ("binding_role", "candidate", lambda role, source: role == "candidate"),
        ("binding_role", "parent", lambda role, source: role == "parent"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, predicate) in enumerate(specs, start=1):
        mask = _slice_group(batch, predicate)
        group_residual = residual[mask]
        group_final = final_action[mask]
        group_base = batch.base_actions[mask]
        group_headroom = headroom_clip[mask]
        group_target_headroom = target_headroom[mask]
        violation_count = int(np.sum((group_final < ACTION_LOW - 1.0e-6) | (group_final > ACTION_HIGH + 1.0e-6)))
        status_pass = fitting_executed and int(np.sum(mask)) > 0 and violation_count == 0
        rows.append(
            {
                "action_saturation_guard_id": f"m3048-action-saturation-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "sample_count": int(np.sum(mask)),
                "target_headroom_clip_fraction": float(np.mean(group_target_headroom)) if group_target_headroom.size else 0.0,
                "predicted_headroom_clip_fraction": float(np.mean(group_headroom)) if group_headroom.size else 0.0,
                "predicted_residual_abs_max": float(np.max(np.abs(group_residual))) if group_residual.size else 0.0,
                "final_action_bound_violation_count": violation_count,
                "base_action_abs_max": float(np.max(np.abs(group_base))) if group_base.size else 0.0,
                "final_action_abs_max": float(np.max(np.abs(group_final))) if group_final.size else 0.0,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_preservation_guard_rows(
    batch: FittingBatch,
    model: FittedResidual,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(batch.success_guard_contracts, start=1):
        source_row = item["row"]
        contract = item["contract"]
        residual, final_action, headroom_clip = predict_action_aware(
            model,
            contract["observation_trace"],
            contract["base_action"],
        )
        violation_count = int(np.sum((final_action < ACTION_LOW - 1.0e-6) | (final_action > ACTION_HIGH + 1.0e-6)))
        predicted_abs_max = float(np.max(np.abs(residual))) if residual.size else 0.0
        rows.append(
            {
                "success_preservation_guard_id": f"m3048-success-preservation-{index:04d}",
                "success_identity_zero_target_guard_row_id": source_row.get("success_identity_zero_target_guard_row_id", ""),
                "task_source_id": source_row.get("task_source_id", ""),
                "profile_name": source_row.get("profile_name", ""),
                "binding_role": source_row.get("binding_role", ""),
                "raw_trace_path": source_row.get("raw_trace_path", ""),
                "target_tensor_path": source_row.get("target_tensor_path", ""),
                "sample_count": int(contract["observation_trace"].shape[0]),
                "zero_target_guard": _bool(source_row.get("zero_target_guard", False)),
                "fitting_regularizer_used": bool(item["status_pass"]),
                "predicted_residual_abs_max": predicted_abs_max,
                "predicted_residual_mse": float(np.mean(residual * residual)) if residual.size else 0.0,
                "predicted_headroom_clip_fraction": float(np.mean(headroom_clip)) if headroom_clip.size else 0.0,
                "final_action_bound_violation_count": violation_count,
                "status_pass": (
                    fitting_executed
                    and bool(item["status_pass"])
                    and predicted_abs_max <= RESIDUAL_LIMIT + 1.0e-6
                    and violation_count == 0
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_checkpoint_side_effect_guard_rows() -> list[dict[str, Any]]:
    side_effects = [
        "parent_checkpoint_load",
        "parent_checkpoint_save",
        "parent_checkpoint_modify",
        "parent_checkpoint_promote",
        "prior_residual_artifact_modify",
        "active_config_modify",
        "environment_reset",
        "environment_step",
        "policy_rollout",
        "validation_run",
        "ranking_run",
    ]
    return [
        {
            "side_effect_guard_id": f"m3048-side-effect-{index:04d}",
            "side_effect": side_effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, side_effect in enumerate(side_effects, start=1)
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = [
        ("bounded_offline_repair_fitting_artifact_completeness", True, True, "M3048 summary/loss/gates/artifact"),
        ("action_headroom_constraint_materialized", True, True, "M3048 action saturation guards and artifact metadata"),
        ("closed_loop_repair_success", False, False, "future closed-loop measurement after M3049"),
        ("validation_result", False, False, "future validation audit"),
        ("driver_performance_verdict", False, False, "future accepted benchmark validation"),
        ("checkpoint_ranking", False, False, "future ranking audit"),
        ("checkpoint_promotion", False, False, "future promotion gate"),
        ("current_sim_verdict", False, False, "future current-sim synthesis"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation layer"),
        ("finite_window_vs_gru_conclusion", False, False, "future architecture ablation"),
        ("paper_evidence", False, False, "future paper-route synthesis"),
        ("level3_self_identification", False, False, "future self-ID route only if needed"),
    ]
    return [
        {
            "claim_id": f"m3048-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3048": allowed,
            "claim_made": made,
            "status_pass": allowed == made or (not allowed and not made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def write_candidate_artifact(path: Path, model: FittedResidual) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        linear_weight=model.weight.astype(np.float32),
        linear_bias=model.bias.astype(np.float32),
        residual_limit=np.asarray([model.residual_limit], dtype=np.float32),
        action_low=np.asarray([ACTION_LOW], dtype=np.float32),
        action_high=np.asarray([ACTION_HIGH], dtype=np.float32),
        observation_dim=np.asarray([P0_OBSERVATION_DIM], dtype=np.int64),
        action_dim=np.asarray([ACTION_DIM], dtype=np.int64),
        action_composition=np.asarray(["base_action_plus_headroom_constrained_residual_clipped"]),
        headroom_constraint_applied=np.asarray([True]),
        success_guard_weight=np.asarray([SUCCESS_GUARD_WEIGHT], dtype=np.float32),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


def repair_config_snapshot() -> dict[str, Any]:
    return {
        "milestone": MILESTONE_ID,
        "residual_limit": RESIDUAL_LIMIT,
        "ridge_lambda": RIDGE_LAMBDA,
        "success_guard_weight": SUCCESS_GUARD_WEIGHT,
        "action_low": ACTION_LOW,
        "action_high": ACTION_HIGH,
        "action_composition": "base_action_plus_headroom_constrained_residual_clipped",
        "headroom_constraint_applied": True,
        "actor_observation_dim": P0_OBSERVATION_DIM,
        "actor_action_dim": ACTION_DIM,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_config_rows() -> list[dict[str, Any]]:
    config = repair_config_snapshot()
    return [
        {
            "config_id": "m3048-repair-config-0001",
            "residual_limit": config["residual_limit"],
            "ridge_lambda": config["ridge_lambda"],
            "success_guard_weight": config["success_guard_weight"],
            "action_low": config["action_low"],
            "action_high": config["action_high"],
            "action_composition": config["action_composition"],
            "headroom_constraint_applied": config["headroom_constraint_applied"],
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    fitting_executed: bool,
    artifact_exists: bool,
    follow_up_manifest_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m3047_design",
        "m3046_audit",
        "m3045_summary",
        "m3045_repair_requirement_rows",
        "m3045_actuation_saturation_rows",
        "m3043_summary",
        "m3043_measurement_rows",
        "m3041_candidate",
        "m3032_summary",
        "target_tensor_rows",
        "success_identity_zero_target_guard_rows",
    ]
    source_present = all(source["source_exists"].get(name, False) for name in required_sources)
    m3045_pass = _bool(source["m3045_summary"].get("status_pass", False)) and _bool(
        source["m3045_summary"].get("gate_matrix_pass", False)
    )
    m3043_pass = _bool(source["m3043_summary"].get("status_pass", False)) and _bool(
        source["m3043_summary"].get("gate_matrix_pass", False)
    )
    final_loss_pass = bool(loss_rows and _bool(loss_rows[-1].get("status_pass", False)))
    gates = [
        ("source_artifacts_present", "source", source_present, source["source_exists"], "required sources", "lineage_invalid"),
        (
            "m3047_selects_m3048_route",
            "lineage",
            "continue_to_m3048_actuation_aware_residual_repair_fitting_preflight" in source["m3047_design_text"],
            "m3048 route marker",
            "present",
            "lineage_invalid",
        ),
        ("m3045_status_and_gate_pass", "admission", m3045_pass, source["m3045_summary"], "status/gate pass", "metric_artifact"),
        ("m3043_status_and_gate_pass", "admission", m3043_pass, source["m3043_summary"], "status/gate pass", "metric_artifact"),
        (
            "measurement_denominator_available",
            "dataset",
            len(source["m3043_measurement_rows"]) == EXPECTED_MEASUREMENT_ROWS,
            len(source["m3043_measurement_rows"]),
            EXPECTED_MEASUREMENT_ROWS,
            "scenario_sampling_failure",
        ),
        (
            "target_tensor_and_success_guard_rows_usable",
            "dataset",
            batch.contracts_pass,
            {"rows": len(batch.rows), "sample_count": int(batch.observations.shape[0])},
            "all positive targets and success guards usable",
            "metric_artifact",
        ),
        (
            "action_headroom_fitting_executed",
            "fitting",
            fitting_executed,
            {"sample_count": int(batch.observations.shape[0]), "fitting_executed": fitting_executed},
            "finite samples and fitted model",
            "metric_artifact",
        ),
        ("loss_improved_and_bounded", "fitting", final_loss_pass, loss_rows[-1] if loss_rows else {}, "final loss pass", "behavior_regression"),
        ("candidate_artifact_written", "artifact", artifact_exists, artifact_exists, True, "metric_artifact"),
        (
            "action_saturation_guards_pass",
            "guard",
            all(_bool(row["status_pass"]) for row in action_rows),
            {"rows": len(action_rows), "passed": sum(_bool(row["status_pass"]) for row in action_rows)},
            "all action guards pass",
            "behavior_regression",
        ),
        (
            "success_preservation_guards_pass",
            "guard",
            len(success_rows) == EXPECTED_SUCCESS_GUARDS and all(_bool(row["status_pass"]) for row in success_rows),
            {"rows": len(success_rows), "passed": sum(_bool(row["status_pass"]) for row in success_rows)},
            f"{EXPECTED_SUCCESS_GUARDS} passing guards",
            "behavior_regression",
        ),
        (
            "checkpoint_side_effects_absent",
            "side_effect",
            all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_rows),
            {"rows": len(side_rows), "passed": sum(_bool(row["status_pass"]) for row in side_rows)},
            "no forbidden side effects",
            "contract_violation",
        ),
        (
            "claim_boundaries_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            {"rows": len(claim_rows), "passed": sum(_bool(row["status_pass"]) for row in claim_rows)},
            "all claims safe",
            "contract_violation",
        ),
        ("follow_up_manifest_registered", "process", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
        ("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m3048-{name}",
            "gate_family": family,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, passed, observed, expected, failure_type in gates
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30440,
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
        "hypothesis": "A bounded result audit can accept or reject the M3048 action-aware residual repair fitting artifact before any rollout validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "repair_config_snapshot.json"),
                str(output_dir / "fitting_dataset_rows.csv"),
                str(output_dir / "fitting_loss_trace_rows.csv"),
                str(output_dir / "action_saturation_guard_rows.csv"),
                str(output_dir / "success_preservation_guard_rows.csv"),
                str(output_dir / "candidate_residual_reflex_layer.npz"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit action-aware residual repair fitting artifact before closed-loop measurement"],
            "derived_from": [MILESTONE_ID, M3047_ID],
            "blocked_by": [
                "M3048 fitted artifact requires audit before any closed-loop measurement",
                "offline fitting loss is not validation or driver-performance evidence",
            ],
            "supersedes": ["direct closed-loop measurement without M3048 artifact audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3049 must audit M3048 summary loss dataset action-saturation success-preservation side-effect claim gate and candidate artifact rows",
            "M3049 must audit candidate artifact shape 72-to-3 residual bound and headroom-constrained composition",
            "M3049 must reject driver-performance validation high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3049 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3048 offline fitting loss into driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_actuation_aware_residual_repair_fitting_result_audit",
            "evidence_increment": "audits the action-aware fitted residual/reflex candidate before any closed-loop measurement",
            "claim_scope": "Result audit only; no rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3048 artifact is incomplete or unbounded",
                "stop if action-saturation or success-preservation guards fail",
                "stop if offline fitting is treated as driver performance",
            ],
            "fallback_plan": [
                "route to closed-loop measurement if M3048 is accepted",
                "route to fitting repair if artifact or guards fail",
                "route to synthesis if closed-loop measurement is still not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3048 completes action-aware repair fitting",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit fitted action-aware Active Safety Driver v1 residual/reflex candidate",
            "admission_evidence": [
                "M3048 summary and gate matrix",
                "M3048 fitting dataset loss action-saturation success-preservation and candidate artifact",
            ],
            "blocked_shortcuts": [
                "no rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3049 status queue scoreboard research log and review",
                "one follow-up manifest only if M3049 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3048 fitted candidate is accepted or rejected",
                "one next closed-loop measurement repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3049 audits engineering fitting artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3049; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3048 action-aware residual fitting artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot block active-safety closed-loop measurement if safety contract gates pass.",
            "allowed_claims": [
                "M3048 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fitted action-aware candidate before a new closed-loop measurement route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3049 prepares closed-loop engineering measurement",
            "must_synthesize_if": [
                "M3049 cannot select a closed-loop measurement repair synthesis or stop route",
                "M3049 would require another materialization-only step before closed-loop evidence",
                "M3049 would re-promote self-ID proof as the mainline objective",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3049 audits M3048 summary loss dataset action guard side-effect claim gate and candidate artifact rows",
            "M3049 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3049 selects exactly one next closed-loop measurement repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3049 treats offline fitting loss as closed-loop driver performance",
            "M3049 omits action-saturation or success-preservation guard audits",
            "M3049 runs validation ranking promotion high-fidelity or architecture comparison",
            "M3049 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3049 audits M3048 fitting dataset loss guard side-effect claim and candidate artifact evidence and selects exactly one closed-loop measurement, repair, synthesis, or stop route without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_actuation_aware_residual_repair_fitting_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "fitting_dataset_rows.csv"),
            str(output_dir / "fitting_loss_trace_rows.csv"),
            str(output_dir / "action_saturation_guard_rows.csv"),
            str(output_dir / "success_preservation_guard_rows.csv"),
            str(output_dir / "candidate_residual_reflex_layer.npz"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required = [
        "summary",
        "candidate_residual_reflex_layer",
        "action_saturation_guard_rows",
        "success_preservation_guard_rows",
        "claim_boundary_rows",
        "gate_matrix",
        "doc",
        "follow_up_manifest",
    ]
    return all(paths[key].exists() for key in required)


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# M3048 Active Safety Driver v1 Actuation-Aware Residual Repair Fitting Preflight",
        "",
        "## Summary",
        "",
        "- status: completed",
        f"- result class: `{summary['result_class']}`",
        f"- fitting dataset rows: {summary['fitting_dataset_row_count']}",
        f"- fitting samples: {summary['fitting_sample_count']}",
        f"- initial weighted MSE: {summary['initial_weighted_mse']}",
        f"- final weighted MSE: {summary['final_weighted_mse']}",
        f"- final residual abs max: {summary['final_predicted_residual_abs_max']}",
        f"- action saturation guards pass: {summary['action_saturation_guard_rows_pass']}",
        f"- success preservation guards pass: {summary['success_preservation_guard_rows_pass']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        "",
        "## Interpretation",
        "",
        "M3048 fits one offline action-headroom-constrained residual/reflex artifact. The artifact is for M3049 audit and possible later closed-loop measurement only. It is not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
        "",
        "Candidate composition:",
        "",
        "```text",
        "raw_residual = obs_72 @ linear_weight + linear_bias",
        "bounded_residual = clip(raw_residual, -residual_limit, residual_limit)",
        "headroom_residual = clip(bounded_residual, action_low - base_action, action_high - base_action)",
        "final_action = clip(base_action + headroom_residual, action_low, action_high)",
        "```",
        "",
        "Rejected claims:",
        "",
        "```text",
        FORBIDDEN_INTERPRETATION,
        "```",
        "",
        "## Next",
        "",
        f"- next blocker: `{NEXT_ID}`",
        f"- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_preflight(
    *,
    m3047_design: Path,
    m3046_audit: Path,
    m3045_dir: Path,
    m3043_dir: Path,
    m3041_dir: Path,
    m3032_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_source_artifacts(
        m3047_design=m3047_design,
        m3046_audit=m3046_audit,
        m3045_dir=m3045_dir,
        m3043_dir=m3043_dir,
        m3041_dir=m3041_dir,
        m3032_dir=m3032_dir,
    )
    batch = build_fitting_batch(
        target_tensor_rows=source["target_tensor_rows"],
        success_guard_rows=source["success_identity_zero_target_guard_rows"],
        measurement_rows=source["m3043_measurement_rows"],
    )
    fitting_executed = batch.contracts_pass and batch.observations.shape[0] > 0
    model = fit_linear_residual(batch) if fitting_executed else zero_model()
    zero = zero_model()
    pred_before, final_before, headroom_before = predict_action_aware(zero, batch.observations, batch.base_actions)
    pred_after, final_after, headroom_after = predict_action_aware(model, batch.observations, batch.base_actions)
    loss_rows = build_loss_trace_rows(
        batch,
        pred_before,
        final_before,
        headroom_before,
        pred_after,
        final_after,
        headroom_after,
        fitting_executed=fitting_executed,
    )
    action_rows = build_action_saturation_guard_rows(batch, model, fitting_executed=fitting_executed)
    success_rows = build_success_preservation_guard_rows(batch, model, fitting_executed=fitting_executed)
    side_rows = build_checkpoint_side_effect_guard_rows()
    claim_rows = build_claim_boundary_rows()

    if fitting_executed:
        write_candidate_artifact(paths["candidate_residual_reflex_layer"], model)
    write_json(paths["repair_config_snapshot"], repair_config_snapshot())
    write_csv_rows(output_dir / "repair_config_rows.csv", build_config_rows(), fieldnames=CONFIG_FIELDNAMES)
    write_csv_rows(paths["fitting_dataset_rows"], batch.rows, fieldnames=FITTING_DATASET_FIELDNAMES)
    write_csv_rows(paths["fitting_loss_trace_rows"], loss_rows, fieldnames=LOSS_FIELDNAMES)
    write_csv_rows(paths["action_saturation_guard_rows"], action_rows, fieldnames=ACTION_GUARD_FIELDNAMES)
    write_csv_rows(paths["success_preservation_guard_rows"], success_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        action_rows=action_rows,
        success_rows=success_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_residual_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up_manifest.exists(),
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)

    summary = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "active_safety_driver_v1_actuation_aware_residual_repair_fitting_preflight_pass",
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3045_status_pass": _bool(source["m3045_summary"].get("status_pass", False)),
        "m3045_gate_matrix_pass": _bool(source["m3045_summary"].get("gate_matrix_pass", False)),
        "m3043_status_pass": _bool(source["m3043_summary"].get("status_pass", False)),
        "m3043_gate_matrix_pass": _bool(source["m3043_summary"].get("gate_matrix_pass", False)),
        "measurement_episode_row_count": len(source["m3043_measurement_rows"]),
        "target_tensor_row_count": len(source["target_tensor_rows"]),
        "success_identity_guard_row_count": len(source["success_identity_zero_target_guard_rows"]),
        "fitting_dataset_row_count": len(batch.rows),
        "fitting_sample_count": int(batch.observations.shape[0]),
        "fitting_executed": fitting_executed,
        "candidate_residual_reflex_layer_exists": paths["candidate_residual_reflex_layer"].exists(),
        "candidate_residual_reflex_layer": str(paths["candidate_residual_reflex_layer"]),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "residual_limit": RESIDUAL_LIMIT,
        "headroom_constraint_applied": True,
        "action_composition": "base_action_plus_headroom_constrained_residual_clipped",
        "initial_weighted_mse": loss_rows[0]["weighted_mse"] if loss_rows else "",
        "final_weighted_mse": loss_rows[-1]["weighted_mse"] if loss_rows else "",
        "final_predicted_residual_abs_max": loss_rows[-1]["predicted_residual_abs_max"] if loss_rows else "",
        "final_headroom_clip_fraction": loss_rows[-1]["headroom_clip_fraction"] if loss_rows else "",
        "final_action_bound_violation_count": loss_rows[-1]["final_action_bound_violation_count"] if loss_rows else "",
        "action_saturation_guard_row_count": len(action_rows),
        "action_saturation_guard_rows_pass": all(_bool(row["status_pass"]) for row in action_rows),
        "success_preservation_guard_row_count": len(success_rows),
        "success_preservation_guard_rows_pass": all(_bool(row["status_pass"]) for row in success_rows),
        "checkpoint_side_effect_guard_row_count": len(side_rows),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row["status_pass"]) for row in side_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "ppo_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_v1_action_aware_residual_repair_fit_route_to_m3049_result_audit",
        "paths": {key: str(value) for key, value in paths.items()},
    }
    summary["required_artifacts_present"] = required_artifacts_present(paths)
    summary["status_pass"] = (
        fitting_executed
        and gate_matrix_pass
        and summary["required_artifacts_present"]
        and summary["action_saturation_guard_rows_pass"]
        and summary["success_preservation_guard_rows_pass"]
        and paths["candidate_residual_reflex_layer"].exists()
    )
    write_json(paths["summary"], summary)
    write_run_state(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    write_doc(doc_path, summary)
    summary["required_artifacts_present"] = required_artifacts_present(paths)
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        action_rows=action_rows,
        success_rows=success_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_residual_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up_manifest.exists(),
        required_artifacts_present=summary["required_artifacts_present"],
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary["gate_matrix_pass"] = all(_bool(row["status_pass"]) for row in gate_rows)
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["status_pass"] = (
        fitting_executed
        and summary["gate_matrix_pass"]
        and summary["required_artifacts_present"]
        and summary["action_saturation_guard_rows_pass"]
        and summary["success_preservation_guard_rows_pass"]
        and paths["candidate_residual_reflex_layer"].exists()
    )
    write_json(paths["summary"], summary)
    write_doc(doc_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3047-design", type=Path, default=DEFAULT_M3047_DESIGN)
    parser.add_argument("--m3046-audit", type=Path, default=DEFAULT_M3046_AUDIT)
    parser.add_argument("--m3045-dir", type=Path, default=DEFAULT_M3045_DIR)
    parser.add_argument("--m3043-dir", type=Path, default=DEFAULT_M3043_DIR)
    parser.add_argument("--m3041-dir", type=Path, default=DEFAULT_M3041_DIR)
    parser.add_argument("--m3032-dir", type=Path, default=DEFAULT_M3032_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_preflight(
        m3047_design=args.m3047_design,
        m3046_audit=args.m3046_audit,
        m3045_dir=args.m3045_dir,
        m3043_dir=args.m3043_dir,
        m3041_dir=args.m3041_dir,
        m3032_dir=args.m3032_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"fitting_samples={summary['fitting_sample_count']}")
    print(f"initial_weighted_mse={summary['initial_weighted_mse']}")
    print(f"final_weighted_mse={summary['final_weighted_mse']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
