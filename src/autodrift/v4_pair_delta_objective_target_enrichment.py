"""No-training enrichment of pair-delta rows with sequence action targets."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import time
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.v4_pair_delta_corpus_dedup_resplit import closed_loop_signature
from autodrift.v4_wrong_cross_fault_history_intervention import GATE_SUMMARY_FIELDS, read_csv_rows


JOIN_KEY_FIELDS = [
    "pair_id",
    "left_candidate_id",
    "right_candidate_id",
    "left_source_group_id",
    "right_source_group_id",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "direction",
    "hold_steps",
    "epsilon_l2",
    "normal_margin",
    "sequence_margin",
]

TARGET_FIELDS = [
    "normal_first_steer",
    "normal_first_throttle",
    "normal_first_brake",
    "right_first_steer",
    "right_first_throttle",
    "right_first_brake",
    "first_override_steer",
    "first_override_throttle",
    "first_override_brake",
    "requested_delta_l2_per_step",
    "effective_delta_l2_max",
    "clip_fraction_mean",
    "first_action_l2_vs_normal",
    "prefix_l2_mean_vs_normal",
    "prefix_l2_max_vs_normal",
    "terminal_reason",
    "steps",
]

CONSISTENCY_FIELDS = [
    "effective_delta_l2_mean",
    "effective_sequence_l2",
    "clip_fraction_max",
    "severe_clip_steps",
]

ENRICHMENT_FIELDS = [
    *TARGET_FIELDS,
    "sequence_source",
    "sequence_source_path",
    "enrichment_join_key",
    "enrichment_match_count",
    "enrichment_join_status",
]

DUPLICATE_METADATA_FIELDS = [
    "dedup_signature",
    "duplicate_row_count",
    "duplicate_retarget_axes",
    "duplicate_pair_ids",
    "evidence_origin",
    "dedup_role",
    "objective_sample_weight",
]


def join_key(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(field, "")) for field in JOIN_KEY_FIELDS)


def sequence_source_name(path: Path) -> str:
    text = str(path)
    if "m867" in text:
        return "m867_sequence"
    if "m873" in text:
        return "m873_boundary_preserving_sequence"
    return path.parent.name or path.stem


def _same_targets(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    first = {field: str(rows[0].get(field, "")) for field in TARGET_FIELDS}
    return all({field: str(row.get(field, "")) for field in TARGET_FIELDS} == first for row in rows[1:])


def _required_target_fields_present(row: dict[str, Any]) -> bool:
    return all(str(row.get(field, "")) != "" for field in TARGET_FIELDS)


def build_sequence_index(sequence_paths: list[Path]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sequence_paths:
        source = sequence_source_name(path)
        for row in read_csv_rows(path):
            tagged = {
                **row,
                "sequence_source": source,
                "sequence_source_path": str(path),
            }
            by_identity[join_key(tagged)].append(tagged)
            by_signature[closed_loop_signature(tagged)].append(tagged)
    return by_identity, by_signature


def _select_sequence_match(
    row: dict[str, Any],
    by_identity: dict[str, list[dict[str, Any]]],
    by_signature: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str, int]:
    key = join_key(row)
    matches = by_identity.get(key, [])
    if len(matches) == 1:
        return matches[0], "identity_unique", 1
    if len(matches) > 1:
        if _same_targets(matches):
            return matches[0], "identity_duplicate_identical_targets", len(matches)
        return None, "identity_ambiguous", len(matches)

    signature = str(row.get("dedup_signature", "")) or closed_loop_signature(row)
    fallback = by_signature.get(signature, [])
    if len(fallback) == 1:
        return fallback[0], "signature_unique", 1
    if len(fallback) > 1:
        if _same_targets(fallback):
            return fallback[0], "signature_duplicate_identical_targets", len(fallback)
        return None, "signature_ambiguous", len(fallback)
    return None, "missing", 0


def enrich_rows(
    rows: list[dict[str, Any]],
    by_identity: dict[str, list[dict[str, Any]]],
    by_signature: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched: list[dict[str, Any]] = []
    join_rows: list[dict[str, Any]] = []
    for row in rows:
        match, status, count = _select_sequence_match(row, by_identity, by_signature)
        output = dict(row)
        if match is not None:
            for field in TARGET_FIELDS:
                output[field] = match.get(field, "")
            for field in CONSISTENCY_FIELDS:
                if field not in output or str(output.get(field, "")) == "":
                    output[field] = match.get(field, "")
            output["sequence_source"] = match.get("sequence_source", "")
            output["sequence_source_path"] = match.get("sequence_source_path", "")
        output["enrichment_join_key"] = join_key(row)
        output["enrichment_match_count"] = count
        output["enrichment_join_status"] = status
        enriched.append(output)
        join_rows.append(
            {
                "dedup_signature": row.get("dedup_signature", ""),
                "pair_id": row.get("pair_id", ""),
                "evidence_origin": row.get("evidence_origin", ""),
                "split": row.get("split", ""),
                "enrichment_join_key": output["enrichment_join_key"],
                "enrichment_join_status": status,
                "enrichment_match_count": count,
                "sequence_source": output.get("sequence_source", ""),
                "sequence_source_path": output.get("sequence_source_path", ""),
                "target_action_fields_present": _required_target_fields_present(output),
            }
        )
    return enriched, join_rows


def _has_fields(rows: list[dict[str, Any]], fields: list[str]) -> bool:
    return bool(rows) and all(all(field in row for field in fields) for row in rows)


def _count_new(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if str(row.get("evidence_origin", "")) == "new_m873")


def _all_split(rows: list[dict[str, Any]], split: str) -> bool:
    return bool(rows) and all(str(row.get("split", "")) == split for row in rows)


def _output_fields(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    for field in [*TARGET_FIELDS, *ENRICHMENT_FIELDS]:
        if field not in fields:
            fields.append(field)
    return fields


def classify_target_enrichment(
    *,
    dedup_rows_enriched: int,
    missing_join_count: int,
    ambiguous_join_count: int,
    target_action_fields_present: bool,
    split_labels_preserved: bool,
    duplicate_metadata_preserved: bool,
    caveat_78055_recorded: bool,
) -> str:
    if int(dedup_rows_enriched) <= 0:
        return "v4_pair_delta_objective_target_enrichment_empty"
    if int(missing_join_count) > 0 or int(ambiguous_join_count) > 0:
        return "v4_pair_delta_objective_target_enrichment_join_failed"
    if not bool(target_action_fields_present) or not bool(split_labels_preserved) or not bool(duplicate_metadata_preserved):
        return "v4_pair_delta_objective_target_enrichment_artifact_invalid"
    if not bool(caveat_78055_recorded):
        return "v4_pair_delta_objective_target_enrichment_artifact_invalid"
    return "v4_pair_delta_objective_target_enrichment_pass"


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "dedup_rows_enriched",
            "value": summary["dedup_rows_enriched"],
            "threshold": ">0",
            "passed": int(summary["dedup_rows_enriched"]) > 0,
            "notes": "dedup rows must be enriched",
        },
        {
            "gate_name": "missing_join_count",
            "value": summary["missing_join_count"],
            "threshold": "0",
            "passed": int(summary["missing_join_count"]) == 0,
            "notes": "every row needs a sequence target source",
        },
        {
            "gate_name": "ambiguous_join_count",
            "value": summary["ambiguous_join_count"],
            "threshold": "0",
            "passed": int(summary["ambiguous_join_count"]) == 0,
            "notes": "target actions must not be ambiguous",
        },
        {
            "gate_name": "target_action_fields_present",
            "value": summary["target_action_fields_present"],
            "threshold": "true",
            "passed": bool(summary["target_action_fields_present"]),
            "notes": "normal/right/override first actions restored",
        },
        {
            "gate_name": "split_labels_preserved",
            "value": summary["split_labels_preserved"],
            "threshold": "true",
            "passed": bool(summary["split_labels_preserved"]),
            "notes": "split rows keep their purpose labels",
        },
        {
            "gate_name": "duplicate_metadata_preserved",
            "value": summary["duplicate_metadata_preserved"],
            "threshold": "true",
            "passed": bool(summary["duplicate_metadata_preserved"]),
            "notes": "dedup metadata retained",
        },
        {
            "gate_name": "caveat_78055_recorded",
            "value": summary["caveat_78055_recorded"],
            "threshold": "true",
            "passed": bool(summary["caveat_78055_recorded"]),
            "notes": "78055 remains a visible caveat",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M880 cannot train or promote",
        },
    ]


def run_target_enrichment(
    *,
    dedup_rows_path: Path,
    objective_train_rows_path: Path,
    objective_eval_rows_path: Path,
    source_holdout_rows_path: Path,
    new_signature_holdout_rows_path: Path,
    sequence_rows_paths: list[Path],
    run_dir: Path,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    by_identity, by_signature = build_sequence_index(sequence_rows_paths)

    dedup_rows = read_csv_rows(dedup_rows_path)
    objective_train = read_csv_rows(objective_train_rows_path)
    objective_eval = read_csv_rows(objective_eval_rows_path)
    source_holdout = read_csv_rows(source_holdout_rows_path)
    new_signature_holdout = read_csv_rows(new_signature_holdout_rows_path)

    enriched_dedup, dedup_join_rows = enrich_rows(dedup_rows, by_identity, by_signature)
    enriched_train, train_join_rows = enrich_rows(objective_train, by_identity, by_signature)
    enriched_eval, eval_join_rows = enrich_rows(objective_eval, by_identity, by_signature)
    enriched_source_holdout, source_join_rows = enrich_rows(source_holdout, by_identity, by_signature)
    enriched_new_signature_holdout, signature_join_rows = enrich_rows(new_signature_holdout, by_identity, by_signature)
    all_enriched = [
        *enriched_dedup,
        *enriched_train,
        *enriched_eval,
        *enriched_source_holdout,
        *enriched_new_signature_holdout,
    ]
    all_join_rows = [*dedup_join_rows, *train_join_rows, *eval_join_rows, *source_join_rows, *signature_join_rows]
    missing_join_count = sum(1 for row in all_join_rows if row["enrichment_join_status"] == "missing")
    ambiguous_join_count = sum(1 for row in all_join_rows if "ambiguous" in str(row["enrichment_join_status"]))
    target_action_fields_present = all(_required_target_fields_present(row) for row in all_enriched)
    split_labels_preserved = (
        _all_split(enriched_train, "objective_train_public")
        and _all_split(enriched_eval, "objective_eval_public")
        and _all_split(enriched_source_holdout, "source_holdout_public")
        and _all_split(enriched_new_signature_holdout, "new_signature_holdout_public")
    )
    duplicate_metadata_preserved = _has_fields(enriched_dedup, DUPLICATE_METADATA_FIELDS)
    new_source_holdout_available = _count_new(enriched_source_holdout) > 0
    caveat_78055_recorded = "78055" not in {str(row.get("left_seed", "")) for row in enriched_dedup if str(row.get("evidence_origin", "")) == "new_m873"}
    result_class = classify_target_enrichment(
        dedup_rows_enriched=len(enriched_dedup),
        missing_join_count=missing_join_count,
        ambiguous_join_count=ambiguous_join_count,
        target_action_fields_present=target_action_fields_present,
        split_labels_preserved=split_labels_preserved,
        duplicate_metadata_preserved=duplicate_metadata_preserved,
        caveat_78055_recorded=caveat_78055_recorded,
    )

    fields = _output_fields(all_enriched)
    write_csv_rows(run_dir / "enriched_dedup_pair_delta_rows.csv", enriched_dedup, fieldnames=fields)
    write_csv_rows(run_dir / "enriched_objective_train_public_rows.csv", enriched_train, fieldnames=fields)
    write_csv_rows(run_dir / "enriched_objective_eval_public_rows.csv", enriched_eval, fieldnames=fields)
    write_csv_rows(run_dir / "enriched_source_holdout_public_rows.csv", enriched_source_holdout, fieldnames=fields)
    write_csv_rows(run_dir / "enriched_new_signature_holdout_public_rows.csv", enriched_new_signature_holdout, fieldnames=fields)
    write_csv_rows(run_dir / "join_summary.csv", all_join_rows)

    summary = {
        "run_type": "v4_pair_delta_objective_target_enrichment",
        "dedup_rows_path": dedup_rows_path,
        "objective_train_rows_path": objective_train_rows_path,
        "objective_eval_rows_path": objective_eval_rows_path,
        "source_holdout_rows_path": source_holdout_rows_path,
        "new_signature_holdout_rows_path": new_signature_holdout_rows_path,
        "sequence_rows_paths": sequence_rows_paths,
        "dedup_rows_enriched": len(enriched_dedup),
        "objective_train_rows_enriched": len(enriched_train),
        "objective_eval_rows_enriched": len(enriched_eval),
        "source_holdout_rows_enriched": len(enriched_source_holdout),
        "new_signature_holdout_rows_enriched": len(enriched_new_signature_holdout),
        "objective_train_new_rows_enriched": _count_new(enriched_train),
        "objective_eval_new_rows_enriched": _count_new(enriched_eval),
        "source_holdout_new_rows_enriched": _count_new(enriched_source_holdout),
        "new_signature_holdout_new_rows_enriched": _count_new(enriched_new_signature_holdout),
        "join_rows": len(all_join_rows),
        "missing_join_count": missing_join_count,
        "ambiguous_join_count": ambiguous_join_count,
        "target_action_fields_present": target_action_fields_present,
        "split_labels_preserved": split_labels_preserved,
        "duplicate_metadata_preserved": duplicate_metadata_preserved,
        "new_source_holdout_available": new_source_holdout_available,
        "caveat_78055_recorded": caveat_78055_recorded,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "enriched_dedup_pair_delta_rows_csv": run_dir / "enriched_dedup_pair_delta_rows.csv",
        "enriched_objective_train_public_rows_csv": run_dir / "enriched_objective_train_public_rows.csv",
        "enriched_objective_eval_public_rows_csv": run_dir / "enriched_objective_eval_public_rows.csv",
        "enriched_source_holdout_public_rows_csv": run_dir / "enriched_source_holdout_public_rows.csv",
        "enriched_new_signature_holdout_public_rows_csv": run_dir / "enriched_new_signature_holdout_public_rows.csv",
        "join_summary_csv": run_dir / "join_summary.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 pair-delta objective target enrichment.")
    parser.add_argument("--dedup-rows", type=Path, required=True)
    parser.add_argument("--objective-train-rows", type=Path, required=True)
    parser.add_argument("--objective-eval-rows", type=Path, required=True)
    parser.add_argument("--source-holdout-rows", type=Path, required=True)
    parser.add_argument("--new-signature-holdout-rows", type=Path, required=True)
    parser.add_argument("--sequence-rows", type=Path, action="append", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_target_enrichment(
        dedup_rows_path=args.dedup_rows,
        objective_train_rows_path=args.objective_train_rows,
        objective_eval_rows_path=args.objective_eval_rows,
        source_holdout_rows_path=args.source_holdout_rows,
        new_signature_holdout_rows_path=args.new_signature_holdout_rows,
        sequence_rows_paths=list(args.sequence_rows),
        run_dir=args.run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
