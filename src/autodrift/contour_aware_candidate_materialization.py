"""Offline materialization of contour-aware public-pass candidate rows."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.temporal_active_set_anchor_sensitivity_miner import _max_share


DEFAULT_PRIMARY_CLASSIFIED_ROWS = Path("runs/m1609_diagnostic_complete_bounded_replay/primary_classified_rows.csv")
DEFAULT_DIAGNOSTIC_CLASSIFIED_ROWS = Path("runs/m1609_diagnostic_complete_bounded_replay/diagnostic_classified_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1612_contour_aware_candidate_materialization")
CLEAN_LABEL = "history_control_separated"
DOMINATED_LABEL = "history_positive_control_dominated"
CONTROL_ONLY_LABEL = "control_only_positive"
NULL_LABEL = "history_null_all_controls_null"
PRIMARY_BUCKET = "primary"
PRIMARY_REASON = "clean_edge_window_primary"
DIAGNOSTIC_BUCKET = "diagnostic"
FORBIDDEN_GUARDRAILS = {
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def _truthy_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def is_candidate_row(row: Mapping[str, Any]) -> bool:
    """Return whether a classified M1609 row is eligible for candidate artifacts."""

    return (
        str(row.get("rule_bucket", "")) == PRIMARY_BUCKET
        and str(row.get("rule_reason", "")) == PRIMARY_REASON
        and str(row.get("label", "")) == CLEAN_LABEL
        and str(row.get("m1602_label", "")) == CLEAN_LABEL
        and not _truthy_text(row.get("missing_variants", ""))
        and _truthy_text(row.get("pair_id", ""))
    )


def select_candidate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Select candidate rows from M1609 primary classified rows."""

    return [dict(row) for row in rows if is_candidate_row(row)]


def select_diagnostic_guardrail_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Carry all diagnostic rows as guardrails, without label-based selection."""

    return [dict(row) for row in rows]


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("label", "")) for row in rows)


def _source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("source_edge", "")) for row in rows if str(row.get("source_edge", "")))


def _reason_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("rule_reason", "")) for row in rows if str(row.get("rule_reason", "")))


def _summary_rows(counter: Counter[str], *, key_name: str, count_name: str) -> list[dict[str, Any]]:
    total = sum(counter.values())
    rows: list[dict[str, Any]] = []
    for key, count in sorted(counter.items()):
        rows.append({key_name: key, count_name: count, "share": count / total if total else 0.0})
    return rows


def diagnostic_guardrail_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Summarize diagnostic guardrails by reason."""

    output: list[dict[str, Any]] = []
    for reason in sorted(_reason_counts(rows)):
        group = [row for row in rows if str(row.get("rule_reason", "")) == reason]
        labels = _label_counts(group)
        output.append(
            {
                "rule_reason": reason,
                "directed_pair_count": len(group),
                "clean_directed_pair_count": labels.get(CLEAN_LABEL, 0),
                "dominated_history_positive_directed_pair_count": labels.get(DOMINATED_LABEL, 0),
                "control_only_positive_directed_pair_count": labels.get(CONTROL_ONLY_LABEL, 0),
                "history_null_all_controls_null_directed_pair_count": labels.get(NULL_LABEL, 0),
            }
        )
    return output


