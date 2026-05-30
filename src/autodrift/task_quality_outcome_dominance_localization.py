"""No-rollout localization of task-quality outcome dominance in repaired taxonomy rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import aggregate_outcome_rows
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite


DEFAULT_EPISODE_ROWS = Path("runs/m1738_repaired_scenario_taxonomy_execution/episode_rows.csv")
DEFAULT_SUMMARY = Path("runs/m1738_repaired_scenario_taxonomy_execution/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1740_repaired_taxonomy_outcome_dominance_localization")
TARGET_EPISODE_COUNT = 864
MIN_DOMINANT_EPISODES = 12
NON_SUCCESS_DOMINANCE_THRESHOLD = 0.75
OUTCOME_DOMINANCE_THRESHOLD = 0.50
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
    "unsupported_faults_treated_as_covered",
)


def _float(row: Mapping[str, Any], key: str) -> float:
    try:
        return float(row.get(key, "nan"))
    except (TypeError, ValueError):
        return float("nan")


def _int(row: Mapping[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0)))
    except (TypeError, ValueError):
        return 0


def _dominant_non_success(row: Mapping[str, Any]) -> tuple[str, float]:
    candidates = {
        "collision_failure": _float(row, "collision_failure_rate"),
        "off_track_noncollision_noncompletion": _float(row, "off_track_noncollision_noncompletion_rate"),
        "max_steps_noncompletion": _float(row, "max_steps_noncompletion_rate"),
        "safe_noncollision_noncompletion": _float(row, "safe_noncollision_noncompletion_rate"),
    }
    outcome, rate = max(candidates.items(), key=lambda item: item[1])
    return outcome, rate


def dominant_slices_from_aggregates(
    aggregate_rows: list[dict[str, Any]],
    *,
    slice_type: str,
    slice_keys: tuple[str, ...],
    min_episode_count: int = MIN_DOMINANT_EPISODES,
) -> list[dict[str, Any]]:
    """Find non-success-dominated slices without turning them into ranking claims."""

    dominant: list[dict[str, Any]] = []
    for row in aggregate_rows:
        episode_count = _int(row, "episode_count")
        if episode_count < min_episode_count:
            continue
        success_rate = _float(row, "success_obstacle_pass_rate")
        collision_rate = _float(row, "collision_failure_rate")
        off_track_rate = _float(row, "off_track_noncollision_noncompletion_rate")
        max_steps_rate = _float(row, "max_steps_noncompletion_rate")
        safe_noncompletion_rate = _float(row, "safe_noncollision_noncompletion_rate")
        non_success_rate = 1.0 - success_rate
        dominant_outcome, dominant_rate = _dominant_non_success(row)
        if non_success_rate < NON_SUCCESS_DOMINANCE_THRESHOLD and dominant_rate < OUTCOME_DOMINANCE_THRESHOLD:
            continue
        dominant.append(
            {
                "slice_type": slice_type,
                "slice_id": "::".join(str(row.get(key, "")) for key in slice_keys),
                **{key: row.get(key, "") for key in slice_keys},
                "episode_count": episode_count,
                "success_obstacle_pass_rate": success_rate,
                "collision_failure_rate": collision_rate,
                "off_track_noncollision_noncompletion_rate": off_track_rate,
                "max_steps_noncompletion_rate": max_steps_rate,
                "safe_noncollision_noncompletion_rate": safe_noncompletion_rate,
                "non_success_rate": non_success_rate,
                "dominant_outcome": dominant_outcome,
                "dominant_outcome_rate": dominant_rate,
                "clearance_margin_mean": row.get("clearance_margin_mean", ""),
                "clearance_margin_p10": row.get("clearance_margin_p10", ""),
                "localization_reason": (
                    f"non_success>={NON_SUCCESS_DOMINANCE_THRESHOLD} "
                    f"or dominant_outcome>={OUTCOME_DOMINANCE_THRESHOLD}"
                ),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
    return sorted(
        dominant,
        key=lambda row: (
            -float(row["non_success_rate"]),
            -float(row["dominant_outcome_rate"]),
            str(row["slice_type"]),
            str(row["slice_id"]),
        ),
    )


def _write_aggregate(output: Path, name: str, rows: list[dict[str, Any]]) -> int:
    write_csv_rows(output / f"{name}.csv", rows)
    return len(rows)


def localize_task_quality_outcome_dominance(
    *,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    summary_path: Path | str = DEFAULT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episode_rows = [dict(row) for row in read_csv_rows(episode_rows_path)]
    source_summary = read_json(summary_path) if Path(summary_path).exists() else {}

    aggregate_specs: dict[str, tuple[str, ...]] = {
        "scenario_family_aggregate": ("scenario_family",),
        "scenario_family_label_aggregate": ("scenario_family", "sampled_obstacle_label"),
        "scenario_family_profile_aggregate": ("scenario_family", "profile_name"),
        "scenario_family_road_bucket_aggregate": ("scenario_family", "road_boundary_bucket"),
        "scenario_family_hidden_bucket_aggregate": ("scenario_family", "hidden_dynamics_bucket"),
        "scenario_family_timing_bucket_aggregate": ("scenario_family", "obstacle_timing_bucket"),
        "sampling_repair_variant_aggregate": ("sampling_repair_variant_id",),
        "profile_aggregate": ("profile_name",),
    }

    aggregate_rows: dict[str, list[dict[str, Any]]] = {
        name: aggregate_outcome_rows(episode_rows, keys) for name, keys in aggregate_specs.items()
    }
    aggregate_rows["profile_outcome_aggregate"] = aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket"))
    aggregate_rows["scenario_family_outcome_aggregate"] = aggregate_outcome_rows(
        episode_rows,
        ("scenario_family", "outcome_bucket"),
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

    dominant_family_count = len(
        {
            str(row.get("scenario_family"))
            for row in dominant_slices
            if row.get("scenario_family") not in (None, "")
        }
    )
    dominant_profile_count = len(
        {str(row.get("profile_name")) for row in dominant_slices if row.get("profile_name") not in (None, "")}
    )
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    result_passes = (
        len(episode_rows) == target_episode_count
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and bool(dominant_slices)
        and bool(aggregate_rows["scenario_family_aggregate"])
        and bool(aggregate_rows["profile_aggregate"])
        and bool(aggregate_rows["scenario_family_label_aggregate"])
    )
    outcome_dominance_class = (
        "diffuse_outcome_dominance"
        if dominant_family_count >= 5 and dominant_profile_count >= 8
        else "localized_outcome_dominance"
    )
    summary = {
        "result_class": (
            "task_quality_outcome_dominance_localization_pass"
            if result_passes
            else "task_quality_outcome_dominance_localization_incomplete_or_fail"
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
        "dominant_family_count": dominant_family_count,
        "dominant_profile_count": dominant_profile_count,
        "outcome_dominance_class": outcome_dominance_class,
        "dominance_thresholds": {
            "min_dominant_episodes": MIN_DOMINANT_EPISODES,
            "non_success_dominance_threshold": NON_SUCCESS_DOMINANCE_THRESHOLD,
            "outcome_dominance_threshold": OUTCOME_DOMINANCE_THRESHOLD,
        },
        "top_dominant_slice": dominant_slices[0] if dominant_slices else None,
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
        "unsupported_faults_treated_as_covered": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "dominant_slices": str(output / "dominant_slices.csv"),
            **{name: str(output / f"{name}.csv") for name in aggregate_rows},
        },
        "next_blocker": "m1741-paper-route-task-quality-repaired-taxonomy-outcome-dominance-result-audit",
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Localize task-quality outcome dominance from M1738 rows.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = localize_task_quality_outcome_dominance(
        episode_rows_path=args.episode_rows,
        summary_path=args.summary,
        output_dir=args.output_dir,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"dominant_slice_count={summary['dominant_slice_count']}")
    print(f"outcome_dominance_class={summary['outcome_dominance_class']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
