"""No-rollout source-coverage repair for the controlled comparison panel."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
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


DEFAULT_PANEL_SOURCES = Path("runs/m2023_paper_route_controlled_comparison_panel_preflight/panel_sources.csv")
DEFAULT_M1983_SOURCE_ROWS = Path(
    "runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv"
)
DEFAULT_M1952_SOURCE_ROWS = Path(
    "runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2026_paper_route_controlled_comparison_source_coverage_repair")
DEFAULT_NEXT_BLOCKER = "m2027-paper-route-controlled-comparison-source-coverage-repair-result-audit"
T1_FAMILY = "T1_reactive_active_safety"
T2_FAMILY = "T2_same_current_different_older_history"
T3_FAMILY = "T3_active_diagnostic_warmup"

REPAIR_ACTION_FIELDNAMES = [
    "action_id",
    "panel_task_family",
    "action_type",
    "source_origin",
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
    "before_min_clean_sources_pass",
    "after_min_clean_sources_pass",
    "before_source_kind_share_pass",
    "after_source_kind_share_pass",
    "status",
]


def _is_false(value: Any) -> bool:
    return str(value).strip().lower() in ("", "false", "0", "none")


def _is_clean_supported_candidate(row: Mapping[str, Any]) -> bool:
    if str(row.get("source_support_status", "")).lower() != "supported":
        return False
    for key in (
        "labels_enter_actor_input",
        "profile_specific_tuning",
        "controller_family_ranking_claim_made",
        "paper_level_claim_made",
        "level3_self_id_claim_made",
    ):
        if not _is_false(row.get(key, "")):
            return False
    return True


def _candidate_to_t1_source(row: Mapping[str, Any], *, origin: str, index: int) -> dict[str, Any]:
    repair_id = str(row.get("repair_candidate_id", f"{origin}-{index:04d}"))
    role = str(row.get("source_role_semantics", row.get("target_source_role_semantics", "")))
    tier = str(row.get("feasibility_tier_id", row.get("target_feasibility_tier_id", "")))
    surface = str(row.get("normalized_surface_variant", row.get("target_normalized_surface_variant", "")))
    label = str(row.get("sampled_obstacle_label", row.get("target_sampled_obstacle_label", "")))
    source_kind = str(row.get("repair_source_kind", "unknown_repair_source"))
    return {
        "panel_source_id": f"m2026-t1-{origin}-{repair_id}",
        "panel_task_family": T1_FAMILY,
        "source_origin": origin,
        "source_kind": source_kind,
        "source_edge": "|".join([role, tier, surface, label]),
        "window_tag": "m2026_source_coverage_repair",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": tier,
        "normalized_surface_variant": surface,
        "sampled_obstacle_label": label,
        "source_reference": repair_id,
    }


def load_t1_candidates(paths: Iterable[tuple[str, Path]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for origin, path in paths:
        if not Path(path).exists():
            continue
        for index, row in enumerate(read_csv_rows(path)):
            if not _is_clean_supported_candidate(row):
                continue
            source = _candidate_to_t1_source(row, origin=origin, index=index)
            key = (source["source_kind"], source["source_reference"])
            if key in seen:
                continue
            seen.add(key)
            candidates.append(source)
    return candidates


def _coverage_by_family(coverage_rows: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["panel_task_family"]): row for row in coverage_rows}


def _bool(value: Any) -> bool:
    return str(value).lower() == "true"


def _family_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row["min_clean_sources_pass"]) and _bool(row["source_kind_share_pass"])


def _t1_passes(source_rows: list[Mapping[str, Any]]) -> bool:
    row = _coverage_by_family(build_coverage(source_rows))[T1_FAMILY]
    return _family_ready(row)


def repair_t1_sources(
    *,
    source_rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    repaired = list(source_rows)
    actions: list[dict[str, Any]] = []
    existing_ids = {str(row["panel_source_id"]) for row in repaired}
    grouped: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for candidate in candidates:
        if candidate["panel_source_id"] in existing_ids:
            continue
        if candidate["source_kind"] == "success_stabilizer":
            continue
        grouped[str(candidate["source_kind"])].append(candidate)

    action_index = 0
    while not _t1_passes(repaired):
        t1_rows = [row for row in repaired if row["panel_task_family"] == T1_FAMILY]
        kind_counts = Counter(str(row["source_kind"]) for row in t1_rows)
        available = [kind for kind, rows in grouped.items() if rows]
        if not available:
            actions.append(
                {
                    "action_id": f"repair-{action_index:04d}",
                    "panel_task_family": T1_FAMILY,
                    "action_type": "fail_closed_no_clean_t1_candidate",
                    "source_origin": "",
                    "source_kind": "",
                    "panel_source_id": "",
                    "reason": "no remaining clean non-success-stabilizer T1 repair candidates",
                }
            )
            break
        selected_kind = min(available, key=lambda kind: (kind_counts.get(kind, 0), kind))
        selected = grouped[selected_kind].popleft()
        repaired.append(selected)
        existing_ids.add(str(selected["panel_source_id"]))
        actions.append(
            {
                "action_id": f"repair-{action_index:04d}",
                "panel_task_family": T1_FAMILY,
                "action_type": "add_t1_source",
                "source_origin": selected["source_origin"],
                "source_kind": selected["source_kind"],
                "panel_source_id": selected["panel_source_id"],
                "reason": "increase T1 count and reduce success_stabilizer singleton dominance",
            }
        )
        action_index += 1
        if action_index > 256:
            raise RuntimeError("T1 source repair exceeded safety iteration limit")
    return repaired, actions


def unresolved_t2_t3_actions(source_rows: list[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    coverage = _coverage_by_family(build_coverage(list(source_rows)))
    for offset, family in enumerate((T2_FAMILY, T3_FAMILY)):
        row = coverage[family]
        if _family_ready(row):
            continue
        actions.append(
            {
                "action_id": f"repair-{start_index + offset:04d}",
                "panel_task_family": family,
                "action_type": "unresolved_no_clean_topup_in_current_artifacts",
                "source_origin": "",
                "source_kind": "",
                "panel_source_id": "",
                "reason": (
                    "current M1680/M2023 pool has no additional clean same-family sources; "
                    "route to audit rather than weakening thresholds or duplicating sources"
                ),
            }
        )
    return actions


def coverage_comparison_rows(
    before_rows: list[Mapping[str, Any]], after_rows: list[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    before = _coverage_by_family(build_coverage(list(before_rows)))
    after = _coverage_by_family(build_coverage(list(after_rows)))
    output: list[dict[str, Any]] = []
    for family in TASK_FAMILIES:
        b = before[family]
        a = after[family]
        before_ready = _family_ready(b)
        after_ready = _family_ready(a)
        if after_ready and not before_ready:
            status = "passes_after_repair"
        elif after_ready and before_ready:
            status = "already_ready"
        elif int(a["source_count"]) > int(b["source_count"]) or float(a["max_single_source_kind_share"]) < float(
            b["max_single_source_kind_share"]
        ):
            status = "improved_but_unready"
        else:
            status = "unchanged_unready"
        output.append(
            {
                "panel_task_family": family,
                "before_source_count": b["source_count"],
                "after_source_count": a["source_count"],
                "before_source_kind_count": b["source_kind_count"],
                "after_source_kind_count": a["source_kind_count"],
                "before_max_single_source_kind_share": b["max_single_source_kind_share"],
                "after_max_single_source_kind_share": a["max_single_source_kind_share"],
                "before_min_clean_sources_pass": b["min_clean_sources_pass"],
                "after_min_clean_sources_pass": a["min_clean_sources_pass"],
                "before_source_kind_share_pass": b["source_kind_share_pass"],
                "after_source_kind_share_pass": a["source_kind_share_pass"],
                "status": status,
            }
        )
    return output


def run_source_coverage_repair(
    *,
    panel_sources_path: Path = DEFAULT_PANEL_SOURCES,
    m1983_sources_path: Path = DEFAULT_M1983_SOURCE_ROWS,
    m1952_sources_path: Path = DEFAULT_M1952_SOURCE_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_sources = read_csv_rows(panel_sources_path)
    t1_candidates = load_t1_candidates(
        (
            ("m1983_outcome_support", m1983_sources_path),
            ("m1952_calibrated_offtrack_support", m1952_sources_path),
        )
    )
    repaired_sources, repair_actions = repair_t1_sources(source_rows=base_sources, candidates=t1_candidates)
    repair_actions.extend(unresolved_t2_t3_actions(repaired_sources, start_index=len(repair_actions)))

    repaired_coverage = build_coverage(repaired_sources)
    coverage_comparison = coverage_comparison_rows(base_sources, repaired_sources)
    coverage_by_family = _coverage_by_family(repaired_coverage)
    ready_families = [family for family in TASK_FAMILIES if _family_ready(coverage_by_family[family])]
    unresolved_families = [family for family in TASK_FAMILIES if family not in ready_families]
    panel_ready = not unresolved_families
    added_source_count = sum(1 for action in repair_actions if action["action_type"] == "add_t1_source")
    improved_family_count = sum(1 for row in coverage_comparison if row["status"] in ("passes_after_repair", "improved_but_unready"))
    if panel_ready:
        result_class = "controlled_comparison_source_coverage_repair_pass"
    elif added_source_count or improved_family_count:
        result_class = "controlled_comparison_source_coverage_repair_partial"
    else:
        result_class = "controlled_comparison_source_coverage_repair_fail_closed"

    claim_rows = [
        {
            "claim": "controlled_comparison_source_coverage_repair_completed",
            "admissible": True,
            "reason": "M2026 writes no-rollout repaired source coverage and repair action artifacts",
        },
        {
            "claim": "panel_ready_for_routing_smoke",
            "admissible": panel_ready,
            "reason": "requires all five task families to pass source count and source-kind share thresholds",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2026 does not execute the panel or use private holdout",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2026 is source-coverage repair only and does not compare outcomes",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2026 only repairs public preflight artifacts",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2026 does not run wrong/delayed/mismatched history outcome tests",
        },
    ]

    artifacts = {
        "summary": output_dir / "summary.json",
        "repaired_panel_sources": output_dir / "repaired_panel_sources.csv",
        "repaired_source_coverage": output_dir / "repaired_source_coverage.csv",
        "coverage_comparison": output_dir / "coverage_comparison.csv",
        "repair_actions": output_dir / "repair_actions.csv",
        "claim_boundary": output_dir / "claim_boundary.csv",
    }
    write_csv_rows(artifacts["repaired_panel_sources"], repaired_sources, SOURCE_FIELDNAMES)
    write_csv_rows(artifacts["repaired_source_coverage"], repaired_coverage, COVERAGE_FIELDNAMES)
    write_csv_rows(artifacts["coverage_comparison"], coverage_comparison, COVERAGE_COMPARISON_FIELDNAMES)
    write_csv_rows(artifacts["repair_actions"], repair_actions, REPAIR_ACTION_FIELDNAMES)
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
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "panel_sources_path": str(panel_sources_path),
        "m1983_sources_path": str(m1983_sources_path),
        "m1952_sources_path": str(m1952_sources_path),
        "base_source_count": len(base_sources),
        "repaired_source_count": len(repaired_sources),
        "added_source_count": added_source_count,
        "t1_candidate_count": len(t1_candidates),
        "ready_families": ready_families,
        "unresolved_families": unresolved_families,
        "panel_ready_for_routing_smoke": panel_ready,
        "min_clean_sources_per_family": MIN_CLEAN_SOURCES_PER_FAMILY,
        "max_single_source_kind_share": MAX_SINGLE_SOURCE_KIND_SHARE,
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
    parser.add_argument("--panel-sources", type=Path, default=DEFAULT_PANEL_SOURCES)
    parser.add_argument("--m1983-sources", type=Path, default=DEFAULT_M1983_SOURCE_ROWS)
    parser.add_argument("--m1952-sources", type=Path, default=DEFAULT_M1952_SOURCE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_source_coverage_repair(
        panel_sources_path=args.panel_sources,
        m1983_sources_path=args.m1983_sources,
        m1952_sources_path=args.m1952_sources,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"base_source_count={summary['base_source_count']}")
    print(f"repaired_source_count={summary['repaired_source_count']}")
    print(f"added_source_count={summary['added_source_count']}")
    print(f"panel_ready_for_routing_smoke={summary['panel_ready_for_routing_smoke']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
