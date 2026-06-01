"""No-rerun profile/history failure diagnosis for current-sim diagnostics."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_EPISODE_ROWS = Path("runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv")
DEFAULT_DIAGNOSTIC_SUMMARY = Path("runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json")
DEFAULT_SCENE_CANDIDATE_SUMMARY = Path(
    "runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_summary.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit"
TARGET_PROFILES = (
    "L3_online_gru",
    "L3_reset_control",
    "L2_window_25",
    "L2_window_50",
    "L0_current_masked",
    "L1_one_step",
)
PAIRWISE_DELTAS = (
    ("L2_window_25", "L3_online_gru"),
    ("L2_window_25", "L3_reset_control"),
    ("L2_window_50", "L3_online_gru"),
    ("L2_window_50", "L3_reset_control"),
    ("L3_online_gru", "L3_reset_control"),
)
MEAN_METRICS = (
    "return",
    "action_rate_mean",
    "min_clearance_margin",
    "max_off_track_overshoot",
    "off_track_severity_proxy",
    "time_to_first_off_track_s",
    "impact_speed_proxy",
    "impact_severity_proxy",
    "high_sideslip_fraction",
    "max_abs_beta",
    "max_abs_yaw_rate",
)
SUMMARY_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "group_axis",
    "group_name",
    "failure_mode_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "mean_return",
    "mean_action_rate",
    "mean_min_clearance_margin",
    "mean_max_off_track_overshoot",
    "mean_off_track_severity_proxy",
    "mean_time_to_first_off_track_s",
    "mean_impact_speed_proxy",
    "mean_impact_severity_proxy",
    "mean_high_sideslip_fraction",
    "mean_max_abs_beta",
    "mean_max_abs_yaw_rate",
    "drift_used_rate",
    "recovery_success_rate",
    "missing_metric_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
]
DELTA_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "left_profile",
    "right_profile",
    "success_rate_delta",
    "offtrack_rate_delta",
    "collision_rate_delta",
    "mean_time_to_first_off_track_delta",
    "mean_min_clearance_margin_delta",
    "mean_action_rate_delta",
    "mean_max_abs_beta_delta",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
]
L3_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "l3_online_label",
    "l3_reset_label",
    "l3_online_success_count",
    "l3_reset_success_count",
    "l3_online_offtrack_count",
    "l3_reset_offtrack_count",
    "l3_online_collision_count",
    "l3_reset_collision_count",
    "l3_zero_success",
    "reset_equivalent_to_online",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _mean_metric(rows: Iterable[Mapping[str, Any]], key: str) -> tuple[float | None, int]:
    values: list[float] = []
    missing = 0
    for row in rows:
        value = _float_or_none(row.get(key))
        if value is None:
            missing += 1
        else:
            values.append(value)
    if not values:
        return None, missing
    return sum(values) / len(values), missing


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _outcome_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        bucket = str(row.get("outcome_bucket", "")).strip()
        if bucket == "success_obstacle_pass" or _bool(row.get("success")):
            counter["success"] += 1
        elif bucket == "collision_failure" or _bool(row.get("collision")):
            counter["collision"] += 1
        elif bucket == "off_track_noncollision_noncompletion" or str(row.get("termination_reason", "")).strip() == "off_track":
            counter["offtrack"] += 1
        else:
            counter["other"] += 1
    return dict(counter)


def parse_group_filter(group_value: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    for item in str(group_value).split("|"):
        if "=" not in item:
            continue
        key, value = item.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if key:
            filters[key] = value
    return filters


def _matches(row: Mapping[str, Any], filters: Mapping[str, str]) -> bool:
    return all(str(row.get(key, "")).strip() == value for key, value in filters.items())


def _aggregate_metrics(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _outcome_counts(rows)
    episode_count = len(rows)
    success_count = int(counts.get("success", 0))
    collision_count = int(counts.get("collision", 0))
    offtrack_count = int(counts.get("offtrack", 0))
    output: dict[str, Any] = {
        "episode_count": episode_count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_count": offtrack_count,
        "success_rate": _rate(success_count, episode_count),
        "collision_rate": _rate(collision_count, episode_count),
        "offtrack_rate": _rate(offtrack_count, episode_count),
    }
    missing_total = 0
    for metric in MEAN_METRICS:
        mean, missing = _mean_metric(rows, metric)
        if metric == "return":
            output_key = "mean_return"
        elif metric == "action_rate_mean":
            output_key = "mean_action_rate"
        else:
            output_key = f"mean_{metric}"
        output[output_key] = mean
        missing_total += missing
    drift_used = sum(1 for row in rows if _bool(row.get("drift_used")))
    recovery_success = sum(1 for row in rows if _bool(row.get("recovery_success")))
    output["drift_used_rate"] = _rate(drift_used, episode_count)
    output["recovery_success_rate"] = _rate(recovery_success, episode_count)
    output["missing_metric_count"] = missing_total
    return output


def failure_mode_label(metrics: Mapping[str, Any]) -> str:
    success_count = int(metrics.get("success_count", 0))
    collision_count = int(metrics.get("collision_count", 0))
    offtrack_count = int(metrics.get("offtrack_count", 0))
    time_to_offtrack = metrics.get("mean_time_to_first_off_track_s")
    max_beta = metrics.get("mean_max_abs_beta")
    high_sideslip = metrics.get("mean_high_sideslip_fraction")
    if success_count >= 8:
        return "supported_success"
    if collision_count >= max(success_count, offtrack_count):
        return "collision_dominated_failure"
    if offtrack_count > success_count and time_to_offtrack is not None and float(time_to_offtrack) <= 2.0:
        return "early_offtrack_failure"
    if offtrack_count > success_count and (time_to_offtrack is None or float(time_to_offtrack) > 2.0):
        return "late_offtrack_or_noncompletion"
    if (max_beta is not None and float(max_beta) >= 0.8) or (
        high_sideslip is not None and float(high_sideslip) >= 0.25
    ):
        return "high_instability_failure"
    if success_count < 8:
        return "low_support_failure"
    return "mixed_failure"


def _summary_row(
    *,
    candidate: Mapping[str, Any],
    group_axis: str,
    group_name: str,
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    metrics = _aggregate_metrics(rows)
    return {
        "candidate_id": candidate["candidate_id"],
        "group_key": candidate["group_key"],
        "group_value": candidate["group_value"],
        "group_axis": group_axis,
        "group_name": group_name,
        "failure_mode_label": failure_mode_label(metrics),
        **metrics,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
    }


def _candidate_rows(episodes: list[Mapping[str, Any]], candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    filters = parse_group_filter(str(candidate.get("group_value", "")))
    return [row for row in episodes if _matches(row, filters)]


def _group_by_profile(
    *,
    episodes: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        rows = _candidate_rows(episodes, candidate)
        for profile in TARGET_PROFILES:
            group = [row for row in rows if str(row.get("profile_name", "")).strip() == profile]
            if group:
                output.append(_summary_row(candidate=candidate, group_axis="profile_name", group_name=profile, rows=group))
    return output


def _group_by_history(
    *,
    episodes: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        rows = _candidate_rows(episodes, candidate)
        histories = sorted({str(row.get("history_representation", "")).strip() for row in rows})
        for history in histories:
            group = [row for row in rows if str(row.get("history_representation", "")).strip() == history]
            output.append(_summary_row(candidate=candidate, group_axis="history_representation", group_name=history, rows=group))
    return output


def _delta(left: Any, right: Any) -> float | None:
    left_value = _float_or_none(left)
    right_value = _float_or_none(right)
    if left_value is None or right_value is None:
        return None
    return left_value - right_value


def _pairwise_deltas(profile_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in profile_rows:
        by_candidate.setdefault(str(row["candidate_id"]), {})[str(row["group_name"])] = row
    output: list[dict[str, Any]] = []
    for candidate_id, by_profile in sorted(by_candidate.items()):
        sample = next(iter(by_profile.values()))
        for left, right in PAIRWISE_DELTAS:
            if left not in by_profile or right not in by_profile:
                continue
            left_row = by_profile[left]
            right_row = by_profile[right]
            output.append(
                {
                    "candidate_id": candidate_id,
                    "group_key": sample["group_key"],
                    "group_value": sample["group_value"],
                    "left_profile": left,
                    "right_profile": right,
                    "success_rate_delta": _delta(left_row.get("success_rate"), right_row.get("success_rate")),
                    "offtrack_rate_delta": _delta(left_row.get("offtrack_rate"), right_row.get("offtrack_rate")),
                    "collision_rate_delta": _delta(left_row.get("collision_rate"), right_row.get("collision_rate")),
                    "mean_time_to_first_off_track_delta": _delta(
                        left_row.get("mean_time_to_first_off_track_s"),
                        right_row.get("mean_time_to_first_off_track_s"),
                    ),
                    "mean_min_clearance_margin_delta": _delta(
                        left_row.get("mean_min_clearance_margin"),
                        right_row.get("mean_min_clearance_margin"),
                    ),
                    "mean_action_rate_delta": _delta(left_row.get("mean_action_rate"), right_row.get("mean_action_rate")),
                    "mean_max_abs_beta_delta": _delta(left_row.get("mean_max_abs_beta"), right_row.get("mean_max_abs_beta")),
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                    "finite_window_vs_gru_conclusion_made": False,
                }
            )
    return output


def _l3_breakdown(profile_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in profile_rows:
        by_candidate.setdefault(str(row["candidate_id"]), {})[str(row["group_name"])] = row
    output: list[dict[str, Any]] = []
    for candidate_id, by_profile in sorted(by_candidate.items()):
        online = by_profile.get("L3_online_gru")
        reset = by_profile.get("L3_reset_control")
        if online is None or reset is None:
            continue
        online_counts = (int(online["success_count"]), int(online["offtrack_count"]), int(online["collision_count"]))
        reset_counts = (int(reset["success_count"]), int(reset["offtrack_count"]), int(reset["collision_count"]))
        output.append(
            {
                "candidate_id": candidate_id,
                "group_key": online["group_key"],
                "group_value": online["group_value"],
                "l3_online_label": online["failure_mode_label"],
                "l3_reset_label": reset["failure_mode_label"],
                "l3_online_success_count": online_counts[0],
                "l3_reset_success_count": reset_counts[0],
                "l3_online_offtrack_count": online_counts[1],
                "l3_reset_offtrack_count": reset_counts[1],
                "l3_online_collision_count": online_counts[2],
                "l3_reset_collision_count": reset_counts[2],
                "l3_zero_success": online_counts[0] == 0 and reset_counts[0] == 0,
                "reset_equivalent_to_online": online_counts == reset_counts,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "profile_history_failure_diagnosis", "admissible": True, "reason": "M2221 uses existing episode metrics"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2221 forces ranking_admissible false"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2221 does not select a profile"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2221 is diagnostic only"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2221 is public no-rerun diagnosis"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2221 runs no history intervention"},
    ]


def run_profile_history_failure_diagnosis(
    *,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    diagnostic_summary: Path | str = DEFAULT_DIAGNOSTIC_SUMMARY,
    scene_candidate_summary: Path | str = DEFAULT_SCENE_CANDIDATE_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episodes = read_csv_rows(episode_rows)
    parent_summary = read_json(diagnostic_summary)
    candidates = read_csv_rows(scene_candidate_summary)
    profile_rows = _group_by_profile(episodes=episodes, candidates=candidates)
    history_rows = _group_by_history(episodes=episodes, candidates=candidates)
    delta_rows = _pairwise_deltas(profile_rows)
    l3_rows = _l3_breakdown(profile_rows)

    profile_totals: dict[str, int] = {}
    for profile in TARGET_PROFILES:
        profile_totals[profile] = sum(int(row["success_count"]) for row in profile_rows if row["group_name"] == profile)
    l3_zero_success_confirmed = profile_totals.get("L3_online_gru", 0) == 0 and profile_totals.get("L3_reset_control", 0) == 0
    l3_reset_equivalent_to_online = bool(l3_rows) and all(_bool(row["reset_equivalent_to_online"]) for row in l3_rows)
    finite_window_support_visible = profile_totals.get("L2_window_25", 0) > 0 or profile_totals.get("L2_window_50", 0) > 0
    ranking_admissible_count = 0
    winner_selected = False
    guardrail_flags = {
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": winner_selected,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_profile_history_failure_diagnosis_pass"
        if candidates and ranking_admissible_count == 0 and not winner_selected and guardrail_violation_count == 0
        else "current_sim_profile_history_failure_diagnosis_fail"
    )

    write_csv_rows(output / "profile_failure_metric_summary.csv", profile_rows, fieldnames=SUMMARY_FIELDNAMES)
    write_csv_rows(output / "history_failure_metric_summary.csv", history_rows, fieldnames=SUMMARY_FIELDNAMES)
    write_csv_rows(output / "profile_pair_delta_metrics.csv", delta_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "l3_failure_mode_breakdown.csv", l3_rows, fieldnames=L3_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary_payload = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "episode_rows": str(episode_rows),
        "diagnostic_summary": str(diagnostic_summary),
        "scene_candidate_summary": str(scene_candidate_summary),
        "parent_result_class": parent_summary.get("result_class"),
        "target_profile_count": len(TARGET_PROFILES),
        "scene_candidate_count": len(candidates),
        "episode_row_count": len(episodes),
        "profile_metric_row_count": len(profile_rows),
        "history_metric_row_count": len(history_rows),
        "pair_delta_row_count": len(delta_rows),
        "l3_failure_breakdown_row_count": len(l3_rows),
        "l3_online_success_count": profile_totals.get("L3_online_gru", 0),
        "l3_reset_success_count": profile_totals.get("L3_reset_control", 0),
        "l2_window_25_success_count": profile_totals.get("L2_window_25", 0),
        "l2_window_50_success_count": profile_totals.get("L2_window_50", 0),
        "l3_zero_success_confirmed": l3_zero_success_confirmed,
        "l3_reset_equivalent_to_online": l3_reset_equivalent_to_online,
        "finite_window_support_visible": finite_window_support_visible,
        "failure_mode_counts": dict(sorted(Counter(str(row["failure_mode_label"]) for row in profile_rows).items())),
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected": winner_selected,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "profile_failure_metric_summary": str(output / "profile_failure_metric_summary.csv"),
            "history_failure_metric_summary": str(output / "history_failure_metric_summary.csv"),
            "profile_pair_delta_metrics": str(output / "profile_pair_delta_metrics.csv"),
            "l3_failure_mode_breakdown": str(output / "l3_failure_mode_breakdown.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary_payload)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2221-paper-route-current-sim-profile-history-failure-diagnosis-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary_payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--diagnostic-summary", type=Path, default=DEFAULT_DIAGNOSTIC_SUMMARY)
    parser.add_argument("--scene-candidate-summary", type=Path, default=DEFAULT_SCENE_CANDIDATE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_profile_history_failure_diagnosis(
        episode_rows=args.episode_rows,
        diagnostic_summary=args.diagnostic_summary,
        scene_candidate_summary=args.scene_candidate_summary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scene_candidate_count={summary['scene_candidate_count']}")
    print(f"l3_online_success_count={summary['l3_online_success_count']}")
    print(f"l3_reset_success_count={summary['l3_reset_success_count']}")
    print(f"l2_window_25_success_count={summary['l2_window_25_success_count']}")
    print(f"l3_zero_success_confirmed={summary['l3_zero_success_confirmed']}")
    print(f"l3_reset_equivalent_to_online={summary['l3_reset_equivalent_to_online']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
