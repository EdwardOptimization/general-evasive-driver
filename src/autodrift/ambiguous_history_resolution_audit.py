"""M147 audit for resolving M146 ambiguous body-history pairs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.body_feedback_observability_audit import (
    H1_BODY_ONLY,
    collect_body_feedback_dataset,
)
from autodrift.input_observability_audit import HISTORY_MODES, TARGETS, parse_history_windows
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


P0_CURRENT_BASELINE = "p0_current_baseline"
H1_PLUS_RAW_WHEEL = "h1_plus_raw_wheel"
H1_PLUS_RAW_WHEEL_VPARALLEL = "h1_plus_raw_wheel_vparallel"
EXTRA_VX = "extra_vx"
EXTRA_VY = "extra_vy"
EXTRA_VX_VY = "extra_vx_vy"
EXTRA_STEER_RATE_PROXY = "extra_steer_rate_proxy"
EXTRA_P0_MISSING = "extra_p0_missing"
EXTRA_RAW_WHEEL = "extra_raw_wheel"
EXTRA_VPARALLEL = "extra_vparallel"

RESOLUTION_PROFILE_ORDER = (
    H1_BODY_ONLY,
    P0_CURRENT_BASELINE,
    H1_PLUS_RAW_WHEEL,
    H1_PLUS_RAW_WHEEL_VPARALLEL,
    EXTRA_VX,
    EXTRA_VY,
    EXTRA_VX_VY,
    EXTRA_STEER_RATE_PROXY,
    EXTRA_P0_MISSING,
    EXTRA_RAW_WHEEL,
    EXTRA_VPARALLEL,
)


@dataclass(frozen=True)
class ResolutionProfileSpec:
    name: str
    description: str
    per_frame_indices: tuple[int, ...]
    role: str


def resolution_profile_specs() -> tuple[ResolutionProfileSpec, ...]:
    context_indices = tuple(range(WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_OBS_DIM))
    h1_response = (
        2,  # yaw_rate
        3,  # ax
        4,  # ay
        5,  # steering actuator state
        7,  # throttle actuator state
        8,  # brake actuator state
        9,  # previous steering command
        10,  # previous physical throttle command
        11,  # previous physical brake command
    )
    raw_wheel = (12, 13)
    vparallel = (14, 15)
    return (
        ResolutionProfileSpec(
            name=H1_BODY_ONLY,
            description="M146 H1 body-history baseline used to mine ambiguous pairs",
            per_frame_indices=h1_response + context_indices,
            role="base",
        ),
        ResolutionProfileSpec(
            name=P0_CURRENT_BASELINE,
            description="current no-wheel actor contract: H1 plus vx/vy and steer-rate proxy",
            per_frame_indices=tuple(range(0, 12)) + context_indices,
            role="full_candidate",
        ),
        ResolutionProfileSpec(
            name=H1_PLUS_RAW_WHEEL,
            description="H1 plus raw front/rear wheel-speed proxy",
            per_frame_indices=h1_response + raw_wheel + context_indices,
            role="full_candidate",
        ),
        ResolutionProfileSpec(
            name=H1_PLUS_RAW_WHEEL_VPARALLEL,
            description="H1 plus raw wheel-speed proxy and local ground-speed diagnostic slots",
            per_frame_indices=h1_response + raw_wheel + vparallel + context_indices,
            role="full_candidate_diagnostic",
        ),
        ResolutionProfileSpec(
            name=EXTRA_VX,
            description="additional longitudinal ego-speed cue only",
            per_frame_indices=(0,),
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_VY,
            description="additional lateral ego-speed cue only",
            per_frame_indices=(1,),
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_VX_VY,
            description="additional body-frame ego velocity cues only",
            per_frame_indices=(0, 1),
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_STEER_RATE_PROXY,
            description="additional steering-rate proxy only",
            per_frame_indices=(6,),
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_P0_MISSING,
            description="all P0 channels absent from H1: vx, vy, steer-rate proxy",
            per_frame_indices=(0, 1, 6),
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_RAW_WHEEL,
            description="raw front/rear wheel-speed proxy only",
            per_frame_indices=raw_wheel,
            role="extra_only",
        ),
        ResolutionProfileSpec(
            name=EXTRA_VPARALLEL,
            description="front/rear local ground-speed diagnostic slots only",
            per_frame_indices=vparallel,
            role="extra_only_diagnostic",
        ),
    )


def resolution_profile_spec_rows() -> list[dict[str, Any]]:
    return [
        {
            "profile": spec.name,
            "feature_count_per_frame": len(spec.per_frame_indices),
            "indices": " ".join(str(index) for index in spec.per_frame_indices),
            "description": spec.description,
            "role": spec.role,
        }
        for spec in resolution_profile_specs()
    ]


def resolution_profile_spec_by_name() -> dict[str, ResolutionProfileSpec]:
    return {spec.name: spec for spec in resolution_profile_specs()}


def resolution_history_sequence(frames: np.ndarray, profile: str) -> np.ndarray:
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3 or frames.shape[2] != WHEEL_HUMAN_VIEW_OBS_DIM:
        raise ValueError(
            "resolution history sequences require frames with shape "
            f"(samples, steps, {WHEEL_HUMAN_VIEW_OBS_DIM})"
        )
    specs = resolution_profile_spec_by_name()
    if profile not in specs:
        raise ValueError("unknown resolution profile: " + profile)
    return frames[:, :, list(specs[profile].per_frame_indices)].astype(np.float32)


def build_resolution_feature_profiles(observations: np.ndarray) -> dict[str, np.ndarray]:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] % WHEEL_HUMAN_VIEW_OBS_DIM != 0:
        raise ValueError(
            "ambiguous-history resolution audit requires one or more concatenated "
            f"{WHEEL_HUMAN_VIEW_OBS_DIM}-value wheel-response frames"
        )
    frame_count = observations.shape[1] // WHEEL_HUMAN_VIEW_OBS_DIM
    frames = observations.reshape(observations.shape[0], frame_count, WHEEL_HUMAN_VIEW_OBS_DIM)
    return {
        spec.name: resolution_history_sequence(frames, spec.name).reshape(observations.shape[0], -1).astype(np.float32)
        for spec in resolution_profile_specs()
    }


def read_pair_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _standardized_features(features: np.ndarray) -> np.ndarray:
    features = np.asarray(features, dtype=np.float64)
    return (features - features.mean(axis=0, keepdims=True)) / (features.std(axis=0, keepdims=True) + 1e-6)


def _pair_distances(features: np.ndarray, pair_rows: list[dict[str, Any]]) -> np.ndarray:
    normalized = _standardized_features(features)
    distances: list[float] = []
    for row in pair_rows:
        index_i = int(row["sample_i"])
        index_j = int(row["sample_j"])
        if index_i >= normalized.shape[0] or index_j >= normalized.shape[0]:
            raise ValueError("pair row references a sample index outside the collected dataset")
        diff = normalized[index_i] - normalized[index_j]
        distances.append(float(np.sqrt(np.mean(np.square(diff)))))
    return np.asarray(distances, dtype=np.float64)


def _target_distances(target_matrix: np.ndarray, pair_rows: list[dict[str, Any]]) -> np.ndarray:
    return _pair_distances(target_matrix, pair_rows)


def _pearson_corr(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    if len(left) < 2 or float(np.std(left)) <= 1e-12 or float(np.std(right)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def evaluate_resolution_profiles(
    observations: np.ndarray,
    targets: dict[str, np.ndarray],
    pair_rows: list[dict[str, Any]],
    min_full_gain: float = 0.05,
    min_full_ratio: float = 1.25,
    min_extra_distance: float = 0.25,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not pair_rows:
        return [], []
    profiles = build_resolution_feature_profiles(observations)
    target_matrix = np.stack([targets[name] for name in TARGETS], axis=1).astype(np.float32)
    target_distances = _target_distances(target_matrix, pair_rows)
    h1_distances = _pair_distances(profiles[H1_BODY_ONLY], pair_rows)
    specs = resolution_profile_spec_by_name()
    pair_metric_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for profile in RESOLUTION_PROFILE_ORDER:
        distances = _pair_distances(profiles[profile], pair_rows)
        gains = distances - h1_distances
        ratios = distances / (h1_distances + 1e-6)
        spec = specs[profile]
        if spec.role.startswith("extra_only"):
            resolved = distances >= min_extra_distance
        elif profile == H1_BODY_ONLY:
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
                    "phase_i": str(row.get("phase_i", "")),
                    "phase_j": str(row.get("phase_j", "")),
                    "h1_feature_distance": float(h1_distances[index]),
                    "profile_feature_distance": float(distances[index]),
                    "distance_gain_vs_h1": float(gains[index]),
                    "distance_ratio_vs_h1": float(ratios[index]),
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
                "mean_gain_vs_h1": float(np.mean(gains)),
                "median_gain_vs_h1": float(np.median(gains)),
                "positive_gain_fraction": float(np.mean(gains > 0.0)),
                "resolved_fraction": float(np.mean(resolved)),
                "feature_target_corr": _pearson_corr(distances, target_distances),
                "min_full_gain": min_full_gain,
                "min_full_ratio": min_full_ratio,
                "min_extra_distance": min_extra_distance,
            }
        )
    return pair_metric_rows, summary_rows


def run_ambiguous_history_resolution_audit(
    env_config_path: Path,
    pair_csv: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    history_mode: str,
    post_slip_beta_threshold: float,
    min_full_gain: float,
    min_full_ratio: float,
    min_extra_distance: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if history_mode not in HISTORY_MODES:
        raise ValueError("history_mode must be one of: " + ", ".join(HISTORY_MODES))
    pair_rows = read_pair_rows(pair_csv)
    observations_by_window, targets, _, _ = collect_body_feedback_dataset(
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
    pair_metric_rows, summary_rows = evaluate_resolution_profiles(
        observations=observations_by_window[history_window],
        targets=targets,
        pair_rows=pair_rows,
        min_full_gain=min_full_gain,
        min_full_ratio=min_full_ratio,
        min_extra_distance=min_extra_distance,
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
    for profile in RESOLUTION_PROFILE_ORDER:
        rows = by_profile.get(profile, [])
        if not rows:
            continue
        role = str(rows[0]["role"])
        aggregate_rows.append(
            {
                "profile": profile,
                "role": role,
                "seed_count": len(rows),
                "pairs": int(sum(int(row["pairs"]) for row in rows)),
                "mean_feature_distance": float(np.mean([float(row["mean_feature_distance"]) for row in rows])),
                "mean_gain_vs_h1": float(np.mean([float(row["mean_gain_vs_h1"]) for row in rows])),
                "positive_gain_fraction": float(np.mean([float(row["positive_gain_fraction"]) for row in rows])),
                "resolved_fraction": float(np.mean([float(row["resolved_fraction"]) for row in rows])),
                "feature_target_corr": float(np.mean([float(row["feature_target_corr"]) for row in rows])),
            }
        )
    return {
        "run_type": "ambiguous_history_resolution_audit_multiseed",
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
    pairs_csv = run_dir / "input_ambiguous_pairs.csv"
    pair_metrics_csv = run_dir / "resolution_pair_metrics.csv"
    summary_csv = run_dir / "resolution_summary.csv"
    profile_spec_csv = run_dir / "profile_spec.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(pairs_csv, pair_rows)
    write_csv_rows(pair_metrics_csv, pair_metric_rows)
    write_csv_rows(summary_csv, summary_rows)
    write_csv_rows(profile_spec_csv, resolution_profile_spec_rows())
    write_json(
        summary_json,
        {
            "run_type": "ambiguous_history_resolution_audit",
            "env_config": args.env_config,
            "pair_csv": args.pair_csv,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_window": args.history_window,
            "history_mode": args.history_mode,
            "post_slip_beta_threshold": args.post_slip_beta_threshold,
            "resolution_profiles": RESOLUTION_PROFILE_ORDER,
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
            "run_type": "ambiguous_history_resolution_audit",
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


def write_resolution_multiseed_artifacts(run_dir: Path, summary_paths: tuple[Path, ...]) -> None:
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
    parser = argparse.ArgumentParser(description="Run the M147 ambiguous-history resolution audit.")
    parser.add_argument("--mode", choices=("run", "aggregate"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--pair-csv", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--history-window", type=int, default=25)
    parser.add_argument("--history-windows", type=parse_history_windows, default=(25,))
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--post-slip-beta-threshold", type=float, default=0.06)
    parser.add_argument("--min-full-gain", type=float, default=0.05)
    parser.add_argument("--min-full-ratio", type=float, default=1.25)
    parser.add_argument("--min-extra-distance", type=float, default=0.25)
    parser.add_argument("--summary-jsons", type=parse_summary_paths, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "aggregate":
        if not args.summary_jsons:
            raise SystemExit("--summary-jsons is required for aggregate mode")
        run_dir = args.run_dir or Path("runs/m147_ambiguous_history_resolution_multiseed")
        write_resolution_multiseed_artifacts(run_dir, args.summary_jsons)
        print(pd.DataFrame(read_json(run_dir / "summary.json")["resolution_summary"]).to_string(index=False))
        return

    if args.pair_csv is None:
        raise SystemExit("--pair-csv is required for run mode")
    pair_rows, pair_metric_rows, summary_rows = run_ambiguous_history_resolution_audit(
        env_config_path=args.env_config,
        pair_csv=args.pair_csv,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        history_window=args.history_window,
        history_mode=args.history_mode,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
        min_full_gain=args.min_full_gain,
        min_full_ratio=args.min_full_ratio,
        min_extra_distance=args.min_extra_distance,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m147_ambiguous_history_resolution", seed=args.seed)
    write_resolution_artifacts(run_dir, args, pair_rows, pair_metric_rows, summary_rows)
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
