"""Artifact-only failure-slice diagnosis for M2293 scenario task-family rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json")
DEFAULT_EPISODE_ROWS = Path("runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit"

SLICE_AXES = (
    "role_family",
    "scenario_family_id",
    "sampled_obstacle_label",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "hidden_dynamics_bucket",
    "profile_name",
    "profile_seed",
    "outcome_bucket",
    "termination_reason",
)
SLICE_FIELDNAMES = [
    "axis",
    "group_key",
    "episode_count",
    "success_count",
    "success_rate",
    "failure_count",
    "failure_rate",
    "offtrack_count",
    "offtrack_rate",
    "collision_count",
    "collision_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_failure_count",
    "other_failure_rate",
    "mean_return",
    "mean_steps",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_high_sideslip_fraction",
    "mean_action_rate",
    "dominant_failure_mode",
    "dominant_failure_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROUTE_FIELDNAMES = [
    "route",
    "admitted",
    "support_reason",
    "support_axis",
    "support_group",
    "support_failure_mode",
    "support_failure_count",
    "global_success_rate",
    "global_offtrack_rate",
    "global_collision_rate",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


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
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(parsed):
        return None
    return float(parsed)


def _mean(values: Sequence[Any]) -> float | None:
    finite = [_float_or_none(value) for value in values]
    finite = [value for value in finite if value is not None]
    if not finite:
        return None
    return float(np.mean(finite))


def _min(values: Sequence[Any]) -> float | None:
    finite = [_float_or_none(value) for value in values]
    finite = [value for value in finite if value is not None]
    if not finite:
        return None
    return float(np.min(finite))


def _is_success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success"))
    return str(row.get("outcome_bucket", "")) == "success_obstacle_pass" or (
        _bool(row.get("obstacle_completed")) and not _bool(row.get("collision"))
    )


def _is_collision(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "collision_failure" or _bool(row.get("collision"))


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion" or str(
        row.get("termination_reason", "")
    ) == "off_track"


def _is_max_step(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "max_steps_noncompletion" or _bool(row.get("truncated"))


def _counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    success = 0
    offtrack = 0
    collision = 0
    max_step = 0
    other = 0
    for row in rows:
        if _is_success(row):
            success += 1
        elif _is_collision(row):
            collision += 1
        elif _is_offtrack(row):
            offtrack += 1
        elif _is_max_step(row):
            max_step += 1
        else:
            other += 1
    total = len(rows)
    return {
        "total": total,
        "success": success,
        "offtrack": offtrack,
        "collision": collision,
        "max_step": max_step,
        "other": other,
        "failure": total - success,
    }


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _dominant_failure(counts: Mapping[str, int]) -> tuple[str, int]:
    failures = {
        "offtrack_dominated_failure": int(counts.get("offtrack", 0)),
        "collision_dominated_failure": int(counts.get("collision", 0)),
        "max_step_noncompletion_dominated_failure": int(counts.get("max_step", 0)),
        "mixed_or_other_failure": int(counts.get("other", 0)),
    }
    label, value = max(failures.items(), key=lambda item: item[1])
    if value <= 0:
        return "success_supported", 0
    return label, int(value)


def _group_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    return grouped


def slice_row(*, axis: str, group_key: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _counts(rows)
    total = counts["total"]
    failure_mode, failure_count = _dominant_failure(counts)
    return {
        "axis": axis,
        "group_key": group_key,
        "episode_count": total,
        "success_count": counts["success"],
        "success_rate": _rate(counts["success"], total),
        "failure_count": counts["failure"],
        "failure_rate": _rate(counts["failure"], total),
        "offtrack_count": counts["offtrack"],
        "offtrack_rate": _rate(counts["offtrack"], total),
        "collision_count": counts["collision"],
        "collision_rate": _rate(counts["collision"], total),
        "max_step_noncompletion_count": counts["max_step"],
        "max_step_noncompletion_rate": _rate(counts["max_step"], total),
        "other_failure_count": counts["other"],
        "other_failure_rate": _rate(counts["other"], total),
        "mean_return": _mean([row.get("return") for row in rows]),
        "mean_steps": _mean([row.get("steps") for row in rows]),
        "mean_min_clearance_margin": _mean([row.get("min_clearance_margin") for row in rows]),
        "min_min_clearance_margin": _min([row.get("min_clearance_margin") for row in rows]),
        "mean_high_sideslip_fraction": _mean([row.get("high_sideslip_fraction") for row in rows]),
        "mean_action_rate": _mean([row.get("action_rate_mean") for row in rows]),
        "dominant_failure_mode": failure_mode,
        "dominant_failure_count": failure_count,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def build_slice_rows(rows: Sequence[Mapping[str, Any]], axis: str) -> list[dict[str, Any]]:
    return [
        slice_row(axis=axis, group_key=group_key, rows=group_rows)
        for group_key, group_rows in sorted(_group_by(rows, axis).items())
    ]


def _dominant_slices(all_slices: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in all_slices if int(row.get("failure_count", 0) or 0) > 0]
    rows.sort(
        key=lambda row: (
            -int(row.get("dominant_failure_count", 0) or 0),
            -int(row.get("episode_count", 0) or 0),
            str(row.get("axis", "")),
            str(row.get("group_key", "")),
        )
    )
    return rows


def _route_rows(global_row: Mapping[str, Any], dominant_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    top = dict(dominant_rows[0]) if dominant_rows else {}
    global_success_rate = float(global_row.get("success_rate", 0.0) or 0.0)
    global_offtrack_rate = float(global_row.get("offtrack_rate", 0.0) or 0.0)
    global_collision_rate = float(global_row.get("collision_rate", 0.0) or 0.0)
    route = "scenario_task_family_failure_slice_result_audit"
    reason = "failure slices are available for audit"

    if not dominant_rows:
        route = "readiness_floor_or_success_support_audit"
        reason = "no dominant failure slice is present"
    elif global_offtrack_rate >= 0.5:
        route = "offtrack_primary_collision_guardrail_failure_slice_result_audit"
        reason = "global offtrack dominates while collision slices remain a guardrail"
    elif global_collision_rate >= 0.5:
        route = "collision_primary_failure_slice_result_audit"
        reason = "global collision dominates"
    elif global_success_rate < 0.2:
        route = "low_success_mixed_failure_slice_result_audit"
        reason = "success is low but no single global failure mode dominates"

    return [
        {
            "route": route,
            "admitted": True,
            "support_reason": reason,
            "support_axis": str(top.get("axis", "")),
            "support_group": str(top.get("group_key", "")),
            "support_failure_mode": str(top.get("dominant_failure_mode", "")),
            "support_failure_count": int(top.get("dominant_failure_count", 0) or 0),
            "global_success_rate": global_success_rate,
            "global_offtrack_rate": global_offtrack_rate,
            "global_collision_rate": global_collision_rate,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
    ]


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "failure_slice_diagnosis",
            "admissible": True,
            "reason": "diagnosis consumes existing M2293 artifacts without rerun",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "profile slices are diagnostic only and are not a ranking denominator",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "artifact-only public diagnosis is not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "diagnosis does not run the denominator-backed comparison protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "diagnosis does not test wrong-history or history necessity",
        },
    ]


def _summary_counts_match(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    counts = _counts(rows)
    global_summary = summary.get("global_outcome", {})
    if not isinstance(global_summary, Mapping):
        global_summary = {}
    return {
        "episode_count_match": counts["total"] == int(summary.get("episode_count", -1)),
        "success_count_match": counts["success"] == int(global_summary.get("success_count", -1)),
        "offtrack_count_match": counts["offtrack"] == int(global_summary.get("offtrack_count", -1)),
        "collision_count_match": counts["collision"] == int(global_summary.get("collision_count", -1)),
        "max_step_count_match": counts["max_step"] == int(global_summary.get("max_step_noncompletion_count", -1)),
    }


def run_failure_slice_diagnosis(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = read_json(summary_path)
    rows = read_csv_rows(episode_rows_path)

    global_row = slice_row(axis="global", group_key="all", rows=rows)
    all_slices: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {
        "summary": str(output / "summary.json"),
        "global_slice": str(output / "global_slice.csv"),
        "all_slices": str(output / "all_slices.csv"),
        "dominant_slices": str(output / "dominant_slices.csv"),
        "route_recommendation": str(output / "route_recommendation.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    write_csv_rows(output / "global_slice.csv", [global_row], fieldnames=SLICE_FIELDNAMES)
    for axis in SLICE_AXES:
        axis_rows = build_slice_rows(rows, axis)
        filename = f"slice_by_{axis}.csv"
        write_csv_rows(output / filename, axis_rows, fieldnames=SLICE_FIELDNAMES)
        artifacts[f"slice_by_{axis}"] = str(output / filename)
        all_slices.extend(axis_rows)
    write_csv_rows(output / "all_slices.csv", all_slices, fieldnames=SLICE_FIELDNAMES)
    dominant_rows = _dominant_slices(all_slices)
    write_csv_rows(output / "dominant_slices.csv", dominant_rows, fieldnames=SLICE_FIELDNAMES)
    route_rows = _route_rows(global_row, dominant_rows)
    write_csv_rows(output / "route_recommendation.csv", route_rows, fieldnames=ROUTE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    count_matches = _summary_counts_match(summary, rows)
    required_axis_artifacts_exist = all(Path(path).exists() for key, path in artifacts.items() if key.startswith("slice_by_"))
    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        bool(rows)
        and all(count_matches.values())
        and required_axis_artifacts_exist
        and bool(dominant_rows)
        and bool(route_rows)
        and guardrail_violation_count == 0
    )
    result = {
        "result_class": (
            "current_sim_scenario_task_family_failure_slice_diagnosis_pass"
            if passes
            else "current_sim_scenario_task_family_failure_slice_diagnosis_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "summary_path": str(summary_path),
        "episode_rows_path": str(episode_rows_path),
        "output_dir": str(output),
        "input_episode_count": len(rows),
        "summary_episode_count": int(summary.get("episode_count", -1)),
        "count_matches": count_matches,
        "global_success_count": int(global_row["success_count"]),
        "global_success_rate": float(global_row["success_rate"]),
        "global_offtrack_count": int(global_row["offtrack_count"]),
        "global_offtrack_rate": float(global_row["offtrack_rate"]),
        "global_collision_count": int(global_row["collision_count"]),
        "global_collision_rate": float(global_row["collision_rate"]),
        "global_dominant_failure_mode": str(global_row["dominant_failure_mode"]),
        "dominant_slice_count": len(dominant_rows),
        "top_dominant_slice": dominant_rows[0] if dominant_rows else {},
        "primary_route": str(route_rows[0]["route"]) if route_rows else "",
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_failure_slice_diagnosis(
        summary_path=args.summary,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_episode_count={summary['input_episode_count']}")
    print(f"primary_route={summary['primary_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
