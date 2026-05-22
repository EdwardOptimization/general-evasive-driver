"""Continuation outcome gates for matched-history interventions."""

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
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import (
    ACTION_VARIANTS,
    _pairs_for_checkpoint,
    deterministic_action_from_hidden,
    requested_snapshot_steps,
    zero_action_history_observation,
    zero_current_response_observation,
)
from autodrift.train_ppo import ActorCritic, resolve_device


OUTCOME_VARIANTS = ("normal", *ACTION_VARIANTS)


@dataclass
class OutcomeSnapshot:
    seed: int
    step: int
    observation: np.ndarray
    hidden: torch.Tensor
    env: AutoDriftEnv
    info: dict[str, Any]


def collect_requested_outcome_snapshots(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    requests: dict[int, set[int]],
    device: torch.device,
) -> dict[tuple[int, int], OutcomeSnapshot]:
    if not model.is_online_recurrent:
        raise ValueError("matched history outcome gate requires an online recurrent checkpoint")
    snapshots: dict[tuple[int, int], OutcomeSnapshot] = {}
    env = AutoDriftEnv(env_config)
    try:
        for seed, requested_steps in sorted(requests.items()):
            if not requested_steps:
                continue
            max_requested_step = max(int(step) for step in requested_steps)
            obs, info = env.reset(seed=int(seed))
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                step = int(env.step_count)
                if step in requested_steps:
                    snapshots[(int(seed), step)] = OutcomeSnapshot(
                        seed=int(seed),
                        step=step,
                        observation=np.asarray(obs, dtype=np.float32).copy(),
                        hidden=hidden.detach().clone(),
                        env=copy.deepcopy(env),
                        info=dict(info),
                    )
                action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
                obs, _, terminated, truncated, info = env.step(action)
                hidden = next_hidden
                if int(env.step_count) > max_requested_step and all(
                    (int(seed), int(step_item)) in snapshots for step_item in requested_steps
                ):
                    break
    finally:
        env.close()
    return snapshots


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed outcome snapshot seed={seed} step={step}")
    return snapshots[key]


def replay_outcome_variant(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    env_config: DriftEnvConfig,
    variant: str,
    response_dim: int,
    variant_hidden: torch.Tensor | None,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    if variant not in OUTCOME_VARIANTS:
        raise ValueError(f"unknown matched-history outcome variant: {variant}")
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    if variant == "normal":
        hidden = snapshot.hidden.detach().clone()
    elif variant == "reset_hidden":
        hidden = model.initial_hidden(1, device)
    elif variant_hidden is not None:
        hidden = variant_hidden.detach().clone()
    else:
        hidden = snapshot.hidden.detach().clone()

    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)

    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if variant == "zero_current_response":
            policy_obs = zero_current_response_observation(policy_obs, response_dim)
        elif variant == "zero_action_history":
            policy_obs = zero_action_history_observation(policy_obs)
        action_hidden = model.initial_hidden(1, device) if variant == "reset_hidden" else hidden
        action, next_hidden = deterministic_action_from_hidden(model, policy_obs, action_hidden, device)
        actions.append(action)
        hidden = model.initial_hidden(1, device) if variant == "reset_hidden" else next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break

    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_action_distance = (
        float(np.linalg.norm(first_action - normal_first_action))
        if normal_first_action is not None and np.all(np.isfinite(first_action))
        else 0.0
        if variant == "normal"
        else float("nan")
    )
    trajectory_distances = (
        zero_action_trajectory_distances(len(actions))
        if variant == "normal"
        else action_trajectory_distances(actions, normal_actions)
    )
    reason = terminal_reason(info, terminated, truncated, env_config)
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    return {
        "variant": variant,
        "steps": len(rewards),
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
        "first_action_distance": first_action_distance,
        **trajectory_distances,
    }, actions


