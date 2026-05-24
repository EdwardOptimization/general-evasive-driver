"""Select terminal-boundary-aware wrong-history rows from scored candidates."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key


def _clip01(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(value, 0.0, 1.0))


def _label_priority(label: str) -> float:
    return {
        "drift_required": 0.30,
        "unavoidable": 0.25,
        "aes_feasible": 0.10,
    }.get(str(label), 0.0)


def low_margin_bonus(margin: float, boundary_margin: float) -> float:
    return _clip01((float(boundary_margin) - float(margin)) / max(float(boundary_margin), 1e-6))


def terminal_boundary_score(row: dict[str, Any], *, boundary_margin: float) -> float:
    margin = float(row.get("normal_min_clearance_margin", float("inf")))
    return float(
        2.0 * low_margin_bonus(margin, boundary_margin)
        + _clip01(float(row.get("action_trajectory_distance_mean", 0.0) or 0.0) / 0.12)
        + 0.75 * _clip01(float(row.get("first_action_distance", 0.0) or 0.0) / 0.12)
        + 0.50 * _clip01(float(row.get("action_trajectory_distance_max", 0.0) or 0.0) / 0.25)
        + 0.25 * _clip01(float(row.get("target_z_delta", 0.0) or 0.0) / 4.0)
        + _label_priority(str(row.get("left_obstacle_label", "")))
    )


def build_terminal_boundary_candidates(
    frame: pd.DataFrame,
    *,
    max_normal_margin: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
) -> pd.DataFrame:
    candidates = frame.copy()
    if candidates.empty:
        return candidates
    candidates["boundary_pass"] = (
        candidates["normal_min_clearance_margin"].astype(float) <= float(max_normal_margin)
    )
    candidates["soft_action_pass"] = (
        (candidates["first_action_distance"].astype(float) >= float(first_action_threshold))
        | (candidates["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
        | (candidates["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
    )
    candidates["terminal_boundary_score"] = [
        terminal_boundary_score(row, boundary_margin=max_normal_margin)
        for row in candidates.to_dict(orient="records")
    ]
    return candidates[candidates["boundary_pass"].astype(bool) & candidates["soft_action_pass"].astype(bool)].copy()


def select_terminal_boundary_rows(
    candidates: pd.DataFrame,
    *,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_offset: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    if candidates.empty or max_rows == 0:
        return candidates.head(0).copy()
    frame = candidates.copy()
    frame["obstacle_bucket"] = [
        source_obstacle_bucket_key(
            row,
            distance_width=obstacle_distance_bucket_width,
            lateral_width=obstacle_lateral_bucket_width,
        )
        for row in frame.to_dict(orient="records")
    ]
    frame = frame.sort_values(
        [
            "terminal_boundary_score",
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
        "decision_offset": {},
        "obstacle_bucket": {},
    }
    caps = {
        "probe_seed": int(max_per_probe_seed),
        "left_seed": int(max_per_left_seed),
        "left_obstacle_label": int(max_per_label),
        "target": int(max_per_target),
        "config": int(max_per_config),
        "decision_offset": int(max_per_offset),
        "obstacle_bucket": int(max_per_obstacle_bucket),
    }
    for row in frame.to_dict(orient="records"):
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
    return pd.DataFrame(selected, columns=list(frame.columns))


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


def summarize_selection(
    candidates: pd.DataFrame,
    targeted: pd.DataFrame,
    *,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_margin_le_2_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
) -> dict[str, Any]:
    trajectory_mean = (
        float(targeted["action_trajectory_distance_mean"].astype(float).mean()) if len(targeted) else None
    )
    trajectory_p90 = (
        float(targeted["action_trajectory_distance_mean"].astype(float).quantile(0.90)) if len(targeted) else None
    )
    probe_seed_count = int(targeted["probe_seed"].nunique()) if "probe_seed" in targeted else 0
    label_count = int(targeted["left_obstacle_label"].nunique()) if "left_obstacle_label" in targeted else 0
    target_count = int(targeted["target"].nunique()) if "target" in targeted else 0
    config_count = int(targeted["config"].nunique()) if "config" in targeted else 0
    single_seed_share = _max_share(targeted, "probe_seed")
    single_label_share = _max_share(targeted, "left_obstacle_label")
    single_config_share = _max_share(targeted, "config")
    rows_le_0_50 = _le_count(targeted, 0.50)
    rows_le_1_00 = _le_count(targeted, 1.00)
    rows_le_2_00 = _le_count(targeted, 2.00)
    gate_pass = (
        len(targeted) >= int(min_targeted_rows)
        and probe_seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_obstacle_label_count)
        and target_count >= int(min_target_count)
        and config_count >= int(min_config_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
        and single_config_share <= float(max_single_config_share)
        and rows_le_0_50 >= int(min_margin_le_0_50_rows)
        and rows_le_1_00 >= int(min_margin_le_1_00_rows)
        and rows_le_2_00 >= int(min_margin_le_2_00_rows)
        and trajectory_mean is not None
        and trajectory_mean >= float(min_trajectory_mean)
        and trajectory_p90 is not None
        and trajectory_p90 >= float(min_trajectory_p90)
    )
    return {
        "candidate_row_count": int(len(candidates)),
        "targeted_pair_count": int(len(targeted)),
        "targeted_probe_seed_count": probe_seed_count,
        "targeted_obstacle_label_count": label_count,
        "targeted_target_count": target_count,
        "targeted_config_count": config_count,
        "single_seed_share": single_seed_share,
        "single_label_share": single_label_share,
        "single_config_share": single_config_share,
        "targeted_rows_normal_margin_le_0_50": rows_le_0_50,
        "targeted_rows_normal_margin_le_1_00": rows_le_1_00,
        "targeted_rows_normal_margin_le_2_00": rows_le_2_00,
        "targeted_trajectory_mean": trajectory_mean,
        "targeted_trajectory_p90": trajectory_p90,
        "targeted_normal_margin_min": (
            float(targeted["normal_min_clearance_margin"].astype(float).min()) if len(targeted) else None
        ),
        "targeted_normal_margin_p50": (
            float(targeted["normal_min_clearance_margin"].astype(float).quantile(0.50)) if len(targeted) else None
        ),
        "targeted_by_probe_seed": _counts(targeted, "probe_seed"),
        "targeted_by_left_obstacle_label": _counts(targeted, "left_obstacle_label"),
        "targeted_by_target": _counts(targeted, "target"),
        "targeted_by_config": _counts(targeted, "config"),
        "targeted_by_offset": _counts(targeted, "decision_offset"),
        "terminal_boundary_gate_pass": bool(gate_pass),
    }


def run_selector(
    *,
    candidate_rows_csv: Path,
    max_normal_margin: float,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_offset: int,
    max_per_obstacle_bucket: int,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    min_margin_le_0_50_rows: int,
    min_margin_le_1_00_rows: int,
    min_margin_le_2_00_rows: int,
    min_trajectory_mean: float,
    min_trajectory_p90: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(candidate_rows_csv)
    candidates = build_terminal_boundary_candidates(
        frame,
        max_normal_margin=max_normal_margin,
        first_action_threshold=first_action_threshold,
        trajectory_mean_threshold=trajectory_mean_threshold,
        trajectory_max_threshold=trajectory_max_threshold,
    )
    targeted = select_terminal_boundary_rows(
        candidates,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_config=max_per_config,
        max_per_offset=max_per_offset,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )
    summary = {
        "run_type": "terminal_boundary_aware_selector",
        "candidate_rows_csv": candidate_rows_csv,
        "max_normal_margin": float(max_normal_margin),
        "first_action_threshold": float(first_action_threshold),
        "trajectory_mean_threshold": float(trajectory_mean_threshold),
        "trajectory_max_threshold": float(trajectory_max_threshold),
        "max_rows": int(max_rows),
        **summarize_selection(
            candidates,
            targeted,
            min_targeted_rows=min_targeted_rows,
            min_probe_seed_count=min_probe_seed_count,
            min_obstacle_label_count=min_obstacle_label_count,
            min_target_count=min_target_count,
            min_config_count=min_config_count,
            max_single_seed_share=max_single_seed_share,
            max_single_label_share=max_single_label_share,
            max_single_config_share=max_single_config_share,
            min_margin_le_0_50_rows=min_margin_le_0_50_rows,
            min_margin_le_1_00_rows=min_margin_le_1_00_rows,
            min_margin_le_2_00_rows=min_margin_le_2_00_rows,
            min_trajectory_mean=min_trajectory_mean,
            min_trajectory_p90=min_trajectory_p90,
        ),
        "terminal_boundary_candidates_csv": run_dir / "terminal_boundary_candidates.csv",
        "targeted_pairs_csv": run_dir / "targeted_pairs.csv",
    }
    write_csv_rows(run_dir / "terminal_boundary_candidates.csv", candidates.to_dict(orient="records"))
    write_csv_rows(run_dir / "targeted_pairs.csv", targeted.to_dict(orient="records"), fieldnames=list(targeted.columns))
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select terminal-boundary-aware wrong-history pairs.")
    parser.add_argument("--candidate-rows-csv", type=Path, required=True)
    parser.add_argument("--max-normal-margin", type=float, default=2.0)
    parser.add_argument("--first-action-threshold", type=float, default=0.04)
    parser.add_argument("--trajectory-mean-threshold", type=float, default=0.04)
    parser.add_argument("--trajectory-max-threshold", type=float, default=0.08)
    parser.add_argument("--max-rows", type=int, default=300)
    parser.add_argument("--max-per-probe-seed", type=int, default=60)
    parser.add_argument("--max-per-left-seed", type=int, default=6)
    parser.add_argument("--max-per-label", type=int, default=150)
    parser.add_argument("--max-per-target", type=int, default=130)
    parser.add_argument("--max-per-config", type=int, default=160)
    parser.add_argument("--max-per-offset", type=int, default=90)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=20)
    parser.add_argument("--min-targeted-rows", type=int, default=240)
    parser.add_argument("--min-probe-seed-count", type=int, default=6)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--min-config-count", type=int, default=2)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.70)
    parser.add_argument("--max-single-config-share", type=float, default=0.70)
    parser.add_argument("--min-margin-le-0-50-rows", type=int, default=40)
    parser.add_argument("--min-margin-le-1-00-rows", type=int, default=100)
    parser.add_argument("--min-margin-le-2-00-rows", type=int, default=180)
    parser.add_argument("--min-trajectory-mean", type=float, default=0.04)
    parser.add_argument("--min-trajectory-p90", type=float, default=0.08)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="terminal_boundary_aware_selector")
    summary = run_selector(
        candidate_rows_csv=args.candidate_rows_csv,
        max_normal_margin=args.max_normal_margin,
        first_action_threshold=args.first_action_threshold,
        trajectory_mean_threshold=args.trajectory_mean_threshold,
        trajectory_max_threshold=args.trajectory_max_threshold,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_config=args.max_per_config,
        max_per_offset=args.max_per_offset,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        min_targeted_rows=args.min_targeted_rows,
        min_probe_seed_count=args.min_probe_seed_count,
        min_obstacle_label_count=args.min_obstacle_label_count,
        min_target_count=args.min_target_count,
        min_config_count=args.min_config_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_label_share=args.max_single_label_share,
        max_single_config_share=args.max_single_config_share,
        min_margin_le_0_50_rows=args.min_margin_le_0_50_rows,
        min_margin_le_1_00_rows=args.min_margin_le_1_00_rows,
        min_margin_le_2_00_rows=args.min_margin_le_2_00_rows,
        min_trajectory_mean=args.min_trajectory_mean,
        min_trajectory_p90=args.min_trajectory_p90,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
