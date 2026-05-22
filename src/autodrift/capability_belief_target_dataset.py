"""M151 capability-belief target dataset builder."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.body_feedback_observability_audit import collect_body_feedback_dataset
from autodrift.input_observability_audit import HISTORY_MODES, TARGETS
from autodrift.p0_close_hidden_cause_audit import HIDDEN_CAUSE_GROUPS
from autodrift.p0_close_resolution_audit import read_p0_close_pair_rows, select_profile_sequence
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


CAPABILITY_TARGETS = TARGETS
P0_PER_FRAME_INDICES = tuple(range(0, 12)) + tuple(range(WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_OBS_DIM))
DOMINANT_TARGET_TO_INDEX = {name: index for index, name in enumerate(CAPABILITY_TARGETS)}
HIDDEN_GROUP_TO_INDEX = {name: index for index, name in enumerate(HIDDEN_CAUSE_GROUPS)}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def hidden_metric_by_pair(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    rows = read_csv_rows(path)
    mapping: dict[tuple[int, int], dict[str, str]] = {}
    for row in rows:
        key = (int(row["sample_i"]), int(row["sample_j"]))
        mapping[key] = row
    return mapping


def p0_history_features(observations: np.ndarray) -> np.ndarray:
    return select_profile_sequence(observations, P0_PER_FRAME_INDICES)


def build_capability_belief_dataset(
    observations: np.ndarray,
    targets: dict[str, np.ndarray],
    pair_rows: list[dict[str, Any]],
    hidden_metric_rows: dict[tuple[int, int], dict[str, str]],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    if not pair_rows:
        raise ValueError("capability-belief dataset requires at least one P0-close pair")
    p0_features = p0_history_features(observations)
    target_matrix = np.stack([targets[name] for name in CAPABILITY_TARGETS], axis=1).astype(np.float32)
    target_mean = target_matrix.mean(axis=0, keepdims=True)
    target_std = target_matrix.std(axis=0, keepdims=True) + 1e-6
    target_z = (target_matrix - target_mean) / target_std

    left_indices: list[int] = []
    right_indices: list[int] = []
    rows: list[dict[str, Any]] = []
    dominant_target_indices: list[int] = []
    dominant_hidden_indices: list[int] = []
    pair_weights: list[float] = []
    hidden_group_distances: list[list[float]] = []
    for row in pair_rows:
        sample_i = int(row["sample_i"])
        sample_j = int(row["sample_j"])
        metric = hidden_metric_rows.get((sample_i, sample_j))
        if metric is None:
            metric = hidden_metric_rows.get((sample_j, sample_i))
        if metric is None:
            raise ValueError(f"missing hidden metric row for pair {(sample_i, sample_j)}")
        left_indices.append(sample_i)
        right_indices.append(sample_j)
        dominant_target = str(metric["dominant_target"])
        dominant_hidden_group = str(metric["dominant_hidden_group"])
        dominant_target_index = DOMINANT_TARGET_TO_INDEX[dominant_target]
        dominant_hidden_index = HIDDEN_GROUP_TO_INDEX[dominant_hidden_group]
        target_delta_z = np.abs(target_z[sample_i] - target_z[sample_j])
        weight = float(np.max(target_delta_z))
        group_distances = [float(metric[f"{group}_distance"]) for group in HIDDEN_CAUSE_GROUPS]
        dominant_target_indices.append(dominant_target_index)
        dominant_hidden_indices.append(dominant_hidden_index)
        pair_weights.append(weight)
        hidden_group_distances.append(group_distances)
        rows.append(
            {
                "sample_i": sample_i,
                "sample_j": sample_j,
                "seed_i": int(row["seed_i"]),
                "seed_j": int(row["seed_j"]),
                "episode_i": int(row["episode_i"]),
                "episode_j": int(row["episode_j"]),
                "step_i": int(row["step_i"]),
                "step_j": int(row["step_j"]),
                "dominant_target": dominant_target,
                "dominant_hidden_group": dominant_hidden_group,
                "pair_weight": weight,
                "target_distance": float(metric["target_distance"]),
                **{f"{target}_i": float(target_matrix[sample_i, idx]) for idx, target in enumerate(CAPABILITY_TARGETS)},
                **{f"{target}_j": float(target_matrix[sample_j, idx]) for idx, target in enumerate(CAPABILITY_TARGETS)},
                **{f"{target}_abs_delta": float(abs(target_matrix[sample_i, idx] - target_matrix[sample_j, idx])) for idx, target in enumerate(CAPABILITY_TARGETS)},
                **{f"{group}_distance": group_distances[idx] for idx, group in enumerate(HIDDEN_CAUSE_GROUPS)},
            }
        )

    left = np.asarray(left_indices, dtype=np.int64)
    right = np.asarray(right_indices, dtype=np.int64)
    arrays: dict[str, np.ndarray] = {
        "student_p0_i": p0_features[left].astype(np.float32),
        "student_p0_j": p0_features[right].astype(np.float32),
        "teacher_capability_i": target_matrix[left].astype(np.float32),
        "teacher_capability_j": target_matrix[right].astype(np.float32),
        "teacher_capability_delta": (target_matrix[left] - target_matrix[right]).astype(np.float32),
        "teacher_capability_abs_delta_z": np.abs(target_z[left] - target_z[right]).astype(np.float32),
        "pair_weight": np.asarray(pair_weights, dtype=np.float32),
        "dominant_target_index": np.asarray(dominant_target_indices, dtype=np.int64),
        "dominant_hidden_group_index": np.asarray(dominant_hidden_indices, dtype=np.int64),
        "hidden_group_distances": np.asarray(hidden_group_distances, dtype=np.float32),
        "sample_i": left,
        "sample_j": right,
    }
    summary = summarize_capability_rows(rows)
    summary.update(
        {
            "pairs": len(rows),
            "student_feature_dim": int(arrays["student_p0_i"].shape[1]),
            "capability_target_dim": int(arrays["teacher_capability_i"].shape[1]),
            "student_inputs": "P0 deployable history only",
            "teacher_targets": "future capability envelope plus diagnostic hidden cause metadata",
        }
    )
    return arrays, rows, summary


def summarize_capability_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_counts = {target: 0 for target in CAPABILITY_TARGETS}
    hidden_counts = {group: 0 for group in HIDDEN_CAUSE_GROUPS}
    episode_pairs: set[tuple[int, int]] = set()
    for row in rows:
        target_counts[str(row["dominant_target"])] += 1
        hidden_counts[str(row["dominant_hidden_group"])] += 1
        episode_pairs.add(tuple(sorted((int(row["episode_i"]), int(row["episode_j"])))))
    total = max(len(rows), 1)
    return {
        "dominant_target_counts": target_counts,
        "dominant_target_fractions": {key: value / total for key, value in target_counts.items()},
        "dominant_hidden_group_counts": hidden_counts,
        "dominant_hidden_group_fractions": {key: value / total for key, value in hidden_counts.items()},
        "unique_episode_pairs": len(episode_pairs),
        "mean_pair_weight": float(np.mean([float(row["pair_weight"]) for row in rows])) if rows else float("nan"),
    }


def run_capability_belief_target_dataset(
    env_config_path: Path,
    pair_csv: Path,
    hidden_metrics_csv: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_window: int,
    history_mode: str,
    post_slip_beta_threshold: float,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    if history_mode not in HISTORY_MODES:
        raise ValueError("history_mode must be one of: " + ", ".join(HISTORY_MODES))
    pair_rows = read_p0_close_pair_rows(pair_csv)
    hidden_metrics = hidden_metric_by_pair(hidden_metrics_csv)
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
    arrays, rows, summary = build_capability_belief_dataset(
        observations=observations_by_window[history_window],
        targets=targets,
        pair_rows=pair_rows,
        hidden_metric_rows=hidden_metrics,
    )
    summary.update(
        {
            "seed": seed,
            "history_window": history_window,
            "pair_csv": str(pair_csv),
            "hidden_metrics_csv": str(hidden_metrics_csv),
        }
    )
    return arrays, rows, summary


def write_dataset_artifacts(
    run_dir: Path,
    args: argparse.Namespace,
    arrays: dict[str, np.ndarray],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    dataset_npz = run_dir / "capability_belief_dataset.npz"
    rows_csv = run_dir / "capability_belief_rows.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    np.savez_compressed(dataset_npz, **arrays)
    write_csv_rows(rows_csv, rows)
    write_json(
        summary_json,
        {
            "run_type": "capability_belief_target_dataset",
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
            "capability_targets": CAPABILITY_TARGETS,
            "hidden_cause_groups": tuple(HIDDEN_CAUSE_GROUPS),
            "actor_contract": "student arrays contain only deployable P0 history features",
            "teacher_contract": "capability targets and hidden group diagnostics are training-time only",
            **summary,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "capability_belief_target_dataset",
            "seed": args.seed,
            "artifacts": {
                "dataset_npz": dataset_npz,
                "rows_csv": rows_csv,
                "summary_json": summary_json,
            },
        },
    )


def combine_datasets(dataset_npzs: tuple[Path, ...], summary_paths: tuple[Path, ...]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    if not dataset_npzs:
        raise ValueError("at least one dataset npz path is required")
    loaded = [np.load(path) for path in dataset_npzs]
    keys = list(loaded[0].files)
    arrays: dict[str, np.ndarray] = {}
    for key in keys:
        arrays[key] = np.concatenate([item[key] for item in loaded], axis=0)
    summaries = [read_json(path) for path in summary_paths] if summary_paths else []
    del summaries  # Per-seed summaries are recorded in metadata; counts come from the merged arrays.
    target_counts = {target: int(np.sum(arrays["dominant_target_index"] == index)) for target, index in DOMINANT_TARGET_TO_INDEX.items()}
    hidden_counts = {group: int(np.sum(arrays["dominant_hidden_group_index"] == index)) for group, index in HIDDEN_GROUP_TO_INDEX.items()}
    total = int(arrays["pair_weight"].shape[0])
    summary = {
        "run_type": "capability_belief_target_dataset_multiseed",
        "dataset_npzs": [str(path) for path in dataset_npzs],
        "summary_paths": [str(path) for path in summary_paths],
        "pairs": total,
        "student_feature_dim": int(arrays["student_p0_i"].shape[1]),
        "capability_target_dim": int(arrays["teacher_capability_i"].shape[1]),
        "dominant_target_counts": target_counts,
        "dominant_target_fractions": {key: value / max(total, 1) for key, value in target_counts.items()},
        "dominant_hidden_group_counts": hidden_counts,
        "dominant_hidden_group_fractions": {key: value / max(total, 1) for key, value in hidden_counts.items()},
        "mean_pair_weight": float(np.mean(arrays["pair_weight"])) if total else float("nan"),
        "actor_contract": "student arrays contain only deployable P0 history features",
        "teacher_contract": "capability targets and hidden group diagnostics are training-time only",
    }
    return arrays, summary


def write_combined_artifacts(run_dir: Path, dataset_npzs: tuple[Path, ...], summary_paths: tuple[Path, ...]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays, summary = combine_datasets(dataset_npzs, summary_paths)
    np.savez_compressed(run_dir / "capability_belief_dataset.npz", **arrays)
    summary_rows = [
        {"kind": "target", "name": key, "count": count, "fraction": summary["dominant_target_fractions"][key]}
        for key, count in summary["dominant_target_counts"].items()
    ]
    summary_rows.extend(
        {"kind": "hidden_group", "name": key, "count": count, "fraction": summary["dominant_hidden_group_fractions"][key]}
        for key, count in summary["dominant_hidden_group_counts"].items()
    )
    write_csv_rows(run_dir / "coverage_summary.csv", summary_rows)
    write_json(run_dir / "summary.json", summary)


def parse_path_list(value: str) -> tuple[Path, ...]:
    paths = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
    if not paths:
        raise argparse.ArgumentTypeError("path list cannot be empty")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Build M151 capability-belief target datasets.")
    parser.add_argument("--mode", choices=("run", "combine"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--pair-csv", type=Path, default=None)
    parser.add_argument("--hidden-metrics-csv", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--history-window", type=int, default=25)
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--post-slip-beta-threshold", type=float, default=0.06)
    parser.add_argument("--dataset-npzs", type=parse_path_list, default=())
    parser.add_argument("--summary-jsons", type=parse_path_list, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "combine":
        if not args.dataset_npzs:
            raise SystemExit("--dataset-npzs is required for combine mode")
        run_dir = args.run_dir or Path("runs/m151_capability_belief_dataset_multiseed")
        write_combined_artifacts(run_dir, args.dataset_npzs, args.summary_jsons)
        print(pd.DataFrame(read_json(run_dir / "summary.json")["dominant_target_counts"], index=[0]).to_string(index=False))
        return

    if args.pair_csv is None or args.hidden_metrics_csv is None:
        raise SystemExit("--pair-csv and --hidden-metrics-csv are required for run mode")
    arrays, rows, summary = run_capability_belief_target_dataset(
        env_config_path=args.env_config,
        pair_csv=args.pair_csv,
        hidden_metrics_csv=args.hidden_metrics_csv,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        history_window=args.history_window,
        history_mode=args.history_mode,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m151_capability_belief_dataset", seed=args.seed)
    write_dataset_artifacts(run_dir, args, arrays, rows, summary)
    print(pd.DataFrame([summary]).to_string(index=False))


if __name__ == "__main__":
    main()
