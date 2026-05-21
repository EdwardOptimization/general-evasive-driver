"""Mine matched-current-response ambiguity surfaces for self-ID probes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec, parse_seed_list
from autodrift.hidden_envelope_probe import (
    CURRENT_RESPONSE,
    FULL_OBSERVATION,
    POLICY_FEATURES,
    RESET_POLICY_FEATURES,
    RESET_RESPONSE_HIDDEN,
    RESPONSE_HIDDEN,
    collect_hidden_envelope_dataset,
    response_feature_dim_for_model,
)
from autodrift.input_observability_audit import TARGETS
from autodrift.train_ppo import resolve_device


MATCH_CURRENT_RESPONSE = "current_response"
MATCH_CONTEXT = "context"
MATCH_CURRENT_RESPONSE_CONTEXT = "current_response_context"
MATCH_FULL_OBSERVATION = "full_observation"
MATCH_FEATURE_SETS = (
    MATCH_CURRENT_RESPONSE,
    MATCH_CONTEXT,
    MATCH_CURRENT_RESPONSE_CONTEXT,
    MATCH_FULL_OBSERVATION,
)

COMPARISON_FEATURE_SETS = (
    CURRENT_RESPONSE,
    POLICY_FEATURES,
    RESPONSE_HIDDEN,
    RESET_POLICY_FEATURES,
    RESET_RESPONSE_HIDDEN,
    FULL_OBSERVATION,
)


def _standardize(features: np.ndarray) -> np.ndarray:
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("features must be a 2D array")
    mean = np.nanmean(values, axis=0, keepdims=True)
    std = np.nanstd(values, axis=0, keepdims=True)
    std = np.where(std > 1e-6, std, 1.0)
    return np.nan_to_num((values - mean) / std, copy=False).astype(np.float32)


def _normalized_distance(values: np.ndarray, index: int) -> np.ndarray:
    diff = values - values[index]
    return np.sqrt(np.mean(np.square(diff), axis=1))


def _safe_correlation(x_values: list[float], y_values: list[float]) -> float:
    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(y_values, dtype=np.float64)
    finite = np.isfinite(x) & np.isfinite(y)
    if int(np.sum(finite)) < 2:
        return float("nan")
    x = x[finite]
    y = y[finite]
    if float(np.std(x)) <= 1e-12 or float(np.std(y)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def build_match_features(
    full_observation: np.ndarray,
    current_response: np.ndarray,
    *,
    response_dim: int,
    match_feature_set: str,
) -> np.ndarray:
    if match_feature_set not in MATCH_FEATURE_SETS:
        raise ValueError(f"unknown match feature set: {match_feature_set}")
    context = np.asarray(full_observation, dtype=np.float32)[:, response_dim:]
    if match_feature_set == MATCH_CURRENT_RESPONSE:
        return np.asarray(current_response, dtype=np.float32)
    if match_feature_set == MATCH_CONTEXT:
        return context
    if match_feature_set == MATCH_CURRENT_RESPONSE_CONTEXT:
        return np.concatenate([current_response, context], axis=1).astype(np.float32)
    return np.asarray(full_observation, dtype=np.float32)


def nearest_visible_candidate_pairs(
    *,
    rows: list[dict[str, Any]],
    match_features: np.ndarray,
    targets: dict[str, np.ndarray],
    nearest_k: int,
    exclude_same_episode: bool,
) -> list[dict[str, Any]]:
    if nearest_k < 1:
        raise ValueError("nearest_k must be at least 1")
    sample_count = len(rows)
    if sample_count != int(match_features.shape[0]):
        raise ValueError("rows and match_features must have the same length")
    if sample_count < 2:
        return []

    standardized = _standardize(match_features)
    target_stds = {
        target: float(np.nanstd(np.asarray(values, dtype=np.float64)))
        for target, values in targets.items()
    }
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for left_index, left_row in enumerate(rows):
        distances = _normalized_distance(standardized, left_index)
        valid_mask = np.ones(sample_count, dtype=bool)
        valid_mask[left_index] = False
        if exclude_same_episode:
            left_episode = int(left_row["episode"])
            valid_mask &= np.asarray([int(row["episode"]) != left_episode for row in rows], dtype=bool)
        valid_indices = np.flatnonzero(valid_mask)
        if valid_indices.size == 0:
            continue
        take = min(int(nearest_k), int(valid_indices.size))
        nearest_local = np.argpartition(distances[valid_indices], take - 1)[:take]
        for right_index in valid_indices[nearest_local]:
            pair_left = min(left_index, int(right_index))
            pair_right = max(left_index, int(right_index))
            for target in TARGETS:
                key = (pair_left, pair_right, target)
                if key in seen:
                    continue
                seen.add(key)
                target_values = np.asarray(targets[target], dtype=np.float64)
                target_delta = float(abs(target_values[pair_left] - target_values[pair_right]))
                target_std = target_stds[target]
                target_z_delta = target_delta / target_std if target_std > 1e-12 else float("nan")
                candidates.append(
                    {
                        "left_index": int(pair_left),
                        "right_index": int(pair_right),
                        "target": target,
                        "visible_distance": float(distances[pair_right] if pair_left == left_index else distances[pair_left]),
                        "target_left": float(target_values[pair_left]),
                        "target_right": float(target_values[pair_right]),
                        "target_delta": target_delta,
                        "target_std": target_std,
                        "target_z_delta": float(target_z_delta),
                        "left_episode": int(rows[pair_left]["episode"]),
                        "right_episode": int(rows[pair_right]["episode"]),
                        "left_seed": int(rows[pair_left]["seed"]),
                        "right_seed": int(rows[pair_right]["seed"]),
                        "left_step": int(rows[pair_left]["step"]),
                        "right_step": int(rows[pair_right]["step"]),
                    }
                )
    return candidates


def visible_distance_threshold(
    candidates: list[dict[str, Any]],
    *,
    max_visible_distance: float | None,
    max_visible_quantile: float,
) -> float:
    if max_visible_distance is not None:
        if max_visible_distance < 0.0:
            raise ValueError("max_visible_distance must be non-negative")
        return float(max_visible_distance)
    if not 0.0 < max_visible_quantile <= 1.0:
        raise ValueError("max_visible_quantile must be in (0, 1]")
    if not candidates:
        return float("nan")
    distances = np.asarray([float(row["visible_distance"]) for row in candidates], dtype=np.float64)
    return float(np.quantile(distances, max_visible_quantile))


def physical_pair_key(row: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(row["left_seed"]),
        int(row["left_step"]),
        int(row["right_seed"]),
        int(row["right_step"]),
    )


def select_ambiguity_pairs(
    candidates: list[dict[str, Any]],
    *,
    visible_threshold: float,
    min_target_z_delta: float,
    max_pairs_per_target: int,
    max_pairs_per_physical_pair: int = 0,
) -> list[dict[str, Any]]:
    accepted = [
        {**row, "accepted": True}
        for row in candidates
        if float(row["visible_distance"]) <= float(visible_threshold)
        and float(row["target_z_delta"]) >= float(min_target_z_delta)
    ]
    if max_pairs_per_target <= 0 and max_pairs_per_physical_pair <= 0:
        return sorted(accepted, key=lambda row: (row["target"], row["visible_distance"], -row["target_z_delta"]))

    selected: list[dict[str, Any]] = []
    physical_counts: dict[tuple[int, int, int, int], int] = {}
    for target in TARGETS:
        target_rows = [row for row in accepted if str(row["target"]) == target]
        target_rows.sort(key=lambda row: (-float(row["target_z_delta"]), float(row["visible_distance"])))
        target_selected = 0
        for row in target_rows:
            if max_pairs_per_target > 0 and target_selected >= int(max_pairs_per_target):
                break
            key = physical_pair_key(row)
            if max_pairs_per_physical_pair > 0 and physical_counts.get(key, 0) >= int(max_pairs_per_physical_pair):
                continue
            selected.append(row)
            target_selected += 1
            physical_counts[key] = physical_counts.get(key, 0) + 1
    return selected


def add_feature_distances(
    pair_rows: list[dict[str, Any]],
    features: dict[str, np.ndarray],
    *,
    feature_sets: tuple[str, ...] = COMPARISON_FEATURE_SETS,
) -> list[dict[str, Any]]:
    if not pair_rows:
        return []
    standardized = {name: _standardize(features[name]) for name in feature_sets if name in features}
    output: list[dict[str, Any]] = []
    for row in pair_rows:
        left = int(row["left_index"])
        right = int(row["right_index"])
        next_row = dict(row)
        for name, values in standardized.items():
            diff = values[left] - values[right]
            next_row[f"{name}_distance"] = float(np.sqrt(np.mean(np.square(diff))))
        if CURRENT_RESPONSE in standardized and RESPONSE_HIDDEN in standardized:
            next_row["response_hidden_minus_current_response_distance"] = (
                float(next_row[f"{RESPONSE_HIDDEN}_distance"]) - float(next_row[f"{CURRENT_RESPONSE}_distance"])
            )
            next_row["response_hidden_more_separated_than_current_response"] = bool(
                float(next_row[f"{RESPONSE_HIDDEN}_distance"]) > float(next_row[f"{CURRENT_RESPONSE}_distance"])
            )
        output.append(next_row)
    return output


def summarize_ambiguity_pairs(
    *,
    checkpoint_label: str,
    probe_seed: int,
    sample_count: int,
    match_feature_set: str,
    nearest_k: int,
    visible_threshold: float,
    min_target_z_delta: float,
    candidate_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for target in TARGETS:
        candidates = [row for row in candidate_rows if str(row["target"]) == target]
        accepted = [row for row in accepted_rows if str(row["target"]) == target]
        candidate_count = len(candidates)
        accepted_count = len(accepted)
        accepted_fraction = accepted_count / candidate_count if candidate_count else 0.0
        target_deltas = [float(row["target_z_delta"]) for row in accepted]
        visible_distances = [float(row["visible_distance"]) for row in accepted]
        current_distances = [float(row.get(f"{CURRENT_RESPONSE}_distance", float("nan"))) for row in accepted]
        hidden_distances = [float(row.get(f"{RESPONSE_HIDDEN}_distance", float("nan"))) for row in accepted]
        reset_hidden_distances = [float(row.get(f"{RESET_RESPONSE_HIDDEN}_distance", float("nan"))) for row in accepted]
        hidden_more = [
            bool(row.get("response_hidden_more_separated_than_current_response", False))
            for row in accepted
        ]
        summary.append(
            {
                "checkpoint_label": checkpoint_label,
                "probe_seed": int(probe_seed),
                "sample_count": int(sample_count),
                "match_feature_set": match_feature_set,
                "nearest_k": int(nearest_k),
                "target": target,
                "candidate_count": int(candidate_count),
                "accepted_count": int(accepted_count),
                "accepted_fraction": float(accepted_fraction),
                "visible_threshold": float(visible_threshold),
                "min_target_z_delta": float(min_target_z_delta),
                "accepted_target_z_delta_mean": float(np.mean(target_deltas)) if target_deltas else float("nan"),
                "accepted_target_z_delta_max": float(np.max(target_deltas)) if target_deltas else float("nan"),
                "accepted_visible_distance_mean": (
                    float(np.mean(visible_distances)) if visible_distances else float("nan")
                ),
                "accepted_visible_distance_max": (
                    float(np.max(visible_distances)) if visible_distances else float("nan")
                ),
                "accepted_current_response_distance_mean": (
                    float(np.mean(current_distances)) if current_distances else float("nan")
                ),
                "accepted_response_hidden_distance_mean": (
                    float(np.mean(hidden_distances)) if hidden_distances else float("nan")
                ),
                "accepted_reset_response_hidden_distance_mean": (
                    float(np.mean(reset_hidden_distances)) if reset_hidden_distances else float("nan")
                ),
                "response_hidden_more_separated_fraction": (
                    float(np.mean(hidden_more)) if hidden_more else float("nan")
                ),
                "candidate_current_distance_target_corr": _safe_correlation(
                    [float(row.get(f"{CURRENT_RESPONSE}_distance", row["visible_distance"])) for row in candidates],
                    [float(row["target_z_delta"]) for row in candidates],
                ),
                "accepted_current_distance_target_corr": _safe_correlation(
                    current_distances,
                    target_deltas,
                ),
                "accepted_response_hidden_distance_target_corr": _safe_correlation(
                    hidden_distances,
                    target_deltas,
                ),
            }
        )
    return summary


def run_matched_current_response_ambiguity_audit(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    probe_seeds: tuple[int, ...],
    episodes: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    nearest_k: int,
    match_feature_set: str,
    max_visible_distance: float | None,
    max_visible_quantile: float,
    min_target_z_delta: float,
    max_pairs_per_target: int,
    max_pairs_per_physical_pair: int,
    min_accepted_pairs: int,
    exclude_same_episode: bool,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    all_candidate_rows: list[dict[str, Any]] = []
    all_pair_rows: list[dict[str, Any]] = []
    all_summary_rows: list[dict[str, Any]] = []

    for checkpoint_spec in checkpoint_specs:
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        response_dim = response_feature_dim_for_model(model)
        for probe_seed in probe_seeds:
            dataset = collect_hidden_envelope_dataset(
                model=model,
                env_config=env_config,
                episodes=episodes,
                seed=probe_seed,
                horizon_steps=horizon_steps,
                sample_stride=sample_stride,
                max_samples=max_samples,
                device=resolved_device,
            )
            match_features = build_match_features(
                dataset.features[FULL_OBSERVATION],
                dataset.features[CURRENT_RESPONSE],
                response_dim=response_dim,
                match_feature_set=match_feature_set,
            )
            candidates = nearest_visible_candidate_pairs(
                rows=dataset.rows,
                match_features=match_features,
                targets=dataset.targets,
                nearest_k=nearest_k,
                exclude_same_episode=exclude_same_episode,
            )
            threshold = visible_distance_threshold(
                candidates,
                max_visible_distance=max_visible_distance,
                max_visible_quantile=max_visible_quantile,
            )
            selected = select_ambiguity_pairs(
                candidates,
                visible_threshold=threshold,
                min_target_z_delta=min_target_z_delta,
                max_pairs_per_target=max_pairs_per_target,
                max_pairs_per_physical_pair=max_pairs_per_physical_pair,
            )
            candidates_with_distances = add_feature_distances(candidates, dataset.features)
            selected_with_distances = add_feature_distances(selected, dataset.features)
            for row in candidates_with_distances:
                row.update(
                    {
                        "checkpoint_label": checkpoint_spec.label,
                        "checkpoint_path": str(checkpoint_spec.path),
                        "probe_seed": int(probe_seed),
                        "match_feature_set": match_feature_set,
                        "visible_threshold": float(threshold),
                        "min_target_z_delta": float(min_target_z_delta),
                        "accepted": bool(
                            float(row["visible_distance"]) <= float(threshold)
                            and float(row["target_z_delta"]) >= float(min_target_z_delta)
                        ),
                    }
                )
            for row in selected_with_distances:
                row.update(
                    {
                        "checkpoint_label": checkpoint_spec.label,
                        "checkpoint_path": str(checkpoint_spec.path),
                        "probe_seed": int(probe_seed),
                        "match_feature_set": match_feature_set,
                        "visible_threshold": float(threshold),
                        "min_target_z_delta": float(min_target_z_delta),
                    }
                )
            all_candidate_rows.extend(candidates_with_distances)
            all_pair_rows.extend(selected_with_distances)
            all_summary_rows.extend(
                summarize_ambiguity_pairs(
                    checkpoint_label=checkpoint_spec.label,
                    probe_seed=probe_seed,
                    sample_count=len(dataset.rows),
                    match_feature_set=match_feature_set,
                    nearest_k=nearest_k,
                    visible_threshold=threshold,
                    min_target_z_delta=min_target_z_delta,
                    candidate_rows=candidates_with_distances,
                    accepted_rows=selected_with_distances,
                )
            )

    total_accepted = len(all_pair_rows)
    accepted_physical_pairs = {physical_pair_key(row) for row in all_pair_rows}
    accepted_physical_counts: dict[tuple[int, int, int, int], int] = {}
    for row in all_pair_rows:
        key = physical_pair_key(row)
        accepted_physical_counts[key] = accepted_physical_counts.get(key, 0) + 1
    accepted_by_target = {
        target: int(sum(1 for row in all_pair_rows if str(row["target"]) == target))
        for target in TARGETS
    }
    summary = {
        "run_type": "matched_current_response_ambiguity_audit",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "probe_seeds": probe_seeds,
        "episodes": int(episodes),
        "horizon_steps": int(horizon_steps),
        "sample_stride": int(sample_stride),
        "max_samples": max_samples,
        "nearest_k": int(nearest_k),
        "match_feature_set": match_feature_set,
        "max_visible_distance": max_visible_distance,
        "max_visible_quantile": float(max_visible_quantile),
        "min_target_z_delta": float(min_target_z_delta),
        "max_pairs_per_target": int(max_pairs_per_target),
        "max_pairs_per_physical_pair": int(max_pairs_per_physical_pair),
        "min_accepted_pairs": int(min_accepted_pairs),
        "exclude_same_episode": bool(exclude_same_episode),
        "device": str(resolved_device),
        "candidate_pair_count": int(len(all_candidate_rows)),
        "accepted_pair_count": int(total_accepted),
        "accepted_physical_pair_count": int(len(accepted_physical_pairs)),
        "accepted_max_rows_per_physical_pair": (
            int(max(accepted_physical_counts.values())) if accepted_physical_counts else 0
        ),
        "accepted_by_target": accepted_by_target,
        "ambiguity_surface_found": bool(total_accepted >= int(min_accepted_pairs)),
        "candidate_pairs_csv": run_dir / "candidate_pairs.csv",
        "matched_pairs_csv": run_dir / "matched_pairs.csv",
        "target_summary_csv": run_dir / "target_summary.csv",
    }
    write_csv_rows(run_dir / "candidate_pairs.csv", all_candidate_rows)
    write_csv_rows(run_dir / "matched_pairs.csv", all_pair_rows)
    write_csv_rows(run_dir / "target_summary.csv", all_summary_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit matched-current-response ambiguity for self-ID.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--probe-seeds", type=parse_seed_list, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--nearest-k", type=int, default=10)
    parser.add_argument("--match-feature-set", choices=MATCH_FEATURE_SETS, default=MATCH_CURRENT_RESPONSE_CONTEXT)
    parser.add_argument("--max-visible-distance", type=float, default=None)
    parser.add_argument("--max-visible-quantile", type=float, default=0.05)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--max-pairs-per-target", type=int, default=200)
    parser.add_argument("--max-pairs-per-physical-pair", type=int, default=0)
    parser.add_argument("--min-accepted-pairs", type=int, default=30)
    parser.add_argument("--allow-same-episode", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="matched_current_response_ambiguity", seed=args.probe_seeds[0])
    summary = run_matched_current_response_ambiguity_audit(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        probe_seeds=args.probe_seeds,
        episodes=args.episodes,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        nearest_k=args.nearest_k,
        match_feature_set=args.match_feature_set,
        max_visible_distance=args.max_visible_distance,
        max_visible_quantile=args.max_visible_quantile,
        min_target_z_delta=args.min_target_z_delta,
        max_pairs_per_target=args.max_pairs_per_target,
        max_pairs_per_physical_pair=args.max_pairs_per_physical_pair,
        min_accepted_pairs=args.min_accepted_pairs,
        exclude_same_episode=not args.allow_same_episode,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
