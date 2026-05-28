"""Export M1222 action-divergent rows as terminal-boundary candidates."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json


PHYSICAL_PAIR_COLUMNS = ("left_seed", "left_step", "right_seed", "right_step")

DEFAULT_MIN_NORMAL_MARGIN = 0.0
DEFAULT_MAX_NORMAL_MARGIN = 1.0
DEFAULT_MIN_FIRST_ACTION_L2 = 0.002
DEFAULT_MIN_WRONG_SEQUENCE_MEAN_L2 = 0.006
DEFAULT_MIN_PREFERRED_REJECTED_MEAN_L2 = 0.010

DEFAULT_MIN_SELECTED_ROWS = 120
DEFAULT_MIN_PHYSICAL_PAIRS = 40
DEFAULT_MIN_LEFT_SEEDS = 6
DEFAULT_MIN_RIGHT_SEEDS = 15
DEFAULT_MIN_LEFT_STEPS = 4
DEFAULT_MIN_TARGETS = 2
DEFAULT_MIN_SOURCE_OBSTACLE_BUCKETS = 4
DEFAULT_MAX_ROWS_PER_PHYSICAL_PAIR_FRACTION = 0.05
DEFAULT_MAX_LEFT_SEED_SHARE = 0.40
DEFAULT_MAX_TARGET_SHARE = 0.70


REQUIRED_COLUMNS = (
    "variant",
    "target",
    "left_seed",
    "left_step",
    "right_seed",
    "right_step",
    "normal_success",
    "wrong_success",
    "normal_margin",
    "wrong_margin",
    "margin_gap",
    "wrong_first_action_l2",
    "wrong_action_sequence_mean_l2",
    "wrong_action_sequence_max_l2",
    "preferred_vs_rejected_action_mean_l2",
    "preferred_vs_rejected_action_max_l2",
    "left_obstacle_x_m",
    "left_obstacle_y_m",
    "left_obstacle_distance",
)

NUMERIC_COLUMNS = (
    "left_seed",
    "left_step",
    "right_seed",
    "right_step",
    "sequence_length",
    "left_obstacle_distance",
    "right_obstacle_distance",
    "left_obstacle_x_m",
    "right_obstacle_x_m",
    "left_obstacle_y_m",
    "right_obstacle_y_m",
    "context_distance",
    "response_distance",
    "obstacle_x_abs_delta",
    "obstacle_y_abs_delta",
    "step_abs_delta",
    "hidden_distance",
    "normal_margin",
    "wrong_margin",
    "preferred_margin",
    "rejected_margin",
    "normal_risk_score",
    "wrong_risk_score",
    "preferred_risk_score",
    "rejected_risk_score",
    "margin_gap",
    "risk_gap",
    "wrong_first_action_l2",
    "wrong_action_sequence_mean_l2",
    "wrong_action_sequence_max_l2",
    "preferred_vs_rejected_action_mean_l2",
    "preferred_vs_rejected_action_max_l2",
)

OUTPUT_COLUMNS = (
    "checkpoint_label",
    "variant",
    "surface",
    "grid_name",
    "source_index",
    "target",
    "split",
    "preferred_sequence_source",
    "left_seed",
    "left_step",
    "right_seed",
    "right_step",
    "sequence_length",
    "normal_success",
    "variant_success",
    "success_drop",
    "normal_collision",
    "variant_collision",
    "normal_terminal_reason",
    "variant_terminal_reason",
    "normal_margin",
    "variant_margin",
    "margin_gap",
    "normal_better",
    "normal_risk_score",
    "variant_risk_score",
    "risk_gap",
    "first_action_distance",
    "wrong_action_sequence_mean_l2",
    "wrong_action_sequence_max_l2",
    "action_trajectory_distance_mean",
    "action_trajectory_distance_max",
    "action_trajectory_distance_rms",
    "source_obstacle_body_x",
    "source_obstacle_body_y",
    "source_obstacle_distance",
    "source_obstacle_lateral_offset",
    "context_distance",
    "response_distance",
    "hidden_distance",
    "obstacle_x_abs_delta",
    "obstacle_y_abs_delta",
    "step_abs_delta",
    "left_obstacle_label",
    "right_obstacle_label",
    "source_physical_pair_key",
    "physical_pair_key",
    "source_obstacle_bucket",
    "_candidate_export_index",
    "export_rejection_reason",
)


def _as_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot convert {value!r} to int") from exc


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _format_bucket(value: float, width: float) -> str:
    if width <= 0.0:
        raise ValueError("bucket width must be positive")
    if not np.isfinite(value):
        return "nan"
    start = math.floor(float(value) / float(width)) * float(width)
    return f"{start:.3f}-{start + float(width):.3f}"


def physical_pair_key(row: pd.Series | dict[str, Any]) -> str:
    missing = [column for column in PHYSICAL_PAIR_COLUMNS if column not in row]
    if missing:
        raise ValueError(f"row missing physical pair columns: {missing}")
    return ":".join(str(_as_int(row[column])) for column in PHYSICAL_PAIR_COLUMNS)


def source_obstacle_bucket(
    row: pd.Series | dict[str, Any],
    *,
    distance_bucket_width: float,
    lateral_bucket_width: float,
) -> str:
    distance = _as_float(row.get("source_obstacle_body_x", row.get("source_obstacle_distance")))
    lateral = _as_float(row.get("source_obstacle_body_y", row.get("source_obstacle_lateral_offset")))
    return (
        f"x={_format_bucket(distance, distance_bucket_width)}|"
        f"y={_format_bucket(lateral, lateral_bucket_width)}"
    )


def _require_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"candidate scores missing required columns: {missing}")


def _numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    converted = frame.copy()
    for column in NUMERIC_COLUMNS:
        if column in converted.columns:
            converted[column] = pd.to_numeric(converted[column], errors="coerce")
    return converted


def _bool_series(frame: pd.DataFrame, column: str, default: bool = False) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([default] * len(frame), index=frame.index, dtype=bool)
    return frame[column].map(_as_bool).astype(bool)


def _value(frame: pd.DataFrame, column: str, default: Any = "") -> pd.Series:
    if column in frame.columns:
        return frame[column]
    return pd.Series([default] * len(frame), index=frame.index)


def _finite_at_least(series: pd.Series, threshold: float) -> pd.Series:
    return series.notna() & np.isfinite(series.astype(float)) & (series.astype(float) >= float(threshold))


def _finite_between(series: pd.Series, lower: float, upper: float) -> pd.Series:
    values = series.astype(float)
    return values.notna() & np.isfinite(values) & (values >= float(lower)) & (values <= float(upper))


def _rejection_reason(
    row: pd.Series,
    *,
    min_normal_margin: float,
    max_normal_margin: float,
    min_first_action_l2: float,
    min_wrong_sequence_mean_l2: float,
    min_preferred_rejected_mean_l2: float,
) -> str:
    reasons: list[str] = []
    if str(row.get("variant", "")) != "wrong_matched_history":
        reasons.append("variant_not_wrong_matched_history")
    if not _as_bool(row.get("normal_success", False)):
        reasons.append("normal_not_success")
    normal_margin = _as_float(row.get("normal_margin"))
    if not np.isfinite(normal_margin) or normal_margin < min_normal_margin or normal_margin > max_normal_margin:
        reasons.append("normal_margin_out_of_window")
    if _as_float(row.get("wrong_first_action_l2")) < min_first_action_l2:
        reasons.append("first_action_l2_below_threshold")
    if _as_float(row.get("wrong_action_sequence_mean_l2")) < min_wrong_sequence_mean_l2:
        reasons.append("wrong_sequence_mean_l2_below_threshold")
    if _as_float(row.get("preferred_vs_rejected_action_mean_l2")) < min_preferred_rejected_mean_l2:
        reasons.append("preferred_rejected_mean_l2_below_threshold")
    return ";".join(reasons) if reasons else "selected"


def build_terminal_boundary_candidate_pool(
    frame: pd.DataFrame,
    *,
    checkpoint_label: str,
    min_normal_margin: float = DEFAULT_MIN_NORMAL_MARGIN,
    max_normal_margin: float = DEFAULT_MAX_NORMAL_MARGIN,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
    min_wrong_sequence_mean_l2: float = DEFAULT_MIN_WRONG_SEQUENCE_MEAN_L2,
    min_preferred_rejected_mean_l2: float = DEFAULT_MIN_PREFERRED_REJECTED_MEAN_L2,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return selected and rejected relocation-compatible candidate rows."""

    _require_columns(frame)
    source = _numeric_frame(frame)

    variant_mask = source["variant"].astype(str).eq("wrong_matched_history")
    normal_success_mask = _bool_series(source, "normal_success")
    normal_margin_mask = _finite_between(source["normal_margin"], min_normal_margin, max_normal_margin)
    first_action_mask = _finite_at_least(source["wrong_first_action_l2"], min_first_action_l2)
    wrong_sequence_mask = _finite_at_least(source["wrong_action_sequence_mean_l2"], min_wrong_sequence_mean_l2)
    preferred_rejected_mask = _finite_at_least(
        source["preferred_vs_rejected_action_mean_l2"],
        min_preferred_rejected_mean_l2,
    )
    selected_mask = (
        variant_mask
        & normal_success_mask
        & normal_margin_mask
        & first_action_mask
        & wrong_sequence_mask
        & preferred_rejected_mask
    )

    source_physical_pair_key = source["physical_pair_key"].astype(str) if "physical_pair_key" in source else ""
    normal_success = _bool_series(source, "normal_success")
    variant_success = _bool_series(source, "wrong_success")
    success_drop = normal_success & ~variant_success
    normal_collision = _bool_series(source, "normal_collision")
    variant_collision = _bool_series(source, "wrong_collision")
    normal_margin = source["normal_margin"].astype(float)
    variant_margin = source["wrong_margin"].astype(float)
    normal_better = success_drop | (normal_margin > variant_margin)

    exported = pd.DataFrame(
        {
            "checkpoint_label": checkpoint_label,
            "variant": source["variant"].astype(str),
            "surface": _value(source, "surface"),
            "grid_name": _value(source, "grid_name"),
            "source_index": _value(source, "source_index"),
            "target": source["target"].astype(str),
            "split": _value(source, "split", "unassigned"),
            "preferred_sequence_source": _value(source, "preferred_sequence_source", "normal_policy_base"),
            "left_seed": source["left_seed"].astype(int),
            "left_step": source["left_step"].astype(int),
            "right_seed": source["right_seed"].astype(int),
            "right_step": source["right_step"].astype(int),
            "sequence_length": _value(source, "sequence_length"),
            "normal_success": normal_success,
            "variant_success": variant_success,
            "success_drop": success_drop,
            "normal_collision": normal_collision,
            "variant_collision": variant_collision,
            "normal_terminal_reason": _value(source, "normal_terminal_reason"),
            "variant_terminal_reason": _value(source, "wrong_terminal_reason"),
            "normal_margin": normal_margin,
            "variant_margin": variant_margin,
            "margin_gap": source["margin_gap"].astype(float),
            "normal_better": normal_better,
            "normal_risk_score": _value(source, "normal_risk_score"),
            "variant_risk_score": _value(source, "wrong_risk_score"),
            "risk_gap": _value(source, "risk_gap"),
            "first_action_distance": source["wrong_first_action_l2"].astype(float),
            "wrong_action_sequence_mean_l2": source["wrong_action_sequence_mean_l2"].astype(float),
            "wrong_action_sequence_max_l2": source["wrong_action_sequence_max_l2"].astype(float),
            "action_trajectory_distance_mean": source["preferred_vs_rejected_action_mean_l2"].astype(float),
            "action_trajectory_distance_max": source["preferred_vs_rejected_action_max_l2"].astype(float),
            "action_trajectory_distance_rms": source["preferred_vs_rejected_action_mean_l2"].astype(float),
            "source_obstacle_body_x": source["left_obstacle_x_m"].astype(float),
            "source_obstacle_body_y": source["left_obstacle_y_m"].astype(float),
            "source_obstacle_distance": source["left_obstacle_distance"].astype(float),
            "source_obstacle_lateral_offset": source["left_obstacle_y_m"].astype(float),
            "context_distance": _value(source, "context_distance"),
            "response_distance": _value(source, "response_distance"),
            "hidden_distance": _value(source, "hidden_distance"),
            "obstacle_x_abs_delta": _value(source, "obstacle_x_abs_delta"),
            "obstacle_y_abs_delta": _value(source, "obstacle_y_abs_delta"),
            "step_abs_delta": _value(source, "step_abs_delta"),
            "left_obstacle_label": _value(source, "left_obstacle_label"),
            "right_obstacle_label": _value(source, "right_obstacle_label"),
            "source_physical_pair_key": source_physical_pair_key,
        }
    )
    exported["physical_pair_key"] = [physical_pair_key(row) for _, row in exported.iterrows()]
    exported["source_obstacle_bucket"] = [
        source_obstacle_bucket(
            row,
            distance_bucket_width=distance_bucket_width,
            lateral_bucket_width=lateral_bucket_width,
        )
        for _, row in exported.iterrows()
    ]
    exported["export_rejection_reason"] = [
        _rejection_reason(
            row,
            min_normal_margin=min_normal_margin,
            max_normal_margin=max_normal_margin,
            min_first_action_l2=min_first_action_l2,
            min_wrong_sequence_mean_l2=min_wrong_sequence_mean_l2,
            min_preferred_rejected_mean_l2=min_preferred_rejected_mean_l2,
        )
        for _, row in source.iterrows()
    ]
    exported["_selected"] = selected_mask.to_numpy(dtype=bool)

    selected = exported[exported["_selected"]].copy().reset_index(drop=True)
    selected["_candidate_export_index"] = np.arange(len(selected), dtype=int)
    rejected = exported[~exported["_selected"]].copy().reset_index(drop=True)
    rejected["_candidate_export_index"] = np.arange(len(rejected), dtype=int)
    selected = selected.drop(columns=["_selected"])
    rejected = rejected.drop(columns=["_selected"])

    sort_columns = ["target", "left_seed", "left_step", "right_seed", "right_step"]
    selected = selected.sort_values(sort_columns).reset_index(drop=True)
    selected["_candidate_export_index"] = np.arange(len(selected), dtype=int)
    rejected = rejected.sort_values(["export_rejection_reason", *sort_columns]).reset_index(drop=True)
    rejected["_candidate_export_index"] = np.arange(len(rejected), dtype=int)

    return selected.loc[:, list(OUTPUT_COLUMNS)], rejected.loc[:, list(OUTPUT_COLUMNS)]


