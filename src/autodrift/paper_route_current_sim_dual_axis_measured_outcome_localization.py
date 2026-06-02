"""Artifact-only outcome localization for the dual-axis measured panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json")
DEFAULT_EPISODE_ROWS = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization")
DEFAULT_TARGET_EPISODE_COUNT = 5400
DEFAULT_MINIMUM_SLICE_EPISODE_COUNT = 30
DEFAULT_OFFTRACK_TARGET_THRESHOLD = 0.70
DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD = 0.85
DEFAULT_COLLISION_GUARDRAIL_THRESHOLD = 0.15
RESULT_PASS = "current_sim_dual_axis_measured_outcome_localization_pass"
RESULT_FAIL = "current_sim_dual_axis_measured_outcome_localization_incomplete_or_fail"
DEFAULT_NEXT_BLOCKER = "m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit"

SINGLE_AXES = (
    ("global", ("global",)),
    ("pack_id", ("pack_id",)),
    ("profile_name", ("profile_name",)),
    ("role_family", ("role_family",)),
    ("scenario_family_id", ("scenario_family_id",)),
    ("sampled_obstacle_label", ("sampled_obstacle_label",)),
    ("hidden_dynamics_bucket", ("hidden_dynamics_bucket",)),
    ("obstacle_longitudinal_timing_bucket", ("obstacle_longitudinal_timing_bucket",)),
    ("obstacle_lateral_offset_bucket", ("obstacle_lateral_offset_bucket",)),
    ("sampling_repair_class", ("sampling_repair_class",)),
)
COMPOSITE_AXES = (
    ("pack_id+role_family", ("pack_id", "role_family")),
    ("profile_name+role_family", ("profile_name", "role_family")),
    ("role_family+hidden_dynamics_bucket", ("role_family", "hidden_dynamics_bucket")),
    ("role_family+obstacle_longitudinal_timing_bucket", ("role_family", "obstacle_longitudinal_timing_bucket")),
    ("role_family+obstacle_lateral_offset_bucket", ("role_family", "obstacle_lateral_offset_bucket")),
    ("pack_id+profile_name+role_family", ("pack_id", "profile_name", "role_family")),
)
SLICE_FIELDNAMES = [
    "slice_axis",
    "slice_key",
    "slice_value",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_failure_count",
    "other_failure_rate",
    "dominant_failure_mode",
    "is_offtrack_target",
    "is_collision_guardrail",
    "is_r4_mitigation_semantics",
    "is_high_priority_offtrack",
    "route_class",
    "priority_score",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success")) or str(row.get("outcome_bucket", "")) == "success_obstacle_pass"


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision")) or str(row.get("outcome_bucket", "")) == "collision_failure"


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion"
        or str(row.get("termination_reason", "")) == "off_track"
    )


def _is_max_step(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "max_steps_noncompletion" or _bool(row.get("truncated"))


def _counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        if _is_success(row):
            counts["success"] += 1
        elif _is_collision(row):
            counts["collision"] += 1
        elif _is_offtrack(row):
            counts["offtrack"] += 1
        elif _is_max_step(row):
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
    return dict(counts)


def _dominant_failure_mode(counts: Mapping[str, int], total: int) -> str:
    if total <= 0:
        return "low_support_or_incomplete"
    success = int(counts.get("success", 0))
    if _rate(success, total) >= 2.0 / 3.0:
        return "success_supported"
    failures = max(1, total - success)
    buckets = (
        ("offtrack_dominated_failure", int(counts.get("offtrack", 0))),
        ("collision_dominated_failure", int(counts.get("collision", 0))),
        ("max_step_noncompletion_dominated_failure", int(counts.get("max_step_noncompletion", 0))),
    )
    for label, count in buckets:
        if count / failures >= 0.5:
            return label
    return "mixed_failure"


def _slice_value(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    if keys == ("global",):
        return "all"
    return "|".join(str(row.get(key, "")) for key in keys)


def _group_rows(rows: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> dict[str, list[Mapping[str, Any]]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_slice_value(row, keys)].append(row)
    return dict(groups)


def _route_class(*, is_offtrack_target: bool, is_collision_guardrail: bool, is_r4: bool) -> str:
    if is_r4:
        return "r4_mitigation_semantics"
    if is_offtrack_target and is_collision_guardrail:
        return "offtrack_target_with_collision_guardrail"
    if is_offtrack_target:
        return "offtrack_target"
    if is_collision_guardrail:
        return "collision_guardrail"
    return "diagnostic_only"


def _priority_score(
    *,
    counts: Mapping[str, int],
    total: int,
    offtrack_rate: float,
    is_offtrack_target: bool,
    is_collision_guardrail: bool,
    is_r4: bool,
    high_priority_offtrack_threshold: float,
) -> float:
    failure_mass = int(counts.get("offtrack", 0)) + int(counts.get("collision", 0))
    score = float(failure_mass)
    if is_offtrack_target:
        score += 1000.0
    if offtrack_rate >= float(high_priority_offtrack_threshold):
        score += 500.0
    if is_collision_guardrail:
        score += 250.0
    if is_r4:
        score += 125.0
    return score + float(total) / 1000.0


def slice_row(
    *,
    slice_axis: str,
    slice_key: str,
    slice_value: str,
    rows: Sequence[Mapping[str, Any]],
    minimum_slice_episode_count: int,
    offtrack_target_threshold: float,
    high_priority_offtrack_threshold: float,
    collision_guardrail_threshold: float,
) -> dict[str, Any]:
    total = len(rows)
    counts = _counts(rows)
    success_count = int(counts.get("success", 0))
    collision_count = int(counts.get("collision", 0))
    offtrack_count = int(counts.get("offtrack", 0))
    max_step_count = int(counts.get("max_step_noncompletion", 0))
    other_count = int(counts.get("other_failure", 0))
    success_rate = _rate(success_count, total)
    collision_rate = _rate(collision_count, total)
    offtrack_rate = _rate(offtrack_count, total)
    enough_support = total >= int(minimum_slice_episode_count)
    role_values = {str(row.get("role_family", "")) for row in rows}
    is_r4_semantics = enough_support and role_values == {"R4_unavoidable_mitigation"}
    is_offtrack_target = enough_support and not is_r4_semantics and offtrack_rate >= float(offtrack_target_threshold)
    is_collision_guardrail = (
        enough_support and not is_r4_semantics and collision_rate >= float(collision_guardrail_threshold)
    )
    is_high_priority_offtrack = is_offtrack_target and offtrack_rate >= float(high_priority_offtrack_threshold)
    route = _route_class(
        is_offtrack_target=is_offtrack_target,
        is_collision_guardrail=is_collision_guardrail,
        is_r4=is_r4_semantics,
    )
    return {
        "slice_axis": slice_axis,
        "slice_key": slice_key,
        "slice_value": slice_value,
        "episode_count": total,
        "success_count": success_count,
        "success_rate": success_rate,
        "collision_count": collision_count,
        "collision_rate": collision_rate,
        "offtrack_count": offtrack_count,
        "offtrack_rate": offtrack_rate,
        "max_step_noncompletion_count": max_step_count,
        "max_step_noncompletion_rate": _rate(max_step_count, total),
        "other_failure_count": other_count,
        "other_failure_rate": _rate(other_count, total),
        "dominant_failure_mode": _dominant_failure_mode(counts, total),
        "is_offtrack_target": bool(is_offtrack_target),
        "is_collision_guardrail": bool(is_collision_guardrail),
        "is_r4_mitigation_semantics": bool(is_r4_semantics),
        "is_high_priority_offtrack": bool(is_high_priority_offtrack),
        "route_class": route,
        "priority_score": _priority_score(
            counts=counts,
            total=total,
            offtrack_rate=offtrack_rate,
            is_offtrack_target=is_offtrack_target,
            is_collision_guardrail=is_collision_guardrail,
            is_r4=is_r4_semantics,
            high_priority_offtrack_threshold=high_priority_offtrack_threshold,
        ),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def build_slice_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_slice_episode_count: int,
    offtrack_target_threshold: float,
    high_priority_offtrack_threshold: float,
    collision_guardrail_threshold: float,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for axis, keys in (*SINGLE_AXES, *COMPOSITE_AXES):
        groups = _group_rows(rows, keys)
        for value, group in sorted(groups.items()):
            output.append(
                slice_row(
                    slice_axis=axis,
                    slice_key="+".join(keys),
                    slice_value=value,
                    rows=group,
                    minimum_slice_episode_count=minimum_slice_episode_count,
                    offtrack_target_threshold=offtrack_target_threshold,
                    high_priority_offtrack_threshold=high_priority_offtrack_threshold,
                    collision_guardrail_threshold=collision_guardrail_threshold,
                )
            )
    return sorted(output, key=lambda row: float(row["priority_score"]), reverse=True)


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_outcome_localization",
            "admissible": True,
            "reason": "M2365 may claim only target and guardrail slice materialization from existing artifacts",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "slice rows are diagnostic and do not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2365 does not select or promote a winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2365 is artifact localization, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2365 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2365 does not run history interventions",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2365 localizes existing measured outcomes and does not redesign scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2365 does not train, repair, replay, or run PPO",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_measured_outcome_localization(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = DEFAULT_TARGET_EPISODE_COUNT,
    minimum_slice_episode_count: int = DEFAULT_MINIMUM_SLICE_EPISODE_COUNT,
    offtrack_target_threshold: float = DEFAULT_OFFTRACK_TARGET_THRESHOLD,
    high_priority_offtrack_threshold: float = DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD,
    collision_guardrail_threshold: float = DEFAULT_COLLISION_GUARDRAIL_THRESHOLD,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    episode_rows = read_csv_rows(episode_rows_path)
    slice_rows = build_slice_rows(
        episode_rows,
        minimum_slice_episode_count=minimum_slice_episode_count,
        offtrack_target_threshold=offtrack_target_threshold,
        high_priority_offtrack_threshold=high_priority_offtrack_threshold,
        collision_guardrail_threshold=collision_guardrail_threshold,
    )
    offtrack_rows = [row for row in slice_rows if _bool(row.get("is_offtrack_target"))]
    collision_rows = [row for row in slice_rows if _bool(row.get("is_collision_guardrail"))]
    r4_rows = [row for row in slice_rows if _bool(row.get("is_r4_mitigation_semantics"))]
    high_priority_offtrack_rows = [row for row in slice_rows if _bool(row.get("is_high_priority_offtrack"))]
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
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    ranking_admissible_count = _flag_count(slice_rows, "ranking_admissible")
    winner_selected_count = _flag_count(slice_rows, "winner_selected")
    source_episode_count = len(episode_rows)
    passes = (
        source_episode_count == int(target_episode_count)
        and len(slice_rows) > 0
        and len(offtrack_rows) > 0
        and len(r4_rows) > 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "slice_rows.csv", slice_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "offtrack_target_slice_rows.csv", offtrack_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_slice_rows.csv", collision_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_semantics_rows.csv", r4_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_episode_rows": str(episode_rows_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_episode_count": source_episode_count,
        "target_episode_count": int(target_episode_count),
        "slice_row_count": len(slice_rows),
        "offtrack_target_slice_count": len(offtrack_rows),
        "collision_guardrail_slice_count": len(collision_rows),
        "r4_mitigation_semantics_slice_count": len(r4_rows),
        "high_priority_offtrack_slice_count": len(high_priority_offtrack_rows),
        "minimum_slice_episode_count": int(minimum_slice_episode_count),
        "offtrack_target_threshold": float(offtrack_target_threshold),
        "high_priority_offtrack_threshold": float(high_priority_offtrack_threshold),
        "collision_guardrail_threshold": float(collision_guardrail_threshold),
        "route_class_counts": _count_by(slice_rows, "route_class"),
        "top_offtrack_target_slices": offtrack_rows[:10],
        "top_collision_guardrail_slices": collision_rows[:10],
        "top_r4_mitigation_semantics_slices": r4_rows[:10],
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
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "slice_rows": str(output / "slice_rows.csv"),
            "offtrack_target_slice_rows": str(output / "offtrack_target_slice_rows.csv"),
            "collision_guardrail_slice_rows": str(output / "collision_guardrail_slice_rows.csv"),
            "r4_mitigation_semantics_rows": str(output / "r4_mitigation_semantics_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=DEFAULT_TARGET_EPISODE_COUNT)
    parser.add_argument("--minimum-slice-episode-count", type=int, default=DEFAULT_MINIMUM_SLICE_EPISODE_COUNT)
    parser.add_argument("--offtrack-target-threshold", type=float, default=DEFAULT_OFFTRACK_TARGET_THRESHOLD)
    parser.add_argument("--high-priority-offtrack-threshold", type=float, default=DEFAULT_HIGH_PRIORITY_OFFTRACK_THRESHOLD)
    parser.add_argument("--collision-guardrail-threshold", type=float, default=DEFAULT_COLLISION_GUARDRAIL_THRESHOLD)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_measured_outcome_localization(
        summary_path=args.summary,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        minimum_slice_episode_count=int(args.minimum_slice_episode_count),
        offtrack_target_threshold=float(args.offtrack_target_threshold),
        high_priority_offtrack_threshold=float(args.high_priority_offtrack_threshold),
        collision_guardrail_threshold=float(args.collision_guardrail_threshold),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_episode_count={summary['source_episode_count']}")
    print(f"slice_row_count={summary['slice_row_count']}")
    print(f"offtrack_target_slice_count={summary['offtrack_target_slice_count']}")
    print(f"collision_guardrail_slice_count={summary['collision_guardrail_slice_count']}")
    print(f"r4_mitigation_semantics_slice_count={summary['r4_mitigation_semantics_slice_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
