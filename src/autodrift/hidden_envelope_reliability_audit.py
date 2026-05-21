"""Reliability audit for hidden-envelope supervised probes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec, parse_seed_list
from autodrift.hidden_envelope_probe import (
    CURRENT_RESPONSE,
    RESET_RESPONSE_HIDDEN,
    RESPONSE_HIDDEN,
    collect_hidden_envelope_dataset,
)
from autodrift.input_observability_audit import TARGETS, split_by_episode, train_ridge_regression_probe
from autodrift.train_ppo import resolve_device


FEATURE_SETS_FOR_RELIABILITY = (
    CURRENT_RESPONSE,
    RESPONSE_HIDDEN,
    RESET_RESPONSE_HIDDEN,
)


@dataclass(frozen=True)
class ReliabilityThresholds:
    mean_lift_threshold: float = 0.0
    min_lift_threshold: float = 0.0
    pass_fraction_threshold: float = 1.0


def parse_sample_limits(value: str) -> tuple[int, ...]:
    try:
        limits = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("sample limits must be comma-separated integers") from exc
    if not limits:
        raise argparse.ArgumentTypeError("at least one sample limit is required")
    if any(limit < 2 for limit in limits):
        raise argparse.ArgumentTypeError("sample limits must be at least 2")
    return tuple(sorted(set(limits)))


def target_distribution_rows(
    *,
    checkpoint_label: str,
    sample_limit: int,
    probe_seed: int,
    targets: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, values in targets.items():
        finite = np.asarray(values, dtype=np.float64)
        finite = finite[np.isfinite(finite)]
        if finite.size == 0:
            rows.append(
                {
                    "checkpoint_label": checkpoint_label,
                    "sample_limit": int(sample_limit),
                    "probe_seed": int(probe_seed),
                    "target": target,
                    "samples": 0,
                    "mean": float("nan"),
                    "std": float("nan"),
                    "min": float("nan"),
                    "p10": float("nan"),
                    "p50": float("nan"),
                    "p90": float("nan"),
                    "max": float("nan"),
                }
            )
            continue
        rows.append(
            {
                "checkpoint_label": checkpoint_label,
                "sample_limit": int(sample_limit),
                "probe_seed": int(probe_seed),
                "target": target,
                "samples": int(finite.size),
                "mean": float(np.mean(finite)),
                "std": float(np.std(finite)),
                "min": float(np.min(finite)),
                "p10": float(np.percentile(finite, 10)),
                "p50": float(np.percentile(finite, 50)),
                "p90": float(np.percentile(finite, 90)),
                "max": float(np.max(finite)),
            }
        )
    return rows


def summarize_target_shift(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_key.setdefault((str(row["checkpoint_label"]), int(row["sample_limit"]), str(row["target"])), []).append(row)
    summary: list[dict[str, Any]] = []
    for (label, sample_limit, target), group in sorted(by_key.items()):
        means = np.asarray([float(row["mean"]) for row in group], dtype=np.float64)
        stds = np.asarray([float(row["std"]) for row in group], dtype=np.float64)
        summary.append(
            {
                "checkpoint_label": label,
                "sample_limit": int(sample_limit),
                "target": target,
                "probe_seed_count": len(group),
                "target_mean_mean": float(np.mean(means)),
                "target_mean_std": float(np.std(means)),
                "target_mean_min": float(np.min(means)),
                "target_mean_max": float(np.max(means)),
                "target_mean_range": float(np.max(means) - np.min(means)),
                "target_std_mean": float(np.mean(stds)),
            }
        )
    return summary


def split_probe_rows(
    *,
    checkpoint_label: str,
    sample_limit: int,
    probe_seed: int,
    split_seeds: tuple[int, ...],
    features: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
    rows: list[dict[str, Any]],
    ridge: float,
    train_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    probe_rows: list[dict[str, Any]] = []
    lift_rows: list[dict[str, Any]] = []
    for split_seed in split_seeds:
        train_mask = split_by_episode(rows, train_fraction=train_fraction, seed=split_seed)
        split_results: dict[tuple[str, str], Any] = {}
        for target_name, target_values in targets.items():
            for feature_set in FEATURE_SETS_FOR_RELIABILITY:
                result = train_ridge_regression_probe(
                    features=features[feature_set],
                    targets=target_values,
                    train_mask=train_mask,
                    target_name=target_name,
                    feature_set=feature_set,
                    ridge=ridge,
                )
                row = {
                    "checkpoint_label": checkpoint_label,
                    "sample_limit": int(sample_limit),
                    "probe_seed": int(probe_seed),
                    "split_seed": int(split_seed),
                    **result.__dict__,
                }
                probe_rows.append(row)
                split_results[(target_name, feature_set)] = result
        for target_name in TARGETS:
            response = split_results[(target_name, RESPONSE_HIDDEN)]
            reset = split_results[(target_name, RESET_RESPONSE_HIDDEN)]
            current = split_results[(target_name, CURRENT_RESPONSE)]
            lift_rows.append(
                {
                    "checkpoint_label": checkpoint_label,
                    "sample_limit": int(sample_limit),
                    "probe_seed": int(probe_seed),
                    "split_seed": int(split_seed),
                    "target": target_name,
                    "response_hidden_test_r2": response.test_r2,
                    "reset_response_hidden_test_r2": reset.test_r2,
                    "current_response_test_r2": current.test_r2,
                    "response_hidden_minus_reset_test_r2": response.test_r2 - reset.test_r2,
                    "response_hidden_minus_current_response_test_r2": response.test_r2 - current.test_r2,
                    "response_hidden_mae_improvement": response.mae_improvement,
                    "reset_response_hidden_mae_improvement": reset.mae_improvement,
                    "response_hidden_minus_reset_mae_improvement": response.mae_improvement
                    - reset.mae_improvement,
                    "train_samples": response.train_samples,
                    "test_samples": response.test_samples,
                    "status": (
                        "ok"
                        if response.status == "ok" and reset.status == "ok" and current.status == "ok"
                        else "skipped"
                    ),
                }
            )
    return probe_rows, lift_rows


def aggregate_lift_rows(
    lift_rows: list[dict[str, Any]],
    thresholds: ReliabilityThresholds,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for row in lift_rows:
        by_key.setdefault((str(row["checkpoint_label"]), int(row["sample_limit"]), str(row["target"])), []).append(row)
    summary: list[dict[str, Any]] = []
    for (label, sample_limit, target), group in sorted(by_key.items()):
        lifts = np.asarray([float(row["response_hidden_minus_reset_test_r2"]) for row in group], dtype=np.float64)
        pass_mask = lifts >= float(thresholds.min_lift_threshold)
        lift_mean = float(np.mean(lifts))
        lift_min = float(np.min(lifts))
        pass_fraction = float(np.mean(pass_mask))
        mean_pass = lift_mean >= float(thresholds.mean_lift_threshold)
        min_pass = lift_min >= float(thresholds.min_lift_threshold)
        fraction_pass = pass_fraction >= float(thresholds.pass_fraction_threshold)
        summary.append(
            {
                "checkpoint_label": label,
                "sample_limit": int(sample_limit),
                "target": target,
                "lift_count": int(lifts.size),
                "lift_mean": lift_mean,
                "lift_std": float(np.std(lifts)),
                "lift_min": lift_min,
                "lift_p10": float(np.percentile(lifts, 10)),
                "lift_p50": float(np.percentile(lifts, 50)),
                "lift_p90": float(np.percentile(lifts, 90)),
                "lift_max": float(np.max(lifts)),
                "pass_count": int(np.sum(pass_mask)),
                "pass_fraction": pass_fraction,
                "mean_lift_threshold": float(thresholds.mean_lift_threshold),
                "min_lift_threshold": float(thresholds.min_lift_threshold),
                "pass_fraction_threshold": float(thresholds.pass_fraction_threshold),
                "mean_pass": bool(mean_pass),
                "min_pass": bool(min_pass),
                "fraction_pass": bool(fraction_pass),
                "passed": bool(mean_pass and min_pass and fraction_pass),
            }
        )
    return summary


def run_hidden_envelope_reliability_audit(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    probe_seeds: tuple[int, ...],
    split_seeds: tuple[int, ...],
    sample_limits: tuple[int, ...],
    episodes: int,
    horizon_steps: int,
    sample_stride: int,
    ridge: float,
    train_fraction: float,
    device: str,
    thresholds: ReliabilityThresholds,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    target_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    lift_rows: list[dict[str, Any]] = []

    for checkpoint_spec in checkpoint_specs:
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        for sample_limit in sample_limits:
            for probe_seed in probe_seeds:
                dataset = collect_hidden_envelope_dataset(
                    model=model,
                    env_config=env_config,
                    episodes=episodes,
                    seed=probe_seed,
                    horizon_steps=horizon_steps,
                    sample_stride=sample_stride,
                    max_samples=sample_limit,
                    device=resolved_device,
                )
                target_rows.extend(
                    target_distribution_rows(
                        checkpoint_label=checkpoint_spec.label,
                        sample_limit=sample_limit,
                        probe_seed=probe_seed,
                        targets=dataset.targets,
                    )
                )
                split_rows, split_lifts = split_probe_rows(
                    checkpoint_label=checkpoint_spec.label,
                    sample_limit=sample_limit,
                    probe_seed=probe_seed,
                    split_seeds=split_seeds,
                    features=dataset.features,
                    targets=dataset.targets,
                    rows=dataset.rows,
                    ridge=ridge,
                    train_fraction=train_fraction,
                )
                probe_rows.extend(split_rows)
                lift_rows.extend(split_lifts)

    target_shift_rows = summarize_target_shift(target_rows)
    aggregate_rows = aggregate_lift_rows(lift_rows, thresholds)
    passed = all(bool(row["passed"]) for row in aggregate_rows)

    write_csv_rows(run_dir / "target_distribution.csv", target_rows)
    write_csv_rows(run_dir / "target_shift_summary.csv", target_shift_rows)
    write_csv_rows(run_dir / "split_probe_metrics.csv", probe_rows)
    write_csv_rows(run_dir / "split_lifts.csv", lift_rows)
    write_csv_rows(run_dir / "aggregate_lift_summary.csv", aggregate_rows)
    summary = {
        "run_type": "hidden_envelope_reliability_audit",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "probe_seeds": probe_seeds,
        "split_seeds": split_seeds,
        "sample_limits": sample_limits,
        "episodes": int(episodes),
        "horizon_steps": int(horizon_steps),
        "sample_stride": int(sample_stride),
        "ridge": float(ridge),
        "train_fraction": float(train_fraction),
        "device": str(resolved_device),
        "thresholds": thresholds,
        "passed": bool(passed),
        "target_distribution_csv": run_dir / "target_distribution.csv",
        "target_shift_summary_csv": run_dir / "target_shift_summary.csv",
        "split_probe_metrics_csv": run_dir / "split_probe_metrics.csv",
        "split_lifts_csv": run_dir / "split_lifts.csv",
        "aggregate_lift_summary_csv": run_dir / "aggregate_lift_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit hidden-envelope probe reliability.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--probe-seeds", type=parse_seed_list, required=True)
    parser.add_argument("--split-seeds", type=parse_seed_list, required=True)
    parser.add_argument("--sample-limits", type=parse_sample_limits, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--mean-lift-threshold", type=float, default=0.0)
    parser.add_argument("--min-lift-threshold", type=float, default=0.0)
    parser.add_argument("--pass-fraction-threshold", type=float, default=1.0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="hidden_envelope_reliability_audit", seed=args.probe_seeds[0])
    summary = run_hidden_envelope_reliability_audit(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        probe_seeds=args.probe_seeds,
        split_seeds=args.split_seeds,
        sample_limits=args.sample_limits,
        episodes=args.episodes,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        ridge=args.ridge,
        train_fraction=args.train_fraction,
        device=args.device,
        thresholds=ReliabilityThresholds(
            mean_lift_threshold=args.mean_lift_threshold,
            min_lift_threshold=args.min_lift_threshold,
            pass_fraction_threshold=args.pass_fraction_threshold,
        ),
        run_dir=run_dir,
    )
    print(f"passed={summary['passed']}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
