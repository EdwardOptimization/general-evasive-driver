"""Artifact-only source mapping for support-policy coverage gaps."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_RESCORE_DIR = Path("runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore")
DEFAULT_RESIDUAL_DIR = Path("runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit")
DEFAULT_SUPPORT_DIR = Path("runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration")
DEFAULT_OUTPUT_DIR = Path("runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping")
DEFAULT_TARGET_COVERAGE_GAP_ROW_COUNT = 23
DEFAULT_NEXT_BLOCKER = "m2341-paper-route-current-sim-support-coverage-gap-source-mapping-result-audit"
SUPPORT_POLICIES = ("aeb", "aes", "envelope_aes")
SOURCE_ROW_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
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
    "rescore_route_label",
    "dominant_failure_mode",
    "best_support_success_count",
    "best_support_policy_name_metadata_only",
    "aeb_success_count",
    "aeb_collision_count",
    "aeb_offtrack_count",
    "aes_success_count",
    "aes_collision_count",
    "aes_offtrack_count",
    "envelope_aes_success_count",
    "envelope_aes_collision_count",
    "envelope_aes_offtrack_count",
    "source_signature",
    "role_timing_lateral_signature",
    "hidden_role_signature",
    "support_outcome_pattern",
    "dominant_failure_bucket",
    "source_concentration_bucket",
    "recommended_next_route",
    "route_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
AXIS_SUMMARY_FIELDNAMES = [
    "axis",
    "group_value",
    "coverage_gap_count",
    "support_policy_coverage_materialization_candidate_count",
    "scenario_or_support_redesign_candidate_count",
    "metric_edge_audit_candidate_count",
    "needs_user_review_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
SUPPORT_POLICY_SUMMARY_FIELDNAMES = [
    "support_policy_name",
    "scenario_count",
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
RECOMMENDED_ROUTE_SUMMARY_FIELDNAMES = [
    "recommended_next_route",
    "coverage_gap_count",
    "role_families",
    "hidden_dynamics_buckets",
    "obstacle_longitudinal_timing_buckets",
    "obstacle_lateral_offset_buckets",
    "dominant_failure_buckets",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "allowed", "made", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _int_value(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _index_by_scenario(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("scenario_spec_id", "")): row for row in rows}


def _rows_by_scenario(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scenario_spec_id", ""))].append(row)
    return grouped


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool_value(row.get("collision", False)) or str(row.get("outcome_bucket", "")) == "collision_failure"


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    bucket = str(row.get("outcome_bucket", ""))
    return _bool_value(row.get("offtrack", False)) or "offtrack" in bucket or str(row.get("termination_reason", "")) == "off_track"


def _policy_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        if _bool_value(row.get("success", False)) or str(row.get("outcome_bucket", "")) == "success_obstacle_pass":
            counts["success"] += 1
        elif _is_collision(row):
            counts["collision"] += 1
        elif _is_offtrack(row):
            counts["offtrack"] += 1
        elif _bool_value(row.get("truncated", False)) or str(row.get("outcome_bucket", "")) == "max_steps_noncompletion":
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
    return {key: int(counts[key]) for key in ("success", "collision", "offtrack", "max_step_noncompletion", "other_failure")}


def _dominant_failure_bucket(row: Mapping[str, Any]) -> str:
    mode = str(row.get("dominant_failure_mode", ""))
    if mode in {
        "collision_dominated_failure",
        "offtrack_dominated_failure",
        "max_step_noncompletion_dominated_failure",
        "mixed_failure",
    }:
        return mode
    collision = _int_value(row.get("collision_count", 0))
    offtrack = _int_value(row.get("offtrack_count", 0))
    max_step = _int_value(row.get("max_step_noncompletion_count", 0))
    if collision >= offtrack and collision >= max_step and collision > 0:
        return "collision_dominated_failure"
    if offtrack >= collision and offtrack >= max_step and offtrack > 0:
        return "offtrack_dominated_failure"
    if max_step > 0:
        return "max_step_noncompletion_dominated_failure"
    return "metric_edge_or_other"


def _support_outcome_pattern(row: Mapping[str, Any]) -> str:
    tokens: list[str] = []
    for policy in SUPPORT_POLICIES:
        successes = _int_value(row.get(f"{policy}_success_count", 0))
        collisions = _int_value(row.get(f"{policy}_collision_count", 0))
        offtracks = _int_value(row.get(f"{policy}_offtrack_count", 0))
        status = []
        if successes:
            status.append("success")
        if collisions:
            status.append("collision")
        if offtracks:
            status.append("offtrack")
        tokens.append(f"{policy}:{'+'.join(status) if status else 'none'}")
    return "|".join(tokens)


def _recommended_route(row: Mapping[str, Any]) -> tuple[str, str]:
    support_label = str(row.get("support_label", ""))
    total_success = sum(_int_value(row.get(f"{policy}_success_count", 0)) for policy in SUPPORT_POLICIES)
    collision_policies = sum(_int_value(row.get(f"{policy}_collision_count", 0)) > 0 for policy in SUPPORT_POLICIES)
    offtrack_policies = sum(_int_value(row.get(f"{policy}_offtrack_count", 0)) > 0 for policy in SUPPORT_POLICIES)
    if support_label == "metric_conflict":
        return "metric_edge_audit_candidate", "support label is metric_conflict"
    if total_success > 0:
        return (
            "support_policy_coverage_materialization_candidate",
            "partial success evidence exists but current support panel does not make the scenario support_clear",
        )
    if collision_policies == len(SUPPORT_POLICIES) or offtrack_policies == len(SUPPORT_POLICIES):
        return (
            "scenario_or_support_redesign_candidate",
            "all support policies fail in a shared dominant mode",
        )
    if support_label == "support_mixed" and (collision_policies > 0 or offtrack_policies > 0):
        return (
            "support_policy_coverage_materialization_candidate",
            "support policies fail in different modes, so coverage remains under-materialized",
        )
    return "needs_user_review", "artifact-only fields do not justify coverage or redesign routing"


def _source_concentration_bucket(source_count: int, total_rows: int) -> str:
    if source_count <= 1:
        return "source_singleton"
    share = float(source_count) / float(max(1, total_rows))
    if share >= 0.25:
        return "source_concentrated"
    return "source_cluster"


def build_source_rows(
    *,
    rescore_rows: Sequence[Mapping[str, Any]],
    residual_rows: Sequence[Mapping[str, Any]],
    support_label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    residual_by_id = _index_by_scenario(residual_rows)
    support_by_id = _index_by_scenario(support_label_rows)
    coverage_ids = [
        str(row.get("scenario_spec_id", ""))
        for row in rescore_rows
        if str(row.get("rescore_route_label", "")) == "support_policy_coverage_gap"
    ]
    base_rows: list[dict[str, Any]] = []
    for scenario_id in coverage_ids:
        residual = residual_by_id.get(scenario_id, {})
        support = support_by_id.get(scenario_id, {})
        if not residual and not support:
            base_rows.append(
                {
                    "scenario_spec_id": scenario_id,
                    "source_signature": "missing",
                    "role_timing_lateral_signature": "missing",
                    "hidden_role_signature": "missing",
                    "support_outcome_pattern": "missing",
                    "dominant_failure_bucket": "metric_edge_or_other",
                    "source_concentration_bucket": "source_singleton",
                    "recommended_next_route": "needs_user_review",
                    "route_reason": "required scenario row missing",
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
            continue
        merged = {**support, **residual}
        role = str(merged.get("role_family", ""))
        hidden = str(merged.get("hidden_dynamics_bucket", ""))
        timing = str(merged.get("obstacle_longitudinal_timing_bucket", ""))
        lateral = str(merged.get("obstacle_lateral_offset_bucket", ""))
        route, reason = _recommended_route(merged)
        row = {
            "scenario_spec_id": scenario_id,
            "scenario_family_id": merged.get("scenario_family_id", ""),
            "role_family": role,
            "sampled_obstacle_label": merged.get("sampled_obstacle_label", ""),
            "same_scene_group_id": merged.get("same_scene_group_id", ""),
            "hidden_dynamics_bucket": hidden,
            "obstacle_longitudinal_timing_bucket": timing,
            "obstacle_lateral_offset_bucket": lateral,
            "initial_speed_mps": merged.get("initial_speed_mps", ""),
            "track_radius_m": merged.get("track_radius_m", ""),
            "track_width_m": merged.get("track_width_m", ""),
            "actor_contract_id": merged.get("actor_contract_id", ""),
            "support_label": merged.get("support_label", ""),
            "rescore_route_label": "support_policy_coverage_gap",
            "dominant_failure_mode": merged.get("dominant_failure_mode", ""),
            "best_support_success_count": merged.get("best_support_success_count", ""),
            "best_support_policy_name_metadata_only": merged.get("best_support_policy_name", ""),
            "aeb_success_count": merged.get("aeb_success_count", 0),
            "aeb_collision_count": merged.get("aeb_collision_count", 0),
            "aeb_offtrack_count": merged.get("aeb_offtrack_count", 0),
            "aes_success_count": merged.get("aes_success_count", 0),
            "aes_collision_count": merged.get("aes_collision_count", 0),
            "aes_offtrack_count": merged.get("aes_offtrack_count", 0),
            "envelope_aes_success_count": merged.get("envelope_aes_success_count", 0),
            "envelope_aes_collision_count": merged.get("envelope_aes_collision_count", 0),
            "envelope_aes_offtrack_count": merged.get("envelope_aes_offtrack_count", 0),
            "source_signature": f"{role}|{hidden}|{timing}|{lateral}",
            "role_timing_lateral_signature": f"{role}|{timing}|{lateral}",
            "hidden_role_signature": f"{role}|{hidden}",
            "support_outcome_pattern": _support_outcome_pattern(merged),
            "dominant_failure_bucket": _dominant_failure_bucket(merged),
            "recommended_next_route": route,
            "route_reason": reason,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
        base_rows.append(row)
    source_counts = Counter(str(row.get("source_signature", "")) for row in base_rows)
    total = len(base_rows)
    for row in base_rows:
        row["source_concentration_bucket"] = _source_concentration_bucket(
            source_counts[str(row.get("source_signature", ""))], total
        )
    return base_rows


def axis_summary_rows(source_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        "role_family",
        "hidden_dynamics_bucket",
        "obstacle_longitudinal_timing_bucket",
        "obstacle_lateral_offset_bucket",
        "dominant_failure_bucket",
        "source_concentration_bucket",
        "recommended_next_route",
        "support_outcome_pattern",
    ]
    rows: list[dict[str, Any]] = []
    for axis in axes:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[str(row.get(axis, ""))].append(row)
        for group_value in sorted(grouped):
            group = grouped[group_value]
            routes = Counter(str(row.get("recommended_next_route", "")) for row in group)
            rows.append(
                {
                    "axis": axis,
                    "group_value": group_value,
                    "coverage_gap_count": len(group),
                    "support_policy_coverage_materialization_candidate_count": routes[
                        "support_policy_coverage_materialization_candidate"
                    ],
                    "scenario_or_support_redesign_candidate_count": routes[
                        "scenario_or_support_redesign_candidate"
                    ],
                    "metric_edge_audit_candidate_count": routes["metric_edge_audit_candidate"],
                    "needs_user_review_count": routes["needs_user_review"],
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return rows


def support_policy_summary_rows(
    *,
    source_rows: Sequence[Mapping[str, Any]],
    episode_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    target_ids = {str(row.get("scenario_spec_id", "")) for row in source_rows}
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    scenarios_by_policy: dict[str, set[str]] = defaultdict(set)
    for row in episode_rows:
        scenario_id = str(row.get("scenario_spec_id", ""))
        if scenario_id not in target_ids:
            continue
        policy = str(row.get("support_policy_name", row.get("policy", "")))
        if policy not in SUPPORT_POLICIES:
            continue
        grouped[policy].append(row)
        scenarios_by_policy[policy].add(scenario_id)
    output: list[dict[str, Any]] = []
    for policy in SUPPORT_POLICIES:
        rows = grouped.get(policy, [])
        counts = _policy_counts(rows)
        output.append(
            {
                "support_policy_name": policy,
                "scenario_count": len(scenarios_by_policy.get(policy, set())),
                "episode_count": len(rows),
                "success_count": counts["success"],
                "collision_count": counts["collision"],
                "offtrack_count": counts["offtrack"],
                "max_step_noncompletion_count": counts["max_step_noncompletion"],
                "other_failure_count": counts["other_failure"],
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def recommended_route_summary_rows(source_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in source_rows:
        grouped[str(row.get("recommended_next_route", ""))].append(row)
    output: list[dict[str, Any]] = []
    for route in sorted(grouped):
        rows = grouped[route]
        output.append(
            {
                "recommended_next_route": route,
                "coverage_gap_count": len(rows),
                "role_families": "|".join(sorted({str(row.get("role_family", "")) for row in rows})),
                "hidden_dynamics_buckets": "|".join(
                    sorted({str(row.get("hidden_dynamics_bucket", "")) for row in rows})
                ),
                "obstacle_longitudinal_timing_buckets": "|".join(
                    sorted({str(row.get("obstacle_longitudinal_timing_bucket", "")) for row in rows})
                ),
                "obstacle_lateral_offset_buckets": "|".join(
                    sorted({str(row.get("obstacle_lateral_offset_bucket", "")) for row in rows})
                ),
                "dominant_failure_buckets": "|".join(
                    sorted({str(row.get("dominant_failure_bucket", "")) for row in rows})
                ),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_support_coverage_gap_source_mapping",
            "allowed": True,
            "made": True,
            "reason": "M2340 only maps existing support coverage gap artifacts.",
        },
        {
            "claim": "support_policy_ranking",
            "allowed": False,
            "made": False,
            "reason": "Support policy aggregates are diagnostic and do not select a winner.",
        },
        {
            "claim": "controller_comparison_ready",
            "allowed": False,
            "made": False,
            "reason": "Source mapping selects the next task-quality route before comparison.",
        },
        {
            "claim": "residual_support_solved",
            "allowed": False,
            "made": False,
            "reason": "Source mapping classifies residual coverage gaps but does not solve them.",
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


def run_support_coverage_gap_source_mapping(
    *,
    rescore_dir: Path | str = DEFAULT_RESCORE_DIR,
    residual_dir: Path | str = DEFAULT_RESIDUAL_DIR,
    support_dir: Path | str = DEFAULT_SUPPORT_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_coverage_gap_row_count: int = DEFAULT_TARGET_COVERAGE_GAP_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    rescore_path = Path(rescore_dir)
    residual_path = Path(residual_dir)
    support_path = Path(support_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rescore_rows = read_csv_rows(rescore_path / "residual_rescore_rows.csv")
    residual_rows = read_csv_rows(residual_path / "residual_scenario_rows.csv")
    support_label_rows = read_csv_rows(support_path / "scenario_support_labels.csv")
    episode_rows = read_csv_rows(support_path / "episode_rows.csv")

    source_rows = build_source_rows(
        rescore_rows=rescore_rows,
        residual_rows=residual_rows,
        support_label_rows=support_label_rows,
    )
    axis_rows = axis_summary_rows(source_rows)
    support_rows = support_policy_summary_rows(source_rows=source_rows, episode_rows=episode_rows)
    route_rows = recommended_route_summary_rows(source_rows)
    claims = claim_boundary_rows()

    write_csv_rows(output / "coverage_gap_source_rows.csv", source_rows, fieldnames=SOURCE_ROW_FIELDNAMES)
    write_csv_rows(output / "coverage_gap_axis_summary.csv", axis_rows, fieldnames=AXIS_SUMMARY_FIELDNAMES)
    write_csv_rows(
        output / "coverage_gap_support_policy_summary.csv",
        support_rows,
        fieldnames=SUPPORT_POLICY_SUMMARY_FIELDNAMES,
    )
    write_csv_rows(
        output / "coverage_gap_recommended_route_summary.csv",
        route_rows,
        fieldnames=RECOMMENDED_ROUTE_SUMMARY_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    route_counts = Counter(str(row.get("recommended_next_route", "")) for row in source_rows)
    source_counts = Counter(str(row.get("source_signature", "")) for row in source_rows)
    ranking_admissible_count = sum(_bool_value(row.get("ranking_admissible", False)) for row in source_rows)
    winner_selected_count = sum(_bool_value(row.get("winner_selected", False)) for row in source_rows)
    paper_level_claim_count = sum(_bool_value(row.get("paper_level_claim_made", False)) for row in source_rows)
    level3_self_id_claim_count = sum(_bool_value(row.get("level3_self_id_claim_made", False)) for row in source_rows)
    unclassified_count = route_counts["needs_user_review"]
    guardrail_violation_count = (
        ranking_admissible_count + winner_selected_count + paper_level_claim_count + level3_self_id_claim_count
    )
    max_source_signature_share = (
        max(source_counts.values()) / float(max(1, len(source_rows))) if source_counts else 0.0
    )
    result_passes = (
        len(source_rows) == int(target_coverage_gap_row_count)
        and unclassified_count == 0
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_support_coverage_gap_source_mapping_pass"
            if result_passes
            else "current_sim_support_coverage_gap_source_mapping_incomplete_or_fail"
        ),
        "rescore_dir": str(rescore_path),
        "residual_dir": str(residual_path),
        "support_dir": str(support_path),
        "output_dir": str(output),
        "coverage_gap_row_count": len(source_rows),
        "target_coverage_gap_row_count": int(target_coverage_gap_row_count),
        "role_count": len({str(row.get("role_family", "")) for row in source_rows}),
        "role_counts": dict(Counter(str(row.get("role_family", "")) for row in source_rows)),
        "source_signature_count": len(source_counts),
        "max_source_signature_share": max_source_signature_share,
        "recommended_route_counts": dict(route_counts),
        "support_policy_coverage_materialization_candidate_count": route_counts[
            "support_policy_coverage_materialization_candidate"
        ],
        "scenario_or_support_redesign_candidate_count": route_counts["scenario_or_support_redesign_candidate"],
        "metric_edge_audit_candidate_count": route_counts["metric_edge_audit_candidate"],
        "needs_user_review_count": route_counts["needs_user_review"],
        "unclassified_count": unclassified_count,
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
            "coverage_gap_source_rows": str(output / "coverage_gap_source_rows.csv"),
            "coverage_gap_axis_summary": str(output / "coverage_gap_axis_summary.csv"),
            "coverage_gap_support_policy_summary": str(output / "coverage_gap_support_policy_summary.csv"),
            "coverage_gap_recommended_route_summary": str(output / "coverage_gap_recommended_route_summary.csv"),
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
    parser.add_argument("--support-dir", type=Path, default=DEFAULT_SUPPORT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-coverage-gap-row-count", type=int, default=DEFAULT_TARGET_COVERAGE_GAP_ROW_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_support_coverage_gap_source_mapping(
        rescore_dir=args.rescore_dir,
        residual_dir=args.residual_dir,
        support_dir=args.support_dir,
        output_dir=args.output_dir,
        target_coverage_gap_row_count=int(args.target_coverage_gap_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"coverage_gap_row_count={summary['coverage_gap_row_count']}")
    print(
        "support_policy_coverage_materialization_candidate_count="
        f"{summary['support_policy_coverage_materialization_candidate_count']}"
    )
    print(f"scenario_or_support_redesign_candidate_count={summary['scenario_or_support_redesign_candidate_count']}")
    print(f"unclassified_count={summary['unclassified_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
