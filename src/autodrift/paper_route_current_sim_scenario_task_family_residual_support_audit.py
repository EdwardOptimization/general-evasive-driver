"""Artifact-only residual-support audit for repaired scenario task-family rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics import (
    bool_value,
    is_collision,
    is_offtrack,
    role_success,
)


DEFAULT_EPISODE_ROWS = Path(
    "runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv"
)
DEFAULT_SCENARIO_SUPPORT_LABELS = Path(
    "runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/scenario_support_labels_rescored.csv"
)
DEFAULT_ROLE_SUPPORT_SUMMARY = Path(
    "runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/role_support_summary_rescored.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit")
DEFAULT_NEXT_BLOCKER = "m2322-paper-route-current-sim-scenario-task-family-residual-support-audit-result-audit"

SCENARIO_FIELDS = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "sampled_obstacle_label",
    "allowed_labels_metadata_only",
    "same_scene_group_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "initial_speed_mps",
    "track_radius_m",
    "track_width_m",
    "actor_contract_id",
]
SUPPORT_POLICIES = ("aeb", "aes", "envelope_aes")
ROUTE_LABELS = (
    "metric_semantics_audit_candidate",
    "support_policy_coverage_candidate",
    "scenario_or_support_redesign_candidate",
    "mitigation_semantics_or_support_redesign_candidate",
)
RESIDUAL_SCENARIO_FIELDNAMES = [
    *SCENARIO_FIELDS,
    "support_label",
    "support_label_reason",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "max_step_noncompletion_count",
    "other_failure_count",
    "dominant_failure_mode",
    "primary_route_label",
    "primary_route_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "aeb_success_count",
    "aeb_collision_count",
    "aeb_offtrack_count",
    "aes_success_count",
    "aes_collision_count",
    "aes_offtrack_count",
    "envelope_aes_success_count",
    "envelope_aes_collision_count",
    "envelope_aes_offtrack_count",
]
ROLE_SUMMARY_FIELDNAMES = [
    "role_family",
    "residual_scenario_count",
    "support_mixed_count",
    "support_blocked_count",
    "metric_conflict_count",
    *[f"{label}_count" for label in ROUTE_LABELS],
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
AXIS_SUMMARY_FIELDNAMES = [
    "axis",
    "group_value",
    "residual_scenario_count",
    "support_mixed_count",
    "support_blocked_count",
    "metric_conflict_count",
    *[f"{label}_count" for label in ROUTE_LABELS],
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROUTE_SUMMARY_FIELDNAMES = [
    "primary_route_label",
    "residual_scenario_count",
    "role_families",
    "support_labels",
    "dominant_failure_modes",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
SUPPORT_POLICY_SUMMARY_FIELDNAMES = [
    "support_policy_name",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "max_step_noncompletion_count",
    "other_failure_count",
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


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _failure_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        bucket = str(row.get("outcome_bucket", ""))
        if bucket == "success_obstacle_pass" or role_success(row):
            counts["success"] += 1
        elif bucket == "collision_failure" or is_collision(row):
            counts["collision"] += 1
        elif is_offtrack(row):
            counts["offtrack"] += 1
        elif bucket == "max_steps_noncompletion" or bool_value(row.get("truncated")):
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
    return dict(counts)


def _dominant_failure_mode(rows: Sequence[Mapping[str, Any]]) -> str:
    total = len(rows)
    if not total:
        return "low_support_or_incomplete"
    counts = _failure_counts(rows)
    success = counts.get("success", 0)
    if _rate(success, total) >= 2.0 / 3.0:
        return "success_supported"
    failures = max(1, total - success)
    for label, key in (
        ("collision_dominated_failure", "collision"),
        ("offtrack_dominated_failure", "offtrack"),
        ("max_step_noncompletion_dominated_failure", "max_step_noncompletion"),
    ):
        if counts.get(key, 0) / failures >= 0.5:
            return label
    return "mixed_failure"


def _scenario_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in SCENARIO_FIELDS}


def primary_route_label(row: Mapping[str, Any]) -> tuple[str, str]:
    support_label = str(row.get("support_label", ""))
    role_family = str(row.get("role_family", ""))
    if role_family == "R4_unavoidable_mitigation" and support_label in {"support_mixed", "support_blocked"}:
        return (
            "mitigation_semantics_or_support_redesign_candidate",
            "unavoidable mitigation residual needs mitigation-specific semantics or support redesign",
        )
    if support_label == "metric_conflict":
        return "metric_semantics_audit_candidate", "support policy behavior conflicts with current terminal metric"
    if support_label == "support_mixed":
        return "support_policy_coverage_candidate", "some support evidence exists but no policy reaches clear threshold"
    if support_label == "support_blocked":
        return "scenario_or_support_redesign_candidate", "no support policy reaches enough success evidence"
    return "non_residual_support_clear", "support_clear rows are excluded from residual audit"


def residual_scenario_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    scenario_support_labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_scenario: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        rows_by_scenario[str(row.get("scenario_spec_id", ""))].append(row)
    output: list[dict[str, Any]] = []
    for scenario in scenario_support_labels:
        if str(scenario.get("support_label", "")) == "support_clear":
            continue
        scenario_id = str(scenario.get("scenario_spec_id", ""))
        rows = rows_by_scenario.get(scenario_id, [])
        counts = _failure_counts(rows)
        route, reason = primary_route_label(scenario)
        row = {
            **_scenario_metadata(scenario),
            "support_label": scenario.get("support_label", ""),
            "support_label_reason": scenario.get("support_label_reason", ""),
            "episode_count": len(rows),
            "success_count": counts.get("success", 0),
            "collision_count": counts.get("collision", 0),
            "offtrack_count": counts.get("offtrack", 0),
            "max_step_noncompletion_count": counts.get("max_step_noncompletion", 0),
            "other_failure_count": counts.get("other_failure", 0),
            "dominant_failure_mode": _dominant_failure_mode(rows),
            "primary_route_label": route,
            "primary_route_reason": reason,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
        for policy_name in SUPPORT_POLICIES:
            policy_rows = [episode for episode in rows if str(episode.get("support_policy_name", "")) == policy_name]
            policy_counts = _failure_counts(policy_rows)
            row[f"{policy_name}_success_count"] = policy_counts.get("success", 0)
            row[f"{policy_name}_collision_count"] = policy_counts.get("collision", 0)
            row[f"{policy_name}_offtrack_count"] = policy_counts.get("offtrack", 0)
        output.append(row)
    return output


def _summary_row(rows: Sequence[Mapping[str, Any]], *, key: str, value: str, field: str) -> dict[str, Any]:
    label_counts = Counter(str(row.get("support_label", "")) for row in rows)
    route_counts = Counter(str(row.get("primary_route_label", "")) for row in rows)
    output = {
        field: value,
        "residual_scenario_count": len(rows),
        "support_mixed_count": label_counts.get("support_mixed", 0),
        "support_blocked_count": label_counts.get("support_blocked", 0),
        "metric_conflict_count": label_counts.get("metric_conflict", 0),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }
    if key:
        output["axis"] = key
        output["group_value"] = value
    for route in ROUTE_LABELS:
        output[f"{route}_count"] = route_counts.get(route, 0)
    return output


def residual_role_summary_rows(residual_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in residual_rows:
        grouped[str(row.get("role_family", ""))].append(row)
    return [
        _summary_row(group, key="", value=role, field="role_family")
        for role, group in sorted(grouped.items())
    ]


def residual_axis_summary_rows(residual_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    axes = (
        "role_family",
        "sampled_obstacle_label",
        "support_label",
        "hidden_dynamics_bucket",
        "obstacle_longitudinal_timing_bucket",
        "obstacle_lateral_offset_bucket",
        "primary_route_label",
        "dominant_failure_mode",
    )
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in residual_rows:
        for axis in axes:
            grouped[(axis, str(row.get(axis, "")))].append(row)
    return [
        _summary_row(group, key=axis, value=value, field="group_value")
        for (axis, value), group in sorted(grouped.items())
    ]


def residual_route_summary_rows(residual_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in residual_rows:
        grouped[str(row.get("primary_route_label", ""))].append(row)
    output: list[dict[str, Any]] = []
    for route, rows in sorted(grouped.items()):
        output.append(
            {
                "primary_route_label": route,
                "residual_scenario_count": len(rows),
                "role_families": ";".join(sorted({str(row.get("role_family", "")) for row in rows})),
                "support_labels": ";".join(sorted({str(row.get("support_label", "")) for row in rows})),
                "dominant_failure_modes": ";".join(sorted({str(row.get("dominant_failure_mode", "")) for row in rows})),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def residual_support_policy_summary_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    residual_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    residual_ids = {str(row.get("scenario_spec_id", "")) for row in residual_rows}
    output: list[dict[str, Any]] = []
    for policy_name in SUPPORT_POLICIES:
        rows = [
            row
            for row in episode_rows
            if str(row.get("scenario_spec_id", "")) in residual_ids
            and str(row.get("support_policy_name", "")) == policy_name
        ]
        counts = _failure_counts(rows)
        output.append(
            {
                "support_policy_name": policy_name,
                "episode_count": len(rows),
                "success_count": counts.get("success", 0),
                "collision_count": counts.get("collision", 0),
                "offtrack_count": counts.get("offtrack", 0),
                "max_step_noncompletion_count": counts.get("max_step_noncompletion", 0),
                "other_failure_count": counts.get("other_failure", 0),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "residual_support_audit_completed",
            "admissible": True,
            "reason": "M2321 classifies residual support rows from repaired M2318 artifacts",
        },
        {
            "claim": "environment_rollout_or_training",
            "admissible": False,
            "reason": "M2321 does not run reset, rollout, policy action, training, replay, or PPO",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "support policies remain diagnostic support bounds",
        },
        {
            "claim": "residual_support_solved",
            "admissible": False,
            "reason": "M2321 classifies residuals but does not repair them",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2321 is artifact-only support diagnosis",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2321 runs no history intervention",
        },
    ]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_residual_support_audit(
    *,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    scenario_support_labels: Path | str = DEFAULT_SCENARIO_SUPPORT_LABELS,
    role_support_summary: Path | str = DEFAULT_ROLE_SUPPORT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_scenario_count: int = 72,
    target_residual_scenario_count: int = 48,
    target_support_clear_count: int = 24,
    target_support_mixed_count: int = 26,
    target_support_blocked_count: int = 21,
    target_metric_conflict_count: int = 1,
    target_r2_r5_residual_count: int = 48,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episodes = read_csv_rows(episode_rows)
    scenario_labels = read_csv_rows(scenario_support_labels)
    role_rows = read_csv_rows(role_support_summary)
    residual_rows = residual_scenario_rows(episode_rows=episodes, scenario_support_labels=scenario_labels)
    role_summary_rows = residual_role_summary_rows(residual_rows)
    axis_summary_rows = residual_axis_summary_rows(residual_rows)
    route_summary_rows = residual_route_summary_rows(residual_rows)
    support_policy_rows = residual_support_policy_summary_rows(episode_rows=episodes, residual_rows=residual_rows)

    write_csv_rows(output / "residual_scenario_rows.csv", residual_rows, fieldnames=RESIDUAL_SCENARIO_FIELDNAMES)
    write_csv_rows(output / "residual_role_summary.csv", role_summary_rows, fieldnames=ROLE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "residual_axis_summary.csv", axis_summary_rows, fieldnames=AXIS_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "residual_route_summary.csv", route_summary_rows, fieldnames=ROUTE_SUMMARY_FIELDNAMES)
    write_csv_rows(
        output / "residual_support_policy_summary.csv",
        support_policy_rows,
        fieldnames=SUPPORT_POLICY_SUMMARY_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    support_counts = _count_by(scenario_labels, "support_label")
    residual_counts = _count_by(residual_rows, "support_label")
    route_counts = _count_by(residual_rows, "primary_route_label")
    r0_residual_count = sum(str(row.get("role_family", "")) == "R0_stable_avoidable" for row in residual_rows)
    r1_residual_count = sum(str(row.get("role_family", "")) == "R1_aeb_infeasible_stable_aes" for row in residual_rows)
    r2_r5_residual_count = len(residual_rows) - r0_residual_count - r1_residual_count
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
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
    }
    guardrail_violation_count = sum(bool(value) for value in guardrail_flags.values())
    passes = (
        len(scenario_labels) == int(target_scenario_count)
        and len(residual_rows) == int(target_residual_scenario_count)
        and support_counts.get("support_clear", 0) == int(target_support_clear_count)
        and support_counts.get("support_mixed", 0) == int(target_support_mixed_count)
        and support_counts.get("support_blocked", 0) == int(target_support_blocked_count)
        and support_counts.get("metric_conflict", 0) == int(target_metric_conflict_count)
        and r0_residual_count == 0
        and r1_residual_count == 0
        and r2_r5_residual_count == int(target_r2_r5_residual_count)
        and guardrail_violation_count == 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "residual_scenario_rows": str(output / "residual_scenario_rows.csv"),
        "residual_role_summary": str(output / "residual_role_summary.csv"),
        "residual_axis_summary": str(output / "residual_axis_summary.csv"),
        "residual_route_summary": str(output / "residual_route_summary.csv"),
        "residual_support_policy_summary": str(output / "residual_support_policy_summary.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
        "run_state": str(output / "run_state.json"),
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_residual_support_audit_pass"
            if passes
            else "current_sim_scenario_task_family_residual_support_audit_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "input_episode_count": len(episodes),
        "input_scenario_count": len(scenario_labels),
        "input_role_summary_count": len(role_rows),
        "target_scenario_count": int(target_scenario_count),
        "residual_scenario_count": len(residual_rows),
        "target_residual_scenario_count": int(target_residual_scenario_count),
        "support_label_counts": support_counts,
        "target_support_clear_count": int(target_support_clear_count),
        "target_support_mixed_count": int(target_support_mixed_count),
        "target_support_blocked_count": int(target_support_blocked_count),
        "target_metric_conflict_count": int(target_metric_conflict_count),
        "residual_support_label_counts": residual_counts,
        "route_label_counts": route_counts,
        "residual_role_counts": _count_by(residual_rows, "role_family"),
        "r0_residual_count": int(r0_residual_count),
        "r1_residual_count": int(r1_residual_count),
        "r2_r5_residual_count": int(r2_r5_residual_count),
        "target_r2_r5_residual_count": int(target_r2_r5_residual_count),
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
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
        "diagnostic_only": True,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "input_scenario_count": len(scenario_labels),
            "residual_scenario_count": len(residual_rows),
            "complete": bool(passes),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--scenario-support-labels", type=Path, default=DEFAULT_SCENARIO_SUPPORT_LABELS)
    parser.add_argument("--role-support-summary", type=Path, default=DEFAULT_ROLE_SUPPORT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-scenario-count", type=int, default=72)
    parser.add_argument("--target-residual-scenario-count", type=int, default=48)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_residual_support_audit(
        episode_rows=args.episode_rows,
        scenario_support_labels=args.scenario_support_labels,
        role_support_summary=args.role_support_summary,
        output_dir=args.output_dir,
        target_scenario_count=int(args.target_scenario_count),
        target_residual_scenario_count=int(args.target_residual_scenario_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"residual_scenario_count={summary['residual_scenario_count']}")
    print(f"r0_residual_count={summary['r0_residual_count']}")
    print(f"r1_residual_count={summary['r1_residual_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
