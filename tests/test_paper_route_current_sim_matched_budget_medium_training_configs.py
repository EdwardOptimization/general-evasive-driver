from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift import paper_route_current_sim_matched_budget_medium_training_configs as materializer


def test_medium_training_config_materialization_writes_32768_step_matrix(tmp_path: Path) -> None:
    source_dir = Path("configs/paper_route_profiles/m2227_matched_budget_short_v0")
    output_dir = tmp_path / "run"
    config_dir = tmp_path / "configs"

    summary = materializer.materialize_medium_training_configs(
        output_dir=output_dir,
        config_output_dir=config_dir,
        source_config_dir=source_dir,
    )

    assert summary["result_class"] == "current_sim_matched_budget_medium_training_config_materialization_pass"
    assert summary["generated_config_count"] == 15
    assert summary["training_matrix_row_count"] == 15
    assert summary["medium_total_steps_count"] == 15
    assert summary["budget_matched"] is True
    assert summary["contract_violation_count"] == 0
    assert summary["training_started"] is False

    for generated_path in summary["artifacts"]["generated_configs"]:
        config = read_json(generated_path)
        assert config["matched_budget_training_protocol"]["stage"] == "matched_budget_medium_v1"
        assert config["ppo"]["total_steps"] == 32768
        assert config["ppo"]["rollout_steps"] == 128
        assert config["ppo"]["eval_episodes"] == 32
        assert config["controller_profile"]["uses_hidden_oracle_actor_inputs"] is False
        assert config["controller_profile"]["uses_wheel_or_slip_inputs"] is False
        assert config["env"]["wheel_observation_mode"] == "none"


def test_medium_config_filename_is_seed_specific() -> None:
    assert (
        materializer.config_filename("L2_window_50", 222603)
        == "m2233_matched_budget_medium_v1_l2_window_50_seed222603.json"
    )
