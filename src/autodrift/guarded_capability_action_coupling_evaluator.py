"""No-update evaluator for capability-action coupling gaps."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_capability_belief_intervention_probe import REAL_HISTORY_VARIANTS


JOIN_COLUMNS = (
    "pair_id",
    "checkpoint_label",
    "source_checkpoint_label",
    "surface",
    "probe_seed",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
)
COUPLING_CLASSES = (
    "belief_only_gap",
    "action_and_belief",
    "action_without_belief",
    "inactive",
)


def coupling_class(
    *,
    capability_z_distance: float,
    action_distance: float,
    capability_threshold: float,
    action_threshold: float,
) -> str:
    capability_active = float(capability_z_distance) >= float(capability_threshold)
    action_active = float(action_distance) >= float(action_threshold)
    if capability_active and not action_active:
        return "belief_only_gap"
    if capability_active and action_active:
        return "action_and_belief"
    if not capability_active and action_active:
        return "action_without_belief"
    return "inactive"


def _load_rows(paths: list[Path | str], *, row_type: str) -> pd.DataFrame:
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        frame["source_csv"] = str(path)
        frames.append(frame)
    if not frames:
        raise ValueError(f"at least one {row_type} CSV is required")
    return pd.concat(frames, ignore_index=True)


def build_coupling_rows(
    *,
    capability_rows: pd.DataFrame,
    action_rows: pd.DataFrame,
    capability_threshold: float = 0.25,
    action_threshold: float = 0.02,
    coupling_gap_epsilon: float = 1e-6,
) -> list[dict[str, Any]]:
    missing_capability = [column for column in JOIN_COLUMNS if column not in capability_rows.columns]
    missing_action = [column for column in JOIN_COLUMNS if column not in action_rows.columns]
    if missing_capability:
        raise ValueError(f"capability rows missing columns: {missing_capability}")
    if missing_action:
        raise ValueError(f"action rows missing columns: {missing_action}")
    merged = capability_rows.merge(
        action_rows,
        on=list(JOIN_COLUMNS),
        how="inner",
        suffixes=("_capability", "_action"),
    )
    if merged.empty:
        raise ValueError("no coupling rows after joining capability and action artifacts")

    output_rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        capability_distance = float(row["capability_z_distance"])
        action_distance = float(row["action_distance"])
        class_name = coupling_class(
            capability_z_distance=capability_distance,
            action_distance=action_distance,
            capability_threshold=capability_threshold,
            action_threshold=action_threshold,
        )
        is_real_history = str(row["variant"]) in REAL_HISTORY_VARIANTS
        output_rows.append(
            {
                "pair_id": int(row["pair_id"]),
                "checkpoint_label": str(row["checkpoint_label"]),
                "source_checkpoint_label": str(row["source_checkpoint_label"]),
                "surface": str(row["surface"]),
                "probe_seed": int(row["probe_seed"]),
                "target": str(row["target"]),
                "variant": str(row["variant"]),
                "variant_kind": str(row.get("variant_kind", "")),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "visible_distance": float(row.get("visible_distance_capability", row.get("visible_distance", np.nan))),
                "target_z_delta": float(row.get("target_z_delta_capability", row.get("target_z_delta", np.nan))),
                "capability_z_distance": capability_distance,
                "action_distance": action_distance,
                "coupling_gap": float(capability_distance / max(float(action_distance), float(coupling_gap_epsilon))),
                "coupling_class": class_name,
                "capability_active": bool(capability_distance >= float(capability_threshold)),
                "action_active": bool(action_distance >= float(action_threshold)),
                "is_real_history_variant": bool(is_real_history),
                "candidate_for_grounding": bool(is_real_history and class_name == "belief_only_gap"),
                "grounding_status": "requires_grounding"
                if is_real_history and class_name == "belief_only_gap"
                else "not_a_grounded_target",
                "normal_steer": float(row["normal_steer"]),
                "normal_throttle": float(row["normal_throttle"]),
                "normal_brake": float(row["normal_brake"]),
                "variant_steer": float(row["variant_steer"]),
                "variant_throttle": float(row["variant_throttle"]),
                "variant_brake": float(row["variant_brake"]),
                "normal_future_braking_deceleration": float(row["normal_future_braking_deceleration"]),
                "variant_future_braking_deceleration": float(row["variant_future_braking_deceleration"]),
                "normal_future_yaw_response": float(row["normal_future_yaw_response"]),
                "variant_future_yaw_response": float(row["variant_future_yaw_response"]),
                "normal_future_lateral_accel_response": float(row["normal_future_lateral_accel_response"]),
                "variant_future_lateral_accel_response": float(row["variant_future_lateral_accel_response"]),
                "source_csv_capability": str(row.get("source_csv_capability", "")),
                "source_csv_action": str(row.get("source_csv_action", "")),
            }
        )
    return output_rows


def _class_counts(group: pd.DataFrame) -> dict[str, int]:
    counts = group["coupling_class"].value_counts()
    return {f"{name}_count": int(counts.get(name, 0)) for name in COUPLING_CLASSES}


def summarize_coupling_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], []
    frame = pd.DataFrame(rows)
    by_target: list[dict[str, Any]] = []
    aggregate: list[dict[str, Any]] = []
    for (surface, target, variant), group in frame.groupby(["surface", "target", "variant"], observed=True):
        row: dict[str, Any] = {
            "surface": str(surface),
            "target": str(target),
            "variant": str(variant),
            "pair_count": int(len(group)),
            "real_history_pair_count": int(group["is_real_history_variant"].astype(bool).sum()),
            "candidate_for_grounding_count": int(group["candidate_for_grounding"].astype(bool).sum()),
            "capability_z_distance_mean": float(group["capability_z_distance"].astype(float).mean()),
            "action_distance_mean": float(group["action_distance"].astype(float).mean()),
            "coupling_gap_median": float(group["coupling_gap"].astype(float).median()),
            "coupling_gap_p90": float(group["coupling_gap"].astype(float).quantile(0.90)),
        }
        row.update(_class_counts(group))
        by_target.append(row)
    for (surface, variant), group in frame.groupby(["surface", "variant"], observed=True):
        row = {
            "surface": str(surface),
            "variant": str(variant),
            "pair_count": int(len(group)),
            "real_history_pair_count": int(group["is_real_history_variant"].astype(bool).sum()),
            "candidate_for_grounding_count": int(group["candidate_for_grounding"].astype(bool).sum()),
            "capability_z_distance_mean": float(group["capability_z_distance"].astype(float).mean()),
            "action_distance_mean": float(group["action_distance"].astype(float).mean()),
            "coupling_gap_median": float(group["coupling_gap"].astype(float).median()),
            "coupling_gap_p90": float(group["coupling_gap"].astype(float).quantile(0.90)),
        }
        row.update(_class_counts(group))
        aggregate.append(row)
    return by_target, aggregate


def run_guarded_capability_action_coupling_evaluator(
    *,
    capability_row_paths: list[Path],
    action_row_paths: list[Path],
    capability_threshold: float,
    action_threshold: float,
    coupling_gap_epsilon: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    capability_frame = _load_rows(capability_row_paths, row_type="capability")
    action_frame = _load_rows(action_row_paths, row_type="action")
    rows = build_coupling_rows(
        capability_rows=capability_frame,
        action_rows=action_frame,
        capability_threshold=capability_threshold,
        action_threshold=action_threshold,
        coupling_gap_epsilon=coupling_gap_epsilon,
    )
    variant_rows, aggregate_rows = summarize_coupling_rows(rows)
    frame = pd.DataFrame(rows)
    real_history = frame[frame["is_real_history_variant"].astype(bool)]
    summary = {
        "run_type": "guarded_capability_action_coupling_evaluator",
        "capability_row_paths": capability_row_paths,
        "action_row_paths": action_row_paths,
        "capability_threshold": float(capability_threshold),
        "action_threshold": float(action_threshold),
        "coupling_gap_epsilon": float(coupling_gap_epsilon),
        "capability_input_rows": int(len(capability_frame)),
        "action_input_rows": int(len(action_frame)),
        "coupling_row_count": int(len(rows)),
        "variant_summary_rows": int(len(variant_rows)),
        "variant_aggregate_summary_rows": int(len(aggregate_rows)),
        "belief_only_gap_count": int((frame["coupling_class"] == "belief_only_gap").sum()),
        "real_history_belief_only_gap_count": int(
            ((frame["coupling_class"] == "belief_only_gap") & frame["is_real_history_variant"].astype(bool)).sum()
        ),
        "real_history_candidate_for_grounding_count": int(real_history["candidate_for_grounding"].astype(bool).sum()),
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "coupling_rows_csv": run_dir / "coupling_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "variant_aggregate_summary_csv": run_dir / "variant_aggregate_summary.csv",
    }
    write_csv_rows(run_dir / "coupling_rows.csv", rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_rows)
    write_csv_rows(run_dir / "variant_aggregate_summary.csv", aggregate_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate capability-action coupling gaps without model updates.")
    parser.add_argument("--capability-rows", type=Path, action="append", required=True)
    parser.add_argument("--action-rows", type=Path, action="append", required=True)
    parser.add_argument("--capability-threshold", type=float, default=0.25)
    parser.add_argument("--action-threshold", type=float, default=0.02)
    parser.add_argument("--coupling-gap-epsilon", type=float, default=1e-6)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="guarded_capability_action_coupling_evaluator")
    summary = run_guarded_capability_action_coupling_evaluator(
        capability_row_paths=list(args.capability_rows),
        action_row_paths=list(args.action_rows),
        capability_threshold=args.capability_threshold,
        action_threshold=args.action_threshold,
        coupling_gap_epsilon=args.coupling_gap_epsilon,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
