"""Run M3065 bounded direct-action fitting preflight.

M3065 consumes the M3064-admitted M3061 target tensors and M3055 direct-action
fitting contract. It fits or fails closed one offline obs72-to-action3
candidate artifact for later result audit. It does not run environment
validation, rank candidates, mutate checkpoints, promote checkpoints, or make
performance claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "bounded-direct-action-fitting-preflight"
)
NEXT_ID = (
    "m3066-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "bounded-direct-action-fitting-result-audit"
)
DEFAULT_M3064_DESIGN = Path(
    "docs/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "fitting-admission-design.md"
)
DEFAULT_M3063_SYNTHESIS = Path(
    "docs/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "target-tensor-to-fitting-branch-synthesis.md"
)
DEFAULT_M3062_AUDIT = Path(
    "docs/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "target-tensor-rerun-result-audit.md"
)
DEFAULT_M3061_DIR = Path(
    "runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "target_tensor_rerun_preflight"
)
DEFAULT_M3055_DIR = Path(
    "runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "fitting_contract_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "bounded_direct_action_fitting_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_ROWS = 24
EXPECTED_MASKED_STEPS = 768
EXPECTED_WEIGHT_SUM = 1344.0000114440918
RIDGE_LAMBDA = 1.0e-3
EPS = 1.0e-12
NEXT_PRIORITY = 30610

CLAIM_SCOPE = (
    "M3065 Active Safety Driver v1 offtrack-dominant behavior bounded direct-action fitting "
    "preflight only; M3064 design, M3063 synthesis, M3062 audit, M3061 trainer-side target "
    "tensors, and M3055 direct-action fitting contracts may be consumed to fit or fail closed "
    "one offline obs72-to-action3 [steer throttle brake] candidate artifact for later M3066 "
    "audit. Target labels, target provenance, source, route, outcome, progress, verdict, TTC, "
    "oracle, and paper labels remain actor-invisible. No environment reset, step, rollout, "
    "replay, validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair success, driver-performance verdict, current-sim verdict, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality, closed-loop repair success, validation readiness or result, driver "
    "performance, controller/checkpoint/candidate ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

FITTING_DATASET_FIELDNAMES = [
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "measurement_episode_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "raw_trace_termination_reason",
    "target_tensor_path",
    "observation_shape",
    "target_action_shape",
    "target_action_mask_shape",
    "target_loss_weight_shape",
    "masked_step_count",
    "target_loss_weight_sum",
    "target_action_abs_max",
    "split",
    "fitting_denominator_used",
    "target_rule_family",
    "raw_action_trace_used_as_target",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "target_quality_validated",
    "status_pass",
    "claim_boundary",
]
SPLIT_FIELDNAMES = [
    "split_row_id",
    "split",
    "row_count",
    "masked_step_count",
    "target_loss_weight_sum",
    "validation_claim_made",
    "ranking_claim_made",
    "status_pass",
    "claim_boundary",
]
MASK_WEIGHT_FIELDNAMES = [
    "mask_weight_row_id",
    "target_tensor_row_id",
    "split",
    "mask_shape",
    "weight_shape",
    "masked_step_count",
    "positive_action_weight_count",
    "target_loss_weight_sum",
    "target_action_abs_max",
    "status_pass",
    "claim_boundary",
]
LOSS_FIELDNAMES = [
    "loss_trace_id",
    "fit_stage",
    "split",
    "step",
    "sample_count",
    "weight_sum",
    "weighted_mse",
    "weighted_l1",
    "predicted_action_abs_max",
    "status_pass",
    "claim_boundary",
]
TARGET_QUALITY_FIELDNAMES = [
    "target_quality_boundary_id",
    "boundary_family",
    "artifact_complete",
    "target_quality_validated",
    "driver_performance_claim_made",
    "evidence_required_before_claim",
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
    "allowed_in_m3065",
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
class LoadedTensor:
    observation: np.ndarray
    target_action: np.ndarray
    mask: np.ndarray
    weight: np.ndarray
    raw_action_trace_used_as_target: bool
    status_pass: bool


@dataclass(frozen=True)
class FittingBatch:
    fit_observation: np.ndarray
    fit_target: np.ndarray
    fit_weight: np.ndarray
    all_observation: np.ndarray
    all_target: np.ndarray
    all_weight: np.ndarray
    dataset_rows: list[dict[str, Any]]
    mask_weight_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    contracts_pass: bool


@dataclass(frozen=True)
class DirectActionModel:
    weight: np.ndarray
    bias: np.ndarray
    fitted: bool


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(int(part)) for part in shape)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "fitting_dataset_rows": output_dir / "fitting_dataset_rows.csv",
        "split_rows": output_dir / "split_rows.csv",
        "mask_weight_rows": output_dir / "mask_weight_rows.csv",
        "fitting_loss_trace_rows": output_dir / "fitting_loss_trace_rows.csv",
        "target_quality_boundary_rows": output_dir / "target_quality_boundary_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_direct_action_reflex_layer": output_dir / "candidate_direct_action_reflex_layer.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3064_design: Path,
    m3063_synthesis: Path,
    m3062_audit: Path,
    m3061_dir: Path,
    m3055_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3064_design": m3064_design,
        "m3063_synthesis": m3063_synthesis,
        "m3062_audit": m3062_audit,
        "m3061_summary": m3061_dir / "summary.json",
        "behavior_target_tensor_rows": m3061_dir / "behavior_target_tensor_rows.csv",
        "target_tensor_file_index_rows": m3061_dir / "target_tensor_file_index_rows.csv",
        "target_tensor_weight_rows": m3061_dir / "target_tensor_weight_rows.csv",
        "m3055_summary": m3055_dir / "summary.json",
        "fitting_contract_rows": m3055_dir / "fitting_contract_rows.csv",
        "loss_family_rows": m3055_dir / "loss_family_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3064_design_text": paths["m3064_design"].read_text(encoding="utf-8")
        if exists["m3064_design"]
        else "",
        "m3063_synthesis_text": paths["m3063_synthesis"].read_text(encoding="utf-8")
        if exists["m3063_synthesis"]
        else "",
        "m3062_audit_text": paths["m3062_audit"].read_text(encoding="utf-8") if exists["m3062_audit"] else "",
        "m3061_summary": read_json(paths["m3061_summary"]) if exists["m3061_summary"] else {},
        "behavior_target_tensor_rows": read_csv_rows(paths["behavior_target_tensor_rows"])
        if exists["behavior_target_tensor_rows"]
        else [],
        "target_tensor_file_index_rows": read_csv_rows(paths["target_tensor_file_index_rows"])
        if exists["target_tensor_file_index_rows"]
        else [],
        "target_tensor_weight_rows": read_csv_rows(paths["target_tensor_weight_rows"])
        if exists["target_tensor_weight_rows"]
        else [],
        "m3055_summary": read_json(paths["m3055_summary"]) if exists["m3055_summary"] else {},
        "fitting_contract_rows": read_csv_rows(paths["fitting_contract_rows"])
        if exists["fitting_contract_rows"]
        else [],
        "loss_family_rows": read_csv_rows(paths["loss_family_rows"]) if exists["loss_family_rows"] else [],
    }


def _empty_tensor() -> LoadedTensor:
    return LoadedTensor(
        observation=np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        target_action=np.zeros((0, ACTION_DIM), dtype=np.float32),
        mask=np.zeros((0, ACTION_DIM), dtype=np.float32),
        weight=np.zeros((0, ACTION_DIM), dtype=np.float32),
        raw_action_trace_used_as_target=True,
        status_pass=False,
    )


def load_target_tensor(path: Path) -> LoadedTensor:
    if not path.exists():
        return _empty_tensor()
    with np.load(path, allow_pickle=False) as data:
        required = {
            "observation_trace",
            "target_action",
            "target_action_mask",
            "target_loss_weight",
            "raw_action_trace_used_as_target",
        }
        if not required.issubset(set(data.files)):
            return _empty_tensor()
        observation = np.asarray(data["observation_trace"], dtype=np.float32)
        target_action = np.asarray(data["target_action"], dtype=np.float32)
        mask = np.asarray(data["target_action_mask"], dtype=np.float32)
        weight = np.asarray(data["target_loss_weight"], dtype=np.float32)
        raw_used = bool(np.asarray(data["raw_action_trace_used_as_target"]).item())
    steps = observation.shape[0] if observation.ndim == 2 else -1
    status_pass = (
        observation.shape == (steps, P0_OBSERVATION_DIM)
        and target_action.shape == (steps, ACTION_DIM)
        and mask.shape == (steps, ACTION_DIM)
        and weight.shape == (steps, ACTION_DIM)
        and np.all(np.isfinite(observation))
        and np.all(np.isfinite(target_action))
        and np.all(np.isfinite(mask))
        and np.all(np.isfinite(weight))
        and float(np.max(np.abs(target_action))) <= 1.0 + 1.0e-6
        and not raw_used
    )
    return LoadedTensor(
        observation=observation if status_pass else np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
        target_action=target_action if status_pass else np.zeros((0, ACTION_DIM), dtype=np.float32),
        mask=mask if status_pass else np.zeros((0, ACTION_DIM), dtype=np.float32),
        weight=weight if status_pass else np.zeros((0, ACTION_DIM), dtype=np.float32),
        raw_action_trace_used_as_target=raw_used,
        status_pass=status_pass,
    )


def _split_for_row(index: int) -> str:
    return "internal_accounting" if index % 4 == 0 else "fit"


def build_fitting_batch(source: dict[str, Any]) -> FittingBatch:
    target_rows = source["behavior_target_tensor_rows"]
    fit_obs: list[np.ndarray] = []
    fit_targets: list[np.ndarray] = []
    fit_weights: list[np.ndarray] = []
    all_obs: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    all_weights: list[np.ndarray] = []
    dataset_rows: list[dict[str, Any]] = []
    mask_weight_rows: list[dict[str, Any]] = []
    split_acc: dict[str, dict[str, float]] = {
        "fit": {"row_count": 0.0, "masked_step_count": 0.0, "target_loss_weight_sum": 0.0},
        "internal_accounting": {"row_count": 0.0, "masked_step_count": 0.0, "target_loss_weight_sum": 0.0},
    }

    for index, row in enumerate(target_rows, start=1):
        split = _split_for_row(index)
        tensor_path = Path(str(row.get("target_tensor_path", "")))
        loaded = load_target_tensor(tensor_path)
        positive = (loaded.mask > 0.0) & (loaded.weight > 0.0)
        masked_steps = int(np.sum(np.any(positive, axis=1))) if loaded.status_pass else 0
        positive_weight_count = int(np.sum(positive)) if loaded.status_pass else 0
        weight_sum = float(np.sum(loaded.weight)) if loaded.status_pass else 0.0
        target_abs_max = float(np.max(np.abs(loaded.target_action))) if loaded.target_action.size else 0.0
        actor_visible = _bool(row.get("target_labels_actor_visible")) or _bool(row.get("target_provenance_actor_visible"))
        hidden_required = _bool(row.get("hidden_oracle_actor_input_required")) or _bool(row.get("ttc_actor_input_required"))
        materialized = _bool(row.get("numeric_target_tensor_materialized"))
        row_status = (
            loaded.status_pass
            and materialized
            and positive_weight_count > 0
            and not actor_visible
            and not hidden_required
            and not _bool(row.get("target_tensor_quality_claim_made"))
        )
        if row_status:
            all_obs.append(loaded.observation)
            all_targets.append(loaded.target_action)
            all_weights.append(loaded.weight * loaded.mask)
            split_acc[split]["row_count"] += 1
            split_acc[split]["masked_step_count"] += masked_steps
            split_acc[split]["target_loss_weight_sum"] += weight_sum
            if split == "fit":
                fit_obs.append(loaded.observation)
                fit_targets.append(loaded.target_action)
                fit_weights.append(loaded.weight * loaded.mask)
        dataset_rows.append(
            {
                "fitting_dataset_row_id": f"m3065-fitting-dataset-{index:04d}",
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "raw_trace_termination_reason": row.get("raw_trace_termination_reason", ""),
                "target_tensor_path": str(tensor_path),
                "observation_shape": _shape_text(loaded.observation.shape),
                "target_action_shape": _shape_text(loaded.target_action.shape),
                "target_action_mask_shape": _shape_text(loaded.mask.shape),
                "target_loss_weight_shape": _shape_text(loaded.weight.shape),
                "masked_step_count": masked_steps,
                "target_loss_weight_sum": weight_sum,
                "target_action_abs_max": target_abs_max,
                "split": split,
                "fitting_denominator_used": row_status and split == "fit",
                "target_rule_family": row.get("target_rule_family", ""),
                "raw_action_trace_used_as_target": loaded.raw_action_trace_used_as_target,
                "target_labels_actor_visible": _bool(row.get("target_labels_actor_visible")),
                "target_provenance_actor_visible": _bool(row.get("target_provenance_actor_visible")),
                "hidden_oracle_actor_input_required": _bool(row.get("hidden_oracle_actor_input_required")),
                "ttc_actor_input_required": _bool(row.get("ttc_actor_input_required")),
                "target_quality_validated": False,
                "status_pass": row_status,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        mask_weight_rows.append(
            {
                "mask_weight_row_id": f"m3065-mask-weight-{index:04d}",
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "split": split,
                "mask_shape": _shape_text(loaded.mask.shape),
                "weight_shape": _shape_text(loaded.weight.shape),
                "masked_step_count": masked_steps,
                "positive_action_weight_count": positive_weight_count,
                "target_loss_weight_sum": weight_sum,
                "target_action_abs_max": target_abs_max,
                "status_pass": row_status,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    def concat(items: list[np.ndarray], shape: tuple[int, int]) -> np.ndarray:
        return np.concatenate(items, axis=0).astype(np.float32) if items else np.zeros(shape, dtype=np.float32)

    split_rows = [
        {
            "split_row_id": f"m3065-split-{name}",
            "split": name,
            "row_count": int(values["row_count"]),
            "masked_step_count": int(values["masked_step_count"]),
            "target_loss_weight_sum": float(values["target_loss_weight_sum"]),
            "validation_claim_made": False,
            "ranking_claim_made": False,
            "status_pass": values["row_count"] > 0,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, values in split_acc.items()
    ]
    all_weight_sum = sum(float(row["target_loss_weight_sum"]) for row in dataset_rows if _bool(row["status_pass"]))
    all_masked_steps = sum(int(row["masked_step_count"]) for row in dataset_rows if _bool(row["status_pass"]))
    contracts_pass = (
        len(dataset_rows) == EXPECTED_TARGET_ROWS
        and all(_bool(row["status_pass"]) for row in dataset_rows)
        and all(_bool(row["status_pass"]) for row in split_rows)
        and all_masked_steps == EXPECTED_MASKED_STEPS
        and abs(all_weight_sum - EXPECTED_WEIGHT_SUM) < 1.0e-3
    )
    return FittingBatch(
        fit_observation=concat(fit_obs, (0, P0_OBSERVATION_DIM)),
        fit_target=concat(fit_targets, (0, ACTION_DIM)),
        fit_weight=concat(fit_weights, (0, ACTION_DIM)),
        all_observation=concat(all_obs, (0, P0_OBSERVATION_DIM)),
        all_target=concat(all_targets, (0, ACTION_DIM)),
        all_weight=concat(all_weights, (0, ACTION_DIM)),
        dataset_rows=dataset_rows,
        mask_weight_rows=mask_weight_rows,
        split_rows=split_rows,
        contracts_pass=contracts_pass,
    )


def zero_model() -> DirectActionModel:
    return DirectActionModel(
        weight=np.zeros((P0_OBSERVATION_DIM, ACTION_DIM), dtype=np.float32),
        bias=np.zeros((ACTION_DIM,), dtype=np.float32),
        fitted=False,
    )


def fit_direct_action(batch: FittingBatch) -> DirectActionModel:
    if batch.fit_observation.shape[0] == 0:
        return zero_model()
    x = batch.fit_observation.astype(np.float64)
    y = batch.fit_target.astype(np.float64)
    w = np.maximum(batch.fit_weight.astype(np.float64), 0.0)
    x_aug = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float64)], axis=1)
    coefficients = np.zeros((x_aug.shape[1], ACTION_DIM), dtype=np.float64)
    regularizer = np.eye(x_aug.shape[1], dtype=np.float64) * RIDGE_LAMBDA
    regularizer[-1, -1] = 0.0
    for action_index in range(ACTION_DIM):
        wd = w[:, action_index]
        if float(np.sum(wd)) <= EPS:
            continue
        sqrt_w = np.sqrt(wd + EPS)
        weighted_x = x_aug * sqrt_w[:, None]
        lhs = weighted_x.T @ weighted_x
        rhs = weighted_x.T @ (y[:, action_index] * sqrt_w)
        try:
            coef = np.linalg.solve(lhs + regularizer, rhs)
        except np.linalg.LinAlgError:
            coef = np.linalg.lstsq(lhs + regularizer, rhs, rcond=None)[0]
        coefficients[:, action_index] = coef
    return DirectActionModel(
        weight=coefficients[:-1].astype(np.float32),
        bias=coefficients[-1].astype(np.float32),
        fitted=True,
    )


def predict_action(model: DirectActionModel, observations: np.ndarray) -> np.ndarray:
    if observations.shape[0] == 0:
        return np.zeros((0, ACTION_DIM), dtype=np.float32)
    action = observations.astype(np.float32) @ model.weight + model.bias
    return np.clip(action, -1.0, 1.0).astype(np.float32)


def _weighted_metrics(prediction: np.ndarray, target: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    if prediction.shape[0] == 0 or target.shape[0] == 0:
        return {"weighted_mse": float("inf"), "weighted_l1": float("inf"), "action_abs_max": 0.0}
    error = prediction.astype(np.float64) - target.astype(np.float64)
    weights = weight.astype(np.float64)
    denom = max(float(np.sum(weights)), EPS)
    return {
        "weighted_mse": float(np.sum(weights * error * error) / denom),
        "weighted_l1": float(np.sum(weights * np.abs(error)) / denom),
        "action_abs_max": float(np.max(np.abs(prediction))) if prediction.size else 0.0,
    }


def build_loss_trace_rows(
    batch: FittingBatch,
    prediction_before: np.ndarray,
    prediction_after_fit: np.ndarray,
    prediction_after_all: np.ndarray,
    *,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    before_fit = _weighted_metrics(prediction_before, batch.fit_target, batch.fit_weight)
    after_fit = _weighted_metrics(prediction_after_fit, batch.fit_target, batch.fit_weight)
    after_all = _weighted_metrics(prediction_after_all, batch.all_target, batch.all_weight)
    fit_pass = (
        fitting_executed
        and np.isfinite(after_fit["weighted_mse"])
        and after_fit["weighted_mse"] <= before_fit["weighted_mse"] + 1.0e-9
        and after_fit["action_abs_max"] <= 1.0 + 1.0e-6
    )
    all_pass = fitting_executed and np.isfinite(after_all["weighted_mse"]) and after_all["action_abs_max"] <= 1.0 + 1.0e-6
    return [
        {
            "loss_trace_id": "m3065-loss-0001-zero-action-fit-baseline",
            "fit_stage": "zero_action_baseline",
            "split": "fit",
            "step": 0,
            "sample_count": int(batch.fit_observation.shape[0]),
            "weight_sum": float(np.sum(batch.fit_weight)),
            "weighted_mse": before_fit["weighted_mse"],
            "weighted_l1": before_fit["weighted_l1"],
            "predicted_action_abs_max": before_fit["action_abs_max"],
            "status_pass": batch.fit_observation.shape[0] > 0 and np.isfinite(before_fit["weighted_mse"]),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3065-loss-0002-bounded-direct-action-fit",
            "fit_stage": "bounded_linear_direct_action",
            "split": "fit",
            "step": 1,
            "sample_count": int(batch.fit_observation.shape[0]),
            "weight_sum": float(np.sum(batch.fit_weight)),
            "weighted_mse": after_fit["weighted_mse"],
            "weighted_l1": after_fit["weighted_l1"],
            "predicted_action_abs_max": after_fit["action_abs_max"],
            "status_pass": fit_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3065-loss-0003-bounded-direct-action-internal-accounting",
            "fit_stage": "bounded_linear_direct_action",
            "split": "all_public_accounting",
            "step": 1,
            "sample_count": int(batch.all_observation.shape[0]),
            "weight_sum": float(np.sum(batch.all_weight)),
            "weighted_mse": after_all["weighted_mse"],
            "weighted_l1": after_all["weighted_l1"],
            "predicted_action_abs_max": after_all["action_abs_max"],
            "status_pass": all_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_target_quality_boundary_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    summary = source["m3061_summary"]
    rows = [
        (
            "artifact_completeness",
            bool(summary.get("status_pass")) and bool(summary.get("gate_matrix_pass")),
            False,
            False,
            "M3062 audit and M3061 row/file/gate accounting",
        ),
        (
            "target_quality",
            True,
            False,
            False,
            "future target-quality audit plus closed-loop behavior evidence",
        ),
        (
            "driver_performance",
            True,
            False,
            False,
            "future closed-loop measurement and validation gates",
        ),
    ]
    return [
        {
            "target_quality_boundary_id": f"m3065-target-quality-boundary-{index:04d}",
            "boundary_family": family,
            "artifact_complete": artifact_complete,
            "target_quality_validated": target_quality,
            "driver_performance_claim_made": performance,
            "evidence_required_before_claim": evidence,
            "status_pass": artifact_complete and not target_quality and not performance,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, artifact_complete, target_quality, performance, evidence) in enumerate(rows, start=1)
    ]


def build_actor_input_exclusion_rows() -> list[dict[str, Any]]:
    forbidden = [
        "target_action",
        "target_action_mask",
        "target_loss_weight",
        "target_rule_family",
        "target_provenance",
        "source_offtrack_target_source_id",
        "source_raw_trace_path",
        "route_decision",
        "outcome_label",
        "progress_label",
        "verdict_label",
        "ttc",
        "oracle_state",
        "paper_label",
    ]
    return [
        {
            "actor_input_exclusion_id": f"m3065-actor-input-exclusion-{index:04d}",
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
        "candidate_artifact_promote",
        "active_config_modify",
        "environment_reset",
        "environment_step",
        "policy_rollout",
        "validation_run",
        "ranking_run",
    ]
    return [
        {
            "side_effect_guard_id": f"m3065-side-effect-{index:04d}",
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
        ("bounded_offline_direct_action_fitting_artifact_completeness", True, False, "M3065 summary/loss/gates/artifact"),
        ("target_quality", False, False, "future target-quality and behavior audit"),
        ("closed_loop_repair_success", False, False, "future closed-loop measurement after M3066"),
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
            "claim_id": f"m3065-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3065": allowed,
            "claim_made": made,
            "status_pass": allowed or not made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def write_candidate_artifact(path: Path, model: DirectActionModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        linear_weight=model.weight.astype(np.float32),
        linear_bias=model.bias.astype(np.float32),
        action_low=np.asarray([-1.0, -1.0, -1.0], dtype=np.float32),
        action_high=np.asarray([1.0, 1.0, 1.0], dtype=np.float32),
        observation_dim=np.asarray([P0_OBSERVATION_DIM], dtype=np.int64),
        action_dim=np.asarray([ACTION_DIM], dtype=np.int64),
        output_semantics=np.asarray(["direct_action_clipped"]),
        output_components=np.asarray(["steer", "throttle", "brake"]),
        base_policy_required_at_runtime=np.asarray([False]),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


def _source_preconditions_pass(source: dict[str, Any]) -> bool:
    required_sources = [
        "m3064_design",
        "m3063_synthesis",
        "m3062_audit",
        "m3061_summary",
        "behavior_target_tensor_rows",
        "target_tensor_file_index_rows",
        "target_tensor_weight_rows",
        "m3055_summary",
        "fitting_contract_rows",
        "loss_family_rows",
    ]
    direct_contract = any(
        row.get("output_semantics") == "direct_action"
        and row.get("actor_observation_shape") == str(P0_OBSERVATION_DIM)
        and row.get("actor_action_shape") == str(ACTION_DIM)
        and row.get("base_policy_required_at_runtime") in {"False", "false", False}
        for row in source["fitting_contract_rows"]
    )
    return (
        all(source["source_exists"].get(name, False) for name in required_sources)
        and "admit_m3065_bounded_direct_action_fitting_preflight_without_validation_or_promotion"
        in source["m3064_design_text"]
        and "continue_to_m3064_fitting_admission_design" in source["m3063_synthesis_text"]
        and "accept_m3061_target_tensor_rerun_claim_safe_route_to_m3063_branch_synthesis"
        in source["m3062_audit_text"]
        and bool(source["m3061_summary"].get("status_pass"))
        and bool(source["m3061_summary"].get("gate_matrix_pass"))
        and direct_contract
    )


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    fitting_executed: bool,
    artifact_exists: bool,
    follow_up_manifest_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_ready = _source_preconditions_pass(source)
    final_loss_pass = bool(loss_rows and _bool(loss_rows[1].get("status_pass", False)))
    gates = [
        ("source_artifacts_present", "source", source_ready, source["source_exists"], "required sources and route markers", "lineage_invalid"),
        (
            "direct_action_contract_present",
            "actor_contract",
            any(row.get("output_semantics") == "direct_action" for row in source["fitting_contract_rows"]),
            source["fitting_contract_rows"],
            "direct_action contract",
            "contract_violation",
        ),
        (
            "target_tensor_rows_usable",
            "dataset",
            len(batch.dataset_rows) == EXPECTED_TARGET_ROWS and all(_bool(row["status_pass"]) for row in batch.dataset_rows),
            {"rows": len(batch.dataset_rows), "contracts_pass": batch.contracts_pass},
            f"{EXPECTED_TARGET_ROWS} passing rows",
            "metric_artifact",
        ),
        (
            "split_rows_pass",
            "dataset",
            all(_bool(row["status_pass"]) for row in batch.split_rows),
            batch.split_rows,
            "fit and internal_accounting rows present",
            "metric_artifact",
        ),
        (
            "mask_weight_accounting_pass",
            "dataset",
            all(_bool(row["status_pass"]) for row in batch.mask_weight_rows),
            {"rows": len(batch.mask_weight_rows)},
            "all mask weight rows pass",
            "metric_artifact",
        ),
        (
            "bounded_fitting_executed",
            "fitting",
            fitting_executed,
            {"sample_count": int(batch.fit_observation.shape[0]), "fitting_executed": fitting_executed},
            "finite samples and fitted model",
            "metric_artifact",
        ),
        ("loss_improved_and_bounded", "fitting", final_loss_pass, loss_rows[1] if len(loss_rows) > 1 else {}, "final fit loss pass", "behavior_regression"),
        ("candidate_artifact_written", "artifact", artifact_exists, artifact_exists, True, "metric_artifact"),
        (
            "target_quality_boundaries_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in quality_rows),
            {"rows": len(quality_rows), "passed": sum(_bool(row["status_pass"]) for row in quality_rows)},
            "no target-quality or performance claim",
            "contract_violation",
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
            "gate_id": f"m3065-{name}",
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
        "hypothesis": "A bounded result audit can accept or reject the M3065 fitted direct-action Active Safety Driver v1 reflex candidate before any rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.",
        "commands": [{"name": "active_safety_driver_v1_direct_action_fitting_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3066 audits M3065 fitting dataset split mask weight loss target-quality side-effect claim and candidate artifact evidence and selects exactly one closed-loop measurement, repair, synthesis, or stop route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3066 audits M3065 summary loss dataset split mask weight target-quality side-effect claim gate and candidate artifact rows",
            "M3066 rejects target-quality validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3066 selects exactly one next closed-loop measurement repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3066 treats offline fitting loss as target quality or closed-loop driver performance",
            "M3066 omits actor-input side-effect target-quality or claim-boundary audits",
            "M3066 runs validation ranking promotion high-fidelity or architecture comparison",
            "M3066 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "fitting_dataset_rows.csv"),
            str(output_dir / "split_rows.csv"),
            str(output_dir / "mask_weight_rows.csv"),
            str(output_dir / "fitting_loss_trace_rows.csv"),
            str(output_dir / "target_quality_boundary_rows.csv"),
            str(output_dir / "candidate_direct_action_reflex_layer.npz"),
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
                str(output_dir / "split_rows.csv"),
                str(output_dir / "mask_weight_rows.csv"),
                str(output_dir / "fitting_loss_trace_rows.csv"),
                str(output_dir / "target_quality_boundary_rows.csv"),
                str(output_dir / "candidate_direct_action_reflex_layer.npz"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit fitted direct-action reflex candidate before closed-loop measurement"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": [
                "M3065 fitting output requires audit before any closed-loop measurement",
                "offline fitting loss is not target-quality validation or driver-performance evidence",
            ],
            "supersedes": ["direct rollout ranking or promotion before fitted candidate audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3066 must audit M3065 summary and gate_matrix pass status",
            "M3066 must audit candidate artifact shape 72-to-3 and direct-action bounds",
            "M3066 must audit target-quality actor-input side-effect and claim boundaries",
            "M3066 must reject driver-performance validation high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3066 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3065 offline fitting loss into target-quality driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles fitted artifacts or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_direct_action_fitting_result_audit",
            "evidence_increment": "audits the first fitted direct-action reflex candidate before closed-loop measurement",
            "claim_scope": "Result audit only; no rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3065 artifact is incomplete or unbounded",
                "stop if actor-input target-quality or side-effect guards fail",
                "stop if offline fitting is treated as target quality or driver performance",
            ],
            "fallback_plan": [
                "route to closed-loop measurement admission if M3065 is accepted",
                "route to fitting repair if artifact or guards fail",
                "route to synthesis if closed-loop measurement is still not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3065 completes bounded direct-action fitting",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit fitted Active Safety Driver v1 direct-action reflex candidate",
            "admission_evidence": [
                "M3065 summary and gate matrix",
                "M3065 fitting dataset split mask weight and loss trace",
                "M3065 candidate direct-action artifact",
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
                "M3066 status queue scoreboard research log and review",
                "one follow-up manifest only if M3066 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3065 fitted candidate is accepted or rejected",
                "one next closed-loop measurement repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3066 audits engineering fitting artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3066; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3065 bounded direct-action fitting artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety closed-loop measurement if safety contract gates pass.",
            "allowed_claims": [
                "M3065 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fitted direct-action candidate before a new closed-loop measurement route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3066 prepares closed-loop engineering measurement",
            "must_synthesize_if": [
                "M3066 cannot select a closed-loop measurement repair synthesis or stop route",
                "M3066 would require another materialization-only step before closed-loop evidence",
                "M3066 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }
    write_json(path, manifest)


def _required_outputs_present(
    paths: dict[str, Path],
    *,
    include_summary: bool = False,
    include_gate_matrix: bool = True,
) -> bool:
    required = [
        "fitting_dataset_rows",
        "split_rows",
        "mask_weight_rows",
        "fitting_loss_trace_rows",
        "target_quality_boundary_rows",
        "actor_input_exclusion_rows",
        "checkpoint_side_effect_guard_rows",
        "claim_boundary_rows",
        "candidate_direct_action_reflex_layer",
        "run_state",
        "doc",
        "follow_up_manifest",
    ]
    if include_gate_matrix:
        required.append("gate_matrix")
    if include_summary:
        required.append("summary")
    return all(paths[key].exists() for key in required)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    fitting_executed: bool,
    follow_up_manifest: Path,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = gate_matrix_pass and required_artifacts_present
    fit_split = next((row for row in batch.split_rows if row["split"] == "fit"), {})
    internal_split = next((row for row in batch.split_rows if row["split"] == "internal_accounting"), {})
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "result_class": "active_safety_driver_v1_offtrack_behavior_bounded_direct_action_fitting_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_bounded_direct_action_fitting_preflight_fail",
        "decision": "active_safety_driver_v1_offtrack_behavior_direct_action_fit_route_to_m3066_result_audit"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_direct_action_fitting_incomplete",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "output_dir": str(output_dir),
        "paths": {key: str(path) for key, path in paths.items()},
        "m3061_status_pass": bool(source["m3061_summary"].get("status_pass")),
        "m3061_gate_matrix_pass": bool(source["m3061_summary"].get("gate_matrix_pass")),
        "behavior_target_tensor_row_count": len(source["behavior_target_tensor_rows"]),
        "target_tensor_file_index_row_count": len(source["target_tensor_file_index_rows"]),
        "target_tensor_weight_row_count": len(source["target_tensor_weight_rows"]),
        "fitting_dataset_row_count": len(batch.dataset_rows),
        "fit_row_count": int(fit_split.get("row_count", 0) or 0),
        "internal_accounting_row_count": int(internal_split.get("row_count", 0) or 0),
        "fitting_sample_count": int(batch.fit_observation.shape[0]),
        "all_accounting_sample_count": int(batch.all_observation.shape[0]),
        "fit_weight_sum": float(np.sum(batch.fit_weight)),
        "all_weight_sum": float(np.sum(batch.all_weight)),
        "masked_step_count_total": sum(int(row["masked_step_count"]) for row in batch.dataset_rows if _bool(row["status_pass"])),
        "fitting_contracts_pass": batch.contracts_pass,
        "bounded_offline_direct_action_fitting_run": fitting_executed,
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
        "candidate_direct_action_reflex_layer_exists": paths["candidate_direct_action_reflex_layer"].exists(),
        "candidate_direct_action_reflex_layer": str(paths["candidate_direct_action_reflex_layer"]),
        "initial_fit_weighted_mse": loss_rows[0]["weighted_mse"] if loss_rows else "",
        "final_fit_weighted_mse": loss_rows[1]["weighted_mse"] if len(loss_rows) > 1 else "",
        "all_accounting_weighted_mse": loss_rows[2]["weighted_mse"] if len(loss_rows) > 2 else "",
        "final_predicted_action_abs_max": loss_rows[1]["predicted_action_abs_max"] if len(loss_rows) > 1 else "",
        "target_quality_boundary_row_count": len(quality_rows),
        "target_quality_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in quality_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "actor_input_exclusion_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_rows),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in side_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "output_semantics": "direct_action",
        "output_components": ["steer", "throttle", "brake"],
        "base_policy_required_at_runtime": False,
        "actor_contract_shape_72_action_3": True,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "hidden_oracle_actor_input_detected": False,
        "ttc_actor_input_required": False,
        "raw_action_trace_used_as_target": False,
        "target_tensor_quality_claim_made": False,
        "fitted_policy_quality_claim_made": False,
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
            "# M3065 Active Safety Driver v1 Offtrack-Dominant Behavior Bounded Direct-Action Fitting Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- decision: `{summary['decision']}`",
            f"- fitting dataset rows: {summary['fitting_dataset_row_count']}",
            f"- fit/internal rows: {summary['fit_row_count']} / {summary['internal_accounting_row_count']}",
            f"- fitting samples: {summary['fitting_sample_count']}",
            f"- bounded offline direct-action fitting run: {summary['bounded_offline_direct_action_fitting_run']}",
            f"- candidate direct-action artifact: `{summary['candidate_direct_action_reflex_layer']}`",
            f"- initial fit weighted MSE: {summary['initial_fit_weighted_mse']}",
            f"- final fit weighted MSE: {summary['final_fit_weighted_mse']}",
            f"- all-accounting weighted MSE: {summary['all_accounting_weighted_mse']}",
            f"- final action abs max: {summary['final_predicted_action_abs_max']}",
            f"- actor exclusion pass: {summary['actor_input_exclusion_rows_pass']}",
            f"- side-effect guard pass: {summary['checkpoint_side_effect_guard_rows_pass']}",
            f"- target-quality boundary pass: {summary['target_quality_boundary_rows_pass']}",
            f"- claim boundary pass: {summary['claim_boundary_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3065 fits one bounded offline direct-action obs72-to-action3 candidate from actor-visible observation traces and actor-invisible trainer-side target_action tensors. The candidate artifact is an engineering implementation artifact for later audit and closed-loop measurement admission. It is not target-quality validation, a validation result, ranking, promotion, repair-success claim, driver-performance verdict, paper result, high-fidelity result, finite-window-vs-GRU conclusion, or self-ID claim.",
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
            "output: direct action shape 3",
            "components: steer; throttle; brake",
            "action bounds: clip each output to [-1, 1]",
            "base policy required at runtime: false",
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
        ]
    )


def run_bounded_direct_action_fitting_preflight(
    *,
    m3064_design: Path | str = DEFAULT_M3064_DESIGN,
    m3063_synthesis: Path | str = DEFAULT_M3063_SYNTHESIS,
    m3062_audit: Path | str = DEFAULT_M3062_AUDIT,
    m3061_dir: Path | str = DEFAULT_M3061_DIR,
    m3055_dir: Path | str = DEFAULT_M3055_DIR,
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
        m3064_design=Path(m3064_design),
        m3063_synthesis=Path(m3063_synthesis),
        m3062_audit=Path(m3062_audit),
        m3061_dir=Path(m3061_dir),
        m3055_dir=Path(m3055_dir),
    )
    batch = build_fitting_batch(source)
    source_ready = _source_preconditions_pass(source)
    model = fit_direct_action(batch) if source_ready and batch.contracts_pass else zero_model()
    fitting_executed = bool(source_ready and batch.contracts_pass and model.fitted)
    prediction_before = np.zeros_like(batch.fit_target, dtype=np.float32)
    prediction_after_fit = predict_action(model, batch.fit_observation) if fitting_executed else prediction_before
    prediction_after_all = (
        predict_action(model, batch.all_observation)
        if fitting_executed
        else np.zeros_like(batch.all_target, dtype=np.float32)
    )
    loss_rows = build_loss_trace_rows(
        batch,
        prediction_before,
        prediction_after_fit,
        prediction_after_all,
        fitting_executed=fitting_executed,
    )
    if fitting_executed:
        write_candidate_artifact(paths["candidate_direct_action_reflex_layer"], model)

    quality_rows = build_target_quality_boundary_rows(source)
    actor_rows = build_actor_input_exclusion_rows()
    side_rows = build_checkpoint_side_effect_guard_rows()
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["fitting_dataset_rows"], batch.dataset_rows, fieldnames=FITTING_DATASET_FIELDNAMES)
    write_csv_rows(paths["split_rows"], batch.split_rows, fieldnames=SPLIT_FIELDNAMES)
    write_csv_rows(paths["mask_weight_rows"], batch.mask_weight_rows, fieldnames=MASK_WEIGHT_FIELDNAMES)
    write_csv_rows(paths["fitting_loss_trace_rows"], loss_rows, fieldnames=LOSS_FIELDNAMES)
    write_csv_rows(paths["target_quality_boundary_rows"], quality_rows, fieldnames=TARGET_QUALITY_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], actor_rows, fieldnames=ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_follow_up_manifest(follow_up, summary_path=paths["summary"], doc_path=doc, output_dir=output)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "fitting_executed": fitting_executed,
            "candidate_artifact": str(paths["candidate_direct_action_reflex_layer"]),
            "claim_scope": CLAIM_SCOPE,
        },
    )

    draft_summary = {
        "status_pass": fitting_executed,
        "decision": "draft_before_gate",
        "fitting_dataset_row_count": len(batch.dataset_rows),
        "fit_row_count": sum(1 for row in batch.dataset_rows if row["split"] == "fit"),
        "internal_accounting_row_count": sum(1 for row in batch.dataset_rows if row["split"] == "internal_accounting"),
        "fitting_sample_count": int(batch.fit_observation.shape[0]),
        "bounded_offline_direct_action_fitting_run": fitting_executed,
        "candidate_direct_action_reflex_layer": str(paths["candidate_direct_action_reflex_layer"]),
        "initial_fit_weighted_mse": loss_rows[0]["weighted_mse"] if loss_rows else "",
        "final_fit_weighted_mse": loss_rows[1]["weighted_mse"] if len(loss_rows) > 1 else "",
        "all_accounting_weighted_mse": loss_rows[2]["weighted_mse"] if len(loss_rows) > 2 else "",
        "final_predicted_action_abs_max": loss_rows[1]["predicted_action_abs_max"] if len(loss_rows) > 1 else "",
        "actor_input_exclusion_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in side_rows),
        "target_quality_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in quality_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_pass": fitting_executed,
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
    }
    doc.write_text(render_doc(draft_summary), encoding="utf-8")

    required_present_before_gate = _required_outputs_present(
        paths,
        include_summary=False,
        include_gate_matrix=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_direct_action_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up.exists(),
        required_artifacts_present=required_present_before_gate,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    required_present_before_summary = _required_outputs_present(
        paths,
        include_summary=False,
        include_gate_matrix=True,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_direct_action_reflex_layer"].exists(),
        follow_up_manifest_exists=follow_up.exists(),
        required_artifacts_present=required_present_before_summary,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        follow_up_manifest=follow_up,
        required_artifacts_present=required_present_before_summary,
    )
    doc.write_text(render_doc(summary), encoding="utf-8")
    write_json(paths["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M3065 bounded direct-action fitting preflight.")
    parser.add_argument("--m3064-design", type=Path, default=DEFAULT_M3064_DESIGN)
    parser.add_argument("--m3063-synthesis", type=Path, default=DEFAULT_M3063_SYNTHESIS)
    parser.add_argument("--m3062-audit", type=Path, default=DEFAULT_M3062_AUDIT)
    parser.add_argument("--m3061-dir", type=Path, default=DEFAULT_M3061_DIR)
    parser.add_argument("--m3055-dir", type=Path, default=DEFAULT_M3055_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_bounded_direct_action_fitting_preflight(
        m3064_design=args.m3064_design,
        m3063_synthesis=args.m3063_synthesis,
        m3062_audit=args.m3062_audit,
        m3061_dir=args.m3061_dir,
        m3055_dir=args.m3055_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
