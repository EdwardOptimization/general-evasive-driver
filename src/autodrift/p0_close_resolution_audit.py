"""M149 resolution audit for M148 P0-close ambiguous pairs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.body_feedback_observability_audit import collect_body_feedback_dataset
from autodrift.input_observability_audit import HISTORY_MODES, TARGETS
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


P0_W25 = "p0_w25"
P0_W50 = "p0_w50"
P0_PLUS_RAW_WHEEL_W25 = "p0_plus_raw_wheel_w25"
P0_PLUS_RAW_WHEEL_VPARALLEL_W25 = "p0_plus_raw_wheel_vparallel_w25"
EXTRA_RAW_WHEEL_W25 = "extra_raw_wheel_w25"
EXTRA_VPARALLEL_W25 = "extra_vparallel_w25"
EXTRA_RAW_WHEEL_VPARALLEL_W25 = "extra_raw_wheel_vparallel_w25"

P0_CLOSE_RESOLUTION_PROFILE_ORDER = (
    P0_W25,
    P0_W50,
    P0_PLUS_RAW_WHEEL_W25,
    P0_PLUS_RAW_WHEEL_VPARALLEL_W25,
    EXTRA_RAW_WHEEL_W25,
    EXTRA_VPARALLEL_W25,
    EXTRA_RAW_WHEEL_VPARALLEL_W25,
)


@dataclass(frozen=True)
class ResolutionProfileSpec:
    name: str
    history_window: int
    per_frame_indices: tuple[int, ...]
    role: str
    description: str


def p0_close_resolution_profile_specs(base_history_window: int = 25, long_history_window: int = 50) -> tuple[ResolutionProfileSpec, ...]:
    context_indices = tuple(range(WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_OBS_DIM))
    p0_indices = tuple(range(0, 12)) + context_indices
    raw_wheel = (12, 13)
    vparallel = (14, 15)
    return (
        ResolutionProfileSpec(
            name=P0_W25,
            history_window=base_history_window,
            per_frame_indices=p0_indices,
            role="base",
            description="M148 current P0 close surface",
        ),
        ResolutionProfileSpec(
            name=P0_W50,
            history_window=long_history_window,
            per_frame_indices=p0_indices,
            role="long_history_candidate",
            description="current P0 with longer raw history",
        ),
        ResolutionProfileSpec(
            name=P0_PLUS_RAW_WHEEL_W25,
            history_window=base_history_window,
            per_frame_indices=tuple(range(0, 14)) + context_indices,
            role="full_candidate",
            description="P0 plus raw front/rear wheel-speed proxy",
        ),
        ResolutionProfileSpec(
            name=P0_PLUS_RAW_WHEEL_VPARALLEL_W25,
            history_window=base_history_window,
            per_frame_indices=tuple(range(0, 16)) + context_indices,
            role="full_candidate_diagnostic",
            description="P0 plus raw wheel-speed proxy and local ground-speed diagnostic slots",
        ),
        ResolutionProfileSpec(
            name=EXTRA_RAW_WHEEL_W25,
            history_window=base_history_window,
            per_frame_indices=raw_wheel,
            role="extra_only",
            description="raw front/rear wheel-speed proxy only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_VPARALLEL_W25,
            history_window=base_history_window,
            per_frame_indices=vparallel,
            role="extra_only_diagnostic",
            description="front/rear local ground-speed diagnostic slots only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_RAW_WHEEL_VPARALLEL_W25,
            history_window=base_history_window,
            per_frame_indices=raw_wheel + vparallel,
            role="extra_only_diagnostic",
            description="raw wheel-speed proxy plus local ground-speed diagnostic slots only",
        ),
    )


def resolution_profile_spec_rows(base_history_window: int = 25, long_history_window: int = 50) -> list[dict[str, Any]]:
    return [
        {
            "profile": spec.name,
            "history_window": spec.history_window,
            "feature_count_per_frame": len(spec.per_frame_indices),
            "indices": " ".join(str(index) for index in spec.per_frame_indices),
            "role": spec.role,
            "description": spec.description,
        }
        for spec in p0_close_resolution_profile_specs(base_history_window, long_history_window)
    ]


def select_profile_sequence(observations: np.ndarray, per_frame_indices: tuple[int, ...]) -> np.ndarray:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2 or observations.shape[1] % WHEEL_HUMAN_VIEW_OBS_DIM != 0:
        raise ValueError("observations must be flattened 85-value history frames")
    frame_count = observations.shape[1] // WHEEL_HUMAN_VIEW_OBS_DIM
    frames = observations.reshape(observations.shape[0], frame_count, WHEEL_HUMAN_VIEW_OBS_DIM)
    return frames[:, :, list(per_frame_indices)].reshape(observations.shape[0], -1).astype(np.float32)


def build_profile_features_by_name(
    observations_by_window: dict[int, np.ndarray],
    base_history_window: int = 25,
    long_history_window: int = 50,
) -> dict[str, np.ndarray]:
    features: dict[str, np.ndarray] = {}
    for spec in p0_close_resolution_profile_specs(base_history_window, long_history_window):
        if spec.history_window not in observations_by_window:
            raise ValueError(f"missing observations for history window {spec.history_window}")
        features[spec.name] = select_profile_sequence(observations_by_window[spec.history_window], spec.per_frame_indices)
    return features


def read_p0_close_pair_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return [row for row in rows if row.get("surface") == "p0_close_target_divergent"]


def _standardized(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    return (values - values.mean(axis=0, keepdims=True)) / (values.std(axis=0, keepdims=True) + 1e-6)


def _pair_distances(features: np.ndarray, pair_rows: list[dict[str, Any]]) -> np.ndarray:
    normalized = _standardized(features)
    distances: list[float] = []
    for row in pair_rows:
        index_i = int(row["sample_i"])
        index_j = int(row["sample_j"])
        diff = normalized[index_i] - normalized[index_j]
        distances.append(float(np.sqrt(np.mean(np.square(diff)))))
    return np.asarray(distances, dtype=np.float64)


def _pearson_corr(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or float(np.std(left)) <= 1e-12 or float(np.std(right)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def _top_alignment(feature_distances: np.ndarray, target_distances: np.ndarray, top_fraction: float) -> float:
    if len(feature_distances) == 0:
        return float("nan")
    target_threshold = float(np.quantile(target_distances, 1.0 - top_fraction))
    feature_threshold = float(np.quantile(feature_distances, 1.0 - top_fraction))
    target_top = target_distances >= target_threshold
    feature_top = feature_distances >= feature_threshold
    if int(np.sum(target_top)) == 0:
        return float("nan")
    return float(np.sum(target_top & feature_top) / np.sum(target_top))


def evaluate_p0_close_resolution(
    observations_by_window: dict[int, np.ndarray],
    targets: dict[str, np.ndarray],
    pair_rows: list[dict[str, Any]],
    base_history_window: int = 25,
    long_history_window: int = 50,
    min_full_gain: float = 0.05,
    min_full_ratio: float = 1.25,
    min_extra_distance: float = 0.25,
    top_fraction: float = 0.25,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not pair_rows:
        return [], []
    features = build_profile_features_by_name(observations_by_window, base_history_window, long_history_window)
    target_matrix = np.stack([targets[name] for name in TARGETS], axis=1).astype(np.float32)
    target_distances = _pair_distances(target_matrix, pair_rows)
    base_distances = _pair_distances(features[P0_W25], pair_rows)
    spec_by_name = {spec.name: spec for spec in p0_close_resolution_profile_specs(base_history_window, long_history_window)}
    pair_metric_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for profile in P0_CLOSE_RESOLUTION_PROFILE_ORDER:
        spec = spec_by_name[profile]
        distances = _pair_distances(features[profile], pair_rows)
        gains = distances - base_distances
        ratios = distances / (base_distances + 1e-6)
        if spec.role.startswith("extra_only"):
            resolved = distances >= min_extra_distance
        elif profile == P0_W25:
            resolved = np.zeros_like(distances, dtype=bool)
        else:
            resolved = (gains >= min_full_gain) & (ratios >= min_full_ratio)
        for index, row in enumerate(pair_rows):
            pair_metric_rows.append(
                {
                    "rank": int(row.get("rank", index + 1)),
                    "profile": profile,
                    "role": spec.role,
                    "sample_i": int(row["sample_i"]),
                    "sample_j": int(row["sample_j"]),
                    "episode_i": int(row["episode_i"]),
                    "episode_j": int(row["episode_j"]),
                    "step_i": int(row["step_i"]),
                    "step_j": int(row["step_j"]),
                    "p0_feature_distance": float(base_distances[index]),
                    "profile_feature_distance": float(distances[index]),
                    "distance_gain_vs_p0": float(gains[index]),
                    "distance_ratio_vs_p0": float(ratios[index]),
                    "target_distance": float(target_distances[index]),
                    "resolved": bool(resolved[index]),
                }
            )
        summary_rows.append(
            {
                "profile": profile,
                "role": spec.role,
                "pairs": int(len(pair_rows)),
                "mean_feature_distance": float(np.mean(distances)),
                "median_feature_distance": float(np.median(distances)),
                "mean_gain_vs_p0": float(np.mean(gains)),
                "median_gain_vs_p0": float(np.median(gains)),
                "positive_gain_fraction": float(np.mean(gains > 0.0)),
                "resolved_fraction": float(np.mean(resolved)),
                "feature_target_corr": _pearson_corr(distances, target_distances),
                "target_top_feature_top_overlap": _top_alignment(distances, target_distances, top_fraction),
                "min_full_gain": min_full_gain,
                "min_full_ratio": min_full_ratio,
                "min_extra_distance": min_extra_distance,
                "top_fraction": top_fraction,
            }
        )
    return pair_metric_rows, summary_rows


def run_p0_close_resolution_audit(
    env_config_path: Path,
    pair_csv: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    base_history_window: int,
    long_history_window: int,
    history_mode: str,
    post_slip_beta_threshold: float,
    min_full_gain: float,
    min_full_ratio: float,
    min_extra_distance: float,
    top_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if history_mode not in HISTORY_MODES:
        raise ValueError("history_mode must be one of: " + ", ".join(HISTORY_MODES))
    pair_rows = read_p0_close_pair_rows(pair_csv)
    observations_by_window, targets, _, _ = collect_body_feedback_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=(base_history_window, long_history_window),
        history_mode=history_mode,
        post_slip_beta_threshold=post_slip_beta_threshold,
    )
    pair_metric_rows, summary_rows = evaluate_p0_close_resolution(
        observations_by_window=observations_by_window,
        targets=targets,
        pair_rows=pair_rows,
        base_history_window=base_history_window,
        long_history_window=long_history_window,
        min_full_gain=min_full_gain,
        min_full_ratio=min_full_ratio,
        min_extra_distance=min_extra_distance,
        top_fraction=top_fraction,
    )
    return pair_rows, pair_metric_rows, summary_rows


def aggregate_resolution_summaries(summary_paths: tuple[Path, ...]) -> dict[str, Any]:
    summaries = [read_json(path) for path in summary_paths]
    if not summaries:
        raise ValueError("at least one summary path is required")
    by_profile: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        for row in summary["resolution_summary"]:
            by_profile.setdefault(str(row["profile"]), []).append(row)
    aggregate_rows: list[dict[str, Any]] = []
    for profile in P0_CLOSE_RESOLUTION_PROFILE_ORDER:
        rows = by_profile.get(profile, [])
        if not rows:
            continue
        aggregate_rows.append(
            {
                "profile": profile,
                "role": str(rows[0]["role"]),
                "seed_count": len(rows),
                "pairs": int(sum(int(row["pairs"]) for row in rows)),
                "mean_feature_distance": float(np.mean([float(row["mean_feature_distance"]) for row in rows])),
                "mean_gain_vs_p0": float(np.mean([float(row["mean_gain_vs_p0"]) for row in rows])),
                "positive_gain_fraction": float(np.mean([float(row["positive_gain_fraction"]) for row in rows])),
                "resolved_fraction": float(np.mean([float(row["resolved_fraction"]) for row in rows])),
                "feature_target_corr": float(np.mean([float(row["feature_target_corr"]) for row in rows])),
                "target_top_feature_top_overlap": float(
                    np.mean([float(row["target_top_feature_top_overlap"]) for row in rows])
                ),
            }
        )
    return {
        "run_type": "p0_close_resolution_audit_multiseed",
        "seeds": [int(summary["seed"]) for summary in summaries],
        "summary_paths": [str(path) for path in summary_paths],
        "resolution_summary": aggregate_rows,
    }


def write_resolution_artifacts(
    run_dir: Path,
    args: argparse.Namespace,
    pair_rows: list[dict[str, Any]],
    pair_metric_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    pairs_csv = run_dir / "input_p0_close_pairs.csv"
    pair_metrics_csv = run_dir / "resolution_pair_metrics.csv"
    summary_csv = run_dir / "resolution_summary.csv"
    profile_spec_csv = run_dir / "profile_spec.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(pairs_csv, pair_rows)
    write_csv_rows(pair_metrics_csv, pair_metric_rows)
    write_csv_rows(summary_csv, summary_rows)
    write_csv_rows(profile_spec_csv, resolution_profile_spec_rows(args.base_history_window, args.long_history_window))
    write_json(
        summary_json,
        {
            "run_type": "p0_close_resolution_audit",
            "env_config": args.env_config,
            "pair_csv": args.pair_csv,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "max_samples": args.max_samples,
            "base_history_window": args.base_history_window,
            "long_history_window": args.long_history_window,
            "history_mode": args.history_mode,
            "post_slip_beta_threshold": args.post_slip_beta_threshold,
            "resolution_summary": summary_rows,
            "pair_count": len(pair_rows),
            "input_exclusions": (
                "mu, slip_ratio, tire_force, TTC, path_error, heading_error, "
                "feasibility labels, required clearance"
            ),
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "p0_close_resolution_audit",
            "env_config": args.env_config,
            "seed": args.seed,
            "pair_csv": args.pair_csv,
            "artifacts": {
                "input_pairs_csv": pairs_csv,
                "resolution_pair_metrics_csv": pair_metrics_csv,
                "resolution_summary_csv": summary_csv,
                "profile_spec_csv": profile_spec_csv,
                "summary_json": summary_json,
            },
        },
    )


def write_multiseed_artifacts(run_dir: Path, summary_paths: tuple[Path, ...]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = aggregate_resolution_summaries(summary_paths)
    write_csv_rows(run_dir / "resolution_summary.csv", summary["resolution_summary"])
    write_json(run_dir / "summary.json", summary)


def parse_summary_paths(value: str) -> tuple[Path, ...]:
    paths = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
    if not paths:
        raise argparse.ArgumentTypeError("summary path list cannot be empty")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M149 P0-close resolution audit.")
    parser.add_argument("--mode", choices=("run", "aggregate"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--pair-csv", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--base-history-window", type=int, default=25)
    parser.add_argument("--long-history-window", type=int, default=50)
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--post-slip-beta-threshold", type=float, default=0.06)
    parser.add_argument("--min-full-gain", type=float, default=0.05)
    parser.add_argument("--min-full-ratio", type=float, default=1.25)
    parser.add_argument("--min-extra-distance", type=float, default=0.25)
    parser.add_argument("--top-fraction", type=float, default=0.25)
    parser.add_argument("--summary-jsons", type=parse_summary_paths, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "aggregate":
        if not args.summary_jsons:
            raise SystemExit("--summary-jsons is required for aggregate mode")
        run_dir = args.run_dir or Path("runs/m149_p0_close_resolution_multiseed")
        write_multiseed_artifacts(run_dir, args.summary_jsons)
        print(pd.DataFrame(read_json(run_dir / "summary.json")["resolution_summary"]).to_string(index=False))
        return

    if args.pair_csv is None:
        raise SystemExit("--pair-csv is required for run mode")
    pair_rows, pair_metric_rows, summary_rows = run_p0_close_resolution_audit(
        env_config_path=args.env_config,
        pair_csv=args.pair_csv,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        base_history_window=args.base_history_window,
        long_history_window=args.long_history_window,
        history_mode=args.history_mode,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
        min_full_gain=args.min_full_gain,
        min_full_ratio=args.min_full_ratio,
        min_extra_distance=args.min_extra_distance,
        top_fraction=args.top_fraction,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m149_p0_close_resolution", seed=args.seed)
    write_resolution_artifacts(run_dir, args, pair_rows, pair_metric_rows, summary_rows)
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
