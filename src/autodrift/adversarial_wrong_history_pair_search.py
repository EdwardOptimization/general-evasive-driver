"""Search stronger wrong histories for near-boundary left states."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key


JOIN_KEYS = ["probe_seed", "target", "left_seed", "left_step"]


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


def _clip01(values: pd.Series) -> pd.Series:
    return values.clip(lower=0.0, upper=1.0)


def _obstacle_bucket(row: dict[str, Any], distance_width: float, lateral_width: float) -> str:
    return source_obstacle_bucket_key(
        row,
        distance_width=distance_width,
        lateral_width=lateral_width,
    )


def _counts(frame: pd.DataFrame, key: str) -> dict[str, int]:
    if key not in frame or frame.empty:
        return {}
    return {str(k): int(v) for k, v in frame.groupby(key, observed=True).size().to_dict().items()}


def _max_share(frame: pd.DataFrame, key: str) -> float:
    if key not in frame or frame.empty:
        return 0.0
    counts = frame.groupby(key, observed=True).size()
    return float(counts.max() / len(frame)) if len(frame) else 0.0


def build_adversarial_search_candidates(
    *,
    near_boundary_rows: pd.DataFrame,
    candidate_pairs: pd.DataFrame,
    normal_margin_ceiling: float,
    min_target_z_delta: float,
    use_row_visible_threshold: bool,
    exclude_same_episode: bool,
) -> pd.DataFrame:
    anchors = near_boundary_rows.copy()
    anchors = anchors[anchors["variant"].astype(str) == "wrong_matched_history"].copy()
    normal_margin = _optional_float(anchors, "normal_margin")
    normal_success = _optional_bool(anchors, "normal_success")
    near_boundary = normal_success & (normal_margin > 0.0) & (normal_margin <= float(normal_margin_ceiling))
    anchors = anchors[near_boundary].copy()
    anchor_columns = [
        *JOIN_KEYS,
        "normal_margin",
        "normal_success",
        "left_obstacle_label",
        "normal_return_observed",
        "normal_margin_observed",
    ]
    for column in anchor_columns:
        if column not in anchors:
            anchors[column] = pd.NA
    anchors = anchors[anchor_columns].drop_duplicates(JOIN_KEYS)

    pairs = candidate_pairs.copy()
    target_z = _optional_float(pairs, "target_z_delta")
    visible_distance = _optional_float(pairs, "visible_distance")
    eligible = target_z >= float(min_target_z_delta)
    if use_row_visible_threshold and "visible_threshold" in pairs:
        eligible &= visible_distance <= _optional_float(pairs, "visible_threshold", default=float("inf"))
    if exclude_same_episode and {"left_episode", "right_episode"}.issubset(pairs.columns):
        eligible &= _optional_float(pairs, "left_episode", default=-1.0) != _optional_float(
            pairs, "right_episode", default=-1.0
        )
    pairs = pairs[eligible].copy()

    merged = pairs.merge(anchors, on=JOIN_KEYS, how="inner", suffixes=("", "_anchor"), validate="many_to_one")
    if merged.empty:
        return merged

    hidden_gap = _optional_float(merged, "response_hidden_minus_current_response_distance")
    hidden_more = _optional_bool(merged, "response_hidden_more_separated_than_current_response").astype(float)
    target_score = _clip01(_optional_float(merged, "target_z_delta") / 4.0)
    visible_score = _clip01(1.0 - _optional_float(merged, "visible_distance"))
    if use_row_visible_threshold and "visible_threshold" in merged:
        threshold = _optional_float(merged, "visible_threshold", default=1.0).replace(0.0, pd.NA)
        visible_score = _clip01((1.0 - (_optional_float(merged, "visible_distance") / threshold)).fillna(0.0))
    right_label = merged.get("right_obstacle_label", pd.Series([""] * len(merged), index=merged.index)).astype(str)
    left_label = merged.get("left_obstacle_label", pd.Series([""] * len(merged), index=merged.index)).astype(str)
    label_mismatch = (right_label != left_label).astype(float)
    normal_margin_score = _clip01((float(normal_margin_ceiling) - _optional_float(merged, "normal_margin")) / float(normal_margin_ceiling))
    merged["adversarial_wrong_history_score"] = (
        _clip01(hidden_gap)
        + 0.25 * hidden_more
        + 0.35 * target_score
        + 0.20 * visible_score
        + 0.20 * label_mismatch
        + 0.30 * normal_margin_score
    )
    merged["anchor_key"] = (
        merged["probe_seed"].astype(str)
        + "|"
        + merged["target"].astype(str)
        + "|"
        + merged["left_seed"].astype(str)
        + "|"
        + merged["left_step"].astype(str)
    )
    return merged


def select_adversarial_pairs(
    candidates: pd.DataFrame,
    *,
    max_rows: int,
    max_per_anchor: int,
    max_per_probe_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    if candidates.empty or max_rows == 0:
        return candidates.head(0).copy()
    frame = candidates.copy()
    frame["obstacle_bucket"] = [
        _obstacle_bucket(row, obstacle_distance_bucket_width, obstacle_lateral_bucket_width)
        for row in frame.to_dict(orient="records")
    ]
    frame = frame.sort_values(
        [
            "adversarial_wrong_history_score",
            "response_hidden_minus_current_response_distance",
            "target_z_delta",
            "visible_distance",
        ],
        ascending=[False, False, False, True],
    )
    selected: list[dict[str, Any]] = []
    anchor_counts: dict[str, int] = {}
    seed_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}
    for row in frame.to_dict(orient="records"):
        if max_rows > 0 and len(selected) >= int(max_rows):
            break
        anchor = str(row.get("anchor_key", ""))
        seed = str(row.get("probe_seed", ""))
        label = str(row.get("left_obstacle_label", ""))
        target = str(row.get("target", ""))
        bucket = str(row.get("obstacle_bucket", ""))
        if max_per_anchor > 0 and anchor_counts.get(anchor, 0) >= int(max_per_anchor):
            continue
        if max_per_probe_seed > 0 and seed_counts.get(seed, 0) >= int(max_per_probe_seed):
            continue
        if max_per_label > 0 and label_counts.get(label, 0) >= int(max_per_label):
            continue
        if max_per_target > 0 and target_counts.get(target, 0) >= int(max_per_target):
            continue
        if max_per_obstacle_bucket > 0 and bucket_counts.get(bucket, 0) >= int(max_per_obstacle_bucket):
            continue
        selected.append(row)
        anchor_counts[anchor] = anchor_counts.get(anchor, 0) + 1
        seed_counts[seed] = seed_counts.get(seed, 0) + 1
        label_counts[label] = label_counts.get(label, 0) + 1
        target_counts[target] = target_counts.get(target, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    return pd.DataFrame(selected, columns=list(frame.columns))


def summarize_search(
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
    *,
    min_adversarial_pairs: int,
    min_left_state_count: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
) -> dict[str, Any]:
    left_state_count = int(selected["anchor_key"].nunique()) if "anchor_key" in selected else 0
    seed_count = int(selected["probe_seed"].nunique()) if "probe_seed" in selected else 0
    label_count = int(selected["left_obstacle_label"].nunique()) if "left_obstacle_label" in selected else 0
    target_count = int(selected["target"].nunique()) if "target" in selected else 0
    single_seed_share = _max_share(selected, "probe_seed")
    single_label_share = _max_share(selected, "left_obstacle_label")
    search_pass = (
        len(selected) >= int(min_adversarial_pairs)
        and left_state_count >= int(min_left_state_count)
        and seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_obstacle_label_count)
        and target_count >= int(min_target_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
    )
    return {
        "search_candidate_count": int(len(candidates)),
        "adversarial_pair_count": int(len(selected)),
        "near_boundary_left_state_count": left_state_count,
        "probe_seed_count": seed_count,
        "left_obstacle_label_count": label_count,
        "target_count": target_count,
        "single_seed_share": single_seed_share,
        "single_label_share": single_label_share,
        "adversarial_by_probe_seed": _counts(selected, "probe_seed"),
        "adversarial_by_left_obstacle_label": _counts(selected, "left_obstacle_label"),
        "adversarial_by_target": _counts(selected, "target"),
        "score_min": float(selected["adversarial_wrong_history_score"].min()) if len(selected) else None,
        "score_mean": float(selected["adversarial_wrong_history_score"].mean()) if len(selected) else None,
        "score_max": float(selected["adversarial_wrong_history_score"].max()) if len(selected) else None,
        "search_pass": bool(search_pass),
    }


def run_search(
    *,
    near_boundary_csv: Path,
    candidate_pairs_csv: Path,
    normal_margin_ceiling: float,
    min_target_z_delta: float,
    use_row_visible_threshold: bool,
    exclude_same_episode: bool,
    max_rows: int,
    max_per_anchor: int,
    max_per_probe_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
    min_adversarial_pairs: int,
    min_left_state_count: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    near_boundary = pd.read_csv(near_boundary_csv)
    candidate_pairs = pd.read_csv(candidate_pairs_csv)
    search_candidates = build_adversarial_search_candidates(
        near_boundary_rows=near_boundary,
        candidate_pairs=candidate_pairs,
        normal_margin_ceiling=normal_margin_ceiling,
        min_target_z_delta=min_target_z_delta,
        use_row_visible_threshold=use_row_visible_threshold,
        exclude_same_episode=exclude_same_episode,
    )
    selected = select_adversarial_pairs(
        search_candidates,
        max_rows=max_rows,
        max_per_anchor=max_per_anchor,
        max_per_probe_seed=max_per_probe_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=obstacle_lateral_bucket_width,
    )
    write_csv_rows(
        run_dir / "search_candidates.csv",
        search_candidates.to_dict(orient="records"),
        fieldnames=list(search_candidates.columns),
    )
    write_csv_rows(
        run_dir / "adversarial_pairs.csv",
        selected.to_dict(orient="records"),
        fieldnames=list(selected.columns),
    )
    search_summary = summarize_search(
        search_candidates,
        selected,
        min_adversarial_pairs=min_adversarial_pairs,
        min_left_state_count=min_left_state_count,
        min_probe_seed_count=min_probe_seed_count,
        min_obstacle_label_count=min_obstacle_label_count,
        min_target_count=min_target_count,
        max_single_seed_share=max_single_seed_share,
        max_single_label_share=max_single_label_share,
    )
    summary = {
        "run_type": "adversarial_wrong_history_pair_search",
        "near_boundary_csv": near_boundary_csv,
        "candidate_pairs_csv": candidate_pairs_csv,
        "normal_margin_ceiling": float(normal_margin_ceiling),
        "min_target_z_delta": float(min_target_z_delta),
        "use_row_visible_threshold": bool(use_row_visible_threshold),
        "exclude_same_episode": bool(exclude_same_episode),
        "max_rows": int(max_rows),
        "max_per_anchor": int(max_per_anchor),
        "max_per_probe_seed": int(max_per_probe_seed),
        "max_per_label": int(max_per_label),
        "max_per_target": int(max_per_target),
        "max_per_obstacle_bucket": int(max_per_obstacle_bucket),
        "min_adversarial_pairs": int(min_adversarial_pairs),
        "min_left_state_count": int(min_left_state_count),
        "min_probe_seed_count": int(min_probe_seed_count),
        "min_obstacle_label_count": int(min_obstacle_label_count),
        "min_target_count": int(min_target_count),
        "max_single_seed_share": float(max_single_seed_share),
        "max_single_label_share": float(max_single_label_share),
        **search_summary,
        "search_candidates_csv": run_dir / "search_candidates.csv",
        "adversarial_pairs_csv": run_dir / "adversarial_pairs.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Search adversarial wrong-history pairs.")
    parser.add_argument("--near-boundary-csv", type=Path, required=True)
    parser.add_argument("--candidate-pairs-csv", type=Path, required=True)
    parser.add_argument("--normal-margin-ceiling", type=float, default=0.75)
    parser.add_argument("--min-target-z-delta", type=float, default=1.0)
    parser.add_argument("--disable-row-visible-threshold", action="store_true")
    parser.add_argument("--allow-same-episode", action="store_true")
    parser.add_argument("--max-rows", type=int, default=128)
    parser.add_argument("--max-per-anchor", type=int, default=4)
    parser.add_argument("--max-per-probe-seed", type=int, default=64)
    parser.add_argument("--max-per-label", type=int, default=96)
    parser.add_argument("--max-per-target", type=int, default=64)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=24)
    parser.add_argument("--obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--obstacle-lateral-bucket-width", type=float, default=1.0)
    parser.add_argument("--min-adversarial-pairs", type=int, default=64)
    parser.add_argument("--min-left-state-count", type=int, default=16)
    parser.add_argument("--min-probe-seed-count", type=int, default=3)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.70)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="adversarial_wrong_history_pair_search")
    summary = run_search(
        near_boundary_csv=args.near_boundary_csv,
        candidate_pairs_csv=args.candidate_pairs_csv,
        normal_margin_ceiling=args.normal_margin_ceiling,
        min_target_z_delta=args.min_target_z_delta,
        use_row_visible_threshold=not args.disable_row_visible_threshold,
        exclude_same_episode=not args.allow_same_episode,
        max_rows=args.max_rows,
        max_per_anchor=args.max_per_anchor,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        obstacle_distance_bucket_width=args.obstacle_distance_bucket_width,
        obstacle_lateral_bucket_width=args.obstacle_lateral_bucket_width,
        min_adversarial_pairs=args.min_adversarial_pairs,
        min_left_state_count=args.min_left_state_count,
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
