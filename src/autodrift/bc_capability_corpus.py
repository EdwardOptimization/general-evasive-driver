"""Closed-loop capability corpus exporter for BC hidden repair."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.input_observability_audit import TARGETS, future_envelope_targets
from autodrift.l2_teacher_corpus import parse_seed_list
from autodrift.matched_current_response_ambiguity import (
    MATCH_CURRENT_RESPONSE_CONTEXT,
    build_match_features,
    nearest_visible_candidate_pairs,
    select_ambiguity_pairs,
    visible_distance_threshold,
)
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, ActorCritic, resolve_device


CAPABILITY_CORPUS_ARRAYS = (
    "student_obs_seq",
    "anchor_action_seq",
    "capability_target_seq",
    "done_seq",
    "episode_start_seq",
    "seed_seq",
    "episode_id_seq",
    "step_seq",
    "base_hidden_seq",
    "base_next_hidden_seq",
)


def validate_capability_corpus_arrays(arrays: dict[str, np.ndarray]) -> None:
    missing = [name for name in CAPABILITY_CORPUS_ARRAYS if name not in arrays]
    if missing:
        raise ValueError(f"missing capability corpus arrays: {missing}")
    row_count = int(arrays["student_obs_seq"].shape[0])
    if row_count <= 0:
        raise ValueError("capability corpus must contain at least one row")
    if arrays["student_obs_seq"].ndim != 2 or arrays["student_obs_seq"].shape[1] != HUMAN_VIEW_OBS_DIM:
        raise ValueError(f"student_obs_seq must have shape (N, {HUMAN_VIEW_OBS_DIM})")
    if arrays["anchor_action_seq"].shape != (row_count, 3):
        raise ValueError("anchor_action_seq must have shape (N, 3)")
    if arrays["capability_target_seq"].shape != (row_count, len(TARGETS)):
        raise ValueError(f"capability_target_seq must have shape (N, {len(TARGETS)})")
    for name in ("done_seq", "episode_start_seq", "seed_seq", "episode_id_seq", "step_seq"):
        if arrays[name].shape != (row_count,):
            raise ValueError(f"{name} must have shape (N,)")
    if arrays["base_hidden_seq"].ndim != 2 or arrays["base_hidden_seq"].shape[0] != row_count:
        raise ValueError("base_hidden_seq must have shape (N, H)")
    if arrays["base_next_hidden_seq"].shape != arrays["base_hidden_seq"].shape:
        raise ValueError("base_next_hidden_seq must match base_hidden_seq shape")
    if not np.isfinite(arrays["capability_target_seq"]).all():
        raise ValueError("capability_target_seq contains non-finite values")


def _target_summary_rows(targets: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, target in enumerate(TARGETS):
        values = targets[:, index].astype(np.float64)
        rows.append(
            {
                "target": str(target),
                "count": int(values.size),
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
        )
    return rows


def capability_pair_rows(
    *,
    student_obs_seq: np.ndarray,
    capability_target_seq: np.ndarray,
    seed_seq: np.ndarray,
    episode_id_seq: np.ndarray,
    step_seq: np.ndarray,
    response_dim: int,
    nearest_k: int,
    min_target_z_delta: float,
    max_pairs_per_target: int,
    max_visible_quantile: float,
    exclude_same_episode: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    row_count = int(student_obs_seq.shape[0])
    rows = [
        {
            "episode": int(episode_id_seq[index]),
            "seed": int(seed_seq[index]),
            "step": int(step_seq[index]),
        }
        for index in range(row_count)
    ]
    targets = {
        target: capability_target_seq[:, target_index].astype(np.float32)
        for target_index, target in enumerate(TARGETS)
    }
    current_response = student_obs_seq[:, :response_dim].astype(np.float32)
    match_features = build_match_features(
        student_obs_seq.astype(np.float32),
        current_response,
        response_dim=response_dim,
        match_feature_set=MATCH_CURRENT_RESPONSE_CONTEXT,
    )
    candidates = nearest_visible_candidate_pairs(
        rows=rows,
        match_features=match_features,
        targets=targets,
        nearest_k=nearest_k,
        exclude_same_episode=exclude_same_episode,
    )
    threshold = visible_distance_threshold(
        candidates,
        max_visible_distance=None,
        max_visible_quantile=max_visible_quantile,
    )
    accepted = select_ambiguity_pairs(
        candidates,
        visible_threshold=threshold,
        min_target_z_delta=min_target_z_delta,
        max_pairs_per_target=max_pairs_per_target,
    )
    pair_rows: list[dict[str, Any]] = []
    for row in accepted:
        next_row = dict(row)
        next_row["left_row"] = int(row["left_index"])
        next_row["right_row"] = int(row["right_index"])
        pair_rows.append(next_row)
    pair_summary_rows = []
    for target in TARGETS:
        target_rows = [row for row in pair_rows if str(row["target"]) == target]
        target_z = [float(row["target_z_delta"]) for row in target_rows]
        pair_summary_rows.append(
            {
                "target": str(target),
                "pair_count": int(len(target_rows)),
                "target_z_delta_mean": float(np.mean(target_z)) if target_z else float("nan"),
                "target_z_delta_max": float(np.max(target_z)) if target_z else float("nan"),
                "visible_threshold": float(threshold),
                "min_target_z_delta": float(min_target_z_delta),
            }
        )
    return pair_rows, pair_summary_rows, float(threshold)


def collect_bc_capability_rows(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    seeds: Iterable[int],
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    device: torch.device,
) -> dict[str, np.ndarray]:
    if not model.is_online_recurrent:
        raise ValueError("BC capability corpus requires an online recurrent checkpoint")
    if sample_stride < 1:
        raise ValueError("sample_stride must be at least one")
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be at least one")

    env = AutoDriftEnv(env_config)
    student_obs_rows: list[np.ndarray] = []
    anchor_action_rows: list[np.ndarray] = []
    target_rows: list[np.ndarray] = []
    done_rows: list[bool] = []
    episode_start_rows: list[bool] = []
    seed_rows: list[int] = []
    episode_id_rows: list[int] = []
    step_rows: list[int] = []
    hidden_rows: list[np.ndarray] = []
    next_hidden_rows: list[np.ndarray] = []

    try:
        for episode_id, seed in enumerate(int(seed) for seed in seeds):
            obs, _ = env.reset(seed=seed)
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                step = int(env.step_count)
                observation = np.asarray(obs, dtype=np.float32)
                if observation.shape != (HUMAN_VIEW_OBS_DIM,):
                    raise ValueError(f"expected P0 observation shape {(HUMAN_VIEW_OBS_DIM,)}, got {observation.shape}")
                action, next_hidden = deterministic_action_from_hidden(model, observation, hidden, device)
                target_values = future_envelope_targets(env, horizon_steps=horizon_steps)
                should_sample = step % int(sample_stride) == 0
                next_obs, _, terminated, truncated, _ = env.step(action)
                if should_sample:
                    student_obs_rows.append(observation.copy())
                    anchor_action_rows.append(action.astype(np.float32, copy=False))
                    target_rows.append(np.asarray([target_values[name] for name in TARGETS], dtype=np.float32))
                    done_rows.append(bool(terminated or truncated))
                    episode_start_rows.append(step == 0)
                    seed_rows.append(seed)
                    episode_id_rows.append(int(episode_id))
                    step_rows.append(step)
                    hidden_rows.append(hidden.squeeze(0).detach().cpu().numpy().astype(np.float32))
                    next_hidden_rows.append(next_hidden.squeeze(0).detach().cpu().numpy().astype(np.float32))
                    if max_samples is not None and len(student_obs_rows) >= int(max_samples):
                        break
                obs = next_obs
                hidden = next_hidden
            if max_samples is not None and len(student_obs_rows) >= int(max_samples):
                break
    finally:
        env.close()

    if not student_obs_rows:
        raise ValueError("capability corpus collection produced no rows")

    arrays = {
        "student_obs_seq": np.stack(student_obs_rows).astype(np.float32),
        "anchor_action_seq": np.stack(anchor_action_rows).astype(np.float32),
        "capability_target_seq": np.stack(target_rows).astype(np.float32),
        "done_seq": np.asarray(done_rows, dtype=np.bool_),
        "episode_start_seq": np.asarray(episode_start_rows, dtype=np.bool_),
        "seed_seq": np.asarray(seed_rows, dtype=np.int64),
        "episode_id_seq": np.asarray(episode_id_rows, dtype=np.int64),
        "step_seq": np.asarray(step_rows, dtype=np.int64),
        "base_hidden_seq": np.stack(hidden_rows).astype(np.float32),
        "base_next_hidden_seq": np.stack(next_hidden_rows).astype(np.float32),
    }
    validate_capability_corpus_arrays(arrays)
    return arrays


def export_bc_capability_corpus(
    *,
    base_checkpoint: Path | str,
    env_config_path: Path | str,
    seeds: Iterable[int],
    output_npz: Path | str,
    pairs_csv: Path | str,
    target_summary_csv: Path | str,
    pair_summary_csv: Path | str,
    summary_json: Path | str,
    horizon_steps: int = 8,
    sample_stride: int = 2,
    max_samples: int | None = None,
    nearest_k: int = 16,
    min_target_z_delta: float = 1.0,
    max_pairs_per_target: int = 200,
    max_visible_quantile: float = 0.2,
    device: str = "auto",
) -> dict[str, Any]:
    seed_list = [int(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("at least one seed is required")
    resolved_device = resolve_device(device)
    env_config = load_env_config(Path(env_config_path))
    model, checkpoint = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    arrays = collect_bc_capability_rows(
        model=model,
        env_config=env_config,
        seeds=seed_list,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        device=resolved_device,
    )
    pair_rows, pair_summary_rows, visible_threshold = capability_pair_rows(
        student_obs_seq=arrays["student_obs_seq"],
        capability_target_seq=arrays["capability_target_seq"],
        seed_seq=arrays["seed_seq"],
        episode_id_seq=arrays["episode_id_seq"],
        step_seq=arrays["step_seq"],
        response_dim=response_dim,
        nearest_k=nearest_k,
        min_target_z_delta=min_target_z_delta,
        max_pairs_per_target=max_pairs_per_target,
        max_visible_quantile=max_visible_quantile,
    )

    output_npz_path = Path(output_npz)
    output_npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_npz_path, **arrays)
    write_csv_rows(Path(pairs_csv), pair_rows)
    write_csv_rows(Path(target_summary_csv), _target_summary_rows(arrays["capability_target_seq"]))
    write_csv_rows(Path(pair_summary_csv), pair_summary_rows)
    summary = {
        "run_type": "bc_capability_corpus_export",
        "base_checkpoint": str(base_checkpoint),
        "env_config": str(env_config_path),
        "checkpoint_actor_encoder": checkpoint.get("config", {}).get("actor_encoder", ""),
        "checkpoint_metadata": checkpoint.get("metadata", {}),
        "seeds": seed_list,
        "row_count": int(arrays["student_obs_seq"].shape[0]),
        "student_obs_dim": int(arrays["student_obs_seq"].shape[1]),
        "action_dim": int(arrays["anchor_action_seq"].shape[1]),
        "target_dim": int(arrays["capability_target_seq"].shape[1]),
        "hidden_dim": int(arrays["base_hidden_seq"].shape[1]),
        "targets": list(TARGETS),
        "horizon_steps": int(horizon_steps),
        "sample_stride": int(sample_stride),
        "max_samples": None if max_samples is None else int(max_samples),
        "nearest_k": int(nearest_k),
        "min_target_z_delta": float(min_target_z_delta),
        "max_pairs_per_target": int(max_pairs_per_target),
        "max_visible_quantile": float(max_visible_quantile),
        "visible_threshold": float(visible_threshold),
        "pair_count": int(len(pair_rows)),
        "labels_enter_actor_input": False,
        "contains_privileged_actor_inputs": False,
        "output_npz": output_npz_path,
        "pairs_csv": Path(pairs_csv),
        "target_summary_csv": Path(target_summary_csv),
        "pair_summary_csv": Path(pair_summary_csv),
    }
    write_json(Path(summary_json), summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a closed-loop BC capability repair corpus.")
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--seeds", type=str, default=None)
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--horizon-steps", type=int, default=8)
    parser.add_argument("--sample-stride", type=int, default=2)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--nearest-k", type=int, default=16)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--max-pairs-per-target", type=int, default=200)
    parser.add_argument("--max-visible-quantile", type=float, default=0.2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_capability_corpus")
    run_dir.mkdir(parents=True, exist_ok=True)
    seeds = parse_seed_list(args.seeds, seed_start=args.seed_start, episodes=args.episodes)
    summary = export_bc_capability_corpus(
        base_checkpoint=args.base_checkpoint,
        env_config_path=args.env_config,
        seeds=seeds,
        output_npz=run_dir / "capability_corpus.npz",
        pairs_csv=run_dir / "pairs.csv",
        target_summary_csv=run_dir / "target_summary.csv",
        pair_summary_csv=run_dir / "pair_summary.csv",
        summary_json=run_dir / "summary.json",
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        nearest_k=args.nearest_k,
        min_target_z_delta=args.min_target_z_delta,
        max_pairs_per_target=args.max_pairs_per_target,
        max_visible_quantile=args.max_visible_quantile,
        device=args.device,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
