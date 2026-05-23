"""Evaluate the source-diverse old-key neighborhood replacement gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


MINED_RECORD_TYPE = "m341_mined_case"
DIAGNOSTIC_RECORD_TYPE = "m133_diagnostic"


@dataclass(frozen=True)
class DiversityThresholds:
    min_rows: int
    min_seed_blocks: int
    min_physical_pairs_or_keys: int
    min_source_steps: int
    min_target_buckets: int
    max_seed_block_dominance: float
    max_physical_pair_dominance: float
    max_rows: int | None = None


@dataclass(frozen=True)
class CandidateThresholds:
    max_selected_accepted_regressions: int
    min_selected_gap_p10: float
    min_selected_gap_min: float
    endpoint_repair_accepted_regressions: int
    endpoint_repair_gap_p10: float
    endpoint_repair_gap_min: float


@dataclass(frozen=True)
class OldKeyNeighborhoodThresholds:
    broad: DiversityThresholds
    compact: DiversityThresholds
    candidate: CandidateThresholds
    require_old_key_9944: bool = True


DEFAULT_THRESHOLDS = OldKeyNeighborhoodThresholds(
    broad=DiversityThresholds(
        min_rows=80,
        min_seed_blocks=4,
        min_physical_pairs_or_keys=20,
        min_source_steps=8,
        min_target_buckets=4,
        max_seed_block_dominance=0.25,
        max_physical_pair_dominance=1.0,
    ),
    compact=DiversityThresholds(
        min_rows=20,
        max_rows=40,
        min_seed_blocks=4,
        min_physical_pairs_or_keys=15,
        min_source_steps=6,
        min_target_buckets=4,
        max_seed_block_dominance=0.25,
        max_physical_pair_dominance=0.15,
    ),
    candidate=CandidateThresholds(
        max_selected_accepted_regressions=0,
        min_selected_gap_p10=-0.0005,
        min_selected_gap_min=-0.002,
        endpoint_repair_accepted_regressions=2,
        endpoint_repair_gap_p10=-0.001,
        endpoint_repair_gap_min=-0.01,
    ),
)


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series([False] * len(frame), index=frame.index)
    series = frame[column]
    if series.dtype == bool:
        return series.fillna(False).astype(bool)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").dropna()


def _mined_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if "record_type" not in frame:
        return frame.copy()
    return frame[frame["record_type"].fillna(MINED_RECORD_TYPE).astype(str) == MINED_RECORD_TYPE].copy()


def _value_counts_dict(series: pd.Series, limit: int = 10) -> dict[str, int]:
    counts = series.astype(str).value_counts().head(limit)
    return {str(key): int(value) for key, value in counts.items()}


def _max_dominance(series: pd.Series, row_count: int) -> float:
    if row_count <= 0 or series.empty:
        return 0.0
    return float(series.astype(str).value_counts().max() / row_count)


def _physical_pair_values(frame: pd.DataFrame) -> pd.Series:
    if "case_id" in frame:
        return frame["case_id"].astype(str)
    if "key" in frame:
        target_columns = [
            "target_obstacle_distance",
            "relocated_obstacle_body_y",
            "relocated_obstacle_half_width",
        ]
        if all(column in frame for column in target_columns):
            return frame.apply(
                lambda row: (
                    f"{row['key']}|{row['target_obstacle_distance']}|"
                    f"{row['relocated_obstacle_body_y']}|{row['relocated_obstacle_half_width']}"
                ),
                axis=1,
            )
        return frame["key"].astype(str)
    return pd.Series([str(index) for index in frame.index], index=frame.index)


def _target_bucket_count(frame: pd.DataFrame) -> int:
    target_columns = [
        "target_obstacle_distance",
        "relocated_obstacle_body_y",
        "relocated_obstacle_half_width",
    ]
    if not all(column in frame for column in target_columns):
        return 0
    return int(frame[target_columns].drop_duplicates().shape[0])


def _gap_metrics(frame: pd.DataFrame, prefix: str) -> dict[str, Any]:
    regression_column = f"{prefix}_accepted_regression"
    gap_column = f"{prefix}_gap_delta"
    gaps = _numeric_series(frame, gap_column)
    if gaps.empty:
        gap_mean = 0.0
        gap_p10 = 0.0
        gap_min = 0.0
        gap_regressions_le_0003 = 0
        gap_regressions_le_001 = 0
    else:
        gap_mean = float(gaps.mean())
        gap_p10 = float(gaps.quantile(0.10))
        gap_min = float(gaps.min())
        gap_regressions_le_0003 = int((gaps <= -0.0003).sum())
        gap_regressions_le_001 = int((gaps <= -0.001).sum())
    return {
        f"{prefix}_accepted_regressions": int(_bool_series(frame, regression_column).sum()),
        f"{prefix}_gap_mean": gap_mean,
        f"{prefix}_gap_p10": gap_p10,
        f"{prefix}_gap_min": gap_min,
        f"{prefix}_gap_regressions_le_-0.0003": gap_regressions_le_0003,
        f"{prefix}_gap_regressions_le_-0.001": gap_regressions_le_001,
    }


def _passes_diversity(metrics: dict[str, Any], thresholds: DiversityThresholds) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if metrics["rows"] < thresholds.min_rows:
        failures.append(f"rows<{thresholds.min_rows}")
    if thresholds.max_rows is not None and metrics["rows"] > thresholds.max_rows:
        failures.append(f"rows>{thresholds.max_rows}")
    if metrics["seed_blocks"] < thresholds.min_seed_blocks:
        failures.append(f"seed_blocks<{thresholds.min_seed_blocks}")
    if metrics["physical_pairs_or_keys"] < thresholds.min_physical_pairs_or_keys:
        failures.append(f"physical_pairs_or_keys<{thresholds.min_physical_pairs_or_keys}")
    if metrics["source_steps"] < thresholds.min_source_steps:
        failures.append(f"source_steps<{thresholds.min_source_steps}")
    if metrics["target_buckets"] < thresholds.min_target_buckets:
        failures.append(f"target_buckets<{thresholds.min_target_buckets}")
    if metrics["max_seed_block_dominance"] > thresholds.max_seed_block_dominance:
        failures.append(f"max_seed_block_dominance>{thresholds.max_seed_block_dominance}")
    if metrics["max_physical_pair_dominance"] > thresholds.max_physical_pair_dominance:
        failures.append(f"max_physical_pair_dominance>{thresholds.max_physical_pair_dominance}")
    return (not failures, failures)


def summarize_old_key_surface(
    frame: pd.DataFrame,
    *,
    thresholds: DiversityThresholds,
) -> dict[str, Any]:
    """Summarize mined old-key rows and check source-diversity thresholds."""

    mined = _mined_rows(frame)
    row_count = int(len(mined))
    seed_blocks = mined["seed_block"].astype(str) if "seed_block" in mined else pd.Series(dtype=str)
    physical_pairs = _physical_pair_values(mined)
    source_steps = mined["source_step"] if "source_step" in mined else pd.Series(dtype=object)
    metrics: dict[str, Any] = {
        "rows": row_count,
        "seed_blocks": int(seed_blocks.nunique()) if not seed_blocks.empty else 0,
        "physical_pairs_or_keys": int(physical_pairs.nunique()) if not physical_pairs.empty else 0,
        "source_steps": int(source_steps.nunique()) if not source_steps.empty else 0,
        "target_buckets": _target_bucket_count(mined),
        "max_seed_block_dominance": _max_dominance(seed_blocks, row_count),
        "max_physical_pair_dominance": _max_dominance(physical_pairs, row_count),
        "seed_block_counts": _value_counts_dict(seed_blocks),
        "top_case_counts": _value_counts_dict(physical_pairs),
    }
    metrics.update(_gap_metrics(mined, "selected"))
    metrics.update(_gap_metrics(mined, "endpoint"))
    passes, failures = _passes_diversity(metrics, thresholds)
    metrics["passes_diversity_targets"] = bool(passes)
    metrics["diversity_failures"] = failures
    return metrics


def summarize_diagnostics(frame: pd.DataFrame, *, require_old_key_9944: bool) -> dict[str, Any]:
    if "record_type" not in frame:
        diagnostics = frame.iloc[0:0].copy()
    else:
        diagnostics = frame[
            frame["record_type"].fillna("").astype(str) == DIAGNOSTIC_RECORD_TYPE
        ].copy()
    if "old_key_9944" in diagnostics:
        old_key_9944_included = bool(_bool_series(diagnostics, "old_key_9944").any())
    elif "key" in diagnostics:
        old_key_9944_included = bool(diagnostics["key"].astype(str).str.startswith("9944|").any())
    else:
        old_key_9944_included = False
    visible = len(diagnostics) > 0 and (old_key_9944_included or not require_old_key_9944)
    return {
        "rows": int(len(diagnostics)),
        "old_key_9944_included": old_key_9944_included,
        "visible": bool(visible),
        "required_old_key_9944": bool(require_old_key_9944),
    }


def evaluate_candidate_metrics(
    metrics: dict[str, Any],
    thresholds: CandidateThresholds,
) -> dict[str, Any]:
    selected_failures: list[str] = []
    if metrics["selected_accepted_regressions"] > thresholds.max_selected_accepted_regressions:
        selected_failures.append(
            f"selected_accepted_regressions>{thresholds.max_selected_accepted_regressions}"
        )
    if metrics["selected_gap_p10"] < thresholds.min_selected_gap_p10:
        selected_failures.append(f"selected_gap_p10<{thresholds.min_selected_gap_p10}")
    if metrics["selected_gap_min"] < thresholds.min_selected_gap_min:
        selected_failures.append(f"selected_gap_min<{thresholds.min_selected_gap_min}")

    repair_reasons: list[str] = []
    if metrics["endpoint_accepted_regressions"] >= thresholds.endpoint_repair_accepted_regressions:
        repair_reasons.append(
            f"endpoint_accepted_regressions>={thresholds.endpoint_repair_accepted_regressions}"
        )
    if metrics["endpoint_gap_p10"] <= thresholds.endpoint_repair_gap_p10:
        repair_reasons.append(f"endpoint_gap_p10<={thresholds.endpoint_repair_gap_p10}")
    if metrics["endpoint_gap_min"] <= thresholds.endpoint_repair_gap_min:
        repair_reasons.append(f"endpoint_gap_min<={thresholds.endpoint_repair_gap_min}")

    return {
        "selected_alpha_passes": not selected_failures,
        "selected_alpha_failures": selected_failures,
        "endpoint_repair_needed": bool(repair_reasons),
        "endpoint_repair_reasons": repair_reasons,
    }


def _flat_metrics_row(label: str, metrics: dict[str, Any]) -> dict[str, Any]:
    scalar_keys = [
        "rows",
        "seed_blocks",
        "physical_pairs_or_keys",
        "source_steps",
        "target_buckets",
        "max_seed_block_dominance",
        "max_physical_pair_dominance",
        "passes_diversity_targets",
        "selected_accepted_regressions",
        "selected_gap_mean",
        "selected_gap_p10",
        "selected_gap_min",
        "selected_gap_regressions_le_-0.0003",
        "selected_gap_regressions_le_-0.001",
        "endpoint_accepted_regressions",
        "endpoint_gap_mean",
        "endpoint_gap_p10",
        "endpoint_gap_min",
        "endpoint_gap_regressions_le_-0.0003",
        "endpoint_gap_regressions_le_-0.001",
        "selected_alpha_passes",
        "endpoint_repair_needed",
    ]
    row = {"surface": label}
    for key in scalar_keys:
        if key in metrics:
            row[key] = metrics[key]
    row["diversity_failures"] = ";".join(metrics.get("diversity_failures", []))
    row["selected_alpha_failures"] = ";".join(metrics.get("selected_alpha_failures", []))
    row["endpoint_repair_reasons"] = ";".join(metrics.get("endpoint_repair_reasons", []))
    return row


def failure_types_for_gate(
    *,
    broad_metrics: dict[str, Any],
    compact_metrics: dict[str, Any],
    diagnostics: dict[str, Any],
) -> list[str]:
    failures: set[str] = set()
    if not broad_metrics["passes_diversity_targets"] or not compact_metrics["passes_diversity_targets"]:
        failures.add("lineage_invalid")
    if not broad_metrics["selected_alpha_passes"] or not compact_metrics["selected_alpha_passes"]:
        failures.add("protected_key_window_failure")
    if not compact_metrics["endpoint_repair_needed"]:
        failures.add("metric_artifact")
    if not diagnostics["visible"]:
        failures.add("lineage_invalid")
    return ["none"] if not failures else sorted(failures)


def run_old_key_neighborhood_gate(
    *,
    candidate_pool_csv: Path,
    compact_corpus_csv: Path,
    run_dir: Path,
    thresholds: OldKeyNeighborhoodThresholds = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    """Run the M341 old-key neighborhood replacement gate from saved CSV artifacts."""

    run_dir.mkdir(parents=True, exist_ok=True)
    candidate_pool = pd.read_csv(candidate_pool_csv)
    compact_corpus = pd.read_csv(compact_corpus_csv)
    broad_metrics = summarize_old_key_surface(candidate_pool, thresholds=thresholds.broad)
    compact_metrics = summarize_old_key_surface(compact_corpus, thresholds=thresholds.compact)
    broad_metrics.update(evaluate_candidate_metrics(broad_metrics, thresholds.candidate))
    compact_metrics.update(evaluate_candidate_metrics(compact_metrics, thresholds.candidate))
    diagnostics = summarize_diagnostics(
        candidate_pool,
        require_old_key_9944=thresholds.require_old_key_9944,
    )
    failure_types = failure_types_for_gate(
        broad_metrics=broad_metrics,
        compact_metrics=compact_metrics,
        diagnostics=diagnostics,
    )
    overall_pass = failure_types == ["none"]
    result = {
        "run_type": "old_key_neighborhood_gate",
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "candidate_pool_csv": candidate_pool_csv,
        "compact_corpus_csv": compact_corpus_csv,
        "broad_pool": broad_metrics,
        "compact_corpus": compact_metrics,
        "m133_diagnostics": diagnostics,
        "replacement_gate_ready": bool(overall_pass),
        "selected_alpha_passes": bool(
            broad_metrics["selected_alpha_passes"] and compact_metrics["selected_alpha_passes"]
        ),
        "endpoint_repair_needed": bool(compact_metrics["endpoint_repair_needed"]),
        "overall_pass": bool(overall_pass),
        "failure_types": failure_types,
        "decision": (
            "admit_m343_old_key_neighborhood_gate_probe"
            if overall_pass
            else "reject_old_key_neighborhood_gate"
        ),
    }
    broad_row = _flat_metrics_row("broad_pool", broad_metrics)
    compact_row = _flat_metrics_row("compact_corpus", compact_metrics)
    write_csv_rows(run_dir / "broad_metrics.csv", [broad_row])
    write_csv_rows(run_dir / "compact_metrics.csv", [compact_row])
    write_csv_rows(run_dir / "diagnostic_summary.csv", [diagnostics])
    write_json(run_dir / "summary.json", result)
    return result


def _thresholds_from_args(args: argparse.Namespace) -> OldKeyNeighborhoodThresholds:
    return OldKeyNeighborhoodThresholds(
        broad=DiversityThresholds(
            min_rows=args.broad_min_rows,
            min_seed_blocks=args.broad_min_seed_blocks,
            min_physical_pairs_or_keys=args.broad_min_physical_pairs,
            min_source_steps=args.broad_min_source_steps,
            min_target_buckets=args.broad_min_target_buckets,
            max_seed_block_dominance=args.broad_max_seed_block_dominance,
            max_physical_pair_dominance=args.broad_max_physical_pair_dominance,
        ),
        compact=DiversityThresholds(
            min_rows=args.compact_min_rows,
            max_rows=args.compact_max_rows,
            min_seed_blocks=args.compact_min_seed_blocks,
            min_physical_pairs_or_keys=args.compact_min_physical_pairs,
            min_source_steps=args.compact_min_source_steps,
            min_target_buckets=args.compact_min_target_buckets,
            max_seed_block_dominance=args.compact_max_seed_block_dominance,
            max_physical_pair_dominance=args.compact_max_physical_pair_dominance,
        ),
        candidate=CandidateThresholds(
            max_selected_accepted_regressions=args.max_selected_accepted_regressions,
            min_selected_gap_p10=args.min_selected_gap_p10,
            min_selected_gap_min=args.min_selected_gap_min,
            endpoint_repair_accepted_regressions=args.endpoint_repair_accepted_regressions,
            endpoint_repair_gap_p10=args.endpoint_repair_gap_p10,
            endpoint_repair_gap_min=args.endpoint_repair_gap_min,
        ),
        require_old_key_9944=not args.allow_missing_old_key_9944,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the M341 old-key neighborhood gate.")
    parser.add_argument("--candidate-pool-csv", type=Path, required=True)
    parser.add_argument("--compact-corpus-csv", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--broad-min-rows", type=int, default=DEFAULT_THRESHOLDS.broad.min_rows)
    parser.add_argument("--broad-min-seed-blocks", type=int, default=DEFAULT_THRESHOLDS.broad.min_seed_blocks)
    parser.add_argument(
        "--broad-min-physical-pairs",
        type=int,
        default=DEFAULT_THRESHOLDS.broad.min_physical_pairs_or_keys,
    )
    parser.add_argument("--broad-min-source-steps", type=int, default=DEFAULT_THRESHOLDS.broad.min_source_steps)
    parser.add_argument(
        "--broad-min-target-buckets",
        type=int,
        default=DEFAULT_THRESHOLDS.broad.min_target_buckets,
    )
    parser.add_argument(
        "--broad-max-seed-block-dominance",
        type=float,
        default=DEFAULT_THRESHOLDS.broad.max_seed_block_dominance,
    )
    parser.add_argument(
        "--broad-max-physical-pair-dominance",
        type=float,
        default=DEFAULT_THRESHOLDS.broad.max_physical_pair_dominance,
    )
    parser.add_argument("--compact-min-rows", type=int, default=DEFAULT_THRESHOLDS.compact.min_rows)
    parser.add_argument("--compact-max-rows", type=int, default=DEFAULT_THRESHOLDS.compact.max_rows)
    parser.add_argument(
        "--compact-min-seed-blocks",
        type=int,
        default=DEFAULT_THRESHOLDS.compact.min_seed_blocks,
    )
    parser.add_argument(
        "--compact-min-physical-pairs",
        type=int,
        default=DEFAULT_THRESHOLDS.compact.min_physical_pairs_or_keys,
    )
    parser.add_argument(
        "--compact-min-source-steps",
        type=int,
        default=DEFAULT_THRESHOLDS.compact.min_source_steps,
    )
    parser.add_argument(
        "--compact-min-target-buckets",
        type=int,
        default=DEFAULT_THRESHOLDS.compact.min_target_buckets,
    )
    parser.add_argument(
        "--compact-max-seed-block-dominance",
        type=float,
        default=DEFAULT_THRESHOLDS.compact.max_seed_block_dominance,
    )
    parser.add_argument(
        "--compact-max-physical-pair-dominance",
        type=float,
        default=DEFAULT_THRESHOLDS.compact.max_physical_pair_dominance,
    )
    parser.add_argument(
        "--max-selected-accepted-regressions",
        type=int,
        default=DEFAULT_THRESHOLDS.candidate.max_selected_accepted_regressions,
    )
    parser.add_argument(
        "--min-selected-gap-p10",
        type=float,
        default=DEFAULT_THRESHOLDS.candidate.min_selected_gap_p10,
    )
    parser.add_argument(
        "--min-selected-gap-min",
        type=float,
        default=DEFAULT_THRESHOLDS.candidate.min_selected_gap_min,
    )
    parser.add_argument(
        "--endpoint-repair-accepted-regressions",
        type=int,
        default=DEFAULT_THRESHOLDS.candidate.endpoint_repair_accepted_regressions,
    )
    parser.add_argument(
        "--endpoint-repair-gap-p10",
        type=float,
        default=DEFAULT_THRESHOLDS.candidate.endpoint_repair_gap_p10,
    )
    parser.add_argument(
        "--endpoint-repair-gap-min",
        type=float,
        default=DEFAULT_THRESHOLDS.candidate.endpoint_repair_gap_min,
    )
    parser.add_argument("--allow-missing-old-key-9944", action="store_true")
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="old_key_neighborhood_gate")
    result = run_old_key_neighborhood_gate(
        candidate_pool_csv=args.candidate_pool_csv,
        compact_corpus_csv=args.compact_corpus_csv,
        run_dir=run_dir,
        thresholds=_thresholds_from_args(args),
    )
    print(pd.Series({
        "overall_pass": result["overall_pass"],
        "replacement_gate_ready": result["replacement_gate_ready"],
        "selected_alpha_passes": result["selected_alpha_passes"],
        "endpoint_repair_needed": result["endpoint_repair_needed"],
        "failure_types": ",".join(result["failure_types"]),
        "run_dir": str(run_dir),
    }).to_string())


if __name__ == "__main__":
    main()
