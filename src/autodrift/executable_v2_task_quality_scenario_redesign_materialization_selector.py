"""Select a bounded non-holdout materialization subset for task-quality scenarios."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.executable_v2_task_quality_scenario_redesign_source_mining_audit import (
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    TIER_E,
)
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


DEFAULT_JOINED_SOURCE_SUPPORT = Path(
    "runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv"
)
DEFAULT_OUTPUT_CONFIG = Path("configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation")
DEFAULT_NEXT_BLOCKER = "m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design"
SCENARIO_QUALITY_BRANCH_ID = "paper_route_task_quality_scenario_redesign"
SELECTION_PROTOCOL_VERSION = "task_quality_materialization_subset_v0"
TIERS = (TIER_A, TIER_B, TIER_C, TIER_D, TIER_E)
ROLES = (ROLE_DRIFT_REQUIRED, ROLE_STABLE_AEB, ROLE_STABLE_AES, ROLE_UNAVOIDABLE)
SURFACES = ("steady_surface", "post_friction_step")
SOURCE_SPLIT_PRIORITY = {"public_gate": 0, "public_debug": 1}
PRESERVED_SOURCE_FIELDS = (
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "feasibility_tier_id",
    "source_role_semantics",
    "source_split",
    "surface_variant",
    "speed_ref",
    "mu",
    "target_support_mode",
    "target_boundary_mode",
    "source_support_status",
    "materialization_admissible",
    "source_support_accepted_cell_count_total",
    "source_support_feasible_profile_count",
    "source_support_profile_count",
    "diagnostic_only_no_ranking_claim",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _eligible(row: Mapping[str, Any]) -> bool:
    return (
        _bool_value(row.get("materialization_admissible"))
        and str(row.get("source_split", "")) in SOURCE_SPLIT_PRIORITY
        and not _bool_value(row.get("paper_holdout_candidate"))
        and not _bool_value(row.get("labels_enter_actor_input"))
        and not _bool_value(row.get("v2_ranking_admissible_by_default"))
    )


def _sort_key(row: Mapping[str, Any]) -> tuple[int, float, float, str]:
    return (
        SOURCE_SPLIT_PRIORITY.get(str(row.get("source_split", "")), 99),
        _float_value(row.get("speed_ref")),
        _float_value(row.get("mu")),
        str(row.get("candidate_source_id", "")),
    )


def _selected_source(row: Mapping[str, Any], *, selection_index: int) -> dict[str, Any]:
    out = {field: row.get(field, "") for field in PRESERVED_SOURCE_FIELDS}
    out.update(
        {
            "selection_index": int(selection_index),
            "selection_protocol_version": SELECTION_PROTOCOL_VERSION,
            "speed_ref": _float_value(row.get("speed_ref")),
            "mu": _float_value(row.get("mu")),
            "materialization_admissible": True,
            "source_support_accepted_cell_count_total": _int_value(
                row.get("source_support_accepted_cell_count_total")
            ),
            "source_support_feasible_profile_count": _int_value(row.get("source_support_feasible_profile_count")),
            "source_support_profile_count": _int_value(row.get("source_support_profile_count")),
            "paper_holdout_candidate": False,
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
            "diagnostic_only_no_ranking_claim": True,
        }
    )
    return out


def select_materialization_sources(
    rows: Iterable[Mapping[str, Any]],
    *,
    tiers: Sequence[str] = TIERS,
    roles: Sequence[str] = ROLES,
    surfaces: Sequence[str] = SURFACES,
    sources_per_surface: int = 2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return selected rows and selection failures."""

    eligible_rows = [dict(row) for row in rows if _eligible(row)]
    by_group_surface: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible_rows:
        key = (
            str(row.get("feasibility_tier_id", "")),
            str(row.get("source_role_semantics", "")),
            str(row.get("surface_variant", "")),
        )
        by_group_surface[key].append(row)

    selected: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    selection_index = 0
    for tier in tiers:
        for role in roles:
            for surface in surfaces:
                candidates = sorted(by_group_surface[(tier, role, surface)], key=_sort_key)
                if len(candidates) < sources_per_surface:
                    failures.append(
                        {
                            "feasibility_tier_id": tier,
                            "source_role_semantics": role,
                            "surface_variant": surface,
                            "eligible_candidate_count": len(candidates),
                            "required_candidate_count": int(sources_per_surface),
                            "failure_reason": "insufficient_eligible_surface_candidates",
                        }
                    )
                    continue
                for row in candidates[:sources_per_surface]:
                    selection_index += 1
                    selected.append(_selected_source(row, selection_index=selection_index))
    return selected, failures


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_counts(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        group_key = "|".join(str(row.get(key, "")) for key in keys)
        counts[group_key] += 1
    return dict(sorted(counts.items()))


def _selection_summary(
    selected_sources: list[Mapping[str, Any]],
    failures: list[Mapping[str, Any]],
    *,
    input_rows: list[Mapping[str, Any]],
    expected_controller_profile_count: int,
) -> dict[str, Any]:
    selected_source_count = len(selected_sources)
    selected_tier_role_counts = _group_counts(
        selected_sources,
        ("feasibility_tier_id", "source_role_semantics"),
    )
    selected_tier_role_surface_counts = _group_counts(
        selected_sources,
        ("feasibility_tier_id", "source_role_semantics", "surface_variant"),
    )
    expected_group_count = len(TIERS) * len(ROLES)
    expected_surface_group_count = expected_group_count * len(SURFACES)
    paper_holdout_selected_count = sum(_bool_value(row.get("paper_holdout_candidate")) for row in selected_sources)
    labels_enter_actor_input_count = sum(_bool_value(row.get("labels_enter_actor_input")) for row in selected_sources)
    ranking_default_count = sum(_bool_value(row.get("v2_ranking_admissible_by_default")) for row in selected_sources)
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    tier_role_balance_pass = (
        len(selected_tier_role_counts) == expected_group_count
        and all(count == 4 for count in selected_tier_role_counts.values())
    )
    surface_balance_pass = (
        len(selected_tier_role_surface_counts) == expected_surface_group_count
        and all(count == 2 for count in selected_tier_role_surface_counts.values())
    )
    result_passes = (
        selected_source_count == 80
        and not failures
        and tier_role_balance_pass
        and surface_balance_pass
        and paper_holdout_selected_count == 0
        and labels_enter_actor_input_count == 0
        and ranking_default_count == 0
        and guardrail_violation_count == 0
    )
    return {
        "result_class": (
            "task_quality_scenario_materialization_selector_pass"
            if result_passes
            else "task_quality_scenario_materialization_selector_incomplete_or_fail"
        ),
        "input_row_count": len(input_rows),
        "eligible_source_count": sum(_eligible(row) for row in input_rows),
        "selected_source_count": selected_source_count,
        "expected_selected_source_count": 80,
        "expected_controller_profile_count": int(expected_controller_profile_count),
        "expected_planned_workload_cell_count": int(selected_source_count * expected_controller_profile_count),
        "selected_tier_counts": _count_by(selected_sources, "feasibility_tier_id"),
        "selected_role_counts": _count_by(selected_sources, "source_role_semantics"),
        "selected_split_counts": _count_by(selected_sources, "source_split"),
        "selected_surface_counts": _count_by(selected_sources, "surface_variant"),
        "selected_tier_role_counts": selected_tier_role_counts,
        "selected_tier_role_surface_counts": selected_tier_role_surface_counts,
        "tier_role_balance_pass": bool(tier_role_balance_pass),
        "surface_balance_pass": bool(surface_balance_pass),
        "selection_failure_count": len(failures),
        "paper_holdout_selected_count": int(paper_holdout_selected_count),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_default_count),
        "source_support_accepted_cell_count_total": int(
            sum(_int_value(row.get("source_support_accepted_cell_count_total")) for row in selected_sources)
        ),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
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
        "level3_self_id_claim_made": False,
        "recommended_next_route": (
            "route_to_materialization_command_design"
            if result_passes
            else "route_to_source_template_repair_or_branch_synthesis"
        ),
    }


