"""No-rerun denominator-source inventory for comparison-support panel units."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_PROTOCOL_SUMMARY = Path(
    "runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json"
)
DEFAULT_PANEL_UNITS = Path(
    "runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/panel_units_normalized.csv"
)
DEFAULT_SUPPORT_MATRIX = Path(
    "runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_matrix.csv"
)
DEFAULT_PROTOCOL_CLAIM_BOUNDARY = Path(
    "runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/claim_boundary.csv"
)
DEFAULT_PROFILE_SOURCE_KIND = Path(
    "runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/"
    "outcome_by_profile_source_kind.csv"
)
DEFAULT_MEASURED_SUMMARY = Path(
    "runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json"
)
DEFAULT_PROFILE_AGGREGATE = Path(
    "runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/profile_aggregate.csv"
)
DEFAULT_MEASURED_CLAIM_BOUNDARY = Path(
    "runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/claim_boundary.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory"
)
DEFAULT_NEXT_BLOCKER = (
    "m2142-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-audit"
)

DISALLOWED_CLAIMS = {
    "controller_family_ranking",
    "finite_window_vs_gru_conclusion",
    "paper_level_benchmark_result",
    "level3_self_identification",
}
FORBIDDEN_LOCAL_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)

DENOMINATOR_FIELDNAMES = [
    "panel_unit_id",
    "source_kind",
    "comparison_support_intent",
    "profile_label",
    "availability_label",
    "denominator_source_artifact",
    "denominator_source_row_count",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "clearance_margin_mean",
    "return_mean",
    "steps_mean",
    "all_selected_metrics_finite",
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
    "termination_off_track",
    "termination_obstacle_collision",
    "termination_empty",
    "observed_success_support",
    "support_absence_semantics",
    "generated_proxy_boundary_only",
]
PROFILE_SUMMARY_FIELDNAMES = [
    "profile_label",
    "expected_source_kind_count",
    "available_denominator_count",
    "missing_denominator_count",
    "duplicate_denominator_count",
    "nonfinite_denominator_count",
    "episode_count_sum",
    "success_count_sum",
    "collision_count_sum",
    "offtrack_outcome_count_sum",
]
SOURCE_KIND_SUMMARY_FIELDNAMES = [
    "source_kind",
    "expected_profile_count",
    "available_denominator_count",
    "missing_denominator_count",
    "duplicate_denominator_count",
    "nonfinite_denominator_count",
    "episode_count_sum",
    "success_count_sum",
    "collision_count_sum",
    "offtrack_outcome_count_sum",
]
METRIC_CONTRACT_FIELDNAMES = ["metric", "admissible", "reason"]
CLAIM_BOUNDARY_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _profile_sort_key(label: str) -> tuple[int, str]:
    prefix_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    prefix = label.split("_", 1)[0]
    return (prefix_rank.get(prefix, 99), label)


def _claim_boundary_violation_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("claim") in DISALLOWED_CLAIMS and _bool(row.get("admissible")))


def _claim_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = list(source_rows)
    rows.append(
        {
            "claim": "denominator_source_inventory_completed",
            "admissible": True,
            "reason": "M2141 inventories denominator rows from existing artifacts without rerun or ranking",
        }
    )
    rows.extend(
        [
            {
                "claim": "controller_family_ranking",
                "admissible": False,
                "reason": "denominator inventory records availability only and is not a ranking experiment",
            },
            {
                "claim": "finite_window_vs_gru_conclusion",
                "admissible": False,
                "reason": "denominator inventory does not run a controlled comparison",
            },
            {
                "claim": "paper_level_benchmark_result",
                "admissible": False,
                "reason": "generated comparison-support rows remain smoke proxies",
            },
            {
                "claim": "level3_self_identification",
                "admissible": False,
                "reason": "no history-necessity intervention is run",
            },
        ]
    )
    return rows


def _metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "episode_count",
            "admissible": True,
            "reason": "denominator field copied from existing profile-source-kind aggregate",
        },
        {
            "metric": "success_count",
            "admissible": True,
            "reason": "row-level numerator copied for later audited comparison design",
        },
        {
            "metric": "collision_count",
            "admissible": True,
            "reason": "row-level numerator copied for later audited comparison design",
        },
        {
            "metric": "success_rate",
            "admissible": True,
            "reason": "row-level aggregate is copied but not ranked",
        },
        {
            "metric": "winner_or_rank",
            "admissible": False,
            "reason": "inventory does not compare or rank profiles",
        },
        {
            "metric": "finite_window_vs_gru_verdict",
            "admissible": False,
            "reason": "inventory is not a controlled family comparison",
        },
        {
            "metric": "paper_level_benchmark_verdict",
            "admissible": False,
            "reason": "generated proxy rows remain paper_validity_claim false",
        },
        {
            "metric": "level3_self_id_verdict",
            "admissible": False,
            "reason": "inventory does not test history necessity",
        },
    ]


def _support_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], tuple[bool, str]]:
    lookup: dict[tuple[str, str], tuple[bool, str]] = {}
    for row in rows:
        key = (str(row.get("source_kind", "")), str(row.get("profile_label", "")))
        lookup[key] = (
            _bool(row.get("observed_success_support")),
            str(row.get("absence_semantics", "")),
        )
    return lookup


def _index_profile_source_kind(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("slice_kind") != "outcome_by_profile_source_kind":
            continue
        index[(str(row.get("profile_name", "")), str(row.get("source_kind", "")))].append(row)
    return index


def _denominator_row(
    *,
    panel_row: Mapping[str, Any],
    profile_label: str,
    source_rows: list[dict[str, str]],
    source_artifact: Path | str,
    support_lookup: dict[tuple[str, str], tuple[bool, str]],
    claim_boundary_blocked: bool,
) -> dict[str, Any]:
    source_kind = str(panel_row.get("source_kind", ""))
    support_key = (source_kind, profile_label)
    observed_support, absence_semantics = support_lookup.get(
        support_key,
        (False, "profile_not_in_m2138_success_support_union"),
    )

    if claim_boundary_blocked:
        label = "claim_boundary_blocked"
        source: Mapping[str, Any] = {}
    elif not source_rows:
        label = "missing_profile_source_kind_denominator"
        source = {}
    elif len(source_rows) > 1:
        label = "duplicate_profile_source_kind_denominator"
        source = source_rows[0]
    elif not _bool(source_rows[0].get("all_selected_metrics_finite")):
        label = "nonfinite_denominator_metrics"
        source = source_rows[0]
    else:
        label = "denominator_available_from_profile_source_kind_aggregate"
        source = source_rows[0]

    return {
        "panel_unit_id": panel_row.get("panel_unit_id", ""),
        "source_kind": source_kind,
        "comparison_support_intent": panel_row.get("comparison_support_intent", ""),
        "profile_label": profile_label,
        "availability_label": label,
        "denominator_source_artifact": str(source_artifact),
        "denominator_source_row_count": len(source_rows),
        "episode_count": _int(source.get("episode_count")),
        "success_count": _int(source.get("success_count") or source.get("success_obstacle_pass")),
        "collision_count": _int(source.get("collision_count") or source.get("collision_failure")),
        "offtrack_outcome_count": _int(source.get("offtrack_outcome_count") or source.get("off_track_noncollision_noncompletion")),
        "success_rate": _float(source.get("success_rate")),
        "collision_rate": _float(source.get("collision_rate")),
        "offtrack_outcome_rate": _float(source.get("offtrack_outcome_rate")),
        "clearance_margin_mean": _float(source.get("clearance_margin_mean")),
        "return_mean": _float(source.get("return_mean")),
        "steps_mean": _float(source.get("steps_mean")),
        "all_selected_metrics_finite": _bool(source.get("all_selected_metrics_finite")),
        "success_obstacle_pass": _int(source.get("success_obstacle_pass")),
        "collision_failure": _int(source.get("collision_failure")),
        "off_track_noncollision_noncompletion": _int(source.get("off_track_noncollision_noncompletion")),
        "termination_off_track": _int(source.get("termination_off_track")),
        "termination_obstacle_collision": _int(source.get("termination_obstacle_collision")),
        "termination_empty": _int(source.get("termination_empty")),
        "observed_success_support": observed_support,
        "support_absence_semantics": absence_semantics if not observed_support else "observed_success_support",
        "generated_proxy_boundary_only": _bool(panel_row.get("generated_proxy_boundary_only")),
    }


def _availability_summary(rows: list[dict[str, Any]], key_field: str, expected_count_field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key_field])].append(row)
    output: list[dict[str, Any]] = []
    for key, group_rows in sorted(groups.items(), key=lambda item: _profile_sort_key(item[0]) if key_field == "profile_label" else (0, item[0])):
        counts = Counter(str(row["availability_label"]) for row in group_rows)
        output.append(
            {
                key_field: key,
                expected_count_field: len(group_rows),
                "available_denominator_count": counts.get("denominator_available_from_profile_source_kind_aggregate", 0),
                "missing_denominator_count": counts.get("missing_profile_source_kind_denominator", 0),
                "duplicate_denominator_count": counts.get("duplicate_profile_source_kind_denominator", 0),
                "nonfinite_denominator_count": counts.get("nonfinite_denominator_metrics", 0),
                "episode_count_sum": sum(_int(row.get("episode_count")) for row in group_rows),
                "success_count_sum": sum(_int(row.get("success_count")) for row in group_rows),
                "collision_count_sum": sum(_int(row.get("collision_count")) for row in group_rows),
                "offtrack_outcome_count_sum": sum(_int(row.get("offtrack_outcome_count")) for row in group_rows),
            }
        )
    return output


def materialize_denominator_inventory(
    *,
    protocol_summary_path: Path | str = DEFAULT_PROTOCOL_SUMMARY,
    panel_units_path: Path | str = DEFAULT_PANEL_UNITS,
    support_matrix_path: Path | str = DEFAULT_SUPPORT_MATRIX,
    protocol_claim_boundary_path: Path | str = DEFAULT_PROTOCOL_CLAIM_BOUNDARY,
    profile_source_kind_path: Path | str = DEFAULT_PROFILE_SOURCE_KIND,
    measured_summary_path: Path | str = DEFAULT_MEASURED_SUMMARY,
    profile_aggregate_path: Path | str = DEFAULT_PROFILE_AGGREGATE,
    measured_claim_boundary_path: Path | str = DEFAULT_MEASURED_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    expected_panel_units: int = 6,
    expected_profile_count: int = 5,
    expected_denominator_count: int = 30,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    protocol_summary = read_json(protocol_summary_path)
    measured_summary = read_json(measured_summary_path)
    panel_rows = read_csv_rows(panel_units_path)
    support_rows = read_csv_rows(support_matrix_path)
    profile_source_kind_rows = read_csv_rows(profile_source_kind_path)
    profile_aggregate_rows = read_csv_rows(profile_aggregate_path)
    claim_rows = read_csv_rows(protocol_claim_boundary_path) + read_csv_rows(measured_claim_boundary_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    measured_profiles = sorted(
        {str(row.get("key", "")) for row in profile_aggregate_rows if row.get("key")},
        key=_profile_sort_key,
    )
    support = _support_lookup(support_rows)
    source_index = _index_profile_source_kind(profile_source_kind_rows)
    claim_boundary_violation_count = _claim_boundary_violation_count(claim_rows)
    claim_boundary_blocked = claim_boundary_violation_count > 0

    inventory_rows: list[dict[str, Any]] = []
    for panel_row in panel_rows:
        for profile_label in measured_profiles:
            source_rows = source_index.get((profile_label, str(panel_row.get("source_kind", ""))), [])
            inventory_rows.append(
                _denominator_row(
                    panel_row=panel_row,
                    profile_label=profile_label,
                    source_rows=source_rows,
                    source_artifact=profile_source_kind_path,
                    support_lookup=support,
                    claim_boundary_blocked=claim_boundary_blocked,
                )
            )

    profile_summary_rows = _availability_summary(inventory_rows, "profile_label", "expected_source_kind_count")
    source_kind_summary_rows = _availability_summary(inventory_rows, "source_kind", "expected_profile_count")
    metric_contract_rows = _metric_contract_rows()
    output_claim_rows = _claim_boundary_rows(claim_rows)
    availability_counts = Counter(str(row["availability_label"]) for row in inventory_rows)
    available_count = availability_counts.get("denominator_available_from_profile_source_kind_aggregate", 0)
    missing_count = availability_counts.get("missing_profile_source_kind_denominator", 0)
    duplicate_count = availability_counts.get("duplicate_profile_source_kind_denominator", 0)
    nonfinite_count = availability_counts.get("nonfinite_denominator_metrics", 0)
    expected_count = len(panel_rows) * len(measured_profiles)

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
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for key in FORBIDDEN_LOCAL_GUARDRAILS if guardrail_flags.get(key))
    result_pass = (
        protocol_summary.get("result_class") == "comparison_support_comparison_protocol_materialization_pass"
        and measured_summary.get("result_class") == "comparison_support_measured_execution_pass"
        and len(panel_rows) == expected_panel_units
        and len(measured_profiles) == expected_profile_count
        and len(inventory_rows) == expected_count
        and expected_count == expected_denominator_count
        and available_count == expected_count
        and missing_count == 0
        and duplicate_count == 0
        and nonfinite_count == 0
        and claim_boundary_violation_count == 0
        and guardrail_violation_count == 0
    )

    artifacts = {
        "summary": str(output_path / "summary.json"),
        "denominator_inventory_rows": str(output_path / "denominator_inventory_rows.csv"),
        "profile_denominator_summary": str(output_path / "profile_denominator_summary.csv"),
        "source_kind_denominator_summary": str(output_path / "source_kind_denominator_summary.csv"),
        "metric_contract": str(output_path / "metric_contract.csv"),
        "claim_boundary": str(output_path / "claim_boundary.csv"),
        "run_state": str(output_path / "run_state.json"),
    }
    write_csv_rows(artifacts["denominator_inventory_rows"], inventory_rows, DENOMINATOR_FIELDNAMES)
    write_csv_rows(artifacts["profile_denominator_summary"], profile_summary_rows, PROFILE_SUMMARY_FIELDNAMES)
    write_csv_rows(artifacts["source_kind_denominator_summary"], source_kind_summary_rows, SOURCE_KIND_SUMMARY_FIELDNAMES)
    write_csv_rows(artifacts["metric_contract"], metric_contract_rows, METRIC_CONTRACT_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], output_claim_rows, CLAIM_BOUNDARY_FIELDNAMES)
    write_run_state(
        output_path / "run_state.json",
        {
            "result_class": "comparison_support_denominator_source_inventory_pass"
            if result_pass
            else "comparison_support_denominator_source_inventory_fail",
            "environment_reset_started": False,
            "environment_rollout_started": False,
            "policy_action_executed": False,
            "measured_rollout_started": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
        },
    )

    summary: dict[str, Any] = {
        "result_class": "comparison_support_denominator_source_inventory_pass"
        if result_pass
        else "comparison_support_denominator_source_inventory_fail",
        "generated_at_utc": utc_timestamp(),
        "protocol_summary_path": str(protocol_summary_path),
        "protocol_result_class": protocol_summary.get("result_class"),
        "measured_summary_path": str(measured_summary_path),
        "source_result_class": measured_summary.get("result_class"),
        "profile_source_kind_path": str(profile_source_kind_path),
        "panel_unit_count": len(panel_rows),
        "expected_panel_unit_count": expected_panel_units,
        "measured_profile_count": len(measured_profiles),
        "expected_measured_profile_count": expected_profile_count,
        "measured_profiles": measured_profiles,
        "configured_expected_denominator_row_count": expected_denominator_count,
        "expected_denominator_row_count": expected_count,
        "denominator_inventory_row_count": len(inventory_rows),
        "available_denominator_row_count": available_count,
        "missing_denominator_row_count": missing_count,
        "duplicate_denominator_row_count": duplicate_count,
        "nonfinite_denominator_row_count": nonfinite_count,
        "availability_counts": dict(sorted(availability_counts.items())),
        "claim_boundary_violation_count": claim_boundary_violation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "winner_or_rank_computed": False,
        "finite_window_vs_gru_verdict_computed": False,
        "required_files_written": True,
        "next_blocker": next_blocker,
        "artifacts": artifacts,
    }
    write_json(artifacts["summary"], summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-summary", type=Path, default=DEFAULT_PROTOCOL_SUMMARY)
    parser.add_argument("--panel-units", type=Path, default=DEFAULT_PANEL_UNITS)
    parser.add_argument("--support-matrix", type=Path, default=DEFAULT_SUPPORT_MATRIX)
    parser.add_argument("--protocol-claim-boundary", type=Path, default=DEFAULT_PROTOCOL_CLAIM_BOUNDARY)
    parser.add_argument("--profile-source-kind", type=Path, default=DEFAULT_PROFILE_SOURCE_KIND)
    parser.add_argument("--measured-summary", type=Path, default=DEFAULT_MEASURED_SUMMARY)
    parser.add_argument("--profile-aggregate", type=Path, default=DEFAULT_PROFILE_AGGREGATE)
    parser.add_argument("--measured-claim-boundary", type=Path, default=DEFAULT_MEASURED_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--expected-panel-units", type=int, default=6)
    parser.add_argument("--expected-profile-count", type=int, default=5)
    parser.add_argument("--expected-denominator-count", type=int, default=30)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_denominator_inventory(
        protocol_summary_path=args.protocol_summary,
        panel_units_path=args.panel_units,
        support_matrix_path=args.support_matrix,
        protocol_claim_boundary_path=args.protocol_claim_boundary,
        profile_source_kind_path=args.profile_source_kind,
        measured_summary_path=args.measured_summary,
        profile_aggregate_path=args.profile_aggregate,
        measured_claim_boundary_path=args.measured_claim_boundary,
        output_dir=args.output_dir,
        expected_panel_units=args.expected_panel_units,
        expected_profile_count=args.expected_profile_count,
        expected_denominator_count=args.expected_denominator_count,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_unit_count={summary['panel_unit_count']}")
    print(f"measured_profile_count={summary['measured_profile_count']}")
    print(f"denominator_inventory_row_count={summary['denominator_inventory_row_count']}")
    print(f"available_denominator_row_count={summary['available_denominator_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == "comparison_support_denominator_source_inventory_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
