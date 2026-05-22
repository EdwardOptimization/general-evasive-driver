"""M150 hidden-cause audit for P0-close target-divergent pairs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.body_feedback_observability_audit import collect_body_feedback_dataset
from autodrift.input_observability_audit import HISTORY_MODES, TARGETS
from autodrift.p0_close_resolution_audit import read_p0_close_pair_rows


HIDDEN_FIELDS = (
    "mu",
    "mass_scale",
    "inertia_scale",
    "cg_shift",
    "front_tire_stiffness_scale",
    "rear_tire_stiffness_scale",
    "drive_scale",
    "brake_scale",
    "steer_tau_scale",
    "drive_tau_scale",
)

HIDDEN_CAUSE_GROUPS: dict[str, tuple[str, ...]] = {
    "friction": ("mu",),
    "braking_authority": ("brake_scale",),
    "drive_authority": ("drive_scale",),
    "tire_lateral_authority": ("front_tire_stiffness_scale", "rear_tire_stiffness_scale"),
    "mass_geometry": ("mass_scale", "inertia_scale", "cg_shift"),
    "actuator_delay": ("steer_tau_scale", "drive_tau_scale"),
}


def collect_hidden_cause_dataset(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    post_slip_beta_threshold: float,
) -> list[dict[str, Any]]:
    """Collect rows matching the M148 ordering and include hidden diagnostics."""

    _, _, _, sample_rows = collect_body_feedback_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=(1,),
        history_mode="raw",
        post_slip_beta_threshold=post_slip_beta_threshold,
    )
    # collect_body_feedback_dataset keeps rows intentionally deployable. Re-run
    # hidden values from deterministic env info is heavier; for M150 we instead
    # require the collector rows below to be extended by the environment info.
    # This guard catches stale callers after implementation changes.
    missing = [field for field in HIDDEN_FIELDS if sample_rows and field not in sample_rows[0]]
    if missing:
        raise ValueError(
            "hidden-cause rows are missing fields "
            + ", ".join(missing)
            + "; collect_body_feedback_dataset must include diagnostic hidden fields"
        )
    return sample_rows


def _standardized_matrix(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> np.ndarray:
    matrix = np.asarray([[float(row[field]) for field in fields] for row in rows], dtype=np.float64)
    return (matrix - matrix.mean(axis=0, keepdims=True)) / (matrix.std(axis=0, keepdims=True) + 1e-6)


def _raw_matrix(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> np.ndarray:
    return np.asarray([[float(row[field]) for field in fields] for row in rows], dtype=np.float64)


def _pair_index_arrays(pair_rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    left = np.asarray([int(row["sample_i"]) for row in pair_rows], dtype=np.int64)
    right = np.asarray([int(row["sample_j"]) for row in pair_rows], dtype=np.int64)
    return left, right


def _pearson_corr(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or float(np.std(left)) <= 1e-12 or float(np.std(right)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def _top_overlap(candidate: np.ndarray, target: np.ndarray, top_fraction: float) -> float:
    if len(candidate) == 0:
        return float("nan")
    target_threshold = float(np.quantile(target, 1.0 - top_fraction))
    candidate_threshold = float(np.quantile(candidate, 1.0 - top_fraction))
    target_top = target >= target_threshold
    candidate_top = candidate >= candidate_threshold
    if int(np.sum(target_top)) == 0:
        return float("nan")
    return float(np.sum(target_top & candidate_top) / np.sum(target_top))


def evaluate_hidden_causes(
    sample_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    top_fraction: float = 0.25,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not pair_rows:
        return [], [], [], []
    left, right = _pair_index_arrays(pair_rows)
    max_index = max(int(np.max(left)), int(np.max(right)))
    if max_index >= len(sample_rows):
        raise ValueError("pair rows reference sample indices outside the hidden-cause dataset")

    hidden_z = _standardized_matrix(sample_rows, HIDDEN_FIELDS)
    target_z = _standardized_matrix(sample_rows, TARGETS)
    target_raw = _raw_matrix(sample_rows, TARGETS)
    hidden_field_index = {field: index for index, field in enumerate(HIDDEN_FIELDS)}

    target_diff_z = np.abs(target_z[left] - target_z[right])
    target_diff_raw = np.abs(target_raw[left] - target_raw[right])
    target_distance = np.sqrt(np.mean(np.square(target_diff_z), axis=1))
    dominant_target_indices = np.argmax(target_diff_z, axis=1)

    group_distances: dict[str, np.ndarray] = {}
    for group, fields in HIDDEN_CAUSE_GROUPS.items():
        indices = [hidden_field_index[field] for field in fields]
        diffs = hidden_z[left][:, indices] - hidden_z[right][:, indices]
        group_distances[group] = np.sqrt(np.mean(np.square(diffs), axis=1))
    group_names = tuple(HIDDEN_CAUSE_GROUPS)
    group_matrix = np.stack([group_distances[group] for group in group_names], axis=1)
    dominant_group_indices = np.argmax(group_matrix, axis=1)

    pair_metric_rows: list[dict[str, Any]] = []
    for pair_index, row in enumerate(pair_rows):
        output: dict[str, Any] = {
            "rank": int(row.get("rank", pair_index + 1)),
            "sample_i": int(row["sample_i"]),
            "sample_j": int(row["sample_j"]),
            "episode_i": int(row["episode_i"]),
            "episode_j": int(row["episode_j"]),
            "step_i": int(row["step_i"]),
            "step_j": int(row["step_j"]),
            "target_distance": float(target_distance[pair_index]),
            "dominant_target": TARGETS[int(dominant_target_indices[pair_index])],
            "dominant_hidden_group": group_names[int(dominant_group_indices[pair_index])],
            "dominant_hidden_group_distance": float(group_matrix[pair_index, dominant_group_indices[pair_index]]),
        }
        for target_index, target in enumerate(TARGETS):
            output[f"{target}_abs_diff"] = float(target_diff_raw[pair_index, target_index])
            output[f"{target}_z_abs_diff"] = float(target_diff_z[pair_index, target_index])
        for group in group_names:
            output[f"{group}_distance"] = float(group_distances[group][pair_index])
        pair_metric_rows.append(output)

    group_summary_rows: list[dict[str, Any]] = []
    for group in group_names:
        distances = group_distances[group]
        group_summary_rows.append(
            {
                "hidden_group": group,
                "fields": " ".join(HIDDEN_CAUSE_GROUPS[group]),
                "pairs": int(len(pair_rows)),
                "mean_distance": float(np.mean(distances)),
                "median_distance": float(np.median(distances)),
                "feature_target_corr": _pearson_corr(distances, target_distance),
                "target_top_group_top_overlap": _top_overlap(distances, target_distance, top_fraction),
                "dominant_fraction": float(np.mean([row["dominant_hidden_group"] == group for row in pair_metric_rows])),
            }
        )

    target_summary_rows: list[dict[str, Any]] = []
    for target_index, target in enumerate(TARGETS):
        target_summary_rows.append(
            {
                "target": target,
                "pairs": int(len(pair_rows)),
                "mean_abs_diff": float(np.mean(target_diff_raw[:, target_index])),
                "median_abs_diff": float(np.median(target_diff_raw[:, target_index])),
                "mean_z_abs_diff": float(np.mean(target_diff_z[:, target_index])),
                "median_z_abs_diff": float(np.median(target_diff_z[:, target_index])),
                "dominant_fraction": float(np.mean(dominant_target_indices == target_index)),
            }
        )

    dominant_cross_rows: list[dict[str, Any]] = []
    for group in group_names:
        for target_index, target in enumerate(TARGETS):
            mask = [
                row["dominant_hidden_group"] == group and row["dominant_target"] == target
                for row in pair_metric_rows
            ]
            dominant_cross_rows.append(
                {
                    "hidden_group": group,
                    "target": target,
                    "pair_fraction": float(np.mean(mask)),
                    "pair_count": int(np.sum(mask)),
                }
            )
    return pair_metric_rows, group_summary_rows, target_summary_rows, dominant_cross_rows


def aggregate_hidden_cause_summaries(summary_paths: tuple[Path, ...]) -> dict[str, Any]:
    summaries = [read_json(path) for path in summary_paths]
    if not summaries:
        raise ValueError("at least one summary path is required")
    group_rows_by_name: dict[str, list[dict[str, Any]]] = {}
    target_rows_by_name: dict[str, list[dict[str, Any]]] = {}
    for summary in summaries:
        for row in summary["hidden_group_summary"]:
            group_rows_by_name.setdefault(str(row["hidden_group"]), []).append(row)
        for row in summary["target_summary"]:
            target_rows_by_name.setdefault(str(row["target"]), []).append(row)

    group_rows: list[dict[str, Any]] = []
    for group in HIDDEN_CAUSE_GROUPS:
        rows = group_rows_by_name.get(group, [])
        if not rows:
            continue
        group_rows.append(
            {
                "hidden_group": group,
                "seed_count": len(rows),
                "pairs": int(sum(int(row["pairs"]) for row in rows)),
                "mean_distance": float(np.mean([float(row["mean_distance"]) for row in rows])),
                "feature_target_corr": float(np.mean([float(row["feature_target_corr"]) for row in rows])),
                "target_top_group_top_overlap": float(
                    np.mean([float(row["target_top_group_top_overlap"]) for row in rows])
                ),
                "dominant_fraction": float(np.mean([float(row["dominant_fraction"]) for row in rows])),
            }
        )
    target_rows: list[dict[str, Any]] = []
    for target in TARGETS:
        rows = target_rows_by_name.get(target, [])
        if not rows:
            continue
        target_rows.append(
            {
                "target": target,
                "seed_count": len(rows),
                "pairs": int(sum(int(row["pairs"]) for row in rows)),
                "mean_abs_diff": float(np.mean([float(row["mean_abs_diff"]) for row in rows])),
                "mean_z_abs_diff": float(np.mean([float(row["mean_z_abs_diff"]) for row in rows])),
                "dominant_fraction": float(np.mean([float(row["dominant_fraction"]) for row in rows])),
            }
        )
    return {
        "run_type": "p0_close_hidden_cause_audit_multiseed",
        "seeds": [int(summary["seed"]) for summary in summaries],
        "summary_paths": [str(path) for path in summary_paths],
        "hidden_group_summary": group_rows,
        "target_summary": target_rows,
    }


def run_hidden_cause_audit(
    env_config_path: Path,
    pair_csv: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    post_slip_beta_threshold: float,
    top_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pair_rows = read_p0_close_pair_rows(pair_csv)
    sample_rows = collect_hidden_cause_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        post_slip_beta_threshold=post_slip_beta_threshold,
    )
    pair_metric_rows, group_summary_rows, target_summary_rows, dominant_cross_rows = evaluate_hidden_causes(
        sample_rows=sample_rows,
        pair_rows=pair_rows,
        top_fraction=top_fraction,
    )
    return pair_rows, pair_metric_rows, group_summary_rows, target_summary_rows, dominant_cross_rows


def write_hidden_cause_artifacts(
    run_dir: Path,
    args: argparse.Namespace,
    pair_rows: list[dict[str, Any]],
    pair_metric_rows: list[dict[str, Any]],
    group_summary_rows: list[dict[str, Any]],
    target_summary_rows: list[dict[str, Any]],
    dominant_cross_rows: list[dict[str, Any]],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "input_p0_close_pairs.csv", pair_rows)
    write_csv_rows(run_dir / "hidden_pair_metrics.csv", pair_metric_rows)
    write_csv_rows(run_dir / "hidden_group_summary.csv", group_summary_rows)
    write_csv_rows(run_dir / "target_summary.csv", target_summary_rows)
    write_csv_rows(run_dir / "dominant_hidden_target_cross.csv", dominant_cross_rows)
    write_json(
        run_dir / "summary.json",
        {
            "run_type": "p0_close_hidden_cause_audit",
            "env_config": args.env_config,
            "pair_csv": args.pair_csv,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "max_samples": args.max_samples,
            "post_slip_beta_threshold": args.post_slip_beta_threshold,
            "hidden_fields": HIDDEN_FIELDS,
            "hidden_cause_groups": HIDDEN_CAUSE_GROUPS,
            "pair_count": len(pair_rows),
            "hidden_group_summary": group_summary_rows,
            "target_summary": target_summary_rows,
            "diagnostic_only": (
                "hidden parameters are used only for offline cause analysis and teacher-target design; "
                "they are not actor inputs"
            ),
        },
    )
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "p0_close_hidden_cause_audit",
            "env_config": args.env_config,
            "seed": args.seed,
            "pair_csv": args.pair_csv,
            "artifacts": {
                "input_pairs_csv": run_dir / "input_p0_close_pairs.csv",
                "hidden_pair_metrics_csv": run_dir / "hidden_pair_metrics.csv",
                "hidden_group_summary_csv": run_dir / "hidden_group_summary.csv",
                "target_summary_csv": run_dir / "target_summary.csv",
                "dominant_hidden_target_cross_csv": run_dir / "dominant_hidden_target_cross.csv",
                "summary_json": run_dir / "summary.json",
            },
        },
    )


def write_multiseed_artifacts(run_dir: Path, summary_paths: tuple[Path, ...]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = aggregate_hidden_cause_summaries(summary_paths)
    write_csv_rows(run_dir / "hidden_group_summary.csv", summary["hidden_group_summary"])
    write_csv_rows(run_dir / "target_summary.csv", summary["target_summary"])
    write_json(run_dir / "summary.json", summary)


def parse_summary_paths(value: str) -> tuple[Path, ...]:
    paths = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
    if not paths:
        raise argparse.ArgumentTypeError("summary path list cannot be empty")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M150 P0-close hidden-cause audit.")
    parser.add_argument("--mode", choices=("run", "aggregate"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--pair-csv", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--post-slip-beta-threshold", type=float, default=0.06)
    parser.add_argument("--top-fraction", type=float, default=0.25)
    parser.add_argument("--summary-jsons", type=parse_summary_paths, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "aggregate":
        if not args.summary_jsons:
            raise SystemExit("--summary-jsons is required for aggregate mode")
        run_dir = args.run_dir or Path("runs/m150_p0_close_hidden_cause_multiseed")
        write_multiseed_artifacts(run_dir, args.summary_jsons)
        print(pd.DataFrame(read_json(run_dir / "summary.json")["hidden_group_summary"]).to_string(index=False))
        return

    if args.pair_csv is None:
        raise SystemExit("--pair-csv is required for run mode")
    pair_rows, pair_metric_rows, group_summary_rows, target_summary_rows, dominant_cross_rows = run_hidden_cause_audit(
        env_config_path=args.env_config,
        pair_csv=args.pair_csv,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
        top_fraction=args.top_fraction,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m150_p0_close_hidden_cause", seed=args.seed)
    write_hidden_cause_artifacts(
        run_dir,
        args,
        pair_rows,
        pair_metric_rows,
        group_summary_rows,
        target_summary_rows,
        dominant_cross_rows,
    )
    print(pd.DataFrame(group_summary_rows).to_string(index=False))
    print(pd.DataFrame(target_summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
