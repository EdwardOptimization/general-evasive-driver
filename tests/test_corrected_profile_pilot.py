from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.corrected_profile_pilot import (
    aggregate_profile_rows,
    corrected_profile_config_paths,
    finite_selected_metrics,
    training_seed,
    write_seed_config,
)


def test_corrected_profile_config_paths_find_committed_configs() -> None:
    paths = corrected_profile_config_paths()
    assert len(paths) == 12
    assert {path.name for path in paths} >= {
        "m1207_l2_window_13_current_tiled.json",
        "m1207_l2_window_25_current_tiled.json",
        "m1207_l2_window_50_current_tiled.json",
        "m1207_l2_window_100_current_tiled.json",
        "m1207_l3_reset_control_corrected.json",
    }


def test_write_seed_config_updates_seed_without_changing_profile(tmp_path: Path) -> None:
    source = Path("configs/paper_route_corrected_profiles/m1207_l3_online_gru.json")
    target = tmp_path / "seeded.json"

    config = write_seed_config(source, target, seed=123456)
    persisted = read_json(target)

    assert config["ppo"]["seed"] == 123456
    assert persisted["ppo"]["seed"] == 123456
    assert persisted["ppo"]["eval_episodes"] == 1
    assert persisted["controller_profile"]["name"] == "L3_online_gru"
    assert persisted["controller_profile"]["uses_hidden_oracle_actor_inputs"] is False


def test_training_seed_uses_base_plus_offset() -> None:
    assert training_seed(110600, 2) == 110602


def test_aggregate_profile_rows_computes_completed_profile_means() -> None:
    rows = [
        {
            "profile_name": "L1_one_step",
            "status": "completed",
            "eval_success_rate": 0.25,
            "eval_collision_rate": 0.5,
            "eval_clearance_margin_mean": 0.1,
            "eval_clearance_margin_p10": -0.1,
            "eval_return_mean": 10.0,
            "eval_termination_rate": 0.75,
            "eval_steps_mean": 50.0,
            "eval_min_clearance_margin_min": -0.2,
            "eval_lateral_rmse_mean": 1.0,
            "eval_beta_abs_error_mean": 0.2,
            "eval_control_smoothness": 0.01,
            "eval_spin_or_unstable_rate": 0.0,
            "parameter_count": 10,
        },
        {
            "profile_name": "L1_one_step",
            "status": "completed",
            "eval_success_rate": 0.75,
            "eval_collision_rate": 0.0,
            "eval_clearance_margin_mean": 0.3,
            "eval_clearance_margin_p10": 0.0,
            "eval_return_mean": 20.0,
            "eval_termination_rate": 0.25,
            "eval_steps_mean": 60.0,
            "eval_min_clearance_margin_min": -0.1,
            "eval_lateral_rmse_mean": 2.0,
            "eval_beta_abs_error_mean": 0.4,
            "eval_control_smoothness": 0.03,
            "eval_spin_or_unstable_rate": 0.0,
            "parameter_count": 10,
        },
    ]

    aggregate = aggregate_profile_rows(rows)

    assert aggregate[0]["profile_name"] == "L1_one_step"
    assert aggregate[0]["completed_seed_runs"] == 2
    assert aggregate[0]["eval_success_rate_mean"] == 0.5
    assert aggregate[0]["eval_collision_rate_mean"] == 0.25
    assert aggregate[0]["all_selected_metrics_finite"] is True
    assert finite_selected_metrics(rows[0]) is True
