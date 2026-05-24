"""Frozen source-surface evaluation for matched history baselines."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM, resolve_device


@dataclass(frozen=True)
class BaselineCheckpointSpec:
    label: str
    history_level: str
    path: Path


@dataclass
class FrozenSourceSnapshot:
    seed: int
    step: int
    observation: np.ndarray
    base_history: tuple[np.ndarray, ...]
    prefix_observations: tuple[np.ndarray, ...]
    env: AutoDriftEnv
    info: dict[str, Any]


def parse_baseline_checkpoint_spec(value: str) -> BaselineCheckpointSpec:
    if "=" not in value or ":" not in value:
        raise argparse.ArgumentTypeError("baseline checkpoint must be label=history_level:path")
    label, rest = value.split("=", 1)
    history_level, path_text = rest.split(":", 1)
    label = label.strip()
    history_level = history_level.strip()
    path_text = path_text.strip()
    if not label or not history_level or not path_text:
        raise argparse.ArgumentTypeError("baseline checkpoint must have non-empty label, history_level, and path")
    return BaselineCheckpointSpec(label=label, history_level=history_level, path=Path(path_text))


def parse_tail_offsets(value: str) -> tuple[int, ...]:
    offsets = tuple(int(part.strip()) for part in str(value).split(",") if part.strip())
    if not offsets:
        raise argparse.ArgumentTypeError("at least one tail offset is required")
    if any(offset < 0 for offset in offsets):
        raise argparse.ArgumentTypeError("tail offsets must be non-negative")
    return tuple(dict.fromkeys(offsets))


def validate_checkpoint_metadata(checkpoint: dict[str, Any], spec: BaselineCheckpointSpec) -> dict[str, Any]:
    config_level = str(checkpoint.get("config", {}).get("history_baseline_level", ""))
    metadata = checkpoint.get("metadata", {}) if isinstance(checkpoint.get("metadata", {}), dict) else {}
    history_metadata = metadata.get("history_baseline", {}) if isinstance(metadata.get("history_baseline", {}), dict) else {}
    metadata_level = str(history_metadata.get("level", ""))
    input_contract = str(history_metadata.get("input_contract", ""))
    if config_level != spec.history_level:
        raise ValueError(
            f"{spec.label}: checkpoint config history_baseline_level={config_level!r} "
            f"does not match declared {spec.history_level!r}"
        )
    if metadata_level != spec.history_level:
        raise ValueError(
            f"{spec.label}: checkpoint metadata history_baseline.level={metadata_level!r} "
            f"does not match declared {spec.history_level!r}"
        )
    if input_contract != "P0_human_view_no_wheel_no_oracle":
        raise ValueError(f"{spec.label}: checkpoint input contract is not P0 human-view: {input_contract!r}")
    return {
        "label": spec.label,
        "history_level": spec.history_level,
        "path": str(spec.path),
        "input_contract": input_contract,
    }


def load_validated_baseline(
    spec: BaselineCheckpointSpec,
    *,
    device: torch.device,
) -> tuple[ActorCritic, dict[str, Any], dict[str, Any]]:
    model, checkpoint = load_actor_critic_checkpoint(spec.path, device=str(device))
    metadata_row = validate_checkpoint_metadata(checkpoint, spec)
    model.eval()
    return model, checkpoint, metadata_row


def requested_left_tail_steps(pair_rows: pd.DataFrame, tail_offsets: tuple[int, ...]) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in pair_rows.iterrows():
        left_seed = int(row["left_seed"])
        left_step = int(row["left_step"])
        for offset in tail_offsets:
            requests.setdefault(left_seed, set()).add(left_step + int(offset))
    return requests


def _update_base_history(base_history: list[np.ndarray], next_base_observation: np.ndarray, max_history_length: int) -> list[np.ndarray]:
    return [np.asarray(next_base_observation, dtype=np.float32).copy()] + base_history[: max_history_length - 1]


def collect_frozen_source_snapshots(
    *,
    source_model: ActorCritic,
    env_config: DriftEnvConfig,
    requests: dict[int, set[int]],
    max_history_length: int,
    device: torch.device,
) -> dict[tuple[int, int], FrozenSourceSnapshot]:
    if not source_model.is_online_recurrent:
        raise ValueError("source checkpoint must be online recurrent so source natural histories can be reconstructed")
    if env_config.history_length != 1:
        raise ValueError("frozen source-surface evaluator currently expects source env history_length=1")
    max_history_length = max(1, int(max_history_length))
    snapshots: dict[tuple[int, int], FrozenSourceSnapshot] = {}
    env = AutoDriftEnv(env_config)
    try:
        for seed, requested_steps in sorted(requests.items()):
            if not requested_steps:
                continue
            max_requested_step = max(int(step) for step in requested_steps)
            obs, info = env.reset(seed=int(seed))
            base_obs = np.asarray(obs, dtype=np.float32).copy()
            base_history = [base_obs.copy() for _ in range(max_history_length)]
            prefix_observations: list[np.ndarray] = []
            hidden = source_model.initial_hidden(1, device)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                step = int(env.step_count)
                if step in requested_steps:
                    snapshots[(int(seed), step)] = FrozenSourceSnapshot(
                        seed=int(seed),
                        step=step,
                        observation=np.asarray(obs, dtype=np.float32).copy(),
                        base_history=tuple(item.copy() for item in base_history),
                        prefix_observations=tuple(item.copy() for item in prefix_observations),
                        env=copy.deepcopy(env),
                        info=dict(info),
                    )
                action, _, _, next_hidden = source_model.act_recurrent(
                    np.asarray(obs, dtype=np.float32),
                    hidden,
                    deterministic=True,
                )
                prefix_observations.append(np.asarray(obs, dtype=np.float32).copy())
                obs, _, terminated, truncated, info = env.step(action)
                next_base = np.asarray(obs, dtype=np.float32)
                if next_base.shape[0] != HUMAN_VIEW_OBS_DIM:
                    next_base = next_base[:HUMAN_VIEW_OBS_DIM]
                base_history = _update_base_history(base_history, next_base, max_history_length)
                hidden = next_hidden
                if int(env.step_count) > max_requested_step and all(
                    (int(seed), int(step_item)) in snapshots for step_item in requested_steps
                ):
                    break
    finally:
        env.close()
    return snapshots


def observation_for_model(model: ActorCritic, base_history: tuple[np.ndarray, ...] | list[np.ndarray]) -> np.ndarray:
    if not base_history:
        raise ValueError("base_history cannot be empty")
    if model.actor_encoder == "temporal_gru":
        if len(base_history) < model.actor_history_length:
            padded = list(base_history) + [base_history[-1]] * (model.actor_history_length - len(base_history))
        else:
            padded = list(base_history[: model.actor_history_length])
        obs = np.concatenate([np.asarray(item, dtype=np.float32) for item in padded]).astype(np.float32)
    else:
        obs = np.asarray(base_history[0], dtype=np.float32).copy()
    if obs.shape[0] != model.obs_dim:
        raise ValueError(
            f"observation dimension {obs.shape[0]} does not match {model.actor_encoder} model obs_dim {model.obs_dim}"
        )
    return obs


def build_offpolicy_recurrent_hidden(
    model: ActorCritic,
    prefix_observations: tuple[np.ndarray, ...] | list[np.ndarray],
    *,
    device: torch.device,
) -> torch.Tensor | None:
    if not model.is_online_recurrent:
        return None
    hidden = model.initial_hidden(1, device)
    with torch.no_grad():
        for observation in prefix_observations:
            obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
            _, hidden = model.recurrent_features_tensor(obs_t, hidden)
    return hidden.detach()


def deterministic_action_for_model(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor | None,
) -> tuple[np.ndarray, torch.Tensor | None]:
    if model.is_online_recurrent:
        action, _, _, next_hidden = model.act_recurrent(observation, hidden, deterministic=True)
        return action, next_hidden
    action, _, _ = model.act(observation, deterministic=True)
    return action, None


def replay_baseline_from_snapshot(
    *,
    model: ActorCritic,
    snapshot: FrozenSourceSnapshot,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    env = copy.deepcopy(snapshot.env)
    base_history = [item.copy() for item in snapshot.base_history]
    hidden = build_offpolicy_recurrent_hidden(model, snapshot.prefix_observations, device=device)
    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env.config.max_steps - int(snapshot.step))
    for _ in range(max_steps):
        model_obs = observation_for_model(model, base_history)
        action, hidden = deterministic_action_for_model(model, model_obs, hidden)
        actions.append(np.asarray(action, dtype=np.float32).copy())
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        next_base = np.asarray(obs, dtype=np.float32)
        if next_base.shape[0] != HUMAN_VIEW_OBS_DIM:
            next_base = next_base[:HUMAN_VIEW_OBS_DIM]
        base_history = _update_base_history(base_history, next_base, len(base_history))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env.config)
    return {
        "steps": int(len(rewards)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
    }


def summarize_surface_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (baseline_label, history_level, target, tail_offset), group in frame.groupby(
        ["baseline_label", "history_level", "target", "tail_offset"],
        observed=True,
    ):
        margins = group["min_clearance_margin"].astype(float)
        finite_margins = margins[np.isfinite(margins)]
        summary_rows.append(
            {
                "baseline_label": str(baseline_label),
                "history_level": str(history_level),
                "target": str(target),
                "tail_offset": int(tail_offset),
                "row_count": int(len(group)),
                "success_rate": float(group["success"].astype(bool).mean()),
                "obstacle_completion_rate": float(group["obstacle_completed"].astype(bool).mean()),
                "collision_rate": float(group["collision"].astype(bool).mean()),
                "return_mean": float(group["return"].astype(float).mean()),
                "steps_mean": float(group["steps"].astype(float).mean()),
                "min_clearance_margin_mean": float(finite_margins.mean()) if len(finite_margins) else None,
                "min_clearance_margin_p10": float(finite_margins.quantile(0.10)) if len(finite_margins) else None,
                "min_clearance_margin_p90": float(finite_margins.quantile(0.90)) if len(finite_margins) else None,
                "first_steer_mean": float(group["first_steer"].astype(float).mean()),
                "first_throttle_mean": float(group["first_throttle"].astype(float).mean()),
                "first_brake_mean": float(group["first_brake"].astype(float).mean()),
            }
        )
    return summary_rows


def run_frozen_source_surface_eval(
    *,
    source_checkpoint: Path,
    baselines: tuple[BaselineCheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    tail_offsets: tuple[int, ...],
    max_continuation_steps: int,
    max_pairs: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    pair_frame = pd.read_csv(pairs_csv)
    if max_pairs > 0:
        pair_frame = pair_frame.head(int(max_pairs)).copy()
    source_model, _ = load_actor_critic_checkpoint(source_checkpoint, device=str(resolved_device))
    source_model.eval()
    loaded_baselines = []
    metadata_rows = []
    for baseline in baselines:
        model, _, metadata_row = load_validated_baseline(baseline, device=resolved_device)
        loaded_baselines.append((baseline, model))
        metadata_rows.append(metadata_row)
    max_history_length = max([1] + [model.actor_history_length for _, model in loaded_baselines])
    snapshots = collect_frozen_source_snapshots(
        source_model=source_model,
        env_config=env_config,
        requests=requested_left_tail_steps(pair_frame, tail_offsets),
        max_history_length=max_history_length,
        device=resolved_device,
    )
    rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for pair_id, pair in pair_frame.reset_index(drop=True).iterrows():
        for offset in tail_offsets:
            left_tail_step = int(pair["left_step"]) + int(offset)
            snapshot = snapshots.get((int(pair["left_seed"]), left_tail_step))
            if snapshot is None:
                invalid_rows.append(
                    {
                        "pair_id": int(pair_id),
                        "left_seed": int(pair["left_seed"]),
                        "left_step": int(pair["left_step"]),
                        "left_tail_step": left_tail_step,
                        "tail_offset": int(offset),
                        "target": str(pair.get("target", "")),
                        "invalid_reason": "missing_source_tail_snapshot",
                    }
                )
                continue
            for baseline, model in loaded_baselines:
                result = replay_baseline_from_snapshot(
                    model=model,
                    snapshot=snapshot,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
                rows.append(
                    {
                        "pair_id": int(pair_id),
                        "baseline_label": baseline.label,
                        "history_level": baseline.history_level,
                        "baseline_checkpoint": str(baseline.path),
                        "source_checkpoint": str(source_checkpoint),
                        "target": str(pair.get("target", "")),
                        "probe_seed": int(pair.get("probe_seed", -1)),
                        "tail_offset": int(offset),
                        "left_seed": int(pair["left_seed"]),
                        "right_seed": int(pair.get("right_seed", -1)),
                        "left_step": int(pair["left_step"]),
                        "right_step": int(pair.get("right_step", -1)),
                        "left_tail_step": left_tail_step,
                        "left_obstacle_label": str(pair.get("left_obstacle_label", "")),
                        "right_obstacle_label": str(pair.get("right_obstacle_label", "")),
                        **result,
                    }
                )
    summary_rows = summarize_surface_rows(rows)
    write_csv_rows(run_dir / "surface_outcomes.csv", rows)
    write_csv_rows(run_dir / "surface_summary.csv", summary_rows)
    write_csv_rows(run_dir / "invalid_rows.csv", invalid_rows)
    write_csv_rows(run_dir / "baseline_metadata.csv", metadata_rows)
    summary = {
        "run_type": "frozen_source_surface_eval",
        "source_checkpoint": source_checkpoint,
        "baselines": metadata_rows,
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "tail_offsets": list(tail_offsets),
        "max_continuation_steps": int(max_continuation_steps),
        "max_pairs": int(max_pairs),
        "input_pair_count": int(len(pair_frame)),
        "source_snapshot_count": int(len(snapshots)),
        "outcome_row_count": int(len(rows)),
        "invalid_row_count": int(len(invalid_rows)),
        "surface_outcomes_csv": run_dir / "surface_outcomes.csv",
        "surface_summary_csv": run_dir / "surface_summary.csv",
        "invalid_rows_csv": run_dir / "invalid_rows.csv",
        "baseline_metadata_csv": run_dir / "baseline_metadata.csv",
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate baselines on frozen source-policy natural surfaces.")
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--baseline-checkpoint", action="append", type=parse_baseline_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--tail-offsets", type=parse_tail_offsets, default=(0, 2, 4, 8))
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="frozen_source_surface_eval")
    summary = run_frozen_source_surface_eval(
        source_checkpoint=args.source_checkpoint,
        baselines=tuple(args.baseline_checkpoint),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        tail_offsets=tuple(args.tail_offsets),
        max_continuation_steps=args.max_continuation_steps,
        max_pairs=int(args.max_pairs),
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
