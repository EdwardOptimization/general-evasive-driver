"""Candidate-level replay adapter for old-key neighborhood guard results."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.old_key_neighborhood_gate import (
    DEFAULT_THRESHOLDS,
    CandidateThresholds,
    OldKeyNeighborhoodThresholds,
    summarize_diagnostics,
    summarize_old_key_surface,
)


KEY_COLUMNS = [
    "key",
    "target_obstacle_distance",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
]

GUARD_RESULT_COLUMNS = [
    "policy",
    "key",
    "seed",
    "source_condition",
    "source_step",
    "paired_step",
    "target_obstacle_distance",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
    "accepted",
    "normal_success",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
]


def _case_uid(row: pd.Series) -> str:
    return "|".join(
        [
            str(row["key"]),
            f"{float(row['target_obstacle_distance']):.9f}",
            f"{float(row['relocated_obstacle_body_y']):.9f}",
            f"{float(row['relocated_obstacle_half_width']):.9f}",
        ]
    )


def _require_columns(frame: pd.DataFrame, columns: list[str], *, label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _load_guard_results(paths: tuple[Path, ...]) -> pd.DataFrame:
    if not paths:
        raise ValueError("at least one guard results CSV is required")
    frames = [pd.read_csv(path) for path in paths]
    guard = pd.concat(frames, ignore_index=True)
    _require_columns(guard, GUARD_RESULT_COLUMNS, label="guard results")
    return guard


def infer_guard_results_from_compact(compact_frame: pd.DataFrame) -> tuple[Path, ...]:
    if "source_csv" not in compact_frame.columns:
        raise ValueError("compact corpus cannot infer guard results without source_csv column")
    paths = sorted({Path(str(path)) for path in compact_frame["source_csv"].dropna().tolist()})
    if not paths:
        raise ValueError("compact corpus did not contain any source_csv paths")
    return tuple(paths)


def _compact_cases(compact_frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(compact_frame, KEY_COLUMNS, label="compact corpus")
    compact = compact_frame.copy()
    if "record_type" in compact:
        compact = compact[compact["record_type"].astype(str).eq("m341_mined_case")].copy()
    compact["_case_uid"] = compact.apply(_case_uid, axis=1)
    return compact.drop_duplicates("_case_uid").reset_index(drop=True)


def filter_guard_results_to_compact(
    guard_results: pd.DataFrame,
    compact_frame: pd.DataFrame,
) -> pd.DataFrame:
    compact = _compact_cases(compact_frame)
    guard = guard_results.copy()
    guard["_case_uid"] = guard.apply(_case_uid, axis=1)
    return guard[guard["_case_uid"].isin(set(compact["_case_uid"]))].copy()


def compare_candidate_guard_results(
    *,
    compact_frame: pd.DataFrame,
    guard_results: pd.DataFrame,
    baseline_policy: str,
    candidate_policy: str,
) -> pd.DataFrame:
    """Compare old-key compact cases for one baseline/candidate policy pair."""

    compact = _compact_cases(compact_frame)
    filtered = filter_guard_results_to_compact(guard_results, compact)
    baseline = filtered[filtered["policy"].astype(str).eq(str(baseline_policy))].copy()
    candidate = filtered[filtered["policy"].astype(str).eq(str(candidate_policy))].copy()
    if baseline.empty:
        raise ValueError(f"baseline policy {baseline_policy!r} has no compact guard rows")
    if candidate.empty:
        raise ValueError(f"candidate policy {candidate_policy!r} has no compact guard rows")

    merged = compact.merge(
        baseline,
        on="_case_uid",
        suffixes=("", "_baseline"),
        validate="one_to_one",
    ).merge(
        candidate,
        on="_case_uid",
        suffixes=("", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(compact):
        raise ValueError(
            f"guard results cover {len(merged)} compact rows but corpus has {len(compact)} rows"
        )

    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        baseline_accepted = _bool_value(row["accepted"])
        candidate_accepted = _bool_value(row["accepted_candidate"])
        baseline_normal_success = _bool_value(row["normal_success"])
        candidate_normal_success = _bool_value(row["normal_success_candidate"])
        baseline_normal_margin = float(row["normal_margin"])
        candidate_normal_margin = float(row["normal_margin_candidate"])
        baseline_wrong_margin = float(row["wrong_history_margin"])
        candidate_wrong_margin = float(row["wrong_history_margin_candidate"])
        baseline_gap = float(row["margin_gap"])
        candidate_gap = float(row["margin_gap_candidate"])
        rows.append(
            {
                "record_type": "m341_mined_case",
                "case_id": row.get("case_id", row["_case_uid"]),
                "key": str(row["key"]),
                "seed_block": row.get("seed_block", ""),
                "seed": int(row["seed"]),
                "source_condition": str(row["source_condition"]),
                "source_step": int(row["source_step"]),
                "paired_step": int(row["paired_step"]),
                "target_obstacle_distance": float(row["target_obstacle_distance"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "baseline_policy": str(baseline_policy),
                "candidate_policy": str(candidate_policy),
                "baseline_accepted": baseline_accepted,
                "candidate_accepted": candidate_accepted,
                "candidate_accepted_regression": bool(baseline_accepted and not candidate_accepted),
                "baseline_normal_success": baseline_normal_success,
                "candidate_normal_success": candidate_normal_success,
                "candidate_normal_success_regression": bool(
                    baseline_normal_success and not candidate_normal_success
                ),
                "baseline_normal_margin": baseline_normal_margin,
                "candidate_normal_margin": candidate_normal_margin,
                "baseline_wrong_history_margin": baseline_wrong_margin,
                "candidate_wrong_history_margin": candidate_wrong_margin,
                "baseline_margin_gap": baseline_gap,
                "candidate_margin_gap": candidate_gap,
                "candidate_normal_delta": candidate_normal_margin - baseline_normal_margin,
                "candidate_wrong_delta": candidate_wrong_margin - baseline_wrong_margin,
                "candidate_gap_delta": candidate_gap - baseline_gap,
            }
        )
    return pd.DataFrame(rows)


def summarize_candidate_comparison(
    comparison_frame: pd.DataFrame,
    *,
    thresholds: OldKeyNeighborhoodThresholds = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    diversity = summarize_old_key_surface(comparison_frame, thresholds=thresholds.compact)
    candidate_metrics = _candidate_metrics(comparison_frame, thresholds.candidate)
    return {**diversity, **candidate_metrics}


def _candidate_metrics(frame: pd.DataFrame, thresholds: CandidateThresholds) -> dict[str, Any]:
    gaps = pd.to_numeric(frame["candidate_gap_delta"], errors="coerce").dropna()
    if gaps.empty:
        gap_mean = 0.0
        gap_p10 = 0.0
        gap_min = 0.0
    else:
        gap_mean = float(gaps.mean())
        gap_p10 = float(gaps.quantile(0.10))
        gap_min = float(gaps.min())
    accepted_regressions = int(frame["candidate_accepted_regression"].map(_bool_value).sum())
    normal_success_regressions = int(frame["candidate_normal_success_regression"].map(_bool_value).sum())

    failures: list[str] = []
    if accepted_regressions > thresholds.max_selected_accepted_regressions:
        failures.append(f"candidate_accepted_regressions>{thresholds.max_selected_accepted_regressions}")
    if gap_p10 < thresholds.min_selected_gap_p10:
        failures.append(f"candidate_gap_p10<{thresholds.min_selected_gap_p10}")
    if gap_min < thresholds.min_selected_gap_min:
        failures.append(f"candidate_gap_min<{thresholds.min_selected_gap_min}")

    repair_reasons: list[str] = []
    if accepted_regressions >= thresholds.endpoint_repair_accepted_regressions:
        repair_reasons.append(
            f"candidate_accepted_regressions>={thresholds.endpoint_repair_accepted_regressions}"
        )
    if gap_p10 <= thresholds.endpoint_repair_gap_p10:
        repair_reasons.append(f"candidate_gap_p10<={thresholds.endpoint_repair_gap_p10}")
    if gap_min <= thresholds.endpoint_repair_gap_min:
        repair_reasons.append(f"candidate_gap_min<={thresholds.endpoint_repair_gap_min}")

    return {
        "candidate_accepted_regressions": accepted_regressions,
        "candidate_normal_success_regressions": normal_success_regressions,
        "candidate_gap_mean": gap_mean,
        "candidate_gap_p10": gap_p10,
        "candidate_gap_min": gap_min,
        "candidate_gate_pass": not failures,
        "candidate_gate_failures": failures,
        "candidate_repair_needed": bool(repair_reasons),
        "candidate_repair_reasons": repair_reasons,
    }


def _failure_types(metrics: dict[str, Any], diagnostics: dict[str, Any]) -> list[str]:
    failures: set[str] = set()
    if not metrics["passes_diversity_targets"] or not diagnostics["visible"]:
        failures.add("lineage_invalid")
    if not metrics["candidate_gate_pass"]:
        failures.add("protected_key_window_failure")
    return ["none"] if not failures else sorted(failures)


def run_old_key_neighborhood_replay_gate(
    *,
    compact_corpus_csv: Path,
    guard_results_csvs: tuple[Path, ...],
    baseline_policy: str,
    candidate_policy: str,
    run_dir: Path,
    candidate_pool_csv: Path | None = None,
    thresholds: OldKeyNeighborhoodThresholds = DEFAULT_THRESHOLDS,
    pass_decision: str = "admit_next_old_key_neighborhood_replay_step",
    fail_decision: str = "reject_old_key_neighborhood_candidate",
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    compact = pd.read_csv(compact_corpus_csv)
    guard_results = _load_guard_results(guard_results_csvs)
    comparison = compare_candidate_guard_results(
        compact_frame=compact,
        guard_results=guard_results,
        baseline_policy=baseline_policy,
        candidate_policy=candidate_policy,
    )
    metrics = summarize_candidate_comparison(comparison, thresholds=thresholds)
    diagnostics = (
        summarize_diagnostics(pd.read_csv(candidate_pool_csv), require_old_key_9944=True)
        if candidate_pool_csv is not None
        else {"rows": 0, "old_key_9944_included": False, "visible": False, "required_old_key_9944": True}
    )
    failure_types = _failure_types(metrics, diagnostics)
    overall_pass = failure_types == ["none"]
    result = {
        "run_type": "old_key_neighborhood_replay_gate",
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "compact_corpus_csv": compact_corpus_csv,
        "guard_results_csvs": list(guard_results_csvs),
        "candidate_pool_csv": candidate_pool_csv,
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "compact_metrics": metrics,
        "m133_diagnostics": diagnostics,
        "overall_pass": bool(overall_pass),
        "failure_types": failure_types,
        "decision": pass_decision if overall_pass else fail_decision,
        "comparison_rows_csv": run_dir / "old_key_replay_comparison_rows.csv",
        "compact_metrics_csv": run_dir / "compact_metrics.csv",
        "diagnostic_summary_csv": run_dir / "diagnostic_summary.csv",
    }
    write_csv_rows(run_dir / "old_key_replay_comparison_rows.csv", comparison.to_dict("records"))
    write_csv_rows(run_dir / "compact_metrics.csv", [_flat_metrics_row(metrics)])
    write_csv_rows(run_dir / "diagnostic_summary.csv", [diagnostics])
    write_json(run_dir / "summary.json", result)
    return result


def _flat_metrics_row(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "rows": metrics["rows"],
        "seed_blocks": metrics["seed_blocks"],
        "physical_pairs_or_keys": metrics["physical_pairs_or_keys"],
        "source_steps": metrics["source_steps"],
        "target_buckets": metrics["target_buckets"],
        "max_seed_block_dominance": metrics["max_seed_block_dominance"],
        "max_physical_pair_dominance": metrics["max_physical_pair_dominance"],
        "passes_diversity_targets": metrics["passes_diversity_targets"],
        "candidate_accepted_regressions": metrics["candidate_accepted_regressions"],
        "candidate_normal_success_regressions": metrics["candidate_normal_success_regressions"],
        "candidate_gap_mean": metrics["candidate_gap_mean"],
        "candidate_gap_p10": metrics["candidate_gap_p10"],
        "candidate_gap_min": metrics["candidate_gap_min"],
        "candidate_gate_pass": metrics["candidate_gate_pass"],
        "candidate_repair_needed": metrics["candidate_repair_needed"],
        "diversity_failures": ";".join(metrics.get("diversity_failures", [])),
        "candidate_gate_failures": ";".join(metrics.get("candidate_gate_failures", [])),
        "candidate_repair_reasons": ";".join(metrics.get("candidate_repair_reasons", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate replayed old-key neighborhood candidate results.")
    parser.add_argument("--compact-corpus-csv", type=Path, required=True)
    parser.add_argument("--guard-results-csv", action="append", type=Path, default=[])
    parser.add_argument("--infer-guard-results-from-compact", action="store_true")
    parser.add_argument("--candidate-pool-csv", type=Path, default=None)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--pass-decision", default="admit_next_old_key_neighborhood_replay_step")
    parser.add_argument("--fail-decision", default="reject_old_key_neighborhood_candidate")
    args = parser.parse_args()

    compact = pd.read_csv(args.compact_corpus_csv)
    guard_results_csvs = tuple(args.guard_results_csv)
    if args.infer_guard_results_from_compact:
        guard_results_csvs = tuple(sorted(set(guard_results_csvs + infer_guard_results_from_compact(compact))))
    run_dir = args.run_dir or make_run_dir(prefix="old_key_neighborhood_replay_gate")
    result = run_old_key_neighborhood_replay_gate(
        compact_corpus_csv=args.compact_corpus_csv,
        guard_results_csvs=guard_results_csvs,
        baseline_policy=args.baseline_policy,
        candidate_policy=args.candidate_policy,
        candidate_pool_csv=args.candidate_pool_csv,
        run_dir=run_dir,
        pass_decision=args.pass_decision,
        fail_decision=args.fail_decision,
    )
    print(pd.Series({
        "overall_pass": result["overall_pass"],
        "candidate_gate_pass": result["compact_metrics"]["candidate_gate_pass"],
        "candidate_repair_needed": result["compact_metrics"]["candidate_repair_needed"],
        "failure_types": ",".join(result["failure_types"]),
        "decision": result["decision"],
        "run_dir": str(run_dir),
    }).to_string())


if __name__ == "__main__":
    main()
