"""No-rollout outcome localization for the metric-specific bounded panel."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import aggregate_outcome_rows
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite
from autodrift.task_quality_outcome_dominance_localization import dominant_slices_from_aggregates


DEFAULT_EPISODE_ROWS = Path("runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv")
DEFAULT_SUMMARY = Path("runs/m1777_metric_specific_bounded_panel_measured_execution/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1779_metric_specific_bounded_panel_outcome_localization")
DEFAULT_NEXT_BLOCKER = "m1780-paper-route-metric-specific-bounded-panel-branch-synthesis"
TARGET_EPISODE_COUNT = 288
TARGET_LOCALIZATION_SLICE_TYPES = (
    "role_panel",
    "role_panel_profile",
    "role_panel_primary_metric",
    "role_panel_hidden_bucket",
    "role_panel_road_bucket",
    "role_panel_timing_bucket",
    "role_panel_lateral_bucket",
    "role_panel_sampled_label",
    "profile",
    "profile_role_panel",
    "profile_primary_metric",
    "primary_metric_family",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "sampled_obstacle_label",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _write_aggregate(output: Path, name: str, rows: list[dict[str, Any]]) -> int:
    write_csv_rows(output / f"{name}.csv", rows)
    return len(rows)


def _dominant_slice_counts_by_type(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        slice_type = str(row.get("slice_type", ""))
        counts[slice_type] = counts.get(slice_type, 0) + 1
    return dict(sorted(counts.items()))


def localize_metric_specific_bounded_panel_outcomes(
    *,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    summary_path: Path | str = DEFAULT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episode_rows = [dict(row) for row in read_csv_rows(episode_rows_path)]
    source_summary = read_json(summary_path) if Path(summary_path).exists() else {}

    aggregate_specs: dict[str, tuple[str, ...]] = {
        "role_panel_aggregate": ("role_panel_id",),
        "role_panel_profile_aggregate": ("role_panel_id", "profile_name"),
        "role_panel_primary_metric_aggregate": ("role_panel_id", "primary_metric_family"),
        "role_panel_hidden_bucket_aggregate": ("role_panel_id", "hidden_dynamics_bucket"),
        "role_panel_road_bucket_aggregate": ("role_panel_id", "road_boundary_bucket"),
        "role_panel_timing_bucket_aggregate": ("role_panel_id", "obstacle_timing_bucket"),
        "role_panel_lateral_bucket_aggregate": ("role_panel_id", "obstacle_lateral_bucket"),
        "role_panel_sampled_label_aggregate": ("role_panel_id", "sampled_obstacle_label"),
        "profile_aggregate": ("profile_name",),
        "profile_role_panel_aggregate": ("profile_name", "role_panel_id"),
        "profile_primary_metric_aggregate": ("profile_name", "primary_metric_family"),
        "primary_metric_family_aggregate": ("primary_metric_family",),
        "hidden_dynamics_bucket_aggregate": ("hidden_dynamics_bucket",),
        "road_boundary_bucket_aggregate": ("road_boundary_bucket",),
        "obstacle_timing_bucket_aggregate": ("obstacle_timing_bucket",),
        "obstacle_lateral_bucket_aggregate": ("obstacle_lateral_bucket",),
        "sampled_obstacle_label_aggregate": ("sampled_obstacle_label",),
    }
    aggregate_rows: dict[str, list[dict[str, Any]]] = {
        name: aggregate_outcome_rows(episode_rows, keys) for name, keys in aggregate_specs.items()
    }
    aggregate_rows["role_panel_outcome_aggregate"] = aggregate_outcome_rows(
        episode_rows,
        ("role_panel_id", "outcome_bucket"),
    )
    aggregate_rows["profile_outcome_aggregate"] = aggregate_outcome_rows(
        episode_rows,
        ("profile_name", "outcome_bucket"),
    )
    aggregate_rows["primary_metric_family_outcome_aggregate"] = aggregate_outcome_rows(
        episode_rows,
        ("primary_metric_family", "outcome_bucket"),
    )

    aggregate_row_counts = {
        f"{name}_rows": _write_aggregate(output, name, rows) for name, rows in aggregate_rows.items()
    }

    dominant_slices: list[dict[str, Any]] = []
    for name, keys in aggregate_specs.items():
        dominant_slices.extend(
            dominant_slices_from_aggregates(
                aggregate_rows[name],
                slice_type=name.removesuffix("_aggregate"),
                slice_keys=keys,
            )
        )
    dominant_slices = sorted(
        dominant_slices,
        key=lambda row: (
            -float(row["non_success_rate"]),
            -float(row["dominant_outcome_rate"]),
            str(row["slice_type"]),
            str(row["slice_id"]),
        ),
    )
    write_csv_rows(output / "dominant_slices.csv", dominant_slices)
    target_dominant_slices = [
        row for row in dominant_slices if str(row.get("slice_type", "")) in TARGET_LOCALIZATION_SLICE_TYPES
    ]
    write_csv_rows(output / "target_dominant_slices.csv", target_dominant_slices)

    dominant_role_panel_count = len(
        {str(row.get("role_panel_id")) for row in dominant_slices if row.get("role_panel_id") not in (None, "")}
    )
    dominant_profile_count = len(
        {str(row.get("profile_name")) for row in dominant_slices if row.get("profile_name") not in (None, "")}
    )
    dominant_primary_metric_count = len(
        {
            str(row.get("primary_metric_family"))
            for row in dominant_slices
            if row.get("primary_metric_family") not in (None, "")
        }
    )
    target_slice_types_present = sorted(
        {
            str(row.get("slice_type", ""))
            for row in target_dominant_slices
            if str(row.get("slice_type", "")) in TARGET_LOCALIZATION_SLICE_TYPES
        }
    )
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    outcome_dominance_class = (
        "diffuse_role_profile_outcome_dominance"
        if dominant_role_panel_count >= 3 and dominant_profile_count >= 8
        else "localized_role_profile_outcome_dominance"
    )
    ranking_blocked = bool(dominant_slices)
    result_passes = (
        len(episode_rows) == target_episode_count
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and bool(dominant_slices)
        and bool(aggregate_rows["role_panel_aggregate"])
        and bool(aggregate_rows["profile_aggregate"])
        and bool(aggregate_rows["primary_metric_family_aggregate"])
    )

    summary = {
        "result_class": (
            "metric_specific_bounded_panel_outcome_localization_pass"
            if result_passes
            else "metric_specific_bounded_panel_outcome_localization_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "episode_rows_path": str(episode_rows_path),
        "source_summary_path": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "episode_count": len(episode_rows),
        "target_episode_count": target_episode_count,
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_row_counts,
        "dominant_slice_count": len(dominant_slices),
        "target_dominant_slice_count": len(target_dominant_slices),
        "target_localization_slice_types": list(TARGET_LOCALIZATION_SLICE_TYPES),
        "target_slice_types_present": target_slice_types_present,
        "dominant_slice_counts_by_type": _dominant_slice_counts_by_type(dominant_slices),
        "dominant_role_panel_count": dominant_role_panel_count,
        "dominant_profile_count": dominant_profile_count,
        "dominant_primary_metric_count": dominant_primary_metric_count,
        "outcome_dominance_class": outcome_dominance_class,
        "ranking_blocked": ranking_blocked,
        "top_dominant_slice": dominant_slices[0] if dominant_slices else None,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "dominant_slices": str(output / "dominant_slices.csv"),
            "target_dominant_slices": str(output / "target_dominant_slices.csv"),
            **{name: str(output / f"{name}.csv") for name in aggregate_rows},
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Localize bounded-panel outcome dominance from M1777 rows.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = localize_metric_specific_bounded_panel_outcomes(
        episode_rows_path=args.episode_rows,
        summary_path=args.summary,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"dominant_slice_count={summary['dominant_slice_count']}")
    print(f"target_dominant_slice_count={summary['target_dominant_slice_count']}")
    print(f"outcome_dominance_class={summary['outcome_dominance_class']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
