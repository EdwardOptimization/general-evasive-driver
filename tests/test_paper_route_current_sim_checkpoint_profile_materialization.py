from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_json
from autodrift.paper_route_current_sim_checkpoint_profile_materialization import (
    RESET_CONTROL_PROFILE,
    materialize_profile_checkpoints,
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
    actor_encoder = "human_view_online_gru" if profile_name.startswith("L3") else "mlp"
    actor_history_length = 1
    env_history_length = 1
    observation_dim = 72
    if profile_name.startswith("L2_window_"):
        actor_encoder = "temporal_gru"
        actor_history_length = int(profile_name.rsplit("_", 1)[-1])
        env_history_length = actor_history_length
        observation_dim = 72 * actor_history_length
    write_json(
        path,
        {
            "controller_profile": {
                "name": profile_name,
                "level": "test",
                "actor_encoder": actor_encoder,
                "actor_history_length": actor_history_length,
                "env_history_length": env_history_length,
                "observation_dim": observation_dim,
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


def _workload(path: Path, config_dir: Path) -> None:
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
            config_path = config_dir / f"{profile_name}.json"
            rows.append(
                {
                    "workload_id": f"task-{task_index}::{profile_name}",
                    "task_source_id": f"task-{task_index}",
                    "benchmark_spec_id": "spec",
                    "profile_name": profile_name,
                    "profile_level": "test",
                    "profile_config_path": str(config_path),
                    "checkpoint_path": "",
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


def test_materialization_trains_seven_profiles_and_aliases_reset_control(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    for profile_name in PROFILE_NAMES:
        _profile_config(config_dir / f"{profile_name}.json", profile_name=profile_name, training_enabled=profile_name != RESET_CONTROL_PROFILE)
    workload_path = tmp_path / "workload.csv"
    _workload(workload_path, config_dir)

    def fake_runner(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
        checkpoint_path = Path(command[command.index("--save") + 1])
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("checkpoint", encoding="utf-8")
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("ok", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return 0

    summary = materialize_profile_checkpoints(
        workload_path=workload_path,
        output_dir=tmp_path / "out",
        target_workload_count=16,
        target_profile_count=8,
        training_runner=fake_runner,
    )

    assert summary["result_class"] == "current_sim_checkpoint_profile_materialization_pass"
    assert summary["training_command_count"] == 7
    assert summary["successful_training_command_count"] == 7
    assert summary["alias_profile_count"] == 1
    assert summary["checkpoint_path_missing_count"] == 0
    assert summary["checkpoint_path_exists_count"] == 16
    profile_rows = _rows(tmp_path / "out" / "profile_checkpoint_rows.csv")
    reset_row = next(row for row in profile_rows if row["profile_name"] == RESET_CONTROL_PROFILE)
    online_row = next(row for row in profile_rows if row["profile_name"] == "L3_online_gru")
    assert reset_row["checkpoint_path"] == online_row["checkpoint_path"]
    assert reset_row["checkpoint_materialization_mode"] == "alias_same_weights_reset_hidden_control"
    assert reset_row["training_started_for_profile"] == "False"


def test_materialization_fails_closed_when_checkpoint_training_fails(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    for profile_name in PROFILE_NAMES:
        _profile_config(config_dir / f"{profile_name}.json", profile_name=profile_name, training_enabled=profile_name != RESET_CONTROL_PROFILE)
    workload_path = tmp_path / "workload.csv"
    _workload(workload_path, config_dir)

    def failing_runner(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("failed", encoding="utf-8")
        return 7

    summary = materialize_profile_checkpoints(
        workload_path=workload_path,
        output_dir=tmp_path / "out",
        target_workload_count=16,
        target_profile_count=8,
        training_runner=failing_runner,
    )

    assert summary["result_class"] == "current_sim_checkpoint_profile_materialization_fail_closed"
    assert summary["failed_training_command_count"] == 7
    assert summary["checkpoint_path_exists_count"] == 0
    assert summary["measured_rollout_started"] is False
    assert summary["guardrail_violation_count"] == 0
