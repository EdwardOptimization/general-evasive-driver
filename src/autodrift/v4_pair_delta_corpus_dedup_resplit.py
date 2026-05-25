"""No-training pair-delta corpus deduplication and resplitting."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import time
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.v4_pair_delta_focused_source_balanced_mining import split_source_aware
from autodrift.v4_wrong_cross_fault_history_intervention import GATE_SUMMARY_FIELDS, _as_int, read_csv_rows


DEDUP_EXTRA_FIELDS = [
    "dedup_signature",
    "dedup_group_index",
    "duplicate_row_count",
    "duplicate_retarget_axes",
    "duplicate_pair_ids",
    "evidence_origin",
    "dedup_role",
    "objective_sample_weight",
]
SPLIT_EXTRA_FIELDS = [*DEDUP_EXTRA_FIELDS, "split"]


def evidence_origin(row: dict[str, Any]) -> str:
    return "new_m873" if str(row.get("coverage_source", "")) == "m873_boundary_preserving" else "existing_m867_or_m870"


def _rounded(value: Any, digits: int = 9) -> str:
    numeric = _finite_float(value)
    if numeric != numeric:
        return ""
    return f"{numeric:.{digits}f}"


def closed_loop_signature(row: dict[str, Any]) -> str:
    """Return a signature that ignores diagnostic retarget-axis labels."""

    parts = [
        str(row.get("left_source_group_id", "")),
        str(row.get("right_source_group_id", "")),
        str(row.get("left_step", "")),
        str(row.get("right_step", "")),
        str(row.get("left_seed", "")),
        str(row.get("right_seed", "")),
        str(row.get("left_fault_family", "")),
        str(row.get("right_fault_family", "")),
        _rounded(row.get("retarget_target_body_x")),
        _rounded(row.get("retarget_target_body_y")),
        _rounded(row.get("retarget_target_half_width")),
        str(row.get("direction", "")),
        str(row.get("hold_steps", "")),
        _rounded(row.get("epsilon_l2")),
        _rounded(row.get("normal_margin")),
        _rounded(row.get("sequence_margin")),
    ]
    return "|".join(parts)


def _canonical_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            0 if evidence_origin(row) == "new_m873" else 1,
            -_finite_float(row.get("abs_margin_delta"), default=0.0),
            _as_int(row.get("pair_id")),
            str(row.get("retarget_axis", "")),
        ),
    )[0]


def deduplicate_pair_delta_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[closed_loop_signature(row)].append(row)

    deduped: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    for index, (signature, group) in enumerate(sorted(grouped.items(), key=lambda item: item[0])):
        canonical = dict(_canonical_row(group))
        axes = sorted({str(row.get("retarget_axis", "")) for row in group if str(row.get("retarget_axis", ""))})
        pair_ids = sorted({str(row.get("pair_id", "")) for row in group if str(row.get("pair_id", ""))})
        origin = "new_m873" if any(evidence_origin(row) == "new_m873" for row in group) else "existing_m867_or_m870"
        canonical.update(
            {
                "dedup_signature": signature,
                "dedup_group_index": index,
                "duplicate_row_count": len(group),
                "duplicate_retarget_axes": ";".join(axes),
                "duplicate_pair_ids": ";".join(pair_ids),
                "evidence_origin": origin,
                "dedup_role": "canonical",
                "objective_sample_weight": 1.0,
            }
        )
        deduped.append(canonical)
        group_rows.append(
            {
                "dedup_signature": signature,
                "dedup_group_index": index,
                "duplicate_row_count": len(group),
                "duplicate_retarget_axes": ";".join(axes),
                "duplicate_pair_ids": ";".join(pair_ids),
                "evidence_origin": origin,
                "left_seed": canonical.get("left_seed", ""),
                "left_source_group_id": canonical.get("left_source_group_id", ""),
                "right_source_group_id": canonical.get("right_source_group_id", ""),
                "direction": canonical.get("direction", ""),
                "hold_steps": canonical.get("hold_steps", ""),
                "epsilon_l2": canonical.get("epsilon_l2", ""),
                "normal_margin": canonical.get("normal_margin", ""),
                "sequence_margin": canonical.get("sequence_margin", ""),
                "abs_margin_delta": canonical.get("abs_margin_delta", ""),
            }
        )
    return deduped, group_rows


def _tag_split(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [{**row, "split": split} for row in rows]


def split_deduped_corpus(deduped_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Create purpose-specific public splits from deduped rows."""

    new_rows = [row for row in deduped_rows if str(row.get("evidence_origin", "")) == "new_m873"]
    existing_rows = [row for row in deduped_rows if str(row.get("evidence_origin", "")) != "new_m873"]
    existing_train, existing_eval, existing_holdout = split_source_aware(existing_rows)
    existing_train = [{key: value for key, value in row.items() if key != "split"} for row in existing_train]
    existing_eval = [{key: value for key, value in row.items() if key != "split"} for row in existing_eval]
    existing_holdout = [{key: value for key, value in row.items() if key != "split"} for row in existing_holdout]

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in new_rows:
        by_source[str(row.get("left_source_group_id", ""))].append(row)
    source_groups = sorted(by_source, key=lambda group: (-len(by_source[group]), group))
    train_new: list[dict[str, Any]] = []
    eval_new: list[dict[str, Any]] = []
    signature_holdout: list[dict[str, Any]] = []
    if source_groups:
        train_source = source_groups[0]
        train_source_rows = sorted(by_source[train_source], key=lambda row: (str(row.get("direction", "")), _as_int(row.get("hold_steps")), _finite_float(row.get("epsilon_l2"))))
        train_holdout_count = max(1, len(train_source_rows) // 5) if len(train_source_rows) > 1 else 0
        signature_holdout.extend(train_source_rows[-train_holdout_count:] if train_holdout_count else [])
        train_new.extend(train_source_rows[:-train_holdout_count] if train_holdout_count else train_source_rows)
    if len(source_groups) >= 2:
        eval_source = source_groups[1]
        eval_source_rows = sorted(by_source[eval_source], key=lambda row: (str(row.get("direction", "")), _as_int(row.get("hold_steps")), _finite_float(row.get("epsilon_l2"))))
        eval_holdout_count = 1 if len(eval_source_rows) > 1 else 0
        signature_holdout.extend(eval_source_rows[-eval_holdout_count:] if eval_holdout_count else [])
        eval_new.extend(eval_source_rows[:-eval_holdout_count] if eval_holdout_count else eval_source_rows)
    for source in source_groups[2:]:
        signature_holdout.extend(by_source[source])

    return {
        "objective_train_public": _tag_split([*existing_train, *train_new], "objective_train_public"),
        "objective_eval_public": _tag_split([*existing_eval, *eval_new], "objective_eval_public"),
        "source_holdout_public": _tag_split(existing_holdout, "source_holdout_public"),
        "new_signature_holdout_public": _tag_split(signature_holdout, "new_signature_holdout_public"),
    }


def _count(rows: list[dict[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows})


def _max_share(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values(), default=0) / float(len(rows))


def classify_dedup_resplit(
    *,
    dedup_rows: int,
    new_dedup_rows: int,
    new_dedup_unique_left_source_group_count: int,
    new_duplicate_factor_after: float,
    objective_train_rows: int,
    objective_eval_rows: int,
    source_holdout_rows: int,
    objective_train_new_rows: int,
    objective_eval_new_rows: int,
    new_signature_holdout_rows: int,
    caveat_78055_recorded: bool,
    max_new_duplicate_factor_after: float,
    min_new_dedup_rows: int,
    min_new_source_groups: int,
) -> str:
    if int(dedup_rows) <= 0:
        return "v4_pair_delta_corpus_dedup_resplit_too_sparse"
    if int(new_dedup_rows) < int(min_new_dedup_rows) or int(new_dedup_unique_left_source_group_count) < int(min_new_source_groups):
        return "v4_pair_delta_corpus_dedup_resplit_too_sparse"
    if float(new_duplicate_factor_after) > float(max_new_duplicate_factor_after):
        return "v4_pair_delta_corpus_dedup_resplit_split_limited"
    if (
        int(objective_train_rows) <= 0
        or int(objective_eval_rows) <= 0
        or int(source_holdout_rows) <= 0
        or int(objective_train_new_rows) <= 0
        or int(objective_eval_new_rows) <= 0
        or int(new_signature_holdout_rows) <= 0
        or not bool(caveat_78055_recorded)
    ):
        return "v4_pair_delta_corpus_dedup_resplit_split_limited"
    return "v4_pair_delta_corpus_dedup_resplit_pass"


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "dedup_rows",
            "value": summary["dedup_rows"],
            "threshold": ">0",
            "passed": int(summary["dedup_rows"]) > 0,
            "notes": "deduplicated corpus must not be empty",
        },
        {
            "gate_name": "new_dedup_rows",
            "value": summary["new_dedup_rows"],
            "threshold": summary["min_new_dedup_rows"],
            "passed": int(summary["new_dedup_rows"]) >= int(summary["min_new_dedup_rows"]),
            "notes": "new M873 evidence retained after dedup",
        },
        {
            "gate_name": "new_duplicate_factor_after",
            "value": summary["new_duplicate_factor_after"],
            "threshold": summary["max_new_duplicate_factor_after"],
            "passed": float(summary["new_duplicate_factor_after"]) <= float(summary["max_new_duplicate_factor_after"]),
            "notes": "axis-label duplicates collapsed",
        },
        {
            "gate_name": "objective_train_new_rows",
            "value": summary["objective_train_new_rows"],
            "threshold": ">0",
            "passed": int(summary["objective_train_new_rows"]) > 0,
            "notes": "train split carries new evidence",
        },
        {
            "gate_name": "objective_eval_new_rows",
            "value": summary["objective_eval_new_rows"],
            "threshold": ">0",
            "passed": int(summary["objective_eval_new_rows"]) > 0,
            "notes": "eval split carries new evidence",
        },
        {
            "gate_name": "new_signature_holdout_rows",
            "value": summary["new_signature_holdout_rows"],
            "threshold": ">0",
            "passed": int(summary["new_signature_holdout_rows"]) > 0,
            "notes": "within-source signature holdout for new evidence",
        },
        {
            "gate_name": "caveat_78055_recorded",
            "value": summary["caveat_78055_recorded"],
            "threshold": "true",
            "passed": bool(summary["caveat_78055_recorded"]),
            "notes": "78055 still lacks new accepted pair-delta rows",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M877 cannot train or promote",
        },
    ]


