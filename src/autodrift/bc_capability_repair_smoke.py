"""Head-only capability repair objective smoke runner."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_capability_corpus import validate_capability_corpus_arrays
from autodrift.bc_capability_repair import (
    CapabilityHead,
    capability_rank_loss,
    capability_regression_loss,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import ActorCritic, resolve_device


def load_capability_arrays(path: Path | str) -> dict[str, np.ndarray]:
    data = np.load(path)
    arrays = {name: data[name] for name in data.files}
    validate_capability_corpus_arrays(arrays)
    return arrays


def _target_stats(targets: np.ndarray, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    values = torch.as_tensor(targets, dtype=torch.float32, device=device)
    mean = values.mean(dim=0, keepdim=True)
    std = values.std(dim=0, keepdim=True)
    std = torch.clamp(std, min=1e-6)
    return mean, std


def _pair_tensors(
    arrays: dict[str, np.ndarray],
    pairs: pd.DataFrame,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    left_indices = torch.as_tensor(pairs["left_row"].to_numpy(dtype=np.int64).copy(), dtype=torch.long, device=device)
    right_indices = torch.as_tensor(pairs["right_row"].to_numpy(dtype=np.int64).copy(), dtype=torch.long, device=device)
    hidden = torch.as_tensor(arrays["base_next_hidden_seq"], dtype=torch.float32, device=device)
    targets = torch.as_tensor(arrays["capability_target_seq"], dtype=torch.float32, device=device)
    return hidden[left_indices], hidden[right_indices], targets[left_indices], targets[right_indices]


def _regression_loss_for_arrays(
    head: CapabilityHead,
    arrays: dict[str, np.ndarray],
    *,
    target_mean: torch.Tensor,
    target_std: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    hidden = torch.as_tensor(arrays["base_next_hidden_seq"], dtype=torch.float32, device=device)
    targets = torch.as_tensor(arrays["capability_target_seq"], dtype=torch.float32, device=device)
    return capability_regression_loss(
        head(hidden),
        targets,
        target_mean=target_mean,
        target_std=target_std,
    )


def _rank_loss_for_arrays(
    head: CapabilityHead,
    arrays: dict[str, np.ndarray],
    pairs: pd.DataFrame,
    *,
    target_std: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    if pairs.empty:
        return torch.zeros((), dtype=torch.float32, device=device)
    left_hidden, right_hidden, left_target, right_target = _pair_tensors(arrays, pairs, device)
    return capability_rank_loss(
        head(left_hidden),
        head(right_hidden),
        left_target,
        right_target,
        target_std=target_std,
    )


def recompute_action_anchor_mse(
    model: ActorCritic,
    arrays: dict[str, np.ndarray],
    *,
    device: torch.device,
) -> float:
    squared_error = 0.0
    element_count = 0
    for obs, hidden, anchor in zip(
        arrays["student_obs_seq"],
        arrays["base_hidden_seq"],
        arrays["anchor_action_seq"],
        strict=True,
    ):
        hidden_t = torch.as_tensor(hidden, dtype=torch.float32, device=device).unsqueeze(0)
        action, _ = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden_t, device)
        diff = np.asarray(action, dtype=np.float64) - np.asarray(anchor, dtype=np.float64)
        squared_error += float(np.square(diff).sum())
        element_count += int(diff.size)
    if element_count == 0:
        raise ValueError("cannot compute action anchor MSE for empty arrays")
    return squared_error / float(element_count)


def _actor_parameter_snapshot(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: parameter.detach().cpu().clone() for name, parameter in model.named_parameters()}


def _actor_parameters_changed(model: ActorCritic, before: dict[str, torch.Tensor]) -> bool:
    for name, parameter in model.named_parameters():
        if name not in before:
            return True
        if not torch.equal(parameter.detach().cpu(), before[name]):
            return True
    return False


def train_head_only_smoke(
    *,
    train_arrays: dict[str, np.ndarray],
    train_pairs: pd.DataFrame,
    val_arrays: dict[str, np.ndarray],
    val_pairs: pd.DataFrame,
    hidden_size: int,
    epochs: int,
    learning_rate: float,
    rank_loss_weight: float,
    seed: int,
    device: torch.device,
) -> tuple[CapabilityHead, list[dict[str, Any]], dict[str, Any]]:
    torch.manual_seed(int(seed))
    head = CapabilityHead(hidden_size=hidden_size, output_dim=train_arrays["capability_target_seq"].shape[1]).to(device)
    target_mean, target_std = _target_stats(train_arrays["capability_target_seq"], device)
    optimizer = torch.optim.Adam(head.parameters(), lr=float(learning_rate))

    def metrics_for(split: str, arrays: dict[str, np.ndarray], pairs: pd.DataFrame) -> dict[str, float | str | int]:
        with torch.no_grad():
            regression = _regression_loss_for_arrays(
                head,
                arrays,
                target_mean=target_mean,
                target_std=target_std,
                device=device,
            )
            ranking = _rank_loss_for_arrays(head, arrays, pairs, target_std=target_std, device=device)
            total = regression + float(rank_loss_weight) * ranking
        return {
            "split": split,
            "regression_loss": float(regression.item()),
            "rank_loss": float(ranking.item()),
            "total_loss": float(total.item()),
        }

    metric_rows: list[dict[str, Any]] = []
    initial_train = metrics_for("train", train_arrays, train_pairs)
    initial_val = metrics_for("validation", val_arrays, val_pairs)
    metric_rows.append({"epoch": 0, **initial_train})
    metric_rows.append({"epoch": 0, **initial_val})

    train_hidden = torch.as_tensor(train_arrays["base_next_hidden_seq"], dtype=torch.float32, device=device)
    train_targets = torch.as_tensor(train_arrays["capability_target_seq"], dtype=torch.float32, device=device)
    train_left_hidden, train_right_hidden, train_left_target, train_right_target = _pair_tensors(
        train_arrays,
        train_pairs,
        device,
    )
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        prediction = head(train_hidden)
        regression = capability_regression_loss(
            prediction,
            train_targets,
            target_mean=target_mean,
            target_std=target_std,
        )
        ranking = capability_rank_loss(
            head(train_left_hidden),
            head(train_right_hidden),
            train_left_target,
            train_right_target,
            target_std=target_std,
        )
        loss = regression + float(rank_loss_weight) * ranking
        loss.backward()
        optimizer.step()
        if epoch == int(epochs):
            metric_rows.append({"epoch": epoch, **metrics_for("train", train_arrays, train_pairs)})
            metric_rows.append({"epoch": epoch, **metrics_for("validation", val_arrays, val_pairs)})

    final_train = metrics_for("train", train_arrays, train_pairs)
    final_val = metrics_for("validation", val_arrays, val_pairs)
    summary = {
        "train_initial_regression_loss": float(initial_train["regression_loss"]),
        "train_final_regression_loss": float(final_train["regression_loss"]),
        "validation_initial_regression_loss": float(initial_val["regression_loss"]),
        "validation_final_regression_loss": float(final_val["regression_loss"]),
        "train_initial_rank_loss": float(initial_train["rank_loss"]),
        "train_final_rank_loss": float(final_train["rank_loss"]),
        "validation_initial_rank_loss": float(initial_val["rank_loss"]),
        "validation_final_rank_loss": float(final_val["rank_loss"]),
        "target_mean": target_mean.detach().cpu().numpy().astype(float).reshape(-1).tolist(),
        "target_std": target_std.detach().cpu().numpy().astype(float).reshape(-1).tolist(),
    }
    return head, metric_rows, summary


def _relative_drop(initial: float, final: float) -> float:
    if abs(initial) <= 1e-12:
        return 0.0
    return (float(initial) - float(final)) / abs(float(initial))


def run_capability_repair_smoke(
    *,
    train_corpus: Path,
    train_pairs: Path,
    val_corpus: Path,
    val_pairs: Path,
    base_checkpoint: Path,
    epochs: int,
    learning_rate: float,
    rank_loss_weight: float,
    seed: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    train_arrays = load_capability_arrays(train_corpus)
    val_arrays = load_capability_arrays(val_corpus)
    train_pair_frame = pd.read_csv(train_pairs)
    val_pair_frame = pd.read_csv(val_pairs)
    if train_pair_frame.empty or val_pair_frame.empty:
        raise ValueError("train and validation pair CSVs must be non-empty")

    model, checkpoint = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    model.eval()
    actor_before = _actor_parameter_snapshot(model)
    train_anchor_mse = recompute_action_anchor_mse(model, train_arrays, device=resolved_device)
    val_anchor_mse = recompute_action_anchor_mse(model, val_arrays, device=resolved_device)
    head, metric_rows, loss_summary = train_head_only_smoke(
        train_arrays=train_arrays,
        train_pairs=train_pair_frame,
        val_arrays=val_arrays,
        val_pairs=val_pair_frame,
        hidden_size=int(train_arrays["base_next_hidden_seq"].shape[1]),
        epochs=epochs,
        learning_rate=learning_rate,
        rank_loss_weight=rank_loss_weight,
        seed=seed,
        device=resolved_device,
    )
    actor_changed = _actor_parameters_changed(model, actor_before)
    train_regression_drop = _relative_drop(
        loss_summary["train_initial_regression_loss"],
        loss_summary["train_final_regression_loss"],
    )
    val_regression_drop = _relative_drop(
        loss_summary["validation_initial_regression_loss"],
        loss_summary["validation_final_regression_loss"],
    )
    train_rank_drop = _relative_drop(
        loss_summary["train_initial_rank_loss"],
        loss_summary["train_final_rank_loss"],
    )
    val_rank_change = (
        loss_summary["validation_final_rank_loss"] - loss_summary["validation_initial_rank_loss"]
    ) / max(abs(loss_summary["validation_initial_rank_loss"]), 1e-12)
    passed = bool(
        train_regression_drop >= 0.30
        and val_regression_drop >= 0.10
        and train_rank_drop >= 0.10
        and val_rank_change <= 0.10
        and train_anchor_mse <= 1e-8
        and val_anchor_mse <= 1e-8
        and not actor_changed
    )

    torch.save(
        {
            "state_dict": head.state_dict(),
            "targets": checkpoint.get("metadata", {}).get("capability_repair", {}).get("training_only_targets", []),
            "run_type": "bc_capability_repair_head_only_smoke",
            "promoted": False,
            "ppo_used": False,
            "labels_enter_actor_input": False,
        },
        run_dir / "capability_head.pt",
    )
    write_csv_rows(run_dir / "train_metrics.csv", [row for row in metric_rows if row["split"] == "train"])
    write_csv_rows(run_dir / "validation_metrics.csv", [row for row in metric_rows if row["split"] == "validation"])
    summary = {
        "run_type": "bc_capability_repair_head_only_smoke",
        "train_corpus": train_corpus,
        "train_pairs": train_pairs,
        "val_corpus": val_corpus,
        "val_pairs": val_pairs,
        "base_checkpoint": base_checkpoint,
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "rank_loss_weight": float(rank_loss_weight),
        "seed": int(seed),
        "device": str(resolved_device),
        **loss_summary,
        "train_regression_drop_fraction": float(train_regression_drop),
        "validation_regression_drop_fraction": float(val_regression_drop),
        "train_rank_drop_fraction": float(train_rank_drop),
        "validation_rank_change_fraction": float(val_rank_change),
        "train_action_anchor_mse": float(train_anchor_mse),
        "validation_action_anchor_mse": float(val_anchor_mse),
        "actor_parameters_changed": bool(actor_changed),
        "labels_enter_actor_input": False,
        "promoted": False,
        "ppo_used": False,
        "passed": passed,
        "capability_head": run_dir / "capability_head.pt",
        "train_metrics_csv": run_dir / "train_metrics.csv",
        "validation_metrics_csv": run_dir / "validation_metrics.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen-actor capability-head objective smoke.")
    parser.add_argument("--train-corpus", type=Path, required=True)
    parser.add_argument("--train-pairs", type=Path, required=True)
    parser.add_argument("--val-corpus", type=Path, required=True)
    parser.add_argument("--val-pairs", type=Path, required=True)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=0.003)
    parser.add_argument("--rank-loss-weight", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=5980)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_capability_repair_head_only_smoke")
    summary = run_capability_repair_smoke(
        train_corpus=args.train_corpus,
        train_pairs=args.train_pairs,
        val_corpus=args.val_corpus,
        val_pairs=args.val_pairs,
        base_checkpoint=args.base_checkpoint,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        rank_loss_weight=args.rank_loss_weight,
        seed=args.seed,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
