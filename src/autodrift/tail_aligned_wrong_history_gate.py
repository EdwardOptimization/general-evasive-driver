"""Tail-aligned one-shot wrong-history intervention gate."""

from __future__ import annotations

import argparse
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
from autodrift.matched_history_intervention_gate import _pairs_for_checkpoint
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.train_ppo import ActorCritic, resolve_device


TAIL_VARIANTS = ("normal_tail", "wrong_tail_once", "reset_tail", "zero_current_tail")


def parse_tail_offsets(value: str) -> tuple[int, ...]:
    offsets = tuple(int(part.strip()) for part in str(value).split(",") if part.strip())
    if not offsets:
        raise ValueError("at least one tail offset is required")
    if any(offset < 0 for offset in offsets):
        raise ValueError("tail offsets must be non-negative")
    return tuple(dict.fromkeys(offsets))


def tail_requested_snapshot_steps(pair_rows: pd.DataFrame, tail_offsets: tuple[int, ...]) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in pair_rows.iterrows():
        for offset in tail_offsets:
            for prefix in ("left", "right"):
                seed = int(row[f"{prefix}_seed"])
                step = int(row[f"{prefix}_step"]) + int(offset)
                requests.setdefault(seed, set()).add(step)
    return requests


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _event_count(proof: pd.DataFrame) -> int:
    if proof.empty:
        return 0
    return int(
        (
            proof["success_drop"].astype(bool)
            | proof["collision_gap"].astype(bool)
            | proof["obstacle_completion_drop"].astype(bool)
        ).sum()
    )


def build_tail_aligned_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    tail_offsets: tuple[int, ...],
    max_continuation_steps: int,
    min_margin_gap: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outcome_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for pair_id, pair in pair_rows.reset_index(drop=True).iterrows():
        for offset in tail_offsets:
            left_tail_step = int(pair["left_step"]) + int(offset)
            right_tail_step = int(pair["right_step"]) + int(offset)
            left = _snapshot(snapshots, int(pair["left_seed"]), left_tail_step)
            right = _snapshot(snapshots, int(pair["right_seed"]), right_tail_step)
            if left is None or right is None:
                invalid_rows.append(
                    {
                        "pair_id": int(pair_id),
                        "checkpoint_label": str(pair.get("checkpoint_label", "")),
                        "probe_seed": int(pair.get("probe_seed", -1)),
                        "target": str(pair["target"]),
                        "tail_offset": int(offset),
                        "left_seed": int(pair["left_seed"]),
                        "right_seed": int(pair["right_seed"]),
                        "left_step": int(pair["left_step"]),
                        "right_step": int(pair["right_step"]),
                        "left_tail_step": left_tail_step,
                        "right_tail_step": right_tail_step,
                        "missing_left_tail": left is None,
                        "missing_right_tail": right is None,
                    }
                )
                continue

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
            replay_specs = {
                "normal_tail": ("normal", None, "baseline"),
                "wrong_tail_once": ("wrong_matched_history", right.hidden, "wrong_tail_once"),
                "reset_tail": ("reset_hidden", None, "baseline"),
                "zero_current_tail": ("zero_current_response", None, "baseline"),
            }
            variant_results: dict[str, dict[str, Any]] = {}
            for variant_name, (replay_variant, variant_hidden, variant_family) in replay_specs.items():
                if variant_name == "normal_tail":
                    result = dict(normal)
                    result["variant"] = variant_name
                    result["variant_family"] = variant_family
                else:
                    result, _ = replay_outcome_variant(
                        model=model,
                        snapshot=left,
                        env_config=env_config,
                        variant=replay_variant,
                        response_dim=response_dim,
                        variant_hidden=variant_hidden,
                        normal_first_action=normal_first_action,
                        normal_actions=normal_actions,
                        max_continuation_steps=max_continuation_steps,
                        device=device,
                    )
                    result = dict(result)
                    result["variant"] = variant_name
                    result["variant_family"] = variant_family
                variant_results[variant_name] = result

            normal_margin = float(normal.get("min_clearance_margin", float("nan")))
            normal_success = bool(normal.get("success", False))
            normal_collision = bool(normal.get("collision", False))
            normal_completed = bool(normal.get("obstacle_completed", False))
            for variant_name in TAIL_VARIANTS:
                result = variant_results[variant_name]
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
                outcome_rows.append(
                    {
                        "pair_id": int(pair_id),
                        "checkpoint_label": str(pair.get("checkpoint_label", "")),
                        "probe_seed": int(pair.get("probe_seed", -1)),
                        "target": str(pair["target"]),
                        "tail_offset": int(offset),
                        "variant": variant_name,
                        "variant_family": str(result["variant_family"]),
                        "left_seed": int(pair["left_seed"]),
                        "right_seed": int(pair["right_seed"]),
                        "left_step": int(pair["left_step"]),
                        "right_step": int(pair["right_step"]),
                        "left_tail_step": left_tail_step,
                        "right_tail_step": right_tail_step,
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
    return outcome_rows, invalid_rows


def summarize_tail_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (checkpoint_label, target, tail_offset, variant), group in frame.groupby(
        ["checkpoint_label", "target", "tail_offset", "variant"],
        observed=True,
    ):
        finite_gap = group["margin_gap"].astype(float)
        finite_gap = finite_gap[np.isfinite(finite_gap)]
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "tail_offset": int(tail_offset),
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
            }
        )
    return summary_rows


