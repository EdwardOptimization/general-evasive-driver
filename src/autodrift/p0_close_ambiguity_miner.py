"""M148 miner for P0-close future-envelope ambiguity."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.ambiguous_history_resolution_audit import (
    H1_BODY_ONLY,
    P0_CURRENT_BASELINE,
    build_resolution_feature_profiles,
)
from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.body_feedback_observability_audit import collect_body_feedback_dataset, sample_phase_summary
from autodrift.input_observability_audit import HISTORY_MODES, TARGETS


def _standardize(features: np.ndarray) -> np.ndarray:
    features = np.asarray(features, dtype=np.float64)
    return (features - features.mean(axis=0, keepdims=True)) / (features.std(axis=0, keepdims=True) + 1e-6)


def _distance_matrix(features: np.ndarray) -> np.ndarray:
    normalized = _standardize(features)
    squared = np.sum(np.square(normalized), axis=1, keepdims=True)
    distances = np.sqrt(np.maximum(squared + squared.T - 2.0 * (normalized @ normalized.T), 0.0))
    return distances / np.sqrt(max(normalized.shape[1], 1))


def _select_search_indices(sample_count: int, max_search_samples: int, seed: int) -> np.ndarray:
    if sample_count < 2:
        raise ValueError("at least two samples are required for ambiguity mining")
    if sample_count > max_search_samples:
        rng = np.random.default_rng(seed)
        return np.sort(rng.choice(sample_count, size=max_search_samples, replace=False))
    return np.arange(sample_count)


def _source_diversity(rows: list[dict[str, Any]]) -> dict[str, int]:
    episodes: set[int] = set()
    episode_pairs: set[tuple[int, int]] = set()
    step_pairs: set[tuple[int, int, int, int]] = set()
    for row in rows:
        episode_i = int(row["episode_i"])
        episode_j = int(row["episode_j"])
        step_i = int(row["step_i"])
        step_j = int(row["step_j"])
        episodes.update((episode_i, episode_j))
        episode_pairs.add(tuple(sorted((episode_i, episode_j))))
        step_pairs.add((episode_i, step_i, episode_j, step_j))
    return {
        "unique_episodes": len(episodes),
        "unique_episode_pairs": len(episode_pairs),
        "unique_step_pairs": len(step_pairs),
    }


def mine_close_ambiguity_pairs(
    observations: np.ndarray,
    targets: dict[str, np.ndarray],
    sample_rows: list[dict[str, Any]],
    seed: int,
    max_search_samples: int = 450,
    feature_quantile: float = 0.05,
    target_quantile: float = 0.90,
    max_export_pairs: int = 80,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if len(sample_rows) != observations.shape[0]:
        raise ValueError("sample_rows and observations must have matching sample counts")
    if any(len(value) != observations.shape[0] for value in targets.values()):
        raise ValueError("all target arrays must match observation sample count")
    selected = _select_search_indices(len(sample_rows), max_search_samples=max_search_samples, seed=seed)
    feature_profiles = build_resolution_feature_profiles(observations)
    target_matrix = np.stack([targets[name] for name in TARGETS], axis=1).astype(np.float32)
    h1_dist = _distance_matrix(feature_profiles[H1_BODY_ONLY][selected])
    p0_dist = _distance_matrix(feature_profiles[P0_CURRENT_BASELINE][selected])
    target_dist = _distance_matrix(target_matrix[selected])
    episodes = np.asarray([int(sample_rows[int(index)]["episode"]) for index in selected], dtype=np.int64)
    valid = np.triu(np.ones_like(target_dist, dtype=bool), k=1)
    valid &= episodes[:, None] != episodes[None, :]
    if not np.any(valid):
        raise ValueError("no valid cross-episode pairs were available")

    target_threshold = float(np.quantile(target_dist[valid], target_quantile))
    h1_threshold = float(np.quantile(h1_dist[valid], feature_quantile))
    p0_threshold = float(np.quantile(p0_dist[valid], feature_quantile))
    target_divergent = target_dist >= target_threshold
    h1_close = h1_dist <= h1_threshold
    p0_close = p0_dist <= p0_threshold
    h1_accepted = valid & h1_close & target_divergent
    p0_accepted = valid & p0_close & target_divergent
    both_accepted = h1_accepted & p0_accepted
    h1_only = h1_accepted & ~p0_close
    p0_only = p0_accepted & ~h1_close

    def rows_for(mask: np.ndarray, surface: str) -> list[dict[str, Any]]:
        local_pairs = np.argwhere(mask)
        if len(local_pairs) == 0:
            return []
        scores = target_dist[mask] / (p0_dist[mask] + 1e-6)
        order = np.argsort(-scores)
        output_rows: list[dict[str, Any]] = []
        for rank, local_index in enumerate(order[:max_export_pairs], start=1):
            local_i, local_j = local_pairs[int(local_index)]
            global_i = int(selected[int(local_i)])
            global_j = int(selected[int(local_j)])
            row_i = sample_rows[global_i]
            row_j = sample_rows[global_j]
            output_rows.append(
                {
                    "rank": rank,
                    "surface": surface,
                    "sample_i": global_i,
                    "sample_j": global_j,
                    "seed_i": int(row_i["seed"]),
                    "seed_j": int(row_j["seed"]),
                    "episode_i": int(row_i["episode"]),
                    "episode_j": int(row_j["episode"]),
                    "step_i": int(row_i["step"]),
                    "step_j": int(row_j["step"]),
                    "phase_i": str(row_i["sample_phase"]),
                    "phase_j": str(row_j["sample_phase"]),
                    "h1_feature_distance": float(h1_dist[local_i, local_j]),
                    "p0_feature_distance": float(p0_dist[local_i, local_j]),
                    "target_distance": float(target_dist[local_i, local_j]),
                    "h1_close": bool(h1_close[local_i, local_j]),
                    "p0_close": bool(p0_close[local_i, local_j]),
                    "future_braking_i": float(row_i["future_braking_deceleration"]),
                    "future_braking_j": float(row_j["future_braking_deceleration"]),
                    "future_yaw_i": float(row_i["future_yaw_response"]),
                    "future_yaw_j": float(row_j["future_yaw_response"]),
                    "future_lateral_i": float(row_i["future_lateral_accel_response"]),
                    "future_lateral_j": float(row_j["future_lateral_accel_response"]),
                }
            )
        return output_rows

    h1_rows = rows_for(h1_accepted, "h1_close_target_divergent")
    p0_rows = rows_for(p0_accepted, "p0_close_target_divergent")
    exported_rows = h1_rows + p0_rows
    h1_diversity = _source_diversity(h1_rows)
    p0_diversity = _source_diversity(p0_rows)
    summary = {
        "searched_samples": int(len(selected)),
        "valid_pairs": int(np.sum(valid)),
        "feature_quantile": feature_quantile,
        "target_quantile": target_quantile,
        "h1_feature_distance_threshold": h1_threshold,
        "p0_feature_distance_threshold": p0_threshold,
        "target_distance_threshold": target_threshold,
        "h1_close_target_divergent_count": int(np.sum(h1_accepted)),
        "p0_close_target_divergent_count": int(np.sum(p0_accepted)),
        "both_h1_p0_close_target_divergent_count": int(np.sum(both_accepted)),
        "h1_only_target_divergent_count": int(np.sum(h1_only)),
        "p0_only_target_divergent_count": int(np.sum(p0_only)),
        "h1_unique_episodes": h1_diversity["unique_episodes"],
        "h1_unique_episode_pairs": h1_diversity["unique_episode_pairs"],
        "h1_unique_step_pairs": h1_diversity["unique_step_pairs"],
        "p0_unique_episodes": p0_diversity["unique_episodes"],
        "p0_unique_episode_pairs": p0_diversity["unique_episode_pairs"],
        "p0_unique_step_pairs": p0_diversity["unique_step_pairs"],
        "h1_exported_pairs": len(h1_rows),
        "p0_exported_pairs": len(p0_rows),
    }
    summary_rows = [
        {"surface": "h1_close_target_divergent", "accepted_count": summary["h1_close_target_divergent_count"], **h1_diversity},
        {"surface": "p0_close_target_divergent", "accepted_count": summary["p0_close_target_divergent_count"], **p0_diversity},
        {
            "surface": "both_h1_p0_close_target_divergent",
            "accepted_count": summary["both_h1_p0_close_target_divergent_count"],
            "unique_episodes": 0,
            "unique_episode_pairs": 0,
            "unique_step_pairs": 0,
        },
        {
            "surface": "h1_only_target_divergent",
            "accepted_count": summary["h1_only_target_divergent_count"],
            "unique_episodes": 0,
            "unique_episode_pairs": 0,
            "unique_step_pairs": 0,
        },
        {
            "surface": "p0_only_target_divergent",
            "accepted_count": summary["p0_only_target_divergent_count"],
            "unique_episodes": 0,
            "unique_episode_pairs": 0,
            "unique_step_pairs": 0,
        },
    ]
    return exported_rows, summary_rows, summary


def run_p0_close_ambiguity_miner(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    history_mode: str,
    post_slip_beta_threshold: float,
    max_search_samples: int,
    feature_quantile: float,
    target_quantile: float,
    max_export_pairs: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    if history_mode not in HISTORY_MODES:
        raise ValueError("history_mode must be one of: " + ", ".join(HISTORY_MODES))
    observations_by_window, targets, _, sample_rows = collect_body_feedback_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=(history_window,),
        history_mode=history_mode,
        post_slip_beta_threshold=post_slip_beta_threshold,
    )
    pair_rows, summary_rows, summary = mine_close_ambiguity_pairs(
        observations=observations_by_window[history_window],
        targets=targets,
        sample_rows=sample_rows,
        seed=seed + 59,
        max_search_samples=max_search_samples,
        feature_quantile=feature_quantile,
        target_quantile=target_quantile,
        max_export_pairs=max_export_pairs,
    )
    summary["phase_summary"] = sample_phase_summary(sample_rows)
    summary["history_window"] = history_window
    return pair_rows, summary_rows, summary, sample_rows


def aggregate_miner_summaries(summary_paths: tuple[Path, ...]) -> dict[str, Any]:
    summaries = [read_json(path) for path in summary_paths]
    if not summaries:
        raise ValueError("at least one summary path is required")
    metrics = (
        "h1_close_target_divergent_count",
        "p0_close_target_divergent_count",
        "both_h1_p0_close_target_divergent_count",
        "h1_only_target_divergent_count",
        "p0_only_target_divergent_count",
        "h1_unique_episode_pairs",
        "p0_unique_episode_pairs",
    )
    aggregate = {f"mean_{metric}": float(np.mean([float(summary[metric]) for summary in summaries])) for metric in metrics}
    totals = {f"total_{metric}": int(sum(int(summary[metric]) for summary in summaries)) for metric in metrics}
    return {
        "run_type": "p0_close_ambiguity_miner_multiseed",
        "seeds": [int(summary["seed"]) for summary in summaries],
        "summary_paths": [str(path) for path in summary_paths],
        "metric_means": aggregate,
        "metric_totals": totals,
        "h1_to_p0_count_ratio": (
            float(totals["total_p0_close_target_divergent_count"])
            / max(float(totals["total_h1_close_target_divergent_count"]), 1.0)
        ),
    }


def write_miner_artifacts(
    run_dir: Path,
    args: argparse.Namespace,
    pair_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    pairs_csv = run_dir / "accepted_pairs.csv"
    summary_csv = run_dir / "surface_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(pairs_csv, pair_rows)
    write_csv_rows(summary_csv, summary_rows)
    write_json(
        summary_json,
        {
            "run_type": "p0_close_ambiguity_miner",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "max_samples": args.max_samples,
            "history_window": args.history_window,
            "history_mode": args.history_mode,
            "post_slip_beta_threshold": args.post_slip_beta_threshold,
            **summary,
            "input_exclusions": (
                "mu, slip_ratio, vparallel, tire_force, TTC, path_error, "
                "heading_error, feasibility labels, required clearance"
            ),
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "p0_close_ambiguity_miner",
            "env_config": args.env_config,
            "seed": args.seed,
            "artifacts": {
                "accepted_pairs_csv": pairs_csv,
                "surface_summary_csv": summary_csv,
                "summary_json": summary_json,
            },
        },
    )


def write_multiseed_artifacts(run_dir: Path, summary_paths: tuple[Path, ...]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = aggregate_miner_summaries(summary_paths)
    rows = [{"metric": key, "value": value} for key, value in sorted(summary["metric_means"].items())]
    rows.extend({"metric": key, "value": value} for key, value in sorted(summary["metric_totals"].items()))
    rows.append({"metric": "h1_to_p0_count_ratio", "value": summary["h1_to_p0_count_ratio"]})
    write_csv_rows(run_dir / "aggregate_metric_summary.csv", rows)
    write_json(run_dir / "summary.json", summary)


def parse_summary_paths(value: str) -> tuple[Path, ...]:
    paths = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
    if not paths:
        raise argparse.ArgumentTypeError("summary path list cannot be empty")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M148 P0-close ambiguity miner.")
    parser.add_argument("--mode", choices=("run", "aggregate"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--history-window", type=int, default=25)
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--post-slip-beta-threshold", type=float, default=0.06)
    parser.add_argument("--max-search-samples", type=int, default=450)
    parser.add_argument("--feature-quantile", type=float, default=0.05)
    parser.add_argument("--target-quantile", type=float, default=0.90)
    parser.add_argument("--max-export-pairs", type=int, default=80)
    parser.add_argument("--summary-jsons", type=parse_summary_paths, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "aggregate":
        if not args.summary_jsons:
            raise SystemExit("--summary-jsons is required for aggregate mode")
        run_dir = args.run_dir or Path("runs/m148_p0_close_ambiguity_multiseed")
        write_multiseed_artifacts(run_dir, args.summary_jsons)
        print(pd.DataFrame([read_json(run_dir / "summary.json")["metric_totals"]]).to_string(index=False))
        return

    pair_rows, summary_rows, summary, _ = run_p0_close_ambiguity_miner(
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        history_window=args.history_window,
        history_mode=args.history_mode,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
        max_search_samples=args.max_search_samples,
        feature_quantile=args.feature_quantile,
        target_quantile=args.target_quantile,
        max_export_pairs=args.max_export_pairs,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m148_p0_close_ambiguity", seed=args.seed)
    write_miner_artifacts(run_dir, args, pair_rows, summary_rows, summary)
    print(pd.DataFrame(summary_rows).to_string(index=False))
    print(pd.DataFrame([summary]).to_string(index=False))


if __name__ == "__main__":
    main()
