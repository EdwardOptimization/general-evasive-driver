from __future__ import annotations

from autodrift.executable_v2_support_first_task_quality_repair_axis_execution import (
    IMPORT_ROW_KIND,
    POSTPROCESS_ROW_KIND,
    ROLLOUT_ROW_KIND,
    dry_run_prepare_execution,
    import_postprocess_episode_rows,
    planned_rollout_rows,
    split_axis_matrix_rows,
)


def _matrix_row(row_id: str, *, kind: str, variant: str = "original_retained") -> dict[str, object]:
    return {
        "task_quality_repair_axis_row_id": row_id,
        "task_quality_axis_id": "baseline_and_semantics_retention"
        if variant in {"original_retained", "role_semantics_only"}
        else "post_clearance_containment_recovery",
        "repair_axis_variant_id": variant,
        "axis_applicability": "all",
        "target_conflict_class": "baseline",
        "target_near_miss_class": "none",
        "target_role_surface_id": "stable_aeb::steady_surface",
        "source_conflict_class": "clearance_only_offtrack",
        "source_near_miss_flags": "near_containment_after_clearance",
        "source_episode_workload_id": "source-w0",
        "base_task_source_id": "spec0",
        "base_support_first_workload_id": "spec0::L0_current_masked",
        "axis_task_source_id": f"spec0__{variant}",
        "axis_workload_id": f"spec0::L0_current_masked__{variant}",
        "support_first_workload_id": "spec0::L0_current_masked",
        "task_source_id": "spec0",
        "support_first_v2_panel_spec_id": "spec0",
        "source_scenario_spec_id": "spec0_scenario",
        "controller_profile_name": "L0_current_masked",
        "profile_name": "L0_current_masked",
        "scenario_profile_name": "stable_aeb_steady_surface_grid_v0",
        "role_panel_id": "stable_aeb",
        "v2_role_surface_id": "stable_aeb::steady_surface",
        "surface_variant": "steady_surface",
        "hidden_dynamics_bucket": "mu_0p4::steady_surface",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": "steady_surface",
        "obstacle_lateral_bucket": "support_first_width_0p65",
        "sampled_obstacle_label": "aeb_feasible",
        "geometry_delta_json": "{}"
        if kind != ROLLOUT_ROW_KIND
        else '{"finish_rule":"post_obstacle_recovery_window_plus"}',
        "semantics_delta_json": "{}",
        "execution_row_kind": kind,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_ranking_claim": True,
    }


def _source_episode() -> dict[str, object]:
    return {
        "workload_id": "source-w0",
        "collision": False,
        "obstacle_clearance_pass": True,
        "road_containment_pass": False,
        "collision_failure": False,
        "min_clearance_margin": 0.4,
        "max_off_track_overshoot": 0.1,
        "time_to_first_off_track_s": 2.5,
        "termination_reason": "off_track",
        "outcome_bucket": "off_track_noncollision_noncompletion",
        "environment_rollout_started": True,
        "measured_rollout_started": True,
        "policy_action_executed": True,
    }


def test_split_and_planned_rollout_rows_preserve_axis_metadata() -> None:
    rows = [
        _matrix_row("r0", kind=ROLLOUT_ROW_KIND, variant="post_clearance_recovery_window_plus"),
        _matrix_row("r1", kind=IMPORT_ROW_KIND),
        _matrix_row("r2", kind=POSTPROCESS_ROW_KIND, variant="role_semantics_only"),
    ]
    rollout_rows, import_rows = split_axis_matrix_rows(rows)
    planned, failures = planned_rollout_rows(rollout_rows, eval_seed_base=1000)

    assert len(rollout_rows) == 1
    assert len(import_rows) == 2
    assert not failures
    assert planned[0]["workload_id"].endswith("post_clearance_recovery_window_plus")
    assert planned[0]["eval_seed"] == 1000
    assert planned[0]["row_provenance"] == "planned_rollout_geometry_variant"
    assert planned[0]["task_quality_repair_axis_row_id"] == "r0"
    assert planned[0]["environment_rollout_started"] is False


def test_import_postprocess_join_overlays_axis_metadata_and_resets_provenance() -> None:
    rows = [
        _matrix_row("r1", kind=IMPORT_ROW_KIND),
        _matrix_row("r2", kind=POSTPROCESS_ROW_KIND, variant="role_semantics_only"),
    ]
    imported, failures = import_postprocess_episode_rows(rows, [_source_episode()])

    assert not failures
    assert len(imported) == 2
    assert imported[0]["workload_id"].endswith("original_retained")
    assert imported[0]["import_source_episode_workload_id"] == "source-w0"
    assert imported[0]["environment_rollout_started"] is False
    assert imported[0]["policy_action_executed"] is False
    assert imported[0]["near_containment_after_clearance"] is True
    assert imported[1]["repair_axis_variant_id"] == "role_semantics_only"


def test_dry_run_prepare_execution_summarizes_wrapper_contract() -> None:
    matrix_rows = [
        _matrix_row("r0", kind=ROLLOUT_ROW_KIND, variant="post_clearance_recovery_window_plus"),
        _matrix_row("r1", kind=IMPORT_ROW_KIND),
        _matrix_row("r2", kind=POSTPROCESS_ROW_KIND, variant="role_semantics_only"),
    ]
    result = dry_run_prepare_execution(matrix_rows=matrix_rows, source_episode_rows=[_source_episode()])
    summary = result["summary"]

    assert summary["result_class"] == "task_quality_repair_axis_execution_wrapper_preflight_pass"
    assert summary["matrix_row_count"] == 3
    assert summary["planned_rollout_row_count"] == 1
    assert summary["import_postprocess_row_count"] == 2
    assert summary["combined_panel_row_count"] == 3
    assert summary["failure_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["controller_family_ranking_claim_made"] is False
