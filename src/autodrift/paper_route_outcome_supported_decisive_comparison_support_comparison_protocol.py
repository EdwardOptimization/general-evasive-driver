"""No-rerun support-matrix materialization for M2134 comparison-support panel units."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path("runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json")
DEFAULT_PANEL_UNITS = Path(
    "runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/controlled_panel_units.csv"
)
DEFAULT_EXCLUDED = Path(
    "runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/excluded_qualified_candidates.csv"
)
DEFAULT_CLAIM_BOUNDARY = Path(
    "runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/claim_boundary.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol"
)
DEFAULT_NEXT_BLOCKER = (
    "m2139-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-materialization-audit"
)

DISALLOWED_CLAIMS = {
    "controller_family_ranking",
    "finite_window_vs_gru_conclusion",
    "paper_level_benchmark_result",
    "level3_self_identification",
}
PRIMARY_SLICE_KINDS = {"outcome_by_intent_source_kind", "outcome_by_source_kind"}
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

NORMALIZED_PANEL_FIELDNAMES = [
    "panel_unit_id",
    "source_kind",
    "comparison_support_intent",
    "generated_proxy_boundary_only",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "success_profile_count",
    "success_source_count",
    "profiles_with_success",
    "sources_with_success",
]
SUPPORT_MATRIX_FIELDNAMES = [
    "panel_unit_id",
    "source_kind",
    "comparison_support_intent",
    "profile_label",
    "observed_success_support",
    "absence_semantics",
    "generated_proxy_boundary_only",
    "unit_success_rate",
    "unit_collision_rate",
    "unit_offtrack_outcome_rate",
]
PROFILE_SUMMARY_FIELDNAMES = [
    "profile_label",
    "profile_supported_unit_count",
    "profile_supported_unit_fraction",
    "profile_supported_intent_count",
    "profile_supported_source_kind_count",
    "profile_collision_relief_support_count",
    "profile_discriminative_boundary_support_count",
    "profile_support_ladder_medium_support_count",
    "profile_generated_proxy_boundary_only",
    "supported_panel_units",
    "supported_source_kinds",
    "supported_intents",
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


def split_profiles(value: Any) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _profile_sort_key(label: str) -> tuple[int, str]:
    prefix_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    prefix = label.split("_", 1)[0]
    return (prefix_rank.get(prefix, 99), label)


def _normal_panel_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "panel_unit_id": row.get("panel_unit_id", ""),
        "source_kind": row.get("source_kind", ""),
        "comparison_support_intent": row.get("comparison_support_intent", ""),
        "generated_proxy_boundary_only": _bool(row.get("generated_proxy_boundary_only")),
        "episode_count": _int(row.get("episode_count")),
        "success_count": _int(row.get("success_count")),
        "collision_count": _int(row.get("collision_count")),
        "offtrack_outcome_count": _int(row.get("offtrack_outcome_count")),
        "success_rate": _float(row.get("success_rate")),
        "collision_rate": _float(row.get("collision_rate")),
        "offtrack_outcome_rate": _float(row.get("offtrack_outcome_rate")),
        "success_profile_count": _int(row.get("success_profile_count")),
        "success_source_count": _int(row.get("success_source_count")),
        "profiles_with_success": ";".join(split_profiles(row.get("profiles_with_success"))),
        "sources_with_success": row.get("sources_with_success", ""),
    }


def _matrix_rows(panel_rows: list[dict[str, Any]], profile_labels: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel_row in panel_rows:
        profiles = set(split_profiles(panel_row.get("profiles_with_success")))
        for profile in profile_labels:
            supported = profile in profiles
            rows.append(
                {
                    "panel_unit_id": panel_row.get("panel_unit_id", ""),
                    "source_kind": panel_row.get("source_kind", ""),
                    "comparison_support_intent": panel_row.get("comparison_support_intent", ""),
                    "profile_label": profile,
                    "observed_success_support": supported,
                    "absence_semantics": "observed_success_support"
                    if supported
                    else "no_success_support_observed_in_m2134_aggregate",
                    "generated_proxy_boundary_only": _bool(panel_row.get("generated_proxy_boundary_only")),
                    "unit_success_rate": _float(panel_row.get("success_rate")),
                    "unit_collision_rate": _float(panel_row.get("collision_rate")),
                    "unit_offtrack_outcome_rate": _float(panel_row.get("offtrack_outcome_rate")),
                }
            )
    return rows


def _profile_summary_rows(matrix_rows: list[dict[str, Any]], panel_unit_count: int) -> list[dict[str, Any]]:
    profiles = sorted({str(row["profile_label"]) for row in matrix_rows}, key=_profile_sort_key)
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        supported = [row for row in matrix_rows if row["profile_label"] == profile and _bool(row["observed_success_support"])]
        intents = sorted({str(row["comparison_support_intent"]) for row in supported if row.get("comparison_support_intent")})
        source_kinds = sorted({str(row["source_kind"]) for row in supported if row.get("source_kind")})
        panel_units = sorted({str(row["panel_unit_id"]) for row in supported if row.get("panel_unit_id")})
        rows.append(
            {
                "profile_label": profile,
                "profile_supported_unit_count": len(panel_units),
                "profile_supported_unit_fraction": (len(panel_units) / panel_unit_count) if panel_unit_count else 0.0,
                "profile_supported_intent_count": len(intents),
                "profile_supported_source_kind_count": len(source_kinds),
                "profile_collision_relief_support_count": sum(
                    1 for row in supported if row.get("comparison_support_intent") == "collision_relief_probe"
                ),
                "profile_discriminative_boundary_support_count": sum(
                    1 for row in supported if row.get("comparison_support_intent") == "discriminative_boundary"
                ),
                "profile_support_ladder_medium_support_count": sum(
                    1 for row in supported if row.get("comparison_support_intent") == "support_ladder_medium"
                ),
                "profile_generated_proxy_boundary_only": bool(supported)
                and all(_bool(row.get("generated_proxy_boundary_only")) for row in supported),
                "supported_panel_units": ";".join(panel_units),
                "supported_source_kinds": ";".join(source_kinds),
                "supported_intents": ";".join(intents),
            }
        )
    return rows


def _metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "profile_supported_unit_count",
            "admissible": True,
            "reason": "counts observed success support across non-overlapping panel units",
        },
        {
            "metric": "profile_supported_intent_count",
            "admissible": True,
            "reason": "counts intent diversity of observed success support",
        },
        {
            "metric": "profile_supported_source_kind_count",
            "admissible": True,
            "reason": "counts source-kind diversity of observed success support",
        },
        {
            "metric": "per_profile_success_rate",
            "admissible": False,
            "reason": "M2134 does not carry per-profile denominators",
        },
        {
            "metric": "winner_or_rank",
            "admissible": False,
            "reason": "M2138 materializes support coverage only and does not rank controller families",
        },
        {
            "metric": "finite_window_vs_gru_verdict",
            "admissible": False,
            "reason": "support matrix is not a controlled finite-window-vs-GRU comparison",
        },
        {
            "metric": "paper_level_benchmark_verdict",
            "admissible": False,
            "reason": "generated proxy rows remain paper_validity_claim false",
        },
        {
            "metric": "level3_self_id_verdict",
            "admissible": False,
            "reason": "materialization does not run history-necessity interventions",
        },
    ]


def _claim_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = list(source_rows)
    rows.append(
        {
            "claim": "comparison_protocol_materialization_completed",
            "admissible": True,
            "reason": "M2138 materializes support-matrix artifacts without rerun or ranking",
        }
    )
    rows.extend(
        [
            {
                "claim": "controller_family_ranking",
                "admissible": False,
                "reason": "support matrix records coverage only and is not a ranking experiment",
            },
            {
                "claim": "finite_window_vs_gru_conclusion",
                "admissible": False,
                "reason": "support matrix lacks controlled per-profile denominators",
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


def _claim_boundary_violation_count(claim_rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in claim_rows:
        if str(row.get("claim", "")) in DISALLOWED_CLAIMS and _bool(row.get("admissible")):
            count += 1
    return count


def materialize_comparison_protocol(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    controlled_panel_units_path: Path | str = DEFAULT_PANEL_UNITS,
    excluded_qualified_candidates_path: Path | str = DEFAULT_EXCLUDED,
    claim_boundary_path: Path | str = DEFAULT_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    min_panel_units: int = 6,
    min_profile_labels: int = 3,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_summary = read_json(summary_path)
    raw_panel_rows = read_csv_rows(controlled_panel_units_path)
    excluded_rows = read_csv_rows(excluded_qualified_candidates_path)
    source_claim_rows = read_csv_rows(claim_boundary_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    panel_rows = [_normal_panel_row(row) for row in raw_panel_rows]
    profile_labels = sorted(
        {profile for row in panel_rows for profile in split_profiles(row.get("profiles_with_success"))},
        key=_profile_sort_key,
    )
    support_matrix_rows = _matrix_rows(panel_rows, profile_labels)
    profile_summary_rows = _profile_summary_rows(support_matrix_rows, len(panel_rows))
    metric_contract_rows = _metric_contract_rows()
    claim_boundary_rows = _claim_boundary_rows(source_claim_rows)

    source_kinds = [str(row.get("source_kind", "")) for row in panel_rows if row.get("source_kind")]
    source_kind_counts = Counter(source_kinds)
    intents = sorted(
        {str(row.get("comparison_support_intent", "")) for row in panel_rows if row.get("comparison_support_intent")}
    )
    direct_broad_aggregate_count = sum(
        1
        for row in raw_panel_rows
        if str(row.get("slice_kind", "")) not in PRIMARY_SLICE_KINDS or not str(row.get("source_kind", "")).strip()
    )
    generated_proxy_boundary_count = sum(1 for row in panel_rows if _bool(row.get("generated_proxy_boundary_only")))
    duplicate_source_kind_count = len(source_kinds) - len(source_kind_counts)
    claim_boundary_violation_count = _claim_boundary_violation_count(claim_boundary_rows)
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
    expected_matrix_rows = len(panel_rows) * len(profile_labels)
    result_pass = (
        source_summary.get("result_class") == "comparison_support_controlled_panel_construction_pass"
        and len(panel_rows) >= min_panel_units
        and len(source_kind_counts) >= min_panel_units
        and duplicate_source_kind_count == 0
        and direct_broad_aggregate_count == 0
        and len(profile_labels) >= min_profile_labels
        and len(support_matrix_rows) == expected_matrix_rows
        and generated_proxy_boundary_count == len(panel_rows)
        and claim_boundary_violation_count == 0
        and guardrail_violation_count == 0
    )

    artifacts = {
        "summary": str(output_path / "summary.json"),
        "comparison_protocol": str(output_path / "comparison_protocol.json"),
        "panel_units_normalized": str(output_path / "panel_units_normalized.csv"),
        "profile_support_matrix": str(output_path / "profile_support_matrix.csv"),
        "profile_support_summary": str(output_path / "profile_support_summary.csv"),
        "metric_contract": str(output_path / "metric_contract.csv"),
        "claim_boundary": str(output_path / "claim_boundary.csv"),
        "run_state": str(output_path / "run_state.json"),
    }
    protocol = {
        "protocol_name": "m2138_comparison_support_support_matrix",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "support matrix only; no ranking, paper, finite-window-vs-GRU, or self-ID claim",
        "source_summary_path": str(summary_path),
        "controlled_panel_units_path": str(controlled_panel_units_path),
        "excluded_qualified_candidates_path": str(excluded_qualified_candidates_path),
        "claim_boundary_path": str(claim_boundary_path),
        "panel_unit_ids": [str(row.get("panel_unit_id", "")) for row in panel_rows],
        "profile_labels": profile_labels,
        "allowed_metrics": [row["metric"] for row in metric_contract_rows if _bool(row["admissible"])],
        "blocked_metrics": [row["metric"] for row in metric_contract_rows if not _bool(row["admissible"])],
        "absence_semantics": "no_success_support_observed_in_m2134_aggregate",
    }
    write_csv_rows(artifacts["panel_units_normalized"], panel_rows, NORMALIZED_PANEL_FIELDNAMES)
    write_csv_rows(artifacts["profile_support_matrix"], support_matrix_rows, SUPPORT_MATRIX_FIELDNAMES)
    write_csv_rows(artifacts["profile_support_summary"], profile_summary_rows, PROFILE_SUMMARY_FIELDNAMES)
    write_csv_rows(artifacts["metric_contract"], metric_contract_rows, METRIC_CONTRACT_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_boundary_rows, CLAIM_BOUNDARY_FIELDNAMES)
    write_json(artifacts["comparison_protocol"], protocol)
    write_run_state(
        output_path / "run_state.json",
        {
            "result_class": "comparison_support_comparison_protocol_materialization_pass"
            if result_pass
            else "comparison_support_comparison_protocol_materialization_fail",
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
        "result_class": "comparison_support_comparison_protocol_materialization_pass"
        if result_pass
        else "comparison_support_comparison_protocol_materialization_fail",
        "materialization_status": "materialization_pass"
        if result_pass
        else "materialization_blocked_panel_or_claim_contract_violation",
        "generated_at_utc": utc_timestamp(),
        "source_summary_path": str(summary_path),
        "source_result_class": source_summary.get("result_class"),
        "controlled_panel_units_path": str(controlled_panel_units_path),
        "excluded_qualified_candidates_path": str(excluded_qualified_candidates_path),
        "source_excluded_qualified_candidate_count": len(excluded_rows),
        "panel_unit_count": len(panel_rows),
        "min_panel_units": min_panel_units,
        "profile_label_count": len(profile_labels),
        "min_profile_labels": min_profile_labels,
        "profile_labels": profile_labels,
        "support_matrix_row_count": len(support_matrix_rows),
        "expected_support_matrix_row_count": expected_matrix_rows,
        "supported_intent_count": len(intents),
        "supported_intents": intents,
        "supported_source_kind_count": len(source_kind_counts),
        "panel_duplicate_source_kind_count": duplicate_source_kind_count,
        "direct_broad_aggregate_panel_unit_count": direct_broad_aggregate_count,
        "generated_proxy_boundary_panel_unit_count": generated_proxy_boundary_count,
        "claim_boundary_violation_count": claim_boundary_violation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "per_profile_rate_computed": False,
        "winner_or_rank_computed": False,
        "required_files_written": True,
        "next_blocker": next_blocker,
        "artifacts": artifacts,
    }
    write_json(artifacts["summary"], summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--controlled-panel-units", type=Path, default=DEFAULT_PANEL_UNITS)
    parser.add_argument("--excluded-qualified-candidates", type=Path, default=DEFAULT_EXCLUDED)
    parser.add_argument("--claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-panel-units", type=int, default=6)
    parser.add_argument("--min-profile-labels", type=int, default=3)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_comparison_protocol(
        summary_path=args.summary,
        controlled_panel_units_path=args.controlled_panel_units,
        excluded_qualified_candidates_path=args.excluded_qualified_candidates,
        claim_boundary_path=args.claim_boundary,
        output_dir=args.output_dir,
        min_panel_units=args.min_panel_units,
        min_profile_labels=args.min_profile_labels,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_unit_count={summary['panel_unit_count']}")
    print(f"profile_label_count={summary['profile_label_count']}")
    print(f"support_matrix_row_count={summary['support_matrix_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == "comparison_support_comparison_protocol_materialization_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
