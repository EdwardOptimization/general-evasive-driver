"""No-rerun outcome localization for the current-sim offtrack-support panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_EPISODE_ROWS = Path("runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv")
DEFAULT_SUMMARY = Path("runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization")
DEFAULT_NEXT_BLOCKER = "m2213-paper-route-current-sim-offtrack-support-outcome-localization-branch-synthesis"
GROUP_KEYS: tuple[tuple[str, ...], ...] = (
    ("overall",),
    ("task_family",),
    ("source_family_template",),
    ("capability_pair",),
    ("profile_name",),
    ("history_representation",),
    ("profile_level",),
    ("task_family", "history_representation"),
    ("task_family", "profile_name"),
    ("source_family_template", "history_representation"),
    ("source_family_template", "profile_name"),
    ("capability_pair", "history_representation"),
    ("capability_pair", "profile_name"),
)
GROUP_FIELDNAMES = [
    "group_key",
    "group_value",
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
    "support_label",
    "comparison_ready_candidate",
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


def support_label(*, episode_count: int, success_count: int, collision_count: int, offtrack_count: int) -> str:
    success_rate = _rate(success_count, episode_count)
    collision_rate = _rate(collision_count, episode_count)
    offtrack_rate = _rate(offtrack_count, episode_count)
    if episode_count < 32:
        return "low_sample_count"
    if (
        episode_count >= 64
        and success_count >= 24
        and success_rate >= 0.25
        and offtrack_rate <= 0.60
        and collision_rate <= 0.20
    ):
        return "comparison_ready_candidate"
    if episode_count >= 64 and success_count >= 8 and success_rate >= 0.10 and offtrack_rate <= 0.80:
        return "candidate_support"
    if offtrack_rate >= 0.75 or offtrack_count >= 3 * max(success_count, 1):
        return "offtrack_dominated"
    if collision_rate >= 0.25:
        return "collision_dominated"
    if success_count < 8 or success_rate < 0.10:
        return "low_success_support"
    return "mixed_unresolved"


def _group_value(row: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    if keys == ("overall",):
        return "overall"
    return "|".join(f"{key}={str(row.get(key, '')).strip()}" for key in keys)


def _aggregate_group(*, group_key: str, group_value: str, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _outcome_counts(rows)
    episode_count = len(rows)
    success_count = int(counts.get("success", 0))
    collision_count = int(counts.get("collision", 0))
    offtrack_count = int(counts.get("offtrack", 0))
    label = support_label(
        episode_count=episode_count,
        success_count=success_count,
        collision_count=collision_count,
        offtrack_count=offtrack_count,
    )
    return {
        "group_key": group_key,
        "group_value": group_value,
        "episode_count": episode_count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_count": offtrack_count,
        "success_rate": _rate(success_count, episode_count),
        "collision_rate": _rate(collision_count, episode_count),
        "offtrack_rate": _rate(offtrack_count, episode_count),
        "profile_count": len({str(row.get("profile_name", "")) for row in rows}),
        "history_representation_count": len({str(row.get("history_representation", "")) for row in rows}),
        "task_source_count": len({str(row.get("task_source_id", "")) for row in rows}),
        "support_label": label,
        "comparison_ready_candidate": label == "comparison_ready_candidate",
        "controller_family_ranking_claim_made": False,
    }


def _group_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for keys in GROUP_KEYS:
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        group_key = " x ".join(keys)
        for row in rows:
            grouped.setdefault(_group_value(row, keys), []).append(row)
        for value, group in sorted(grouped.items()):
            output.append(_aggregate_group(group_key=group_key, group_value=value, rows=group))
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "outcome_localization", "admissible": True, "reason": "M2212 uses no-rerun aggregate analysis"},
        {"claim": "measured_execution_rerun", "admissible": False, "reason": "M2212 does not execute policies"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2212 labels support slices only"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2212 does not select a controller"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2212 is not a comparison verdict"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2212 is public no-rerun localization"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2212 runs no history intervention"},
    ]


def run_outcome_localization(
    *,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    summary: Path | str = DEFAULT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = read_csv_rows(episode_rows)
    parent_summary = read_json(summary)
    grouped_rows = _group_rows(rows)
    label_counts = Counter(str(row["support_label"]) for row in grouped_rows)
    overall = next(row for row in grouped_rows if row["group_key"] == "overall")

    comparison_ready = [row for row in grouped_rows if row["support_label"] == "comparison_ready_candidate"]
    offtrack_dominated = [row for row in grouped_rows if row["support_label"] == "offtrack_dominated"]
    collision_dominated = [row for row in grouped_rows if row["support_label"] == "collision_dominated"]
    low_success = [row for row in grouped_rows if row["support_label"] == "low_success_support"]

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
        "current_sim_offtrack_support_outcome_localization_pass"
        if rows and guardrail_violation_count == 0
        else "current_sim_offtrack_support_outcome_localization_fail"
    )

    write_csv_rows(output / "group_outcome_support.csv", grouped_rows, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(output / "comparison_ready_candidate_slices.csv", comparison_ready, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(output / "offtrack_dominated_slices.csv", offtrack_dominated, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(output / "collision_dominated_slices.csv", collision_dominated, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(output / "low_success_support_slices.csv", low_success, fieldnames=GROUP_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary_payload = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "episode_rows": str(episode_rows),
        "parent_summary": str(summary),
        "parent_result_class": parent_summary.get("result_class"),
        "input_episode_count": len(rows),
        "parent_episode_count": int(parent_summary.get("episode_count", 0)),
        "overall_success_rate": overall["success_rate"],
        "overall_collision_rate": overall["collision_rate"],
        "overall_offtrack_rate": overall["offtrack_rate"],
        "group_row_count": len(grouped_rows),
        "support_label_counts": dict(sorted(label_counts.items())),
        "comparison_ready_candidate_count": int(label_counts.get("comparison_ready_candidate", 0)),
        "candidate_support_count": int(label_counts.get("candidate_support", 0)),
        "offtrack_dominated_count": int(label_counts.get("offtrack_dominated", 0)),
        "collision_dominated_count": int(label_counts.get("collision_dominated", 0)),
        "low_success_support_count": int(label_counts.get("low_success_support", 0)),
        "low_sample_count": int(label_counts.get("low_sample_count", 0)),
        "mixed_unresolved_count": int(label_counts.get("mixed_unresolved", 0)),
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
            "group_outcome_support": str(output / "group_outcome_support.csv"),
            "comparison_ready_candidate_slices": str(output / "comparison_ready_candidate_slices.csv"),
            "offtrack_dominated_slices": str(output / "offtrack_dominated_slices.csv"),
            "collision_dominated_slices": str(output / "collision_dominated_slices.csv"),
            "low_success_support_slices": str(output / "low_success_support_slices.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary_payload)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2212-paper-route-current-sim-offtrack-support-outcome-localization-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary_payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_outcome_localization(
        episode_rows=args.episode_rows,
        summary=args.summary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_episode_count={summary['input_episode_count']}")
    print(f"comparison_ready_candidate_count={summary['comparison_ready_candidate_count']}")
    print(f"offtrack_dominated_count={summary['offtrack_dominated_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
