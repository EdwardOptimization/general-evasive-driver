"""Action-level interventions on matched-current-response history pairs."""

from __future__ import annotations

import argparse
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
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.train_ppo import ActorCritic, resolve_device


ACTION_VARIANTS = (
    "reset_hidden",
    "wrong_matched_history",
    "delayed_history",
    "zero_current_response",
    "zero_action_history",
)
PREVIOUS_COMMAND_INDICES = (9, 10, 11)


@dataclass(frozen=True)
class RecurrentSnapshot:
    seed: int
    step: int
    observation: np.ndarray
    hidden: torch.Tensor


def deterministic_action_from_hidden(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, next_hidden = model.recurrent_features_tensor(obs_t, hidden_t)
        action = torch.tanh(model.actor_mean(features))
    return action.squeeze(0).detach().cpu().numpy().astype(np.float32), next_hidden.detach()


def zero_current_response_observation(observation: np.ndarray, response_dim: int) -> np.ndarray:
    next_observation = np.asarray(observation, dtype=np.float32).copy()
    next_observation[:response_dim] = 0.0
    return next_observation


def zero_action_history_observation(observation: np.ndarray) -> np.ndarray:
    next_observation = np.asarray(observation, dtype=np.float32).copy()
    for index in PREVIOUS_COMMAND_INDICES:
        if index < next_observation.shape[0]:
            next_observation[index] = 0.0
    return next_observation


def action_distance(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def requested_snapshot_steps(pair_rows: pd.DataFrame, delay_steps: int) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in pair_rows.iterrows():
        for prefix in ("left", "right"):
            seed = int(row[f"{prefix}_seed"])
            step = int(row[f"{prefix}_step"])
            requests.setdefault(seed, set()).add(step)
            if prefix == "left":
                requests[seed].add(max(0, step - int(delay_steps)))
    return requests


def collect_requested_snapshots(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    requests: dict[int, set[int]],
    device: torch.device,
) -> dict[tuple[int, int], RecurrentSnapshot]:
    if not model.is_online_recurrent:
        raise ValueError("matched history intervention gate requires an online recurrent checkpoint")
    snapshots: dict[tuple[int, int], RecurrentSnapshot] = {}
    env = AutoDriftEnv(env_config)
    try:
        for seed, requested_steps in sorted(requests.items()):
            if not requested_steps:
                continue
            max_requested_step = max(int(step) for step in requested_steps)
            obs, _ = env.reset(seed=int(seed))
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                step = int(env.step_count)
                if step in requested_steps:
                    snapshots[(int(seed), step)] = RecurrentSnapshot(
                        seed=int(seed),
                        step=step,
                        observation=np.asarray(obs, dtype=np.float32).copy(),
                        hidden=hidden.detach().clone(),
                    )
                action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
                obs, _, terminated, truncated, _ = env.step(action)
                hidden = next_hidden
                if int(env.step_count) > max_requested_step and all(
                    (int(seed), int(step_item)) in snapshots for step_item in requested_steps
                ):
                    break
    finally:
        env.close()
    return snapshots


def _snapshot(snapshots: dict[tuple[int, int], RecurrentSnapshot], seed: int, step: int) -> RecurrentSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def build_action_intervention_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], RecurrentSnapshot],
    model: ActorCritic,
    response_dim: int,
    delay_steps: int,
    min_action_distance: float,
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reset_hidden = model.initial_hidden(1, device)
    for pair_id, pair in pair_rows.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
        right = _snapshot(snapshots, int(pair["right_seed"]), int(pair["right_step"]))
        delayed = _snapshot(
            snapshots,
            int(pair["left_seed"]),
            max(0, int(pair["left_step"]) - int(delay_steps)),
        )
        normal_left, _ = deterministic_action_from_hidden(model, left.observation, left.hidden, device)
        normal_right, _ = deterministic_action_from_hidden(model, right.observation, right.hidden, device)
        normal_pair_action_distance = action_distance(normal_left, normal_right)
        variants = {
            "reset_hidden": (left.observation, reset_hidden),
            "wrong_matched_history": (left.observation, right.hidden),
            "delayed_history": (left.observation, delayed.hidden),
            "zero_current_response": (
                zero_current_response_observation(left.observation, response_dim),
                left.hidden,
            ),
            "zero_action_history": (zero_action_history_observation(left.observation), left.hidden),
        }
        for variant, (variant_observation, variant_hidden) in variants.items():
            variant_action, _ = deterministic_action_from_hidden(model, variant_observation, variant_hidden, device)
            variant_distance = action_distance(normal_left, variant_action)
            variant_to_right_distance = action_distance(normal_right, variant_action)
            rows.append(
                {
                    "pair_id": int(pair_id),
                    "checkpoint_label": str(pair.get("checkpoint_label", "")),
                    "source_checkpoint_label": str(
                        pair.get("source_checkpoint_label", pair.get("checkpoint_label", ""))
                    ),
                    "probe_seed": int(pair.get("probe_seed", -1)),
                    "target": str(pair["target"]),
                    "variant": variant,
                    "left_seed": int(pair["left_seed"]),
                    "right_seed": int(pair["right_seed"]),
                    "left_step": int(pair["left_step"]),
                    "right_step": int(pair["right_step"]),
                    "target_z_delta": float(pair["target_z_delta"]),
                    "visible_distance": float(pair["visible_distance"]),
                    "normal_pair_action_distance": normal_pair_action_distance,
                    "action_distance": variant_distance,
                    "action_distance_above_threshold": bool(variant_distance >= float(min_action_distance)),
                    "variant_to_right_action_distance": variant_to_right_distance,
                    "wrong_history_closer_to_right_action": bool(
                        variant == "wrong_matched_history"
                        and variant_to_right_distance < normal_pair_action_distance
                    ),
                    "normal_steer": float(normal_left[0]),
                    "normal_throttle": float(normal_left[1]),
                    "normal_brake": float(normal_left[2]),
                    "variant_steer": float(variant_action[0]),
                    "variant_throttle": float(variant_action[1]),
                    "variant_brake": float(variant_action[2]),
                    "abs_steer_delta": float(abs(normal_left[0] - variant_action[0])),
                    "abs_throttle_delta": float(abs(normal_left[1] - variant_action[1])),
                    "abs_brake_delta": float(abs(normal_left[2] - variant_action[2])),
                }
            )
    return rows


