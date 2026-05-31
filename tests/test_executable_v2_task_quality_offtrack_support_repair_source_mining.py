from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_offtrack_support_repair_source_mining as mining
from autodrift import executable_v2_task_quality_offtrack_support_repair_templates as templates
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _comparison_row(surface: str) -> dict[str, object]:
    return {
        "feasibility_tier_id": "tier_c_boundary_near_miss",
        "source_role_semantics": "stable_aeb",
        "surface_variant": surface,
        "sampled_obstacle_label": "aeb_feasible",
        "episode_count": 24,
        "success_count": 5,
        "collision_count": 1,
        "offtrack_outcome_count": 18,
        "profiles_with_success": "L1_one_step;L3_online_gru",
        "support_label": "candidate_support",
    }


def _success_row(index: int, *, tier: str, role: str, surface: str, label: str) -> dict[str, object]:
    source_id = f"source_{index}_{tier}_{role}_{surface}"
    return {
        "workload_id": f"{source_id}::L1_one_step",
        "candidate_source_id": source_id,
        "task_source_id": f"exec_{source_id}",
        "profile_name": "L1_one_step",
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "surface_variant": surface,
        "sampled_obstacle_label": label,
        "target_boundary_mode": "near_miss",
        "target_support_mode": "boundary_mixed_support",
        "selected_accepted_cell_rule": "positive_support_max_threshold",
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "",
        "min_clearance_margin": 1.0,
        "return": 10.0,
        "steps": 20,
    }


def _offtrack_row(index: int) -> dict[str, object]:
    return {
        "slice_kind": "outcome_by_profile_role",
        "dominance_type": "offtrack",
        "episode_count": 16,
        "success_count": 0,
        "collision_count": 1,
        "offtrack_outcome_count": 15,
        "collision_rate": 0.0625,
        "offtrack_outcome_rate": 0.9375,
        "support_label": "no_support",
        "profile_name": "L2_window_13",
        "feasibility_tier_id": ("tier_b_feasible_emergency", "tier_c_boundary_near_miss")[index % 2],
        "source_role_semantics": ("stable_aeb", "stable_aes_only")[index % 2],
        "surface_variant": ("post_friction_step", "steady_surface")[index % 2],
        "sampled_obstacle_label": ("aeb_feasible", "aes_feasible")[index % 2],
    }


def _write_template_inputs(tmp_path: Path) -> Path:
    comparison_path = tmp_path / "comparison.csv"
    success_path = tmp_path / "success.csv"
    offtrack_path = tmp_path / "offtrack.csv"
    write_csv_rows(comparison_path, [_comparison_row("post_friction_step"), _comparison_row("steady_surface")])
    success_rows = []
    for index in range(32):
        success_rows.append(
            _success_row(
                index,
                tier=(
                    "tier_b_feasible_emergency",
                    "tier_c_boundary_near_miss",
                    "tier_d_handling_limit_drift_required",
                )[index % 3],
                role=("stable_aeb", "stable_aes_only", "drift_required_recovery")[index % 3],
                surface=("post_friction_step", "steady_surface")[index % 2],
                label=("aeb_feasible", "aes_feasible", "drift_required")[index % 3],
            )
        )
    for index in range(8):
        success_rows.append(
            _success_row(
                100 + index,
                tier="tier_e_mitigation_only",
                role="unavoidable_mitigation",
                surface=("post_friction_step", "steady_surface")[index % 2],
                label="unavoidable",
            )
        )
    write_csv_rows(success_path, success_rows)
    write_csv_rows(offtrack_path, [_offtrack_row(index) for index in range(8)])
    output = tmp_path / "templates.json"
    templates.build_repair_template_artifact(
        success_source_rows_path=success_path,
        comparison_support_candidates_path=comparison_path,
        offtrack_dominance_rows_path=offtrack_path,
        output_path=output,
    )
    return output


def _write_specs(tmp_path: Path) -> Path:
    specs = []
    for index in range(48):
        specs.append(
            {
                "task_source_id": f"exec_source_{index}_tier_b_feasible_emergency_stable_aeb_post_friction_step",
                "candidate_source_id": f"source_{index}_tier_b_feasible_emergency_stable_aeb_post_friction_step",
                "source_v1_bounded_panel_spec_id": f"source_{index}_tier_b_feasible_emergency_stable_aeb_post_friction_step",
                "source_scenario_spec_id": f"scenario_{index}",
                "speed_ref": 18.0,
                "mu": 0.60,
                "obstacle_distance": 30.0,
                "obstacle_half_width": 0.80,
                "track_width": 6.0,
            }
        )
    path = tmp_path / "specs.json"
    write_json(path, {"executable_task_specs": specs})
    return path


def test_source_mining_adapter_runs_no_rollout_and_writes_artifacts(tmp_path: Path) -> None:
    templates_path = _write_template_inputs(tmp_path)
    specs_path = _write_specs(tmp_path)

    summary = mining.run_offtrack_support_repair_source_mining(
        repair_templates_path=templates_path,
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
    )

    assert summary["input_template_count"] == 160
    assert summary["source_candidate_count"] == 160
    assert summary["resolution_failure_count"] == 0
    assert summary["accepted_cell_count_total"] > 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert (tmp_path / "out" / "repair_source_rows.csv").exists()
    assert (tmp_path / "out" / "repair_accepted_cells.csv").exists()
    assert (tmp_path / "out" / "source_kind_aggregate.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["source_candidate_count"] == 160


def test_template_to_source_candidate_preserves_repair_metadata(tmp_path: Path) -> None:
    templates_path = _write_template_inputs(tmp_path)
    specs_path = _write_specs(tmp_path)
    template_row = read_json(templates_path)["repair_candidate_sources"][0]
    specs = mining._spec_lookup(mining._load_specs(specs_path))

    candidate = mining.template_to_source_candidate(template_row, specs)
    cell = evaluate = mining.evaluate_candidate_cell(
        candidate=candidate,
        obstacle_distance=candidate["obstacle_distance_min"],
        obstacle_half_width=candidate["obstacle_half_width_min"],
    )

    assert candidate["repair_candidate_id"] == template_row["repair_candidate_id"]
    assert candidate["labels_enter_actor_input"] is False
    assert "accepted" in cell
    assert evaluate["reject_reason"]
