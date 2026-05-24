"""Frozen-actor response-amplification shadow objective."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
import torch.nn.functional as F

from autodrift.action_divergent_wrong_history_corpus import (
    action_sequence_distance,
    action_sequence_prefix,
    snapshot_requests,
    _snapshot,
)
from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_repeat import parse_seed_list
from autodrift.bc_v2_head_only_smoke import freeze_actor, masked_weighted_delta_mse, row_delta_mse
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import _hidden_array, parse_surface_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots, replay_outcome_variant
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.sequence_target_miner import parse_int_list
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.wrong_history_feature_separability_audit import batched_recurrent_outputs
from autodrift.wrong_history_fusion_boundary_probe import build_feature_views, parse_views


EPS = 1e-12
VALID_SPLITS = ("train", "source_holdout_validation")


class ResponseAmplifierHead(nn.Module):
    """Training-only residual-sequence head attached to frozen actor features."""

    def __init__(self, feature_dim: int, hidden_dim: int, max_sequence_length: int, action_dim: int = 3) -> None:
        super().__init__()
        self.max_sequence_length = int(max_sequence_length)
        self.action_dim = int(action_dim)
        self.net = nn.Sequential(
            nn.Linear(int(feature_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), self.max_sequence_length * self.action_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        raw = self.net(features)
        return raw.reshape(features.shape[0], self.max_sequence_length, self.action_dim)


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def select_shadow_candidate_rows(
    frame: pd.DataFrame,
    *,
    sequence_lengths: tuple[int, ...],
    max_rows: int,
    max_rows_per_physical_pair: int,
    max_rows_per_left_seed: int,
    min_wrong_first_action_l2: float,
    normal_margin_min: float = 0.0,
    normal_margin_max: float = 1.0,
) -> pd.DataFrame:
    """Filter and source-cap M667 candidate rows for the shadow corpus."""

    required = {
        "normal_success",
        "wrong_success",
        "normal_margin",
        "wrong_first_action_l2",
        "wrong_action_sequence_mean_l2",
        "context_distance",
        "sequence_length",
        "physical_pair_key",
        "left_seed",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("candidate rows missing columns: " + ", ".join(missing))
    mask = (
        _bool_series(frame["normal_success"])
        & _bool_series(frame["wrong_success"])
        & (frame["normal_margin"].astype(float) >= float(normal_margin_min))
        & (frame["normal_margin"].astype(float) <= float(normal_margin_max))
        & (frame["wrong_first_action_l2"].astype(float) >= float(min_wrong_first_action_l2))
        & frame["sequence_length"].astype(int).isin([int(item) for item in sequence_lengths])
    )
    filtered = frame.loc[mask].copy()
    if filtered.empty:
        return filtered.reset_index(drop=True)
    filtered = filtered.sort_values(
        ["wrong_first_action_l2", "wrong_action_sequence_mean_l2", "context_distance"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    kept: list[pd.Series] = []
    per_pair: dict[str, int] = {}
    per_left_seed: dict[int, int] = {}
    for _, row in filtered.iterrows():
        pair_key = str(row["physical_pair_key"])
        left_seed = int(row["left_seed"])
        if per_pair.get(pair_key, 0) >= int(max_rows_per_physical_pair):
            continue
        if per_left_seed.get(left_seed, 0) >= int(max_rows_per_left_seed):
            continue
        kept.append(row)
        per_pair[pair_key] = per_pair.get(pair_key, 0) + 1
        per_left_seed[left_seed] = per_left_seed.get(left_seed, 0) + 1
        if len(kept) >= int(max_rows):
            break
    if not kept:
        return filtered.iloc[0:0].reset_index(drop=True)
    return pd.DataFrame(kept).reset_index(drop=True)


def assign_source_holdout_by_pair(rows: list[dict[str, Any]]) -> None:
    """Assign source-heldout validation by whole physical pair."""

    if not rows:
        return
    pair_keys = sorted({str(row["physical_pair_key"]) for row in rows})
    heldout = {pair for index, pair in enumerate(pair_keys) if index % 5 == 0}
    if len(pair_keys) > 1 and len(heldout) == len(pair_keys):
        heldout = {pair_keys[-1]}
    for row in rows:
        row["split"] = "source_holdout_validation" if str(row["physical_pair_key"]) in heldout else "train"
    if not any(row["split"] == "source_holdout_validation" for row in rows) and len(rows) > 1:
        rows[-1]["split"] = "source_holdout_validation"


def assign_source_balanced_weights(rows: list[dict[str, Any]]) -> None:
    """Assign weights so each source contributes equal total mass."""

    if not rows:
        return
    frame = pd.DataFrame(rows)
    source_counts = frame.groupby("source_index", observed=True).size().to_dict()
    source_count = max(len(source_counts), 1)
    for row in rows:
        count = int(source_counts.get(int(row["source_index"]), 1))
        row["corpus_weight"] = float(1.0 / (source_count * max(count, 1)))
        row["weight"] = row["corpus_weight"]


def amplify_wrong_delta(
    base_delta: np.ndarray,
    *,
    target_wrong_sequence_mean_l2: float,
    max_abs_delta: float,
    min_base_direction_norm: float,
) -> np.ndarray | None:
    """Scale an existing wrong-normal direction without inventing a new one."""

    delta = np.asarray(base_delta, dtype=np.float32)
    if delta.ndim != 2 or delta.shape[1] != 3:
        raise ValueError(f"base_delta must have shape (K, 3), got {delta.shape}")
    step_l2 = np.linalg.norm(delta.astype(np.float64), axis=1)
    mean_l2 = float(step_l2.mean()) if step_l2.size else 0.0
    if not np.isfinite(mean_l2) or mean_l2 <= float(min_base_direction_norm):
        return None
    scale = float(target_wrong_sequence_mean_l2) / max(mean_l2, EPS)
    amplified = np.clip(delta * scale, -float(max_abs_delta), float(max_abs_delta))
    if not np.isfinite(amplified).all():
        return None
    return amplified.astype(np.float32)


def _pad_sequences(sequences: list[np.ndarray], max_len: int) -> tuple[np.ndarray, np.ndarray]:
    padded = np.zeros((len(sequences), int(max_len), 3), dtype=np.float32)
    mask = np.zeros((len(sequences), int(max_len)), dtype=np.float32)
    for index, sequence in enumerate(sequences):
        seq = np.asarray(sequence, dtype=np.float32)
        if seq.ndim != 2 or seq.shape[1] != 3:
            raise ValueError(f"expected (K, 3) sequence, got {seq.shape}")
        padded[index, : seq.shape[0]] = seq
        mask[index, : seq.shape[0]] = 1.0
    return padded, mask


def _first_action(result: dict[str, Any]) -> np.ndarray:
    return np.asarray([result["first_steer"], result["first_throttle"], result["first_brake"]], dtype=np.float32)


def _surface_requests(rows: pd.DataFrame) -> dict[int, set[int]]:
    return snapshot_requests(rows)


def reconstruct_shadow_corpus(
    *,
    selected_rows: pd.DataFrame,
    model: ActorCritic,
    surface_configs: dict[str, Path],
    sequence_lengths: tuple[int, ...],
    target_wrong_sequence_mean_l2: float,
    max_abs_delta: float,
    min_base_direction_norm: float,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, np.ndarray], pd.DataFrame, dict[str, Any]]:
    """Reconstruct snapshots and action sequences from selected candidate rows."""

    if selected_rows.empty:
        raise ValueError("selected candidate rows are empty")
    max_len = max(int(length) for length in sequence_lengths)
    response_dim = response_feature_dim_for_model(model)
    metadata_rows: list[dict[str, Any]] = []
    observations: list[np.ndarray] = []
    normal_hidden: list[np.ndarray] = []
    variant_hidden: list[np.ndarray] = []
    normal_sequences: list[np.ndarray] = []
    wrong_sequences: list[np.ndarray] = []
    target_delta_wrong: list[np.ndarray] = []
    source_rows: list[dict[str, Any]] = []
    rejected_direction_rows = 0
    missing_snapshot_rows = 0

    for surface, group in selected_rows.groupby("surface", observed=True):
        surface_name = str(surface)
        if surface_name not in surface_configs:
            raise ValueError(f"missing surface config for {surface_name}")
        env_config = load_env_config(surface_configs[surface_name])
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=_surface_requests(group),
            device=device,
        )
        for _, candidate in group.reset_index(drop=True).iterrows():
            left = _snapshot(snapshots, int(candidate["left_seed"]), int(candidate["left_step"]))
            right = _snapshot(snapshots, int(candidate["right_seed"]), int(candidate["right_step"]))
            if left is None or right is None:
                missing_snapshot_rows += 1
                continue
            sequence_length = int(candidate["sequence_length"])
            normal, normal_actions = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant="normal",
                response_dim=response_dim,
                variant_hidden=None,
                normal_first_action=None,
                normal_actions=None,
                max_continuation_steps=max(int(max_continuation_steps), max_len),
                device=device,
            )
            normal_first = _first_action(normal)
            wrong, wrong_actions = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant="wrong_matched_history",
                response_dim=response_dim,
                variant_hidden=right.hidden,
                normal_first_action=normal_first,
                normal_actions=normal_actions,
                max_continuation_steps=max(int(max_continuation_steps), max_len),
                device=device,
            )
            normal_seq = action_sequence_prefix(normal_actions, sequence_length)
            wrong_seq = action_sequence_prefix(wrong_actions, sequence_length)
            amplified = amplify_wrong_delta(
                wrong_seq - normal_seq,
                target_wrong_sequence_mean_l2=target_wrong_sequence_mean_l2,
                max_abs_delta=max_abs_delta,
                min_base_direction_norm=min_base_direction_norm,
            )
            if amplified is None:
                rejected_direction_rows += 1
                continue
            distances = action_sequence_distance(normal_seq, wrong_seq)
            amplified_distances = action_sequence_distance(np.zeros_like(amplified), amplified)
            row = {
                "source_index": int(candidate["source_index"]),
                "physical_pair_key": str(candidate["physical_pair_key"]),
                "grid_name": "response_amplification_shadow",
                "surface": surface_name,
                "target": str(candidate["target"]),
                "variant": "wrong_matched_history",
                "split": "unassigned",
                "preferred_sequence_source": "normal_policy_base",
                "left_seed": int(candidate["left_seed"]),
                "right_seed": int(candidate["right_seed"]),
                "left_step": int(candidate["left_step"]),
                "right_step": int(candidate["right_step"]),
                "sequence_length": sequence_length,
                "normal_success": bool(normal.get("success", False)),
                "wrong_success": bool(wrong.get("success", False)),
                "normal_collision": bool(normal.get("collision", False)),
                "wrong_collision": bool(wrong.get("collision", False)),
                "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                "wrong_terminal_reason": str(wrong.get("terminal_reason", "")),
                "normal_margin": float(normal.get("min_clearance_margin", np.nan)),
                "wrong_margin": float(wrong.get("min_clearance_margin", np.nan)),
                "wrong_first_action_l2": float(distances["first_l2"]),
                "wrong_action_sequence_mean_l2": float(distances["mean_l2"]),
                "wrong_action_sequence_max_l2": float(distances["max_l2"]),
                "target_wrong_sequence_mean_l2_actual": float(amplified_distances["mean_l2"]),
                "target_wrong_sequence_max_l2_actual": float(amplified_distances["max_l2"]),
                "original_candidate_context_distance": float(candidate.get("context_distance", np.nan)),
                "original_candidate_response_distance": float(candidate.get("response_distance", np.nan)),
                "original_candidate_hidden_distance": float(candidate.get("hidden_distance", np.nan)),
            }
            metadata_rows.append(row)
            observations.append(np.asarray(left.observation, dtype=np.float32).copy())
            normal_hidden.append(_hidden_array(left.hidden))
            variant_hidden.append(_hidden_array(right.hidden))
            normal_sequences.append(normal_seq)
            wrong_sequences.append(wrong_seq)
            target_delta_wrong.append(amplified)
            source_rows.append(row)

    assign_source_holdout_by_pair(metadata_rows)
    assign_source_balanced_weights(metadata_rows)

    if not metadata_rows:
        raise ValueError("no shadow corpus rows survived reconstruction")
    normal_base, mask = _pad_sequences(normal_sequences, max_len)
    wrong_base, _ = _pad_sequences(wrong_sequences, max_len)
    wrong_target_delta_padded, _ = _pad_sequences(target_delta_wrong, max_len)
    target_sequence = normal_base.copy()
    metadata = pd.DataFrame(metadata_rows).reset_index(drop=True)
    arrays: dict[str, np.ndarray] = {
        "observation": np.asarray(observations, dtype=np.float32),
        "normal_hidden": np.asarray(normal_hidden, dtype=np.float32),
        "variant_hidden": np.asarray(variant_hidden, dtype=np.float32),
        "normal_base_action_sequence": normal_base,
        "variant_base_action_sequence": wrong_base,
        "normal_action_sequence": normal_base,
        "wrong_action_sequence": wrong_base,
        "target_action_sequence": target_sequence,
        "target_delta_normal": np.zeros_like(normal_base, dtype=np.float32),
        "target_delta_wrong": wrong_target_delta_padded.astype(np.float32),
        "wrong_target_action_sequence": (normal_base + wrong_target_delta_padded).astype(np.float32),
        "sequence_mask": mask,
        "variant_base_action": wrong_base[:, 0, :],
        "weight": metadata["corpus_weight"].astype(float).to_numpy(dtype=np.float32),
        "row_id": np.arange(len(metadata_rows), dtype=np.int64),
        "source_index": metadata["source_index"].astype(int).to_numpy(dtype=np.int64),
        "sequence_length": metadata["sequence_length"].astype(int).to_numpy(dtype=np.int64),
    }
    validate_sequence_corpus_contract(arrays)
    validate_metadata_alignment(arrays, metadata)
    reconstruction_summary = {
        "selected_candidate_rows": int(len(selected_rows)),
        "shadow_corpus_rows": int(len(metadata_rows)),
        "missing_snapshot_rows": int(missing_snapshot_rows),
        "rejected_direction_rows": int(rejected_direction_rows),
        "source_count": int(metadata["source_index"].nunique()),
        "physical_pair_count": int(metadata["physical_pair_key"].nunique()),
        "source_holdout_nonempty": bool((metadata["split"] == "source_holdout_validation").any()),
        "train_rows": int((metadata["split"] == "train").sum()),
        "source_holdout_rows": int((metadata["split"] == "source_holdout_validation").sum()),
    }
    return arrays, metadata, reconstruction_summary


def save_shadow_corpus(output_npz: Path, arrays: dict[str, np.ndarray]) -> None:
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_npz, **arrays)


def _split_indices(metadata: pd.DataFrame, split: str) -> np.ndarray:
    return np.flatnonzero(metadata["split"].astype(str).to_numpy() == split).astype(np.int64)


def _tensor_batch(
    arrays: dict[str, np.ndarray],
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    return {
        "features_normal": torch.as_tensor(features_normal, dtype=torch.float32, device=device),
        "features_variant": torch.as_tensor(features_variant, dtype=torch.float32, device=device),
        "target_delta_normal": torch.as_tensor(arrays["target_delta_normal"], dtype=torch.float32, device=device),
        "target_delta_wrong": torch.as_tensor(arrays["target_delta_wrong"], dtype=torch.float32, device=device),
        "mask": torch.as_tensor(arrays["sequence_mask"], dtype=torch.float32, device=device),
        "weight": torch.as_tensor(arrays["weight"], dtype=torch.float32, device=device),
    }


def _weighted_mean(values: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    return (values * weight).sum() / torch.clamp(weight.sum(), min=EPS)


def _masked_mean_step_l2(delta: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    step_l2 = torch.linalg.norm(delta, dim=2) * mask
    valid = torch.clamp(mask.sum(dim=1), min=1.0)
    return step_l2.sum(dim=1) / valid


def _gap_margin_loss(prediction_normal: torch.Tensor, prediction_wrong: torch.Tensor, mask: torch.Tensor, weight: torch.Tensor, target_gap: float) -> torch.Tensor:
    row_gap = _masked_mean_step_l2(prediction_wrong - prediction_normal, mask)
    # Scale the smooth hinge by the target gap so this diagnostic term does not
    # dominate the small residual-MSE anchors when target gaps are centimeter-scale.
    scaled = F.softplus(float(target_gap) - row_gap) * max(abs(float(target_gap)), 1e-6)
    return _weighted_mean(scaled, weight)


def _loss_components(
    head: ResponseAmplifierHead,
    batch: dict[str, torch.Tensor],
    indices: np.ndarray,
    *,
    wrong_target_coef: float,
    gap_margin_coef: float,
    zero_regularizer_coef: float,
    target_gap: float,
) -> dict[str, torch.Tensor]:
    index_t = torch.as_tensor(indices, dtype=torch.long, device=batch["mask"].device)
    pred_normal = head(batch["features_normal"].index_select(0, index_t))
    pred_wrong = head(batch["features_variant"].index_select(0, index_t))
    mask = batch["mask"].index_select(0, index_t)
    weight = batch["weight"].index_select(0, index_t)
    normal_target = batch["target_delta_normal"].index_select(0, index_t)
    wrong_target = batch["target_delta_wrong"].index_select(0, index_t)
    normal_anchor = masked_weighted_delta_mse(pred_normal, normal_target, mask, weight)
    wrong_target_loss = masked_weighted_delta_mse(pred_wrong, wrong_target, mask, weight)
    gap_loss = _gap_margin_loss(pred_normal, pred_wrong, mask, weight, target_gap)
    zero_regularizer = masked_weighted_delta_mse(pred_normal, torch.zeros_like(normal_target), mask, weight)
    total = (
        normal_anchor
        + float(wrong_target_coef) * wrong_target_loss
        + float(gap_margin_coef) * gap_loss
        + float(zero_regularizer_coef) * zero_regularizer
    )
    return {
        "total_loss": total,
        "normal_anchor_mse": normal_anchor,
        "wrong_target_mse": wrong_target_loss,
        "gap_margin_loss": gap_loss,
        "zero_regularizer_mse": zero_regularizer,
    }


def _predict(head: ResponseAmplifierHead, features: np.ndarray, device: torch.device, batch_size: int = 4096) -> np.ndarray:
    chunks: list[np.ndarray] = []
    head.eval()
    with torch.no_grad():
        for start in range(0, features.shape[0], int(batch_size)):
            end = min(start + int(batch_size), features.shape[0])
            tensor = torch.as_tensor(features[start:end], dtype=torch.float32, device=device)
            chunks.append(head(tensor).detach().cpu().numpy().astype(np.float32))
    return np.concatenate(chunks, axis=0)


def _row_mean_step_l2(delta: np.ndarray, mask: np.ndarray) -> np.ndarray:
    step_l2 = np.linalg.norm(delta.astype(np.float64), axis=2) * mask.astype(np.float64)
    valid = np.maximum(mask.astype(np.float64).sum(axis=1), 1.0)
    return step_l2.sum(axis=1) / valid


def summarize_shadow_predictions(
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    *,
    prediction_normal: np.ndarray,
    prediction_wrong: np.ndarray,
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    mask = arrays["sequence_mask"]
    weights = arrays["weight"].astype(np.float64)
    normal_target = arrays["target_delta_normal"]
    wrong_target = arrays["target_delta_wrong"]
    base_gap = _row_mean_step_l2(arrays["wrong_action_sequence"] - arrays["normal_action_sequence"], mask)
    predicted_gap = _row_mean_step_l2(prediction_wrong - prediction_normal, mask)
    normal_delta_l2 = _row_mean_step_l2(prediction_normal, mask)
    wrong_delta_l2 = _row_mean_step_l2(prediction_wrong, mask)
    normal_mse = row_delta_mse(prediction_normal, normal_target, mask)
    wrong_mse = row_delta_mse(prediction_wrong, wrong_target, mask)
    zero_wrong_mse = row_delta_mse(np.zeros_like(wrong_target), wrong_target, mask)
    rows = pd.DataFrame(
        {
            "row_id": arrays["row_id"].astype(int),
            "source_index": arrays["source_index"].astype(int),
            "split": metadata["split"].astype(str).to_numpy(),
            "surface": metadata["surface"].astype(str).to_numpy(),
            "target": metadata["target"].astype(str).to_numpy(),
            "variant": metadata["variant"].astype(str).to_numpy(),
            "grid_name": metadata["grid_name"].astype(str).to_numpy(),
            "physical_pair_key": metadata["physical_pair_key"].astype(str).to_numpy(),
            "sequence_length": arrays["sequence_length"].astype(int),
            "weight": weights,
            "normal_delta_l2": normal_delta_l2,
            "wrong_delta_l2": wrong_delta_l2,
            "predicted_normal_wrong_gap_l2": predicted_gap,
            "baseline_actor_sequence_gap_l2": base_gap,
            "normal_anchor_mse": normal_mse,
            "wrong_target_mse": wrong_mse,
            "zero_head_wrong_target_mse": zero_wrong_mse,
        }
    )
    rows["weighted_normal_anchor_mse"] = rows["weight"] * rows["normal_anchor_mse"]
    rows["weighted_wrong_target_mse"] = rows["weight"] * rows["wrong_target_mse"]
    rows["weighted_zero_head_wrong_target_mse"] = rows["weight"] * rows["zero_head_wrong_target_mse"]

    def group_summary(group_column: str) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for value, group in rows.groupby(group_column, observed=True, dropna=False):
            weight_sum = float(group["weight"].sum())
            predicted_gap_mean = float((group["weight"] * group["predicted_normal_wrong_gap_l2"]).sum() / max(weight_sum, EPS))
            baseline_gap_mean = float((group["weight"] * group["baseline_actor_sequence_gap_l2"]).sum() / max(weight_sum, EPS))
            wrong_mse_mean = float(group["weighted_wrong_target_mse"].sum() / max(weight_sum, EPS))
            zero_wrong_mse_mean = float(group["weighted_zero_head_wrong_target_mse"].sum() / max(weight_sum, EPS))
            summaries.append(
                {
                    group_column: value,
                    "rows": int(len(group)),
                    "sources": int(group["source_index"].nunique()),
                    "physical_pairs": int(group["physical_pair_key"].nunique()),
                    "weight_sum": weight_sum,
                    "normal_delta_l2_mean": float((group["weight"] * group["normal_delta_l2"]).sum() / max(weight_sum, EPS)),
                    "normal_delta_l2_p95": float(np.percentile(group["normal_delta_l2"].to_numpy(dtype=float), 95)),
                    "normal_delta_l2_max": float(group["normal_delta_l2"].max()),
                    "wrong_delta_l2_mean": float((group["weight"] * group["wrong_delta_l2"]).sum() / max(weight_sum, EPS)),
                    "predicted_normal_wrong_gap_l2_mean": predicted_gap_mean,
                    "predicted_normal_wrong_gap_l2_p10": float(
                        np.percentile(group["predicted_normal_wrong_gap_l2"].to_numpy(dtype=float), 10)
                    ),
                    "baseline_actor_sequence_gap_l2_mean": baseline_gap_mean,
                    "gap_improvement_ratio": predicted_gap_mean / max(baseline_gap_mean, EPS),
                    "normal_anchor_mse": float(group["weighted_normal_anchor_mse"].sum() / max(weight_sum, EPS)),
                    "wrong_target_mse": wrong_mse_mean,
                    "zero_head_wrong_target_mse": zero_wrong_mse_mean,
                    "wrong_target_mse_improvement": (zero_wrong_mse_mean - wrong_mse_mean) / max(zero_wrong_mse_mean, EPS),
                    "surfaces": ";".join(sorted(group["surface"].astype(str).unique())),
                    "targets": ";".join(sorted(group["target"].astype(str).unique())),
                }
            )
        return summaries

    return rows, group_summary("source_index"), group_summary("split"), group_summary("target")


def shadow_view_seed_passes(summary: dict[str, Any]) -> bool:
    return bool(
        summary["source_holdout_normal_delta_l2_mean"] <= 0.0025
        and summary["source_holdout_normal_delta_l2_p95"] <= 0.0060
        and summary["source_holdout_predicted_normal_wrong_gap_l2_mean"] >= 0.010
        and summary["source_holdout_predicted_normal_wrong_gap_l2_p10"] >= 0.004
        and summary["source_holdout_gap_improvement_ratio"] >= 3.0
        and summary["source_holdout_wrong_target_mse_improvement"] >= 0.50
    )


def train_response_amplifier_head(
    *,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    hidden_dim: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    wrong_target_coef: float,
    gap_margin_coef: float,
    zero_regularizer_coef: float,
    target_gap: float,
    device: torch.device,
) -> tuple[ResponseAmplifierHead, list[dict[str, Any]], dict[str, Any], dict[str, np.ndarray]]:
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_indices = _split_indices(metadata, "train")
    val_indices = _split_indices(metadata, "source_holdout_validation")
    if train_indices.size == 0 or val_indices.size == 0:
        raise ValueError("both train and source_holdout_validation splits are required")
    if features_normal.shape[0] != contract.rows or features_variant.shape[0] != contract.rows:
        raise ValueError("feature rows must match corpus rows")

    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    head = ResponseAmplifierHead(
        feature_dim=int(features_normal.shape[1]),
        hidden_dim=int(hidden_dim),
        max_sequence_length=contract.max_sequence_length,
        action_dim=contract.action_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    metric_rows: list[dict[str, Any]] = []
    log_interval = max(1, int(epochs) // 10)

    def append_metrics(epoch: int) -> None:
        with torch.no_grad():
            for split, indices in (("train", train_indices), ("source_holdout_validation", val_indices)):
                losses = _loss_components(
                    head,
                    batch,
                    indices,
                    wrong_target_coef=wrong_target_coef,
                    gap_margin_coef=gap_margin_coef,
                    zero_regularizer_coef=zero_regularizer_coef,
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
        losses = _loss_components(
            head,
            batch,
            train_indices,
            wrong_target_coef=wrong_target_coef,
            gap_margin_coef=gap_margin_coef,
            zero_regularizer_coef=zero_regularizer_coef,
            target_gap=target_gap,
        )
        losses["total_loss"].backward()
        optimizer.step()
        if epoch == int(epochs) or epoch % log_interval == 0:
            append_metrics(epoch)

    prediction_normal = _predict(head, features_normal, device)
    prediction_wrong = _predict(head, features_variant, device)
    row_metrics, source_summary, split_summary, target_summary = summarize_shadow_predictions(
        arrays,
        metadata,
        prediction_normal=prediction_normal,
        prediction_wrong=prediction_wrong,
    )
    split_frame = pd.DataFrame(split_summary).set_index("split")
    source_holdout = split_frame.loc["source_holdout_validation"]
    train = split_frame.loc["train"]
    summary = {
        "seed": int(seed),
        "feature_dim": int(features_normal.shape[1]),
        "hidden_dim": int(hidden_dim),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "zero_regularizer_coef": float(zero_regularizer_coef),
        "target_gap": float(target_gap),
        "train_normal_delta_l2_mean": float(train["normal_delta_l2_mean"]),
        "train_predicted_normal_wrong_gap_l2_mean": float(train["predicted_normal_wrong_gap_l2_mean"]),
        "train_gap_improvement_ratio": float(train["gap_improvement_ratio"]),
        "source_holdout_normal_delta_l2_mean": float(source_holdout["normal_delta_l2_mean"]),
        "source_holdout_normal_delta_l2_p95": float(source_holdout["normal_delta_l2_p95"]),
        "source_holdout_predicted_normal_wrong_gap_l2_mean": float(
            source_holdout["predicted_normal_wrong_gap_l2_mean"]
        ),
        "source_holdout_predicted_normal_wrong_gap_l2_p10": float(
            source_holdout["predicted_normal_wrong_gap_l2_p10"]
        ),
        "source_holdout_baseline_actor_sequence_gap_l2_mean": float(
            source_holdout["baseline_actor_sequence_gap_l2_mean"]
        ),
        "source_holdout_gap_improvement_ratio": float(source_holdout["gap_improvement_ratio"]),
        "source_holdout_wrong_target_mse": float(source_holdout["wrong_target_mse"]),
        "source_holdout_zero_head_wrong_target_mse": float(source_holdout["zero_head_wrong_target_mse"]),
        "source_holdout_wrong_target_mse_improvement": float(source_holdout["wrong_target_mse_improvement"]),
    }
    summary["shadow_view_seed_passed"] = shadow_view_seed_passes(summary)
    return head, metric_rows, summary, {
        "prediction_normal": prediction_normal,
        "prediction_wrong": prediction_wrong,
        "row_metrics": row_metrics,
        "source_summary": source_summary,
        "split_summary": split_summary,
        "target_summary": target_summary,
    }


def apply_shadow_pass_rules(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    view_counts: dict[str, int] = {}
    for row in seed_summaries:
        view = str(row["view"])
        view_counts.setdefault(view, 0)
        if view != "fused" and bool(row.get("shadow_view_seed_passed", False)):
            view_counts[view] += 1
    passed_views = [view for view, count in sorted(view_counts.items()) if view != "fused" and count >= 2]
    return {
        "shadow_passed": bool(passed_views),
        "passed_views": passed_views,
        "view_pass_counts": view_counts,
    }


def run_response_amplification_shadow(
    *,
    checkpoint_path: Path,
    candidate_rows_csv: Path,
    surface_configs: dict[str, Path],
    views: tuple[str, ...],
    seeds: tuple[int, ...],
    sequence_lengths: tuple[int, ...],
    max_rows: int,
    max_rows_per_physical_pair: int,
    max_rows_per_left_seed: int,
    min_wrong_first_action_l2: float,
    target_wrong_sequence_mean_l2: float,
    max_abs_delta: float,
    min_base_direction_norm: float,
    target_gap: float,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    wrong_target_coef: float,
    gap_margin_coef: float,
    zero_regularizer_coef: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
    batch_size: int = 1024,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    freeze_actor(model)
    before_checksum = model_parameter_checksum(model)
    candidate_frame = pd.read_csv(candidate_rows_csv)
    selected = select_shadow_candidate_rows(
        candidate_frame,
        sequence_lengths=sequence_lengths,
        max_rows=max_rows,
        max_rows_per_physical_pair=max_rows_per_physical_pair,
        max_rows_per_left_seed=max_rows_per_left_seed,
        min_wrong_first_action_l2=min_wrong_first_action_l2,
    )
    arrays, metadata, reconstruction_summary = reconstruct_shadow_corpus(
        selected_rows=selected,
        model=model,
        surface_configs=surface_configs,
        sequence_lengths=sequence_lengths,
        target_wrong_sequence_mean_l2=target_wrong_sequence_mean_l2,
        max_abs_delta=max_abs_delta,
        min_base_direction_norm=min_base_direction_norm,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
    )
    save_shadow_corpus(run_dir / "shadow_corpus.npz", arrays)
    write_csv_rows(run_dir / "shadow_metadata.csv", metadata.to_dict(orient="records"))
    validate_metadata_alignment(load_sequence_corpus_npz(run_dir / "shadow_corpus.npz"), load_metadata_csv(run_dir / "shadow_metadata.csv", expected_rows=len(metadata)))
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
    feature_views = build_feature_views(normal_outputs, variant_outputs, views)
    seed_summaries: list[dict[str, Any]] = []
    train_metric_rows: list[dict[str, Any]] = []
    row_metric_rows: list[dict[str, Any]] = []
    source_metric_rows: list[dict[str, Any]] = []
    split_metric_rows: list[dict[str, Any]] = []
    target_metric_rows: list[dict[str, Any]] = []
    view_feature_dims: dict[str, int] = {}

    for view_name, (features_normal, features_variant) in feature_views.items():
        view_feature_dims[view_name] = int(features_normal.shape[1])
        for seed in seeds:
            seed_dir = run_dir / f"seed_{int(seed)}" / f"view_{view_name}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            head, metrics, summary, predictions = train_response_amplifier_head(
                arrays=arrays,
                metadata=metadata,
                features_normal=features_normal,
                features_variant=features_variant,
                hidden_dim=hidden_dim,
                epochs=epochs,
                learning_rate=learning_rate,
                weight_decay=weight_decay,
                seed=int(seed),
                wrong_target_coef=wrong_target_coef,
                gap_margin_coef=gap_margin_coef,
                zero_regularizer_coef=zero_regularizer_coef,
                target_gap=target_gap,
                device=resolved_device,
            )
            head_path = seed_dir / "response_amplifier_head.pt"
            torch.save(
                {
                    "head_state": head.state_dict(),
                    "view": view_name,
                    "seed": int(seed),
                    "feature_dim": int(features_normal.shape[1]),
                    "hidden_dim": int(hidden_dim),
                    "max_sequence_length": int(arrays["sequence_mask"].shape[1]),
                    "action_dim": 3,
                },
                head_path,
            )
            summary.update(
                {
                    "view": view_name,
                    "view_feature_dim": int(features_normal.shape[1]),
                    "head_checkpoint": str(head_path),
                }
            )
            seed_summaries.append(summary)
            train_metric_rows.extend({"view": view_name, "seed": int(seed), **row} for row in metrics)
            row_metric_rows.extend(
                {"view": view_name, "seed": int(seed), **row}
                for row in predictions["row_metrics"].to_dict(orient="records")
            )
            source_metric_rows.extend({"view": view_name, "seed": int(seed), **row} for row in predictions["source_summary"])
            split_metric_rows.extend({"view": view_name, "seed": int(seed), **row} for row in predictions["split_summary"])
            target_metric_rows.extend({"view": view_name, "seed": int(seed), **row} for row in predictions["target_summary"])

    after_checksum = model_parameter_checksum(model)
    actor_changed = bool(before_checksum != after_checksum)
    for row in seed_summaries:
        row["actor_parameters_changed"] = actor_changed
        row["actor_checkpoint_written"] = False
    pass_rules = apply_shadow_pass_rules(seed_summaries)
    write_csv_rows(run_dir / "seed_view_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "train_metrics.csv", train_metric_rows)
    write_csv_rows(run_dir / "row_shadow_metrics.csv", row_metric_rows)
    write_csv_rows(run_dir / "source_shadow_summary.csv", source_metric_rows)
    write_csv_rows(run_dir / "split_shadow_summary.csv", split_metric_rows)
    write_csv_rows(run_dir / "target_shadow_summary.csv", target_metric_rows)
    balance_frame = metadata.copy()
    balance_frame["weight"] = balance_frame["corpus_weight"].astype(float)
    balance = source_weight_balance(balance_frame)
    summary = {
        "run_type": "response_amplification_shadow",
        "checkpoint": checkpoint_path,
        "candidate_rows_csv": candidate_rows_csv,
        "surface_configs": surface_configs,
        "views": list(views),
        "seeds": [int(seed) for seed in seeds],
        "sequence_lengths": sequence_lengths,
        "selected_candidate_rows": int(len(selected)),
        **reconstruction_summary,
        "view_feature_dims": view_feature_dims,
        "target_wrong_sequence_mean_l2": float(target_wrong_sequence_mean_l2),
        "max_abs_delta": float(max_abs_delta),
        "target_gap": float(target_gap),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "zero_regularizer_coef": float(zero_regularizer_coef),
        "source_weight_balance": balance,
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": actor_changed,
        "actor_checkpoint_written": False,
        "head_checkpoint_count": int(len(seed_summaries)),
        "shadow_corpus_npz": run_dir / "shadow_corpus.npz",
        "shadow_metadata_csv": run_dir / "shadow_metadata.csv",
        "seed_view_summary_csv": run_dir / "seed_view_summary.csv",
        **pass_rules,
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    summary["shadow_passed"] = bool(summary["shadow_passed"] and not actor_changed)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a frozen-actor response-amplification shadow objective.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--candidate-rows", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--views", type=parse_views, default=("fused", "next_hidden", "fused_plus_next_hidden"))
    parser.add_argument("--seeds", type=parse_seed_list, default=(6700, 6701, 6702))
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(5, 7, 9))
    parser.add_argument("--max-rows", type=int, default=768)
    parser.add_argument("--max-rows-per-physical-pair", type=int, default=18)
    parser.add_argument("--max-rows-per-left-seed", type=int, default=36)
    parser.add_argument("--min-wrong-first-action-l2", type=float, default=0.002)
    parser.add_argument("--target-wrong-sequence-mean-l2", type=float, default=0.012)
    parser.add_argument("--max-abs-delta", type=float, default=0.030)
    parser.add_argument("--min-base-direction-norm", type=float, default=1e-6)
    parser.add_argument("--target-gap", type=float, default=0.010)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--wrong-target-coef", type=float, default=1.0)
    parser.add_argument("--gap-margin-coef", type=float, default=0.25)
    parser.add_argument("--zero-regularizer-coef", type=float, default=0.1)
    parser.add_argument("--max-continuation-steps", type=int, default=9)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="response_amplification_shadow")
    summary = run_response_amplification_shadow(
        checkpoint_path=args.checkpoint,
        candidate_rows_csv=args.candidate_rows,
        surface_configs={item.surface: item.env_config_path for item in args.surface_config},
        views=args.views,
        seeds=args.seeds,
        sequence_lengths=args.sequence_lengths,
        max_rows=args.max_rows,
        max_rows_per_physical_pair=args.max_rows_per_physical_pair,
        max_rows_per_left_seed=args.max_rows_per_left_seed,
        min_wrong_first_action_l2=args.min_wrong_first_action_l2,
        target_wrong_sequence_mean_l2=args.target_wrong_sequence_mean_l2,
        max_abs_delta=args.max_abs_delta,
        min_base_direction_norm=args.min_base_direction_norm,
        target_gap=args.target_gap,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        wrong_target_coef=args.wrong_target_coef,
        gap_margin_coef=args.gap_margin_coef,
        zero_regularizer_coef=args.zero_regularizer_coef,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"shadow_passed={summary['shadow_passed']}")
    print(f"passed_views={summary['passed_views']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
