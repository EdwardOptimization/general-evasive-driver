"""No-rollout source mining for calibrated outcome-support repair templates."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_support_first_source_mining import (
    ACCEPTED_CELL_FIELDS as BASE_ACCEPTED_CELL_FIELDS,
    PROFILE_SUPPORT_FIELDS as BASE_PROFILE_SUPPORT_FIELDS,
    SUPPORTED,
    required_label_for_role,
    scan_candidate_profile,
)
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


DEFAULT_REPAIR_TEMPLATES = Path("configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json")
DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json"
)
DEFAULT_ANCHOR_FALLBACK_GEOMETRY = Path(
    "runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/"
    "selected_anchor_fallback_geometry.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining")
DEFAULT_NEXT_BLOCKER = "m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit"
CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX = "m1950_calibrated_anchor_fallback"

AXIS_ORDER = (
    "offtrack_anchor_relief",
    "offtrack_boundary_relief_extension",
    "success_support_expansion",
    "collision_mitigation_relief",
    "mitigation_metric_isolation",
)
AXIS_TARGET_COUNTS = {
    "offtrack_anchor_relief": 64,
    "offtrack_boundary_relief_extension": 32,
    "success_support_expansion": 48,
    "collision_mitigation_relief": 32,
    "mitigation_metric_isolation": 16,
}
AXIS_SUPPORT_FLOORS = {
    "offtrack_anchor_relief": 32,
    "offtrack_boundary_relief_extension": 8,
    "success_support_expansion": 24,
    "collision_mitigation_relief": 8,
}
AXIS_SCAN_WINDOWS = {
    "offtrack_anchor_relief": {
        "distance_radius": 4.0,
        "distance_count": 9,
        "half_width_radius": 0.15,
        "half_width_count": 7,
        "min_accepted_cells": 3,
    },
    "offtrack_boundary_relief_extension": {
        "distance_radius": 5.0,
        "distance_count": 11,
        "half_width_radius": 0.20,
        "half_width_count": 7,
        "min_accepted_cells": 3,
    },
    "success_support_expansion": {
        "distance_radius": 2.0,
        "distance_count": 7,
        "half_width_radius": 0.10,
        "half_width_count": 5,
        "min_accepted_cells": 2,
    },
    "collision_mitigation_relief": {
        "distance_radius": 2.0,
        "distance_count": 5,
        "half_width_radius": 0.15,
        "half_width_count": 5,
        "min_accepted_cells": 1,
    },
    "mitigation_metric_isolation": {
        "distance_radius": 1.0,
        "distance_count": 3,
        "half_width_radius": 0.05,
        "half_width_count": 3,
        "min_accepted_cells": 1,
    },
}
ROLE_FALLBACK_GEOMETRY = {
    ROLE_STABLE_AEB: {
        "obstacle_distance": 52.0,
        "obstacle_half_width": 0.75,
        "base_track_width": 5.75,
    },
    ROLE_STABLE_AES: {
        "obstacle_distance": 30.0,
        "obstacle_half_width": 0.80,
        "base_track_width": 6.0,
    },
    ROLE_DRIFT_REQUIRED: {
        "obstacle_distance": 22.0,
        "obstacle_half_width": 0.80,
        "base_track_width": 6.0,
    },
    ROLE_UNAVOIDABLE: {
        "obstacle_distance": 10.0,
        "obstacle_half_width": 1.30,
        "base_track_width": 6.0,
    },
}
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
REPAIR_METADATA_FIELDS = [
    "repair_candidate_id",
    "repair_axis",
    "repair_source_kind",
    "repair_source_family",
    "source_split",
    "recovery_corridor_profile",
    "mitigation_metric_mode",
    "parent_candidate_source_id",
    "parent_task_source_id",
    "parent_profile_name",
    "parent_repair_source_kind",
    "parent_selection_quota_name",
    "parent_feasibility_tier_id",
    "parent_source_role_semantics",
    "parent_surface_variant",
    "parent_normalized_surface_variant",
    "parent_sampled_obstacle_label",
    "parent_base_geometry_source",
    "parent_outcome_bucket",
    "parent_termination_reason",
    "target_feasibility_tier_id",
    "target_source_role_semantics",
    "target_surface_variant",
    "target_normalized_surface_variant",
    "target_sampled_obstacle_label",
]
SOURCE_ROW_FIELDS = [
    *REPAIR_METADATA_FIELDS,
    *BASE_PROFILE_SUPPORT_FIELDS,
    "feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "post_obstacle_track_width",
    "base_geometry_source",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
ACCEPTED_CELL_FIELDS = [
    *REPAIR_METADATA_FIELDS,
    *BASE_ACCEPTED_CELL_FIELDS,
    "feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "post_obstacle_track_width",
    "base_geometry_source",
]
BLOCKED_ROW_FIELDS = [
    *REPAIR_METADATA_FIELDS,
    "candidate_source_id",
    "source_role_semantics",
    "source_support_status",
    "source_support_failure_reason",
    "accepted_cell_count",
    "min_accepted_cells",
    "dominant_label",
    "dominant_reject_reason",
]
RESOLUTION_FAILURE_FIELDS = ["repair_candidate_id", "repair_axis", "repair_source_kind", "error_type", "error_message"]
AGGREGATE_FIELDS = [
    "aggregate_key",
    "candidate_count",
    "supported_source_count",
    "unsupported_source_count",
    "accepted_cell_count_total",
    "guardrail_violation_count",
]
ROLE_SURFACE_AGGREGATE_FIELDS = [
    "source_role_semantics",
    "feasibility_tier_id",
    "normalized_surface_variant",
    "sampled_obstacle_label",
    "candidate_count",
    "supported_source_count",
    "accepted_cell_count_total",
]
CLAIM_BOUNDARY_FIELDS = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _load_templates(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("repair_candidate_sources")
    if not isinstance(rows, list):
        raise ValueError("repair template artifact must contain repair_candidate_sources")
    return [dict(row) for row in rows]


def _load_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("executable task specs must contain executable_task_specs")
    return [dict(row) for row in rows]


def _load_anchor_fallback_geometry(path: Path | str | None) -> dict[str, dict[str, Any]]:
    if path is None or str(path).strip() == "":
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("anchor fallback geometry artifact must be a JSON object")
    output: dict[str, dict[str, Any]] = {}
    for key, value in payload.items():
        if not isinstance(value, dict):
            raise ValueError(f"anchor fallback geometry entry {key!r} must be an object")
        output[str(key)] = dict(value)
    return output


def _spec_lookup(specs: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    lookup: dict[str, Mapping[str, Any]] = {}
    for spec in specs:
        for key in ("task_source_id", "candidate_source_id", "source_v1_bounded_panel_spec_id", "source_scenario_spec_id"):
            value = str(spec.get(key, "")).strip()
            if value:
                lookup[value] = spec
    return lookup


def normalize_template_row(row: Mapping[str, Any]) -> dict[str, Any]:
    role = str(row.get("target_source_role_semantics", ""))
    tier = str(row.get("target_feasibility_tier_id", ""))
    surface = str(row.get("target_surface_variant", row.get("target_normalized_surface_variant", "")))
    normalized_surface = str(row.get("target_normalized_surface_variant", surface))
    sampled_label = str(row.get("target_sampled_obstacle_label", ""))
    normalized = dict(row)
    normalized.update(
        {
            "source_role_semantics": role,
            "feasibility_tier_id": tier,
            "surface_variant": surface,
            "normalized_surface_variant": normalized_surface,
            "sampled_obstacle_label": sampled_label,
        }
    )
    return normalized


def _calibrated_anchor_fallback_geometry(
    row: Mapping[str, Any],
    anchor_fallback_geometry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if not anchor_fallback_geometry:
        return None
    if str(row.get("repair_axis", "")) != "offtrack_anchor_relief":
        return None
    if str(row.get("source_role_semantics", "")) != ROLE_STABLE_AEB:
        return None
    tier = str(row.get("feasibility_tier_id", ""))
    role = str(row.get("source_role_semantics", ""))
    label = str(row.get("sampled_obstacle_label", ""))
    surface = str(row.get("surface_variant", ""))
    key = f"{tier}::{role}::{label}::{surface}"
    selected = anchor_fallback_geometry.get(key)
    if selected is None:
        return None
    required = {"speed_ref", "mu", "obstacle_distance", "obstacle_half_width", "base_track_width"}
    missing = sorted(required - set(selected))
    if missing:
        raise ValueError(f"calibrated anchor fallback {key!r} is missing fields: {', '.join(missing)}")
    return {
        "base_geometry_source": f"{CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX}::{surface}",
        "speed_ref": _float(selected.get("speed_ref"), _float(row.get("speed_ref"), 18.0)),
        "mu": _float(selected.get("mu"), _float(row.get("mu"), 0.40)),
        "obstacle_distance": _float(selected.get("obstacle_distance"), 52.0),
        "obstacle_half_width": _float(selected.get("obstacle_half_width"), 0.75),
        "base_track_width": _float(selected.get("base_track_width"), 5.75),
    }


def _fallback_geometry(row: Mapping[str, Any]) -> dict[str, Any]:
    role = str(row.get("source_role_semantics", ""))
    fallback = dict(ROLE_FALLBACK_GEOMETRY.get(role, ROLE_FALLBACK_GEOMETRY[ROLE_STABLE_AES]))
    return {
        "base_geometry_source": f"axis_role_fallback::{str(row.get('repair_axis', ''))}::{role}",
        "speed_ref": _float(row.get("speed_ref"), 18.0),
        "mu": _float(row.get("mu"), 0.40),
        "obstacle_distance": _float(fallback.get("obstacle_distance"), 30.0),
        "obstacle_half_width": _float(fallback.get("obstacle_half_width"), 0.80),
        "base_track_width": _float(fallback.get("base_track_width"), 6.0),
    }


def resolve_base_geometry(
    row: Mapping[str, Any],
    specs_by_id: Mapping[str, Mapping[str, Any]],
    anchor_fallback_geometry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    for key in ("parent_task_source_id", "parent_candidate_source_id"):
        value = str(row.get(key, "")).strip()
        spec = specs_by_id.get(value)
        if spec is not None:
            return {
                "base_geometry_source": f"m1969::{key}",
                "speed_ref": _float(spec.get("speed_ref"), _float(row.get("speed_ref"), 18.0)),
                "mu": _float(spec.get("mu"), _float(row.get("mu"), 0.40)),
                "obstacle_distance": _float(spec.get("obstacle_distance"), 30.0),
                "obstacle_half_width": _float(spec.get("obstacle_half_width"), 0.90),
                "base_track_width": _float(spec.get("track_width"), 6.0),
            }
    calibrated = _calibrated_anchor_fallback_geometry(row, anchor_fallback_geometry)
    if calibrated is not None:
        return calibrated
    return _fallback_geometry(row)


def _role_contract_fields(role: str) -> dict[str, Any]:
    return {
        "require_aeb_infeasible": role in {ROLE_STABLE_AES, ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE},
        "recovery_horizon_required": role == ROLE_DRIFT_REQUIRED,
        "mitigation_metric_contract_present": role == ROLE_UNAVOIDABLE,
    }


def template_to_source_candidate(
    row: Mapping[str, Any],
    specs_by_id: Mapping[str, Mapping[str, Any]],
    anchor_fallback_geometry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized = normalize_template_row(row)
    axis = str(normalized.get("repair_axis", ""))
    if axis not in AXIS_SCAN_WINDOWS:
        raise ValueError(f"unknown repair_axis {axis!r}")
    geometry = resolve_base_geometry(normalized, specs_by_id, anchor_fallback_geometry=anchor_fallback_geometry)
    window = AXIS_SCAN_WINDOWS[axis]
    distance_center = float(geometry["obstacle_distance"]) + _float(normalized.get("obstacle_distance_delta"), 0.0)
    half_width_center = max(0.10, float(geometry["obstacle_half_width"]) + _float(normalized.get("obstacle_half_width_delta"), 0.0))
    post_width = float(geometry["base_track_width"]) + _float(normalized.get("post_obstacle_track_width_delta"), 0.0)
    role = str(normalized.get("source_role_semantics", ""))
    surface = str(normalized.get("surface_variant", ""))
    distance_radius = float(window["distance_radius"])
    half_width_radius = float(window["half_width_radius"])
    return {
        **{field: normalized.get(field, "") for field in REPAIR_METADATA_FIELDS},
        "candidate_source_id": str(normalized.get("repair_candidate_id", "")),
        "source_v1_bounded_panel_spec_id": str(normalized.get("repair_candidate_id", "")),
        "source_scenario_spec_id": f"{normalized.get('repair_candidate_id', '')}_scenario",
        "source_role_semantics": role,
        "profile_name": str(normalized.get("parent_profile_name", normalized.get("repair_candidate_id", "repair_profile"))),
        "profile_group": role,
        "speed_ref": float(geometry["speed_ref"]),
        "mu": float(geometry["mu"]),
        "friction_step_enabled": surface == "post_friction_step",
        "friction_step_at": 20 if surface == "post_friction_step" else "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.30 if surface == "post_friction_step" else 0.0,
        "obstacle_distance_min": max(1.0, distance_center - distance_radius),
        "obstacle_distance_max": max(1.0, distance_center + distance_radius),
        "obstacle_distance_count": int(window["distance_count"]),
        "obstacle_half_width_min": max(0.10, half_width_center - half_width_radius),
        "obstacle_half_width_max": max(0.10, half_width_center + half_width_radius),
        "obstacle_half_width_count": int(window["half_width_count"]),
        "min_accepted_cells": int(window["min_accepted_cells"]),
        "max_threshold_score": "",
        "feasibility_tier_id": str(normalized.get("feasibility_tier_id", "")),
        "normalized_surface_variant": str(normalized.get("normalized_surface_variant", "")),
        "sampled_obstacle_label": str(normalized.get("sampled_obstacle_label", "")),
        "post_obstacle_track_width": post_width,
        "base_geometry_source": geometry["base_geometry_source"],
        "source_required_label": required_label_for_role(role),
        "source_allowed_labels": required_label_for_role(role),
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        **_role_contract_fields(role),
    }


def _enrich(row: Mapping[str, Any], metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {**{field: metadata.get(field, "") for field in REPAIR_METADATA_FIELDS}, **dict(row)}


def _aggregate(rows: list[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    output: list[dict[str, Any]] = []
    for group, items in sorted(groups.items()):
        output.append(
            {
                "aggregate_key": group,
                "candidate_count": len(items),
                "supported_source_count": sum(str(row.get("source_support_status", "")) == SUPPORTED for row in items),
                "unsupported_source_count": sum(str(row.get("source_support_status", "")) != SUPPORTED for row in items),
                "accepted_cell_count_total": sum(int(float(row.get("accepted_cell_count", 0) or 0)) for row in items),
                "guardrail_violation_count": sum(
                    1
                    for row in items
                    if _bool(row.get("labels_enter_actor_input"))
                    or _bool(row.get("v2_ranking_admissible_by_default"))
                    or _bool(row.get("profile_specific_tuning"))
                ),
            }
        )
    return output


def _role_surface_aggregate(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                str(row.get("source_role_semantics", "")),
                str(row.get("feasibility_tier_id", "")),
                str(row.get("normalized_surface_variant", "")),
                str(row.get("sampled_obstacle_label", "")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (role, tier, surface, label), items in sorted(groups.items()):
        output.append(
            {
                "source_role_semantics": role,
                "feasibility_tier_id": tier,
                "normalized_surface_variant": surface,
                "sampled_obstacle_label": label,
                "candidate_count": len(items),
                "supported_source_count": sum(str(row.get("source_support_status", "")) == SUPPORTED for row in items),
                "accepted_cell_count_total": sum(int(float(row.get("accepted_cell_count", 0) or 0)) for row in items),
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "calibrated_outcome_support_source_mining_completed",
            "admissible": True,
            "reason": "source mining is a no-rollout task-quality artifact",
        },
        {
            "claim": "reset_validity",
            "admissible": False,
            "reason": "source mining does not reset environments",
        },
        {
            "claim": "measured_execution_readiness",
            "admissible": False,
            "reason": "source mining must be audited before materialization and reset validation",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "source mining is not a controller comparison",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "source mining is not paper-level evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "source mining does not test history necessity",
        },
    ]


def run_outcome_support_source_mining(
    *,
    repair_templates_path: Path | str = DEFAULT_REPAIR_TEMPLATES,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    anchor_fallback_geometry_path: Path | str | None = DEFAULT_ANCHOR_FALLBACK_GEOMETRY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    template_rows = _load_templates(repair_templates_path)
    specs_by_id = _spec_lookup(_load_specs(executable_task_specs_path))
    anchor_fallback_geometry = _load_anchor_fallback_geometry(anchor_fallback_geometry_path)

    source_candidates: list[dict[str, Any]] = []
    resolution_failures: list[dict[str, Any]] = []
    for row in template_rows:
        try:
            source_candidates.append(
                template_to_source_candidate(row, specs_by_id, anchor_fallback_geometry=anchor_fallback_geometry)
            )
        except Exception as exc:  # noqa: BLE001 - source mining should preserve row-level failures.
            resolution_failures.append(
                {
                    "repair_candidate_id": str(row.get("repair_candidate_id", "")),
                    "repair_axis": str(row.get("repair_axis", "")),
                    "repair_source_kind": str(row.get("repair_source_kind", "")),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )

    source_rows: list[dict[str, Any]] = []
    accepted_cells: list[dict[str, Any]] = []
    for candidate in source_candidates:
        scanned = scan_candidate_profile(candidate=candidate)
        support_row = _enrich(scanned["profile_support"], candidate)
        support_row.update(
            {
                "feasibility_tier_id": candidate.get("feasibility_tier_id", ""),
                "normalized_surface_variant": candidate.get("normalized_surface_variant", ""),
                "sampled_obstacle_label": candidate.get("sampled_obstacle_label", ""),
                "post_obstacle_track_width": candidate.get("post_obstacle_track_width", ""),
                "base_geometry_source": candidate.get("base_geometry_source", ""),
                "labels_enter_actor_input": False,
                "v2_ranking_admissible_by_default": False,
                "profile_specific_tuning": False,
                "controller_family_ranking_claim_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
        source_rows.append(support_row)
        for cell in scanned["accepted_cells"]:
            accepted_cells.append(
                {
                    **_enrich(cell, candidate),
                    "feasibility_tier_id": candidate.get("feasibility_tier_id", ""),
                    "normalized_surface_variant": candidate.get("normalized_surface_variant", ""),
                    "sampled_obstacle_label": candidate.get("sampled_obstacle_label", ""),
                    "post_obstacle_track_width": candidate.get("post_obstacle_track_width", ""),
                    "base_geometry_source": candidate.get("base_geometry_source", ""),
                }
            )

    blocked_rows = [
        {field: row.get(field, "") for field in BLOCKED_ROW_FIELDS}
        for row in source_rows
        if str(row.get("source_support_status", "")) != SUPPORTED
    ]
    repair_axis_rows = _aggregate(source_rows, "repair_axis")
    split_rows = _aggregate(source_rows, "source_split")
    role_surface_rows = _role_surface_aggregate(source_rows)
    write_csv_rows(output / "outcome_support_source_rows.csv", source_rows, fieldnames=SOURCE_ROW_FIELDS)
    write_csv_rows(output / "outcome_support_accepted_cells.csv", accepted_cells, fieldnames=ACCEPTED_CELL_FIELDS)
    write_csv_rows(output / "outcome_support_blocked_rows.csv", blocked_rows, fieldnames=BLOCKED_ROW_FIELDS)
    write_csv_rows(output / "resolution_failure_rows.csv", resolution_failures, fieldnames=RESOLUTION_FAILURE_FIELDS)
    write_csv_rows(output / "repair_axis_aggregate.csv", repair_axis_rows, fieldnames=AGGREGATE_FIELDS)
    write_csv_rows(output / "split_aggregate.csv", split_rows, fieldnames=AGGREGATE_FIELDS)
    write_csv_rows(output / "role_surface_aggregate.csv", role_surface_rows, fieldnames=ROLE_SURFACE_AGGREGATE_FIELDS)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_BOUNDARY_FIELDS)

    supported_source_count = sum(str(row.get("source_support_status", "")) == SUPPORTED for row in source_rows)
    public_gate_supported_source_count = sum(
        str(row.get("source_support_status", "")) == SUPPORTED and str(row.get("source_split", "")) == "public_gate"
        for row in source_rows
    )
    axis_counts = dict(sorted(Counter(str(row.get("repair_axis", "")) for row in source_rows).items()))
    axis_supported = {
        axis: sum(
            str(row.get("source_support_status", "")) == SUPPORTED and str(row.get("repair_axis", "")) == axis
            for row in source_rows
        )
        for axis in AXIS_ORDER
    }
    geometry_source_counts = dict(sorted(Counter(str(row.get("base_geometry_source", "")) for row in source_rows).items()))
    calibrated_anchor_fallback_rows = [
        row
        for row in source_rows
        if str(row.get("base_geometry_source", "")).startswith(CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX)
    ]
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    axis_support_passes = all(axis_supported.get(axis, 0) >= floor for axis, floor in AXIS_SUPPORT_FLOORS.items())
    axis_count_passes = all(int(axis_counts.get(axis, 0)) == int(count) for axis, count in AXIS_TARGET_COUNTS.items())
    result_passes = (
        len(template_rows) == 192
        and len(source_candidates) == 192
        and not resolution_failures
        and len(accepted_cells) > 0
        and supported_source_count >= 96
        and public_gate_supported_source_count >= 32
        and axis_count_passes
        and axis_support_passes
        and axis_counts.get("mitigation_metric_isolation", 0) == 16
        and guardrail_violation_count == 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "outcome_support_source_rows": str(output / "outcome_support_source_rows.csv"),
        "outcome_support_accepted_cells": str(output / "outcome_support_accepted_cells.csv"),
        "outcome_support_blocked_rows": str(output / "outcome_support_blocked_rows.csv"),
        "resolution_failure_rows": str(output / "resolution_failure_rows.csv"),
        "repair_axis_aggregate": str(output / "repair_axis_aggregate.csv"),
        "split_aggregate": str(output / "split_aggregate.csv"),
        "role_surface_aggregate": str(output / "role_surface_aggregate.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    summary = {
        "result_class": (
            "task_quality_calibrated_outcome_support_source_mining_pass"
            if result_passes
            else "task_quality_calibrated_outcome_support_source_mining_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repair_templates_path": str(repair_templates_path),
        "executable_task_specs_path": str(executable_task_specs_path),
        "anchor_fallback_geometry_path": str(anchor_fallback_geometry_path or ""),
        "input_template_count": len(template_rows),
        "target_input_template_count": 192,
        "source_candidate_count": len(source_candidates),
        "target_source_candidate_count": 192,
        "resolution_failure_count": len(resolution_failures),
        "accepted_cell_count_total": len(accepted_cells),
        "supported_source_count": supported_source_count,
        "public_gate_supported_source_count": public_gate_supported_source_count,
        "unsupported_source_count": len(source_rows) - supported_source_count,
        "repair_axis_counts": axis_counts,
        "target_repair_axis_counts": AXIS_TARGET_COUNTS,
        "repair_axis_supported_source_counts": axis_supported,
        "repair_axis_support_floors": AXIS_SUPPORT_FLOORS,
        "repair_axis_count_passes": axis_count_passes,
        "repair_axis_support_passes": axis_support_passes,
        "source_split_counts": dict(sorted(Counter(str(row.get("source_split", "")) for row in source_rows).items())),
        "geometry_source_counts": geometry_source_counts,
        "calibrated_anchor_fallback_used_count": len(calibrated_anchor_fallback_rows),
        "labels_enter_actor_input_count": 0,
        "v2_ranking_admissible_by_default_count": 0,
        "profile_specific_tuning_count": 0,
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
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-templates", type=Path, default=DEFAULT_REPAIR_TEMPLATES)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--anchor-fallback-geometry", type=Path, default=DEFAULT_ANCHOR_FALLBACK_GEOMETRY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_outcome_support_source_mining(
        repair_templates_path=args.repair_templates,
        executable_task_specs_path=args.executable_task_specs,
        anchor_fallback_geometry_path=args.anchor_fallback_geometry,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_template_count={summary['input_template_count']}")
    print(f"source_candidate_count={summary['source_candidate_count']}")
    print(f"supported_source_count={summary['supported_source_count']}")
    print(f"public_gate_supported_source_count={summary['public_gate_supported_source_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
