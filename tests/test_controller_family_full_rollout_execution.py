from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json
from autodrift.controller_family_full_rollout_execution import (
    append_csv_row,
    aggregate_profile_outcome_rows,
    aggregate_rows,
    comparison_rows,
    env_config_for_executable_profile,
    read_csv_rows,
    selected_metrics_are_finite,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract


def _first_executable_spec() -> dict:
    return read_json(
        "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json"
    )["executable_task_specs"][0]


def test_env_config_for_executable_profile_preserves_profile_history_and_p0_contract() -> None:
    profile_config = read_json("runs/m1674_controller_family_one_seed_public_pilot/configs/L2_window_25_seed167400.json")

    env_config = env_config_for_executable_profile(
        executable_spec=_first_executable_spec(),
        profile_config=profile_config,
    )

    assert env_config.history_length == 25
    assert env_config.action_history_mode == "full"
    assert env_config.include_privileged_params is False
    assert env_config.wheel_observation_mode == "none"
    assert env_config.obstacle_relative_velocity_mode == "zero"
    assert_human_view_env_contract(env_config)


def test_append_csv_row_recovers_empty_header_file(tmp_path: Path) -> None:
    path = tmp_path / "failure_rows.csv"
    path.write_text("\n", encoding="utf-8")

    append_csv_row(path, {"workload_id": "w0", "error_type": "ValueError"})

    rows = read_csv_rows(path)
    assert rows == [{"workload_id": "w0", "error_type": "ValueError"}]


def test_aggregates_parse_csv_boolean_strings_correctly() -> None:
    rows = [
        {
            "profile_name": "L1_one_step",
            "task_source_id": "spec0",
            "task_family": "T4",
            "executable_source_family": "t4_capability_step_temporal",
            "success": "True",
            "collision": "False",
            "min_clearance_margin": "0.2",
            "return": "1.0",
            "steps": "10",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
        {
            "profile_name": "L1_one_step",
            "task_source_id": "spec1",
            "task_family": "T5",
            "executable_source_family": "t5_near_boundary_warmup",
            "success": "False",
            "collision": "True",
            "min_clearance_margin": "-0.1",
            "return": "-1.0",
            "steps": "8",
            "action_rate_mean": "0.3",
            "high_sideslip_fraction": "0.8",
        },
    ]

    aggregates = aggregate_rows(rows, "profile_name")

    assert selected_metrics_are_finite(rows) is True
    assert len(aggregates) == 1
    assert aggregates[0]["success_rate"] == 0.5
    assert aggregates[0]["collision_rate"] == 0.5
    assert np.isfinite(float(aggregates[0]["clearance_margin_p10"]))


def test_comparison_rows_include_required_diagnostic_boundaries() -> None:
    profile_names = [
        "L0_current_masked",
        "L1_one_step",
        "L2_window_13",
        "L2_window_13_current_tiled",
        "L2_window_25",
        "L2_window_25_current_tiled",
        "L2_window_50",
        "L2_window_50_current_tiled",
        "L2_window_100",
        "L2_window_100_current_tiled",
        "L3_online_gru",
        "L3_reset_control_corrected",
    ]
    rows = []
    for index, profile_name in enumerate(profile_names):
        rows.append(
            {
                "profile_name": profile_name,
                "task_family": "T4" if index % 2 == 0 else "T5",
                "strata": "all_72_specs;explicit_window_subset"
                if index % 2 == 0
                else "all_72_specs;mapping_window_unspecified",
                "success": "True" if index % 3 else "False",
                "collision": "False",
                "min_clearance_margin": str(0.01 * index),
                "return": str(float(index)),
                "steps": "10",
                "action_rate_mean": "0.1",
                "high_sideslip_fraction": "0.0",
            }
        )

    comparisons = {row["comparison"]: row for row in comparison_rows(rows)}

    assert "L2_window_13_normal_minus_current_tiled" in comparisons
    assert "L3_online_minus_L3_reset_control" in comparisons
    assert "L3_online_minus_best_L2_normal" in comparisons
    assert "L1_one_step_minus_history_capable" in comparisons
    assert "task_family_T4_minus_T5" in comparisons
    assert "explicit_window_subset_minus_all_72_specs" in comparisons
    assert "mapping_window_unspecified_minus_all_72_specs" in comparisons
    assert all(row["diagnostic_only_no_ranking_claim"] for row in comparisons.values())


def test_profile_outcome_aggregate_uses_profile_and_outcome_bucket() -> None:
    rows = [
        {
            "profile_name": "L3_online_gru",
            "task_source_id": "spec0",
            "task_family": "T5",
            "executable_source_family": "t5_near_boundary_warmup",
            "outcome_bucket": "success_obstacle_pass",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.2,
            "return": 1.0,
            "steps": 10,
            "action_rate_mean": 0.1,
            "high_sideslip_fraction": 0.0,
        },
        {
            "profile_name": "L3_online_gru",
            "task_source_id": "spec1",
            "task_family": "T5",
            "executable_source_family": "t5_near_boundary_warmup",
            "outcome_bucket": "off_track_noncollision_noncompletion",
            "success": False,
            "collision": False,
            "min_clearance_margin": 0.4,
            "return": -1.0,
            "steps": 8,
            "action_rate_mean": 0.2,
            "high_sideslip_fraction": 0.0,
        },
    ]

    aggregates = aggregate_profile_outcome_rows(rows)
    keys = {row["profile_outcome"] for row in aggregates}

    assert keys == {
        "L3_online_gru::success_obstacle_pass",
        "L3_online_gru::off_track_noncollision_noncompletion",
    }
