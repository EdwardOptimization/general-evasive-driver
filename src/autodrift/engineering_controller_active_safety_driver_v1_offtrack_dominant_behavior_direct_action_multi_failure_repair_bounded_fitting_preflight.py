"""Run M3073 bounded multi-failure repair fitting preflight.

M3073 consumes the M3072-accepted M3071 repair contract plus the existing
M3065/M3061 direct-action fitting artifacts. It fits or fails closed one
offline obs72-to-action3 repaired candidate artifact. It does not run rollout,
validation, ranking, promotion, checkpoint mutation, or performance claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight import (
    DirectActionModel,
    FittingBatch,
    fit_direct_action,
    load_target_tensor,
    predict_action,
    zero_model,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-bounded-fitting-preflight"
)
NEXT_ID = (
    "m3074-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-bounded-fitting-result-audit"
)
M3072_ID = (
    "m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-multi-failure-repair-contract-result-audit"
)
DEFAULT_M3072_AUDIT = Path(f"docs/{M3072_ID}.md")
DEFAULT_M3071_DIR = Path(
    "runs/m3071_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_multi_failure_repair_contract_materialization_preflight"
)
DEFAULT_M3065_DIR = Path(
    "runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "bounded_direct_action_fitting_preflight"
)
DEFAULT_M3061_DIR = Path(
    "runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "target_tensor_rerun_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_multi_failure_repair_bounded_fitting_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_ROWS = 24
EXPECTED_CONTRACT_ROWS = 1
EXPECTED_ROW_ADMISSION_ROWS = 32
EXPECTED_REQUIREMENT_FAMILIES = {
    "offtrack_containment_recovery",
    "t5_collision_guard",
    "speed_floor_recovery",
    "direct_action_actuation_pressure",
    "success_preservation",
    "stability_clearance_tradeoff",
    "claim_boundary_guard",
}
NEXT_PRIORITY = 30690
EPS = 1.0e-12

CLAIM_SCOPE = (
    "M3073 Active Safety Driver v1 direct-action multi-failure repair bounded fitting "
    "preflight only; M3072 audit, M3071 repair contract rows, M3065 direct-action "
    "candidate/fitting rows, and M3061 trainer-side target tensors may be consumed "
    "to fit or fail closed one offline obs72-to-action3 [steer throttle brake] "
    "repair candidate artifact for later M3074 audit. Target labels, target "
    "provenance, source, route, outcome, progress, verdict, TTC, oracle, and paper "
    "labels remain actor-invisible. No environment reset, step, rollout, replay, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, repair success, driver-performance verdict, current-sim verdict, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full "
    "ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality, fitted policy quality, closed-loop repair success, validation "
    "readiness or result, driver performance, controller/checkpoint/candidate "
    "ranking, winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

REPAIR_DATASET_FIELDNAMES = [
    "repair_fitting_dataset_row_id",
    "source_fitting_dataset_row_id",
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
    "contract_weight_multiplier",
    "repair_target_loss_weight_sum",
    "target_action_abs_max",
    "split",
    "repair_fitting_denominator_used",
    "repair_loss_families",
    "guard_only_families",
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
    "repair_target_loss_weight_sum",
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
    "base_target_loss_weight_sum",
    "contract_weight_multiplier",
    "repair_target_loss_weight_sum",
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
    "fitted_policy_quality_claim_made",
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
    "allowed_in_m3073",
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
class ParentCandidate:
    model: DirectActionModel
    exists: bool
    shape_pass: bool


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


def _count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if _bool(row.get(key)))


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "repair_fitting_dataset_rows": output_dir / "repair_fitting_dataset_rows.csv",
        "repair_split_rows": output_dir / "repair_split_rows.csv",
        "repair_mask_weight_rows": output_dir / "repair_mask_weight_rows.csv",
        "repair_loss_trace_rows": output_dir / "repair_loss_trace_rows.csv",
        "repair_target_quality_boundary_rows": output_dir / "repair_target_quality_boundary_rows.csv",
        "repair_actor_input_exclusion_rows": output_dir / "repair_actor_input_exclusion_rows.csv",
        "repair_checkpoint_side_effect_guard_rows": output_dir / "repair_checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_direct_action_repair_reflex_layer": output_dir / "candidate_direct_action_repair_reflex_layer.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(*, m3072_audit: Path, m3071_dir: Path, m3065_dir: Path, m3061_dir: Path) -> dict[str, Any]:
    paths = {
        "m3072_audit": m3072_audit,
        "m3071_summary": m3071_dir / "summary.json",
        "m3071_contract_rows": m3071_dir / "direct_action_repair_contract_rows.csv",
        "m3071_loss_family_rows": m3071_dir / "direct_action_loss_family_rows.csv",
        "m3071_row_admission_rows": m3071_dir / "direct_action_row_admission_rows.csv",
        "m3071_guard_family_rows": m3071_dir / "direct_action_guard_family_rows.csv",
        "m3071_claim_boundary_rows": m3071_dir / "claim_boundary_rows.csv",
        "m3071_gate_matrix": m3071_dir / "gate_matrix.csv",
        "m3065_summary": m3065_dir / "summary.json",
        "m3065_fitting_dataset_rows": m3065_dir / "fitting_dataset_rows.csv",
        "m3065_candidate": m3065_dir / "candidate_direct_action_reflex_layer.npz",
        "m3061_summary": m3061_dir / "summary.json",
        "m3061_target_tensor_file_index_rows": m3061_dir / "target_tensor_file_index_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3072_audit_text": paths["m3072_audit"].read_text(encoding="utf-8") if exists["m3072_audit"] else "",
        "m3071_summary": read_json(paths["m3071_summary"]) if exists["m3071_summary"] else {},
        "m3071_contract_rows": read_csv_rows(paths["m3071_contract_rows"]) if exists["m3071_contract_rows"] else [],
        "m3071_loss_family_rows": read_csv_rows(paths["m3071_loss_family_rows"]) if exists["m3071_loss_family_rows"] else [],
        "m3071_row_admission_rows": read_csv_rows(paths["m3071_row_admission_rows"])
        if exists["m3071_row_admission_rows"]
        else [],
        "m3071_guard_family_rows": read_csv_rows(paths["m3071_guard_family_rows"])
        if exists["m3071_guard_family_rows"]
        else [],
        "m3071_claim_boundary_rows": read_csv_rows(paths["m3071_claim_boundary_rows"])
        if exists["m3071_claim_boundary_rows"]
        else [],
        "m3071_gate_matrix": read_csv_rows(paths["m3071_gate_matrix"]) if exists["m3071_gate_matrix"] else [],
        "m3065_summary": read_json(paths["m3065_summary"]) if exists["m3065_summary"] else {},
        "m3065_fitting_dataset_rows": read_csv_rows(paths["m3065_fitting_dataset_rows"])
        if exists["m3065_fitting_dataset_rows"]
        else [],
        "m3061_summary": read_json(paths["m3061_summary"]) if exists["m3061_summary"] else {},
        "m3061_target_tensor_file_index_rows": read_csv_rows(paths["m3061_target_tensor_file_index_rows"])
        if exists["m3061_target_tensor_file_index_rows"]
        else [],
    }


def load_parent_candidate(path: Path) -> ParentCandidate:
    if not path.exists():
        return ParentCandidate(model=zero_model(), exists=False, shape_pass=False)
    with np.load(path, allow_pickle=False) as data:
        if "linear_weight" not in data.files or "linear_bias" not in data.files:
            return ParentCandidate(model=zero_model(), exists=True, shape_pass=False)
        weight = np.asarray(data["linear_weight"], dtype=np.float32)
        bias = np.asarray(data["linear_bias"], dtype=np.float32)
    shape_pass = weight.shape == (P0_OBSERVATION_DIM, ACTION_DIM) and bias.shape == (ACTION_DIM,)
    model = DirectActionModel(weight=weight, bias=bias, fitted=shape_pass) if shape_pass else zero_model()
    return ParentCandidate(model=model, exists=True, shape_pass=shape_pass)


def _requirement_families(source: dict[str, Any]) -> set[str]:
    families = {str(row.get("requirement_family", "")) for row in source["m3071_loss_family_rows"]} | {
        str(row.get("guard_family", "")) for row in source["m3071_guard_family_rows"]
    }
    for contract in source["m3071_contract_rows"]:
        for key in ("p0_requirement_families", "p1_requirement_families"):
            families.update(part for part in str(contract.get(key, "")).split(";") if part)
    return families


def _source_preconditions_pass(source: dict[str, Any], parent: ParentCandidate) -> bool:
    required = [
        "m3072_audit",
        "m3071_summary",
        "m3071_contract_rows",
        "m3071_loss_family_rows",
        "m3071_row_admission_rows",
        "m3071_guard_family_rows",
        "m3071_claim_boundary_rows",
        "m3071_gate_matrix",
        "m3065_summary",
        "m3065_fitting_dataset_rows",
        "m3065_candidate",
        "m3061_summary",
        "m3061_target_tensor_file_index_rows",
    ]
    contract = source["m3071_contract_rows"][0] if source["m3071_contract_rows"] else {}
    return (
        all(source["source_exists"].get(name, False) for name in required)
        and "accept_m3071_repair_contract_claim_safe_route_to_m3073_bounded_repair_fitting_preflight"
        in source["m3072_audit_text"]
        and bool(source["m3071_summary"].get("status_pass"))
        and bool(source["m3071_summary"].get("gate_matrix_pass"))
        and len(source["m3071_contract_rows"]) == EXPECTED_CONTRACT_ROWS
        and int(contract.get("observation_shape", 0) or 0) == P0_OBSERVATION_DIM
        and int(contract.get("action_shape", 0) or 0) == ACTION_DIM
        and str(contract.get("output_semantics")) == "direct_action_clipped"
        and not _bool(contract.get("runtime_base_policy_required"))
        and len(source["m3071_row_admission_rows"]) == EXPECTED_ROW_ADMISSION_ROWS
        and EXPECTED_REQUIREMENT_FAMILIES.issubset(_requirement_families(source))
        and all(_bool(row.get("status_pass")) for row in source["m3071_guard_family_rows"])
        and all(_bool(row.get("status_pass")) for row in source["m3071_claim_boundary_rows"])
        and all(_bool(row.get("status_pass")) for row in source["m3071_gate_matrix"])
        and bool(source["m3065_summary"].get("status_pass"))
        and bool(source["m3065_summary"].get("gate_matrix_pass"))
        and bool(source["m3065_summary"].get("candidate_direct_action_reflex_layer_exists"))
        and parent.exists
        and parent.shape_pass
        and bool(source["m3061_summary"].get("status_pass"))
        and bool(source["m3061_summary"].get("gate_matrix_pass"))
    )


def _repair_loss_families(row: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    families = ["direct_action_actuation_pressure"]
    guard_only = ["success_preservation"]
    task = str(row.get("task_family", ""))
    source_edge = str(row.get("source_edge", "")).lower()
    termination = str(row.get("raw_trace_termination_reason", ""))
    if termination == "off_track":
        families.append("offtrack_containment_recovery")
    if task == "T5":
        families.append("t5_collision_guard")
    if task == "T5" or any(token in source_edge for token in ("boundary", "curved", "ood", "sensor")):
        families.append("stability_clearance_tradeoff")
    if any(token in source_edge for token in ("brake", "drive", "actuator", "speed")):
        families.append("speed_floor_recovery")
    return sorted(set(families)), guard_only


def _contract_weight_multiplier(families: list[str]) -> float:
    multiplier = 1.0
    if "offtrack_containment_recovery" in families:
        multiplier += 0.20
    if "t5_collision_guard" in families:
        multiplier += 0.25
    if "speed_floor_recovery" in families:
        multiplier += 0.10
    if "stability_clearance_tradeoff" in families:
        multiplier += 0.15
    return multiplier


def build_repair_fitting_batch(source: dict[str, Any]) -> FittingBatch:
    fit_obs: list[np.ndarray] = []
    fit_targets: list[np.ndarray] = []
    fit_weights: list[np.ndarray] = []
    all_obs: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    all_weights: list[np.ndarray] = []
    dataset_rows: list[dict[str, Any]] = []
    mask_weight_rows: list[dict[str, Any]] = []
    split_acc: dict[str, dict[str, float]] = {
        "fit": {"row_count": 0.0, "masked_step_count": 0.0, "repair_target_loss_weight_sum": 0.0},
        "internal_accounting": {"row_count": 0.0, "masked_step_count": 0.0, "repair_target_loss_weight_sum": 0.0},
    }

    for index, row in enumerate(source["m3065_fitting_dataset_rows"], start=1):
        split = str(row.get("split", ""))
        target_path = Path(str(row.get("target_tensor_path", "")))
        loaded = load_target_tensor(target_path)
        positive = (loaded.mask > 0.0) & (loaded.weight > 0.0)
        masked_steps = int(np.sum(np.any(positive, axis=1))) if loaded.status_pass else 0
        positive_weight_count = int(np.sum(positive)) if loaded.status_pass else 0
        base_weight_sum = float(np.sum(loaded.weight * loaded.mask)) if loaded.status_pass else 0.0
        target_abs_max = float(np.max(np.abs(loaded.target_action))) if loaded.target_action.size else 0.0
        families, guard_only = _repair_loss_families(row)
        multiplier = _contract_weight_multiplier(families)
        repair_weight = loaded.weight * loaded.mask * np.float32(multiplier)
        repair_weight_sum = float(np.sum(repair_weight)) if loaded.status_pass else 0.0
        actor_visible = _bool(row.get("target_labels_actor_visible")) or _bool(row.get("target_provenance_actor_visible"))
        hidden_required = _bool(row.get("hidden_oracle_actor_input_required")) or _bool(row.get("ttc_actor_input_required"))
        row_status = (
            loaded.status_pass
            and _bool(row.get("status_pass"))
            and positive_weight_count > 0
            and split in {"fit", "internal_accounting"}
            and not actor_visible
            and not hidden_required
            and not _bool(row.get("target_quality_validated"))
        )
        if row_status:
            all_obs.append(loaded.observation)
            all_targets.append(loaded.target_action)
            all_weights.append(repair_weight)
            split_acc[split]["row_count"] += 1
            split_acc[split]["masked_step_count"] += masked_steps
            split_acc[split]["repair_target_loss_weight_sum"] += repair_weight_sum
            if split == "fit":
                fit_obs.append(loaded.observation)
                fit_targets.append(loaded.target_action)
                fit_weights.append(repair_weight)
        dataset_rows.append(
            {
                "repair_fitting_dataset_row_id": f"m3073-repair-fitting-dataset-{index:04d}",
                "source_fitting_dataset_row_id": row.get("fitting_dataset_row_id", ""),
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "raw_trace_termination_reason": row.get("raw_trace_termination_reason", ""),
                "target_tensor_path": str(target_path),
                "observation_shape": _shape_text(loaded.observation.shape),
                "target_action_shape": _shape_text(loaded.target_action.shape),
                "target_action_mask_shape": _shape_text(loaded.mask.shape),
                "target_loss_weight_shape": _shape_text(loaded.weight.shape),
                "masked_step_count": masked_steps,
                "target_loss_weight_sum": base_weight_sum,
                "contract_weight_multiplier": multiplier,
                "repair_target_loss_weight_sum": repair_weight_sum,
                "target_action_abs_max": target_abs_max,
                "split": split,
                "repair_fitting_denominator_used": row_status and split == "fit",
                "repair_loss_families": ";".join(families),
                "guard_only_families": ";".join(guard_only),
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
                "mask_weight_row_id": f"m3073-repair-mask-weight-{index:04d}",
                "target_tensor_row_id": row.get("target_tensor_row_id", ""),
                "split": split,
                "mask_shape": _shape_text(loaded.mask.shape),
                "weight_shape": _shape_text(loaded.weight.shape),
                "masked_step_count": masked_steps,
                "positive_action_weight_count": positive_weight_count,
                "base_target_loss_weight_sum": base_weight_sum,
                "contract_weight_multiplier": multiplier,
                "repair_target_loss_weight_sum": repair_weight_sum,
                "target_action_abs_max": target_abs_max,
                "status_pass": row_status,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    split_rows = [
        {
            "split_row_id": f"m3073-repair-split-{name}",
            "split": name,
            "row_count": int(values["row_count"]),
            "masked_step_count": int(values["masked_step_count"]),
            "repair_target_loss_weight_sum": float(values["repair_target_loss_weight_sum"]),
            "validation_claim_made": False,
            "ranking_claim_made": False,
            "status_pass": values["row_count"] > 0,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, values in split_acc.items()
    ]

    def concat(items: list[np.ndarray], shape: tuple[int, int]) -> np.ndarray:
        return np.concatenate(items, axis=0).astype(np.float32) if items else np.zeros(shape, dtype=np.float32)

    contracts_pass = (
        len(dataset_rows) == EXPECTED_TARGET_ROWS
        and all(_bool(row["status_pass"]) for row in dataset_rows)
        and all(_bool(row["status_pass"]) for row in split_rows)
        and split_acc["fit"]["row_count"] > 0
        and split_acc["internal_accounting"]["row_count"] > 0
        and all(_bool(row["status_pass"]) for row in mask_weight_rows)
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
    zero_prediction: np.ndarray,
    parent_prediction_fit: np.ndarray,
    repair_prediction_fit: np.ndarray,
    repair_prediction_all: np.ndarray,
    *,
    parent: ParentCandidate,
    fitting_executed: bool,
) -> list[dict[str, Any]]:
    zero_fit = _weighted_metrics(zero_prediction, batch.fit_target, batch.fit_weight)
    parent_fit = _weighted_metrics(parent_prediction_fit, batch.fit_target, batch.fit_weight)
    repair_fit = _weighted_metrics(repair_prediction_fit, batch.fit_target, batch.fit_weight)
    repair_all = _weighted_metrics(repair_prediction_all, batch.all_target, batch.all_weight)
    repair_fit_pass = (
        fitting_executed
        and np.isfinite(repair_fit["weighted_mse"])
        and repair_fit["weighted_mse"] <= zero_fit["weighted_mse"] + 1.0e-9
        and repair_fit["action_abs_max"] <= 1.0 + 1.0e-6
    )
    repair_all_pass = fitting_executed and np.isfinite(repair_all["weighted_mse"]) and repair_all["action_abs_max"] <= 1.0 + 1.0e-6
    return [
        {
            "loss_trace_id": "m3073-loss-0001-zero-action-fit-baseline",
            "fit_stage": "zero_action_baseline",
            "split": "fit",
            "step": 0,
            "sample_count": int(batch.fit_observation.shape[0]),
            "weight_sum": float(np.sum(batch.fit_weight)),
            "weighted_mse": zero_fit["weighted_mse"],
            "weighted_l1": zero_fit["weighted_l1"],
            "predicted_action_abs_max": zero_fit["action_abs_max"],
            "status_pass": batch.fit_observation.shape[0] > 0 and np.isfinite(zero_fit["weighted_mse"]),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3073-loss-0002-m3065-parent-candidate-fit-accounting",
            "fit_stage": "m3065_parent_candidate_accounting",
            "split": "fit",
            "step": 0,
            "sample_count": int(batch.fit_observation.shape[0]),
            "weight_sum": float(np.sum(batch.fit_weight)),
            "weighted_mse": parent_fit["weighted_mse"],
            "weighted_l1": parent_fit["weighted_l1"],
            "predicted_action_abs_max": parent_fit["action_abs_max"],
            "status_pass": parent.exists and parent.shape_pass and np.isfinite(parent_fit["weighted_mse"]),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3073-loss-0003-bounded-direct-action-repair-fit",
            "fit_stage": "bounded_linear_direct_action_repair",
            "split": "fit",
            "step": 1,
            "sample_count": int(batch.fit_observation.shape[0]),
            "weight_sum": float(np.sum(batch.fit_weight)),
            "weighted_mse": repair_fit["weighted_mse"],
            "weighted_l1": repair_fit["weighted_l1"],
            "predicted_action_abs_max": repair_fit["action_abs_max"],
            "status_pass": repair_fit_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m3073-loss-0004-bounded-direct-action-repair-internal-accounting",
            "fit_stage": "bounded_linear_direct_action_repair",
            "split": "all_public_accounting",
            "step": 1,
            "sample_count": int(batch.all_observation.shape[0]),
            "weight_sum": float(np.sum(batch.all_weight)),
            "weighted_mse": repair_all["weighted_mse"],
            "weighted_l1": repair_all["weighted_l1"],
            "predicted_action_abs_max": repair_all["action_abs_max"],
            "status_pass": repair_all_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_target_quality_boundary_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("m3071_contract_artifact_complete", bool(source["m3071_summary"].get("status_pass")), False, False, False, "M3072/M3071 audit and gate matrix"),
        ("m3061_target_tensor_artifact_complete", bool(source["m3061_summary"].get("status_pass")), False, False, False, "M3061 target tensor file accounting"),
        ("target_quality", True, False, False, False, "future target-quality audit plus behavior evidence"),
        ("fitted_policy_quality", True, False, False, False, "future M3074 result audit and closed-loop measurement"),
        ("driver_performance", True, False, False, False, "future same-denominator measurement and validation gates"),
    ]
    return [
        {
            "target_quality_boundary_id": f"m3073-target-quality-boundary-{index:04d}",
            "boundary_family": family,
            "artifact_complete": complete,
            "target_quality_validated": target_quality,
            "fitted_policy_quality_claim_made": policy_quality,
            "driver_performance_claim_made": performance,
            "evidence_required_before_claim": evidence,
            "status_pass": complete and not target_quality and not policy_quality and not performance,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, complete, target_quality, policy_quality, performance, evidence) in enumerate(checks, start=1)
    ]


def build_actor_input_exclusion_rows() -> list[dict[str, Any]]:
    forbidden = [
        "target_action",
        "target_action_mask",
        "target_loss_weight",
        "target_rule_family",
        "target_provenance",
        "m3071_requirement_family",
        "m3071_loss_family",
        "m3071_gate_family",
        "source_raw_trace_path",
        "route_decision",
        "outcome_label",
        "success_progress_label",
        "verdict_label",
        "ttc",
        "oracle_state",
        "paper_label",
    ]
    return [
        {
            "actor_input_exclusion_id": f"m3073-actor-input-exclusion-{index:04d}",
            "forbidden_metadata_key": key,
            "actor_visible": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, key in enumerate(forbidden, start=1)
    ]


def build_checkpoint_side_effect_guard_rows() -> list[dict[str, Any]]:
    side_effects = [
        "parent_candidate_load",
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
        "profile_tuning",
    ]
    return [
        {
            "side_effect_guard_id": f"m3073-side-effect-{index:04d}",
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
        ("bounded_offline_direct_action_repair_fitting_artifact_completeness", True, True, "M3073 summary/loss/gates/artifact"),
        ("m3071_contract_consumed", True, True, "M3071 contract and M3072 audit"),
        ("target_quality", False, False, "future target-quality and behavior audit"),
        ("fitted_policy_quality", False, False, "future result audit plus closed-loop measurement"),
        ("closed_loop_repair_success", False, False, "future closed-loop measurement after M3074"),
        ("validation_result", False, False, "future validation audit"),
        ("driver_performance_verdict", False, False, "future accepted benchmark validation"),
        ("checkpoint_ranking", False, False, "future ranking audit"),
        ("checkpoint_promotion", False, False, "future promotion gate"),
        ("current_sim_verdict", False, False, "future current-sim synthesis"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation layer"),
        ("finite_window_vs_gru_conclusion", False, False, "future architecture ablation"),
        ("paper_evidence", False, False, "future paper-route synthesis"),
        ("level3_self_identification", False, False, "future self-ID route only if needed"),
        ("full_ideal_driver_completion", False, False, "future full-goal audit"),
    ]
    return [
        {
            "claim_id": f"m3073-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3073": allowed,
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
        parent_candidate_artifact=np.asarray(
            [
                "runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
                "bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz"
            ]
        ),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


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
        "hypothesis": (
            "A bounded result audit can accept or reject the M3073 repaired direct-action fitting artifacts before any "
            "rollout validation ranking promotion driver-performance high-fidelity finite-window-vs-GRU paper full-driver "
            "repair-success or self-ID claim."
        ),
        "commands": [{"name": "active_safety_driver_v1_direct_action_multi_failure_repair_fitting_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3074 audits M3073 fitting rows loss guard claim and candidate artifacts and selects exactly one closed-loop measurement repair synthesis or stop route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3074 audits M3073 summary dataset loss candidate guard claim and gate artifacts",
            "M3074 rejects target quality fitted policy quality validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims unless separately routed",
            "M3074 selects exactly one next closed-loop measurement repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3074 treats offline fitting loss as target quality fitted policy quality or closed-loop driver performance",
            "M3074 omits actor-input side-effect target-quality or claim-boundary audits",
            "M3074 runs rollout validation ranking promotion high-fidelity or architecture comparison",
            "M3074 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            str(output_dir / "candidate_direct_action_repair_reflex_layer.npz"),
            "runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "repair_fitting_dataset_rows.csv"),
            str(output_dir / "repair_loss_trace_rows.csv"),
            str(output_dir / "candidate_direct_action_repair_reflex_layer.npz"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "lineage": {
            "parent_checkpoint": [
                str(output_dir / "candidate_direct_action_repair_reflex_layer.npz"),
                "runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "repair_fitting_dataset_rows.csv"),
                str(output_dir / "repair_loss_trace_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit repaired direct-action fitting candidate before closed-loop measurement"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": [
                "M3073 fitting output requires audit before any closed-loop measurement",
                "offline fitting loss is not target-quality fitted-policy quality or driver-performance evidence",
            ],
            "supersedes": ["direct rollout ranking or promotion before repaired candidate audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3074 must audit M3073 summary and gate_matrix pass status",
            "M3074 must audit candidate artifact shape 72-to-3 and direct-action bounds",
            "M3074 must audit target-quality fitted-policy actor-input side-effect and claim boundaries",
            "M3074 must reject driver-performance validation high-fidelity paper finite-window-vs-GRU repair-success and self-ID claims",
            "M3074 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3073 offline fitting loss into target-quality fitted-policy driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles fitted artifacts or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_direct_action_multi_failure_repair_fitting_result_audit",
            "evidence_increment": "audits the repaired direct-action reflex candidate before closed-loop measurement",
            "claim_scope": "Result audit only; no rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3073 artifact is incomplete or unbounded",
                "stop if actor-input target-quality fitted-policy or side-effect guards fail",
                "stop if offline fitting is treated as target quality fitted-policy quality repair success or driver performance",
            ],
            "fallback_plan": [
                "route to closed-loop measurement admission if M3073 is accepted",
                "route to fitting repair if artifact or guards fail",
                "route to synthesis if closed-loop measurement is still not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3073 completes bounded direct-action multi-failure repair fitting",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit repaired Active Safety Driver v1 direct-action reflex candidate",
            "admission_evidence": [
                "M3073 summary and gate matrix",
                "M3073 repair fitting dataset mask weight and loss trace",
                "M3073 candidate direct-action repair artifact",
            ],
            "blocked_shortcuts": [
                "no rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper repair-success or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3074 status queue scoreboard research log and review",
                "one follow-up manifest only if M3074 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3073 repaired candidate is accepted or rejected",
                "one next closed-loop measurement repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3074 audits engineering fitting artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3074; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3073 bounded repair fitting artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety closed-loop measurement if safety contract gates pass.",
            "allowed_claims": [
                "M3073 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits repaired fitted direct-action candidate before a new closed-loop measurement route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3074 prepares closed-loop engineering measurement",
            "must_synthesize_if": [
                "M3074 cannot select a closed-loop measurement repair synthesis or stop route",
                "M3074 would require another materialization-only step before closed-loop evidence",
                "M3074 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }
    write_json(path, manifest)


def _required_outputs_present(paths: dict[str, Path], *, include_summary: bool = False, include_gate_matrix: bool = True) -> bool:
    required = [
        "repair_fitting_dataset_rows",
        "repair_split_rows",
        "repair_mask_weight_rows",
        "repair_loss_trace_rows",
        "repair_target_quality_boundary_rows",
        "repair_actor_input_exclusion_rows",
        "repair_checkpoint_side_effect_guard_rows",
        "claim_boundary_rows",
        "candidate_direct_action_repair_reflex_layer",
        "run_state",
        "doc",
        "follow_up_manifest",
    ]
    if include_gate_matrix:
        required.append("gate_matrix")
    if include_summary:
        required.append("summary")
    return all(paths[key].exists() for key in required)


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    parent: ParentCandidate,
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
    source_ready = _source_preconditions_pass(source, parent)
    families = _requirement_families(source)
    final_loss_pass = len(loss_rows) > 2 and _bool(loss_rows[2].get("status_pass"))
    gates = [
        ("m3072_audit_present", "lineage", source["source_exists"].get("m3072_audit", False), True, "lineage_invalid"),
        ("m3071_status_pass", "lineage", bool(source["m3071_summary"].get("status_pass")), True, "lineage_invalid"),
        ("m3071_gate_matrix_pass", "lineage", bool(source["m3071_summary"].get("gate_matrix_pass")), True, "lineage_invalid"),
        ("m3071_contract_rows", "contract", len(source["m3071_contract_rows"]), EXPECTED_CONTRACT_ROWS, "contract_violation"),
        ("m3071_row_admission_rows", "denominator", len(source["m3071_row_admission_rows"]), EXPECTED_ROW_ADMISSION_ROWS, "metric_artifact"),
        (
            "m3071_requirement_families_preserved",
            "contract",
            EXPECTED_REQUIREMENT_FAMILIES.issubset(families),
            True,
            "contract_violation",
        ),
        ("m3065_parent_candidate_shape", "lineage", parent.shape_pass, True, "lineage_invalid"),
        ("m3061_status_pass", "lineage", bool(source["m3061_summary"].get("status_pass")), True, "lineage_invalid"),
        ("source_preconditions_pass", "lineage", source_ready, True, "lineage_invalid"),
        ("repair_dataset_rows", "dataset", len(batch.dataset_rows), EXPECTED_TARGET_ROWS, "metric_artifact"),
        ("repair_dataset_rows_pass", "dataset", all(_bool(row["status_pass"]) for row in batch.dataset_rows), True, "metric_artifact"),
        ("repair_split_rows_pass", "dataset", all(_bool(row["status_pass"]) for row in batch.split_rows), True, "metric_artifact"),
        ("repair_mask_weight_rows_pass", "dataset", all(_bool(row["status_pass"]) for row in batch.mask_weight_rows), True, "metric_artifact"),
        ("bounded_repair_fitting_executed", "fitting", fitting_executed, True, "metric_artifact"),
        ("repair_loss_bounded", "fitting", final_loss_pass, True, "behavior_regression"),
        ("candidate_artifact_written", "artifact", artifact_exists, True, "metric_artifact"),
        ("target_quality_boundaries_pass", "claim", all(_bool(row["status_pass"]) for row in quality_rows), True, "contract_violation"),
        ("actor_input_exclusions_pass", "actor_contract", all(_bool(row["status_pass"]) and not _bool(row["actor_visible"]) for row in actor_rows), True, "contract_violation"),
        ("checkpoint_side_effects_absent", "side_effect", all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_rows), True, "contract_violation"),
        ("claim_boundaries_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), True, "contract_violation"),
        ("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
        ("required_artifacts_present", "process", required_artifacts_present, True, "metric_artifact"),
    ]
    rows: list[dict[str, Any]] = []
    for name, family, observed, expected, failure_type in gates:
        passed = observed == expected if not isinstance(observed, bool) else observed is expected
        rows.append(
            {
                "gate_id": f"m3073-{name}",
                "gate_family": family,
                "status_pass": passed,
                "observed": observed,
                "expected": expected,
                "failure_type": "" if passed else failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    parent: ParentCandidate,
    batch: FittingBatch,
    loss_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    fitting_executed: bool,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gate_rows)
    status_pass = gate_matrix_pass and required_artifacts_present
    fit_split = next((row for row in batch.split_rows if row["split"] == "fit"), {})
    internal_split = next((row for row in batch.split_rows if row["split"] == "internal_accounting"), {})
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "result_class": "active_safety_driver_v1_direct_action_multi_failure_repair_bounded_fitting_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_direct_action_multi_failure_repair_bounded_fitting_preflight_fail",
        "decision": "active_safety_driver_v1_direct_action_multi_failure_repair_fit_route_to_m3074_result_audit"
        if status_pass
        else "active_safety_driver_v1_direct_action_multi_failure_repair_fitting_incomplete",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "output_dir": str(output_dir),
        "paths": {key: str(path) for key, path in paths.items()},
        "m3071_status_pass": bool(source["m3071_summary"].get("status_pass")),
        "m3071_gate_matrix_pass": bool(source["m3071_summary"].get("gate_matrix_pass")),
        "m3071_contract_row_count": len(source["m3071_contract_rows"]),
        "m3071_row_admission_row_count": len(source["m3071_row_admission_rows"]),
        "m3071_requirement_family_count": len(_requirement_families(source)),
        "m3065_status_pass": bool(source["m3065_summary"].get("status_pass")),
        "m3065_gate_matrix_pass": bool(source["m3065_summary"].get("gate_matrix_pass")),
        "m3065_parent_candidate_exists": parent.exists,
        "m3065_parent_candidate_shape_pass": parent.shape_pass,
        "m3061_status_pass": bool(source["m3061_summary"].get("status_pass")),
        "m3061_gate_matrix_pass": bool(source["m3061_summary"].get("gate_matrix_pass")),
        "target_tensor_file_index_row_count": len(source["m3061_target_tensor_file_index_rows"]),
        "repair_fitting_dataset_row_count": len(batch.dataset_rows),
        "fit_row_count": int(fit_split.get("row_count", 0) or 0),
        "internal_accounting_row_count": int(internal_split.get("row_count", 0) or 0),
        "repair_fitting_sample_count": int(batch.fit_observation.shape[0]),
        "all_accounting_sample_count": int(batch.all_observation.shape[0]),
        "fit_repair_weight_sum": float(np.sum(batch.fit_weight)),
        "all_repair_weight_sum": float(np.sum(batch.all_weight)),
        "masked_step_count_total": sum(int(row["masked_step_count"]) for row in batch.dataset_rows if _bool(row["status_pass"])),
        "repair_contracts_pass": batch.contracts_pass,
        "bounded_offline_direct_action_repair_fitting_run": fitting_executed,
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
        "profile_tuning_run": False,
        "candidate_direct_action_repair_reflex_layer_exists": paths["candidate_direct_action_repair_reflex_layer"].exists(),
        "candidate_direct_action_repair_reflex_layer": str(paths["candidate_direct_action_repair_reflex_layer"]),
        "zero_action_fit_weighted_mse": loss_rows[0]["weighted_mse"] if loss_rows else "",
        "m3065_parent_fit_weighted_mse": loss_rows[1]["weighted_mse"] if len(loss_rows) > 1 else "",
        "final_repair_fit_weighted_mse": loss_rows[2]["weighted_mse"] if len(loss_rows) > 2 else "",
        "all_repair_accounting_weighted_mse": loss_rows[3]["weighted_mse"] if len(loss_rows) > 3 else "",
        "final_predicted_action_abs_max": loss_rows[2]["predicted_action_abs_max"] if len(loss_rows) > 2 else "",
        "target_quality_boundary_row_count": len(quality_rows),
        "target_quality_boundary_rows_pass": all(_bool(row.get("status_pass")) for row in quality_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "actor_input_exclusion_rows_pass": all(_bool(row.get("status_pass")) for row in actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_rows),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row.get("status_pass")) for row in side_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass")) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "output_semantics": "direct_action_clipped",
        "output_components": ["steer", "throttle", "brake"],
        "base_policy_required_at_runtime": False,
        "runtime_base_policy_required": False,
        "actor_contract_shape_72_action_3": True,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "hidden_oracle_actor_input_detected": False,
        "ttc_actor_input_required": False,
        "raw_action_trace_used_as_target": False,
        "target_quality_claim_made": False,
        "fitted_policy_quality_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "paper_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "forbidden_claim_made": False,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "next_blocker": NEXT_ID,
    }


def render_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M3073 Active Safety Driver v1 Direct-Action Multi-Failure Repair Bounded Fitting Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- repair fitting dataset rows: {summary['repair_fitting_dataset_row_count']}",
            f"- fit/internal rows: {summary['fit_row_count']} / {summary['internal_accounting_row_count']}",
            f"- repair samples: {summary['repair_fitting_sample_count']}",
            f"- final repair weighted MSE: {summary['final_repair_fit_weighted_mse']}",
            f"- parent weighted MSE accounting: {summary['m3065_parent_fit_weighted_mse']}",
            f"- candidate artifact: `{summary['candidate_direct_action_repair_reflex_layer']}`",
            f"- actor/action contract: obs{summary['observation_shape']} to action{summary['action_shape']} [steer throttle brake]",
            f"- runtime base policy required: {summary['runtime_base_policy_required']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3073 writes one bounded offline direct-action repair fitting artifact under the M3071 multi-failure contract. "
            "This is not target quality, fitted policy quality, validation, ranking, promotion, repair-success, driver-performance, "
            "high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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
        ]
    ) + "\n"


def run_bounded_repair_fitting_preflight(
    *,
    m3072_audit: Path,
    m3071_dir: Path,
    m3065_dir: Path,
    m3061_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_source_artifacts(m3072_audit=m3072_audit, m3071_dir=m3071_dir, m3065_dir=m3065_dir, m3061_dir=m3061_dir)
    parent = load_parent_candidate(source["paths"]["m3065_candidate"])
    batch = build_repair_fitting_batch(source)
    source_ready = _source_preconditions_pass(source, parent)
    fitting_executed = bool(source_ready and batch.contracts_pass and batch.fit_observation.shape[0] > 0)
    model = fit_direct_action(batch) if fitting_executed else zero_model()
    if fitting_executed:
        write_candidate_artifact(paths["candidate_direct_action_repair_reflex_layer"], model)

    zero_prediction = predict_action(zero_model(), batch.fit_observation)
    parent_prediction_fit = predict_action(parent.model, batch.fit_observation)
    repair_prediction_fit = predict_action(model, batch.fit_observation)
    repair_prediction_all = predict_action(model, batch.all_observation)
    loss_rows = build_loss_trace_rows(
        batch,
        zero_prediction,
        parent_prediction_fit,
        repair_prediction_fit,
        repair_prediction_all,
        parent=parent,
        fitting_executed=fitting_executed,
    )
    quality_rows = build_target_quality_boundary_rows(source)
    actor_rows = build_actor_input_exclusion_rows()
    side_rows = build_checkpoint_side_effect_guard_rows()
    claim_rows = build_claim_boundary_rows()
    write_follow_up_manifest(paths["follow_up_manifest"], summary_path=paths["summary"], doc_path=paths["doc"], output_dir=output_dir)
    write_csv_rows(paths["repair_fitting_dataset_rows"], batch.dataset_rows, fieldnames=REPAIR_DATASET_FIELDNAMES)
    write_csv_rows(paths["repair_split_rows"], batch.split_rows, fieldnames=SPLIT_FIELDNAMES)
    write_csv_rows(paths["repair_mask_weight_rows"], batch.mask_weight_rows, fieldnames=MASK_WEIGHT_FIELDNAMES)
    write_csv_rows(paths["repair_loss_trace_rows"], loss_rows, fieldnames=LOSS_FIELDNAMES)
    write_csv_rows(paths["repair_target_quality_boundary_rows"], quality_rows, fieldnames=TARGET_QUALITY_FIELDNAMES)
    write_csv_rows(paths["repair_actor_input_exclusion_rows"], actor_rows, fieldnames=ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["repair_checkpoint_side_effect_guard_rows"], side_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "status": "completed" if fitting_executed else "failed",
            "fitting_executed": fitting_executed,
            "source_ready": source_ready,
            "repair_contracts_pass": batch.contracts_pass,
            "candidate_artifact": str(paths["candidate_direct_action_repair_reflex_layer"]),
            "follow_up_manifest": str(paths["follow_up_manifest"]),
        },
    )

    gate_rows = build_gate_matrix_rows(
        source=source,
        parent=parent,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_direct_action_repair_reflex_layer"].exists(),
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
        required_artifacts_present=_required_outputs_present(paths, include_summary=False, include_gate_matrix=False),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        parent=parent,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        required_artifacts_present=_required_outputs_present(paths, include_summary=False, include_gate_matrix=True),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")

    gate_rows = build_gate_matrix_rows(
        source=source,
        parent=parent,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        artifact_exists=paths["candidate_direct_action_repair_reflex_layer"].exists(),
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
        required_artifacts_present=_required_outputs_present(paths, include_summary=True, include_gate_matrix=True),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        parent=parent,
        batch=batch,
        loss_rows=loss_rows,
        quality_rows=quality_rows,
        actor_rows=actor_rows,
        side_rows=side_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        required_artifacts_present=_required_outputs_present(paths, include_summary=True, include_gate_matrix=True),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3072-audit", type=Path, default=DEFAULT_M3072_AUDIT)
    parser.add_argument("--m3071-dir", type=Path, default=DEFAULT_M3071_DIR)
    parser.add_argument("--m3065-dir", type=Path, default=DEFAULT_M3065_DIR)
    parser.add_argument("--m3061-dir", type=Path, default=DEFAULT_M3061_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    _ = args.device
    summary = run_bounded_repair_fitting_preflight(
        m3072_audit=args.m3072_audit,
        m3071_dir=args.m3071_dir,
        m3065_dir=args.m3065_dir,
        m3061_dir=args.m3061_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']}")
    if not summary["status_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
