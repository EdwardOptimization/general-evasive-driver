from __future__ import annotations

import csv
from pathlib import Path

from autodrift.executable_v2_support_first_task_quality_repair_axis_materialization import (
    REPAIR_AXIS_VARIANTS,
    build_role_surface_axis_target_map,
    materialize,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _episode_row(
    *,
    workload_id: str,
    spec_id: str,
    profile: str,
    role: str,
    surface: str,
    repair_variant: str = "original",
    clearance: bool = True,
    contained: bool = False,
    collision: bool = False,
    margin: float = 0.5,
    overshoot: float = 0.1,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "support_first_workload_id": f"{spec_id}::{profile}",
        "task_source_id": spec_id,
        "support_first_v2_panel_spec_id": spec_id,
        "support_first_materialized_v2_panel_spec_id": spec_id,
        "source_scenario_spec_id": f"{spec_id}_scenario",
        "controller_profile_name": profile,
        "profile_name": profile,
        "scenario_profile_name": f"{role}_profile",
        "scenario_profile_group": role,
        "profile_config_path": f"configs/{profile}.json",
        "checkpoint_path": f"runs/{profile}/checkpoint.pt",
        "role_panel_id": role,
        "v2_role_surface_id": surface,
        "surface_variant": surface.split("::")[-1],
        "hidden_dynamics_bucket": "mu_0p4",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": "steady_surface",
        "obstacle_lateral_bucket": "support_first_width_0p65",
        "sampled_obstacle_label": "aes_feasible",
        "allowed_labels_metadata_only": "aes_feasible",
        "repair_variant_id": repair_variant,
        "obstacle_clearance_pass": clearance,
        "road_containment_pass": contained,
        "collision_failure": collision,
        "min_clearance_margin": margin,
        "max_off_track_overshoot": overshoot,
        "impact_severity_proxy": 12.0 if collision else 0.0,
        "time_to_first_off_track_s": 2.5 if not contained else "nan",
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
    }


def test_role_surface_axis_targets_separate_repair_axes() -> None:
    rows = [
        {
            "v2_role_surface_id": "stable_aes_only::steady_surface",
            "episode_count": 10,
            "clearance_only_offtrack_rate": 0.9,
            "containment_collision_rate": 0.0,
            "near_containment_after_clearance_rate": 0.4,
            "near_clearance_with_containment_rate": 0.0,
        },
        {
            "v2_role_surface_id": "unavoidable_mitigation::steady_surface",
            "episode_count": 10,
            "clearance_only_offtrack_rate": 0.1,
            "containment_collision_rate": 0.8,
            "near_containment_after_clearance_rate": 0.1,
            "near_clearance_with_containment_rate": 0.5,
        },
    ]

    target_rows = build_role_surface_axis_target_map(rows)
    stable_axes = {
        row["task_quality_axis_id"]
        for row in target_rows
        if row["v2_role_surface_id"] == "stable_aes_only::steady_surface"
    }
    unavoidable_axes = {
        row["task_quality_axis_id"]
        for row in target_rows
        if row["v2_role_surface_id"] == "unavoidable_mitigation::steady_surface"
    }

    assert "post_clearance_containment_recovery" in stable_axes
    assert "contained_collision_clearance_feasibility" in unavoidable_axes
    assert "unavoidable_mitigation_semantics" in unavoidable_axes


def test_materialize_axis_matrix_preserves_baseline_and_counts(tmp_path: Path) -> None:
    episodes = tmp_path / "episode_rows.csv"
    surfaces = tmp_path / "role_surface.csv"
    output = tmp_path / "out"
    episode_rows = [
        _episode_row(
            workload_id="w0",
            spec_id="spec0",
            profile="L0_current_masked",
            role="stable_aes_only",
            surface="stable_aes_only::steady_surface",
        ),
        _episode_row(
            workload_id="w1",
            spec_id="spec0",
            profile="L1_one_step",
            role="unavoidable_mitigation",
            surface="unavoidable_mitigation::steady_surface",
            clearance=False,
            contained=True,
            collision=True,
            margin=-0.1,
            overshoot=0.0,
        ),
        _episode_row(
            workload_id="w2",
            spec_id="spec0",
            profile="L1_one_step",
            role="unavoidable_mitigation",
            surface="unavoidable_mitigation::steady_surface",
            repair_variant="semantics_only",
            clearance=True,
            contained=False,
        ),
    ]
    episode_rows[-1]["environment_rollout_started"] = True
    episode_rows[-1]["measured_rollout_started"] = True
    surface_rows = [
        {
            "v2_role_surface_id": "stable_aes_only::steady_surface",
            "episode_count": 1,
            "clearance_only_offtrack_rate": 1.0,
            "containment_collision_rate": 0.0,
            "near_containment_after_clearance_rate": 1.0,
            "near_clearance_with_containment_rate": 0.0,
        },
        {
            "v2_role_surface_id": "unavoidable_mitigation::steady_surface",
            "episode_count": 1,
            "clearance_only_offtrack_rate": 0.0,
            "containment_collision_rate": 1.0,
            "near_containment_after_clearance_rate": 0.0,
            "near_clearance_with_containment_rate": 1.0,
        },
    ]
    _write_csv(episodes, episode_rows)
    _write_csv(surfaces, surface_rows)

    summary = materialize(
        episode_rows_path=episodes,
        role_surface_conflict_aggregate_path=surfaces,
        output_dir=output,
        target_source_spec_count=1,
        target_controller_profile_count=2,
        target_repair_axis_variant_count=len(REPAIR_AXIS_VARIANTS),
        target_matrix_row_count=2 * len(REPAIR_AXIS_VARIANTS),
        target_original_retained_row_count=2,
        next_blocker="m-test",
    )

    assert summary["result_class"] == "task_quality_repair_axis_materialization_pass"
    assert summary["base_original_row_count"] == 2
    assert summary["source_spec_count"] == 1
    assert summary["controller_profile_count"] == 2
    assert summary["repair_axis_matrix_row_count"] == 2 * len(REPAIR_AXIS_VARIANTS)
    assert summary["original_retained_row_count"] == 2
    assert summary["guardrail_violation_count"] == 0
    assert (output / "summary.json").exists()
    assert (output / "task_quality_repair_axis_matrix.csv").exists()
    assert (output / "task_quality_repair_axis_spec.json").exists()
    assert (output / "role_surface_axis_target_map.csv").exists()
