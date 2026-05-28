"""Export stratified four-wheel source corpora from accepted source rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _min_own_margin(row: dict[str, Any]) -> float:
    return min(
        _finite_float(row.get("margin_A_best_A")),
        _finite_float(row.get("margin_B_best_B")),
    )


def _min_cross_regret(row: dict[str, Any]) -> float:
    return min(
        _finite_float(row.get("cross_regret_A")),
        _finite_float(row.get("cross_regret_B")),
    )


def _enrich_accepted_row(row: dict[str, str], scenarios_by_id: dict[str, dict[str, str]]) -> dict[str, Any]:
    scenario = scenarios_by_id.get(str(row.get("scenario_id", "")), {})
    min_own = _min_own_margin(row)
    min_regret = _min_cross_regret(row)
    enriched = dict(row)
    enriched.update(
        {
            "speed": _finite_float(scenario.get("vx")),
            "min_own_margin": min_own,
            "min_cross_regret": min_regret,
            "near_boundary_margin_le_0_05": bool(min_own <= 0.05),
            "near_boundary_margin_le_0_10": bool(min_own <= 0.10),
            "near_boundary_margin_le_0_20": bool(min_own <= 0.20),
            "high_regret_ge_0_05": bool(min_regret >= 0.05),
            "high_regret_ge_0_10": bool(min_regret >= 0.10),
            "source_family": row.get("fault_family_pair", ""),
        }
    )
    return enriched


def _family_balanced_rows(rows: list[dict[str, Any]], *, cap_per_family: int) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row.get("source_family", ""))].append(row)

    balanced: list[dict[str, Any]] = []
    for family in sorted(by_family):
        ranked = sorted(
            by_family[family],
            key=lambda item: (
                _finite_float(item.get("min_own_margin"), default=float("inf")),
                -_finite_float(item.get("min_cross_regret"), default=0.0),
                int(float(item.get("pair_id", 0))),
            ),
        )
        for rank, row in enumerate(ranked[: int(cap_per_family)], start=1):
            selected = dict(row)
            selected["family_balance_rank"] = rank
            selected["family_balance_cap"] = int(cap_per_family)
            balanced.append(selected)
    return sorted(balanced, key=lambda item: (str(item.get("source_family", "")), int(item["family_balance_rank"])))


def _inactive_fault_family_rows(
    matched_rows: list[dict[str, str]],
    accepted_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    accepted_by_family = Counter(str(row.get("source_family", "")) for row in accepted_rows)
    rows_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in matched_rows:
        rows_by_family[str(row.get("fault_family_pair", ""))].append(row)

    inactive_rows: list[dict[str, Any]] = []
    for family in sorted(rows_by_family):
        rows = rows_by_family[family]
        if accepted_by_family.get(family, 0) > 0:
            continue
        best_action_l2_values = [_finite_float(row.get("best_action_l2")) for row in rows]
        min_regret_values = [_min_cross_regret(row) for row in rows]
        own_viable_count = sum(
            str(row.get("best_A_success", "")).lower() == "true"
            and str(row.get("best_B_success", "")).lower() == "true"
            for row in rows
        )
        reason_counts = Counter(str(row.get("rejection_reason", "")) for row in rows)
        inactive_rows.append(
            {
                "fault_family_pair": family,
                "matched_rows": len(rows),
                "accepted_rows": 0,
                "own_branch_viable_count": int(own_viable_count),
                "max_best_action_l2": max(best_action_l2_values) if best_action_l2_values else 0.0,
                "max_min_cross_regret": max(min_regret_values) if min_regret_values else 0.0,
                "rejection_reason_counts": ";".join(
                    f"{reason}:{count}" for reason, count in sorted(reason_counts.items())
                ),
            }
        )
    return inactive_rows


def export_four_wheel_source_corpus(
    *,
    source_run_dir: Path,
    run_dir: Path,
    near_boundary_margin: float = 0.20,
    high_regret_margin: float = 0.05,
    family_cap: int = 21,
) -> dict[str, Any]:
    source_run_dir = Path(source_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source_run_dir / "summary.json")
    accepted_input = _read_csv(source_run_dir / "accepted_separable_pairs.csv")
    matched_rows = _read_csv(source_run_dir / "matched_capability_pairs.csv")
    scenario_rows = _read_csv(source_run_dir / "scenario_summary.csv")
    scenarios_by_id = {str(row.get("scenario_id", "")): row for row in scenario_rows}

    accepted_rows = [_enrich_accepted_row(row, scenarios_by_id) for row in accepted_input]
    near_boundary_rows = [
        row for row in accepted_rows if _finite_float(row.get("min_own_margin"), default=float("inf")) <= near_boundary_margin
    ]
    high_regret_rows = [
        row for row in accepted_rows if _finite_float(row.get("min_cross_regret")) >= high_regret_margin
    ]
    family_balanced_rows = _family_balanced_rows(accepted_rows, cap_per_family=family_cap)
    inactive_rows = _inactive_fault_family_rows(matched_rows, accepted_rows)

    write_csv_rows(run_dir / "all_accepted_source_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "near_boundary_source_rows.csv", near_boundary_rows)
    write_csv_rows(run_dir / "high_regret_source_rows.csv", high_regret_rows)
    write_csv_rows(run_dir / "family_balanced_source_rows.csv", family_balanced_rows)
    write_csv_rows(
        run_dir / "inactive_fault_families.csv",
        inactive_rows,
        fieldnames=[
            "fault_family_pair",
            "matched_rows",
            "accepted_rows",
            "own_branch_viable_count",
            "max_best_action_l2",
            "max_min_cross_regret",
            "rejection_reason_counts",
        ],
    )

    family_counts = Counter(str(row.get("source_family", "")) for row in accepted_rows)
    near_boundary_family_counts = Counter(str(row.get("source_family", "")) for row in near_boundary_rows)
    high_regret_family_counts = Counter(str(row.get("source_family", "")) for row in high_regret_rows)
    summary = {
        "run_type": "four_wheel_source_corpus_export",
        "source_run_dir": str(source_run_dir),
        "source_scenario_profile": source_summary.get("scenario_profile", ""),
        "source_accepted_separable_pairs": int(source_summary.get("accepted_separable_pairs", 0)),
        "exported_accepted_rows": int(len(accepted_rows)),
        "near_boundary_margin_threshold": float(near_boundary_margin),
        "near_boundary_rows": int(len(near_boundary_rows)),
        "high_regret_margin_threshold": float(high_regret_margin),
        "high_regret_rows": int(len(high_regret_rows)),
        "family_balance_cap": int(family_cap),
        "family_balanced_rows": int(len(family_balanced_rows)),
        "accepted_family_counts": dict(sorted(family_counts.items())),
        "near_boundary_family_counts": dict(sorted(near_boundary_family_counts.items())),
        "high_regret_family_counts": dict(sorted(high_regret_family_counts.items())),
        "inactive_fault_family_count": int(len(inactive_rows)),
        "inactive_fault_families": [row["fault_family_pair"] for row in inactive_rows],
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "all_accepted_source_rows_csv": run_dir / "all_accepted_source_rows.csv",
        "near_boundary_source_rows_csv": run_dir / "near_boundary_source_rows.csv",
        "high_regret_source_rows_csv": run_dir / "high_regret_source_rows.csv",
        "family_balanced_source_rows_csv": run_dir / "family_balanced_source_rows.csv",
        "inactive_fault_families_csv": run_dir / "inactive_fault_families.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export stratified four-wheel source corpus artifacts.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--near-boundary-margin", type=float, default=0.20)
    parser.add_argument("--high-regret-margin", type=float, default=0.05)
    parser.add_argument("--family-cap", type=int, default=21)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="four_wheel_source_corpus_export")
    summary = export_four_wheel_source_corpus(
        source_run_dir=args.source_run_dir,
        run_dir=run_dir,
        near_boundary_margin=args.near_boundary_margin,
        high_regret_margin=args.high_regret_margin,
        family_cap=args.family_cap,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
