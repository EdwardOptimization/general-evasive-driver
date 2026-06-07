"""Run M3041 Active Safety Driver v1 bounded residual fitting preflight."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m3041-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-preflight"
NEXT_ID = "m3042-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-result-audit"
M3040_ID = (
    "m3040-engineering-controller-active-safety-driver-v1-guarded-training-admission-"
    "materialization-result-audit"
)
DEFAULT_M3040_AUDIT = Path(f"docs/{M3040_ID}.md")
DEFAULT_M3039_DIR = Path(
    "runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_"
    "admission_materialization_preflight"
)
DEFAULT_M3032_DIR = Path(
    "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_"
    "failure_target_tensor_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3041_engineering_controller_active_safety_driver_v1_bounded_residual_fitting_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_ROWS = 29
EXPECTED_SUCCESS_GUARDS = 3
RESIDUAL_LIMIT = 0.08
RIDGE_LAMBDA = 1.0e-3
EPS = 1.0e-12
NEXT_PRIORITY = 30370

CLAIM_SCOPE = (
    "M3041 Active Safety Driver v1 bounded residual fitting preflight only; "
    "accepted M3040/M3039 admission artifacts and M3032 trainer-side target "
    "tensors may be consumed to fit one offline 72-to-3 residual/reflex "
    "candidate artifact for later audit. Target labels, provenance, objective "
    "families, source rows, route decisions, and audit verdicts remain actor-"
    "invisible. No environment reset, rollout, replay, validation, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, repair "
    "success, driver-performance verdict, current-sim verdict, high-fidelity "
    "validation, paper evidence, full ideal driver, finite-window-vs-GRU, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "closed-loop repair success, driver performance, validation readiness or "
    "result, controller/checkpoint/candidate ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

FITTING_DATASET_FIELDNAMES = [
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "objective_family",
    "failure_family",
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
    "positive_residual_target",
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
    "status_pass",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_guard_loss_id",
    "success_identity_zero_target_guard_row_id",
    "raw_trace_path",
    "target_tensor_path",
    "zero_target_guard",
    "fitting_denominator_used",
    "positive_residual_target",
    "target_action_delta_abs_max",
    "predicted_residual_abs_max",
    "predicted_residual_mse",
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
    "allowed_in_m3041",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "fitting_dataset_rows": output_dir / "fitting_dataset_rows.csv",
        "fitting_loss_trace_rows": output_dir / "fitting_loss_trace_rows.csv",
        "success_guard_loss_rows": output_dir / "success_guard_loss_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_residual_reflex_layer": output_dir / "candidate_residual_reflex_layer.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(*, m3040_audit: Path, m3039_dir: Path, m3032_dir: Path) -> dict[str, Any]:
    paths = {
        "m3040_audit": m3040_audit,
        "m3039_summary": m3039_dir / "summary.json",
        "m3039_objective_rows": m3039_dir / "active_safety_training_objective_rows.csv",
        "m3039_scenario_rows": m3039_dir / "scenario_panel_rows.csv",
        "m3039_guardrail_rows": m3039_dir / "training_guardrail_rows.csv",
        "m3039_pressure_rows": m3039_dir / "baseline_pressure_rows.csv",
        "m3039_gate_matrix": m3039_dir / "gate_matrix.csv",
        "m3032_summary": m3032_dir / "summary.json",
        "target_tensor_rows": m3032_dir / "target_tensor_rows.csv",
        "success_identity_zero_target_guard_rows": m3032_dir / "success_identity_zero_target_guard_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3040_audit_text": paths["m3040_audit"].read_text() if exists["m3040_audit"] else "",
        "m3039_summary": read_json(paths["m3039_summary"]) if exists["m3039_summary"] else {},
        "m3039_objective_rows": read_csv_rows(paths["m3039_objective_rows"])
        if exists["m3039_objective_rows"]
        else [],
        "m3039_scenario_rows": read_csv_rows(paths["m3039_scenario_rows"]) if exists["m3039_scenario_rows"] else [],
        "m3039_guardrail_rows": read_csv_rows(paths["m3039_guardrail_rows"])
        if exists["m3039_guardrail_rows"]
        else [],
        "m3039_pressure_rows": read_csv_rows(paths["m3039_pressure_rows"]) if exists["m3039_pressure_rows"] else [],
        "m3039_gate_rows": read_csv_rows(paths["m3039_gate_matrix"]) if exists["m3039_gate_matrix"] else [],
        "m3032_summary": read_json(paths["m3032_summary"]) if exists["m3032_summary"] else {},
        "target_tensor_rows": read_csv_rows(paths["target_tensor_rows"]) if exists["target_tensor_rows"] else [],
        "success_identity_zero_target_guard_rows": read_csv_rows(
            paths["success_identity_zero_target_guard_rows"]
        )
        if exists["success_identity_zero_target_guard_rows"]
        else [],
    }


def _shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(int(part)) for part in shape)


def _empty_contract() -> dict[str, Any]:
    return {
        "status_pass": False,
        "observation_trace": np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        "target_action_delta": np.zeros((0, ACTION_DIM), dtype=np.float32),
        "target_valid_mask": np.zeros((0,), dtype=bool),
        "target_loss_weight": np.zeros((0,), dtype=np.float32),
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
    if not status_pass:
        return _empty_contract()
    return {
        "status_pass": True,
        "observation_trace": observation,
        "target_action_delta": target_delta,
        "target_valid_mask": mask,
        "target_loss_weight": weight,
    }


def build_fitting_batch(target_tensor_rows: list[dict[str, Any]]) -> FittingBatch:
    observations: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    weights: list[np.ndarray] = []
    dataset_rows: list[dict[str, Any]] = []
    for index, row in enumerate(target_tensor_rows, start=1):
        tensor_path = Path(str(row.get("target_tensor_path", "")))
        raw_trace_path = Path(str(row.get("raw_trace_path", "")))
        contract = _load_contract(tensor_path=tensor_path, raw_trace_path=raw_trace_path)
        target_quality_validated = _bool(row.get("target_quality_validated", False))
        labels_actor_visible = _bool(row.get("target_labels_actor_visible", False))
        provenance_actor_visible = _bool(row.get("target_provenance_actor_visible", False))
        positive_target = _bool(row.get("positive_residual_target", False))
        materialized = _bool(row.get("numeric_target_tensor_materialized", False))
        denominator = contract["target_valid_mask"] & (contract["target_loss_weight"] > 0.0)
        sample_count = int(np.sum(denominator))
        status_pass = (
            bool(contract["status_pass"])
            and materialized
            and positive_target
            and sample_count > 0
            and not target_quality_validated
            and not labels_actor_visible
            and not provenance_actor_visible
        )
        if status_pass:
            observations.append(contract["observation_trace"][denominator])
            targets.append(contract["target_action_delta"][denominator])
            weights.append(contract["target_loss_weight"][denominator])
        dataset_rows.append(
            {
                "fitting_dataset_row_id": f"m3041-fitting-dataset-{index:04d}",
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "objective_family": row.get("objective_family", ""),
                "failure_family": row.get("failure_family", ""),
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(tensor_path),
                "observation_shape": _shape_text(contract["observation_trace"].shape),
                "target_action_delta_shape": _shape_text(contract["target_action_delta"].shape),
                "fit_sample_count": sample_count,
                "target_valid_mask_true_count": int(np.sum(contract["target_valid_mask"])),
                "target_loss_weight_sum": float(np.sum(contract["target_loss_weight"])),
                "fitting_denominator_used": status_pass,
                "target_quality_validated": target_quality_validated,
                "target_labels_actor_visible": labels_actor_visible,
                "target_provenance_actor_visible": provenance_actor_visible,
                "positive_residual_target": positive_target,
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
        len(dataset_rows) == EXPECTED_TARGET_ROWS
        and all(_bool(row["status_pass"]) for row in dataset_rows)
        and observation_array.shape[0] > 0
    )
    return FittingBatch(
        observations=observation_array,
        targets=target_array,
        weights=weight_array,
        rows=dataset_rows,
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


def predict_residual(model: FittedResidual, observations: np.ndarray) -> np.ndarray:
    if observations.shape[0] == 0:
        return np.zeros((0, ACTION_DIM), dtype=np.float32)
    raw = observations.astype(np.float32) @ model.weight + model.bias
    return np.clip(raw, -float(model.residual_limit), float(model.residual_limit)).astype(np.float32)


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
    prediction_after: np.ndarray,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    before = _weighted_metrics(prediction_before, batch.targets, batch.weights)
    after = _weighted_metrics(prediction_after, batch.targets, batch.weights)
    after_pass = (
        fitting_executed
        and np.isfinite(after["weighted_mse"])
        and after["weighted_mse"] <= before["weighted_mse"] + 1.0e-9
        and after["residual_abs_max"] <= RESIDUAL_LIMIT + 1.0e-6
    )
    return [
        {
            "loss_trace_id": "m3041-loss-0001-zero-residual-baseline",
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
            "loss_trace_id": "m3041-loss-0002-bounded-linear-residual",
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


def _load_observation_trace(path: Path) -> np.ndarray:
    if not path.exists():
        return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
    with np.load(path, allow_pickle=False) as data:
        if "observation_trace" not in data.files:
            return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
        observation = np.asarray(data["observation_trace"], dtype=np.float32)
    if observation.ndim != 2 or observation.shape[1] != P0_OBSERVATION_DIM or not np.all(np.isfinite(observation)):
        return np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
    return observation


def build_success_guard_loss_rows(
    success_guard_rows: list[dict[str, Any]],
    *,
    model: FittedResidual,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(success_guard_rows, start=1):
        raw_trace_path = Path(str(row.get("raw_trace_path", "")))
        target_tensor_path = Path(str(row.get("target_tensor_path", "")))
        observation = _load_observation_trace(raw_trace_path)
        prediction = predict_residual(model, observation) if fitting_executed else np.zeros((0, ACTION_DIM), dtype=np.float32)
        predicted_abs_max = float(np.max(np.abs(prediction))) if prediction.size else 0.0
        zero_guard = _bool(row.get("zero_target_guard", False)) and not _bool(row.get("positive_residual_target", False))
        target_actor_visible = _bool(row.get("target_labels_actor_visible", False)) or _bool(
            row.get("target_provenance_actor_visible", False)
        )
        rows.append(
            {
                "success_guard_loss_id": f"m3041-success-guard-{index:04d}",
                "success_identity_zero_target_guard_row_id": row.get("success_identity_zero_target_guard_row_id", ""),
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(target_tensor_path),
                "zero_target_guard": zero_guard,
                "fitting_denominator_used": False,
                "positive_residual_target": False,
                "target_action_delta_abs_max": float(row.get("target_action_delta_abs_max", 0.0)),
                "predicted_residual_abs_max": predicted_abs_max,
                "predicted_residual_mse": float(np.mean(prediction * prediction)) if prediction.size else 0.0,
                "status_pass": (
                    fitting_executed
                    and zero_guard
                    and not target_actor_visible
                    and observation.shape[0] > 0
                    and predicted_abs_max <= RESIDUAL_LIMIT + 1.0e-6
                ),
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
        "failure_family",
        "source_target_source_candidate_row_id",
        "target_source_plan_row_id",
        "route_decision",
        "audit_verdict",
        "validation_label",
        "driver_performance_label",
    ]
    return [
        {
            "actor_input_exclusion_id": f"m3041-actor-input-exclusion-{index:04d}",
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
        "parent_checkpoint_promote",
        "active_config_modify",
        "environment_reset",
        "environment_step",
        "policy_rollout",
        "validation_run",
        "ranking_run",
    ]
    return [
        {
            "side_effect_guard_id": f"m3041-side-effect-{index:04d}",
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
        ("bounded_offline_fitting_artifact_completeness", True, False, "M3041 summary/loss/gates/artifact"),
        ("closed_loop_repair_success", False, False, "future closed-loop measurement after M3042"),
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
            "claim_id": f"m3041-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3041": allowed,
            "claim_made": made,
            "status_pass": allowed or not made,
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
        observation_dim=np.asarray([P0_OBSERVATION_DIM], dtype=np.int64),
        action_dim=np.asarray([ACTION_DIM], dtype=np.int64),
        action_composition=np.asarray(["base_action_plus_residual_clipped"]),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    fitting_executed: bool,
    artifact_exists: bool,
    follow_up_manifest_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m3040_audit",
        "m3039_summary",
        "m3039_objective_rows",
        "m3039_scenario_rows",
        "m3039_guardrail_rows",
        "m3039_gate_matrix",
        "target_tensor_rows",
        "success_identity_zero_target_guard_rows",
    ]
    source_present = all(source["source_exists"].get(name, False) for name in required_sources)
    m3039_pass = _bool(source["m3039_summary"].get("status_pass", False)) and _bool(
        source["m3039_summary"].get("gate_matrix_pass", False)
    )
    final_loss_pass = bool(loss_rows and _bool(loss_rows[-1].get("status_pass", False)))
    gates = [
        ("source_artifacts_present", "source", source_present, source["source_exists"], "required sources", "lineage_invalid"),
        (
            "m3040_accepts_m3041_route",
            "lineage",
            "accept_m3039_guarded_training_admission_route_to_m3041_bounded_residual_fitting_preflight"
            in source["m3040_audit_text"],
            "m3041 route marker",
            "present",
            "lineage_invalid",
        ),
        ("m3039_status_and_gate_pass", "admission", m3039_pass, source["m3039_summary"], "status/gate pass", "metric_artifact"),
        (
            "target_tensor_rows_usable",
            "dataset",
            len(batch.rows) == EXPECTED_TARGET_ROWS and all(_bool(row["status_pass"]) for row in batch.rows),
            {"rows": len(batch.rows), "contracts_pass": batch.contracts_pass},
            f"{EXPECTED_TARGET_ROWS} passing rows",
            "metric_artifact",
        ),
        (
            "bounded_fitting_executed",
            "fitting",
            fitting_executed,
            {"sample_count": int(batch.observations.shape[0]), "fitting_executed": fitting_executed},
            "finite samples and fitted model",
            "metric_artifact",
        ),
        ("loss_improved_and_bounded", "fitting", final_loss_pass, loss_rows[-1] if loss_rows else {}, "final loss pass", "behavior_regression"),
        ("candidate_artifact_written", "artifact", artifact_exists, artifact_exists, True, "metric_artifact"),
        (
            "success_identity_guards_pass",
            "guard",
            len(success_rows) == EXPECTED_SUCCESS_GUARDS and all(_bool(row["status_pass"]) for row in success_rows),
            {"rows": len(success_rows), "passed": sum(_bool(row["status_pass"]) for row in success_rows)},
            f"{EXPECTED_SUCCESS_GUARDS} passing guards",
            "behavior_regression",
        ),
        (
            "actor_input_exclusions_pass",
            "actor_contract",
            all(_bool(row["status_pass"]) and not _bool(row["actor_visible"]) for row in actor_rows),
            {"rows": len(actor_rows), "passed": sum(_bool(row["status_pass"]) for row in actor_rows)},
            "all actor exclusions pass",
            "contract_violation",
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
            "gate_id": f"m3041-{name}",
            "gate_family": family,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, passed, observed, expected, failure_type in gates
    ]


def write_follow_up_manifest(path: Path, *, summary_path: Path, doc_path: Path, output_dir: Path) -> None:
    manifest = {
        "id": NEXT_ID,
        "priority": NEXT_PRIORITY,
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
        "hypothesis": "A bounded result audit can accept or reject the M3041 fitted Active Safety Driver v1 residual/reflex candidate before any rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.",
        "commands": [{"name": "active_safety_driver_v1_bounded_residual_fitting_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3042 audits M3041 fitting dataset loss guard side-effect claim and candidate artifact evidence and selects exactly one closed-loop measurement, repair, synthesis, or stop route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3042 audits M3041 summary loss dataset guard side-effect claim gate and candidate artifact rows",
            "M3042 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3042 selects exactly one next closed-loop measurement repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3042 treats offline fitting loss as closed-loop driver performance",
            "M3042 omits success identity or side-effect guard audits",
            "M3042 runs validation ranking promotion high-fidelity or architecture comparison",
            "M3042 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "fitting_dataset_rows.csv"),
            str(output_dir / "fitting_loss_trace_rows.csv"),
            str(output_dir / "success_guard_loss_rows.csv"),
            str(output_dir / "candidate_residual_reflex_layer.npz"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "fitting_dataset_rows.csv"),
                str(output_dir / "fitting_loss_trace_rows.csv"),
                str(output_dir / "success_guard_loss_rows.csv"),
                str(output_dir / "candidate_residual_reflex_layer.npz"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit fitted residual/reflex candidate before closed-loop measurement"],
            "derived_from": [MILESTONE_ID, M3040_ID],
            "blocked_by": [
                "M3041 fitting output requires audit before any closed-loop measurement",
                "offline fitting loss is not validation or driver-performance evidence",
            ],
            "supersedes": ["direct rollout or ranking before fitted candidate audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3042 must audit M3041 summary and gate_matrix pass status",
            "M3042 must audit candidate artifact shape 72-to-3 and residual bound",
            "M3042 must audit success identity and side-effect guards",
            "M3042 must reject driver-performance validation high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3042 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3041 offline fitting loss into driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_bounded_residual_fitting_result_audit",
            "evidence_increment": "audits the first fitted residual/reflex candidate before closed-loop measurement",
            "claim_scope": "Result audit only; no rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3041 artifact is incomplete or unbounded",
                "stop if success identity guards fail",
                "stop if offline fitting is treated as driver performance",
            ],
            "fallback_plan": [
                "route to closed-loop measurement if M3041 is accepted",
                "route to fitting repair if artifact or guards fail",
                "route to synthesis if closed-loop measurement is still not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3041 completes bounded residual fitting",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit fitted Active Safety Driver v1 residual/reflex candidate",
            "admission_evidence": [
                "M3041 summary and gate matrix",
                "M3041 fitting dataset and loss trace",
                "M3041 candidate residual artifact",
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
                "M3042 status queue scoreboard research log and review",
                "one follow-up manifest only if M3042 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3041 fitted candidate is accepted or rejected",
                "one next closed-loop measurement repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3042 audits engineering fitting artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3042; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3041 bounded residual fitting artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot block active-safety closed-loop measurement if safety contract gates pass.",
            "allowed_claims": [
                "M3041 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fitted candidate before a new closed-loop measurement route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3042 prepares closed-loop engineering measurement",
            "must_synthesize_if": [
                "M3042 cannot select a closed-loop measurement repair synthesis or stop route",
                "M3042 would require another materialization-only step before closed-loop evidence",
                "M3042 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }
    write_json(path, manifest)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    fitting_executed: bool,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = gate_matrix_pass
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "result_class": "active_safety_driver_v1_bounded_residual_fitting_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_bounded_residual_fitting_preflight_fail",
        "decision": "active_safety_driver_v1_bounded_residual_fit_route_to_m3042_result_audit"
        if status_pass
        else "active_safety_driver_v1_bounded_residual_fitting_incomplete",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "output_dir": str(output_dir),
        "paths": {key: str(path) for key, path in paths.items()},
        "m3039_status_pass": _bool(source["m3039_summary"].get("status_pass", False)),
        "m3039_gate_matrix_pass": _bool(source["m3039_summary"].get("gate_matrix_pass", False)),
        "target_tensor_row_count": len(source["target_tensor_rows"]),
        "success_identity_zero_guard_row_count": len(source["success_identity_zero_target_guard_rows"]),
        "fitting_dataset_row_count": len(batch.rows),
        "fitting_sample_count": int(batch.observations.shape[0]),
        "fitting_contracts_pass": batch.contracts_pass,
        "bounded_offline_fitting_run": fitting_executed,
        "fitting_run": fitting_executed,
        "ppo_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "candidate_residual_reflex_layer_exists": paths["candidate_residual_reflex_layer"].exists(),
        "candidate_residual_reflex_layer": str(paths["candidate_residual_reflex_layer"]),
        "initial_weighted_mse": loss_rows[0]["weighted_mse"] if loss_rows else "",
        "final_weighted_mse": loss_rows[-1]["weighted_mse"] if loss_rows else "",
        "final_predicted_residual_abs_max": loss_rows[-1]["predicted_residual_abs_max"] if loss_rows else "",
        "success_guard_loss_row_count": len(success_rows),
        "success_guard_loss_rows_pass": all(_bool(row.get("status_pass", False)) for row in success_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "actor_input_exclusion_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_rows),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in side_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": True,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "hidden_oracle_actor_input_detected": False,
        "ttc_actor_input_required": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "paper_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "next_blocker": NEXT_ID,
    }


def render_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M3041 Active Safety Driver v1 Bounded Residual Fitting Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- decision: `{summary['decision']}`",
            f"- fitting dataset rows: {summary['fitting_dataset_row_count']}",
            f"- fitting samples: {summary['fitting_sample_count']}",
            f"- bounded offline fitting run: {summary['bounded_offline_fitting_run']}",
            f"- candidate residual artifact: `{summary['candidate_residual_reflex_layer']}`",
            f"- initial weighted MSE: {summary['initial_weighted_mse']}",
            f"- final weighted MSE: {summary['final_weighted_mse']}",
            f"- final residual abs max: {summary['final_predicted_residual_abs_max']}",
            f"- success guard pass: {summary['success_guard_loss_rows_pass']}",
            f"- actor exclusion pass: {summary['actor_input_exclusion_rows_pass']}",
            f"- side-effect guard pass: {summary['checkpoint_side_effect_guard_rows_pass']}",
            f"- claim boundary pass: {summary['claim_boundary_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3041 fits one bounded offline 72-to-3 residual/reflex candidate from actor-visible observation traces and actor-invisible trainer-side target deltas. The candidate artifact is an engineering implementation artifact for later audit and closed-loop measurement. It is not a validation result, ranking, promotion, repair-success claim, driver-performance verdict, paper result, high-fidelity result, finite-window-vs-GRU conclusion, or self-ID claim.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Runtime Contract",
            "",
            "```text",
            "input: observation vector shape 72",
            "output: action residual shape 3",
            "composition: base [steer, throttle, brake] + bounded residual, clipped by downstream action bounds",
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
        ]
    )


def run_bounded_residual_fitting_preflight(
    *,
    m3040_audit: Path | str = DEFAULT_M3040_AUDIT,
    m3039_dir: Path | str = DEFAULT_M3039_DIR,
    m3032_dir: Path | str = DEFAULT_M3032_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    follow_up = Path(follow_up_manifest)
    paths = artifact_paths(output, doc_path=doc, follow_up_manifest=follow_up)
    source = load_source_artifacts(
        m3040_audit=Path(m3040_audit),
        m3039_dir=Path(m3039_dir),
        m3032_dir=Path(m3032_dir),
    )
    batch = build_fitting_batch(source["target_tensor_rows"])
    model = fit_linear_residual(batch) if batch.contracts_pass else zero_model()
    fitting_executed = bool(batch.contracts_pass and model.fitted)
    prediction_before = np.zeros_like(batch.targets, dtype=np.float32)
    prediction_after = predict_residual(model, batch.observations) if fitting_executed else prediction_before
    loss_rows = build_loss_trace_rows(
        batch,
        prediction_before,
        prediction_after,
        fitting_executed=fitting_executed,
    )
    if fitting_executed:
        write_candidate_artifact(paths["candidate_residual_reflex_layer"], model)
    success_rows = build_success_guard_loss_rows(
        source["success_identity_zero_target_guard_rows"],
        model=model,
        fitting_executed=fitting_executed,
    )
    actor_rows = build_actor_input_exclusion_rows()
    side_rows = build_checkpoint_side_effect_guard_rows()
    claim_rows = build_claim_boundary_rows()
    write_follow_up_manifest(
        follow_up,
        summary_path=paths["summary"],
        doc_path=doc,
        output_dir=output,
    )

    write_csv_rows(paths["fitting_dataset_rows"], batch.rows, fieldnames=FITTING_DATASET_FIELDNAMES)
    write_csv_rows(paths["fitting_loss_trace_rows"], loss_rows, fieldnames=LOSS_FIELDNAMES)
    write_csv_rows(paths["success_guard_loss_rows"], success_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], actor_rows, fieldnames=ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_residual_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up.exists(),
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "bounded_offline_fitting_run": fitting_executed,
            "training_run": False,
            "validation_run": False,
            "ranking_run": False,
            "checkpoint_mutated": False,
            "checkpoint_promoted": False,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    required_artifacts_present = all(
        paths[key].exists()
        for key in (
            "summary",
            "fitting_dataset_rows",
            "fitting_loss_trace_rows",
            "success_guard_loss_rows",
            "actor_input_exclusion_rows",
            "checkpoint_side_effect_guard_rows",
            "claim_boundary_rows",
            "gate_matrix",
            "candidate_residual_reflex_layer",
            "run_state",
            "doc",
            "follow_up_manifest",
        )
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_residual_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up.exists(),
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        follow_up_manifest=follow_up,
    )
    write_json(paths["summary"], summary)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render_doc(summary))
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_residual_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up.exists(),
        required_artifacts_present=all(
            paths[key].exists()
            for key in (
                "summary",
                "fitting_dataset_rows",
                "fitting_loss_trace_rows",
                "success_guard_loss_rows",
                "actor_input_exclusion_rows",
                "checkpoint_side_effect_guard_rows",
                "claim_boundary_rows",
                "gate_matrix",
                "candidate_residual_reflex_layer",
                "run_state",
                "doc",
                "follow_up_manifest",
            )
        ),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        follow_up_manifest=follow_up,
    )
    write_json(paths["summary"], summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3040-audit", type=Path, default=DEFAULT_M3040_AUDIT)
    parser.add_argument("--m3039-dir", type=Path, default=DEFAULT_M3039_DIR)
    parser.add_argument("--m3032-dir", type=Path, default=DEFAULT_M3032_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_bounded_residual_fitting_preflight(
        m3040_audit=args.m3040_audit,
        m3039_dir=args.m3039_dir,
        m3032_dir=args.m3032_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
