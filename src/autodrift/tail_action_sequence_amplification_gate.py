"""Tail-aligned diagnostic action-sequence amplification gate."""

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
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.persistent_wrong_history_intervention_gate import PersistentVariantSpec, replay_persistent_variant
from autodrift.tail_aligned_wrong_history_gate import _event_count, parse_tail_offsets, tail_requested_snapshot_steps
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_HOLD_STEPS = (2, 4, 8, 12)


def parse_hold_steps(value: str) -> tuple[int, ...]:
    steps = tuple(int(part.strip()) for part in str(value).split(",") if part.strip())
    if not steps:
        raise ValueError("at least one hold step is required")
    if any(step <= 0 for step in steps):
        raise ValueError("hold steps must be positive")
    return tuple(dict.fromkeys(steps))


def tail_amplification_variant_specs(
    hold_steps: tuple[int, ...] = DEFAULT_HOLD_STEPS,
) -> tuple[PersistentVariantSpec, ...]:
    return (
        PersistentVariantSpec(name="normal", family="baseline"),
        PersistentVariantSpec(name="wrong_tail_once", family="wrong_tail_once", injection_start_step=0, hold_steps=1),
        PersistentVariantSpec(name="reset_tail", family="baseline", reset_hidden=True),
        PersistentVariantSpec(name="zero_current_tail", family="baseline", zero_current_response=True),
        *(
            PersistentVariantSpec(
                name=f"wrong_tail_hidden_hold_{int(step)}",
                family="wrong_tail_hidden_hold",
                injection_start_step=0,
                hold_steps=int(step),
                clamp_hidden=True,
            )
            for step in hold_steps
        ),
    )


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _variant_output_name(spec: PersistentVariantSpec) -> str:
    return "normal_tail" if spec.name == "normal" else spec.name


