"""No-policy source-history corpus expansion plan builder."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


TARGET_SOURCE_FAMILIES = (
    "single_wheel_grip_collapse->single_wheel_grip_collapse",
    "tire_blowout_like->tire_blowout_like",
    "single_wheel_brake_pull->single_wheel_brake_pull",
    "halfshaft_torque_loss->halfshaft_torque_loss",
    "left_right_split_mu->left_right_split_mu",
    "steering_actuator_fault->steering_actuator_fault",
    "global_friction_step->global_friction_step",
    "load_cg_perturbation->load_cg_perturbation",
)
PROBE_TEMPLATES = ("left_brake_probe", "right_brake_probe")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _stable_fold(pair_id: int, fold_count: int) -> int:
    return int((int(pair_id) * 2654435761) % int(fold_count))


def _corner_variant(fault_a: str, fault_b: str) -> str:
    return f"{fault_a}->{fault_b}"


def _margin_bucket(row: dict[str, str]) -> str:
    margin = _finite_float(row.get("min_own_margin", 0.0))
    if margin < 0.0:
        return "negative"
    if margin <= 0.05:
        return "near_005"
    if margin <= 0.20:
        return "near_020"
    return "positive"


def _speed_bin(row: dict[str, str]) -> str:
    speed = _finite_float(row.get("speed", 0.0))
    if speed < 12.0:
        return "low"
    if speed < 16.0:
        return "medium"
    if speed < 22.0:
        return "high"
    return "extreme"


def _obstacle_bin(row: dict[str, str]) -> str:
    x = _finite_float(row.get("obstacle_body_x", 0.0))
    if x < 10.0:
        return "late"
    if x < 16.0:
        return "medium"
    return "early"


def _source_rows(source_corpus_run_dir: Path) -> list[dict[str, str]]:
    path = Path(source_corpus_run_dir) / "all_accepted_source_rows.csv"
    rows = _read_csv_rows(path)
    if not rows:
        raise ValueError(f"no accepted source rows in {path}")
    return rows


def _materialized_pair_ids(history_run_dir: Path) -> set[int]:
    path = Path(history_run_dir) / "history_intervention_rows.csv"
    if not path.exists():
        return set()
    pair_ids: set[int] = set()
    for row in _read_csv_rows(path):
        pair_ids.add(int(float(row["pair_id"])))
    return pair_ids


def _planned_source_rows(rows: list[dict[str, str]], materialized_pairs: set[int], fold_count: int) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: int(float(item["pair_id"]))):
        pair_id = int(float(row["pair_id"]))
        fault_a = str(row["condition_A_fault"])
        fault_b = str(row["condition_B_fault"])
        planned.append(
            {
                "pair_id": pair_id,
                "seed": int(float(row["seed"])),
                "scenario_id": str(row["scenario_id"]),
                "fold": _stable_fold(pair_id, fold_count),
                "fault_family_pair": str(row["fault_family_pair"]),
                "source_family": str(row.get("source_family", row["fault_family_pair"])),
                "source_fault_pair": _corner_variant(fault_a, fault_b),
                "condition_A_fault": fault_a,
                "condition_B_fault": fault_b,
                "severity_pair": str(row.get("severity_pair", "")),
                "speed_bin": _speed_bin(row),
                "obstacle_timing_bin": _obstacle_bin(row),
                "margin_bucket": _margin_bucket(row),
                "min_own_margin": _finite_float(row.get("min_own_margin", 0.0)),
                "min_cross_regret": _finite_float(row.get("min_cross_regret", 0.0)),
                "materialized_in_current_history": pair_id in materialized_pairs,
                "plan_status": "available_existing",
            }
        )
    return planned


def _planned_pair_probe_rows(planned_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in planned_sources:
        for probe_template in PROBE_TEMPLATES:
            rows.append(
                {
                    "pair_id": int(source["pair_id"]),
                    "probe_template": probe_template,
                    "fold": int(source["fold"]),
                    "fault_family_pair": str(source["fault_family_pair"]),
                    "source_fault_pair": str(source["source_fault_pair"]),
                    "margin_bucket": str(source["margin_bucket"]),
                    "speed_bin": str(source["speed_bin"]),
                    "obstacle_timing_bin": str(source["obstacle_timing_bin"]),
                    "materialized_in_current_history": bool(source["materialized_in_current_history"]),
                    "plan_status": str(source["plan_status"]),
                }
            )
    return rows


def _fold_balance_rows(pair_probe_rows: list[dict[str, Any]], fold_count: int) -> tuple[list[dict[str, Any]], float, bool]:
    rows: list[dict[str, Any]] = []
    all_nonempty = True
    max_share = 0.0
    for fold in range(int(fold_count)):
        values = [row for row in pair_probe_rows if int(row["fold"]) == fold]
        all_nonempty = all_nonempty and bool(values)
        family_counts: dict[str, int] = defaultdict(int)
        probe_counts: dict[str, int] = defaultdict(int)
        for row in values:
            family_counts[str(row["fault_family_pair"])] += 1
            probe_counts[str(row["probe_template"])] += 1
        top_family_count = max(family_counts.values()) if family_counts else 0
        top_probe_count = max(probe_counts.values()) if probe_counts else 0
        family_share = float(top_family_count / len(values)) if values else 0.0
        probe_share = float(top_probe_count / len(values)) if values else 0.0
        max_share = max(max_share, family_share)
        rows.append(
            {
                "fold": fold,
                "pair_probe_group_count": int(len(values)),
                "source_family_count": int(len(family_counts)),
                "top_source_family_pair": max(family_counts, key=family_counts.get) if family_counts else "",
                "top_source_family_count": int(top_family_count),
                "top_source_family_share": family_share,
                "top_probe_template_count": int(top_probe_count),
                "top_probe_template_share": probe_share,
            }
        )
    return rows, max_share, all_nonempty


def _family_coverage_rows(planned_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in planned_sources:
        grouped[str(row["fault_family_pair"])].append(row)
    rows: list[dict[str, Any]] = []
    for family in sorted(set(TARGET_SOURCE_FAMILIES) | set(grouped)):
        values = grouped.get(family, [])
        rows.append(
            {
                "fault_family_pair": family,
                "planned_source_pairs": int(len(values)),
                "materialized_source_pairs": int(sum(bool(row["materialized_in_current_history"]) for row in values)),
                "corner_or_side_variant_count": int(len({str(row["source_fault_pair"]) for row in values})),
                "speed_bin_count": int(len({str(row["speed_bin"]) for row in values})),
                "obstacle_timing_bin_count": int(len({str(row["obstacle_timing_bin"]) for row in values})),
                "coverage_status": "available" if values else "missing",
            }
        )
    return rows


def _requires_update_rows(family_rows: list[dict[str, Any]], target_source_pairs: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_per_family = max(1, int(target_source_pairs) // len(TARGET_SOURCE_FAMILIES))
    for row in family_rows:
        planned = int(row["planned_source_pairs"])
        if planned >= target_per_family and str(row["coverage_status"]) == "available":
            continue
        if planned == 0:
            reason = "family_missing"
        else:
            reason = "family_under_target"
        rows.append(
            {
                "fault_family_pair": str(row["fault_family_pair"]),
                "planned_source_pairs": planned,
                "target_source_pairs_for_family": int(target_per_family),
                "reason": reason,
                "recommended_next_step": "source_generator_update",
            }
        )
    return rows


def run_corpus_expansion_plan(
    *,
    source_corpus_run_dir: Path,
    history_run_dir: Path,
    run_dir: Path,
    target_source_pairs: int = 240,
    fold_count: int = 5,
) -> dict[str, Any]:
    source_corpus_run_dir = Path(source_corpus_run_dir)
    history_run_dir = Path(history_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if int(fold_count) < 2:
        raise ValueError("fold_count must be at least 2")

    source_rows = _source_rows(source_corpus_run_dir)
    materialized_pairs = _materialized_pair_ids(history_run_dir)
    planned_sources = _planned_source_rows(source_rows, materialized_pairs, int(fold_count))
    pair_probe_rows = _planned_pair_probe_rows(planned_sources)
    fold_rows, max_family_fold_share, all_folds_nonempty = _fold_balance_rows(pair_probe_rows, int(fold_count))
    family_rows = _family_coverage_rows(planned_sources)
    update_rows = _requires_update_rows(family_rows, int(target_source_pairs))

    family_count = len({str(row["fault_family_pair"]) for row in planned_sources})
    corner_variant_count = len({str(row["source_fault_pair"]) for row in planned_sources})
    planned_source_pairs = len(planned_sources)
    planned_pair_probe_groups = len(pair_probe_rows)
    coverage_gap_reported = bool(update_rows)
    target_pairs_met = planned_source_pairs >= int(target_source_pairs)
    target_groups_met = planned_pair_probe_groups >= int(target_source_pairs) * len(PROBE_TEMPLATES)
    target_family_met = family_count >= 6
    result_class = (
        "source_history_corpus_expansion_plan_admissible"
        if target_pairs_met and target_groups_met and target_family_met and max_family_fold_share <= 0.40
        else "source_history_corpus_expansion_plan_gap_reported"
    )
    recommended_next_step = (
        "route to source-history materialization design"
        if result_class == "source_history_corpus_expansion_plan_admissible"
        else "route to source generator update design before materialization"
    )

    summary = {
        "run_type": "source_history_corpus_expansion_plan",
        "result_class": result_class,
        "source_corpus_run_dir": str(source_corpus_run_dir),
        "history_run_dir": str(history_run_dir),
        "target_source_pairs": int(target_source_pairs),
        "target_pair_probe_groups": int(target_source_pairs) * len(PROBE_TEMPLATES),
        "fold_count": int(fold_count),
        "planned_source_pairs": int(planned_source_pairs),
        "planned_pair_probe_groups": int(planned_pair_probe_groups),
        "source_fault_family_count": int(family_count),
        "corner_or_side_variant_count": int(corner_variant_count),
        "materialized_source_pair_count": int(sum(bool(row["materialized_in_current_history"]) for row in planned_sources)),
        "all_folds_nonempty": bool(all_folds_nonempty),
        "pair_disjoint": True,
        "max_source_family_fold_share": float(max_family_fold_share),
        "pair_specific_weight_used": False,
        "target_source_pairs_met": bool(target_pairs_met),
        "target_pair_probe_groups_met": bool(target_groups_met),
        "target_source_family_count_met": bool(target_family_met),
        "coverage_gap_reported": bool(coverage_gap_reported),
        "unsupported_or_undercovered_family_count": int(len(update_rows)),
        "recommended_next_step": recommended_next_step,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "planned_source_pairs_csv": str(run_dir / "planned_source_pairs.csv"),
        "planned_pair_probe_groups_csv": str(run_dir / "planned_pair_probe_groups.csv"),
        "fold_balance_summary_csv": str(run_dir / "fold_balance_summary.csv"),
        "family_coverage_summary_csv": str(run_dir / "family_coverage_summary.csv"),
        "requires_source_generator_update_csv": str(run_dir / "requires_source_generator_update.csv"),
    }
    write_csv_rows(run_dir / "planned_source_pairs.csv", planned_sources)
    write_csv_rows(run_dir / "planned_pair_probe_groups.csv", pair_probe_rows)
    write_csv_rows(run_dir / "fold_balance_summary.csv", fold_rows)
    write_csv_rows(run_dir / "family_coverage_summary.csv", family_rows)
    write_csv_rows(run_dir / "requires_source_generator_update.csv", update_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-corpus-run-dir", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--target-source-pairs", type=int, default=240)
    parser.add_argument("--fold-count", type=int, default=5)
    args = parser.parse_args()
    summary = run_corpus_expansion_plan(
        source_corpus_run_dir=args.source_corpus_run_dir,
        history_run_dir=args.history_run_dir,
        run_dir=args.run_dir,
        target_source_pairs=args.target_source_pairs,
        fold_count=args.fold_count,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
