"""Deterministic candidate templates for task-quality scenario redesign."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import utc_timestamp, write_json
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


TEMPLATE_ID = "task_quality_scenario_redesign_candidates_v0"
DEFAULT_OUTPUT_PATH = Path("configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json")
SCENARIO_QUALITY_BRANCH_ID = "paper_route_task_quality_scenario_redesign"
SPEEDS = (12.0, 18.0, 24.0, 30.0)
MU_VALUES = (0.25, 0.40, 0.60, 0.80)
SOURCE_SPLITS = ("public_debug", "public_gate", "paper_holdout_candidate")
SPLIT_PATTERN = (
    "public_debug",
    "public_debug",
    "public_debug",
    "public_debug",
    "public_debug",
    "public_debug",
    "public_gate",
    "public_gate",
    "public_gate",
    "paper_holdout_candidate",
)
SURFACES = (
    {
        "surface_variant": "steady_surface",
        "source_family_id": "steady_surface",
        "friction_step_enabled": False,
        "friction_step_at": "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.0,
    },
    {
        "surface_variant": "post_friction_step",
        "source_family_id": "post_friction_step",
        "friction_step_enabled": True,
        "friction_step_at": 20,
        "dt": 0.05,
        "min_time_after_friction_step": 0.30,
    },
)
ROLE_SETTINGS: dict[str, dict[str, Any]] = {
    ROLE_STABLE_AEB: {
        "source_required_label": "aeb_feasible",
        "source_allowed_labels": "aeb_feasible",
        "require_aeb_infeasible": False,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": False,
    },
    ROLE_STABLE_AES: {
        "source_required_label": "aes_feasible",
        "source_allowed_labels": "aes_feasible",
        "require_aeb_infeasible": True,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": False,
    },
    ROLE_DRIFT_REQUIRED: {
        "source_required_label": "drift_required",
        "source_allowed_labels": "drift_required",
        "require_aeb_infeasible": True,
        "recovery_horizon_required": True,
        "mitigation_metric_contract_present": False,
    },
    ROLE_UNAVOIDABLE: {
        "source_required_label": "unavoidable",
        "source_allowed_labels": "unavoidable",
        "require_aeb_infeasible": True,
        "recovery_horizon_required": False,
        "mitigation_metric_contract_present": True,
    },
}
TIER_SETTINGS: tuple[dict[str, Any], ...] = (
    {
        "feasibility_tier_id": "tier_a_positive_support_sanity",
        "target_support_mode": "joint_positive_support",
        "target_boundary_mode": "benign",
        "road_corridor_profile": "wide_sanity",
        "pre_obstacle_track_width": 7.5,
        "post_obstacle_track_width": 7.5,
        "obstacle_lateral_profile": "centered_low_width",
        "reaction_distance_profile": "long",
        "obstacle_distance_min": 22.0,
        "obstacle_distance_max": 90.0,
        "obstacle_distance_count": 35,
        "obstacle_half_width_min": 0.15,
        "obstacle_half_width_max": 0.80,
        "obstacle_half_width_count": 14,
        "max_threshold_score": "",
        "expected_joint_support": True,
        "expected_near_miss_support": False,
        "mitigation_only": False,
        "positive_support_gate_required": True,
    },
    {
        "feasibility_tier_id": "tier_b_feasible_emergency",
        "target_support_mode": "joint_positive_support",
        "target_boundary_mode": "feasible_emergency",
        "road_corridor_profile": "normal_plus_recovery",
        "pre_obstacle_track_width": 6.25,
        "post_obstacle_track_width": 6.25,
        "obstacle_lateral_profile": "moderate_offset",
        "reaction_distance_profile": "medium",
        "obstacle_distance_min": 14.0,
        "obstacle_distance_max": 70.0,
        "obstacle_distance_count": 29,
        "obstacle_half_width_min": 0.25,
        "obstacle_half_width_max": 1.10,
        "obstacle_half_width_count": 18,
        "max_threshold_score": "",
        "expected_joint_support": True,
        "expected_near_miss_support": True,
        "mitigation_only": False,
        "positive_support_gate_required": True,
    },
    {
        "feasibility_tier_id": "tier_c_boundary_near_miss",
        "target_support_mode": "boundary_mixed_support",
        "target_boundary_mode": "near_miss",
        "road_corridor_profile": "bounded_recovery",
        "pre_obstacle_track_width": 5.5,
        "post_obstacle_track_width": 5.75,
        "obstacle_lateral_profile": "boundary_offset",
        "reaction_distance_profile": "short_medium",
        "obstacle_distance_min": 8.0,
        "obstacle_distance_max": 55.0,
        "obstacle_distance_count": 25,
        "obstacle_half_width_min": 0.45,
        "obstacle_half_width_max": 1.40,
        "obstacle_half_width_count": 20,
        "max_threshold_score": 0.30,
        "expected_joint_support": True,
        "expected_near_miss_support": True,
        "mitigation_only": False,
        "positive_support_gate_required": True,
    },
    {
        "feasibility_tier_id": "tier_d_handling_limit_drift_required",
        "target_support_mode": "sparse_extreme_support",
        "target_boundary_mode": "handling_limit",
        "road_corridor_profile": "narrow_recovery",
        "pre_obstacle_track_width": 5.0,
        "post_obstacle_track_width": 5.25,
        "obstacle_lateral_profile": "wide_boundary_offset",
        "reaction_distance_profile": "short",
        "obstacle_distance_min": 5.0,
        "obstacle_distance_max": 45.0,
        "obstacle_distance_count": 21,
        "obstacle_half_width_min": 0.70,
        "obstacle_half_width_max": 1.65,
        "obstacle_half_width_count": 20,
        "max_threshold_score": 0.22,
        "expected_joint_support": True,
        "expected_near_miss_support": True,
        "mitigation_only": False,
        "positive_support_gate_required": True,
    },
    {
        "feasibility_tier_id": "tier_e_mitigation_only",
        "target_support_mode": "mitigation_only",
        "target_boundary_mode": "unavoidable_or_near_unavoidable",
        "road_corridor_profile": "mitigation_diagnostic",
        "pre_obstacle_track_width": 5.0,
        "post_obstacle_track_width": 5.0,
        "obstacle_lateral_profile": "blocked_path",
        "reaction_distance_profile": "very_short",
        "obstacle_distance_min": 2.0,
        "obstacle_distance_max": 35.0,
        "obstacle_distance_count": 18,
        "obstacle_half_width_min": 1.00,
        "obstacle_half_width_max": 2.10,
        "obstacle_half_width_count": 23,
        "max_threshold_score": "",
        "expected_joint_support": False,
        "expected_near_miss_support": True,
        "mitigation_only": True,
        "positive_support_gate_required": False,
    },
)


def _tag_float(prefix: str, value: float) -> str:
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return prefix + text.replace(".", "p")


def _profile_control_hash(row: Mapping[str, Any]) -> str:
    keys = [
        "template_id",
        "scenario_quality_branch_id",
        "feasibility_tier_id",
        "source_role_semantics",
        "speed_ref",
        "mu",
        "surface_variant",
        "friction_step_enabled",
        "friction_step_at",
        "obstacle_distance_min",
        "obstacle_distance_max",
        "obstacle_distance_count",
        "obstacle_half_width_min",
        "obstacle_half_width_max",
        "obstacle_half_width_count",
        "road_corridor_profile",
        "obstacle_lateral_profile",
        "reaction_distance_profile",
    ]
    payload = {key: row.get(key, "") for key in keys}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _candidate_row(
    *,
    index: int,
    tier: Mapping[str, Any],
    role: str,
    surface: Mapping[str, Any],
    speed: float,
    mu: float,
) -> dict[str, Any]:
    tier_id = str(tier["feasibility_tier_id"])
    speed_tag = _tag_float("v", speed)
    mu_tag = _tag_float("mu", mu)
    role_tag = role.replace("_", "-")
    source_id = f"tqsr_v0_{tier_id}_{role_tag}_{surface['surface_variant']}_{speed_tag}_{mu_tag}"
    source_split = SPLIT_PATTERN[index % len(SPLIT_PATTERN)]
    role_settings = dict(ROLE_SETTINGS[role])
    mitigation_only = bool(tier["mitigation_only"]) or role == ROLE_UNAVOIDABLE
    row: dict[str, Any] = {
        "template_id": TEMPLATE_ID,
        "scenario_quality_branch_id": SCENARIO_QUALITY_BRANCH_ID,
        "candidate_source_id": source_id,
        "source_v1_bounded_panel_spec_id": source_id,
        "source_scenario_spec_id": f"{source_id}_scenario",
        "source_family_id": surface["source_family_id"],
        "surface_variant": surface["surface_variant"],
        "source_role_semantics": role,
        "profile_name": f"{tier_id}_{role}_{surface['surface_variant']}_grid_v0",
        "profile_group": role,
        "speed_ref": float(speed),
        "mu": float(mu),
        "source_split": source_split,
        "paper_holdout_candidate": source_split == "paper_holdout_candidate",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "ego_half_width": 0.90,
        "safety_margin": 0.30,
        "brake_mu_fraction": 0.90,
        "conventional_lateral_mu_fraction": 0.42,
        "drift_lateral_mu_fraction": 0.85,
        "gravity": 9.81,
        "mitigation_only": mitigation_only,
        **surface,
        **tier,
        **role_settings,
    }
    row["profile_control_hash"] = _profile_control_hash(row)
    return row


def generate_v0_candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for tier in TIER_SETTINGS:
        for role in (ROLE_STABLE_AEB, ROLE_STABLE_AES, ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE):
            for surface in SURFACES:
                for speed in SPEEDS:
                    for mu in MU_VALUES:
                        rows.append(
                            _candidate_row(
                                index=index,
                                tier=tier,
                                role=role,
                                surface=surface,
                                speed=float(speed),
                                mu=float(mu),
                            )
                        )
                        index += 1
    return rows


def summarize_candidate_rows(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    tier_counts = Counter(str(row["feasibility_tier_id"]) for row in rows)
    role_counts = Counter(str(row["source_role_semantics"]) for row in rows)
    surface_counts = Counter(str(row["surface_variant"]) for row in rows)
    speed_counts = Counter(str(row["speed_ref"]) for row in rows)
    mu_counts = Counter(str(row["mu"]) for row in rows)
    split_counts = Counter(str(row["source_split"]) for row in rows)
    grid_cell_count_total = sum(
        int(row["obstacle_distance_count"]) * int(row["obstacle_half_width_count"]) for row in rows
    )
    return {
        "template_id": TEMPLATE_ID,
        "scenario_quality_branch_id": SCENARIO_QUALITY_BRANCH_ID,
        "candidate_row_count": len(rows),
        "feasibility_tier_counts": dict(sorted(tier_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "surface_counts": dict(sorted(surface_counts.items())),
        "speed_counts": dict(sorted(speed_counts.items(), key=lambda item: float(item[0]))),
        "mu_counts": dict(sorted(mu_counts.items(), key=lambda item: float(item[0]))),
        "source_split_counts": dict(sorted(split_counts.items())),
        "grid_cell_count_total": int(grid_cell_count_total),
        "positive_support_gate_required_count": sum(bool(row["positive_support_gate_required"]) for row in rows),
        "expected_joint_support_count": sum(bool(row["expected_joint_support"]) for row in rows),
        "expected_near_miss_support_count": sum(bool(row["expected_near_miss_support"]) for row in rows),
        "mitigation_only_count": sum(bool(row["mitigation_only"]) for row in rows),
        "paper_holdout_candidate_count": sum(bool(row["paper_holdout_candidate"]) for row in rows),
        "labels_enter_actor_input_count": sum(bool(row["labels_enter_actor_input"]) for row in rows),
        "ranking_admissible_by_default_count": sum(bool(row["v2_ranking_admissible_by_default"]) for row in rows),
        "materialized_row_count": 0,
        "source_mining_execution_started": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_violation_count": 0,
    }


def build_v0_template_payload() -> dict[str, Any]:
    rows = generate_v0_candidate_rows()
    return {
        "template_id": TEMPLATE_ID,
        "generated_at_utc": utc_timestamp(),
        "candidate_sources": rows,
        "summary": summarize_candidate_rows(rows),
    }


def write_v0_template(output_path: Path | str = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    payload = build_v0_template_payload()
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    payload = write_v0_template(args.output)
    summary = payload["summary"]
    print(f"template={args.output}")
    print(f"template_id={summary['template_id']}")
    print(f"candidate_row_count={summary['candidate_row_count']}")
    print(f"feasibility_tier_count={len(summary['feasibility_tier_counts'])}")
    print(f"role_count={len(summary['role_counts'])}")
    print(f"surface_count={len(summary['surface_counts'])}")
    print(f"speed_bucket_count={len(summary['speed_counts'])}")
    print(f"mu_bucket_count={len(summary['mu_counts'])}")
    print(f"labels_enter_actor_input_count={summary['labels_enter_actor_input_count']}")
    print(f"ranking_admissible_by_default_count={summary['ranking_admissible_by_default_count']}")


if __name__ == "__main__":
    main()
