"""Diagnostic history-value summaries from replay outcome tables."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.terminal_boundary_anchor_miner import _counts, _max_share


DEFAULT_LEVEL_VARIANTS = {
    "L3_online_gru": "normal_projected",
    "L0_reset_hidden_each_step": "reset_projected",
}

KEY_COLUMNS = (
    "pair_id",
    "checkpoint_label",
    "probe_seed",
    "config",
    "target",
    "tail_offset",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "left_tail_step",
    "right_tail_step",
)


def _as_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return bool(int(value))
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def _finite(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if np.isfinite(number) else float("nan")


def _available_key_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in KEY_COLUMNS if column in frame.columns]


def parse_level_variant(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("level variants must be LEVEL=variant")
    level, variant = value.split("=", 1)
    level = level.strip()
    variant = variant.strip()
    if not level or not variant:
        raise argparse.ArgumentTypeError("level variants must have non-empty LEVEL and variant")
    return level, variant


def parse_surface_outcomes(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("surface outcomes must be surface_name=path")
    surface_name, path_text = value.split("=", 1)
    surface_name = surface_name.strip()
    path_text = path_text.strip()
    if not surface_name or not path_text:
        raise argparse.ArgumentTypeError("surface outcomes must have non-empty surface_name and path")
    return surface_name, Path(path_text)


def _success_value(row: pd.Series, *, l3: bool) -> bool:
    if "success" in row:
        return _as_bool(row.get("success"))
    if not l3 and "variant_success" in row:
        return _as_bool(row.get("variant_success"))
    if "normal_success" in row:
        return _as_bool(row.get("normal_success"))
    if "variant_success" in row:
        return _as_bool(row.get("variant_success"))
    return False


def build_history_value_rows(
    outcome_frame: pd.DataFrame,
    *,
    surface_name: str,
    min_margin_gap: float,
    level_variants: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Compare diagnostic history levels against the L3 normal rollout."""

    level_variants = dict(level_variants or DEFAULT_LEVEL_VARIANTS)
    if "L3_online_gru" not in level_variants:
        raise ValueError("level mapping must include L3_online_gru")
    if "L0_reset_hidden_each_step" not in level_variants:
        raise ValueError("level mapping must include L0_reset_hidden_each_step")
    if "variant" not in outcome_frame.columns:
        raise ValueError("outcome table must contain a variant column")
    key_columns = _available_key_columns(outcome_frame)
    if not key_columns:
        raise ValueError("outcome table does not contain any recognized key columns")

    l3_variant = level_variants["L3_online_gru"]
    l3_frame = outcome_frame[outcome_frame["variant"].astype(str) == l3_variant].copy()
    if l3_frame.empty:
        raise ValueError(f"outcome table contains no {l3_variant!r} rows")

    l3_by_key = {tuple(row[column] for column in key_columns): row for _, row in l3_frame.iterrows()}
    rows: list[dict[str, Any]] = []
    for level, variant in level_variants.items():
        level_frame = outcome_frame[outcome_frame["variant"].astype(str) == variant].copy()
        for _, level_row in level_frame.iterrows():
            key = tuple(level_row[column] for column in key_columns)
            l3_row = l3_by_key.get(key)
            if l3_row is None:
                continue
            l3_success = _success_value(l3_row, l3=True)
            level_success = _success_value(level_row, l3=False)
            l3_collision = _as_bool(l3_row.get("collision", False))
            level_collision = _as_bool(level_row.get("collision", False))
            l3_completed = _as_bool(l3_row.get("obstacle_completed", False))
            level_completed = _as_bool(level_row.get("obstacle_completed", False))
            l3_margin = _finite(l3_row.get("min_clearance_margin", l3_row.get("normal_margin")))
            level_margin = _finite(level_row.get("min_clearance_margin", level_row.get("variant_margin")))
            margin_gap = l3_margin - level_margin if np.isfinite(l3_margin) and np.isfinite(level_margin) else float("nan")
            success_drop = _as_bool(level_row.get("success_drop", bool(l3_success and not level_success)))
            collision_gap = _as_bool(level_row.get("collision_gap", bool(not l3_collision and level_collision)))
            completion_drop = _as_bool(
                level_row.get("obstacle_completion_drop", bool(l3_completed and not level_completed))
            )
            margin_drop = bool(np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap))
            history_value_candidate = bool(success_drop or collision_gap or completion_drop or margin_drop)
            row = {
                "surface_name": str(surface_name),
                "history_level": str(level),
                "variant": str(variant),
                "key_complete": True,
                "l3_success": l3_success,
                "level_success": level_success,
                "success_drop_vs_l3": success_drop,
                "l3_collision": l3_collision,
                "level_collision": level_collision,
                "collision_gap_vs_l3": collision_gap,
                "l3_obstacle_completed": l3_completed,
                "level_obstacle_completed": level_completed,
                "obstacle_completion_drop_vs_l3": completion_drop,
                "l3_margin": l3_margin,
                "level_margin": level_margin,
                "margin_gap_l3_minus_level": margin_gap,
                "margin_drop_vs_l3": margin_drop,
                "history_value_candidate": history_value_candidate,
                "first_action_distance_to_l3": _finite(level_row.get("first_action_distance")),
                "trajectory_distance_mean_to_l3": _finite(level_row.get("action_trajectory_distance_mean")),
                "trajectory_distance_max_to_l3": _finite(level_row.get("action_trajectory_distance_max")),
            }
            for column in key_columns:
                row[column] = level_row[column]
            for column in (
                "projected_obstacle_bucket",
                "projection_bucket",
                "projected_obstacle_label",
                "proof_surface_type",
            ):
                if column in level_row:
                    row[column] = level_row[column]
            rows.append(row)
    return rows


