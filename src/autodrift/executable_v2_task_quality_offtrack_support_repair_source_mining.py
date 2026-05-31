"""No-rollout source-mining adapter for offtrack-support repair templates."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_support_first_source_mining import (
    ACCEPTED_CELL_FIELDS,
    PROFILE_SUPPORT_FIELDS,
    SUPPORTED,
    evaluate_candidate_cell,
    required_label_for_role,
    scan_candidate_profile,
)
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


DEFAULT_REPAIR_TEMPLATES = Path("configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json")
DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining")
DEFAULT_NEXT_BLOCKER = "m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit"
CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX = "m1950_calibrated_anchor_fallback"
SOURCE_KIND_ORDER = (
    "anchor_neighborhood",
    "success_stabilizer",
    "offtrack_boundary_relief",
    "mitigation_isolation_check",
)
SOURCE_KIND_SUPPORT_FLOORS = {
    "anchor_neighborhood": 16,
    "success_stabilizer": 16,
    "offtrack_boundary_relief": 8,
}
FALLBACK_GEOMETRY = {
    "tier_c_boundary_near_miss::stable_aeb::aeb_feasible": {
        "speed_ref": 18.0,
        "mu": 0.40,
        "obstacle_distance": 28.0,
        "obstacle_half_width": 0.80,
        "base_track_width": 5.75,
    },
    "tier_e_mitigation_only": {
        "obstacle_distance": 22.0,
        "obstacle_half_width": 1.20,
        "base_track_width": 5.25,
    },
    "default": {
        "obstacle_distance": 30.0,
        "obstacle_half_width": 0.90,
        "base_track_width": 6.00,
    },
}
SCAN_WINDOWS = {
    "anchor_neighborhood": {"distance_radius": 4.0, "distance_count": 9, "half_width_radius": 0.15, "half_width_count": 7},
    "success_stabilizer": {"distance_radius": 2.0, "distance_count": 7, "half_width_radius": 0.10, "half_width_count": 5},
    "offtrack_boundary_relief": {"distance_radius": 5.0, "distance_count": 11, "half_width_radius": 0.20, "half_width_count": 7},
    "mitigation_isolation_check": {"distance_radius": 2.0, "distance_count": 5, "half_width_radius": 0.15, "half_width_count": 5},
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
]
SOURCE_ROW_FIELDS = [
    *REPAIR_METADATA_FIELDS,
    *PROFILE_SUPPORT_FIELDS,
    "post_obstacle_track_width",
    "base_geometry_source",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
ACCEPTED_REPAIR_CELL_FIELDS = [
    *REPAIR_METADATA_FIELDS,
    *ACCEPTED_CELL_FIELDS,
    "post_obstacle_track_width",
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
RESOLUTION_FAILURE_FIELDS = ["repair_candidate_id", "repair_source_kind", "error_type", "error_message"]
AGGREGATE_FIELDS = [
    "aggregate_key",
    "candidate_count",
    "supported_source_count",
    "unsupported_source_count",
    "accepted_cell_count_total",
    "guardrail_violation_count",
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


def _fallback_geometry(row: Mapping[str, Any]) -> dict[str, float]:
    tier = str(row.get("feasibility_tier_id", ""))
    role = str(row.get("source_role_semantics", ""))
    label = str(row.get("sampled_obstacle_label", ""))
    keyed = FALLBACK_GEOMETRY.get(f"{tier}::{role}::{label}")
    if keyed is not None:
        return dict(keyed)
    base = dict(FALLBACK_GEOMETRY["tier_e_mitigation_only"] if tier == "tier_e_mitigation_only" else FALLBACK_GEOMETRY["default"])
    base["speed_ref"] = _float(row.get("speed_ref"), 18.0)
    base["mu"] = _float(row.get("mu"), 0.40)
    return base


def _calibrated_anchor_fallback_geometry(
    row: Mapping[str, Any],
    anchor_fallback_geometry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if not anchor_fallback_geometry:
        return None
    if str(row.get("repair_source_kind", "")) != "anchor_neighborhood":
        return None
    tier = str(row.get("feasibility_tier_id", ""))
    role = str(row.get("source_role_semantics", ""))
    label = str(row.get("sampled_obstacle_label", ""))
    surface = str(row.get("surface_variant", ""))
    key = f"{tier}::{role}::{label}::{surface}"
    selected = anchor_fallback_geometry.get(key)
    if selected is None:
        return None
    required = {
        "speed_ref",
        "mu",
        "obstacle_distance",
        "obstacle_half_width",
        "base_track_width",
    }
    missing = sorted(required - set(selected))
    if missing:
        raise ValueError(f"calibrated anchor fallback {key!r} is missing fields: {', '.join(missing)}")
    return {
        "base_geometry_source": f"{CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX}::{surface}",
        "speed_ref": _float(selected.get("speed_ref"), _float(row.get("speed_ref"), 18.0)),
        "mu": _float(selected.get("mu"), _float(row.get("mu"), 0.40)),
        "obstacle_distance": _float(selected.get("obstacle_distance"), 30.0),
        "obstacle_half_width": _float(selected.get("obstacle_half_width"), 0.90),
        "base_track_width": _float(selected.get("base_track_width"), 6.0),
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
                "base_geometry_source": f"m1928::{key}",
                "speed_ref": _float(spec.get("speed_ref"), _float(row.get("speed_ref"), 18.0)),
                "mu": _float(spec.get("mu"), _float(row.get("mu"), 0.40)),
                "obstacle_distance": _float(spec.get("obstacle_distance"), 30.0),
                "obstacle_half_width": _float(spec.get("obstacle_half_width"), 0.90),
                "base_track_width": _float(spec.get("track_width"), 6.0),
            }
    calibrated = _calibrated_anchor_fallback_geometry(row, anchor_fallback_geometry)
    if calibrated is not None:
        return calibrated
    fallback = _fallback_geometry(row)
    return {
        "base_geometry_source": "tier_role_surface_default",
        "speed_ref": _float(fallback.get("speed_ref"), _float(row.get("speed_ref"), 18.0)),
        "mu": _float(fallback.get("mu"), _float(row.get("mu"), 0.40)),
        "obstacle_distance": _float(fallback.get("obstacle_distance"), 30.0),
        "obstacle_half_width": _float(fallback.get("obstacle_half_width"), 0.90),
        "base_track_width": _float(fallback.get("base_track_width"), 6.0),
    }


def _role_contract_fields(role: str) -> dict[str, Any]:
    return {
        "require_aeb_infeasible": role in {ROLE_STABLE_AES, ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE},
        "recovery_horizon_required": role == ROLE_DRIFT_REQUIRED,
        "mitigation_metric_contract_present": role == ROLE_UNAVOIDABLE,
    }


def _min_accepted_cells(source_kind: str) -> int:
    if source_kind == "mitigation_isolation_check":
        return 1
    if source_kind == "success_stabilizer":
        return 2
    return 3


def template_to_source_candidate(
    row: Mapping[str, Any],
    specs_by_id: Mapping[str, Mapping[str, Any]],
    anchor_fallback_geometry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source_kind = str(row.get("repair_source_kind", ""))
    if source_kind not in SCAN_WINDOWS:
        raise ValueError(f"unknown repair_source_kind {source_kind!r}")
    geometry = resolve_base_geometry(row, specs_by_id, anchor_fallback_geometry=anchor_fallback_geometry)
    window = SCAN_WINDOWS[source_kind]
    distance_center = float(geometry["obstacle_distance"]) + _float(row.get("obstacle_distance_delta"), 0.0)
    half_width_center = max(0.10, float(geometry["obstacle_half_width"]) + _float(row.get("obstacle_half_width_delta"), 0.0))
    post_width = float(geometry["base_track_width"]) + _float(row.get("post_obstacle_track_width_delta"), 0.0)
    distance_radius = float(window["distance_radius"])
    half_width_radius = float(window["half_width_radius"])
    role = str(row.get("source_role_semantics", ""))
    surface = str(row.get("surface_variant", ""))
    return {
        **{field: row.get(field, "") for field in REPAIR_METADATA_FIELDS},
        "candidate_source_id": str(row.get("repair_candidate_id", "")),
        "source_v1_bounded_panel_spec_id": str(row.get("repair_candidate_id", "")),
        "source_scenario_spec_id": f"{row.get('repair_candidate_id', '')}_scenario",
        "source_role_semantics": role,
        "profile_name": str(row.get("parent_profile_name", row.get("repair_candidate_id", "repair_profile"))),
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
        "min_accepted_cells": _min_accepted_cells(source_kind),
        "max_threshold_score": "",
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


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "offtrack_support_repair_source_mining_completed",
            "admissible": True,
            "reason": "source mining/preflight is a no-rollout task-quality artifact",
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
            "reason": "task-quality source mining is not a controller comparison",
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


def run_offtrack_support_repair_source_mining(
    *,
    repair_templates_path: Path | str = DEFAULT_REPAIR_TEMPLATES,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    anchor_fallback_geometry_path: Path | str | None = None,
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
        except Exception as exc:  # noqa: BLE001 - adapter must preserve row-level failures.
            resolution_failures.append(
                {
                    "repair_candidate_id": str(row.get("repair_candidate_id", "")),
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
            accepted_cells.append({**_enrich(cell, candidate), "post_obstacle_track_width": candidate["post_obstacle_track_width"]})

    blocked_rows = [
        {field: row.get(field, "") for field in BLOCKED_ROW_FIELDS}
        for row in source_rows
        if str(row.get("source_support_status", "")) != SUPPORTED
    ]
    source_kind_rows = _aggregate(source_rows, "repair_source_kind")
    split_rows = _aggregate(source_rows, "source_split")
    write_csv_rows(output / "repair_source_rows.csv", source_rows, fieldnames=SOURCE_ROW_FIELDS)
    write_csv_rows(output / "repair_accepted_cells.csv", accepted_cells, fieldnames=ACCEPTED_REPAIR_CELL_FIELDS)
    write_csv_rows(output / "repair_blocked_rows.csv", blocked_rows, fieldnames=BLOCKED_ROW_FIELDS)
    write_csv_rows(output / "resolution_failure_rows.csv", resolution_failures, fieldnames=RESOLUTION_FAILURE_FIELDS)
    write_csv_rows(output / "source_kind_aggregate.csv", source_kind_rows, fieldnames=AGGREGATE_FIELDS)
    write_csv_rows(output / "split_aggregate.csv", split_rows, fieldnames=AGGREGATE_FIELDS)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_BOUNDARY_FIELDS)

    supported_source_count = sum(str(row.get("source_support_status", "")) == SUPPORTED for row in source_rows)
    public_gate_supported_source_count = sum(
        str(row.get("source_support_status", "")) == SUPPORTED and str(row.get("source_split", "")) == "public_gate"
        for row in source_rows
    )
    calibrated_anchor_fallback_rows = [
        row
        for row in source_rows
        if str(row.get("base_geometry_source", "")).startswith(CALIBRATED_ANCHOR_FALLBACK_SOURCE_PREFIX)
    ]
    calibrated_anchor_fallback_used_count = len(calibrated_anchor_fallback_rows)
    calibrated_anchor_fallback_used_by_surface = dict(
        sorted(Counter(str(row.get("parent_surface_variant", "")) for row in calibrated_anchor_fallback_rows).items())
    )
    source_kind_supported = {
        kind: sum(
            str(row.get("source_support_status", "")) == SUPPORTED and str(row.get("repair_source_kind", "")) == kind
            for row in source_rows
        )
        for kind in SOURCE_KIND_ORDER
    }
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    calibration_expected = bool(anchor_fallback_geometry)
    calibration_passes = (
        not calibration_expected
        or (
            calibrated_anchor_fallback_used_count == 64
            and calibrated_anchor_fallback_used_by_surface.get("post_friction_step", 0) == 32
            and calibrated_anchor_fallback_used_by_surface.get("steady_surface", 0) == 32
        )
    )
    result_passes = (
        len(template_rows) == 160
        and len(source_candidates) == 160
        and not resolution_failures
        and len(accepted_cells) > 0
        and supported_source_count >= 64
        and public_gate_supported_source_count >= 24
        and source_kind_supported.get("anchor_neighborhood", 0) >= 16
        and source_kind_supported.get("success_stabilizer", 0) >= 16
        and source_kind_supported.get("offtrack_boundary_relief", 0) >= 8
        and sum(1 for row in source_rows if str(row.get("repair_source_kind", "")) == "mitigation_isolation_check") == 16
        and calibration_passes
        and guardrail_violation_count == 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "repair_source_rows": str(output / "repair_source_rows.csv"),
        "repair_accepted_cells": str(output / "repair_accepted_cells.csv"),
        "repair_blocked_rows": str(output / "repair_blocked_rows.csv"),
        "resolution_failure_rows": str(output / "resolution_failure_rows.csv"),
        "source_kind_aggregate": str(output / "source_kind_aggregate.csv"),
        "split_aggregate": str(output / "split_aggregate.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    summary = {
        "result_class": (
            "task_quality_offtrack_support_repair_source_mining_pass"
            if result_passes
            else "task_quality_offtrack_support_repair_source_mining_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repair_templates_path": str(repair_templates_path),
        "executable_task_specs_path": str(executable_task_specs_path),
        "anchor_fallback_geometry_path": str(anchor_fallback_geometry_path or ""),
        "input_template_count": len(template_rows),
        "target_input_template_count": 160,
        "source_candidate_count": len(source_candidates),
        "target_source_candidate_count": 160,
        "resolution_failure_count": len(resolution_failures),
        "accepted_cell_count_total": len(accepted_cells),
        "supported_source_count": supported_source_count,
        "public_gate_supported_source_count": public_gate_supported_source_count,
        "unsupported_source_count": len(source_rows) - supported_source_count,
        "source_kind_supported_source_counts": source_kind_supported,
        "source_kind_counts": dict(sorted(Counter(str(row.get("repair_source_kind", "")) for row in source_rows).items())),
        "split_counts": dict(sorted(Counter(str(row.get("source_split", "")) for row in source_rows).items())),
        "calibrated_anchor_fallback_used_count": calibrated_anchor_fallback_used_count,
        "calibrated_anchor_fallback_used_by_surface": calibrated_anchor_fallback_used_by_surface,
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
    parser.add_argument("--anchor-fallback-geometry", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_offtrack_support_repair_source_mining(
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
