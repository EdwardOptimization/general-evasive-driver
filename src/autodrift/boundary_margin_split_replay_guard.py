"""Margin-split guard for boundary replay rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_fragile_row_guard import validate_replay_rows_frame


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes"}


def _class_for_slack(min_slack: float, *, robust_threshold: float, knife_edge_threshold: float) -> str:
    if min_slack < knife_edge_threshold:
        return "knife_edge"
    if min_slack < robust_threshold:
        return "watchlist"
    return "robust"


def classify_margin_rows(
    frame: pd.DataFrame,
    *,
    class_reference_policy: str,
    robust_threshold: float,
    knife_edge_threshold: float,
) -> list[dict[str, Any]]:
    validate_replay_rows_frame(frame)
    if robust_threshold < knife_edge_threshold:
        raise ValueError("robust_threshold must be >= knife_edge_threshold")
    reference = frame[frame["policy"].astype(str) == str(class_reference_policy)].copy()
    if reference.empty:
        raise ValueError("class reference policy must have replay rows")
    rows: list[dict[str, Any]] = []
    for _, row in reference.sort_values("row_id").iterrows():
        if not _to_bool(row["success_drop"]):
            continue
        normal_margin = float(row["normal_margin"])
        wrong_history_margin = float(row["wrong_history_margin"])
        min_slack = min(normal_margin, -wrong_history_margin)
        row_class = _class_for_slack(
            min_slack,
            robust_threshold=robust_threshold,
            knife_edge_threshold=knife_edge_threshold,
        )
        rows.append(
            {
                "row_id": int(row["row_id"]),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "row_class": row_class,
                "normal_margin_reference": normal_margin,
                "wrong_history_margin_reference": wrong_history_margin,
                "min_slack": float(min_slack),
            }
        )
    return rows


def evaluate_margin_split_replay(
    *,
    class_reference_frame: pd.DataFrame,
    candidate_frame: pd.DataFrame,
    class_reference_policy: str,
    candidate_policy: str,
    robust_threshold: float = 0.001,
    knife_edge_threshold: float = 0.0005,
    max_lost_robust_rows: int = 0,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    class_rows = classify_margin_rows(
        class_reference_frame,
        class_reference_policy=class_reference_policy,
        robust_threshold=robust_threshold,
        knife_edge_threshold=knife_edge_threshold,
    )
    validate_replay_rows_frame(candidate_frame)
    candidate = candidate_frame[candidate_frame["policy"].astype(str) == str(candidate_policy)].copy()
    if candidate.empty:
        raise ValueError("candidate policy must have replay rows")
    candidate_by_row = {int(row["row_id"]): row for _, row in candidate.iterrows()}

    classified_rows: list[dict[str, Any]] = []
    for class_row in class_rows:
        row_id = int(class_row["row_id"])
        candidate_row = candidate_by_row.get(row_id)
        candidate_missing = candidate_row is None
        candidate_success_drop = False if candidate_missing else _to_bool(candidate_row["success_drop"])
        status = "retained" if candidate_success_drop else "lost"
        classified_rows.append(
            {
                **class_row,
                "candidate_policy": str(candidate_policy),
                "candidate_missing": candidate_missing,
                "candidate_success_drop": candidate_success_drop,
                "candidate_normal_success": False
                if candidate_missing
                else _to_bool(candidate_row["normal_success"]),
                "candidate_wrong_history_success": False
                if candidate_missing
                else _to_bool(candidate_row["wrong_history_success"]),
                "candidate_normal_margin": None if candidate_missing else float(candidate_row["normal_margin"]),
                "candidate_wrong_history_margin": None
                if candidate_missing
                else float(candidate_row["wrong_history_margin"]),
                "status": status,
            }
        )

    class_summary: list[dict[str, Any]] = []
    lost_by_class: dict[str, list[int]] = {}
    for row_class in ("robust", "watchlist", "knife_edge"):
        rows = [row for row in classified_rows if row["row_class"] == row_class]
        lost = [int(row["row_id"]) for row in rows if not bool(row["candidate_success_drop"])]
        lost_by_class[row_class] = lost
        class_summary.append(
            {
                "row_class": row_class,
                "rows": len(rows),
                "retained_rows": len(rows) - len(lost),
                "lost_rows": len(lost),
                "lost_row_ids": lost,
            }
        )

    robust_lost = lost_by_class["robust"]
    gates = {
        "robust_row_retention": bool(len(robust_lost) <= int(max_lost_robust_rows)),
    }
    summary = {
        "run_type": "boundary_margin_split_replay_guard",
        "class_reference_policy": str(class_reference_policy),
        "candidate_policy": str(candidate_policy),
        "robust_threshold": float(robust_threshold),
        "knife_edge_threshold": float(knife_edge_threshold),
        "class_reference_success_drop_rows": len(class_rows),
        "robust_rows": [int(row["row_id"]) for row in classified_rows if row["row_class"] == "robust"],
        "watchlist_rows": [int(row["row_id"]) for row in classified_rows if row["row_class"] == "watchlist"],
        "knife_edge_rows": [int(row["row_id"]) for row in classified_rows if row["row_class"] == "knife_edge"],
        "lost_robust_rows": robust_lost,
        "lost_watchlist_rows": lost_by_class["watchlist"],
        "lost_knife_edge_rows": lost_by_class["knife_edge"],
        "max_lost_robust_rows": int(max_lost_robust_rows),
        **{f"{name}_pass": passed for name, passed in gates.items()},
        "gate_pass": bool(all(gates.values())),
    }
    return summary, classified_rows, class_summary


def run_boundary_margin_split_replay_guard(
    *,
    class_reference_replay_rows_csv: Path,
    candidate_replay_rows_csv: Path,
    class_reference_policy: str,
    candidate_policy: str,
    robust_threshold: float,
    knife_edge_threshold: float,
    max_lost_robust_rows: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    class_reference_frame = pd.read_csv(class_reference_replay_rows_csv)
    candidate_frame = pd.read_csv(candidate_replay_rows_csv)
    summary, classified_rows, class_summary = evaluate_margin_split_replay(
        class_reference_frame=class_reference_frame,
        candidate_frame=candidate_frame,
        class_reference_policy=class_reference_policy,
        candidate_policy=candidate_policy,
        robust_threshold=robust_threshold,
        knife_edge_threshold=knife_edge_threshold,
        max_lost_robust_rows=max_lost_robust_rows,
    )
    classified_rows_csv = run_dir / "classified_rows.csv"
    class_summary_csv = run_dir / "class_summary.csv"
    write_csv_rows(classified_rows_csv, classified_rows)
    write_csv_rows(class_summary_csv, class_summary)
    result = {
        "class_reference_replay_rows_csv": class_reference_replay_rows_csv,
        "candidate_replay_rows_csv": candidate_replay_rows_csv,
        "classified_rows_csv": classified_rows_csv,
        "class_summary_csv": class_summary_csv,
        **summary,
    }
    write_json(run_dir / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a margin-split boundary replay guard.")
    parser.add_argument("--class-reference-replay-rows-csv", type=Path, required=True)
    parser.add_argument("--candidate-replay-rows-csv", type=Path, required=True)
    parser.add_argument("--class-reference-policy", required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--robust-threshold", type=float, default=0.001)
    parser.add_argument("--knife-edge-threshold", type=float, default=0.0005)
    parser.add_argument("--max-lost-robust-rows", type=int, default=0)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_margin_split_replay_guard")
    summary = run_boundary_margin_split_replay_guard(
        class_reference_replay_rows_csv=args.class_reference_replay_rows_csv,
        candidate_replay_rows_csv=args.candidate_replay_rows_csv,
        class_reference_policy=args.class_reference_policy,
        candidate_policy=args.candidate_policy,
        robust_threshold=args.robust_threshold,
        knife_edge_threshold=args.knife_edge_threshold,
        max_lost_robust_rows=args.max_lost_robust_rows,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