def _event_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return int(
        (
            frame["success_drop_vs_l3"].astype(bool)
            | frame["collision_gap_vs_l3"].astype(bool)
            | frame["obstacle_completion_drop_vs_l3"].astype(bool)
        ).sum()
    )


def summarize_history_value_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (surface_name, history_level, target), group in frame.groupby(
        ["surface_name", "history_level", "target"],
        observed=True,
    ):
        margin_gap = group["margin_gap_l3_minus_level"].astype(float)
        finite_gap = margin_gap[np.isfinite(margin_gap)]
        summary_rows.append(
            {
                "surface_name": str(surface_name),
                "history_level": str(history_level),
                "variant": str(group["variant"].iloc[0]),
                "target": str(target),
                "row_count": int(len(group)),
                "history_value_candidate_count": int(group["history_value_candidate"].astype(bool).sum()),
                "event_row_count": _event_count(group[group["history_value_candidate"].astype(bool)]),
                "success_drop_count": int(group["success_drop_vs_l3"].astype(bool).sum()),
                "collision_gap_count": int(group["collision_gap_vs_l3"].astype(bool).sum()),
                "obstacle_completion_drop_count": int(group["obstacle_completion_drop_vs_l3"].astype(bool).sum()),
                "l3_success_rate": float(group["l3_success"].astype(bool).mean()),
                "level_success_rate": float(group["level_success"].astype(bool).mean()),
                "l3_margin_mean": float(group["l3_margin"].astype(float).mean()),
                "level_margin_mean": float(group["level_margin"].astype(float).mean()),
                "margin_gap_mean": float(finite_gap.mean()) if len(finite_gap) else None,
                "margin_gap_p10": float(finite_gap.quantile(0.10)) if len(finite_gap) else None,
                "margin_gap_p90": float(finite_gap.quantile(0.90)) if len(finite_gap) else None,
                "margin_gap_max": float(finite_gap.max()) if len(finite_gap) else None,
                "first_action_distance_mean": float(group["first_action_distance_to_l3"].astype(float).mean()),
                "trajectory_distance_mean": float(group["trajectory_distance_mean_to_l3"].astype(float).mean()),
                "probe_seed_count": int(group["probe_seed"].nunique()) if "probe_seed" in group else 0,
                "config_count": int(group["config"].nunique()) if "config" in group else 0,
                "single_seed_share": _max_share(group, "probe_seed"),
                "single_config_share": _max_share(group, "config"),
            }
        )
    return summary_rows


