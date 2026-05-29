"""Selector-only history-vs-control active-set classification."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.temporal_active_set_anchor_sensitivity_miner import _finite_float, _max_share


DEFAULT_INPUT_ROWS = Path("runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1588_history_vs_control_active_set_selector")
HISTORY_VARIANTS = {"wrong_history_hidden", "donor_response_action_plus_hidden"}
CONTROL_VARIANTS = {
    "donor_response_action_only",
    "reset_hidden",
    "zero_current_response",
    "zero_action_history",
    "zero_all_response",
}
REQUIRED_VARIANTS = {"normal"} | HISTORY_VARIANTS | CONTROL_VARIANTS
HISTORY_GAP_THRESHOLD = 0.02
CONTROL_RATIO_THRESHOLD = 0.75
HIDDEN_SPECIFIC_GAP_THRESHOLD = 0.01
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


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _variant_map(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("variant", "")): row for row in rows}


def _gap(row: Mapping[str, Any] | None) -> float:
    if row is None:
        return float("nan")
    return _finite_float(row.get("terminal_margin_gap_from_normal"), default=float("nan"))


def _success_drop(row: Mapping[str, Any] | None) -> bool:
    return bool(row is not None and _parse_bool(row.get("success_drop_from_normal", False)))


def _collision_increase(row: Mapping[str, Any] | None) -> bool:
    return bool(row is not None and _parse_bool(row.get("collision_increase_from_normal", False)))


def _finite_required(values: Sequence[float]) -> bool:
    return all(value == value and value not in (float("inf"), float("-inf")) for value in values)


def classify_directed_pair(pair_id: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Classify one directed pair into clean, dominated, null, or invalid."""

    variants = _variant_map(rows)
    missing = sorted(REQUIRED_VARIANTS - set(variants))
    wrong = variants.get("wrong_history_hidden")
    donor_plus = variants.get("donor_response_action_plus_hidden")
    donor_only = variants.get("donor_response_action_only")
    history_gaps = [_gap(variants.get(variant)) for variant in HISTORY_VARIANTS]
    control_gaps = [_gap(variants.get(variant)) for variant in CONTROL_VARIANTS]
    wrong_history_gap = _gap(wrong)
    donor_plus_hidden_gap = _gap(donor_plus)
    donor_response_action_only_gap = _gap(donor_only)
    history_max_gap = max(history_gaps) if history_gaps else float("nan")
    control_max_gap = max(control_gaps) if control_gaps else float("nan")
    hidden_specific_gap = donor_plus_hidden_gap - donor_response_action_only_gap
    history_success_drop = any(_success_drop(variants.get(variant)) for variant in HISTORY_VARIANTS)
    control_success_drop = any(_success_drop(variants.get(variant)) for variant in CONTROL_VARIANTS)
    history_collision_increase = any(_collision_increase(variants.get(variant)) for variant in HISTORY_VARIANTS)
    control_collision_increase = any(_collision_increase(variants.get(variant)) for variant in CONTROL_VARIANTS)
    finite = _finite_required([history_max_gap, control_max_gap, wrong_history_gap, donor_plus_hidden_gap, donor_response_action_only_gap])
    first = rows[0] if rows else {}
    if missing or not finite:
        label = "replay_or_metric_invalid"
    else:
        history_positive = history_max_gap >= HISTORY_GAP_THRESHOLD or history_success_drop
        control_positive = control_max_gap >= HISTORY_GAP_THRESHOLD or control_success_drop
        clean = (
            history_positive
            and control_max_gap < CONTROL_RATIO_THRESHOLD * max(history_max_gap, 1e-9)
            and (
                hidden_specific_gap >= HIDDEN_SPECIFIC_GAP_THRESHOLD
                or wrong_history_gap >= HISTORY_GAP_THRESHOLD
                or (history_success_drop and not control_success_drop)
            )
        )
        if clean:
            label = "history_control_separated"
        elif history_positive:
            label = "history_positive_control_dominated"
        elif control_positive:
            label = "control_only_positive"
        else:
            label = "history_null_all_controls_null"
    return {
        "pair_id": pair_id,
        "label": label,
        "missing_variants": ";".join(missing),
        "source_edge": str(first.get("source_edge", "")),
        "target_anchor_id": str(first.get("target_anchor_id", "")),
        "donor_anchor_id": str(first.get("donor_anchor_id", "")),
        "target_source_family": str(first.get("target_source_family", "")),
        "donor_source_family": str(first.get("donor_source_family", "")),
        "target_anchor_window": str(first.get("target_anchor_window", "")),
        "donor_anchor_window": str(first.get("donor_anchor_window", "")),
        "history_max_gap": history_max_gap,
        "control_max_gap": control_max_gap,
        "wrong_history_gap": wrong_history_gap,
        "donor_plus_hidden_gap": donor_plus_hidden_gap,
        "donor_response_action_only_gap": donor_response_action_only_gap,
        "hidden_specific_gap": hidden_specific_gap,
        "history_success_drop": history_success_drop,
        "control_success_drop": control_success_drop,
        "history_collision_increase": history_collision_increase,
        "control_collision_increase": control_collision_increase,
    }


