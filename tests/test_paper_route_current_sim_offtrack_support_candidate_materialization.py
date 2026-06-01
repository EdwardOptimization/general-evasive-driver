from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_offtrack_support_candidate_materialization as materialization
from autodrift.artifacts import read_json, write_json


def _parent_spec(task_source_id: str = "parent-a") -> dict[str, object]:
    return {
        "task_source_id": task_source_id,
        "benchmark_spec_id": "bench-a",
        "task_family": "T1_reactive_emergency_avoidance",
        "claim_level_target": "Claim_A_deployable_feedback_driver",
        "scenario_source": "fixture",
        "source_kind": "fixture",
        "source_reference": "fixture:0",
        "source_index": 0,
        "source_seed": 100,
        "eval_seed_override": 200,
        "source_family_template": "t5_boundary_axis_retarget",
        "capability_pair": "reactive_current_response",
        "actor_input_contract": "P0_human_view_no_wheel_no_oracle",
        "profile_specific_tuning": False,
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "wheel_observation_mode": "none",
            "obstacle_relative_velocity_mode": "zero",
            "track_width": 5.0,
            "track_radius": 18.0,
            "speed_range": [9.0, 16.0],
            "obstacle": {
                "enabled": True,
                "max_sample_attempts": 200,
                "distance_range": [12.0, 34.0],
                "half_width_range": [0.65, 1.45],
                "perception_reveal_step": 24,
            },
        },
    }


def _candidate(candidate_id: str = "candidate-a", parent_id: str = "parent-a") -> dict[str, object]:
    return {
        "repair_branch_id": "branch",
        "repair_candidate_id": candidate_id,
        "repair_axis": "offtrack_saturation_relief",
        "repair_variant_id": "road_wide_075",
        "repair_split": "public_debug",
        "parent_task_source_id": parent_id,
        "parent_task_family": "T1_reactive_emergency_avoidance",
        "parent_source_family_template": "t5_boundary_axis_retarget",
        "parent_capability_pair": "reactive_current_response",
        "parent_claim_level_target": "Claim_A_deployable_feedback_driver",
        "parent_support_class": "zero_success_offtrack",
        "delta_track_width": 0.75,
        "delta_track_radius": 4.0,
        "delta_obstacle_distance_min": 2.0,
        "delta_obstacle_distance_max": 4.0,
        "delta_obstacle_half_width_min": -0.05,
        "delta_obstacle_half_width_max": -0.1,
        "delta_reveal_step": -8,
        "delta_speed_min": -1.0,
        "delta_speed_max": -1.0,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_fixture(tmp_path: Path, *, bad_guardrail: bool = False) -> tuple[Path, Path]:
    candidate = _candidate()
    if bad_guardrail:
        candidate["actor_input_contract_changed"] = True
    candidate_path = tmp_path / "candidates.json"
    specs_path = tmp_path / "specs.json"
    write_json(candidate_path, {"candidates": [candidate]})
    write_json(specs_path, {"executable_task_specs": [_parent_spec()]})
    return candidate_path, specs_path


def test_offtrack_support_candidate_materialization_writes_specs_and_workload(tmp_path: Path) -> None:
    candidate_path, specs_path = _write_fixture(tmp_path)

    summary = materialization.materialize_candidates(
        candidate_config=candidate_path,
        executable_task_specs=specs_path,
        output_dir=tmp_path / "out",
        expected_candidate_count=1,
    )

    assert summary["result_class"] == "current_sim_offtrack_support_candidate_materialization_pass"
    assert summary["repaired_executable_spec_count"] == 1
    assert summary["planned_workload_row_count"] == 8
    assert summary["materialization_failure_count"] == 0
    assert summary["contract_violation_count"] == 0
    specs = read_json(tmp_path / "out" / "repaired_executable_task_specs.json")["executable_task_specs"]
    assert specs[0]["task_source_id"] == "candidate-a"
    assert specs[0]["parent_task_source_id"] == "parent-a"
    assert specs[0]["env_config"]["track_width"] == 5.75
    assert specs[0]["env_config"]["track_radius"] == 22.0
    assert specs[0]["env_config"]["obstacle"]["distance_range"] == [14.0, 38.0]
    assert specs[0]["env_config"]["obstacle"]["half_width_range"] == [0.6, 1.3499999999999999]
    assert specs[0]["env_config"]["obstacle"]["perception_reveal_step"] == 16
    assert specs[0]["env_config"]["speed_range"] == [8.0, 15.0]
    assert (tmp_path / "out" / "planned_workload.csv").exists()


def test_offtrack_support_candidate_materialization_fails_closed_on_guardrail(tmp_path: Path) -> None:
    candidate_path, specs_path = _write_fixture(tmp_path, bad_guardrail=True)

    summary = materialization.materialize_candidates(
        candidate_config=candidate_path,
        executable_task_specs=specs_path,
        output_dir=tmp_path / "out",
        expected_candidate_count=1,
    )

    assert summary["result_class"] == "current_sim_offtrack_support_candidate_materialization_fail"
    assert summary["repaired_executable_spec_count"] == 0
    assert summary["materialization_failure_count"] == 1
    assert summary["candidate_guardrail_violation_count"] == 1
