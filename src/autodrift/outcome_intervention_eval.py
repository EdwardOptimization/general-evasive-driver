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


def parse_source_npz(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"source npz spec must be NAME=PATH, got {spec!r}")
    name, raw_path = spec.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"source npz spec has empty name: {spec!r}")
    return name, Path(raw_path)


SNIPPET_MATCH_FIELDS = ("observation", "preferred_hidden", "rejected_hidden", "preferred_action")


def _load_float32_npz(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    return {name: np.asarray(data[name], dtype=np.float32) for name in data.files}


def _row_key(data: dict[str, np.ndarray], index: int) -> bytes:
    return b"|".join(
        np.ascontiguousarray(data[field][index], dtype=np.float32).tobytes() for field in SNIPPET_MATCH_FIELDS
    )


def match_source_rows(snippet_npz: Path, source_npzs: list[tuple[str, Path]]) -> pd.DataFrame:
    """Match combined-corpus rows to named source corpora.

    Source-aware exact reports are promotion-gate evidence, so matching is
    intentionally strict: every combined row must match exactly one source row
    by observation, hidden states, and preferred action.
    """

    combined = _load_float32_npz(snippet_npz)
    missing = [field for field in SNIPPET_MATCH_FIELDS if field not in combined]
    if missing:
        raise ValueError(f"combined snippet npz missing fields for source matching: {missing}")
    source_lookup: dict[bytes, dict[str, Any]] = {}
    for source_name, source_path in source_npzs:
        source = _load_float32_npz(source_path)
        missing_source = [field for field in SNIPPET_MATCH_FIELDS if field not in source]
        if missing_source:
            raise ValueError(f"source npz {source_path} missing fields for source matching: {missing_source}")
        rows = int(source["observation"].shape[0])
        for source_index in range(rows):
            key = _row_key(source, source_index)
            if key in source_lookup:
                previous = source_lookup[key]
                raise ValueError(
                    "source npz row matches more than one source: "
                    f"{previous['source']}:{previous['source_index']} and {source_name}:{source_index}"
                )
            source_lookup[key] = {
                "source": source_name,
                "source_index": int(source_index),
                "source_path": str(source_path),
            }
    rows: list[dict[str, Any]] = []
    for combined_row in range(int(combined["observation"].shape[0])):
        key = _row_key(combined, combined_row)
        match = source_lookup.get(key)
        if match is None:
            raise ValueError(f"combined snippet row {combined_row} did not match any source npz")
        rows.append({"combined_row": int(combined_row), **match})
    return pd.DataFrame(rows)


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


def evaluate_exact_source_reports(
    *,
    checkpoint_policies: list[tuple[str, Path]],
    snippet_npz: Path,
    source_npzs: list[tuple[str, Path]],
    device: str,
    logprob_margin: float,
    baseline_policy: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not source_npzs:
        return pd.DataFrame(), pd.DataFrame()

    row_sources = match_source_rows(snippet_npz, source_npzs)
    data = np.load(snippet_npz)
    obs_dim = int(data["observation"].shape[1])
    act_dim = int(data["preferred_action"].shape[1])
    weights_np = np.asarray(data["weight"], dtype=np.float64).clip(min=0.0)
    weight_sum = float(weights_np.sum())
    combined_denominator = max(weight_sum, 1.0)
    snippets = load_outcome_intervention_snippets(
        snippet_npz,
        device=torch.device("cpu" if device == "auto" else device),
        obs_dim=obs_dim,
        hidden_size=int(data["preferred_hidden"].shape[1]),
        act_dim=act_dim,
    )

    if baseline_policy is None and checkpoint_policies:
        baseline_policy = checkpoint_policies[0][0]

    per_row_records: list[dict[str, Any]] = []
    policy_penalties: dict[str, np.ndarray] = {}
    with torch.no_grad():
        for label, checkpoint in checkpoint_policies:
            model, _ = load_actor_critic_checkpoint(checkpoint, device=device, obs_dim=obs_dim)
            model_device = next(model.parameters()).device
            if snippets.observation.device != model_device:
                snippets = load_outcome_intervention_snippets(
                    snippet_npz,
                    device=model_device,
                    obs_dim=obs_dim,
                    hidden_size=model.actor_mean.in_features,
                    act_dim=act_dim,
                )
            preferred_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.preferred_hidden)
            rejected_dist, _, _ = model.forward_recurrent(snippets.observation, snippets.rejected_hidden)
            preferred_log_prob = squashed_action_log_prob(preferred_dist, snippets.preferred_action)
            rejected_log_prob = squashed_action_log_prob(rejected_dist, snippets.preferred_action)
            penalty = torch.nn.functional.softplus(
                rejected_log_prob - preferred_log_prob + float(logprob_margin)
            )
            penalty_np = penalty.detach().cpu().numpy().astype(np.float64)
            policy_penalties[label] = penalty_np
            weighted_np = penalty_np * weights_np
            for row, penalty_value, weighted_value, row_weight in zip(
                row_sources.to_dict(orient="records"), penalty_np, weighted_np, weights_np
            ):
                per_row_records.append(
                    {
                        "policy": label,
                        "combined_row": int(row["combined_row"]),
                        "source": row["source"],
                        "source_index": int(row["source_index"]),
                        "source_path": row["source_path"],
                        "weight": float(row_weight),
                        "penalty": float(penalty_value),
                        "weighted_penalty": float(weighted_value),
                        "combined_objective_contribution": float(weighted_value / combined_denominator),
                    }
                )

    per_row = pd.DataFrame(per_row_records)
    if baseline_policy is not None and baseline_policy in policy_penalties:
        base = per_row[per_row["policy"] == baseline_policy][
            ["combined_row", "penalty", "weighted_penalty", "combined_objective_contribution"]
        ].rename(
            columns={
                "penalty": "baseline_penalty",
                "weighted_penalty": "baseline_weighted_penalty",
                "combined_objective_contribution": "baseline_combined_objective_contribution",
            }
        )
        per_row = per_row.merge(base, on="combined_row", how="left")
        per_row["penalty_delta_vs_baseline"] = per_row["penalty"] - per_row["baseline_penalty"]
        per_row["weighted_delta_vs_baseline"] = (
            per_row["weighted_penalty"] - per_row["baseline_weighted_penalty"]
        )
        per_row["combined_objective_delta_contribution_vs_baseline"] = (
            per_row["combined_objective_contribution"] - per_row["baseline_combined_objective_contribution"]
        )

    source_records: list[dict[str, Any]] = []
    row_source_array = np.asarray(row_sources["source"])
    baseline_penalty = policy_penalties.get(baseline_policy or "")
    for label, penalty_np in policy_penalties.items():
        weighted_np = penalty_np * weights_np
        delta_np = penalty_np - baseline_penalty if baseline_penalty is not None else np.zeros_like(penalty_np)
        weighted_delta_np = delta_np * weights_np
        for source_name in row_sources["source"].drop_duplicates().tolist():
            mask = row_source_array == source_name
            source_weight_sum = float(weights_np[mask].sum())
            source_denominator = max(source_weight_sum, 1.0)
            source_records.append(
                {
                    "policy": label,
                    "source": source_name,
                    "rows": int(mask.sum()),
                    "source_weight_sum": source_weight_sum,
                    "source_denominator_clamped": source_denominator,
                    "combined_denominator": combined_denominator,
                    "penalty_mean": float(penalty_np[mask].mean()),
                    "weighted_penalty_sum": float(weighted_np[mask].sum()),
                    "combined_objective_component": float(weighted_np[mask].sum() / combined_denominator),
                    "within_source_weighted_loss": float(weighted_np[mask].sum() / source_denominator),
                    "penalty_delta_mean_vs_baseline": float(delta_np[mask].mean()),
                    "weighted_delta_sum_vs_baseline": float(weighted_delta_np[mask].sum()),
                    "combined_objective_delta_component_vs_baseline": float(
                        weighted_delta_np[mask].sum() / combined_denominator
                    ),
                    "within_source_weighted_delta_vs_baseline": float(
                        weighted_delta_np[mask].sum() / source_denominator
                    ),
                }
            )
    return per_row, pd.DataFrame(source_records)


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
    parser.add_argument(
        "--source-npz",
        action="append",
        type=parse_source_npz,
        default=[],
        help="Named source corpus for exact source-aware reports, formatted NAME=PATH.",
    )
    parser.add_argument(
        "--baseline-policy",
        default=None,
        help="Policy label used for source/per-row delta columns. Defaults to the first checkpoint policy.",
    )
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    if args.source_npz and not args.exact:
        parser.error("--source-npz requires --exact")

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
    per_row_csv = None
    source_summary_csv = None
    source_summary_records: list[dict[str, Any]] = []
    if args.source_npz:
        per_row, source_summary = evaluate_exact_source_reports(
            checkpoint_policies=args.checkpoint_policy,
            snippet_npz=args.snippet_npz,
            source_npzs=args.source_npz,
            device=args.device,
            logprob_margin=args.logprob_margin,
            baseline_policy=args.baseline_policy,
        )
        per_row_csv = run_dir / "per_row_losses.csv"
        source_summary_csv = run_dir / "source_summary.csv"
        per_row.to_csv(per_row_csv, index=False)
        source_summary.to_csv(source_summary_csv, index=False)
        source_summary_records = source_summary.to_dict(orient="records")
    write_json(
        run_dir / "summary.json",
        {
            "run_type": "outcome_intervention_eval",
            "snippet_npz": args.snippet_npz,
            "source_npz": {name: path for name, path in args.source_npz},
            "device": args.device,
            "mode": "exact" if args.exact else "sampled",
            "exact": bool(args.exact),
            "batch_size": args.batch_size,
            "batches": args.batches,
            "seed": args.seed,
            "logprob_margin": args.logprob_margin,
            "policy_summary_csv": summary_csv,
            "batch_losses_csv": batch_csv,
            "per_row_losses_csv": per_row_csv,
            "source_summary_csv": source_summary_csv,
            "baseline_policy": args.baseline_policy or (args.checkpoint_policy[0][0] if args.checkpoint_policy else None),
            "policies": summary.to_dict(orient="records"),
            "source_summary": source_summary_records,
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
