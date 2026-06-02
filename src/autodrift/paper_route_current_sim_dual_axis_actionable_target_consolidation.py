"""Artifact-only actionable target consolidation for the dual-axis panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json")
DEFAULT_SLICE_ROWS = Path("runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation")
DEFAULT_TARGET_SLICE_ROW_COUNT = 313
DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT = 30
RESULT_PASS = "current_sim_dual_axis_actionable_target_consolidation_pass"
RESULT_FAIL = "current_sim_dual_axis_actionable_target_consolidation_incomplete_or_fail"
DEFAULT_NEXT_BLOCKER = "m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit"

DIAGNOSTIC_AXES = {
    "global",
    "pack_id",
    "profile_name",
    "sampling_repair_class",
    "pack_id+role_family",
    "profile_name+role_family",
    "pack_id+profile_name+role_family",
}
ACTIONABILITY_CLASS_BY_AXIS = {
    "role_family": "role_semantics",
    "scenario_family_id": "role_semantics",
    "sampled_obstacle_label": "role_semantics",
    "hidden_dynamics_bucket": "hidden_dynamics",
    "obstacle_longitudinal_timing_bucket": "geometry_timing",
    "obstacle_lateral_offset_bucket": "geometry_timing",
    "role_family+hidden_dynamics_bucket": "role_conditioned_hidden_dynamics",
    "role_family+obstacle_longitudinal_timing_bucket": "role_conditioned_geometry_timing",
    "role_family+obstacle_lateral_offset_bucket": "role_conditioned_geometry_timing",
}
CONSOLIDATED_FIELDNAMES = [
    "slice_axis",
    "slice_key",
    "slice_value",
    "episode_count",
    "success_rate",
    "offtrack_rate",
    "collision_rate",
    "dominant_failure_mode",
    "is_high_priority_offtrack",
    "source_route_class",
    "consolidated_route",
    "actionability_class",
    "repair_target_admissible",
    "collision_guardrail_required",
    "r4_mitigation_semantics",
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


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _source_axis(row: Mapping[str, Any]) -> str:
    return str(row.get("slice_axis", ""))


def _actionability_class(row: Mapping[str, Any], *, is_r4: bool) -> str:
    axis = _source_axis(row)
    if is_r4:
        return "r4_mitigation_semantics"
    if axis in DIAGNOSTIC_AXES:
        return "diagnostic_guardrail"
    return ACTIONABILITY_CLASS_BY_AXIS.get(axis, "diagnostic_only")


def _consolidated_route(
    row: Mapping[str, Any],
    *,
    minimum_actionable_episode_count: int,
) -> str:
    axis = _source_axis(row)
    total = _int(row.get("episode_count"))
    enough_support = total >= int(minimum_actionable_episode_count)
    is_r4 = _bool(row.get("is_r4_mitigation_semantics"))
    is_offtrack = _bool(row.get("is_offtrack_target"))
    is_collision = _bool(row.get("is_collision_guardrail"))
    if is_r4:
        return "r4_mitigation_semantics"
    if axis in DIAGNOSTIC_AXES:
        return "diagnostic_guardrail"
    if not enough_support:
        return "diagnostic_only"
    if is_offtrack and is_collision:
        return "offtrack_repair_target_with_collision_guardrail"
    if is_offtrack:
        return "offtrack_repair_target"
    if is_collision:
        return "collision_guardrail"
    return "diagnostic_only"


def consolidate_slice_row(
    row: Mapping[str, Any],
    *,
    minimum_actionable_episode_count: int,
) -> dict[str, Any]:
    route = _consolidated_route(row, minimum_actionable_episode_count=minimum_actionable_episode_count)
    is_r4 = route == "r4_mitigation_semantics"
    repair_target = route in {"offtrack_repair_target", "offtrack_repair_target_with_collision_guardrail"}
    collision_guardrail = route in {"offtrack_repair_target_with_collision_guardrail", "collision_guardrail"}
    return {
        "slice_axis": str(row.get("slice_axis", "")),
        "slice_key": str(row.get("slice_key", "")),
        "slice_value": str(row.get("slice_value", "")),
        "episode_count": _int(row.get("episode_count")),
        "success_rate": _float(row.get("success_rate")),
        "offtrack_rate": _float(row.get("offtrack_rate")),
        "collision_rate": _float(row.get("collision_rate")),
        "dominant_failure_mode": str(row.get("dominant_failure_mode", "")),
        "is_high_priority_offtrack": _bool(row.get("is_high_priority_offtrack")),
        "source_route_class": str(row.get("route_class", "")),
        "consolidated_route": route,
        "actionability_class": _actionability_class(row, is_r4=is_r4),
        "repair_target_admissible": repair_target,
        "collision_guardrail_required": collision_guardrail,
        "r4_mitigation_semantics": is_r4,
        "diagnostic_only": route in {"diagnostic_guardrail", "diagnostic_only"},
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def consolidate_slice_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_actionable_episode_count: int,
) -> list[dict[str, Any]]:
    consolidated = [
        consolidate_slice_row(row, minimum_actionable_episode_count=minimum_actionable_episode_count) for row in rows
    ]
    return sorted(
        consolidated,
        key=lambda row: (
            row["consolidated_route"],
            -float(row["episode_count"]),
            row["slice_axis"],
            row["slice_value"],
        ),
    )


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_actionable_target_consolidation",
            "admissible": True,
            "reason": "M2368 may claim only target and guardrail artifact materialization from existing slices",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "consolidation rows do not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2368 does not select or promote a winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2368 is artifact consolidation, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2368 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2368 does not run history interventions",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2368 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2368 does not train, repair, replay, or run PPO",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_actionable_target_consolidation(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    slice_rows_path: Path | str = DEFAULT_SLICE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_slice_row_count: int = DEFAULT_TARGET_SLICE_ROW_COUNT,
    minimum_actionable_episode_count: int = DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    source_rows = read_csv_rows(slice_rows_path)
    consolidated_rows = consolidate_slice_rows(
        source_rows,
        minimum_actionable_episode_count=minimum_actionable_episode_count,
    )
    offtrack_rows = [row for row in consolidated_rows if _bool(row.get("repair_target_admissible"))]
    collision_rows = [row for row in consolidated_rows if _bool(row.get("collision_guardrail_required"))]
    r4_rows = [row for row in consolidated_rows if _bool(row.get("r4_mitigation_semantics"))]
    diagnostic_rows = [row for row in consolidated_rows if str(row.get("consolidated_route")) == "diagnostic_guardrail"]

    diagnostic_axis_repair_target_count = sum(
        1 for row in consolidated_rows if str(row.get("slice_axis")) in DIAGNOSTIC_AXES and _bool(row.get("repair_target_admissible"))
    )
    r4_ordinary_repair_target_count = sum(
        1
        for row in consolidated_rows
        if _bool(row.get("r4_mitigation_semantics")) and _bool(row.get("repair_target_admissible"))
    )
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
        "training_repair_success_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    ranking_admissible_count = _flag_count(consolidated_rows, "ranking_admissible")
    winner_selected_count = _flag_count(consolidated_rows, "winner_selected")
    source_slice_row_count = len(source_rows)
    passes = (
        source_slice_row_count == int(target_slice_row_count)
        and len(consolidated_rows) > 0
        and len(offtrack_rows) > 0
        and len(collision_rows) > 0
        and len(r4_rows) > 0
        and len(diagnostic_rows) > 0
        and diagnostic_axis_repair_target_count == 0
        and r4_ordinary_repair_target_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "consolidated_rows.csv", consolidated_rows, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "offtrack_repair_target_rows.csv", offtrack_rows, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_rows.csv", collision_rows, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_semantics_rows.csv", r4_rows, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "diagnostic_guardrail_rows.csv", diagnostic_rows, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_slice_rows": str(slice_rows_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_slice_row_count": source_slice_row_count,
        "target_slice_row_count": int(target_slice_row_count),
        "minimum_actionable_episode_count": int(minimum_actionable_episode_count),
        "consolidated_row_count": len(consolidated_rows),
        "offtrack_repair_target_row_count": len(offtrack_rows),
        "collision_guardrail_row_count": len(collision_rows),
        "r4_mitigation_semantics_row_count": len(r4_rows),
        "diagnostic_guardrail_row_count": len(diagnostic_rows),
        "diagnostic_axis_repair_target_count": diagnostic_axis_repair_target_count,
        "r4_ordinary_repair_target_count": r4_ordinary_repair_target_count,
        "consolidated_route_counts": _count_by(consolidated_rows, "consolidated_route"),
        "actionability_class_counts": _count_by(consolidated_rows, "actionability_class"),
        "top_offtrack_repair_targets": offtrack_rows[:10],
        "top_collision_guardrails": collision_rows[:10],
        "top_r4_mitigation_semantics": r4_rows[:10],
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
        "training_repair_success_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "consolidated_rows": str(output / "consolidated_rows.csv"),
            "offtrack_repair_target_rows": str(output / "offtrack_repair_target_rows.csv"),
            "collision_guardrail_rows": str(output / "collision_guardrail_rows.csv"),
            "r4_mitigation_semantics_rows": str(output / "r4_mitigation_semantics_rows.csv"),
            "diagnostic_guardrail_rows": str(output / "diagnostic_guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--slice-rows", type=Path, default=DEFAULT_SLICE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-slice-row-count", type=int, default=DEFAULT_TARGET_SLICE_ROW_COUNT)
    parser.add_argument("--minimum-actionable-episode-count", type=int, default=DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_actionable_target_consolidation(
        summary_path=args.summary,
        slice_rows_path=args.slice_rows,
        output_dir=args.output_dir,
        target_slice_row_count=int(args.target_slice_row_count),
        minimum_actionable_episode_count=int(args.minimum_actionable_episode_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_slice_row_count={summary['source_slice_row_count']}")
    print(f"consolidated_row_count={summary['consolidated_row_count']}")
    print(f"offtrack_repair_target_row_count={summary['offtrack_repair_target_row_count']}")
    print(f"collision_guardrail_row_count={summary['collision_guardrail_row_count']}")
    print(f"r4_mitigation_semantics_row_count={summary['r4_mitigation_semantics_row_count']}")
    print(f"diagnostic_axis_repair_target_count={summary['diagnostic_axis_repair_target_count']}")
    print(f"r4_ordinary_repair_target_count={summary['r4_ordinary_repair_target_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
