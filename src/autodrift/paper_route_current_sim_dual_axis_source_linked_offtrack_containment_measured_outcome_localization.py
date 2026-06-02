"""Artifact-only localization for M2413 source-linked measured outcomes."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_measured_outcome_localization as base_localization
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path("runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization"
)
DEFAULT_TARGET_EPISODE_COUNT = 5250
DEFAULT_TARGET_FAMILY_MEMBERSHIP_ROW_COUNT = 18300
DEFAULT_MINIMUM_SLICE_EPISODE_COUNT = 30
DEFAULT_OFFTRACK_TARGET_THRESHOLD = 0.70
DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD = 0.85
DEFAULT_COLLISION_GUARDRAIL_THRESHOLD = 0.15
DEFAULT_SPEED_TOO_LOW_THRESHOLD = 0.05
DEFAULT_NEXT_BLOCKER = (
    "m2416-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_incomplete_or_fail"

PRIMARY_SINGLE_AXES = (
    ("global", ("global",)),
    ("reset_target_key", ("reset_target_key",)),
    ("pack_id", ("pack_id",)),
    ("profile_name", ("profile_name",)),
    ("role_family", ("role_family",)),
    ("scenario_family_id", ("scenario_family_id",)),
    ("sampled_obstacle_label", ("sampled_obstacle_label",)),
    ("hidden_dynamics_bucket", ("hidden_dynamics_bucket",)),
    ("obstacle_longitudinal_timing_bucket", ("obstacle_longitudinal_timing_bucket",)),
    ("obstacle_lateral_offset_bucket", ("obstacle_lateral_offset_bucket",)),
    ("outcome_bucket", ("outcome_bucket",)),
)
PRIMARY_COMPOSITE_AXES = (
    ("reset_target_key+profile_name", ("reset_target_key", "profile_name")),
    ("reset_target_key+role_family", ("reset_target_key", "role_family")),
    ("profile_name+role_family", ("profile_name", "role_family")),
    ("role_family+hidden_dynamics_bucket", ("role_family", "hidden_dynamics_bucket")),
    ("role_family+obstacle_longitudinal_timing_bucket", ("role_family", "obstacle_longitudinal_timing_bucket")),
    ("role_family+obstacle_lateral_offset_bucket", ("role_family", "obstacle_lateral_offset_bucket")),
    ("pack_id+profile_name+role_family", ("pack_id", "profile_name", "role_family")),
)
MEMBERSHIP_SINGLE_AXES = (
    ("family_id", ("family_id",)),
    ("family_id+profile_name", ("family_id", "profile_name")),
    ("family_id+pack_id", ("family_id", "pack_id")),
    ("family_id+role_family", ("family_id", "role_family")),
    ("family_id+hidden_dynamics_bucket", ("family_id", "hidden_dynamics_bucket")),
    ("family_id+sampled_obstacle_label", ("family_id", "sampled_obstacle_label")),
)
EXTRA_FIELDNAMES = [
    "source_table",
    "source_linked_outcome_localization",
    "candidate_family_ranking_claim_made",
    "support_policy_ranking_claim_made",
    "current_sim_verdict_claim_made",
    "training_repair_success_claim_made",
    "speed_too_low_count",
    "speed_too_low_rate",
    "is_speed_too_low_target",
    "is_max_step_target",
]
SLICE_FIELDNAMES = [*base_localization.SLICE_FIELDNAMES, *EXTRA_FIELDNAMES]
CLAIM_FIELDNAMES = base_localization.CLAIM_FIELDNAMES


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_localization._bool(value, default=default)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return base_localization.read_csv_rows(path)


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _slice_value(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    if keys == ("global",):
        return "all"
    return "|".join(str(row.get(key, "")) for key in keys)


def _group_rows(rows: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> dict[str, list[Mapping[str, Any]]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_slice_value(row, keys)].append(row)
    return dict(groups)


def _is_speed_too_low(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("outcome_bucket", "")) == "speed_too_low_noncollision_noncompletion"
        or str(row.get("termination_reason", "")) == "speed_too_low"
    )


def _speed_too_low_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _is_speed_too_low(row))


def _augment_slice(
    row: Mapping[str, Any],
    *,
    source_table: str,
    rows: Sequence[Mapping[str, Any]],
    speed_too_low_threshold: float,
) -> dict[str, Any]:
    output = dict(row)
    total = len(rows)
    speed_count = _speed_too_low_count(rows)
    speed_rate = _rate(speed_count, total)
    max_step_rate = float(output.get("max_step_noncompletion_rate", 0.0) or 0.0)
    output.update(
        {
            "source_table": source_table,
            "source_linked_outcome_localization": True,
            "candidate_family_ranking_claim_made": False,
            "support_policy_ranking_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
            "speed_too_low_count": int(speed_count),
            "speed_too_low_rate": float(speed_rate),
            "is_speed_too_low_target": bool(speed_count > 0 and speed_rate >= float(speed_too_low_threshold)),
            "is_max_step_target": bool(max_step_rate > 0.0),
        }
    )
    return output


def _build_slice_rows_for_axes(
    rows: Sequence[Mapping[str, Any]],
    *,
    axes: Sequence[tuple[str, Sequence[str]]],
    source_table: str,
    minimum_slice_episode_count: int,
    offtrack_target_threshold: float,
    high_priority_offtrack_threshold: float,
    collision_guardrail_threshold: float,
    speed_too_low_threshold: float,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for axis, keys in axes:
        for value, group in sorted(_group_rows(rows, keys).items()):
            base_row = base_localization.slice_row(
                slice_axis=axis,
                slice_key="+".join(keys),
                slice_value=value,
                rows=group,
                minimum_slice_episode_count=minimum_slice_episode_count,
                offtrack_target_threshold=offtrack_target_threshold,
                high_priority_offtrack_threshold=high_priority_offtrack_threshold,
                collision_guardrail_threshold=collision_guardrail_threshold,
            )
            output.append(
                _augment_slice(
                    base_row,
                    source_table=source_table,
                    rows=group,
                    speed_too_low_threshold=speed_too_low_threshold,
                )
            )
    return output


def build_slice_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    membership_rows: Sequence[Mapping[str, Any]],
    minimum_slice_episode_count: int,
    offtrack_target_threshold: float,
    high_priority_offtrack_threshold: float,
    collision_guardrail_threshold: float,
    speed_too_low_threshold: float,
) -> list[dict[str, Any]]:
    primary_axes = (*PRIMARY_SINGLE_AXES, *PRIMARY_COMPOSITE_AXES)
    rows = _build_slice_rows_for_axes(
        episode_rows,
        axes=primary_axes,
        source_table="episode_rows",
        minimum_slice_episode_count=minimum_slice_episode_count,
        offtrack_target_threshold=offtrack_target_threshold,
        high_priority_offtrack_threshold=high_priority_offtrack_threshold,
        collision_guardrail_threshold=collision_guardrail_threshold,
        speed_too_low_threshold=speed_too_low_threshold,
    )
    rows.extend(
        _build_slice_rows_for_axes(
            membership_rows,
            axes=MEMBERSHIP_SINGLE_AXES,
            source_table="episode_family_membership_rows",
            minimum_slice_episode_count=minimum_slice_episode_count,
            offtrack_target_threshold=offtrack_target_threshold,
            high_priority_offtrack_threshold=high_priority_offtrack_threshold,
            collision_guardrail_threshold=collision_guardrail_threshold,
            speed_too_low_threshold=speed_too_low_threshold,
        )
    )
    return sorted(rows, key=lambda row: float(row["priority_score"]), reverse=True)


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_source_linked_outcome_localization",
            "admissible": True,
            "reason": "M2415 may claim only slice materialization from existing M2413 artifacts",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "family membership is overlapping diagnostic metadata and does not rank candidate families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "profile slices are diagnostic and do not rank support policies",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "slice rows are diagnostic and do not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2415 does not select or promote a winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2415 is artifact localization, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2415 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2415 does not run history interventions",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2415 localizes existing measured outcomes and does not redesign scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2415 does not train, repair, replay, or run PPO",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2415 localizes one artifact and does not make a current-sim verdict",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _unique_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows if str(row.get(key, "")).strip()})


def _write_outputs(
    *,
    output: Path,
    slice_rows: Sequence[Mapping[str, Any]],
    offtrack_rows: Sequence[Mapping[str, Any]],
    collision_rows: Sequence[Mapping[str, Any]],
    r4_rows: Sequence[Mapping[str, Any]],
    max_step_rows: Sequence[Mapping[str, Any]],
    speed_too_low_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
) -> None:
    write_csv_rows(output / "slice_rows.csv", list(slice_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "offtrack_target_slice_rows.csv", list(offtrack_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_slice_rows.csv", list(collision_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_semantics_rows.csv", list(r4_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "max_step_noncompletion_slice_rows.csv", list(max_step_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "speed_too_low_slice_rows.csv", list(speed_too_low_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "diagnostic_only_slice_rows.csv", list(diagnostic_rows), fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)


def run_source_linked_measured_outcome_localization(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = DEFAULT_TARGET_EPISODE_COUNT,
    target_family_membership_row_count: int = DEFAULT_TARGET_FAMILY_MEMBERSHIP_ROW_COUNT,
    minimum_slice_episode_count: int = DEFAULT_MINIMUM_SLICE_EPISODE_COUNT,
    offtrack_target_threshold: float = DEFAULT_OFFTRACK_TARGET_THRESHOLD,
    high_priority_offtrack_threshold: float = DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD,
    collision_guardrail_threshold: float = DEFAULT_COLLISION_GUARDRAIL_THRESHOLD,
    speed_too_low_threshold: float = DEFAULT_SPEED_TOO_LOW_THRESHOLD,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary_path = source / "summary.json"
    episode_rows_path = source / "episode_rows.csv"
    membership_rows_path = source / "episode_family_membership_rows.csv"
    source_summary = read_json(summary_path)
    episode_rows = read_csv_rows(episode_rows_path)
    membership_rows = read_csv_rows(membership_rows_path)
    slice_rows = build_slice_rows(
        episode_rows=episode_rows,
        membership_rows=membership_rows,
        minimum_slice_episode_count=minimum_slice_episode_count,
        offtrack_target_threshold=offtrack_target_threshold,
        high_priority_offtrack_threshold=high_priority_offtrack_threshold,
        collision_guardrail_threshold=collision_guardrail_threshold,
        speed_too_low_threshold=speed_too_low_threshold,
    )
    offtrack_rows = [row for row in slice_rows if _bool(row.get("is_offtrack_target"))]
    collision_rows = [row for row in slice_rows if _bool(row.get("is_collision_guardrail"))]
    r4_rows = [row for row in slice_rows if _bool(row.get("is_r4_mitigation_semantics"))]
    max_step_rows = [row for row in slice_rows if _bool(row.get("is_max_step_target"))]
    speed_too_low_rows = [row for row in slice_rows if _bool(row.get("is_speed_too_low_target"))]
    high_priority_offtrack_rows = [row for row in slice_rows if _bool(row.get("is_high_priority_offtrack"))]
    diagnostic_rows = [row for row in slice_rows if str(row.get("route_class", "")) == "diagnostic_only"]

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    ranking_admissible_count = _flag_count(slice_rows, "ranking_admissible")
    winner_selected_count = _flag_count(slice_rows, "winner_selected")
    source_episode_count = len(episode_rows)
    source_family_membership_row_count = len(membership_rows)
    passes = (
        source_episode_count == int(target_episode_count)
        and source_family_membership_row_count == int(target_family_membership_row_count)
        and str(source_summary.get("result_class", "")).endswith("_pass")
        and len(slice_rows) > 0
        and len(offtrack_rows) > 0
        and len(collision_rows) > 0
        and len(r4_rows) > 0
        and len(diagnostic_rows) > 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    _write_outputs(
        output=output,
        slice_rows=slice_rows,
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        r4_rows=r4_rows,
        max_step_rows=max_step_rows,
        speed_too_low_rows=speed_too_low_rows,
        diagnostic_rows=diagnostic_rows,
    )

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_dir": str(source),
        "source_summary": str(summary_path),
        "source_episode_rows": str(episode_rows_path),
        "source_family_membership_rows": str(membership_rows_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_episode_count": source_episode_count,
        "target_episode_count": int(target_episode_count),
        "source_family_membership_row_count": source_family_membership_row_count,
        "target_family_membership_row_count": int(target_family_membership_row_count),
        "source_reset_target_count": _unique_count(episode_rows, "reset_target_key"),
        "source_family_id_count": _unique_count(membership_rows, "family_id"),
        "source_profile_count": _unique_count(episode_rows, "profile_name"),
        "source_role_family_count": _unique_count(episode_rows, "role_family"),
        "slice_row_count": len(slice_rows),
        "episode_slice_row_count": sum(str(row.get("source_table", "")) == "episode_rows" for row in slice_rows),
        "family_membership_slice_row_count": sum(
            str(row.get("source_table", "")) == "episode_family_membership_rows" for row in slice_rows
        ),
        "offtrack_target_slice_count": len(offtrack_rows),
        "collision_guardrail_slice_count": len(collision_rows),
        "r4_mitigation_semantics_slice_count": len(r4_rows),
        "max_step_noncompletion_slice_count": len(max_step_rows),
        "speed_too_low_slice_count": len(speed_too_low_rows),
        "diagnostic_only_slice_count": len(diagnostic_rows),
        "high_priority_offtrack_slice_count": len(high_priority_offtrack_rows),
        "minimum_slice_episode_count": int(minimum_slice_episode_count),
        "offtrack_target_threshold": float(offtrack_target_threshold),
        "high_priority_offtrack_threshold": float(high_priority_offtrack_threshold),
        "collision_guardrail_threshold": float(collision_guardrail_threshold),
        "speed_too_low_threshold": float(speed_too_low_threshold),
        "route_class_counts": _count_by(slice_rows, "route_class"),
        "slice_axis_counts": _count_by(slice_rows, "slice_axis"),
        "source_table_counts": _count_by(slice_rows, "source_table"),
        "top_offtrack_target_slices": offtrack_rows[:10],
        "top_collision_guardrail_slices": collision_rows[:10],
        "top_r4_mitigation_semantics_slices": r4_rows[:10],
        "top_max_step_noncompletion_slices": max_step_rows[:10],
        "top_speed_too_low_slices": speed_too_low_rows[:10],
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "slice_rows": str(output / "slice_rows.csv"),
            "offtrack_target_slice_rows": str(output / "offtrack_target_slice_rows.csv"),
            "collision_guardrail_slice_rows": str(output / "collision_guardrail_slice_rows.csv"),
            "r4_mitigation_semantics_rows": str(output / "r4_mitigation_semantics_rows.csv"),
            "max_step_noncompletion_slice_rows": str(output / "max_step_noncompletion_slice_rows.csv"),
            "speed_too_low_slice_rows": str(output / "speed_too_low_slice_rows.csv"),
            "diagnostic_only_slice_rows": str(output / "diagnostic_only_slice_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=DEFAULT_TARGET_EPISODE_COUNT)
    parser.add_argument(
        "--target-family-membership-row-count",
        type=int,
        default=DEFAULT_TARGET_FAMILY_MEMBERSHIP_ROW_COUNT,
    )
    parser.add_argument("--minimum-slice-episode-count", type=int, default=DEFAULT_MINIMUM_SLICE_EPISODE_COUNT)
    parser.add_argument("--offtrack-target-threshold", type=float, default=DEFAULT_OFFTRACK_TARGET_THRESHOLD)
    parser.add_argument("--high-priority-offtrack-threshold", type=float, default=DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD)
    parser.add_argument("--collision-guardrail-threshold", type=float, default=DEFAULT_COLLISION_GUARDRAIL_THRESHOLD)
    parser.add_argument("--speed-too-low-threshold", type=float, default=DEFAULT_SPEED_TOO_LOW_THRESHOLD)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_measured_outcome_localization(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        target_family_membership_row_count=int(args.target_family_membership_row_count),
        minimum_slice_episode_count=int(args.minimum_slice_episode_count),
        offtrack_target_threshold=float(args.offtrack_target_threshold),
        high_priority_offtrack_threshold=float(args.high_priority_offtrack_threshold),
        collision_guardrail_threshold=float(args.collision_guardrail_threshold),
        speed_too_low_threshold=float(args.speed_too_low_threshold),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_episode_count={summary['source_episode_count']}")
    print(f"source_family_membership_row_count={summary['source_family_membership_row_count']}")
    print(f"slice_row_count={summary['slice_row_count']}")
    print(f"offtrack_target_slice_count={summary['offtrack_target_slice_count']}")
    print(f"collision_guardrail_slice_count={summary['collision_guardrail_slice_count']}")
    print(f"r4_mitigation_semantics_slice_count={summary['r4_mitigation_semantics_slice_count']}")
    print(f"max_step_noncompletion_slice_count={summary['max_step_noncompletion_slice_count']}")
    print(f"speed_too_low_slice_count={summary['speed_too_low_slice_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
