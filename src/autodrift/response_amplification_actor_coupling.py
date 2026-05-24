"""Frozen-backbone response-amplification actor-coupling probe."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_repeat import parse_seed_list
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.response_amplification_shadow import (
    ResponseAmplifierHead,
    _loss_components,
    _split_indices,
    _tensor_batch,
    _weighted_mean,
    summarize_shadow_predictions,
)
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_feature_separability_audit import batched_recurrent_outputs
from autodrift.wrong_history_fusion_boundary_probe import build_feature_views


VALID_ACTOR_COUPLING_VIEWS = ("fused_plus_next_hidden",)
VALID_HEAD_TYPES = ("mlp", "gated")
EPS = 1e-12


class GatedResponseAmplifierHead(nn.Module):
    """Bounded residual sequence head with a separate activation gate."""

    def __init__(
        self,
        feature_dim: int,
        hidden_dim: int,
        max_sequence_length: int,
        action_dim: int = 3,
        max_residual: float = 0.04,
    ) -> None:
        super().__init__()
        self.max_sequence_length = int(max_sequence_length)
        self.action_dim = int(action_dim)
        self.max_residual = float(max_residual)
        self.amplifier = nn.Sequential(
            nn.Linear(int(feature_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), self.max_sequence_length * self.action_dim),
        )
        self.gate_net = nn.Sequential(
            nn.Linear(int(feature_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward_with_aux(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        raw_logits = self.amplifier(features)
        raw = self.max_residual * torch.tanh(
            raw_logits.reshape(features.shape[0], self.max_sequence_length, self.action_dim)
        )
        gate = torch.sigmoid(self.gate_net(features)).reshape(features.shape[0], 1, 1)
        return gate * raw, raw, gate

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        prediction, _raw, _gate = self.forward_with_aux(features)
        return prediction


def parse_alpha_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("alpha list cannot be empty")
    if any(value < 0.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be nonnegative")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("alphas must not contain duplicates")
    return tuple(sorted(values))


def parse_actor_coupling_view(raw: str) -> str:
    value = str(raw).strip()
    if value not in VALID_ACTOR_COUPLING_VIEWS:
        raise argparse.ArgumentTypeError(
            "actor-coupling view must be one of: " + ", ".join(VALID_ACTOR_COUPLING_VIEWS)
        )
    return value


def parse_head_type(raw: str) -> str:
    value = str(raw).strip()
    if value not in VALID_HEAD_TYPES:
        raise argparse.ArgumentTypeError("head type must be one of: " + ", ".join(VALID_HEAD_TYPES))
    return value


def _head_forward_with_aux(
    head: nn.Module,
    features: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
    if hasattr(head, "forward_with_aux"):
        prediction, raw, gate = head.forward_with_aux(features)  # type: ignore[attr-defined]
        return prediction, raw, gate
    prediction = head(features)
    return prediction, prediction, None


def _predict_with_aux(
    head: nn.Module,
    features: np.ndarray,
    device: torch.device,
    batch_size: int = 4096,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    head.eval()
    predictions: list[np.ndarray] = []
    raw_rows: list[np.ndarray] = []
    gate_rows: list[np.ndarray] = []
    has_gate = False
    with torch.no_grad():
        for start in range(0, int(features.shape[0]), int(batch_size)):
            chunk = torch.as_tensor(features[start : start + int(batch_size)], dtype=torch.float32, device=device)
            prediction, raw, gate = _head_forward_with_aux(head, chunk)
            predictions.append(prediction.detach().cpu().numpy())
            raw_rows.append(raw.detach().cpu().numpy())
            if gate is not None:
                has_gate = True
                gate_rows.append(gate.detach().cpu().numpy())
    prediction_np = np.concatenate(predictions, axis=0)
    raw_np = np.concatenate(raw_rows, axis=0)
    gate_np = np.concatenate(gate_rows, axis=0) if has_gate else None
    return prediction_np, raw_np, gate_np


def _sequence_smoothness(prediction: torch.Tensor, mask: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    if prediction.shape[1] <= 1:
        return torch.zeros((), dtype=prediction.dtype, device=prediction.device)
    diff = prediction[:, 1:, :] - prediction[:, :-1, :]
    pair_mask = mask[:, 1:] * mask[:, :-1]
    per_row = (torch.square(diff) * pair_mask[:, :, None]).sum(dim=(1, 2))
    denom = torch.clamp(pair_mask.sum(dim=1) * prediction.shape[2], min=1.0)
    return _weighted_mean(per_row / denom, weight)


def _normal_first_mse(prediction_normal: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    per_row = torch.square(prediction_normal[:, 0, :]).mean(dim=1)
    return _weighted_mean(per_row, weight)


def _normal_first_topk_hinge(
    prediction_normal: torch.Tensor,
    *,
    threshold: float,
    fraction: float,
) -> torch.Tensor:
    first_l2 = torch.linalg.norm(prediction_normal[:, 0, :], dim=1)
    hinge = torch.square(torch.relu(first_l2 - float(threshold)))
    if hinge.numel() == 0:
        return torch.zeros((), dtype=prediction_normal.dtype, device=prediction_normal.device)
    k = max(1, int(np.ceil(float(fraction) * int(hinge.numel()))))
    k = min(k, int(hinge.numel()))
    return torch.topk(hinge, k=k, largest=True).values.mean()


def _row_sequence_l2(prediction: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    step_l2 = torch.linalg.norm(prediction, dim=2) * mask
    valid = torch.clamp(mask.sum(dim=1), min=1.0)
    return step_l2.sum(dim=1) / valid


def _normal_sequence_mean_hinge(
    prediction_normal: torch.Tensor,
    mask: torch.Tensor,
    weight: torch.Tensor,
    *,
    threshold: float,
) -> torch.Tensor:
    row_l2 = _row_sequence_l2(prediction_normal, mask)
    per_row = torch.square(torch.relu(row_l2 - float(threshold)))
    return _weighted_mean(per_row, weight)


def _normal_sequence_topk_hinge(
    prediction_normal: torch.Tensor,
    mask: torch.Tensor,
    *,
    threshold: float,
    fraction: float,
) -> torch.Tensor:
    row_l2 = _row_sequence_l2(prediction_normal, mask)
    hinge = torch.square(torch.relu(row_l2 - float(threshold)))
    if hinge.numel() == 0:
        return torch.zeros((), dtype=prediction_normal.dtype, device=prediction_normal.device)
    k = max(1, int(np.ceil(float(fraction) * int(hinge.numel()))))
    k = min(k, int(hinge.numel()))
    return torch.topk(hinge, k=k, largest=True).values.mean()


def _gate_row_values(gate: torch.Tensor) -> torch.Tensor:
    return gate.reshape(gate.shape[0], -1).mean(dim=1)


def _normal_gate_mean_loss(gate_normal: torch.Tensor | None, weight: torch.Tensor) -> torch.Tensor:
    if gate_normal is None:
        return torch.zeros((), dtype=weight.dtype, device=weight.device)
    per_row = torch.square(_gate_row_values(gate_normal))
    return _weighted_mean(per_row, weight)


def _normal_gate_topk_hinge(
    gate_normal: torch.Tensor | None,
    weight: torch.Tensor,
    *,
    threshold: float,
    fraction: float,
) -> torch.Tensor:
    if gate_normal is None:
        return torch.zeros((), dtype=weight.dtype, device=weight.device)
    hinge = torch.square(torch.relu(_gate_row_values(gate_normal) - float(threshold)))
    if hinge.numel() == 0:
        return torch.zeros((), dtype=weight.dtype, device=weight.device)
    k = max(1, int(np.ceil(float(fraction) * int(hinge.numel()))))
    k = min(k, int(hinge.numel()))
    return torch.topk(hinge, k=k, largest=True).values.mean()


def _wrong_gate_open_hinge(
    gate_wrong: torch.Tensor | None,
    weight: torch.Tensor,
    *,
    target: float,
) -> torch.Tensor:
    if gate_wrong is None:
        return torch.zeros((), dtype=weight.dtype, device=weight.device)
    per_row = torch.square(torch.relu(float(target) - _gate_row_values(gate_wrong)))
    return _weighted_mean(per_row, weight)


def _gate_margin_values(gate_normal: torch.Tensor, gate_wrong: torch.Tensor) -> torch.Tensor:
    return _gate_row_values(gate_wrong) - _gate_row_values(gate_normal).detach()


def _wrong_gate_margin_hinge(
    gate_normal: torch.Tensor | None,
    gate_wrong: torch.Tensor | None,
    weight: torch.Tensor,
    *,
    margin: float,
) -> torch.Tensor:
    if gate_normal is None or gate_wrong is None:
        return torch.zeros((), dtype=weight.dtype, device=weight.device)
    per_row = torch.square(torch.relu(float(margin) - _gate_margin_values(gate_normal, gate_wrong)))
    return _weighted_mean(per_row, weight)


def _hard_wrong_gate_loss(
    gate_normal: torch.Tensor | None,
    gate_wrong: torch.Tensor | None,
    weight: torch.Tensor,
    *,
    target: float,
    margin: float,
    fraction: float,
) -> tuple[torch.Tensor, int]:
    if gate_normal is None or gate_wrong is None:
        return torch.zeros((), dtype=weight.dtype, device=weight.device), 0
    gate_wrong_values = _gate_row_values(gate_wrong)
    gate_margin = gate_wrong_values - _gate_row_values(gate_normal).detach()
    if gate_margin.numel() == 0:
        return torch.zeros((), dtype=weight.dtype, device=weight.device), 0
    k = max(1, int(np.ceil(float(fraction) * int(gate_margin.numel()))))
    k = min(k, int(gate_margin.numel()))
    hard_indices = torch.topk(gate_margin, k=k, largest=False).indices
    hard_weight = weight.index_select(0, hard_indices)
    hard_wrong = gate_wrong_values.index_select(0, hard_indices)
    hard_margin = gate_margin.index_select(0, hard_indices)
    open_loss = _weighted_mean(torch.square(torch.relu(float(target) - hard_wrong)), hard_weight)
    margin_loss = _weighted_mean(torch.square(torch.relu(float(margin) - hard_margin)), hard_weight)
    return open_loss + margin_loss, k


def _raw_amplifier_l2(
    raw_normal: torch.Tensor,
    raw_wrong: torch.Tensor,
    mask: torch.Tensor,
    weight: torch.Tensor,
) -> torch.Tensor:
    normal_row = torch.square(_row_sequence_l2(raw_normal, mask))
    wrong_row = torch.square(_row_sequence_l2(raw_wrong, mask))
    return 0.5 * (_weighted_mean(normal_row, weight) + _weighted_mean(wrong_row, weight))


def _wrong_first_gap_hinge(
    prediction_normal: torch.Tensor,
    prediction_wrong: torch.Tensor,
    weight: torch.Tensor,
    *,
    target_gap: float,
) -> torch.Tensor:
    first_gap = torch.linalg.norm(prediction_wrong[:, 0, :] - prediction_normal[:, 0, :], dim=1)
    per_row = torch.square(torch.relu(float(target_gap) - first_gap))
    return _weighted_mean(per_row, weight)


def _row_sequence_gap(prediction_normal: torch.Tensor, prediction_wrong: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    step_l2 = torch.linalg.norm(prediction_wrong - prediction_normal, dim=2) * mask
    valid = torch.clamp(mask.sum(dim=1), min=1.0)
    return step_l2.sum(dim=1) / valid


def _detached_sequence_gap_hinge(
    prediction_normal: torch.Tensor,
    prediction_wrong: torch.Tensor,
    mask: torch.Tensor,
    weight: torch.Tensor,
    *,
    target_gap: float,
) -> torch.Tensor:
    row_gap = _row_sequence_gap(prediction_normal.detach(), prediction_wrong, mask)
    per_row = torch.square(torch.relu(float(target_gap) - row_gap))
    return _weighted_mean(per_row, weight)


def _hard_wrong_rows_loss(
    prediction_normal: torch.Tensor,
    prediction_wrong: torch.Tensor,
    target_wrong: torch.Tensor,
    mask: torch.Tensor,
    weight: torch.Tensor,
    *,
    target_gap: float,
    fraction: float,
) -> tuple[torch.Tensor, int]:
    if prediction_wrong.shape[0] == 0:
        return torch.zeros((), dtype=prediction_wrong.dtype, device=prediction_wrong.device), 0
    row_gap = _row_sequence_gap(prediction_normal.detach(), prediction_wrong, mask)
    k = max(1, int(np.ceil(float(fraction) * int(row_gap.numel()))))
    k = min(k, int(row_gap.numel()))
    hard_indices = torch.topk(row_gap, k=k, largest=False).indices
    hard_pred_normal = prediction_normal.index_select(0, hard_indices)
    hard_pred_wrong = prediction_wrong.index_select(0, hard_indices)
    hard_target_wrong = target_wrong.index_select(0, hard_indices)
    hard_mask = mask.index_select(0, hard_indices)
    hard_weight = weight.index_select(0, hard_indices)
    target_loss = torch.square(hard_pred_wrong - hard_target_wrong) * hard_mask[:, :, None]
    denom = torch.clamp(hard_mask.sum(dim=1) * hard_pred_wrong.shape[2], min=1.0)
    row_loss = target_loss.sum(dim=(1, 2)) / denom
    target_mse = _weighted_mean(row_loss, hard_weight)
    gap_hinge = _detached_sequence_gap_hinge(
        hard_pred_normal,
        hard_pred_wrong,
        hard_mask,
        hard_weight,
        target_gap=target_gap,
    )
    return target_mse + gap_hinge, k


def _coupling_loss_components(
    head: ResponseAmplifierHead,
    batch: dict[str, torch.Tensor],
    indices: np.ndarray,
    *,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_sequence_mean_coef: float,
    normal_sequence_mean_threshold: float,
    normal_sequence_topk_coef: float,
    normal_sequence_topk_threshold: float,
    normal_sequence_topk_fraction: float,
    normal_gate_coef: float,
    normal_gate_topk_coef: float,
    normal_gate_threshold: float,
    normal_gate_topk_fraction: float,
    normal_first_coef: float,
    normal_first_topk_coef: float,
    normal_first_threshold: float,
    normal_first_topk_fraction: float,
    wrong_first_gap_coef: float,
    wrong_first_target_gap: float,
    branch_specific_gap: bool,
    wrong_sequence_gap_coef: float,
    wrong_sequence_target_gap: float,
    wrong_hard_coef: float,
    wrong_hard_fraction: float,
    wrong_gate_open_coef: float,
    wrong_gate_target: float,
    wrong_gate_margin_coef: float,
    wrong_gate_margin: float,
    wrong_gate_hard_coef: float,
    wrong_gate_hard_fraction: float,
    raw_amplifier_l2_coef: float,
    target_gap: float,
) -> dict[str, torch.Tensor]:
    losses = _loss_components(
        head,
        batch,
        indices,
        wrong_target_coef=wrong_target_coef,
        gap_margin_coef=gap_margin_coef,
        zero_regularizer_coef=0.0,
        target_gap=target_gap,
    )
    index_t = torch.as_tensor(indices, dtype=torch.long, device=batch["mask"].device)
    pred_normal, raw_normal, gate_normal = _head_forward_with_aux(
        head,
        batch["features_normal"].index_select(0, index_t),
    )
    pred_wrong, raw_wrong, gate_wrong = _head_forward_with_aux(
        head,
        batch["features_variant"].index_select(0, index_t),
    )
    mask = batch["mask"].index_select(0, index_t)
    weight = batch["weight"].index_select(0, index_t)
    wrong_target = batch["target_delta_wrong"].index_select(0, index_t)
    smoothness = 0.5 * (
        _sequence_smoothness(pred_normal, mask, weight) + _sequence_smoothness(pred_wrong, mask, weight)
    )
    normal_sequence_mean = _normal_sequence_mean_hinge(
        pred_normal,
        mask,
        weight,
        threshold=normal_sequence_mean_threshold,
    )
    normal_sequence_topk = _normal_sequence_topk_hinge(
        pred_normal,
        mask,
        threshold=normal_sequence_topk_threshold,
        fraction=normal_sequence_topk_fraction,
    )
    normal_gate = _normal_gate_mean_loss(gate_normal, weight)
    normal_gate_topk = _normal_gate_topk_hinge(
        gate_normal,
        weight,
        threshold=normal_gate_threshold,
        fraction=normal_gate_topk_fraction,
    )
    wrong_gate_open = _wrong_gate_open_hinge(
        gate_wrong,
        weight,
        target=wrong_gate_target,
    )
    wrong_gate_margin_loss = _wrong_gate_margin_hinge(
        gate_normal,
        gate_wrong,
        weight,
        margin=wrong_gate_margin,
    )
    hard_gate_loss, hard_gate_row_count = _hard_wrong_gate_loss(
        gate_normal,
        gate_wrong,
        weight,
        target=wrong_gate_target,
        margin=wrong_gate_margin,
        fraction=wrong_gate_hard_fraction,
    )
    raw_l2 = _raw_amplifier_l2(raw_normal, raw_wrong, mask, weight)
    normal_first = _normal_first_mse(pred_normal, weight)
    normal_topk = _normal_first_topk_hinge(
        pred_normal,
        threshold=normal_first_threshold,
        fraction=normal_first_topk_fraction,
    )
    normal_gap_ref = pred_normal.detach() if branch_specific_gap else pred_normal
    wrong_first_gap = _wrong_first_gap_hinge(
        normal_gap_ref,
        pred_wrong,
        weight,
        target_gap=wrong_first_target_gap,
    )
    wrong_sequence_gap = _detached_sequence_gap_hinge(
        pred_normal,
        pred_wrong,
        mask,
        weight,
        target_gap=wrong_sequence_target_gap,
    ) if branch_specific_gap else torch.zeros((), dtype=pred_wrong.dtype, device=pred_wrong.device)
    hard_wrong_loss, hard_row_count = _hard_wrong_rows_loss(
        pred_normal,
        pred_wrong,
        wrong_target,
        mask,
        weight,
        target_gap=wrong_sequence_target_gap,
        fraction=wrong_hard_fraction,
    ) if branch_specific_gap else (
        torch.zeros((), dtype=pred_wrong.dtype, device=pred_wrong.device),
        0,
    )
    losses["sequence_smoothness_mse"] = smoothness
    losses["normal_sequence_mean_hinge"] = normal_sequence_mean
    losses["normal_sequence_topk_hinge"] = normal_sequence_topk
    losses["normal_gate_mean_loss"] = normal_gate
    losses["normal_gate_topk_hinge"] = normal_gate_topk
    losses["wrong_gate_open_hinge"] = wrong_gate_open
    losses["wrong_gate_margin_hinge"] = wrong_gate_margin_loss
    losses["wrong_gate_hard_loss"] = hard_gate_loss
    losses["hard_gate_row_count"] = torch.as_tensor(
        float(hard_gate_row_count),
        dtype=pred_wrong.dtype,
        device=pred_wrong.device,
    )
    losses["raw_amplifier_l2"] = raw_l2
    losses["gated_head_active"] = torch.as_tensor(
        float(gate_normal is not None and gate_wrong is not None),
        dtype=pred_wrong.dtype,
        device=pred_wrong.device,
    )
    losses["normal_first_mse"] = normal_first
    losses["normal_first_topk_hinge"] = normal_topk
    losses["wrong_first_gap_hinge"] = wrong_first_gap
    losses["wrong_sequence_gap_hinge"] = wrong_sequence_gap
    losses["hard_wrong_loss"] = hard_wrong_loss
    losses["hard_row_count"] = torch.as_tensor(float(hard_row_count), dtype=pred_wrong.dtype, device=pred_wrong.device)
    losses["total_loss"] = (
        losses["total_loss"]
        + float(smoothness_coef) * smoothness
        + float(normal_sequence_mean_coef) * normal_sequence_mean
        + float(normal_sequence_topk_coef) * normal_sequence_topk
        + float(normal_gate_coef) * normal_gate
        + float(normal_gate_topk_coef) * normal_gate_topk
        + float(normal_first_coef) * normal_first
        + float(normal_first_topk_coef) * normal_topk
        + float(wrong_first_gap_coef) * wrong_first_gap
        + float(wrong_sequence_gap_coef) * wrong_sequence_gap
        + float(wrong_hard_coef) * hard_wrong_loss
        + float(wrong_gate_open_coef) * wrong_gate_open
        + float(wrong_gate_margin_coef) * wrong_gate_margin_loss
        + float(wrong_gate_hard_coef) * hard_gate_loss
        + float(raw_amplifier_l2_coef) * raw_l2
    )
    return losses


def _first_l2(prediction: np.ndarray) -> np.ndarray:
    return np.linalg.norm(prediction[:, 0, :].astype(np.float64), axis=1)


def _gate_values_np(gate: np.ndarray) -> np.ndarray:
    return np.asarray(gate, dtype=np.float64).reshape(gate.shape[0], -1).mean(axis=1)


def _gate_margin_values_np(gate_normal: np.ndarray, gate_wrong: np.ndarray) -> np.ndarray:
    return _gate_values_np(gate_wrong) - _gate_values_np(gate_normal)


def _row_sequence_l2_np(prediction: np.ndarray, mask: np.ndarray) -> np.ndarray:
    step_l2 = np.linalg.norm(np.asarray(prediction, dtype=np.float64), axis=2) * np.asarray(mask, dtype=np.float64)
    valid = np.maximum(np.asarray(mask, dtype=np.float64).sum(axis=1), 1.0)
    return step_l2.sum(axis=1) / valid


def alpha_candidate_passes(row: dict[str, Any]) -> bool:
    return bool(
        row["split"] == "source_holdout_validation"
        and float(row["alpha"]) > 0.0
        and row["normal_delta_l2_mean"] <= 0.0025
        and row["normal_delta_l2_p95"] <= 0.0060
        and row["predicted_normal_wrong_gap_l2_mean"] >= 0.010
        and row["predicted_normal_wrong_gap_l2_p10"] >= 0.004
        and row["gap_improvement_ratio"] >= 3.0
        and row["wrong_target_mse_improvement"] >= 0.50
        and row["normal_action_drift_first_l2_p95"] <= 0.0060
    )


def evaluate_alpha_ladder(
    *,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    prediction_normal: np.ndarray,
    prediction_wrong: np.ndarray,
    alphas: tuple[float, ...],
    gate_normal: np.ndarray | None = None,
    gate_wrong: np.ndarray | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    alpha_rows: list[dict[str, Any]] = []
    gate_normal_values = _gate_values_np(gate_normal) if gate_normal is not None else None
    gate_wrong_values = _gate_values_np(gate_wrong) if gate_wrong is not None else None
    gate_margin_values = (
        _gate_margin_values_np(gate_normal, gate_wrong)
        if gate_normal is not None and gate_wrong is not None
        else None
    )
    for alpha in alphas:
        scaled_normal = prediction_normal * float(alpha)
        scaled_wrong = prediction_wrong * float(alpha)
        row_metrics, _source, split_summary, _target = summarize_shadow_predictions(
            arrays,
            metadata,
            prediction_normal=scaled_normal,
            prediction_wrong=scaled_wrong,
        )
        first_normal = _first_l2(scaled_normal)
        first_wrong = _first_l2(scaled_wrong)
        row_metrics = row_metrics.copy()
        row_metrics["normal_action_drift_first_l2"] = first_normal
        row_metrics["wrong_action_drift_first_l2"] = first_wrong
        if gate_normal_values is not None:
            row_metrics["normal_gate"] = gate_normal_values
        if gate_wrong_values is not None:
            row_metrics["wrong_gate"] = gate_wrong_values
        if gate_margin_values is not None:
            row_metrics["wrong_gate_margin"] = gate_margin_values
        for split_row in split_summary:
            split = str(split_row["split"])
            split_metrics = row_metrics[row_metrics["split"].astype(str) == split]
            output = {
                "alpha": float(alpha),
                **split_row,
                "normal_action_drift_first_l2_mean": float(split_metrics["normal_action_drift_first_l2"].mean()),
                "normal_action_drift_first_l2_p95": float(
                    np.percentile(split_metrics["normal_action_drift_first_l2"].to_numpy(dtype=float), 95)
                ),
                "wrong_action_drift_first_l2_mean": float(split_metrics["wrong_action_drift_first_l2"].mean()),
                "wrong_action_drift_first_l2_p95": float(
                    np.percentile(split_metrics["wrong_action_drift_first_l2"].to_numpy(dtype=float), 95)
                ),
            }
            if gate_normal_values is not None:
                output["normal_gate_mean"] = float(split_metrics["normal_gate"].mean())
                output["normal_gate_p95"] = float(
                    np.percentile(split_metrics["normal_gate"].to_numpy(dtype=float), 95)
                )
            if gate_wrong_values is not None:
                output["wrong_gate_mean"] = float(split_metrics["wrong_gate"].mean())
                output["wrong_gate_p10"] = float(
                    np.percentile(split_metrics["wrong_gate"].to_numpy(dtype=float), 10)
                )
            if gate_margin_values is not None:
                output["wrong_gate_margin_mean"] = float(split_metrics["wrong_gate_margin"].mean())
                output["wrong_gate_margin_p10"] = float(
                    np.percentile(split_metrics["wrong_gate_margin"].to_numpy(dtype=float), 10)
                )
            output["alpha_candidate_passed"] = alpha_candidate_passes(output)
            alpha_rows.append(output)
    source_holdout_passes = [
        row
        for row in alpha_rows
        if row["split"] == "source_holdout_validation" and bool(row["alpha_candidate_passed"])
    ]
    selected = max(source_holdout_passes, key=lambda row: float(row["alpha"])) if source_holdout_passes else None
    summary = {
        "alpha_passed": bool(selected is not None),
        "selected_alpha": float(selected["alpha"]) if selected is not None else 0.0,
        "selected_source_holdout_normal_delta_l2_mean": float(selected["normal_delta_l2_mean"]) if selected else None,
        "selected_source_holdout_predicted_normal_wrong_gap_l2_mean": float(selected["predicted_normal_wrong_gap_l2_mean"]) if selected else None,
        "selected_source_holdout_gap_improvement_ratio": float(selected["gap_improvement_ratio"]) if selected else None,
        "selected_source_holdout_normal_action_drift_first_l2_p95": float(
            selected["normal_action_drift_first_l2_p95"]
        )
        if selected
        else None,
    }
    return alpha_rows, summary


def train_actor_coupling_seed(
    *,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    alphas: tuple[float, ...],
    hidden_dim: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    head_type: str = "mlp",
    max_residual: float = 0.04,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_sequence_mean_coef: float = 0.0,
    normal_sequence_mean_threshold: float = 0.002,
    normal_sequence_topk_coef: float = 0.0,
    normal_sequence_topk_threshold: float = 0.0045,
    normal_sequence_topk_fraction: float = 0.10,
    normal_gate_coef: float = 0.0,
    normal_gate_topk_coef: float = 0.0,
    normal_gate_threshold: float = 0.10,
    normal_gate_topk_fraction: float = 0.10,
    normal_first_coef: float = 0.0,
    normal_first_topk_coef: float = 0.0,
    normal_first_threshold: float = 0.004,
    normal_first_topk_fraction: float = 0.10,
    wrong_first_gap_coef: float = 0.0,
    wrong_first_target_gap: float = 0.006,
    branch_specific_gap: bool = False,
    wrong_sequence_gap_coef: float = 0.0,
    wrong_sequence_target_gap: float = 0.012,
    wrong_hard_coef: float = 0.0,
    wrong_hard_fraction: float = 0.25,
    wrong_gate_open_coef: float = 0.0,
    wrong_gate_target: float = 0.50,
    wrong_gate_margin_coef: float = 0.0,
    wrong_gate_margin: float = 0.30,
    wrong_gate_hard_coef: float = 0.0,
    wrong_gate_hard_fraction: float = 0.25,
    raw_amplifier_l2_coef: float = 0.0,
    target_gap: float,
    device: torch.device,
) -> tuple[nn.Module, list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_indices = _split_indices(metadata, "train")
    val_indices = _split_indices(metadata, "source_holdout_validation")
    if train_indices.size == 0 or val_indices.size == 0:
        raise ValueError("both train and source_holdout_validation splits are required")
    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    if head_type == "mlp":
        head: nn.Module = ResponseAmplifierHead(
            feature_dim=int(features_normal.shape[1]),
            hidden_dim=int(hidden_dim),
            max_sequence_length=contract.max_sequence_length,
            action_dim=contract.action_dim,
        ).to(device)
    elif head_type == "gated":
        head = GatedResponseAmplifierHead(
            feature_dim=int(features_normal.shape[1]),
            hidden_dim=int(hidden_dim),
            max_sequence_length=contract.max_sequence_length,
            action_dim=contract.action_dim,
            max_residual=max_residual,
        ).to(device)
    else:
        raise ValueError(f"unsupported head type: {head_type}")
    optimizer = torch.optim.AdamW(head.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    metric_rows: list[dict[str, Any]] = []
    log_interval = max(1, int(epochs) // 10)

    def append_metrics(epoch: int) -> None:
        with torch.no_grad():
            for split, indices in (("train", train_indices), ("source_holdout_validation", val_indices)):
                losses = _coupling_loss_components(
                    head,
                    batch,
                    indices,
                    wrong_target_coef=wrong_target_coef,
                    gap_margin_coef=gap_margin_coef,
                    smoothness_coef=smoothness_coef,
                    normal_sequence_mean_coef=normal_sequence_mean_coef,
                    normal_sequence_mean_threshold=normal_sequence_mean_threshold,
                    normal_sequence_topk_coef=normal_sequence_topk_coef,
                    normal_sequence_topk_threshold=normal_sequence_topk_threshold,
                    normal_sequence_topk_fraction=normal_sequence_topk_fraction,
                    normal_gate_coef=normal_gate_coef,
                    normal_gate_topk_coef=normal_gate_topk_coef,
                    normal_gate_threshold=normal_gate_threshold,
                    normal_gate_topk_fraction=normal_gate_topk_fraction,
                    normal_first_coef=normal_first_coef,
                    normal_first_topk_coef=normal_first_topk_coef,
                    normal_first_threshold=normal_first_threshold,
                    normal_first_topk_fraction=normal_first_topk_fraction,
                    wrong_first_gap_coef=wrong_first_gap_coef,
                    wrong_first_target_gap=wrong_first_target_gap,
                    branch_specific_gap=branch_specific_gap,
                    wrong_sequence_gap_coef=wrong_sequence_gap_coef,
                    wrong_sequence_target_gap=wrong_sequence_target_gap,
                    wrong_hard_coef=wrong_hard_coef,
                    wrong_hard_fraction=wrong_hard_fraction,
                    wrong_gate_open_coef=wrong_gate_open_coef,
                    wrong_gate_target=wrong_gate_target,
                    wrong_gate_margin_coef=wrong_gate_margin_coef,
                    wrong_gate_margin=wrong_gate_margin,
                    wrong_gate_hard_coef=wrong_gate_hard_coef,
                    wrong_gate_hard_fraction=wrong_gate_hard_fraction,
                    raw_amplifier_l2_coef=raw_amplifier_l2_coef,
                    target_gap=target_gap,
                )
                metric_rows.append(
                    {
                        "epoch": int(epoch),
                        "split": split,
                        **{key: float(value.detach().cpu().item()) for key, value in losses.items()},
                    }
                )

    append_metrics(0)
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        losses = _coupling_loss_components(
            head,
            batch,
            train_indices,
            wrong_target_coef=wrong_target_coef,
            gap_margin_coef=gap_margin_coef,
            smoothness_coef=smoothness_coef,
            normal_sequence_mean_coef=normal_sequence_mean_coef,
            normal_sequence_mean_threshold=normal_sequence_mean_threshold,
            normal_sequence_topk_coef=normal_sequence_topk_coef,
            normal_sequence_topk_threshold=normal_sequence_topk_threshold,
            normal_sequence_topk_fraction=normal_sequence_topk_fraction,
            normal_gate_coef=normal_gate_coef,
            normal_gate_topk_coef=normal_gate_topk_coef,
            normal_gate_threshold=normal_gate_threshold,
            normal_gate_topk_fraction=normal_gate_topk_fraction,
            normal_first_coef=normal_first_coef,
            normal_first_topk_coef=normal_first_topk_coef,
            normal_first_threshold=normal_first_threshold,
            normal_first_topk_fraction=normal_first_topk_fraction,
            wrong_first_gap_coef=wrong_first_gap_coef,
            wrong_first_target_gap=wrong_first_target_gap,
            branch_specific_gap=branch_specific_gap,
            wrong_sequence_gap_coef=wrong_sequence_gap_coef,
            wrong_sequence_target_gap=wrong_sequence_target_gap,
            wrong_hard_coef=wrong_hard_coef,
            wrong_hard_fraction=wrong_hard_fraction,
            wrong_gate_open_coef=wrong_gate_open_coef,
            wrong_gate_target=wrong_gate_target,
            wrong_gate_margin_coef=wrong_gate_margin_coef,
            wrong_gate_margin=wrong_gate_margin,
            wrong_gate_hard_coef=wrong_gate_hard_coef,
            wrong_gate_hard_fraction=wrong_gate_hard_fraction,
            raw_amplifier_l2_coef=raw_amplifier_l2_coef,
            target_gap=target_gap,
        )
        losses["total_loss"].backward()
        optimizer.step()
        if epoch == int(epochs) or epoch % log_interval == 0:
            append_metrics(epoch)

    prediction_normal, raw_normal, gate_normal = _predict_with_aux(head, features_normal, device)
    prediction_wrong, raw_wrong, gate_wrong = _predict_with_aux(head, features_variant, device)
    alpha_rows, alpha_summary = evaluate_alpha_ladder(
        arrays=arrays,
        metadata=metadata,
        prediction_normal=prediction_normal,
        prediction_wrong=prediction_wrong,
        alphas=alphas,
        gate_normal=gate_normal,
        gate_wrong=gate_wrong,
    )
    summary = {
        "seed": int(seed),
        "head_type": head_type,
        "max_residual": float(max_residual),
        "feature_dim": int(features_normal.shape[1]),
        "hidden_dim": int(hidden_dim),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "smoothness_coef": float(smoothness_coef),
        "normal_sequence_mean_coef": float(normal_sequence_mean_coef),
        "normal_sequence_mean_threshold": float(normal_sequence_mean_threshold),
        "normal_sequence_topk_coef": float(normal_sequence_topk_coef),
        "normal_sequence_topk_threshold": float(normal_sequence_topk_threshold),
        "normal_sequence_topk_fraction": float(normal_sequence_topk_fraction),
        "normal_gate_coef": float(normal_gate_coef),
        "normal_gate_topk_coef": float(normal_gate_topk_coef),
        "normal_gate_threshold": float(normal_gate_threshold),
        "normal_gate_topk_fraction": float(normal_gate_topk_fraction),
        "normal_first_coef": float(normal_first_coef),
        "normal_first_topk_coef": float(normal_first_topk_coef),
        "normal_first_threshold": float(normal_first_threshold),
        "normal_first_topk_fraction": float(normal_first_topk_fraction),
        "wrong_first_gap_coef": float(wrong_first_gap_coef),
        "wrong_first_target_gap": float(wrong_first_target_gap),
        "branch_specific_gap": bool(branch_specific_gap),
        "wrong_sequence_gap_coef": float(wrong_sequence_gap_coef),
        "wrong_sequence_target_gap": float(wrong_sequence_target_gap),
        "wrong_hard_coef": float(wrong_hard_coef),
        "wrong_hard_fraction": float(wrong_hard_fraction),
        "wrong_gate_open_coef": float(wrong_gate_open_coef),
        "wrong_gate_target": float(wrong_gate_target),
        "wrong_gate_margin_coef": float(wrong_gate_margin_coef),
        "wrong_gate_margin": float(wrong_gate_margin),
        "wrong_gate_hard_coef": float(wrong_gate_hard_coef),
        "wrong_gate_hard_fraction": float(wrong_gate_hard_fraction),
        "raw_amplifier_l2_coef": float(raw_amplifier_l2_coef),
        "normal_raw_sequence_l2_mean": float(_row_sequence_l2_np(raw_normal, arrays["sequence_mask"]).mean()),
        "wrong_raw_sequence_l2_mean": float(_row_sequence_l2_np(raw_wrong, arrays["sequence_mask"]).mean()),
        "normal_gate_mean": float(_gate_values_np(gate_normal).mean()) if gate_normal is not None else None,
        "wrong_gate_mean": float(_gate_values_np(gate_wrong).mean()) if gate_wrong is not None else None,
        "wrong_gate_margin_mean": float(_gate_margin_values_np(gate_normal, gate_wrong).mean())
        if gate_normal is not None and gate_wrong is not None
        else None,
        "target_gap": float(target_gap),
        **alpha_summary,
    }
    return head, metric_rows, summary, alpha_rows


def apply_actor_coupling_pass_rules(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row for row in seed_summaries if bool(row.get("alpha_passed", False))]
    return {
        "actor_coupling_exact_passed": bool(passed),
        "passed_seed_count": int(len(passed)),
        "best_selected_alpha": float(max((row["selected_alpha"] for row in passed), default=0.0)),
        "passed_seeds": [int(row["seed"]) for row in passed],
    }


def run_response_amplification_actor_coupling(
    *,
    checkpoint_path: Path,
    shadow_corpus_npz: Path,
    metadata_csv: Path,
    view: str,
    seeds: tuple[int, ...],
    alphas: tuple[float, ...],
    target_gap: float,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    head_type: str,
    max_residual: float,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_sequence_mean_coef: float,
    normal_sequence_mean_threshold: float,
    normal_sequence_topk_coef: float,
    normal_sequence_topk_threshold: float,
    normal_sequence_topk_fraction: float,
    normal_gate_coef: float,
    normal_gate_topk_coef: float,
    normal_gate_threshold: float,
    normal_gate_topk_fraction: float,
    normal_first_coef: float,
    normal_first_topk_coef: float,
    normal_first_threshold: float,
    normal_first_topk_fraction: float,
    wrong_first_gap_coef: float,
    wrong_first_target_gap: float,
    branch_specific_gap: bool,
    wrong_sequence_gap_coef: float,
    wrong_sequence_target_gap: float,
    wrong_hard_coef: float,
    wrong_hard_fraction: float,
    wrong_gate_open_coef: float,
    wrong_gate_target: float,
    wrong_gate_margin_coef: float,
    wrong_gate_margin: float,
    wrong_gate_hard_coef: float,
    wrong_gate_hard_fraction: float,
    raw_amplifier_l2_coef: float,
    device: str,
    run_dir: Path,
    batch_size: int = 1024,
) -> dict[str, Any]:
    if view not in VALID_ACTOR_COUPLING_VIEWS:
        raise ValueError(f"unsupported actor-coupling view: {view}")
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(shadow_corpus_npz)
    contract = validate_sequence_corpus_contract(arrays)
    metadata = load_metadata_csv(metadata_csv, expected_rows=contract.rows)
    validate_metadata_alignment(arrays, metadata)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    freeze_actor(model)
    before_checksum = model_parameter_checksum(model)
    normal_outputs = batched_recurrent_outputs(
        model,
        arrays["observation"],
        arrays["normal_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    variant_outputs = batched_recurrent_outputs(
        model,
        arrays["observation"],
        arrays["variant_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    features_normal, features_variant = build_feature_views(normal_outputs, variant_outputs, (view,))[view]
    seed_summaries: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    alpha_rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_dir = run_dir / f"seed_{int(seed)}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        head, metrics, summary, seed_alpha_rows = train_actor_coupling_seed(
            arrays=arrays,
            metadata=metadata,
            features_normal=features_normal,
            features_variant=features_variant,
            alphas=alphas,
            hidden_dim=hidden_dim,
            epochs=epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            seed=int(seed),
            head_type=head_type,
            max_residual=max_residual,
            wrong_target_coef=wrong_target_coef,
            gap_margin_coef=gap_margin_coef,
            smoothness_coef=smoothness_coef,
            normal_sequence_mean_coef=normal_sequence_mean_coef,
            normal_sequence_mean_threshold=normal_sequence_mean_threshold,
            normal_sequence_topk_coef=normal_sequence_topk_coef,
            normal_sequence_topk_threshold=normal_sequence_topk_threshold,
            normal_sequence_topk_fraction=normal_sequence_topk_fraction,
            normal_gate_coef=normal_gate_coef,
            normal_gate_topk_coef=normal_gate_topk_coef,
            normal_gate_threshold=normal_gate_threshold,
            normal_gate_topk_fraction=normal_gate_topk_fraction,
            normal_first_coef=normal_first_coef,
            normal_first_topk_coef=normal_first_topk_coef,
            normal_first_threshold=normal_first_threshold,
            normal_first_topk_fraction=normal_first_topk_fraction,
            wrong_first_gap_coef=wrong_first_gap_coef,
            wrong_first_target_gap=wrong_first_target_gap,
            branch_specific_gap=branch_specific_gap,
            wrong_sequence_gap_coef=wrong_sequence_gap_coef,
            wrong_sequence_target_gap=wrong_sequence_target_gap,
            wrong_hard_coef=wrong_hard_coef,
            wrong_hard_fraction=wrong_hard_fraction,
            wrong_gate_open_coef=wrong_gate_open_coef,
            wrong_gate_target=wrong_gate_target,
            wrong_gate_margin_coef=wrong_gate_margin_coef,
            wrong_gate_margin=wrong_gate_margin,
            wrong_gate_hard_coef=wrong_gate_hard_coef,
            wrong_gate_hard_fraction=wrong_gate_hard_fraction,
            raw_amplifier_l2_coef=raw_amplifier_l2_coef,
            target_gap=target_gap,
            device=resolved_device,
        )
        head_path = seed_dir / "residual_sequence_head.pt"
        torch.save(
            {
                "head_state": head.state_dict(),
                "head_type": head_type,
                "max_residual": float(max_residual),
                "gate_diagnostics_available": bool(head_type == "gated"),
                "view": view,
                "seed": int(seed),
                "feature_dim": int(features_normal.shape[1]),
                "hidden_dim": int(hidden_dim),
                "max_sequence_length": int(arrays["sequence_mask"].shape[1]),
                "action_dim": 3,
                "execution": "first_residual_only",
            },
            head_path,
        )
        summary.update({"view": view, "head_checkpoint": str(head_path)})
        seed_summaries.append(summary)
        metric_rows.extend({"seed": int(seed), **row} for row in metrics)
        alpha_rows.extend({"seed": int(seed), **row} for row in seed_alpha_rows)

    after_checksum = model_parameter_checksum(model)
    actor_changed = bool(before_checksum != after_checksum)
    for row in seed_summaries:
        row["actor_parameters_changed"] = actor_changed
        row["base_actor_checkpoint_written"] = False
        row["ppo_used"] = False
        row["promoted"] = False
    pass_rules = apply_actor_coupling_pass_rules(seed_summaries)
    write_csv_rows(run_dir / "seed_view_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "train_metrics.csv", metric_rows)
    write_csv_rows(run_dir / "alpha_summary.csv", alpha_rows)
    summary = {
        "run_type": "response_amplification_actor_coupling",
        "checkpoint": checkpoint_path,
        "shadow_corpus_npz": shadow_corpus_npz,
        "metadata_csv": metadata_csv,
        "view": view,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "seeds": [int(seed) for seed in seeds],
        "alphas": [float(alpha) for alpha in alphas],
        "target_gap": float(target_gap),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "head_type": head_type,
        "max_residual": float(max_residual),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "smoothness_coef": float(smoothness_coef),
        "normal_sequence_mean_coef": float(normal_sequence_mean_coef),
        "normal_sequence_mean_threshold": float(normal_sequence_mean_threshold),
        "normal_sequence_topk_coef": float(normal_sequence_topk_coef),
        "normal_sequence_topk_threshold": float(normal_sequence_topk_threshold),
        "normal_sequence_topk_fraction": float(normal_sequence_topk_fraction),
        "normal_gate_coef": float(normal_gate_coef),
        "normal_gate_topk_coef": float(normal_gate_topk_coef),
        "normal_gate_threshold": float(normal_gate_threshold),
        "normal_gate_topk_fraction": float(normal_gate_topk_fraction),
        "normal_first_coef": float(normal_first_coef),
        "normal_first_topk_coef": float(normal_first_topk_coef),
        "normal_first_threshold": float(normal_first_threshold),
        "normal_first_topk_fraction": float(normal_first_topk_fraction),
        "wrong_first_gap_coef": float(wrong_first_gap_coef),
        "wrong_first_target_gap": float(wrong_first_target_gap),
        "branch_specific_gap": bool(branch_specific_gap),
        "wrong_sequence_gap_coef": float(wrong_sequence_gap_coef),
        "wrong_sequence_target_gap": float(wrong_sequence_target_gap),
        "wrong_hard_coef": float(wrong_hard_coef),
        "wrong_hard_fraction": float(wrong_hard_fraction),
        "wrong_gate_open_coef": float(wrong_gate_open_coef),
        "wrong_gate_target": float(wrong_gate_target),
        "wrong_gate_margin_coef": float(wrong_gate_margin_coef),
        "wrong_gate_margin": float(wrong_gate_margin),
        "wrong_gate_hard_coef": float(wrong_gate_hard_coef),
        "wrong_gate_hard_fraction": float(wrong_gate_hard_fraction),
        "raw_amplifier_l2_coef": float(raw_amplifier_l2_coef),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": actor_changed,
        "base_actor_checkpoint_written": False,
        "residual_head_checkpoint_count": int(len(seed_summaries)),
        "ppo_used": False,
        "promoted": False,
        "execution": "first_residual_only",
        "seed_view_summary_csv": run_dir / "seed_view_summary.csv",
        "alpha_summary_csv": run_dir / "alpha_summary.csv",
        **pass_rules,
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
    }
    summary["actor_coupling_exact_passed"] = bool(summary["actor_coupling_exact_passed"] and not actor_changed)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a frozen-backbone residual actor-coupling exact probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--shadow-corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--view", type=parse_actor_coupling_view, default="fused_plus_next_hidden")
    parser.add_argument("--seeds", type=parse_seed_list, default=(6740, 6741, 6742))
    parser.add_argument("--alphas", type=parse_alpha_list, default=(0.02, 0.05, 0.10, 0.20, 0.50, 1.00))
    parser.add_argument("--target-gap", type=float, default=0.010)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--head-type", type=parse_head_type, default="mlp")
    parser.add_argument("--max-residual", type=float, default=0.04)
    parser.add_argument("--wrong-target-coef", type=float, default=1.0)
    parser.add_argument("--gap-margin-coef", type=float, default=0.25)
    parser.add_argument("--smoothness-coef", type=float, default=0.05)
    parser.add_argument("--normal-sequence-mean-coef", type=float, default=0.0)
    parser.add_argument("--normal-sequence-mean-threshold", type=float, default=0.002)
    parser.add_argument("--normal-sequence-topk-coef", type=float, default=0.0)
    parser.add_argument("--normal-sequence-topk-threshold", type=float, default=0.0045)
    parser.add_argument("--normal-sequence-topk-fraction", type=float, default=0.10)
    parser.add_argument("--normal-gate-coef", type=float, default=0.0)
    parser.add_argument("--normal-gate-topk-coef", type=float, default=0.0)
    parser.add_argument("--normal-gate-threshold", type=float, default=0.10)
    parser.add_argument("--normal-gate-topk-fraction", type=float, default=0.10)
    parser.add_argument("--normal-first-coef", type=float, default=0.0)
    parser.add_argument("--normal-first-topk-coef", type=float, default=0.0)
    parser.add_argument("--normal-first-threshold", type=float, default=0.004)
    parser.add_argument("--normal-first-topk-fraction", type=float, default=0.10)
    parser.add_argument("--wrong-first-gap-coef", type=float, default=0.0)
    parser.add_argument("--wrong-first-target-gap", type=float, default=0.006)
    parser.add_argument("--branch-specific-gap", action="store_true")
    parser.add_argument("--wrong-sequence-gap-coef", type=float, default=0.0)
    parser.add_argument("--wrong-sequence-target-gap", type=float, default=0.012)
    parser.add_argument("--wrong-hard-coef", type=float, default=0.0)
    parser.add_argument("--wrong-hard-fraction", type=float, default=0.25)
    parser.add_argument("--wrong-gate-open-coef", type=float, default=0.0)
    parser.add_argument("--wrong-gate-target", type=float, default=0.50)
    parser.add_argument("--wrong-gate-margin-coef", type=float, default=0.0)
    parser.add_argument("--wrong-gate-margin", type=float, default=0.30)
    parser.add_argument("--wrong-gate-hard-coef", type=float, default=0.0)
    parser.add_argument("--wrong-gate-hard-fraction", type=float, default=0.25)
    parser.add_argument("--raw-amplifier-l2-coef", type=float, default=0.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="response_amplification_actor_coupling")
    summary = run_response_amplification_actor_coupling(
        checkpoint_path=args.checkpoint,
        shadow_corpus_npz=args.shadow_corpus,
        metadata_csv=args.metadata,
        view=args.view,
        seeds=args.seeds,
        alphas=args.alphas,
        target_gap=args.target_gap,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        head_type=args.head_type,
        max_residual=args.max_residual,
        wrong_target_coef=args.wrong_target_coef,
        gap_margin_coef=args.gap_margin_coef,
        smoothness_coef=args.smoothness_coef,
        normal_sequence_mean_coef=args.normal_sequence_mean_coef,
        normal_sequence_mean_threshold=args.normal_sequence_mean_threshold,
        normal_sequence_topk_coef=args.normal_sequence_topk_coef,
        normal_sequence_topk_threshold=args.normal_sequence_topk_threshold,
        normal_sequence_topk_fraction=args.normal_sequence_topk_fraction,
        normal_gate_coef=args.normal_gate_coef,
        normal_gate_topk_coef=args.normal_gate_topk_coef,
        normal_gate_threshold=args.normal_gate_threshold,
        normal_gate_topk_fraction=args.normal_gate_topk_fraction,
        normal_first_coef=args.normal_first_coef,
        normal_first_topk_coef=args.normal_first_topk_coef,
        normal_first_threshold=args.normal_first_threshold,
        normal_first_topk_fraction=args.normal_first_topk_fraction,
        wrong_first_gap_coef=args.wrong_first_gap_coef,
        wrong_first_target_gap=args.wrong_first_target_gap,
        branch_specific_gap=args.branch_specific_gap,
        wrong_sequence_gap_coef=args.wrong_sequence_gap_coef,
        wrong_sequence_target_gap=args.wrong_sequence_target_gap,
        wrong_hard_coef=args.wrong_hard_coef,
        wrong_hard_fraction=args.wrong_hard_fraction,
        wrong_gate_open_coef=args.wrong_gate_open_coef,
        wrong_gate_target=args.wrong_gate_target,
        wrong_gate_margin_coef=args.wrong_gate_margin_coef,
        wrong_gate_margin=args.wrong_gate_margin,
        wrong_gate_hard_coef=args.wrong_gate_hard_coef,
        wrong_gate_hard_fraction=args.wrong_gate_hard_fraction,
        raw_amplifier_l2_coef=args.raw_amplifier_l2_coef,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"actor_coupling_exact_passed={summary['actor_coupling_exact_passed']}")
    print(f"passed_seeds={summary['passed_seeds']}")
    print(f"best_selected_alpha={summary['best_selected_alpha']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
