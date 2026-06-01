"""Artifact-only role-success semantics repair and rescore for M2318."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.paper_route_current_sim_scenario_task_family_feasibility_calibration import (
    CLAIM_FIELDNAMES,
    DEFAULT_SUPPORT_POLICIES,
    EPISODE_FIELDNAMES,
    ROLE_SUPPORT_FIELDNAMES,
    SCENARIO_SUPPORT_FIELDNAMES,
    SUPPORT_AGGREGATE_FIELDNAMES,
    _count_by,
    read_csv_rows,
    role_support_summary_rows,
    scenario_support_label_rows,
    support_aggregate_rows,
)
from autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics import (
    R0_STABLE_AVOIDABLE,
    annotate_role_success,
    bool_value,
    is_r0_safe_stop_success,
)


DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_EPISODE_ROWS = Path("runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv")
DEFAULT_BASELINE_SCENARIO_SUPPORT_LABELS = Path(
    "runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair")
DEFAULT_NEXT_BLOCKER = "m2319-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-result-audit"
TARGET_EPISODE_COUNT = 1080
TARGET_SCENARIO_SPEC_COUNT = 72

CLAIM_BOUNDARY_FIELDNAMES = ["claim", "admissible", "reason"]


def load_scenario_specs(config_path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(config_path)
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return [dict(spec) for spec in specs]


def infer_seed_repeats(rows: Sequence[Mapping[str, Any]]) -> int:
    per_cell: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = (str(row.get("scenario_spec_id", "")), str(row.get("support_policy_name", "")))
        if key[0] and key[1]:
            per_cell[key] += 1
    return max(per_cell.values()) if per_cell else 0


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "role_success_semantics_repair_rescore_completed",
            "admissible": True,
            "reason": "M2318 rescored existing M2313 artifacts with bounded R0 safe-stop semantics",
        },
        {
            "claim": "environment_rollout_or_training",
            "admissible": False,
            "reason": "M2318 does not run environment reset, rollout, policy action, training, replay, or PPO",
        },
        {
            "claim": "global_safe_stop_success",
            "admissible": False,
            "reason": "safe-stop success is role-bounded to R0_stable_avoidable",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "support policies remain diagnostic support bounds and are not ranked",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2318 is metric semantics repair, not a paper-level result",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2318 runs no history intervention",
        },
    ]


def _role_summary_row(rows: Sequence[Mapping[str, Any]], role_family: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("role_family", "")) == role_family:
            return dict(row)
    return {}


def _support_label_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("support_label", "")) for row in rows).items()))


def _count_role_success(rows: Sequence[Mapping[str, Any]], *, role_family: str, support_policy_name: str | None = None) -> int:
    count = 0
    for row in rows:
        if str(row.get("role_family", "")) != role_family:
            continue
        if support_policy_name is not None and str(row.get("support_policy_name", "")) != support_policy_name:
            continue
        if bool_value(row.get("role_success")):
            count += 1
    return count


def rescore_episode_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [annotate_role_success(row) for row in rows]


def run_role_success_semantics_repair(
    *,
    config: Path | str = DEFAULT_CONFIG,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    baseline_scenario_support_labels: Path | str = DEFAULT_BASELINE_SCENARIO_SUPPORT_LABELS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    target_scenario_spec_count: int = TARGET_SCENARIO_SPEC_COUNT,
    target_support_policy_count: int = len(DEFAULT_SUPPORT_POLICIES),
    target_r0_support_clear_count: int = 12,
    target_r0_aeb_role_success_count: int = 60,
    target_r0_safe_stop_success_count: int = 60,
    min_support_clear_delta: int = 12,
    max_metric_conflict_delta: int = -12,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_scenario_specs(config)
    input_rows = read_csv_rows(episode_rows)
    baseline_labels = read_csv_rows(baseline_scenario_support_labels)
    rescored_rows = rescore_episode_rows(input_rows)
    seed_repeats = infer_seed_repeats(rescored_rows)
    scenario_labels = scenario_support_label_rows(
        rescored_rows,
        scenario_specs=specs,
        seed_repeats=int(seed_repeats),
    )
    role_summary = role_support_summary_rows(scenario_labels)
    aggregates = support_aggregate_rows(rescored_rows)
    baseline_counts = _support_label_counts(baseline_labels)
    repaired_counts = _support_label_counts(scenario_labels)
    r0_role = _role_summary_row(role_summary, R0_STABLE_AVOIDABLE)
    r0_safe_stop_success_count = sum(1 for row in rescored_rows if is_r0_safe_stop_success(row))
    r0_aeb_role_success_count = _count_role_success(
        rescored_rows,
        role_family=R0_STABLE_AVOIDABLE,
        support_policy_name="aeb",
    )
    non_r0_safe_stop_success_count = sum(
        1
        for row in rescored_rows
        if str(row.get("role_family", "")) != R0_STABLE_AVOIDABLE
        and str(row.get("role_success_reason", "")) == "r0_safe_stop_success"
    )
    r0_support_clear_count = int(r0_role.get("support_clear_count") or 0)
    r0_metric_conflict_count = int(r0_role.get("metric_conflict_count") or 0)
    support_clear_delta = repaired_counts.get("support_clear", 0) - baseline_counts.get("support_clear", 0)
    metric_conflict_delta = repaired_counts.get("metric_conflict", 0) - baseline_counts.get("metric_conflict", 0)

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
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(bool(value) for value in guardrail_flags.values())
    scenario_spec_count = len({str(row.get("scenario_spec_id", "")) for row in rescored_rows})
    support_policy_count = len({str(row.get("support_policy_name", "")) for row in rescored_rows})
    pass_gate = (
        len(input_rows) == int(target_episode_count)
        and len(rescored_rows) == int(target_episode_count)
        and scenario_spec_count == int(target_scenario_spec_count)
        and support_policy_count == int(target_support_policy_count)
        and r0_support_clear_count == int(target_r0_support_clear_count)
        and r0_metric_conflict_count == 0
        and r0_aeb_role_success_count >= int(target_r0_aeb_role_success_count)
        and r0_safe_stop_success_count >= int(target_r0_safe_stop_success_count)
        and non_r0_safe_stop_success_count == 0
        and support_clear_delta >= int(min_support_clear_delta)
        and metric_conflict_delta <= int(max_metric_conflict_delta)
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "episode_rows_rescored.csv", rescored_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(output / "support_aggregate_rows_rescored.csv", aggregates, fieldnames=SUPPORT_AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "scenario_support_labels_rescored.csv", scenario_labels, fieldnames=SCENARIO_SUPPORT_FIELDNAMES)
    write_csv_rows(output / "role_support_summary_rescored.csv", role_summary, fieldnames=ROLE_SUPPORT_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    artifacts = {
        "summary": str(output / "summary.json"),
        "episode_rows_rescored": str(output / "episode_rows_rescored.csv"),
        "support_aggregate_rows_rescored": str(output / "support_aggregate_rows_rescored.csv"),
        "scenario_support_labels_rescored": str(output / "scenario_support_labels_rescored.csv"),
        "role_support_summary_rescored": str(output / "role_support_summary_rescored.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
        "run_state": str(output / "run_state.json"),
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_role_success_semantics_repair_pass"
            if pass_gate
            else "current_sim_scenario_task_family_role_success_semantics_repair_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "input_episode_count": len(input_rows),
        "rescored_episode_count": len(rescored_rows),
        "target_episode_count": int(target_episode_count),
        "scenario_spec_count": scenario_spec_count,
        "target_scenario_spec_count": int(target_scenario_spec_count),
        "support_policy_count": support_policy_count,
        "target_support_policy_count": int(target_support_policy_count),
        "seed_repeats": int(seed_repeats),
        "baseline_support_label_counts": baseline_counts,
        "repaired_support_label_counts": repaired_counts,
        "support_clear_delta": int(support_clear_delta),
        "min_support_clear_delta": int(min_support_clear_delta),
        "metric_conflict_delta": int(metric_conflict_delta),
        "max_metric_conflict_delta": int(max_metric_conflict_delta),
        "r0_support_clear_count": int(r0_support_clear_count),
        "target_r0_support_clear_count": int(target_r0_support_clear_count),
        "r0_metric_conflict_count": int(r0_metric_conflict_count),
        "r0_safe_stop_success_count": int(r0_safe_stop_success_count),
        "target_r0_safe_stop_success_count": int(target_r0_safe_stop_success_count),
        "r0_aeb_role_success_count": int(r0_aeb_role_success_count),
        "target_r0_aeb_role_success_count": int(target_r0_aeb_role_success_count),
        "non_r0_safe_stop_success_count": int(non_r0_safe_stop_success_count),
        "global_role_success_count": sum(1 for row in rescored_rows if bool_value(row.get("role_success"))),
        "role_support_summary_counts": _count_by(role_summary, "role_family"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": int(guardrail_violation_count),
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only": True,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "input_episode_count": len(input_rows),
            "rescored_episode_count": len(rescored_rows),
            "complete": bool(pass_gate),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--baseline-scenario-support-labels", type=Path, default=DEFAULT_BASELINE_SCENARIO_SUPPORT_LABELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--target-scenario-spec-count", type=int, default=TARGET_SCENARIO_SPEC_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_role_success_semantics_repair(
        config=args.config,
        episode_rows=args.episode_rows,
        baseline_scenario_support_labels=args.baseline_scenario_support_labels,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        target_scenario_spec_count=int(args.target_scenario_spec_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"r0_support_clear_count={summary['r0_support_clear_count']}")
    print(f"r0_metric_conflict_count={summary['r0_metric_conflict_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
