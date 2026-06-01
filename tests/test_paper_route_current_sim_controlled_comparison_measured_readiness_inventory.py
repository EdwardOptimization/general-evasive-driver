from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_controlled_comparison_measured_readiness_inventory import (
    run_current_sim_measured_readiness_inventory,
)


def _write_specs(path: Path) -> None:
    write_json(
        path,
        {
            "executable_task_specs": [
                {
                    "task_source_id": "task-0",
                    "task_family": "T1_reactive_emergency_avoidance",
                    "source_kind": "reactive_avoidance",
                    "source_reference": "unit",
                    "materialization_semantics": "current_sim_executable_spec_v0",
                    "env_config": {"history_length": 1},
                },
                {
                    "task_source_id": "task-1",
                    "task_family": "T5_terminal_boundary_near_constraint",
                    "source_kind": "terminal_boundary",
                    "source_reference": "unit",
                    "materialization_semantics": "current_sim_executable_spec_v0",
                    "env_config": {"history_length": 1},
                },
            ]
        },
    )


def _write_workload(path: Path, profile_config: Path) -> None:
    rows = [
        {
            "workload_id": "task-0::L0",
            "task_source_id": "task-0",
            "benchmark_spec_id": "bench-0",
            "profile_name": "L0",
            "profile_level": "L0_current_observation",
            "profile_config_path": str(profile_config),
            "checkpoint_path": "",
            "checkpoint_required_for_measured_execution": "true",
            "task_family": "T1_reactive_emergency_avoidance",
            "history_representation": "current_response",
            "history_window_steps": "1",
            "reset_or_truncated_control": "false",
            "environment_reset_scheduled": "false",
            "environment_rollout_scheduled": "false",
            "training_scheduled": "false",
            "profile_specific_tuning": "false",
            "controller_family_ranking_claim_made": "false",
            "finite_window_vs_gru_conclusion_made": "false",
            "paper_level_claim_made": "false",
            "level3_self_id_claim_made": "false",
        },
        {
            "workload_id": "task-1::L3",
            "task_source_id": "task-1",
            "benchmark_spec_id": "bench-1",
            "profile_name": "L3",
            "profile_level": "L3_recurrent",
            "profile_config_path": str(profile_config),
            "checkpoint_path": str(path.parent / "missing.pt"),
            "checkpoint_required_for_measured_execution": "true",
            "task_family": "T5_terminal_boundary_near_constraint",
            "history_representation": "online_gru",
            "history_window_steps": "100",
            "reset_or_truncated_control": "false",
            "environment_reset_scheduled": "false",
            "environment_rollout_scheduled": "false",
            "training_scheduled": "false",
            "profile_specific_tuning": "false",
            "controller_family_ranking_claim_made": "false",
            "finite_window_vs_gru_conclusion_made": "false",
            "paper_level_claim_made": "false",
            "level3_self_id_claim_made": "false",
        },
    ]
    write_csv_rows(path, rows)


def test_current_sim_measured_readiness_inventory_reports_checkpoint_and_schema_gaps(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    output_dir = tmp_path / "out"
    profile_config = tmp_path / "profile.json"
    profile_config.write_text("{}", encoding="utf-8")
    _write_specs(specs_path)
    _write_workload(workload_path, profile_config)

    summary = run_current_sim_measured_readiness_inventory(
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        output_dir=output_dir,
        target_spec_count=2,
        target_workload_count=2,
        target_profile_count=2,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_measured_readiness_inventory_complete"
    assert summary["input_executable_spec_count"] == 2
    assert summary["input_workload_count"] == 2
    assert summary["profile_count"] == 2
    assert summary["checkpoint_required_workload_count"] == 2
    assert summary["checkpoint_path_missing_count"] == 1
    assert summary["checkpoint_path_present_count"] == 1
    assert summary["checkpoint_path_exists_count"] == 0
    assert summary["workload_ready_count"] == 0
    assert summary["profile_ready_count"] == 0
    assert summary["old_runner_compatible_with_current_sim_panel"] is False
    assert summary["old_runner_missing_field_count"] > 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["guardrail_violation_count"] == 0

    persisted = read_json(output_dir / "summary.json")
    assert persisted["next_blocker"] == "next-audit"
    assert (output_dir / "workload_readiness_rows.csv").exists()
    assert (output_dir / "profile_readiness_rows.csv").exists()
    assert (output_dir / "runner_schema_gap_rows.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    assert (output_dir / "run_state.json").exists()