def build_outcome_intervention_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    delay_steps: int,
    max_continuation_steps: int,
    min_margin_gap: float,
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair_id, pair in pair_rows.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
        right = _snapshot(snapshots, int(pair["right_seed"]), int(pair["right_step"]))
        delayed = _snapshot(
            snapshots,
            int(pair["left_seed"]),
            max(0, int(pair["left_step"]) - int(delay_steps)),
        )
        normal, normal_actions = replay_outcome_variant(
            model=model,
            snapshot=left,
            env_config=env_config,
            variant="normal",
            response_dim=response_dim,
            variant_hidden=None,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        variant_hidden = {
            "wrong_matched_history": right.hidden,
            "delayed_history": delayed.hidden,
        }
        variant_results: dict[str, dict[str, Any]] = {"normal": normal}
        for variant in ACTION_VARIANTS:
            result, _ = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant=variant,
                response_dim=response_dim,
                variant_hidden=variant_hidden.get(variant),
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            variant_results[variant] = result

        normal_margin = float(normal.get("min_clearance_margin", float("nan")))
        normal_success = bool(normal.get("success", False))
        for variant in OUTCOME_VARIANTS:
            result = variant_results[variant]
            variant_margin = float(result.get("min_clearance_margin", float("nan")))
            margin_gap = (
                normal_margin - variant_margin
                if np.isfinite(normal_margin) and np.isfinite(variant_margin)
                else float("nan")
            )
            success_drop = bool(normal_success and not bool(result.get("success", False)))
            normal_better = bool(success_drop or (np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap)))
            rows.append(
                {
                    "pair_id": int(pair_id),
                    "checkpoint_label": str(pair.get("checkpoint_label", "")),
                    "probe_seed": int(pair.get("probe_seed", -1)),
                    "target": str(pair["target"]),
                    "variant": variant,
                    "left_seed": int(pair["left_seed"]),
                    "right_seed": int(pair["right_seed"]),
                    "left_step": int(pair["left_step"]),
                    "right_step": int(pair["right_step"]),
                    "target_z_delta": float(pair["target_z_delta"]),
                    "visible_distance": float(pair["visible_distance"]),
                    "normal_success": normal_success,
                    "variant_success": bool(result.get("success", False)),
                    "success_drop": success_drop,
                    "normal_margin": normal_margin,
                    "variant_margin": variant_margin,
                    "margin_gap": margin_gap,
                    "normal_better": normal_better if variant != "normal" else False,
                    **result,
                }
            )
    return rows


def summarize_outcome_interventions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (checkpoint_label, target, variant), group in frame.groupby(
        ["checkpoint_label", "target", "variant"],
        observed=True,
    ):
        margin_gap = group["margin_gap"].astype(float)
        finite_gap = margin_gap[np.isfinite(margin_gap)]
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "variant": str(variant),
                "pair_count": int(len(group)),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "success_drop_rate": float(group["success_drop"].astype(bool).mean()),
                "normal_better_fraction": float(group["normal_better"].astype(bool).mean()),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "variant_margin_mean": float(group["variant_margin"].astype(float).mean()),
                "margin_gap_mean": float(finite_gap.mean()) if len(finite_gap) else float("nan"),
                "margin_gap_p50": float(finite_gap.quantile(0.50)) if len(finite_gap) else float("nan"),
                "margin_gap_p90": float(finite_gap.quantile(0.90)) if len(finite_gap) else float("nan"),
                "return_mean": float(group["return"].astype(float).mean()),
                "collision_rate": float(group["collision"].astype(bool).mean()),
                "off_road_rate": float(group["off_road"].astype(bool).mean()),
                "obstacle_completion_rate": float(group["obstacle_completed"].astype(bool).mean()),
                "first_action_distance_mean": float(group["first_action_distance"].astype(float).mean()),
                "trajectory_distance_mean": float(group["action_trajectory_distance_mean"].astype(float).mean()),
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


def run_matched_history_outcome_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    delay_steps: int,
    max_continuation_steps: int,
    min_margin_gap: float,
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
    outcome_rows: list[dict[str, Any]] = []

    for checkpoint_spec in checkpoint_specs:
        checkpoint_pairs = _pairs_for_checkpoint(pair_frame, checkpoint_spec.label, pair_label_mode)
        if checkpoint_pairs.empty:
            continue
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        response_dim = response_feature_dim_for_model(model)
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=requested_snapshot_steps(checkpoint_pairs, delay_steps=delay_steps),
            device=resolved_device,
        )
        outcome_rows.extend(
            build_outcome_intervention_rows(
                pair_rows=checkpoint_pairs,
                snapshots=snapshots,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                delay_steps=delay_steps,
                max_continuation_steps=max_continuation_steps,
                min_margin_gap=min_margin_gap,
                device=resolved_device,
            )
        )

    summary_rows = summarize_outcome_interventions(outcome_rows)
    write_csv_rows(run_dir / "outcome_interventions.csv", outcome_rows)
    write_csv_rows(run_dir / "outcome_summary.csv", summary_rows)
    summary = {
        "run_type": "matched_history_outcome_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "delay_steps": int(delay_steps),
        "max_continuation_steps": int(max_continuation_steps),
        "min_margin_gap": float(min_margin_gap),
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "pair_label_mode": str(pair_label_mode),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "outcome_row_count": int(len(outcome_rows)),
        "outcome_summary_rows": int(len(summary_rows)),
        "outcome_interventions_csv": run_dir / "outcome_interventions.csv",
        "outcome_summary_csv": run_dir / "outcome_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run continuation outcome gates on matched-history interventions.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--delay-steps", type=int, default=10)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=40)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="matched_history_outcome_gate")
    summary = run_matched_history_outcome_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        delay_steps=args.delay_steps,
        max_continuation_steps=args.max_continuation_steps,
        min_margin_gap=args.min_margin_gap,
        max_pairs_per_checkpoint_target=args.max_pairs_per_checkpoint_target,
        pair_label_mode=args.pair_label_mode,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
