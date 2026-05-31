"""Select a calibrated materialization subset from M1952 repaired source rows."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


DEFAULT_REPAIR_SOURCE_ROWS = Path(
    "runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv"
)
DEFAULT_REPAIR_ACCEPTED_CELLS = Path(
    "runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv"
)
DEFAULT_OUTPUT_CONFIG = Path("configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector")
DEFAULT_NEXT_BLOCKER = "m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design"
SCENARIO_QUALITY_BRANCH_ID = "paper_route_task_quality_calibrated_materialization"
SELECTION_PROTOCOL_VERSION = "task_quality_calibrated_materialization_subset_v0"

ROLE_STABLE_AEB = "stable_aeb"
ROLE_STABLE_AES_ONLY = "stable_aes_only"
ROLE_DRIFT_REQUIRED = "drift_required_recovery"
ROLE_UNAVOIDABLE = "unavoidable_mitigation"
SURFACE_POST = "post_friction_step"
SURFACE_STEADY = "steady_surface"
SURFACE_RELIEF_UNSPECIFIED = "relief_surface_unspecified"

SOURCE_SPLIT_PRIORITY = {"public_gate": 0, "public_debug": 1}
SOURCE_KIND_QUOTAS = {
    "anchor_neighborhood": 32,
    "success_stabilizer": 24,
    "offtrack_boundary_relief": 8,
    "mitigation_isolation_check": 16,
}
QUOTA_SPECS: tuple[dict[str, Any], ...] = (
    {
        "quota_name": "anchor_post",
        "repair_source_kind": "anchor_neighborhood",
        "source_role_semantics": ROLE_STABLE_AEB,
        "parent_surface_variant": SURFACE_POST,
        "base_geometry_prefix": "m1950_calibrated_anchor_fallback",
        "count": 16,
    },
    {
        "quota_name": "anchor_steady",
        "repair_source_kind": "anchor_neighborhood",
        "source_role_semantics": ROLE_STABLE_AEB,
        "parent_surface_variant": SURFACE_STEADY,
        "base_geometry_prefix": "m1950_calibrated_anchor_fallback",
        "count": 16,
    },
    {
        "quota_name": "success_stable_aeb_post",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_STABLE_AEB,
        "parent_surface_variant": SURFACE_POST,
        "count": 4,
    },
    {
        "quota_name": "success_stable_aeb_steady",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_STABLE_AEB,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 4,
    },
    {
        "quota_name": "success_stable_aes_post",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_STABLE_AES_ONLY,
        "parent_surface_variant": SURFACE_POST,
        "count": 3,
    },
    {
        "quota_name": "success_stable_aes_steady",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_STABLE_AES_ONLY,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 3,
    },
    {
        "quota_name": "success_drift_post",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_DRIFT_REQUIRED,
        "parent_surface_variant": SURFACE_POST,
        "count": 4,
    },
    {
        "quota_name": "success_drift_steady",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_DRIFT_REQUIRED,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 2,
    },
    {
        "quota_name": "success_unavoidable_post",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_UNAVOIDABLE,
        "parent_surface_variant": SURFACE_POST,
        "count": 1,
    },
    {
        "quota_name": "success_unavoidable_steady",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": ROLE_UNAVOIDABLE,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 3,
    },
    {
        "quota_name": "offtrack_relief_stable_aes",
        "repair_source_kind": "offtrack_boundary_relief",
        "source_role_semantics": ROLE_STABLE_AES_ONLY,
        "parent_surface_variant": "",
        "count": 8,
    },
    {
        "quota_name": "mitigation_unavoidable_post",
        "repair_source_kind": "mitigation_isolation_check",
        "source_role_semantics": ROLE_UNAVOIDABLE,
        "parent_surface_variant": SURFACE_POST,
        "count": 4,
    },
    {
        "quota_name": "mitigation_unavoidable_steady",
        "repair_source_kind": "mitigation_isolation_check",
        "source_role_semantics": ROLE_UNAVOIDABLE,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 5,
    },
    {
        "quota_name": "mitigation_stable_aeb_post",
        "repair_source_kind": "mitigation_isolation_check",
        "source_role_semantics": ROLE_STABLE_AEB,
        "parent_surface_variant": SURFACE_POST,
        "count": 4,
    },
    {
        "quota_name": "mitigation_drift_steady",
        "repair_source_kind": "mitigation_isolation_check",
        "source_role_semantics": ROLE_DRIFT_REQUIRED,
        "parent_surface_variant": SURFACE_STEADY,
        "count": 3,
    },
)
PRESERVED_SOURCE_FIELDS = (
    "repair_candidate_id",
    "repair_source_kind",
    "repair_source_family",
    "source_split",
    "offtrack_repair_mode",
    "recovery_corridor_profile",
    "parent_candidate_source_id",
    "parent_task_source_id",
    "parent_profile_name",
    "parent_feasibility_tier_id",
    "parent_source_role_semantics",
    "parent_surface_variant",
    "parent_sampled_obstacle_label",
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "source_role_semantics",
    "profile_name",
    "profile_group",
    "speed_ref",
    "mu",
    "friction_step_enabled",
    "friction_step_at",
    "grid_cell_count",
    "accepted_cell_count",
    "source_support_status",
    "accepted_distance_min",
    "accepted_distance_max",
    "accepted_half_width_min",
    "accepted_half_width_max",
    "dominant_label",
    "post_obstacle_track_width",
    "base_geometry_source",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
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


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _eligible(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("source_support_status", "")) == "supported"
        and str(row.get("source_split", "")) in SOURCE_SPLIT_PRIORITY
        and not _bool_value(row.get("labels_enter_actor_input"))
        and not _bool_value(row.get("v2_ranking_admissible_by_default"))
        and not _bool_value(row.get("profile_specific_tuning"))
        and not _bool_value(row.get("controller_family_ranking_claim_made"))
        and not _bool_value(row.get("paper_level_claim_made"))
        and not _bool_value(row.get("level3_self_id_claim_made"))
    )


def _normalized_surface(row: Mapping[str, Any]) -> str:
    surface = str(row.get("parent_surface_variant", ""))
    if surface:
        return surface
    if str(row.get("repair_source_kind", "")) == "offtrack_boundary_relief":
        return SURFACE_RELIEF_UNSPECIFIED
    return surface


def _matches_spec(row: Mapping[str, Any], spec: Mapping[str, Any]) -> bool:
    if str(row.get("repair_source_kind", "")) != str(spec["repair_source_kind"]):
        return False
    if str(row.get("source_role_semantics", "")) != str(spec["source_role_semantics"]):
        return False
    if str(row.get("parent_surface_variant", "")) != str(spec.get("parent_surface_variant", "")):
        return False
    prefix = str(spec.get("base_geometry_prefix", ""))
    return not prefix or str(row.get("base_geometry_source", "")).startswith(prefix)


def _sort_key(row: Mapping[str, Any]) -> tuple[int, int, str, str, str]:
    return (
        -_int_value(row.get("accepted_cell_count")),
        SOURCE_SPLIT_PRIORITY.get(str(row.get("source_split", "")), 99),
        str(row.get("base_geometry_source", "")),
        str(row.get("candidate_source_id", "")),
        str(row.get("repair_candidate_id", "")),
    )


def _selected_source(row: Mapping[str, Any], *, selection_index: int, quota_name: str) -> dict[str, Any]:
    out = {field: row.get(field, "") for field in PRESERVED_SOURCE_FIELDS}
    out.update(
        {
            "selection_index": int(selection_index),
            "selection_quota_name": quota_name,
            "selection_protocol_version": SELECTION_PROTOCOL_VERSION,
            "normalized_surface_variant": _normalized_surface(row),
            "speed_ref": _float_value(row.get("speed_ref")),
            "mu": _float_value(row.get("mu")),
            "friction_step_enabled": _bool_value(row.get("friction_step_enabled")),
            "friction_step_at": _int_value(row.get("friction_step_at")),
            "grid_cell_count": _int_value(row.get("grid_cell_count")),
            "accepted_cell_count": _int_value(row.get("accepted_cell_count")),
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "diagnostic_only_no_ranking_claim": True,
        }
    )
    return out


def _duplicate_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    counts = Counter(str(row.get(key, "")) for row in rows)
    return sum(1 for value, count in counts.items() if value and count > 1)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_counts(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts["|".join(str(row.get(key, "")) for key in keys)] += 1
    return dict(sorted(counts.items()))


def _quota_key(spec: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(spec["repair_source_kind"]),
        str(spec["source_role_semantics"]),
        str(spec.get("parent_surface_variant", "")) or SURFACE_RELIEF_UNSPECIFIED,
    )


def _quota_summary_rows(selected_sources: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("repair_source_kind", "")) for row in selected_sources)
    rows: list[dict[str, Any]] = []
    for kind, expected in SOURCE_KIND_QUOTAS.items():
        actual = counts.get(kind, 0)
        rows.append(
            {
                "repair_source_kind": kind,
                "expected_selected_count": int(expected),
                "actual_selected_count": int(actual),
                "quota_pass": actual == expected,
            }
        )
    return rows


def _role_surface_summary_rows(selected_sources: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    selected_counts = Counter(
        (
            str(row.get("repair_source_kind", "")),
            str(row.get("source_role_semantics", "")),
            str(row.get("normalized_surface_variant", "")),
        )
        for row in selected_sources
    )
    rows: list[dict[str, Any]] = []
    for spec in QUOTA_SPECS:
        key = _quota_key(spec)
        actual = selected_counts.get(key, 0)
        expected = int(spec["count"])
        rows.append(
            {
                "quota_name": str(spec["quota_name"]),
                "repair_source_kind": key[0],
                "source_role_semantics": key[1],
                "normalized_surface_variant": key[2],
                "expected_selected_count": expected,
                "actual_selected_count": int(actual),
                "quota_pass": actual == expected,
            }
        )
    return rows


def _claim_boundary_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim": "calibrated_source_materialization_subset",
            "supported": summary.get("result_class") == "task_quality_calibrated_materialization_selector_pass",
            "reason": "selector artifact preserves M1955 quotas and guardrails",
        },
        {
            "claim": "reset_validity",
            "supported": False,
            "reason": "M1956 does not run environment reset",
        },
        {
            "claim": "measured_execution_readiness",
            "supported": False,
            "reason": "M1956 writes source-only subset artifacts",
        },
        {
            "claim": "controller_family_ranking",
            "supported": False,
            "reason": "M1956 does not execute or compare controller profiles",
        },
        {
            "claim": "paper_level_evidence",
            "supported": False,
            "reason": "M1956 is a materialization selector milestone",
        },
        {
            "claim": "level3_self_identification",
            "supported": False,
            "reason": "M1956 does not test history necessity",
        },
    ]


def select_calibrated_materialization_sources(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return selected source rows and quota failures."""

    eligible_rows = [dict(row) for row in rows if _eligible(row)]
    used_ids: set[str] = set()
    selected: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    selection_index = 0

    for spec in QUOTA_SPECS:
        quota_name = str(spec["quota_name"])
        required = int(spec["count"])
        candidates = [
            row
            for row in eligible_rows
            if _matches_spec(row, spec) and str(row.get("candidate_source_id", "")) not in used_ids
        ]
        candidates = sorted(candidates, key=_sort_key)
        if len(candidates) < required:
            failures.append(
                {
                    "quota_name": quota_name,
                    "repair_source_kind": str(spec["repair_source_kind"]),
                    "source_role_semantics": str(spec["source_role_semantics"]),
                    "parent_surface_variant": str(spec.get("parent_surface_variant", "")),
                    "eligible_candidate_count": len(candidates),
                    "required_candidate_count": required,
                    "failure_reason": "insufficient_eligible_quota_candidates",
                }
            )
            continue
        for row in candidates[:required]:
            used_ids.add(str(row.get("candidate_source_id", "")))
            selection_index += 1
            selected.append(_selected_source(row, selection_index=selection_index, quota_name=quota_name))
    return selected, failures


