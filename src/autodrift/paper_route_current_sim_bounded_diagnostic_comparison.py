"""No-rerun bounded diagnostic comparison for scene-backed current-sim slices."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_EPISODE_ROWS = Path("runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv")
DEFAULT_SCENE_BACKED_CANDIDATES = Path(
    "runs/m2215_paper_route_current_sim_support_slice_validity_audit/scene_backed_candidates.csv"
)
DEFAULT_VALIDITY_SUMMARY = Path("runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison")
DEFAULT_NEXT_BLOCKER = "m2219-paper-route-current-sim-bounded-diagnostic-comparison-branch-synthesis"
SUMMARY_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "diagnostic_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "profile_count",
    "history_representation_count",
    "profiles_with_success_ge_8",
    "max_profile_success_share",
    "max_history_success_share",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "controller_family_ranking_claim_made",
]
MATRIX_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "matrix_axis",
    "matrix_value",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "controller_family_ranking_claim_made",
]
PROFILE_HISTORY_FIELDNAMES = [
    "candidate_id",
    "group_key",
    "group_value",
    "profile_name",
    "history_representation",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "controller_family_ranking_claim_made",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


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


def _aggregate_counts(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _outcome_counts(rows)
    episode_count = len(rows)
    success_count = int(counts.get("success", 0))
    collision_count = int(counts.get("collision", 0))
    offtrack_count = int(counts.get("offtrack", 0))
    return {
        "episode_count": episode_count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_count": offtrack_count,
        "success_rate": _rate(success_count, episode_count),
        "collision_rate": _rate(collision_count, episode_count),
        "offtrack_rate": _rate(offtrack_count, episode_count),
    }


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


def _success_counts_by(rows: list[Mapping[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        if str(row.get("outcome_bucket", "")).strip() == "success_obstacle_pass" or _bool(row.get("success")):
            counter[str(row.get(key, "")).strip()] += 1
    return counter


def diagnostic_label(rows: list[Mapping[str, Any]]) -> str:
    counts = _aggregate_counts(rows)
    profile_success = _success_counts_by(rows, "profile_name")
    history_success = _success_counts_by(rows, "history_representation")
    success_count = int(counts["success_count"])
    max_profile_share = max(profile_success.values(), default=0) / success_count if success_count else 0.0
    max_history_share = max(history_success.values(), default=0) / success_count if success_count else 0.0
    profiles_with_success_ge_8 = sum(1 for value in profile_success.values() if value >= 8)
    if (
        counts["episode_count"] >= 64
        and success_count >= 24
        and profiles_with_success_ge_8 >= 2
        and counts["offtrack_rate"] <= 0.80
    ):
        return "multi_profile_diagnostic_support"
    if counts["episode_count"] >= 64 and success_count >= 24 and max_profile_share >= 0.75:
        return "profile_concentrated_support"
    if counts["episode_count"] >= 64 and success_count >= 24 and max_history_share >= 0.75:
        return "history_family_concentrated_support"
    if counts["offtrack_rate"] >= 0.75:
        return "offtrack_dominated_diagnostic"
    if success_count < 24:
        return "low_support_diagnostic"
    return "mixed_diagnostic"


def _matrix_rows(
    *,
    candidate_id: str,
    group_key: str,
    group_value: str,
    rows: list[Mapping[str, Any]],
    axis: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    values = sorted({str(row.get(axis, "")).strip() for row in rows})
    for value in values:
        group = [row for row in rows if str(row.get(axis, "")).strip() == value]
        output.append(
            {
                "candidate_id": candidate_id,
                "group_key": group_key,
                "group_value": group_value,
                "matrix_axis": axis,
                "matrix_value": value,
                **_aggregate_counts(group),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "controller_family_ranking_claim_made": False,
            }
        )
    return output


def _profile_history_rows(
    *,
    candidate_id: str,
    group_key: str,
    group_value: str,
    rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    keys = sorted({(str(row.get("profile_name", "")).strip(), str(row.get("history_representation", "")).strip()) for row in rows})
    for profile_name, history_representation in keys:
        group = [
            row
            for row in rows
            if str(row.get("profile_name", "")).strip() == profile_name
            and str(row.get("history_representation", "")).strip() == history_representation
        ]
        output.append(
            {
                "candidate_id": candidate_id,
                "group_key": group_key,
                "group_value": group_value,
                "profile_name": profile_name,
                "history_representation": history_representation,
                **_aggregate_counts(group),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "controller_family_ranking_claim_made": False,
            }
        )
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "bounded_diagnostic_comparison", "admissible": True, "reason": "M2218 writes diagnostic tables only"},
        {"claim": "measured_execution_rerun", "admissible": False, "reason": "M2218 does not execute policies"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2218 forces ranking_admissible false"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2218 does not select a controller"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2218 is not a verdict"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2218 is public no-rerun diagnostics"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2218 runs no history intervention"},
    ]


def run_bounded_diagnostic_comparison(
    *,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    scene_backed_candidates: Path | str = DEFAULT_SCENE_BACKED_CANDIDATES,
    validity_summary: Path | str = DEFAULT_VALIDITY_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episodes = read_csv_rows(episode_rows)
    candidates = read_csv_rows(scene_backed_candidates)
    parent_summary = read_json(validity_summary)
    candidate_summary_rows: list[dict[str, Any]] = []
    profile_matrix_rows: list[dict[str, Any]] = []
    history_matrix_rows: list[dict[str, Any]] = []
    profile_history_rows: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates):
        group_key = str(candidate.get("group_key", "")).strip()
        group_value = str(candidate.get("group_value", "")).strip()
        candidate_id = f"scene_candidate_{index:03d}"
        filters = parse_group_filter(group_value)
        matching = [row for row in episodes if _matches(row, filters)]
        counts = _aggregate_counts(matching)
        profile_success = _success_counts_by(matching, "profile_name")
        history_success = _success_counts_by(matching, "history_representation")
        success_count = int(counts["success_count"])
        max_profile_share = max(profile_success.values(), default=0) / success_count if success_count else 0.0
        max_history_share = max(history_success.values(), default=0) / success_count if success_count else 0.0
        candidate_summary_rows.append(
            {
                "candidate_id": candidate_id,
                "group_key": group_key,
                "group_value": group_value,
                "diagnostic_label": diagnostic_label(matching),
                **counts,
                "profile_count": len({str(row.get("profile_name", "")).strip() for row in matching}),
                "history_representation_count": len(
                    {str(row.get("history_representation", "")).strip() for row in matching}
                ),
                "profiles_with_success_ge_8": sum(1 for value in profile_success.values() if value >= 8),
                "max_profile_success_share": max_profile_share,
                "max_history_success_share": max_history_share,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "controller_family_ranking_claim_made": False,
            }
        )
        profile_matrix_rows.extend(
            _matrix_rows(
                candidate_id=candidate_id,
                group_key=group_key,
                group_value=group_value,
                rows=matching,
                axis="profile_name",
            )
        )
        history_matrix_rows.extend(
            _matrix_rows(
                candidate_id=candidate_id,
                group_key=group_key,
                group_value=group_value,
                rows=matching,
                axis="history_representation",
            )
        )
        profile_history_rows.extend(
            _profile_history_rows(
                candidate_id=candidate_id,
                group_key=group_key,
                group_value=group_value,
                rows=matching,
            )
        )

    diagnostic_counts = Counter(str(row["diagnostic_label"]) for row in candidate_summary_rows)
    ranking_admissible_count = sum(1 for row in candidate_summary_rows if bool(row["ranking_admissible"]))
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
        "current_sim_bounded_diagnostic_comparison_pass"
        if candidates and ranking_admissible_count == 0 and not winner_selected and guardrail_violation_count == 0
        else "current_sim_bounded_diagnostic_comparison_fail"
    )

    write_csv_rows(output / "scene_candidate_summary.csv", candidate_summary_rows, fieldnames=SUMMARY_FIELDNAMES)
    write_csv_rows(output / "scene_candidate_profile_matrix.csv", profile_matrix_rows, fieldnames=MATRIX_FIELDNAMES)
    write_csv_rows(output / "scene_candidate_history_matrix.csv", history_matrix_rows, fieldnames=MATRIX_FIELDNAMES)
    write_csv_rows(
        output / "scene_candidate_profile_history_matrix.csv",
        profile_history_rows,
        fieldnames=PROFILE_HISTORY_FIELDNAMES,
    )
    write_csv_rows(output / "diagnostic_claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)
    summary_payload = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "episode_rows": str(episode_rows),
        "scene_backed_candidates": str(scene_backed_candidates),
        "validity_summary": str(validity_summary),
        "parent_result_class": parent_summary.get("result_class"),
        "parent_scene_backed_candidate_count": int(parent_summary.get("scene_backed_candidate_count", 0)),
        "episode_row_count": len(episodes),
        "scene_candidate_count": len(candidates),
        "diagnostic_row_count": len(candidate_summary_rows),
        "diagnostic_label_counts": dict(sorted(diagnostic_counts.items())),
        "multi_profile_diagnostic_support_count": int(diagnostic_counts.get("multi_profile_diagnostic_support", 0)),
        "profile_concentrated_support_count": int(diagnostic_counts.get("profile_concentrated_support", 0)),
        "history_family_concentrated_support_count": int(
            diagnostic_counts.get("history_family_concentrated_support", 0)
        ),
        "offtrack_dominated_diagnostic_count": int(diagnostic_counts.get("offtrack_dominated_diagnostic", 0)),
        "low_support_diagnostic_count": int(diagnostic_counts.get("low_support_diagnostic", 0)),
        "mixed_diagnostic_count": int(diagnostic_counts.get("mixed_diagnostic", 0)),
        "profile_matrix_row_count": len(profile_matrix_rows),
        "history_matrix_row_count": len(history_matrix_rows),
        "profile_history_matrix_row_count": len(profile_history_rows),
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
            "scene_candidate_summary": str(output / "scene_candidate_summary.csv"),
            "scene_candidate_profile_matrix": str(output / "scene_candidate_profile_matrix.csv"),
            "scene_candidate_history_matrix": str(output / "scene_candidate_history_matrix.csv"),
            "scene_candidate_profile_history_matrix": str(output / "scene_candidate_profile_history_matrix.csv"),
            "diagnostic_claim_boundary": str(output / "diagnostic_claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary_payload)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2218-paper-route-current-sim-bounded-diagnostic-comparison-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary_payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--scene-backed-candidates", type=Path, default=DEFAULT_SCENE_BACKED_CANDIDATES)
    parser.add_argument("--validity-summary", type=Path, default=DEFAULT_VALIDITY_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_bounded_diagnostic_comparison(
        episode_rows=args.episode_rows,
        scene_backed_candidates=args.scene_backed_candidates,
        validity_summary=args.validity_summary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scene_candidate_count={summary['scene_candidate_count']}")
    print(f"multi_profile_diagnostic_support_count={summary['multi_profile_diagnostic_support_count']}")
    print(f"profile_concentrated_support_count={summary['profile_concentrated_support_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"winner_selected={summary['winner_selected']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
