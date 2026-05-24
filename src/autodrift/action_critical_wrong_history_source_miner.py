"""Mine action/outcome-critical wrong-history source rows."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.action_divergent_wrong_history_corpus import (
    _assign_splits,
    _candidate_distribution_summary,
    _max_share,
    _summary_rows,
    action_sequence_distance,
    action_sequence_prefix,
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
    risk_score,
    source_diversity_weights,
)
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, replay_outcome_variant
from autodrift.sequence_target_miner import parse_int_list
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device


@dataclass(frozen=True)
class SurfaceSeedRange:
    surface: str
    start_seed: int
    end_seed: int


@dataclass
class BankSnapshot:
    snapshot: OutcomeSnapshot
    surface: str
    target: str
    obstacle_x_m: float
    obstacle_y_m: float
    obstacle_distance: float
    scene_context: np.ndarray
    response_context: np.ndarray
    hidden_flat: np.ndarray
    normal_first_action: np.ndarray


def parse_surface_seed_range(raw: str) -> SurfaceSeedRange:
    if "=" not in str(raw) or ":" not in str(raw):
        raise argparse.ArgumentTypeError(f"seed range must be SURFACE=START:END, got {raw!r}")
    surface, seeds = str(raw).split("=", 1)
    start, end = seeds.split(":", 1)
    surface = surface.strip()
    if not surface:
        raise argparse.ArgumentTypeError(f"seed range has empty surface: {raw!r}")
    start_seed = int(start)
    end_seed = int(end)
    if end_seed < start_seed:
        raise argparse.ArgumentTypeError(f"seed range end must be >= start: {raw!r}")
    return SurfaceSeedRange(surface=surface, start_seed=start_seed, end_seed=end_seed)


def normalized_l2(left: np.ndarray, right: np.ndarray) -> float:
    left_arr = np.asarray(left, dtype=np.float64).reshape(-1)
    right_arr = np.asarray(right, dtype=np.float64).reshape(-1)
    if left_arr.shape != right_arr.shape:
        raise ValueError(f"expected matching vectors, got {left_arr.shape} and {right_arr.shape}")
    if left_arr.size == 0:
        return 0.0
    return float(np.linalg.norm(left_arr - right_arr) / np.sqrt(left_arr.size))


def scene_context_vector(observation: np.ndarray) -> np.ndarray:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    if obs.shape[0] < 72:
        raise ValueError("action-critical miner expects the 72-dim human-view observation")
    road = obs[12:44]
    obstacle_slots = obs[44:72].reshape(4, 7)
    obstacle_geometry = obstacle_slots[:, [0, 1, 2, 5, 6]].reshape(-1)
    return np.concatenate([road, obstacle_geometry]).astype(np.float32)


def response_context_vector(observation: np.ndarray) -> np.ndarray:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    if obs.shape[0] < 12:
        raise ValueError("observation must have at least 12 response/action fields")
    return obs[:12].copy()


def obstacle_xy_from_observation(observation: np.ndarray) -> tuple[float, float]:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    if obs.shape[0] < 51:
        return float("nan"), float("nan")
    present = float(obs[44])
    if present <= 0.5:
        return float("nan"), float("nan")
    return float(obs[45] * 80.0), float(obs[46] * 20.0)


def action_critical_rejection_reason(
    *,
    first_l2: float,
    sequence_mean_l2: float,
    preferred_rejected_mean_l2: float,
    margin_gap: float,
    normal_margin: float,
    wrong_margin: float,
    success_drop: bool,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
) -> str:
    reasons: list[str] = []
    if first_l2 < float(min_wrong_first_action_l2):
        reasons.append("wrong_first_action_l2_below_threshold")
    if sequence_mean_l2 < float(min_wrong_action_sequence_mean_l2):
        reasons.append("wrong_action_sequence_mean_l2_below_threshold")
    if preferred_rejected_mean_l2 < float(min_preferred_rejected_action_mean_l2):
        reasons.append("preferred_rejected_action_mean_l2_below_threshold")
    if not np.isfinite(normal_margin) or normal_margin < 0.0:
        reasons.append("normal_margin_negative_or_missing")
    outcome_ok = bool(success_drop) or (
        np.isfinite(margin_gap)
        and margin_gap >= float(min_margin_gap)
        and np.isfinite(wrong_margin)
        and wrong_margin <= normal_margin - float(min_margin_gap)
    )
    if not outcome_ok:
        reasons.append("no_success_drop_or_margin_gap")
    return "accepted" if not reasons else ";".join(reasons)


def is_compatible_pair(
    left: BankSnapshot,
    right: BankSnapshot,
    *,
    context_distance_threshold: float,
    response_distance_threshold: float,
    obstacle_x_abs_delta: float,
    obstacle_y_abs_delta: float,
    step_abs_delta: int,
    same_surface_only: bool = True,
) -> tuple[bool, dict[str, float]]:
    context_distance = normalized_l2(left.scene_context, right.scene_context)
    response_distance = normalized_l2(left.response_context, right.response_context)
    obstacle_x_delta = abs(float(left.obstacle_x_m) - float(right.obstacle_x_m))
    obstacle_y_delta = abs(float(left.obstacle_y_m) - float(right.obstacle_y_m))
    step_delta = abs(int(left.snapshot.step) - int(right.snapshot.step))
    hidden_distance = normalized_l2(left.hidden_flat, right.hidden_flat)
    compatible = bool(
        int(left.snapshot.seed) != int(right.snapshot.seed)
        and (not same_surface_only or str(left.surface) == str(right.surface))
        and np.isfinite(context_distance)
        and context_distance <= float(context_distance_threshold)
        and np.isfinite(response_distance)
        and response_distance <= float(response_distance_threshold)
        and np.isfinite(obstacle_x_delta)
        and obstacle_x_delta <= float(obstacle_x_abs_delta)
        and np.isfinite(obstacle_y_delta)
        and obstacle_y_delta <= float(obstacle_y_abs_delta)
        and step_delta <= int(step_abs_delta)
    )
    return compatible, {
        "context_distance": context_distance,
        "response_distance": response_distance,
        "obstacle_x_abs_delta": float(obstacle_x_delta),
        "obstacle_y_abs_delta": float(obstacle_y_delta),
        "step_abs_delta": float(step_delta),
        "hidden_distance": hidden_distance,
    }


def _target_label(info: dict[str, Any]) -> str:
    label = str(info.get("obstacle_label", "") or "")
    return label if label else "unknown_obstacle"


def _capture_candidate_snapshot(
    *,
    model: ActorCritic,
    env: AutoDriftEnv,
    surface: str,
    seed: int,
    obs: np.ndarray,
    hidden: torch.Tensor,
    info: dict[str, Any],
    device: torch.device,
) -> BankSnapshot | None:
    if not bool(info.get("obstacle_perception_visible", False)):
        return None
    obstacle_distance = _finite_float(info.get("obstacle_distance"))
    if not np.isfinite(obstacle_distance) or obstacle_distance < 0.0:
        return None
    obstacle_x_m, obstacle_y_m = obstacle_xy_from_observation(obs)
    if not np.isfinite(obstacle_x_m) or not np.isfinite(obstacle_y_m):
        return None
    action, _ = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
    return BankSnapshot(
        snapshot=OutcomeSnapshot(
            seed=int(seed),
            step=int(env.step_count),
            observation=np.asarray(obs, dtype=np.float32).copy(),
            hidden=hidden.detach().clone(),
            env=copy.deepcopy(env),
            info=dict(info),
        ),
        surface=str(surface),
        target=_target_label(info),
        obstacle_x_m=float(obstacle_x_m),
        obstacle_y_m=float(obstacle_y_m),
        obstacle_distance=float(obstacle_distance),
        scene_context=scene_context_vector(obs),
        response_context=response_context_vector(obs),
        hidden_flat=_hidden_array(hidden),
        normal_first_action=np.asarray(action, dtype=np.float32).copy(),
    )


def collect_snapshot_bank(
    *,
    model: ActorCritic,
    surface: str,
    env_config: DriftEnvConfig,
    start_seed: int,
    end_seed: int,
    max_snapshots_per_surface: int,
    max_snapshots_per_seed: int,
    sample_stride: int,
    device: torch.device,
) -> list[BankSnapshot]:
    if not model.is_online_recurrent:
        raise ValueError("action-critical wrong-history source mining requires an online recurrent checkpoint")
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
                if step % max(int(sample_stride), 1) == 0:
                    candidate = _capture_candidate_snapshot(
                        model=model,
                        env=env,
                        surface=surface,
                        seed=int(seed),
                        obs=np.asarray(obs, dtype=np.float32),
                        hidden=hidden,
                        info=info,
                        device=device,
                    )
                    if candidate is not None:
                        seed_candidates.append(candidate)
                action, next_hidden = deterministic_action_from_hidden(
                    model,
                    np.asarray(obs, dtype=np.float32),
                    hidden,
                    device,
                )
                obs, _, terminated, truncated, info = env.step(action)
                hidden = next_hidden
            seed_candidates = sorted(seed_candidates, key=lambda item: (item.obstacle_distance, item.snapshot.step))
            if max_snapshots_per_seed > 0:
                seed_candidates = seed_candidates[: int(max_snapshots_per_seed)]
            snapshots.extend(seed_candidates)
            if max_snapshots_per_surface > 0 and len(snapshots) >= int(max_snapshots_per_surface):
                snapshots = snapshots[: int(max_snapshots_per_surface)]
                break
    finally:
        env.close()
    return snapshots


def candidate_pairs_for_bank(
    snapshots: list[BankSnapshot],
    *,
    max_right_candidates_per_left: int,
    context_distance_threshold: float,
    response_distance_threshold: float,
    obstacle_x_abs_delta: float,
    obstacle_y_abs_delta: float,
    step_abs_delta: int,
) -> list[tuple[BankSnapshot, BankSnapshot, dict[str, float]]]:
    pairs: list[tuple[BankSnapshot, BankSnapshot, dict[str, float]]] = []
    for left in snapshots:
        compatible_rights: list[tuple[BankSnapshot, dict[str, float]]] = []
        for right in snapshots:
            compatible, metrics = is_compatible_pair(
                left,
                right,
                context_distance_threshold=context_distance_threshold,
                response_distance_threshold=response_distance_threshold,
                obstacle_x_abs_delta=obstacle_x_abs_delta,
                obstacle_y_abs_delta=obstacle_y_abs_delta,
                step_abs_delta=step_abs_delta,
                same_surface_only=True,
            )
            if compatible:
                compatible_rights.append((right, metrics))
        compatible_rights.sort(
            key=lambda item: (
                -float(item[1]["hidden_distance"]),
                float(item[1]["context_distance"]),
                float(item[1]["response_distance"]),
                int(item[0].snapshot.seed),
                int(item[0].snapshot.step),
            )
        )
        if max_right_candidates_per_left > 0:
            compatible_rights = compatible_rights[: int(max_right_candidates_per_left)]
        pairs.extend((left, right, metrics) for right, metrics in compatible_rights)
    return pairs


def score_action_critical_pair(
    *,
    source_index: int,
    left: BankSnapshot,
    right: BankSnapshot,
    pair_metrics: dict[str, float],
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    sequence_lengths: tuple[int, ...],
    max_continuation_steps: int,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, list[np.ndarray]]]:
    normal, normal_actions = replay_outcome_variant(
        model=model,
        snapshot=left.snapshot,
        env_config=env_config,
        variant="normal",
        response_dim=response_dim,
        variant_hidden=None,
        normal_first_action=None,
        normal_actions=None,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_first = np.asarray(
        [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
        dtype=np.float32,
    )
    wrong, wrong_actions = replay_outcome_variant(
        model=model,
        snapshot=left.snapshot,
        env_config=env_config,
        variant="wrong_matched_history",
        response_dim=response_dim,
        variant_hidden=right.snapshot.hidden,
        normal_first_action=normal_first,
        normal_actions=normal_actions,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    wrong_margin = _finite_float(wrong.get("min_clearance_margin"))
    margin_gap = normal_margin - wrong_margin if np.isfinite(normal_margin) and np.isfinite(wrong_margin) else float("nan")
    normal_success = bool(normal.get("success", False))
    wrong_success = bool(wrong.get("success", False))
    success_drop = bool(normal_success and not wrong_success)
    normal_risk = risk_score(normal)
    wrong_risk = risk_score(wrong)
    first_l2 = _finite_float(wrong.get("first_action_distance"), 0.0)
    rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observation": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "preferred_action_sequence": [],
        "rejected_action_sequence": [],
        "normal_base_action_sequence": [],
        "variant_base_action_sequence": [],
    }
    for sequence_length in sequence_lengths:
        preferred_sequence = action_sequence_prefix(normal_actions, int(sequence_length))
        rejected_sequence = action_sequence_prefix(wrong_actions, int(sequence_length))
        distances = action_sequence_distance(preferred_sequence, rejected_sequence)
        reason = action_critical_rejection_reason(
            first_l2=first_l2,
            sequence_mean_l2=distances["mean_l2"],
            preferred_rejected_mean_l2=distances["mean_l2"],
            margin_gap=margin_gap,
            normal_margin=normal_margin,
            wrong_margin=wrong_margin,
            success_drop=success_drop,
            min_wrong_first_action_l2=min_wrong_first_action_l2,
            min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
            min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
            min_margin_gap=min_margin_gap,
        )
        accepted = reason == "accepted"
        row = {
            "source_index": int(source_index),
            "physical_pair_key": f"{left.surface}:{int(left.snapshot.seed)}:{int(right.snapshot.seed)}",
            "grid_name": "action_critical_wrong_history",
            "surface": str(left.surface),
            "target": str(left.target),
            "variant": "wrong_matched_history",
            "split": "unassigned",
            "preferred_sequence_source": "normal_policy_base",
            "left_seed": int(left.snapshot.seed),
            "right_seed": int(right.snapshot.seed),
            "left_step": int(left.snapshot.step),
            "right_step": int(right.snapshot.step),
            "sequence_length": int(sequence_length),
            "left_obstacle_label": str(left.target),
            "right_obstacle_label": str(right.target),
            "left_obstacle_distance": float(left.obstacle_distance),
            "right_obstacle_distance": float(right.obstacle_distance),
            "left_obstacle_x_m": float(left.obstacle_x_m),
            "right_obstacle_x_m": float(right.obstacle_x_m),
            "left_obstacle_y_m": float(left.obstacle_y_m),
            "right_obstacle_y_m": float(right.obstacle_y_m),
            **pair_metrics,
            "normal_success": normal_success,
            "wrong_success": wrong_success,
            "success_drop": success_drop,
            "normal_collision": bool(normal.get("collision", False)),
            "wrong_collision": bool(wrong.get("collision", False)),
            "normal_terminal_reason": str(normal.get("terminal_reason", "")),
            "wrong_terminal_reason": str(wrong.get("terminal_reason", "")),
            "normal_margin": normal_margin,
            "wrong_margin": wrong_margin,
            "preferred_margin": normal_margin,
            "rejected_margin": wrong_margin,
            "normal_risk_score": normal_risk,
            "wrong_risk_score": wrong_risk,
            "preferred_risk_score": normal_risk,
            "rejected_risk_score": wrong_risk,
            "margin_gap": margin_gap,
            "risk_gap": wrong_risk - normal_risk,
            "wrong_first_action_l2": first_l2,
            "wrong_action_sequence_mean_l2": distances["mean_l2"],
            "wrong_action_sequence_max_l2": distances["max_l2"],
            "preferred_vs_rejected_action_mean_l2": distances["mean_l2"],
            "preferred_vs_rejected_action_max_l2": distances["max_l2"],
            "accepted": accepted,
            "rejection_reason": reason,
        }
        rows.append(row)
        if accepted:
            corpus["observation"].append(np.asarray(left.snapshot.observation, dtype=np.float32).copy())
            corpus["normal_hidden"].append(_hidden_array(left.snapshot.hidden))
            corpus["variant_hidden"].append(_hidden_array(right.snapshot.hidden))
            corpus["preferred_action_sequence"].append(preferred_sequence)
            corpus["rejected_action_sequence"].append(rejected_sequence)
            corpus["normal_base_action_sequence"].append(preferred_sequence)
            corpus["variant_base_action_sequence"].append(rejected_sequence)
    return rows, corpus


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


def run_action_critical_wrong_history_source_miner(
    *,
    checkpoint_path: Path,
    surface_configs: dict[str, Path],
    surface_seed_ranges: dict[str, SurfaceSeedRange],
    sequence_lengths: tuple[int, ...],
    max_right_candidates_per_left: int,
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
    max_candidate_pairs_per_surface: int,
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

    missing_ranges = sorted(set(surface_configs).difference(surface_seed_ranges))
    if missing_ranges:
        raise ValueError(f"missing seed ranges for surfaces: {missing_ranges}")

    snapshots_by_surface: dict[str, list[BankSnapshot]] = {}
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
    for surface, config_path in sorted(surface_configs.items()):
        seed_range = surface_seed_ranges[surface]
        env_config = load_env_config(config_path)
        snapshots = collect_snapshot_bank(
            model=model,
            surface=surface,
            env_config=env_config,
            start_seed=seed_range.start_seed,
            end_seed=seed_range.end_seed,
            max_snapshots_per_surface=max_snapshots_per_surface,
            max_snapshots_per_seed=max_snapshots_per_seed,
            sample_stride=sample_stride,
            device=resolved_device,
        )
        snapshots_by_surface[surface] = snapshots
        pairs = candidate_pairs_for_bank(
            snapshots,
            max_right_candidates_per_left=max_right_candidates_per_left,
            context_distance_threshold=context_distance_threshold,
            response_distance_threshold=response_distance_threshold,
            obstacle_x_abs_delta=obstacle_x_abs_delta,
            obstacle_y_abs_delta=obstacle_y_abs_delta,
            step_abs_delta=step_abs_delta,
        )
        if max_candidate_pairs_per_surface > 0:
            pairs = pairs[: int(max_candidate_pairs_per_surface)]
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
    write_csv_rows(run_dir / "candidate_scores.csv", candidate_rows)
    write_csv_rows(run_dir / "action_critical_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "source_summary.csv", _summary_rows(accepted_frame, "source_index"))
    write_csv_rows(run_dir / "split_summary.csv", _summary_rows(accepted_frame, "split"))
    write_csv_rows(run_dir / "target_summary.csv", _summary_rows(accepted_frame, "target"))
    write_action_divergent_corpus(
        output_npz=run_dir / "action_critical_corpus.npz",
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
        accepted_count >= 40
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
    summary = {
        "run_type": "action_critical_wrong_history_source_miner",
        "checkpoint": checkpoint_path,
        "surface_configs": surface_configs,
        "surface_seed_ranges": {
            key: {"start_seed": item.start_seed, "end_seed": item.end_seed}
            for key, item in surface_seed_ranges.items()
        },
        "sequence_lengths": sequence_lengths,
        "snapshot_count": int(sum(len(items) for items in snapshots_by_surface.values())),
        "snapshots_by_surface": {key: int(len(items)) for key, items in snapshots_by_surface.items()},
        "candidate_pairs": int(pair_count),
        "max_candidate_pairs_per_surface": int(max_candidate_pairs_per_surface),
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
        "min_wrong_first_action_l2": float(min_wrong_first_action_l2),
        "min_wrong_action_sequence_mean_l2": float(min_wrong_action_sequence_mean_l2),
        "min_preferred_rejected_action_mean_l2": float(min_preferred_rejected_action_mean_l2),
        "min_margin_gap": float(min_margin_gap),
        "context_distance_threshold": float(context_distance_threshold),
        "response_distance_threshold": float(response_distance_threshold),
        "obstacle_x_abs_delta": float(obstacle_x_abs_delta),
        "obstacle_y_abs_delta": float(obstacle_y_abs_delta),
        "step_abs_delta": int(step_abs_delta),
        **candidate_summary,
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "actor_checkpoint_written": False,
        "corpus_passed": corpus_passed,
        "snapshot_bank_summary_csv": run_dir / "snapshot_bank_summary.csv",
        "candidate_scores_csv": run_dir / "candidate_scores.csv",
        "action_critical_rows_csv": run_dir / "action_critical_rows.csv",
        "action_critical_corpus_npz": run_dir / "action_critical_corpus.npz",
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
    parser = argparse.ArgumentParser(description="Mine action-critical wrong-history source rows without training.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--surface-seed-range", type=parse_surface_seed_range, action="append", required=True)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(5, 7, 9))
    parser.add_argument("--max-right-candidates-per-left", type=int, default=64)
    parser.add_argument("--context-distance-threshold", type=float, default=0.25)
    parser.add_argument("--response-distance-threshold", type=float, default=0.20)
    parser.add_argument("--obstacle-x-abs-delta", type=float, default=8.0)
    parser.add_argument("--obstacle-y-abs-delta", type=float, default=1.5)
    parser.add_argument("--step-abs-delta", type=int, default=20)
    parser.add_argument("--min-wrong-first-action-l2", type=float, default=0.002)
    parser.add_argument("--min-wrong-action-sequence-mean-l2", type=float, default=0.006)
    parser.add_argument("--min-preferred-rejected-action-mean-l2", type=float, default=0.010)
    parser.add_argument("--min-margin-gap", type=float, default=0.010)
    parser.add_argument("--max-snapshots-per-surface", type=int, default=240)
    parser.add_argument("--max-snapshots-per-seed", type=int, default=4)
    parser.add_argument("--max-candidate-pairs-per-surface", type=int, default=1200)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-continuation-steps", type=int, default=9)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="action_critical_wrong_history_source_miner")
    summary = run_action_critical_wrong_history_source_miner(
        checkpoint_path=args.checkpoint,
        surface_configs={item.surface: item.env_config_path for item in args.surface_config},
        surface_seed_ranges={item.surface: item for item in args.surface_seed_range},
        sequence_lengths=args.sequence_lengths,
        max_right_candidates_per_left=args.max_right_candidates_per_left,
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
        max_candidate_pairs_per_surface=args.max_candidate_pairs_per_surface,
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
