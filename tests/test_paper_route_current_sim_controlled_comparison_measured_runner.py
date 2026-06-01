from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_measured_runner as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _spec(task_id: str, task_family: str = "T1_reactive_emergency_avoidance") -> dict[str, object]:
    return {
        "task_source_id": task_id,
        "benchmark_spec_id": f"bench-{task_id}",
        "task_family": task_family,
        "claim_level_target": "Claim_A_deployable_feedback_driver",
        "scenario_source": "current_sim_executable_materialization_v0",
        "source_kind": "reactive_avoidance",
        "source_reference": f"ref-{task_id}",
        "source_index": 0,
        "source_seed": 215100,
        "eval_seed_override": 219100,
        "materialization_semantics": "current_sim_executable_spec_v0",
        "paper_validity_status": "current_sim_executable_candidate_not_reset_validated",
        "generated_proxy_source": False,
        "actor_input_contract": "P0_human_view_no_wheel_no_oracle",
        "metric_gap_policy": "preserve_explicit_deferred_gaps",
        "source_family_template": "t5_boundary_axis_retarget",
        "capability_pair": "reactive_current_response",
        "reveal_step": 24,
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "obstacle_relative_velocity_mode": "zero",
            "wheel_observation_mode": "none",
        },
    }


def _workload(
    task_id: str,
    profile: str,
    profile_config: Path,
    checkpoint: Path | str = "",
    task_family: str = "T1_reactive_emergency_avoidance",
) -> dict[str, object]:
    return {
        "workload_id": f"{task_id}::{profile}",
        "task_source_id": task_id,
        "benchmark_spec_id": f"bench-{task_id}",
        "profile_name": profile,
        "profile_level": "L3_recurrent" if "L3" in profile else "L0_current_observation",
        "profile_config_path": str(profile_config),
        "checkpoint_path": str(checkpoint),
        "checkpoint_required_for_measured_execution": "true",
        "task_family": task_family,
        "history_representation": "online_gru" if "L3" in profile else "current_response",
        "history_window_steps": "100" if "L3" in profile else "1",
        "reset_or_truncated_control": "false",
        "environment_reset_scheduled": "false",
        "environment_rollout_scheduled": "false",
        "training_scheduled": "false",
        "checkpoint_materialization_mode": "train_frozen_profile_config",
        "profile_specific_tuning": "false",
        "controller_family_ranking_claim_made": "false",
        "finite_window_vs_gru_conclusion_made": "false",
        "paper_level_claim_made": "false",
        "level3_self_id_claim_made": "false",
    }


def _repeat_metadata(*, repeat_id: str = "repeat_1_seed_21761") -> dict[str, str]:
    return {
        "training_repeat_id": repeat_id,
        "training_seed_group": "seed_21761",
        "profile_training_seed": "2176106",
        "profile_checkpoint_source_profile": "L3_online_gru",
        "checkpoint_materialization_mode": "trained_checkpoint",
        "base_workload_id": "base-task::L3_online_gru",
    }


def _write_inputs(
    tmp_path: Path,
    *,
    missing_checkpoint: bool = False,
    repeat_metadata: bool = False,
    partial_repeat_metadata: bool = False,
) -> tuple[Path, Path]:
    profile_config = tmp_path / "profile.json"
    profile_config.write_text("{}", encoding="utf-8")
    checkpoint = "" if missing_checkpoint else tmp_path / "checkpoint.pt"
    if checkpoint:
        Path(checkpoint).write_bytes(b"placeholder")
    specs = [_spec("task_a"), _spec("task_b", task_family="T5_terminal_boundary_near_constraint")]
    workloads = [
        _workload("task_a", "L0_current_masked", profile_config, checkpoint),
        _workload("task_a", "L3_online_gru", profile_config, checkpoint),
        _workload(
            "task_b",
            "L0_current_masked",
            profile_config,
            checkpoint,
            task_family="T5_terminal_boundary_near_constraint",
        ),
        _workload(
            "task_b",
            "L3_online_gru",
            profile_config,
            checkpoint,
            task_family="T5_terminal_boundary_near_constraint",
        ),
    ]
    if repeat_metadata:
        for row in workloads:
            row.update(_repeat_metadata(repeat_id="repeat_1_seed_21761"))
    if partial_repeat_metadata:
        for row in workloads:
            row.update({"training_repeat_id": "repeat_1_seed_21761"})
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    write_json(specs_path, {"executable_task_specs": specs})
    write_csv_rows(workload_path, workloads)
    return specs_path, workload_path


def _fake_rollout(workload_row, executable_spec, eval_seed):
    return {
        "return": 1.0,
        "steps": 20,
        "collision": False,
        "obstacle_completed": True,
        "min_clearance_margin": 0.25,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
        "outcome_bucket": "success",
        "termination_reason": "obstacle_completed",
        "obstacle_label": "aeb_feasible",
    }


def test_current_sim_measured_runner_preserves_metadata_with_fake_rollout(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)

    summary = runner.run_current_sim_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=216900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_measured_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["task_family_quota_pass"] is True
    assert summary["profile_quota_pass"] is True
    assert summary["history_representation_quota_pass"] is True
    assert summary["profile_counts"] == {"L0_current_masked": 2, "L3_online_gru": 2}
    assert summary["environment_rollout_started"] is True
    assert summary["policy_action_executed"] is True
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["finite_window_vs_gru_conclusion_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["next_blocker"] == "m2170-paper-route-current-sim-controlled-comparison-measured-execution-result-audit"
    assert (tmp_path / "out" / "episode_rows.csv").exists()
    assert (tmp_path / "out" / "profile_aggregate.csv").exists()
    assert (tmp_path / "out" / "history_representation_aggregate.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()
    assert not (tmp_path / "out" / "training_repeat_aggregate.csv").exists()


def test_current_sim_measured_runner_preserves_repeat_metadata_with_fake_rollout(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path, repeat_metadata=True)

    summary = runner.run_current_sim_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=216900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_measured_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["metadata_missing_count"] == 0
    assert "training_repeat_aggregate" in summary["artifacts"]

    episode_rows = runner.read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert {row["training_repeat_id"] for row in episode_rows} == {"repeat_1_seed_21761"}
    assert {row["training_seed_group"] for row in episode_rows} == {"seed_21761"}
    assert {row["checkpoint_materialization_mode"] for row in episode_rows} == {"trained_checkpoint"}

    repeat_aggregate = runner.read_csv_rows(tmp_path / "out" / "training_repeat_aggregate.csv")
    assert repeat_aggregate == [
        {
            "key": "repeat_1_seed_21761",
            "episode_count": "4",
            "success_rate": "1.0",
            "collision_rate": "0.0",
            "clearance_margin_mean": "0.25",
            "return_mean": "1.0",
            "steps_mean": "20.0",
            "all_selected_metrics_finite": "True",
        }
    ]


def test_current_sim_measured_runner_fails_closed_on_partial_repeat_metadata(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path, partial_repeat_metadata=True)

    summary = runner.run_current_sim_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=216900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False

    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "missing_repeat_metadata_field" in validation_rows
    assert "training_seed_group" in validation_rows


def test_current_sim_measured_runner_fails_closed_on_missing_checkpoints(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path, missing_checkpoint=True)

    summary = runner.run_current_sim_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=216900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=None,
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    assert summary["failure_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False

    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "missing_checkpoint_path" in validation_rows
