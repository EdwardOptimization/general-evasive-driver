"""M155 small capability-belief auxiliary candidate from an existing checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, to_jsonable, write_csv_rows, write_json
from autodrift.capability_belief_hidden_integration import (
    CapabilityBeliefHead,
    _hidden_batch,
    _sequence_features,
    _target_normalization,
    evaluate_hidden_objective,
    trainable_hidden_integration_parameters,
)
from autodrift.capability_belief_objective_sanity import (
    _loss_components,
    _row_by_phase,
    load_dataset_npz,
    parse_seed_list,
    split_pairs,
    validate_dataset_contract,
)
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, ActorCritic


def save_checkpoint_like(
    model: ActorCritic,
    source_checkpoint: dict[str, Any],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": source_checkpoint["config"],
            "metadata": to_jsonable(metadata),
        },
        path,
    )


def _feature_anchor_loss(
    model: ActorCritic,
    reference_model: ActorCritic,
    seq_i: torch.Tensor,
    seq_j: torch.Tensor,
    feature_source: str,
) -> torch.Tensor:
    current_i = _sequence_features(model, seq_i, feature_source)
    current_j = _sequence_features(model, seq_j, feature_source)
    with torch.no_grad():
        reference_i = _sequence_features(reference_model, seq_i, feature_source)
        reference_j = _sequence_features(reference_model, seq_j, feature_source)
    return 0.5 * (torch.square(current_i - reference_i).mean() + torch.square(current_j - reference_j).mean())


def _evaluate_candidate(
    model: ActorCritic,
    reference_model: ActorCritic,
    head: CapabilityBeliefHead,
    batch: Any,
    feature_source: str,
    delta_loss_coef: float,
    anchor_coef: float,
) -> dict[str, float]:
    metrics = evaluate_hidden_objective(model, head, batch, feature_source, delta_loss_coef)
    with torch.no_grad():
        anchor_loss = _feature_anchor_loss(
            model=model,
            reference_model=reference_model,
            seq_i=batch.seq_i,
            seq_j=batch.seq_j,
            feature_source=feature_source,
        )
    metrics["feature_anchor_loss"] = float(anchor_loss.detach().cpu().item())
    metrics["anchored_combined_loss"] = float(metrics["combined_loss"] + anchor_coef * metrics["feature_anchor_loss"])
    return metrics


def train_one_candidate_seed(
    *,
    checkpoint_path: Path,
    arrays: dict[str, np.ndarray],
    optimization_seed: int,
    train_fraction: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    history_window: int,
    feature_source: str,
    delta_loss_coef: float,
    anchor_coef: float,
    device: torch.device,
) -> tuple[ActorCritic, dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    contract = validate_dataset_contract(arrays)
    if contract.student_feature_dim != history_window * HUMAN_VIEW_OBS_DIM:
        raise ValueError("dataset does not match the requested P0 history window")
    model, source_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(device), obs_dim=HUMAN_VIEW_OBS_DIM)
    reference_model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(device), obs_dim=HUMAN_VIEW_OBS_DIM)
    if model.actor_encoder != "human_view_online_gru":
        raise ValueError("M155 candidate requires a human_view_online_gru checkpoint")
    reference_model.eval()
    for parameter in reference_model.parameters():
        parameter.requires_grad_(False)

    split = split_pairs(contract.pairs, train_fraction=train_fraction, seed=optimization_seed)
    target_mean, target_std = _target_normalization(arrays, split.train_indices)
    train_batch = _hidden_batch(arrays, split.train_indices, target_mean, target_std, history_window, device)
    val_batch = _hidden_batch(arrays, split.val_indices, target_mean, target_std, history_window, device)

    torch.manual_seed(optimization_seed)
    rng = np.random.default_rng(optimization_seed)
    head = CapabilityBeliefHead(model.actor_mean.in_features, contract.target_dim).to(device)
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
                **_evaluate_candidate(
                    model,
                    reference_model,
                    head,
                    batch,
                    feature_source,
                    delta_loss_coef,
                    anchor_coef,
                ),
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
        belief_loss, _ = _loss_components(
            pred_i=pred_i,
            pred_j=pred_j,
            y_i=batch.y_i,
            y_j=batch.y_j,
            weights=batch.weights,
            delta_loss_coef=delta_loss_coef,
        )
        anchor_loss = _feature_anchor_loss(
            model=model,
            reference_model=reference_model,
            seq_i=batch.seq_i,
            seq_j=batch.seq_j,
            feature_source=feature_source,
        )
        loss = belief_loss + anchor_coef * anchor_loss
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
                **_evaluate_candidate(
                    model,
                    reference_model,
                    head,
                    batch,
                    feature_source,
                    delta_loss_coef,
                    anchor_coef,
                ),
            }
        )

    summary = summarize_candidate_seed(rows, optimization_seed)
    summary.update(
        {
            "train_pairs": int(len(split.train_indices)),
            "val_pairs": int(len(split.val_indices)),
            "feature_dim": contract.student_feature_dim,
            "target_dim": contract.target_dim,
            "history_window": int(history_window),
            "feature_source": feature_source,
        }
    )
    return model, source_checkpoint, rows, summary


def summarize_candidate_seed(rows: list[dict[str, Any]], optimization_seed: int) -> dict[str, Any]:
    before_val = _row_by_phase(rows, optimization_seed, "before", "val")
    after_val = _row_by_phase(rows, optimization_seed, "after", "val")
    before_train = _row_by_phase(rows, optimization_seed, "before", "train")
    after_train = _row_by_phase(rows, optimization_seed, "after", "train")
    summary = {
        "optimization_seed": optimization_seed,
        "train_combined_loss_improvement": float(before_train["combined_loss"] - after_train["combined_loss"]),
        "train_target_loss_improvement": float(before_train["target_loss"] - after_train["target_loss"]),
        "train_delta_loss_improvement": float(before_train["delta_loss"] - after_train["delta_loss"]),
        "train_anchor_loss_after": float(after_train["feature_anchor_loss"]),
        "val_combined_loss_improvement": float(before_val["combined_loss"] - after_val["combined_loss"]),
        "val_target_loss_improvement": float(before_val["target_loss"] - after_val["target_loss"]),
        "val_delta_loss_improvement": float(before_val["delta_loss"] - after_val["delta_loss"]),
        "val_anchor_loss_after": float(after_val["feature_anchor_loss"]),
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


def summarize_candidate_run(
    *,
    checkpoint_path: Path,
    dataset_npz: Path,
    arrays: dict[str, np.ndarray],
    seed_summary: dict[str, Any],
    optimized_checkpoint: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    contract = validate_dataset_contract(arrays)
    per_target = {
        name: float(seed_summary[f"val_{name}_loss_improvement"])
        for name in CAPABILITY_TARGETS
    }
    per_delta = {
        name: float(seed_summary[f"val_{name}_delta_loss_improvement"])
        for name in CAPABILITY_TARGETS
    }
    objective_pass = bool(
        seed_summary["objective_seed_pass"]
        and all(value > 0.0 for value in per_target.values())
        and all(value > 0.0 for value in per_delta.values())
    )
    return {
        "run_type": "capability_belief_aux_candidate_smoke",
        "init_checkpoint": str(checkpoint_path),
        "optimized_checkpoint": str(optimized_checkpoint),
        "dataset_npz": str(dataset_npz),
        "optimization_seed": int(seed_summary["optimization_seed"]),
        "pairs": contract.pairs,
        "student_feature_dim": contract.student_feature_dim,
        "history_window": int(args.history_window),
        "target_dim": contract.target_dim,
        "actor_encoder": "human_view_online_gru",
        "actor_obs_dim": HUMAN_VIEW_OBS_DIM,
        "feature_source": args.feature_source,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "delta_loss_coef": args.delta_loss_coef,
        "anchor_coef": args.anchor_coef,
        "val_combined_loss_improvement": float(seed_summary["val_combined_loss_improvement"]),
        "val_target_loss_improvement": float(seed_summary["val_target_loss_improvement"]),
        "val_delta_loss_improvement": float(seed_summary["val_delta_loss_improvement"]),
        "val_anchor_loss_after": float(seed_summary["val_anchor_loss_after"]),
        "val_target_loss_improvement_by_target": per_target,
        "val_delta_loss_improvement_by_target": per_delta,
        "objective_pass": objective_pass,
        "candidate_created": True,
        "actor_contract": "optimized checkpoint keeps 72-value P0 human-view actor inputs; no hidden diagnostics or hidden physics are actor inputs",
        "next_gate": "run M154 cheap pre-screens before strict miners or PPO promotion",
    }


def run_aux_candidate(args: argparse.Namespace) -> dict[str, Any]:
    arrays = load_dataset_npz(args.dataset_npz)
    device = torch.device(args.device)
    optimization_seed = int(args.optimization_seeds[0])
    model, source_checkpoint, rows, seed_summary = train_one_candidate_seed(
        checkpoint_path=args.init_checkpoint,
        arrays=arrays,
        optimization_seed=optimization_seed,
        train_fraction=args.train_fraction,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        history_window=args.history_window,
        feature_source=args.feature_source,
        delta_loss_coef=args.delta_loss_coef,
        anchor_coef=args.anchor_coef,
        device=device,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m155_capability_belief_aux_candidate")
    run_dir.mkdir(parents=True, exist_ok=True)
    optimized_checkpoint = run_dir / "optimized_checkpoint.pt"
    save_checkpoint_like(
        model,
        source_checkpoint,
        optimized_checkpoint,
        {
            "run_type": "capability_belief_aux_candidate_smoke",
            "init_checkpoint": args.init_checkpoint,
            "dataset_npz": args.dataset_npz,
            "optimization_seed": optimization_seed,
            "steps": args.steps,
            "feature_source": args.feature_source,
            "anchor_coef": args.anchor_coef,
        },
    )
    summary = summarize_candidate_run(
        checkpoint_path=args.init_checkpoint,
        dataset_npz=args.dataset_npz,
        arrays=arrays,
        seed_summary=seed_summary,
        optimized_checkpoint=optimized_checkpoint,
        args=args,
    )
    write_csv_rows(run_dir / "loss_summary.csv", rows)
    write_csv_rows(run_dir / "seed_summary.csv", [seed_summary])
    write_json(run_dir / "summary.json", summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "capability_belief_aux_candidate_smoke",
            "init_checkpoint": args.init_checkpoint,
            "dataset_npz": args.dataset_npz,
            "artifacts": {
                "optimized_checkpoint": optimized_checkpoint,
                "loss_summary_csv": run_dir / "loss_summary.csv",
                "seed_summary_csv": run_dir / "seed_summary.csv",
                "summary_json": run_dir / "summary.json",
            },
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a small M155 capability-belief auxiliary checkpoint candidate.")
    parser.add_argument("--init-checkpoint", type=Path, default=Path("runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt"))
    parser.add_argument("--dataset-npz", type=Path, default=Path("runs/m151_capability_belief_dataset_multiseed/capability_belief_dataset.npz"))
    parser.add_argument("--optimization-seeds", type=parse_seed_list, default=(9620,))
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=0.001)
    parser.add_argument("--history-window", type=int, default=25)
    parser.add_argument("--feature-source", choices=("response_hidden", "policy_features"), default="response_hidden")
    parser.add_argument("--delta-loss-coef", type=float, default=0.5)
    parser.add_argument("--anchor-coef", type=float, default=10.0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    if len(args.optimization_seeds) != 1:
        raise SystemExit("M155 candidate smoke expects exactly one optimization seed")
    summary = run_aux_candidate(args)
    print(
        "candidate_created={candidate_created} objective_pass={objective_pass} "
        "val_combined_loss_improvement={val_combined_loss_improvement:.6f} "
        "val_anchor_loss_after={val_anchor_loss_after:.6f}".format(**summary)
    )


if __name__ == "__main__":
    main()
