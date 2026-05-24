"""No-training audit for wrong-history feature separability."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device


EPS = 1e-12
DISTANCE_COLUMNS = (
    "raw_hidden_l2",
    "raw_hidden_cosine_distance",
    "next_hidden_l2",
    "next_hidden_cosine_distance",
    "fused_feature_l2",
    "fused_feature_cosine_distance",
    "actor_mean_l2",
    "actor_tanh_action_l2",
    "next_hidden_retention_ratio",
    "feature_retention_ratio",
    "action_feature_ratio",
    "sequence_delta_mse",
    "sequence_delta_mean_step_l2",
    "sequence_delta_max_step_l2",
    "normal_base_action_reconstruction_l2",
    "variant_base_action_reconstruction_l2",
)


def row_l2(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape != right.shape:
        raise ValueError("left and right must have the same shape")
    return np.linalg.norm(left.astype(np.float64) - right.astype(np.float64), axis=1)


def row_cosine_distance(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape != right.shape:
        raise ValueError("left and right must have the same shape")
    left64 = left.astype(np.float64)
    right64 = right.astype(np.float64)
    left_norm = np.linalg.norm(left64, axis=1)
    right_norm = np.linalg.norm(right64, axis=1)
    denom = left_norm * right_norm
    dot = np.sum(left64 * right64, axis=1)
    cosine = np.divide(dot, denom, out=np.zeros_like(dot), where=denom > EPS)
    both_zero = (left_norm <= EPS) & (right_norm <= EPS)
    distance = 1.0 - np.clip(cosine, -1.0, 1.0)
    distance[both_zero] = 0.0
    return distance


def safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return numerator.astype(np.float64) / np.maximum(denominator.astype(np.float64), EPS)


def masked_sequence_delta_metrics(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    target = arrays["target_action_sequence"].astype(np.float64)
    base = arrays["normal_base_action_sequence"].astype(np.float64)
    mask = arrays["sequence_mask"].astype(np.float64)
    delta = (target - base) * mask[:, :, None]
    valid_steps = np.maximum(mask.sum(axis=1), 1.0)
    step_l2 = np.linalg.norm(delta, axis=2)
    return {
        "sequence_delta_mse": np.square(delta).sum(axis=(1, 2)) / np.maximum(valid_steps * target.shape[2], 1.0),
        "sequence_delta_mean_step_l2": step_l2.sum(axis=1) / valid_steps,
        "sequence_delta_max_step_l2": step_l2.max(axis=1),
    }


def batched_recurrent_outputs(
    model: ActorCritic,
    observations: np.ndarray,
    hidden: np.ndarray,
    *,
    device: torch.device,
    batch_size: int = 1024,
) -> dict[str, np.ndarray]:
    features: list[np.ndarray] = []
    next_hidden: list[np.ndarray] = []
    means: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, observations.shape[0], int(batch_size)):
            end = min(start + int(batch_size), observations.shape[0])
            obs_t = torch.as_tensor(observations[start:end], dtype=torch.float32, device=device)
            hidden_t = torch.as_tensor(hidden[start:end], dtype=torch.float32, device=device)
            feature_t, next_hidden_t = model.recurrent_features_tensor(obs_t, hidden_t)
            mean_t = model.actor_mean(feature_t)
            action_t = torch.tanh(mean_t)
            features.append(feature_t.detach().cpu().numpy().astype(np.float32))
            next_hidden.append(next_hidden_t.detach().cpu().numpy().astype(np.float32))
            means.append(mean_t.detach().cpu().numpy().astype(np.float32))
            actions.append(action_t.detach().cpu().numpy().astype(np.float32))
    return {
        "features": np.concatenate(features, axis=0),
        "next_hidden": np.concatenate(next_hidden, axis=0),
        "actor_mean": np.concatenate(means, axis=0),
        "actor_action": np.concatenate(actions, axis=0),
    }


def compute_row_feature_metrics(
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    *,
    normal_outputs: dict[str, np.ndarray],
    variant_outputs: dict[str, np.ndarray],
) -> pd.DataFrame:
    rows = int(arrays["observation"].shape[0])
    for name, output in (("normal", normal_outputs), ("variant", variant_outputs)):
        for key in ("features", "next_hidden", "actor_mean", "actor_action"):
            if output[key].shape[0] != rows:
                raise ValueError(f"{name} {key} row count mismatch")

    raw_hidden_l2 = row_l2(arrays["normal_hidden"], arrays["variant_hidden"])
    next_hidden_l2 = row_l2(normal_outputs["next_hidden"], variant_outputs["next_hidden"])
    fused_feature_l2 = row_l2(normal_outputs["features"], variant_outputs["features"])
    actor_action_l2 = row_l2(normal_outputs["actor_action"], variant_outputs["actor_action"])
    sequence = masked_sequence_delta_metrics(arrays)
    normal_base = arrays["normal_base_action_sequence"][:, 0, :].astype(np.float64)
    variant_base = arrays["variant_base_action"].astype(np.float64)
    normal_action = normal_outputs["actor_action"].astype(np.float64)
    variant_action = variant_outputs["actor_action"].astype(np.float64)
    weights = arrays["weight"].astype(np.float64)
    return pd.DataFrame(
        {
            "row_id": arrays["row_id"].astype(int),
            "source_index": arrays["source_index"].astype(int),
            "split": metadata["split"].astype(str).to_numpy(),
            "surface": metadata["surface"].astype(str).to_numpy(),
            "target": metadata["target"].astype(str).to_numpy(),
            "variant": metadata["variant"].astype(str).to_numpy(),
            "grid_name": metadata["grid_name"].astype(str).to_numpy(),
            "sequence_length": arrays["sequence_length"].astype(int),
            "weight": weights,
            "raw_hidden_l2": raw_hidden_l2,
            "raw_hidden_cosine_distance": row_cosine_distance(arrays["normal_hidden"], arrays["variant_hidden"]),
            "next_hidden_l2": next_hidden_l2,
            "next_hidden_cosine_distance": row_cosine_distance(
                normal_outputs["next_hidden"],
                variant_outputs["next_hidden"],
            ),
            "fused_feature_l2": fused_feature_l2,
            "fused_feature_cosine_distance": row_cosine_distance(
                normal_outputs["features"],
                variant_outputs["features"],
            ),
            "actor_mean_l2": row_l2(normal_outputs["actor_mean"], variant_outputs["actor_mean"]),
            "actor_tanh_action_l2": actor_action_l2,
            "next_hidden_retention_ratio": safe_ratio(next_hidden_l2, raw_hidden_l2),
            "feature_retention_ratio": safe_ratio(fused_feature_l2, raw_hidden_l2),
            "action_feature_ratio": safe_ratio(actor_action_l2, fused_feature_l2),
            "sequence_delta_mse": sequence["sequence_delta_mse"],
            "sequence_delta_mean_step_l2": sequence["sequence_delta_mean_step_l2"],
            "sequence_delta_max_step_l2": sequence["sequence_delta_max_step_l2"],
            "normal_base_action_reconstruction_l2": np.linalg.norm(normal_action - normal_base, axis=1),
            "variant_base_action_reconstruction_l2": np.linalg.norm(variant_action - variant_base, axis=1),
        }
    )


def weighted_mean(group: pd.DataFrame, column: str) -> float:
    weight = group["weight"].astype(float)
    return float((weight * group[column].astype(float)).sum() / max(float(weight.sum()), EPS))


def weighted_median(group: pd.DataFrame, column: str) -> float:
    values = group[column].astype(float).to_numpy()
    weights = group["weight"].astype(float).to_numpy()
    if values.size == 0:
        return float("nan")
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cutoff = 0.5 * float(sorted_weights.sum())
    index = int(np.searchsorted(np.cumsum(sorted_weights), cutoff, side="left"))
    index = min(index, sorted_values.size - 1)
    return float(sorted_values[index])


def summarize_feature_group(rows: pd.DataFrame, group_columns: str | Iterable[str]) -> list[dict[str, Any]]:
    columns = [group_columns] if isinstance(group_columns, str) else list(group_columns)
    output: list[dict[str, Any]] = []
    grouped = rows.groupby(columns, observed=True, dropna=False)
    for key, group in grouped:
        key_tuple = key if isinstance(key, tuple) else (key,)
        item: dict[str, Any] = {column: value for column, value in zip(columns, key_tuple)}
        item.update(
            {
                "rows": int(len(group)),
                "sources": int(group["source_index"].nunique()),
                "weight_sum": float(group["weight"].sum()),
            }
        )
        for metric in DISTANCE_COLUMNS:
            item[f"{metric}_weighted_mean"] = weighted_mean(group, metric)
            item[f"{metric}_weighted_median"] = weighted_median(group, metric)
        item["actor_tanh_action_l2_min"] = float(group["actor_tanh_action_l2"].min())
        item["actor_tanh_action_l2_max"] = float(group["actor_tanh_action_l2"].max())
        item["surfaces"] = ";".join(sorted(group["surface"].astype(str).unique()))
        item["targets"] = ";".join(sorted(group["target"].astype(str).unique()))
        item["variants"] = ";".join(sorted(group["variant"].astype(str).unique()))
        item["grids"] = ";".join(sorted(group["grid_name"].astype(str).unique()))
        output.append(item)
    return output


def _subset_weighted_mean(rows: pd.DataFrame, variant: str, column: str) -> float:
    subset = rows[rows["variant"] == variant]
    if subset.empty:
        return float("nan")
    return weighted_mean(subset, column)


def classify_signal_collapse(rows: pd.DataFrame) -> dict[str, Any]:
    wrong_raw = _subset_weighted_mean(rows, "wrong_matched_history", "raw_hidden_l2")
    wrong_next_ratio = _subset_weighted_mean(rows, "wrong_matched_history", "next_hidden_retention_ratio")
    wrong_feature_ratio = _subset_weighted_mean(rows, "wrong_matched_history", "feature_retention_ratio")
    wrong_action = _subset_weighted_mean(rows, "wrong_matched_history", "actor_tanh_action_l2")
    wrong_feature = _subset_weighted_mean(rows, "wrong_matched_history", "fused_feature_l2")
    delayed_action = _subset_weighted_mean(rows, "delayed_history", "actor_tanh_action_l2")
    delayed_feature = _subset_weighted_mean(rows, "delayed_history", "fused_feature_l2")
    if np.isfinite(wrong_raw) and wrong_raw < 0.01:
        classification = "weak_stored_history_intervention"
    elif np.isfinite(wrong_next_ratio) and wrong_next_ratio < 0.20:
        classification = "gru_update_washout"
    elif np.isfinite(wrong_feature_ratio) and wrong_feature_ratio < 0.20:
        classification = "fusion_washout"
    elif np.isfinite(wrong_action) and wrong_action < 0.005:
        classification = "actor_action_insensitivity"
    else:
        classification = "signal_survives_to_actor_action"
    return {
        "classification": classification,
        "wrong_raw_hidden_l2_mean": wrong_raw,
        "wrong_next_hidden_retention_ratio_mean": wrong_next_ratio,
        "wrong_feature_retention_ratio_mean": wrong_feature_ratio,
        "wrong_fused_feature_l2_mean": wrong_feature,
        "wrong_actor_tanh_action_l2_mean": wrong_action,
        "delayed_fused_feature_l2_mean": delayed_feature,
        "delayed_actor_tanh_action_l2_mean": delayed_action,
        "wrong_to_delayed_feature_l2_ratio": wrong_feature / max(delayed_feature, EPS)
        if np.isfinite(wrong_feature) and np.isfinite(delayed_feature)
        else float("nan"),
        "wrong_to_delayed_action_l2_ratio": wrong_action / max(delayed_action, EPS)
        if np.isfinite(wrong_action) and np.isfinite(delayed_action)
        else float("nan"),
    }


def run_wrong_history_feature_separability_audit(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    device: str,
    run_dir: Path,
    batch_size: int = 1024,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(corpus_npz)
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
    rows = compute_row_feature_metrics(
        arrays,
        metadata,
        normal_outputs=normal_outputs,
        variant_outputs=variant_outputs,
    )
    after_checksum = model_parameter_checksum(model)
    write_csv_rows(run_dir / "row_feature_separability.csv", rows.to_dict("records"))
    summary_specs = {
        "variant_summary.csv": "variant",
        "split_summary.csv": "split",
        "source_summary.csv": "source_index",
        "source_split_variant_summary.csv": ("source_index", "split", "variant"),
        "target_summary.csv": "target",
        "surface_summary.csv": "surface",
    }
    written_summaries: dict[str, str] = {}
    for filename, group_columns in summary_specs.items():
        path = run_dir / filename
        write_csv_rows(path, summarize_feature_group(rows, group_columns))
        written_summaries[filename] = str(path)
    classification = classify_signal_collapse(rows)
    pt_files = sorted(str(path) for path in run_dir.rglob("*.pt"))
    summary = {
        "run_type": "wrong_history_feature_separability_audit",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "checkpoint": checkpoint_path,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "variant_counts": {str(key): int(value) for key, value in metadata["variant"].value_counts().to_dict().items()},
        "split_counts": {str(key): int(value) for key, value in metadata["split"].value_counts().to_dict().items()},
        "device": str(resolved_device),
        "batch_size": int(batch_size),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "checkpoint_written": bool(pt_files),
        "written_pt_files": pt_files,
        "row_feature_separability_csv": run_dir / "row_feature_separability.csv",
        "summary_csvs": written_summaries,
        "source_weight_balance": source_weight_balance(
            pd.DataFrame(
                {
                    "source_index": arrays["source_index"].astype(int),
                    "weight": arrays["weight"].astype(float),
                }
            )
        ),
        "collapse_classification": classification,
        "diagnostic_only": True,
        "training_started": False,
        "optimizer_started": False,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit wrong-history feature separability without training.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="wrong_history_feature_separability_audit")
    summary = run_wrong_history_feature_separability_audit(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"classification={summary['collapse_classification']['classification']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
