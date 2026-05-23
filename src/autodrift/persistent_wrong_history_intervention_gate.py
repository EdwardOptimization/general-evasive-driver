"""Diagnostic persistent wrong-history intervention gate."""

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
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import (
    _pairs_for_checkpoint,
    deterministic_action_from_hidden,
    requested_snapshot_steps,
    zero_current_response_observation,
)
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
)
from autodrift.train_ppo import ActorCritic, resolve_device


@dataclass(frozen=True)
class PersistentVariantSpec:
    name: str
    family: str
    injection_start_step: int = -1
    hold_steps: int = 0
    clamp_hidden: bool = False
    reset_hidden: bool = False
    zero_current_response: bool = False


DEFAULT_VARIANTS: tuple[PersistentVariantSpec, ...] = (
    PersistentVariantSpec(name="normal", family="baseline"),
    PersistentVariantSpec(name="wrong_once", family="wrong_once", injection_start_step=0, hold_steps=1),
    PersistentVariantSpec(
        name="wrong_hold_4",
        family="wrong_hold",
        injection_start_step=0,
        hold_steps=4,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_hold_8",
        family="wrong_hold",
        injection_start_step=0,
        hold_steps=8,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_hold_16",
        family="wrong_hold",
        injection_start_step=0,
        hold_steps=16,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_late_4_hold_4",
        family="wrong_late",
        injection_start_step=4,
        hold_steps=4,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_late_8_hold_4",
        family="wrong_late",
        injection_start_step=8,
        hold_steps=4,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_late_4_hold_8",
        family="wrong_late",
        injection_start_step=4,
        hold_steps=8,
        clamp_hidden=True,
    ),
    PersistentVariantSpec(
        name="wrong_late_2_once",
        family="wrong_late_once",
        injection_start_step=2,
        hold_steps=1,
        clamp_hidden=False,
    ),
    PersistentVariantSpec(
        name="wrong_late_4_once",
        family="wrong_late_once",
        injection_start_step=4,
        hold_steps=1,
        clamp_hidden=False,
    ),
    PersistentVariantSpec(
        name="wrong_late_8_once",
        family="wrong_late_once",
        injection_start_step=8,
        hold_steps=1,
        clamp_hidden=False,
    ),
    PersistentVariantSpec(
        name="wrong_late_12_once",
        family="wrong_late_once",
        injection_start_step=12,
        hold_steps=1,
        clamp_hidden=False,
    ),
    PersistentVariantSpec(
        name="wrong_reseed_4",
        family="wrong_reseed",
        injection_start_step=0,
        hold_steps=4,
        clamp_hidden=False,
    ),
    PersistentVariantSpec(name="reset_hidden", family="baseline", reset_hidden=True),
    PersistentVariantSpec(name="zero_current_response", family="baseline", zero_current_response=True),
)


def persistent_variant_specs() -> tuple[PersistentVariantSpec, ...]:
    return DEFAULT_VARIANTS


def variant_injects_at_step(spec: PersistentVariantSpec, continuation_step: int) -> bool:
    if spec.hold_steps <= 0 or spec.injection_start_step < 0:
        return False
    step = int(continuation_step)
    start = int(spec.injection_start_step)
    return start <= step < start + int(spec.hold_steps)


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed persistent outcome snapshot seed={seed} step={step}")
    return snapshots[key]