def build_summary(
    primary_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    diagnostic_guardrail_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build M1612 materialization summary."""

    candidate_ids = [str(row.get("pair_id", "")) for row in candidate_rows]
    diagnostic_ids = {str(row.get("pair_id", "")) for row in diagnostic_guardrail_rows}
    candidate_labels = _label_counts(candidate_rows)
    diagnostic_labels = _label_counts(diagnostic_guardrail_rows)
    candidate_source_edge_counts = _source_edge_counts(candidate_rows)
    diagnostic_reason_counts = _reason_counts(diagnostic_guardrail_rows)
    candidate_missing_variants_count = sum(1 for row in candidate_rows if _truthy_text(row.get("missing_variants", "")))
    diagnostic_rows_enter_candidate_rows = any(pair_id in diagnostic_ids for pair_id in candidate_ids)
    candidate_rows_from_primary_only = all(
        str(row.get("rule_bucket", "")) == PRIMARY_BUCKET and str(row.get("rule_reason", "")) == PRIMARY_REASON
        for row in candidate_rows
    )
    candidate_rows_all_clean = all(
        str(row.get("label", "")) == CLEAN_LABEL and str(row.get("m1602_label", "")) == CLEAN_LABEL
        for row in candidate_rows
    )
    diagnostic_clean_share = (
        diagnostic_labels.get(CLEAN_LABEL, 0) / len(diagnostic_guardrail_rows)
        if diagnostic_guardrail_rows
        else 0.0
    )
    diagnostic_dominated_or_control_count = diagnostic_labels.get(DOMINATED_LABEL, 0) + diagnostic_labels.get(CONTROL_ONLY_LABEL, 0)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_candidate_materialization",
        "primary_input_directed_pair_count": len(primary_rows),
        "diagnostic_input_directed_pair_count": len(diagnostic_rows),
        "candidate_directed_pair_count": len(candidate_rows),
        "candidate_source_edge_count": len(candidate_source_edge_counts),
        "max_candidate_source_edge_share": _max_share(candidate_source_edge_counts),
        "candidate_rows_from_primary_only": bool(candidate_rows_from_primary_only),
        "candidate_rows_all_clean": bool(candidate_rows_all_clean),
        "candidate_rows_missing_variants_count": candidate_missing_variants_count,
        "candidate_pair_ids_unique": len(candidate_ids) == len(set(candidate_ids)),
        "diagnostic_guardrail_directed_pair_count": len(diagnostic_guardrail_rows),
        "diagnostic_reason_count": len(diagnostic_reason_counts),
        "diagnostic_dominated_or_control_count": diagnostic_dominated_or_control_count,
        "diagnostic_clean_share": diagnostic_clean_share,
        "diagnostic_rows_enter_candidate_rows": bool(diagnostic_rows_enter_candidate_rows),
        "candidate_label_counts": dict(sorted(candidate_labels.items())),
        "diagnostic_label_counts": dict(sorted(diagnostic_labels.items())),
        "candidate_materialized": True,
        "candidate_materialization_only": True,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["candidate_directed_pair_count"]) == 39
        and int(summary["candidate_source_edge_count"]) == 4
        and float(summary["max_candidate_source_edge_share"]) <= 0.35
        and bool(summary["candidate_rows_from_primary_only"])
        and bool(summary["candidate_rows_all_clean"])
        and int(summary["candidate_rows_missing_variants_count"]) == 0
        and bool(summary["candidate_pair_ids_unique"])
        and int(summary["diagnostic_guardrail_directed_pair_count"]) == 232
        and int(summary["diagnostic_reason_count"]) == 3
        and int(summary["diagnostic_dominated_or_control_count"]) >= 75
        and float(summary["diagnostic_clean_share"]) <= 0.02
        and not bool(summary["diagnostic_rows_enter_candidate_rows"])
        and not bool(summary["training_corpus_exported"])
        and bool(summary["candidate_materialized"])
        and bool(summary["candidate_materialization_only"])
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"])
    if int(summary["candidate_directed_pair_count"]) != 39:
        null_class = "candidate_count_mismatch"
    elif not bool(summary["candidate_rows_all_clean"]):
        null_class = "non_clean_candidate_leakage"
    elif bool(summary["diagnostic_rows_enter_candidate_rows"]):
        null_class = "diagnostic_candidate_leakage"
    elif float(summary["max_candidate_source_edge_share"]) > 0.35:
        null_class = "candidate_source_share_failure"
    elif int(summary["diagnostic_dominated_or_control_count"]) < 75:
        null_class = "diagnostic_guardrail_failure"
    elif bool(summary["training_corpus_exported"]):
        null_class = "training_corpus_export_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_candidate_materialization_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_contour_aware_candidate_materialization(
    output_dir: Path | str,
    *,
    primary_classified_rows: Path | str = DEFAULT_PRIMARY_CLASSIFIED_ROWS,
    diagnostic_classified_rows: Path | str = DEFAULT_DIAGNOSTIC_CLASSIFIED_ROWS,
) -> dict[str, Any]:
    """Run offline candidate materialization."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    primary_rows = read_csv_rows(primary_classified_rows)
    diagnostic_rows = read_csv_rows(diagnostic_classified_rows)
    candidate_rows = select_candidate_rows(primary_rows)
    diagnostic_guardrail_rows = select_diagnostic_guardrail_rows(diagnostic_rows)
    summary = build_summary(primary_rows, diagnostic_rows, candidate_rows, diagnostic_guardrail_rows)
    write_csv_rows(output / "candidate_rows.csv", candidate_rows)
    write_csv_rows(
        output / "candidate_source_edge_summary.csv",
        _summary_rows(_source_edge_counts(candidate_rows), key_name="source_edge", count_name="candidate_directed_pair_count"),
    )
    write_csv_rows(output / "diagnostic_guardrail_rows.csv", diagnostic_guardrail_rows)
    write_csv_rows(output / "diagnostic_guardrail_summary.csv", diagnostic_guardrail_summary(diagnostic_guardrail_rows))
    guardrail_rows = [{"guardrail": "candidate_materialized", "violated": False, "value": True}]
    guardrail_rows.append({"guardrail": "candidate_materialization_only", "violated": False, "value": True})
    guardrail_rows.extend({"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items())
    write_csv_rows(output / "guardrail_summary.csv", guardrail_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize contour-aware candidate artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--primary-classified-rows", type=Path, default=DEFAULT_PRIMARY_CLASSIFIED_ROWS)
    parser.add_argument("--diagnostic-classified-rows", type=Path, default=DEFAULT_DIAGNOSTIC_CLASSIFIED_ROWS)
    args = parser.parse_args()
    summary = run_contour_aware_candidate_materialization(
        args.output_dir,
        primary_classified_rows=args.primary_classified_rows,
        diagnostic_classified_rows=args.diagnostic_classified_rows,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"candidate_directed_pair_count={summary['candidate_directed_pair_count']}")
    print(f"diagnostic_guardrail_directed_pair_count={summary['diagnostic_guardrail_directed_pair_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