def classify_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair_id", ""))].append(row)
    return [classify_directed_pair(pair_id, grouped[pair_id]) for pair_id in sorted(grouped)]


def _endpoint_families(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(str(row.get("target_source_family", "")))
        result.add(str(row.get("donor_source_family", "")))
    return {item for item in result if item}


def group_summary(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        label_counts = Counter(str(row.get("label", "")) for row in group)
        result.append(
            {
                key: value,
                "directed_pair_count": len(group),
                "clean_directed_pair_count": label_counts.get("history_control_separated", 0),
                "dominated_history_positive_directed_pair_count": label_counts.get("history_positive_control_dominated", 0),
                "control_only_positive_directed_pair_count": label_counts.get("control_only_positive", 0),
                "history_null_all_controls_null_directed_pair_count": label_counts.get("history_null_all_controls_null", 0),
                "invalid_directed_pair_count": label_counts.get("replay_or_metric_invalid", 0),
                "max_history_gap": max((_finite_float(row.get("history_max_gap"), default=0.0) for row in group), default=0.0),
                "max_control_gap": max((_finite_float(row.get("control_max_gap"), default=0.0) for row in group), default=0.0),
            }
        )
    return result


def label_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    label_counts = Counter(str(row.get("label", "")) for row in rows)
    return [{"label": label, "directed_pair_count": count} for label, count in sorted(label_counts.items())]


def build_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(str(row.get("label", "")) for row in rows)
    clean_rows = [row for row in rows if row.get("label") == "history_control_separated"]
    clean_edge_counts = Counter(str(row.get("source_edge", "")) for row in clean_rows)
    null_or_control = label_counts.get("control_only_positive", 0) + label_counts.get("history_null_all_controls_null", 0)
    invalid_count = label_counts.get("replay_or_metric_invalid", 0)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "history_vs_control_active_set_selector",
        "input_directed_pair_count": len(rows),
        "classified_directed_pair_count": len(rows),
        "required_variant_coverage_complete": invalid_count == 0,
        "clean_directed_pair_count": len(clean_rows),
        "clean_source_edge_count": len(clean_edge_counts),
        "clean_endpoint_source_family_count": len(_endpoint_families(clean_rows)),
        "max_clean_source_edge_share": _max_share(clean_edge_counts),
        "dominated_history_positive_directed_pair_count": label_counts.get("history_positive_control_dominated", 0),
        "control_only_positive_directed_pair_count": label_counts.get("control_only_positive", 0),
        "history_null_all_controls_null_directed_pair_count": label_counts.get("history_null_all_controls_null", 0),
        "null_or_control_only_directed_pair_count": null_or_control,
        "invalid_directed_pair_count": invalid_count,
        "label_counts": dict(sorted(label_counts.items())),
        "max_history_gap": max((_finite_float(row.get("history_max_gap"), default=0.0) for row in rows), default=0.0),
        "max_control_gap": max((_finite_float(row.get("control_max_gap"), default=0.0) for row in rows), default=0.0),
        "history_interventions_executed": False,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["input_directed_pair_count"]) >= 144
        and bool(summary["required_variant_coverage_complete"])
        and int(summary["classified_directed_pair_count"]) >= 144
        and int(summary["clean_directed_pair_count"]) >= 7
        and int(summary["clean_source_edge_count"]) >= 4
        and int(summary["dominated_history_positive_directed_pair_count"]) >= 16
        and int(summary["null_or_control_only_directed_pair_count"]) >= 100
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
        and not bool(summary["candidate_materialized"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["training_corpus_exported"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["clean_directed_pair_count"]) >= 8
        and int(summary["clean_source_edge_count"]) >= 4
        and int(summary["clean_endpoint_source_family_count"]) >= 4
        and float(summary["max_clean_source_edge_share"]) <= 0.40
    )
    if invalid_count:
        null_class = "metric_invalid"
    elif not clean_rows:
        null_class = "clean_surface_absent"
    elif float(summary["max_clean_source_edge_share"]) > 0.40:
        null_class = "source_singleton_clean_surface"
    elif bool(summary["passes_evidence_quality_targets"]):
        null_class = "selector_public_and_evidence_pass"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "selector_public_pass_clean_shortfall"
    else:
        null_class = "selector_public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_selector(input_rows: Path | str, output_dir: Path | str) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    classified = classify_rows(read_csv_rows(input_rows))
    clean = [row for row in classified if row.get("label") == "history_control_separated"]
    summary = build_summary(classified)
    write_csv_rows(output / "classified_directed_pair_rows.csv", classified)
    write_csv_rows(output / "clean_directed_pair_rows.csv", clean)
    write_csv_rows(output / "source_edge_summary.csv", group_summary(classified, "source_edge"))
    write_csv_rows(output / "source_family_summary.csv", group_summary(classified, "target_source_family"))
    write_csv_rows(output / "label_summary.csv", label_summary(classified))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify history-vs-control active-set rows.")
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = run_selector(args.input_rows, args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"clean_directed_pair_count={summary['clean_directed_pair_count']}")
    print(f"clean_source_edge_count={summary['clean_source_edge_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
