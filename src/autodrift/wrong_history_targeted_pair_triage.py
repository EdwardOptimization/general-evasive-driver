"""Target matched-current pairs for wrong-history outcome probes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key


def _bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.astype(str).str.lower().isin(("true", "1", "yes"))


def _optional_bool(frame: pd.DataFrame, key: str, default: bool = False) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=bool)
    return _bool_series(frame[key])


def _optional_float(frame: pd.DataFrame, key: str, default: float = 0.0) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=float)
    return pd.to_numeric(frame[key], errors="coerce").fillna(default)


def _optional_str(frame: pd.DataFrame, key: str, default: str = "") -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=str)
    return frame[key].fillna(default).astype(str)


def _clip01(values: pd.Series) -> pd.Series:
    return values.clip(lower=0.0, upper=1.0)


def _label_priority(labels: pd.Series) -> pd.Series:
    weights = {
        "drift_required": 0.35,
        "unavoidable": 0.25,
        "aes_feasible": 0.10,
    }
    return labels.map(weights).fillna(0.0).astype(float)


def _obstacle_bucket(row: dict[str, Any], distance_width: float, lateral_width: float) -> str:
    return source_obstacle_bucket_key(
        row,
        distance_width=distance_width,
        lateral_width=lateral_width,
    )


def build_targeted_pair_candidates(
    pairs: pd.DataFrame,
    *,
    min_target_z_delta: float,
    max_visible_distance: float | None,
    use_row_visible_threshold: bool,
    exclude_same_episode: bool,
    obstacle_distance_ceiling: float,
) -> pd.DataFrame:
    """Filter and score candidate pairs for wrong-history intervention probes."""

    frame = pairs.copy()
    target_z = _optional_float(frame, "target_z_delta")
    visible_distance = _optional_float(frame, "visible_distance")
    matched_current_pass = target_z >= float(min_target_z_delta)
    if max_visible_distance is not None:
        matched_current_pass &= visible_distance <= float(max_visible_distance)
    if use_row_visible_threshold and "visible_threshold" in frame:
        matched_current_pass &= visible_distance <= _optional_float(frame, "visible_threshold", default=float("inf"))
    if exclude_same_episode and {"left_episode", "right_episode"}.issubset(frame.columns):
        matched_current_pass &= _optional_float(frame, "left_episode", default=-1.0) != _optional_float(
            frame, "right_episode", default=-1.0
        )

    hidden_gap = _optional_float(frame, "response_hidden_minus_current_response_distance")
    hidden_gap_score = _clip01(hidden_gap)
    hidden_more = _optional_bool(frame, "response_hidden_more_separated_than_current_response").astype(float)
    target_score = _clip01(target_z / 4.0)

    obstacle_distance = _optional_float(frame, "left_obstacle_distance", default=obstacle_distance_ceiling)
    near_boundary_proxy = _clip01((float(obstacle_distance_ceiling) - obstacle_distance) / float(obstacle_distance_ceiling))
    label_score = _label_priority(_optional_str(frame, "left_obstacle_label"))

    if use_row_visible_threshold and "visible_threshold" in frame:
        visible_limit = _optional_float(frame, "visible_threshold", default=1.0).replace(0.0, np.nan)
        visible_score = (1.0 - (visible_distance / visible_limit)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        visible_score = _clip01(visible_score)
    else:
        visible_score = _clip01(1.0 - visible_distance)

    frame["matched_current_pass"] = matched_current_pass
    frame["hidden_gap_score"] = hidden_gap_score
    frame["hidden_more_score"] = hidden_more
    frame["target_z_score"] = target_score
    frame["near_boundary_proxy"] = near_boundary_proxy
    frame["label_priority_score"] = label_score
    frame["visible_similarity_score"] = visible_score
    frame["wrong_history_target_score"] = (
        hidden_gap_score
        + 0.25 * hidden_more
        + 0.35 * target_score
        + 0.30 * near_boundary_proxy
        + label_score
        + 0.15 * visible_score
    )
    if "accepted" in frame:
        frame["original_matched_pair_accepted"] = _optional_bool(frame, "accepted")
    else:
        frame["original_matched_pair_accepted"] = False
    return frame


def select_targeted_pairs(
    candidates: pd.DataFrame,
    *,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    eligible = candidates[candidates["matched_current_pass"].astype(bool)].copy()
    if eligible.empty or max_rows == 0:
        return eligible.head(0).copy()
    eligible["obstacle_bucket"] = [
        _obstacle_bucket(row, obstacle_distance_bucket_width, obstacle_lateral_bucket_width)
        for row in eligible.to_dict(orient="records")
    ]
    eligible = eligible.sort_values(
        [
            "wrong_history_target_score",
            "hidden_gap_score",
            "target_z_delta",
            "near_boundary_proxy",
            "visible_distance",
        ],
        ascending=[False, False, False, False, True],
    )

    selected: list[dict[str, Any]] = []
    probe_seed_counts: dict[int, int] = {}
    left_seed_counts: dict[int, int] = {}
    label_counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}
    for row in eligible.to_dict(orient="records"):
        if max_rows > 0 and len(selected) >= int(max_rows):
            break
        probe_seed = int(row.get("probe_seed", -1))
        left_seed = int(row.get("left_seed", -1))
        label = str(row.get("left_obstacle_label", ""))
        target = str(row.get("target", ""))
        bucket = str(row.get("obstacle_bucket", ""))
        if max_per_probe_seed > 0 and probe_seed_counts.get(probe_seed, 0) >= int(max_per_probe_seed):
            continue
        if max_per_left_seed > 0 and left_seed_counts.get(left_seed, 0) >= int(max_per_left_seed):
            continue
        if max_per_label > 0 and label_counts.get(label, 0) >= int(max_per_label):
            continue
        if max_per_target > 0 and target_counts.get(target, 0) >= int(max_per_target):
            continue
        if max_per_obstacle_bucket > 0 and bucket_counts.get(bucket, 0) >= int(max_per_obstacle_bucket):
            continue
        selected.append(row)
        probe_seed_counts[probe_seed] = probe_seed_counts.get(probe_seed, 0) + 1
        left_seed_counts[left_seed] = left_seed_counts.get(left_seed, 0) + 1
        label_counts[label] = label_counts.get(label, 0) + 1
        target_counts[target] = target_counts.get(target, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    return pd.DataFrame(selected, columns=list(eligible.columns))


def _counts(frame: pd.DataFrame, key: str) -> dict[str, int]:
    if key not in frame or frame.empty:
        return {}
    return {str(k): int(v) for k, v in frame.groupby(key, observed=True).size().to_dict().items()}


def _max_share(frame: pd.DataFrame, key: str) -> float:
    if key not in frame or frame.empty:
        return 0.0
    counts = frame.groupby(key, observed=True).size()
    return float(counts.max() / len(frame)) if len(frame) else 0.0


def summarize_triage(
    candidates: pd.DataFrame,
    targeted: pd.DataFrame,
    *,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
) -> dict[str, Any]:
    eligible = candidates[candidates["matched_current_pass"].astype(bool)]
    probe_seed_count = int(targeted["probe_seed"].nunique()) if "probe_seed" in targeted else 0
    label_count = int(targeted["left_obstacle_label"].nunique()) if "left_obstacle_label" in targeted else 0
    target_count = int(targeted["target"].nunique()) if "target" in targeted else 0
    single_seed_share = _max_share(targeted, "probe_seed")
    single_label_share = _max_share(targeted, "left_obstacle_label")
    triage_pass = (
        len(targeted) >= int(min_targeted_rows)
        and probe_seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_obstacle_label_count)
        and target_count >= int(min_target_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
    )
    return {
        "candidate_pair_count": int(len(candidates)),
        "eligible_pair_count": int(len(eligible)),
        "targeted_pair_count": int(len(targeted)),
        "targeted_probe_seed_count": probe_seed_count,
        "targeted_obstacle_label_count": label_count,
        "targeted_target_count": target_count,
        "single_seed_share": single_seed_share,
        "single_label_share": single_label_share,
        "targeted_by_probe_seed": _counts(targeted, "probe_seed"),
        "targeted_by_left_obstacle_label": _counts(targeted, "left_obstacle_label"),
        "targeted_by_target": _counts(targeted, "target"),
        "original_matched_pair_accepted_count": int(targeted["original_matched_pair_accepted"].astype(bool).sum())
        if "original_matched_pair_accepted" in targeted
        else 0,
        "score_mean": float(targeted["wrong_history_target_score"].mean()) if len(targeted) else None,
        "score_min": float(targeted["wrong_history_target_score"].min()) if len(targeted) else None,
        "score_max": float(targeted["wrong_history_target_score"].max()) if len(targeted) else None,
        "triage_pass": bool(triage_pass),
    }


def run_triage(
    *,
    candidate_pairs_csv: Path,
    min_target_z_delta: float,
    max_visible_distance: float | None,
    use_row_visible_threshold: bool,
    exclude_same_episode: bool,
    obstacle_distance_ceiling: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_csv(candidate_pairs_csv)
    candidates = build_targeted_pair_candidates(
        pairs,
        min_target_z_delta=min_target_z_delta,
        max_visible_distance=max_visible_distance,
        use_row_visible_threshold=use_row_visible_threshold,
        exclude_same_episode=exclude_same_episode,
        obstacle_distance_ceiling=obstacle_distance_ceiling,
    )
    targeted = select_targeted_pairs(
        candidates,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=obstacle_lateral_bucket_width,
    )
    candidate_path = run_dir / "target_candidates.csv"
    targeted_path = run_dir / "targeted_pairs.csv"
    write_csv_rows(candidate_path, candidates.to_dict(orient="records"))
    write_csv_rows(targeted_path, targeted.to_dict(orient="records"), fieldnames=list(targeted.columns))
    triage_summary = summarize_triage(
        candidates,
        targeted,
        min_targeted_rows=min_targeted_rows,
        min_probe_seed_count=min_probe_seed_count,
        min_obstacle_label_count=min_obstacle_label_count,
        min_target_count=min_target_count,
        max_single_seed_share=max_single_seed_share,
        max_single_label_share=max_single_label_share,
    )
    summary = {
        "run_type": "wrong_history_targeted_pair_triage",
        "candidate_pairs_csv": candidate_pairs_csv,
        "min_target_z_delta": float(min_target_z_delta),
        "max_visible_distance": max_visible_distance,
        "use_row_visible_threshold": bool(use_row_visible_threshold),
        "exclude_same_episode": bool(exclude_same_episode),
        "obstacle_distance_ceiling": float(obstacle_distance_ceiling),
        "max_rows": int(max_rows),
        "max_per_probe_seed": int(max_per_probe_seed),
        "max_per_left_seed": int(max_per_left_seed),
        "max_per_label": int(max_per_label),
        "max_per_target": int(max_per_target),
        "max_per_obstacle_bucket": int(max_per_obstacle_bucket),
        "min_targeted_rows": int(min_targeted_rows),
        "min_probe_seed_count": int(min_probe_seed_count),
        "min_obstacle_label_count": int(min_obstacle_label_count),
        "min_target_count": int(min_target_count),
        "max_single_seed_share": float(max_single_seed_share),
        "max_single_label_share": float(max_single_label_share),
        **triage_summary,
        "target_candidates_csv": candidate_path,
        "targeted_pairs_csv": targeted_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Target matched-current pairs for wrong-history probes.")
    parser.add_argument("--candidate-pairs-csv", type=Path, required=True)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--max-visible-distance", type=float, default=None)
    parser.add_argument("--disable-row-visible-threshold", action="store_true")
    parser.add_argument("--allow-same-episode", action="store_true")
    parser.add_argument("--obstacle-distance-ceiling", type=float, default=30.0)
    parser.add_argument("--max-rows", type=int, default=240)
    parser.add_argument("--max-per-probe-seed", type=int, default=90)
    parser.add_argument("--max-per-left-seed", type=int, default=8)
    parser.add_argument("--max-per-label", type=int, default=120)
    parser.add_argument("--max-per-target", type=int, default=90)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=18)
    parser.add_argument("--obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--obstacle-lateral-bucket-width", type=float, default=1.0)
    parser.add_argument("--min-targeted-rows", type=int, default=180)
    parser.add_argument("--min-probe-seed-count", type=int, default=3)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=3)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.60)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="wrong_history_targeted_pair_triage")
    summary = run_triage(
        candidate_pairs_csv=args.candidate_pairs_csv,
        min_target_z_delta=args.min_target_z_delta,
        max_visible_distance=args.max_visible_distance,
        use_row_visible_threshold=not args.disable_row_visible_threshold,
        exclude_same_episode=not args.allow_same_episode,
        obstacle_distance_ceiling=args.obstacle_distance_ceiling,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        obstacle_distance_bucket_width=args.obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=args.obstacle_lateral_bucket_width,
        min_targeted_rows=args.min_targeted_rows,
        min_probe_seed_count=args.min_probe_seed_count,
        min_obstacle_label_count=args.min_obstacle_label_count,
        min_target_count=args.min_target_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_label_share=args.max_single_label_share,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