def summarize_action_interventions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (checkpoint_label, target, variant), group in frame.groupby(
        ["checkpoint_label", "target", "variant"],
        observed=True,
    ):
        action_distance_values = group["action_distance"].astype(float)
        threshold_mask = group["action_distance_above_threshold"].astype(bool)
        wrong_closer = (
            group["wrong_history_closer_to_right_action"].astype(bool)
            if "wrong_history_closer_to_right_action" in group
            else pd.Series([False] * len(group))
        )
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "variant": str(variant),
                "pair_count": int(len(group)),
                "action_distance_mean": float(action_distance_values.mean()),
                "action_distance_p50": float(action_distance_values.quantile(0.50)),
                "action_distance_p90": float(action_distance_values.quantile(0.90)),
                "action_distance_max": float(action_distance_values.max()),
                "above_threshold_count": int(threshold_mask.sum()),
                "above_threshold_fraction": float(threshold_mask.mean()),
                "normal_pair_action_distance_mean": float(group["normal_pair_action_distance"].astype(float).mean()),
                "variant_to_right_action_distance_mean": float(
                    group["variant_to_right_action_distance"].astype(float).mean()
                ),
                "wrong_history_closer_to_right_fraction": float(wrong_closer.mean()),
                "abs_steer_delta_mean": float(group["abs_steer_delta"].astype(float).mean()),
                "abs_throttle_delta_mean": float(group["abs_throttle_delta"].astype(float).mean()),
                "abs_brake_delta_mean": float(group["abs_brake_delta"].astype(float).mean()),
            }
        )
    return summary_rows


def _limit_pairs(frame: pd.DataFrame, max_pairs_per_checkpoint_target: int) -> pd.DataFrame:
    if max_pairs_per_checkpoint_target <= 0:
        return frame.reset_index(drop=True)
    selected = []
    for _, group in frame.groupby(["checkpoint_label", "target"], observed=True):
        selected.append(
            group.sort_values(["target_z_delta", "visible_distance"], ascending=[False, True]).head(
                int(max_pairs_per_checkpoint_target)
            )
        )
    if not selected:
        return frame.head(0).copy()
    return pd.concat(selected, ignore_index=True)


def _pairs_for_checkpoint(pair_frame: pd.DataFrame, checkpoint_label: str, pair_label_mode: str) -> pd.DataFrame:
    if pair_label_mode == "matching":
        return pair_frame[pair_frame["checkpoint_label"].astype(str) == str(checkpoint_label)].copy()
    if pair_label_mode == "all":
        output = pair_frame.copy()
        output["source_checkpoint_label"] = output["checkpoint_label"].astype(str)
        output["checkpoint_label"] = str(checkpoint_label)
        return output
    raise ValueError("pair_label_mode must be 'matching' or 'all'")


def run_matched_history_intervention_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    delay_steps: int,
    min_action_distance: float,
    max_pairs_per_checkpoint_target: int,
    pair_label_mode: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    pair_frame = pd.read_csv(pairs_csv)
    pair_frame = _limit_pairs(pair_frame, max_pairs_per_checkpoint_target=max_pairs_per_checkpoint_target)
    intervention_rows: list[dict[str, Any]] = []

    for checkpoint_spec in checkpoint_specs:
        checkpoint_pairs = _pairs_for_checkpoint(pair_frame, checkpoint_spec.label, pair_label_mode)
        if checkpoint_pairs.empty:
            continue
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        response_dim = response_feature_dim_for_model(model)
        snapshots = collect_requested_snapshots(
            model=model,
            env_config=env_config,
            requests=requested_snapshot_steps(checkpoint_pairs, delay_steps=delay_steps),
            device=resolved_device,
        )
        intervention_rows.extend(
            build_action_intervention_rows(
                pair_rows=checkpoint_pairs,
                snapshots=snapshots,
                model=model,
                response_dim=response_dim,
                delay_steps=delay_steps,
                min_action_distance=min_action_distance,
                device=resolved_device,
            )
        )

    summary_rows = summarize_action_interventions(intervention_rows)
    write_csv_rows(run_dir / "action_interventions.csv", intervention_rows)
    write_csv_rows(run_dir / "variant_summary.csv", summary_rows)
    summary = {
        "run_type": "matched_history_intervention_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "delay_steps": int(delay_steps),
        "min_action_distance": float(min_action_distance),
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "pair_label_mode": str(pair_label_mode),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "intervention_row_count": int(len(intervention_rows)),
        "variant_summary_rows": int(len(summary_rows)),
        "action_interventions_csv": run_dir / "action_interventions.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run action-level matched-history intervention gates.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--delay-steps", type=int, default=10)
    parser.add_argument("--min-action-distance", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=80)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="matched_history_intervention_gate")
    summary = run_matched_history_intervention_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        delay_steps=args.delay_steps,
        min_action_distance=args.min_action_distance,
        max_pairs_per_checkpoint_target=args.max_pairs_per_checkpoint_target,
        pair_label_mode=args.pair_label_mode,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
