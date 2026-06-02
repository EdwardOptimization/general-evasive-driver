"""Artifact-only role-stratified residual support rescore."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_RESIDUAL_DIR = Path("runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit")
DEFAULT_ROLE_REDESIGN_DIR = Path("runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign")
DEFAULT_R4_SEMANTICS_DIR = Path("runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics")
DEFAULT_OUTPUT_DIR = Path("runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore")
DEFAULT_TARGET_RESIDUAL_SCENARIO_COUNT = 48
DEFAULT_NEXT_BLOCKER = "m2337-paper-route-current-sim-role-stratified-residual-support-rescore-result-audit"
R4_ROLE_FAMILY = "R4_unavoidable_mitigation"
RESCORE_FIELDNAMES = [
    "scenario_spec_id",
    "role_family",
    "old_support_label",
    "old_primary_route_label",
    "old_design_route_label",
    "rescore_route_label",
    "rescore_category",
    "rescore_reason",
    "requires_artifact_only_followup",
    "requires_new_rollout",
    "requires_post_collision_continuation",
    "comparison_admissibility",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
ROLE_SUMMARY_FIELDNAMES = [
    "role_family",
    "residual_count",
    "support_policy_coverage_gap_count",
    "scenario_or_support_redesign_gap_count",
    "r4_proxy_semantics_post_collision_blocked_count",
    "metric_semantics_edge_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROUTE_SUMMARY_FIELDNAMES = [
    "rescore_route_label",
    "rescore_category",
    "residual_count",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = [
    "claim",
    "allowed",
    "made",
    "reason",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _r4_semantics_map(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("scenario_spec_id", "")): row for row in rows}


def _rescore_non_r4(row: Mapping[str, Any]) -> tuple[str, str, str]:
    design_route = str(row.get("design_route_label", ""))
    if design_route == "support_policy_coverage_materialization_required":
        return (
            "support_policy_coverage_gap",
            "support_policy_coverage_gap",
            "partial diagnostic support exists but support-policy coverage remains insufficient",
        )
    if design_route == "scenario_or_support_redesign_materialization_required":
        return (
            "scenario_or_support_redesign_gap",
            "scenario_or_support_redesign_gap",
            "no current support policy provides enough support; scenario or support needs redesign",
        )
    if design_route == "metric_semantics_edge_case":
        return (
            "metric_semantics_edge_case",
            "metric_semantics_edge_case",
            "metric semantics edge case remains after R0 and R4 semantics repairs",
        )
    return (
        "unclassified_residual_route",
        "unclassified_residual_route",
        f"unrecognized design_route_label={design_route}",
    )


def build_rescore_rows(
    *,
    role_rows: Sequence[Mapping[str, Any]],
    r4_semantics_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    semantics_by_id = _r4_semantics_map(r4_semantics_rows)
    output: list[dict[str, Any]] = []
    for row in role_rows:
        scenario_id = str(row.get("scenario_spec_id", ""))
        role_family = str(row.get("role_family", ""))
        if role_family == R4_ROLE_FAMILY:
            semantics = semantics_by_id.get(scenario_id, {})
            status = str(semantics.get("r4_metric_semantics_status", ""))
            if status == "proxy_metric_available_post_collision_blocked":
                route = "r4_proxy_metric_semantics_available_post_collision_blocked"
                category = "role_semantics_proxy_available_current_sim_limited"
                reason = "R4 impact-proxy metrics are available but post-collision canonical semantics remain blocked"
                requires_post_collision = True
                comparison = "blocked_until_rescore_audited"
            else:
                route = "r4_proxy_metric_semantics_missing"
                category = "r4_metric_semantics_gap"
                reason = "R4 semantics row is missing or not proxy-available"
                requires_post_collision = True
                comparison = "blocked_until_semantics_repaired"
        else:
            route, category, reason = _rescore_non_r4(row)
            requires_post_collision = False
            comparison = "blocked_until_rescore_audited"
        output.append(
            {
                "scenario_spec_id": scenario_id,
                "role_family": role_family,
                "old_support_label": row.get("support_label", ""),
                "old_primary_route_label": row.get("primary_route_label", ""),
                "old_design_route_label": row.get("design_route_label", ""),
                "rescore_route_label": route,
                "rescore_category": category,
                "rescore_reason": reason,
                "requires_artifact_only_followup": True,
                "requires_new_rollout": False,
                "requires_post_collision_continuation": requires_post_collision,
                "comparison_admissibility": comparison,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
    return output


def role_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("role_family", ""))].append(row)
    output: list[dict[str, Any]] = []
    for role_family in sorted(grouped):
        role_rows = grouped[role_family]
        routes = Counter(str(row.get("rescore_route_label", "")) for row in role_rows)
        output.append(
            {
                "role_family": role_family,
                "residual_count": len(role_rows),
                "support_policy_coverage_gap_count": routes["support_policy_coverage_gap"],
                "scenario_or_support_redesign_gap_count": routes["scenario_or_support_redesign_gap"],
                "r4_proxy_semantics_post_collision_blocked_count": routes[
                    "r4_proxy_metric_semantics_available_post_collision_blocked"
                ],
                "metric_semantics_edge_count": routes["metric_semantics_edge_case"],
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def route_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], int] = Counter(
        (str(row.get("rescore_route_label", "")), str(row.get("rescore_category", ""))) for row in rows
    )
    return [
        {
            "rescore_route_label": route,
            "rescore_category": category,
            "residual_count": count,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
        for (route, category), count in sorted(grouped.items())
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_residual_support_rescore",
            "allowed": True,
            "made": True,
            "reason": "M2336 only materializes residual route categories from existing artifacts.",
        },
        {
            "claim": "residual_support_solved",
            "allowed": False,
            "made": False,
            "reason": "Rescore updates categories but does not solve coverage or redesign gaps.",
        },
        {
            "claim": "controller_family_ranking",
            "allowed": False,
            "made": False,
            "reason": "No controller comparison is run.",
        },
        {
            "claim": "r4_mitigation_performance",
            "allowed": False,
            "made": False,
            "reason": "R4 proxy semantics are descriptive and post-collision metrics remain blocked.",
        },
        {
            "claim": "level3_self_identification",
            "allowed": False,
            "made": False,
            "reason": "No history intervention or self-ID test is run.",
        },
    ]


def run_role_stratified_residual_support_rescore(
    *,
    residual_dir: Path | str = DEFAULT_RESIDUAL_DIR,
    role_redesign_dir: Path | str = DEFAULT_ROLE_REDESIGN_DIR,
    r4_semantics_dir: Path | str = DEFAULT_R4_SEMANTICS_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_residual_scenario_count: int = DEFAULT_TARGET_RESIDUAL_SCENARIO_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    residual_path = Path(residual_dir)
    role_path = Path(role_redesign_dir)
    r4_path = Path(r4_semantics_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    residual_rows = read_csv_rows(residual_path / "residual_scenario_rows.csv")
    role_rows = read_csv_rows(role_path / "role_stratified_residual_rows.csv")
    r4_rows = read_csv_rows(r4_path / "r4_metric_semantics_rows.csv")
    rescored = build_rescore_rows(role_rows=role_rows, r4_semantics_rows=r4_rows)
    role_summary = role_summary_rows(rescored)
    route_summary = route_summary_rows(rescored)
    claims = claim_boundary_rows()

    write_csv_rows(output / "residual_rescore_rows.csv", rescored, fieldnames=RESCORE_FIELDNAMES)
    write_csv_rows(output / "role_rescore_summary.csv", role_summary, fieldnames=ROLE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "route_rescore_summary.csv", route_summary, fieldnames=ROUTE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    route_counts = Counter(str(row.get("rescore_route_label", "")) for row in rescored)
    ranking_admissible_count = sum(_bool_value(row.get("ranking_admissible", False)) for row in rescored)
    winner_selected_count = sum(_bool_value(row.get("winner_selected", False)) for row in rescored)
    paper_level_claim_count = sum(_bool_value(row.get("paper_level_claim_made", False)) for row in rescored)
    level3_self_id_claim_count = sum(_bool_value(row.get("level3_self_id_claim_made", False)) for row in rescored)
    guardrail_violation_count = (
        ranking_admissible_count + winner_selected_count + paper_level_claim_count + level3_self_id_claim_count
    )
    result_passes = (
        len(rescored) == int(target_residual_scenario_count)
        and len(residual_rows) == int(target_residual_scenario_count)
        and route_counts["unclassified_residual_route"] == 0
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_role_stratified_residual_support_rescore_pass"
            if result_passes
            else "current_sim_role_stratified_residual_support_rescore_incomplete_or_fail"
        ),
        "residual_dir": str(residual_path),
        "role_redesign_dir": str(role_path),
        "r4_semantics_dir": str(r4_path),
        "output_dir": str(output),
        "input_residual_scenario_count": len(residual_rows),
        "rescored_residual_scenario_count": len(rescored),
        "target_residual_scenario_count": int(target_residual_scenario_count),
        "role_summary_count": len(role_summary),
        "route_summary_count": len(route_summary),
        "r4_proxy_semantics_post_collision_blocked_count": route_counts[
            "r4_proxy_metric_semantics_available_post_collision_blocked"
        ],
        "support_policy_coverage_gap_count": route_counts["support_policy_coverage_gap"],
        "scenario_or_support_redesign_gap_count": route_counts["scenario_or_support_redesign_gap"],
        "metric_semantics_edge_count": route_counts["metric_semantics_edge_case"],
        "unclassified_residual_route_count": route_counts["unclassified_residual_route"],
        "r0_residual_count": sum(str(row.get("role_family", "")).startswith("R0_") for row in rescored),
        "r1_residual_count": sum(str(row.get("role_family", "")).startswith("R1_") for row in rescored),
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "paper_level_claim_count": paper_level_claim_count,
        "level3_self_id_claim_count": level3_self_id_claim_count,
        "guardrail_violation_count": guardrail_violation_count,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "support_policy_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
        "artifacts": {
            "residual_rescore_rows": str(output / "residual_rescore_rows.csv"),
            "role_rescore_summary": str(output / "role_rescore_summary.csv"),
            "route_rescore_summary": str(output / "route_rescore_summary.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--residual-dir", type=Path, default=DEFAULT_RESIDUAL_DIR)
    parser.add_argument("--role-redesign-dir", type=Path, default=DEFAULT_ROLE_REDESIGN_DIR)
    parser.add_argument("--r4-semantics-dir", type=Path, default=DEFAULT_R4_SEMANTICS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-residual-scenario-count", type=int, default=DEFAULT_TARGET_RESIDUAL_SCENARIO_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_role_stratified_residual_support_rescore(
        residual_dir=args.residual_dir,
        role_redesign_dir=args.role_redesign_dir,
        r4_semantics_dir=args.r4_semantics_dir,
        output_dir=args.output_dir,
        target_residual_scenario_count=int(args.target_residual_scenario_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"rescored_residual_scenario_count={summary['rescored_residual_scenario_count']}")
    print(f"r4_proxy_semantics_post_collision_blocked_count={summary['r4_proxy_semantics_post_collision_blocked_count']}")
    print(f"support_policy_coverage_gap_count={summary['support_policy_coverage_gap_count']}")
    print(f"scenario_or_support_redesign_gap_count={summary['scenario_or_support_redesign_gap_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
