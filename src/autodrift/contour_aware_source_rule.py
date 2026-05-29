"""Offline contour-aware source rule over M1599 contour rows."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.temporal_active_set_anchor_sensitivity_miner import _max_share


DEFAULT_CONTOUR_ROWS = Path("runs/m1599_clean_active_set_contour_mapper/enriched_contour_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1602_contour_aware_source_rule")
CLEAN_LABEL = "history_control_separated"
DOMINATED_LABEL = "history_positive_control_dominated"
CONTROL_ONLY_LABEL = "control_only_positive"
NULL_LABEL = "history_null_all_controls_null"
PRIMARY_SELECTION_SOURCE = "clean_edge_window"
ENDPOINT_NEIGHBOR_SELECTION_SOURCE = "clean_endpoint_neighbor"
NEGATIVE_DIAGNOSTIC_SELECTION_SOURCE = "negative_diagnostic_edge"
MIXED_DIAGNOSTIC_EDGE = "capability_step_up|t5_near_boundary_warmup"
PRIMARY_SOURCE_EDGES = (
    "actuator_delay_step|capability_step_up",
    "curved_boundary_obstacle|t5_boundary_axis_retarget",
    "actuator_delay_step|t5_near_boundary_warmup",
    "capability_step_down|t5_near_boundary_warmup",
)
FORBIDDEN_GUARDRAILS = {
    "candidate_materialized": False,
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


def is_primary_rule_row(row: Mapping[str, Any]) -> bool:
    """Return whether a contour row belongs to the M1601 primary source rule."""

    return (
        str(row.get("selection_source", "")) == PRIMARY_SELECTION_SOURCE
        and str(row.get("source_edge", "")) in set(PRIMARY_SOURCE_EDGES)
    )


def diagnostic_reason(row: Mapping[str, Any]) -> str:
    """Return the diagnostic bucket for rows excluded from primary evidence."""

    if str(row.get("selection_source", "")) == ENDPOINT_NEIGHBOR_SELECTION_SOURCE:
        return "endpoint_neighbor_exclusion"
    if str(row.get("source_edge", "")) == MIXED_DIAGNOSTIC_EDGE:
        return "mixed_dominated_edge"
    if str(row.get("selection_source", "")) == NEGATIVE_DIAGNOSTIC_SELECTION_SOURCE:
        return "negative_diagnostic_edge"
    return ""


def apply_contour_aware_source_rule(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split contour rows into primary, diagnostic, and excluded buckets."""

    primary: list[dict[str, Any]] = []
    diagnostic: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if is_primary_rule_row(item):
            item["rule_bucket"] = "primary"
            item["rule_reason"] = "clean_edge_window_primary"
            primary.append(item)
            continue
        reason = diagnostic_reason(item)
        if reason:
            item["rule_bucket"] = "diagnostic"
            item["rule_reason"] = reason
            diagnostic.append(item)
        else:
            item["rule_bucket"] = "excluded"
            item["rule_reason"] = "outside_contour_rule"
            excluded.append(item)
    return primary, diagnostic, excluded


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("label", "")) for row in rows)


def _source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("source_edge", "")) for row in rows if str(row.get("source_edge", "")))


def _clean_source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return _source_edge_counts([row for row in rows if str(row.get("label", "")) == CLEAN_LABEL])


def _count_primary_leakage(rows: Sequence[Mapping[str, Any]], *, selection_source: str | None = None, source_edge: str | None = None) -> int:
    count = 0
    for row in rows:
        if selection_source is not None and str(row.get("selection_source", "")) == selection_source:
            count += 1
        elif source_edge is not None and str(row.get("source_edge", "")) == source_edge:
            count += 1
    return count