def materialize_source_subset(
    *,
    joined_source_support_path: Path | str = DEFAULT_JOINED_SOURCE_SUPPORT,
    output_config_path: Path | str = DEFAULT_OUTPUT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    expected_controller_profile_count: int = 12,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    input_rows = [dict(row) for row in read_csv_rows(joined_source_support_path)]
    selected_sources, failures = select_materialization_sources(input_rows)
    summary = _selection_summary(
        selected_sources,
        failures,
        input_rows=input_rows,
        expected_controller_profile_count=expected_controller_profile_count,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_csv = output / "selected_sources.csv"
    failure_csv = output / "selection_failures.csv"
    summary_path = output / "summary.json"
    write_csv_rows(selected_csv, selected_sources)
    write_csv_rows(failure_csv, [dict(row) for row in failures])

    config = {
        "scenario_quality_branch_id": SCENARIO_QUALITY_BRANCH_ID,
        "source_support_parent_artifact": str(joined_source_support_path),
        "selected_source_count": summary["selected_source_count"],
        "expected_controller_profile_count": int(expected_controller_profile_count),
        "expected_planned_workload_cell_count": summary["expected_planned_workload_cell_count"],
        "selection_protocol_version": SELECTION_PROTOCOL_VERSION,
        "selected_sources": selected_sources,
        "selection_summary": summary,
        "guardrail_flags": summary["guardrail_flags"],
    }
    write_json(output_config_path, config)
    summary.update(
        {
            "generated_at_utc": utc_timestamp(),
            "joined_source_support_path": str(joined_source_support_path),
            "output_config_path": str(output_config_path),
            "selected_sources_csv": str(selected_csv),
            "selection_failures_csv": str(failure_csv),
            "summary_path": str(summary_path),
            "next_blocker": next_blocker,
        }
    )
    write_json(summary_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joined-source-support", type=Path, default=DEFAULT_JOINED_SOURCE_SUPPORT)
    parser.add_argument("--output-config", type=Path, default=DEFAULT_OUTPUT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--expected-controller-profile-count", type=int, default=12)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = materialize_source_subset(
        joined_source_support_path=args.joined_source_support,
        output_config_path=args.output_config,
        output_dir=args.output_dir,
        expected_controller_profile_count=int(args.expected_controller_profile_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"output_config={args.output_config}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_source_count={summary['selected_source_count']}")
    print(f"expected_planned_workload_cell_count={summary['expected_planned_workload_cell_count']}")
    print(f"tier_role_balance_pass={summary['tier_role_balance_pass']}")
    print(f"surface_balance_pass={summary['surface_balance_pass']}")
    print(f"recommended_next_route={summary['recommended_next_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