def replay_persistent_variant(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    env_config: DriftEnvConfig,
    spec: PersistentVariantSpec,
    response_dim: int,
    wrong_hidden: torch.Tensor,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    reset_hidden = model.initial_hidden(1, device)
    wrong_hidden = wrong_hidden.detach().clone()

    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)

    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    injection_count = 0
    terminated = False
    truncated = False
    info = dict(snapshot.info)

    for continuation_step in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if spec.zero_current_response:
            policy_obs = zero_current_response_observation(policy_obs, response_dim)

        inject_wrong = variant_injects_at_step(spec, continuation_step)
        if spec.reset_hidden:
            action_hidden = reset_hidden
        elif inject_wrong:
            action_hidden = wrong_hidden
            injection_count += 1
        else:
            action_hidden = hidden

        action, next_hidden = deterministic_action_from_hidden(model, policy_obs, action_hidden, device)
        actions.append(action)

        if spec.reset_hidden:
            hidden = reset_hidden
        elif inject_wrong and spec.clamp_hidden and variant_injects_at_step(spec, continuation_step + 1):
            hidden = wrong_hidden
        else:
            hidden = next_hidden

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
        if spec.name == "normal"
        else float("nan")
    )
    trajectory_distances = (
        zero_action_trajectory_distances(len(actions))
        if spec.name == "normal"
        else action_trajectory_distances(actions, normal_actions)
    )
    reason = terminal_reason(info, terminated, truncated, env_config)
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    return {
        "variant": spec.name,
        "variant_family": spec.family,
        "injection_start_step": int(spec.injection_start_step),
        "hold_steps": int(spec.hold_steps),
        "clamp_hidden": bool(spec.clamp_hidden),
        "injection_count": int(injection_count),
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


def _normal_and_variant_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    max_continuation_steps: int,
    min_margin_gap: float,
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    specs = persistent_variant_specs()
    normal_spec = specs[0]
    for pair_id, pair in pair_rows.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
        right = _snapshot(snapshots, int(pair["right_seed"]), int(pair["right_step"]))
        normal, normal_actions = replay_persistent_variant(
            model=model,
            snapshot=left,
            env_config=env_config,
            spec=normal_spec,
            response_dim=response_dim,
            wrong_hidden=right.hidden,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        variant_results: dict[str, dict[str, Any]] = {"normal": normal}
        for spec in specs[1:]:
            result, _ = replay_persistent_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                spec=spec,
                response_dim=response_dim,
                wrong_hidden=right.hidden,
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            variant_results[spec.name] = result

        normal_margin = float(normal.get("min_clearance_margin", float("nan")))
        normal_success = bool(normal.get("success", False))
        normal_collision = bool(normal.get("collision", False))
        normal_completed = bool(normal.get("obstacle_completed", False))
        for spec in specs:
            result = variant_results[spec.name]
            variant_margin = float(result.get("min_clearance_margin", float("nan")))
            margin_gap = (
                normal_margin - variant_margin
                if np.isfinite(normal_margin) and np.isfinite(variant_margin)
                else float("nan")
            )
            success_drop = bool(normal_success and not bool(result.get("success", False)))
            collision_gap = bool(not normal_collision and bool(result.get("collision", False)))
            completion_drop = bool(normal_completed and not bool(result.get("obstacle_completed", False)))
            proof_margin_gap = bool(np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap))
            rows.append(
                {
                    "pair_id": int(pair_id),
                    "checkpoint_label": str(pair.get("checkpoint_label", "")),
                    "probe_seed": int(pair.get("probe_seed", -1)),
                    "target": str(pair["target"]),
                    "left_seed": int(pair["left_seed"]),
                    "right_seed": int(pair["right_seed"]),
                    "left_step": int(pair["left_step"]),
                    "right_step": int(pair["right_step"]),
                    "target_z_delta": float(pair["target_z_delta"]),
                    "visible_distance": float(pair["visible_distance"]),
                    "left_obstacle_label": str(pair.get("left_obstacle_label", "")),
                    "right_obstacle_label": str(pair.get("right_obstacle_label", "")),
                    "normal_success": normal_success,
                    "variant_success": bool(result.get("success", False)),
                    "success_drop": success_drop,
                    "collision_gap": collision_gap,
                    "obstacle_completion_drop": completion_drop,
                    "normal_margin": normal_margin,
                    "variant_margin": variant_margin,
                    "margin_gap": margin_gap,
                    "proof_margin_gap": proof_margin_gap,
                    "proof_candidate": bool(success_drop or collision_gap or completion_drop or proof_margin_gap),
                    **result,
                }
            )
    return rows


def summarize_persistent_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (checkpoint_label, target, variant), group in frame.groupby(
        ["checkpoint_label", "target", "variant"],
        observed=True,
    ):
        finite_gap = group["margin_gap"].astype(float)
        finite_gap = finite_gap[np.isfinite(finite_gap)]
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "variant": str(variant),
                "variant_family": str(group["variant_family"].iloc[0]),
                "pair_count": int(len(group)),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "collision_gap_count": int(group["collision_gap"].astype(bool).sum()),
                "completion_drop_count": int(group["obstacle_completion_drop"].astype(bool).sum()),
                "proof_margin_gap_count": int(group["proof_margin_gap"].astype(bool).sum()),
                "proof_candidate_count": int(group["proof_candidate"].astype(bool).sum()),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "variant_margin_mean": float(group["variant_margin"].astype(float).mean()),
                "margin_gap_mean": float(finite_gap.mean()) if len(finite_gap) else float("nan"),
                "margin_gap_max": float(finite_gap.max()) if len(finite_gap) else float("nan"),
                "first_action_distance_mean": float(group["first_action_distance"].astype(float).mean()),
                "trajectory_distance_mean": float(group["action_trajectory_distance_mean"].astype(float).mean()),
                "trajectory_distance_max": float(group["action_trajectory_distance_max"].astype(float).max()),
                "injection_count_mean": float(group["injection_count"].astype(float).mean()),
            }
        )
    return summary_rows


