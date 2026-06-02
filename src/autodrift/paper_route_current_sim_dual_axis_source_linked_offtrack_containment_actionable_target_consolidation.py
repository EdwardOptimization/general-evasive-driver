"""Artifact-only consolidation for M2415 source-linked localization."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_actionable_target_consolidation as base_consolidation
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path(
    "runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2417_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation"
)
DEFAULT_TARGET_SLICE_ROW_COUNT = 2844
DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT = 30
DEFAULT_NEXT_BLOCKER = (
    "m2418-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_incomplete_or_fail"

DIAGNOSTIC_AXES = {
    "global",
    "family_id",
    "family_id+hidden_dynamics_bucket",
    "family_id+pack_id",
    "family_id+profile_name",
    "family_id+role_family",
    "family_id+sampled_obstacle_label",
    "pack_id",
    "pack_id+profile_name+role_family",
    "profile_name",
    "profile_name+role_family",
    "reset_target_key",
    "reset_target_key+profile_name",
    "reset_target_key+role_family",
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
    "outcome_bucket": "outcome_failure_surface",
}
EXTRA_FIELDNAMES = [
    "source_table",
    "source_linked_target_consolidation",
    "source_priority_score",
    "max_step_noncompletion_rate",
    "speed_too_low_rate",
    "is_max_step_target",
    "is_speed_too_low_target",
    "max_step_guardrail_required",
    "speed_too_low_guardrail_required",
    "candidate_family_ranking_claim_made",
    "support_policy_ranking_claim_made",
    "current_sim_verdict_claim_made",
    "training_repair_success_claim_made",
]
CONSOLIDATED_FIELDNAMES = [*base_consolidation.CONSOLIDATED_FIELDNAMES, *EXTRA_FIELDNAMES]
CLAIM_FIELDNAMES = base_consolidation.CLAIM_FIELDNAMES


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return base_consolidation.read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_consolidation._bool(value, default=default)


def _int(value: Any, *, default: int = 0) -> int:
    return base_consolidation._int(value, default=default)


def _float(value: Any, *, default: float = 0.0) -> float:
    return base_consolidation._float(value, default=default)


def _source_axis(row: Mapping[str, Any]) -> str:
    return str(row.get("slice_axis", ""))


def _source_table(row: Mapping[str, Any]) -> str:
    return str(row.get("source_table", ""))


def _is_family_axis(row: Mapping[str, Any]) -> bool:
    axis = _source_axis(row)
    return axis == "family_id" or axis.startswith("family_id+")


def _is_source_family_membership_row(row: Mapping[str, Any]) -> bool:
    return _source_table(row) == "episode_family_membership_rows" or _is_family_axis(row)


def _actionability_class(row: Mapping[str, Any], *, route: str) -> str:
    axis = _source_axis(row)
    if _is_source_family_membership_row(row):
        return "source_linked_family_membership_diagnostic"
    if route == "r4_mitigation_semantics":
        return "r4_mitigation_semantics"
    if route == "max_step_noncompletion_target":
        return "max_step_noncompletion"
    if route == "speed_too_low_target":
        return "speed_too_low"
    if axis in DIAGNOSTIC_AXES:
        return "diagnostic_guardrail"
    return ACTIONABILITY_CLASS_BY_AXIS.get(axis, "diagnostic_only")


def _consolidated_route(row: Mapping[str, Any], *, minimum_actionable_episode_count: int) -> str:
    axis = _source_axis(row)
    total = _int(row.get("episode_count"))
    enough_support = total >= int(minimum_actionable_episode_count)
    is_r4 = _bool(row.get("is_r4_mitigation_semantics"))
    is_offtrack = _bool(row.get("is_offtrack_target"))
    is_collision = _bool(row.get("is_collision_guardrail"))
    is_max_step = _bool(row.get("is_max_step_target"))
    is_speed_too_low = _bool(row.get("is_speed_too_low_target"))
    if _is_source_family_membership_row(row):
        return "source_linked_family_diagnostic_guardrail"
    if is_r4:
        return "r4_mitigation_semantics"
    if axis in DIAGNOSTIC_AXES:
        return "diagnostic_guardrail"
    if not enough_support:
        return "diagnostic_only"
    if is_max_step and not is_offtrack and not is_collision:
        return "max_step_noncompletion_target"
    if is_speed_too_low and not is_offtrack and not is_collision:
        return "speed_too_low_target"
    if is_offtrack and is_collision:
        return "offtrack_repair_target_with_collision_guardrail"
    if is_offtrack:
        return "offtrack_repair_target"
    if is_collision:
        return "collision_guardrail"
    return "diagnostic_only"


def consolidate_slice_row(row: Mapping[str, Any], *, minimum_actionable_episode_count: int) -> dict[str, Any]:
    route = _consolidated_route(row, minimum_actionable_episode_count=minimum_actionable_episode_count)
    repair_target = route in {"offtrack_repair_target", "offtrack_repair_target_with_collision_guardrail"}
    collision_guardrail = route in {"offtrack_repair_target_with_collision_guardrail", "collision_guardrail"}
    r4 = route == "r4_mitigation_semantics"
    max_step = route == "max_step_noncompletion_target"
    speed_too_low = route == "speed_too_low_target"
    diagnostic = route in {
        "diagnostic_guardrail",
        "diagnostic_only",
        "source_linked_family_diagnostic_guardrail",
    }
    return {
        "slice_axis": _source_axis(row),
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
        "actionability_class": _actionability_class(row, route=route),
        "repair_target_admissible": repair_target,
        "collision_guardrail_required": collision_guardrail,
        "r4_mitigation_semantics": r4,
        "diagnostic_only": diagnostic,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "source_table": _source_table(row),
        "source_linked_target_consolidation": True,
        "source_priority_score": _float(row.get("priority_score")),
        "max_step_noncompletion_rate": _float(row.get("max_step_noncompletion_rate")),
        "speed_too_low_rate": _float(row.get("speed_too_low_rate")),
        "is_max_step_target": _bool(row.get("is_max_step_target")),
        "is_speed_too_low_target": _bool(row.get("is_speed_too_low_target")),
        "max_step_guardrail_required": max_step,
        "speed_too_low_guardrail_required": speed_too_low,
        "candidate_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "training_repair_success_claim_made": False,
    }


def consolidate_slice_rows(
    rows: Sequence[Mapping[str, Any]], *, minimum_actionable_episode_count: int
) -> list[dict[str, Any]]:
    consolidated = [
        consolidate_slice_row(row, minimum_actionable_episode_count=minimum_actionable_episode_count) for row in rows
    ]
    return sorted(
        consolidated,
        key=lambda row: (
            row["consolidated_route"],
            -float(row["episode_count"]),
            row["source_table"],
            row["slice_axis"],
            row["slice_value"],
        ),
    )


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_source_linked_actionable_target_consolidation",
            "admissible": True,
            "reason": "M2417 may claim only target and guardrail artifact materialization from M2415 slices",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "source-linked family slices are overlapping diagnostics, not rankings",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "profile slices are diagnostic and do not rank support policies",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "consolidation rows do not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2417 does not select or promote a winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2417 is artifact consolidation, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2417 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2417 does not run history interventions",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2417 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2417 does not train, repair, replay, or run PPO",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2417 consolidates one localization artifact and does not make a current-sim verdict",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _write_rows(
    *,
    output: Path,
    consolidated_rows: Sequence[Mapping[str, Any]],
    offtrack_rows: Sequence[Mapping[str, Any]],
    collision_rows: Sequence[Mapping[str, Any]],
    r4_rows: Sequence[Mapping[str, Any]],
    max_step_rows: Sequence[Mapping[str, Any]],
    speed_too_low_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    family_diagnostic_rows: Sequence[Mapping[str, Any]],
) -> None:
    write_csv_rows(output / "consolidated_rows.csv", list(consolidated_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "offtrack_repair_target_rows.csv", list(offtrack_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_rows.csv", list(collision_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_semantics_rows.csv", list(r4_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "max_step_noncompletion_rows.csv", list(max_step_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "speed_too_low_rows.csv", list(speed_too_low_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "diagnostic_guardrail_rows.csv", list(diagnostic_rows), fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(
        output / "family_membership_diagnostic_rows.csv",
        list(family_diagnostic_rows),
        fieldnames=CONSOLIDATED_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)


def run_source_linked_actionable_target_consolidation(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_slice_row_count: int = DEFAULT_TARGET_SLICE_ROW_COUNT,
    minimum_actionable_episode_count: int = DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary_path = source / "summary.json"
    slice_rows_path = source / "slice_rows.csv"
    source_summary = read_json(summary_path)
    source_rows = read_csv_rows(slice_rows_path)
    consolidated_rows = consolidate_slice_rows(
        source_rows,
        minimum_actionable_episode_count=minimum_actionable_episode_count,
    )
    offtrack_rows = [row for row in consolidated_rows if _bool(row.get("repair_target_admissible"))]
    collision_rows = [row for row in consolidated_rows if _bool(row.get("collision_guardrail_required"))]
    r4_rows = [row for row in consolidated_rows if _bool(row.get("r4_mitigation_semantics"))]
    max_step_rows = [row for row in consolidated_rows if _bool(row.get("max_step_guardrail_required"))]
    speed_too_low_rows = [row for row in consolidated_rows if _bool(row.get("speed_too_low_guardrail_required"))]
    diagnostic_rows = [row for row in consolidated_rows if _bool(row.get("diagnostic_only"))]
    family_diagnostic_rows = [
        row
        for row in consolidated_rows
        if str(row.get("consolidated_route", "")) == "source_linked_family_diagnostic_guardrail"
    ]

    diagnostic_axis_repair_target_count = sum(
        1 for row in consolidated_rows if str(row.get("slice_axis")) in DIAGNOSTIC_AXES and _bool(row.get("repair_target_admissible"))
    )
    family_axis_repair_target_count = sum(
        1
        for row in consolidated_rows
        if (
            str(row.get("source_table", "")) == "episode_family_membership_rows"
            or str(row.get("slice_axis", "")).startswith("family_id")
        )
        and _bool(row.get("repair_target_admissible"))
    )
    profile_axis_repair_target_count = sum(
        1 for row in consolidated_rows if "profile_name" in str(row.get("slice_axis", "")) and _bool(row.get("repair_target_admissible"))
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
    ranking_admissible_count = _flag_count(consolidated_rows, "ranking_admissible")
    winner_selected_count = _flag_count(consolidated_rows, "winner_selected")
    source_slice_row_count = len(source_rows)
    passes = (
        source_slice_row_count == int(target_slice_row_count)
        and str(source_summary.get("result_class", "")).endswith("_pass")
        and len(consolidated_rows) > 0
        and len(offtrack_rows) > 0
        and len(collision_rows) > 0
        and len(r4_rows) > 0
        and len(max_step_rows) > 0
        and len(speed_too_low_rows) > 0
        and len(diagnostic_rows) > 0
        and len(family_diagnostic_rows) > 0
        and diagnostic_axis_repair_target_count == 0
        and family_axis_repair_target_count == 0
        and profile_axis_repair_target_count == 0
        and r4_ordinary_repair_target_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    _write_rows(
        output=output,
        consolidated_rows=consolidated_rows,
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        r4_rows=r4_rows,
        max_step_rows=max_step_rows,
        speed_too_low_rows=speed_too_low_rows,
        diagnostic_rows=diagnostic_rows,
        family_diagnostic_rows=family_diagnostic_rows,
    )

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_dir": str(source),
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
        "max_step_noncompletion_row_count": len(max_step_rows),
        "speed_too_low_row_count": len(speed_too_low_rows),
        "diagnostic_guardrail_row_count": len(diagnostic_rows),
        "family_membership_diagnostic_row_count": len(family_diagnostic_rows),
        "diagnostic_axis_repair_target_count": diagnostic_axis_repair_target_count,
        "family_axis_repair_target_count": family_axis_repair_target_count,
        "profile_axis_repair_target_count": profile_axis_repair_target_count,
        "r4_ordinary_repair_target_count": r4_ordinary_repair_target_count,
        "consolidated_route_counts": _count_by(consolidated_rows, "consolidated_route"),
        "actionability_class_counts": _count_by(consolidated_rows, "actionability_class"),
        "source_table_counts": _count_by(consolidated_rows, "source_table"),
        "top_offtrack_repair_targets": offtrack_rows[:10],
        "top_collision_guardrails": collision_rows[:10],
        "top_r4_mitigation_semantics": r4_rows[:10],
        "top_max_step_noncompletion_targets": max_step_rows[:10],
        "top_speed_too_low_targets": speed_too_low_rows[:10],
        "top_family_membership_diagnostics": family_diagnostic_rows[:10],
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
            "consolidated_rows": str(output / "consolidated_rows.csv"),
            "offtrack_repair_target_rows": str(output / "offtrack_repair_target_rows.csv"),
            "collision_guardrail_rows": str(output / "collision_guardrail_rows.csv"),
            "r4_mitigation_semantics_rows": str(output / "r4_mitigation_semantics_rows.csv"),
            "max_step_noncompletion_rows": str(output / "max_step_noncompletion_rows.csv"),
            "speed_too_low_rows": str(output / "speed_too_low_rows.csv"),
            "diagnostic_guardrail_rows": str(output / "diagnostic_guardrail_rows.csv"),
            "family_membership_diagnostic_rows": str(output / "family_membership_diagnostic_rows.csv"),
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
    parser.add_argument("--target-slice-row-count", type=int, default=DEFAULT_TARGET_SLICE_ROW_COUNT)
    parser.add_argument("--minimum-actionable-episode-count", type=int, default=DEFAULT_MINIMUM_ACTIONABLE_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_actionable_target_consolidation(
        source_dir=args.source_dir,
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
    print(f"max_step_noncompletion_row_count={summary['max_step_noncompletion_row_count']}")
    print(f"speed_too_low_row_count={summary['speed_too_low_row_count']}")
    print(f"diagnostic_axis_repair_target_count={summary['diagnostic_axis_repair_target_count']}")
    print(f"family_axis_repair_target_count={summary['family_axis_repair_target_count']}")
    print(f"profile_axis_repair_target_count={summary['profile_axis_repair_target_count']}")
    print(f"r4_ordinary_repair_target_count={summary['r4_ordinary_repair_target_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
