"""Aggregate hidden-envelope probes across checkpoints and probe seeds."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import run_hidden_envelope_probe
from autodrift.input_observability_audit import TARGETS
from autodrift.train_ppo import resolve_device


@dataclass(frozen=True)
class CheckpointSpec:
    label: str
    path: Path


def parse_checkpoint_spec(value: str) -> CheckpointSpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("checkpoint spec must be LABEL=PATH")
    label, path_text = value.split("=", 1)
    label = label.strip()
    path_text = path_text.strip()
    if not label:
        raise argparse.ArgumentTypeError("checkpoint spec label cannot be empty")
    if not path_text:
        raise argparse.ArgumentTypeError("checkpoint spec path cannot be empty")
    return CheckpointSpec(label=label, path=Path(path_text))


def parse_seed_list(value: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("probe seeds must be comma-separated integers") from exc
    if not seeds:
        raise argparse.ArgumentTypeError("at least one probe seed is required")
    return seeds


def aggregate_hidden_lift_rows(
    rows: list[dict[str, Any]],
    *,
    min_lift_threshold: float,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_key.setdefault((str(row["checkpoint_label"]), str(row["target"])), []).append(row)

    aggregate_rows: list[dict[str, Any]] = []
    for (label, target), target_rows in sorted(by_key.items()):
        lifts = [float(row["response_hidden_minus_reset_test_r2"]) for row in target_rows]
        pass_count = sum(lift >= float(min_lift_threshold) for lift in lifts)
        aggregate_rows.append(
            {
                "checkpoint_label": label,
                "target": target,
                "probe_count": len(lifts),
                "lift_mean": sum(lifts) / len(lifts),
                "lift_min": min(lifts),
                "lift_max": max(lifts),
                "pass_count": pass_count,
                "pass_fraction": pass_count / len(lifts),
                "min_lift_threshold": float(min_lift_threshold),
            }
        )
    return aggregate_rows


def evaluate_aggregate_gates(
    aggregate_rows: list[dict[str, Any]],
    *,
    mean_lift_threshold: float,
    min_lift_threshold: float,
    pass_fraction_threshold: float,
) -> list[dict[str, Any]]:
    gate_rows: list[dict[str, Any]] = []
    for row in aggregate_rows:
        mean_pass = float(row["lift_mean"]) >= float(mean_lift_threshold)
        min_pass = float(row["lift_min"]) >= float(min_lift_threshold)
        fraction_pass = float(row["pass_fraction"]) >= float(pass_fraction_threshold)
        passed = bool(mean_pass and min_pass and fraction_pass)
        gate_rows.append(
            {
                **row,
                "mean_lift_threshold": float(mean_lift_threshold),
                "pass_fraction_threshold": float(pass_fraction_threshold),
                "mean_pass": mean_pass,
                "min_pass": min_pass,
                "fraction_pass": fraction_pass,
                "passed": passed,
            }
        )
    return gate_rows


def run_multiseed_hidden_envelope_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    probe_seeds: tuple[int, ...],
    episodes: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    ridge: float,
    train_fraction: float,
    device: str,
    mean_lift_threshold: float,
    min_lift_threshold: float,
    pass_fraction_threshold: float,
    run_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)

    probe_rows: list[dict[str, Any]] = []
    gain_rows: list[dict[str, Any]] = []
    for checkpoint_spec in checkpoint_specs:
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        for seed in probe_seeds:
            _, _, gains = run_hidden_envelope_probe(
                model=model,
                env_config=env_config,
                episodes=episodes,
                seed=seed,
                horizon_steps=horizon_steps,
                sample_stride=sample_stride,
                max_samples=max_samples,
                ridge=ridge,
                train_fraction=train_fraction,
                device=resolved_device,
            )
            for gain in gains:
                gain_rows.append(
                    {
                        "checkpoint_label": checkpoint_spec.label,
                        "checkpoint": checkpoint_spec.path,
                        "probe_seed": int(seed),
                        **gain,
                    }
                )
            for target in TARGETS:
                target_gain = next(gain for gain in gains if gain["target"] == target)
                probe_rows.append(
                    {
                        "checkpoint_label": checkpoint_spec.label,
                        "checkpoint": checkpoint_spec.path,
                        "probe_seed": int(seed),
                        "target": target,
                        "response_hidden_minus_reset_test_r2": target_gain[
                            "response_hidden_minus_reset_test_r2"
                        ],
                    }
                )

    aggregate_rows = aggregate_hidden_lift_rows(gain_rows, min_lift_threshold=min_lift_threshold)
    gate_rows = evaluate_aggregate_gates(
        aggregate_rows,
        mean_lift_threshold=mean_lift_threshold,
        min_lift_threshold=min_lift_threshold,
        pass_fraction_threshold=pass_fraction_threshold,
    )
    summary = {
        "run_type": "hidden_envelope_multiseed_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "probe_seeds": probe_seeds,
        "episodes": int(episodes),
        "horizon_steps": int(horizon_steps),
        "sample_stride": int(sample_stride),
        "max_samples": max_samples,
        "ridge": float(ridge),
        "train_fraction": float(train_fraction),
        "device": str(resolved_device),
        "mean_lift_threshold": float(mean_lift_threshold),
        "min_lift_threshold": float(min_lift_threshold),
        "pass_fraction_threshold": float(pass_fraction_threshold),
        "passed": all(bool(row["passed"]) for row in gate_rows),
    }
    write_csv_rows(run_dir / "probe_lifts.csv", probe_rows)
    write_csv_rows(run_dir / "hidden_gain_rows.csv", gain_rows)
    write_csv_rows(run_dir / "aggregate_summary.csv", aggregate_rows)
    write_csv_rows(run_dir / "gate_summary.csv", gate_rows)
    write_json(
        run_dir / "summary.json",
        {
            **summary,
            "probe_lifts_csv": run_dir / "probe_lifts.csv",
            "hidden_gain_rows_csv": run_dir / "hidden_gain_rows.csv",
            "aggregate_summary_csv": run_dir / "aggregate_summary.csv",
            "gate_summary_csv": run_dir / "gate_summary.csv",
        },
    )
    return gain_rows, aggregate_rows, gate_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a multi-seed hidden-envelope gate.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--probe-seeds", type=parse_seed_list, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--mean-lift-threshold", type=float, default=0.0)
    parser.add_argument("--min-lift-threshold", type=float, default=0.0)
    parser.add_argument("--pass-fraction-threshold", type=float, default=1.0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="hidden_envelope_multiseed_gate", seed=args.probe_seeds[0])
    _, aggregate_rows, gate_rows, summary = run_multiseed_hidden_envelope_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        probe_seeds=args.probe_seeds,
        episodes=args.episodes,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        ridge=args.ridge,
        train_fraction=args.train_fraction,
        device=args.device,
        mean_lift_threshold=args.mean_lift_threshold,
        min_lift_threshold=args.min_lift_threshold,
        pass_fraction_threshold=args.pass_fraction_threshold,
        run_dir=run_dir,
    )
    print("aggregate_summary")
    for row in aggregate_rows:
        print(row)
    print("gate_summary")
    for row in gate_rows:
        print(row)
    print(f"passed={summary['passed']}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
