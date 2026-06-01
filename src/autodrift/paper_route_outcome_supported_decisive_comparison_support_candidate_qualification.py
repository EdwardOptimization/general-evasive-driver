"""No-rerun candidate qualification for comparison-support localization outputs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SUMMARY = Path("runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/summary.json")
DEFAULT_COMPARISON_READY = Path(
    "runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/"
    "comparison_ready_candidates.csv"
)
DEFAULT_COMPARISON_SUPPORT = Path(
    "runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/"
    "comparison_support_candidates.csv"
)
DEFAULT_CLAIM_BOUNDARY = Path(
    "runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/claim_boundary.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification")
DEFAULT_NEXT_BLOCKER = (
    "m2132-paper-route-outcome-supported-decisive-comparison-support-candidate-qualification-result-audit"
)

TARGET_READY_COUNT = 15
TARGET_SUPPORT_COUNT = 37
MIN_EPISODE_COUNT = 50
MIN_SUCCESS_COUNT = 6
MIN_SUCCESS_PROFILE_COUNT = 3
MIN_SUCCESS_SOURCE_COUNT = 5
MAX_COLLISION_RATE = 0.30
MAX_OFFTRACK_RATE = 0.70

SOURCE_FIELDS = [
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
    "profile_name",
    "comparison_support_intent",
    "target_support_tier",
    "source_kind",
    "proxy_template_family",
    "generated_source_row",
    "materialization_semantics",
    "paper_validity_claim",
]
QUALIFIED_FIELDNAMES = [
    "candidate_key",
    "qualification_label",
    "rejection_reasons",
    "has_l3_success",
    "has_non_l3_success",
    "source_diverse",
    "profile_diverse",
    "low_collision_ready",
    "offtrack_bounded",
    "generated_proxy_boundary_only",
    *SOURCE_FIELDS,
]
REJECTION_FIELDNAMES = [
    "candidate_key",
    "reason",
    "support_label",
    "slice_kind",
    "comparison_support_intent",
    "target_support_tier",
    "source_kind",
    "proxy_template_family",
]
CLAIM_BOUNDARY_FIELDNAMES = ["claim", "admissible", "reason"]
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
        return float("nan")


def _split_profiles(value: Any) -> set[str]:
    return {item.strip() for item in str(value or "").split(";") if item.strip()}


def _nonempty_unique(rows: Iterable[Mapping[str, Any]], field: str) -> set[str]:
    return {str(row.get(field, "")).strip() for row in rows if str(row.get(field, "")).strip()}


def claim_boundary_blocks_paper_result(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        if str(row.get("claim", "")) == "paper_level_benchmark_result":
            return not _bool(row.get("admissible"))
    return True


def _candidate_key(index: int, row: Mapping[str, Any]) -> str:
    axes = [
        str(row.get("slice_kind", "")),
        str(row.get("comparison_support_intent", "")),
        str(row.get("target_support_tier", "")),
        str(row.get("source_kind", "")),
        str(row.get("proxy_template_family", "")),
    ]
    axis_text = "|".join(axis or "_" for axis in axes)
    return f"q{index:04d}|{axis_text}"


def _rejection_reasons(row: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if str(row.get("support_label", "")) != "comparison_ready_candidate":
        reasons.append("not_comparison_ready")
    if _int(row.get("episode_count")) < MIN_EPISODE_COUNT:
        reasons.append("insufficient_episode_count")
    if _int(row.get("success_count")) < MIN_SUCCESS_COUNT:
        reasons.append("insufficient_success_count")
    if _int(row.get("success_profile_count")) < MIN_SUCCESS_PROFILE_COUNT:
        reasons.append("insufficient_profile_coverage")
    if _int(row.get("success_source_count")) < MIN_SUCCESS_SOURCE_COUNT:
        reasons.append("insufficient_source_coverage")
    if _float(row.get("collision_rate")) > MAX_COLLISION_RATE:
        reasons.append("collision_rate_too_high")
    if _float(row.get("offtrack_outcome_rate")) > MAX_OFFTRACK_RATE:
        reasons.append("offtrack_rate_too_high")
    if not _bool(row.get("all_selected_metrics_finite", True)):
        reasons.append("nonfinite_metric")
    return reasons


def _qualification_row(
    *,
    index: int,
    row: Mapping[str, Any],
    reasons: list[str],
    generated_proxy_boundary_only: bool,
) -> dict[str, Any]:
    profiles = _split_profiles(row.get("profiles_with_success"))
    output: dict[str, Any] = {
        "candidate_key": _candidate_key(index, row),
        "qualification_label": "qualified_candidate" if not reasons else "diagnostic_only_candidate",
        "rejection_reasons": ";".join(reasons),
        "has_l3_success": any(profile in profiles for profile in {"L3_online_gru", "L3_reset_control_corrected"}),
        "has_non_l3_success": any(profile in profiles for profile in {"L0_current_masked", "L1_one_step", "L2_window_50"}),
        "source_diverse": _int(row.get("success_source_count")) >= 8,
        "profile_diverse": _int(row.get("success_profile_count")) >= 4,
        "low_collision_ready": _float(row.get("collision_rate")) <= 0.20,
        "offtrack_bounded": _float(row.get("offtrack_outcome_rate")) <= 0.65,
        "generated_proxy_boundary_only": generated_proxy_boundary_only,
    }
    for field in SOURCE_FIELDS:
        output[field] = row.get(field, "")
    return output


def _claim_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = list(source_rows)
    rows.append(
        {
            "claim": "candidate_qualification_completed",
            "admissible": True,
            "reason": "M2131 classifies localized support slices without rerun or ranking",
        }
    )
    rows.append(
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "qualification produces candidate slices only and does not compare profiles",
        }
    )
    return rows


def qualify_comparison_support_candidates(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    comparison_ready_candidates_path: Path | str = DEFAULT_COMPARISON_READY,
    comparison_support_candidates_path: Path | str = DEFAULT_COMPARISON_SUPPORT,
    claim_boundary_path: Path | str = DEFAULT_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    min_qualified_candidates: int = 6,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    summary = read_json(summary_path)
    ready_rows = read_csv_rows(comparison_ready_candidates_path)
    support_file_rows = read_csv_rows(comparison_support_candidates_path)
    support_rows = [
        row for row in support_file_rows if str(row.get("support_label", "")) == "candidate_support"
    ]
    source_claim_rows = read_csv_rows(claim_boundary_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source_ready_count = int(summary.get("comparison_ready_candidate_count", -1))
    source_support_count = int(summary.get("comparison_support_candidate_count", -1))
    ready_counts_match = len(ready_rows) == source_ready_count
    support_counts_match = len(support_rows) == source_support_count
    generated_proxy_boundary_only = claim_boundary_blocks_paper_result(source_claim_rows)

    all_rows: list[dict[str, str]] = [*ready_rows, *support_rows]
    qualified_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, Any]] = []

    for index, row in enumerate(all_rows):
        reasons = _rejection_reasons(row)
        qualified = _qualification_row(
            index=index,
            row=row,
            reasons=reasons,
            generated_proxy_boundary_only=generated_proxy_boundary_only,
        )
        if reasons:
            diagnostic_rows.append(qualified)
            for reason in reasons:
                rejection_rows.append(
                    {
                        "candidate_key": qualified["candidate_key"],
                        "reason": reason,
                        "support_label": row.get("support_label", ""),
                        "slice_kind": row.get("slice_kind", ""),
                        "comparison_support_intent": row.get("comparison_support_intent", ""),
                        "target_support_tier": row.get("target_support_tier", ""),
                        "source_kind": row.get("source_kind", ""),
                        "proxy_template_family": row.get("proxy_template_family", ""),
                    }
                )
        else:
            qualified_rows.append(qualified)

    qualified_source_kinds = _nonempty_unique(qualified_rows, "source_kind")
    qualified_intents = _nonempty_unique(qualified_rows, "comparison_support_intent")
    qualified_tiers = _nonempty_unique(qualified_rows, "target_support_tier")
    axis_coverage_pass = (
        len(qualified_source_kinds) >= 3
        or len(qualified_intents) >= 3
        or len(qualified_tiers) >= 3
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
        summary.get("result_class") == "comparison_support_outcome_localization_pass"
        and source_ready_count == TARGET_READY_COUNT
        and source_support_count == TARGET_SUPPORT_COUNT
        and ready_counts_match
        and support_counts_match
        and len(qualified_rows) >= min_qualified_candidates
        and axis_coverage_pass
        and guardrail_violation_count == 0
    )

    claim_rows = _claim_boundary_rows(source_claim_rows)
    artifacts = {
        "summary": str(output_path / "summary.json"),
        "qualified_candidates": str(output_path / "qualified_candidates.csv"),
        "diagnostic_only_candidates": str(output_path / "diagnostic_only_candidates.csv"),
        "rejection_reasons": str(output_path / "rejection_reasons.csv"),
        "claim_boundary": str(output_path / "claim_boundary.csv"),
        "run_state": str(output_path / "run_state.json"),
    }
    write_csv_rows(artifacts["qualified_candidates"], qualified_rows, QUALIFIED_FIELDNAMES)
    write_csv_rows(artifacts["diagnostic_only_candidates"], diagnostic_rows, QUALIFIED_FIELDNAMES)
    write_csv_rows(artifacts["rejection_reasons"], rejection_rows, REJECTION_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_rows, CLAIM_BOUNDARY_FIELDNAMES)
    write_run_state(
        output_path / "run_state.json",
        {
            "result_class": "comparison_support_candidate_qualification_pass"
            if result_pass
            else "comparison_support_candidate_qualification_incomplete_or_fail",
            "environment_reset_started": False,
            "environment_rollout_started": False,
            "policy_action_executed": False,
            "measured_rollout_started": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
        },
    )

    rejection_reason_counts = dict(sorted(Counter(row["reason"] for row in rejection_rows).items()))
    summary_out: dict[str, Any] = {
        "result_class": "comparison_support_candidate_qualification_pass"
        if result_pass
        else "comparison_support_candidate_qualification_incomplete_or_fail",
        "generated_at_utc": utc_timestamp(),
        "source_summary_path": str(summary_path),
        "source_result_class": summary.get("result_class"),
        "source_comparison_ready_candidate_count": source_ready_count,
        "source_comparison_support_candidate_count": source_support_count,
        "actual_comparison_ready_candidate_count": len(ready_rows),
        "actual_comparison_support_candidate_count": len(support_rows),
        "support_candidate_file_row_count": len(support_file_rows),
        "ready_counts_match_source_summary": ready_counts_match,
        "support_counts_match_source_summary": support_counts_match,
        "target_ready_count": TARGET_READY_COUNT,
        "target_support_count": TARGET_SUPPORT_COUNT,
        "qualified_candidate_count": len(qualified_rows),
        "diagnostic_only_candidate_count": len(diagnostic_rows),
        "min_qualified_candidates": min_qualified_candidates,
        "qualified_candidate_threshold_pass": len(qualified_rows) >= min_qualified_candidates,
        "qualified_axis_coverage_pass": axis_coverage_pass,
        "qualified_source_kind_count": len(qualified_source_kinds),
        "qualified_intent_count": len(qualified_intents),
        "qualified_target_support_tier_count": len(qualified_tiers),
        "qualified_slice_kind_counts": dict(sorted(Counter(row.get("slice_kind", "") for row in qualified_rows).items())),
        "qualified_intent_counts": dict(
            sorted(Counter(row.get("comparison_support_intent", "") for row in qualified_rows).items())
        ),
        "qualified_target_support_tier_counts": dict(
            sorted(Counter(row.get("target_support_tier", "") for row in qualified_rows).items())
        ),
        "qualified_source_kind_counts": dict(
            sorted(Counter(row.get("source_kind", "") for row in qualified_rows).items())
        ),
        "qualified_proxy_template_counts": dict(
            sorted(Counter(row.get("proxy_template_family", "") for row in qualified_rows).items())
        ),
        "rejection_reason_counts": rejection_reason_counts,
        "generated_proxy_boundary_only": generated_proxy_boundary_only,
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
    write_json(output_path / "summary.json", summary_out)
    return summary_out


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--comparison-ready-candidates", type=Path, default=DEFAULT_COMPARISON_READY)
    parser.add_argument("--comparison-support-candidates", type=Path, default=DEFAULT_COMPARISON_SUPPORT)
    parser.add_argument("--claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-qualified-candidates", type=int, default=6)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = qualify_comparison_support_candidates(
        summary_path=args.summary,
        comparison_ready_candidates_path=args.comparison_ready_candidates,
        comparison_support_candidates_path=args.comparison_support_candidates,
        claim_boundary_path=args.claim_boundary,
        output_dir=args.output_dir,
        min_qualified_candidates=args.min_qualified_candidates,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"qualified_candidate_count={summary['qualified_candidate_count']}")
    print(f"diagnostic_only_candidate_count={summary['diagnostic_only_candidate_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
