"""Frozen-actor BC-v2 sequence-delta head-only smoke."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
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


class SequenceDeltaHead(nn.Module):
    """Training-only sequence-delta head attached to frozen actor features."""

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


def freeze_actor(model: ActorCritic) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()


def batched_recurrent_features(
    model: ActorCritic,
    observations: np.ndarray,
    hidden: np.ndarray,
    *,
    device: torch.device,
    batch_size: int = 1024,
) -> np.ndarray:
    features: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, observations.shape[0], int(batch_size)):
            end = min(start + int(batch_size), observations.shape[0])
            obs_t = torch.as_tensor(observations[start:end], dtype=torch.float32, device=device)
            hidden_t = torch.as_tensor(hidden[start:end], dtype=torch.float32, device=device)
            batch_features, _ = model.recurrent_features_tensor(obs_t, hidden_t)
            features.append(batch_features.detach().cpu().numpy().astype(np.float32))
    return np.concatenate(features, axis=0)


def masked_weighted_delta_mse(
    prediction: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    weight: torch.Tensor,
) -> torch.Tensor:
    if prediction.shape != target.shape:
        raise ValueError("prediction and target must have matching shape")
    if mask.shape != prediction.shape[:2]:
        raise ValueError("mask must have shape (rows, K)")
    per_row = (torch.square(prediction - target) * mask[:, :, None]).sum(dim=(1, 2))
    denom = torch.clamp(mask.sum(dim=1) * prediction.shape[2], min=1.0)
    per_row = per_row / denom
    return (per_row * weight).sum() / torch.clamp(weight.sum(), min=1e-12)


def row_delta_mse(prediction: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
    delta = (prediction.astype(np.float64) - target.astype(np.float64)) * mask[:, :, None].astype(np.float64)
    denom = np.maximum(mask.astype(np.float64).sum(axis=1) * prediction.shape[2], 1.0)
    return np.square(delta).sum(axis=(1, 2)) / denom


def _relative_drop(initial: float, final: float) -> float:
    if abs(float(initial)) <= 1e-12:
        return 0.0
    return (float(initial) - float(final)) / abs(float(initial))


def _tensor_batch(arrays: dict[str, np.ndarray], features_normal: np.ndarray, features_variant: np.ndarray, device: torch.device) -> dict[str, torch.Tensor]:
    target_delta = arrays["target_action_sequence"] - arrays["normal_base_action_sequence"]
    return {
        "features_normal": torch.as_tensor(features_normal, dtype=torch.float32, device=device),
        "features_variant": torch.as_tensor(features_variant, dtype=torch.float32, device=device),
        "target_delta": torch.as_tensor(target_delta, dtype=torch.float32, device=device),
        "mask": torch.as_tensor(arrays["sequence_mask"], dtype=torch.float32, device=device),
        "weight": torch.as_tensor(arrays["weight"], dtype=torch.float32, device=device),
    }


def _split_indices(metadata: pd.DataFrame, split: str) -> np.ndarray:
    return np.flatnonzero(metadata["split"].astype(str).to_numpy() == split).astype(np.int64)


def _loss_for_indices(head: SequenceDeltaHead, batch: dict[str, torch.Tensor], indices: np.ndarray, *, variant: bool = False) -> torch.Tensor:
    index_t = torch.as_tensor(indices, dtype=torch.long, device=batch["target_delta"].device)
    feature_key = "features_variant" if variant else "features_normal"
    prediction = head(batch[feature_key].index_select(0, index_t))
    return masked_weighted_delta_mse(
        prediction,
        batch["target_delta"].index_select(0, index_t),
        batch["mask"].index_select(0, index_t),
        batch["weight"].index_select(0, index_t),
    )


def _metric_row(epoch: int, split: str, normal_loss: torch.Tensor, variant_loss: torch.Tensor) -> dict[str, Any]:
    return {
        "epoch": int(epoch),
        "split": split,
        "normal_delta_mse": float(normal_loss.detach().cpu().item()),
        "variant_delta_mse": float(variant_loss.detach().cpu().item()),
    }


def train_sequence_delta_head(
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
    device: torch.device,
) -> tuple[SequenceDeltaHead, list[dict[str, Any]], dict[str, Any], dict[str, np.ndarray]]:
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_indices = _split_indices(metadata, "train")
    val_indices = _split_indices(metadata, "source_holdout_validation")
    if train_indices.size == 0 or val_indices.size == 0:
        raise ValueError("both train and source_holdout_validation splits are required")

    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    head = SequenceDeltaHead(
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
            metric_rows.append(
                _metric_row(
                    epoch,
                    "train",
                    _loss_for_indices(head, batch, train_indices),
                    _loss_for_indices(head, batch, train_indices, variant=True),
                )
            )
            metric_rows.append(
                _metric_row(
                    epoch,
                    "source_holdout_validation",
                    _loss_for_indices(head, batch, val_indices),
                    _loss_for_indices(head, batch, val_indices, variant=True),
                )
            )

    append_metrics(0)
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        loss = _loss_for_indices(head, batch, train_indices)
        loss.backward()
        optimizer.step()
        if epoch == int(epochs) or epoch % log_interval == 0:
            append_metrics(epoch)

    initial_train = next(row for row in metric_rows if row["epoch"] == 0 and row["split"] == "train")
    final_train = next(row for row in reversed(metric_rows) if row["split"] == "train")
    initial_val = next(row for row in metric_rows if row["epoch"] == 0 and row["split"] == "source_holdout_validation")
    final_val = next(row for row in reversed(metric_rows) if row["split"] == "source_holdout_validation")

    with torch.no_grad():
        normal_prediction = head(batch["features_normal"]).detach().cpu().numpy().astype(np.float32)
        variant_prediction = head(batch["features_variant"]).detach().cpu().numpy().astype(np.float32)
    summary = {
        "train_initial_delta_mse": float(initial_train["normal_delta_mse"]),
        "train_final_delta_mse": float(final_train["normal_delta_mse"]),
        "train_delta_mse_improvement": _relative_drop(initial_train["normal_delta_mse"], final_train["normal_delta_mse"]),
        "validation_initial_delta_mse": float(initial_val["normal_delta_mse"]),
        "validation_final_delta_mse": float(final_val["normal_delta_mse"]),
        "validation_delta_mse_improvement": _relative_drop(initial_val["normal_delta_mse"], final_val["normal_delta_mse"]),
        "final_train_variant_delta_mse": float(final_train["variant_delta_mse"]),
        "final_validation_variant_delta_mse": float(final_val["variant_delta_mse"]),
    }
    return head, metric_rows, summary, {
        "normal_prediction": normal_prediction,
        "variant_prediction": variant_prediction,
    }


def summarize_predictions(
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    predictions: dict[str, np.ndarray],
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    target_delta = arrays["target_action_sequence"] - arrays["normal_base_action_sequence"]
    normal = predictions["normal_prediction"]
    variant = predictions["variant_prediction"]
    mask = arrays["sequence_mask"]
    weights = arrays["weight"].astype(np.float64)
    normal_row_loss = row_delta_mse(normal, target_delta, mask)
    variant_row_loss = row_delta_mse(variant, target_delta, mask)
    gap = np.linalg.norm((normal - variant) * mask[:, :, None], axis=2)
    valid_steps = np.maximum(mask.sum(axis=1), 1.0)
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
            "normal_delta_mse": normal_row_loss,
            "variant_delta_mse": variant_row_loss,
            "normal_variant_prediction_gap_l2": gap.sum(axis=1) / valid_steps,
            "weighted_normal_delta_mse": weights * normal_row_loss,
        }
    )

    def group_summary(group_column: str) -> list[dict[str, Any]]:
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
                    "normal_variant_prediction_gap_l2": float(
                        (group["weight"] * group["normal_variant_prediction_gap_l2"]).sum() / max(weight_sum, 1e-12)
                    ),
                    "surfaces": ";".join(sorted(group["surface"].astype(str).unique())),
                    "targets": ";".join(sorted(group["target"].astype(str).unique())),
                    "variants": ";".join(sorted(group["variant"].astype(str).unique())),
                    "grids": ";".join(sorted(group["grid_name"].astype(str).unique())),
                }
            )
        return output

    return rows, group_summary("source_index"), group_summary("split"), group_summary("target")


def run_bc_v2_head_only_smoke(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    seed: int,
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
    head, metric_rows, train_summary, predictions = train_sequence_delta_head(
        arrays=arrays,
        metadata=metadata,
        features_normal=features_normal,
        features_variant=features_variant,
        hidden_dim=hidden_dim,
        epochs=epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        seed=seed,
        device=resolved_device,
    )
    after_checksum = model_parameter_checksum(model)

    row_predictions, source_summary, split_summary, target_summary = summarize_predictions(arrays, metadata, predictions)
    write_csv_rows(run_dir / "train_metrics.csv", [row for row in metric_rows if row["split"] == "train"])
    write_csv_rows(run_dir / "validation_metrics.csv", [row for row in metric_rows if row["split"] == "source_holdout_validation"])
    write_csv_rows(run_dir / "row_predictions.csv", row_predictions.to_dict(orient="records"))
    write_csv_rows(run_dir / "source_head_summary.csv", source_summary)
    write_csv_rows(run_dir / "split_head_summary.csv", split_summary)
    write_csv_rows(run_dir / "target_head_summary.csv", target_summary)
    head_path = run_dir / "sequence_delta_head.pt"
    torch.save(
        {
            "head_state": head.state_dict(),
            "feature_dim": int(features_normal.shape[1]),
            "hidden_dim": int(hidden_dim),
            "max_sequence_length": int(contract.max_sequence_length),
            "action_dim": int(contract.action_dim),
            "seed": int(seed),
        },
        head_path,
    )
    balance = source_weight_balance(
        row_predictions.rename(
            columns={
                "normal_delta_mse": "sequence_mse",
                "normal_variant_prediction_gap_l2": "sequence_mean_step_l2",
            }
        )
    )
    split_frame = pd.DataFrame(split_summary).set_index("split")
    normal_head_loss = float(row_predictions["weighted_normal_delta_mse"].sum() / max(float(row_predictions["weight"].sum()), 1e-12))
    variant_head_loss = float((row_predictions["weight"] * row_predictions["variant_delta_mse"]).sum() / max(float(row_predictions["weight"].sum()), 1e-12))
    normal_variant_gap = float(
        (row_predictions["weight"] * row_predictions["normal_variant_prediction_gap_l2"]).sum()
        / max(float(row_predictions["weight"].sum()), 1e-12)
    )
    summary = {
        "run_type": "bc_v2_head_only_smoke",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "checkpoint": checkpoint_path,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "seed": int(seed),
        **train_summary,
        "normal_head_loss": normal_head_loss,
        "variant_head_loss": variant_head_loss,
        "normal_variant_prediction_gap_l2": normal_variant_gap,
        "train_split_final_delta_mse": float(split_frame.loc["train", "normal_delta_mse"]),
        "source_holdout_validation_split_final_delta_mse": float(
            split_frame.loc["source_holdout_validation", "normal_delta_mse"]
        ),
        "source_weight_balance": balance,
        "finite_metrics": bool(np.isfinite(row_predictions.select_dtypes(include=[np.number]).to_numpy()).all()),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "head_checkpoint_written": head_path.exists(),
        "checkpoint_written": False,
        "actor_checkpoint_written": False,
        "sequence_delta_head": head_path,
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "validation_metrics_csv": run_dir / "validation_metrics.csv",
        "row_predictions_csv": run_dir / "row_predictions.csv",
        "source_head_summary_csv": run_dir / "source_head_summary.csv",
        "split_head_summary_csv": run_dir / "split_head_summary.csv",
        "target_head_summary_csv": run_dir / "target_head_summary.csv",
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    summary["passed_head_only_smoke"] = bool(
        summary["actor_parameters_changed"] is False
        and summary["head_checkpoint_written"] is True
        and summary["checkpoint_written"] is False
        and summary["train_delta_mse_improvement"] >= 0.30
        and summary["validation_final_delta_mse"] <= summary["validation_initial_delta_mse"] + 1e-12
        and summary["finite_metrics"] is True
        and summary["source_weight_balance"]["source_weight_balanced"] is True
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a frozen-actor BC-v2 sequence-delta head-only smoke.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--seed", type=int, default=6460)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_v2_head_only_smoke")
    summary = run_bc_v2_head_only_smoke(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        seed=args.seed,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"train_delta_mse_improvement={summary['train_delta_mse_improvement']:.6f}")
    print(f"validation_delta_mse_improvement={summary['validation_delta_mse_improvement']:.6f}")
    print(f"actor_parameters_changed={summary['actor_parameters_changed']}")
    print(f"passed_head_only_smoke={summary['passed_head_only_smoke']}")


if __name__ == "__main__":
    main()