def _max_share(frame: pd.DataFrame, column: str) -> tuple[int, float]:
    if frame.empty or column not in frame.columns:
        return 0, 0.0
    counts = frame[column].astype(str).value_counts()
    max_rows = int(counts.max()) if len(counts) else 0
    return max_rows, float(max_rows / max(len(frame), 1)) if max_rows else 0.0


def summarize_source_diversity(
    selected: pd.DataFrame,
    *,
    min_selected_rows: int = DEFAULT_MIN_SELECTED_ROWS,
    min_physical_pairs: int = DEFAULT_MIN_PHYSICAL_PAIRS,
    min_left_seeds: int = DEFAULT_MIN_LEFT_SEEDS,
    min_right_seeds: int = DEFAULT_MIN_RIGHT_SEEDS,
    min_left_steps: int = DEFAULT_MIN_LEFT_STEPS,
    min_targets: int = DEFAULT_MIN_TARGETS,
    min_source_obstacle_buckets: int = DEFAULT_MIN_SOURCE_OBSTACLE_BUCKETS,
    max_rows_per_physical_pair_fraction: float = DEFAULT_MAX_ROWS_PER_PHYSICAL_PAIR_FRACTION,
    max_left_seed_share: float = DEFAULT_MAX_LEFT_SEED_SHARE,
    max_target_share: float = DEFAULT_MAX_TARGET_SHARE,
) -> dict[str, Any]:
    selected_count = int(len(selected))
    max_pair_rows, max_pair_share = _max_share(selected, "physical_pair_key")
    max_left_seed_rows, observed_max_left_seed_share = _max_share(selected, "left_seed")
    max_target_rows, observed_max_target_share = _max_share(selected, "target")

    selected_physical_pairs = int(selected["physical_pair_key"].astype(str).nunique()) if selected_count else 0
    selected_left_seeds = int(selected["left_seed"].astype(str).nunique()) if selected_count else 0
    selected_right_seeds = int(selected["right_seed"].astype(str).nunique()) if selected_count else 0
    selected_left_steps = int(selected["left_step"].astype(str).nunique()) if selected_count else 0
    selected_targets = int(selected["target"].astype(str).nunique()) if selected_count else 0
    selected_buckets = int(selected["source_obstacle_bucket"].astype(str).nunique()) if selected_count else 0
    passed = bool(
        selected_count >= int(min_selected_rows)
        and selected_physical_pairs >= int(min_physical_pairs)
        and selected_left_seeds >= int(min_left_seeds)
        and selected_right_seeds >= int(min_right_seeds)
        and selected_left_steps >= int(min_left_steps)
        and selected_targets >= int(min_targets)
        and selected_buckets >= int(min_source_obstacle_buckets)
        and max_pair_share <= float(max_rows_per_physical_pair_fraction)
        and observed_max_left_seed_share <= float(max_left_seed_share)
        and observed_max_target_share <= float(max_target_share)
    )
    return {
        "selected_rows": selected_count,
        "selected_physical_pairs": selected_physical_pairs,
        "selected_left_seeds": selected_left_seeds,
        "selected_right_seeds": selected_right_seeds,
        "selected_left_steps": selected_left_steps,
        "selected_targets": selected_targets,
        "selected_source_obstacle_buckets": selected_buckets,
        "max_rows_per_physical_pair": max_pair_rows,
        "max_rows_per_physical_pair_fraction": max_pair_share,
        "max_left_seed_rows": max_left_seed_rows,
        "max_left_seed_share": observed_max_left_seed_share,
        "max_target_rows": max_target_rows,
        "max_target_share": observed_max_target_share,
        "criteria": {
            "min_selected_rows": int(min_selected_rows),
            "min_physical_pairs": int(min_physical_pairs),
            "min_left_seeds": int(min_left_seeds),
            "min_right_seeds": int(min_right_seeds),
            "min_left_steps": int(min_left_steps),
            "min_targets": int(min_targets),
            "min_source_obstacle_buckets": int(min_source_obstacle_buckets),
            "max_rows_per_physical_pair_fraction": float(max_rows_per_physical_pair_fraction),
            "max_left_seed_share": float(max_left_seed_share),
            "max_target_share": float(max_target_share),
        },
        "decision": (
            "terminal_boundary_candidates_source_diverse"
            if passed
            else "terminal_boundary_candidates_source_limited"
        ),
        "passed": passed,
    }


