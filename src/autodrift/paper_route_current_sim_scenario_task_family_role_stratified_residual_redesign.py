"""Role-stratified residual redesign materialization for scenario task-family rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_RESIDUAL_SCENARIO_ROWS = Path(
    "runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv"
)
DEFAULT_EPISODE_ROWS = Path(
    "runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign"
)
DEFAULT_NEXT_BLOCKER = (
    "m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit"
)

REQUIRED_MITIGATION_FIELDS = (
    "impact_speed_mps",
    "delta_v_at_impact_mps",
    "time_to_collision_s",
    "collision_angle_or_side",
    "post_event_speed_mps",
    "post_event_yaw_rate_abs",
    "post_event_offtrack_overshoot",
    "recoverability_window_success",
)
MITIGATION_PROXY_FIELDS = (
    "collision",
    "outcome_bucket",
    "termination_reason",
    "min_clearance_margin",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "high_sideslip_fraction",
    "action_rate_mean",
    "return",
)
ROLE_STRATIFIED_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "sampled_obstacle_label",
    "support_label",
    "primary_route_label",
    "dominant_failure_mode",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "aeb_success_count",
    "aes_success_count",
    "envelope_aes_success_count",
    "design_route_label",
    "design_route_reason",
    "requires_artifact_only_followup",
    "requires_new_measurement",
    "mitigation_performance_claim_admissible",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
R4_AVAILABILITY_FIELDNAMES = [
    "metric_name",
    "metric_kind",
    "available_in_episode_rows",
    "required_for_mitigation_claim",
    "proxy_only",
    "action",
]
COVERAGE_REDESIGN_FIELDNAMES = [
    "scenario_spec_id",
    "role_family",
    "support_label",
    "primary_route_label",
    "dominant_failure_mode",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "design_route_label",
    "design_route_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
AXIS_ROUTE_FIELDNAMES = [
    "axis",
    "group_value",
    "row_count",
    "r4_mitigation_metric_availability_gap_count",
    "r4_mitigation_semantics_ready_count",
    "support_policy_coverage_materialization_required_count",
    "scenario_or_support_redesign_materialization_required_count",
    "metric_semantics_edge_case_count",
    "unexpected_route_label_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_table(path: Path | str) -> tuple[list[dict[str, str]], list[str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return [], []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    rows, _ = read_csv_table(path)
    return rows


def _bool_str(value: bool) -> bool:
    return bool(value)


def _missing_required_mitigation_fields(fieldnames: Iterable[str]) -> list[str]:
    available = set(fieldnames)
    return [field for field in REQUIRED_MITIGATION_FIELDS if field not in available]


def design_route_label(row: Mapping[str, Any], episode_fieldnames: Sequence[str]) -> tuple[str, str, bool]:
    role_family = str(row.get("role_family", ""))
    primary_route = str(row.get("primary_route_label", ""))
    missing = _missing_required_mitigation_fields(episode_fieldnames)
    if role_family == "R4_unavoidable_mitigation":
        if missing:
            return (
                "r4_mitigation_metric_availability_gap",
                "R4 requires mitigation severity metrics before mitigation performance can be claimed",
                True,
            )
        return (
            "r4_mitigation_semantics_ready",
            "R4 required mitigation severity metrics are present for a future semantics audit",
            False,
        )
    if primary_route == "support_policy_coverage_candidate":
        return (
            "support_policy_coverage_materialization_required",
            "partial diagnostic support exists but support-policy coverage is insufficient for ranking",
            False,
        )
    if primary_route == "scenario_or_support_redesign_candidate":
        return (
            "scenario_or_support_redesign_materialization_required",
            "no current support policy provides enough support; scenario or support needs redesign",
            False,
        )
    if primary_route == "metric_semantics_audit_candidate":
        return "metric_semantics_edge_case", "single metric edge case retained as diagnostic", False
    return "unexpected_route_label", "row has an unrecognized residual route label", False


def role_stratified_rows(
    residual_rows: Sequence[Mapping[str, Any]],
    *,
    episode_fieldnames: Sequence[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in residual_rows:
        route, reason, requires_new_measurement = design_route_label(row, episode_fieldnames)
        mitigation_claim_admissible = (
            str(row.get("role_family", "")) == "R4_unavoidable_mitigation"
            and route == "r4_mitigation_semantics_ready"
        )
        output.append(
            {
                "scenario_spec_id": row.get("scenario_spec_id", ""),
                "scenario_family_id": row.get("scenario_family_id", ""),
                "role_family": row.get("role_family", ""),
                "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
                "support_label": row.get("support_label", ""),
                "primary_route_label": row.get("primary_route_label", ""),
                "dominant_failure_mode": row.get("dominant_failure_mode", ""),
                "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
                "obstacle_longitudinal_timing_bucket": row.get("obstacle_longitudinal_timing_bucket", ""),
                "obstacle_lateral_offset_bucket": row.get("obstacle_lateral_offset_bucket", ""),
                "episode_count": row.get("episode_count", ""),
                "success_count": row.get("success_count", ""),
                "collision_count": row.get("collision_count", ""),
                "offtrack_count": row.get("offtrack_count", ""),
                "aeb_success_count": row.get("aeb_success_count", ""),
                "aes_success_count": row.get("aes_success_count", ""),
                "envelope_aes_success_count": row.get("envelope_aes_success_count", ""),
                "design_route_label": route,
                "design_route_reason": reason,
                "requires_artifact_only_followup": True,
                "requires_new_measurement": requires_new_measurement,
                "mitigation_performance_claim_admissible": mitigation_claim_admissible,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def mitigation_metric_availability_rows(episode_fieldnames: Sequence[str]) -> list[dict[str, Any]]:
    available = set(episode_fieldnames)
    rows: list[dict[str, Any]] = []
    for field in REQUIRED_MITIGATION_FIELDS:
        is_available = field in available
        rows.append(
            {
                "metric_name": field,
                "metric_kind": "required_mitigation_severity",
                "available_in_episode_rows": is_available,
                "required_for_mitigation_claim": True,
                "proxy_only": False,
                "action": "available" if is_available else "requires_new_measurement_instrumentation",
            }
        )
    for field in MITIGATION_PROXY_FIELDS:
        rows.append(
            {
                "metric_name": field,
                "metric_kind": "coarse_proxy",
                "available_in_episode_rows": field in available,
                "required_for_mitigation_claim": False,
                "proxy_only": True,
                "action": "diagnostic_proxy_only",
            }
        )
    return rows


def coverage_redesign_rows(stratified_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in stratified_rows:
        route = str(row.get("design_route_label", ""))
        if route.startswith("r4_"):
            continue
        rows.append({field: row.get(field, "") for field in COVERAGE_REDESIGN_FIELDNAMES})
    return rows


def axis_route_summary_rows(stratified_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    axes = (
        "role_family",
        "support_label",
        "primary_route_label",
        "dominant_failure_mode",
        "hidden_dynamics_bucket",
        "obstacle_longitudinal_timing_bucket",
        "obstacle_lateral_offset_bucket",
        "design_route_label",
    )
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in stratified_rows:
        for axis in axes:
            grouped[(axis, str(row.get(axis, "")))].append(row)
    output: list[dict[str, Any]] = []
    for (axis, value), rows in sorted(grouped.items()):
        counts = Counter(str(row.get("design_route_label", "")) for row in rows)
        output.append(
            {
                "axis": axis,
                "group_value": value,
                "row_count": len(rows),
                "r4_mitigation_metric_availability_gap_count": counts.get(
                    "r4_mitigation_metric_availability_gap", 0
                ),
                "r4_mitigation_semantics_ready_count": counts.get("r4_mitigation_semantics_ready", 0),
                "support_policy_coverage_materialization_required_count": counts.get(
                    "support_policy_coverage_materialization_required", 0
                ),
                "scenario_or_support_redesign_materialization_required_count": counts.get(
                    "scenario_or_support_redesign_materialization_required", 0
                ),
                "metric_semantics_edge_case_count": counts.get("metric_semantics_edge_case", 0),
                "unexpected_route_label_count": counts.get("unexpected_route_label", 0),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def claim_boundary_rows(*, mitigation_metric_gap: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "role_stratified_residual_redesign_materialized",
            "admissible": True,
            "reason": "M2324 writes role-stratified residual redesign artifacts from existing CSV inputs",
        },
        {
            "claim": "mitigation_metric_availability_gap_identified",
            "admissible": bool(mitigation_metric_gap),
            "reason": "required R4 mitigation severity fields are absent from current artifacts"
            if mitigation_metric_gap
            else "required R4 mitigation severity fields are present",
        },
        {
            "claim": "mitigation_performance_measured",
            "admissible": False,
            "reason": "M2324 does not run measured execution and proxy columns cannot support mitigation performance claims",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "support policies remain diagnostic support bounds",
        },
        {
            "claim": "residual_support_solved",
            "admissible": False,
            "reason": "M2324 materializes redesign routes but does not repair or rerun scenarios",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2324 is artifact-only scenario/task-quality infrastructure",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2324 runs no history intervention",
        },
    ]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_role_stratified_residual_redesign(
    *,
    residual_scenario_rows: Path | str = DEFAULT_RESIDUAL_SCENARIO_ROWS,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_residual_scenario_count: int = 48,
    target_r4_mitigation_row_count: int = 12,
    target_coverage_row_count: int = 23,
    target_redesign_row_count: int = 12,
    target_metric_edge_row_count: int = 1,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    residual_rows = read_csv_rows(residual_scenario_rows)
    episodes, episode_fieldnames = read_csv_table(episode_rows)
    stratified_rows = role_stratified_rows(residual_rows, episode_fieldnames=episode_fieldnames)
    availability_rows = mitigation_metric_availability_rows(episode_fieldnames)
    coverage_rows = coverage_redesign_rows(stratified_rows)
    axis_rows = axis_route_summary_rows(stratified_rows)

    write_csv_rows(
        output / "role_stratified_residual_rows.csv",
        stratified_rows,
        fieldnames=ROLE_STRATIFIED_FIELDNAMES,
    )
    write_csv_rows(
        output / "r4_mitigation_metric_availability.csv",
        availability_rows,
        fieldnames=R4_AVAILABILITY_FIELDNAMES,
    )
    write_csv_rows(
        output / "r2_r3_r5_coverage_redesign_rows.csv",
        coverage_rows,
        fieldnames=COVERAGE_REDESIGN_FIELDNAMES,
    )
    write_csv_rows(output / "axis_route_summary.csv", axis_rows, fieldnames=AXIS_ROUTE_FIELDNAMES)

    missing_required = _missing_required_mitigation_fields(episode_fieldnames)
    route_counts = _count_by(stratified_rows, "design_route_label")
    r4_rows = [row for row in stratified_rows if str(row.get("role_family", "")) == "R4_unavoidable_mitigation"]
    coverage_count = route_counts.get("support_policy_coverage_materialization_required", 0)
    redesign_count = route_counts.get("scenario_or_support_redesign_materialization_required", 0)
    metric_edge_count = route_counts.get("metric_semantics_edge_case", 0)
    r4_gap_count = route_counts.get("r4_mitigation_metric_availability_gap", 0)
    r4_ready_count = route_counts.get("r4_mitigation_semantics_ready", 0)
    mitigation_metric_gap = bool(missing_required)
    write_csv_rows(
        output / "claim_boundary.csv",
        claim_boundary_rows(mitigation_metric_gap=mitigation_metric_gap),
        fieldnames=CLAIM_FIELDNAMES,
    )

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
        "mitigation_performance_claim_made": False,
    }
    guardrail_violation_count = sum(bool(value) for value in guardrail_flags.values())
    passes = (
        len(stratified_rows) == int(target_residual_scenario_count)
        and len(r4_rows) == int(target_r4_mitigation_row_count)
        and coverage_count == int(target_coverage_row_count)
        and redesign_count == int(target_redesign_row_count)
        and metric_edge_count == int(target_metric_edge_row_count)
        and guardrail_violation_count == 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "role_stratified_residual_rows": str(output / "role_stratified_residual_rows.csv"),
        "r4_mitigation_metric_availability": str(output / "r4_mitigation_metric_availability.csv"),
        "r2_r3_r5_coverage_redesign_rows": str(output / "r2_r3_r5_coverage_redesign_rows.csv"),
        "axis_route_summary": str(output / "axis_route_summary.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
        "run_state": str(output / "run_state.json"),
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_role_stratified_residual_redesign_pass"
            if passes
            else "current_sim_scenario_task_family_role_stratified_residual_redesign_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "input_residual_scenario_count": len(residual_rows),
        "input_episode_count": len(episodes),
        "episode_field_count": len(episode_fieldnames),
        "target_residual_scenario_count": int(target_residual_scenario_count),
        "role_stratified_residual_row_count": len(stratified_rows),
        "target_r4_mitigation_row_count": int(target_r4_mitigation_row_count),
        "r4_mitigation_row_count": len(r4_rows),
        "r4_mitigation_metric_availability_gap_count": int(r4_gap_count),
        "r4_mitigation_semantics_ready_count": int(r4_ready_count),
        "r4_required_mitigation_metric_count": len(REQUIRED_MITIGATION_FIELDS),
        "r4_available_required_mitigation_metric_count": len(REQUIRED_MITIGATION_FIELDS) - len(missing_required),
        "r4_missing_required_mitigation_metric_count": len(missing_required),
        "r4_missing_required_mitigation_metrics": missing_required,
        "r4_mitigation_metric_availability_gap": bool(mitigation_metric_gap),
        "target_coverage_row_count": int(target_coverage_row_count),
        "r2_r3_r5_coverage_row_count": int(coverage_count),
        "target_redesign_row_count": int(target_redesign_row_count),
        "r2_r3_r5_redesign_row_count": int(redesign_count),
        "target_metric_edge_row_count": int(target_metric_edge_row_count),
        "metric_edge_row_count": int(metric_edge_count),
        "design_route_label_counts": route_counts,
        "role_counts": _count_by(stratified_rows, "role_family"),
        "support_label_counts": _count_by(stratified_rows, "support_label"),
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
        "mitigation_performance_claim_made": False,
        "diagnostic_only": True,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "input_residual_scenario_count": len(residual_rows),
            "role_stratified_residual_row_count": len(stratified_rows),
            "complete": bool(passes),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--residual-scenario-rows", type=Path, default=DEFAULT_RESIDUAL_SCENARIO_ROWS)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-residual-scenario-count", type=int, default=48)
    parser.add_argument("--target-r4-mitigation-row-count", type=int, default=12)
    parser.add_argument("--target-coverage-row-count", type=int, default=23)
    parser.add_argument("--target-redesign-row-count", type=int, default=12)
    parser.add_argument("--target-metric-edge-row-count", type=int, default=1)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_role_stratified_residual_redesign(
        residual_scenario_rows=args.residual_scenario_rows,
        episode_rows=args.episode_rows,
        output_dir=args.output_dir,
        target_residual_scenario_count=int(args.target_residual_scenario_count),
        target_r4_mitigation_row_count=int(args.target_r4_mitigation_row_count),
        target_coverage_row_count=int(args.target_coverage_row_count),
        target_redesign_row_count=int(args.target_redesign_row_count),
        target_metric_edge_row_count=int(args.target_metric_edge_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"role_stratified_residual_row_count={summary['role_stratified_residual_row_count']}")
    print(f"r4_mitigation_row_count={summary['r4_mitigation_row_count']}")
    print(f"r4_mitigation_metric_availability_gap={summary['r4_mitigation_metric_availability_gap']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
