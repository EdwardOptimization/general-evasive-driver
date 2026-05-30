from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import metric_specific_bounded_panel_measured_execution as bounded_exec


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    specs = []
    matrix = []
    profile_names = [f"profile_{index}" for index in range(12)]
    roles = [
        ("stable_avoidance_aes", "avoidance_success"),
        ("drift_required_recovery", "controlled_drift_recovery"),
        ("hidden_dynamics_robustness", "hidden_dynamics_robustness"),
        ("unavoidable_mitigation", "collision_mitigation"),
    ]
    for role_index, (role_id, metric_family) in enumerate(roles):
        for spec_index in range(6):
            spec_id = f"spec_{role_index}_{spec_index}"
            specs.append(
                {
                    "bounded_panel_spec_id": spec_id,
                    "scenario_spec_id": spec_id,
                    "env_config": {"history_length": 1},
                }
            )
            for profile_name in profile_names:
                matrix.append(
                    {
                        "bounded_panel_workload_id": f"{spec_id}::{profile_name}",
                        "scenario_workload_id": f"{spec_id}::{profile_name}",
                        "scenario_spec_id": spec_id,
                        "bounded_panel_spec_id": spec_id,
                        "source_scenario_spec_id": f"source_{spec_id}",
                        "m1728_scenario_spec_id": f"source_{spec_id}",
                        "role_panel_id": role_id,
                        "role_panel_label": role_id,
                        "scenario_family_id": f"S{role_index}",
                        "scenario_family": f"family_{role_index}",
                        "scenario_role": "test role",
                        "profile_name": profile_name,
                        "evaluation_role": "benchmark",
                        "primary_metric_family": metric_family,
                        "panel_evaluation_role": "benchmark",
                        "panel_primary_metric_family": metric_family,
                        "panel_metric_contract": "benchmark_success;avoidance_success",
                        "ranking_eligible_after_audit": False,
                        "diagnostic_only_no_ranking_claim": True,
                        "benchmark_row": True,
                        "labels_enter_actor_input": False,
                        "allowed_labels_metadata_only": "aes_feasible",
                        "hidden_dynamics_bucket": "nominal",
                        "road_boundary_bucket": "moderate",
                        "obstacle_timing_bucket": "close",
                        "obstacle_lateral_bucket": "center",
                        "sampling_repair_source": "test",
                        "sampling_repair_variant_id": "none",
                        "sampling_repair_applied": False,
                        "metric_required_avoidance_success": True,
                        "metric_required_benchmark_success": True,
                        "metric_required_collision_mitigation_score": False,
                        "metric_required_controlled_drift_recovery_success": False,
                        "metric_required_diagnostic_only_no_ranking_claim": True,
                        "metric_required_hidden_dynamics_robustness": False,
                        "metric_required_impact_severity_proxy": False,
                        "metric_required_off_track_severity_proxy": True,
                        "metric_required_off_track_violation": True,
                        "metric_required_recovery_success": True,
                        "metric_required_recovery_time_proxy": True,
                        "metric_required_drift_used": False,
                        "metric_required_impact_beta_abs": False,
                        "metric_required_impact_speed_proxy": False,
                        "metric_required_impact_yaw_rate_abs": False,
                    }
                )
    specs_path = tmp_path / "specs.json"
    matrix_path = tmp_path / "matrix.csv"
    write_json(specs_path, {"bounded_panel_specs": specs})
    write_csv_rows(matrix_path, matrix)
    return specs_path, matrix_path


def _fake_episode_row(workload_row, eval_seed: int):
    return {
        "workload_id": workload_row["workload_id"],
        "task_source_id": workload_row["task_source_id"],
        "profile_name": workload_row["profile_name"],
        "task_family": workload_row["task_family"],
        "source_edge": workload_row["source_edge"],
        "window_tag": workload_row["window_tag"],
        "strata": workload_row["strata"],
        "executable_source_family": workload_row["executable_source_family"],
        "env_template_family": workload_row["env_template_family"],
        "profile_config_path": "fake_config.json",
        "checkpoint_path": "fake_checkpoint.pt",
        "profile_env_history_length": 1,
        "eval_seed": eval_seed,
        "routing_smoke_only": False,
        "full_rollout_execution": True,
        "private_holdout_used": False,
        "promoted": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "success": True,
        "obstacle_completed": True,
        "obstacle_passed_raw": True,
        "collision": False,
        "obstacle_label": "aes_feasible",
        "sampled_obstacle_label": "aes_feasible",
        "min_clearance_margin": 1.0,
        "return": 10.0,
        "steps": 32,
        "action_rate_mean": 0.05,
        "high_sideslip_fraction": 0.0,
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "obstacle_passed",
        "dt": 0.02,
        "track_width": 5.0,
        "first_obstacle_pass_step": 16,
        "first_obstacle_pass_time_s": 0.32,
        "first_recovery_step": 20,
        "first_recovery_time_s": 0.40,
        "recovery_success": True,
        "recovery_time_proxy": 0.08,
        "max_abs_beta": 0.1,
        "max_abs_yaw_rate": 0.2,
        "drift_used": False,
        "controlled_drift_recovery_success": True,
        "impact_speed_proxy": 0.0,
        "impact_beta_abs": 0.0,
        "impact_yaw_rate_abs": 0.0,
        "impact_severity_proxy": 0.0,
        "collision_mitigation_score": 0.0,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "off_track_severity_proxy": 0.0,
    }


def test_bounded_panel_measured_execution_adapter_smoke(tmp_path: Path, monkeypatch) -> None:
    specs_path, matrix_path = _write_inputs(tmp_path)
    profile_rows = [
        {
            "profile_name": f"profile_{index}",
            "config_path": str(tmp_path / f"profile_{index}.json"),
            "checkpoint_path": str(tmp_path / f"profile_{index}.pt"),
        }
        for index in range(12)
    ]
    monkeypatch.setattr(bounded_exec, "profile_artifact_rows", lambda m1674_run_dir: profile_rows)
    monkeypatch.setattr(
        bounded_exec,
        "_load_profile_cache",
        lambda rows, device: {row["profile_name"]: ({}, object()) for row in rows},
    )
    monkeypatch.setattr(
        bounded_exec,
        "run_workload_cell",
        lambda workload_row, executable_spec, profile_config, model, profile_row, eval_seed: _fake_episode_row(
            workload_row,
            eval_seed,
        ),
    )

    summary = bounded_exec.run_metric_specific_bounded_panel_measured_execution(
        bounded_panel_specs_path=specs_path,
        bounded_panel_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
        resume=False,
    )

    assert summary["result_class"] == "metric_specific_bounded_panel_measured_execution_pass"
    assert summary["episode_count"] == 288
    assert summary["failure_count"] == 0
    assert summary["profile_count"] == 12
    assert summary["bounded_panel_spec_count"] == 24
    assert summary["role_panel_count"] == 4
    assert summary["role_panel_aggregate_rows"] == 4
    assert summary["metric_completeness_passed"] is True
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "episode_rows.csv").exists()
    assert (tmp_path / "out" / "role_panel_aggregate.csv").exists()
    assert (tmp_path / "out" / "metric_completeness_summary.csv").exists()
