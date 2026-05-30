from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    TARGET_EXECUTABLE_SPECS,
    TARGET_WORKLOAD_CELLS,
    choose_executable_source_family,
    env_template_family,
    materialize_executable_spec,
    run_materialization_preflight,
    source_family_task_map,
)


def _first_spec() -> dict:
    return read_json(
        "runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json"
    )["task_source_specs"][0]


def test_choose_executable_source_family_prefers_matching_task_family() -> None:
    family_task = source_family_task_map()
    spec = {
        "task_source_id": "unit",
        "task_family": "T5",
        "source_family_left": "actuator_delay_step",
        "source_family_right": "t5_near_boundary_warmup",
    }

    family, rule = choose_executable_source_family(spec, family_task)

    assert family == "t5_near_boundary_warmup"
    assert rule == "task_family_matched_endpoint"


def test_env_template_family_maps_proxy_sources() -> None:
    assert env_template_family("t4_actuator_delay_response") == (
        "t4_actuator_delay_response",
        "direct_env_template",
    )
    assert env_template_family("curved_boundary_obstacle") == (
        "t5_boundary_axis_retarget",
        "proxy_env_template",
    )


def test_materialize_executable_spec_preserves_p0_contract() -> None:
    spec = materialize_executable_spec(_first_spec())
    checks = spec["contract_checks"]
    env_config = spec["env_config"]

    assert spec["task_source_id"] == "m1680-spec-0000"
    assert all(checks.values())
    assert env_config["history_length"] == 1
    assert env_config["action_history_mode"] == "full"
    assert env_config["include_privileged_params"] is False
    assert env_config["wheel_observation_mode"] == "none"
    assert env_config["obstacle_relative_velocity_mode"] == "zero"


def test_run_materialization_preflight_writes_72_specs_and_864_cells(tmp_path: Path) -> None:
    summary = run_materialization_preflight(output_dir=tmp_path)

    executable_payload = read_json(tmp_path / "executable_task_specs.json")
    workload_rows = (tmp_path / "executable_workload_matrix.csv").read_text(encoding="utf-8").splitlines()
    persisted_summary = read_json(tmp_path / "summary.json")

    assert summary["passes_public_smoke_gates"] is True
    assert persisted_summary["executable_spec_count"] == TARGET_EXECUTABLE_SPECS
    assert persisted_summary["workload_cell_count"] == TARGET_WORKLOAD_CELLS
    assert persisted_summary["reference_workload_cell_count"] == TARGET_WORKLOAD_CELLS
    assert persisted_summary["contract_violation_count"] == 0
    assert persisted_summary["unmappable_spec_count"] == 0
    assert persisted_summary["guardrail_violation_count"] == 0
    assert persisted_summary["environment_rollout_started"] is False
    assert persisted_summary["training_started"] is False
    assert len(executable_payload["executable_task_specs"]) == TARGET_EXECUTABLE_SPECS
    assert len(workload_rows) == TARGET_WORKLOAD_CELLS + 1
