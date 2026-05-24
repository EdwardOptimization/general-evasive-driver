"""Mine wrong-history rows from normal-success near-boundary source windows."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.action_critical_wrong_history_source_miner import (
    BankSnapshot,
    SurfaceSeedRange,
    candidate_pairs_for_bank,
    obstacle_xy_from_observation,
    parse_surface_seed_range,
    response_context_vector,
    scene_context_vector,
    score_action_critical_pair,
)
from autodrift.action_divergent_wrong_history_corpus import (
    _assign_splits,
    _candidate_distribution_summary,
    _max_share,
    _summary_rows,
    write_action_divergent_corpus,
)
from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    _finite_float,
    _hidden_array,
    parse_surface_config,
    source_diversity_weights,
)
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, replay_outcome_variant
from autodrift.sequence_target_miner import parse_int_list
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device


def select_evenly_by_step(snapshots: list[BankSnapshot], limit: int) -> list[BankSnapshot]:
    if int(limit) <= 0 or len(snapshots) <= int(limit):
        return list(snapshots)
    ordered = sorted(snapshots, key=lambda item: int(item.snapshot.step))
    indices = np.linspace(0, len(ordered) - 1, int(limit), dtype=int)
    return [ordered[int(index)] for index in indices]


def collect_wide_snapshot_bank(
    *,
    model: ActorCritic,
    surface: str,
    env_config: DriftEnvConfig,
    start_seed: int,
    end_seed: int,
    obstacle_distance_min: float,
    obstacle_distance_max: float,
    max_snapshots_per_surface: int,
    max_snapshots_per_seed: int,
    sample_stride: int,
    device: torch.device,
) -> list[BankSnapshot]:
    if not model.is_online_recurrent:
        raise ValueError("normal-success boundary source mining requires an online recurrent checkpoint")
    env = AutoDriftEnv(env_config)
    snapshots: list[BankSnapshot] = []
    try:
        for seed in range(int(start_seed), int(end_seed) + 1):
            obs, info = env.reset(seed=int(seed))
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            seed_candidates: list[BankSnapshot] = []
            while not (terminated or truncated):
                step = int(env.step_count)
                obstacle_distance = _finite_float(info.get("obstacle_distance"))
                if (
                    step % max(int(sample_stride), 1) == 0
                    and bool(info.get("obstacle_perception_visible", False))
                    and np.isfinite(obstacle_distance)
                    and float(obstacle_distance_min) <= obstacle_distance <= float(obstacle_distance_max)
                ):
                    obstacle_x_m, obstacle_y_m = obstacle_xy_from_observation(obs)
                    if np.isfinite(obstacle_x_m) and np.isfinite(obstacle_y_m):
                        action, _ = deterministic_action_from_hidden(
                            model,
                            np.asarray(obs, dtype=np.float32),
                            hidden,
                            device,
                        )
                        label = str(info.get("obstacle_label", "") or "unknown_obstacle")
                        seed_candidates.append(
                            BankSnapshot(
                                snapshot=OutcomeSnapshot(
                                    seed=int(seed),
                                    step=step,
                                    observation=np.asarray(obs, dtype=np.float32).copy(),
                                    hidden=hidden.detach().clone(),
                                    env=copy.deepcopy(env),
                                    info=dict(info),
                                ),
                                surface=str(surface),
                                target=label,
                                obstacle_x_m=float(obstacle_x_m),
                                obstacle_y_m=float(obstacle_y_m),
                                obstacle_distance=float(obstacle_distance),
                                scene_context=scene_context_vector(obs),
                                response_context=response_context_vector(obs),
                                hidden_flat=_hidden_array(hidden),
                                normal_first_action=np.asarray(action, dtype=np.float32).copy(),
                            )
                        )
                action, next_hidden = deterministic_action_from_hidden(
                    model,
                    np.asarray(obs, dtype=np.float32),
                    hidden,
                    device,
                )
                obs, _, terminated, truncated, info = env.step(action)
                hidden = next_hidden
            snapshots.extend(select_evenly_by_step(seed_candidates, max_snapshots_per_seed))
            if max_snapshots_per_surface > 0 and len(snapshots) >= int(max_snapshots_per_surface):
                snapshots = snapshots[: int(max_snapshots_per_surface)]
                break
    finally:
        env.close()
    return snapshots


def classify_normal_window(
    *,
    normal_success: bool,
    normal_margin: float,
    normal_margin_min: float,
    normal_margin_max: float,
) -> str:
    if bool(normal_success) and np.isfinite(normal_margin):
        if float(normal_margin_min) <= float(normal_margin) <= float(normal_margin_max):
            return "near_boundary_preferred"
        if float(normal_margin) > float(normal_margin_max):
            return "early_safe_diagnostic"
    return "already_failed_diagnostic"


def normal_prepass_rows(
    *,
    snapshots: list[BankSnapshot],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    normal_margin_min: float,
    normal_margin_max: float,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[BankSnapshot]]:
    rows: list[dict[str, Any]] = []
    near_boundary: list[BankSnapshot] = []
    for index, snapshot in enumerate(snapshots):
        normal, _ = replay_outcome_variant(
            model=model,
            snapshot=snapshot.snapshot,
            env_config=env_config,
            variant="normal",
            response_dim=response_dim,
            variant_hidden=None,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        normal_margin = _finite_float(normal.get("min_clearance_margin"))
        normal_success = bool(normal.get("success", False))
        window_class = classify_normal_window(
            normal_success=normal_success,
            normal_margin=normal_margin,
            normal_margin_min=normal_margin_min,
            normal_margin_max=normal_margin_max,
        )
        if window_class == "near_boundary_preferred":
            near_boundary.append(snapshot)
        rows.append(
            {
                "snapshot_index": int(index),
                "surface": snapshot.surface,
                "target": snapshot.target,
                "seed": int(snapshot.snapshot.seed),
                "step": int(snapshot.snapshot.step),
                "obstacle_distance": float(snapshot.obstacle_distance),
                "obstacle_x_m": float(snapshot.obstacle_x_m),
                "obstacle_y_m": float(snapshot.obstacle_y_m),
                "normal_success": normal_success,
                "normal_collision": bool(normal.get("collision", False)),
                "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                "normal_margin": normal_margin,
                "window_class": window_class,
            }
        )
    return rows, near_boundary


def candidate_pairs_for_lefts(
    left_snapshots: list[BankSnapshot],
    right_snapshots: list[BankSnapshot],
    *,
    max_right_candidates_per_left: int,
    max_candidate_pairs: int,
    context_distance_threshold: float,
    response_distance_threshold: float,
    obstacle_x_abs_delta: float,
    obstacle_y_abs_delta: float,
    step_abs_delta: int,
) -> list[tuple[BankSnapshot, BankSnapshot, dict[str, float]]]:
    if not left_snapshots:
        return []
    left_keys = {(item.surface, item.snapshot.seed, item.snapshot.step) for item in left_snapshots}
    combined = list(left_snapshots) + [
        item
        for item in right_snapshots
        if (item.surface, item.snapshot.seed, item.snapshot.step) not in left_keys
    ]
    all_pairs = candidate_pairs_for_bank(
        combined,
        max_right_candidates_per_left=max_right_candidates_per_left,
        context_distance_threshold=context_distance_threshold,
        response_distance_threshold=response_distance_threshold,
        obstacle_x_abs_delta=obstacle_x_abs_delta,
        obstacle_y_abs_delta=obstacle_y_abs_delta,
        step_abs_delta=step_abs_delta,
    )
    filtered = [
        (left, right, metrics)
        for left, right, metrics in all_pairs
        if (left.surface, left.snapshot.seed, left.snapshot.step) in left_keys
    ]
    if max_candidate_pairs > 0:
        filtered = filtered[: int(max_candidate_pairs)]
    return filtered


def _window_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summaries: list[dict[str, Any]] = []
    for (surface, window_class), group in frame.groupby(["surface", "window_class"], observed=True):
        summaries.append(
            {
                "surface": surface,
                "window_class": window_class,
                "rows": int(len(group)),
                "seeds": int(group["seed"].nunique()),
                "targets": int(group["target"].nunique()),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "obstacle_distance_mean": float(group["obstacle_distance"].astype(float).mean()),
            }
        )
    return summaries


def _snapshot_bank_summary(snapshots_by_surface: dict[str, list[BankSnapshot]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for surface, snapshots in sorted(snapshots_by_surface.items()):
        frame = pd.DataFrame(
            [
                {
                    "surface": item.surface,
                    "seed": item.snapshot.seed,
                    "step": item.snapshot.step,
                    "target": item.target,
                    "obstacle_distance": item.obstacle_distance,
                }
                for item in snapshots
            ]
        )
        if frame.empty:
            rows.append({"surface": surface, "snapshots": 0, "seeds": 0, "targets": 0})
            continue
        rows.append(
            {
                "surface": surface,
                "snapshots": int(len(frame)),
                "seeds": int(frame["seed"].nunique()),
                "targets": int(frame["target"].nunique()),
                "obstacle_distance_min": float(frame["obstacle_distance"].min()),
                "obstacle_distance_mean": float(frame["obstacle_distance"].mean()),
                "obstacle_distance_max": float(frame["obstacle_distance"].max()),
            }
        )
    return rows


def _merge_corpus(dst: dict[str, list[np.ndarray]], src: dict[str, list[np.ndarray]]) -> None:
    for key, values in src.items():
        dst[key].extend(values)


def run_normal_success_boundary_source_miner(
    *,
    checkpoint_path: Path,
    surface_configs: dict[str, Path],
    surface_seed_ranges: dict[str, SurfaceSeedRange],
    sequence_lengths: tuple[int, ...],
    obstacle_distance_min: float,
    obstacle_distance_max: float,
    normal_margin_min: float,
    normal_margin_max: float,
    max_right_candidates_per_left: int,
    max_candidate_pairs_per_surface: int,
    context_distance_threshold: float,
    response_distance_threshold: float,
    obstacle_x_abs_delta: float,
    obstacle_y_abs_delta: float,
    step_abs_delta: int,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
    max_snapshots_per_surface: int,
    max_snapshots_per_seed: int,
    sample_stride: int,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    freeze_actor(model)
    before_checksum = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    max_len = max(int(length) for length in sequence_lengths)

    snapshots_by_surface: dict[str, list[BankSnapshot]] = {}
    normal_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observation": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "preferred_action_sequence": [],
        "rejected_action_sequence": [],
        "normal_base_action_sequence": [],
        "variant_base_action_sequence": [],
    }
    source_index = 0
    pair_count = 0
    near_boundary_count = 0
    for surface, config_path in sorted(surface_configs.items()):
        seed_range = surface_seed_ranges[surface]
        env_config = load_env_config(config_path)
        snapshots = collect_wide_snapshot_bank(
            model=model,
            surface=surface,
            env_config=env_config,
            start_seed=seed_range.start_seed,
            end_seed=seed_range.end_seed,
            obstacle_distance_min=obstacle_distance_min,
            obstacle_distance_max=obstacle_distance_max,
            max_snapshots_per_surface=max_snapshots_per_surface,
            max_snapshots_per_seed=max_snapshots_per_seed,
            sample_stride=sample_stride,
            device=resolved_device,
        )
        snapshots_by_surface[surface] = snapshots
        surface_normal_rows, near_boundary = normal_prepass_rows(
            snapshots=snapshots,
            model=model,
            env_config=env_config,
            response_dim=response_dim,
            normal_margin_min=normal_margin_min,
            normal_margin_max=normal_margin_max,
            max_continuation_steps=max(int(max_continuation_steps), max_len),
            device=resolved_device,
        )
        normal_rows.extend(surface_normal_rows)
        near_boundary_count += len(near_boundary)
        pairs = candidate_pairs_for_lefts(
            near_boundary,
            snapshots,
            max_right_candidates_per_left=max_right_candidates_per_left,
            max_candidate_pairs=max_candidate_pairs_per_surface,
            context_distance_threshold=context_distance_threshold,
            response_distance_threshold=response_distance_threshold,
            obstacle_x_abs_delta=obstacle_x_abs_delta,
            obstacle_y_abs_delta=obstacle_y_abs_delta,
            step_abs_delta=step_abs_delta,
        )
        for left, right, pair_metrics in pairs:
            rows, row_corpus = score_action_critical_pair(
                source_index=source_index,
                left=left,
                right=right,
                pair_metrics=pair_metrics,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                sequence_lengths=sequence_lengths,
                max_continuation_steps=max(int(max_continuation_steps), max_len),
                min_wrong_first_action_l2=min_wrong_first_action_l2,
                min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
                min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
                min_margin_gap=min_margin_gap,
                device=resolved_device,
            )
            candidate_rows.extend(rows)
            _merge_corpus(corpus, row_corpus)
            accepted_rows.extend([row for row in rows if bool(row["accepted"])])
            pair_count += 1
            source_index += 1

    _assign_splits(accepted_rows)
    weights = source_diversity_weights(accepted_rows)
    for row in accepted_rows:
        row["weight"] = float(weights.get(int(row["source_index"]), 1.0))

    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    candidate_summary = _candidate_distribution_summary(
        candidate_frame,
        min_wrong_first_action_l2=min_wrong_first_action_l2,
        min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
        min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
        min_margin_gap=min_margin_gap,
    )

    write_csv_rows(run_dir / "snapshot_bank_summary.csv", _snapshot_bank_summary(snapshots_by_surface))
    write_csv_rows(run_dir / "normal_window_summary.csv", _window_summary(normal_rows))
    write_csv_rows(run_dir / "normal_window_rows.csv", normal_rows)
    write_csv_rows(run_dir / "candidate_scores.csv", candidate_rows)
    write_csv_rows(run_dir / "normal_success_boundary_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "source_summary.csv", _summary_rows(accepted_frame, "source_index"))
    write_csv_rows(run_dir / "split_summary.csv", _summary_rows(accepted_frame, "split"))
    write_csv_rows(run_dir / "target_summary.csv", _summary_rows(accepted_frame, "target"))
    write_action_divergent_corpus(
        output_npz=run_dir / "normal_success_boundary_corpus.npz",
        rows=accepted_rows,
        corpus=corpus,
        obs_dim=int(model.obs_dim),
        hidden_dim=int(model.actor_mean.in_features),
        max_sequence_length=max_len,
    )
    after_checksum = model_parameter_checksum(model)

    accepted_count = int(len(accepted_frame))
    physical_pairs = int(accepted_frame["physical_pair_key"].nunique()) if accepted_count else 0
    left_seeds = int(accepted_frame["left_seed"].nunique()) if accepted_count else 0
    right_seeds = int(accepted_frame["right_seed"].nunique()) if accepted_count else 0
    heldout_nonempty = bool(accepted_count and (accepted_frame["split"] == "source_holdout_validation").any())
    mean_action_l2 = (
        float(accepted_frame["preferred_vs_rejected_action_mean_l2"].mean()) if accepted_count else float("nan")
    )
    mean_margin_gap = float(accepted_frame["margin_gap"].mean()) if accepted_count else float("nan")
    success_drop_rate = float(accepted_frame["success_drop"].astype(bool).mean()) if accepted_count else float("nan")
    corpus_passed = bool(
        near_boundary_count >= 40
        and accepted_count >= 40
        and physical_pairs >= 8
        and left_seeds >= 6
        and right_seeds >= 6
        and heldout_nonempty
        and np.isfinite(mean_action_l2)
        and mean_action_l2 >= 0.010
        and (
            (np.isfinite(mean_margin_gap) and mean_margin_gap >= 0.010)
            or (np.isfinite(success_drop_rate) and success_drop_rate >= 0.25)
        )
        and before_checksum == after_checksum
    )
    normal_frame = pd.DataFrame(normal_rows)
    window_counts = (
        {str(key): int(value) for key, value in normal_frame["window_class"].value_counts().to_dict().items()}
        if not normal_frame.empty
        else {}
    )
    summary = {
        "run_type": "normal_success_boundary_source_miner",
        "checkpoint": checkpoint_path,
        "surface_configs": surface_configs,
        "surface_seed_ranges": {
            key: {"start_seed": item.start_seed, "end_seed": item.end_seed}
            for key, item in surface_seed_ranges.items()
        },
        "sequence_lengths": sequence_lengths,
        "snapshot_count": int(sum(len(items) for items in snapshots_by_surface.values())),
        "snapshots_by_surface": {key: int(len(items)) for key, items in snapshots_by_surface.items()},
        "window_counts": window_counts,
        "near_boundary_preferred_snapshots": int(near_boundary_count),
        "candidate_pairs": int(pair_count),
        "candidate_rows": int(len(candidate_frame)),
        "accepted_rows": accepted_count,
        "accepted_physical_pairs": physical_pairs,
        "accepted_left_seeds": left_seeds,
        "accepted_right_seeds": right_seeds,
        "source_holdout_nonempty": heldout_nonempty,
        "max_physical_pair_share": _max_share(accepted_frame, "physical_pair_key"),
        "max_left_seed_share": _max_share(accepted_frame, "left_seed"),
        "max_source_index_share": _max_share(accepted_frame, "source_index"),
        "mean_preferred_vs_rejected_action_mean_l2": mean_action_l2,
        "mean_margin_gap": mean_margin_gap,
        "accepted_success_drop_rate": success_drop_rate,
        "obstacle_distance_min": float(obstacle_distance_min),
        "obstacle_distance_max": float(obstacle_distance_max),
        "normal_margin_min": float(normal_margin_min),
        "normal_margin_max": float(normal_margin_max),
        "min_wrong_first_action_l2": float(min_wrong_first_action_l2),
        "min_wrong_action_sequence_mean_l2": float(min_wrong_action_sequence_mean_l2),
        "min_preferred_rejected_action_mean_l2": float(min_preferred_rejected_action_mean_l2),
        "min_margin_gap": float(min_margin_gap),
        **candidate_summary,
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "actor_checkpoint_written": False,
        "corpus_passed": corpus_passed,
        "snapshot_bank_summary_csv": run_dir / "snapshot_bank_summary.csv",
        "normal_window_summary_csv": run_dir / "normal_window_summary.csv",
        "normal_window_rows_csv": run_dir / "normal_window_rows.csv",
        "candidate_scores_csv": run_dir / "candidate_scores.csv",
        "normal_success_boundary_rows_csv": run_dir / "normal_success_boundary_rows.csv",
        "normal_success_boundary_corpus_npz": run_dir / "normal_success_boundary_corpus.npz",
        "source_summary_csv": run_dir / "source_summary.csv",
        "split_summary_csv": run_dir / "split_summary.csv",
        "target_summary_csv": run_dir / "target_summary.csv",
        "diagnostic_only": True,
        "training_started": False,
        "optimizer_started": False,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine normal-success boundary wrong-history rows without training.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--surface-seed-range", type=parse_surface_seed_range, action="append", required=True)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(5, 7, 9))
    parser.add_argument("--obstacle-distance-min", type=float, default=0.0)
    parser.add_argument("--obstacle-distance-max", type=float, default=35.0)
    parser.add_argument("--normal-margin-min", type=float, default=0.0)
    parser.add_argument("--normal-margin-max", type=float, default=1.0)
    parser.add_argument("--max-right-candidates-per-left", type=int, default=64)
    parser.add_argument("--max-candidate-pairs-per-surface", type=int, default=1600)
    parser.add_argument("--context-distance-threshold", type=float, default=0.25)
    parser.add_argument("--response-distance-threshold", type=float, default=0.20)
    parser.add_argument("--obstacle-x-abs-delta", type=float, default=10.0)
    parser.add_argument("--obstacle-y-abs-delta", type=float, default=2.0)
    parser.add_argument("--step-abs-delta", type=int, default=30)
    parser.add_argument("--min-wrong-first-action-l2", type=float, default=0.002)
    parser.add_argument("--min-wrong-action-sequence-mean-l2", type=float, default=0.006)
    parser.add_argument("--min-preferred-rejected-action-mean-l2", type=float, default=0.010)
    parser.add_argument("--min-margin-gap", type=float, default=0.010)
    parser.add_argument("--max-snapshots-per-surface", type=int, default=480)
    parser.add_argument("--max-snapshots-per-seed", type=int, default=8)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-continuation-steps", type=int, default=9)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="normal_success_boundary_source_miner")
    summary = run_normal_success_boundary_source_miner(
        checkpoint_path=args.checkpoint,
        surface_configs={item.surface: item.env_config_path for item in args.surface_config},
        surface_seed_ranges={item.surface: item for item in args.surface_seed_range},
        sequence_lengths=args.sequence_lengths,
        obstacle_distance_min=args.obstacle_distance_min,
        obstacle_distance_max=args.obstacle_distance_max,
        normal_margin_min=args.normal_margin_min,
        normal_margin_max=args.normal_margin_max,
        max_right_candidates_per_left=args.max_right_candidates_per_left,
        max_candidate_pairs_per_surface=args.max_candidate_pairs_per_surface,
        context_distance_threshold=args.context_distance_threshold,
        response_distance_threshold=args.response_distance_threshold,
        obstacle_x_abs_delta=args.obstacle_x_abs_delta,
        obstacle_y_abs_delta=args.obstacle_y_abs_delta,
        step_abs_delta=args.step_abs_delta,
        min_wrong_first_action_l2=args.min_wrong_first_action_l2,
        min_wrong_action_sequence_mean_l2=args.min_wrong_action_sequence_mean_l2,
        min_preferred_rejected_action_mean_l2=args.min_preferred_rejected_action_mean_l2,
        min_margin_gap=args.min_margin_gap,
        max_snapshots_per_surface=args.max_snapshots_per_surface,
        max_snapshots_per_seed=args.max_snapshots_per_seed,
        sample_stride=args.sample_stride,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(f"run_dir={run_dir}")
    print(f"corpus_passed={summary['corpus_passed']}")
    print(f"accepted_rows={summary['accepted_rows']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
