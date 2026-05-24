"""Mine terminal-boundary anchors before wrong-history outcome gates."""

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
from autodrift.hidden_envelope_multiseed_gate import (
    CheckpointSpec,
    parse_checkpoint_spec,
    parse_seed_list,
)
from autodrift.hidden_envelope_probe import (
    CURRENT_RESPONSE,
    FULL_OBSERVATION,
    collect_hidden_envelope_dataset,
    response_feature_dim_for_model,
)
from autodrift.input_observability_audit import TARGETS
from autodrift.matched_current_response_ambiguity import (
    MATCH_CURRENT_RESPONSE_CONTEXT,
    MATCH_FEATURE_SETS,
    _standardize,
    build_match_features,
    source_obstacle_bucket_key,
)
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.natural_wrong_history_action_sensitive_selector import (
    _first_action,
    parse_env_config_map,
)
from autodrift.train_ppo import ActorCritic, resolve_device


def _clip01(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(value, 0.0, 1.0))


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _label_priority(label: str) -> float:
    return {
        "drift_required": 0.35,
        "unavoidable": 0.25,
        "aes_feasible": 0.10,
    }.get(str(label), 0.0)


def _counts(frame: pd.DataFrame, key: str) -> dict[str, int]:
    if frame.empty or key not in frame:
        return {}
    return {str(k): int(v) for k, v in frame.groupby(key, observed=True).size().to_dict().items()}


def _max_share(frame: pd.DataFrame, key: str) -> float:
    if frame.empty or key not in frame:
        return 0.0
    counts = frame.groupby(key, observed=True).size()
    return float(counts.max() / len(frame)) if len(frame) else 0.0


def _le_count(frame: pd.DataFrame, margin: float) -> int:
    if frame.empty or "normal_min_clearance_margin" not in frame:
        return 0
    return int((frame["normal_min_clearance_margin"].astype(float) <= float(margin)).sum())


def _snapshot_requests(rows: list[dict[str, Any]]) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for row in rows:
        requests.setdefault(int(row["seed"]), set()).add(int(row["step"]))
    return requests


def _pair_snapshot_requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        for prefix in ("left", "right"):
            requests.setdefault(int(row[f"{prefix}_seed"]), set()).add(int(row[f"{prefix}_step"]))
    return requests


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    *,
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _margin_from_result(result: dict[str, Any]) -> float:
    return _finite_float(result.get("min_clearance_margin", float("nan")))


def anchor_score(row: dict[str, Any], *, anchor_margin_max: float) -> float:
    margin = _finite_float(row.get("normal_min_clearance_margin", float("inf")), float("inf"))
    obstacle_distance = _finite_float(row.get("obstacle_distance", 40.0), 40.0)
    return float(
        2.0 * _clip01((float(anchor_margin_max) - margin) / max(float(anchor_margin_max), 1e-6))
        + 0.5 * _clip01((35.0 - obstacle_distance) / 35.0)
        + _label_priority(str(row.get("obstacle_label", "")))
    )


def pair_action_boundary_score(row: dict[str, Any], *, candidate_margin_max: float) -> float:
    margin = _finite_float(row.get("normal_min_clearance_margin", float("inf")), float("inf"))
    return float(
        2.0 * _clip01((float(candidate_margin_max) - margin) / max(float(candidate_margin_max), 1e-6))
        + 1.5 * _clip01(_finite_float(row.get("action_trajectory_distance_mean", 0.0), 0.0) / 0.12)
        + _clip01(_finite_float(row.get("first_action_distance", 0.0), 0.0) / 0.12)
        + 0.75 * _clip01(_finite_float(row.get("action_trajectory_distance_max", 0.0), 0.0) / 0.25)
        + 0.35 * _clip01(_finite_float(row.get("target_z_delta", 0.0), 0.0) / 4.0)
        + _label_priority(str(row.get("left_obstacle_label", "")))
    )