def run_dedup_resplit(
    *,
    accepted_pair_delta_rows_path: Path,
    new_accepted_pair_delta_rows_path: Path,
    run_dir: Path,
    min_new_dedup_rows: int,
    min_new_source_groups: int,
    max_new_duplicate_factor_after: float,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = read_csv_rows(accepted_pair_delta_rows_path)
    new_rows_raw = read_csv_rows(new_accepted_pair_delta_rows_path)
    deduped, duplicate_groups = deduplicate_pair_delta_rows(rows)
    splits = split_deduped_corpus(deduped)
    new_dedup_rows = [row for row in deduped if str(row.get("evidence_origin", "")) == "new_m873"]
    existing_dedup_rows = [row for row in deduped if str(row.get("evidence_origin", "")) != "new_m873"]
    objective_train = splits["objective_train_public"]
    objective_eval = splits["objective_eval_public"]
    source_holdout = splits["source_holdout_public"]
    new_signature_holdout = splits["new_signature_holdout_public"]
    objective_train_new = [row for row in objective_train if str(row.get("evidence_origin", "")) == "new_m873"]
    objective_eval_new = [row for row in objective_eval if str(row.get("evidence_origin", "")) == "new_m873"]
    source_holdout_new = [row for row in source_holdout if str(row.get("evidence_origin", "")) == "new_m873"]
    new_duplicate_factor_before = len(new_rows_raw) / float(max(len(new_dedup_rows), 1))
    new_duplicate_factor_after = len(new_dedup_rows) / float(max(len({str(row.get("dedup_signature", "")) for row in new_dedup_rows}), 1))
    caveat_78055_recorded = "78055" not in {str(row.get("left_seed", "")) for row in new_dedup_rows}
    new_source_holdout_available = bool(source_holdout_new)
    result_class = classify_dedup_resplit(
        dedup_rows=len(deduped),
        new_dedup_rows=len(new_dedup_rows),
        new_dedup_unique_left_source_group_count=_count(new_dedup_rows, "left_source_group_id"),
        new_duplicate_factor_after=new_duplicate_factor_after,
        objective_train_rows=len(objective_train),
        objective_eval_rows=len(objective_eval),
        source_holdout_rows=len(source_holdout),
        objective_train_new_rows=len(objective_train_new),
        objective_eval_new_rows=len(objective_eval_new),
        new_signature_holdout_rows=len(new_signature_holdout),
        caveat_78055_recorded=caveat_78055_recorded,
        max_new_duplicate_factor_after=float(max_new_duplicate_factor_after),
        min_new_dedup_rows=int(min_new_dedup_rows),
        min_new_source_groups=int(min_new_source_groups),
    )
    split_summary = {
        "objective_train": {
            "rows": len(objective_train),
            "new_rows": len(objective_train_new),
            "unique_left_seed_count": _count(objective_train, "left_seed"),
            "unique_left_source_group_count": _count(objective_train, "left_source_group_id"),
        },
        "objective_eval": {
            "rows": len(objective_eval),
            "new_rows": len(objective_eval_new),
            "unique_left_seed_count": _count(objective_eval, "left_seed"),
            "unique_left_source_group_count": _count(objective_eval, "left_source_group_id"),
        },
        "source_holdout": {
            "rows": len(source_holdout),
            "new_rows": len(source_holdout_new),
            "unique_left_seed_count": _count(source_holdout, "left_seed"),
            "unique_left_source_group_count": _count(source_holdout, "left_source_group_id"),
        },
        "new_signature_holdout": {
            "rows": len(new_signature_holdout),
            "unique_left_seed_count": _count(new_signature_holdout, "left_seed"),
            "unique_left_source_group_count": _count(new_signature_holdout, "left_source_group_id"),
        },
    }
    output_fields = [*list(deduped[0].keys())] if deduped else []
    for field in DEDUP_EXTRA_FIELDS:
        if field not in output_fields:
            output_fields.append(field)
    split_fields = [*output_fields]
    if "split" not in split_fields:
        split_fields.append("split")
    write_csv_rows(run_dir / "dedup_pair_delta_rows.csv", deduped, fieldnames=output_fields)
    write_csv_rows(run_dir / "duplicate_group_rows.csv", duplicate_groups)
    write_csv_rows(run_dir / "objective_train_public_rows.csv", objective_train, fieldnames=split_fields)
    write_csv_rows(run_dir / "objective_eval_public_rows.csv", objective_eval, fieldnames=split_fields)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", source_holdout, fieldnames=split_fields)
    write_csv_rows(run_dir / "new_signature_holdout_public_rows.csv", new_signature_holdout, fieldnames=split_fields)
    write_json(run_dir / "split_summary.json", split_summary)
    summary = {
        "run_type": "v4_pair_delta_corpus_dedup_resplit",
        "accepted_pair_delta_rows": accepted_pair_delta_rows_path,
        "new_accepted_pair_delta_rows": new_accepted_pair_delta_rows_path,
        "raw_rows": len(rows),
        "raw_new_rows": len(new_rows_raw),
        "dedup_rows": len(deduped),
        "existing_dedup_rows": len(existing_dedup_rows),
        "new_dedup_rows": len(new_dedup_rows),
        "new_dedup_unique_left_seed_count": _count(new_dedup_rows, "left_seed"),
        "new_dedup_unique_left_source_group_count": _count(new_dedup_rows, "left_source_group_id"),
        "new_duplicate_factor_before": new_duplicate_factor_before,
        "new_duplicate_factor_after": new_duplicate_factor_after,
        "max_new_duplicate_factor_after": float(max_new_duplicate_factor_after),
        "min_new_dedup_rows": int(min_new_dedup_rows),
        "min_new_source_groups": int(min_new_source_groups),
        "duplicate_group_rows": len(duplicate_groups),
        "objective_train_rows": len(objective_train),
        "objective_eval_rows": len(objective_eval),
        "source_holdout_rows": len(source_holdout),
        "new_signature_holdout_rows": len(new_signature_holdout),
        "objective_train_new_rows": len(objective_train_new),
        "objective_eval_new_rows": len(objective_eval_new),
        "source_holdout_new_rows": len(source_holdout_new),
        "new_source_holdout_available": new_source_holdout_available,
        "new_train_eval_source_overlap": bool(
            {str(row.get("left_source_group_id", "")) for row in objective_train_new}
            & {str(row.get("left_source_group_id", "")) for row in objective_eval_new}
        ),
        "new_max_left_seed_dominance": _max_share(new_dedup_rows, "left_seed"),
        "caveat_78055_recorded": caveat_78055_recorded,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "dedup_pair_delta_rows_csv": run_dir / "dedup_pair_delta_rows.csv",
        "duplicate_group_rows_csv": run_dir / "duplicate_group_rows.csv",
        "objective_train_public_rows_csv": run_dir / "objective_train_public_rows.csv",
        "objective_eval_public_rows_csv": run_dir / "objective_eval_public_rows.csv",
        "source_holdout_public_rows_csv": run_dir / "source_holdout_public_rows.csv",
        "new_signature_holdout_public_rows_csv": run_dir / "new_signature_holdout_public_rows.csv",
        "split_summary_json": run_dir / "split_summary.json",
        "gate_summary_csv": run_dir / "gate_summary.csv",
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 pair-delta corpus dedup/resplit.")
    parser.add_argument("--accepted-pair-delta-rows", type=Path, required=True)
    parser.add_argument("--new-accepted-pair-delta-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--min-new-dedup-rows", type=int, default=10)
    parser.add_argument("--min-new-source-groups", type=int, default=2)
    parser.add_argument("--max-new-duplicate-factor-after", type=float, default=1.25)
    args = parser.parse_args()
    summary = run_dedup_resplit(
        accepted_pair_delta_rows_path=args.accepted_pair_delta_rows,
        new_accepted_pair_delta_rows_path=args.new_accepted_pair_delta_rows,
        run_dir=args.run_dir,
        min_new_dedup_rows=int(args.min_new_dedup_rows),
        min_new_source_groups=int(args.min_new_source_groups),
        max_new_duplicate_factor_after=float(args.max_new_duplicate_factor_after),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
