from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_offtrack_support_measured_readiness as readiness
from autodrift.artifacts import write_csv_rows


def _workload_row(profile_name: str) -> dict[str, object]:
    return {
        "workload_id": f"task-a::{profile_name}",
        "task_source_id": "task-a",
        "repair_candidate_id": "task-a",
        "repair_axis": "offtrack_saturation_relief",
        "repair_split": "public_debug",
        "parent_task_source_id": "parent-a",
        "profile_name": profile_name,
        "profile_level": "L3" if profile_name.startswith("L3") else "L0",
        "profile_config_path": f"configs/{profile_name}.json",
        "checkpoint_path": "",
        "checkpoint_required_for_measured_execution": True,
        "task_family": "T5_terminal_boundary_near_constraint",
        "history_representation": "online_recurrent_hidden",
        "history_window_steps": 0,
        "reset_or_truncated_control": profile_name == "L3_reset_control",
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _profile_row(profile_name: str, checkpoint_path: Path, *, source_profile: str | None = None) -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "profile_level": "L3",
        "profile_config_path": f"configs/{profile_name}.json",
        "actor_encoder": "human_view_online_gru",
        "actor_history_length": 1,
        "env_history_length": 1,
        "observation_dim": 72,
        "training_enabled": profile_name != "L3_reset_control",
        "checkpoint_materialization_mode": "alias_same_weights_reset_hidden_control"
        if profile_name == "L3_reset_control"
        else "train_frozen_profile_config",
        "checkpoint_source_profile_name": source_profile or profile_name,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_exists": checkpoint_path.exists(),
        "input_contract": "P0_human_view_no_wheel_no_oracle",
        "uses_hidden_oracle_actor_inputs": False,
        "uses_wheel_or_slip_inputs": False,
        "uses_reference_or_ttc_inputs": False,
    }


def test_measured_readiness_joins_checkpoint_paths_and_alias(tmp_path: Path) -> None:
    online = tmp_path / "online.pt"
    online.write_text("checkpoint")
    l0 = tmp_path / "l0.pt"
    l0.write_text("checkpoint")
    workload = tmp_path / "workload.csv"
    profiles = tmp_path / "profiles.csv"
    write_csv_rows(workload, [_workload_row("L0_current_masked"), _workload_row("L3_reset_control")])
    write_csv_rows(
        profiles,
        [
            _profile_row("L0_current_masked", l0),
            _profile_row("L3_online_gru", online),
            _profile_row("L3_reset_control", online, source_profile="L3_online_gru"),
        ],
    )

    summary = readiness.materialize_measured_readiness(
        planned_workload=workload,
        profile_checkpoints=profiles,
        output_dir=tmp_path / "out",
        target_workload_count=2,
    )

    assert summary["result_class"] == "current_sim_offtrack_support_measured_readiness_pass"
    assert summary["materialized_workload_count"] == 2
    assert summary["checkpoint_path_exists_count"] == 2
    assert summary["checkpoint_path_missing_count"] == 0
    assert summary["reset_control_alias_pass"] is True
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "materialized_workload.csv").exists()


def test_measured_readiness_fails_closed_on_missing_checkpoint(tmp_path: Path) -> None:
    workload = tmp_path / "workload.csv"
    profiles = tmp_path / "profiles.csv"
    write_csv_rows(workload, [_workload_row("L0_current_masked")])
    write_csv_rows(profiles, [_profile_row("L0_current_masked", tmp_path / "missing.pt")])

    summary = readiness.materialize_measured_readiness(
        planned_workload=workload,
        profile_checkpoints=profiles,
        output_dir=tmp_path / "out",
        target_workload_count=1,
    )

    assert summary["result_class"] == "current_sim_offtrack_support_measured_readiness_fail"
    assert summary["checkpoint_path_missing_count"] == 1
    assert summary["missing_checkpoint_row_count"] == 1
