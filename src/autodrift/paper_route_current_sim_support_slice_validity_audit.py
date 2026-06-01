"""No-rerun validity audit for current-sim support slices."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_GROUP_SUPPORT = Path("runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/group_outcome_support.csv")
DEFAULT_SUMMARY = Path("runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json")
DEFAULT_EPISODE_ROWS = Path("runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2215_paper_route_current_sim_support_slice_validity_audit")
DEFAULT_NEXT_BLOCKER = "m2216-paper-route-current-sim-support-slice-validity-audit-result-audit"
SUPPORT_LABELS = {"comparison_ready_candidate", "candidate_support"}
BLOCKER_LABELS = {"offtrack_dominated", "collision_dominated", "low_success_support"}
SCENE_GROUP_KEYS = {"overall", "task_family", "source_family_template", "capability_pair"}
VALIDITY_FIELDNAMES = [
    "group_key",
    "group_value",
    "support_label",
    "validity_label",
    "validity_reason",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "profile_count",
    "history_representation_count",
    "task_source_count",
    "contains_profile_axis",
    "contains_profile_level_axis",
    "contains_history_axis",
    "profile_denominator_balanced",
    "history_denominator_balanced",
    "task_source_denominator_sufficient",
    "ranking_admissible",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _int(row: Mapping[str, Any], key: str) -> int:
    value = row.get(key, 0)
    if value in (None, ""):
        return 0
    return int(float(value))


def _float(row: Mapping[str, Any], key: str) -> float:
    value = row.get(key, 0.0)
    if value in (None, ""):
        return 0.0
    return float(value)


def _group_contains(group_key: str, axis: str) -> bool:
    parts = {part.strip() for part in group_key.split(" x ")}
    return axis in parts


def _validity_reason(label: str) -> str:
    reasons = {
        "scene_backed_candidate": "support exists on a scene-level group with multi-profile/history denominator",
        "history_family_diagnostic": "support is tied to a history-representation group and is diagnostic only",
        "profile_only_candidate": "support is tied to a profile/profile-level axis and cannot rank controllers by itself",
        "denominator_imbalanced": "support label exists but denominator balance is insufficient",
        "global_or_scene_blocker": "scene-level row remains blocked by offtrack/collision/low-success support",
        "low_sample_or_unresolved": "row is low-sample or unresolved",
        "invalid_for_ranking": "row does not support a ranking-admissible claim",
    }
    return reasons[label]


def classify_validity(row: Mapping[str, Any]) -> dict[str, Any]:
    group_key = str(row.get("group_key", "")).strip()
    support_label = str(row.get("support_label", "")).strip()
    episode_count = _int(row, "episode_count")
    profile_count = _int(row, "profile_count")
    history_count = _int(row, "history_representation_count")
    task_source_count = _int(row, "task_source_count")
    contains_profile_axis = _group_contains(group_key, "profile_name")
    contains_profile_level_axis = _group_contains(group_key, "profile_level")
    contains_history_axis = _group_contains(group_key, "history_representation")
    contains_any_profile_axis = contains_profile_axis or contains_profile_level_axis
    profile_denominator_balanced = profile_count >= 4
    history_denominator_balanced = history_count >= 2
    task_source_denominator_sufficient = task_source_count >= 16

    if (
        support_label in SUPPORT_LABELS
        and not contains_any_profile_axis
        and not contains_history_axis
        and profile_denominator_balanced
        and history_denominator_balanced
        and task_source_denominator_sufficient
        and episode_count >= 64
    ):
        validity_label = "scene_backed_candidate"
    elif (
        support_label in SUPPORT_LABELS
        and contains_history_axis
        and not contains_any_profile_axis
        and profile_count >= 2
        and episode_count >= 64
    ):
        validity_label = "history_family_diagnostic"
    elif support_label in SUPPORT_LABELS and contains_any_profile_axis and episode_count >= 64:
        validity_label = "profile_only_candidate"
    elif (
        support_label in SUPPORT_LABELS
        and (
            profile_count < 2
            or history_count < 1
            or task_source_count < 16
            or episode_count < 64
        )
    ):
        validity_label = "denominator_imbalanced"
    elif group_key in SCENE_GROUP_KEYS and support_label in BLOCKER_LABELS:
        validity_label = "global_or_scene_blocker"
    elif support_label in {"low_sample_count", "mixed_unresolved"}:
        validity_label = "low_sample_or_unresolved"
    else:
        validity_label = "invalid_for_ranking"

    output = dict(row)
    output.update(
        {
            "episode_count": episode_count,
            "success_count": _int(row, "success_count"),
            "collision_count": _int(row, "collision_count"),
            "offtrack_count": _int(row, "offtrack_count"),
            "success_rate": _float(row, "success_rate"),
            "collision_rate": _float(row, "collision_rate"),
            "offtrack_rate": _float(row, "offtrack_rate"),
            "profile_count": profile_count,
            "history_representation_count": history_count,
            "task_source_count": task_source_count,
            "validity_label": validity_label,
            "validity_reason": _validity_reason(validity_label),
            "contains_profile_axis": contains_profile_axis,
            "contains_profile_level_axis": contains_profile_level_axis,
            "contains_history_axis": contains_history_axis,
            "profile_denominator_balanced": profile_denominator_balanced,
            "history_denominator_balanced": history_denominator_balanced,
            "task_source_denominator_sufficient": task_source_denominator_sufficient,
            "ranking_admissible": False,
        }
    )
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "support_slice_validity_audit", "admissible": True, "reason": "M2215 uses no-rerun slice analysis"},
        {"claim": "measured_execution_rerun", "admissible": False, "reason": "M2215 does not execute policies"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2215 forces ranking_admissible false"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2215 does not select a controller"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2215 is not a comparison verdict"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2215 is public no-rerun reanalysis"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2215 runs no history intervention"},
    ]


def _write_subset(output: Path, filename: str, rows: list[dict[str, Any]], label: str) -> None:
    write_csv_rows(output / filename, [row for row in rows if row["validity_label"] == label], fieldnames=VALIDITY_FIELDNAMES)


def run_validity_audit(
    *,
    group_support: Path | str = DEFAULT_GROUP_SUPPORT,
    summary: Path | str = DEFAULT_SUMMARY,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    group_rows = read_csv_rows(group_support)
    episode_count = len(read_csv_rows(episode_rows))
    parent_summary = read_json(summary)
    validity_rows = [classify_validity(row) for row in group_rows]
    label_counts = Counter(str(row["validity_label"]) for row in validity_rows)
    ranking_admissible_count = sum(1 for row in validity_rows if bool(row["ranking_admissible"]))

    write_csv_rows(output / "slice_validity.csv", validity_rows, fieldnames=VALIDITY_FIELDNAMES)
    _write_subset(output, "scene_backed_candidates.csv", validity_rows, "scene_backed_candidate")
    _write_subset(output, "history_family_diagnostic_candidates.csv", validity_rows, "history_family_diagnostic")
    _write_subset(output, "profile_only_candidates.csv", validity_rows, "profile_only_candidate")
    _write_subset(output, "denominator_imbalanced_slices.csv", validity_rows, "denominator_imbalanced")
    _write_subset(output, "global_or_scene_blockers.csv", validity_rows, "global_or_scene_blocker")
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    guardrail_flags = {
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_support_slice_validity_audit_pass"
        if group_rows and ranking_admissible_count == 0 and guardrail_violation_count == 0
        else "current_sim_support_slice_validity_audit_fail"
    )
    summary_payload = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "group_support": str(group_support),
        "parent_summary": str(summary),
        "episode_rows": str(episode_rows),
        "parent_result_class": parent_summary.get("result_class"),
        "parent_input_episode_count": int(parent_summary.get("input_episode_count", 0)),
        "episode_row_count": episode_count,
        "input_group_count": len(group_rows),
        "validity_label_counts": dict(sorted(label_counts.items())),
        "scene_backed_candidate_count": int(label_counts.get("scene_backed_candidate", 0)),
        "history_family_diagnostic_count": int(label_counts.get("history_family_diagnostic", 0)),
        "profile_only_candidate_count": int(label_counts.get("profile_only_candidate", 0)),
        "denominator_imbalanced_count": int(label_counts.get("denominator_imbalanced", 0)),
        "global_or_scene_blocker_count": int(label_counts.get("global_or_scene_blocker", 0)),
        "low_sample_or_unresolved_count": int(label_counts.get("low_sample_or_unresolved", 0)),
        "invalid_for_ranking_count": int(label_counts.get("invalid_for_ranking", 0)),
        "ranking_admissible_count": ranking_admissible_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "slice_validity": str(output / "slice_validity.csv"),
            "scene_backed_candidates": str(output / "scene_backed_candidates.csv"),
            "history_family_diagnostic_candidates": str(output / "history_family_diagnostic_candidates.csv"),
            "profile_only_candidates": str(output / "profile_only_candidates.csv"),
            "denominator_imbalanced_slices": str(output / "denominator_imbalanced_slices.csv"),
            "global_or_scene_blockers": str(output / "global_or_scene_blockers.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary_payload)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2215-paper-route-current-sim-support-slice-validity-audit-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary_payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-support", type=Path, default=DEFAULT_GROUP_SUPPORT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_validity_audit(
        group_support=args.group_support,
        summary=args.summary,
        episode_rows=args.episode_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_group_count={summary['input_group_count']}")
    print(f"scene_backed_candidate_count={summary['scene_backed_candidate_count']}")
    print(f"profile_only_candidate_count={summary['profile_only_candidate_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
