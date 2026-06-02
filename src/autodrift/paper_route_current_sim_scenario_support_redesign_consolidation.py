"""Artifact-only consolidation for scenario/support redesign rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_RESCORE_DIR = Path("runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore")
DEFAULT_RESIDUAL_DIR = Path("runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit")
DEFAULT_SOURCE_MAPPING_DIR = Path("runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping")
DEFAULT_OUTPUT_DIR = Path("runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation")
DEFAULT_ORIGINAL_REDESIGN_GAP_COUNT = 12
DEFAULT_REMAPPED_REDESIGN_CANDIDATE_COUNT = 14
DEFAULT_SECONDARY_COVERAGE_ROW_COUNT = 9
DEFAULT_NEXT_BLOCKER = "m2344-paper-route-current-sim-scenario-support-redesign-consolidation-result-audit"
STRESS_HIDDEN_BUCKETS = {"low_mu", "weak_brake", "slow_steer_actuator", "tire_stiffness_shift"}
CONSOLIDATED_FIELDNAMES = [
    "scenario_spec_id",
    "redesign_source",
    "role_family",
    "scenario_family_id",
    "sampled_obstacle_label",
    "same_scene_group_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "initial_speed_mps",
    "track_radius_m",
    "track_width_m",
    "actor_contract_id",
    "support_label",
    "dominant_failure_mode",
    "dominant_failure_bucket",
    "source_signature",
    "role_timing_lateral_signature",
    "hidden_role_signature",
    "aeb_success_count",
    "aeb_collision_count",
    "aeb_offtrack_count",
    "aes_success_count",
    "aes_collision_count",
    "aes_offtrack_count",
    "envelope_aes_success_count",
    "envelope_aes_collision_count",
    "envelope_aes_offtrack_count",
    "redesign_theme",
    "redesign_priority_bucket",
    "recommended_redesign_route",
    "redesign_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
AXIS_SUMMARY_FIELDNAMES = [
    "axis",
    "group_value",
    "redesign_row_count",
    "geometry_timing_rebalance_candidate_count",
    "hidden_dynamics_range_rebalance_candidate_count",
    "role_semantics_or_success_metric_review_candidate_count",
    "support_policy_after_redesign_candidate_count",
    "needs_user_review_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROUTE_SUMMARY_FIELDNAMES = [
    "recommended_redesign_route",
    "redesign_row_count",
    "redesign_sources",
    "role_families",
    "hidden_dynamics_buckets",
    "timing_buckets",
    "lateral_buckets",
    "redesign_themes",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
SOURCE_SUMMARY_FIELDNAMES = [
    "redesign_source",
    "redesign_row_count",
    "geometry_timing_rebalance_candidate_count",
    "hidden_dynamics_range_rebalance_candidate_count",
    "role_semantics_or_success_metric_review_candidate_count",
    "support_policy_after_redesign_candidate_count",
    "needs_user_review_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "allowed", "made", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _int_value(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def _index_by_scenario(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("scenario_spec_id", "")): row for row in rows}


def _dominant_failure_bucket(row: Mapping[str, Any]) -> str:
    explicit = str(row.get("dominant_failure_bucket", ""))
    if explicit:
        return explicit
    mode = str(row.get("dominant_failure_mode", ""))
    if mode:
        return mode
    collision = _int_value(row.get("collision_count", 0))
    offtrack = _int_value(row.get("offtrack_count", 0))
    if collision >= offtrack and collision > 0:
        return "collision_dominated_failure"
    if offtrack > 0:
        return "offtrack_dominated_failure"
    return "metric_edge_or_other"


def _source_signature(row: Mapping[str, Any]) -> str:
    role = str(row.get("role_family", ""))
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    timing = str(row.get("obstacle_longitudinal_timing_bucket", ""))
    lateral = str(row.get("obstacle_lateral_offset_bucket", ""))
    return f"{role}|{hidden}|{timing}|{lateral}"


def _derive_redesign(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    role = str(row.get("role_family", ""))
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    timing = str(row.get("obstacle_longitudinal_timing_bucket", ""))
    lateral = str(row.get("obstacle_lateral_offset_bucket", ""))
    failure = _dominant_failure_bucket(row)
    if failure == "offtrack_dominated_failure" and lateral != "centerline":
        return (
            "offtrack_geometry_pressure",
            "high",
            "geometry_timing_rebalance_candidate",
            "offtrack-dominated lateral-offset row suggests geometry or timing rebalance",
        )
    if failure == "collision_dominated_failure" and timing == "late_close":
        return (
            "collision_timing_pressure",
            "high",
            "geometry_timing_rebalance_candidate",
            "collision-dominated late-close row suggests timing rebalance",
        )
    if hidden in STRESS_HIDDEN_BUCKETS:
        return (
            "hidden_dynamics_stress",
            "medium",
            "hidden_dynamics_range_rebalance_candidate",
            "row sits in a stress hidden-dynamics bucket",
        )
    if role.startswith("R5_"):
        return (
            "hidden_dynamics_robustness_task_quality",
            "medium",
            "hidden_dynamics_range_rebalance_candidate",
            "R5 hidden-dynamics robustness row needs range or same-scene task-quality review",
        )
    if role.startswith("R2_") or role.startswith("R3_"):
        return (
            "role_recovery_or_drift_task_quality",
            "medium",
            "role_semantics_or_success_metric_review_candidate",
            "R2/R3 handling-limit or recovery task-quality row needs role-specific review",
        )
    return (
        "unclassified_redesign_pressure",
        "needs_review",
        "needs_user_review",
        "artifact-only row did not match a redesign theme",
    )


def _base_row_from_mapping(row: Mapping[str, Any], source: str) -> dict[str, Any]:
    theme, priority, route, reason = _derive_redesign(row)
    source_signature = str(row.get("source_signature", "")) or _source_signature(row)
    role = str(row.get("role_family", ""))
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    timing = str(row.get("obstacle_longitudinal_timing_bucket", ""))
    lateral = str(row.get("obstacle_lateral_offset_bucket", ""))
    return {
        "scenario_spec_id": row.get("scenario_spec_id", ""),
        "redesign_source": source,
        "role_family": role,
        "scenario_family_id": row.get("scenario_family_id", ""),
        "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
        "same_scene_group_id": row.get("same_scene_group_id", ""),
        "hidden_dynamics_bucket": hidden,
        "obstacle_longitudinal_timing_bucket": timing,
        "obstacle_lateral_offset_bucket": lateral,
        "initial_speed_mps": row.get("initial_speed_mps", ""),
        "track_radius_m": row.get("track_radius_m", ""),
        "track_width_m": row.get("track_width_m", ""),
        "actor_contract_id": row.get("actor_contract_id", ""),
        "support_label": row.get("support_label", ""),
        "dominant_failure_mode": row.get("dominant_failure_mode", ""),
        "dominant_failure_bucket": _dominant_failure_bucket(row),
        "source_signature": source_signature,
        "role_timing_lateral_signature": str(row.get("role_timing_lateral_signature", ""))
        or f"{role}|{timing}|{lateral}",
        "hidden_role_signature": str(row.get("hidden_role_signature", "")) or f"{role}|{hidden}",
        "aeb_success_count": row.get("aeb_success_count", 0),
        "aeb_collision_count": row.get("aeb_collision_count", 0),
        "aeb_offtrack_count": row.get("aeb_offtrack_count", 0),
        "aes_success_count": row.get("aes_success_count", 0),
        "aes_collision_count": row.get("aes_collision_count", 0),
        "aes_offtrack_count": row.get("aes_offtrack_count", 0),
        "envelope_aes_success_count": row.get("envelope_aes_success_count", 0),
        "envelope_aes_collision_count": row.get("envelope_aes_collision_count", 0),
        "envelope_aes_offtrack_count": row.get("envelope_aes_offtrack_count", 0),
        "redesign_theme": theme,
        "redesign_priority_bucket": priority,
        "recommended_redesign_route": route,
        "redesign_reason": reason,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def build_consolidated_rows(
    *,
    rescore_rows: Sequence[Mapping[str, Any]],
    residual_rows: Sequence[Mapping[str, Any]],
    source_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    residual_by_id = _index_by_scenario(residual_rows)
    rows: list[dict[str, Any]] = []
    for rescore in rescore_rows:
        if str(rescore.get("rescore_route_label", "")) != "scenario_or_support_redesign_gap":
            continue
        scenario_id = str(rescore.get("scenario_spec_id", ""))
        residual = residual_by_id.get(scenario_id, {"scenario_spec_id": scenario_id})
        rows.append(_base_row_from_mapping(residual, "original_m2336_redesign_gap"))
    secondary: list[dict[str, Any]] = []
    for source in source_rows:
        route = str(source.get("recommended_next_route", ""))
        if route == "scenario_or_support_redesign_candidate":
            rows.append(_base_row_from_mapping(source, "remapped_m2340_coverage_redesign_candidate"))
        elif route == "support_policy_coverage_materialization_candidate":
            secondary.append(dict(source))
    return rows, secondary


def _route_count(row: Mapping[str, Any], route: str) -> bool:
    return str(row.get("recommended_redesign_route", "")) == route


def axis_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        "redesign_source",
        "role_family",
        "hidden_dynamics_bucket",
        "obstacle_longitudinal_timing_bucket",
        "obstacle_lateral_offset_bucket",
        "dominant_failure_bucket",
        "redesign_theme",
        "recommended_redesign_route",
    ]
    output: list[dict[str, Any]] = []
    for axis in axes:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(axis, ""))].append(row)
        for group_value in sorted(grouped):
            group = grouped[group_value]
            output.append(
                {
                    "axis": axis,
                    "group_value": group_value,
                    "redesign_row_count": len(group),
                    "geometry_timing_rebalance_candidate_count": sum(
                        _route_count(row, "geometry_timing_rebalance_candidate") for row in group
                    ),
                    "hidden_dynamics_range_rebalance_candidate_count": sum(
                        _route_count(row, "hidden_dynamics_range_rebalance_candidate") for row in group
                    ),
                    "role_semantics_or_success_metric_review_candidate_count": sum(
                        _route_count(row, "role_semantics_or_success_metric_review_candidate") for row in group
                    ),
                    "support_policy_after_redesign_candidate_count": sum(
                        _route_count(row, "support_policy_after_redesign_candidate") for row in group
                    ),
                    "needs_user_review_count": sum(_route_count(row, "needs_user_review") for row in group),
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return output


def redesign_route_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("recommended_redesign_route", ""))].append(row)
    output: list[dict[str, Any]] = []
    for route in sorted(grouped):
        group = grouped[route]
        output.append(
            {
                "recommended_redesign_route": route,
                "redesign_row_count": len(group),
                "redesign_sources": "|".join(sorted({str(row.get("redesign_source", "")) for row in group})),
                "role_families": "|".join(sorted({str(row.get("role_family", "")) for row in group})),
                "hidden_dynamics_buckets": "|".join(
                    sorted({str(row.get("hidden_dynamics_bucket", "")) for row in group})
                ),
                "timing_buckets": "|".join(
                    sorted({str(row.get("obstacle_longitudinal_timing_bucket", "")) for row in group})
                ),
                "lateral_buckets": "|".join(
                    sorted({str(row.get("obstacle_lateral_offset_bucket", "")) for row in group})
                ),
                "redesign_themes": "|".join(sorted({str(row.get("redesign_theme", "")) for row in group})),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def redesign_source_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("redesign_source", ""))].append(row)
    output: list[dict[str, Any]] = []
    for source in sorted(grouped):
        group = grouped[source]
        output.append(
            {
                "redesign_source": source,
                "redesign_row_count": len(group),
                "geometry_timing_rebalance_candidate_count": sum(
                    _route_count(row, "geometry_timing_rebalance_candidate") for row in group
                ),
                "hidden_dynamics_range_rebalance_candidate_count": sum(
                    _route_count(row, "hidden_dynamics_range_rebalance_candidate") for row in group
                ),
                "role_semantics_or_success_metric_review_candidate_count": sum(
                    _route_count(row, "role_semantics_or_success_metric_review_candidate") for row in group
                ),
                "support_policy_after_redesign_candidate_count": sum(
                    _route_count(row, "support_policy_after_redesign_candidate") for row in group
                ),
                "needs_user_review_count": sum(_route_count(row, "needs_user_review") for row in group),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_scenario_support_redesign_consolidation",
            "allowed": True,
            "made": True,
            "reason": "M2343 only consolidates existing redesign-related artifacts.",
        },
        {
            "claim": "scenario_redesign_executed",
            "allowed": False,
            "made": False,
            "reason": "No scenario pack is changed and no rollout is run.",
        },
        {
            "claim": "support_policy_ranking",
            "allowed": False,
            "made": False,
            "reason": "Support policy data is diagnostic only.",
        },
        {
            "claim": "controller_comparison_ready",
            "allowed": False,
            "made": False,
            "reason": "Consolidation identifies task-quality blockers before comparison.",
        },
        {
            "claim": "paper_level_evidence",
            "allowed": False,
            "made": False,
            "reason": "No controller result, holdout, or comparison is produced.",
        },
        {
            "claim": "level3_self_identification",
            "allowed": False,
            "made": False,
            "reason": "No history intervention or self-ID test is run.",
        },
    ]


def run_scenario_support_redesign_consolidation(
    *,
    rescore_dir: Path | str = DEFAULT_RESCORE_DIR,
    residual_dir: Path | str = DEFAULT_RESIDUAL_DIR,
    source_mapping_dir: Path | str = DEFAULT_SOURCE_MAPPING_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_original_redesign_gap_count: int = DEFAULT_ORIGINAL_REDESIGN_GAP_COUNT,
    target_remapped_redesign_candidate_count: int = DEFAULT_REMAPPED_REDESIGN_CANDIDATE_COUNT,
    target_secondary_coverage_row_count: int = DEFAULT_SECONDARY_COVERAGE_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    rescore_path = Path(rescore_dir)
    residual_path = Path(residual_dir)
    source_path = Path(source_mapping_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rescore_rows = read_csv_rows(rescore_path / "residual_rescore_rows.csv")
    residual_rows = read_csv_rows(residual_path / "residual_scenario_rows.csv")
    source_rows = read_csv_rows(source_path / "coverage_gap_source_rows.csv")

    consolidated, secondary = build_consolidated_rows(
        rescore_rows=rescore_rows,
        residual_rows=residual_rows,
        source_rows=source_rows,
    )
    axis_rows = axis_summary_rows(consolidated)
    route_rows = redesign_route_summary_rows(consolidated)
    source_summary = redesign_source_summary_rows(consolidated)
    claims = claim_boundary_rows()

    write_csv_rows(output / "consolidated_redesign_rows.csv", consolidated, fieldnames=CONSOLIDATED_FIELDNAMES)
    write_csv_rows(output / "secondary_coverage_materialization_rows.csv", secondary)
    write_csv_rows(output / "redesign_axis_summary.csv", axis_rows, fieldnames=AXIS_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "redesign_route_summary.csv", route_rows, fieldnames=ROUTE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "redesign_source_summary.csv", source_summary, fieldnames=SOURCE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    source_counts = Counter(str(row.get("redesign_source", "")) for row in consolidated)
    route_counts = Counter(str(row.get("recommended_redesign_route", "")) for row in consolidated)
    theme_counts = Counter(str(row.get("redesign_theme", "")) for row in consolidated)
    scenario_counts = Counter(str(row.get("scenario_spec_id", "")) for row in consolidated)
    duplicate_count = sum(count - 1 for count in scenario_counts.values() if count > 1)
    ranking_admissible_count = sum(_bool_value(row.get("ranking_admissible", False)) for row in consolidated)
    winner_selected_count = sum(_bool_value(row.get("winner_selected", False)) for row in consolidated)
    paper_level_claim_count = sum(_bool_value(row.get("paper_level_claim_made", False)) for row in consolidated)
    level3_self_id_claim_count = sum(_bool_value(row.get("level3_self_id_claim_made", False)) for row in consolidated)
    guardrail_violation_count = (
        ranking_admissible_count + winner_selected_count + paper_level_claim_count + level3_self_id_claim_count
    )
    original_count = source_counts["original_m2336_redesign_gap"]
    remapped_count = source_counts["remapped_m2340_coverage_redesign_candidate"]
    combined_count = len(consolidated)
    unique_count = len(scenario_counts)
    result_passes = (
        original_count == int(target_original_redesign_gap_count)
        and remapped_count == int(target_remapped_redesign_candidate_count)
        and combined_count == int(target_original_redesign_gap_count) + int(target_remapped_redesign_candidate_count)
        and unique_count == combined_count
        and len(secondary) == int(target_secondary_coverage_row_count)
        and route_counts["needs_user_review"] == 0
        and duplicate_count == 0
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_scenario_support_redesign_consolidation_pass"
            if result_passes
            else "current_sim_scenario_support_redesign_consolidation_incomplete_or_fail"
        ),
        "rescore_dir": str(rescore_path),
        "residual_dir": str(residual_path),
        "source_mapping_dir": str(source_path),
        "output_dir": str(output),
        "original_redesign_gap_count": original_count,
        "target_original_redesign_gap_count": int(target_original_redesign_gap_count),
        "remapped_coverage_redesign_candidate_count": remapped_count,
        "target_remapped_redesign_candidate_count": int(target_remapped_redesign_candidate_count),
        "combined_redesign_related_row_count": combined_count,
        "unique_redesign_scenario_count": unique_count,
        "secondary_coverage_materialization_row_count": len(secondary),
        "target_secondary_coverage_row_count": int(target_secondary_coverage_row_count),
        "redesign_theme_counts": dict(theme_counts),
        "recommended_redesign_route_counts": dict(route_counts),
        "needs_user_review_count": route_counts["needs_user_review"],
        "duplicate_redesign_scenario_count": duplicate_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "paper_level_claim_count": paper_level_claim_count,
        "level3_self_id_claim_count": level3_self_id_claim_count,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "support_policy_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
        "controller_comparison_ready_claim_made": False,
        "artifacts": {
            "consolidated_redesign_rows": str(output / "consolidated_redesign_rows.csv"),
            "secondary_coverage_materialization_rows": str(output / "secondary_coverage_materialization_rows.csv"),
            "redesign_axis_summary": str(output / "redesign_axis_summary.csv"),
            "redesign_route_summary": str(output / "redesign_route_summary.csv"),
            "redesign_source_summary": str(output / "redesign_source_summary.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rescore-dir", type=Path, default=DEFAULT_RESCORE_DIR)
    parser.add_argument("--residual-dir", type=Path, default=DEFAULT_RESIDUAL_DIR)
    parser.add_argument("--source-mapping-dir", type=Path, default=DEFAULT_SOURCE_MAPPING_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-original-redesign-gap-count", type=int, default=DEFAULT_ORIGINAL_REDESIGN_GAP_COUNT)
    parser.add_argument(
        "--target-remapped-redesign-candidate-count",
        type=int,
        default=DEFAULT_REMAPPED_REDESIGN_CANDIDATE_COUNT,
    )
    parser.add_argument("--target-secondary-coverage-row-count", type=int, default=DEFAULT_SECONDARY_COVERAGE_ROW_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_scenario_support_redesign_consolidation(
        rescore_dir=args.rescore_dir,
        residual_dir=args.residual_dir,
        source_mapping_dir=args.source_mapping_dir,
        output_dir=args.output_dir,
        target_original_redesign_gap_count=int(args.target_original_redesign_gap_count),
        target_remapped_redesign_candidate_count=int(args.target_remapped_redesign_candidate_count),
        target_secondary_coverage_row_count=int(args.target_secondary_coverage_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"combined_redesign_related_row_count={summary['combined_redesign_related_row_count']}")
    print(f"unique_redesign_scenario_count={summary['unique_redesign_scenario_count']}")
    print(f"secondary_coverage_materialization_row_count={summary['secondary_coverage_materialization_row_count']}")
    print(f"needs_user_review_count={summary['needs_user_review_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
