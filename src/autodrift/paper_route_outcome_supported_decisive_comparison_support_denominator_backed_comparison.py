"""No-rerun denominator-backed diagnostic comparison materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_INVENTORY_SUMMARY = Path(
    "runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/summary.json"
)
DEFAULT_DENOMINATOR_ROWS = Path(
    "runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/"
    "denominator_inventory_rows.csv"
)
DEFAULT_INVENTORY_CLAIM_BOUNDARY = Path(
    "runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/"
    "claim_boundary.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison"
)
DEFAULT_NEXT_BLOCKER = (
    "m2145-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-result-audit"
)

PROFILE_ORDER = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_50",
    "L3_online_gru",
    "L3_reset_control_corrected",
)
DIAGNOSTIC_CONTRASTS = (
    ("L1_one_step", "L0_current_masked", "L1_minus_L0_current_response_increment"),
    ("L2_window_50", "L1_one_step", "L2_minus_L1_finite_window_increment"),
    ("L3_online_gru", "L1_one_step", "L3_online_minus_L1_recurrent_vs_one_step"),
    ("L3_online_gru", "L2_window_50", "L3_online_minus_L2_recurrent_vs_window"),
    ("L3_reset_control_corrected", "L3_online_gru", "L3_reset_minus_L3_online_reset_control_gap"),
    ("L3_reset_control_corrected", "L2_window_50", "L3_reset_minus_L2_reset_vs_window"),
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

PROFILE_SUMMARY_FIELDNAMES = [
    "profile_label",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "clearance_margin_mean_unweighted",
    "return_mean_unweighted",
    "steps_mean_unweighted",
    "observed_success_support_count",
    "diagnostic_generated_proxy_only",
]
MATRIX_FIELDNAMES = [
    "source_kind",
    "comparison_support_intent",
    "profile_label",
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
    "observed_success_support",
    "support_absence_semantics",
    "diagnostic_generated_proxy_only",
]
CONTRAST_FIELDNAMES = [
    "contrast_name",
    "left_profile",
    "right_profile",
    "success_rate_delta",
    "collision_rate_delta",
    "offtrack_outcome_rate_delta",
    "clearance_margin_mean_delta",
    "return_mean_delta",
    "contrast_scope",
    "verdict_allowed",
    "ranking_allowed",
    "paper_claim_allowed",
    "self_id_claim_allowed",
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
    try:
        return (PROFILE_ORDER.index(label), label)
    except ValueError:
        return (len(PROFILE_ORDER), label)


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _claim_boundary_violation_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("claim") in DISALLOWED_CLAIMS and _bool(row.get("admissible")))


def _claim_boundary_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = list(source_rows)
    rows.append(
        {
            "claim": "denominator_backed_diagnostic_comparison_materialized",
            "admissible": True,
            "reason": "M2144 materializes descriptive diagnostic rates and deltas without rerun or ranking",
        }
    )
    rows.extend(
        [
            {
                "claim": "controller_family_ranking",
                "admissible": False,
                "reason": "diagnostic comparison artifact blocks rank and winner fields",
            },
            {
                "claim": "finite_window_vs_gru_conclusion",
                "admissible": False,
                "reason": "diagnostic deltas require audit and do not issue a family verdict",
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
            "metric": "profile_success_rate",
            "admissible": True,
            "reason": "descriptive rate over complete denominator inventory, not a ranking",
        },
        {
            "metric": "source_kind_profile_success_rate",
            "admissible": True,
            "reason": "descriptive per-source-kind profile rate, not a ranking",
        },
        {
            "metric": "diagnostic_pairwise_delta",
            "admissible": True,
            "reason": "pre-registered diagnostic delta for audit routing only",
        },
        {
            "metric": "winner_or_rank",
            "admissible": False,
            "reason": "materialization does not choose winners or sort rankings",
        },
        {
            "metric": "finite_window_vs_gru_verdict",
            "admissible": False,
            "reason": "generated-proxy diagnostic deltas are not a verdict",
        },
        {
            "metric": "paper_level_benchmark_verdict",
            "admissible": False,
            "reason": "generated proxy rows remain paper_validity_claim false",
        },
        {
            "metric": "level3_self_id_verdict",
            "admissible": False,
            "reason": "materialization does not test wrong, delayed, or reset history outcome interventions",
        },
    ]


def _profile_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("profile_label", ""))].append(row)
    output: list[dict[str, Any]] = []
    for profile in sorted(groups, key=_profile_sort_key):
        group = groups[profile]
        episode_count = sum(_int(row.get("episode_count")) for row in group)
        success_count = sum(_int(row.get("success_count")) for row in group)
        collision_count = sum(_int(row.get("collision_count")) for row in group)
        offtrack_count = sum(_int(row.get("offtrack_outcome_count")) for row in group)
        output.append(
            {
                "profile_label": profile,
                "episode_count": episode_count,
                "success_count": success_count,
                "collision_count": collision_count,
                "offtrack_outcome_count": offtrack_count,
                "success_rate": _safe_rate(success_count, episode_count),
                "collision_rate": _safe_rate(collision_count, episode_count),
                "offtrack_outcome_rate": _safe_rate(offtrack_count, episode_count),
                "clearance_margin_mean_unweighted": _mean([_float(row.get("clearance_margin_mean")) for row in group]),
                "return_mean_unweighted": _mean([_float(row.get("return_mean")) for row in group]),
                "steps_mean_unweighted": _mean([_float(row.get("steps_mean")) for row in group]),
                "observed_success_support_count": sum(1 for row in group if _bool(row.get("observed_success_support"))),
                "diagnostic_generated_proxy_only": True,
            }
        )
    return output


def _source_kind_profile_matrix(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (str(item.get("source_kind", "")), _profile_sort_key(str(item.get("profile_label", ""))))):
        output.append(
            {
                "source_kind": row.get("source_kind", ""),
                "comparison_support_intent": row.get("comparison_support_intent", ""),
                "profile_label": row.get("profile_label", ""),
                "episode_count": _int(row.get("episode_count")),
                "success_count": _int(row.get("success_count")),
                "collision_count": _int(row.get("collision_count")),
                "offtrack_outcome_count": _int(row.get("offtrack_outcome_count")),
                "success_rate": _float(row.get("success_rate")),
                "collision_rate": _float(row.get("collision_rate")),
                "offtrack_outcome_rate": _float(row.get("offtrack_outcome_rate")),
                "clearance_margin_mean": _float(row.get("clearance_margin_mean")),
                "return_mean": _float(row.get("return_mean")),
                "steps_mean": _float(row.get("steps_mean")),
                "observed_success_support": _bool(row.get("observed_success_support")),
                "support_absence_semantics": row.get("support_absence_semantics", ""),
                "diagnostic_generated_proxy_only": True,
            }
        )
    return output


def _diagnostic_contrasts(profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_profile = {str(row["profile_label"]): row for row in profile_rows}
    output: list[dict[str, Any]] = []
    for left, right, name in DIAGNOSTIC_CONTRASTS:
        left_row = by_profile.get(left, {})
        right_row = by_profile.get(right, {})
        output.append(
            {
                "contrast_name": name,
                "left_profile": left,
                "right_profile": right,
                "success_rate_delta": _float(left_row.get("success_rate")) - _float(right_row.get("success_rate")),
                "collision_rate_delta": _float(left_row.get("collision_rate")) - _float(right_row.get("collision_rate")),
                "offtrack_outcome_rate_delta": _float(left_row.get("offtrack_outcome_rate"))
                - _float(right_row.get("offtrack_outcome_rate")),
                "clearance_margin_mean_delta": _float(left_row.get("clearance_margin_mean_unweighted"))
                - _float(right_row.get("clearance_margin_mean_unweighted")),
                "return_mean_delta": _float(left_row.get("return_mean_unweighted"))
                - _float(right_row.get("return_mean_unweighted")),
                "contrast_scope": "diagnostic_generated_proxy_only",
                "verdict_allowed": False,
                "ranking_allowed": False,
                "paper_claim_allowed": False,
                "self_id_claim_allowed": False,
            }
        )
    return output


def materialize_diagnostic_comparison(
    *,
    inventory_summary_path: Path | str = DEFAULT_INVENTORY_SUMMARY,
    denominator_rows_path: Path | str = DEFAULT_DENOMINATOR_ROWS,
    inventory_claim_boundary_path: Path | str = DEFAULT_INVENTORY_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    inventory_summary = read_json(inventory_summary_path)
    denominator_rows = read_csv_rows(denominator_rows_path)
    claim_rows = read_csv_rows(inventory_claim_boundary_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    profile_rows = _profile_summary(denominator_rows)
    matrix_rows = _source_kind_profile_matrix(denominator_rows)
    contrast_rows = _diagnostic_contrasts(profile_rows)
    metric_contract_rows = _metric_contract_rows()
    output_claim_rows = _claim_boundary_rows(claim_rows)

    profile_count = len({row["profile_label"] for row in profile_rows})
    source_kind_count = len({row["source_kind"] for row in matrix_rows})
    denominator_row_count = len(denominator_rows)
    claim_boundary_violation_count = _claim_boundary_violation_count(output_claim_rows)
    blocked_verdict_field_count = 0
    if any(_bool(row.get("verdict_allowed")) or _bool(row.get("ranking_allowed")) for row in contrast_rows):
        blocked_verdict_field_count += 1
    if any(_bool(row.get("paper_claim_allowed")) or _bool(row.get("self_id_claim_allowed")) for row in contrast_rows):
        blocked_verdict_field_count += 1

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
        inventory_summary.get("result_class") == "comparison_support_denominator_source_inventory_pass"
        and profile_count == 5
        and source_kind_count == 6
        and denominator_row_count == 30
        and len(profile_rows) == 5
        and len(matrix_rows) == 30
        and len(contrast_rows) == 6
        and blocked_verdict_field_count == 0
        and claim_boundary_violation_count == 0
        and guardrail_violation_count == 0
    )

    artifacts = {
        "summary": str(output_path / "summary.json"),
        "comparison_protocol": str(output_path / "comparison_protocol.json"),
        "profile_outcome_summary": str(output_path / "profile_outcome_summary.csv"),
        "source_kind_profile_matrix": str(output_path / "source_kind_profile_matrix.csv"),
        "diagnostic_contrast_rows": str(output_path / "diagnostic_contrast_rows.csv"),
        "metric_contract": str(output_path / "metric_contract.csv"),
        "claim_boundary": str(output_path / "claim_boundary.csv"),
        "run_state": str(output_path / "run_state.json"),
    }
    protocol = {
        "protocol_name": "m2144_denominator_backed_diagnostic_comparison",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "descriptive diagnostics only; no ranking, winner, paper, finite-window-vs-GRU, or self-ID claim",
        "inventory_summary_path": str(inventory_summary_path),
        "denominator_rows_path": str(denominator_rows_path),
        "profiles": [row["profile_label"] for row in profile_rows],
        "diagnostic_contrasts": [row["contrast_name"] for row in contrast_rows],
        "blocked_verdicts": [
            "winner",
            "rank",
            "finite_window_vs_gru_verdict",
            "paper_level_benchmark_result",
            "level3_self_identification",
        ],
    }
    write_json(artifacts["comparison_protocol"], protocol)
    write_csv_rows(artifacts["profile_outcome_summary"], profile_rows, PROFILE_SUMMARY_FIELDNAMES)
    write_csv_rows(artifacts["source_kind_profile_matrix"], matrix_rows, MATRIX_FIELDNAMES)
    write_csv_rows(artifacts["diagnostic_contrast_rows"], contrast_rows, CONTRAST_FIELDNAMES)
    write_csv_rows(artifacts["metric_contract"], metric_contract_rows, METRIC_CONTRACT_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], output_claim_rows, CLAIM_BOUNDARY_FIELDNAMES)
    write_run_state(
        output_path / "run_state.json",
        {
            "result_class": "comparison_support_denominator_backed_diagnostic_comparison_pass"
            if result_pass
            else "comparison_support_denominator_backed_diagnostic_comparison_fail",
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
        "result_class": "comparison_support_denominator_backed_diagnostic_comparison_pass"
        if result_pass
        else "comparison_support_denominator_backed_diagnostic_comparison_fail",
        "generated_at_utc": utc_timestamp(),
        "inventory_summary_path": str(inventory_summary_path),
        "source_result_class": inventory_summary.get("result_class"),
        "denominator_rows_path": str(denominator_rows_path),
        "profile_count": profile_count,
        "source_kind_count": source_kind_count,
        "denominator_row_count": denominator_row_count,
        "profile_summary_row_count": len(profile_rows),
        "source_kind_profile_matrix_row_count": len(matrix_rows),
        "diagnostic_contrast_row_count": len(contrast_rows),
        "blocked_verdict_field_count": blocked_verdict_field_count,
        "claim_boundary_violation_count": claim_boundary_violation_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "ranking_claim_made": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "required_files_written": True,
        "next_blocker": next_blocker,
        "artifacts": artifacts,
    }
    write_json(artifacts["summary"], summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-summary", type=Path, default=DEFAULT_INVENTORY_SUMMARY)
    parser.add_argument("--denominator-rows", type=Path, default=DEFAULT_DENOMINATOR_ROWS)
    parser.add_argument("--inventory-claim-boundary", type=Path, default=DEFAULT_INVENTORY_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_diagnostic_comparison(
        inventory_summary_path=args.inventory_summary,
        denominator_rows_path=args.denominator_rows,
        inventory_claim_boundary_path=args.inventory_claim_boundary,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"source_kind_count={summary['source_kind_count']}")
    print(f"diagnostic_contrast_row_count={summary['diagnostic_contrast_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == "comparison_support_denominator_backed_diagnostic_comparison_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
