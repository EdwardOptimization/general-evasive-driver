"""Audit event rows from history-value ablation diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.history_value_ablation_runner import _as_bool
from autodrift.terminal_boundary_anchor_miner import _counts, _max_share


FULL_EVENT_KEY = (
    "surface_name",
    "target",
    "probe_seed",
    "tail_offset",
    "left_seed",
    "right_seed",
    "left_tail_step",
    "right_tail_step",
)
LEFT_EVENT_KEY = ("surface_name", "left_seed", "left_tail_step")
LEFT_TARGET_EVENT_KEY = ("surface_name", "target", "left_seed", "left_tail_step")
AUDIT_SOURCE_KEY = ("surface_name", "probe_seed", "target", "tail_offset", "left_seed", "left_tail_step")


def _finite(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if np.isfinite(number) else float("nan")


def _event_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["success_drop_vs_l3"].map(_as_bool)
        | frame["collision_gap_vs_l3"].map(_as_bool)
        | frame["obstacle_completion_drop_vs_l3"].map(_as_bool)
    )


def select_event_rows(frame: pd.DataFrame, *, level: str = "L0_reset_hidden_each_step") -> pd.DataFrame:
    required = {
        "history_level",
        "success_drop_vs_l3",
        "collision_gap_vs_l3",
        "obstacle_completion_drop_vs_l3",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"history-value rows missing required columns: {missing}")
    level_rows = frame[frame["history_level"].astype(str) == str(level)].copy()
    events = level_rows[_event_mask(level_rows)].copy()
    if events.empty:
        events["event_type"] = []
        return events
    event_types: list[str] = []
    for _, row in events.iterrows():
        labels = []
        if _as_bool(row.get("success_drop_vs_l3")):
            labels.append("success_drop")
        if _as_bool(row.get("collision_gap_vs_l3")):
            labels.append("collision_gap")
        if _as_bool(row.get("obstacle_completion_drop_vs_l3")):
            labels.append("obstacle_completion_drop")
        event_types.append("+".join(labels))
    events["event_type"] = event_types
    return events


def _duplicate_summary(frame: pd.DataFrame, key_columns: tuple[str, ...], label: str) -> dict[str, Any]:
    available = [column for column in key_columns if column in frame.columns]
    if frame.empty or not available:
        return {
            "key_name": label,
            "key_columns": ",".join(available),
            "row_count": int(len(frame)),
            "unique_key_count": 0,
            "duplicate_row_count": 0,
            "duplicate_share": None,
            "max_key_count": 0,
        }
    counts = frame.groupby(available, observed=True).size()
    duplicate_rows = int((counts - 1).clip(lower=0).sum())
    return {
        "key_name": label,
        "key_columns": ",".join(available),
        "row_count": int(len(frame)),
        "unique_key_count": int(len(counts)),
        "duplicate_row_count": duplicate_rows,
        "duplicate_share": float(duplicate_rows / len(frame)) if len(frame) else None,
        "max_key_count": int(counts.max()) if len(counts) else 0,
    }


def build_event_source_summary(events: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for column in ("surface_name", "target", "probe_seed", "tail_offset", "event_type"):
        if column not in events.columns:
            continue
        for value, count in events[column].astype(str).value_counts().sort_index().items():
            rows.append({"summary_type": column, "value": str(value), "count": int(count)})
    return rows


def build_event_margin_action_summary(events: pd.DataFrame) -> list[dict[str, Any]]:
    if events.empty:
        return []
    rows: list[dict[str, Any]] = []
    for (surface_name, target), group in events.groupby(["surface_name", "target"], observed=True):
        margin_gap = group["margin_gap_l3_minus_level"].map(_finite)
        first_action = group["first_action_distance_to_l3"].map(_finite)
        trajectory = group["trajectory_distance_mean_to_l3"].map(_finite)
        rows.append(
            {
                "surface_name": str(surface_name),
                "target": str(target),
                "event_row_count": int(len(group)),
                "margin_gap_mean": float(margin_gap.mean()),
                "margin_gap_min": float(margin_gap.min()),
                "margin_gap_max": float(margin_gap.max()),
                "first_action_distance_mean": float(first_action.mean()),
                "trajectory_distance_mean": float(trajectory.mean()),
            }
        )
    return rows


def classify_event_audit(events: pd.DataFrame, duplicate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    event_count = int(len(events))
    if event_count == 0:
        classification = "invalid_history_value_event_audit"
    else:
        projected_count = int(events["surface_name"].astype(str).str.contains("projected", case=False).sum())
        surface_count = int(events["surface_name"].nunique()) if "surface_name" in events else 0
        seed_count = int(events["probe_seed"].nunique()) if "probe_seed" in events else 0
        target_count = int(events["target"].nunique()) if "target" in events else 0
        left_summary = next((row for row in duplicate_rows if row["key_name"] == "left_state"), {})
        left_unique = int(left_summary.get("unique_key_count", 0) or 0)
        left_duplicate_share = left_summary.get("duplicate_share")
        completion_events = int(events["obstacle_completion_drop_vs_l3"].map(_as_bool).sum())
        success_events = int(events["success_drop_vs_l3"].map(_as_bool).sum())
        collision_events = int(events["collision_gap_vs_l3"].map(_as_bool).sum())
        if projected_count > 0:
            classification = "invalid_history_value_event_audit"
        elif completion_events + success_events + collision_events != event_count:
            classification = "metric_artifact_history_value_events"
        elif (
            event_count >= 10
            and surface_count >= 2
            and seed_count >= 4
            and target_count >= 2
            and left_unique >= 8
            and (left_duplicate_share is None or float(left_duplicate_share) <= 0.60)
        ):
            classification = "source_diverse_history_value_events"
        else:
            classification = "source_narrow_history_value_events"
    return {
        "classification": classification,
        "event_row_count": event_count,
        "event_surface_count": int(events["surface_name"].nunique()) if "surface_name" in events else 0,
        "event_probe_seed_count": int(events["probe_seed"].nunique()) if "probe_seed" in events else 0,
        "event_target_count": int(events["target"].nunique()) if "target" in events else 0,
        "event_tail_offset_count": int(events["tail_offset"].nunique()) if "tail_offset" in events else 0,
        "success_drop_event_count": int(events["success_drop_vs_l3"].map(_as_bool).sum()) if not events.empty else 0,
        "collision_gap_event_count": int(events["collision_gap_vs_l3"].map(_as_bool).sum()) if not events.empty else 0,
        "obstacle_completion_drop_event_count": (
            int(events["obstacle_completion_drop_vs_l3"].map(_as_bool).sum()) if not events.empty else 0
        ),
        "projected_event_row_count": (
            int(events["surface_name"].astype(str).str.contains("projected", case=False).sum())
            if "surface_name" in events
            else 0
        ),
        "single_seed_share": _max_share(events, "probe_seed"),
        "single_surface_share": _max_share(events, "surface_name"),
        "single_target_share": _max_share(events, "target"),
        "events_by_surface": _counts(events, "surface_name"),
        "events_by_target": _counts(events, "target"),
    }


def run_history_value_event_audit(
    *,
    history_value_rows_csv: Path,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(history_value_rows_csv)
    events = select_event_rows(frame)
    duplicate_rows = [
        _duplicate_summary(events, FULL_EVENT_KEY, "full_event"),
        _duplicate_summary(events, LEFT_EVENT_KEY, "left_state"),
        _duplicate_summary(events, LEFT_TARGET_EVENT_KEY, "left_target"),
        _duplicate_summary(events, AUDIT_SOURCE_KEY, "audit_source"),
    ]
    source_rows = build_event_source_summary(events)
    margin_action_rows = build_event_margin_action_summary(events)
    write_csv_rows(run_dir / "event_rows.csv", events.to_dict("records"))
    write_csv_rows(run_dir / "event_source_summary.csv", source_rows)
    write_csv_rows(run_dir / "event_duplicate_summary.csv", duplicate_rows)
    write_csv_rows(run_dir / "event_margin_action_summary.csv", margin_action_rows)
    classification = classify_event_audit(events, duplicate_rows)
    summary = {
        "run_type": "history_value_event_audit",
        "history_value_rows_csv": history_value_rows_csv,
        "event_rows_csv": run_dir / "event_rows.csv",
        "event_source_summary_csv": run_dir / "event_source_summary.csv",
        "event_duplicate_summary_csv": run_dir / "event_duplicate_summary.csv",
        "event_margin_action_summary_csv": run_dir / "event_margin_action_summary.csv",
        "duplicate_summary": duplicate_rows,
        "actor_contract_changed": False,
        "training_or_promotion_performed": False,
        **classification,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit history-value event rows.")
    parser.add_argument("--history-value-rows-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="history_value_event_audit")
    summary = run_history_value_event_audit(
        history_value_rows_csv=args.history_value_rows_csv,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