def classify_history_value(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "classification": "invalid_history_value_ablation",
            "l0_candidate_count": 0,
            "l0_event_row_count": 0,
        }
    frame = pd.DataFrame(rows)
    l0 = frame[frame["history_level"].astype(str) == "L0_reset_hidden_each_step"].copy()
    l0_candidates = l0[l0["history_value_candidate"].astype(bool)].copy()
    l0_events = _event_count(l0_candidates)
    if l0.empty:
        classification = "invalid_history_value_ablation"
    elif l0_events > 0:
        classification = "event_history_value_signal"
    elif len(l0_candidates) > 0:
        classification = "margin_only_history_value_signal"
    else:
        classification = "no_diagnostic_history_value_signal"
    return {
        "classification": classification,
        "history_levels": sorted(str(item) for item in frame["history_level"].unique()),
        "row_count": int(len(frame)),
        "l0_row_count": int(len(l0)),
        "l0_candidate_count": int(len(l0_candidates)),
        "l0_event_row_count": int(l0_events),
        "l0_probe_seed_count": int(l0_candidates["probe_seed"].nunique()) if "probe_seed" in l0_candidates else 0,
        "l0_config_count": int(l0_candidates["config"].nunique()) if "config" in l0_candidates else 0,
        "l0_target_count": int(l0_candidates["target"].nunique()) if "target" in l0_candidates else 0,
        "l0_single_seed_share": _max_share(l0_candidates, "probe_seed"),
        "l0_single_config_share": _max_share(l0_candidates, "config"),
        "l0_candidate_by_target": _counts(l0_candidates, "target"),
    }


def run_history_value_ablation(
    *,
    surface_outcomes: list[tuple[str, Path]],
    level_variants: dict[str, str],
    min_margin_gap: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    invalid_surfaces: list[dict[str, Any]] = []
    for surface_name, outcomes_csv in surface_outcomes:
        try:
            outcome_frame = pd.read_csv(outcomes_csv)
            rows.extend(
                build_history_value_rows(
                    outcome_frame,
                    surface_name=surface_name,
                    min_margin_gap=min_margin_gap,
                    level_variants=level_variants,
                )
            )
        except (OSError, ValueError) as exc:
            invalid_surfaces.append(
                {
                    "surface_name": surface_name,
                    "outcomes_csv": str(outcomes_csv),
                    "invalid_reason": str(exc),
                }
            )
    summary_rows = summarize_history_value_rows(rows)
    classification = classify_history_value(rows)
    write_csv_rows(run_dir / "history_value_rows.csv", rows)
    write_csv_rows(run_dir / "history_value_summary.csv", summary_rows)
    write_csv_rows(run_dir / "invalid_surfaces.csv", invalid_surfaces)
    surface_classifications = {
        str(surface): classify_history_value(group.to_dict("records"))
        for surface, group in pd.DataFrame(rows).groupby("surface_name", observed=True)
    } if rows else {}
    summary = {
        "run_type": "history_value_ablation_runner",
        "surface_outcomes": [{"surface_name": name, "outcomes_csv": path} for name, path in surface_outcomes],
        "min_margin_gap": float(min_margin_gap),
        "history_value_rows_csv": run_dir / "history_value_rows.csv",
        "history_value_summary_csv": run_dir / "history_value_summary.csv",
        "invalid_surfaces_csv": run_dir / "invalid_surfaces.csv",
        "source_variant_mapping": level_variants,
        "surface_classifications": surface_classifications,
        "invalid_surface_count": int(len(invalid_surfaces)),
        "surface_count": int(len(surface_outcomes)),
        "diagnostic_limitations": [
            "L0_reset_hidden_each_step is a reset-hidden diagnostic over the existing recurrent actor, not a separately trained feedforward policy.",
            "L1 and L2 matched-capacity baselines are not implemented in this runner.",
            "Projected mechanism surfaces must not be claimed as broad natural-scenario generalization.",
        ],
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
        **classification,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize diagnostic history-value ablations.")
    parser.add_argument("--outcomes-csv", type=Path, default=None)
    parser.add_argument("--surface-name", type=str, default="unknown_surface")
    parser.add_argument("--surface-outcomes", action="append", type=parse_surface_outcomes, default=[])
    parser.add_argument("--level-variant", action="append", type=parse_level_variant, default=[])
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    surface_outcomes = list(args.surface_outcomes)
    if not surface_outcomes:
        if args.outcomes_csv is None:
            parser.error("--outcomes-csv is required when --surface-outcomes is not provided")
        surface_outcomes = [(args.surface_name, args.outcomes_csv)]
    level_variants = dict(args.level_variant) if args.level_variant else dict(DEFAULT_LEVEL_VARIANTS)
    run_dir = args.run_dir or make_run_dir(prefix="history_value_ablation")
    summary = run_history_value_ablation(
        surface_outcomes=surface_outcomes,
        level_variants=level_variants,
        min_margin_gap=args.min_margin_gap,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
