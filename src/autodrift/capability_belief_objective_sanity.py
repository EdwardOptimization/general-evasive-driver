"""M152 objective-only sanity check for capability-belief targets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS


REQUIRED_ARRAYS = (
    "student_p0_i",
    "student_p0_j",
    "teacher_capability_i",
    "teacher_capability_j",
    "teacher_capability_delta",
    "teacher_capability_abs_delta_z",
    "pair_weight",
    "dominant_target_index",
    "dominant_hidden_group_index",
    "hidden_group_distances",
    "sample_i",
    "sample_j",
)
STUDENT_INPUT_KEYS = ("student_p0_i", "student_p0_j")
TEACHER_TARGET_KEYS = ("teacher_capability_i", "teacher_capability_j")
TRAINING_METADATA_KEYS = (
    "teacher_capability_delta",
    "teacher_capability_abs_delta_z",
    "pair_weight",
    "dominant_target_index",
    "dominant_hidden_group_index",
    "hidden_group_distances",
    "sample_i",
    "sample_j",
)


@dataclass(frozen=True)
class DatasetContract:
    pairs: int
    student_feature_dim: int
    target_dim: int
    student_input_keys: tuple[str, ...]
    teacher_target_keys: tuple[str, ...]
    training_metadata_keys: tuple[str, ...]


@dataclass(frozen=True)
class PairSplit:
    train_indices: np.ndarray
    val_indices: np.ndarray


class CapabilityBeliefRegressor(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, target_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, target_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


def parse_seed_list(value: str) -> tuple[int, ...]:
    seeds = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not seeds:
        raise argparse.ArgumentTypeError("seed list cannot be empty")
    return seeds


def load_dataset_npz(path: Path) -> dict[str, np.ndarray]:
    loaded = np.load(path)
    arrays = {key: loaded[key] for key in loaded.files}
    validate_dataset_contract(arrays)
    return arrays


def validate_dataset_contract(arrays: dict[str, np.ndarray]) -> DatasetContract:
    missing = [key for key in REQUIRED_ARRAYS if key not in arrays]
    if missing:
        raise ValueError("capability-belief dataset is missing arrays: " + ", ".join(missing))
    left_features = arrays["student_p0_i"]
    right_features = arrays["student_p0_j"]
    left_targets = arrays["teacher_capability_i"]
    right_targets = arrays["teacher_capability_j"]
    if left_features.ndim != 2 or right_features.ndim != 2:
        raise ValueError("student_p0_i and student_p0_j must be 2D arrays")
    if left_features.shape != right_features.shape:
        raise ValueError("student_p0_i and student_p0_j must have the same shape")
    if left_targets.ndim != 2 or right_targets.ndim != 2:
        raise ValueError("teacher capability arrays must be 2D")
    if left_targets.shape != right_targets.shape:
        raise ValueError("teacher_capability_i and teacher_capability_j must have the same shape")
    if left_targets.shape[0] != left_features.shape[0]:
        raise ValueError("student and teacher arrays must have the same pair count")
    if left_targets.shape[1] != len(CAPABILITY_TARGETS):
        raise ValueError(f"teacher capability target dimension must be {len(CAPABILITY_TARGETS)}")
    if arrays["pair_weight"].shape != (left_features.shape[0],):
        raise ValueError("pair_weight must have one value per pair")
    for key in STUDENT_INPUT_KEYS + TEACHER_TARGET_KEYS + ("pair_weight",):
        if not np.isfinite(arrays[key]).all():
            raise ValueError(f"{key} contains non-finite values")
    if np.any(arrays["pair_weight"] < 0.0):
        raise ValueError("pair_weight must be non-negative")
    return DatasetContract(
        pairs=int(left_features.shape[0]),
        student_feature_dim=int(left_features.shape[1]),
        target_dim=int(left_targets.shape[1]),
        student_input_keys=STUDENT_INPUT_KEYS,
        teacher_target_keys=TEACHER_TARGET_KEYS,
        training_metadata_keys=TRAINING_METADATA_KEYS,
    )


def split_pairs(num_pairs: int, train_fraction: float, seed: int) -> PairSplit:
    if num_pairs < 4:
        raise ValueError("at least four pairs are required for train/validation split")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    rng = np.random.default_rng(seed)
    indices = rng.permutation(num_pairs)
    train_count = int(round(num_pairs * train_fraction))
    train_count = min(max(train_count, 1), num_pairs - 1)
    return PairSplit(
        train_indices=np.sort(indices[:train_count]),
        val_indices=np.sort(indices[train_count:]),
    )


def _normalization(arrays: dict[str, np.ndarray], train_indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_features = np.concatenate(
        [arrays["student_p0_i"][train_indices], arrays["student_p0_j"][train_indices]],
        axis=0,
    )
    train_targets = np.concatenate(
        [arrays["teacher_capability_i"][train_indices], arrays["teacher_capability_j"][train_indices]],
        axis=0,
    )
    feature_mean = train_features.mean(axis=0, keepdims=True).astype(np.float32)
    feature_std = (train_features.std(axis=0, keepdims=True) + 1e-6).astype(np.float32)
    target_mean = train_targets.mean(axis=0, keepdims=True).astype(np.float32)
    target_std = (train_targets.std(axis=0, keepdims=True) + 1e-6).astype(np.float32)
    return feature_mean, feature_std, target_mean, target_std


def _torch_batch(
    arrays: dict[str, np.ndarray],
    indices: np.ndarray,
    feature_mean: np.ndarray,
    feature_std: np.ndarray,
    target_mean: np.ndarray,
    target_std: np.ndarray,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    x_i = (arrays["student_p0_i"][indices] - feature_mean) / feature_std
    x_j = (arrays["student_p0_j"][indices] - feature_mean) / feature_std
    y_i = (arrays["teacher_capability_i"][indices] - target_mean) / target_std
    y_j = (arrays["teacher_capability_j"][indices] - target_mean) / target_std
    weights = arrays["pair_weight"][indices].astype(np.float32)
    weights = weights / max(float(weights.mean()), 1e-6)
    return {
        "x_i": torch.as_tensor(x_i, dtype=torch.float32, device=device),
        "x_j": torch.as_tensor(x_j, dtype=torch.float32, device=device),
        "y_i": torch.as_tensor(y_i, dtype=torch.float32, device=device),
        "y_j": torch.as_tensor(y_j, dtype=torch.float32, device=device),
        "weights": torch.as_tensor(weights, dtype=torch.float32, device=device),
    }


def _loss_components(
    pred_i: torch.Tensor,
    pred_j: torch.Tensor,
    y_i: torch.Tensor,
    y_j: torch.Tensor,
    weights: torch.Tensor,
    delta_loss_coef: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    target_square = 0.5 * (torch.square(pred_i - y_i) + torch.square(pred_j - y_j))
    delta_square = torch.square((pred_i - pred_j) - (y_i - y_j))
    weight_sum = weights.sum().clamp_min(1e-6)
    target_by_dim = (target_square * weights[:, None]).sum(dim=0) / weight_sum
    delta_by_dim = (delta_square * weights[:, None]).sum(dim=0) / weight_sum
    target_loss = target_by_dim.mean()
    delta_loss = delta_by_dim.mean()
    combined_loss = target_loss + delta_loss_coef * delta_loss
    metrics = {
        "combined_loss": float(combined_loss.detach().cpu().item()),
        "target_loss": float(target_loss.detach().cpu().item()),
        "delta_loss": float(delta_loss.detach().cpu().item()),
    }
    for index, name in enumerate(CAPABILITY_TARGETS):
        metrics[f"{name}_loss"] = float(target_by_dim[index].detach().cpu().item())
        metrics[f"{name}_delta_loss"] = float(delta_by_dim[index].detach().cpu().item())
    return combined_loss, metrics


def evaluate_model(
    model: CapabilityBeliefRegressor | None,
    batch: dict[str, torch.Tensor],
    delta_loss_coef: float,
) -> dict[str, float]:
    with torch.no_grad():
        if model is None:
            pred_i = torch.zeros_like(batch["y_i"])
            pred_j = torch.zeros_like(batch["y_j"])
        else:
            model.eval()
            pred_i = model(batch["x_i"])
            pred_j = model(batch["x_j"])
        _, metrics = _loss_components(
            pred_i=pred_i,
            pred_j=pred_j,
            y_i=batch["y_i"],
            y_j=batch["y_j"],
            weights=batch["weights"],
            delta_loss_coef=delta_loss_coef,
        )
    return metrics


def train_one_seed(
    arrays: dict[str, np.ndarray],
    optimization_seed: int,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    delta_loss_coef: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = validate_dataset_contract(arrays)
    split = split_pairs(contract.pairs, train_fraction=train_fraction, seed=optimization_seed)
    feature_mean, feature_std, target_mean, target_std = _normalization(arrays, split.train_indices)
    train_batch = _torch_batch(arrays, split.train_indices, feature_mean, feature_std, target_mean, target_std, device)
    val_batch = _torch_batch(arrays, split.val_indices, feature_mean, feature_std, target_mean, target_std, device)

    torch.manual_seed(optimization_seed)
    rng = np.random.default_rng(optimization_seed)
    model = CapabilityBeliefRegressor(
        input_dim=contract.student_feature_dim,
        hidden_dim=hidden_dim,
        target_dim=contract.target_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    rows: list[dict[str, Any]] = []

    for phase, model_for_eval in (("constant", None), ("before", model)):
        for split_name, batch in (("train", train_batch), ("val", val_batch)):
            rows.append(
                {
                    "optimization_seed": optimization_seed,
                    "phase": phase,
                    "split": split_name,
                    "pairs": int(batch["weights"].shape[0]),
                    **evaluate_model(model_for_eval, batch, delta_loss_coef=delta_loss_coef),
                }
            )

    for _ in range(steps):
        sampled = rng.choice(split.train_indices, size=min(batch_size, len(split.train_indices)), replace=len(split.train_indices) < batch_size)
        batch = _torch_batch(arrays, sampled, feature_mean, feature_std, target_mean, target_std, device)
        model.train()
        pred_i = model(batch["x_i"])
        pred_j = model(batch["x_j"])
        loss, _ = _loss_components(
            pred_i=pred_i,
            pred_j=pred_j,
            y_i=batch["y_i"],
            y_j=batch["y_j"],
            weights=batch["weights"],
            delta_loss_coef=delta_loss_coef,
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

    for split_name, batch in (("train", train_batch), ("val", val_batch)):
        rows.append(
            {
                "optimization_seed": optimization_seed,
                "phase": "after",
                "split": split_name,
                "pairs": int(batch["weights"].shape[0]),
                **evaluate_model(model, batch, delta_loss_coef=delta_loss_coef),
            }
        )

    seed_summary = summarize_seed(rows, optimization_seed)
    seed_summary.update(
        {
            "train_pairs": int(len(split.train_indices)),
            "val_pairs": int(len(split.val_indices)),
            "feature_dim": contract.student_feature_dim,
            "target_dim": contract.target_dim,
        }
    )
    return rows, seed_summary


def _row_by_phase(rows: list[dict[str, Any]], optimization_seed: int, phase: str, split: str) -> dict[str, Any]:
    matches = [
        row for row in rows
        if int(row["optimization_seed"]) == optimization_seed and str(row["phase"]) == phase and str(row["split"]) == split
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
        "optimization_seed": optimization_seed,
        "train_combined_loss_improvement": float(before_train["combined_loss"] - after_train["combined_loss"]),
        "train_target_loss_improvement": float(before_train["target_loss"] - after_train["target_loss"]),
        "train_delta_loss_improvement": float(before_train["delta_loss"] - after_train["delta_loss"]),
        "val_combined_loss_improvement": float(before_val["combined_loss"] - after_val["combined_loss"]),
        "val_target_loss_improvement": float(before_val["target_loss"] - after_val["target_loss"]),
        "val_delta_loss_improvement": float(before_val["delta_loss"] - after_val["delta_loss"]),
    }
    for name in CAPABILITY_TARGETS:
        summary[f"val_{name}_loss_improvement"] = float(before_val[f"{name}_loss"] - after_val[f"{name}_loss"])
        summary[f"val_{name}_delta_loss_improvement"] = float(before_val[f"{name}_delta_loss"] - after_val[f"{name}_delta_loss"])
    summary["objective_seed_pass"] = bool(
        summary["val_combined_loss_improvement"] > 0.0
        and summary["val_target_loss_improvement"] > 0.0
        and summary["val_delta_loss_improvement"] > 0.0
    )
    return summary


def summarize_run(
    dataset_path: Path,
    arrays: dict[str, np.ndarray],
    seed_summaries: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    contract = validate_dataset_contract(arrays)
    val_combined = np.asarray([row["val_combined_loss_improvement"] for row in seed_summaries], dtype=np.float32)
    val_target = np.asarray([row["val_target_loss_improvement"] for row in seed_summaries], dtype=np.float32)
    val_delta = np.asarray([row["val_delta_loss_improvement"] for row in seed_summaries], dtype=np.float32)
    per_target = {
        name: float(np.mean([row[f"val_{name}_loss_improvement"] for row in seed_summaries]))
        for name in CAPABILITY_TARGETS
    }
    per_delta = {
        name: float(np.mean([row[f"val_{name}_delta_loss_improvement"] for row in seed_summaries]))
        for name in CAPABILITY_TARGETS
    }
    objective_pass = bool(
        len(seed_summaries) >= 3
        and all(bool(row["objective_seed_pass"]) for row in seed_summaries)
        and all(value > 0.0 for value in per_target.values())
        and all(value > 0.0 for value in per_delta.values())
    )
    return {
        "run_type": "capability_belief_objective_sanity",
        "dataset_npz": str(dataset_path),
        "optimization_seeds": list(args.optimization_seeds),
        "pairs": contract.pairs,
        "student_feature_dim": contract.student_feature_dim,
        "target_dim": contract.target_dim,
        "student_input_keys_used": list(contract.student_input_keys),
        "teacher_target_keys_used": list(contract.teacher_target_keys),
        "training_metadata_keys_not_used_as_inputs": list(contract.training_metadata_keys),
        "capability_targets": list(CAPABILITY_TARGETS),
        "train_fraction": args.train_fraction,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "hidden_dim": args.hidden_dim,
        "delta_loss_coef": args.delta_loss_coef,
        "mean_val_combined_loss_improvement": float(np.mean(val_combined)),
        "mean_val_target_loss_improvement": float(np.mean(val_target)),
        "mean_val_delta_loss_improvement": float(np.mean(val_delta)),
        "min_val_combined_loss_improvement": float(np.min(val_combined)),
        "min_val_target_loss_improvement": float(np.min(val_target)),
        "min_val_delta_loss_improvement": float(np.min(val_delta)),
        "mean_val_target_loss_improvement_by_target": per_target,
        "mean_val_delta_loss_improvement_by_target": per_delta,
        "seed_pass_count": int(sum(bool(row["objective_seed_pass"]) for row in seed_summaries)),
        "objective_pass": objective_pass,
        "admission_decision": (
            "admit_for_guarded_actor_hidden_state_integration_test"
            if objective_pass
            else "do_not_admit_until_objective_losses_reduce_on_all_required_axes"
        ),
        "actor_contract": "objective uses student_p0_i/student_p0_j deployable history only; hidden diagnostics are not actor inputs",
    }


def run_objective_sanity(args: argparse.Namespace) -> dict[str, Any]:
    arrays = load_dataset_npz(args.dataset_npz)
    device = torch.device(args.device)
    all_loss_rows: list[dict[str, Any]] = []
    seed_summaries: list[dict[str, Any]] = []
    for optimization_seed in args.optimization_seeds:
        loss_rows, seed_summary = train_one_seed(
            arrays=arrays,
            optimization_seed=optimization_seed,
            train_fraction=args.train_fraction,
            steps=args.steps,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            hidden_dim=args.hidden_dim,
            delta_loss_coef=args.delta_loss_coef,
            device=device,
        )
        all_loss_rows.extend(loss_rows)
        seed_summaries.append(seed_summary)
    summary = summarize_run(args.dataset_npz, arrays, seed_summaries, args)

    run_dir = args.run_dir or make_run_dir(prefix="m152_capability_belief_objective_sanity")
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "loss_summary.csv", all_loss_rows)
    write_csv_rows(run_dir / "seed_summary.csv", seed_summaries)
    write_json(run_dir / "summary.json", summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "capability_belief_objective_sanity",
            "dataset_npz": args.dataset_npz,
            "run_dir": run_dir,
            "artifacts": {
                "loss_summary_csv": run_dir / "loss_summary.csv",
                "seed_summary_csv": run_dir / "seed_summary.csv",
                "summary_json": run_dir / "summary.json",
            },
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M152 capability-belief objective-only sanity.")
    parser.add_argument("--dataset-npz", type=Path, default=Path("runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz"))
    parser.add_argument("--optimization-seeds", type=parse_seed_list, default=(9600, 9601, 9602))
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--hidden-dim", type=int, default=96)
    parser.add_argument("--delta-loss-coef", type=float, default=0.5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    summary = run_objective_sanity(args)
    print(
        "objective_pass={objective_pass} seed_pass_count={seed_pass_count} "
        "mean_val_combined_loss_improvement={mean_val_combined_loss_improvement:.6f}".format(**summary)
    )


if __name__ == "__main__":
    main()
