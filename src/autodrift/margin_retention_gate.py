"""Promotion gate for margin-retention checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


REQUIRED_COLUMNS = {
    "source",
    "seed",
    "baseline_policy",
    "candidate_policy",
    "baseline_success",
    "candidate_success",
    "outcome",
    "critical_reason",
    "near_boundary",
    "margin_regressed",
    "near_margin_regressed",
    "baseline_min_clearance_margin",
    "candidate_min_clearance_margin",
    "min_clearance_margin_delta",
}


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).astype(bool)
    normalized = series.astype(str).str.strip().str.lower()
    truthy = {"true", "1", "yes", "y"}
    falsy = {"false", "0", "no", "n"}
    unknown = sorted(set(normalized).difference(truthy | falsy))
    if unknown:
        raise ValueError(f"cannot parse boolean values: {unknown}")
    return normalized.isin(truthy)


def load_margin_deltas(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"margin delta CSV is missing columns: {missing}")
    output = frame.copy()
    for column in [
        "baseline_success",
        "candidate_success",
        "near_boundary",
        "margin_regressed",
        "near_margin_regressed",
    ]:
        output[column] = _bool_series(output[column])
    output["critical_reason"] = output["critical_reason"].fillna("").astype(str)
    return output


def summarize_candidates(deltas: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_policy, group in deltas.groupby("candidate_policy", observed=True):
        rows.append(
            {
                "baseline_policy": str(group["baseline_policy"].iloc[0]),
                "candidate_policy": str(candidate_policy),
                "pairs": int(len(group)),
                "baseline_success_rate": float(group["baseline_success"].mean()),
                "candidate_success_rate": float(group["candidate_success"].mean()),
                "success_delta_rate": float(group["candidate_success"].mean() - group["baseline_success"].mean()),
                "binary_regressed_seeds": int((group["outcome"] == "regressed").sum()),
                "binary_improved_seeds": int((group["outcome"] == "improved").sum()),
                "critical_seeds": int((group["critical_reason"] != "").sum()),
                "near_boundary_seeds": int(group["near_boundary"].sum()),
                "margin_regressed_seeds": int(group["margin_regressed"].sum()),
                "near_margin_regressed_seeds": int(group["near_margin_regressed"].sum()),
                "baseline_margin_mean": float(group["baseline_min_clearance_margin"].mean()),
                "candidate_margin_mean": float(group["candidate_min_clearance_margin"].mean()),
                "margin_delta_mean": float(group["min_clearance_margin_delta"].mean()),
                "candidate_margin_min": float(group["candidate_min_clearance_margin"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values("candidate_policy").reset_index(drop=True)


def summarize_sources(deltas: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (source, candidate_policy), group in deltas.groupby(["source", "candidate_policy"], observed=True):
        rows.append(
            {
                "source": str(source),
                "candidate_policy": str(candidate_policy),
                "pairs": int(len(group)),
                "baseline_success_rate": float(group["baseline_success"].mean()),
                "candidate_success_rate": float(group["candidate_success"].mean()),
                "success_delta_rate": float(group["candidate_success"].mean() - group["baseline_success"].mean()),
                "binary_regressed_seeds": int((group["outcome"] == "regressed").sum()),
                "binary_improved_seeds": int((group["outcome"] == "improved").sum()),
                "near_margin_regressed_seeds": int(group["near_margin_regressed"].sum()),
                "margin_delta_mean": float(group["min_clearance_margin_delta"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["source", "candidate_policy"]).reset_index(drop=True)


def apply_gate_checks(
    candidate_summary: pd.DataFrame,
    *,
    min_success_delta: float,
    max_binary_regressed_seeds: int,
    max_near_margin_regressed_seeds: int,
    min_margin_delta_mean: float,
) -> pd.DataFrame:
    output = candidate_summary.copy()
    output["success_retained"] = output["success_delta_rate"] >= float(min_success_delta)
    output["binary_regression_ok"] = output["binary_regressed_seeds"] <= int(max_binary_regressed_seeds)
    output["near_margin_regression_ok"] = output["near_margin_regressed_seeds"] <= int(
        max_near_margin_regressed_seeds
    )
    output["mean_margin_retained"] = output["margin_delta_mean"] >= float(min_margin_delta_mean)
    check_columns = [
        "success_retained",
        "binary_regression_ok",
        "near_margin_regression_ok",
        "mean_margin_retained",
    ]
    output["passed"] = output[check_columns].all(axis=1)
    return output


def build_gate_summary(
    deltas: pd.DataFrame,
    *,
    min_success_delta: float,
    max_binary_regressed_seeds: int,
    max_near_margin_regressed_seeds: int,
    min_margin_delta_mean: float,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    candidate_summary = summarize_candidates(deltas)
    candidate_summary = apply_gate_checks(
        candidate_summary,
        min_success_delta=min_success_delta,
        max_binary_regressed_seeds=max_binary_regressed_seeds,
        max_near_margin_regressed_seeds=max_near_margin_regressed_seeds,
        min_margin_delta_mean=min_margin_delta_mean,
    )
    source_summary = summarize_sources(deltas)
    passed_candidates = candidate_summary.loc[candidate_summary["passed"], "candidate_policy"].astype(str).tolist()
    summary = {
        "status": "passed" if passed_candidates else "needs_iteration",
        "passed_candidates": passed_candidates,
        "candidate_count": int(len(candidate_summary)),
        "thresholds": {
            "min_success_delta": float(min_success_delta),
            "max_binary_regressed_seeds": int(max_binary_regressed_seeds),
            "max_near_margin_regressed_seeds": int(max_near_margin_regressed_seeds),
            "min_margin_delta_mean": float(min_margin_delta_mean),
        },
    }
    return summary, candidate_summary, source_summary


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [header, separator]
    for _, row in frame[columns].iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_gate_report(
    path: Path,
    summary: dict[str, Any],
    candidate_summary: pd.DataFrame,
    source_summary: pd.DataFrame,
) -> None:
    lines = [
        "# M51 Margin-Retention Gate Report",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Thresholds",
        "",
    ]
    for name, value in summary["thresholds"].items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(
        [
            "",
            "## Candidate Summary",
            "",
            _markdown_table(
                candidate_summary,
                [
                    "candidate_policy",
                    "passed",
                    "success_delta_rate",
                    "binary_regressed_seeds",
                    "near_margin_regressed_seeds",
                    "margin_delta_mean",
                    "candidate_margin_min",
                ],
            ),
            "",
            "## Source Summary",
            "",
            _markdown_table(
                source_summary,
                [
                    "source",
                    "candidate_policy",
                    "success_delta_rate",
                    "binary_regressed_seeds",
                    "near_margin_regressed_seeds",
                    "margin_delta_mean",
                ],
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_margin_retention_gate(
    run_dir: Path,
    *,
    seed_delta_csv: Path | str,
    min_success_delta: float,
    max_binary_regressed_seeds: int,
    max_near_margin_regressed_seeds: int,
    min_margin_delta_mean: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    deltas = load_margin_deltas(seed_delta_csv)
    summary, candidate_summary, source_summary = build_gate_summary(
        deltas,
        min_success_delta=min_success_delta,
        max_binary_regressed_seeds=max_binary_regressed_seeds,
        max_near_margin_regressed_seeds=max_near_margin_regressed_seeds,
        min_margin_delta_mean=min_margin_delta_mean,
    )
    candidate_summary_csv = run_dir / "candidate_gate_summary.csv"
    source_summary_csv = run_dir / "source_gate_summary.csv"
    summary_json = run_dir / "gate_summary.json"
    report_md = run_dir / "gate_report.md"
    candidate_summary.to_csv(candidate_summary_csv, index=False)
    source_summary.to_csv(source_summary_csv, index=False)
    write_json(summary_json, summary)
    write_gate_report(report_md, summary, candidate_summary, source_summary)
    manifest = {
        "run_type": "margin_retention_gate",
        "seed_delta_csv": str(seed_delta_csv),
        "artifacts": {
            "candidate_summary_csv": str(candidate_summary_csv),
            "source_summary_csv": str(source_summary_csv),
            "summary_json": str(summary_json),
            "report_md": str(report_md),
        },
        "summary": summary,
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the margin-retention promotion gate.")
    parser.add_argument("--seed-delta-csv", type=Path, required=True)
    parser.add_argument("--min-success-delta", type=float, default=0.0)
    parser.add_argument("--max-binary-regressed-seeds", type=int, default=0)
    parser.add_argument("--max-near-margin-regressed-seeds", type=int, default=0)
    parser.add_argument("--min-margin-delta-mean", type=float, default=0.0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="margin_retention_gate")
    manifest = write_margin_retention_gate(
        run_dir,
        seed_delta_csv=args.seed_delta_csv,
        min_success_delta=args.min_success_delta,
        max_binary_regressed_seeds=args.max_binary_regressed_seeds,
        max_near_margin_regressed_seeds=args.max_near_margin_regressed_seeds,
        min_margin_delta_mean=args.min_margin_delta_mean,
    )
    print(pd.Series(manifest["summary"]).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
