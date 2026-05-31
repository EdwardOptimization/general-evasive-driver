from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_outcome_support_repair_templates as templates
from autodrift import executable_v2_task_quality_calibrated_outcome_support_source_mining as mining
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _success_row(index: int, *, role: str = "stable_aes_only", label: str = "aes_feasible") -> dict[str, object]:
    return {
        "workload_id": f"success_{index}::L1_one_step",
        "candidate_source_id": f"success_candidate_{index}",
        "task_source_id": f"success_task_{index}",
        "profile_name": "L1_one_step",
        "repair_source_kind": "success_stabilizer",
        "selection_quota_name": "success_support",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "parent_surface_variant": "steady_surface",
        "normalized_surface_variant": "steady_surface",
        "sampled_obstacle_label": label,
        "base_geometry_source": "unit_success",
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "",
        "speed_ref": 18.0,
        "mu": 0.4,
    }


def _dominance_row(
    index: int,
    *,
    dominance_type: str,
    repair_source_kind: str,
    role: str,
    label: str,
) -> dict[str, object]:
    return {
        "slice_kind": "outcome_by_repair_source_kind",
        "dominance_type": dominance_type,
        "episode_count": 32,
        "success_count": 0 if dominance_type == "offtrack" else 5,
        "collision_count": 0 if dominance_type == "offtrack" else 27,
        "offtrack_outcome_count": 32 if dominance_type == "offtrack" else 0,
        "collision_rate": 0.0 if dominance_type == "offtrack" else 0.84,
        "offtrack_outcome_rate": 1.0 if dominance_type == "offtrack" else 0.0,
        "support_label": "no_support",
        "profile_name": "",
        "repair_source_kind": repair_source_kind,
        "source_role_semantics": role,
        "parent_feasibility_tier_id": (
            "tier_not_applicable_offtrack_boundary_relief"
            if repair_source_kind == "offtrack_boundary_relief"
            else "tier_c_boundary_near_miss"
        ),
        "normalized_surface_variant": (
            "relief_surface_unspecified"
            if repair_source_kind == "offtrack_boundary_relief"
            else "steady_surface"
        ),
        "sampled_obstacle_label": label,
        "candidate_source_id": f"{repair_source_kind}_{dominance_type}_{index}",
    }


def _write_template_inputs(tmp_path: Path) -> Path:
    output_dir = tmp_path / "loc"
    output_dir.mkdir()
    success_rows = [_success_row(index) for index in range(16)]
    success_rows.extend(_success_row(100 + index, role="unavoidable_mitigation", label="unavoidable") for index in range(8))
    offtrack_rows = [
        _dominance_row(
            index,
            dominance_type="offtrack",
            repair_source_kind=("anchor_neighborhood" if index < 4 else "offtrack_boundary_relief"),
            role=("stable_aeb" if index < 4 else "stable_aes_only"),
            label=("aeb_feasible" if index < 4 else "aes_feasible"),
        )
        for index in range(8)
    ]
    collision_rows = [
        _dominance_row(
            index,
            dominance_type="collision",
            repair_source_kind="mitigation_isolation_check",
            role="unavoidable_mitigation",
            label="unavoidable",
        )
        for index in range(8)
    ]
    write_csv_rows(output_dir / "success_source_rows.csv", success_rows)
    write_csv_rows(output_dir / "offtrack_dominance_rows.csv", offtrack_rows)
    write_csv_rows(output_dir / "collision_dominance_rows.csv", collision_rows)
    summary_path = output_dir / "summary.json"
    write_json(
        summary_path,
        {
            "result_class": "task_quality_calibrated_repaired_measured_outcome_localization_pass",
            "artifacts": {
                "success_source_rows": str(output_dir / "success_source_rows.csv"),
                "offtrack_dominance_rows": str(output_dir / "offtrack_dominance_rows.csv"),
                "collision_dominance_rows": str(output_dir / "collision_dominance_rows.csv"),
            },
        },
    )
    output = tmp_path / "templates.json"
    templates.build_repair_template_artifact(localization_summary_path=summary_path, output_path=output)
    return output


def _write_specs(tmp_path: Path) -> Path:
    specs = []
    for index in range(24):
        specs.append(
            {
                "task_source_id": f"success_task_{index}",
                "candidate_source_id": f"success_candidate_{index}",
                "source_v1_bounded_panel_spec_id": f"success_candidate_{index}",
                "source_scenario_spec_id": f"scenario_{index}",
                "speed_ref": 18.0,
                "mu": 0.40,
                "obstacle_distance": 30.0 if index < 16 else 10.0,
                "obstacle_half_width": 0.80 if index < 16 else 1.30,
                "track_width": 6.0,
            }
        )
    path = tmp_path / "specs.json"
    write_json(path, {"executable_task_specs": specs})
    return path


def _write_anchor_fallback(tmp_path: Path) -> Path:
    path = tmp_path / "selected_anchor_fallback_geometry.json"
    write_json(
        path,
        {
            f"tier_c_boundary_near_miss::stable_aeb::aeb_feasible::{surface}": {
                "speed_ref": 18.0,
                "mu": 0.40,
                "obstacle_distance": 52.0,
                "obstacle_half_width": 0.75,
                "base_track_width": 5.75,
            }
            for surface in ("post_friction_step", "steady_surface")
        },
    )
    return path


def test_template_to_source_candidate_normalizes_target_fields(tmp_path: Path) -> None:
    templates_path = _write_template_inputs(tmp_path)
    specs_path = _write_specs(tmp_path)
    template_row = next(
        row for row in read_json(templates_path)["repair_candidate_sources"] if row["repair_axis"] == "success_support_expansion"
    )
    specs = mining._spec_lookup(mining._load_specs(specs_path))

    candidate = mining.template_to_source_candidate(template_row, specs)

    assert candidate["candidate_source_id"] == template_row["repair_candidate_id"]
    assert candidate["source_role_semantics"] == template_row["target_source_role_semantics"]
    assert candidate["feasibility_tier_id"] == template_row["target_feasibility_tier_id"]
    assert candidate["normalized_surface_variant"] == template_row["target_normalized_surface_variant"]
    assert candidate["labels_enter_actor_input"] is False
    assert candidate["base_geometry_source"] == "m1969::parent_task_source_id"


def test_outcome_support_source_mining_runs_no_rollout_and_writes_artifacts(tmp_path: Path) -> None:
    templates_path = _write_template_inputs(tmp_path)
    specs_path = _write_specs(tmp_path)
    fallback_path = _write_anchor_fallback(tmp_path)

    summary = mining.run_outcome_support_source_mining(
        repair_templates_path=templates_path,
        executable_task_specs_path=specs_path,
        anchor_fallback_geometry_path=fallback_path,
        output_dir=tmp_path / "out",
    )

    assert summary["input_template_count"] == 192
    assert summary["source_candidate_count"] == 192
    assert summary["resolution_failure_count"] == 0
    assert summary["accepted_cell_count_total"] > 0
    assert summary["repair_axis_counts"] == mining.AXIS_TARGET_COUNTS
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert (tmp_path / "out" / "outcome_support_source_rows.csv").exists()
    assert (tmp_path / "out" / "outcome_support_accepted_cells.csv").exists()
    assert (tmp_path / "out" / "repair_axis_aggregate.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["source_candidate_count"] == 192
