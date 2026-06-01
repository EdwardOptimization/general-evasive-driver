"""Artifact-only target/guardrail slice deltas for guarded repair."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_BASELINE_EPISODE_ROWS = Path("runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv")
DEFAULT_CANDIDATE_EPISODE_ROWS = Path(
    "runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/episode_rows.csv"
)
DEFAULT_REPAIR_GATE_SPEC = Path(
    "runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2310-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-result-audit"

OFFTRACK_OUTCOME = "off_track_noncollision_noncompletion"
COLLISION_OUTCOME = "collision_failure"
OFFTRACK_TERMINATION = "off_track"
COLLISION_TERMINATION = "obstacle_collision"
GROUP_COUNT_AXES = {"outcome_bucket", "termination_reason"}

SLICE_FIELDNAMES = [
    "slice_role",
    "metric_name",
    "axis",
    "group_key",
    "baseline_total",
    "candidate_total",
    "baseline_metric_count",
    "candidate_metric_count",
    "metric_delta",
    "nonincrease_pass",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _slice_count(rows: Sequence[Mapping[str, Any]], *, axis: str, group_key: str, metric_name: str) -> tuple[int, int]:
    total = 0
    metric_count = 0
    for row in rows:
        if str(row.get(axis, "")) != group_key:
            continue
        total += 1
        if axis in GROUP_COUNT_AXES:
            metric_count += 1
        elif metric_name == "offtrack_count":
            metric_count += int(str(row.get("outcome_bucket", "")) == OFFTRACK_OUTCOME)
        elif metric_name == "collision_count":
            metric_count += int(_truthy(row.get("collision", False)) or str(row.get("outcome_bucket", "")) == COLLISION_OUTCOME)
    return total, metric_count


def _slice_delta_row(
    *,
    slice_role: str,
    metric_name: str,
    axis: str,
    group_key: str,
    baseline_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    baseline_total, baseline_metric = _slice_count(
        baseline_rows,
        axis=axis,
        group_key=group_key,
        metric_name=metric_name,
    )
    candidate_total, candidate_metric = _slice_count(
        candidate_rows,
        axis=axis,
        group_key=group_key,
        metric_name=metric_name,
    )
    delta = candidate_metric - baseline_metric
    return {
        "slice_role": slice_role,
        "metric_name": metric_name,
        "axis": axis,
        "group_key": group_key,
        "baseline_total": baseline_total,
        "candidate_total": candidate_total,
        "baseline_metric_count": baseline_metric,
        "candidate_metric_count": candidate_metric,
        "metric_delta": delta,
        "nonincrease_pass": delta <= 0,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _policy_rows(
    *,
    spec: Mapping[str, Any],
    baseline_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in spec.get("offtrack_target_policy", {}).get("target_slices", []):
        rows.append(
            _slice_delta_row(
                slice_role="offtrack_target",
                metric_name="offtrack_count",
                axis=str(item.get("axis", "")),
                group_key=str(item.get("group_key", "")),
                baseline_rows=baseline_rows,
                candidate_rows=candidate_rows,
            )
        )
    for item in spec.get("collision_guardrail_policy", {}).get("guardrail_slices", []):
        rows.append(
            _slice_delta_row(
                slice_role="collision_guardrail",
                metric_name="collision_count",
                axis=str(item.get("axis", "")),
                group_key=str(item.get("group_key", "")),
                baseline_rows=baseline_rows,
                candidate_rows=candidate_rows,
            )
        )
    return rows


def _global_count(rows: Sequence[Mapping[str, Any]], metric_name: str) -> int:
    if metric_name == "offtrack_count":
        return sum(1 for row in rows if str(row.get("outcome_bucket", "")) == OFFTRACK_OUTCOME)
    if metric_name == "collision_count":
        return sum(1 for row in rows if _truthy(row.get("collision", False)) or str(row.get("outcome_bucket", "")) == COLLISION_OUTCOME)
    raise ValueError(f"unsupported metric_name: {metric_name}")


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "target_guardrail_slice_diagnosis",
            "admissible": True,
            "reason": "diagnosis consumes existing measured episode rows without rerun",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "profile axes and deltas remain diagnostic-only",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "slice diagnosis is public repair-route evidence, not a paper-level statistical result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "diagnosis does not run the comparison protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "diagnosis does not test history necessity",
        },
    ]


def run_slice_diagnosis(
    *,
    baseline_episode_rows: Path | str = DEFAULT_BASELINE_EPISODE_ROWS,
    candidate_episode_rows: Path | str = DEFAULT_CANDIDATE_EPISODE_ROWS,
    repair_gate_spec: Path | str = DEFAULT_REPAIR_GATE_SPEC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    baseline_rows = read_csv_rows(baseline_episode_rows)
    candidate_rows = read_csv_rows(candidate_episode_rows)
    spec = read_json(repair_gate_spec)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    slice_rows = _policy_rows(spec=spec, baseline_rows=baseline_rows, candidate_rows=candidate_rows)
    offtrack_rows = [row for row in slice_rows if row["slice_role"] == "offtrack_target"]
    collision_rows = [row for row in slice_rows if row["slice_role"] == "collision_guardrail"]

    baseline_offtrack = _global_count(baseline_rows, "offtrack_count")
    candidate_offtrack = _global_count(candidate_rows, "offtrack_count")
    baseline_collision = _global_count(baseline_rows, "collision_count")
    candidate_collision = _global_count(candidate_rows, "collision_count")

    offtrack_nonincrease_count = sum(1 for row in offtrack_rows if bool(row["nonincrease_pass"]))
    collision_nonincrease_count = sum(1 for row in collision_rows if bool(row["nonincrease_pass"]))
    offtrack_target_policy_pass = bool(offtrack_rows and offtrack_nonincrease_count == len(offtrack_rows))
    collision_guardrail_policy_pass = bool(collision_rows and collision_nonincrease_count == len(collision_rows))
    global_offtrack_delta = candidate_offtrack - baseline_offtrack
    global_collision_delta = candidate_collision - baseline_collision
    global_offtrack_policy_pass = global_offtrack_delta < 0 if spec.get("offtrack_target_policy", {}).get("reduce_global_offtrack_count") else True
    global_collision_policy_pass = global_collision_delta <= 0 if spec.get("collision_guardrail_policy", {}).get("do_not_increase_global_collision_count") else True
    repair_gate_pass = bool(
        global_offtrack_policy_pass
        and global_collision_policy_pass
        and offtrack_target_policy_pass
        and collision_guardrail_policy_pass
    )

    guardrail_flags = {
        "private_holdout_used": False,
        "training_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_scenario_task_family_guarded_repair_slice_diagnosis_pass"
        if (
            len(offtrack_rows) == int(spec.get("offtrack_target_policy", {}).get("target_slice_count", -1))
            and len(collision_rows) == int(spec.get("collision_guardrail_policy", {}).get("guardrail_slice_count", -1))
            and baseline_rows
            and candidate_rows
            and guardrail_violation_count == 0
        )
        else "current_sim_scenario_task_family_guarded_repair_slice_diagnosis_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "baseline_episode_rows": str(baseline_episode_rows),
        "candidate_episode_rows": str(candidate_episode_rows),
        "repair_gate_spec": str(repair_gate_spec),
        "output_dir": str(output),
        "next_blocker": str(next_blocker),
        "input_episode_count_baseline": len(baseline_rows),
        "input_episode_count_candidate": len(candidate_rows),
        "offtrack_target_slice_count": len(offtrack_rows),
        "collision_guardrail_slice_count": len(collision_rows),
        "slice_delta_row_count": len(slice_rows),
        "offtrack_target_nonincrease_count": offtrack_nonincrease_count,
        "offtrack_target_increase_count": len(offtrack_rows) - offtrack_nonincrease_count,
        "collision_guardrail_nonincrease_count": collision_nonincrease_count,
        "collision_guardrail_increase_count": len(collision_rows) - collision_nonincrease_count,
        "baseline_global_offtrack_count": baseline_offtrack,
        "candidate_global_offtrack_count": candidate_offtrack,
        "global_offtrack_delta": global_offtrack_delta,
        "baseline_global_collision_count": baseline_collision,
        "candidate_global_collision_count": candidate_collision,
        "global_collision_delta": global_collision_delta,
        "global_offtrack_policy_pass": global_offtrack_policy_pass,
        "global_collision_policy_pass": global_collision_policy_pass,
        "offtrack_target_policy_pass": offtrack_target_policy_pass,
        "collision_guardrail_policy_pass": collision_guardrail_policy_pass,
        "repair_gate_pass": repair_gate_pass,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "diagnostic_only": True,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "slice_delta_rows": str(output / "slice_delta_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
    }
    write_csv_rows(output / "slice_delta_rows.csv", slice_rows, fieldnames=SLICE_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows())
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2309-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize guarded-repair target/guardrail slice deltas.")
    parser.add_argument("--baseline-episode-rows", type=Path, default=DEFAULT_BASELINE_EPISODE_ROWS)
    parser.add_argument("--candidate-episode-rows", type=Path, default=DEFAULT_CANDIDATE_EPISODE_ROWS)
    parser.add_argument("--repair-gate-spec", type=Path, default=DEFAULT_REPAIR_GATE_SPEC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", type=str, default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = run_slice_diagnosis(
        baseline_episode_rows=args.baseline_episode_rows,
        candidate_episode_rows=args.candidate_episode_rows,
        repair_gate_spec=args.repair_gate_spec,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"slice_delta_rows={Path(args.output_dir) / 'slice_delta_rows.csv'}")
    print(f"result_class={summary['result_class']}")
    print(f"offtrack_target_slice_count={summary['offtrack_target_slice_count']}")
    print(f"collision_guardrail_slice_count={summary['collision_guardrail_slice_count']}")
    print(f"repair_gate_pass={summary['repair_gate_pass']}")
    raise SystemExit(0 if str(summary["result_class"]).endswith("_pass") else 1)


if __name__ == "__main__":
    main()
