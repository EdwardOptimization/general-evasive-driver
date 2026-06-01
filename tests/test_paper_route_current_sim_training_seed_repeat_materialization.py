from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_json
from autodrift.paper_route_current_sim_training_seed_repeat_materialization import (
    RESET_CONTROL_PROFILE,
    materialize_training_seed_repeats,
)


PROFILE_NAMES = [
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_25",
    "L2_window_50",
    "L2_window_100",
    "L3_online_gru",
    "L3_reset_control",
]


def _profile_config(path: Path, *, profile_name: str, training_enabled: bool) -> None:
    write_json(
        path,
        {
            "controller_profile": {
                "name": profile_name,
                "level": "test",
                "actor_encoder": "human_view_online_gru" if profile_name.startswith("L3") else "mlp",
                "actor_history_length": 1,
                "env_history_length": 1,
                "observation_dim": 72,
                "training_enabled": training_enabled,
                "input_contract": "P0_human_view_no_wheel_no_oracle",
                "uses_hidden_oracle_actor_inputs": False,
                "uses_wheel_or_slip_inputs": False,
                "uses_reference_or_ttc_inputs": False,
            },
            "env": {},
            "ppo": {"total_steps": 1},
        },
    )


def _write_workload(path: Path, config_dir: Path, *, checkpoint_paths: bool) -> None:
    fieldnames = [
        "workload_id",
        "task_source_id",
        "benchmark_spec_id",
        "profile_name",
        "profile_level",
        "profile_config_path",
        "checkpoint_path",
        "checkpoint_required_for_measured_execution",
        "task_family",
        "history_representation",
        "history_window_steps",
        "reset_or_truncated_control",
        "environment_reset_scheduled",
        "environment_rollout_scheduled",
        "training_scheduled",
        "profile_specific_tuning",
        "controller_family_ranking_claim_made",
        "finite_window_vs_gru_conclusion_made",
        "paper_level_claim_made",
        "level3_self_id_claim_made",
    ]
    rows = []
    for task_index in range(2):
        for profile_name in PROFILE_NAMES:
            checkpoint = ""
            if checkpoint_paths:
                checkpoint_file = config_dir / "existing" / profile_name / "checkpoint.pt"
                checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
                checkpoint_file.write_text("checkpoint", encoding="utf-8")
                checkpoint = str(checkpoint_file)
            rows.append(
                {
                    "workload_id": f"task-{task_index}::{profile_name}",
                    "task_source_id": f"task-{task_index}",
                    "benchmark_spec_id": "spec",
                    "profile_name": profile_name,
                    "profile_level": "test",
                    "profile_config_path": str(config_dir / f"{profile_name}.json"),
                    "checkpoint_path": checkpoint,
                    "checkpoint_required_for_measured_execution": "True",
                    "task_family": "T",
                    "history_representation": "test",
                    "history_window_steps": "1",
                    "reset_or_truncated_control": str(profile_name == RESET_CONTROL_PROFILE),
                    "environment_reset_scheduled": "False",
                    "environment_rollout_scheduled": "False",
                    "training_scheduled": "False",
                    "profile_specific_tuning": "False",
                    "controller_family_ranking_claim_made": "False",
                    "finite_window_vs_gru_conclusion_made": "False",
                    "paper_level_claim_made": "False",
                    "level3_self_id_claim_made": "False",
                }
            )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_repeat_materialization_trains_two_new_groups_and_aliases_reset(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    for profile_name in PROFILE_NAMES:
        _profile_config(config_dir / f"{profile_name}.json", profile_name=profile_name, training_enabled=profile_name != RESET_CONTROL_PROFILE)
    base_workload = tmp_path / "base_workload.csv"
    existing_workload = tmp_path / "existing_workload.csv"
    _write_workload(base_workload, config_dir, checkpoint_paths=False)
    _write_workload(existing_workload, config_dir, checkpoint_paths=True)

    def fake_runner(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
        checkpoint_path = Path(command[command.index("--save") + 1])
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("checkpoint", encoding="utf-8")
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("ok", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return 0

    summary = materialize_training_seed_repeats(
        base_workload=base_workload,
        existing_materialized_workload=existing_workload,
        output_dir=tmp_path / "out",
        target_new_workload_count=32,
        training_runner=fake_runner,
    )

    assert summary["result_class"] == "current_sim_training_seed_repeat_materialization_pass"
    assert summary["repeat_group_count"] == 3
    assert summary["new_training_command_count"] == 14
    assert summary["successful_training_command_count"] == 14
    assert summary["new_materialized_workload_count"] == 32
    assert summary["checkpoint_path_missing_count"] == 0
    assert summary["checkpoint_path_exists_count"] == 32
    assert summary["reset_control_trained_count"] == 0
    rows = _rows(tmp_path / "out" / "profile_checkpoint_rows.csv")
    reset_rows = [row for row in rows if row["profile_name"] == RESET_CONTROL_PROFILE]
    assert len(reset_rows) == 2
    assert all(row["checkpoint_materialization_mode"] == "alias_same_weights_reset_hidden_control" for row in reset_rows)
    assert all(row["training_started_for_profile"] == "False" for row in reset_rows)


def test_repeat_materialization_fails_closed_on_training_failure(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    for profile_name in PROFILE_NAMES:
        _profile_config(config_dir / f"{profile_name}.json", profile_name=profile_name, training_enabled=profile_name != RESET_CONTROL_PROFILE)
    base_workload = tmp_path / "base_workload.csv"
    existing_workload = tmp_path / "existing_workload.csv"
    _write_workload(base_workload, config_dir, checkpoint_paths=False)
    _write_workload(existing_workload, config_dir, checkpoint_paths=True)

    def failing_runner(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("failed", encoding="utf-8")
        return 3

    summary = materialize_training_seed_repeats(
        base_workload=base_workload,
        existing_materialized_workload=existing_workload,
        output_dir=tmp_path / "out",
        target_new_workload_count=32,
        training_runner=failing_runner,
    )

    assert summary["result_class"] == "current_sim_training_seed_repeat_materialization_fail_closed"
    assert summary["failed_training_command_count"] == 14
    assert summary["checkpoint_path_exists_count"] == 0
    assert summary["measured_rollout_started"] is False
    assert summary["guardrail_violation_count"] == 0