def _summary_row(group_name: str, group_key: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = _label_counts(rows)
    clean_count = labels.get(CLEAN_LABEL, 0)
    return {
        "group_name": group_name,
        "group_key": group_key,
        "directed_pair_count": len(rows),
        "clean_directed_pair_count": clean_count,
        "dominated_history_positive_directed_pair_count": labels.get(DOMINATED_LABEL, 0),
        "control_only_positive_directed_pair_count": labels.get(CONTROL_ONLY_LABEL, 0),
        "history_null_all_controls_null_directed_pair_count": labels.get(NULL_LABEL, 0),
        "clean_share": clean_count / len(rows) if rows else 0.0,
    }


def source_rule_summary(
    primary_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    excluded_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return source-rule group summaries."""

    all_rows = list(primary_rows) + list(diagnostic_rows) + list(excluded_rows)
    summaries: list[dict[str, Any]] = []
    for bucket, rows in (
        ("primary", list(primary_rows)),
        ("diagnostic", list(diagnostic_rows)),
        ("excluded", list(excluded_rows)),
    ):
        summaries.append(_summary_row("rule_bucket", bucket, rows))
    for reason in sorted({str(row.get("rule_reason", "")) for row in all_rows}):
        rows = [row for row in all_rows if str(row.get("rule_reason", "")) == reason]
        summaries.append(_summary_row("rule_reason", reason, rows))
    for edge in sorted({str(row.get("source_edge", "")) for row in all_rows if str(row.get("source_edge", ""))}):
        rows = [row for row in all_rows if str(row.get("source_edge", "")) == edge]
        summaries.append(_summary_row("source_edge", edge, rows))
    return summaries


def build_summary(
    rows: Sequence[Mapping[str, Any]],
    primary_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    excluded_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the M1602 offline source-rule summary."""

    primary_label_counts = _label_counts(primary_rows)
    diagnostic_label_counts = _label_counts(diagnostic_rows)
    primary_clean_edge_counts = _clean_source_edge_counts(primary_rows)
    endpoint_neighbor_primary_count = _count_primary_leakage(
        primary_rows,
        selection_source=ENDPOINT_NEIGHBOR_SELECTION_SOURCE,
    )
    negative_diagnostic_primary_count = _count_primary_leakage(
        primary_rows,
        selection_source=NEGATIVE_DIAGNOSTIC_SELECTION_SOURCE,
    )
    mixed_diagnostic_primary_count = _count_primary_leakage(primary_rows, source_edge=MIXED_DIAGNOSTIC_EDGE)
    diagnostic_dominated_or_control_count = diagnostic_label_counts.get(DOMINATED_LABEL, 0) + diagnostic_label_counts.get(CONTROL_ONLY_LABEL, 0)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_source_rule",
        "input_contour_row_count": len(rows),
        "primary_rule_directed_pair_count": len(primary_rows),
        "primary_source_edge_count": len(_source_edge_counts(primary_rows)),
        "primary_clean_directed_pair_count": primary_label_counts.get(CLEAN_LABEL, 0),
        "primary_clean_source_edge_count": len(primary_clean_edge_counts),
        "max_primary_clean_source_edge_share": _max_share(primary_clean_edge_counts),
        "endpoint_neighbor_primary_count": endpoint_neighbor_primary_count,
        "negative_diagnostic_primary_count": negative_diagnostic_primary_count,
        "mixed_diagnostic_primary_count": mixed_diagnostic_primary_count,
        "diagnostic_directed_pair_count": len(diagnostic_rows),
        "diagnostic_dominated_or_control_count": diagnostic_dominated_or_control_count,
        "diagnostic_endpoint_neighbor_count": sum(
            1 for row in diagnostic_rows if str(row.get("rule_reason", "")) == "endpoint_neighbor_exclusion"
        ),
        "diagnostic_negative_edge_count": sum(
            1 for row in diagnostic_rows if str(row.get("rule_reason", "")) == "negative_diagnostic_edge"
        ),
        "diagnostic_mixed_edge_count": sum(
            1 for row in diagnostic_rows if str(row.get("rule_reason", "")) == "mixed_dominated_edge"
        ),
        "excluded_directed_pair_count": len(excluded_rows),
        "primary_label_counts": dict(sorted(primary_label_counts.items())),
        "diagnostic_label_counts": dict(sorted(diagnostic_label_counts.items())),
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["input_contour_row_count"]) >= 528
        and int(summary["primary_rule_directed_pair_count"]) >= 144
        and int(summary["primary_source_edge_count"]) == 4
        and int(summary["primary_clean_directed_pair_count"]) >= 39
        and int(summary["primary_clean_source_edge_count"]) >= 4
        and float(summary["max_primary_clean_source_edge_share"]) <= 0.35
        and int(summary["endpoint_neighbor_primary_count"]) == 0
        and int(summary["negative_diagnostic_primary_count"]) == 0
        and int(summary["mixed_diagnostic_primary_count"]) == 0
        and int(summary["diagnostic_directed_pair_count"]) >= 150
        and int(summary["diagnostic_dominated_or_control_count"]) >= 50
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["replay_started"])
        and not bool(summary["history_interventions_executed"])
        and not bool(summary["candidate_materialized"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"])
    if endpoint_neighbor_primary_count or negative_diagnostic_primary_count or mixed_diagnostic_primary_count:
        null_class = "endpoint_neighbor_or_diagnostic_leakage"
    elif int(summary["primary_clean_directed_pair_count"]) < 39:
        null_class = "primary_clean_shortfall"
    elif float(summary["max_primary_clean_source_edge_share"]) > 0.35:
        null_class = "source_share_failure"
    elif int(summary["diagnostic_dominated_or_control_count"]) < 50:
        null_class = "diagnostic_missing"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_source_rule_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_contour_aware_source_rule(
    output_dir: Path | str,
    *,
    contour_rows: Path | str = DEFAULT_CONTOUR_ROWS,
) -> dict[str, Any]:
    """Run the offline contour-aware source rule."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = read_csv_rows(contour_rows)
    primary_rows, diagnostic_rows, excluded_rows = apply_contour_aware_source_rule(rows)
    summary = build_summary(rows, primary_rows, diagnostic_rows, excluded_rows)
    write_csv_rows(output / "primary_rule_rows.csv", primary_rows)
    write_csv_rows(output / "diagnostic_rule_rows.csv", diagnostic_rows)
    write_csv_rows(output / "excluded_rule_rows.csv", excluded_rows)
    write_csv_rows(output / "source_rule_summary.csv", source_rule_summary(primary_rows, diagnostic_rows, excluded_rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline contour-aware source rule.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--contour-rows", type=Path, default=DEFAULT_CONTOUR_ROWS)
    args = parser.parse_args()
    summary = run_contour_aware_source_rule(args.output_dir, contour_rows=args.contour_rows)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"primary_rule_directed_pair_count={summary['primary_rule_directed_pair_count']}")
    print(f"primary_clean_directed_pair_count={summary['primary_clean_directed_pair_count']}")
    print(f"diagnostic_directed_pair_count={summary['diagnostic_directed_pair_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
