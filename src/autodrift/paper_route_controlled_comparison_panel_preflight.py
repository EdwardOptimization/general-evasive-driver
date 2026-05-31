"""No-rollout preflight for the paper-route controlled comparison panel."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.bounded_comparison_candidate_qualification import read_csv_rows
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


DEFAULT_TASK_SPECS = Path("runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json")
DEFAULT_M2020_CANDIDATE_SUPPORT = Path("runs/m2020_multi_slice_bounded_diagnostic_comparison/candidate_support.csv")
DEFAULT_M1683_SUMMARY = Path("runs/m1683_controller_family_bounded_rollout_protocol_preflight/summary.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2023_paper_route_controlled_comparison_panel_preflight")
DEFAULT_NEXT_BLOCKER = "m2024-paper-route-controlled-comparison-panel-preflight-result-audit"

TASK_FAMILIES = (
    "T1_reactive_active_safety",
    "T2_same_current_different_older_history",
    "T3_active_diagnostic_warmup",
    "T4_variable_diagnostic_delay",
    "T5_source_rich_extreme_dynamics",
)
MIN_CLEAN_SOURCES_PER_FAMILY = 12
TARGET_CLEAN_SOURCES_PER_FAMILY = 24
MAX_SINGLE_SOURCE_KIND_SHARE = 0.35

SOURCE_FIELDNAMES = [
    "panel_source_id",
    "panel_task_family",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_reference",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "panel_source_id",
    "panel_task_family",
    "profile_name",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
]
COVERAGE_FIELDNAMES = [
    "panel_task_family",
    "source_count",
    "source_kind_count",
    "max_single_source_kind_share",
    "min_clean_sources_target",
    "target_clean_sources_target",
    "min_clean_sources_pass",
    "target_clean_sources_pass",
    "source_kind_share_pass",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _source_kind_from_edge(edge: str, fallback: str) -> str:
    edge_lower = edge.lower()
    labels: list[str] = []
    if "actuator_delay" in edge_lower:
        labels.append("actuator_delay_proxy")
    if "capability_step" in edge_lower:
        labels.append("capability_step_proxy")
    if "boundary" in edge_lower:
        labels.append("terminal_boundary_proxy")
    if "warmup" in edge_lower:
        labels.append("warmup_proxy")
    if "friction" in edge_lower:
        labels.append("friction_proxy")
    if labels:
        return "+".join(labels)
    return fallback


def _append_unique(source_rows: list[dict[str, Any]], seen: set[tuple[str, str]], row: dict[str, Any]) -> None:
    key = (str(row["panel_source_id"]), str(row["panel_task_family"]))
    if key in seen:
        return
    seen.add(key)
    source_rows.append(row)


def build_sources(
    *,
    task_specs: list[Mapping[str, Any]],
    candidate_support_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    source_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for index, row in enumerate(candidate_support_rows):
        source_edge = "|".join(
            [
                str(row.get("source_role_semantics", "")),
                str(row.get("parent_feasibility_tier_id", "")),
                str(row.get("normalized_surface_variant", "")),
                str(row.get("sampled_obstacle_label", "")),
            ]
        )
        _append_unique(
            source_rows,
            seen,
            {
                "panel_source_id": f"m2020-active-safety-{index:04d}",
                "panel_task_family": "T1_reactive_active_safety",
                "source_origin": "m2020_multi_slice_bounded_diagnostic",
                "source_kind": str(row.get("repair_source_kind", "m2020_unknown")),
                "source_edge": source_edge,
                "window_tag": "m2020_public_diagnostic",
                "source_role_semantics": row.get("source_role_semantics", ""),
                "parent_feasibility_tier_id": row.get("parent_feasibility_tier_id", ""),
                "normalized_surface_variant": row.get("normalized_surface_variant", ""),
                "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
                "source_reference": row.get("candidate_key", f"m2020_row_{index}"),
            },
        )

    for spec in task_specs:
        source_id = str(spec.get("task_source_id", ""))
        source_edge = str(spec.get("source_edge", ""))
        window_tag = str(spec.get("window_tag", ""))
        source_kind = _source_kind_from_edge(source_edge, fallback=str(spec.get("task_family", "m1680_unknown")))
        base = {
            "panel_source_id": source_id,
            "source_origin": "m1680_controller_family_task_source",
            "source_kind": source_kind,
            "source_edge": source_edge,
            "window_tag": window_tag,
            "source_role_semantics": ";".join(str(v) for v in spec.get("source_metadata_roles", [])),
            "parent_feasibility_tier_id": str(spec.get("task_family", "")),
            "normalized_surface_variant": str(spec.get("source_family_left", "")),
            "sampled_obstacle_label": str(spec.get("source_family_right", "")),
            "source_reference": str(spec.get("mapping_lineage", {}).get("source_mapping_id", source_id)),
        }
        task_family = str(spec.get("task_family", ""))
        edge_lower = source_edge.lower()
        if task_family == "T4":
            _append_unique(
                source_rows,
                seen,
                {**base, "panel_task_family": "T2_same_current_different_older_history"},
            )
        if "warmup" in edge_lower:
            _append_unique(source_rows, seen, {**base, "panel_task_family": "T3_active_diagnostic_warmup"})
        if window_tag and window_tag != "mapping_window_unspecified":
            _append_unique(source_rows, seen, {**base, "panel_task_family": "T4_variable_diagnostic_delay"})
        if task_family == "T5" or any(token in edge_lower for token in ("capability_step", "actuator_delay", "friction")):
            _append_unique(source_rows, seen, {**base, "panel_task_family": "T5_source_rich_extreme_dynamics"})

    return sorted(source_rows, key=lambda row: (row["panel_task_family"], row["panel_source_id"]))


def build_workload(source_rows: Iterable[Mapping[str, Any]], profiles: Iterable[str]) -> list[dict[str, Any]]:
    workload: list[dict[str, Any]] = []
    for source in source_rows:
        for profile in profiles:
            workload.append(
                {
                    "workload_id": f"{source['panel_source_id']}::{source['panel_task_family']}::{profile}",
                    "panel_source_id": source["panel_source_id"],
                    "panel_task_family": source["panel_task_family"],
                    "profile_name": profile,
                    "source_origin": source["source_origin"],
                    "source_kind": source["source_kind"],
                    "source_edge": source["source_edge"],
                    "window_tag": source["window_tag"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return workload


def build_coverage(source_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in source_rows:
        grouped[str(row["panel_task_family"])].append(row)

    coverage: list[dict[str, Any]] = []
    for family in TASK_FAMILIES:
        rows = grouped.get(family, [])
        source_kinds = Counter(str(row["source_kind"]) for row in rows)
        max_share = max(source_kinds.values(), default=0) / max(1, len(rows))
        coverage.append(
            {
                "panel_task_family": family,
                "source_count": len(rows),
                "source_kind_count": len(source_kinds),
                "max_single_source_kind_share": max_share,
                "min_clean_sources_target": MIN_CLEAN_SOURCES_PER_FAMILY,
                "target_clean_sources_target": TARGET_CLEAN_SOURCES_PER_FAMILY,
                "min_clean_sources_pass": len(rows) >= MIN_CLEAN_SOURCES_PER_FAMILY,
                "target_clean_sources_pass": len(rows) >= TARGET_CLEAN_SOURCES_PER_FAMILY,
                "source_kind_share_pass": bool(rows) and max_share <= MAX_SINGLE_SOURCE_KIND_SHARE,
            }
        )
    return coverage


def _bools(rows: list[Mapping[str, Any]], key: str) -> list[bool]:
    return [str(row.get(key, "")).lower() == "true" for row in rows]


def run_panel_preflight(
    *,
    task_specs_path: Path = DEFAULT_TASK_SPECS,
    candidate_support_path: Path = DEFAULT_M2020_CANDIDATE_SUPPORT,
    m1683_summary_path: Path = DEFAULT_M1683_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_specs_payload = read_json(task_specs_path)
    task_specs = list(task_specs_payload.get("task_source_specs", []))
    candidate_support_rows = read_csv_rows(candidate_support_path)
    m1683_summary = read_json(m1683_summary_path)

    profiles = list(EXPECTED_PROFILE_NAMES)
    source_rows = build_sources(task_specs=task_specs, candidate_support_rows=candidate_support_rows)
    workload_rows = build_workload(source_rows, profiles)
    coverage_rows = build_coverage(source_rows)

    all_families_present = all(int(row["source_count"]) > 0 for row in coverage_rows)
    min_family_coverage_pass = all(_bools(coverage_rows, "min_clean_sources_pass"))
    target_family_coverage_pass = all(_bools(coverage_rows, "target_clean_sources_pass"))
    source_kind_share_pass = all(_bools(coverage_rows, "source_kind_share_pass"))
    profile_count_pass = len(profiles) == len(EXPECTED_PROFILE_NAMES)
    m1683_guardrail_pass = int(m1683_summary.get("guardrail_violation_count", 1)) == 0
    panel_ready_for_routing_smoke = bool(
        all_families_present and min_family_coverage_pass and profile_count_pass and m1683_guardrail_pass
    )

    coverage_passes = {
        "profile_count": profile_count_pass,
        "all_task_families_present": all_families_present,
        "min_family_source_count": min_family_coverage_pass,
        "target_family_source_count": target_family_coverage_pass,
        "source_kind_share": source_kind_share_pass,
        "m1683_guardrail": m1683_guardrail_pass,
    }
    claim_rows = [
        {
            "claim": "controlled_comparison_panel_preflight_completed",
            "admissible": True,
            "reason": "M2023 writes no-rollout protocol workload coverage and claim-boundary artifacts",
        },
        {
            "claim": "panel_ready_for_routing_smoke",
            "admissible": panel_ready_for_routing_smoke,
            "reason": "requires all families present, minimum source counts, profile coverage, and clean historical guardrails",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2023 does not execute the panel or use private holdout",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2023 is no-rollout preflight and does not compare outcomes",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2023 only materializes public preflight artifacts",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2023 does not run wrong/delayed/mismatched history outcome tests",
        },
    ]

    panel_protocol = {
        "protocol_name": "paper_route_controlled_comparison_panel_preflight",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "no-rollout panel preflight only",
        "controller_profiles": profiles,
        "task_families": list(TASK_FAMILIES),
        "source_targets": {
            "min_clean_sources_per_family": MIN_CLEAN_SOURCES_PER_FAMILY,
            "target_clean_sources_per_family": TARGET_CLEAN_SOURCES_PER_FAMILY,
            "max_single_source_kind_share": MAX_SINGLE_SOURCE_KIND_SHARE,
        },
        "execution_ladder": [
            "stage0_no_rollout_panel_preflight",
            "stage1_public_routing_smoke",
            "stage2_public_full_panel_execution",
            "stage3_fair_training_evaluation_repeat",
            "stage4_private_holdout_after_public_protocol_freeze",
        ],
        "claim_gates": [
            "deployable_feedback_driver",
            "history_conditioned_output_feedback",
            "recurrent_belief_advantage",
            "strong_self_identification",
        ],
        "coverage": coverage_rows,
        "panel_ready_for_routing_smoke": panel_ready_for_routing_smoke,
    }

    artifacts = {
        "summary": output_dir / "summary.json",
        "panel_protocol": output_dir / "panel_protocol.json",
        "workload_matrix": output_dir / "workload_matrix.csv",
        "source_coverage": output_dir / "source_coverage.csv",
        "panel_sources": output_dir / "panel_sources.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
    }
    write_json(artifacts["panel_protocol"], panel_protocol)
    write_csv_rows(artifacts["panel_sources"], source_rows, SOURCE_FIELDNAMES)
    write_csv_rows(artifacts["workload_matrix"], workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(artifacts["source_coverage"], coverage_rows, COVERAGE_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_rows, CLAIM_FIELDNAMES)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }
    summary = {
        "result_class": (
            "controlled_comparison_panel_preflight_ready"
            if panel_ready_for_routing_smoke
            else "controlled_comparison_panel_preflight_source_repair_required"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "task_specs_path": str(task_specs_path),
        "candidate_support_path": str(candidate_support_path),
        "m1683_summary_path": str(m1683_summary_path),
        "profile_count": len(profiles),
        "task_family_count": len(TASK_FAMILIES),
        "panel_source_count": len(source_rows),
        "workload_cell_count": len(workload_rows),
        "coverage_passes": coverage_passes,
        "panel_ready_for_routing_smoke": panel_ready_for_routing_smoke,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": sum(1 for value in guardrail_flags.values() if value),
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": next_blocker,
    }
    write_json(artifacts["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-specs", type=Path, default=DEFAULT_TASK_SPECS)
    parser.add_argument("--candidate-support", type=Path, default=DEFAULT_M2020_CANDIDATE_SUPPORT)
    parser.add_argument("--m1683-summary", type=Path, default=DEFAULT_M1683_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_panel_preflight(
        task_specs_path=args.task_specs,
        candidate_support_path=args.candidate_support,
        m1683_summary_path=args.m1683_summary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_source_count={summary['panel_source_count']}")
    print(f"workload_cell_count={summary['workload_cell_count']}")
    print(f"panel_ready_for_routing_smoke={summary['panel_ready_for_routing_smoke']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
