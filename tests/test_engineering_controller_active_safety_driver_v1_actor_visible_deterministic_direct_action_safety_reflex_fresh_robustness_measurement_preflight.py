from pathlib import Path

from autodrift.artifacts import write_json
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_measurement_preflight as m3084
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight as m3078


def _panel_row(index: int, *, task_family: str, binding_role: str, axis_id: str, eval_seed: int) -> dict[str, object]:
    return {
        "fresh_panel_row_id": f"m3082-fresh-panel-{index:04d}",
        "panel_family": "m3082_fresh_robustness_panel",
        "axis_id": axis_id,
        "axis_family": "unit_axis_family",
        "task_family": task_family,
        "scenario_family": "unit_scenario",
        "fresh_scenario_distribution": f"fresh_{axis_id}",
        "binding_role": binding_role,
        "base_profile_name": f"route_a_{binding_role}",
        "profile_binding_name": f"route_a_{binding_role}+m3078_deterministic_safety_reflex_fresh_{axis_id}",
        "eval_seed": eval_seed,
        "fresh_seed": True,
        "m3080_reference_measurement_episode_id": f"m3080-measurement-episode-{index:04d}",
        "m3080_reference_eval_seed": 301500 + index,
        "m3080_reference_outcome_bucket": "success_obstacle_pass",
        "source_denominator_reused": False,
        "fixed_denominator_row_reused": False,
        "measurement_admission_after_m3083": True,
        "actor_observation_dim": 72,
        "actor_action_dim": 3,
        "candidate_output_semantics": "direct_action_clipped",
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
    }


def _workload_row(
    tmp_path: Path,
    index: int,
    *,
    task_family: str,
    binding_role: str,
) -> dict[str, object]:
    config_path = tmp_path / f"config-{index}.json"
    write_json(config_path, {"env": {}})
    return {
        "executable_workload_id": f"m3012-executable-workload-{index:04d}",
        "workload_contract_id": f"contract-{index}",
        "source_resolution_id": f"source-resolution-{index}",
        "profile_binding_id": f"profile-binding-{index}",
        "executable_source_spec_id": f"spec-{index}",
        "task_source_id": f"task-{index}",
        "profile_binding_name": f"route_a_{binding_role}",
        "binding_role": binding_role,
        "task_family": task_family,
        "source_edge": "unit",
        "window_tag": "unit",
        "executable_source_family": "unit_family",
        "env_template_family": "unit_env",
        "config_path": str(config_path),
        "actor_observation_dim": "72",
        "actor_action_dim": "3",
        "status_pass": True,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
    }


def test_fresh_measurement_plan_maps_panel_to_matching_workload_and_fresh_seed(tmp_path: Path) -> None:
    source = {
        "m3082_panel_rows": [
            _panel_row(1, task_family="T4", binding_role="candidate", axis_id="collision_lateral_intrusion", eval_seed=401500),
            _panel_row(2, task_family="T5", binding_role="parent", axis_id="offtrack_boundary_recovery", eval_seed=401501),
        ],
        "m3012_workload_rows": [
            _workload_row(tmp_path, 1, task_family="T4", binding_role="candidate"),
            _workload_row(tmp_path, 2, task_family="T5", binding_role="parent"),
        ],
        "m3080_measurement_rows": [
            {"measurement_episode_id": "m3080-measurement-episode-0001", "eval_seed": "301501", "success": "True"},
            {"measurement_episode_id": "m3080-measurement-episode-0002", "eval_seed": "301502", "success": "False"},
        ],
    }

    plan = m3084.fresh_measurement_plan(source)

    assert [row["measurement_episode_id"] for row in plan] == [
        "m3084-measurement-episode-0001",
        "m3084-measurement-episode-0002",
    ]
    assert [row["eval_seed"] for row in plan] == [401500, 401501]
    assert all(row["status_pass"] is True for row in plan)
    assert all(row["runtime_base_policy_required"] is False for row in plan)
    assert all(row["source_denominator_reused"] is False for row in plan)
    assert all(row["fixed_denominator_row_reused"] is False for row in plan)
    assert {(row["task_family"], row["binding_role"]) for row in plan} == {("T4", "candidate"), ("T5", "parent")}
    assert all(str(row["direct_action_profile_name"]).endswith(str(row["axis_id"])) for row in plan)


def test_follow_up_manifest_preserves_result_audit_boundary(tmp_path: Path) -> None:
    output_dir = tmp_path / "m3084"
    doc_path = tmp_path / "m3084.md"
    summary_path = output_dir / "summary.json"

    manifest = m3084.build_follow_up_manifest(
        output_dir=output_dir,
        doc_path=doc_path,
        summary_path=summary_path,
    )

    assert manifest["id"] == m3084.NEXT_ID
    assert manifest["status"] == "pending"
    assert manifest["gate_tier"] == "process"
    assert manifest["promotion_decision"] == "not_applicable"
    assert "Result audit only" in manifest["workflow_synthesis"]["claim_scope"]
    assert "driver-performance" in manifest["forbidden_shortcuts"][1]


def test_metric_summary_rows_include_axis_and_scenario_groups() -> None:
    rows = [
        {
            "success": True,
            "collision": False,
            "termination_reason": "success",
            "min_clearance_margin": 5.0,
            "return": 1.0,
            "high_sideslip_fraction": 0.0,
            "lateral_rmse": 0.2,
            "action_rate_mean": 0.1,
            "raw_action_abs_max": 0.5,
            "raw_action_l2_mean": 0.2,
            "action_clip_fraction": 0.0,
            "final_action_abs_max": 0.5,
            "runtime_base_policy_required": False,
            "axis_id": "collision_lateral_intrusion",
            "axis_family": "collision_preservation",
            "fresh_scenario_distribution": "fresh_obstacle_lateral_offsets_and_reveal_timing",
            "binding_role": "candidate",
            "base_profile_name": "route_a_candidate",
            "task_family": "T5",
        }
    ]

    groups = {row["group"] for row in m3084.metric_summary_rows(rows)}

    assert "all" in groups
    assert "axis_id:collision_lateral_intrusion" in groups
    assert "fresh_scenario_distribution:fresh_obstacle_lateral_offsets_and_reveal_timing" in groups
