from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_profile_runtime_smoke import (
    generated_config_paths,
    run_runtime_smoke,
    smoke_one_profile,
)


def test_generated_config_paths_find_all_profiles() -> None:
    paths = generated_config_paths("configs/paper_route_profiles")
    assert len(paths) == 8
    assert {path.name for path in paths} >= {
        "m1190_l0_current_masked_smoke.json",
        "m1190_l1_one_step_smoke.json",
        "m1190_l2_window_100_smoke.json",
        "m1190_l3_online_gru_smoke.json",
    }


def test_generated_corrected_config_paths_find_all_profiles() -> None:
    paths = generated_config_paths("configs/paper_route_corrected_profiles", config_glob="m1207_*.json")
    assert len(paths) == 8
    assert {path.name for path in paths} >= {
        "m1207_l2_window_13_current_tiled.json",
        "m1207_l2_window_25_current_tiled.json",
        "m1207_l3_reset_control_corrected.json",
    }


def test_l0_runtime_smoke_observes_masked_previous_commands() -> None:
    row = smoke_one_profile("configs/paper_route_profiles/m1190_l0_current_masked_smoke.json", seed=1192)
    assert row["profile_name"] == "L0_current_masked"
    assert row["mask_enabled"] is True
    assert row["raw_step_previous_command_abs_sum"] > 0.0
    assert row["wrapped_step_previous_command_abs_sum"] == 0.0
    assert row["mask_observed"] is True
    assert row["passed"] is True


def test_current_tiled_runtime_smoke_observes_generated_transform() -> None:
    row = smoke_one_profile(
        "configs/paper_route_corrected_profiles/m1207_l2_window_25_current_tiled.json",
        seed=1208,
    )
    assert row["profile_name"] == "L2_window_25_current_tiled"
    assert row["history_transform"] == "current_tiled"
    assert row["current_tiled_expected"] is True
    assert row["wrapped_reset_current_tiled"] is True
    assert row["wrapped_step_current_tiled"] is True
    assert row["raw_step_current_tiled"] is False
    assert row["current_tiled_observed"] is True
    assert row["passed"] is True


def test_corrected_reset_control_runtime_smoke_routes_every_step_policy() -> None:
    row = smoke_one_profile(
        "configs/paper_route_corrected_profiles/m1207_l3_reset_control_corrected.json",
        seed=1208,
    )
    assert row["profile_name"] == "L3_reset_control_corrected"
    assert row["reset_hidden_policy"] == "every_step_control"
    assert row["reset_policy_routing_ok"] is True
    assert row["passed"] is True


def test_runtime_smoke_writes_no_training_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "smoke"
    summary = run_runtime_smoke(config_dir="configs/paper_route_profiles", run_dir=run_dir, seed=1192)

    assert summary["config_count"] == 8
    assert summary["all_configs_instantiated"] is True
    assert summary["l0_mask_observed"] is True
    assert summary["unmasked_profiles_unchanged"] is True
    assert summary["training_started"] is False
    assert summary["optimizer_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "profile_runtime_rows.csv").exists()
    persisted = read_json(run_dir / "summary.json")
    assert persisted["result_class"] == "controller_profile_runtime_smoke_pass"


def test_corrected_runtime_smoke_writes_no_training_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "corrected-smoke"
    summary = run_runtime_smoke(
        config_dir="configs/paper_route_corrected_profiles",
        config_glob="m1207_*.json",
        run_dir=run_dir,
        seed=1208,
    )

    assert summary["config_count"] == 8
    assert summary["all_configs_instantiated"] is True
    assert summary["current_tiled_profile_count"] == 2
    assert summary["current_tiled_profiles_observed"] is True
    assert summary["corrected_reset_profile_count"] == 1
    assert summary["corrected_reset_policy_routing_ok"] is True
    assert summary["training_started"] is False
    assert summary["optimizer_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "profile_runtime_rows.csv").exists()
    persisted = read_json(run_dir / "summary.json")
    assert persisted["result_class"] == "controller_profile_runtime_smoke_pass"
