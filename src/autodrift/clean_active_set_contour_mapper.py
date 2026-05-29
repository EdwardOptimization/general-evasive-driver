"""Offline clean active-set contour mapper over public classified rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.temporal_active_set_anchor_sensitivity_miner import _finite_float, _max_share


DEFAULT_RUN_DIR = Path("runs/m1599_clean_active_set_contour_mapper")
CLEAN_LABEL = "history_control_separated"
DOMINATED_LABEL = "history_positive_control_dominated"
CONTROL_ONLY_LABEL = "control_only_positive"
NULL_LABEL = "history_null_all_controls_null"
INVALID_LABEL = "replay_or_metric_invalid"
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


@dataclass(frozen=True)
class ContourInput:
    source_run: str
    classified_rows: Path
    intervention_rows: Path


DEFAULT_INPUTS = (
    ContourInput(
        source_run="m1588_selector",
        classified_rows=Path("runs/m1588_history_vs_control_active_set_selector/classified_directed_pair_rows.csv"),
        intervention_rows=Path("runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv"),
    ),
    ContourInput(
        source_run="m1592_clean_repair",
        classified_rows=Path("runs/m1592_clean_history_control_source_generation_repair_smoke/classified_directed_pair_rows.csv"),
        intervention_rows=Path("runs/m1592_clean_history_control_source_generation_repair_smoke/intervention_rows.csv"),
    ),
    ContourInput(
        source_run="m1595_balanced_repair",
        classified_rows=Path("runs/m1595_selector_balanced_clean_source_repair_smoke/classified_directed_pair_rows.csv"),
        intervention_rows=Path("runs/m1595_selector_balanced_clean_source_repair_smoke/intervention_rows.csv"),
    ),
)


def read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _metadata_by_pair(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """Return one metadata row per directed pair, preferring the normal variant."""

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair_id", ""))].append(row)
    result: dict[str, Mapping[str, Any]] = {}
    for pair_id, group in grouped.items():
        normal = next((row for row in group if str(row.get("variant", "")) == "normal"), None)
        result[pair_id] = normal if normal is not None else group[0]
    return result


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _direction(pair_id: str) -> str:
    if "|" not in pair_id:
        return ""
    return pair_id.rsplit("|", 1)[-1]


def _band(value: Any, *, cuts: Sequence[tuple[float, str]], default: str = "missing") -> str:
    number = _finite_float(value, default=float("nan"))
    if number != number:
        return default
    for limit, label in cuts:
        if number < limit:
            return label
    return f">={cuts[-1][0]:g}" if cuts else "finite"


def _gap_band(value: Any) -> str:
    return _band(
        value,
        cuts=(
            (0.0, "negative"),
            (1e-9, "zero"),
            (0.02, "sub_threshold"),
            (0.05, "signal_0p02_0p05"),
        ),
    )


def _hidden_specific_band(value: Any) -> str:
    return _band(
        value,
        cuts=(
            (0.0, "negative"),
            (0.01, "below_hidden_specific"),
            (0.03, "signal_0p01_0p03"),
        ),
    )


def _response_band(value: Any) -> str:
    return _band(value, cuts=((0.20, "tight"), (0.55, "tier_a_ok"), (0.75, "tier_b_ok"), (1.00, "loose")))


def _context_band(value: Any) -> str:
    return _band(value, cuts=((0.50, "tight"), (1.00, "moderate"), (4.00, "guard_ok")))


def _hidden_l2_band(value: Any) -> str:
    return _band(value, cuts=((2.00, "low"), (3.00, "moderate"), (5.00, "tier_a_signal")))


def _margin_band(value: Any) -> str:
    return _band(value, cuts=((0.0, "negative"), (0.5, "near_boundary"), (2.0, "positive_low"), (5.0, "positive_mid")))


def enrich_contour_rows(inputs: Sequence[ContourInput]) -> list[dict[str, Any]]:
    """Build enriched contour rows from classified rows and intervention metadata."""

    rows: list[dict[str, Any]] = []
    for item in inputs:
        classified = read_csv_rows(item.classified_rows)
        metadata = _metadata_by_pair(read_csv_rows(item.intervention_rows))
        for row in classified:
            pair_id = str(row.get("pair_id", ""))
            meta = metadata.get(pair_id, {})
            target_window = str(row.get("target_anchor_window", ""))
            donor_window = str(row.get("donor_anchor_window", ""))
            target_family = str(row.get("target_source_family", ""))
            donor_family = str(row.get("donor_source_family", ""))
            history_gap = _finite_float(row.get("history_max_gap"), default=float("nan"))
            control_gap = _finite_float(row.get("control_max_gap"), default=float("nan"))
            enriched = {
                "source_run": item.source_run,
                "pair_id": pair_id,
                "direction": _direction(pair_id),
                "label": str(row.get("label", "")),
                "source_edge": str(row.get("source_edge", "")),
                "target_anchor_id": str(row.get("target_anchor_id", "")),
                "donor_anchor_id": str(row.get("donor_anchor_id", "")),
                "target_source_family": target_family,
                "donor_source_family": donor_family,
                "family_pair": f"{target_family}|{donor_family}",
                "target_anchor_window": target_window,
                "donor_anchor_window": donor_window,
                "window_pair": f"{target_window}|{donor_window}",
                "target_anchor_step": str(meta.get("target_anchor_step", "")),
                "donor_anchor_step": str(meta.get("donor_anchor_step", "")),
                "same_window": _parse_bool(meta.get("same_window", target_window == donor_window)),
                "step_distance": _finite_float(meta.get("step_distance"), default=float("nan")),
                "selection_source": str(meta.get("selection_source", "")),
                "selected_pair_id": str(meta.get("selected_pair_id", "")),
                "original_pair_id": str(meta.get("original_pair_id", "")),
                "pair_response_action_l2": _finite_float(meta.get("pair_response_action_l2"), default=float("nan")),
                "pair_context_l2": _finite_float(meta.get("pair_context_l2"), default=float("nan")),
                "pair_hidden_l2": _finite_float(meta.get("pair_hidden_l2"), default=float("nan")),
                "normal_terminal_margin": _finite_float(meta.get("normal_terminal_margin"), default=float("nan")),
                "history_max_gap": history_gap,
                "control_max_gap": control_gap,
                "wrong_history_gap": _finite_float(row.get("wrong_history_gap"), default=float("nan")),
                "donor_plus_hidden_gap": _finite_float(row.get("donor_plus_hidden_gap"), default=float("nan")),
                "donor_response_action_only_gap": _finite_float(
                    row.get("donor_response_action_only_gap"),
                    default=float("nan"),
                ),
                "hidden_specific_gap": _finite_float(row.get("hidden_specific_gap"), default=float("nan")),
                "metadata_joined": bool(meta),
            }
            enriched.update(
                {
                    "history_gap_band": _gap_band(history_gap),
                    "control_gap_band": _gap_band(control_gap),
                    "hidden_specific_gap_band": _hidden_specific_band(enriched["hidden_specific_gap"]),
                    "response_action_l2_band": _response_band(enriched["pair_response_action_l2"]),
                    "context_l2_band": _context_band(enriched["pair_context_l2"]),
                    "hidden_l2_band": _hidden_l2_band(enriched["pair_hidden_l2"]),
                    "normal_margin_band": _margin_band(enriched["normal_terminal_margin"]),
                    "clean_positive": str(enriched["label"] == CLEAN_LABEL),
                    "control_dominated_positive": str(enriched["label"] == DOMINATED_LABEL),
                    "control_only_positive": str(enriched["label"] == CONTROL_ONLY_LABEL),
                }
            )
            rows.append(enriched)
    return rows


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("label", "")) for row in rows)


def _summary_row(group_name: str, group_key: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = _label_counts(rows)
    clean_count = labels.get(CLEAN_LABEL, 0)
    dominated_count = labels.get(DOMINATED_LABEL, 0)
    control_count = labels.get(CONTROL_ONLY_LABEL, 0)
    null_count = labels.get(NULL_LABEL, 0)
    invalid_count = labels.get(INVALID_LABEL, 0)
    return {
        "group_name": group_name,
        "group_key": group_key,
        "directed_pair_count": len(rows),
        "clean_directed_pair_count": clean_count,
        "dominated_history_positive_directed_pair_count": dominated_count,
        "control_only_positive_directed_pair_count": control_count,
        "history_null_all_controls_null_directed_pair_count": null_count,
        "invalid_directed_pair_count": invalid_count,
        "clean_share": 0.0 if len(rows) == 0 else clean_count / len(rows),
        "dominated_share": 0.0 if len(rows) == 0 else dominated_count / len(rows),
        "control_only_share": 0.0 if len(rows) == 0 else control_count / len(rows),
        "max_history_gap": max((_finite_float(row.get("history_max_gap"), default=0.0) for row in rows), default=0.0),
        "max_control_gap": max((_finite_float(row.get("control_max_gap"), default=0.0) for row in rows), default=0.0),
        "max_hidden_specific_gap": max(
            (_finite_float(row.get("hidden_specific_gap"), default=0.0) for row in rows),
            default=0.0,
        ),
        "metadata_joined_count": sum(1 for row in rows if _parse_bool(row.get("metadata_joined", False))),
    }


def group_summary(rows: Sequence[Mapping[str, Any]], *, group_name: str, keys: Sequence[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        group_key = "|".join(str(row.get(key, "")) for key in keys)
        grouped[group_key].append(row)
    return [_summary_row(group_name, key, grouped[key]) for key in sorted(grouped)]


def source_run_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return group_summary(rows, group_name="source_run", keys=("source_run",))


def source_edge_contour_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return group_summary(rows, group_name="source_edge", keys=("source_edge",))


def selection_source_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return group_summary(rows, group_name="source_run_selection_source", keys=("source_run", "selection_source"))


def feature_group_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups = [
        ("source_run_source_edge", ("source_run", "source_edge")),
        ("source_edge_window_pair", ("source_edge", "window_pair")),
        ("source_edge_selection_source", ("source_edge", "selection_source")),
        ("source_edge_gap_bands", ("source_edge", "history_gap_band", "control_gap_band")),
        ("source_edge_hidden_specific_band", ("source_edge", "hidden_specific_gap_band")),
        ("source_edge_response_hidden_bands", ("source_edge", "response_action_l2_band", "hidden_l2_band")),
        ("source_edge_margin_band", ("source_edge", "normal_margin_band")),
    ]
    result: list[dict[str, Any]] = []
    for name, keys in groups:
        result.extend(group_summary(rows, group_name=name, keys=keys))
    return result


def build_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = _label_counts(rows)
    clean_rows = [row for row in rows if str(row.get("label", "")) == CLEAN_LABEL]
    source_edge_counts = Counter(str(row.get("source_edge", "")) for row in rows)
    feature_groups = feature_group_summary(rows)
    metadata_joined_count = sum(1 for row in rows if _parse_bool(row.get("metadata_joined", False)))
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "clean_active_set_contour_mapper",
        "input_source_run_count": len({str(row.get("source_run", "")) for row in rows}),
        "input_directed_pair_count": len(rows),
        "enriched_directed_pair_count": len(rows),
        "metadata_joined_count": metadata_joined_count,
        "metadata_joined_fraction": 0.0 if len(rows) == 0 else metadata_joined_count / len(rows),
        "clean_directed_pair_count": labels.get(CLEAN_LABEL, 0),
        "dominated_history_positive_directed_pair_count": labels.get(DOMINATED_LABEL, 0),
        "control_only_positive_directed_pair_count": labels.get(CONTROL_ONLY_LABEL, 0),
        "history_null_all_controls_null_directed_pair_count": labels.get(NULL_LABEL, 0),
        "invalid_directed_pair_count": labels.get(INVALID_LABEL, 0),
        "source_edge_count": len(source_edge_counts),
        "feature_group_count": len(feature_groups),
        "clean_source_edge_count": len({str(row.get("source_edge", "")) for row in clean_rows}),
        "max_clean_source_edge_share": _max_share(Counter(str(row.get("source_edge", "")) for row in clean_rows)),
        "label_counts": dict(sorted(labels.items())),
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["input_source_run_count"]) >= 3
        and int(summary["input_directed_pair_count"]) >= 528
        and int(summary["enriched_directed_pair_count"]) >= 528
        and float(summary["metadata_joined_fraction"]) >= 0.90
        and int(summary["clean_directed_pair_count"]) >= 51
        and int(summary["dominated_history_positive_directed_pair_count"]) >= 70
        and int(summary["control_only_positive_directed_pair_count"]) >= 79
        and int(summary["history_null_all_controls_null_directed_pair_count"]) >= 300
        and int(summary["source_edge_count"]) >= 20
        and int(summary["feature_group_count"]) >= 40
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
    if float(summary["metadata_joined_fraction"]) < 0.90:
        null_class = "metadata_join_shortfall"
    elif int(summary["clean_directed_pair_count"]) < 51 or int(summary["dominated_history_positive_directed_pair_count"]) < 70:
        null_class = "label_coverage_shortfall"
    elif int(summary["feature_group_count"]) < 40:
        null_class = "feature_group_shortfall"
    elif int(summary["guardrail_violation_count"]) != 0:
        null_class = "guardrail_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_mapping_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_clean_active_set_contour_mapper(
    output_dir: Path | str,
    *,
    inputs: Sequence[ContourInput] = DEFAULT_INPUTS,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = enrich_contour_rows(inputs)
    summary = build_summary(rows)

    write_csv_rows(output / "enriched_contour_rows.csv", rows)
    write_csv_rows(output / "source_run_summary.csv", source_run_summary(rows))
    write_csv_rows(output / "source_edge_contour_summary.csv", source_edge_contour_summary(rows))
    write_csv_rows(output / "feature_group_summary.csv", feature_group_summary(rows))
    write_csv_rows(output / "selection_source_summary.csv", selection_source_summary(rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Map clean active-set contours offline.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = run_clean_active_set_contour_mapper(args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"input_directed_pair_count={summary['input_directed_pair_count']}")
    print(f"clean_directed_pair_count={summary['clean_directed_pair_count']}")
    print(f"metadata_joined_fraction={summary['metadata_joined_fraction']}")
    print(f"feature_group_count={summary['feature_group_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
