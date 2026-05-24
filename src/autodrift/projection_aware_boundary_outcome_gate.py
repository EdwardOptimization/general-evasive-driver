"""Projection-aware outcome gate for boundary mechanism proof rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import _pairs_for_checkpoint
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.natural_wrong_history_action_sensitive_selector import parse_env_config_map
from autodrift.obstacle_boundary_projection_miner import relocate_outcome_snapshot
from autodrift.tail_aligned_wrong_history_gate import _event_count, parse_tail_offsets
from autodrift.terminal_boundary_anchor_miner import _counts, _finite_float, _max_share
from autodrift.train_ppo import ActorCritic, resolve_device


PROJECTED_VARIANTS = (
    "normal_projected",
    "wrong_projected_once",
    "reset_projected",
    "zero_current_projected",
    "zero_action_history_projected",
)


def projection_tail_requested_snapshot_steps(pair_rows: pd.DataFrame, tail_offsets: tuple[int, ...]) -> dict[int, set[int]]:
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


def _projected_half_width(pair: pd.Series, left: OutcomeSnapshot) -> float | None:
    projected = _finite_float(pair.get("projected_obstacle_half_width"))
    if np.isfinite(projected):
        return float(projected)
    source_half_width = (
        float(left.env.obstacle_scenario.obstacle_half_width)
        if left.env.obstacle_scenario is not None
        else float("nan")
    )
    scale = _finite_float(pair.get("half_width_scale"), 1.0)
    if np.isfinite(source_half_width) and np.isfinite(scale):
        return float(source_half_width) * float(scale)
    return None


def build_projection_aware_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: Any,
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
                        "config": str(pair.get("config", "")),
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
            try:
                projected_left = relocate_outcome_snapshot(
                    left,
                    body_longitudinal=float(pair["projected_obstacle_body_x"]),
                    body_lateral=float(pair["projected_obstacle_body_y"]),
                    half_width=_projected_half_width(pair, left),
                )
            except ValueError as exc:
                invalid_rows.append(
                    {
                        "pair_id": int(pair_id),
                        "checkpoint_label": str(pair.get("checkpoint_label", "")),
                        "probe_seed": int(pair.get("probe_seed", -1)),
                        "config": str(pair.get("config", "")),
                        "target": str(pair["target"]),
                        "tail_offset": int(offset),
                        "left_seed": int(pair["left_seed"]),
                        "left_step": int(pair["left_step"]),
                        "left_tail_step": left_tail_step,
                        "invalid_reason": str(exc),
                    }
                )
                continue

            normal, normal_actions = replay_outcome_variant(
                model=model,
                snapshot=projected_left,
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
                "normal_projected": ("normal", None, "normal_projected"),
                "wrong_projected_once": ("wrong_matched_history", right.hidden, "wrong_projected_once"),
                "reset_projected": ("reset_hidden", None, "control_projected"),
                "zero_current_projected": ("zero_current_response", None, "control_projected"),
                "zero_action_history_projected": ("zero_action_history", None, "control_projected"),
            }
            variant_results: dict[str, dict[str, Any]] = {}
            for variant_name, (replay_variant, variant_hidden, variant_family) in replay_specs.items():
                if variant_name == "normal_projected":
                    result = dict(normal)
                else:
                    result, _ = replay_outcome_variant(
                        model=model,
                        snapshot=projected_left,
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
            for variant_name in PROJECTED_VARIANTS:
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
                        "config": str(pair.get("config", "")),
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
                        "target_z_delta": float(pair.get("target_z_delta", float("nan"))),
                        "visible_distance": float(pair.get("visible_distance", float("nan"))),
                        "projected_obstacle_bucket": str(pair.get("projected_obstacle_bucket", "")),
                        "projection_bucket": str(pair.get("projection_bucket", "")),
                        "projected_obstacle_label": str(pair.get("projected_obstacle_label", "")),
                        "proof_surface_type": str(pair.get("proof_surface_type", "")),
                        "projected_obstacle_body_x": float(pair["projected_obstacle_body_x"]),
                        "projected_obstacle_body_y": float(pair["projected_obstacle_body_y"]),
                        "projection_l2": float(pair.get("projection_l2", float("nan"))),
                        "half_width_delta_abs": float(pair.get("half_width_delta_abs", float("nan"))),
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
                        "relocated_obstacle_geometry_used": True,
                        **result,
                    }
                )
    return outcome_rows, invalid_rows


def summarize_projection_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                "proof_candidate_count": int(group["proof_candidate"].astype(bool).sum()),
                "event_row_count": _event_count(group[group["proof_candidate"].astype(bool)]),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "collision_gap_count": int(group["collision_gap"].astype(bool).sum()),
                "obstacle_completion_drop_count": int(group["obstacle_completion_drop"].astype(bool).sum()),
                "proof_margin_gap_count": int(group["proof_margin_gap"].astype(bool).sum()),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "variant_margin_mean": float(group["variant_margin"].astype(float).mean()),
                "margin_gap_mean": float(finite_gap.mean()) if len(finite_gap) else None,
                "margin_gap_p90": float(finite_gap.quantile(0.90)) if len(finite_gap) else None,
                "margin_gap_max": float(finite_gap.max()) if len(finite_gap) else None,
                "first_action_distance_mean": float(group["first_action_distance"].astype(float).mean()),
                "first_action_distance_p90": float(group["first_action_distance"].astype(float).quantile(0.90)),
                "trajectory_distance_mean": float(group["action_trajectory_distance_mean"].astype(float).mean()),
                "trajectory_distance_p90": float(
                    group["action_trajectory_distance_mean"].astype(float).quantile(0.90)
                ),
            }
        )
    return summary_rows


def _variant_proof(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[(frame["variant"].astype(str) == variant) & frame["proof_candidate"].astype(bool)].copy()


def classify_projection_outcome(rows: list[dict[str, Any]], invalid_count: int, *, input_pair_count: int) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {
            "classification": "invalid_projection_replay",
            "wrong_projected_once_total_proof_candidate_count": 0,
            "wrong_projected_once_total_event_rows": 0,
            "control_total_proof_candidate_count": 0,
            "control_total_event_rows": 0,
        }
    wrong = _variant_proof(frame, "wrong_projected_once")
    controls = frame[
        frame["variant"].astype(str).isin(
            ["reset_projected", "zero_current_projected", "zero_action_history_projected"]
        )
        & frame["proof_candidate"].astype(bool)
    ].copy()
    wrong_event_rows = _event_count(wrong)
    control_event_rows = _event_count(controls)
    wrong_first_action = frame[frame["variant"].astype(str) == "wrong_projected_once"][
        "first_action_distance"
    ].astype(float)
    wrong_trajectory = frame[frame["variant"].astype(str) == "wrong_projected_once"][
        "action_trajectory_distance_mean"
    ].astype(float)
    if invalid_count > max(10, input_pair_count):
        classification = "invalid_projection_replay"
    elif wrong_event_rows > 0:
        classification = "positive_projected_wrong_history_outcome_proof"
    elif len(wrong) > 0:
        classification = "margin_only_projected_history_signal"
    elif len(controls) > 0:
        classification = "control_only_projected_sensitivity"
    elif (
        len(wrong_first_action)
        and float(wrong_first_action.mean()) >= 0.02
        and float(wrong_trajectory.mean()) >= 0.02
    ):
        classification = "fast_correction_no_effect"
    else:
        classification = "projected_wrong_history_no_effect"
    return {
        "classification": classification,
        "wrong_projected_once_total_proof_candidate_count": int(len(wrong)),
        "wrong_projected_once_total_event_rows": int(wrong_event_rows),
        "wrong_projected_once_probe_seed_count": (
            int(wrong["probe_seed"].nunique()) if "probe_seed" in wrong else 0
        ),
        "wrong_projected_once_target_count": int(wrong["target"].nunique()) if "target" in wrong else 0,
        "wrong_projected_once_config_count": int(wrong["config"].nunique()) if "config" in wrong else 0,
        "wrong_projected_once_obstacle_bucket_count": (
            int(wrong["projected_obstacle_bucket"].nunique()) if "projected_obstacle_bucket" in wrong else 0
        ),
        "wrong_projected_once_projection_bucket_count": (
            int(wrong["projection_bucket"].nunique()) if "projection_bucket" in wrong else 0
        ),
        "wrong_projected_once_single_seed_share": _max_share(wrong, "probe_seed"),
        "wrong_projected_once_single_target_share": _max_share(wrong, "target"),
        "wrong_projected_once_single_obstacle_bucket_share": _max_share(wrong, "projected_obstacle_bucket"),
        "wrong_projected_once_single_projection_bucket_share": _max_share(wrong, "projection_bucket"),
        "control_total_proof_candidate_count": int(len(controls)),
        "control_total_event_rows": int(control_event_rows),
        "control_by_variant": _counts(controls, "variant"),
    }


def _limit_pairs(frame: pd.DataFrame, max_pairs_per_checkpoint_target: int) -> pd.DataFrame:
    if max_pairs_per_checkpoint_target <= 0:
        return frame.copy()
    selected: list[pd.DataFrame] = []
    for _, group in frame.groupby(["checkpoint_label", "target"], observed=True):
        selected.append(group.head(int(max_pairs_per_checkpoint_target)).copy())
    if not selected:
        return frame.head(0).copy()
    return pd.concat(selected, ignore_index=True)


def run_projection_aware_boundary_outcome_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_map: dict[str, Path],
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
        for config_name, config_pairs in checkpoint_pairs.groupby("config", observed=True):
            env_config = load_env_config(env_config_map[str(config_name)])
            snapshots = collect_requested_outcome_snapshots(
                model=model,
                env_config=env_config,
                requests=projection_tail_requested_snapshot_steps(config_pairs, tail_offsets=tail_offsets),
                device=resolved_device,
            )
            rows, invalid = build_projection_aware_rows(
                pair_rows=config_pairs,
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

    summary_rows = summarize_projection_outcomes(outcome_rows)
    valid_tail_pair_count = int(len(outcome_rows) / len(PROJECTED_VARIANTS)) if outcome_rows else 0
    classification = classify_projection_outcome(
        outcome_rows,
        len(invalid_rows),
        input_pair_count=int(len(pair_frame)),
    )
    write_csv_rows(run_dir / "projected_outcomes.csv", outcome_rows)
    write_csv_rows(run_dir / "projected_invalid_pairs.csv", invalid_rows)
    write_csv_rows(run_dir / "projected_variant_summary.csv", summary_rows)
    summary = {
        "run_type": "projection_aware_boundary_outcome_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config_map": env_config_map,
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
        "projected_variant_summary_rows": int(len(summary_rows)),
        "projected_outcomes_csv": run_dir / "projected_outcomes.csv",
        "projected_invalid_pairs_csv": run_dir / "projected_invalid_pairs.csv",
        "projected_variant_summary_csv": run_dir / "projected_variant_summary.csv",
        "relocated_obstacle_geometry_used": bool(outcome_rows)
        and all(bool(row.get("relocated_obstacle_geometry_used", False)) for row in outcome_rows),
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
        **classification,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run projection-aware boundary outcome gates.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config-map", action="append", type=parse_env_config_map, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--tail-offsets", type=parse_tail_offsets, default=(0, 2, 4, 8))
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=80)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="projection_aware_boundary_outcome_gate")
    summary = run_projection_aware_boundary_outcome_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_map=dict(args.env_config_map),
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
