"""No-training task-source mapping preflight for controller-family evidence."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


DEFAULT_OUTPUT_DIR = Path("runs/m1677_controller_family_decisive_task_source_mapping_preflight")
M1538_ACCEPTED_PAIRS = Path("runs/m1538_fresh_ambiguity_history_intervention_repeat/accepted_pair_rows.csv")
M1538_SUMMARY = Path("runs/m1538_fresh_ambiguity_history_intervention_repeat/summary.json")
M1595_CLEAN_ROWS = Path("runs/m1595_selector_balanced_clean_source_repair_smoke/clean_directed_pair_rows.csv")
M1595_SUMMARY = Path("runs/m1595_selector_balanced_clean_source_repair_smoke/summary.json")
M1615_POSITIVE_ROWS = Path("runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv")
M1615_SUMMARY = Path("runs/m1615_contour_aware_candidate_corpus/summary.json")
M1599_SOURCE_EDGE_SUMMARY = Path("runs/m1599_clean_active_set_contour_mapper/source_edge_contour_summary.csv")
M1599_SUMMARY = Path("runs/m1599_clean_active_set_contour_mapper/summary.json")

FORBIDDEN_MAPPING_KEY_FRAGMENTS = (
    "hidden_tensor",
    "action_tensor",
    "preferred_action",
    "rejected_action",
    "action_target",
    "actor_label",
)
TERMINAL_SOURCE_TOKENS = ("t5_", "boundary", "obstacle", "late_reveal")


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def infer_task_family(source_families: list[str], explicit: str | None = None) -> str:
    if explicit in {"T4", "T5"}:
        return explicit
    if any(any(token in family for token in TERMINAL_SOURCE_TOKENS) for family in source_families):
        return "T5"
    return "T4"


def source_edge_from_families(source_families: list[str], explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if len(source_families) >= 2:
        return "|".join(source_families[:2])
    if source_families:
        return source_families[0]
    return "unknown"


def seed_namespace_from_identifier(identifier: str) -> str:
    if not identifier:
        return "unknown"
    parts = identifier.split("|")
    if len(parts) >= 2 and parts[1].isdigit():
        return parts[1]
    first = parts[0]
    tokens = first.split("-")
    if len(tokens) >= 2 and tokens[0] in {"calib", "fresh"}:
        return "-".join(tokens[:2])
    return first[:48]


def window_tags_from_row(row: dict[str, str]) -> list[str]:
    tags: list[str] = []
    for key in ("target_anchor_window", "donor_anchor_window"):
        value = row.get(key, "")
        if value:
            tags.append(value)
    selection = row.get("selection_source", "")
    if selection:
        tags.append(f"selection:{selection}")
    rule_bucket = row.get("rule_bucket", "")
    if rule_bucket:
        tags.append(f"rule:{rule_bucket}")
    return sorted(set(tags))


def m1538_mapping_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for row in rows:
        families = [row["left_source_family"], row["right_source_family"]]
        mapped.append(
            {
                "mapping_id": f"m1538::{row['pair_id']}",
                "metadata_source": str(M1538_ACCEPTED_PAIRS),
                "metadata_source_role": "public_measured_intervention_candidate",
                "mapping_status": "mappable_metadata_only",
                "mapping_risk": "public_diagnostic_not_private_holdout",
                "task_family": infer_task_family(families, row.get("task_family")),
                "source_family_left": families[0],
                "source_family_right": families[1],
                "source_edge": source_edge_from_families(families),
                "seed_namespaces": sorted(
                    {
                        seed_namespace_from_identifier(row.get("left_trace_id", "")),
                        seed_namespace_from_identifier(row.get("right_trace_id", "")),
                    }
                ),
                "window_tags": [],
                "allowed_controller_profiles": list(EXPECTED_PROFILE_NAMES),
                "required_controls": [
                    "L1_one_step",
                    "L2_current_tiled",
                    "L3_reset_control_corrected",
                ],
                "safe_for_direct_benchmark_without_regeneration": False,
            }
        )
    return mapped


def clean_pair_mapping_rows(
    rows: list[dict[str, str]],
    *,
    metadata_source: Path,
    metadata_source_role: str,
    diagnostic_only: bool,
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for row in rows:
        families = [row["target_source_family"], row["donor_source_family"]]
        mapped.append(
            {
                "mapping_id": f"{metadata_source.parent.name}::{row['pair_id']}",
                "metadata_source": str(metadata_source),
                "metadata_source_role": metadata_source_role,
                "mapping_status": "diagnostic_only_metadata" if diagnostic_only else "mappable_metadata_only",
                "mapping_risk": (
                    "public_l3_proof_package_do_not_use_hidden_or_action_targets"
                    if diagnostic_only
                    else "public_diagnostic_not_private_holdout"
                ),
                "task_family": infer_task_family(families),
                "source_family_left": families[0],
                "source_family_right": families[1],
                "source_edge": source_edge_from_families(families, row.get("source_edge")),
                "seed_namespaces": sorted(
                    {
                        seed_namespace_from_identifier(row.get("target_anchor_id", "")),
                        seed_namespace_from_identifier(row.get("donor_anchor_id", "")),
                    }
                ),
                "window_tags": window_tags_from_row(row),
                "allowed_controller_profiles": list(EXPECTED_PROFILE_NAMES),
                "required_controls": [
                    "L1_one_step",
                    "L2_current_tiled",
                    "L3_reset_control_corrected",
                ],
                "safe_for_direct_benchmark_without_regeneration": False,
            }
        )
    return mapped


def aggregate_source_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for row in rows:
        if row.get("group_name") != "source_edge":
            continue
        families = row["group_key"].split("|")
        mapped.append(
            {
                "mapping_id": f"m1599_aggregate::{row['group_key']}",
                "metadata_source": str(M1599_SOURCE_EDGE_SUMMARY),
                "metadata_source_role": "aggregate_contour_inventory",
                "mapping_status": "aggregate_inventory_only",
                "mapping_risk": "not_a_task_instance",
                "task_family": infer_task_family(families),
                "source_family_left": families[0] if families else "unknown",
                "source_family_right": families[1] if len(families) > 1 else "unknown",
                "source_edge": row["group_key"],
                "seed_namespaces": [],
                "window_tags": [],
                "allowed_controller_profiles": list(EXPECTED_PROFILE_NAMES),
                "required_controls": [
                    "L1_one_step",
                    "L2_current_tiled",
                    "L3_reset_control_corrected",
                ],
                "safe_for_direct_benchmark_without_regeneration": False,
            }
        )
    return mapped


def source_diversity_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    task_rows = [row for row in rows if row["mapping_status"] != "aggregate_inventory_only"]
    family_counter: Counter[str] = Counter()
    edge_counter: Counter[str] = Counter()
    task_counter: Counter[str] = Counter()
    window_counter: Counter[str] = Counter()
    seed_counter: Counter[str] = Counter()
    source_role_counter: Counter[str] = Counter()

    for row in task_rows:
        for key in ("source_family_left", "source_family_right"):
            family = str(row.get(key) or "unknown")
            family_counter[family] += 1
        edge_counter[str(row["source_edge"])] += 1
        task_counter[str(row["task_family"])] += 1
        source_role_counter[str(row["metadata_source_role"])] += 1
        for tag in row.get("window_tags", []):
            window_counter[str(tag)] += 1
        for seed in row.get("seed_namespaces", []):
            seed_counter[str(seed)] += 1

    endpoint_total = sum(family_counter.values())
    max_family_share = (max(family_counter.values()) / endpoint_total) if endpoint_total else 0.0
    row_total = len(task_rows)
    max_source_role_share = (max(source_role_counter.values()) / row_total) if row_total else 0.0
    thresholds = {
        "candidate_source_family_count_min": 5,
        "candidate_task_family_count_min": 2,
        "candidate_edge_count_min": 8,
        "candidate_window_count_min": 4,
        "max_single_source_family_share_max": 0.35,
    }
    values = {
        "candidate_row_count": row_total,
        "candidate_source_family_count": len(family_counter),
        "candidate_task_family_count": len(task_counter),
        "candidate_edge_count": len(edge_counter),
        "candidate_window_count": len(window_counter),
        "candidate_seed_namespace_count": len(seed_counter),
        "max_single_source_family_share": max_family_share,
        "max_single_metadata_source_role_share": max_source_role_share,
    }
    threshold_passes = {
        "candidate_source_family_count": values["candidate_source_family_count"]
        >= thresholds["candidate_source_family_count_min"],
        "candidate_task_family_count": values["candidate_task_family_count"]
        >= thresholds["candidate_task_family_count_min"],
        "candidate_edge_count": values["candidate_edge_count"] >= thresholds["candidate_edge_count_min"],
        "candidate_window_count": values["candidate_window_count"] >= thresholds["candidate_window_count_min"],
        "max_single_source_family_share": values["max_single_source_family_share"]
        <= thresholds["max_single_source_family_share_max"],
    }
    return {
        **values,
        "source_family_counts": dict(sorted(family_counter.items())),
        "source_edge_counts": dict(sorted(edge_counter.items())),
        "task_family_counts": dict(sorted(task_counter.items())),
        "window_tag_counts": dict(sorted(window_counter.items())),
        "seed_namespace_counts": dict(sorted(seed_counter.items())),
        "metadata_source_role_counts": dict(sorted(source_role_counter.items())),
        "implementation_thresholds": thresholds,
        "implementation_threshold_passes": threshold_passes,
        "implementation_thresholds_pass": all(threshold_passes.values()),
    }


def mapping_key_violations(rows: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for row in rows:
        for key in row:
            lowered = key.lower()
            if any(fragment in lowered for fragment in FORBIDDEN_MAPPING_KEY_FRAGMENTS):
                violations.append(f"{row.get('mapping_id', 'unknown')}::{key}")
    return violations


def build_task_source_mapping(rows: list[dict[str, Any]]) -> dict[str, Any]:
    diversity = source_diversity_counts(rows)
    key_violations = mapping_key_violations(rows)
    return {
        "protocol_name": "controller_family_decisive_task_source_mapping_preflight",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "metadata preflight only; no controller ranking or self-ID claim",
        "m1615_use_policy": "diagnostic_metadata_only_no_hidden_tensor_or_action_targets",
        "control_profile_requirements": [
            "L1_one_step",
            "L2_normal_windows",
            "matched_L2_current_tiled_windows",
            "L3_online_gru",
            "L3_reset_control_corrected",
        ],
        "source_diversity": diversity,
        "key_violation_count": len(key_violations),
        "key_violations": key_violations,
        "candidate_rows": rows,
    }


def run_mapping_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    m1538_pairs_path: Path | str = M1538_ACCEPTED_PAIRS,
    m1595_clean_rows_path: Path | str = M1595_CLEAN_ROWS,
    m1615_positive_rows_path: Path | str = M1615_POSITIVE_ROWS,
    m1599_source_edge_summary_path: Path | str = M1599_SOURCE_EDGE_SUMMARY,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    rows.extend(m1538_mapping_rows(read_csv_rows(m1538_pairs_path)))
    rows.extend(
        clean_pair_mapping_rows(
            read_csv_rows(m1595_clean_rows_path),
            metadata_source=Path(m1595_clean_rows_path),
            metadata_source_role="clean_history_control_public_pairs",
            diagnostic_only=False,
        )
    )
    rows.extend(
        clean_pair_mapping_rows(
            read_csv_rows(m1615_positive_rows_path),
            metadata_source=Path(m1615_positive_rows_path),
            metadata_source_role="m1615_public_diagnostic_positive_package",
            diagnostic_only=True,
        )
    )
    rows.extend(aggregate_source_rows(read_csv_rows(m1599_source_edge_summary_path)))

    mapping = build_task_source_mapping(rows)
    write_json(output / "task_source_mapping.json", mapping)

    guardrail_flags = {
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "environment_rollout_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "m1615_hidden_tensor_or_action_target_used": bool(mapping["key_violation_count"]),
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    diversity = mapping["source_diversity"]
    passes = (
        diversity["candidate_row_count"] > 0
        and diversity["candidate_source_family_count"] > 0
        and diversity["candidate_task_family_count"] > 0
        and guardrail_violation_count == 0
    )
    route = (
        "audit_mapping_preflight_before_task_source_generation"
        if diversity["implementation_thresholds_pass"]
        else "fresh_source_generation_design_due_to_metadata_threshold_shortfall"
    )
    summary = {
        "result_class": (
            "controller_family_decisive_task_source_mapping_preflight_pass"
            if passes
            else "controller_family_decisive_task_source_mapping_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "task_source_mapping": str(output / "task_source_mapping.json"),
        "m1615_use_policy": mapping["m1615_use_policy"],
        "candidate_row_count": diversity["candidate_row_count"],
        "candidate_source_family_count": diversity["candidate_source_family_count"],
        "candidate_task_family_count": diversity["candidate_task_family_count"],
        "candidate_edge_count": diversity["candidate_edge_count"],
        "candidate_window_count": diversity["candidate_window_count"],
        "candidate_seed_namespace_count": diversity["candidate_seed_namespace_count"],
        "max_single_source_family_share": diversity["max_single_source_family_share"],
        "implementation_thresholds_pass": diversity["implementation_thresholds_pass"],
        "implementation_threshold_passes": diversity["implementation_threshold_passes"],
        "key_violation_count": mapping["key_violation_count"],
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "passes_public_smoke_gates": passes,
        "private_holdout_used": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "environment_rollout_started": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "level3_self_id_claim_made": False,
        "next_blocker": route,
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_mapping_preflight(output_dir=args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"task_source_mapping={args.output_dir / 'task_source_mapping.json'}")
    return 0 if summary["passes_public_smoke_gates"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
