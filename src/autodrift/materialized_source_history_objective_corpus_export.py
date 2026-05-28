"""Export active/quarantined materialized source-history objective corpus rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


HALFSHAFT_FAMILY = "halfshaft_torque_loss->halfshaft_torque_loss"
GLOBAL_FRICTION_FAMILY = "global_friction_step->global_friction_step"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _pair_id(row: dict[str, Any]) -> str:
    return str(int(float(row["pair_id"])))


def _active_pair_ids(
    source_rows: list[dict[str, str]],
    prefix_rows: list[dict[str, str]],
    *,
    min_response_l2: float,
) -> tuple[set[str], dict[str, str]]:
    prefixes_by_pair: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in prefix_rows:
        prefixes_by_pair[_pair_id(row)].append(row)

    reasons: dict[str, str] = {}
    active: set[str] = set()
    for row in source_rows:
        pair_id = _pair_id(row)
        source_family = str(row.get("source_family", row.get("fault_family_pair", "")))
        pair_prefixes = prefixes_by_pair.get(pair_id, [])
        if source_family == HALFSHAFT_FAMILY:
            reasons[pair_id] = "halfshaft_probe_silent"
            continue
        if not pair_prefixes:
            reasons[pair_id] = "missing_history_prefix"
            continue
        if any(_finite_float(prefix.get("response_l2_from_opposite_branch")) < float(min_response_l2) for prefix in pair_prefixes):
            reasons[pair_id] = "response_l2_below_threshold"
            continue
        active.add(pair_id)
    return active, reasons


def _filter(rows: list[dict[str, str]], pair_ids: set[str]) -> list[dict[str, str]]:
    return [row for row in rows if _pair_id(row) in pair_ids]


def _source_identity_duplicate_count(rows: list[dict[str, str]]) -> int:
    identities = [str(row.get("source_identity", "")) for row in rows]
    return int(len(identities) - len(set(identities)))


def _metadata_preserved(rows_by_name: dict[str, list[dict[str, str]]]) -> bool:
    required = ("source_run_id", "source_row_id", "original_pair_id", "source_identity")
    for rows in rows_by_name.values():
        for row in rows:
            for key in required:
                if not str(row.get(key, "")):
                    return False
    return True


def _family_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("source_family", row.get("fault_family_pair", ""))) for row in rows)
    return [
        {"source_family": family, "source_pair_rows": int(count)}
        for family, count in sorted(counts.items())
    ]


def _fold_summary(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], float]:
    by_fold: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_fold[str(row.get("fold", ""))].append(row)
    output: list[dict[str, Any]] = []
    max_share = 0.0
    for fold in sorted(by_fold, key=lambda value: int(float(value)) if value else -1):
        values = by_fold[fold]
        family_counts = Counter(str(row.get("source_family", row.get("fault_family_pair", ""))) for row in values)
        top_count = max(family_counts.values()) if family_counts else 0
        share = float(top_count / len(values)) if values else 0.0
        max_share = max(max_share, share)
        output.append(
            {
                "fold": int(float(fold)) if fold else -1,
                "source_pair_rows": int(len(values)),
                "source_family_count": int(len(family_counts)),
                "top_source_family": max(family_counts, key=family_counts.get) if family_counts else "",
                "top_source_family_count": int(top_count),
                "top_source_family_share": float(share),
            }
        )
    return output, max_share


def _quarantine_source_rows(
    source_rows: list[dict[str, str]],
    reasons_by_pair: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        pair_id = _pair_id(row)
        if pair_id not in reasons_by_pair:
            continue
        rows.append(dict(row) | {"quarantine_reason": reasons_by_pair[pair_id]})
    return rows


def _quarantine_family_rows(
    quarantine_source_rows: list[dict[str, Any]],
    *,
    global_friction_missing: bool,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in quarantine_source_rows:
        family = str(row.get("source_family", row.get("fault_family_pair", "")))
        reason = str(row.get("quarantine_reason", ""))
        grouped[(family, reason)].append(row)
    rows = [
        {
            "source_family": family,
            "quarantine_reason": reason,
            "source_pair_rows": int(len(values)),
        }
        for (family, reason), values in sorted(grouped.items())
    ]
    if global_friction_missing:
        rows.append(
            {
                "source_family": GLOBAL_FRICTION_FAMILY,
                "quarantine_reason": "global_friction_missing",
                "source_pair_rows": 0,
            }
        )
    return rows


def export_materialized_source_history_objective_corpus(
    *,
    materialized_run_dir: Path,
    run_dir: Path,
    min_response_l2: float = 0.01,
) -> dict[str, Any]:
    materialized_run_dir = Path(materialized_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    materialized_summary = read_json(materialized_run_dir / "summary.json")
    source_rows = _read_csv(materialized_run_dir / "source_pair_rows.csv")
    prefix_rows = _read_csv(materialized_run_dir / "history_prefix_rows.csv")
    frame_rows = _read_csv(materialized_run_dir / "history_frame_rows.csv")
    intervention_rows = _read_csv(materialized_run_dir / "history_intervention_rows.csv")
    wrong_rows = _read_csv(materialized_run_dir / "wrong_history_pair_rows.csv")
    lineage_rows = _read_csv(materialized_run_dir / "source_lineage_rows.csv")

    active_ids, quarantine_reasons = _active_pair_ids(
        source_rows,
        prefix_rows,
        min_response_l2=float(min_response_l2),
    )
    quarantine_ids = set(quarantine_reasons)

    active_source = _filter(source_rows, active_ids)
    active_prefix = _filter(prefix_rows, active_ids)
    active_frames = _filter(frame_rows, active_ids)
    active_interventions = _filter(intervention_rows, active_ids)
    active_wrong = _filter(wrong_rows, active_ids)

    quarantine_source = _quarantine_source_rows(source_rows, quarantine_reasons)
    quarantine_prefix = _filter(prefix_rows, quarantine_ids)
    quarantine_frames = _filter(frame_rows, quarantine_ids)
    quarantine_interventions = _filter(intervention_rows, quarantine_ids)
    quarantine_wrong = _filter(wrong_rows, quarantine_ids)
    quarantine_family = _quarantine_family_rows(
        quarantine_source,
        global_friction_missing=bool(materialized_summary.get("global_friction_missing", False)),
    )
    active_family = _family_summary(active_source)
    active_fold, max_fold_share = _fold_summary(active_source)

    write_csv_rows(run_dir / "active_source_pair_rows.csv", active_source)
    write_csv_rows(run_dir / "active_history_prefix_rows.csv", active_prefix)
    write_csv_rows(run_dir / "active_history_frame_rows.csv", active_frames)
    write_csv_rows(run_dir / "active_history_intervention_rows.csv", active_interventions)
    write_csv_rows(run_dir / "active_wrong_history_pair_rows.csv", active_wrong)
    write_csv_rows(run_dir / "quarantine_source_pair_rows.csv", quarantine_source)
    write_csv_rows(run_dir / "quarantine_history_prefix_rows.csv", quarantine_prefix)
    write_csv_rows(run_dir / "quarantine_history_frame_rows.csv", quarantine_frames)
    write_csv_rows(run_dir / "quarantine_history_intervention_rows.csv", quarantine_interventions)
    write_csv_rows(run_dir / "quarantine_wrong_history_pair_rows.csv", quarantine_wrong)
    write_csv_rows(run_dir / "quarantine_family_rows.csv", quarantine_family)
    write_csv_rows(run_dir / "active_family_summary.csv", active_family)
    write_csv_rows(run_dir / "active_fold_summary.csv", active_fold)
    write_csv_rows(run_dir / "source_lineage_rows.csv", lineage_rows)

    active_l2_values = [_finite_float(row.get("response_l2_from_opposite_branch")) for row in active_prefix]
    active_zero_l2 = int(sum(value == 0.0 for value in active_l2_values))
    active_l2_ge_threshold = int(sum(value >= float(min_response_l2) for value in active_l2_values))
    source_identity_duplicate_count = _source_identity_duplicate_count(active_source + quarantine_source)
    source_identity_metadata_preserved = _metadata_preserved(
        {
            "active_source": active_source,
            "active_prefix": active_prefix,
            "active_frames": active_frames,
            "active_interventions": active_interventions,
            "active_wrong": active_wrong,
            "quarantine_source": quarantine_source,
            "quarantine_prefix": quarantine_prefix,
            "quarantine_frames": quarantine_frames,
            "quarantine_interventions": quarantine_interventions,
            "quarantine_wrong": quarantine_wrong,
        }
    )
    quarantine_reasons_present = sorted({str(row.get("quarantine_reason", "")) for row in quarantine_family})
    result_class = (
        "materialized_source_history_objective_corpus_export_pass"
        if len(active_source) == 344
        and len(active_prefix) == 1376
        and len(active_frames) == 33024
        and len(active_interventions) == 1376
        and len(active_wrong) == 1376
        and len(active_family) == 6
        and active_zero_l2 == 0
        and active_l2_ge_threshold == 1376
        and max_fold_share <= 0.40
        and len(quarantine_source) == 22
        and len(quarantine_prefix) == 88
        and len(quarantine_frames) == 2112
        and "halfshaft_probe_silent" in quarantine_reasons_present
        and "global_friction_missing" in quarantine_reasons_present
        and source_identity_duplicate_count == 0
        and source_identity_metadata_preserved
        else "materialized_source_history_objective_corpus_export_gap_reported"
    )
    summary = {
        "run_type": "materialized_source_history_objective_corpus_export",
        "result_class": result_class,
        "materialized_run_dir": str(materialized_run_dir),
        "min_response_l2": float(min_response_l2),
        "active_source_pair_rows": int(len(active_source)),
        "active_history_prefix_rows": int(len(active_prefix)),
        "active_history_frame_rows": int(len(active_frames)),
        "active_history_intervention_rows": int(len(active_interventions)),
        "active_wrong_history_pair_rows": int(len(active_wrong)),
        "active_source_family_count": int(len(active_family)),
        "active_zero_response_l2_prefix_count": int(active_zero_l2),
        "active_response_l2_ge_0_01_count": int(active_l2_ge_threshold),
        "active_max_source_family_fold_share": float(max_fold_share),
        "quarantine_source_pair_rows": int(len(quarantine_source)),
        "quarantine_history_prefix_rows": int(len(quarantine_prefix)),
        "quarantine_history_frame_rows": int(len(quarantine_frames)),
        "quarantine_history_intervention_rows": int(len(quarantine_interventions)),
        "quarantine_wrong_history_pair_rows": int(len(quarantine_wrong)),
        "quarantine_family_rows": int(len(quarantine_family)),
        "quarantine_reasons": quarantine_reasons_present,
        "source_identity_duplicate_count": int(source_identity_duplicate_count),
        "source_identity_metadata_preserved": bool(source_identity_metadata_preserved),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "active_source_pair_rows_csv": run_dir / "active_source_pair_rows.csv",
        "active_history_prefix_rows_csv": run_dir / "active_history_prefix_rows.csv",
        "active_history_frame_rows_csv": run_dir / "active_history_frame_rows.csv",
        "active_history_intervention_rows_csv": run_dir / "active_history_intervention_rows.csv",
        "active_wrong_history_pair_rows_csv": run_dir / "active_wrong_history_pair_rows.csv",
        "quarantine_source_pair_rows_csv": run_dir / "quarantine_source_pair_rows.csv",
        "quarantine_history_prefix_rows_csv": run_dir / "quarantine_history_prefix_rows.csv",
        "quarantine_history_frame_rows_csv": run_dir / "quarantine_history_frame_rows.csv",
        "quarantine_history_intervention_rows_csv": run_dir / "quarantine_history_intervention_rows.csv",
        "quarantine_wrong_history_pair_rows_csv": run_dir / "quarantine_wrong_history_pair_rows.csv",
        "quarantine_family_rows_csv": run_dir / "quarantine_family_rows.csv",
        "active_family_summary_csv": run_dir / "active_family_summary.csv",
        "active_fold_summary_csv": run_dir / "active_fold_summary.csv",
        "source_lineage_rows_csv": run_dir / "source_lineage_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialized-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--min-response-l2", type=float, default=0.01)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="materialized_source_history_objective_corpus_export")
    summary = export_materialized_source_history_objective_corpus(
        materialized_run_dir=args.materialized_run_dir,
        run_dir=run_dir,
        min_response_l2=args.min_response_l2,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