def _csv_fieldnames(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def export_terminal_boundary_candidates(
    *,
    candidate_scores: Path,
    checkpoint_label: str,
    run_dir: Path,
    min_normal_margin: float = DEFAULT_MIN_NORMAL_MARGIN,
    max_normal_margin: float = DEFAULT_MAX_NORMAL_MARGIN,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
    min_wrong_sequence_mean_l2: float = DEFAULT_MIN_WRONG_SEQUENCE_MEAN_L2,
    min_preferred_rejected_mean_l2: float = DEFAULT_MIN_PREFERRED_REJECTED_MEAN_L2,
    min_selected_rows: int = DEFAULT_MIN_SELECTED_ROWS,
    min_physical_pairs: int = DEFAULT_MIN_PHYSICAL_PAIRS,
    min_left_seeds: int = DEFAULT_MIN_LEFT_SEEDS,
    min_right_seeds: int = DEFAULT_MIN_RIGHT_SEEDS,
    min_left_steps: int = DEFAULT_MIN_LEFT_STEPS,
    min_targets: int = DEFAULT_MIN_TARGETS,
    min_source_obstacle_buckets: int = DEFAULT_MIN_SOURCE_OBSTACLE_BUCKETS,
    max_rows_per_physical_pair_fraction: float = DEFAULT_MAX_ROWS_PER_PHYSICAL_PAIR_FRACTION,
    max_left_seed_share: float = DEFAULT_MAX_LEFT_SEED_SHARE,
    max_target_share: float = DEFAULT_MAX_TARGET_SHARE,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
) -> dict[str, Any]:
    """Export filtered candidate rows and source-diversity accounting."""

    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(candidate_scores)
    selected, rejected = build_terminal_boundary_candidate_pool(
        frame,
        checkpoint_label=checkpoint_label,
        min_normal_margin=min_normal_margin,
        max_normal_margin=max_normal_margin,
        min_first_action_l2=min_first_action_l2,
        min_wrong_sequence_mean_l2=min_wrong_sequence_mean_l2,
        min_preferred_rejected_mean_l2=min_preferred_rejected_mean_l2,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )
    source_diversity = summarize_source_diversity(
        selected,
        min_selected_rows=min_selected_rows,
        min_physical_pairs=min_physical_pairs,
        min_left_seeds=min_left_seeds,
        min_right_seeds=min_right_seeds,
        min_left_steps=min_left_steps,
        min_targets=min_targets,
        min_source_obstacle_buckets=min_source_obstacle_buckets,
        max_rows_per_physical_pair_fraction=max_rows_per_physical_pair_fraction,
        max_left_seed_share=max_left_seed_share,
        max_target_share=max_target_share,
    )

    candidate_pool_csv = run_dir / "candidate_pool.csv"
    candidate_outcomes_csv = run_dir / "candidate_outcomes.csv"
    rejected_candidates_csv = run_dir / "rejected_candidates.csv"
    write_csv_rows(candidate_pool_csv, selected.to_dict("records"), fieldnames=_csv_fieldnames(selected))
    write_csv_rows(candidate_outcomes_csv, selected.to_dict("records"), fieldnames=_csv_fieldnames(selected))
    write_csv_rows(rejected_candidates_csv, rejected.to_dict("records"), fieldnames=_csv_fieldnames(rejected))

    wrong_rows = int((frame["variant"].astype(str) == "wrong_matched_history").sum()) if "variant" in frame else 0
    summary = {
        "run_type": "terminal_boundary_candidate_export",
        "candidate_scores_csv": candidate_scores,
        "checkpoint_label": checkpoint_label,
        "candidate_pool_csv": candidate_pool_csv,
        "candidate_outcomes_csv": candidate_outcomes_csv,
        "rejected_candidates_csv": rejected_candidates_csv,
        "input_rows": int(len(frame)),
        "wrong_matched_history_rows": wrong_rows,
        "candidate_pool_rows": int(len(selected)),
        "rejected_rows": int(len(rejected)),
        "filters": {
            "variant": "wrong_matched_history",
            "normal_success": True,
            "min_normal_margin": float(min_normal_margin),
            "max_normal_margin": float(max_normal_margin),
            "min_first_action_l2": float(min_first_action_l2),
            "min_wrong_sequence_mean_l2": float(min_wrong_sequence_mean_l2),
            "min_preferred_rejected_mean_l2": float(min_preferred_rejected_mean_l2),
        },
        "source_diversity": source_diversity,
        "selection": source_diversity,
        "selection_passed": bool(source_diversity["passed"]),
        "relocation_compatible_fields": list(OUTPUT_COLUMNS),
        "relocation_replay_started": False,
        "replay_started": False,
        "source_mining_started": False,
        "outcome_intervention_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
        "labels_enter_actor_input": False,
        "self_identification_claimed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-scores", type=Path, required=True)
    parser.add_argument("--checkpoint-label", type=str, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--min-normal-margin", type=float, default=DEFAULT_MIN_NORMAL_MARGIN)
    parser.add_argument("--max-normal-margin", type=float, default=DEFAULT_MAX_NORMAL_MARGIN)
    parser.add_argument("--min-first-action-l2", type=float, default=DEFAULT_MIN_FIRST_ACTION_L2)
    parser.add_argument("--min-wrong-sequence-mean-l2", type=float, default=DEFAULT_MIN_WRONG_SEQUENCE_MEAN_L2)
    parser.add_argument(
        "--min-preferred-rejected-mean-l2",
        type=float,
        default=DEFAULT_MIN_PREFERRED_REJECTED_MEAN_L2,
    )
    parser.add_argument("--min-selected-rows", type=int, default=DEFAULT_MIN_SELECTED_ROWS)
    parser.add_argument("--min-physical-pairs", type=int, default=DEFAULT_MIN_PHYSICAL_PAIRS)
    parser.add_argument("--min-left-seeds", type=int, default=DEFAULT_MIN_LEFT_SEEDS)
    parser.add_argument("--min-right-seeds", type=int, default=DEFAULT_MIN_RIGHT_SEEDS)
    parser.add_argument("--min-left-steps", type=int, default=DEFAULT_MIN_LEFT_STEPS)
    parser.add_argument("--min-targets", type=int, default=DEFAULT_MIN_TARGETS)
    parser.add_argument("--min-source-obstacle-buckets", type=int, default=DEFAULT_MIN_SOURCE_OBSTACLE_BUCKETS)
    parser.add_argument(
        "--max-rows-per-physical-pair-fraction",
        type=float,
        default=DEFAULT_MAX_ROWS_PER_PHYSICAL_PAIR_FRACTION,
    )
    parser.add_argument("--max-left-seed-share", type=float, default=DEFAULT_MAX_LEFT_SEED_SHARE)
    parser.add_argument("--max-target-share", type=float, default=DEFAULT_MAX_TARGET_SHARE)
    parser.add_argument("--source-obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--source-obstacle-lateral-bucket-width", type=float, default=1.0)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    summary = export_terminal_boundary_candidates(
        candidate_scores=args.candidate_scores,
        checkpoint_label=args.checkpoint_label,
        run_dir=args.run_dir,
        min_normal_margin=args.min_normal_margin,
        max_normal_margin=args.max_normal_margin,
        min_first_action_l2=args.min_first_action_l2,
        min_wrong_sequence_mean_l2=args.min_wrong_sequence_mean_l2,
        min_preferred_rejected_mean_l2=args.min_preferred_rejected_mean_l2,
        min_selected_rows=args.min_selected_rows,
        min_physical_pairs=args.min_physical_pairs,
        min_left_seeds=args.min_left_seeds,
        min_right_seeds=args.min_right_seeds,
        min_left_steps=args.min_left_steps,
        min_targets=args.min_targets,
        min_source_obstacle_buckets=args.min_source_obstacle_buckets,
        max_rows_per_physical_pair_fraction=args.max_rows_per_physical_pair_fraction,
        max_left_seed_share=args.max_left_seed_share,
        max_target_share=args.max_target_share,
        distance_bucket_width=args.source_obstacle_distance_bucket_width,
        lateral_bucket_width=args.source_obstacle_lateral_bucket_width,
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"candidate_outcomes_csv={summary['candidate_outcomes_csv']}")
    print(f"decision={summary['source_diversity']['decision']}")
    print(f"passed={summary['selection_passed']}")


if __name__ == "__main__":
    main()