def collect_source_rows(
    *,
    model: ActorCritic,
    env_config_map: dict[str, Path],
    probe_seeds: tuple[int, ...],
    episodes_per_seed: int,
    horizon_steps: int,
    snapshot_stride: int,
    max_samples_per_config_seed: int | None,
    checkpoint_label: str,
    response_dim: int,
    match_feature_set: str,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    rows: list[dict[str, Any]] = []
    feature_chunks: dict[str, list[np.ndarray]] = {
        FULL_OBSERVATION: [],
        CURRENT_RESPONSE: [],
        "match_features": [],
    }
    target_chunks: dict[str, list[np.ndarray]] = {name: [] for name in TARGETS}

    for config_name, config_path in env_config_map.items():
        env_config = load_env_config(config_path)
        for probe_seed in probe_seeds:
            dataset = collect_hidden_envelope_dataset(
                model=model,
                env_config=env_config,
                episodes=episodes_per_seed,
                seed=probe_seed,
                horizon_steps=horizon_steps,
                sample_stride=snapshot_stride,
                max_samples=max_samples_per_config_seed,
                device=device,
            )
            if not dataset.rows:
                continue
            match_features = build_match_features(
                dataset.features[FULL_OBSERVATION],
                dataset.features[CURRENT_RESPONSE],
                response_dim=response_dim,
                match_feature_set=match_feature_set,
            )
            start_index = len(rows)
            for local_index, row in enumerate(dataset.rows):
                next_row = dict(row)
                next_row.update(
                    {
                        "source_index": int(start_index + local_index),
                        "checkpoint_label": checkpoint_label,
                        "config": str(config_name),
                        "env_config": str(config_path),
                        "probe_seed": int(probe_seed),
                    }
                )
                rows.append(next_row)
            feature_chunks[FULL_OBSERVATION].append(dataset.features[FULL_OBSERVATION])
            feature_chunks[CURRENT_RESPONSE].append(dataset.features[CURRENT_RESPONSE])
            feature_chunks["match_features"].append(match_features)
            for target in TARGETS:
                target_chunks[target].append(dataset.targets[target])

    features: dict[str, np.ndarray] = {}
    for name, chunks in feature_chunks.items():
        if chunks:
            features[name] = np.concatenate(chunks, axis=0).astype(np.float32)
        else:
            features[name] = np.empty((0, 0), dtype=np.float32)
    for target, chunks in target_chunks.items():
        features[f"target:{target}"] = (
            np.concatenate(chunks, axis=0).astype(np.float32) if chunks else np.empty((0,), dtype=np.float32)
        )
    if rows and int(features["match_features"].shape[0]) != len(rows):
        raise RuntimeError("source rows and match features are misaligned")
    return rows, features


def preliminary_anchor_candidates(
    source_rows: list[dict[str, Any]],
    *,
    max_anchor_obstacle_distance: float,
    max_per_config_seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in source_rows:
        obstacle_distance = _finite_float(row.get("obstacle_distance"))
        if not np.isfinite(obstacle_distance):
            continue
        if obstacle_distance > float(max_anchor_obstacle_distance):
            continue
        candidate = dict(row)
        grouped.setdefault((str(candidate["config"]), int(candidate["probe_seed"])), []).append(candidate)

    selected: list[dict[str, Any]] = []
    for _, rows in sorted(grouped.items()):
        rows.sort(
            key=lambda row: (
                _finite_float(row.get("obstacle_distance"), float("inf")),
                -_label_priority(str(row.get("obstacle_label", ""))),
                int(row.get("step", 0)),
            )
        )
        selected.extend(rows[: int(max_per_config_seed)] if max_per_config_seed > 0 else rows)
    return selected


def score_normal_anchor_candidates(
    *,
    candidate_rows: list[dict[str, Any]],
    model: ActorCritic,
    env_config_map: dict[str, Path],
    response_dim: int,
    horizon_steps: int,
    anchor_margin_max: float,
    candidate_margin_max: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if not candidate_rows:
        return scored, invalid

    by_config: dict[str, list[dict[str, Any]]] = {}
    for row in candidate_rows:
        by_config.setdefault(str(row["config"]), []).append(row)

    for config_name, rows in sorted(by_config.items()):
        env_config = load_env_config(env_config_map[config_name])
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=_snapshot_requests(rows),
            device=device,
        )
        for row in rows:
            snap = _snapshot(snapshots, seed=int(row["seed"]), step=int(row["step"]))
            if snap is None:
                invalid.append({**row, "invalid_reason": "missing_snapshot"})
                continue
            if bool(snap.info.get("collision", False)):
                invalid.append({**row, "invalid_reason": "collision_at_snapshot"})
                continue
            normal, _ = replay_outcome_variant(
                model=model,
                snapshot=snap,
                env_config=env_config,
                variant="normal",
                response_dim=response_dim,
                variant_hidden=None,
                normal_first_action=None,
                normal_actions=None,
                max_continuation_steps=horizon_steps,
                device=device,
            )
            normal_margin = _margin_from_result(normal)
            if not np.isfinite(normal_margin):
                invalid.append({**row, "invalid_reason": "nonfinite_normal_margin"})
                continue
            next_row = dict(row)
            next_row.update(
                {
                    "normal_success": bool(normal.get("success", False)),
                    "normal_collision": bool(normal.get("collision", False)),
                    "normal_obstacle_completed": bool(normal.get("obstacle_completed", False)),
                    "normal_min_clearance_margin": normal_margin,
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "normal_first_steer": float(normal.get("first_steer", float("nan"))),
                    "normal_first_throttle": float(normal.get("first_throttle", float("nan"))),
                    "normal_first_brake": float(normal.get("first_brake", float("nan"))),
                    "anchor_margin_pass": bool(normal_margin <= float(anchor_margin_max)),
                    "candidate_margin_pass": bool(normal_margin <= float(candidate_margin_max)),
                }
            )
            next_row["anchor_score"] = anchor_score(next_row, anchor_margin_max=anchor_margin_max)
            scored.append(next_row)
    return scored, invalid


def build_anchor_wrong_history_candidates(
    *,
    anchors: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    features: dict[str, np.ndarray],
    nearest_k: int,
    max_current_distance_quantile: float,
    min_target_z_delta: float,
    same_config_only: bool,
    exclude_same_seed: bool,
    max_pair_score_candidates: int,
) -> tuple[list[dict[str, Any]], float]:
    if not anchors or not source_rows:
        return [], float("nan")
    match_features = features["match_features"]
    if int(match_features.shape[0]) != len(source_rows):
        raise ValueError("source rows and feature matrix must be aligned")
    standardized = _standardize(match_features)
    target_values = {
        target: np.asarray(features[f"target:{target}"], dtype=np.float64)
        for target in TARGETS
    }
    target_stds = {
        target: float(np.nanstd(values))
        for target, values in target_values.items()
    }
    source_by_index = {int(row["source_index"]): row for row in source_rows}
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for anchor in anchors:
        left_index = int(anchor["source_index"])
        distances = np.sqrt(np.mean(np.square(standardized - standardized[left_index]), axis=1))
        valid_mask = np.ones(len(source_rows), dtype=bool)
        valid_mask[left_index] = False
        if same_config_only:
            valid_mask &= np.asarray(
                [str(row["config"]) == str(anchor["config"]) for row in source_rows],
                dtype=bool,
            )
        if exclude_same_seed:
            valid_mask &= np.asarray(
                [int(row["seed"]) != int(anchor["seed"]) for row in source_rows],
                dtype=bool,
            )
        valid_indices = np.flatnonzero(valid_mask)
        if valid_indices.size == 0:
            continue
        take = min(int(nearest_k), int(valid_indices.size))
        nearest_local = np.argpartition(distances[valid_indices], take - 1)[:take]
        nearest_indices = valid_indices[nearest_local]
        nearest_indices = nearest_indices[np.argsort(distances[nearest_indices])]
        for right_index in nearest_indices:
            right = source_by_index[int(right_index)]
            for target in TARGETS:
                key = (left_index, int(right_index), target)
                if key in seen:
                    continue
                seen.add(key)
                values = target_values[target]
                target_std = target_stds[target]
                target_delta = float(abs(values[left_index] - values[int(right_index)]))
                target_z_delta = target_delta / target_std if target_std > 1e-12 else float("nan")
                if not np.isfinite(target_z_delta) or target_z_delta < float(min_target_z_delta):
                    continue
                candidates.append(
                    {
                        "checkpoint_label": str(anchor["checkpoint_label"]),
                        "config": str(anchor["config"]),
                        "env_config": str(anchor["env_config"]),
                        "probe_seed": int(anchor["probe_seed"]),
                        "target": target,
                        "left_index": left_index,
                        "right_index": int(right_index),
                        "left_seed": int(anchor["seed"]),
                        "right_seed": int(right["seed"]),
                        "left_episode": int(anchor["episode"]),
                        "right_episode": int(right["episode"]),
                        "left_step": int(anchor["step"]),
                        "right_step": int(right["step"]),
                        "left_obstacle_label": str(anchor.get("obstacle_label", "")),
                        "right_obstacle_label": str(right.get("obstacle_label", "")),
                        "left_obstacle_distance": _finite_float(anchor.get("obstacle_distance")),
                        "right_obstacle_distance": _finite_float(right.get("obstacle_distance")),
                        "left_obstacle_lateral_offset": _finite_float(anchor.get("obstacle_lateral_offset")),
                        "right_obstacle_lateral_offset": _finite_float(right.get("obstacle_lateral_offset")),
                        "normal_min_clearance_margin": _finite_float(anchor.get("normal_min_clearance_margin")),
                        "normal_success": bool(anchor.get("normal_success", False)),
                        "normal_collision": bool(anchor.get("normal_collision", False)),
                        "normal_terminal_reason": str(anchor.get("normal_terminal_reason", "")),
                        "visible_distance": float(distances[int(right_index)]),
                        "target_left": float(values[left_index]),
                        "target_right": float(values[int(right_index)]),
                        "target_delta": target_delta,
                        "target_std": target_std,
                        "target_z_delta": float(target_z_delta),
                    }
                )
    if not candidates:
        return [], float("nan")
    distances = np.asarray([float(row["visible_distance"]) for row in candidates], dtype=np.float64)
    threshold = float(np.quantile(distances, max_current_distance_quantile))
    accepted = [row for row in candidates if float(row["visible_distance"]) <= threshold]
    accepted.sort(
        key=lambda row: (
            _finite_float(row["normal_min_clearance_margin"], float("inf")),
            float(row["visible_distance"]),
            -float(row["target_z_delta"]),
        )
    )
    if max_pair_score_candidates > 0:
        accepted = accepted[: int(max_pair_score_candidates)]
    return accepted, threshold


def score_wrong_history_pairs(
    *,
    candidate_pairs: pd.DataFrame,
    model: ActorCritic,
    env_config_map: dict[str, Path],
    response_dim: int,
    horizon_steps: int,
    candidate_margin_max: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if candidate_pairs.empty:
        return scored, invalid

    for config_name, group in candidate_pairs.groupby("config", observed=True):
        env_config = load_env_config(env_config_map[str(config_name)])
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=_pair_snapshot_requests(group),
            device=device,
        )
        for pair_id, pair in group.reset_index(drop=True).iterrows():
            left = _snapshot(snapshots, seed=int(pair["left_seed"]), step=int(pair["left_step"]))
            right = _snapshot(snapshots, seed=int(pair["right_seed"]), step=int(pair["right_step"]))
            if left is None or right is None:
                invalid.append(
                    {
                        "config": str(config_name),
                        "pair_id": int(pair_id),
                        "left_seed": int(pair["left_seed"]),
                        "right_seed": int(pair["right_seed"]),
                        "left_step": int(pair["left_step"]),
                        "right_step": int(pair["right_step"]),
                        "missing_left_snapshot": left is None,
                        "missing_right_snapshot": right is None,
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
                max_continuation_steps=horizon_steps,
                device=device,
            )
            wrong, _ = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant="wrong_matched_history",
                response_dim=response_dim,
                variant_hidden=right.hidden,
                normal_first_action=_first_action(normal),
                normal_actions=normal_actions,
                max_continuation_steps=horizon_steps,
                device=device,
            )
            normal_margin = _margin_from_result(normal)
            wrong_margin = _margin_from_result(wrong)
            row = dict(pair.to_dict())
            row.update(
                {
                    "pair_id": int(pair_id),
                    "normal_success": bool(normal.get("success", False)),
                    "wrong_success": bool(wrong.get("success", False)),
                    "normal_collision": bool(normal.get("collision", False)),
                    "wrong_collision": bool(wrong.get("collision", False)),
                    "normal_obstacle_completed": bool(normal.get("obstacle_completed", False)),
                    "wrong_obstacle_completed": bool(wrong.get("obstacle_completed", False)),
                    "normal_min_clearance_margin": normal_margin,
                    "wrong_min_clearance_margin": wrong_margin,
                    "short_horizon_margin_gap": (
                        normal_margin - wrong_margin
                        if np.isfinite(normal_margin) and np.isfinite(wrong_margin)
                        else float("nan")
                    ),
                    "first_action_distance": _finite_float(wrong.get("first_action_distance")),
                    "action_trajectory_distance_mean": _finite_float(
                        wrong.get("action_trajectory_distance_mean")
                    ),
                    "action_trajectory_distance_max": _finite_float(
                        wrong.get("action_trajectory_distance_max")
                    ),
                    "candidate_margin_pass": bool(normal_margin <= float(candidate_margin_max)),
                }
            )
            row["pair_action_boundary_score"] = pair_action_boundary_score(
                row,
                candidate_margin_max=candidate_margin_max,
            )
            scored.append(row)
    return scored, invalid


def select_terminal_boundary_anchor_pairs(
    candidates: pd.DataFrame,
    *,
    candidate_margin_max: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    if candidates.empty or max_rows == 0:
        return candidates.head(0).copy()
    frame = candidates.copy()
    frame["boundary_pass"] = (
        frame["normal_min_clearance_margin"].astype(float) <= float(candidate_margin_max)
    )
    frame["soft_action_pass"] = (
        (frame["first_action_distance"].astype(float) >= float(first_action_threshold))
        | (frame["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
        | (frame["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
    )
    eligible = frame[frame["boundary_pass"].astype(bool) & frame["soft_action_pass"].astype(bool)].copy()
    if eligible.empty:
        return eligible
    eligible["obstacle_bucket"] = [
        source_obstacle_bucket_key(
            row,
            distance_width=obstacle_distance_bucket_width,
            lateral_width=obstacle_lateral_bucket_width,
        )
        for row in eligible.to_dict(orient="records")
    ]
    eligible = eligible.sort_values(
        [
            "pair_action_boundary_score",
            "normal_min_clearance_margin",
            "action_trajectory_distance_mean",
            "first_action_distance",
            "target_z_delta",
        ],
        ascending=[False, True, False, False, False],
    )
    selected: list[dict[str, Any]] = []
    counts: dict[str, dict[Any, int]] = {
        "probe_seed": {},
        "left_seed": {},
        "left_obstacle_label": {},
        "target": {},
        "config": {},
        "obstacle_bucket": {},
    }
    caps = {
        "probe_seed": int(max_per_probe_seed),
        "left_seed": int(max_per_left_seed),
        "left_obstacle_label": int(max_per_label),
        "target": int(max_per_target),
        "config": int(max_per_config),
        "obstacle_bucket": int(max_per_obstacle_bucket),
    }
    for row in eligible.to_dict(orient="records"):
        if len(selected) >= int(max_rows):
            break
        blocked = False
        for key, cap in caps.items():
            if cap <= 0:
                continue
            value = row.get(key)
            if counts[key].get(value, 0) >= cap:
                blocked = True
                break
        if blocked:
            continue
        selected.append(row)
        for key in counts:
            value = row.get(key)
            counts[key][value] = counts[key].get(value, 0) + 1
    return pd.DataFrame(selected, columns=list(eligible.columns))


def summarize_anchor_mining(
    *,
    source_rows: list[dict[str, Any]],
    anchor_candidates: list[dict[str, Any]],
    scored_anchors: pd.DataFrame,
    candidate_pairs: pd.DataFrame,
    scored_pairs: pd.DataFrame,
    targeted_pairs: pd.DataFrame,
    current_distance_threshold: float,
    min_anchor_count: int,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
) -> dict[str, Any]:
    anchors = (
        scored_anchors[scored_anchors["anchor_margin_pass"].astype(bool)].copy()
        if not scored_anchors.empty and "anchor_margin_pass" in scored_anchors
        else scored_anchors.head(0).copy()
    )
    pair_count = int(len(targeted_pairs))
    probe_seed_count = int(targeted_pairs["probe_seed"].nunique()) if "probe_seed" in targeted_pairs else 0
    label_count = (
        int(targeted_pairs["left_obstacle_label"].nunique()) if "left_obstacle_label" in targeted_pairs else 0
    )
    config_count = int(targeted_pairs["config"].nunique()) if "config" in targeted_pairs else 0
    single_seed_share = _max_share(targeted_pairs, "probe_seed")
    single_label_share = _max_share(targeted_pairs, "left_obstacle_label")
    single_config_share = _max_share(targeted_pairs, "config")
    rows_le_0_50 = _le_count(targeted_pairs, 0.50)
    rows_le_1_00 = _le_count(targeted_pairs, 1.00)
    trajectory_mean = (
        float(targeted_pairs["action_trajectory_distance_mean"].astype(float).mean())
        if len(targeted_pairs)
        else None
    )
    trajectory_p90 = (
        float(targeted_pairs["action_trajectory_distance_mean"].astype(float).quantile(0.90))
        if len(targeted_pairs)
        else None
    )
    gate_pass = (
        len(anchors) >= int(min_anchor_count)
        and pair_count >= int(min_pair_count)
        and probe_seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_obstacle_label_count)
        and config_count >= int(min_config_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
        and single_config_share <= float(max_single_config_share)
        and rows_le_0_50 >= int(min_margin_le_0_50_rows)
        and rows_le_1_00 >= int(min_margin_le_1_00_rows)
        and trajectory_mean is not None
        and trajectory_mean >= float(min_trajectory_mean)
        and trajectory_p90 is not None
        and trajectory_p90 >= float(min_trajectory_p90)
    )
    return {
        "run_type": "terminal_boundary_anchor_miner",
        "source_row_count": int(len(source_rows)),
        "anchor_candidate_row_count": int(len(anchor_candidates)),
        "normal_scored_anchor_count": int(len(scored_anchors)),
        "anchor_count": int(len(anchors)),
        "candidate_pair_count": int(len(candidate_pairs)),
        "scored_pair_count": int(len(scored_pairs)),
        "pair_count": pair_count,
        "current_distance_threshold": current_distance_threshold,
        "probe_seed_count": probe_seed_count,
        "obstacle_label_count": label_count,
        "target_count": int(targeted_pairs["target"].nunique()) if "target" in targeted_pairs else 0,
        "config_count": config_count,
        "single_seed_share": single_seed_share,
        "single_label_share": single_label_share,
        "single_config_share": single_config_share,
        "rows_normal_margin_le_0_50": rows_le_0_50,
        "rows_normal_margin_le_1_00": rows_le_1_00,
        "targeted_trajectory_mean": trajectory_mean,
        "targeted_trajectory_p90": trajectory_p90,
        "targeted_first_action_mean": (
            float(targeted_pairs["first_action_distance"].astype(float).mean()) if len(targeted_pairs) else None
        ),
        "targeted_normal_margin_min": (
            float(targeted_pairs["normal_min_clearance_margin"].astype(float).min()) if len(targeted_pairs) else None
        ),
        "targeted_normal_margin_p50": (
            float(targeted_pairs["normal_min_clearance_margin"].astype(float).quantile(0.50))
            if len(targeted_pairs)
            else None
        ),
        "anchors_by_probe_seed": _counts(anchors, "probe_seed"),
        "anchors_by_obstacle_label": _counts(anchors, "obstacle_label"),
        "anchors_by_config": _counts(anchors, "config"),
        "targeted_by_probe_seed": _counts(targeted_pairs, "probe_seed"),
        "targeted_by_left_obstacle_label": _counts(targeted_pairs, "left_obstacle_label"),
        "targeted_by_target": _counts(targeted_pairs, "target"),
        "targeted_by_config": _counts(targeted_pairs, "config"),
        "terminal_boundary_anchor_gate_pass": bool(gate_pass),
        "outcome_gate_admitted": bool(gate_pass),
    }


def run_anchor_miner(
    *,
    checkpoint_spec: CheckpointSpec,
    env_config_map: dict[str, Path],
    anchor_seeds: tuple[int, ...],
    episodes_per_seed: int,
    horizon_steps: int,
    snapshot_stride: int,
    max_samples_per_config_seed: int | None,
    max_anchor_obstacle_distance: float,
    max_anchor_score_candidates_per_config_seed: int,
    anchor_margin_max: float,
    candidate_margin_max: float,
    nearest_k: int,
    max_current_distance_quantile: float,
    min_target_z_delta: float,
    max_pair_score_candidates: int,
    short_horizon_steps: int,
    same_config_only: bool,
    exclude_same_seed: bool,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_obstacle_bucket: int,
    min_anchor_count: int,
    min_pair_count: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
    match_feature_set: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    source_rows, features = collect_source_rows(
        model=model,
        env_config_map=env_config_map,
        probe_seeds=anchor_seeds,
        episodes_per_seed=episodes_per_seed,
        horizon_steps=horizon_steps,
        snapshot_stride=snapshot_stride,
        max_samples_per_config_seed=max_samples_per_config_seed,
        checkpoint_label=checkpoint_spec.label,
        response_dim=response_dim,
        match_feature_set=match_feature_set,
        device=resolved_device,
    )
    anchor_candidates = preliminary_anchor_candidates(
        source_rows,
        max_anchor_obstacle_distance=max_anchor_obstacle_distance,
        max_per_config_seed=max_anchor_score_candidates_per_config_seed,
    )
    scored_anchors, invalid_anchor_rows = score_normal_anchor_candidates(
        candidate_rows=anchor_candidates,
        model=model,
        env_config_map=env_config_map,
        response_dim=response_dim,
        horizon_steps=short_horizon_steps,
        anchor_margin_max=anchor_margin_max,
        candidate_margin_max=candidate_margin_max,
        device=resolved_device,
    )
    scored_anchor_frame = pd.DataFrame(scored_anchors)
    boundary_anchors = (
        scored_anchor_frame[scored_anchor_frame["anchor_margin_pass"].astype(bool)]
        if not scored_anchor_frame.empty and "anchor_margin_pass" in scored_anchor_frame
        else scored_anchor_frame.head(0)
    )
    candidate_pairs, current_distance_threshold = build_anchor_wrong_history_candidates(
        anchors=boundary_anchors.to_dict(orient="records"),
        source_rows=source_rows,
        features=features,
        nearest_k=nearest_k,
        max_current_distance_quantile=max_current_distance_quantile,
        min_target_z_delta=min_target_z_delta,
        same_config_only=same_config_only,
        exclude_same_seed=exclude_same_seed,
        max_pair_score_candidates=max_pair_score_candidates,
    )
    candidate_pair_frame = pd.DataFrame(candidate_pairs)
    scored_pairs, invalid_pair_rows = score_wrong_history_pairs(
        candidate_pairs=candidate_pair_frame,
        model=model,
        env_config_map=env_config_map,
        response_dim=response_dim,
        horizon_steps=short_horizon_steps,
        candidate_margin_max=candidate_margin_max,
        device=resolved_device,
    )
    scored_pair_frame = pd.DataFrame(scored_pairs)
    targeted_pairs = select_terminal_boundary_anchor_pairs(
        scored_pair_frame,
        candidate_margin_max=candidate_margin_max,
        first_action_threshold=first_action_threshold,
        trajectory_mean_threshold=trajectory_mean_threshold,
        trajectory_max_threshold=trajectory_max_threshold,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_config=max_per_config,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )
    summary = {
        "checkpoint": {"label": checkpoint_spec.label, "path": checkpoint_spec.path},
        "env_config_map": env_config_map,
        "anchor_seeds": anchor_seeds,
        "episodes_per_seed": int(episodes_per_seed),
        "horizon_steps": int(horizon_steps),
        "snapshot_stride": int(snapshot_stride),
        "max_samples_per_config_seed": max_samples_per_config_seed,
        "max_anchor_obstacle_distance": float(max_anchor_obstacle_distance),
        "max_anchor_score_candidates_per_config_seed": int(max_anchor_score_candidates_per_config_seed),
        "anchor_margin_max": float(anchor_margin_max),
        "candidate_margin_max": float(candidate_margin_max),
        "nearest_k": int(nearest_k),
        "max_current_distance_quantile": float(max_current_distance_quantile),
        "min_target_z_delta": float(min_target_z_delta),
        "max_pair_score_candidates": int(max_pair_score_candidates),
        "short_horizon_steps": int(short_horizon_steps),
        "same_config_only": bool(same_config_only),
        "exclude_same_seed": bool(exclude_same_seed),
        "first_action_threshold": float(first_action_threshold),
        "trajectory_mean_threshold": float(trajectory_mean_threshold),
        "trajectory_max_threshold": float(trajectory_max_threshold),
        **summarize_anchor_mining(
            source_rows=source_rows,
            anchor_candidates=anchor_candidates,
            scored_anchors=scored_anchor_frame,
            candidate_pairs=candidate_pair_frame,
            scored_pairs=scored_pair_frame,
            targeted_pairs=targeted_pairs,
            current_distance_threshold=current_distance_threshold,
            min_anchor_count=min_anchor_count,
            min_pair_count=min_pair_count,
            min_probe_seed_count=min_probe_seed_count,
            min_obstacle_label_count=min_obstacle_label_count,
            min_config_count=min_config_count,
            max_single_seed_share=max_single_seed_share,
            max_single_label_share=max_single_label_share,
            max_single_config_share=max_single_config_share,
            min_margin_le_0_50_rows=min_margin_le_0_50_rows,
            min_margin_le_1_00_rows=min_margin_le_1_00_rows,
            min_trajectory_mean=min_trajectory_mean,
            min_trajectory_p90=min_trajectory_p90,
        ),
        "source_rows_csv": run_dir / "source_rows.csv",
        "anchor_candidates_csv": run_dir / "anchor_candidates.csv",
        "anchors_csv": run_dir / "anchors.csv",
        "candidate_pairs_csv": run_dir / "candidate_pairs.csv",
        "scored_pairs_csv": run_dir / "scored_pairs.csv",
        "targeted_pairs_csv": run_dir / "targeted_pairs.csv",
        "invalid_anchor_snapshots_csv": run_dir / "invalid_anchor_snapshots.csv",
        "invalid_pair_snapshots_csv": run_dir / "invalid_pair_snapshots.csv",
    }
    anchor_frame_to_write = (
        scored_anchor_frame[scored_anchor_frame["anchor_margin_pass"].astype(bool)]
        if not scored_anchor_frame.empty and "anchor_margin_pass" in scored_anchor_frame
        else scored_anchor_frame.head(0)
    )
    write_csv_rows(run_dir / "source_rows.csv", source_rows)
    write_csv_rows(run_dir / "anchor_candidates.csv", scored_anchors)
    write_csv_rows(run_dir / "anchors.csv", anchor_frame_to_write.to_dict(orient="records"))
    write_csv_rows(run_dir / "candidate_pairs.csv", candidate_pairs)
    write_csv_rows(run_dir / "scored_pairs.csv", scored_pairs)
    write_csv_rows(run_dir / "targeted_pairs.csv", targeted_pairs.to_dict(orient="records"), fieldnames=list(targeted_pairs.columns))
    write_csv_rows(run_dir / "invalid_anchor_snapshots.csv", invalid_anchor_rows)
    write_csv_rows(run_dir / "invalid_pair_snapshots.csv", invalid_pair_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine terminal-boundary anchors for wrong-history probes.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config-map", action="append", type=parse_env_config_map, required=True)
    parser.add_argument("--anchor-seeds", type=parse_seed_list, required=True)
    parser.add_argument("--episodes-per-seed", type=int, default=64)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--snapshot-stride", type=int, default=2)
    parser.add_argument("--max-samples-per-config-seed", type=int, default=2400)
    parser.add_argument("--max-anchor-obstacle-distance", type=float, default=40.0)
    parser.add_argument("--max-anchor-score-candidates-per-config-seed", type=int, default=800)
    parser.add_argument("--anchor-margin-max", type=float, default=1.0)
    parser.add_argument("--candidate-margin-max", type=float, default=2.0)
    parser.add_argument("--nearest-k", type=int, default=48)
    parser.add_argument("--max-current-distance-quantile", type=float, default=0.05)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--max-pair-score-candidates", type=int, default=3000)
    parser.add_argument("--short-horizon-steps", type=int, default=8)
    parser.add_argument("--allow-cross-config", action="store_true")
    parser.add_argument("--allow-same-seed", action="store_true")
    parser.add_argument("--first-action-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-mean-threshold", type=float, default=0.02)
    parser.add_argument("--trajectory-max-threshold", type=float, default=0.05)
    parser.add_argument("--max-rows", type=int, default=360)
    parser.add_argument("--max-per-probe-seed", type=int, default=80)
    parser.add_argument("--max-per-left-seed", type=int, default=8)
    parser.add_argument("--max-per-label", type=int, default=180)
    parser.add_argument("--max-per-target", type=int, default=150)
    parser.add_argument("--max-per-config", type=int, default=190)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=24)
    parser.add_argument("--min-anchor-count", type=int, default=120)
    parser.add_argument("--min-pair-count", type=int, default=240)
    parser.add_argument("--min-probe-seed-count", type=int, default=6)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-config-count", type=int, default=2)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.70)
    parser.add_argument("--max-single-config-share", type=float, default=0.70)
    parser.add_argument("--min-margin-le-0-50-rows", type=int, default=40)
    parser.add_argument("--min-margin-le-1-00-rows", type=int, default=100)
    parser.add_argument("--min-trajectory-mean", type=float, default=0.04)
    parser.add_argument("--min-trajectory-p90", type=float, default=0.08)
    parser.add_argument("--match-feature-set", choices=MATCH_FEATURE_SETS, default=MATCH_CURRENT_RESPONSE_CONTEXT)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="terminal_boundary_anchor_miner")
    summary = run_anchor_miner(
        checkpoint_spec=args.checkpoint_policy,
        env_config_map=dict(args.env_config_map),
        anchor_seeds=tuple(args.anchor_seeds),
        episodes_per_seed=args.episodes_per_seed,
        horizon_steps=args.horizon_steps,
        snapshot_stride=args.snapshot_stride,
        max_samples_per_config_seed=args.max_samples_per_config_seed,
        max_anchor_obstacle_distance=args.max_anchor_obstacle_distance,
        max_anchor_score_candidates_per_config_seed=args.max_anchor_score_candidates_per_config_seed,
        anchor_margin_max=args.anchor_margin_max,
        candidate_margin_max=args.candidate_margin_max,
        nearest_k=args.nearest_k,
        max_current_distance_quantile=args.max_current_distance_quantile,
        min_target_z_delta=args.min_target_z_delta,
        max_pair_score_candidates=args.max_pair_score_candidates,
        short_horizon_steps=args.short_horizon_steps,
        same_config_only=not args.allow_cross_config,
        exclude_same_seed=not args.allow_same_seed,
        first_action_threshold=args.first_action_threshold,
        trajectory_mean_threshold=args.trajectory_mean_threshold,
        trajectory_max_threshold=args.trajectory_max_threshold,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_config=args.max_per_config,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        min_anchor_count=args.min_anchor_count,
        min_pair_count=args.min_pair_count,
        min_probe_seed_count=args.min_probe_seed_count,
        min_obstacle_label_count=args.min_obstacle_label_count,
        min_config_count=args.min_config_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_label_share=args.max_single_label_share,
        max_single_config_share=args.max_single_config_share,
        min_margin_le_0_50_rows=args.min_margin_le_0_50_rows,
        min_margin_le_1_00_rows=args.min_margin_le_1_00_rows,
        min_trajectory_mean=args.min_trajectory_mean,
        min_trajectory_p90=args.min_trajectory_p90,
        match_feature_set=args.match_feature_set,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