def summarize_tail_proof_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    empty = {
        "best_tail_offset": -1,
        "best_tail_proof_candidate_count": 0,
        "best_tail_success_or_collision_or_completion_rows": 0,
        "best_tail_probe_seed_count": 0,
        "best_tail_obstacle_label_count": 0,
        "best_tail_target_count": 0,
        "best_tail_single_seed_share": 0.0,
        "best_tail_single_label_share": 0.0,
        "wrong_tail_once_total_proof_candidate_count": 0,
        "wrong_tail_once_total_event_rows": 0,
    }
    if not rows:
        return empty
    frame = pd.DataFrame(rows)
    tail = frame[frame["variant_family"].astype(str) == "wrong_tail_once"].copy()
    if tail.empty:
        return empty
    total_proof = tail[tail["proof_candidate"].astype(bool)]
    best: dict[str, Any] | None = None
    for tail_offset, group in tail.groupby("tail_offset", observed=True):
        proof = group[group["proof_candidate"].astype(bool)]
        count = int(len(proof))
        row = {
            "best_tail_offset": int(tail_offset),
            "best_tail_proof_candidate_count": count,
            "best_tail_success_or_collision_or_completion_rows": _event_count(proof),
            "best_tail_probe_seed_count": int(proof["probe_seed"].nunique()) if count else 0,
            "best_tail_obstacle_label_count": int(proof["left_obstacle_label"].nunique()) if count else 0,
            "best_tail_target_count": int(proof["target"].nunique()) if count else 0,
            "best_tail_single_seed_share": float(proof["probe_seed"].value_counts().max() / count) if count else 0.0,
            "best_tail_single_label_share": float(proof["left_obstacle_label"].value_counts().max() / count)
            if count
            else 0.0,
        }
        if best is None or row["best_tail_proof_candidate_count"] > best["best_tail_proof_candidate_count"]:
            best = row
    return {
        **empty,
        **(best or {}),
        "wrong_tail_once_total_proof_candidate_count": int(len(total_proof)),
        "wrong_tail_once_total_event_rows": _event_count(total_proof),
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


def run_tail_aligned_wrong_history_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    tail_offsets: tuple[int, ...],
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
    invalid_rows: list[dict[str, Any]] = []

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
            requests=tail_requested_snapshot_steps(checkpoint_pairs, tail_offsets=tail_offsets),
            device=resolved_device,
        )
        rows, invalid = build_tail_aligned_rows(
            pair_rows=checkpoint_pairs,
            snapshots=snapshots,
            model=model,
            env_config=env_config,
            response_dim=response_dim,
            tail_offsets=tail_offsets,
            max_continuation_steps=max_continuation_steps,
            min_margin_gap=min_margin_gap,
            device=resolved_device,
        )
        outcome_rows.extend(rows)
        invalid_rows.extend(invalid)

    summary_rows = summarize_tail_outcomes(outcome_rows)
    proof_summary = summarize_tail_proof_candidates(outcome_rows)
    write_csv_rows(run_dir / "tail_outcomes.csv", outcome_rows)
    write_csv_rows(run_dir / "tail_invalid_pairs.csv", invalid_rows)
    write_csv_rows(run_dir / "tail_variant_summary.csv", summary_rows)
    valid_tail_pair_count = int(len(outcome_rows) / len(TAIL_VARIANTS)) if outcome_rows else 0
    summary = {
        "run_type": "tail_aligned_wrong_history_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "tail_offsets": list(tail_offsets),
        "max_continuation_steps": int(max_continuation_steps),
        "min_margin_gap": float(min_margin_gap),
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "pair_label_mode": str(pair_label_mode),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "valid_tail_pair_count": valid_tail_pair_count,
        "invalid_tail_pair_count": int(len(invalid_rows)),
        "outcome_row_count": int(len(outcome_rows)),
        "tail_variant_summary_rows": int(len(summary_rows)),
        "tail_outcomes_csv": run_dir / "tail_outcomes.csv",
        "tail_invalid_pairs_csv": run_dir / "tail_invalid_pairs.csv",
        "tail_variant_summary_csv": run_dir / "tail_variant_summary.csv",
        **proof_summary,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tail-aligned one-shot wrong-history diagnostic gates.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--tail-offsets", type=parse_tail_offsets, default=(4, 8, 12, 16))
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=160)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="tail_aligned_wrong_history_gate")
    summary = run_tail_aligned_wrong_history_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        tail_offsets=tuple(args.tail_offsets),
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
