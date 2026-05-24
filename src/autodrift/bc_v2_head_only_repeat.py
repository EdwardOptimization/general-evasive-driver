"""Multi-seed best-validation repeat for frozen BC-v2 sequence heads."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_smoke import (
    SequenceDeltaHead,
    batched_recurrent_features,
    freeze_actor,
    row_delta_mse,
    summarize_predictions,
)
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


def parse_seed_list(value: str) -> tuple[int, ...]:
    seeds = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not seeds:
        raise argparse.ArgumentTypeError("seed list cannot be empty")
    return seeds


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
        "target_delta": torch.as_tensor(
            arrays["target_action_sequence"] - arrays["normal_base_action_sequence"],
            dtype=torch.float32,
            device=device,
        ),
        "mask": torch.as_tensor(arrays["sequence_mask"], dtype=torch.float32, device=device),
        "weight": torch.as_tensor(arrays["weight"], dtype=torch.float32, device=device),
    }


def _masked_loss(prediction: torch.Tensor, target: torch.Tensor, mask: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    row = (torch.square(prediction - target) * mask[:, :, None]).sum(dim=(1, 2))
    denom = torch.clamp(mask.sum(dim=1) * prediction.shape[2], min=1.0)
    row = row / denom
    return (row * weight).sum() / torch.clamp(weight.sum(), min=1e-12)


def _loss_for_indices(
    head: SequenceDeltaHead,
    batch: dict[str, torch.Tensor],
    indices: np.ndarray,
    *,
    variant: bool = False,
) -> torch.Tensor:
    index_t = torch.as_tensor(indices, dtype=torch.long, device=batch["target_delta"].device)
    feature_key = "features_variant" if variant else "features_normal"
    return _masked_loss(
        head(batch[feature_key].index_select(0, index_t)),
        batch["target_delta"].index_select(0, index_t),
        batch["mask"].index_select(0, index_t),
        batch["weight"].index_select(0, index_t),
    )


def _relative_drop(initial: float, final: float) -> float:
    if abs(float(initial)) <= 1e-12:
        return 0.0
    return (float(initial) - float(final)) / abs(float(initial))


def _predict(head: SequenceDeltaHead, features: np.ndarray, device: torch.device) -> np.ndarray:
    with torch.no_grad():
        tensor = torch.as_tensor(features, dtype=torch.float32, device=device)
        return head(tensor).detach().cpu().numpy().astype(np.float32)


def train_one_repeat_seed(
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
    device: torch.device,
    seed_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    seed_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_indices = _split_indices(metadata, "train")
    val_indices = _split_indices(metadata, "source_holdout_validation")
    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    head = SequenceDeltaHead(
        feature_dim=int(features_normal.shape[1]),
        hidden_dim=int(hidden_dim),
        max_sequence_length=contract.max_sequence_length,
        action_dim=contract.action_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))

    metric_rows: list[dict[str, Any]] = []
    best_validation = float("inf")
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    best_train_loss = float("inf")
    best_variant_validation = float("inf")

    def metrics(epoch: int) -> dict[str, float]:
        with torch.no_grad():
            train_loss = float(_loss_for_indices(head, batch, train_indices).detach().cpu().item())
            val_loss = float(_loss_for_indices(head, batch, val_indices).detach().cpu().item())
            train_variant = float(_loss_for_indices(head, batch, train_indices, variant=True).detach().cpu().item())
            val_variant = float(_loss_for_indices(head, batch, val_indices, variant=True).detach().cpu().item())
        return {
            "epoch": int(epoch),
            "train_delta_mse": train_loss,
            "validation_delta_mse": val_loss,
            "train_variant_delta_mse": train_variant,
            "validation_variant_delta_mse": val_variant,
        }

    def maybe_record_best(row: dict[str, float]) -> None:
        nonlocal best_validation, best_epoch, best_state, best_train_loss, best_variant_validation
        validation = float(row["validation_delta_mse"])
        if validation < best_validation:
            best_validation = validation
            best_epoch = int(row["epoch"])
            best_train_loss = float(row["train_delta_mse"])
            best_variant_validation = float(row["validation_variant_delta_mse"])
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in head.state_dict().items()}

    row0 = metrics(0)
    metric_rows.append({"seed": int(seed), **row0})
    maybe_record_best(row0)
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        loss = _loss_for_indices(head, batch, train_indices)
        loss.backward()
        optimizer.step()
        row = metrics(epoch)
        metric_rows.append({"seed": int(seed), **row})
        maybe_record_best(row)

    final_row = metric_rows[-1]
    initial_row = metric_rows[0]
    final_path = seed_dir / "sequence_delta_head_final.pt"
    best_path = seed_dir / "sequence_delta_head_best_validation.pt"
    torch.save({"head_state": head.state_dict(), "seed": int(seed), "epoch": int(epochs)}, final_path)
    if best_state is None:
        raise RuntimeError("best validation state was not recorded")
    torch.save({"head_state": best_state, "seed": int(seed), "epoch": int(best_epoch)}, best_path)
    head.load_state_dict(best_state)
    predictions = {
        "normal_prediction": _predict(head, features_normal, device),
        "variant_prediction": _predict(head, features_variant, device),
    }
    row_predictions, source_summary, _, target_summary = summarize_predictions(arrays, metadata, predictions)
    final_vs_best = float(final_row["validation_delta_mse"]) / max(float(best_validation), 1e-12)
    train_improvement = _relative_drop(initial_row["train_delta_mse"], best_train_loss)
    validation_improvement = _relative_drop(initial_row["validation_delta_mse"], best_validation)
    seed_passed = bool(
        train_improvement >= 0.30
        and validation_improvement >= 0.50
        and best_validation <= 0.00075
        and final_vs_best <= 3.0
    )
    summary = {
        "seed": int(seed),
        "initial_train_delta_mse": float(initial_row["train_delta_mse"]),
        "initial_validation_delta_mse": float(initial_row["validation_delta_mse"]),
        "best_epoch": int(best_epoch),
        "best_train_delta_mse": float(best_train_loss),
        "best_validation_delta_mse": float(best_validation),
        "best_validation_variant_delta_mse": float(best_variant_validation),
        "final_train_delta_mse": float(final_row["train_delta_mse"]),
        "final_validation_delta_mse": float(final_row["validation_delta_mse"]),
        "train_delta_mse_improvement_at_best": float(train_improvement),
        "validation_delta_mse_improvement_at_best": float(validation_improvement),
        "final_vs_best_validation_ratio": float(final_vs_best),
        "best_head_checkpoint_written": best_path.exists(),
        "final_head_checkpoint_written": final_path.exists(),
        "actor_checkpoint_written": False,
        "seed_passed": seed_passed,
        "best_head_checkpoint": best_path,
        "final_head_checkpoint": final_path,
    }
    return summary, metric_rows, row_predictions, source_summary, target_summary


def run_bc_v2_head_only_repeat(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    seeds: tuple[int, ...],
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
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
    wrong_history_rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_dir = run_dir / f"seed_{int(seed)}"
        seed_summary, seed_metrics, _, seed_source, seed_target = train_one_repeat_seed(
            seed=int(seed),
            arrays=arrays,
            metadata=metadata,
            features_normal=features_normal,
            features_variant=features_variant,
            epochs=epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            hidden_dim=hidden_dim,
            device=resolved_device,
            seed_dir=seed_dir,
        )
        seed_summaries.append(seed_summary)
        metric_rows.extend(seed_metrics)
        for row in seed_source:
            enriched = {"seed": int(seed), **row}
            source_rows.append(enriched)
            if "wrong_matched_history" in str(row.get("variants", "")):
                wrong_history_rows.append(enriched)
        target_rows.extend({"seed": int(seed), **row} for row in seed_target)

    after_checksum = model_parameter_checksum(model)
    write_csv_rows(run_dir / "seed_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "seed_metrics.csv", metric_rows)
    write_csv_rows(run_dir / "source_repeat_summary.csv", source_rows)
    write_csv_rows(run_dir / "target_repeat_summary.csv", target_rows)
    write_csv_rows(run_dir / "wrong_history_source_summary.csv", wrong_history_rows)
    pass_count = int(sum(1 for row in seed_summaries if row["seed_passed"]))
    balance = source_weight_balance(
        pd.DataFrame(
            {
                "source_index": arrays["source_index"].astype(int),
                "weight": arrays["weight"].astype(float),
            }
        )
    )
    summary = {
        "run_type": "bc_v2_head_only_repeat",
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
        "passed_seed_count": pass_count,
        "total_seed_count": int(len(seeds)),
        "repeat_passed": bool(pass_count >= 2),
        "all_actor_checksums_unchanged": bool(before_checksum == after_checksum),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "source_weight_balance": balance,
        "all_best_heads_written": bool(all(row["best_head_checkpoint_written"] for row in seed_summaries)),
        "all_final_heads_written": bool(all(row["final_head_checkpoint_written"] for row in seed_summaries)),
        "actor_checkpoint_written": False,
        "seed_summary_csv": run_dir / "seed_summary.csv",
        "seed_metrics_csv": run_dir / "seed_metrics.csv",
        "source_repeat_summary_csv": run_dir / "source_repeat_summary.csv",
        "target_repeat_summary_csv": run_dir / "target_repeat_summary.csv",
        "wrong_history_source_summary_csv": run_dir / "wrong_history_source_summary.csv",
        "wrong_history_rows": int(len(wrong_history_rows)),
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-seed frozen BC-v2 head-only repeat.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seeds", type=parse_seed_list, required=True)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_v2_head_only_repeat")
    summary = run_bc_v2_head_only_repeat(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        seeds=args.seeds,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"passed_seed_count={summary['passed_seed_count']}/{summary['total_seed_count']}")
    print(f"repeat_passed={summary['repeat_passed']}")
    print(f"actor_parameters_changed={summary['actor_parameters_changed']}")


if __name__ == "__main__":
    main()
