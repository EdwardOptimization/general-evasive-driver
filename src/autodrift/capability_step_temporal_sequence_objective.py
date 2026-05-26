"""Exact no-update evaluator for the temporal sequence objective."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.capability_step_temporal_sequence_corpus_export import (
    _replay_action_l2_max,
    _sequence_logp_sums,
    actor_checksum,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic, resolve_device


REQUIRED_ARRAYS = (
    "normal_rollout_observations",
    "normal_rollout_actions",
    "normal_initial_hidden",
    "variant_initial_hidden",
    "sequence_mask",
    "row_weight",
)


def sequence_lengths(mask: np.ndarray) -> np.ndarray:
    values = np.asarray(mask, dtype=bool).sum(axis=1).astype(np.float32)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("sequence mask must be a non-empty 2D array")
    if np.any(values <= 0):
        raise ValueError("all sequence rows must contain at least one valid step")
    return values


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    values_arr = np.asarray(values, dtype=np.float64)
    weights_arr = np.asarray(weights, dtype=np.float64)
    if values_arr.shape != weights_arr.shape:
        raise ValueError(f"value/weight shapes differ: {values_arr.shape} vs {weights_arr.shape}")
    if not np.isfinite(values_arr).all() or not np.isfinite(weights_arr).all():
        raise ValueError("weighted_mean received non-finite values")
    denominator = float(np.sum(weights_arr))
    if denominator <= 0.0:
        raise ValueError("weights must have positive sum")
    return float(np.sum(values_arr * weights_arr) / denominator)


def temporal_preference_loss(
    *,
    normal_logp: np.ndarray,
    variant_on_normal_logp: np.ndarray,
    lengths: np.ndarray,
    margin: float,
) -> np.ndarray:
    normal = np.asarray(normal_logp, dtype=np.float64)
    variant = np.asarray(variant_on_normal_logp, dtype=np.float64)
    seq_lengths = np.asarray(lengths, dtype=np.float64)
    if normal.shape != variant.shape or normal.shape != seq_lengths.shape:
        raise ValueError("normal_logp, variant_on_normal_logp, and lengths must have matching shapes")
    logits = (variant - normal) / seq_lengths + float(margin)
    return np.logaddexp(0.0, logits).astype(np.float32)


def load_corpus(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        missing = [name for name in REQUIRED_ARRAYS if name not in data.files]
        if missing:
            raise ValueError(f"{path} missing arrays {missing}")
        return {name: data[name] for name in data.files}


def _finite_quantile(values: np.ndarray, q: float) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("cannot compute quantile for non-finite values")
    return float(np.quantile(arr, q))


def evaluate_temporal_sequence_objective(
    *,
    model: ActorCritic,
    corpus: dict[str, np.ndarray],
    device: torch.device,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> dict[str, Any]:
    mask = np.asarray(corpus["sequence_mask"], dtype=bool)
    weights = np.asarray(corpus["row_weight"], dtype=np.float32)
    lengths = sequence_lengths(mask)
    if abs(float(weights.mean()) - 1.0) > 1e-5:
        raise ValueError(f"row_weight mean must be 1.0, got {float(weights.mean())}")
    normal_logp = _sequence_logp_sums(
        model=model,
        observations=np.asarray(corpus["normal_rollout_observations"], dtype=np.float32),
        actions=np.asarray(corpus["normal_rollout_actions"], dtype=np.float32),
        masks=mask,
        hiddens=np.asarray(corpus["normal_initial_hidden"], dtype=np.float32),
        device=device,
    )
    variant_on_normal_logp = _sequence_logp_sums(
        model=model,
        observations=np.asarray(corpus["normal_rollout_observations"], dtype=np.float32),
        actions=np.asarray(corpus["normal_rollout_actions"], dtype=np.float32),
        masks=mask,
        hiddens=np.asarray(corpus["variant_initial_hidden"], dtype=np.float32),
        device=device,
    )
    normal_action_replay_l2_max = _replay_action_l2_max(
        model=model,
        observations=np.asarray(corpus["normal_rollout_observations"], dtype=np.float32),
        actions=np.asarray(corpus["normal_rollout_actions"], dtype=np.float32),
        masks=mask,
        hiddens=np.asarray(corpus["normal_initial_hidden"], dtype=np.float32),
        device=device,
    )
    normal_nll_per_step = -normal_logp / lengths
    variant_nll_per_step = -variant_on_normal_logp / lengths
    logp_gap_per_step = (normal_logp - variant_on_normal_logp) / lengths
    pref_loss = temporal_preference_loss(
        normal_logp=normal_logp,
        variant_on_normal_logp=variant_on_normal_logp,
        lengths=lengths,
        margin=preference_margin,
    )
    base_logp_anchor = np.zeros_like(pref_loss, dtype=np.float32)
    weighted_normal_nll = weighted_mean(normal_nll_per_step, weights)
    weighted_pref_loss = weighted_mean(pref_loss, weights)
    weighted_anchor = weighted_mean(base_logp_anchor, weights)
    total_loss = weighted_normal_nll + float(lambda_pref) * weighted_pref_loss + float(lambda_anchor) * weighted_anchor
    finite_metrics = bool(
        np.isfinite(normal_logp).all()
        and np.isfinite(variant_on_normal_logp).all()
        and np.isfinite(pref_loss).all()
        and np.isfinite(normal_nll_per_step).all()
        and np.isfinite(logp_gap_per_step).all()
    )
    return {
        "row_count": int(mask.shape[0]),
        "sequence_length_mean": float(np.mean(lengths)),
        "sequence_length_min": float(np.min(lengths)),
        "sequence_length_max": float(np.max(lengths)),
        "row_weight_mean": float(np.mean(weights)),
        "normal_sequence_logp_sum_mean": float(np.mean(normal_logp)),
        "variant_on_normal_sequence_logp_sum_mean": float(np.mean(variant_on_normal_logp)),
        "normal_sequence_nll_mean": float(np.mean(normal_nll_per_step)),
        "variant_on_normal_sequence_nll_mean": float(np.mean(variant_nll_per_step)),
        "temporal_preference_loss_mean": float(np.mean(pref_loss)),
        "temporal_logp_gap_sum_mean": float(np.mean(normal_logp - variant_on_normal_logp)),
        "temporal_logp_gap_mean": float(np.mean(logp_gap_per_step)),
        "temporal_logp_gap_p10": _finite_quantile(logp_gap_per_step, 0.10),
        "temporal_logp_gap_p50": _finite_quantile(logp_gap_per_step, 0.50),
        "temporal_logp_gap_p90": _finite_quantile(logp_gap_per_step, 0.90),
        "weighted_normal_sequence_nll": weighted_normal_nll,
        "weighted_temporal_preference_loss": weighted_pref_loss,
        "weighted_logp_gap_mean": weighted_mean(logp_gap_per_step, weights),
        "weighted_base_logp_anchor": weighted_anchor,
        "weighted_total_loss": float(total_loss),
        "normal_action_replay_l2_max": float(normal_action_replay_l2_max),
        "finite_metrics": finite_metrics,
        "mask_sanity_passed": bool(np.all(lengths > 0)),
        "weight_sanity_passed": bool(abs(float(np.mean(weights)) - 1.0) <= 1e-5 and np.all(weights > 0.0)),
        "replay_sanity_passed": bool(normal_action_replay_l2_max <= 1e-5),
        "preference_margin": float(preference_margin),
        "lambda_pref": float(lambda_pref),
        "lambda_anchor": float(lambda_anchor),
    }


def run_temporal_sequence_objective_evaluator(
    *,
    checkpoint_path: Path,
    corpus_path: Path,
    metadata_path: Path,
    run_dir: Path,
    device: str,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = actor_checksum(model)
    corpus = load_corpus(corpus_path)
    metadata = pd.read_csv(metadata_path)
    metrics = evaluate_temporal_sequence_objective(
        model=model,
        corpus=corpus,
        device=resolved_device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    checksum_after = actor_checksum(model)
    actor_parameters_changed = bool(abs(checksum_after - checksum_before) > 1e-8)
    variant_counts = metadata["variant"].astype(str).value_counts().to_dict() if "variant" in metadata.columns else {}
    positive_count = int(metadata["positive_target"].astype(bool).sum()) if "positive_target" in metadata.columns else int(len(metadata))
    summary = {
        "run_type": "capability_step_temporal_sequence_objective_evaluator",
        "checkpoint": checkpoint_path,
        "corpus": corpus_path,
        "metadata": metadata_path,
        "positive_row_count": positive_count,
        "variant_counts": variant_counts,
        **metrics,
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
    }
    summary["exact_objective_sanity_passed"] = bool(
        summary["finite_metrics"]
        and summary["mask_sanity_passed"]
        and summary["weight_sanity_passed"]
        and summary["replay_sanity_passed"]
        and not actor_parameters_changed
    )
    summary["result_class"] = (
        "temporal_sequence_objective_evaluator_pass"
        if summary["exact_objective_sanity_passed"]
        else "temporal_sequence_objective_evaluator_failed_sanity"
    )
    write_json(run_dir / "summary.json", summary)
    if summary["result_class"] != "temporal_sequence_objective_evaluator_pass":
        raise RuntimeError(f"M1000 objective evaluator failed sanity: {summary}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the temporal sequence objective without updating actor parameters.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="temporal_sequence_objective_evaluator")
    summary = run_temporal_sequence_objective_evaluator(
        checkpoint_path=args.checkpoint,
        corpus_path=args.corpus,
        metadata_path=args.metadata,
        run_dir=run_dir,
        device=args.device,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
