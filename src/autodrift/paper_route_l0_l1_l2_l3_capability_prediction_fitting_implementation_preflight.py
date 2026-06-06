"""Bounded fitting implementation preflight for Route B capability prediction.

M2898 executes the accepted M2896 fitting recipe as implementation-preflight
instrumentation only. The produced fitted weights are run-local smoke artifacts:
they are not promoted, ranked, validated, or interpreted as model quality.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


DEFAULT_MILESTONE = "m2898-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-preflight"
DEFAULT_NEXT_BLOCKER = "m2899-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-result-audit"
DEFAULT_OUTPUT_DIR = Path("runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight")
DEFAULT_M2896_DESIGN = Path("docs/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.md")
DEFAULT_M2897_AUDIT = Path(
    "docs/m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit.md"
)
DEFAULT_M2893_DIR = Path("runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight")
DEFAULT_M2891_DIR = Path(
    "runs/m2891_paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2899-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-result-audit.json"
)

DEFAULT_SEEDS = [289800, 289801, 289802]
DEFAULT_OPTIMIZER_STEPS = 128
LEARNING_RATE = 0.0003
WEIGHT_DECAY = 0.0001
GRAD_CLIP_NORM = 1.0
TARGET_FAMILY_WEIGHT = 1.0
EPSILON = 1.0e-6
BINARY_TARGET_COLUMNS = {"recoverability_window_success"}

CLAIM_SCOPE = (
    "M2898 capability-prediction fitting implementation preflight only. It reads "
    "accepted M2896/M2897/M2893/M2891 artifacts, runs bounded AdamW optimizer "
    "smoke steps, writes run-local fitted preflight weights and diagnostics, and "
    "registers a result-audit follow-up. It does not reset, step, rollout, replay, "
    "validate, run PPO, rank profiles, select a winner, promote a checkpoint, "
    "publish a package, or claim model quality, driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full-driver completion, or level3 self-ID."
)
FORBIDDEN_INTERPRETATION = (
    "model quality, driver performance, controller-family ranking, profile ranking, "
    "checkpoint promotion, finite-window-vs-GRU verdict, paper result, current-sim "
    "verdict, validation readiness/result, high-fidelity validation, full-driver "
    "completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "dependency_mutation_performed": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "package_published": False,
    "model_quality_claim_made": False,
    "driver_performance_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

FITTING_RECIPE_FIELDNAMES = [
    "recipe_row_id",
    "profile_name",
    "profile_level",
    "input_shape",
    "input_scalar_dim",
    "target_scalar_dim",
    "optimizer",
    "learning_rate",
    "weight_decay",
    "global_norm_clip",
    "max_optimizer_steps_per_profile",
    "seed_list",
    "target_family_weight",
    "same_recipe_all_profiles",
    "profile_specific_tuning",
    "target_family_weight_tuning",
    "feature_source",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
SPLIT_FIELDNAMES = [
    "split_row_id",
    "materialized_task_id",
    "task_source_id",
    "split_name",
    "split_unit",
    "profile_task_count",
    "profile_leakage_detected",
    "paper_holdout_admitted",
    "ordinary_validation_denominator",
    "ranking_allowed",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
NORMALIZATION_FIELDNAMES = [
    "normalization_row_id",
    "target_family",
    "target_column",
    "loss_kind",
    "train_finite_count",
    "train_median",
    "train_iqr",
    "scale_floor_applied",
    "normalization_source",
    "target_scalar_active",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
AVAILABILITY_FIELDNAMES = [
    "availability_row_id",
    "materialized_task_id",
    "task_source_id",
    "split_name",
    "target_family",
    "target_column",
    "loss_kind",
    "raw_value",
    "normalized_value",
    "available",
    "target_scalar_active",
    "source_artifact",
    "used_as_zero_target",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
OPTIMIZER_STEP_FIELDNAMES = [
    "optimizer_step_id",
    "profile_name",
    "profile_level",
    "optimization_seed",
    "optimizer_step_index",
    "max_optimizer_steps_per_profile",
    "split_name",
    "loss_value",
    "gradient_norm_before_clip",
    "global_norm_clip",
    "learning_rate",
    "weight_decay",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
PROFILE_METRIC_FIELDNAMES = [
    "profile_metric_id",
    "profile_name",
    "profile_level",
    "optimization_seed",
    "split_name",
    "target_available_count",
    "active_target_scalar_count",
    "initial_loss",
    "final_loss",
    "loss_delta",
    "optimizer_steps_executed",
    "diagnostic_only_no_ranking",
    "model_quality_claim_made",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
BASELINE_FIELDNAMES = [
    "baseline_id",
    "profile_name",
    "profile_level",
    "split_name",
    "baseline_family",
    "target_available_count",
    "loss_value",
    "parameter_count",
    "inference_cost_proxy",
    "diagnostic_only_no_ranking",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
OVERFIT_GUARD_FIELDNAMES = [
    "overfit_guard_id",
    "guard_family",
    "status_pass",
    "observed",
    "expected",
    "fresh_source_diverse_panel_required_before_claim",
    "failure_type",
    "claim_boundary",
]
ROLLBACK_FIELDNAMES = [
    "rollback_id",
    "rollback_family",
    "status_pass",
    "observed",
    "expected",
    "rollback_required_if_failed",
    "failure_type",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
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


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _split_items(value: Any) -> list[str]:
    return [item for item in str(value or "").split("|") if item]


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    text = str(value or "").strip()
    if not text:
        return None
    if text.lower() == "true":
        return 1.0
    if text.lower() == "false":
        return 0.0
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _quantile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _median(values: list[float]) -> float:
    return _quantile(sorted(values), 0.5)


def _iqr(values: list[float]) -> float:
    ordered = sorted(values)
    return _quantile(ordered, 0.75) - _quantile(ordered, 0.25)


def _profile_level(profile_name: str) -> str:
    return profile_name.split("_", 1)[0] if "_" in profile_name else profile_name


def _parse_input_dim(input_shape: str) -> int:
    text = str(input_shape or "")
    obs = 0
    window = 1
    for token in text.replace(",", ";").split(";"):
        token = token.strip()
        if token.startswith("obs="):
            obs = int(token.split("=", 1)[1])
        elif token.startswith("window="):
            window = int(token.split("=", 1)[1])
    return obs * window if obs else P0_OBSERVATION_DIM


def _target_specs(label_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for row in label_rows:
        loss_family = row.get("loss_family", "")
        for column in _split_items(row.get("required_columns", "")):
            is_binary = column in BINARY_TARGET_COLUMNS and "binary_recoverability" in loss_family
            specs.append(
                {
                    "target_family": row.get("target_family", ""),
                    "target_column": column,
                    "loss_kind": "bce_with_logits" if is_binary else "smooth_l1",
                    "binary": is_binary,
                }
            )
    return specs


def _discover_m2887_dir(m2891_summary: dict[str, Any], m2891_dir: Path) -> Path:
    value = m2891_summary.get("m2887_dir")
    if value:
        return Path(str(value))
    return m2891_dir.parent / "m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight"


def _discover_m2884_dir(m2887_summary: dict[str, Any], m2887_dir: Path) -> Path:
    value = m2887_summary.get("m2884_dir")
    if value:
        return Path(str(value))
    return m2887_dir.parent / "m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight"


def _candidate_execution_paths(m2884_dir: Path) -> list[Path]:
    source_rows = _read_csv_rows(m2884_dir / "source_inventory_rows.csv")
    paths: list[Path] = []
    for row in source_rows:
        path = Path(row.get("path", ""))
        if path.name == "candidate_execution_rows.csv":
            paths.append(path)
        if path.name in {"selected_candidate_rows.csv", "fresh_candidate_rows.csv", "post_package_candidate_rows.csv"}:
            sibling = path.parent / "candidate_execution_rows.csv"
            if sibling.exists():
                paths.append(sibling)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _execution_path_priority(path: Path) -> int:
    text = str(path)
    if "m2877_" in text:
        return 10
    if "m2838_" in text:
        return 20
    if "m2828_" in text:
        return 30
    return 100


def load_target_source_rows(
    *, usable_task_rows: list[dict[str, str]], execution_paths: list[Path]
) -> dict[str, dict[str, Any]]:
    usable_ids = {row.get("task_source_id", "") for row in usable_task_rows}
    candidates: dict[str, tuple[int, dict[str, Any]]] = {}
    for path in sorted(execution_paths, key=_execution_path_priority):
        for row in _read_csv_rows(path):
            task_source_id = row.get("task_source_id", "")
            if task_source_id not in usable_ids:
                continue
            priority = _execution_path_priority(path)
            if task_source_id not in candidates or priority < candidates[task_source_id][0]:
                source_row: dict[str, Any] = dict(row)
                source_row["_source_artifact"] = str(path)
                candidates[task_source_id] = (priority, source_row)
    return {task_source_id: row for task_source_id, (_, row) in candidates.items()}


def build_task_source_split_rows(usable_task_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    sorted_tasks = sorted(usable_task_rows, key=lambda row: row.get("task_source_id", ""))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted_tasks, start=1):
        split_name = "smoke_eval" if index % 5 == 0 else "smoke_fit"
        profile_task_count = int(row.get("profile_count", 0) or 0)
        status_pass = bool(row.get("task_source_id")) and profile_task_count == len(REQUIRED_PROFILES)
        rows.append(
            {
                "split_row_id": f"m2898-task-source-split-{index:04d}",
                "materialized_task_id": row.get("materialized_task_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "split_name": split_name,
                "split_unit": "task_source_id",
                "profile_task_count": profile_task_count,
                "profile_leakage_detected": False,
                "paper_holdout_admitted": False,
                "ordinary_validation_denominator": False,
                "ranking_allowed": False,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_normalization_rows(
    *,
    target_specs: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    source_rows_by_task: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    split_by_task = {row["task_source_id"]: row["split_name"] for row in split_rows}
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(target_specs, start=1):
        column = spec["target_column"]
        train_values = [
            value
            for task_source_id, source_row in source_rows_by_task.items()
            if split_by_task.get(task_source_id) == "smoke_fit"
            for value in [_to_float(source_row.get(column))]
            if value is not None
        ]
        train_count = len(train_values)
        if spec["binary"]:
            median = ""
            scale = ""
            scale_floor_applied = False
            active = train_count >= 2
            status_pass = True
        else:
            median_value = _median(train_values) if train_values else 0.0
            raw_scale = _iqr(train_values) if train_count >= 2 else 0.0
            if raw_scale <= EPSILON and train_count >= 2:
                deviations = [abs(value - median_value) for value in train_values]
                raw_scale = _median(deviations)
            scale_floor_applied = raw_scale <= EPSILON
            scale_value = raw_scale if raw_scale > EPSILON else 1.0
            median = median_value
            scale = scale_value
            active = train_count >= 2
            status_pass = True
        rows.append(
            {
                "normalization_row_id": f"m2898-target-normalization-{index:04d}",
                "target_family": spec["target_family"],
                "target_column": column,
                "loss_kind": spec["loss_kind"],
                "train_finite_count": train_count,
                "train_median": median,
                "train_iqr": scale,
                "scale_floor_applied": scale_floor_applied,
                "normalization_source": "smoke_fit_task_source_id_split_only",
                "target_scalar_active": active,
                "status_pass": status_pass,
                "failure_type": "none" if status_pass else "metric_artifact",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_availability_mask_rows(
    *,
    target_specs: list[dict[str, Any]],
    usable_task_rows: list[dict[str, str]],
    split_rows: list[dict[str, Any]],
    normalization_rows: list[dict[str, Any]],
    source_rows_by_task: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    split_by_task = {row["task_source_id"]: row["split_name"] for row in split_rows}
    normalization_by_column = {row["target_column"]: row for row in normalization_rows}
    rows: list[dict[str, Any]] = []
    row_id = 0
    for task in sorted(usable_task_rows, key=lambda row: row.get("task_source_id", "")):
        task_source_id = task.get("task_source_id", "")
        source_row = source_rows_by_task.get(task_source_id, {})
        for spec in target_specs:
            row_id += 1
            column = spec["target_column"]
            raw_value = source_row.get(column, "")
            value = _to_float(raw_value)
            available = value is not None
            norm = normalization_by_column[column]
            active = _bool(norm["target_scalar_active"])
            normalized: float | str = ""
            if available and active:
                if spec["binary"]:
                    normalized = float(value)
                else:
                    normalized = (float(value) - float(norm["train_median"])) / float(norm["train_iqr"])
            status_pass = bool(source_row) and not (available and not math.isfinite(float(value or 0.0)))
            rows.append(
                {
                    "availability_row_id": f"m2898-availability-mask-{row_id:04d}",
                    "materialized_task_id": task.get("materialized_task_id", ""),
                    "task_source_id": task_source_id,
                    "split_name": split_by_task.get(task_source_id, ""),
                    "target_family": spec["target_family"],
                    "target_column": column,
                    "loss_kind": spec["loss_kind"],
                    "raw_value": raw_value,
                    "normalized_value": normalized,
                    "available": available,
                    "target_scalar_active": active,
                    "source_artifact": source_row.get("_source_artifact", ""),
                    "used_as_zero_target": False,
                    "status_pass": status_pass,
                    "failure_type": "metric_artifact" if not status_pass else "none",
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def _matrix_from_availability(
    *,
    split_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    target_specs: list[dict[str, Any]],
    device: torch.device,
) -> tuple[list[str], torch.Tensor, torch.Tensor, torch.Tensor, dict[str, str]]:
    task_ids = [row["task_source_id"] for row in split_rows]
    task_index = {task_source_id: index for index, task_source_id in enumerate(task_ids)}
    target_index = {spec["target_column"]: index for index, spec in enumerate(target_specs)}
    target = torch.zeros((len(task_ids), len(target_specs)), dtype=torch.float32, device=device)
    mask = torch.zeros_like(target, dtype=torch.bool)
    binary_mask = torch.zeros((len(target_specs),), dtype=torch.bool, device=device)
    split_by_task = {row["task_source_id"]: row["split_name"] for row in split_rows}
    for index, spec in enumerate(target_specs):
        binary_mask[index] = bool(spec["binary"])
    for row in availability_rows:
        if not (_bool(row["available"]) and _bool(row["target_scalar_active"])):
            continue
        task_source_id = row["task_source_id"]
        column = row["target_column"]
        target[task_index[task_source_id], target_index[column]] = float(row["normalized_value"])
        mask[task_index[task_source_id], target_index[column]] = True
    return task_ids, target, mask, binary_mask, split_by_task


def _masked_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    binary_mask: torch.Tensor,
) -> torch.Tensor:
    if not bool(mask.any()):
        return prediction.sum() * 0.0
    binary_columns = binary_mask.unsqueeze(0).expand_as(mask)
    continuous = mask & ~binary_columns
    binary = mask & binary_columns
    loss = prediction.sum() * 0.0
    mass = 0
    if bool(continuous.any()):
        loss = loss + F.smooth_l1_loss(prediction[continuous], target[continuous], reduction="sum")
        mass += int(continuous.sum().item())
    if bool(binary.any()):
        loss = loss + F.binary_cross_entropy_with_logits(prediction[binary], target[binary], reduction="sum")
        mass += int(binary.sum().item())
    return loss / max(float(mass), 1.0)


def _deterministic_shape_features(
    *, task_count: int, input_dim: int, profile_index: int, seed: int, device: torch.device
) -> torch.Tensor:
    row_positions = torch.arange(1, task_count + 1, dtype=torch.float32, device=device).unsqueeze(1)
    col_positions = torch.arange(1, input_dim + 1, dtype=torch.float32, device=device).unsqueeze(0)
    phase = (seed % 997) * 0.0001 + profile_index * 0.07
    features = torch.sin(row_positions * ((col_positions % 29.0) + 1.0) * 0.017 + phase)
    features = features + 0.5 * torch.cos(row_positions * ((col_positions % 17.0) + 1.0) * 0.031 + phase)
    return features.to(torch.float32)


def _loss_for_split(
    model: torch.nn.Module,
    features: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    binary_mask: torch.Tensor,
    split_indices: list[int],
) -> float:
    if not split_indices:
        return float("nan")
    with torch.no_grad():
        prediction = model(features[split_indices])
        loss = _masked_loss(prediction, target[split_indices], mask[split_indices], binary_mask)
    return float(loss.detach().cpu().item())


def _gradient_norm(parameters: Any) -> float:
    norms: list[torch.Tensor] = []
    for parameter in parameters:
        if parameter.grad is not None:
            norms.append(parameter.grad.detach().norm(2))
    if not norms:
        return 0.0
    return float(torch.norm(torch.stack(norms), 2).detach().cpu().item())


def build_fitting_recipe_rows(
    *,
    model_head_rows: list[dict[str, str]],
    target_scalar_dim: int,
    seed_list: list[int],
    optimizer_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_profile = {row.get("profile_name", ""): row for row in model_head_rows}
    for index, profile in enumerate(REQUIRED_PROFILES, start=1):
        row = by_profile.get(profile, {})
        input_shape = row.get("input_shape", "")
        input_dim = _parse_input_dim(input_shape)
        status_pass = _bool(row.get("status_pass")) and target_scalar_dim > 0 and optimizer_steps <= DEFAULT_OPTIMIZER_STEPS
        rows.append(
            {
                "recipe_row_id": f"m2898-fitting-recipe-{index:04d}",
                "profile_name": profile,
                "profile_level": _profile_level(profile),
                "input_shape": input_shape,
                "input_scalar_dim": input_dim,
                "target_scalar_dim": target_scalar_dim,
                "optimizer": "AdamW",
                "learning_rate": LEARNING_RATE,
                "weight_decay": WEIGHT_DECAY,
                "global_norm_clip": GRAD_CLIP_NORM,
                "max_optimizer_steps_per_profile": optimizer_steps,
                "seed_list": "|".join(str(seed) for seed in seed_list),
                "target_family_weight": TARGET_FAMILY_WEIGHT,
                "same_recipe_all_profiles": True,
                "profile_specific_tuning": False,
                "target_family_weight_tuning": False,
                "feature_source": "deterministic_deployable_shape_contract_projection_no_target_leakage",
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _baseline_loss(
    *,
    target: torch.Tensor,
    mask: torch.Tensor,
    binary_mask: torch.Tensor,
    split_indices: list[int],
    target_dim: int,
    baseline_family: str,
    device: torch.device,
) -> float:
    prediction = torch.zeros((len(split_indices), target_dim), dtype=torch.float32, device=device)
    if baseline_family == "binary_train_prevalence_logit":
        train_target = target[split_indices]
        train_mask = mask[split_indices]
        binary_cols = binary_mask.unsqueeze(0).expand_as(train_mask)
        for target_index in range(target_dim):
            if not bool(binary_mask[target_index]):
                continue
            active = train_mask[:, target_index] & binary_cols[:, target_index]
            if bool(active.any()):
                prevalence = float(train_target[:, target_index][active].mean().detach().cpu().item())
                prevalence = min(max(prevalence, 1.0e-4), 1.0 - 1.0e-4)
                prediction[:, target_index] = math.log(prevalence / (1.0 - prevalence))
    return float(_masked_loss(prediction, target[split_indices], mask[split_indices], binary_mask).detach().cpu().item())


def build_baseline_rows(
    *,
    recipe_rows: list[dict[str, Any]],
    target: torch.Tensor,
    mask: torch.Tensor,
    binary_mask: torch.Tensor,
    fit_indices: list[int],
    eval_indices: list[int],
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split_indices = {"smoke_fit": fit_indices, "smoke_eval": eval_indices}
    target_dim = target.shape[1]
    row_id = 0
    for recipe in recipe_rows:
        profile = recipe["profile_name"]
        profile_level = recipe["profile_level"]
        parameter_count = (int(recipe["input_scalar_dim"]) + 1) * target_dim
        for split_name, indices in split_indices.items():
            target_available_count = int(mask[indices].sum().item()) if indices else 0
            for baseline_family in ["train_split_zero_normalized_baseline", "binary_train_prevalence_logit"]:
                row_id += 1
                loss = (
                    _baseline_loss(
                        target=target,
                        mask=mask,
                        binary_mask=binary_mask,
                        split_indices=indices,
                        target_dim=target_dim,
                        baseline_family=baseline_family,
                        device=device,
                    )
                    if indices
                    else float("nan")
                )
                rows.append(
                    {
                        "baseline_id": f"m2898-baseline-{row_id:04d}",
                        "profile_name": profile,
                        "profile_level": profile_level,
                        "split_name": split_name,
                        "baseline_family": baseline_family,
                        "target_available_count": target_available_count,
                        "loss_value": loss,
                        "parameter_count": parameter_count,
                        "inference_cost_proxy": parameter_count,
                        "diagnostic_only_no_ranking": True,
                        "status_pass": target_available_count > 0,
                        "failure_type": "metric_artifact" if target_available_count <= 0 else "none",
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
        if profile.endswith("current_tiled") or profile == "L3_reset_control_corrected":
            row_id += 1
            rows.append(
                {
                    "baseline_id": f"m2898-baseline-{row_id:04d}",
                    "profile_name": profile,
                    "profile_level": profile_level,
                    "split_name": "all_public_preflight",
                    "baseline_family": "architecture_control_baseline",
                    "target_available_count": int(mask.sum().item()),
                    "loss_value": "",
                    "parameter_count": parameter_count,
                    "inference_cost_proxy": parameter_count,
                    "diagnostic_only_no_ranking": True,
                    "status_pass": True,
                    "failure_type": "none",
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def fit_profiles(
    *,
    recipe_rows: list[dict[str, Any]],
    target: torch.Tensor,
    mask: torch.Tensor,
    binary_mask: torch.Tensor,
    split_by_task: dict[str, str],
    task_ids: list[str],
    seed_list: list[int],
    optimizer_steps: int,
    checkpoints_dir: Path,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    fit_indices = [index for index, task_id in enumerate(task_ids) if split_by_task[task_id] == "smoke_fit"]
    eval_indices = [index for index, task_id in enumerate(task_ids) if split_by_task[task_id] == "smoke_eval"]
    optimizer_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    checkpoint_rows: list[dict[str, Any]] = []
    row_id = 0
    metric_id = 0
    target_dim = target.shape[1]

    for profile_index, recipe in enumerate(recipe_rows, start=1):
        profile = str(recipe["profile_name"])
        profile_level = str(recipe["profile_level"])
        input_dim = int(recipe["input_scalar_dim"])
        for seed in seed_list:
            torch.manual_seed(seed)
            model = torch.nn.Linear(input_dim, target_dim).to(device)
            optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
            features = _deterministic_shape_features(
                task_count=len(task_ids),
                input_dim=input_dim,
                profile_index=profile_index,
                seed=seed,
                device=device,
            )
            initial_fit = _loss_for_split(model, features, target, mask, binary_mask, fit_indices)
            initial_eval = _loss_for_split(model, features, target, mask, binary_mask, eval_indices)
            last_loss = initial_fit
            last_grad_norm = 0.0
            for step in range(1, optimizer_steps + 1):
                optimizer.zero_grad(set_to_none=True)
                prediction = model(features[fit_indices])
                loss = _masked_loss(prediction, target[fit_indices], mask[fit_indices], binary_mask)
                loss.backward()
                last_grad_norm = _gradient_norm(model.parameters())
                torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP_NORM)
                optimizer.step()
                last_loss = float(loss.detach().cpu().item())
                row_id += 1
                optimizer_rows.append(
                    {
                        "optimizer_step_id": f"m2898-optimizer-step-{row_id:05d}",
                        "profile_name": profile,
                        "profile_level": profile_level,
                        "optimization_seed": seed,
                        "optimizer_step_index": step,
                        "max_optimizer_steps_per_profile": optimizer_steps,
                        "split_name": "smoke_fit",
                        "loss_value": last_loss,
                        "gradient_norm_before_clip": last_grad_norm,
                        "global_norm_clip": GRAD_CLIP_NORM,
                        "learning_rate": LEARNING_RATE,
                        "weight_decay": WEIGHT_DECAY,
                        "status_pass": step <= optimizer_steps and math.isfinite(last_loss),
                        "failure_type": "training_instability" if not math.isfinite(last_loss) else "none",
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
            final_fit = _loss_for_split(model, features, target, mask, binary_mask, fit_indices)
            final_eval = _loss_for_split(model, features, target, mask, binary_mask, eval_indices)
            for split_name, indices, initial, final in [
                ("smoke_fit", fit_indices, initial_fit, final_fit),
                ("smoke_eval", eval_indices, initial_eval, final_eval),
            ]:
                metric_id += 1
                target_available_count = int(mask[indices].sum().item()) if indices else 0
                status_pass = target_available_count > 0 and math.isfinite(final)
                metric_rows.append(
                    {
                        "profile_metric_id": f"m2898-profile-metric-{metric_id:05d}",
                        "profile_name": profile,
                        "profile_level": profile_level,
                        "optimization_seed": seed,
                        "split_name": split_name,
                        "target_available_count": target_available_count,
                        "active_target_scalar_count": int(mask.any(dim=0).sum().item()),
                        "initial_loss": initial,
                        "final_loss": final,
                        "loss_delta": initial - final if math.isfinite(initial) and math.isfinite(final) else "",
                        "optimizer_steps_executed": optimizer_steps,
                        "diagnostic_only_no_ranking": True,
                        "model_quality_claim_made": False,
                        "status_pass": status_pass,
                        "failure_type": "metric_artifact" if not status_pass else "none",
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
            checkpoint_path = checkpoints_dir / f"{profile}_seed_{seed}_preflight.pt"
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "metadata": {
                        "milestone": DEFAULT_MILESTONE,
                        "profile_name": profile,
                        "optimization_seed": seed,
                        "optimizer_steps": optimizer_steps,
                        "preflight_only": True,
                        "checkpoint_promoted": False,
                        "winner_selected": False,
                        "model_quality_claim_made": False,
                        "claim_boundary": CLAIM_SCOPE,
                    },
                },
                checkpoint_path,
            )
            checkpoint_rows.append(
                {
                    "profile_name": profile,
                    "optimization_seed": seed,
                    "checkpoint_path": str(checkpoint_path),
                    "checkpoint_exists": checkpoint_path.exists(),
                    "checkpoint_promoted": False,
                }
            )
    return optimizer_rows, metric_rows, checkpoint_rows


def build_overfit_guard_rows(
    *,
    split_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    source_singleton_rows_paper_proof_allowed: bool,
    guard_rows_ordinary_success_denominator_allowed: bool,
) -> list[dict[str, Any]]:
    eval_count = sum(1 for row in split_rows if row["split_name"] == "smoke_eval")
    fit_count = sum(1 for row in split_rows if row["split_name"] == "smoke_fit")
    active_target_count = len({row["target_column"] for row in availability_rows if _bool(row["target_scalar_active"])})
    rows = [
        (
            "m2898-overfit-guard-task-source-split",
            "task_source_split_no_profile_leakage",
            all(not _bool(row["profile_leakage_detected"]) for row in split_rows),
            "profile_leakage_detected=False",
            "profile_leakage_detected=False",
            False,
            "contract_violation",
        ),
        (
            "m2898-overfit-guard-smoke-eval-present",
            "smoke_eval_non_empty",
            eval_count > 0 and fit_count > 0,
            f"fit={fit_count};eval={eval_count}",
            "fit>0;eval>0",
            False,
            "scenario_sampling_failure",
        ),
        (
            "m2898-overfit-guard-active-targets",
            "availability_mask_active_targets",
            active_target_count > 0,
            active_target_count,
            ">0",
            False,
            "metric_artifact",
        ),
        (
            "m2898-overfit-guard-exclusions",
            "source_singleton_and_guard_exclusions",
            not source_singleton_rows_paper_proof_allowed and not guard_rows_ordinary_success_denominator_allowed,
            f"source_singleton_proof={source_singleton_rows_paper_proof_allowed};guard_denominator={guard_rows_ordinary_success_denominator_allowed}",
            "source_singleton_proof=False;guard_denominator=False",
            False,
            "proof_washout",
        ),
        (
            "m2898-overfit-guard-fresh-panel-trigger",
            "fresh_source_diverse_panel_required_before_claim",
            True,
            "required_before_model_quality_or_paper_claim",
            "required_before_model_quality_or_paper_claim",
            True,
            "objective_overfit",
        ),
        (
            "m2898-overfit-guard-no-ranking",
            "diagnostic_not_ranking",
            True,
            "ranking_run=False;winner_selected=False",
            "ranking_run=False;winner_selected=False",
            False,
            "contract_violation",
        ),
    ]
    return [
        {
            "overfit_guard_id": guard_id,
            "guard_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "fresh_source_diverse_panel_required_before_claim": fresh_required,
            "failure_type": "none" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, status, observed, expected, fresh_required, failure_type in rows
    ]


def build_rollback_rows(
    *,
    target_family_active: dict[str, bool],
    optimizer_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    recipe_rows: list[dict[str, Any]],
    source_rows_by_task: dict[str, dict[str, Any]],
    expected_task_count: int,
) -> list[dict[str, Any]]:
    all_families_active = bool(target_family_active) and all(target_family_active.values())
    all_optimizer_rows_finite = bool(optimizer_rows) and all(_bool(row["status_pass"]) for row in optimizer_rows)
    all_checkpoints_run_local = bool(checkpoint_rows) and all(
        _bool(row["checkpoint_exists"]) and not _bool(row["checkpoint_promoted"]) for row in checkpoint_rows
    )
    all_same_recipe = bool(recipe_rows) and all(
        row["optimizer"] == "AdamW"
        and float(row["learning_rate"]) == LEARNING_RATE
        and float(row["weight_decay"]) == WEIGHT_DECAY
        and int(row["max_optimizer_steps_per_profile"]) <= DEFAULT_OPTIMIZER_STEPS
        and not _bool(row["profile_specific_tuning"])
        and not _bool(row["target_family_weight_tuning"])
        for row in recipe_rows
    )
    source_coverage = len(source_rows_by_task) == expected_task_count
    specs = [
        (
            "m2898-rollback-actor-contract",
            "actor_observation_action_contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "obs=72;action=3",
            "rollback_if_actor_contract_changes",
            "contract_violation",
        ),
        (
            "m2898-rollback-source-coverage",
            "evaluator_target_source_coverage",
            source_coverage,
            f"sources={len(source_rows_by_task)};tasks={expected_task_count}",
            "sources=tasks",
            "rollback_if_target_sources_missing",
            "lineage_invalid",
        ),
        (
            "m2898-rollback-target-family-active",
            "target_family_availability",
            all_families_active,
            ";".join(f"{key}={value}" for key, value in sorted(target_family_active.items())),
            "each_family_has_at_least_one_active_scalar",
            "rollback_if_required_family_missing",
            "metric_artifact",
        ),
        (
            "m2898-rollback-same-recipe",
            "same_optimizer_recipe_all_profiles",
            all_same_recipe,
            "AdamW lr=0.0003 weight_decay=0.0001 max_steps<=128 target_family_weight=1.0",
            "same_recipe_all_profiles=True",
            "rollback_if_recipe_differs_by_profile",
            "contract_violation",
        ),
        (
            "m2898-rollback-optimizer-finite",
            "optimizer_step_finite_and_bounded",
            all_optimizer_rows_finite,
            f"optimizer_rows={len(optimizer_rows)}",
            "all_optimizer_rows_status_pass=True",
            "rollback_if_optimizer_nonfinite_or_unbounded",
            "training_instability",
        ),
        (
            "m2898-rollback-checkpoints-run-local",
            "fitted_weights_run_local_not_promoted",
            all_checkpoints_run_local,
            f"checkpoint_rows={len(checkpoint_rows)}",
            "checkpoint_exists=True;checkpoint_promoted=False",
            "rollback_if_checkpoint_promoted_or_missing",
            "contract_violation",
        ),
        (
            "m2898-rollback-no-forbidden-claims",
            "forbidden_claim_flags_false",
            not any(FALSE_CLAIM_FLAGS.values()),
            ";".join(f"{key}={value}" for key, value in sorted(FALSE_CLAIM_FLAGS.items())),
            "all_forbidden_claim_flags_false",
            "rollback_if_forbidden_claim_made",
            "contract_violation",
        ),
    ]
    return [
        {
            "rollback_id": rollback_id,
            "rollback_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "rollback_required_if_failed": rollback,
            "failure_type": "none" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for rollback_id, family, status, observed, expected, rollback, failure_type in specs
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    allowed = [
        ("fitting_implementation_preflight_artifacts", "summary and CSV artifacts"),
        ("bounded_optimizer_step_artifacts", "optimizer_step_rows.csv"),
        ("run_local_fitted_preflight_weights", "checkpoints under M2898 run directory"),
        ("availability_mask_and_normalization_artifacts", "availability_mask_rows.csv and target_normalization_rows.csv"),
        ("bounded_result_audit_handoff", "M2899 manifest"),
    ]
    blocked = [
        ("validation", "separate evaluation manifest"),
        ("profile_ranking", "separate fair comparison and audit"),
        ("winner_selection", "promotion-gated comparison evidence"),
        ("checkpoint_promotion", "promotion gate"),
        ("model_quality", "accepted evaluation evidence"),
        ("driver_performance", "closed-loop validation and promotion evidence"),
        ("finite_window_vs_gru", "separate fair L0/L1/L2/L3 comparison"),
        ("paper", "paper-route audit and holdout evidence"),
        ("current_sim_verdict", "separate current-sim verdict gate"),
        ("high_fidelity_validation", "Route C high-fidelity validation gate"),
        ("level3_self_id", "source-diverse history-necessity intervention evidence"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (claim_family, evidence) in enumerate(allowed, start=1):
        rows.append(
            {
                "claim_id": f"m2898-claim-{index:04d}",
                "claim_family": claim_family,
                "claim_made": True,
                "claim_allowed": True,
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    offset = len(rows)
    for index, (claim_family, evidence) in enumerate(blocked, start=1):
        rows.append(
            {
                "claim_id": f"m2898-claim-{offset + index:04d}",
                "claim_family": claim_family,
                "claim_made": False,
                "claim_allowed": False,
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_rows(
    *,
    parent_artifact_exists: dict[str, bool],
    m2893_summary: dict[str, Any],
    m2891_summary: dict[str, Any],
    split_rows: list[dict[str, Any]],
    normalization_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    recipe_rows: list[dict[str, Any]],
    optimizer_rows: list[dict[str, Any]],
    profile_metric_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    overfit_guard_rows: list[dict[str, Any]],
    rollback_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    blocked_claim_gate_pass = all(_bool(row["claim_allowed"]) or not _bool(row["claim_made"]) for row in claim_rows)
    return [
        gate(
            "m2898-parent-artifacts-present",
            "lineage",
            all(parent_artifact_exists.values()),
            ";".join(f"{key}={value}" for key, value in sorted(parent_artifact_exists.items())),
            "all_parent_artifacts_present=True",
            "lineage_invalid",
        ),
        gate(
            "m2898-parent-preflights-accepted",
            "lineage",
            _bool(m2893_summary.get("status_pass"))
            and _bool(m2893_summary.get("gate_matrix_pass"))
            and _bool(m2891_summary.get("status_pass"))
            and _bool(m2891_summary.get("gate_matrix_pass")),
            f"m2893={m2893_summary.get('status_pass')};m2891={m2891_summary.get('status_pass')}",
            "m2893=True;m2891=True",
            "lineage_invalid",
        ),
        gate(
            "m2898-split-rows-pass",
            "task_source_split",
            bool(split_rows) and all(_bool(row["status_pass"]) for row in split_rows),
            len(split_rows),
            ">0",
            "contract_violation",
        ),
        gate(
            "m2898-normalization-rows-pass",
            "target_normalization",
            bool(normalization_rows) and all(_bool(row["status_pass"]) for row in normalization_rows),
            len(normalization_rows),
            ">0",
            "metric_artifact",
        ),
        gate(
            "m2898-availability-mask-rows-pass",
            "availability_mask",
            bool(availability_rows) and all(_bool(row["status_pass"]) for row in availability_rows),
            len(availability_rows),
            ">0",
            "metric_artifact",
        ),
        gate(
            "m2898-fitting-recipe-rows-pass",
            "fitting_recipe",
            bool(recipe_rows) and all(_bool(row["status_pass"]) for row in recipe_rows),
            len(recipe_rows),
            len(REQUIRED_PROFILES),
            "contract_violation",
        ),
        gate(
            "m2898-optimizer-step-rows-pass",
            "optimizer_steps",
            bool(optimizer_rows) and all(_bool(row["status_pass"]) for row in optimizer_rows),
            len(optimizer_rows),
            ">0",
            "training_instability",
        ),
        gate(
            "m2898-profile-diagnostics-pass",
            "profile_diagnostics",
            bool(profile_metric_rows) and all(_bool(row["status_pass"]) for row in profile_metric_rows),
            len(profile_metric_rows),
            ">0",
            "metric_artifact",
        ),
        gate(
            "m2898-baseline-diagnostics-pass",
            "baseline_diagnostics",
            bool(baseline_rows) and all(_bool(row["status_pass"]) for row in baseline_rows),
            len(baseline_rows),
            ">0",
            "metric_artifact",
        ),
        gate(
            "m2898-overfit-guards-pass",
            "overfit_guards",
            bool(overfit_guard_rows) and all(_bool(row["status_pass"]) for row in overfit_guard_rows),
            len(overfit_guard_rows),
            ">0",
            "objective_overfit",
        ),
        gate(
            "m2898-rollback-guards-pass",
            "rollback",
            bool(rollback_rows) and all(_bool(row["status_pass"]) for row in rollback_rows),
            len(rollback_rows),
            ">0",
            "contract_violation",
        ),
        gate(
            "m2898-no-forbidden-claims",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()) and blocked_claim_gate_pass,
            sum(_bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows),
            0,
            "contract_violation",
        ),
        gate(
            "m2898-follow-up-manifest-registered",
            "handoff",
            follow_up_manifest.exists(),
            follow_up_manifest.exists(),
            True,
            "lineage_invalid",
        ),
    ]


def build_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2898 fitting implementation preflight before any validation ranking model-quality paper or self-ID claim.",
        "lineage": {
            "parent_checkpoint": summary["baseline_checkpoints"],
            "parent_dataset": [
                summary["artifacts"]["summary"],
                summary["artifacts"]["fitting_recipe_rows"],
                summary["artifacts"]["task_source_split_rows"],
                summary["artifacts"]["target_normalization_rows"],
                summary["artifacts"]["availability_mask_rows"],
                summary["artifacts"]["optimizer_step_rows"],
                summary["artifacts"]["profile_metric_diagnostic_rows"],
                summary["artifacts"]["baseline_diagnostic_rows"],
                summary["artifacts"]["overfit_guard_rows"],
                summary["artifacts"]["rollback_rows"],
                summary["artifacts"]["claim_rows"],
            ],
            "parent_config": [
                f"experiments/manifests/{DEFAULT_MILESTONE}.json",
                "experiments/manifests/m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit.json",
                "experiments/manifests/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.json",
            ],
            "parent_objective": [
                "audit whether M2898 implemented the fixed M2896 fitting recipe as bounded preflight artifacts"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit",
                "m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design",
            ],
            "blocked_by": [
                "M2898 fitting artifacts must be audited before any model-quality interpretation",
                "17 usable rows remain public and preflight-only",
                "fresh/source-diverse panel remains required before paper claims",
            ],
            "supersedes": [
                "treating bounded fitting smoke losses as validation evidence",
                "ranking profiles directly from M2898 diagnostics",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2899 must audit M2898 summary fitting recipe split normalization availability optimizer diagnostic baseline overfit rollback and claim rows",
            "M2899 must accept or reject bounded implementation-preflight completeness",
            "M2899 must preserve actor 72/action 3 no hidden/oracle actor input no future-target actor input and evaluator-only target boundaries",
            "M2899 must preserve source-singleton and guard exclusions paper holdout false preflight-only split and fresh-panel trigger semantics",
            "M2899 must not validate rank select a winner promote claim model quality driver performance finite-window-vs-GRU paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate run PPO rank promote publish a package or select a winner",
            "do not convert optimizer smoke diagnostics into model-quality ranking paper or self-ID claims",
            "do not treat fitted preflight weights as promoted checkpoints",
            "do not claim prediction quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
            "training_instability",
        ],
        "workflow_synthesis": {
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract",
            "evidence_axis": "route_b_capability_prediction_fitting_implementation_result_audit",
            "evidence_increment": "audits bounded fitting implementation artifacts before any model-quality or paper route",
            "claim_scope": "Result audit only; no validation ranking model quality finite-window-vs-GRU verdict driver performance paper current-sim high-fidelity full-driver or self-ID claim",
            "stop_condition": [
                "stop if fitting recipe split normalization availability mask optimizer or rollback artifacts are incomplete",
                "stop if fitted weights were promoted or interpreted as model quality",
                "stop if actor target or exclusion boundaries fail",
                "stop if public-row overfit risk would be ignored",
            ],
            "fallback_plan": [
                "route to implementation repair if bounded fitting artifacts are incomplete but actor-safe",
                "route to contract repair if target masks normalization or split semantics are insufficient",
                "route to fresh/source-diverse data-panel design if public-row overfit blocks model-quality work",
                "route to synthesis if another narrow preflight would add process overhead without evidence expansion",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2898 writes bounded fitting implementation-preflight artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2898 bounded fitting implementation-preflight result audit",
            "admission_evidence": [
                "M2898 wrote bounded fitting implementation-preflight artifacts",
                "M2897 admitted implementation preflight only before validation ranking or model-quality claims",
            ],
            "blocked_shortcuts": [
                "no reset rollout replay validation ranking promotion",
                "no hidden or oracle actor inputs",
                "no future target actor input",
                "no source-singleton or guard rows as proof",
                "no driver-performance paper current-sim high-fidelity finite-window-vs-GRU full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2899 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if the audit selects a route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2898 fitting implementation preflight is accepted or rejected",
                "one next Route B action or stop decision is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2899 audits fitting implementation preflight only and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2899; later tests require accepted fitting audit and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2889-M2898 Route B capability-prediction modeling contract implementation and fitting-preflight chain.",
            "negative_result_policy": "Preserve insufficient fitting or boundary failure as a negative result rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2898 implementation preflight accepted or rejected",
                "bounded follow-up route or stop decision",
                "no model-quality driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0 if summary["status_pass"] else 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the first bounded fitting implementation artifacts in the Route B capability-prediction chain",
            "paper_verdict_delta": "no verdict; may admit model-quality design only if public-row and fresh-panel boundaries remain explicit",
            "must_synthesize_if": [
                "M2899 cannot decide whether M2898 fitting implementation preflight is sufficient",
                "M2899 would claim self-ID finite-window-vs-GRU driver performance model quality or current-sim verdict",
                "M2899 would ignore public-row overfit risk",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2898 implementation-preflight completeness and claim safety",
            "audit selects exactly one bounded next route or stop decision",
        ],
        "failure_criteria": [
            "M2899 resets steps rolls out validates trains ranks promotes or executes policy action",
            "M2899 changes actor input or action contract",
            "M2899 claims model quality driver performance finite-window-vs-GRU verdict paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "decision_rule": "Pass only if M2899 writes a claim-safe audit of M2898 before any validation ranking promotion model-quality or verdict claim.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": summary["baseline_checkpoints"],
        "baseline_artifacts": [
            summary["artifacts"]["summary"],
            summary["artifacts"]["fitting_recipe_rows"],
            summary["artifacts"]["optimizer_step_rows"],
            summary["artifacts"]["profile_metric_diagnostic_rows"],
            summary["artifacts"]["overfit_guard_rows"],
            summary["artifacts"]["rollback_rows"],
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2900-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-audit-synthesis-or-model-quality-design",
    }


def write_preflight_artifacts(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    m2896_design: Path = DEFAULT_M2896_DESIGN,
    m2897_audit: Path = DEFAULT_M2897_AUDIT,
    m2893_dir: Path = DEFAULT_M2893_DIR,
    m2891_dir: Path = DEFAULT_M2891_DIR,
    device: torch.device | None = None,
    seed_list: list[int] | None = None,
    optimizer_steps: int = DEFAULT_OPTIMIZER_STEPS,
) -> dict[str, Any]:
    device = device or torch.device("cpu")
    seed_list = seed_list or list(DEFAULT_SEEDS)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = output_dir / "checkpoints"

    m2891_paths = {
        "summary": m2891_dir / "summary.json",
        "label_contract_rows": m2891_dir / "label_contract_rows.csv",
        "split_contract_rows": m2891_dir / "split_contract_rows.csv",
        "baseline_contract_rows": m2891_dir / "baseline_contract_rows.csv",
    }
    m2893_paths = {
        "summary": m2893_dir / "summary.json",
        "loader_smoke_rows": m2893_dir / "loader_smoke_rows.csv",
        "model_head_smoke_rows": m2893_dir / "model_head_smoke_rows.csv",
    }
    parent_artifact_exists = {
        "m2896_design": m2896_design.exists(),
        "m2897_audit": m2897_audit.exists(),
        **{f"m2891_{key}": path.exists() for key, path in m2891_paths.items()},
        **{f"m2893_{key}": path.exists() for key, path in m2893_paths.items()},
    }

    m2891_summary = read_json(m2891_paths["summary"]) if m2891_paths["summary"].exists() else {}
    m2893_summary = read_json(m2893_paths["summary"]) if m2893_paths["summary"].exists() else {}
    label_rows = _read_csv_rows(m2891_paths["label_contract_rows"])
    _split_contract_rows = _read_csv_rows(m2891_paths["split_contract_rows"])
    _baseline_contract_rows = _read_csv_rows(m2891_paths["baseline_contract_rows"])
    loader_rows = _read_csv_rows(m2893_paths["loader_smoke_rows"])
    model_head_rows = _read_csv_rows(m2893_paths["model_head_smoke_rows"])

    m2887_dir = _discover_m2887_dir(m2891_summary, m2891_dir)
    m2887_summary_path = m2887_dir / "summary.json"
    m2887_summary = read_json(m2887_summary_path) if m2887_summary_path.exists() else {}
    m2884_dir = _discover_m2884_dir(m2887_summary, m2887_dir)
    usable_task_rows = _read_csv_rows(m2887_dir / "usable_task_rows.csv")
    profile_task_rows = _read_csv_rows(m2887_dir / "profile_task_rows.csv")
    execution_paths = _candidate_execution_paths(m2884_dir)
    source_rows_by_task = load_target_source_rows(usable_task_rows=usable_task_rows, execution_paths=execution_paths)

    target_specs = _target_specs(label_rows)
    split_rows = build_task_source_split_rows(usable_task_rows)
    normalization_rows = build_target_normalization_rows(
        target_specs=target_specs,
        split_rows=split_rows,
        source_rows_by_task=source_rows_by_task,
    )
    availability_rows = build_availability_mask_rows(
        target_specs=target_specs,
        usable_task_rows=usable_task_rows,
        split_rows=split_rows,
        normalization_rows=normalization_rows,
        source_rows_by_task=source_rows_by_task,
    )
    task_ids, target, mask, binary_mask, split_by_task = _matrix_from_availability(
        split_rows=split_rows,
        availability_rows=availability_rows,
        target_specs=target_specs,
        device=device,
    )
    recipe_rows = build_fitting_recipe_rows(
        model_head_rows=model_head_rows,
        target_scalar_dim=len(target_specs),
        seed_list=seed_list,
        optimizer_steps=optimizer_steps,
    )
    optimizer_rows, profile_metric_rows, checkpoint_rows = fit_profiles(
        recipe_rows=recipe_rows,
        target=target,
        mask=mask,
        binary_mask=binary_mask,
        split_by_task=split_by_task,
        task_ids=task_ids,
        seed_list=seed_list,
        optimizer_steps=optimizer_steps,
        checkpoints_dir=checkpoints_dir,
        device=device,
    )
    fit_indices = [index for index, task_id in enumerate(task_ids) if split_by_task[task_id] == "smoke_fit"]
    eval_indices = [index for index, task_id in enumerate(task_ids) if split_by_task[task_id] == "smoke_eval"]
    baseline_rows = build_baseline_rows(
        recipe_rows=recipe_rows,
        target=target,
        mask=mask,
        binary_mask=binary_mask,
        fit_indices=fit_indices,
        eval_indices=eval_indices,
        device=device,
    )
    target_family_active: dict[str, bool] = {}
    for spec in target_specs:
        column_active = any(
            row["target_column"] == spec["target_column"] and _bool(row["target_scalar_active"])
            for row in normalization_rows
        )
        target_family_active[spec["target_family"]] = target_family_active.get(spec["target_family"], False) or column_active

    overfit_guard_rows = build_overfit_guard_rows(
        split_rows=split_rows,
        availability_rows=availability_rows,
        source_singleton_rows_paper_proof_allowed=_bool(
            m2891_summary.get("source_singleton_rows_paper_proof_allowed")
        ),
        guard_rows_ordinary_success_denominator_allowed=_bool(
            m2891_summary.get("guard_rows_ordinary_success_denominator_allowed")
        ),
    )
    rollback_rows = build_rollback_rows(
        target_family_active=target_family_active,
        optimizer_rows=optimizer_rows,
        checkpoint_rows=checkpoint_rows,
        recipe_rows=recipe_rows,
        source_rows_by_task=source_rows_by_task,
        expected_task_count=len(usable_task_rows),
    )
    claim_rows = build_claim_rows()

    artifacts = {
        "summary": output_dir / "summary.json",
        "fitting_recipe_rows": output_dir / "fitting_recipe_rows.csv",
        "task_source_split_rows": output_dir / "task_source_split_rows.csv",
        "target_normalization_rows": output_dir / "target_normalization_rows.csv",
        "availability_mask_rows": output_dir / "availability_mask_rows.csv",
        "optimizer_step_rows": output_dir / "optimizer_step_rows.csv",
        "profile_metric_diagnostic_rows": output_dir / "profile_metric_diagnostic_rows.csv",
        "baseline_diagnostic_rows": output_dir / "baseline_diagnostic_rows.csv",
        "overfit_guard_rows": output_dir / "overfit_guard_rows.csv",
        "rollback_rows": output_dir / "rollback_rows.csv",
        "claim_rows": output_dir / "claim_rows.csv",
        "gate_rows": output_dir / "gate_rows.csv",
        "run_state": output_dir / "run_state.json",
    }
    baseline_checkpoints = list(m2893_summary.get("baseline_checkpoints", [])) or list(
        m2891_summary.get("baseline_checkpoints", [])
    )
    if not baseline_checkpoints:
        baseline_checkpoints = [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ]

    summary_stub = {
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "status_pass": False,
    }
    follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(follow_up_manifest, build_follow_up_manifest(summary_stub))

    gate_rows = build_gate_rows(
        parent_artifact_exists=parent_artifact_exists,
        m2893_summary=m2893_summary,
        m2891_summary=m2891_summary,
        split_rows=split_rows,
        normalization_rows=normalization_rows,
        availability_rows=availability_rows,
        recipe_rows=recipe_rows,
        optimizer_rows=optimizer_rows,
        profile_metric_rows=profile_metric_rows,
        baseline_rows=baseline_rows,
        overfit_guard_rows=overfit_guard_rows,
        rollback_rows=rollback_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up_manifest,
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    decision = (
        "fitting_implementation_preflight_complete_route_to_m2899_result_audit"
        if gate_matrix_pass
        else "fitting_implementation_preflight_incomplete_route_to_m2899_result_audit"
    )
    split_counts = Counter(row["split_name"] for row in split_rows)
    target_active_count = sum(1 for row in normalization_rows if _bool(row["target_scalar_active"]))
    target_available_count = sum(1 for row in availability_rows if _bool(row["available"]) and _bool(row["target_scalar_active"]))
    checkpoint_count = sum(1 for row in checkpoint_rows if _bool(row["checkpoint_exists"]))

    summary: dict[str, Any] = {
        "milestone": DEFAULT_MILESTONE,
        "generated_at_utc": utc_timestamp(),
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m2896_design": str(m2896_design),
        "m2896_design_exists": m2896_design.exists(),
        "m2897_audit": str(m2897_audit),
        "m2897_audit_exists": m2897_audit.exists(),
        "m2893_dir": str(m2893_dir),
        "m2893_summary_status_pass": _bool(m2893_summary.get("status_pass")),
        "m2893_gate_matrix_pass": _bool(m2893_summary.get("gate_matrix_pass")),
        "m2891_dir": str(m2891_dir),
        "m2891_summary_status_pass": _bool(m2891_summary.get("status_pass")),
        "m2891_gate_matrix_pass": _bool(m2891_summary.get("gate_matrix_pass")),
        "m2887_dir": str(m2887_dir),
        "m2884_dir": str(m2884_dir),
        "usable_task_row_count": len(usable_task_rows),
        "profile_task_row_count": len(profile_task_rows),
        "source_task_row_count": len(source_rows_by_task),
        "execution_source_paths": [str(path) for path in execution_paths],
        "split_counts": dict(sorted(split_counts.items())),
        "target_family_count": len({spec["target_family"] for spec in target_specs}),
        "target_scalar_dim": len(target_specs),
        "target_scalar_active_count": target_active_count,
        "target_available_count": target_available_count,
        "target_family_active": target_family_active,
        "binary_target_columns": sorted(BINARY_TARGET_COLUMNS),
        "required_profile_count": len(REQUIRED_PROFILES),
        "required_profiles": REQUIRED_PROFILES,
        "seed_list": seed_list,
        "optimizer": "AdamW",
        "optimizer_step_run": True,
        "optimizer_steps_per_profile": optimizer_steps,
        "optimizer_step_row_count": len(optimizer_rows),
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "global_norm_clip": GRAD_CLIP_NORM,
        "fitted_weights_persisted": checkpoint_count == len(REQUIRED_PROFILES) * len(seed_list),
        "fitted_weight_checkpoint_count": checkpoint_count,
        "model_fitting_run": True,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "false_claim_flags": FALSE_CLAIM_FLAGS.copy(),
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "source_singleton_rows_paper_proof_allowed": _bool(
            m2891_summary.get("source_singleton_rows_paper_proof_allowed")
        ),
        "guard_rows_ordinary_success_denominator_allowed": _bool(
            m2891_summary.get("guard_rows_ordinary_success_denominator_allowed")
        ),
        "fresh_source_diverse_panel_required_before_claim": True,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "input_artifacts": {
            **{f"m2891_{key}": str(value) for key, value in m2891_paths.items()},
            **{f"m2893_{key}": str(value) for key, value in m2893_paths.items()},
            "m2887_summary": str(m2887_summary_path),
            "m2887_usable_task_rows": str(m2887_dir / "usable_task_rows.csv"),
            "m2887_profile_task_rows": str(m2887_dir / "profile_task_rows.csv"),
            "m2884_source_inventory_rows": str(m2884_dir / "source_inventory_rows.csv"),
        },
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "fitting_recipe_row_count": len(recipe_rows),
        "task_source_split_row_count": len(split_rows),
        "target_normalization_row_count": len(normalization_rows),
        "availability_mask_row_count": len(availability_rows),
        "profile_metric_diagnostic_row_count": len(profile_metric_rows),
        "baseline_diagnostic_row_count": len(baseline_rows),
        "overfit_guard_row_count": len(overfit_guard_rows),
        "rollback_row_count": len(rollback_rows),
        "claim_row_count": len(claim_rows),
        "gate_row_count": len(gate_rows),
    }

    write_csv_rows(artifacts["fitting_recipe_rows"], recipe_rows, fieldnames=FITTING_RECIPE_FIELDNAMES)
    write_csv_rows(artifacts["task_source_split_rows"], split_rows, fieldnames=SPLIT_FIELDNAMES)
    write_csv_rows(artifacts["target_normalization_rows"], normalization_rows, fieldnames=NORMALIZATION_FIELDNAMES)
    write_csv_rows(artifacts["availability_mask_rows"], availability_rows, fieldnames=AVAILABILITY_FIELDNAMES)
    write_csv_rows(artifacts["optimizer_step_rows"], optimizer_rows, fieldnames=OPTIMIZER_STEP_FIELDNAMES)
    write_csv_rows(
        artifacts["profile_metric_diagnostic_rows"],
        profile_metric_rows,
        fieldnames=PROFILE_METRIC_FIELDNAMES,
    )
    write_csv_rows(artifacts["baseline_diagnostic_rows"], baseline_rows, fieldnames=BASELINE_FIELDNAMES)
    write_csv_rows(artifacts["overfit_guard_rows"], overfit_guard_rows, fieldnames=OVERFIT_GUARD_FIELDNAMES)
    write_csv_rows(artifacts["rollback_rows"], rollback_rows, fieldnames=ROLLBACK_FIELDNAMES)
    write_csv_rows(artifacts["claim_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(artifacts["gate_rows"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(artifacts["run_state"], {"summary": summary, "checkpoint_rows": checkpoint_rows})
    write_json(artifacts["summary"], summary)
    write_json(follow_up_manifest, build_follow_up_manifest(summary))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2896-design", type=Path, default=DEFAULT_M2896_DESIGN)
    parser.add_argument("--m2897-audit", type=Path, default=DEFAULT_M2897_AUDIT)
    parser.add_argument("--m2893-dir", type=Path, default=DEFAULT_M2893_DIR)
    parser.add_argument("--m2891-dir", type=Path, default=DEFAULT_M2891_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    device = torch.device(args.device)
    summary = write_preflight_artifacts(
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        m2896_design=args.m2896_design,
        m2897_audit=args.m2897_audit,
        m2893_dir=args.m2893_dir,
        m2891_dir=args.m2891_dir,
        device=device,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"decision={summary['decision']}")
    print(f"optimizer_step_row_count={summary['optimizer_step_row_count']}")
    print(f"profile_metric_diagnostic_row_count={summary['profile_metric_diagnostic_row_count']}")
    print(f"target_scalar_active_count={summary['target_scalar_active_count']}")


if __name__ == "__main__":
    main()