def _selection_summary(
    selected_sources: list[Mapping[str, Any]],
    failures: list[Mapping[str, Any]],
    *,
    input_rows: list[Mapping[str, Any]],
    accepted_cell_rows: list[Mapping[str, Any]],
    expected_controller_profile_count: int,
) -> dict[str, Any]:
    selected_source_count = len(selected_sources)
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    source_kind_counts = Counter(str(row.get("repair_source_kind", "")) for row in selected_sources)
    role_surface_counts = Counter(
        (
            str(row.get("repair_source_kind", "")),
            str(row.get("source_role_semantics", "")),
            str(row.get("normalized_surface_variant", "")),
        )
        for row in selected_sources
    )
    calibrated_anchor_rows = [
        row
        for row in selected_sources
        if str(row.get("repair_source_kind", "")) == "anchor_neighborhood"
        and str(row.get("base_geometry_source", "")).startswith("m1950_calibrated_anchor_fallback")
    ]
    success_rows = [row for row in selected_sources if str(row.get("repair_source_kind", "")) == "success_stabilizer"]
    selected_supported_source_count = sum(str(row.get("source_support_status", "")) == "supported" for row in selected_sources)
    labels_enter_actor_input_count = sum(_bool_value(row.get("labels_enter_actor_input")) for row in selected_sources)
    ranking_default_count = sum(_bool_value(row.get("v2_ranking_admissible_by_default")) for row in selected_sources)
    profile_tuning_count = sum(_bool_value(row.get("profile_specific_tuning")) for row in selected_sources)

    source_kind_quota_pass = all(source_kind_counts.get(kind, 0) == expected for kind, expected in SOURCE_KIND_QUOTAS.items())
    role_surface_quota_pass = all(role_surface_counts.get(_quota_key(spec), 0) == int(spec["count"]) for spec in QUOTA_SPECS)
    calibrated_anchor_surface_counts = Counter(str(row.get("normalized_surface_variant", "")) for row in calibrated_anchor_rows)
    success_surface_counts = Counter(str(row.get("normalized_surface_variant", "")) for row in success_rows)
    duplicate_candidate_source_id_count = _duplicate_count(selected_sources, "candidate_source_id")
    result_passes = (
        selected_source_count == 80
        and not failures
        and source_kind_quota_pass
        and role_surface_quota_pass
        and len(calibrated_anchor_rows) == 32
        and calibrated_anchor_surface_counts.get(SURFACE_POST, 0) == 16
        and calibrated_anchor_surface_counts.get(SURFACE_STEADY, 0) == 16
        and success_surface_counts.get(SURFACE_POST, 0) == 12
        and success_surface_counts.get(SURFACE_STEADY, 0) == 12
        and selected_supported_source_count == 80
        and duplicate_candidate_source_id_count == 0
        and labels_enter_actor_input_count == 0
        and ranking_default_count == 0
        and profile_tuning_count == 0
        and guardrail_violation_count == 0
    )
    return {
        "result_class": (
            "task_quality_calibrated_materialization_selector_pass"
            if result_passes
            else "task_quality_calibrated_materialization_selector_incomplete_or_fail"
        ),
        "input_source_row_count": len(input_rows),
        "input_accepted_cell_row_count": len(accepted_cell_rows),
        "eligible_source_count": sum(_eligible(row) for row in input_rows),
        "selected_source_count": selected_source_count,
        "expected_selected_source_count": 80,
        "expected_controller_profile_count": int(expected_controller_profile_count),
        "expected_planned_workload_cell_count": int(selected_source_count * expected_controller_profile_count),
        "source_kind_quotas": SOURCE_KIND_QUOTAS,
        "selected_source_kind_counts": dict(sorted(source_kind_counts.items())),
        "selected_role_counts": _count_by(selected_sources, "source_role_semantics"),
        "selected_split_counts": _count_by(selected_sources, "source_split"),
        "selected_normalized_surface_counts": _count_by(selected_sources, "normalized_surface_variant"),
        "selected_kind_role_surface_counts": _group_counts(
            selected_sources,
            ("repair_source_kind", "source_role_semantics", "normalized_surface_variant"),
        ),
        "source_kind_quota_pass": bool(source_kind_quota_pass),
        "role_surface_quota_pass": bool(role_surface_quota_pass),
        "selection_failure_count": len(failures),
        "selected_supported_source_count": int(selected_supported_source_count),
        "calibrated_anchor_selected_count": len(calibrated_anchor_rows),
        "calibrated_anchor_post_friction_step_selected_count": int(calibrated_anchor_surface_counts.get(SURFACE_POST, 0)),
        "calibrated_anchor_steady_surface_selected_count": int(calibrated_anchor_surface_counts.get(SURFACE_STEADY, 0)),
        "success_stabilizer_selected_count": int(source_kind_counts.get("success_stabilizer", 0)),
        "success_stabilizer_post_friction_step_selected_count": int(success_surface_counts.get(SURFACE_POST, 0)),
        "success_stabilizer_steady_surface_selected_count": int(success_surface_counts.get(SURFACE_STEADY, 0)),
        "anchor_neighborhood_selected_count": int(source_kind_counts.get("anchor_neighborhood", 0)),
        "offtrack_boundary_relief_selected_count": int(source_kind_counts.get("offtrack_boundary_relief", 0)),
        "mitigation_isolation_check_selected_count": int(source_kind_counts.get("mitigation_isolation_check", 0)),
        "duplicate_candidate_source_id_count": int(duplicate_candidate_source_id_count),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_default_count),
        "profile_specific_tuning_count": int(profile_tuning_count),
        "selected_accepted_cell_count_total": int(sum(_int_value(row.get("accepted_cell_count")) for row in selected_sources)),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
        "level3_self_id_claim_made": False,
        "recommended_next_route": (
            "route_to_calibrated_materialization_preflight_command_design"
            if result_passes
            else "route_to_materialization_quota_repair_or_branch_synthesis"
        ),
    }


