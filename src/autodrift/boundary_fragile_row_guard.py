"""Row-level guard for fragile boundary replay success-drop rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


REQUIRED_REPLAY_COLUMNS = (
    "policy",
    "row_id",
    "target",
    "physical_pair_key",
    "normal_success",
    "wrong_history_success",
    "success_drop",
    "normal_margin",
    "wrong_history_margin",
    "margin_gap",
)


def validate_replay_rows_frame(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_REPLAY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("boundary replay rows CSV is missing columns: " + ", ".join(missing))


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    return series.astype(str).str.lower().isin(("true", "1", "yes"))


def _row_ids(row_ids: Iterable[int] | None) -> list[int]:
    if row_ids is None:
        return []
    return sorted({int(row_id) for row_id in row_ids})


def _row_flag(baseline_drop: bool, candidate_drop: bool, required: bool) -> str:
    if baseline_drop and candidate_drop:
        return "retained_success_drop"
    if baseline_drop and not candidate_drop:
        return "lost_success_drop"
    if not baseline_drop and candidate_drop:
        return "gained_success_drop"
    if required:
        return "required_without_success_drop"
    return "unchanged_no_success_drop"


def compare_fragile_replay_rows(
    frame: pd.DataFrame,
    *,
    baseline_policy: str,
    candidate_policy: str,
    required_row_ids: Iterable[int] | None = None,
    max_lost_success_drop_rows: int = 0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_replay_rows_frame(frame)
    required_ids = _row_ids(required_row_ids)
    baseline = frame[frame["policy"].astype(str) == str(baseline_policy)].copy()
    candidate = frame[frame["policy"].astype(str) == str(candidate_policy)].copy()
    if baseline.empty or candidate.empty:
        raise ValueError("baseline and candidate policies must both have replay rows")
    merged = baseline.merge(
        candidate,
        on="row_id",
        suffixes=("_baseline", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(baseline) or len(merged) != len(candidate):
        raise ValueError("baseline and candidate replay rows must cover the same row_id set")

    baseline_drop = _bool_series(merged["success_drop_baseline"])
    candidate_drop = _bool_series(merged["success_drop_candidate"])
    row_ids = merged["row_id"].astype(int)
    required_mask = row_ids.isin(required_ids)
    lost_mask = baseline_drop & ~candidate_drop
    gained_mask = ~baseline_drop & candidate_drop
    changed_mask = baseline_drop != candidate_drop

    missing_required_ids = sorted(set(required_ids) - set(int(row_id) for row_id in row_ids))
    required_success_drop_pass = bool(
        not missing_required_ids
        and (not required_ids or bool((baseline_drop[required_mask] & candidate_drop[required_mask]).all()))
    )
    lost_count = int(lost_mask.sum())
    gates = {
        "lost_success_drop_retention": bool(lost_count <= int(max_lost_success_drop_rows)),
        "required_success_drop_retention": required_success_drop_pass,
    }

    comparison_rows: list[dict[str, Any]] = []
    for index, row in merged.iterrows():
        row_id = int(row["row_id"])
        baseline_has_drop = bool(baseline_drop.loc[index])
        candidate_has_drop = bool(candidate_drop.loc[index])
        required = row_id in required_ids
        if not (baseline_has_drop or candidate_has_drop or required or bool(changed_mask.loc[index])):
            continue
        comparison_rows.append(
            {
                "row_id": row_id,
                "target": str(row["target_baseline"]),
                "physical_pair_key": str(row["physical_pair_key_baseline"]),
                "required": required,
                "status": _row_flag(baseline_has_drop, candidate_has_drop, required),
                "baseline_success_drop": baseline_has_drop,
                "candidate_success_drop": candidate_has_drop,
                "baseline_normal_success": bool(_bool_series(pd.Series([row["normal_success_baseline"]])).iloc[0]),
                "candidate_normal_success": bool(_bool_series(pd.Series([row["normal_success_candidate"]])).iloc[0]),
                "baseline_wrong_history_success": bool(
                    _bool_series(pd.Series([row["wrong_history_success_baseline"]])).iloc[0]
                ),
                "candidate_wrong_history_success": bool(
                    _bool_series(pd.Series([row["wrong_history_success_candidate"]])).iloc[0]
                ),
                "baseline_normal_margin": float(row["normal_margin_baseline"]),
                "candidate_normal_margin": float(row["normal_margin_candidate"]),
                "baseline_wrong_history_margin": float(row["wrong_history_margin_baseline"]),
                "candidate_wrong_history_margin": float(row["wrong_history_margin_candidate"]),
                "baseline_margin_gap": float(row["margin_gap_baseline"]),
                "candidate_margin_gap": float(row["margin_gap_candidate"]),
            }
        )

    summary = {
        "run_type": "boundary_fragile_row_guard",
        "baseline_policy": str(baseline_policy),
        "candidate_policy": str(candidate_policy),
        "rows": int(len(merged)),
        "required_row_ids": required_ids,
        "missing_required_row_ids": missing_required_ids,
        "baseline_success_drop_count": int(baseline_drop.sum()),
        "candidate_success_drop_count": int(candidate_drop.sum()),
        "lost_success_drop_rows": [int(row_id) for row_id in row_ids[lost_mask].tolist()],
        "gained_success_drop_rows": [int(row_id) for row_id in row_ids[gained_mask].tolist()],
        "changed_success_drop_rows": [int(row_id) for row_id in row_ids[changed_mask].tolist()],
        "max_lost_success_drop_rows": int(max_lost_success_drop_rows),
        **{f"{name}_pass": passed for name, passed in gates.items()},
        "gate_pass": bool(all(gates.values())),
    }
    return summary, comparison_rows


def run_boundary_fragile_row_guard(
    *,
    replay_rows_csv: Path,
    baseline_policy: str,
    candidate_policy: str,
    required_row_ids: Iterable[int] | None,
    max_lost_success_drop_rows: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(replay_rows_csv)
    summary, comparison_rows = compare_fragile_replay_rows(
        frame,
        baseline_policy=baseline_policy,
        candidate_policy=candidate_policy,
        required_row_ids=required_row_ids,
        max_lost_success_drop_rows=max_lost_success_drop_rows,
    )
    comparison_csv = run_dir / "fragile_row_comparison.csv"
    write_csv_rows(comparison_csv, comparison_rows)
    result = {
        "replay_rows_csv": replay_rows_csv,
        "comparison_csv": comparison_csv,
        **summary,
    }
    write_json(run_dir / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a row-level fragile boundary replay guard.")
    parser.add_argument("--replay-rows-csv", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--required-row-id", action="append", type=int, default=[])
    parser.add_argument("--max-lost-success-drop-rows", type=int, default=0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_fragile_row_guard")
    summary = run_boundary_fragile_row_guard(
        replay_rows_csv=args.replay_rows_csv,
        baseline_policy=args.baseline_policy,
        candidate_policy=args.candidate_policy,
        required_row_ids=args.required_row_id,
        max_lost_success_drop_rows=args.max_lost_success_drop_rows,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
