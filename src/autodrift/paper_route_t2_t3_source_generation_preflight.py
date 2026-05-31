"""No-rollout T2/T3 source-generation preflight for the paper route."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.bounded_comparison_candidate_qualification import read_csv_rows
from autodrift.paper_route_controlled_comparison_panel_preflight import (
    CLAIM_FIELDNAMES,
    COVERAGE_FIELDNAMES,
    MAX_SINGLE_SOURCE_KIND_SHARE,
    MIN_CLEAN_SOURCES_PER_FAMILY,
    SOURCE_FIELDNAMES,
    TASK_FAMILIES,
    build_coverage,
)


DEFAULT_PANEL_SOURCES = Path(
    "runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repaired_panel_sources.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2029_paper_route_t2_t3_source_generation_preflight")
DEFAULT_NEXT_BLOCKER = "m2030-paper-route-t2-t3-source-generation-preflight-result-audit"
T2_FAMILY = "T2_same_current_different_older_history"
T3_FAMILY = "T3_active_diagnostic_warmup"

SOURCE_SPEC_FIELDNAMES = [
    "source_spec_id",
    "panel_task_family",
    "source_kind",
    "source_origin",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "parent_feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "source_reference",
    "same_current_constraint",
    "recent_window_seconds",
    "older_history_offset_seconds",
    "warmup_mode",
    "warmup_duration_seconds",
    "obstacle_reveal_delay_seconds",
    "labels_enter_actor_input",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
GENERATION_ACTION_FIELDNAMES = [
    "action_id",
    "panel_task_family",
    "action_type",
    "source_kind",
    "panel_source_id",
    "reason",
]
COVERAGE_COMPARISON_FIELDNAMES = [
    "panel_task_family",
    "before_source_count",
    "after_source_count",
    "before_source_kind_count",
    "after_source_kind_count",
    "before_max_single_source_kind_share",
    "after_max_single_source_kind_share",
    "before_source_kind_share_pass",
    "after_source_kind_share_pass",
    "status",
]


def _float_tag(value: float) -> str:
    return str(value).replace(".", "p")


def _bool(value: Any) -> bool:
    return str(value).lower() == "true"


def _family_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row["min_clean_sources_pass"]) and _bool(row["source_kind_share_pass"])


def _coverage_by_family(coverage_rows: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["panel_task_family"]): row for row in coverage_rows}


def _clean_flags() -> dict[str, bool]:
    return {
        "labels_enter_actor_input": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def build_t2_source_specs() -> list[dict[str, Any]]:
    source_kinds = [
        "same_current_brake_authority_older_history_proxy",
        "same_current_yaw_authority_older_history_proxy",
        "same_current_steer_lag_older_history_proxy",
        "same_current_drive_brake_asymmetry_older_history_proxy",
        "same_current_rear_lateral_authority_older_history_proxy",
        "same_current_mixed_authority_older_history_proxy",
    ]
    window_pairs = [
        (0.25, 1.5),
        (0.5, 1.5),
        (1.0, 1.5),
        (0.25, 2.0),
        (0.5, 2.0),
        (1.0, 3.0),
    ]
    specs: list[dict[str, Any]] = []
    for kind in source_kinds:
        for index, (recent_window, older_offset) in enumerate(window_pairs):
            spec_id = f"m2029-t2-{kind}-{index:02d}"
            specs.append(
                {
                    "source_spec_id": spec_id,
                    "panel_task_family": T2_FAMILY,
                    "source_kind": kind,
                    "source_origin": "m2029_t2_t3_source_generation_preflight",
                    "source_edge": f"same_current|{kind}|k{_float_tag(recent_window)}|older{_float_tag(older_offset)}",
                    "window_tag": f"m2029_same_current_k{_float_tag(recent_window)}_older{_float_tag(older_offset)}",
                    "source_role_semantics": "same_current_different_older_history",
                    "parent_feasibility_tier_id": "T2_generated",
                    "normalized_surface_variant": kind,
                    "sampled_obstacle_label": "same_current_different_older_history",
                    "source_reference": spec_id,
                    "same_current_constraint": "matched_current_response_previous_command_and_recent_window",
                    "recent_window_seconds": recent_window,
                    "older_history_offset_seconds": older_offset,
                    "warmup_mode": "",
                    "warmup_duration_seconds": "",
                    "obstacle_reveal_delay_seconds": "",
                    **_clean_flags(),
                }
            )
    return specs


def build_t3_source_specs() -> list[dict[str, Any]]:
    source_kinds = [
        "warmup_brake_authority_proxy",
        "warmup_yaw_authority_proxy",
        "warmup_steer_lag_proxy",
        "warmup_rear_lateral_authority_proxy",
        "warmup_mixed_authority_proxy",
        "warmup_terminal_boundary_recovery_proxy",
    ]
    warmups = [
        ("brake_tap", 0.5, 0.2),
        ("steer_pulse", 1.0, 0.5),
        ("brake_plus_steer", 1.5, 1.0),
    ]
    specs: list[dict[str, Any]] = []
    for kind in source_kinds:
        for index, (warmup_mode, warmup_duration, reveal_delay) in enumerate(warmups):
            spec_id = f"m2029-t3-{kind}-{index:02d}"
            specs.append(
                {
                    "source_spec_id": spec_id,
                    "panel_task_family": T3_FAMILY,
                    "source_kind": kind,
                    "source_origin": "m2029_t2_t3_source_generation_preflight",
                    "source_edge": (
                        f"active_diagnostic_warmup|{kind}|{warmup_mode}|"
                        f"duration{_float_tag(warmup_duration)}|reveal{_float_tag(reveal_delay)}"
                    ),
                    "window_tag": f"m2029_warmup_{warmup_mode}_reveal{_float_tag(reveal_delay)}",
                    "source_role_semantics": "active_diagnostic_warmup",
                    "parent_feasibility_tier_id": "T3_generated",
                    "normalized_surface_variant": kind,
                    "sampled_obstacle_label": "active_diagnostic_warmup",
                    "source_reference": spec_id,
                    "same_current_constraint": "",
                    "recent_window_seconds": "",
                    "older_history_offset_seconds": "",
                    "warmup_mode": warmup_mode,
                    "warmup_duration_seconds": warmup_duration,
                    "obstacle_reveal_delay_seconds": reveal_delay,
                    **_clean_flags(),
                }
            )
    return specs


def specs_to_panel_sources(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        rows.append(
            {
                "panel_source_id": str(spec["source_spec_id"]),
                "panel_task_family": spec["panel_task_family"],
                "source_origin": spec["source_origin"],
                "source_kind": spec["source_kind"],
                "source_edge": spec["source_edge"],
                "window_tag": spec["window_tag"],
                "source_role_semantics": spec["source_role_semantics"],
                "parent_feasibility_tier_id": spec["parent_feasibility_tier_id"],
                "normalized_surface_variant": spec["normalized_surface_variant"],
                "sampled_obstacle_label": spec["sampled_obstacle_label"],
                "source_reference": spec["source_reference"],
            }
        )
    return rows


def _coverage_comparison(
    before_rows: list[Mapping[str, Any]], after_rows: list[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    before = _coverage_by_family(build_coverage(before_rows))
    after = _coverage_by_family(build_coverage(after_rows))
    comparison: list[dict[str, Any]] = []
    for family in TASK_FAMILIES:
        b = before[family]
        a = after[family]
        before_ready = _family_ready(b)
        after_ready = _family_ready(a)
        if after_ready and not before_ready:
            status = "passes_after_generation"
        elif after_ready and before_ready:
            status = "already_ready"
        elif int(a["source_count"]) > int(b["source_count"]) or float(a["max_single_source_kind_share"]) < float(
            b["max_single_source_kind_share"]
        ):
            status = "improved_but_unready"
        else:
            status = "unchanged_unready"
        comparison.append(
            {
                "panel_task_family": family,
                "before_source_count": b["source_count"],
                "after_source_count": a["source_count"],
                "before_source_kind_count": b["source_kind_count"],
                "after_source_kind_count": a["source_kind_count"],
                "before_max_single_source_kind_share": b["max_single_source_kind_share"],
                "after_max_single_source_kind_share": a["max_single_source_kind_share"],
                "before_source_kind_share_pass": b["source_kind_share_pass"],
                "after_source_kind_share_pass": a["source_kind_share_pass"],
                "status": status,
            }
        )
    return comparison


def _generation_actions(generated_sources: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for index, row in enumerate(generated_sources):
        actions.append(
            {
                "action_id": f"generation-{index:04d}",
                "panel_task_family": row["panel_task_family"],
                "action_type": "add_generated_source",
                "source_kind": row["source_kind"],
                "panel_source_id": row["panel_source_id"],
                "reason": "increase T2/T3 source-kind diversity with no-rollout generated source rows",
            }
        )
    return actions


def run_t2_t3_source_generation_preflight(
    *,
    panel_sources_path: Path = DEFAULT_PANEL_SOURCES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_sources = read_csv_rows(panel_sources_path)
    specs = build_t2_source_specs() + build_t3_source_specs()
    generated_sources = specs_to_panel_sources(specs)

    existing_ids = {str(row["panel_source_id"]) for row in base_sources}
    duplicate_generated_ids = [row["panel_source_id"] for row in generated_sources if row["panel_source_id"] in existing_ids]
    merged_sources = list(base_sources)
    if not duplicate_generated_ids:
        merged_sources.extend(generated_sources)

    generated_t2_count = sum(1 for row in generated_sources if row["panel_task_family"] == T2_FAMILY)
    generated_t3_count = sum(1 for row in generated_sources if row["panel_task_family"] == T3_FAMILY)
    projection = build_coverage(merged_sources)
    comparison = _coverage_comparison(base_sources, merged_sources)
    coverage_by_family = _coverage_by_family(projection)
    ready_families = [family for family in TASK_FAMILIES if _family_ready(coverage_by_family[family])]
    unresolved_families = [family for family in TASK_FAMILIES if family not in ready_families]
    projected_ready = not unresolved_families

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
        "t4_t5_relabel_used": False,
        "source_kind_threshold_weakened": False,
        "duplicate_generated_source_id": bool(duplicate_generated_ids),
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)

    expected_counts_met = generated_t2_count == 36 and generated_t3_count == 18
    if projected_ready and expected_counts_met and guardrail_violation_count == 0:
        result_class = "t2_t3_source_generation_preflight_pass"
    elif generated_sources and guardrail_violation_count == 0:
        result_class = "t2_t3_source_generation_preflight_partial"
    else:
        result_class = "t2_t3_source_generation_preflight_fail_closed"

    claim_rows = [
        {
            "claim": "t2_t3_source_generation_preflight_completed",
            "admissible": True,
            "reason": "M2029 writes no-rollout generated source specs and projected coverage artifacts",
        },
        {
            "claim": "panel_projected_ready_for_routing_smoke",
            "admissible": projected_ready,
            "reason": "requires all five task families to pass projected source count and source-kind share gates",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2029 does not execute the panel or compare controller outcomes",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2029 is source-generation preflight only",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2029 does not run routing smoke measured execution or private holdout",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2029 does not run wrong delayed reset or mismatched history outcome tests",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "generated_source_specs": output_dir / "generated_source_specs.csv",
        "generated_panel_sources": output_dir / "generated_panel_sources.csv",
        "merged_panel_sources": output_dir / "merged_panel_sources.csv",
        "source_coverage_projection": output_dir / "source_coverage_projection.csv",
        "source_coverage_comparison": output_dir / "source_coverage_comparison.csv",
        "generation_actions": output_dir / "generation_actions.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
    }
    write_csv_rows(artifacts["generated_source_specs"], specs, SOURCE_SPEC_FIELDNAMES)
    write_csv_rows(artifacts["generated_panel_sources"], generated_sources, SOURCE_FIELDNAMES)
    write_csv_rows(artifacts["merged_panel_sources"], merged_sources, SOURCE_FIELDNAMES)
    write_csv_rows(artifacts["source_coverage_projection"], projection, COVERAGE_FIELDNAMES)
    write_csv_rows(artifacts["source_coverage_comparison"], comparison, COVERAGE_COMPARISON_FIELDNAMES)
    write_csv_rows(artifacts["generation_actions"], _generation_actions(generated_sources), GENERATION_ACTION_FIELDNAMES)
    write_csv_rows(artifacts["claim_boundary"], claim_rows, CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "panel_sources_path": str(panel_sources_path),
        "base_source_count": len(base_sources),
        "generated_source_count": len(generated_sources),
        "generated_t2_source_count": generated_t2_count,
        "generated_t3_source_count": generated_t3_count,
        "merged_source_count": len(merged_sources),
        "expected_counts_met": expected_counts_met,
        "duplicate_generated_source_ids": duplicate_generated_ids,
        "ready_families": ready_families,
        "unresolved_families": unresolved_families,
        "panel_projected_ready_for_routing_smoke": projected_ready,
        "min_clean_sources_per_family": MIN_CLEAN_SOURCES_PER_FAMILY,
        "max_single_source_kind_share": MAX_SINGLE_SOURCE_KIND_SHARE,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
    parser.add_argument("--panel-sources", type=Path, default=DEFAULT_PANEL_SOURCES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_t2_t3_source_generation_preflight(
        panel_sources_path=args.panel_sources,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"base_source_count={summary['base_source_count']}")
    print(f"generated_source_count={summary['generated_source_count']}")
    print(f"merged_source_count={summary['merged_source_count']}")
    print(f"panel_projected_ready_for_routing_smoke={summary['panel_projected_ready_for_routing_smoke']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
