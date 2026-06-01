from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_json
from autodrift.paper_route_current_sim_matched_budget_profile_training_execution import (
    EXPECTED_BUDGET,
    EXPECTED_PROFILES,
    EXPECTED_SEED_IDS,
    aggregate_profile_rows,
    build_execution_plan,
    build_arg_parser,
)


def _write_matrix(path: Path, config_dir: Path, *, total_steps: int = 8192) -> None:
    fieldnames = [
        "matrix_id",
        "profile_name",
        "seed_id",
        "generated_config_path",
        *EXPECTED_BUDGET,
        "input_contract",
        "wheel_observation_mode",
        "obstacle_relative_velocity_mode",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for profile_name in EXPECTED_PROFILES:
            for seed_id in EXPECTED_SEED_IDS:
                config_path = config_dir / f"{profile_name}_seed{seed_id}.json"
                write_json(
                    config_path,
                    {
                        "controller_profile": {
                            "name": profile_name,
                            "input_contract": "P0_human_view_no_wheel_no_oracle",
                            "uses_hidden_oracle_actor_inputs": False,
                            "uses_wheel_or_slip_inputs": False,
                            "uses_reference_or_ttc_inputs": False,
                        },
                        "env": {
                            "include_privileged_params": False,
                            "wheel_observation_mode": "none",
                            "obstacle_relative_velocity_mode": "zero",
                        },
                        "ppo": {**EXPECTED_BUDGET, "total_steps": str(total_steps)},
                    },
                )
                writer.writerow(
                    {
                        "matrix_id": f"{profile_name}::seed_{seed_id}",
                        "profile_name": profile_name,
                        "seed_id": str(seed_id),
                        "generated_config_path": str(config_path),
                        **{**EXPECTED_BUDGET, "total_steps": str(total_steps)},
                        "input_contract": "P0_human_view_no_wheel_no_oracle",
                        "wheel_observation_mode": "none",
                        "obstacle_relative_velocity_mode": "zero",
                    }
                )


def test_build_execution_plan_validates_matrix_and_remaps_output_root(tmp_path: Path) -> None:
    matrix_path = tmp_path / "training_matrix.csv"
    config_dir = tmp_path / "configs"
    execution_root = tmp_path / "m2230_execution"
    _write_matrix(matrix_path, config_dir)

    plan, validation = build_execution_plan(training_matrix=matrix_path, execution_root=execution_root)

    assert len(plan) == 15
    assert validation["validation_pass"] is True
    assert validation["budget_signature_count"] == 1
    assert validation["contract_violation_count"] == 0
    assert validation["missing_config_count"] == 0
    assert {row["profile_name"] for row in plan} == set(EXPECTED_PROFILES)
    assert {row["seed_id"] for row in plan} == set(EXPECTED_SEED_IDS)
    assert all(str(execution_root) in row["run_dir"] for row in plan)
    assert all(str(execution_root) in row["checkpoint_path"] for row in plan)


def test_build_execution_plan_accepts_medium_expected_total_steps(tmp_path: Path) -> None:
    matrix_path = tmp_path / "training_matrix.csv"
    config_dir = tmp_path / "configs"
    _write_matrix(matrix_path, config_dir, total_steps=32768)

    _, validation = build_execution_plan(
        training_matrix=matrix_path,
        execution_root=tmp_path / "m2234_execution",
        expected_total_steps=32768,
    )

    assert validation["validation_pass"] is True
    assert validation["expected_total_steps"] == 32768


def test_aggregate_profile_rows_applies_two_of_three_quality_floor() -> None:
    rows = []
    for profile_name in EXPECTED_PROFILES:
        for index, seed_id in enumerate(EXPECTED_SEED_IDS):
            rows.append(
                {
                    "profile_name": profile_name,
                    "seed_id": seed_id,
                    "status": "completed",
                    "readiness_floor_pass": index < 2,
                    "selected_metrics_finite": True,
                    "eval_return_mean": 60.0 if index < 2 else 10.0,
                    "eval_termination_rate": 0.2 if index < 2 else 0.9,
                }
            )

    aggregate = aggregate_profile_rows(rows)

    assert len(aggregate) == len(EXPECTED_PROFILES)
    assert all(row["passing_seed_count"] == 2 for row in aggregate)
    assert all(row["readiness_floor_pass"] is True for row in aggregate)
    assert all(row["ranking_admissible"] is False for row in aggregate)


def test_arg_parser_accepts_task_id_and_expected_total_steps() -> None:
    args = build_arg_parser().parse_args(
        [
            "--expected-total-steps",
            "32768",
            "--task-id",
            "m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run",
        ]
    )

    assert args.expected_total_steps == 32768
    assert args.task_id == "m2234-paper-route-current-sim-matched-budget-medium-training-execution-implementation-and-run"