def build_tail_action_sequence_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    tail_offsets: tuple[int, ...],
    hold_steps: tuple[int, ...],
    max_continuation_steps: int,
    min_margin_gap: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = tail_amplification_variant_specs(hold_steps)
    normal_spec = specs[0]
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
            normal = dict(normal)
            normal["variant"] = "normal_tail"
            normal["variant_family"] = "baseline"
            normal_first_action = np.asarray(
                [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                dtype=np.float32,
            )

            variant_results: dict[str, dict[str, Any]] = {"normal_tail": normal}
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
                result = dict(result)
                result["variant"] = _variant_output_name(spec)
                variant_results[result["variant"]] = result

            normal_margin = float(normal.get("min_clearance_margin", float("nan")))
            normal_success = bool(normal.get("success", False))
            normal_collision = bool(normal.get("collision", False))
            normal_completed = bool(normal.get("obstacle_completed", False))
            for spec in specs:
                variant_name = _variant_output_name(spec)
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


def summarize_amplification_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                "hold_steps": int(group["hold_steps"].iloc[0]),
                "pair_count": int(len(group)),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "collision_gap_count": int(group["collision_gap"].astype(bool).sum()),
                "completion_drop_count": int(group["obstacle_completion_drop"].astype(bool).sum()),
                "event_count": _event_count(group),
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


def summarize_amplification_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    empty = {
        "wrong_tail_once_total_proof_candidate_count": 0,
        "wrong_tail_once_total_event_rows": 0,
        "hidden_hold_total_proof_candidate_count": 0,
        "hidden_hold_total_event_rows": 0,
        "best_hidden_hold_variant": "",
        "best_hidden_hold_proof_candidate_count": 0,
        "best_hidden_hold_event_rows": 0,
        "best_hidden_hold_probe_seed_count": 0,
        "best_hidden_hold_obstacle_label_count": 0,
        "best_hidden_hold_target_count": 0,
        "best_hidden_hold_single_seed_share": 0.0,
        "best_hidden_hold_single_label_share": 0.0,
        "control_proof_candidate_count": 0,
        "control_event_rows": 0,
    }
    if not rows:
        return empty
    frame = pd.DataFrame(rows)
    proof = frame[frame["proof_candidate"].astype(bool)].copy()
    wrong_once = proof[proof["variant_family"].astype(str) == "wrong_tail_once"]
    hidden = proof[proof["variant_family"].astype(str) == "wrong_tail_hidden_hold"]
    controls = proof[proof["variant"].astype(str).isin(["reset_tail", "zero_current_tail"])]

    best: dict[str, Any] | None = None
    hidden_rows = frame[frame["variant_family"].astype(str) == "wrong_tail_hidden_hold"]
    for variant, group in hidden_rows.groupby("variant", observed=True):
        variant_proof = group[group["proof_candidate"].astype(bool)]
        count = int(len(variant_proof))
        events = _event_count(variant_proof)
        row = {
            "best_hidden_hold_variant": str(variant),
            "best_hidden_hold_proof_candidate_count": count,
            "best_hidden_hold_event_rows": events,
            "best_hidden_hold_probe_seed_count": int(variant_proof["probe_seed"].nunique()) if count else 0,
            "best_hidden_hold_obstacle_label_count": int(variant_proof["left_obstacle_label"].nunique()) if count else 0,
            "best_hidden_hold_target_count": int(variant_proof["target"].nunique()) if count else 0,
            "best_hidden_hold_single_seed_share": float(variant_proof["probe_seed"].value_counts().max() / count)
            if count
            else 0.0,
            "best_hidden_hold_single_label_share": float(
                variant_proof["left_obstacle_label"].value_counts().max() / count
            )
            if count
            else 0.0,
        }
        if best is None or (row["best_hidden_hold_event_rows"], row["best_hidden_hold_proof_candidate_count"]) > (
            best["best_hidden_hold_event_rows"],
            best["best_hidden_hold_proof_candidate_count"],
        ):
            best = row

    return {
        **empty,
        **(best or {}),
        "wrong_tail_once_total_proof_candidate_count": int(len(wrong_once)),
        "wrong_tail_once_total_event_rows": _event_count(wrong_once),
        "hidden_hold_total_proof_candidate_count": int(len(hidden)),
        "hidden_hold_total_event_rows": _event_count(hidden),
        "control_proof_candidate_count": int(len(controls)),
        "control_event_rows": _event_count(controls),
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


def run_tail_action_sequence_amplification_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    tail_offsets: tuple[int, ...],
    hold_steps: tuple[int, ...],
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
    variant_count = len(tail_amplification_variant_specs(hold_steps))

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
        rows, invalid = build_tail_action_sequence_rows(
            pair_rows=checkpoint_pairs,
            snapshots=snapshots,
            model=model,
            env_config=env_config,
            response_dim=response_dim,
            tail_offsets=tail_offsets,
            hold_steps=hold_steps,
            max_continuation_steps=max_continuation_steps,
            min_margin_gap=min_margin_gap,
            device=resolved_device,
        )
        outcome_rows.extend(rows)
        invalid_rows.extend(invalid)

    summary_rows = summarize_amplification_outcomes(outcome_rows)
    proof_summary = summarize_amplification_proof(outcome_rows)
    write_csv_rows(run_dir / "tail_amplification_outcomes.csv", outcome_rows)
    write_csv_rows(run_dir / "tail_amplification_invalid_pairs.csv", invalid_rows)
    write_csv_rows(run_dir / "tail_amplification_variant_summary.csv", summary_rows)
    valid_tail_pair_count = int(len(outcome_rows) / variant_count) if outcome_rows else 0
    summary = {
        "run_type": "tail_action_sequence_amplification_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "tail_offsets": list(tail_offsets),
        "hold_steps": list(hold_steps),
        "variant_count": int(variant_count),
        "max_continuation_steps": int(max_continuation_steps),
        "min_margin_gap": float(min_margin_gap),
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "pair_label_mode": str(pair_label_mode),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "valid_tail_pair_count": valid_tail_pair_count,
        "invalid_tail_pair_count": int(len(invalid_rows)),
        "outcome_row_count": int(len(outcome_rows)),
        "tail_amplification_variant_summary_rows": int(len(summary_rows)),
        "tail_amplification_outcomes_csv": run_dir / "tail_amplification_outcomes.csv",
        "tail_amplification_invalid_pairs_csv": run_dir / "tail_amplification_invalid_pairs.csv",
        "tail_amplification_variant_summary_csv": run_dir / "tail_amplification_variant_summary.csv",
        **proof_summary,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tail action-sequence amplification diagnostic gates.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--tail-offsets", type=parse_tail_offsets, default=DEFAULT_HOLD_STEPS)
    parser.add_argument("--hold-steps", type=parse_hold_steps, default=DEFAULT_HOLD_STEPS)
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=160)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="tail_action_sequence_amplification_gate")
    summary = run_tail_action_sequence_amplification_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        tail_offsets=tuple(args.tail_offsets),
        hold_steps=tuple(args.hold_steps),
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
