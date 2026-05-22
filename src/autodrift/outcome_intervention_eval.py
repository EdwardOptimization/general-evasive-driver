"""Evaluate outcome-weighted intervention objectives on fixed random batches."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.intervention_objectives import (
    load_outcome_intervention_snippets,
    outcome_weighted_intervention_loss,
    squashed_action_log_prob,
    weighted_mean,
)


def parse_checkpoint_policy(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"checkpoint policy spec must be NAME=PATH, got {spec!r}")
    name, raw_path = spec.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"checkpoint policy spec has empty name: {spec!r}")
    return name, Path(raw_path)


def evaluate_checkpoint(
    *,
    label: str,
    checkpoint: Path,
    snippet_npz: Path,
    device: str,
    batch_size: int,
    batches: int,
    seed: int,
    logprob_margin: float,
    exact: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = np.load(snippet_npz)
    obs_dim = int(data["observation"].shape[1])
    act_dim = int(data["preferred_action"].shape[1])
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device, obs_dim=obs_dim)
    snippets = load_outcome_intervention_snippets(
        snippet_npz,
        device=next(model.parameters()).device,
        obs_dim=obs_dim,
        hidden_size=model.actor_mean.in_features,
        act_dim=act_dim,
    )
    losses: list[float] = []
    batch_rows: list[dict[str, Any]] = []
    with torch.no_grad():
        if exact:
            preferred_dist, _, _ = model.forward_recurrent(
                snippets.observation,
                snippets.preferred_hidden,
            )
            rejected_dist, _, _ = model.forward_recurrent(
                snippets.observation,
                snippets.rejected_hidden,
            )
            preferred_log_prob = squashed_action_log_prob(preferred_dist, snippets.preferred_action)
            rejected_log_prob = squashed_action_log_prob(rejected_dist, snippets.preferred_action)
            penalty = torch.nn.functional.softplus(
                rejected_log_prob - preferred_log_prob + float(logprob_margin)
            )
            loss = weighted_mean(penalty, snippets.weight.detach())
            value = float(loss.detach().cpu().item())
            losses.append(value)
            batch_rows.append({"policy": label, "batch": 0, "loss": value, "mode": "exact"})
        else:
            torch.manual_seed(int(seed))
            for batch_index in range(max(1, int(batches))):
                loss = outcome_weighted_intervention_loss(
                    model,
                    snippets,
                    batch_size=batch_size,
                    logprob_margin=logprob_margin,
                )
                value = float(loss.detach().cpu().item())
                losses.append(value)
                batch_rows.append({"policy": label, "batch": batch_index, "loss": value, "mode": "sampled"})
    loss_array = np.asarray(losses, dtype=np.float64)
    summary = {
        "policy": label,
        "checkpoint": str(checkpoint),
        "snippet_npz": str(snippet_npz),
        "snippets": snippets.size,
        "mode": "exact" if exact else "sampled",
        "batch_size": int(snippets.size if exact else batch_size),
        "batches": int(len(losses)),
        "seed": int(seed),
        "logprob_margin": float(logprob_margin),
        "loss_mean": float(loss_array.mean()),
        "loss_std": float(loss_array.std(ddof=0)),
        "loss_min": float(loss_array.min()),
        "loss_max": float(loss_array.max()),
    }
    return summary, batch_rows


def evaluate_policies(
    *,
    checkpoint_policies: list[tuple[str, Path]],
    snippet_npz: Path,
    device: str,
    batch_size: int,
    batches: int,
    seed: int,
    logprob_margin: float,
    exact: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries: list[dict[str, Any]] = []
    batch_rows: list[dict[str, Any]] = []
    for label, checkpoint in checkpoint_policies:
        summary, rows = evaluate_checkpoint(
            label=label,
            checkpoint=checkpoint,
            snippet_npz=snippet_npz,
            device=device,
            batch_size=batch_size,
            batches=batches,
            seed=seed,
            logprob_margin=logprob_margin,
            exact=exact,
        )
        summaries.append(summary)
        batch_rows.extend(rows)
    return pd.DataFrame(summaries), pd.DataFrame(batch_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate outcome intervention loss.")
    parser.add_argument("--snippet-npz", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--batches", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--logprob-margin", type=float, default=0.05)
    parser.add_argument(
        "--exact",
        action="store_true",
        help="Evaluate the deterministic full-corpus loss once instead of sampled fixed batches.",
    )
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="outcome_intervention_eval", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    summary, batch_losses = evaluate_policies(
        checkpoint_policies=args.checkpoint_policy,
        snippet_npz=args.snippet_npz,
        device=args.device,
        batch_size=args.batch_size,
        batches=args.batches,
        seed=args.seed,
        logprob_margin=args.logprob_margin,
        exact=args.exact,
    )
    summary_csv = run_dir / "policy_summary.csv"
    batch_csv = run_dir / "batch_losses.csv"
    summary.to_csv(summary_csv, index=False)
    batch_losses.to_csv(batch_csv, index=False)
    write_json(
        run_dir / "summary.json",
        {
            "run_type": "outcome_intervention_eval",
            "snippet_npz": args.snippet_npz,
            "device": args.device,
            "mode": "exact" if args.exact else "sampled",
            "exact": bool(args.exact),
            "batch_size": args.batch_size,
            "batches": args.batches,
            "seed": args.seed,
            "logprob_margin": args.logprob_margin,
            "policy_summary_csv": summary_csv,
            "batch_losses_csv": batch_csv,
            "policies": summary.to_dict(orient="records"),
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
