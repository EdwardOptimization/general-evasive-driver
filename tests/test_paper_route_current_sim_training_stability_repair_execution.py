from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift import paper_route_current_sim_training_stability_repair_execution as repair
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _config(profile: str) -> dict[str, Any]:
    return {
        "ppo": {
            "total_steps": 32768,
            "rollout_steps": 128,
            "num_envs": 4,
            "update_epochs": 2,
            "minibatch_size": 256,
            "learning_rate": 0.0001,
            "clip_coef": 0.1,
            "max_grad_norm": 0.25,
            "eval_episodes": 32,
            "checkpoint_interval_steps": 0,
        },
        "env": {
            "include_privileged_params": False,
            "wheel_observation_mode": "none",
            "obstacle_relative_velocity_mode": "zero",
        },
        "controller_profile": {
            "name": profile,
            "input_contract": "P0_human_view_no_wheel_no_oracle",
            "uses_hidden_oracle_actor_inputs": False,
            "uses_wheel_or_slip_inputs": False,
            "uses_reference_or_ttc_inputs": False,
            "observation_mask": "none",
            "previous_command_mask_indices": [],
            "history_transform": "none",
            "reset_hidden_policy": "not_applicable",
        },
    }


def _matrix(tmp_path: Path, *, write_configs: bool = True) -> Path:
    rows = []
    for profile in repair.EXPECTED_PROFILES:
        for seed in repair.EXPECTED_SEED_IDS:
            config_path = tmp_path / "configs" / profile / f"seed_{seed}" / "config.json"
            if write_configs:
                write_json(config_path, _config(profile))
            rows.append(
                {
                    "matrix_id": f"{profile}::seed_{seed}",
                    "profile_name": profile,
                    "seed_id": seed,
                    "generated_config_path": str(config_path),
                }
            )
    path = tmp_path / "training_matrix.csv"
    write_csv_rows(path, rows)
    return path


def _fake_runner(cmd: Sequence[str], cwd: Path, env: Mapping[str, str], stdout: Any) -> int:
    del cwd, env, stdout
    save_path = Path(cmd[cmd.index("--save") + 1])
    run_dir = Path(cmd[cmd.index("--run-dir") + 1])
    save_path.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    for step in repair.CANDIDATE_STEPS:
        if step == repair.EXPECTED_TOTAL_STEPS:
            continue
        path = save_path.parent / "checkpoints" / f"checkpoint_step_{step}.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake")
    save_path.write_bytes(b"fake")
    write_json(
        run_dir / "eval_summary.json",
        {
            "return_mean": 35.0,
            "steps_mean": 60.0,
            "termination_rate": 0.8,
            "lateral_rmse_mean": 2.0,
            "beta_abs_error_mean": 0.2,
        },
    )
    return 0


def _fake_evaluator(
    checkpoint_path: Path,
    config: Mapping[str, Any],
    seed_id: int,
    eval_episodes: int,
    device: str,
) -> dict[str, float]:
    del config, seed_id, eval_episodes, device
    if checkpoint_path.name == "checkpoint.pt":
        step = repair.EXPECTED_TOTAL_STEPS
    else:
        step = int(checkpoint_path.stem.split("_")[-1])
    if step == 8192:
        return {
            "return_mean": 60.0,
            "steps_mean": 70.0,
            "termination_rate": 0.2,
            "lateral_rmse_mean": 0.5,
            "beta_abs_error_mean": 0.1,
        }
    return {
        "return_mean": 30.0,
        "steps_mean": 55.0,
        "termination_rate": 0.9,
        "lateral_rmse_mean": 3.0,
        "beta_abs_error_mean": 0.3,
    }


def test_training_stability_repair_selects_periodic_checkpoint(tmp_path: Path) -> None:
    summary = repair.execute_training_stability_repair(
        training_matrix=_matrix(tmp_path),
        output_dir=tmp_path / "out",
        command_runner=_fake_runner,
        candidate_evaluator=_fake_evaluator,
    )

    assert summary["result_class"] == "current_sim_training_stability_repair_execution_pass"
    assert summary["completed_run_count"] == 15
    assert summary["candidate_eval_count"] == 120
    assert summary["selected_checkpoint_count"] == 15
    assert summary["selected_checkpoint_profile_floor_pass_count"] == 5
    assert summary["selected_beats_final_count"] == 15
    repair_config = read_json(tmp_path / "out" / "configs" / "L0_current_masked" / "seed_222601" / "config.json")
    assert repair_config["ppo"]["checkpoint_interval_steps"] == 4096
    selected_rows = repair._read_csv(tmp_path / "out" / "selected_checkpoint_rows.csv")
    assert all(row["selected_checkpoint_step"] == "8192" for row in selected_rows)


def test_training_stability_repair_fails_on_missing_configs(tmp_path: Path) -> None:
    summary = repair.execute_training_stability_repair(
        training_matrix=_matrix(tmp_path, write_configs=False),
        output_dir=tmp_path / "out",
        command_runner=_fake_runner,
        candidate_evaluator=_fake_evaluator,
    )

    assert summary["result_class"] == "current_sim_training_stability_repair_execution_fail"
    assert summary["missing_config_count"] == 15
    assert summary["candidate_eval_count"] == 0
