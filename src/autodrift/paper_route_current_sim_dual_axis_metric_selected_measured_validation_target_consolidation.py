"""Artifact-only target consolidation for M2447 metric-selected localization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_LOCALIZATION_DIR = Path(
    "runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization"
)
DEFAULT_SOURCE_SUMMARY = DEFAULT_LOCALIZATION_DIR / "summary.json"
DEFAULT_LOCALIZATION_ROWS = DEFAULT_LOCALIZATION_DIR / "localization_rows.csv"
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation"
)
DEFAULT_TARGET_LOCALIZATION_ROW_COUNT = 65
DEFAULT_MINIMUM_TARGET_EPISODE_COUNT = 90
DEFAULT_MINIMUM_HARD_OFFTRACK_RATE = 0.5
DEFAULT_MINIMUM_COLLISION_GUARDRAIL_RATE = 0.1
DEFAULT_NEXT_BLOCKER = (
    "m2450-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_metric_selected_measured_validation_target_consolidation_pass"
RESULT_FAIL = "current_sim_dual_axis_metric_selected_measured_validation_target_consolidation_incomplete_or_fail"

HARD_OFFTRACK_TARGET_AXES = {
    "role_family",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "sampled_obstacle_label",
}
DIAGNOSTIC_ONLY_AXES = {
    "global",
    "profile_name",
    "profile_seed",
    "pack_id",
    "scenario_family_id",
    "termination_reason",
    "outcome_bucket",
}
ACTIONABILITY_CLASS_BY_AXIS = {
    "role_family": "role_semantics",
    "hidden_dynamics_bucket": "hidden_dynamics",
    "obstacle_longitudinal_timing_bucket": "geometry_timing",
    "obstacle_lateral_offset_bucket": "geometry_timing",
    "sampled_obstacle_label": "scenario_label",
}
ROW_FIELDNAMES = [
    "row_id",
    "row_class",
    "axis",
    "value",
    "episode_count",
    "actual_success_count",
    "actual_success_rate",
    "hard_offtrack_count",
    "hard_offtrack_rate",
    "soft_offtrack_violation_count",
    "soft_offtrack_violation_rate",
    "boundary_tolerated_success_count",
    "boundary_tolerated_success_rate",
    "collision_count",
    "collision_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_count",
    "other_rate",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_overshoot_m",
    "max_overshoot_m",
    "mean_steps",
    "diagnostic_pattern",
    "actionability_class",
    "repair_target_admissible",
    "collision_guardrail_required",
    "soft_boundary_diagnostic",
    "monitoring_only",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
]
DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]


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


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _is_hard_offtrack_target(
    row: Mapping[str, Any],
    *,
    minimum_episode_count: int,
    minimum_hard_offtrack_rate: float,
) -> bool:
    axis = str(row.get("axis", ""))
    if axis not in HARD_OFFTRACK_TARGET_AXES:
        return False
    if _int(row.get("episode_count")) < int(minimum_episode_count):
        return False
    if _float(row.get("hard_offtrack_rate")) < float(minimum_hard_offtrack_rate):
        return False
    return str(row.get("diagnostic_pattern", "")) == "hard_offtrack_dominated"


def _collision_guardrail_required(
    row: Mapping[str, Any],
    *,
    minimum_collision_guardrail_rate: float,
) -> bool:
    return _int(row.get("collision_count")) > 0 and (
        _float(row.get("collision_rate")) >= float(minimum_collision_guardrail_rate)
        or str(row.get("diagnostic_pattern", "")) == "collision_dominated"
    )


def _soft_boundary_diagnostic(row: Mapping[str, Any]) -> bool:
    return _int(row.get("soft_offtrack_violation_count")) > 0 or _int(
        row.get("boundary_tolerated_success_count")
    ) > 0


def _monitoring_only(row: Mapping[str, Any]) -> bool:
    return str(row.get("axis", "")) in DIAGNOSTIC_ONLY_AXES


def _actionability_class(row: Mapping[str, Any]) -> str:
    axis = str(row.get("axis", ""))
    if axis in DIAGNOSTIC_ONLY_AXES:
        return "diagnostic_monitoring"
    return ACTIONABILITY_CLASS_BY_AXIS.get(axis, "diagnostic_only")


def _copy_metric_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {
        "axis": str(row.get("axis", "")),
        "value": str(row.get("value", "")),
        "episode_count": _int(row.get("episode_count")),
        "actual_success_count": _int(row.get("actual_success_count")),
        "actual_success_rate": _float(row.get("actual_success_rate")),
        "hard_offtrack_count": _int(row.get("hard_offtrack_count")),
        "hard_offtrack_rate": _float(row.get("hard_offtrack_rate")),
        "soft_offtrack_violation_count": _int(row.get("soft_offtrack_violation_count")),
        "soft_offtrack_violation_rate": _float(row.get("soft_offtrack_violation_rate")),
        "boundary_tolerated_success_count": _int(row.get("boundary_tolerated_success_count")),
        "boundary_tolerated_success_rate": _float(row.get("boundary_tolerated_success_rate")),
        "collision_count": _int(row.get("collision_count")),
        "collision_rate": _float(row.get("collision_rate")),
        "max_step_noncompletion_count": _int(row.get("max_step_noncompletion_count")),
        "max_step_noncompletion_rate": _float(row.get("max_step_noncompletion_rate")),
        "other_count": _int(row.get("other_count")),
        "other_rate": _float(row.get("other_rate")),
        "mean_min_clearance_margin": _float(row.get("mean_min_clearance_margin")),
        "min_min_clearance_margin": _float(row.get("min_min_clearance_margin")),
        "mean_overshoot_m": _float(row.get("mean_overshoot_m")),
        "max_overshoot_m": _float(row.get("max_overshoot_m")),
        "mean_steps": _float(row.get("mean_steps")),
        "diagnostic_pattern": str(row.get("diagnostic_pattern", "")),
    }
    return copied


def consolidate_localization_row(
    row: Mapping[str, Any],
    *,
    index: int,
    minimum_episode_count: int,
    minimum_hard_offtrack_rate: float,
    minimum_collision_guardrail_rate: float,
) -> dict[str, Any]:
    target = _is_hard_offtrack_target(
        row,
        minimum_episode_count=minimum_episode_count,
        minimum_hard_offtrack_rate=minimum_hard_offtrack_rate,
    )
    collision_guardrail = _collision_guardrail_required(
        row,
        minimum_collision_guardrail_rate=minimum_collision_guardrail_rate,
    )
    soft_diagnostic = _soft_boundary_diagnostic(row)
    monitoring = _monitoring_only(row)
    if target:
        row_class = "hard_offtrack_target"
    elif collision_guardrail:
        row_class = "collision_guardrail"
    elif soft_diagnostic:
        row_class = "soft_boundary_diagnostic"
    else:
        row_class = "monitoring_diagnostic"

    consolidated = _copy_metric_fields(row)
    consolidated.update(
        {
            "row_id": f"m2449_{index:03d}",
            "row_class": row_class,
            "actionability_class": _actionability_class(row),
            "repair_target_admissible": bool(target),
            "collision_guardrail_required": bool(collision_guardrail),
            "soft_boundary_diagnostic": bool(soft_diagnostic),
            "monitoring_only": bool(monitoring),
            "diagnostic_only": not bool(target),
            "ranking_admissible": False,
            "winner_selected": False,
            "paper_level_claim_made": False,
            "finite_window_vs_gru_conclusion_made": False,
            "level3_self_id_claim_made": False,
            "training_repair_success_claim_made": False,
            "current_sim_verdict_claim_made": False,
        }
    )
    return consolidated


def consolidate_localization_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_episode_count: int,
    minimum_hard_offtrack_rate: float,
    minimum_collision_guardrail_rate: float,
) -> list[dict[str, Any]]:
    consolidated = [
        consolidate_localization_row(
            row,
            index=index,
            minimum_episode_count=minimum_episode_count,
            minimum_hard_offtrack_rate=minimum_hard_offtrack_rate,
            minimum_collision_guardrail_rate=minimum_collision_guardrail_rate,
        )
        for index, row in enumerate(rows)
    ]
    route_order = {
        "hard_offtrack_target": 0,
        "collision_guardrail": 1,
        "soft_boundary_diagnostic": 2,
        "monitoring_diagnostic": 3,
    }
    return sorted(
        consolidated,
        key=lambda row: (
            route_order.get(str(row.get("row_class")), 99),
            -float(row.get("hard_offtrack_count", 0.0)),
            -float(row.get("collision_count", 0.0)),
            str(row.get("axis", "")),
            str(row.get("value", "")),
        ),
    )


def decision_rows(next_blocker: str) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "artifact_only_target_consolidation",
            "decision_value": "true",
            "admissible": True,
            "reason": "M2449 reanalyzes M2447/M2445 artifacts only.",
        },
        {
            "decision_key": "hard_offtrack_targets_separated_from_guardrails",
            "decision_value": "true",
            "admissible": True,
            "reason": "Hard-offtrack targets are separate from collision, soft-boundary, and monitoring rows.",
        },
        {
            "decision_key": "diagnostic_axes_used_for_ranking",
            "decision_value": "false",
            "admissible": True,
            "reason": "Profile, pack, family, checkpoint, termination, outcome, and global axes remain diagnostic-only.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2449 executes no repair, training, ranking, or winner selection.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker,
            "admissible": True,
            "reason": "Audit target consolidation before synthesis, repair planning, or any verdict route.",
        },
    ]


def _guardrail_flags() -> dict[str, bool]:
    return {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
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
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }


def run_target_consolidation(
    *,
    source_summary_path: Path | str = DEFAULT_SOURCE_SUMMARY,
    localization_rows_path: Path | str = DEFAULT_LOCALIZATION_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_localization_row_count: int = DEFAULT_TARGET_LOCALIZATION_ROW_COUNT,
    minimum_target_episode_count: int = DEFAULT_MINIMUM_TARGET_EPISODE_COUNT,
    minimum_hard_offtrack_rate: float = DEFAULT_MINIMUM_HARD_OFFTRACK_RATE,
    minimum_collision_guardrail_rate: float = DEFAULT_MINIMUM_COLLISION_GUARDRAIL_RATE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source_summary_path)
    source_rows = read_csv_rows(localization_rows_path)
    consolidated_rows = consolidate_localization_rows(
        source_rows,
        minimum_episode_count=int(minimum_target_episode_count),
        minimum_hard_offtrack_rate=float(minimum_hard_offtrack_rate),
        minimum_collision_guardrail_rate=float(minimum_collision_guardrail_rate),
    )
    target_rows = [row for row in consolidated_rows if _bool(row.get("repair_target_admissible"))]
    guardrail_rows = [
        row
        for row in consolidated_rows
        if _bool(row.get("collision_guardrail_required")) or _bool(row.get("soft_boundary_diagnostic"))
    ]
    diagnostic_rows = [row for row in consolidated_rows if _bool(row.get("diagnostic_only"))]
    monitoring_rows = [row for row in consolidated_rows if _bool(row.get("monitoring_only"))]

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    diagnostic_axis_repair_target_count = sum(
        1 for row in consolidated_rows if str(row.get("axis")) in DIAGNOSTIC_ONLY_AXES and _bool(row.get("repair_target_admissible"))
    )
    ranking_admissible_count = _flag_count(consolidated_rows, "ranking_admissible")
    winner_selected_count = _flag_count(consolidated_rows, "winner_selected")
    source_result_class = str(source_summary.get("result_class", ""))
    passes = (
        source_result_class.endswith("_pass")
        and len(source_rows) == int(target_localization_row_count)
        and len(consolidated_rows) == len(source_rows)
        and len(target_rows) > 0
        and len(guardrail_rows) > 0
        and len(diagnostic_rows) > 0
        and len(monitoring_rows) > 0
        and diagnostic_axis_repair_target_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    decisions = decision_rows(str(next_blocker))

    write_csv_rows(output / "target_rows.csv", target_rows, fieldnames=ROW_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guardrail_rows, fieldnames=ROW_FIELDNAMES)
    write_csv_rows(output / "diagnostic_rows.csv", diagnostic_rows, fieldnames=ROW_FIELDNAMES)
    write_csv_rows(output / "consolidated_rows.csv", consolidated_rows, fieldnames=ROW_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    global_rows = [row for row in consolidated_rows if row.get("axis") == "global"]
    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(source_summary_path),
        "source_result_class": source_result_class,
        "source_localization_rows": str(localization_rows_path),
        "source_localization_row_count": len(source_rows),
        "target_localization_row_count": int(target_localization_row_count),
        "minimum_target_episode_count": int(minimum_target_episode_count),
        "minimum_hard_offtrack_rate": float(minimum_hard_offtrack_rate),
        "minimum_collision_guardrail_rate": float(minimum_collision_guardrail_rate),
        "consolidated_row_count": len(consolidated_rows),
        "hard_offtrack_target_row_count": len(target_rows),
        "guardrail_row_count": len(guardrail_rows),
        "collision_guardrail_row_count": sum(_bool(row.get("collision_guardrail_required")) for row in consolidated_rows),
        "soft_boundary_diagnostic_row_count": sum(_bool(row.get("soft_boundary_diagnostic")) for row in consolidated_rows),
        "diagnostic_row_count": len(diagnostic_rows),
        "monitoring_row_count": len(monitoring_rows),
        "diagnostic_axis_repair_target_count": diagnostic_axis_repair_target_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "row_class_counts": _count_by(consolidated_rows, "row_class"),
        "actionability_class_counts": _count_by(consolidated_rows, "actionability_class"),
        "axis_counts": _count_by(consolidated_rows, "axis"),
        "global_localization": global_rows[0] if global_rows else {},
        "top_hard_offtrack_targets": target_rows[:10],
        "top_collision_guardrails": [
            row for row in consolidated_rows if _bool(row.get("collision_guardrail_required"))
        ][:10],
        "top_soft_boundary_diagnostics": [
            row for row in consolidated_rows if _bool(row.get("soft_boundary_diagnostic"))
        ][:10],
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
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
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "target_rows": str(output / "target_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "diagnostic_rows": str(output / "diagnostic_rows.csv"),
            "consolidated_rows": str(output / "consolidated_rows.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
        },
        "failure_types_observed": [] if passes else ["metric_artifact"],
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-summary", type=Path, default=DEFAULT_SOURCE_SUMMARY)
    parser.add_argument("--localization-rows", type=Path, default=DEFAULT_LOCALIZATION_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-localization-row-count", type=int, default=DEFAULT_TARGET_LOCALIZATION_ROW_COUNT)
    parser.add_argument("--minimum-target-episode-count", type=int, default=DEFAULT_MINIMUM_TARGET_EPISODE_COUNT)
    parser.add_argument("--minimum-hard-offtrack-rate", type=float, default=DEFAULT_MINIMUM_HARD_OFFTRACK_RATE)
    parser.add_argument(
        "--minimum-collision-guardrail-rate",
        type=float,
        default=DEFAULT_MINIMUM_COLLISION_GUARDRAIL_RATE,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_target_consolidation(
        source_summary_path=args.source_summary,
        localization_rows_path=args.localization_rows,
        output_dir=args.output_dir,
        target_localization_row_count=int(args.target_localization_row_count),
        minimum_target_episode_count=int(args.minimum_target_episode_count),
        minimum_hard_offtrack_rate=float(args.minimum_hard_offtrack_rate),
        minimum_collision_guardrail_rate=float(args.minimum_collision_guardrail_rate),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_localization_row_count={summary['source_localization_row_count']}")
    print(f"hard_offtrack_target_row_count={summary['hard_offtrack_target_row_count']}")
    print(f"guardrail_row_count={summary['guardrail_row_count']}")
    print(f"diagnostic_row_count={summary['diagnostic_row_count']}")
    print(f"diagnostic_axis_repair_target_count={summary['diagnostic_axis_repair_target_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"winner_selected_count={summary['winner_selected_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
