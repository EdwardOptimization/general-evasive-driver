from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration as calibration
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _anchor_template(index: int, surface: str) -> dict[str, object]:
    return {
        "feasibility_tier_id": "tier_c_boundary_near_miss",
        "source_role_semantics": "stable_aeb",
        "surface_variant": surface,
        "sampled_obstacle_label": "aeb_feasible",
        "mu": 0.4,
        "speed_ref": 18.0,
        "obstacle_distance_delta": float(2 + 2 * (index % 4)),
        "obstacle_half_width_delta": (0.0, -0.1)[index % 2],
        "post_obstacle_track_width_delta": (0.25, 0.5)[index % 2],
        "offtrack_repair_mode": "anchor_neighborhood_geometry_relief",
        "recovery_corridor_profile": "bounded_anchor_relief",
        "repair_candidate_id": f"anchor_{surface}_{index:02d}",
        "repair_source_kind": "anchor_neighborhood",
        "repair_source_family": f"family_{surface}",
        "source_split": "public_debug",
        "parent_candidate_source_id": f"anchor_neighborhood_{index:03d}",
        "parent_task_source_id": f"anchor_neighborhood_{index:03d}",
        "parent_profile_name": "L1_one_step",
        "parent_feasibility_tier_id": "tier_c_boundary_near_miss",
        "parent_source_role_semantics": "stable_aeb",
        "parent_surface_variant": surface,
        "parent_sampled_obstacle_label": "aeb_feasible",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    templates = []
    blocked = []
    for surface in calibration.SURFACE_ORDER:
        for index in range(32):
            row = _anchor_template(index, surface)
            templates.append(row)
            blocked.append(
                {
                    "repair_candidate_id": row["repair_candidate_id"],
                    "repair_source_kind": "anchor_neighborhood",
                    "repair_source_family": row["repair_source_family"],
                    "source_split": "public_debug",
                    "offtrack_repair_mode": "anchor_neighborhood_geometry_relief",
                    "recovery_corridor_profile": "bounded_anchor_relief",
                    "parent_candidate_source_id": row["parent_candidate_source_id"],
                    "parent_task_source_id": row["parent_task_source_id"],
                    "parent_profile_name": row["parent_profile_name"],
                    "parent_feasibility_tier_id": "tier_c_boundary_near_miss",
                    "parent_source_role_semantics": "stable_aeb",
                    "parent_surface_variant": surface,
                    "parent_sampled_obstacle_label": "aeb_feasible",
                    "candidate_source_id": row["repair_candidate_id"],
                    "source_role_semantics": "stable_aeb",
                    "source_support_status": "unsupported",
                    "source_support_failure_reason": "label_role_mismatch",
                    "accepted_cell_count": 0,
                    "min_accepted_cells": 3,
                    "dominant_label": "aes_feasible",
                    "dominant_reject_reason": "label_not_allowed",
                }
            )
    template_path = tmp_path / "templates.json"
    blocked_path = tmp_path / "blocked.csv"
    write_json(template_path, {"repair_candidate_sources": templates})
    write_csv_rows(blocked_path, blocked)
    return template_path, blocked_path


def test_anchor_fallback_geometry_calibration_passes_without_rollout(tmp_path: Path) -> None:
    templates_path, blocked_path = _write_inputs(tmp_path)

    summary = calibration.run_anchor_fallback_geometry_calibration(
        repair_templates_path=templates_path,
        blocked_rows_path=blocked_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "task_quality_anchor_fallback_geometry_calibration_pass"
    assert summary["input_anchor_template_count"] == 64
    assert summary["blocked_anchor_row_count"] == 64
    assert summary["selected_surface_count"] == 2
    assert summary["selected_supported_anchor_count_total"] >= 32
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    selected = read_json(tmp_path / "out" / "selected_anchor_fallback_geometry.json")
    assert set(selected) == {
        "tier_c_boundary_near_miss::stable_aeb::aeb_feasible::post_friction_step",
        "tier_c_boundary_near_miss::stable_aeb::aeb_feasible::steady_surface",
    }
    assert {row["center_label"] for row in selected.values()} == {"aeb_feasible"}


def test_calibration_ignores_non_anchor_templates(tmp_path: Path) -> None:
    templates_path, blocked_path = _write_inputs(tmp_path)
    payload = read_json(templates_path)
    payload["repair_candidate_sources"].append(
        {
            **_anchor_template(99, "steady_surface"),
            "repair_candidate_id": "ignored_success",
            "repair_source_kind": "success_stabilizer",
        }
    )
    write_json(templates_path, payload)

    summary = calibration.run_anchor_fallback_geometry_calibration(
        repair_templates_path=templates_path,
        blocked_rows_path=blocked_path,
        output_dir=tmp_path / "out",
    )

    assert summary["input_anchor_template_count"] == 64
    assert summary["result_class"] == "task_quality_anchor_fallback_geometry_calibration_pass"
