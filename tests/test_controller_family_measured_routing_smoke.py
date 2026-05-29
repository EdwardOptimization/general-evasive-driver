from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_measured_routing_smoke import (
    ROUTING_SOURCE_FAMILIES,
    aggregate_rows,
    assert_human_view_env_contract,
    discover_m1674_profile_runs,
    select_routing_smoke_specs,
    selected_metrics_are_finite,
    task_env_for_profile,
)


def test_discover_m1674_profile_runs_finds_all_expected_artifacts() -> None:
    rows = discover_m1674_profile_runs()

    assert [row["profile_name"] for row in rows] == list(EXPECTED_PROFILE_NAMES)
    assert all(row["config_exists"] for row in rows)
    assert all(row["checkpoint_exists"] for row in rows)
    assert all(not row["contract_violations"] for row in rows)


def test_select_routing_smoke_specs_is_source_diverse_and_p0() -> None:
    specs = select_routing_smoke_specs()

    assert [spec.source_family for spec in specs] == list(ROUTING_SOURCE_FAMILIES)
    assert {spec.task_family for spec in specs} == {"T4", "T5"}
    for spec in specs:
        assert_human_view_env_contract(spec.env_config)
        assert spec.env_config.history_length == 1
        assert spec.env_config.obstacle_relative_velocity_mode == "zero"
        assert spec.env_config.wheel_observation_mode == "none"
        assert spec.env_config.include_privileged_params is False


def test_task_env_for_profile_preserves_profile_history_without_oracle_inputs() -> None:
    config = read_json("runs/m1674_controller_family_one_seed_public_pilot/configs/L2_window_25_seed167400.json")
    spec = select_routing_smoke_specs()[0]

    env_config = task_env_for_profile(profile_config=config, task_spec=spec)

    assert env_config.history_length == 25
    assert env_config.obstacle.enabled is True
    assert env_config.obstacle_relative_velocity_mode == "zero"
    assert env_config.wheel_observation_mode == "none"
    assert env_config.include_privileged_params is False
    assert_human_view_env_contract(env_config)


def test_selected_metric_finiteness_and_aggregates() -> None:
    rows = [
        {
            "profile_name": "L1_one_step",
            "task_source_id": "m1686-spec-0000",
            "task_family": "T4",
            "source_family": "t4_staged_warmup_capability",
            "obstacle_completed": True,
            "collision": False,
            "min_clearance_margin": 0.1,
            "return": 1.0,
            "steps": 10,
            "action_rate_mean": 0.2,
            "high_sideslip_fraction": 0.0,
        },
        {
            "profile_name": "L1_one_step",
            "task_source_id": "m1686-spec-0001",
            "task_family": "T5",
            "source_family": "t5_near_boundary_warmup",
            "obstacle_completed": False,
            "collision": True,
            "min_clearance_margin": -0.2,
            "return": -1.0,
            "steps": 8,
            "action_rate_mean": 0.4,
            "high_sideslip_fraction": 0.8,
        },
    ]

    aggregates = aggregate_rows(rows, "profile_name")

    assert selected_metrics_are_finite(rows) is True
    assert len(aggregates) == 1
    assert aggregates[0]["episode_count"] == 2
    assert aggregates[0]["success_rate"] == 0.5
    assert aggregates[0]["collision_rate"] == 0.5
    assert np.isfinite(float(aggregates[0]["clearance_margin_p10"]))
