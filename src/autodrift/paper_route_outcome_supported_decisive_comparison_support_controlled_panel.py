"""No-rerun controlled panel construction from qualified comparison-support rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path(
    "runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/summary.json"
)
DEFAULT_QUALIFIED = Path(
    "runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/qualified_candidates.csv"
)
DEFAULT_CLAIM_BOUNDARY = Path(
    "runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/claim_boundary.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel")
DEFAULT_NEXT_BLOCKER = (
    "m2135-paper-route-outcome-supported-decisive-comparison-support-controlled-panel-result-audit"
)

TARGET_QUALIFIED_COUNT = 15
PRIMARY_SLICE_KINDS = {"outcome_by_intent_source_kind", "outcome_by_source_kind"}
BROAD_SLICE_KINDS = {"outcome_by_proxy_template", "outcome_by_intent", "outcome_by_target_support_tier"}
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
SOURCE_FIELDS = [
    "candidate_key",
    "qualification_label",
    "slice_kind",
    "support_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "success_profile_count",
    "profiles_with_success",
    "success_source_count",
    "sources_with_success",
    "comparison_support_intent",
    "target_support_tier",
    "source_kind",
    "proxy_template_family",
    "generated_proxy_boundary_only",
]
PANEL_FIELDNAMES = [
    "panel_unit_id",
    "panel_role",
    "canonical_selection_reason",
    *SOURCE_FIELDS,
]
EXCLUDED_FIELDNAMES = [
    "candidate_key",
    "exclusion_reason",
    "slice_kind",
    "comparison_support_intent",
    "target_support_tier",
    "source_kind",
    "proxy_template_family",
]
DIAGNOSTIC_FIELDNAMES = ["metric", "value"]
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
        return float("inf")


def _candidate_sort_key(row: Mapping[str, Any]) -> tuple[int, int, float, float, str]:
    slice_rank = 0 if row.get("slice_kind") == "outcome_by_intent_source_kind" else 1
    return (
        slice_rank,
        -_int(row.get("success_count")),
        _float(row.get("collision_rate")),
        _float(row.get("offtrack_outcome_rate")),
        str(row.get("candidate_key", "")),
    )


def _panel_row(index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "panel_unit_id": f"panel_unit_{index:03d}_{row.get('source_kind', '')}",
        "panel_role": "primary_source_kind_unit",
        "canonical_selection_reason": "preferred_intent_source_kind"
        if row.get("slice_kind") == "outcome_by_intent_source_kind"
        else "fallback_source_kind",
    }
    for field in SOURCE_FIELDS:
        output[field] = row.get(field, "")
    return output


def _excluded_row(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "candidate_key": row.get("candidate_key", ""),
        "exclusion_reason": reason,
        "slice_kind": row.get("slice_kind", ""),
        "comparison_support_intent": row.get("comparison_support_intent", ""),
        "target_support_tier": row.get("target_support_tier", ""),
        "source_kind": row.get("source_kind", ""),
        "proxy_template_family": row.get("proxy_template_family", ""),
    }


def _claim_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = list(source_rows)
    rows.append(
        {
            "claim": "controlled_panel_construction_completed",
            "admissible": True,
            "reason": "M2134 materializes non-overlapping panel units without rerun or ranking",
        }
    )
    rows.append(
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "controlled panel construction is a pre-comparison artifact",
        }
    )
    return rows


def construct_controlled_panel(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    qualified_candidates_path: Path | str = DEFAULT_QUALIFIED,
    claim_boundary_path: Path | str = DEFAULT_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    min_panel_units: int = 6,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_summary = read_json(summary_path)
    qualified_rows = read_csv_rows(qualified_candidates_path)
    claim_rows = read_csv_rows(claim_boundary_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    actual_qualified_count = len(qualified_rows)
    source_qualified_count = int(source_summary.get("qualified_candidate_count", -1))
    qualified_count_matches_source = actual_qualified_count == source_qualified_count

    eligible_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    excluded_rows: list[dict[str, Any]] = []
    for row in qualified_rows:
        source_kind = str(row.get("source_kind", "")).strip()
        slice_kind = str(row.get("slice_kind", "")).strip()
        if row.get("qualification_label") != "qualified_candidate":
            excluded_rows.append(_excluded_row(row, "not_qualified_candidate"))
        elif not source_kind:
            reason = "broad_aggregate_candidate" if slice_kind in BROAD_SLICE_KINDS else "missing_source_kind"
            excluded_rows.append(_excluded_row(row, reason))
        elif slice_kind not in PRIMARY_SLICE_KINDS:
            excluded_rows.append(_excluded_row(row, "unsupported_slice_kind_for_panel_unit"))
        else:
            eligible_by_source[source_kind].append(row)

    panel_source_rows: list[dict[str, str]] = []
    for source_kind, rows in sorted(eligible_by_source.items()):
        ordered = sorted(rows, key=_candidate_sort_key)
        selected = ordered[0]
        panel_source_rows.append(selected)
        for duplicate in ordered[1:]:
            excluded_rows.append(_excluded_row(duplicate, "duplicate_source_kind_lower_priority"))

    panel_rows = [_panel_row(index, row) for index, row in enumerate(panel_source_rows)]
    panel_source_kinds = [str(row.get("source_kind", "")) for row in panel_rows]
    duplicate_source_kind_count = len(panel_source_kinds) - len(set(panel_source_kinds))
    broad_aggregate_exclusion_count = sum(
        1 for row in excluded_rows if row.get("exclusion_reason") == "broad_aggregate_candidate"
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
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for key in FORBIDDEN_LOCAL_GUARDRAILS if guardrail_flags.get(key))
    result_pass = (
        source_summary.get("result_class") == "comparison_support_candidate_qualification_pass"
        and source_qualified_count == TARGET_QUALIFIED_COUNT
        and qualified_count_matches_source
        and len(panel_rows) >= min_panel_units
        and len(set(panel_source_kinds)) >= min_panel_units
        and duplicate_source_kind_count == 0
        and broad_aggregate_exclusion_count >= 3
        and guardrail_violation_count == 0
    )

    panel_intents = {str(row.get("comparison_support_intent", "")) for row in panel_rows if row.get("comparison_support_intent")}
    claim_boundary_rows = _claim_boundary_rows(claim_rows)
    artifacts = {
        "summary": str(output_path / "summary.json"),
        "controlled_panel_units": str(output_path / "controlled_panel_units.csv"),
        "excluded_qualified_candidates": str(output_path / "excluded_qualified_candidates.csv"),
        "panel_diagnostics": str(output_path / "panel_diagnostics.csv"),
        "claim_boundary": str(output_path / "claim_boundary.csv"),
        "run_state": str(output_path / "run_state.json"),
    }
    diagnostics = [
        {"metric": "source_qualified_candidate_count", "value": source_qualified_count},
        {"metric": "actual_qualified_candidate_count", "value": actual_qualified_count},
        {"metric": "controlled_panel_unit_count", "value": len(panel_rows)},
        {"metric": "panel_source_kind_count", "value": len(set(panel_source_kinds))},
        {"metric": "panel_intent_count", "value": len(panel_intents)},
        {"metric": "panel_duplicate_source_kind_count", "value": duplicate_source_kind_count},
        {"metric": "panel_broad_aggregate_exclusion_count", "value": broad_aggregate_exclusion_count},
    ]
    write_csv_rows(artifacts["controlled_panel_units"], panel_rows, PANEL_FIELDNAMES)
    write_csv_rows(artifacts["excluded_qualified_candidates"], excluded_rows, EXCLUDED_FIELDNAMES)
    write_csv_rows(artifacts["panel_diagnostics"], diagnostics, DIAGNOSTIC_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_boundary_rows, CLAIM_BOUNDARY_FIELDNAMES)
    write_run_state(
        output_path / "run_state.json",
        {
            "result_class": "comparison_support_controlled_panel_construction_pass"
            if result_pass
            else "comparison_support_controlled_panel_construction_incomplete_or_fail",
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
        "result_class": "comparison_support_controlled_panel_construction_pass"
        if result_pass
        else "comparison_support_controlled_panel_construction_incomplete_or_fail",
        "generated_at_utc": utc_timestamp(),
        "source_summary_path": str(summary_path),
        "source_result_class": source_summary.get("result_class"),
        "source_qualified_candidate_count": source_qualified_count,
        "actual_qualified_candidate_count": actual_qualified_count,
        "qualified_count_matches_source": qualified_count_matches_source,
        "target_qualified_candidate_count": TARGET_QUALIFIED_COUNT,
        "controlled_panel_unit_count": len(panel_rows),
        "min_panel_units": min_panel_units,
        "controlled_panel_unit_threshold_pass": len(panel_rows) >= min_panel_units,
        "panel_source_kind_count": len(set(panel_source_kinds)),
        "panel_intent_count": len(panel_intents),
        "panel_duplicate_source_kind_count": duplicate_source_kind_count,
        "panel_broad_aggregate_exclusion_count": broad_aggregate_exclusion_count,
        "excluded_qualified_candidate_count": len(excluded_rows),
        "excluded_reason_counts": dict(sorted(Counter(row["exclusion_reason"] for row in excluded_rows).items())),
        "panel_source_kind_counts": dict(sorted(Counter(panel_source_kinds).items())),
        "panel_intent_counts": dict(
            sorted(Counter(str(row.get("comparison_support_intent", "")) for row in panel_rows).items())
        ),
        "required_files_written": True,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "next_blocker": next_blocker,
        "artifacts": artifacts,
    }
    write_json(output_path / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--qualified-candidates", type=Path, default=DEFAULT_QUALIFIED)
    parser.add_argument("--claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-panel-units", type=int, default=6)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = construct_controlled_panel(
        summary_path=args.summary,
        qualified_candidates_path=args.qualified_candidates,
        claim_boundary_path=args.claim_boundary,
        output_dir=args.output_dir,
        min_panel_units=args.min_panel_units,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"controlled_panel_unit_count={summary['controlled_panel_unit_count']}")
    print(f"panel_duplicate_source_kind_count={summary['panel_duplicate_source_kind_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
