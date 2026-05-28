"""Merge M1322 source export rows with M1327 top-up source rows."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.four_wheel_source_corpus_export import (
    _enrich_accepted_row,
    _family_balanced_rows,
    _finite_float,
    _read_csv,
)

TARGET_FAMILY_ROWS = 30
TARGET_FAMILIES = (
    "global_friction_step->global_friction_step",
    "halfshaft_torque_loss->halfshaft_torque_loss",
    "left_right_split_mu->left_right_split_mu",
    "load_cg_perturbation->load_cg_perturbation",
    "single_wheel_brake_pull->single_wheel_brake_pull",
    "single_wheel_grip_collapse->single_wheel_grip_collapse",
    "steering_actuator_fault->steering_actuator_fault",
    "tire_blowout_like->tire_blowout_like",
)


def _source_identity(row: dict[str, Any]) -> str:
    return f"{row.get('source_run_id', '')}:{row.get('source_row_id', '')}"


def _with_source_identity(
    rows: list[dict[str, Any]],
    *,
    source_run_id: str,
    source_input_path: Path,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        merged = dict(row)
        merged.setdefault("source_family", merged.get("fault_family_pair", ""))
        merged["source_run_id"] = str(source_run_id)
        merged["source_row_id"] = str(row.get("pair_id", ""))
        merged["original_pair_id"] = str(row.get("pair_id", ""))
        merged["source_identity"] = f"{source_run_id}:{row.get('pair_id', '')}"
        merged["source_input_path"] = str(source_input_path)
        output.append(merged)
    return output


def _reindex_merged_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for merged_pair_id, row in enumerate(rows):
        updated = dict(row)
        updated["pair_id"] = int(merged_pair_id)
        output.append(updated)
    return output


def _read_base_export_rows(base_export_run_dir: Path) -> list[dict[str, Any]]:
    path = base_export_run_dir / "all_accepted_source_rows.csv"
    rows = _read_csv(path)
    return _with_source_identity(
        rows,
        source_run_id=base_export_run_dir.name,
        source_input_path=path,
    )


def _read_topup_rows(topup_source_run_dir: Path) -> list[dict[str, Any]]:
    accepted_path = topup_source_run_dir / "accepted_separable_pairs.csv"
    scenario_rows = _read_csv(topup_source_run_dir / "scenario_summary.csv")
    scenarios_by_id = {str(row.get("scenario_id", "")): row for row in scenario_rows}
    accepted_rows = [_enrich_accepted_row(row, scenarios_by_id) for row in _read_csv(accepted_path)]
    return _with_source_identity(
        accepted_rows,
        source_run_id=topup_source_run_dir.name,
        source_input_path=accepted_path,
    )


def _near_boundary_rows(rows: list[dict[str, Any]], *, margin: float) -> list[dict[str, Any]]:
    return [row for row in rows if _finite_float(row.get("min_own_margin"), default=float("inf")) <= margin]


def _high_regret_rows(rows: list[dict[str, Any]], *, margin: float) -> list[dict[str, Any]]:
    return [row for row in rows if _finite_float(row.get("min_cross_regret")) >= margin]


def _source_run_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[str(row.get("source_run_id", ""))].append(row)
    output = []
    for source_run_id in sorted(by_source):
        source_rows = by_source[source_run_id]
        family_counts = Counter(str(row.get("source_family", "")) for row in source_rows)
        output.append(
            {
                "source_run_id": source_run_id,
                "accepted_rows": int(len(source_rows)),
                "source_input_paths": ";".join(sorted({str(row.get("source_input_path", "")) for row in source_rows})),
                "accepted_family_counts": ";".join(
                    f"{family}:{count}" for family, count in sorted(family_counts.items())
                ),
            }
        )
    return output


def _family_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row.get("source_family", ""))].append(row)
    output = []
    for family in sorted(by_family):
        family_rows = by_family[family]
        by_source = Counter(str(row.get("source_run_id", "")) for row in family_rows)
        output.append(
            {
                "fault_family_pair": family,
                "accepted_rows": int(len(family_rows)),
                "source_run_counts": ";".join(f"{source}:{count}" for source, count in sorted(by_source.items())),
                "near_boundary_rows": int(sum(_finite_float(row.get("min_own_margin"), default=float("inf")) <= 0.20 for row in family_rows)),
                "high_regret_rows": int(sum(_finite_float(row.get("min_cross_regret")) >= 0.05 for row in family_rows)),
            }
        )
    return output


def _semantic_duplicate_key(row: dict[str, Any]) -> tuple[str, ...]:
    fields = (
        "condition_A_fault",
        "condition_B_fault",
        "fault_family_pair",
        "severity_pair",
        "corner_or_side_variant_pair",
        "scenario_id",
        "seed",
        "obstacle_body_x",
        "obstacle_body_y",
        "obstacle_half_width",
        "speed_bin",
        "obstacle_timing_bin",
        "scenario_curvature_bin",
        "best_A_template",
        "best_B_template",
        "best_candidate_A",
        "best_candidate_B",
    )
    return tuple(str(row.get(field, "")) for field in fields)


def _semantic_duplicate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_semantic_duplicate_key(row)].append(row)
    output = []
    for group_id, (key, group_rows) in enumerate(sorted(grouped.items(), key=lambda item: item[0])):
        if len(group_rows) <= 1:
            continue
        representative = group_rows[0]
        output.append(
            {
                "semantic_duplicate_group_id": int(group_id),
                "duplicate_count": int(len(group_rows)),
                "source_identities": ";".join(sorted(_source_identity(row) for row in group_rows)),
                "fault_family_pair": representative.get("fault_family_pair", ""),
                "condition_A_fault": representative.get("condition_A_fault", ""),
                "condition_B_fault": representative.get("condition_B_fault", ""),
                "scenario_id": representative.get("scenario_id", ""),
                "best_A_template": representative.get("best_A_template", ""),
                "best_B_template": representative.get("best_B_template", ""),
                "semantic_key": "|".join(key),
            }
        )
    return output


def _inactive_or_undercovered_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_counts = Counter(str(row.get("source_family", "")) for row in rows)
    output = []
    for family in TARGET_FAMILIES:
        accepted = int(family_counts.get(family, 0))
        if accepted >= TARGET_FAMILY_ROWS:
            status = "available"
        elif accepted == 0:
            status = "missing"
        else:
            status = "under_target"
        if status != "available":
            output.append(
                {
                    "fault_family_pair": family,
                    "accepted_rows": accepted,
                    "target_rows": TARGET_FAMILY_ROWS,
                    "coverage_status": status,
                    "recommended_next_step": "source_generator_update",
                }
            )
    return output


def export_source_topup_additive_merge(
    *,
    base_export_run_dir: Path,
    topup_source_run_dir: Path,
    run_dir: Path,
    near_boundary_margin: float = 0.20,
    high_regret_margin: float = 0.05,
    family_cap: int = 40,
) -> dict[str, Any]:
    base_export_run_dir = Path(base_export_run_dir)
    topup_source_run_dir = Path(topup_source_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_summary = read_json(base_export_run_dir / "summary.json")
    topup_summary = read_json(topup_source_run_dir / "summary.json")
    merged_rows = _reindex_merged_rows(
        _read_base_export_rows(base_export_run_dir) + _read_topup_rows(topup_source_run_dir)
    )

    identities = [_source_identity(row) for row in merged_rows]
    duplicate_identity_count = int(len(identities) - len(set(identities)))
    semantic_duplicates = _semantic_duplicate_rows(merged_rows)
    near_boundary = _near_boundary_rows(merged_rows, margin=near_boundary_margin)
    high_regret = _high_regret_rows(merged_rows, margin=high_regret_margin)
    family_balanced = _family_balanced_rows(merged_rows, cap_per_family=family_cap)
    family_summary = _family_summary(merged_rows)
    source_summary_rows = _source_run_summary(merged_rows)
    inactive_or_undercovered = _inactive_or_undercovered_rows(merged_rows)
    family_counts = Counter(str(row.get("source_family", "")) for row in merged_rows)

    write_csv_rows(run_dir / "all_accepted_source_rows.csv", merged_rows)
    write_csv_rows(run_dir / "near_boundary_source_rows.csv", near_boundary)
    write_csv_rows(run_dir / "high_regret_source_rows.csv", high_regret)
    write_csv_rows(run_dir / "family_balanced_source_rows.csv", family_balanced)
    write_csv_rows(run_dir / "source_run_summary.csv", source_summary_rows)
    write_csv_rows(run_dir / "family_source_summary.csv", family_summary)
    write_csv_rows(run_dir / "semantic_duplicate_groups.csv", semantic_duplicates)
    write_csv_rows(
        run_dir / "inactive_or_undercovered_families.csv",
        inactive_or_undercovered,
        fieldnames=[
            "fault_family_pair",
            "accepted_rows",
            "target_rows",
            "coverage_status",
            "recommended_next_step",
        ],
    )

    summary = {
        "run_type": "source_topup_additive_merge_export",
        "base_export_run_dir": str(base_export_run_dir),
        "topup_source_run_dir": str(topup_source_run_dir),
        "base_exported_accepted_rows": int(base_summary.get("exported_accepted_rows", 0)),
        "topup_accepted_separable_pairs": int(topup_summary.get("accepted_separable_pairs", 0)),
        "merged_source_identity_rows": int(len(merged_rows)),
        "source_identity_duplicate_count": duplicate_identity_count,
        "semantic_duplicate_group_count": int(len(semantic_duplicates)),
        "near_boundary_margin_threshold": float(near_boundary_margin),
        "near_boundary_rows": int(len(near_boundary)),
        "high_regret_margin_threshold": float(high_regret_margin),
        "high_regret_rows": int(len(high_regret)),
        "family_balance_cap": int(family_cap),
        "family_balanced_rows": int(len(family_balanced)),
        "accepted_fault_family_pairs": int(len(family_counts)),
        "accepted_family_counts": dict(sorted(family_counts.items())),
        "inactive_or_undercovered_family_count": int(len(inactive_or_undercovered)),
        "inactive_or_undercovered_families": [row["fault_family_pair"] for row in inactive_or_undercovered],
        "global_friction_missing": bool(family_counts.get("global_friction_step->global_friction_step", 0) == 0),
        "halfshaft_undercovered": bool(
            family_counts.get("halfshaft_torque_loss->halfshaft_torque_loss", 0) < TARGET_FAMILY_ROWS
        ),
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
        "source_run_summary_csv": run_dir / "source_run_summary.csv",
        "family_source_summary_csv": run_dir / "family_source_summary.csv",
        "semantic_duplicate_groups_csv": run_dir / "semantic_duplicate_groups.csv",
        "inactive_or_undercovered_families_csv": run_dir / "inactive_or_undercovered_families.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export additive source top-up merge artifacts.")
    parser.add_argument("--base-export-run-dir", type=Path, required=True)
    parser.add_argument("--topup-source-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--near-boundary-margin", type=float, default=0.20)
    parser.add_argument("--high-regret-margin", type=float, default=0.05)
    parser.add_argument("--family-cap", type=int, default=40)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="source_topup_additive_merge_export")
    summary = export_source_topup_additive_merge(
        base_export_run_dir=args.base_export_run_dir,
        topup_source_run_dir=args.topup_source_run_dir,
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
