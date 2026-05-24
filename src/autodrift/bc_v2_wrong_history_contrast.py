"""Frozen-head BC-v2 wrong-history contrast smoke."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_repeat import parse_seed_list
from autodrift.bc_v2_head_only_smoke import SequenceDeltaHead, batched_recurrent_features, freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device


def split_indices(metadata: pd.DataFrame, split: str) -> np.ndarray:
    return np.flatnonzero(metadata["split"].astype(str).to_numpy() == split).astype(np.int64)


def wrong_history_indices(metadata: pd.DataFrame, split: str | None = None) -> np.ndarray:
    mask = metadata["variant"].astype(str).to_numpy() == "wrong_matched_history"
    if split is not None:
        mask &= metadata["split"].astype(str).to_numpy() == split
    return np.flatnonzero(mask).astype(np.int64)


def delayed_history_indices(metadata: pd.DataFrame, split: str | None = None) -> np.ndarray:
    mask = metadata["variant"].astype(str).to_numpy() == "delayed_history"
    if split is not None:
        mask &= metadata["split"].astype(str).to_numpy() == split
    return np.flatnonzero(mask).astype(np.int64)


def per_row_masked_mse(prediction: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    if prediction.shape != target.shape:
        raise ValueError("prediction and target must have the same shape")
    if mask.shape != prediction.shape[:2]:
        raise ValueError("mask must have shape (rows, K)")
    row = (torch.square(prediction - target) * mask[:, :, None]).sum(dim=(1, 2))
    denom = torch.clamp(mask.sum(dim=1) * prediction.shape[2], min=1.0)
    return row / denom


def weighted_row_mean(values: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    return (values * weight).sum() / torch.clamp(weight.sum(), min=1e-12)


def _index_tensor(indices: np.ndarray, device: torch.device) -> torch.Tensor:
    return torch.as_tensor(indices, dtype=torch.long, device=device)


def normal_target_loss(head: SequenceDeltaHead, batch: dict[str, torch.Tensor], indices: np.ndarray) -> torch.Tensor:
    idx = _index_tensor(indices, batch["target_delta"].device)
    pred = head(batch["features_normal"].index_select(0, idx))
    row = per_row_masked_mse(
        pred,
        batch["target_delta"].index_select(0, idx),
        batch["mask"].index_select(0, idx),
    )
    return weighted_row_mean(row, batch["weight"].index_select(0, idx))


def wrong_history_margin_loss(
    head: SequenceDeltaHead,
    batch: dict[str, torch.Tensor],
    indices: np.ndarray,
    *,
    margin_mse: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    idx = _index_tensor(indices, batch["target_delta"].device)
    target = batch["target_delta"].index_select(0, idx)
    mask = batch["mask"].index_select(0, idx)
    weight = batch["weight"].index_select(0, idx)
    normal_pred = head(batch["features_normal"].index_select(0, idx))
    wrong_pred = head(batch["features_variant"].index_select(0, idx))
    d_normal = per_row_masked_mse(normal_pred, target, mask)
    d_wrong = per_row_masked_mse(wrong_pred, target, mask)
    contrast = F.softplus(float(margin_mse) + d_normal - d_wrong)
    return weighted_row_mean(contrast, weight), d_normal, d_wrong


def wrong_zero_loss(head: SequenceDeltaHead, batch: dict[str, torch.Tensor], indices: np.ndarray) -> torch.Tensor:
    idx = _index_tensor(indices, batch["target_delta"].device)
    pred = head(batch["features_variant"].index_select(0, idx))
    mask = batch["mask"].index_select(0, idx)
    zero = torch.zeros_like(pred)
    row = per_row_masked_mse(pred, zero, mask)
    return weighted_row_mean(row, batch["weight"].index_select(0, idx))


def _tensor_batch(
    arrays: dict[str, np.ndarray],
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    return {
        "features_normal": torch.as_tensor(features_normal, dtype=torch.float32, device=device),
        "features_variant": torch.as_tensor(features_variant, dtype=torch.float32, device=device),
        "target_delta": torch.as_tensor(
            arrays["target_action_sequence"] - arrays["normal_base_action_sequence"],
            dtype=torch.float32,
            device=device,
        ),
        "mask": torch.as_tensor(arrays["sequence_mask"], dtype=torch.float32, device=device),
        "weight": torch.as_tensor(arrays["weight"], dtype=torch.float32, device=device),
    }


def _row_mse_np(prediction: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
    row = np.square((prediction - target) * mask[:, :, None]).sum(axis=(1, 2))
    denom = np.maximum(mask.sum(axis=1) * prediction.shape[2], 1.0)
    return row / denom


def _gap_l2_np(normal: np.ndarray, variant: np.ndarray, mask: np.ndarray) -> np.ndarray:
    step = np.linalg.norm((normal - variant) * mask[:, :, None], axis=2)
    return step.sum(axis=1) / np.maximum(mask.sum(axis=1), 1.0)


def _predict(head: SequenceDeltaHead, features: np.ndarray, device: torch.device) -> np.ndarray:
    with torch.no_grad():
        tensor = torch.as_tensor(features, dtype=torch.float32, device=device)
        return head(tensor).detach().cpu().numpy().astype(np.float32)


def row_contrast_metrics(
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    *,
    normal_prediction: np.ndarray,
    variant_prediction: np.ndarray,
) -> pd.DataFrame:
    target = arrays["target_action_sequence"] - arrays["normal_base_action_sequence"]
    mask = arrays["sequence_mask"]
    weights = arrays["weight"].astype(np.float64)
    normal_mse = _row_mse_np(normal_prediction, target, mask)
    variant_mse = _row_mse_np(variant_prediction, target, mask)
    gap_l2 = _gap_l2_np(normal_prediction, variant_prediction, mask)
    rows = pd.DataFrame(
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
            "normal_delta_mse": normal_mse,
            "variant_delta_mse": variant_mse,
            "gap_mse": variant_mse - normal_mse,
            "prediction_gap_l2": gap_l2,
        }
    )
    rows["weighted_normal_delta_mse"] = rows["weight"] * rows["normal_delta_mse"]
    rows["weighted_gap_mse"] = rows["weight"] * rows["gap_mse"]
    rows["weighted_prediction_gap_l2"] = rows["weight"] * rows["prediction_gap_l2"]
    return rows


def summarize_contrast_group(rows: pd.DataFrame, group_column: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for value, group in rows.groupby(group_column, observed=True):
        weight_sum = float(group["weight"].sum())
        output.append(
            {
                group_column: value,
                "rows": int(len(group)),
                "sources": int(group["source_index"].nunique()),
                "weight_sum": weight_sum,
                "normal_delta_mse": float(group["weighted_normal_delta_mse"].sum() / max(weight_sum, 1e-12)),
                "variant_delta_mse": float((group["weight"] * group["variant_delta_mse"]).sum() / max(weight_sum, 1e-12)),
                "gap_mse": float(group["weighted_gap_mse"].sum() / max(weight_sum, 1e-12)),
                "prediction_gap_l2": float(group["weighted_prediction_gap_l2"].sum() / max(weight_sum, 1e-12)),
                "surfaces": ";".join(sorted(group["surface"].astype(str).unique())),
                "targets": ";".join(sorted(group["target"].astype(str).unique())),
                "variants": ";".join(sorted(group["variant"].astype(str).unique())),
                "grids": ";".join(sorted(group["grid_name"].astype(str).unique())),
            }
        )
    return output


def _weighted_metric(rows: pd.DataFrame, column: str) -> float:
    return float((rows["weight"] * rows[column]).sum() / max(float(rows["weight"].sum()), 1e-12))


def _relative_drop(initial: float, final: float) -> float:
    if abs(float(initial)) <= 1e-12:
        return 0.0
    return (float(initial) - float(final)) / abs(float(initial))


def seed_passes(summary: dict[str, Any]) -> bool:
    return bool(
        summary["actor_parameters_changed"] is False
        and summary["best_head_checkpoint_written"] is True
        and summary["actor_checkpoint_written"] is False
        and summary["normal_validation_delta_mse"] <= 0.0010
        and summary["wrong_train_gap_mse"] >= 0.00025
        and summary["wrong_validation_gap_mse"] >= 0.00010
        and summary["wrong_train_prediction_gap_l2"] >= 0.01
        and summary["wrong_validation_prediction_gap_l2"] >= 0.005
    )


def train_one_contrast_seed(
    *,
    seed: int,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    contrast_coef: float,
    wrong_zero_coef: float,
    margin_mse: float,
    device: torch.device,
    seed_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    seed_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_idx = split_indices(metadata, "train")
    val_idx = split_indices(metadata, "source_holdout_validation")
    wrong_train_idx = wrong_history_indices(metadata, "train")
    wrong_val_idx = wrong_history_indices(metadata, "source_holdout_validation")
    delayed_idx = delayed_history_indices(metadata)
    if wrong_train_idx.size == 0 or wrong_val_idx.size == 0:
        raise ValueError("wrong-history train and validation rows are required")
    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    head = SequenceDeltaHead(
        feature_dim=int(features_normal.shape[1]),
        hidden_dim=int(hidden_dim),
        max_sequence_length=contract.max_sequence_length,
        action_dim=contract.action_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    metric_rows: list[dict[str, Any]] = []
    best_score = float("inf")
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None

    def eval_metrics(epoch: int) -> dict[str, Any]:
        with torch.no_grad():
            train_loss = float(normal_target_loss(head, batch, train_idx).detach().cpu().item())
            val_loss = float(normal_target_loss(head, batch, val_idx).detach().cpu().item())
            _, train_dn, train_dw = wrong_history_margin_loss(
                head,
                batch,
                wrong_train_idx,
                margin_mse=margin_mse,
            )
            _, val_dn, val_dw = wrong_history_margin_loss(
                head,
                batch,
                wrong_val_idx,
                margin_mse=margin_mse,
            )
        return {
            "seed": int(seed),
            "epoch": int(epoch),
            "normal_train_delta_mse": train_loss,
            "normal_validation_delta_mse": val_loss,
            "wrong_train_normal_mse": float(train_dn.mean().detach().cpu().item()),
            "wrong_train_variant_mse": float(train_dw.mean().detach().cpu().item()),
            "wrong_train_gap_mse": float((train_dw - train_dn).mean().detach().cpu().item()),
            "wrong_validation_normal_mse": float(val_dn.mean().detach().cpu().item()),
            "wrong_validation_variant_mse": float(val_dw.mean().detach().cpu().item()),
            "wrong_validation_gap_mse": float((val_dw - val_dn).mean().detach().cpu().item()),
        }

    def record_best(row: dict[str, Any]) -> None:
        nonlocal best_score, best_epoch, best_state
        # Lower validation loss is primary. A larger heldout wrong-history gap
        # is the tiebreaker with a small scale so it cannot hide retention loss.
        score = float(row["normal_validation_delta_mse"]) - 0.01 * float(row["wrong_validation_gap_mse"])
        if score < best_score:
            best_score = score
            best_epoch = int(row["epoch"])
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in head.state_dict().items()}

    row0 = eval_metrics(0)
    metric_rows.append(row0)
    record_best(row0)
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        normal_loss = normal_target_loss(head, batch, train_idx)
        margin_loss, _, _ = wrong_history_margin_loss(head, batch, wrong_train_idx, margin_mse=margin_mse)
        zero_loss = wrong_zero_loss(head, batch, wrong_train_idx)
        loss = normal_loss + float(contrast_coef) * margin_loss + float(wrong_zero_coef) * zero_loss
        loss.backward()
        optimizer.step()
        row = eval_metrics(epoch)
        metric_rows.append(row)
        record_best(row)
    if best_state is None:
        raise RuntimeError("best state was not recorded")

    final_path = seed_dir / "sequence_delta_head_final.pt"
    best_path = seed_dir / "sequence_delta_head_best_validation.pt"
    torch.save({"head_state": head.state_dict(), "seed": int(seed), "epoch": int(epochs)}, final_path)
    torch.save({"head_state": best_state, "seed": int(seed), "epoch": int(best_epoch)}, best_path)
    head.load_state_dict(best_state)
    normal_prediction = _predict(head, features_normal, device)
    variant_prediction = _predict(head, features_variant, device)
    row_metrics = row_contrast_metrics(
        arrays,
        metadata,
        normal_prediction=normal_prediction,
        variant_prediction=variant_prediction,
    )
    source_summary = summarize_contrast_group(row_metrics, "source_index")
    target_summary = summarize_contrast_group(row_metrics, "target")
    wrong_rows = row_metrics[row_metrics["variant"] == "wrong_matched_history"].copy()
    wrong_source_summary = summarize_contrast_group(wrong_rows, "source_index")
    delayed_summary = summarize_contrast_group(row_metrics.iloc[delayed_idx], "source_index") if delayed_idx.size else []
    train_rows = row_metrics[row_metrics["split"] == "train"]
    val_rows = row_metrics[row_metrics["split"] == "source_holdout_validation"]
    wrong_train = wrong_rows[wrong_rows["split"] == "train"]
    wrong_val = wrong_rows[wrong_rows["split"] == "source_holdout_validation"]
    initial = metric_rows[0]
    best_metric = metric_rows[best_epoch]
    summary = {
        "seed": int(seed),
        "best_epoch": int(best_epoch),
        "initial_normal_train_delta_mse": float(initial["normal_train_delta_mse"]),
        "initial_normal_validation_delta_mse": float(initial["normal_validation_delta_mse"]),
        "normal_train_delta_mse": _weighted_metric(train_rows, "normal_delta_mse"),
        "normal_validation_delta_mse": _weighted_metric(val_rows, "normal_delta_mse"),
        "normal_train_improvement": _relative_drop(initial["normal_train_delta_mse"], _weighted_metric(train_rows, "normal_delta_mse")),
        "normal_validation_improvement": _relative_drop(initial["normal_validation_delta_mse"], _weighted_metric(val_rows, "normal_delta_mse")),
        "wrong_train_gap_mse": _weighted_metric(wrong_train, "gap_mse"),
        "wrong_validation_gap_mse": _weighted_metric(wrong_val, "gap_mse"),
        "wrong_train_prediction_gap_l2": _weighted_metric(wrong_train, "prediction_gap_l2"),
        "wrong_validation_prediction_gap_l2": _weighted_metric(wrong_val, "prediction_gap_l2"),
        "best_metric_normal_validation_delta_mse": float(best_metric["normal_validation_delta_mse"]),
        "best_metric_wrong_validation_gap_mse": float(best_metric["wrong_validation_gap_mse"]),
        "best_head_checkpoint_written": best_path.exists(),
        "final_head_checkpoint_written": final_path.exists(),
        "actor_checkpoint_written": False,
        "best_head_checkpoint": best_path,
        "final_head_checkpoint": final_path,
    }
    summary["actor_parameters_changed"] = False
    summary["seed_passed"] = seed_passes(summary)
    return summary, metric_rows, row_metrics, source_summary, target_summary, wrong_source_summary + delayed_summary


def run_bc_v2_wrong_history_contrast(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    seeds: tuple[int, ...],
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    contrast_coef: float,
    wrong_zero_coef: float,
    margin_mse: float,
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
    features_normal = batched_recurrent_features(
        model,
        arrays["observation"],
        arrays["normal_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    features_variant = batched_recurrent_features(
        model,
        arrays["observation"],
        arrays["variant_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    seed_summaries: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    for seed in seeds:
        summary, metrics, _, source_summary, target_summary, history_summary = train_one_contrast_seed(
            seed=int(seed),
            arrays=arrays,
            metadata=metadata,
            features_normal=features_normal,
            features_variant=features_variant,
            epochs=epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            hidden_dim=hidden_dim,
            contrast_coef=contrast_coef,
            wrong_zero_coef=wrong_zero_coef,
            margin_mse=margin_mse,
            device=resolved_device,
            seed_dir=run_dir / f"seed_{int(seed)}",
        )
        seed_summaries.append(summary)
        metric_rows.extend(metrics)
        source_rows.extend({"seed": int(seed), **row} for row in source_summary)
        target_rows.extend({"seed": int(seed), **row} for row in target_summary)
        history_rows.extend({"seed": int(seed), **row} for row in history_summary)
    after_checksum = model_parameter_checksum(model)
    for summary in seed_summaries:
        summary["actor_parameters_changed"] = bool(before_checksum != after_checksum)
        summary["seed_passed"] = seed_passes(summary)
    pass_count = int(sum(1 for row in seed_summaries if row["seed_passed"]))
    write_csv_rows(run_dir / "seed_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "seed_metrics.csv", metric_rows)
    write_csv_rows(run_dir / "source_contrast_summary.csv", source_rows)
    write_csv_rows(run_dir / "target_contrast_summary.csv", target_rows)
    write_csv_rows(run_dir / "history_variant_summary.csv", history_rows)
    balance = source_weight_balance(
        pd.DataFrame(
            {
                "source_index": arrays["source_index"].astype(int),
                "weight": arrays["weight"].astype(float),
            }
        )
    )
    summary = {
        "run_type": "bc_v2_wrong_history_contrast",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "checkpoint": checkpoint_path,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "seeds": [int(seed) for seed in seeds],
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "contrast_coef": float(contrast_coef),
        "wrong_zero_coef": float(wrong_zero_coef),
        "margin_mse": float(margin_mse),
        "passed_seed_count": pass_count,
        "total_seed_count": int(len(seeds)),
        "contrast_passed": bool(pass_count >= 2),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "all_best_heads_written": bool(all(row["best_head_checkpoint_written"] for row in seed_summaries)),
        "all_final_heads_written": bool(all(row["final_head_checkpoint_written"] for row in seed_summaries)),
        "actor_checkpoint_written": False,
        "source_weight_balance": balance,
        "seed_summary_csv": run_dir / "seed_summary.csv",
        "seed_metrics_csv": run_dir / "seed_metrics.csv",
        "source_contrast_summary_csv": run_dir / "source_contrast_summary.csv",
        "target_contrast_summary_csv": run_dir / "target_contrast_summary.csv",
        "history_variant_summary_csv": run_dir / "history_variant_summary.csv",
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen-head BC-v2 wrong-history contrast smoke.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seeds", type=parse_seed_list, required=True)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--contrast-coef", type=float, default=1.0)
    parser.add_argument("--wrong-zero-coef", type=float, default=0.05)
    parser.add_argument("--margin-mse", type=float, default=0.00025)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_v2_wrong_history_contrast")
    summary = run_bc_v2_wrong_history_contrast(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        seeds=args.seeds,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        contrast_coef=args.contrast_coef,
        wrong_zero_coef=args.wrong_zero_coef,
        margin_mse=args.margin_mse,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"passed_seed_count={summary['passed_seed_count']}/{summary['total_seed_count']}")
    print(f"contrast_passed={summary['contrast_passed']}")
    print(f"actor_parameters_changed={summary['actor_parameters_changed']}")


if __name__ == "__main__":
    main()
