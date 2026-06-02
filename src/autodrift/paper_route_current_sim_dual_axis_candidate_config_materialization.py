"""Artifact-only materialization of bounded dual-axis candidate config packs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_CANDIDATE_DIR = Path("runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization")
DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization")
DEFAULT_NEXT_BLOCKER = "m2351-paper-route-current-sim-dual-axis-calibration-branch-synthesis"
TARGET_CANDIDATE_INPUT_COUNT = 53
TARGET_G_PRIMARY_SELECTION_COUNT = 13
TARGET_H_PRIMARY_SELECTION_COUNT = 13
TARGET_G_H_PRIMARY_SELECTION_COUNT = 26
TARGET_GH_MINIMAL_SELECTION_COUNT = 26
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"

PACK_IDS = (
    "baseline_reference_pack",
    "g_primary_pack",
    "h_primary_pack",
    "g_h_primary_pack",
    "gh_minimal_pack",
)
G_PRIORITY = {
    "timing_step_earlier": 0,
    "lateral_offset_step_toward_centerline": 1,
    "speed_step_down": 2,
    "track_width_step_up": 3,
    "radius_step_up": 4,
}

SELECTION_FIELDNAMES = [
    "pack_id",
    "scenario_spec_id",
    "candidate_id",
    "candidate_axis",
    "transform_name",
    "selection_rule",
    "selected_for_pack",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed",
]

PATCH_FIELDNAMES = [
    "pack_id",
    "scenario_spec_id",
    "candidate_id",
    "patch_resolution",
    "hidden_dynamics_bucket_before",
    "hidden_dynamics_bucket_after",
    "timing_bucket_before",
    "timing_bucket_after",
    "lateral_bucket_before",
    "lateral_bucket_after",
    "initial_speed_mps_before",
    "initial_speed_mps_after",
    "track_width_m_before",
    "track_width_m_after",
    "track_radius_m_before",
    "track_radius_m_after",
    "env_config_patch_applied",
    "metadata_only_patch",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed",
]

CLAIM_FIELDNAMES = ["claim", "allowed", "made", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _float_value(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _first_scalar_range(value: Any) -> list[float] | None:
    scalar = _float_value(value)
    if scalar is None:
        return None
    return [scalar, scalar]


def _load_config_payload(config: Path | str) -> dict[str, Any]:
    payload = read_json(config)
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return dict(payload)


def _scenario_specs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return [dict(spec) for spec in specs]


def _group_by_scenario(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scenario_spec_id", ""))].append(dict(row))
    return grouped


def _primary_g(candidates: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_scenario = _group_by_scenario(
        [
            candidate
            for candidate in candidates
            if str(candidate.get("candidate_axis", "")) == "G"
            and str(candidate.get("source_recommended_route", "")) == "geometry_timing_rebalance_candidate"
        ]
    )
    selected: dict[str, dict[str, Any]] = {}
    for scenario_id, rows in by_scenario.items():
        rows_sorted = sorted(
            rows,
            key=lambda row: (
                G_PRIORITY.get(str(row.get("transform_name", "")), 99),
                str(row.get("candidate_id", "")),
            ),
        )
        selected[scenario_id] = rows_sorted[0]
    return selected


def _primary_h(candidates: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_scenario = _group_by_scenario(
        [
            candidate
            for candidate in candidates
            if str(candidate.get("candidate_axis", "")) == "H"
            and str(candidate.get("source_recommended_route", "")) == "hidden_dynamics_range_rebalance_candidate"
        ]
    )
    return {scenario_id: sorted(rows, key=lambda row: str(row.get("candidate_id", "")))[0] for scenario_id, rows in by_scenario.items()}


def _primary_gh(candidates: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_scenario = _group_by_scenario(
        [candidate for candidate in candidates if str(candidate.get("candidate_axis", "")) == "GH"]
    )
    return {scenario_id: sorted(rows, key=lambda row: str(row.get("candidate_id", "")))[0] for scenario_id, rows in by_scenario.items()}


def build_pack_selections(candidates: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    g_primary = _primary_g(candidates)
    h_primary = _primary_h(candidates)
    gh_primary = _primary_gh(candidates)
    all_scenarios = sorted(set(g_primary) | set(h_primary))
    gh_minimal: list[dict[str, Any]] = []
    for scenario_id in all_scenarios:
        if scenario_id in gh_primary:
            row = dict(gh_primary[scenario_id])
            row["_selection_rule"] = "gh_minimal_prefer_gh_else_primary"
            gh_minimal.append(row)
        elif scenario_id in g_primary:
            row = dict(g_primary[scenario_id])
            row["_selection_rule"] = "gh_minimal_prefer_gh_else_primary"
            gh_minimal.append(row)
        elif scenario_id in h_primary:
            row = dict(h_primary[scenario_id])
            row["_selection_rule"] = "gh_minimal_prefer_gh_else_primary"
            gh_minimal.append(row)
    g_rows = []
    for row in g_primary.values():
        selected = dict(row)
        selected["_selection_rule"] = "g_primary_priority"
        g_rows.append(selected)
    h_rows = []
    for row in h_primary.values():
        selected = dict(row)
        selected["_selection_rule"] = "h_primary_unique"
        h_rows.append(selected)
    return {
        "baseline_reference_pack": [],
        "g_primary_pack": sorted(g_rows, key=lambda row: str(row.get("scenario_spec_id", ""))),
        "h_primary_pack": sorted(h_rows, key=lambda row: str(row.get("scenario_spec_id", ""))),
        "g_h_primary_pack": sorted([*g_rows, *h_rows], key=lambda row: str(row.get("scenario_spec_id", ""))),
        "gh_minimal_pack": sorted(gh_minimal, key=lambda row: str(row.get("scenario_spec_id", ""))),
    }


def selection_rows(pack_selections: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pack_id in PACK_IDS:
        for candidate in pack_selections.get(pack_id, []):
            rows.append(
                {
                    "pack_id": pack_id,
                    "scenario_spec_id": candidate.get("scenario_spec_id", ""),
                    "candidate_id": candidate.get("candidate_id", ""),
                    "candidate_axis": candidate.get("candidate_axis", ""),
                    "transform_name": candidate.get("transform_name", ""),
                    "selection_rule": candidate.get("_selection_rule", ""),
                    "selected_for_pack": True,
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "scenario_redesign_executed": False,
                }
            )
    return rows


class ReferenceIndex:
    def __init__(self, specs: Sequence[Mapping[str, Any]]) -> None:
        self.specs_by_id = {str(spec.get("scenario_spec_id", "")): dict(spec) for spec in specs}
        self.by_role_timing: dict[tuple[str, str], dict[str, Any]] = {}
        self.by_role_lateral: dict[tuple[str, str], dict[str, Any]] = {}
        self.nominal_by_role: dict[str, dict[str, Any]] = {}
        for spec in specs:
            role = str(spec.get("role_family", ""))
            timing = str(spec.get("obstacle_longitudinal_timing_bucket", ""))
            lateral = str(spec.get("obstacle_lateral_offset_bucket", ""))
            hidden = str(spec.get("hidden_dynamics_bucket", ""))
            self.by_role_timing.setdefault((role, timing), dict(spec))
            self.by_role_lateral.setdefault((role, lateral), dict(spec))
            if hidden == "nominal":
                self.nominal_by_role.setdefault(role, dict(spec))

    def timing_reference(self, role: str, timing: str) -> dict[str, Any] | None:
        return self.by_role_timing.get((role, timing))

    def lateral_reference(self, role: str, lateral: str) -> dict[str, Any] | None:
        return self.by_role_lateral.get((role, lateral))

    def nominal_reference(self, role: str) -> dict[str, Any] | None:
        return self.nominal_by_role.get(role)


def _copy_obstacle_distance(spec: dict[str, Any], reference: Mapping[str, Any] | None) -> bool:
    if reference is None:
        return False
    obstacle = spec.setdefault("env_config", {}).setdefault("obstacle", {})
    ref_obstacle = dict(reference.get("env_config", {})).get("obstacle", {})
    if isinstance(ref_obstacle, Mapping) and "distance_range" in ref_obstacle:
        obstacle["distance_range"] = list(ref_obstacle["distance_range"])
        if "obstacle_longitudinal_distance_m" in reference:
            spec["obstacle_longitudinal_distance_m"] = reference["obstacle_longitudinal_distance_m"]
        return True
    return False


def _copy_lateral_offset(spec: dict[str, Any], lateral: str, reference: Mapping[str, Any] | None) -> bool:
    obstacle = spec.setdefault("env_config", {}).setdefault("obstacle", {})
    if lateral == "centerline":
        obstacle["lateral_offset_range"] = [0.0, 0.0]
        spec["obstacle_lateral_offset_m"] = 0.0
        return True
    if reference is None:
        return False
    ref_obstacle = dict(reference.get("env_config", {})).get("obstacle", {})
    if isinstance(ref_obstacle, Mapping) and "lateral_offset_range" in ref_obstacle:
        obstacle["lateral_offset_range"] = list(ref_obstacle["lateral_offset_range"])
        if "obstacle_lateral_offset_m" in reference:
            spec["obstacle_lateral_offset_m"] = reference["obstacle_lateral_offset_m"]
        return True
    return False


def _copy_nominal_randomization(spec: dict[str, Any], reference: Mapping[str, Any] | None) -> bool:
    if reference is None:
        return False
    ref_randomization = dict(reference.get("env_config", {})).get("randomization", {})
    if not isinstance(ref_randomization, Mapping):
        return False
    spec.setdefault("env_config", {})["randomization"] = deepcopy(dict(ref_randomization))
    for key in (
        "mu_range",
        "brake_scale_range",
        "drive_tau_scale_range",
        "steer_tau_scale_range",
        "tire_stiffness_bucket",
        "front_tire_stiffness_scale_range",
        "rear_tire_stiffness_scale_range",
        "mass_scale_range",
        "inertia_scale_range",
        "friction_bucket",
        "brake_scale_bucket",
        "actuator_lag_bucket",
        "vehicle_mass_or_inertia_bucket",
    ):
        if key in reference:
            spec[key] = reference[key]
    return True


def apply_candidate_patch(
    spec: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    reference: ReferenceIndex,
    pack_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    patched = deepcopy(dict(spec))
    role = str(patched.get("role_family", ""))
    env_patch_applied = False
    metadata_only_reasons: list[str] = []

    hidden_after = str(candidate.get("hidden_dynamics_bucket_after", ""))
    timing_after = str(candidate.get("timing_bucket_after", ""))
    lateral_after = str(candidate.get("lateral_bucket_after", ""))
    speed_after = _float_value(candidate.get("initial_speed_mps_after"))
    width_after = _float_value(candidate.get("track_width_m_after"))
    radius_after = _float_value(candidate.get("track_radius_m_after"))

    if hidden_after:
        patched["hidden_dynamics_bucket"] = hidden_after
        if hidden_after == "nominal_neighbor":
            env_patch_applied = _copy_nominal_randomization(patched, reference.nominal_reference(role)) or env_patch_applied
            if not env_patch_applied:
                metadata_only_reasons.append("hidden_metadata_only")
        elif hidden_after == "same_scene_balanced_panel":
            metadata_only_reasons.append("hidden_panel_metadata_only")

    if timing_after:
        patched["obstacle_longitudinal_timing_bucket"] = timing_after
        if _copy_obstacle_distance(patched, reference.timing_reference(role, timing_after)):
            env_patch_applied = True
        elif timing_after != str(candidate.get("timing_bucket_before", "")):
            metadata_only_reasons.append("timing_metadata_only")

    if lateral_after:
        patched["obstacle_lateral_offset_bucket"] = lateral_after
        if _copy_lateral_offset(patched, lateral_after, reference.lateral_reference(role, lateral_after)):
            env_patch_applied = True
        elif lateral_after != str(candidate.get("lateral_bucket_before", "")):
            metadata_only_reasons.append("lateral_metadata_only")

    if speed_after is not None:
        patched["initial_speed_mps"] = speed_after
        patched.setdefault("env_config", {})["speed_range"] = [speed_after, speed_after]
        env_patch_applied = True

    if width_after is not None:
        patched["track_width_m"] = width_after
        patched.setdefault("env_config", {})["track_width"] = width_after
        env_patch_applied = True

    if radius_after is not None:
        patched["track_radius_m"] = radius_after
        patched.setdefault("env_config", {})["track_radius"] = radius_after
        env_patch_applied = True

    patched["diagnostic_only_no_ranking_claim"] = True
    patched["ranking_admissible"] = False
    patched["paper_level_claim_made"] = False
    patched["level3_self_id_claim_made"] = False
    patched["actor_contract_id"] = ACTOR_CONTRACT_ID

    if metadata_only_reasons and env_patch_applied:
        patch_resolution = "mixed_env_and_metadata"
    elif metadata_only_reasons:
        patch_resolution = "|".join(sorted(set(metadata_only_reasons)))
    elif env_patch_applied:
        patch_resolution = "env_config_patch"
    else:
        patch_resolution = "metadata_unchanged"

    patch_row = {
        "pack_id": pack_id,
        "scenario_spec_id": candidate.get("scenario_spec_id", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "patch_resolution": patch_resolution,
        "hidden_dynamics_bucket_before": candidate.get("hidden_dynamics_bucket_before", ""),
        "hidden_dynamics_bucket_after": hidden_after,
        "timing_bucket_before": candidate.get("timing_bucket_before", ""),
        "timing_bucket_after": timing_after,
        "lateral_bucket_before": candidate.get("lateral_bucket_before", ""),
        "lateral_bucket_after": lateral_after,
        "initial_speed_mps_before": candidate.get("initial_speed_mps_before", ""),
        "initial_speed_mps_after": candidate.get("initial_speed_mps_after", ""),
        "track_width_m_before": candidate.get("track_width_m_before", ""),
        "track_width_m_after": candidate.get("track_width_m_after", ""),
        "track_radius_m_before": candidate.get("track_radius_m_before", ""),
        "track_radius_m_after": candidate.get("track_radius_m_after", ""),
        "env_config_patch_applied": env_patch_applied,
        "metadata_only_patch": bool(metadata_only_reasons),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed": False,
    }
    return patched, patch_row


def materialize_pack_payload(
    *,
    base_payload: Mapping[str, Any],
    pack_id: str,
    selections: Sequence[Mapping[str, Any]],
    reference: ReferenceIndex,
    source_config: Path | str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = deepcopy(dict(base_payload))
    specs = _scenario_specs(payload)
    specs_by_id = {str(spec.get("scenario_spec_id", "")): spec for spec in specs}
    patch_rows: list[dict[str, Any]] = []
    for candidate in selections:
        scenario_id = str(candidate.get("scenario_spec_id", ""))
        base_spec = specs_by_id.get(scenario_id)
        if base_spec is None:
            patch_rows.append(
                {
                    "pack_id": pack_id,
                    "scenario_spec_id": scenario_id,
                    "candidate_id": candidate.get("candidate_id", ""),
                    "patch_resolution": "source_spec_missing",
                    "env_config_patch_applied": False,
                    "metadata_only_patch": True,
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "scenario_redesign_executed": False,
                }
            )
            continue
        patched, patch_row = apply_candidate_patch(base_spec, candidate, reference=reference, pack_id=pack_id)
        specs_by_id[scenario_id] = patched
        patch_rows.append(patch_row)
    payload["scenario_specs"] = [specs_by_id[str(spec.get("scenario_spec_id", ""))] for spec in specs]
    payload["config_pack_id"] = pack_id
    payload["source_config"] = str(source_config)
    payload["active_config_overwritten"] = False
    payload["scenario_redesign_executed_claim_made"] = False
    payload["diagnostic_only_no_ranking_claim"] = True
    return payload, patch_rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_candidate_config_pack_materialization",
            "allowed": True,
            "made": True,
            "reason": "M2350 only writes bounded config-pack artifacts.",
        },
        {
            "claim": "active_config_overwrite",
            "allowed": False,
            "made": False,
            "reason": "The active scenario config is read-only input.",
        },
        {
            "claim": "environment_reset_or_rollout",
            "allowed": False,
            "made": False,
            "reason": "No reset, rollout, policy action, replay, or measured execution is run.",
        },
        {
            "claim": "controller_family_ranking",
            "allowed": False,
            "made": False,
            "reason": "Config packs are artifacts, not controller comparisons.",
        },
        {
            "claim": "paper_level_evidence",
            "allowed": False,
            "made": False,
            "reason": "No validation, holdout, or controller comparison is produced.",
        },
        {
            "claim": "level3_self_identification",
            "allowed": False,
            "made": False,
            "reason": "No history intervention or self-ID test is run.",
        },
    ]


def _guardrail_violation_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(
        int(_bool_value(row.get("ranking_admissible", False)))
        + int(_bool_value(row.get("winner_selected", False)))
        + int(_bool_value(row.get("paper_level_claim_made", False)))
        + int(_bool_value(row.get("level3_self_id_claim_made", False)))
        + int(_bool_value(row.get("scenario_redesign_executed", False)))
        for row in rows
    )


def run_dual_axis_candidate_config_materialization(
    *,
    candidate_dir: Path | str = DEFAULT_CANDIDATE_DIR,
    config: Path | str = DEFAULT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_input_count: int = TARGET_CANDIDATE_INPUT_COUNT,
    target_g_primary_selection_count: int = TARGET_G_PRIMARY_SELECTION_COUNT,
    target_h_primary_selection_count: int = TARGET_H_PRIMARY_SELECTION_COUNT,
    target_g_h_primary_selection_count: int = TARGET_G_H_PRIMARY_SELECTION_COUNT,
    target_gh_minimal_selection_count: int = TARGET_GH_MINIMAL_SELECTION_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    candidate_path = Path(candidate_dir)
    config_path = Path(config)
    output = Path(output_dir)
    pack_dir = output / "config_packs"
    pack_dir.mkdir(parents=True, exist_ok=True)

    candidates = read_csv_rows(candidate_path / "calibration_candidate_rows.csv")
    base_payload = _load_config_payload(config_path)
    base_specs = _scenario_specs(base_payload)
    reference = ReferenceIndex(base_specs)
    pack_selections = build_pack_selections(candidates)
    selections = selection_rows(pack_selections)
    all_patch_rows: list[dict[str, Any]] = []
    pack_manifest_rows: list[dict[str, Any]] = []

    for pack_id in PACK_IDS:
        selected = pack_selections[pack_id]
        if pack_id == "baseline_reference_pack":
            payload = deepcopy(base_payload)
            payload["config_pack_id"] = pack_id
            payload["source_config"] = str(config_path)
            payload["active_config_overwritten"] = False
            payload["scenario_redesign_executed_claim_made"] = False
            patch_rows: list[dict[str, Any]] = []
        else:
            payload, patch_rows = materialize_pack_payload(
                base_payload=base_payload,
                pack_id=pack_id,
                selections=selected,
                reference=reference,
                source_config=config_path,
            )
        pack_path = pack_dir / f"{pack_id}.json"
        write_json(pack_path, payload)
        all_patch_rows.extend(patch_rows)
        pack_manifest_rows.append(
            {
                "pack_id": pack_id,
                "pack_path": str(pack_path),
                "selection_count": len(selected),
                "modified_pack": pack_id != "baseline_reference_pack",
                "baseline_reference_pack": pack_id == "baseline_reference_pack",
                "active_config_overwritten": False,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
                "scenario_redesign_executed": False,
            }
        )

    claims = claim_boundary_rows()
    config_pack_manifest = {
        "claim_scope": "artifact_only_candidate_config_pack_materialization",
        "active_config_overwritten": False,
        "config_pack_count": len(PACK_IDS),
        "packs": pack_manifest_rows,
    }
    write_json(output / "config_pack_manifest.json", config_pack_manifest)
    write_csv_rows(output / "candidate_selection_rows.csv", selections, fieldnames=SELECTION_FIELDNAMES)
    write_csv_rows(output / "scenario_spec_patch_rows.csv", all_patch_rows, fieldnames=PATCH_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    selection_counts = Counter(str(row.get("pack_id", "")) for row in selections)
    metadata_only_patch_count = sum(_bool_value(row.get("metadata_only_patch", False)) for row in all_patch_rows)
    env_config_patch_count = sum(_bool_value(row.get("env_config_patch_applied", False)) for row in all_patch_rows)
    unresolved_patch_count = sum("missing" in str(row.get("patch_resolution", "")) for row in all_patch_rows)
    active_config_overwritten = False
    guardrail_violation_count = (
        _guardrail_violation_count(selections)
        + _guardrail_violation_count(all_patch_rows)
        + _guardrail_violation_count(pack_manifest_rows)
        + int(active_config_overwritten)
    )
    result_passes = (
        len(candidates) == int(target_candidate_input_count)
        and len(PACK_IDS) == 5
        and sum(row["modified_pack"] for row in pack_manifest_rows) == 4
        and sum(row["baseline_reference_pack"] for row in pack_manifest_rows) == 1
        and selection_counts["g_primary_pack"] == int(target_g_primary_selection_count)
        and selection_counts["h_primary_pack"] == int(target_h_primary_selection_count)
        and selection_counts["g_h_primary_pack"] == int(target_g_h_primary_selection_count)
        and selection_counts["gh_minimal_pack"] == int(target_gh_minimal_selection_count)
        and not active_config_overwritten
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_dual_axis_candidate_config_materialization_pass"
            if result_passes
            else "current_sim_dual_axis_candidate_config_materialization_incomplete_or_fail"
        ),
        "candidate_dir": str(candidate_path),
        "config": str(config_path),
        "output_dir": str(output),
        "candidate_input_count": len(candidates),
        "target_candidate_input_count": int(target_candidate_input_count),
        "config_pack_count": len(PACK_IDS),
        "modified_config_pack_count": sum(row["modified_pack"] for row in pack_manifest_rows),
        "baseline_reference_pack_count": sum(row["baseline_reference_pack"] for row in pack_manifest_rows),
        "g_primary_selection_count": selection_counts["g_primary_pack"],
        "target_g_primary_selection_count": int(target_g_primary_selection_count),
        "h_primary_selection_count": selection_counts["h_primary_pack"],
        "target_h_primary_selection_count": int(target_h_primary_selection_count),
        "g_h_primary_selection_count": selection_counts["g_h_primary_pack"],
        "target_g_h_primary_selection_count": int(target_g_h_primary_selection_count),
        "gh_minimal_selection_count": selection_counts["gh_minimal_pack"],
        "target_gh_minimal_selection_count": int(target_gh_minimal_selection_count),
        "metadata_only_patch_count": int(metadata_only_patch_count),
        "env_config_patch_count": int(env_config_patch_count),
        "unresolved_patch_count": int(unresolved_patch_count),
        "active_config_overwritten": active_config_overwritten,
        "guardrail_violation_count": int(guardrail_violation_count),
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "support_policy_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
        "controller_comparison_ready_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "config_pack_manifest": str(output / "config_pack_manifest.json"),
            "candidate_selection_rows": str(output / "candidate_selection_rows.csv"),
            "scenario_spec_patch_rows": str(output / "scenario_spec_patch_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "config_packs_dir": str(pack_dir),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-input-count", type=int, default=TARGET_CANDIDATE_INPUT_COUNT)
    parser.add_argument("--target-g-primary-selection-count", type=int, default=TARGET_G_PRIMARY_SELECTION_COUNT)
    parser.add_argument("--target-h-primary-selection-count", type=int, default=TARGET_H_PRIMARY_SELECTION_COUNT)
    parser.add_argument("--target-g-h-primary-selection-count", type=int, default=TARGET_G_H_PRIMARY_SELECTION_COUNT)
    parser.add_argument("--target-gh-minimal-selection-count", type=int, default=TARGET_GH_MINIMAL_SELECTION_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_dual_axis_candidate_config_materialization(
        candidate_dir=args.candidate_dir,
        config=args.config,
        output_dir=args.output_dir,
        target_candidate_input_count=int(args.target_candidate_input_count),
        target_g_primary_selection_count=int(args.target_g_primary_selection_count),
        target_h_primary_selection_count=int(args.target_h_primary_selection_count),
        target_g_h_primary_selection_count=int(args.target_g_h_primary_selection_count),
        target_gh_minimal_selection_count=int(args.target_gh_minimal_selection_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_input_count={summary['candidate_input_count']}")
    print(f"config_pack_count={summary['config_pack_count']}")
    print(f"g_primary_selection_count={summary['g_primary_selection_count']}")
    print(f"h_primary_selection_count={summary['h_primary_selection_count']}")
    print(f"g_h_primary_selection_count={summary['g_h_primary_selection_count']}")
    print(f"gh_minimal_selection_count={summary['gh_minimal_selection_count']}")
    print(f"active_config_overwritten={summary['active_config_overwritten']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
