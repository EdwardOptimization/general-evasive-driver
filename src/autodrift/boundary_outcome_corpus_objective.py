"""Reusable boundary-outcome corpus and objective-only sanity checks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.matched_history_intervention_gate import (
    deterministic_action_from_hidden,
    requested_snapshot_steps,
)
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots
from autodrift.snapshot_bank_relocation import _outcome_intervention_weight
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


REQUIRED_BOUNDARY_ROW_COLUMNS = (
    "variant",
    "accepted",
    "checkpoint_label",
    "target",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
    "normal_margin",
    "variant_margin",
    "normal_success",
    "variant_success",
    "success_drop",
    "margin_gap",
    "normal_first_steer",
    "normal_first_throttle",
    "normal_first_brake",
)
REQUIRED_CORPUS_ARRAYS = (
    "observation",
    "preferred_hidden",
    "rejected_hidden",
    "preferred_action",
    "weight",
    "preferred_score",
    "rejected_score",
    "score_delta",
    "group_index",
    "target_index",
)
STUDENT_INPUT_ARRAYS = ("observation", "preferred_hidden", "rejected_hidden")
TRAINING_LABEL_ARRAYS = ("preferred_score", "rejected_score", "score_delta", "weight")
TRAINING_METADATA_ARRAYS = ("group_index", "target_index")


@dataclass(frozen=True)
class BoundaryOutcomeCorpusContract:
    rows: int
    obs_dim: int
    hidden_dim: int
    act_dim: int
    groups: int
    targets: int
    student_input_arrays: tuple[str, ...]
    training_label_arrays: tuple[str, ...]
    training_metadata_arrays: tuple[str, ...]


@dataclass(frozen=True)
class GroupSplit:
    train_indices: np.ndarray
    val_indices: np.ndarray
    train_groups: np.ndarray
    val_groups: np.ndarray


class BoundaryOutcomeRiskRegressor(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features).squeeze(-1)


def parse_seed_list(value: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("optimization seeds must be comma-separated integers") from exc
    if not seeds:
        raise argparse.ArgumentTypeError("at least one optimization seed is required")
    return seeds


def physical_pair_key(row: pd.Series | dict[str, Any]) -> str:
    return "{left_seed}:{left_step}:{right_seed}:{right_step}".format(
        left_seed=int(row["left_seed"]),
        left_step=int(row["left_step"]),
        right_seed=int(row["right_seed"]),
        right_step=int(row["right_step"]),
    )


def boundary_geometry_key(row: pd.Series | dict[str, Any]) -> str:
    return "{pair}:{target}:{x:.6f}:{y:.6f}:{half_width:.6f}".format(
        pair=physical_pair_key(row),
        target=str(row["target"]),
        x=float(row["relocated_obstacle_body_x"]),
        y=float(row["relocated_obstacle_body_y"]),
        half_width=float(row["relocated_obstacle_half_width"]),
    )


def outcome_score(success: bool, margin: float, *, success_bonus: float, margin_clip: float) -> float:
    margin_value = float(margin)
    if not np.isfinite(margin_value):
        margin_value = -float(margin_clip)
    clipped_margin = float(np.clip(margin_value, -float(margin_clip), float(margin_clip)))
    return (float(success_bonus) if bool(success) else 0.0) + clipped_margin


def boundary_outcome_weight(
    *,
    normal_margin: float,
    wrong_margin: float,
    normal_success: bool,
    wrong_success: bool,
    min_margin_gap: float,
    boundary_margin_scale: float,
    success_drop_bonus: float,
) -> float:
    base = _outcome_intervention_weight(
        float(normal_margin),
        float(wrong_margin),
        bool(normal_success),
        min_margin_gap=float(min_margin_gap),
        boundary_margin_scale=float(boundary_margin_scale),
    )
    if base <= 0.0:
        return 0.0
    if bool(normal_success) and not bool(wrong_success):
        base += float(success_drop_bonus) * max(base, 1e-6)
    return float(base)


def validate_boundary_row_frame(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_BOUNDARY_ROW_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("boundary rows CSV is missing columns: " + ", ".join(missing))


def select_boundary_outcome_rows(
    frame: pd.DataFrame,
    *,
    checkpoint_label: str,
    accepted_only: bool,
    min_margin_gap: float,
    max_rows_per_physical_pair: int,
    max_rows_per_target: int,
) -> pd.DataFrame:
    validate_boundary_row_frame(frame)
    selected = frame[
        (frame["variant"].astype(str) == "wrong_matched_history")
        & (frame["checkpoint_label"].astype(str) == str(checkpoint_label))
    ].copy()
    if accepted_only:
        selected = selected[selected["accepted"].astype(bool)]
    selected = selected[np.isfinite(selected["margin_gap"].astype(float))]
    selected = selected[selected["margin_gap"].astype(float) >= float(min_margin_gap)]
    if selected.empty:
        return selected.reset_index(drop=True)
    selected["physical_pair_key"] = [physical_pair_key(row) for _, row in selected.iterrows()]
    selected["boundary_geometry_key"] = [boundary_geometry_key(row) for _, row in selected.iterrows()]
    selected["source_row_index"] = selected.index.astype(int)
    sort_columns = ["success_drop", "margin_gap", "normal_margin"]
    selected = selected.sort_values(sort_columns, ascending=[False, False, True])
    selected = selected.drop_duplicates("boundary_geometry_key", keep="first")
    if max_rows_per_physical_pair > 0:
        selected = (
            selected.groupby("physical_pair_key", observed=True, group_keys=False)
            .head(int(max_rows_per_physical_pair))
            .reset_index(drop=True)
        )
    if max_rows_per_target > 0:
        selected = (
            selected.groupby("target", observed=True, group_keys=False)
            .head(int(max_rows_per_target))
            .reset_index(drop=True)
        )
    return selected.reset_index(drop=True)


def _hidden_array(hidden: torch.Tensor) -> np.ndarray:
    return hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)


def _target_maps(rows: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:
    target_names = sorted(str(value) for value in rows["target"].unique())
    group_names = sorted(str(value) for value in rows["physical_pair_key"].unique())
    return (
        {name: index for index, name in enumerate(group_names)},
        {name: index for index, name in enumerate(target_names)},
    )


def build_boundary_outcome_examples(
    *,
    rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], Any],
    model: Any,
    device: torch.device,
    min_margin_gap: float,
    boundary_margin_scale: float,
    success_drop_bonus: float,
    success_bonus: float,
    margin_clip: float,
) -> list[dict[str, Any]]:
    if rows.empty:
        return []
    group_to_index, target_to_index = _target_maps(rows)
    examples: list[dict[str, Any]] = []
    for row_id, row in rows.reset_index(drop=True).iterrows():
        left_key = (int(row["left_seed"]), int(row["left_step"]))
        right_key = (int(row["right_seed"]), int(row["right_step"]))
        if left_key not in snapshots or right_key not in snapshots:
            raise ValueError(f"missing snapshots for boundary row {row_id}")
        left = snapshots[left_key]
        right = snapshots[right_key]
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        action, _ = deterministic_action_from_hidden(
            model,
            np.asarray(relocated.observation, dtype=np.float32),
            relocated.hidden,
            device,
        )
        csv_action = np.asarray(
            [row["normal_first_steer"], row["normal_first_throttle"], row["normal_first_brake"]],
            dtype=np.float32,
        )
        action_error = float(np.linalg.norm(action - csv_action)) if np.all(np.isfinite(csv_action)) else float("nan")
        normal_margin = float(row["normal_margin"])
        wrong_margin = float(row["variant_margin"])
        normal_success = bool(row["normal_success"])
        wrong_success = bool(row["variant_success"])
        preferred_score = outcome_score(
            normal_success,
            normal_margin,
            success_bonus=success_bonus,
            margin_clip=margin_clip,
        )
        rejected_score = outcome_score(
            wrong_success,
            wrong_margin,
            success_bonus=success_bonus,
            margin_clip=margin_clip,
        )
        weight = boundary_outcome_weight(
            normal_margin=normal_margin,
            wrong_margin=wrong_margin,
            normal_success=normal_success,
            wrong_success=wrong_success,
            min_margin_gap=min_margin_gap,
            boundary_margin_scale=boundary_margin_scale,
            success_drop_bonus=success_drop_bonus,
        )
        if weight <= 0.0:
            continue
        physical_key = str(row["physical_pair_key"])
        geometry_key = str(row["boundary_geometry_key"])
        target = str(row["target"])
        examples.append(
            {
                "row_id": int(row_id),
                "source_row_index": int(row.get("source_row_index", row_id)),
                "candidate_id": int(row.get("candidate_id", -1)),
                "source_pair_id": int(row.get("source_pair_id", -1)),
                "checkpoint_label": str(row["checkpoint_label"]),
                "target": target,
                "target_index": int(target_to_index[target]),
                "physical_pair_key": physical_key,
                "boundary_geometry_key": geometry_key,
                "group_index": int(group_to_index[physical_key]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "normal_margin": normal_margin,
                "wrong_history_margin": wrong_margin,
                "margin_gap": float(row["margin_gap"]),
                "normal_success": normal_success,
                "wrong_history_success": wrong_success,
                "success_drop": bool(row["success_drop"]),
                "preferred_score": float(preferred_score),
                "rejected_score": float(rejected_score),
                "score_delta": float(preferred_score - rejected_score),
                "weight": float(weight),
                "action_reconstruction_error": action_error,
                "student_input_contract": "observation plus deployable recurrent hidden states",
                "observation": np.asarray(relocated.observation, dtype=np.float32).copy(),
                "preferred_hidden": _hidden_array(relocated.hidden),
                "rejected_hidden": _hidden_array(right.hidden),
                "preferred_action": np.asarray(action, dtype=np.float32).copy(),
            }
        )
    return examples


def boundary_outcome_corpus_arrays(examples: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not examples:
        return {}
    return {
        "observation": np.stack([example["observation"] for example in examples]).astype(np.float32),
        "preferred_hidden": np.stack([example["preferred_hidden"] for example in examples]).astype(np.float32),
        "rejected_hidden": np.stack([example["rejected_hidden"] for example in examples]).astype(np.float32),
        "preferred_action": np.stack([example["preferred_action"] for example in examples]).astype(np.float32),
        "weight": np.asarray([example["weight"] for example in examples], dtype=np.float32),
        "preferred_score": np.asarray([example["preferred_score"] for example in examples], dtype=np.float32),
        "rejected_score": np.asarray([example["rejected_score"] for example in examples], dtype=np.float32),
        "score_delta": np.asarray([example["score_delta"] for example in examples], dtype=np.float32),
        "group_index": np.asarray([example["group_index"] for example in examples], dtype=np.int64),
        "target_index": np.asarray([example["target_index"] for example in examples], dtype=np.int64),
    }


def boundary_outcome_metadata(examples: list[dict[str, Any]]) -> pd.DataFrame:
    tensor_keys = {"observation", "preferred_hidden", "rejected_hidden", "preferred_action"}
    return pd.DataFrame([{key: value for key, value in example.items() if key not in tensor_keys} for example in examples])


def validate_corpus_arrays(arrays: dict[str, np.ndarray]) -> BoundaryOutcomeCorpusContract:
    missing = [key for key in REQUIRED_CORPUS_ARRAYS if key not in arrays]
    if missing:
        raise ValueError("boundary-outcome corpus is missing arrays: " + ", ".join(missing))
    observation = arrays["observation"]
    preferred_hidden = arrays["preferred_hidden"]
    rejected_hidden = arrays["rejected_hidden"]
    preferred_action = arrays["preferred_action"]
    weight = arrays["weight"]
    preferred_score = arrays["preferred_score"]
    rejected_score = arrays["rejected_score"]
    score_delta = arrays["score_delta"]
    group_index = arrays["group_index"]
    target_index = arrays["target_index"]
    if observation.ndim != 2:
        raise ValueError("observation must be a 2D array")
    if preferred_hidden.shape != rejected_hidden.shape or preferred_hidden.ndim != 2:
        raise ValueError("preferred_hidden and rejected_hidden must be matching 2D arrays")
    if preferred_action.ndim != 2:
        raise ValueError("preferred_action must be a 2D array")
    rows = int(observation.shape[0])
    if rows < 4:
        raise ValueError("boundary-outcome corpus requires at least four rows")
    for key, array in (
        ("preferred_hidden", preferred_hidden),
        ("rejected_hidden", rejected_hidden),
        ("preferred_action", preferred_action),
    ):
        if array.shape[0] != rows:
            raise ValueError(f"{key} row count must match observation")
    for key, array in (
        ("weight", weight),
        ("preferred_score", preferred_score),
        ("rejected_score", rejected_score),
        ("score_delta", score_delta),
        ("group_index", group_index),
        ("target_index", target_index),
    ):
        if array.shape != (rows,):
            raise ValueError(f"{key} must have shape ({rows},)")
    for key in STUDENT_INPUT_ARRAYS + TRAINING_LABEL_ARRAYS:
        if not np.all(np.isfinite(arrays[key])):
            raise ValueError(f"{key} contains non-finite values")
    if np.any(weight < 0.0) or float(np.max(weight)) <= 0.0:
        raise ValueError("weight must contain at least one positive non-negative value")
    if not np.all(score_delta > 0.0):
        raise ValueError("all boundary-outcome rows must prefer normal history")
    groups = int(np.unique(group_index).size)
    targets = int(np.unique(target_index).size)
    if groups < 2:
        raise ValueError("boundary-outcome corpus requires at least two physical groups")
    return BoundaryOutcomeCorpusContract(
        rows=rows,
        obs_dim=int(observation.shape[1]),
        hidden_dim=int(preferred_hidden.shape[1]),
        act_dim=int(preferred_action.shape[1]),
        groups=groups,
        targets=targets,
        student_input_arrays=STUDENT_INPUT_ARRAYS,
        training_label_arrays=TRAINING_LABEL_ARRAYS,
        training_metadata_arrays=TRAINING_METADATA_ARRAYS,
    )


def load_corpus_npz(path: Path) -> dict[str, np.ndarray]:
    loaded = np.load(path)
    arrays = {key: loaded[key] for key in loaded.files}
    validate_corpus_arrays(arrays)
    return arrays


def split_groups(group_index: np.ndarray, train_fraction: float, seed: int) -> GroupSplit:
    groups = np.unique(group_index.astype(np.int64))
    if groups.size < 4:
        raise ValueError("at least four physical groups are required for train/validation split")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(groups)
    train_count = int(round(groups.size * train_fraction))
    train_count = min(max(train_count, 1), groups.size - 1)
    train_groups = np.sort(shuffled[:train_count])
    val_groups = np.sort(shuffled[train_count:])
    train_mask = np.isin(group_index, train_groups)
    val_mask = np.isin(group_index, val_groups)
    return GroupSplit(
        train_indices=np.nonzero(train_mask)[0],
        val_indices=np.nonzero(val_mask)[0],
        train_groups=train_groups,
        val_groups=val_groups,
    )


def _normalization(arrays: dict[str, np.ndarray], train_indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_features = np.concatenate(
        [
            _features(arrays["observation"][train_indices], arrays["preferred_hidden"][train_indices]),
            _features(arrays["observation"][train_indices], arrays["rejected_hidden"][train_indices]),
        ],
        axis=0,
    )
    train_scores = np.concatenate(
        [
            arrays["preferred_score"][train_indices],
            arrays["rejected_score"][train_indices],
        ],
        axis=0,
    ).reshape(-1, 1)
    feature_mean = train_features.mean(axis=0, keepdims=True).astype(np.float32)
    feature_std = (train_features.std(axis=0, keepdims=True) + 1e-6).astype(np.float32)
    target_mean = train_scores.mean(axis=0, keepdims=True).astype(np.float32)
    target_std = (train_scores.std(axis=0, keepdims=True) + 1e-6).astype(np.float32)
    return feature_mean, feature_std, target_mean, target_std


def _features(observation: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    return np.concatenate([observation.astype(np.float32), hidden.astype(np.float32)], axis=1)


def _torch_batch(
    arrays: dict[str, np.ndarray],
    indices: np.ndarray,
    feature_mean: np.ndarray,
    feature_std: np.ndarray,
    target_mean: np.ndarray,
    target_std: np.ndarray,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    preferred_features = (_features(arrays["observation"][indices], arrays["preferred_hidden"][indices]) - feature_mean) / feature_std
    rejected_features = (_features(arrays["observation"][indices], arrays["rejected_hidden"][indices]) - feature_mean) / feature_std
    preferred_score = (arrays["preferred_score"][indices].reshape(-1, 1) - target_mean) / target_std
    rejected_score = (arrays["rejected_score"][indices].reshape(-1, 1) - target_mean) / target_std
    weights = arrays["weight"][indices].astype(np.float32)
    weights = weights / max(float(weights.mean()), 1e-6)
    return {
        "x_preferred": torch.as_tensor(preferred_features, dtype=torch.float32, device=device),
        "x_rejected": torch.as_tensor(rejected_features, dtype=torch.float32, device=device),
        "y_preferred": torch.as_tensor(preferred_score.reshape(-1), dtype=torch.float32, device=device),
        "y_rejected": torch.as_tensor(rejected_score.reshape(-1), dtype=torch.float32, device=device),
        "weights": torch.as_tensor(weights, dtype=torch.float32, device=device),
    }


def _weighted_mean(values: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    return (values * weights).sum() / weights.sum().clamp_min(1e-6)


def _loss_components(
    pred_preferred: torch.Tensor,
    pred_rejected: torch.Tensor,
    y_preferred: torch.Tensor,
    y_rejected: torch.Tensor,
    weights: torch.Tensor,
    delta_loss_coef: float,
    rank_loss_coef: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    score_loss_values = 0.5 * (
        torch.square(pred_preferred - y_preferred) + torch.square(pred_rejected - y_rejected)
    )
    target_delta = y_preferred - y_rejected
    pred_delta = pred_preferred - pred_rejected
    delta_loss_values = torch.square(pred_delta - target_delta)
    rank_loss_values = torch.nn.functional.softplus(-pred_delta)
    score_loss = _weighted_mean(score_loss_values, weights)
    delta_loss = _weighted_mean(delta_loss_values, weights)
    rank_loss = _weighted_mean(rank_loss_values, weights)
    combined_loss = score_loss + float(delta_loss_coef) * delta_loss + float(rank_loss_coef) * rank_loss
    pairwise_accuracy = (pred_delta > 0.0).to(torch.float32).mean()
    metrics = {
        "combined_loss": float(combined_loss.detach().cpu().item()),
        "score_loss": float(score_loss.detach().cpu().item()),
        "delta_loss": float(delta_loss.detach().cpu().item()),
        "rank_loss": float(rank_loss.detach().cpu().item()),
        "pairwise_accuracy": float(pairwise_accuracy.detach().cpu().item()),
        "mean_pred_delta": float(pred_delta.detach().cpu().mean().item()),
        "mean_target_delta": float(target_delta.detach().cpu().mean().item()),
    }
    return combined_loss, metrics


def evaluate_model(
    model: BoundaryOutcomeRiskRegressor | None,
    batch: dict[str, torch.Tensor],
    *,
    delta_loss_coef: float,
    rank_loss_coef: float,
) -> dict[str, float]:
    with torch.no_grad():
        if model is None:
            pred_preferred = torch.zeros_like(batch["y_preferred"])
            pred_rejected = torch.zeros_like(batch["y_rejected"])
        else:
            model.eval()
            pred_preferred = model(batch["x_preferred"])
            pred_rejected = model(batch["x_rejected"])
        _, metrics = _loss_components(
            pred_preferred=pred_preferred,
            pred_rejected=pred_rejected,
            y_preferred=batch["y_preferred"],
            y_rejected=batch["y_rejected"],
            weights=batch["weights"],
            delta_loss_coef=delta_loss_coef,
            rank_loss_coef=rank_loss_coef,
        )
    return metrics


def train_one_seed(
    arrays: dict[str, np.ndarray],
    *,
    optimization_seed: int,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    delta_loss_coef: float,
    rank_loss_coef: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = validate_corpus_arrays(arrays)
    split = split_groups(arrays["group_index"], train_fraction=train_fraction, seed=optimization_seed)
    feature_mean, feature_std, target_mean, target_std = _normalization(arrays, split.train_indices)
    train_batch = _torch_batch(arrays, split.train_indices, feature_mean, feature_std, target_mean, target_std, device)
    val_batch = _torch_batch(arrays, split.val_indices, feature_mean, feature_std, target_mean, target_std, device)

    torch.manual_seed(int(optimization_seed))
    rng = np.random.default_rng(int(optimization_seed))
    model = BoundaryOutcomeRiskRegressor(
        input_dim=contract.obs_dim + contract.hidden_dim,
        hidden_dim=int(hidden_dim),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    rows: list[dict[str, Any]] = []
    for phase, model_for_eval in (("constant", None), ("before", model)):
        for split_name, batch in (("train", train_batch), ("val", val_batch)):
            rows.append(
                {
                    "optimization_seed": int(optimization_seed),
                    "phase": phase,
                    "split": split_name,
                    "rows": int(batch["weights"].shape[0]),
                    **evaluate_model(
                        model_for_eval,
                        batch,
                        delta_loss_coef=delta_loss_coef,
                        rank_loss_coef=rank_loss_coef,
                    ),
                }
            )

    for _ in range(max(0, int(steps))):
        sampled = rng.choice(
            split.train_indices,
            size=min(int(batch_size), len(split.train_indices)),
            replace=len(split.train_indices) < int(batch_size),
        )
        batch = _torch_batch(arrays, sampled, feature_mean, feature_std, target_mean, target_std, device)
        model.train()
        pred_preferred = model(batch["x_preferred"])
        pred_rejected = model(batch["x_rejected"])
        loss, _ = _loss_components(
            pred_preferred=pred_preferred,
            pred_rejected=pred_rejected,
            y_preferred=batch["y_preferred"],
            y_rejected=batch["y_rejected"],
            weights=batch["weights"],
            delta_loss_coef=delta_loss_coef,
            rank_loss_coef=rank_loss_coef,
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

    for split_name, batch in (("train", train_batch), ("val", val_batch)):
        rows.append(
            {
                "optimization_seed": int(optimization_seed),
                "phase": "after",
                "split": split_name,
                "rows": int(batch["weights"].shape[0]),
                **evaluate_model(
                    model,
                    batch,
                    delta_loss_coef=delta_loss_coef,
                    rank_loss_coef=rank_loss_coef,
                ),
            }
        )

    seed_summary = summarize_seed(rows, int(optimization_seed))
    seed_summary.update(
        {
            "train_rows": int(len(split.train_indices)),
            "val_rows": int(len(split.val_indices)),
            "train_groups": int(len(split.train_groups)),
            "val_groups": int(len(split.val_groups)),
            "feature_dim": int(contract.obs_dim + contract.hidden_dim),
        }
    )
    return rows, seed_summary


def _row_by_phase(rows: list[dict[str, Any]], optimization_seed: int, phase: str, split: str) -> dict[str, Any]:
    matches = [
        row for row in rows
        if int(row["optimization_seed"]) == int(optimization_seed)
        and str(row["phase"]) == str(phase)
        and str(row["split"]) == str(split)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one row for seed={optimization_seed} phase={phase} split={split}")
    return matches[0]


def summarize_seed(rows: list[dict[str, Any]], optimization_seed: int) -> dict[str, Any]:
    before_val = _row_by_phase(rows, optimization_seed, "before", "val")
    after_val = _row_by_phase(rows, optimization_seed, "after", "val")
    before_train = _row_by_phase(rows, optimization_seed, "before", "train")
    after_train = _row_by_phase(rows, optimization_seed, "after", "train")
    summary = {
        "optimization_seed": int(optimization_seed),
        "train_combined_loss_improvement": float(before_train["combined_loss"] - after_train["combined_loss"]),
        "train_score_loss_improvement": float(before_train["score_loss"] - after_train["score_loss"]),
        "train_delta_loss_improvement": float(before_train["delta_loss"] - after_train["delta_loss"]),
        "train_rank_loss_improvement": float(before_train["rank_loss"] - after_train["rank_loss"]),
        "train_pairwise_accuracy_improvement": float(
            after_train["pairwise_accuracy"] - before_train["pairwise_accuracy"]
        ),
        "val_combined_loss_improvement": float(before_val["combined_loss"] - after_val["combined_loss"]),
        "val_score_loss_improvement": float(before_val["score_loss"] - after_val["score_loss"]),
        "val_delta_loss_improvement": float(before_val["delta_loss"] - after_val["delta_loss"]),
        "val_rank_loss_improvement": float(before_val["rank_loss"] - after_val["rank_loss"]),
        "val_pairwise_accuracy_before": float(before_val["pairwise_accuracy"]),
        "val_pairwise_accuracy_after": float(after_val["pairwise_accuracy"]),
        "val_pairwise_accuracy_improvement": float(after_val["pairwise_accuracy"] - before_val["pairwise_accuracy"]),
    }
    summary["objective_seed_pass"] = bool(
        summary["val_combined_loss_improvement"] > 0.0
        and summary["val_delta_loss_improvement"] > 0.0
        and summary["val_pairwise_accuracy_after"] >= 0.60
    )
    return summary


def summarize_corpus(
    *,
    checkpoint_label: str,
    boundary_rows_csv: Path,
    selected_rows: pd.DataFrame,
    metadata: pd.DataFrame,
    arrays: dict[str, np.ndarray],
    min_margin_gap: float,
    max_rows_per_physical_pair: int,
    max_rows_per_target: int,
) -> dict[str, Any]:
    contract = validate_corpus_arrays(arrays)
    max_rows_per_pair = int(metadata["physical_pair_key"].value_counts().max()) if len(metadata) else 0
    max_rows_per_geometry = int(metadata["boundary_geometry_key"].value_counts().max()) if len(metadata) else 0
    action_errors = metadata["action_reconstruction_error"].astype(float) if "action_reconstruction_error" in metadata else pd.Series(dtype=float)
    finite_action_errors = action_errors[np.isfinite(action_errors)]
    return {
        "run_type": "boundary_outcome_corpus",
        "checkpoint_label": str(checkpoint_label),
        "boundary_rows_csv": str(boundary_rows_csv),
        "input_rows": int(len(selected_rows)),
        "corpus_rows": int(contract.rows),
        "obs_dim": int(contract.obs_dim),
        "hidden_dim": int(contract.hidden_dim),
        "act_dim": int(contract.act_dim),
        "physical_pairs": int(contract.groups),
        "unique_boundary_geometries": int(metadata["boundary_geometry_key"].nunique()) if len(metadata) else 0,
        "targets": int(contract.targets),
        "target_counts": metadata["target"].value_counts().sort_index().to_dict() if len(metadata) else {},
        "success_drop_rows": int(metadata["success_drop"].astype(bool).sum()) if len(metadata) else 0,
        "mean_margin_gap": float(metadata["margin_gap"].astype(float).mean()) if len(metadata) else 0.0,
        "max_margin_gap": float(metadata["margin_gap"].astype(float).max()) if len(metadata) else 0.0,
        "mean_score_delta": float(np.mean(arrays["score_delta"])),
        "min_score_delta": float(np.min(arrays["score_delta"])),
        "weight_sum": float(np.sum(arrays["weight"])),
        "max_rows_per_physical_pair": max_rows_per_pair,
        "max_rows_per_physical_pair_fraction": float(max_rows_per_pair / max(contract.rows, 1)),
        "max_rows_per_boundary_geometry": max_rows_per_geometry,
        "selection_min_margin_gap": float(min_margin_gap),
        "selection_max_rows_per_physical_pair": int(max_rows_per_physical_pair),
        "selection_max_rows_per_target": int(max_rows_per_target),
        "selected_source_rows": int(selected_rows["source_row_index"].nunique()) if len(selected_rows) else 0,
        "student_input_arrays_used": list(contract.student_input_arrays),
        "training_label_arrays_not_actor_inputs": list(contract.training_label_arrays),
        "training_metadata_arrays_not_actor_inputs": list(contract.training_metadata_arrays),
        "actor_contract": (
            "student features are human-view observation and recurrent hidden states reconstructed from "
            "deployable P0 command-response history; relocated outcomes are labels only"
        ),
        "action_reconstruction_error_max": (
            float(finite_action_errors.max()) if len(finite_action_errors) else None
        ),
        "action_reconstruction_error_mean": (
            float(finite_action_errors.mean()) if len(finite_action_errors) else None
        ),
    }


def summarize_objective_run(
    *,
    corpus_npz: Path,
    arrays: dict[str, np.ndarray],
    seed_summaries: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    contract = validate_corpus_arrays(arrays)
    combined = np.asarray([row["val_combined_loss_improvement"] for row in seed_summaries], dtype=np.float32)
    delta = np.asarray([row["val_delta_loss_improvement"] for row in seed_summaries], dtype=np.float32)
    accuracy = np.asarray([row["val_pairwise_accuracy_after"] for row in seed_summaries], dtype=np.float32)
    objective_pass = bool(
        len(seed_summaries) >= 3
        and all(bool(row["objective_seed_pass"]) for row in seed_summaries)
        and float(np.min(combined)) > 0.0
        and float(np.min(delta)) > 0.0
        and float(np.mean(accuracy)) >= 0.60
    )
    return {
        "run_type": "boundary_outcome_objective_sanity",
        "corpus_npz": str(corpus_npz),
        "optimization_seeds": list(args.optimization_seeds),
        "rows": int(contract.rows),
        "physical_groups": int(contract.groups),
        "targets": int(contract.targets),
        "student_input_arrays_used": list(contract.student_input_arrays),
        "training_label_arrays_not_actor_inputs": list(contract.training_label_arrays),
        "train_fraction": float(args.train_fraction),
        "steps": int(args.steps),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "weight_decay": float(args.weight_decay),
        "hidden_dim": int(args.hidden_dim),
        "delta_loss_coef": float(args.delta_loss_coef),
        "rank_loss_coef": float(args.rank_loss_coef),
        "mean_val_combined_loss_improvement": float(np.mean(combined)),
        "min_val_combined_loss_improvement": float(np.min(combined)),
        "mean_val_delta_loss_improvement": float(np.mean(delta)),
        "min_val_delta_loss_improvement": float(np.min(delta)),
        "mean_val_pairwise_accuracy_after": float(np.mean(accuracy)),
        "min_val_pairwise_accuracy_after": float(np.min(accuracy)),
        "seed_pass_count": int(sum(bool(row["objective_seed_pass"]) for row in seed_summaries)),
        "objective_pass": objective_pass,
        "admission_decision": (
            "admit_for_guarded_actor_update_design"
            if objective_pass
            else "do_not_admit_actor_update_until_objective_signal_is_reliable"
        ),
    }


def run_corpus_build(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, np.ndarray], pd.DataFrame]:
    if len(args.checkpoint_policy) != 1:
        raise ValueError("build exactly one checkpoint corpus per run to avoid mixing hidden-state spaces")
    checkpoint_spec: CheckpointSpec = args.checkpoint_policy[0]
    run_dir = args.run_dir or make_run_dir(prefix="m162_boundary_outcome_corpus")
    args.run_dir = run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(args.device)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    env_config = load_env_config(args.env_config)
    boundary_frame = pd.read_csv(args.boundary_rows_csv)
    selected_rows = select_boundary_outcome_rows(
        boundary_frame,
        checkpoint_label=checkpoint_spec.label,
        accepted_only=not args.include_unaccepted_rows,
        min_margin_gap=args.min_margin_gap,
        max_rows_per_physical_pair=args.max_rows_per_physical_pair,
        max_rows_per_target=args.max_rows_per_target,
    )
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=requested_snapshot_steps(selected_rows, delay_steps=args.delay_steps),
        device=resolved_device,
    )
    examples = build_boundary_outcome_examples(
        rows=selected_rows,
        snapshots=snapshots,
        model=model,
        device=resolved_device,
        min_margin_gap=args.min_margin_gap,
        boundary_margin_scale=args.boundary_margin_scale,
        success_drop_bonus=args.success_drop_bonus,
        success_bonus=args.success_bonus,
        margin_clip=args.margin_clip,
    )
    arrays = boundary_outcome_corpus_arrays(examples)
    metadata = boundary_outcome_metadata(examples)
    validate_corpus_arrays(arrays)

    selected_rows.to_csv(run_dir / "selected_boundary_rows.csv", index=False)
    metadata.to_csv(run_dir / "boundary_outcome_corpus.csv", index=False)
    np.savez_compressed(run_dir / "boundary_outcome_corpus.npz", **arrays)
    corpus_summary = summarize_corpus(
        checkpoint_label=checkpoint_spec.label,
        boundary_rows_csv=args.boundary_rows_csv,
        selected_rows=selected_rows,
        metadata=metadata,
        arrays=arrays,
        min_margin_gap=args.min_margin_gap,
        max_rows_per_physical_pair=args.max_rows_per_physical_pair,
        max_rows_per_target=args.max_rows_per_target,
    )
    write_json(run_dir / "corpus_summary.json", corpus_summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "boundary_outcome_corpus_objective",
            "checkpoint": {"label": checkpoint_spec.label, "path": checkpoint_spec.path},
            "env_config": args.env_config,
            "boundary_rows_csv": args.boundary_rows_csv,
            "device": str(resolved_device),
            "delay_steps": int(args.delay_steps),
            "include_unaccepted_rows": bool(args.include_unaccepted_rows),
            "min_margin_gap": float(args.min_margin_gap),
            "boundary_margin_scale": float(args.boundary_margin_scale),
            "success_drop_bonus": float(args.success_drop_bonus),
            "success_bonus": float(args.success_bonus),
            "margin_clip": float(args.margin_clip),
            "artifacts": {
                "selected_boundary_rows_csv": run_dir / "selected_boundary_rows.csv",
                "boundary_outcome_corpus_csv": run_dir / "boundary_outcome_corpus.csv",
                "boundary_outcome_corpus_npz": run_dir / "boundary_outcome_corpus.npz",
                "corpus_summary_json": run_dir / "corpus_summary.json",
            },
        },
    )
    return corpus_summary, arrays, metadata


def run_objective_sanity(args: argparse.Namespace, arrays: dict[str, np.ndarray] | None = None) -> dict[str, Any]:
    corpus_npz = args.corpus_npz or (args.run_dir / "boundary_outcome_corpus.npz")
    if arrays is None:
        arrays = load_corpus_npz(corpus_npz)
    device = torch.device(args.objective_device)
    all_loss_rows: list[dict[str, Any]] = []
    seed_summaries: list[dict[str, Any]] = []
    for optimization_seed in args.optimization_seeds:
        rows, seed_summary = train_one_seed(
            arrays,
            optimization_seed=int(optimization_seed),
            train_fraction=args.train_fraction,
            steps=args.steps,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            hidden_dim=args.hidden_dim,
            delta_loss_coef=args.delta_loss_coef,
            rank_loss_coef=args.rank_loss_coef,
            device=device,
        )
        all_loss_rows.extend(rows)
        seed_summaries.append(seed_summary)
    objective_summary = summarize_objective_run(
        corpus_npz=corpus_npz,
        arrays=arrays,
        seed_summaries=seed_summaries,
        args=args,
    )
    write_csv_rows(args.run_dir / "objective_loss_summary.csv", all_loss_rows)
    write_csv_rows(args.run_dir / "objective_seed_summary.csv", seed_summaries)
    write_json(args.run_dir / "objective_summary.json", objective_summary)
    return objective_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a boundary-outcome corpus and run objective-only sanity.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--boundary-rows-csv", type=Path, required=True)
    parser.add_argument("--delay-steps", type=int, default=10)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--include-unaccepted-rows", action="store_true")
    parser.add_argument("--min-margin-gap", type=float, default=0.0)
    parser.add_argument("--max-rows-per-physical-pair", type=int, default=12)
    parser.add_argument("--max-rows-per-target", type=int, default=0)
    parser.add_argument("--boundary-margin-scale", type=float, default=0.20)
    parser.add_argument("--success-drop-bonus", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=1.0)
    parser.add_argument("--margin-clip", type=float, default=0.20)
    parser.add_argument("--optimization-seeds", type=parse_seed_list, default=(9620, 9621, 9622))
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=180)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=96)
    parser.add_argument("--delta-loss-coef", type=float, default=0.5)
    parser.add_argument("--rank-loss-coef", type=float, default=0.25)
    parser.add_argument("--objective-device", default="cpu")
    parser.add_argument("--skip-objective", action="store_true")
    parser.add_argument("--corpus-npz", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    corpus_summary, arrays, _ = run_corpus_build(args)
    objective_summary = None
    if not args.skip_objective:
        objective_summary = run_objective_sanity(args, arrays=arrays)
    print(
        "corpus_rows={corpus_rows} physical_pairs={physical_pairs} objective_pass={objective_pass}".format(
            corpus_rows=corpus_summary["corpus_rows"],
            physical_pairs=corpus_summary["physical_pairs"],
            objective_pass=None if objective_summary is None else objective_summary["objective_pass"],
        )
    )
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
