"""Export matched nominal/perturbed hidden-state snapshots."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import DecisionSnapshot, build_pair_row, collect_decision_snapshot
from autodrift.paired_perturbation_gate import (
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)
from autodrift.train_ppo import ActorCritic


@dataclass(frozen=True)
class SnapshotPairRecord:
    seed: int
    pair_row: dict[str, Any]
    nominal: DecisionSnapshot
    perturbed: DecisionSnapshot


def _hidden_numpy(hidden: torch.Tensor | None, hidden_dim: int) -> np.ndarray:
    if hidden is None:
        return np.full(hidden_dim, np.nan, dtype=np.float32)
    hidden_array = hidden.detach().cpu().numpy().astype(np.float32).reshape(-1)
    if len(hidden_array) == hidden_dim:
        return hidden_array
    output = np.full(hidden_dim, np.nan, dtype=np.float32)
    output[: min(hidden_dim, len(hidden_array))] = hidden_array[:hidden_dim]
    return output


def _hidden_dim(records: list[SnapshotPairRecord]) -> int:
    dims: list[int] = []
    for record in records:
        for snapshot in (record.nominal, record.perturbed):
            if snapshot.hidden is not None:
                dims.append(int(np.prod(snapshot.hidden.shape)))
    return max(dims, default=0)


def build_snapshot_arrays(
    records: list[SnapshotPairRecord],
    *,
    accepted_only: bool = True,
) -> dict[str, np.ndarray]:
    selected = [
        record
        for record in records
        if not accepted_only or bool(record.pair_row.get("accepted_match", False))
    ]
    if not selected:
        return {
            "seed": np.empty((0,), dtype=np.int64),
            "accepted_match": np.empty((0,), dtype=bool),
            "nominal_step": np.empty((0,), dtype=np.int64),
            "perturbed_step": np.empty((0,), dtype=np.int64),
            "observation_distance": np.empty((0,), dtype=np.float32),
            "response_observation_distance": np.empty((0,), dtype=np.float32),
            "context_observation_distance": np.empty((0,), dtype=np.float32),
            "hidden_state_distance": np.empty((0,), dtype=np.float32),
            "nominal_observation": np.empty((0, 0), dtype=np.float32),
            "perturbed_observation": np.empty((0, 0), dtype=np.float32),
            "nominal_hidden": np.empty((0, 0), dtype=np.float32),
            "perturbed_hidden": np.empty((0, 0), dtype=np.float32),
        }

    hidden_dim = _hidden_dim(selected)
    return {
        "seed": np.asarray([record.seed for record in selected], dtype=np.int64),
        "accepted_match": np.asarray(
            [bool(record.pair_row.get("accepted_match", False)) for record in selected],
            dtype=bool,
        ),
        "nominal_step": np.asarray([record.nominal.step for record in selected], dtype=np.int64),
        "perturbed_step": np.asarray([record.perturbed.step for record in selected], dtype=np.int64),
        "observation_distance": np.asarray(
            [record.pair_row.get("observation_distance", np.nan) for record in selected],
            dtype=np.float32,
        ),
        "response_observation_distance": np.asarray(
            [record.pair_row.get("response_observation_distance", np.nan) for record in selected],
            dtype=np.float32,
        ),
        "context_observation_distance": np.asarray(
            [record.pair_row.get("context_observation_distance", np.nan) for record in selected],
            dtype=np.float32,
        ),
        "hidden_state_distance": np.asarray(
            [record.pair_row.get("hidden_state_distance", np.nan) for record in selected],
            dtype=np.float32,
        ),
        "nominal_observation": np.stack(
            [np.asarray(record.nominal.observation, dtype=np.float32) for record in selected],
        ),
        "perturbed_observation": np.stack(
            [np.asarray(record.perturbed.observation, dtype=np.float32) for record in selected],
        ),
        "nominal_hidden": np.stack(
            [_hidden_numpy(record.nominal.hidden, hidden_dim) for record in selected],
        ),
        "perturbed_hidden": np.stack(
            [_hidden_numpy(record.perturbed.hidden, hidden_dim) for record in selected],
        ),
    }


def collect_snapshot_pair_records(
    *,
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    nominal_friction_mu_range: tuple[float, float],
    perturbed_friction_mu_range: tuple[float, float],
    nominal_randomization: dict[str, tuple[float, float]],
    perturbed_randomization: dict[str, tuple[float, float]],
    target_obstacle_distance: float,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_observation_distance: float,
) -> tuple[pd.DataFrame, list[SnapshotPairRecord]]:
    configs = {
        "nominal": condition_config(base_config, nominal_friction_mu_range, nominal_randomization),
        "perturbed": condition_config(base_config, perturbed_friction_mu_range, perturbed_randomization),
    }
    pair_rows: list[dict[str, Any]] = []
    records: list[SnapshotPairRecord] = []
    for seed in seeds:
        snapshots = {
            condition: collect_decision_snapshot(
                model,
                env_config,
                condition,
                seed,
                target_obstacle_distance=target_obstacle_distance,
                min_probe_steps=min_probe_steps,
                max_probe_steps=max_probe_steps,
                require_friction_step=require_friction_step,
                min_hidden_updates_after_friction=min_hidden_updates_after_friction,
            )
            for condition, env_config in configs.items()
        }
        pair_row = build_pair_row(
            seed,
            snapshots["nominal"],
            snapshots["perturbed"],
            configs["nominal"],
            max_observation_distance,
        )
        pair_rows.append(pair_row)
        if snapshots["nominal"] is None or snapshots["perturbed"] is None:
            continue
        records.append(
            SnapshotPairRecord(
                seed=seed,
                pair_row=pair_row,
                nominal=snapshots["nominal"],
                perturbed=snapshots["perturbed"],
            )
        )
    return pd.DataFrame(pair_rows), records


def summarize_snapshot_export(
    pair_frame: pd.DataFrame,
    arrays: dict[str, np.ndarray],
) -> dict[str, float | int]:
    total = int(len(pair_frame))
    paired = int((pair_frame.get("pair_status") == "paired").sum()) if total else 0
    accepted = int(pair_frame.get("accepted_match", pd.Series(dtype=bool)).astype(bool).sum()) if total else 0
    exported = int(len(arrays["seed"]))
    return {
        "seeds": total,
        "paired": paired,
        "accepted_matches": accepted,
        "exported_pairs": exported,
        "accepted_rate": float(accepted / total) if total else 0.0,
        "mean_observation_distance": float(pair_frame["observation_distance"].mean()) if paired else float("nan"),
        "mean_context_observation_distance": (
            float(pair_frame["context_observation_distance"].mean()) if paired else float("nan")
        ),
        "mean_hidden_state_distance": float(pair_frame["hidden_state_distance"].mean()) if paired else float("nan"),
        "exported_mean_observation_distance": (
            float(np.mean(arrays["observation_distance"])) if exported else float("nan")
        ),
        "exported_mean_context_observation_distance": (
            float(np.mean(arrays["context_observation_distance"])) if exported else float("nan")
        ),
        "exported_mean_hidden_state_distance": (
            float(np.mean(arrays["hidden_state_distance"])) if exported else float("nan")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export paired hidden-state snapshots.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=4200)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--nominal-randomization", action="append", default=[])
    parser.add_argument("--perturbed-randomization", action="append", default=[])
    parser.add_argument("--target-obstacle-distance", type=float, default=12.0)
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-observation-distance", type=float, default=0.75)
    parser.add_argument("--include-unaccepted", action="store_true")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="paired_hidden_snapshots", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    target_obs_dim = int(AutoDriftEnv(base_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("paired hidden snapshot export requires an online recurrent checkpoint")

    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    pair_frame, records = collect_snapshot_pair_records(
        model=model,
        base_config=base_config,
        seeds=seeds,
        nominal_friction_mu_range=args.nominal_friction_mu_range,
        perturbed_friction_mu_range=args.perturbed_friction_mu_range,
        nominal_randomization=parse_randomization_overrides(args.nominal_randomization),
        perturbed_randomization=parse_randomization_overrides(args.perturbed_randomization),
        target_obstacle_distance=args.target_obstacle_distance,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_observation_distance=args.max_observation_distance,
    )
    arrays = build_snapshot_arrays(records, accepted_only=not args.include_unaccepted)
    summary = summarize_snapshot_export(pair_frame, arrays)

    pairs_csv = run_dir / "pairs.csv"
    snapshots_npz = run_dir / "snapshots.npz"
    summary_json = run_dir / "summary.json"
    pair_frame.to_csv(pairs_csv, index=False)
    np.savez_compressed(snapshots_npz, **arrays)
    write_json(summary_json, summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "paired_hidden_snapshots",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "accepted_only": not args.include_unaccepted,
            "pairs_csv": pairs_csv,
            "snapshots_npz": snapshots_npz,
            "summary_json": summary_json,
        },
    )
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
