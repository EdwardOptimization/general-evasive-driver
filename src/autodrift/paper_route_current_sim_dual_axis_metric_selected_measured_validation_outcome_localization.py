"""Artifact-only localization for M2445 metric-selected measured validation."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path("runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation")
DEFAULT_EPISODE_ROWS = DEFAULT_SOURCE_DIR / "episode_rows.csv"
DEFAULT_SUMMARY = DEFAULT_SOURCE_DIR / "summary.json"
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization"
)
DEFAULT_NEXT_BLOCKER = (
    "m2448-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_metric_selected_measured_validation_outcome_localization_pass"
RESULT_FAIL = "current_sim_dual_axis_metric_selected_measured_validation_outcome_localization_incomplete_or_fail"
TARGET_EPISODE_COUNT = 5250

LOCALIZATION_AXES = (
    "global",
    "profile_name",
    "profile_seed",
    "pack_id",
    "role_family",
    "scenario_family_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "sampled_obstacle_label",
    "termination_reason",
    "outcome_bucket",
)

LOCALIZATION_FIELDNAMES = [
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
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]
GUARDRAIL_FIELDNAMES = ["guardrail", "value", "violation", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _mean(values: Iterable[Any]) -> float:
    finite = [_finite_float(value) for value in values]
    finite = [value for value in finite if np.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def _min(values: Iterable[Any]) -> float:
    finite = [_finite_float(value) for value in values]
    finite = [value for value in finite if np.isfinite(value)]
    return float(np.min(finite)) if finite else float("nan")


def _max(values: Iterable[Any]) -> float:
    finite = [_finite_float(value) for value in values]
    finite = [value for value in finite if np.isfinite(value)]
    return float(np.max(finite)) if finite else float("nan")


def _flag_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    actual_success = sum(_bool(row.get("metric_selected_actual_success", row.get("success"))) for row in rows)
    hard_offtrack = sum(_bool(row.get("metric_selected_hard_offtrack_failure")) for row in rows)
    soft_violation = sum(_bool(row.get("metric_selected_soft_offtrack_violation")) for row in rows)
    boundary_tolerated_success = sum(_bool(row.get("metric_selected_boundary_tolerated_success")) for row in rows)
    collision = sum(_bool(row.get("collision")) for row in rows)
    max_step = sum(str(row.get("outcome_bucket", "")) == "max_steps_noncompletion" for row in rows)
    other = 0
    for row in rows:
        if not (
            _bool(row.get("metric_selected_actual_success", row.get("success")))
            or _bool(row.get("metric_selected_hard_offtrack_failure"))
            or _bool(row.get("metric_selected_soft_offtrack_violation"))
            or _bool(row.get("collision"))
            or str(row.get("outcome_bucket", "")) == "max_steps_noncompletion"
        ):
            other += 1
    return {
        "actual_success": actual_success,
        "hard_offtrack": hard_offtrack,
        "soft_violation": soft_violation,
        "boundary_tolerated_success": boundary_tolerated_success,
        "collision": collision,
        "max_step": max_step,
        "other": other,
    }


def _diagnostic_pattern(counts: Mapping[str, int], total: int) -> str:
    if total <= 0:
        return "empty"
    candidates = (
        ("hard_offtrack_dominated", counts.get("hard_offtrack", 0)),
        ("collision_dominated", counts.get("collision", 0)),
        ("success_supported", counts.get("actual_success", 0)),
        ("soft_violation_visible", counts.get("soft_violation", 0)),
        ("max_step_dominated", counts.get("max_step", 0)),
    )
    for name, count in candidates:
        if _rate(int(count), total) >= 0.5:
            return name
    return "mixed"


def localization_row(rows: Sequence[Mapping[str, Any]], *, axis: str, value: str) -> dict[str, Any]:
    total = len(rows)
    counts = _flag_counts(rows)
    return {
        "axis": axis,
        "value": value,
        "episode_count": total,
        "actual_success_count": counts["actual_success"],
        "actual_success_rate": _rate(counts["actual_success"], total),
        "hard_offtrack_count": counts["hard_offtrack"],
        "hard_offtrack_rate": _rate(counts["hard_offtrack"], total),
        "soft_offtrack_violation_count": counts["soft_violation"],
        "soft_offtrack_violation_rate": _rate(counts["soft_violation"], total),
        "boundary_tolerated_success_count": counts["boundary_tolerated_success"],
        "boundary_tolerated_success_rate": _rate(counts["boundary_tolerated_success"], total),
        "collision_count": counts["collision"],
        "collision_rate": _rate(counts["collision"], total),
        "max_step_noncompletion_count": counts["max_step"],
        "max_step_noncompletion_rate": _rate(counts["max_step"], total),
        "other_count": counts["other"],
        "other_rate": _rate(counts["other"], total),
        "mean_min_clearance_margin": _mean(row.get("min_clearance_margin") for row in rows),
        "min_min_clearance_margin": _min(row.get("min_clearance_margin") for row in rows),
        "mean_overshoot_m": _mean(row.get("metric_selected_max_offtrack_overshoot_m") for row in rows),
        "max_overshoot_m": _max(row.get("metric_selected_max_offtrack_overshoot_m") for row in rows),
        "mean_steps": _mean(row.get("steps") for row in rows),
        "diagnostic_pattern": _diagnostic_pattern(counts, total),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def localization_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [localization_row(episode_rows, axis="global", value="all")]
    for axis in LOCALIZATION_AXES:
        if axis == "global":
            continue
        groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in episode_rows:
            groups[str(row.get(axis, ""))].append(row)
        for value, group in sorted(groups.items()):
            rows.append(localization_row(group, axis=axis, value=value))
    return rows


def decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "measured_policy_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2447 is artifact-only localization over M2445 rows.",
        },
        {
            "decision_key": "policy_action_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "No environment or policy is instantiated.",
        },
        {
            "decision_key": "repair_training_ranking",
            "decision_value": "false",
            "admissible": True,
            "reason": "All localization axes are diagnostic-only and non-ranking.",
        },
        {
            "decision_key": "next_route",
            "decision_value": DEFAULT_NEXT_BLOCKER,
            "admissible": True,
            "reason": "Audit localization before any repair, training, scenario-quality route, or verdict claim.",
        },
    ]


def guardrail_rows() -> list[dict[str, Any]]:
    rows = [
        ("measured_policy_rollout_started", False, "M2447 does not rerun M2445."),
        ("policy_action_executed", False, "M2447 does not instantiate a policy."),
        ("repair_execution_started", False, "M2447 does not execute repair."),
        ("training_started", False, "M2447 does not train."),
        ("ranking_admissible", False, "M2447 keeps all axes diagnostic-only."),
        ("winner_selected", False, "M2447 selects no winner."),
        ("current_sim_verdict_claim_made", False, "M2447 makes no current-sim verdict."),
    ]
    return [
        {
            "guardrail": key,
            "value": value,
            "violation": bool(value),
            "reason": reason,
        }
        for key, value, reason in rows
    ]


def run_outcome_localization(
    *,
    source_summary_path: Path | str = DEFAULT_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    episode_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source_summary_path) if episode_rows is None else {}
    rows = list(episode_rows) if episode_rows is not None else read_csv_rows(episode_rows_path)
    loc_rows = localization_rows(rows)
    decisions = decision_rows()
    guards = guardrail_rows()
    guardrail_violation_count = sum(_bool(row.get("violation")) for row in guards)
    global_row = loc_rows[0] if loc_rows else {}
    passes = (
        len(rows) == int(target_episode_count)
        and loc_rows
        and int(global_row.get("hard_offtrack_count", -1)) >= 0
        and guardrail_violation_count == 0
        and not any(_bool(row.get("ranking_admissible")) or _bool(row.get("winner_selected")) for row in loc_rows)
    )
    hard_rows = [
        row
        for row in loc_rows
        if str(row.get("axis", "")) != "global" and int(row.get("hard_offtrack_count", 0) or 0) > 0
    ]
    hard_rows_sorted = sorted(
        hard_rows,
        key=lambda row: (-int(row.get("hard_offtrack_count", 0) or 0), str(row.get("axis", "")), str(row.get("value", ""))),
    )
    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(source_summary_path),
        "source_result_class": str(source_summary.get("result_class", "")),
        "episode_count": len(rows),
        "target_episode_count": int(target_episode_count),
        "localization_row_count": len(loc_rows),
        "guardrail_violation_count": int(guardrail_violation_count),
        "global_localization": global_row,
        "top_hard_offtrack_diagnostic_slices": hard_rows_sorted[:10],
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "localization_rows": str(output / "localization_rows.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
        },
        "failure_types_observed": [] if passes else ["metric_artifact"],
        "next_blocker": str(next_blocker),
    }
    write_csv_rows(output / "localization_rows.csv", loc_rows, fieldnames=LOCALIZATION_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_outcome_localization(
        source_summary_path=args.source_summary,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        next_blocker=str(args.next_blocker),
    )
    global_row = summary.get("global_localization", {})
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"localization_row_count={summary['localization_row_count']}")
    print(f"hard_offtrack_rate={global_row.get('hard_offtrack_rate')}")
    print(f"collision_rate={global_row.get('collision_rate')}")
    print(f"actual_success_rate={global_row.get('actual_success_rate')}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
