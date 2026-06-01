from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_current_sim_matched_budget_profile_training_configs as materializer
from autodrift.artifacts import read_json


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_matched_budget_config_materialization_writes_equal_budget_matrix(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    config_dir = tmp_path / "configs"

    summary = materializer.materialize_matched_budget_profile_training_configs(
        output_dir=output_dir,
        config_output_dir=config_dir,
    )

    assert summary["result_class"] == "current_sim_matched_budget_profile_training_config_materialization_pass"
    assert summary["trainable_profile_count"] == 5
    assert summary["seeds_per_profile"] == 3
    assert summary["generated_config_count"] == 15
    assert summary["training_matrix_row_count"] == 15
    assert summary["budget_matched"] is True
    assert summary["seed_policy_matched"] is True
    assert summary["contract_violation_count"] == 0
    assert summary["training_started"] is False

    matrix_rows = _rows(output_dir / "training_matrix.csv")
    assert len(matrix_rows) == 15
    assert {row["seed_id"] for row in matrix_rows} == {"222601", "222602", "222603"}
    assert {row["total_steps"] for row in matrix_rows} == {"8192"}
    assert {row["rollout_steps"] for row in matrix_rows} == {"128"}
    assert {row["num_envs"] for row in matrix_rows} == {"4"}
    assert {row["eval_episodes"] for row in matrix_rows} == {"32"}
    assert all(row["training_started"] == "False" for row in matrix_rows)
    assert all(row["ranking_admissible"] == "False" for row in matrix_rows)

    for generated_path in summary["artifacts"]["generated_configs"]:
        config = read_json(generated_path)
        assert config["matched_budget_training_protocol"]["training_started"] is False
        assert config["controller_profile"]["uses_hidden_oracle_actor_inputs"] is False
        assert config["controller_profile"]["uses_wheel_or_slip_inputs"] is False
        assert config["controller_profile"]["uses_reference_or_ttc_inputs"] is False
        assert config["env"]["include_privileged_params"] is False
        assert config["env"]["wheel_observation_mode"] == "none"
        assert config["env"]["obstacle_relative_velocity_mode"] == "zero"
        assert config["ppo"]["total_steps"] == 8192
        assert config["ppo"]["eval_episodes"] == 32

    plan_rows = _rows(output_dir / "profile_plan.csv")
    reset_row = next(row for row in plan_rows if row["profile_name"] == "L3_reset_control")
    assert reset_row["trainable"] == "False"
    assert reset_row["alias_checkpoint_source_profile"] == "L3_online_gru"


def test_config_filename_is_seed_specific() -> None:
    assert (
        materializer.config_filename("L3_online_gru", 222601)
        == "m2227_matched_budget_short_v0_l3_online_gru_seed222601.json"
    )
