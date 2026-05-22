"""M153 recurrent hidden-state smoke for capability-belief targets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_belief_objective_sanity import (
    TEACHER_TARGET_KEYS,
    TRAINING_METADATA_KEYS,
    _loss_components,
    _row_by_phase,
    load_dataset_npz,
    parse_seed_list,
    split_pairs,
    validate_dataset_contract,
)
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS
from autodrift.train_ppo import (
    ActorCritic,
    HUMAN_VIEW_OBS_DIM,
    recurrent_feature_sequence,
    recurrent_response_hidden_sequence,
)


FEATURE_SOURCES = ("response_hidden", "policy_features")
STUDENT_SEQUENCE_KEYS = ("student_p0_i", "student_p0_j")


@dataclass(frozen=True)
class HiddenIntegrationBatch:
    seq_i: torch.Tensor
    seq_j: torch.Tensor
    y_i: torch.Tensor
    y_j: torch.Tensor
    weights: torch.Tensor


class CapabilityBeliefHead(nn.Module):
    def __init__(self, hidden_dim: int, target_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, target_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


def p0_history_sequences(flat_features: np.ndarray, history_window: int) -> np.ndarray:
    values = np.asarray(flat_features, dtype=np.float32)
    if values.ndim != 2:
        raise ValueError("P0 history features must be a 2D array")
    expected_dim = int(history_window) * HUMAN_VIEW_OBS_DIM
    if values.shape[1] != expected_dim:
        raise ValueError(
            f"P0 history feature dim must be {expected_dim} for history_window={history_window}, "
            f"got {values.shape[1]}"
        )
    return values.reshape(values.shape[0], int(history_window), HUMAN_VIEW_OBS_DIM).astype(np.float32)


def _target_normalization(arrays: dict[str, np.ndarray], train_indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    train_targets = np.concatenate(
        [arrays["teacher_capability_i"][train_indices], arrays["teacher_capability_j"][train_indices]],
        axis=0,
    )
    target_mean = train_targets.mean(axis=0, keepdims=True).astype(np.float32)
    target_std = (train_targets.std(axis=0, keepdims=True) + 1e-6).astype(np.float32)
    return target_mean, target_std


def _hidden_batch(
    arrays: dict[str, np.ndarray],
    indices: np.ndarray,
    target_mean: np.ndarray,
    target_std: np.ndarray,
    history_window: int,
    device: torch.device,
) -> HiddenIntegrationBatch:
    seq_i = p0_history_sequences(arrays["student_p0_i"][indices], history_window)
    seq_j = p0_history_sequences(arrays["student_p0_j"][indices], history_window)
    y_i = (arrays["teacher_capability_i"][indices] - target_mean) / target_std
    y_j = (arrays["teacher_capability_j"][indices] - target_mean) / target_std
    weights = arrays["pair_weight"][indices].astype(np.float32)
    weights = weights / max(float(weights.mean()), 1e-6)
    return HiddenIntegrationBatch(
        seq_i=torch.as_tensor(seq_i, dtype=torch.float32, device=device),
        seq_j=torch.as_tensor(seq_j, dtype=torch.float32, device=device),
        y_i=torch.as_tensor(y_i, dtype=torch.float32, device=device),
        y_j=torch.as_tensor(y_j, dtype=torch.float32, device=device),
        weights=torch.as_tensor(weights, dtype=torch.float32, device=device),
    )


def _sequence_features(
    model: ActorCritic,
    sequences: torch.Tensor,
    feature_source: str,
) -> torch.Tensor:
    if feature_source not in FEATURE_SOURCES:
        raise ValueError("feature_source must be one of: " + ", ".join(FEATURE_SOURCES))
    seq_t = sequences.transpose(0, 1)
    dones = torch.zeros(seq_t.shape[0], seq_t.shape[1], dtype=torch.float32, device=sequences.device)
    hidden = model.initial_hidden(seq_t.shape[1], sequences.device)
    if feature_source == "response_hidden":
        features = recurrent_response_hidden_sequence(model, seq_t, hidden, dones)
    else:
        features = recurrent_feature_sequence(model, seq_t, hidden, dones)
    return features[-1]


def trainable_hidden_integration_parameters(
    model: ActorCritic,
    head: CapabilityBeliefHead,
    feature_source: str,
) -> list[nn.Parameter]:
    if model.response_encoder is None or model.online_gru_cell is None:
        raise ValueError("capability-belief hidden integration requires a human-view recurrent model")
    params: list[nn.Parameter] = [
        *model.response_encoder.parameters(),
        *model.online_gru_cell.parameters(),
        *head.parameters(),
    ]
    if feature_source == "policy_features":
        if model.context_encoder is None or model.response_context_fusion is None:
            raise ValueError("policy_features source requires context encoder and fusion modules")
        params.extend(model.context_encoder.parameters())
        params.extend(model.response_context_fusion.parameters())
    elif feature_source != "response_hidden":
        raise ValueError("feature_source must be one of: " + ", ".join(FEATURE_SOURCES))
    return params


def evaluate_hidden_objective(
    model: ActorCritic,
    head: CapabilityBeliefHead,
    batch: HiddenIntegrationBatch,
    feature_source: str,
    delta_loss_coef: float,
) -> dict[str, float]:
    with torch.no_grad():
        model.eval()
        head.eval()
        pred_i = head(_sequence_features(model, batch.seq_i, feature_source))
        pred_j = head(_sequence_features(model, batch.seq_j, feature_source))
        _, metrics = _loss_components(
            pred_i=pred_i,
            pred_j=pred_j,
            y_i=batch.y_i,
            y_j=batch.y_j,
            weights=batch.weights,
            delta_loss_coef=delta_loss_coef,
        )
    return metrics


def train_one_hidden_seed(
    arrays: dict[str, np.ndarray],
    optimization_seed: int,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    hidden_size: int,
    history_window: int,
    feature_source: str,
    delta_loss_coef: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = validate_dataset_contract(arrays)
    expected_dim = history_window * HUMAN_VIEW_OBS_DIM
    if contract.student_feature_dim != expected_dim:
        raise ValueError(
            f"student feature dim {contract.student_feature_dim} does not match "
            f"history_window={history_window} and frame dim {HUMAN_VIEW_OBS_DIM}"
        )
    split = split_pairs(contract.pairs, train_fraction=train_fraction, seed=optimization_seed)
    target_mean, target_std = _target_normalization(arrays, split.train_indices)
    train_batch = _hidden_batch(arrays, split.train_indices, target_mean, target_std, history_window, device)
    val_batch = _hidden_batch(arrays, split.val_indices, target_mean, target_std, history_window, device)

    torch.manual_seed(optimization_seed)
    rng = np.random.default_rng(optimization_seed)
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=hidden_size,
        actor_encoder="human_view_online_gru",
    ).to(device)
    head = CapabilityBeliefHead(hidden_size, contract.target_dim).to(device)
    trainable_parameters = trainable_hidden_integration_parameters(model, head, feature_source)
    optimizer = torch.optim.AdamW(trainable_parameters, lr=learning_rate, weight_decay=weight_decay)
    rows: list[dict[str, Any]] = []

    for split_name, batch in (("train", train_batch), ("val", val_batch)):
        rows.append(
            {
                "optimization_seed": optimization_seed,
                "phase": "before",
                "split": split_name,
                "pairs": int(batch.weights.shape[0]),
                **evaluate_hidden_objective(model, head, batch, feature_source, delta_loss_coef),
            }
        )

    for _ in range(steps):
        sampled = rng.choice(
            split.train_indices,
            size=min(batch_size, len(split.train_indices)),
            replace=len(split.train_indices) < batch_size,
        )
        batch = _hidden_batch(arrays, sampled, target_mean, target_std, history_window, device)
        model.train()
        head.train()
        pred_i = head(_sequence_features(model, batch.seq_i, feature_source))
        pred_j = head(_sequence_features(model, batch.seq_j, feature_source))
        loss, _ = _loss_components(
            pred_i=pred_i,
            pred_j=pred_j,
            y_i=batch.y_i,
            y_j=batch.y_j,
            weights=batch.weights,
            delta_loss_coef=delta_loss_coef,
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable_parameters, max_norm=1.0)
        optimizer.step()

    for split_name, batch in (("train", train_batch), ("val", val_batch)):
        rows.append(
            {
                "optimization_seed": optimization_seed,
                "phase": "after",
                "split": split_name,
                "pairs": int(batch.weights.shape[0]),
                **evaluate_hidden_objective(model, head, batch, feature_source, delta_loss_coef),
            }
        )

    seed_summary = summarize_hidden_seed(rows, optimization_seed)
    seed_summary.update(
        {
            "train_pairs": int(len(split.train_indices)),
            "val_pairs": int(len(split.val_indices)),
            "feature_dim": contract.student_feature_dim,
            "target_dim": contract.target_dim,
            "history_window": int(history_window),
            "feature_source": feature_source,
        }
    )
    return rows, seed_summary


def summarize_hidden_seed(rows: list[dict[str, Any]], optimization_seed: int) -> dict[str, Any]:
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


def summarize_hidden_run(
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
    integration_pass = bool(
        len(seed_summaries) >= 3
        and all(bool(row["objective_seed_pass"]) for row in seed_summaries)
        and all(value > 0.0 for value in per_target.values())
        and all(value > 0.0 for value in per_delta.values())
    )
    return {
        "run_type": "capability_belief_hidden_integration_smoke",
        "dataset_npz": str(dataset_path),
        "optimization_seeds": list(args.optimization_seeds),
        "pairs": contract.pairs,
        "student_feature_dim": contract.student_feature_dim,
        "history_window": int(args.history_window),
        "target_dim": contract.target_dim,
        "student_sequence_keys_used": list(STUDENT_SEQUENCE_KEYS),
        "teacher_target_keys_used": list(TEACHER_TARGET_KEYS),
        "training_metadata_keys_not_used_as_inputs": list(TRAINING_METADATA_KEYS),
        "capability_targets": list(CAPABILITY_TARGETS),
        "feature_source": args.feature_source,
        "actor_encoder": "human_view_online_gru",
        "train_fraction": args.train_fraction,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "hidden_size": args.hidden_size,
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
        "integration_smoke_pass": integration_pass,
        "admission_decision": (
            "admit_guarded_behavior_and_wrong_history_gate_design"
            if integration_pass
            else "do_not_admit_ppo_until_hidden_integration_losses_reduce_on_all_required_axes"
        ),
        "actor_contract": (
            "uses 25-step sequences of canonical 72-value P0 human-view observations; "
            "hidden diagnostics and hidden physics are not actor inputs"
        ),
        "promotion_boundary": "not a driver promotion and not broad PPO; behavior retention and wrong-history gates remain required",
    }


def run_hidden_integration_smoke(args: argparse.Namespace) -> dict[str, Any]:
    arrays = load_dataset_npz(args.dataset_npz)
    device = torch.device(args.device)
    all_loss_rows: list[dict[str, Any]] = []
    seed_summaries: list[dict[str, Any]] = []
    for optimization_seed in args.optimization_seeds:
        loss_rows, seed_summary = train_one_hidden_seed(
            arrays=arrays,
            optimization_seed=optimization_seed,
            train_fraction=args.train_fraction,
            steps=args.steps,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            hidden_size=args.hidden_size,
            history_window=args.history_window,
            feature_source=args.feature_source,
            delta_loss_coef=args.delta_loss_coef,
            device=device,
        )
        all_loss_rows.extend(loss_rows)
        seed_summaries.append(seed_summary)
    summary = summarize_hidden_run(args.dataset_npz, arrays, seed_summaries, args)

    run_dir = args.run_dir or make_run_dir(prefix="m153_capability_belief_hidden_integration")
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "loss_summary.csv", all_loss_rows)
    write_csv_rows(run_dir / "seed_summary.csv", seed_summaries)
    write_json(run_dir / "summary.json", summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "capability_belief_hidden_integration_smoke",
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
    parser = argparse.ArgumentParser(description="Run M153 capability-belief recurrent hidden integration smoke.")
    parser.add_argument("--dataset-npz", type=Path, default=Path("runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz"))
    parser.add_argument("--optimization-seeds", type=parse_seed_list, default=(9610, 9611, 9612))
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--weight-decay", type=float, default=0.001)
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--history-window", type=int, default=25)
    parser.add_argument("--feature-source", choices=FEATURE_SOURCES, default="response_hidden")
    parser.add_argument("--delta-loss-coef", type=float, default=0.5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    summary = run_hidden_integration_smoke(args)
    print(
        "integration_smoke_pass={integration_smoke_pass} seed_pass_count={seed_pass_count} "
        "mean_val_combined_loss_improvement={mean_val_combined_loss_improvement:.6f}".format(**summary)
    )


if __name__ == "__main__":
    main()
