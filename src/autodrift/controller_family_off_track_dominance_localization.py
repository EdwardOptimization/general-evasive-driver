"""No-rollout localization of off-track dominance in calibrated scale-up rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import aggregate_outcome_rows
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite


DEFAULT_EPISODE_ROWS = Path("runs/m1715_controller_family_calibrated_scale_up_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1718_off_track_dominance_localization")
TARGET_EPISODE_COUNT = 864
MIN_TARGET_EPISODES = 12
OFF_TRACK_TARGET_THRESHOLD = 0.80
COLLISION_GUARD_THRESHOLD = 0.10
FORBIDDEN_GUARDRAILS = (
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


def _rate(row: Mapping[str, Any], key: str) -> float:
    try:
        return float(row.get(key, "nan"))
    except (TypeError, ValueError):
        return float("nan")


def _repair_targets_from_aggregate(
    aggregate_rows: list[dict[str, Any]],
    *,
    slice_type: str,
    slice_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for row in aggregate_rows:
        episode_count = int(row.get("episode_count", 0))
        off_track_rate = _rate(row, "off_track_noncollision_noncompletion_rate")
        collision_rate = _rate(row, "collision_failure_rate")
        if (
            episode_count >= MIN_TARGET_EPISODES
            and off_track_rate >= OFF_TRACK_TARGET_THRESHOLD
            and collision_rate <= COLLISION_GUARD_THRESHOLD
        ):
            targets.append(
                {
                    "slice_type": slice_type,
                    "slice_id": "::".join(str(row.get(key, "")) for key in slice_keys),
                    **{key: row.get(key, "") for key in slice_keys},
                    "episode_count": episode_count,
                    "success_obstacle_pass_rate": row.get("success_obstacle_pass_rate", ""),
                    "collision_failure_rate": collision_rate,
                    "off_track_noncollision_noncompletion_rate": off_track_rate,
                    "clearance_margin_mean": row.get("clearance_margin_mean", ""),
                    "repair_reason": (
                        f"off_track>={OFF_TRACK_TARGET_THRESHOLD} "
                        f"and collision<={COLLISION_GUARD_THRESHOLD}"
                    ),
                    "diagnostic_only_no_ranking_claim": True,
                }
            )
    return sorted(
        targets,
        key=lambda row: (
            str(row["slice_type"]),
            -float(row["off_track_noncollision_noncompletion_rate"]),
            float(row["collision_failure_rate"]),
            str(row["slice_id"]),
        ),
    )


def localize_off_track_dominance(
    *,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episode_rows = [dict(row) for row in read_csv_rows(episode_rows_path)]

    variant_source_edge_aggregate = aggregate_outcome_rows(episode_rows, ("scale_up_variant_label", "source_edge"))
    variant_task_family_aggregate = aggregate_outcome_rows(episode_rows, ("scale_up_variant_label", "task_family"))
    variant_profile_aggregate = aggregate_outcome_rows(episode_rows, ("scale_up_variant_label", "profile_name"))
    source_task_family_aggregate = aggregate_outcome_rows(episode_rows, ("source_edge", "task_family"))
    profile_outcome_aggregate = aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket"))

    repair_target_slices = []
    repair_target_slices.extend(
        _repair_targets_from_aggregate(
            variant_source_edge_aggregate,
            slice_type="variant_source_edge",
            slice_keys=("scale_up_variant_label", "source_edge"),
        )
    )
    repair_target_slices.extend(
        _repair_targets_from_aggregate(
            variant_task_family_aggregate,
            slice_type="variant_task_family",
            slice_keys=("scale_up_variant_label", "task_family"),
        )
    )
    repair_target_slices.extend(
        _repair_targets_from_aggregate(
            source_task_family_aggregate,
            slice_type="source_task_family",
            slice_keys=("source_edge", "task_family"),
        )
    )

    write_csv_rows(output / "variant_source_edge_aggregate.csv", variant_source_edge_aggregate)
    write_csv_rows(output / "variant_task_family_aggregate.csv", variant_task_family_aggregate)
    write_csv_rows(output / "variant_profile_aggregate.csv", variant_profile_aggregate)
    write_csv_rows(output / "source_task_family_aggregate.csv", source_task_family_aggregate)
    write_csv_rows(output / "profile_outcome_aggregate.csv", profile_outcome_aggregate)
    write_csv_rows(output / "repair_target_slices.csv", repair_target_slices)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    result_passes = (
        len(episode_rows) == TARGET_EPISODE_COUNT
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and bool(variant_source_edge_aggregate)
        and bool(variant_task_family_aggregate)
        and bool(variant_profile_aggregate)
        and bool(source_task_family_aggregate)
        and bool(repair_target_slices)
    )
    summary = {
        "result_class": (
            "off_track_dominance_localization_pass"
            if result_passes
            else "off_track_dominance_localization_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "episode_rows_path": str(episode_rows_path),
        "episode_count": len(episode_rows),
        "target_episode_count": TARGET_EPISODE_COUNT,
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        "variant_source_edge_aggregate_rows": len(variant_source_edge_aggregate),
        "variant_task_family_aggregate_rows": len(variant_task_family_aggregate),
        "variant_profile_aggregate_rows": len(variant_profile_aggregate),
        "source_task_family_aggregate_rows": len(source_task_family_aggregate),
        "profile_outcome_aggregate_rows": len(profile_outcome_aggregate),
        "repair_target_slice_count": len(repair_target_slices),
        "repair_target_thresholds": {
            "min_target_episodes": MIN_TARGET_EPISODES,
            "off_track_target_threshold": OFF_TRACK_TARGET_THRESHOLD,
            "collision_guard_threshold": COLLISION_GUARD_THRESHOLD,
        },
        "top_repair_target": repair_target_slices[0] if repair_target_slices else None,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
            "variant_source_edge_aggregate": str(output / "variant_source_edge_aggregate.csv"),
            "variant_task_family_aggregate": str(output / "variant_task_family_aggregate.csv"),
            "variant_profile_aggregate": str(output / "variant_profile_aggregate.csv"),
            "source_task_family_aggregate": str(output / "source_task_family_aggregate.csv"),
            "profile_outcome_aggregate": str(output / "profile_outcome_aggregate.csv"),
            "repair_target_slices": str(output / "repair_target_slices.csv"),
        },
        "next_blocker": "m1719-paper-route-controller-family-off-track-dominance-localization-result-audit",
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Localize off-track dominance from M1715 episode rows.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = localize_off_track_dominance(episode_rows_path=args.episode_rows, output_dir=args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"repair_target_slice_count={summary['repair_target_slice_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