def materialize_calibrated_source_subset(
    *,
    repair_source_rows_path: Path | str = DEFAULT_REPAIR_SOURCE_ROWS,
    repair_accepted_cells_path: Path | str = DEFAULT_REPAIR_ACCEPTED_CELLS,
    output_config_path: Path | str = DEFAULT_OUTPUT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    expected_controller_profile_count: int = 12,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    input_rows = [dict(row) for row in read_csv_rows(repair_source_rows_path)]
    accepted_cell_rows = [dict(row) for row in read_csv_rows(repair_accepted_cells_path)]
    selected_sources, failures = select_calibrated_materialization_sources(input_rows)
    summary = _selection_summary(
        selected_sources,
        failures,
        input_rows=input_rows,
        accepted_cell_rows=accepted_cell_rows,
        expected_controller_profile_count=expected_controller_profile_count,
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_csv = output / "selected_sources.csv"
    failure_csv = output / "selection_failures.csv"
    source_kind_summary_csv = output / "source_kind_quota_summary.csv"
    role_surface_summary_csv = output / "role_surface_quota_summary.csv"
    claim_boundary_csv = output / "claim_boundary.csv"
    summary_path = output / "summary.json"

    source_kind_summary = _quota_summary_rows(selected_sources)
    role_surface_summary = _role_surface_summary_rows(selected_sources)
    claim_boundary = _claim_boundary_rows(summary)
    write_csv_rows(selected_csv, [dict(row) for row in selected_sources])
    write_csv_rows(failure_csv, [dict(row) for row in failures])
    write_csv_rows(source_kind_summary_csv, source_kind_summary)
    write_csv_rows(role_surface_summary_csv, role_surface_summary)
    write_csv_rows(claim_boundary_csv, claim_boundary)

    config = {
        "scenario_quality_branch_id": SCENARIO_QUALITY_BRANCH_ID,
        "source_support_parent_artifact": str(repair_source_rows_path),
        "accepted_cells_parent_artifact": str(repair_accepted_cells_path),
        "selected_source_count": summary["selected_source_count"],
        "expected_controller_profile_count": int(expected_controller_profile_count),
        "expected_planned_workload_cell_count": summary["expected_planned_workload_cell_count"],
        "selection_protocol_version": SELECTION_PROTOCOL_VERSION,
        "source_kind_quotas": SOURCE_KIND_QUOTAS,
        "role_surface_quotas": [dict(spec) for spec in QUOTA_SPECS],
        "selected_sources": selected_sources,
        "selection_summary": summary,
        "guardrail_flags": summary["guardrail_flags"],
    }
    write_json(output_config_path, config)
    summary.update(
        {
            "generated_at_utc": utc_timestamp(),
            "repair_source_rows_path": str(repair_source_rows_path),
            "repair_accepted_cells_path": str(repair_accepted_cells_path),
            "output_config_path": str(output_config_path),
            "selected_sources_csv": str(selected_csv),
            "selection_failures_csv": str(failure_csv),
            "source_kind_quota_summary_csv": str(source_kind_summary_csv),
            "role_surface_quota_summary_csv": str(role_surface_summary_csv),
            "claim_boundary_csv": str(claim_boundary_csv),
            "summary_path": str(summary_path),
            "next_blocker": next_blocker,
        }
    )
    write_json(summary_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-source-rows", type=Path, default=DEFAULT_REPAIR_SOURCE_ROWS)
    parser.add_argument("--repair-accepted-cells", type=Path, default=DEFAULT_REPAIR_ACCEPTED_CELLS)
    parser.add_argument("--output-config", type=Path, default=DEFAULT_OUTPUT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--expected-controller-profile-count", type=int, default=12)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = materialize_calibrated_source_subset(
        repair_source_rows_path=args.repair_source_rows,
        repair_accepted_cells_path=args.repair_accepted_cells,
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
    print(f"source_kind_quota_pass={summary['source_kind_quota_pass']}")
    print(f"role_surface_quota_pass={summary['role_surface_quota_pass']}")
    print(f"recommended_next_route={summary['recommended_next_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