def summarize_proof_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "best_variant": "",
            "best_variant_proof_candidate_count": 0,
            "best_variant_success_or_collision_or_completion_rows": 0,
            "best_variant_probe_seed_count": 0,
            "best_variant_obstacle_label_count": 0,
            "best_variant_target_count": 0,
        }
    frame = pd.DataFrame(rows)
    frame = frame[
        frame["variant_family"].isin(["wrong_hold", "wrong_late", "wrong_late_once", "wrong_reseed", "wrong_once"])
    ].copy()
    best: dict[str, Any] | None = None
    for variant, group in frame.groupby("variant", observed=True):
        proof = group[group["proof_candidate"].astype(bool)]
        count = int(len(proof))
        success_or_collision_or_completion = int(
            (
                proof["success_drop"].astype(bool)
                | proof["collision_gap"].astype(bool)
                | proof["obstacle_completion_drop"].astype(bool)
            ).sum()
        )
        row = {
            "best_variant": str(variant),
            "best_variant_proof_candidate_count": count,
            "best_variant_success_or_collision_or_completion_rows": success_or_collision_or_completion,
            "best_variant_probe_seed_count": int(proof["probe_seed"].nunique()) if count else 0,
            "best_variant_obstacle_label_count": int(proof["left_obstacle_label"].nunique()) if count else 0,
            "best_variant_target_count": int(proof["target"].nunique()) if count else 0,
            "best_variant_single_seed_share": float(proof["probe_seed"].value_counts().max() / count) if count else 0.0,
            "best_variant_single_label_share": float(proof["left_obstacle_label"].value_counts().max() / count)
            if count
            else 0.0,
        }
        if best is None or row["best_variant_proof_candidate_count"] > best["best_variant_proof_candidate_count"]:
            best = row
    return best or {
        "best_variant": "",
        "best_variant_proof_candidate_count": 0,
        "best_variant_success_or_collision_or_completion_rows": 0,
        "best_variant_probe_seed_count": 0,
        "best_variant_obstacle_label_count": 0,
        "best_variant_target_count": 0,
        "best_variant_single_seed_share": 0.0,
        "best_variant_single_label_share": 0.0,
    }


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


def run_persistent_wrong_history_intervention_gate(
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
            _normal_and_variant_rows(
                pair_rows=checkpoint_pairs,
                snapshots=snapshots,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                min_margin_gap=min_margin_gap,
                device=resolved_device,
            )
        )

    summary_rows = summarize_persistent_outcomes(outcome_rows)
    proof_summary = summarize_proof_candidates(outcome_rows)
    write_csv_rows(run_dir / "persistent_outcomes.csv", outcome_rows)
    write_csv_rows(run_dir / "variant_summary.csv", summary_rows)
    summary = {
        "run_type": "persistent_wrong_history_intervention_gate",
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
        "variant_summary_rows": int(len(summary_rows)),
        "persistent_outcomes_csv": run_dir / "persistent_outcomes.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        **proof_summary,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run persistent wrong-history diagnostic interventions.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=160)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="persistent_wrong_history_intervention_gate")
    summary = run_persistent_wrong_history_intervention_gate(
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
