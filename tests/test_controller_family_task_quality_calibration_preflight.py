from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.controller_family_task_quality_calibration_preflight import (
    EXPECTED_BASE_SPEC_COUNT,
    EXPECTED_PROFILE_COUNT,
    FINISH_VARIANTS,
    MAX_STEPS_SCALES,
    TRACK_WIDTH_SCALES,
    calibration_env_config,
    load_executable_specs,
    materialize_calibration_specs,
    run_calibration_preflight,
)


def test_calibration_env_config_adjusts_task_quality_axes_without_contract_change() -> None:
    spec = load_executable_specs()[0]
    base_env = spec["env_config"]

    calibrated = calibration_env_config(
        base_env,
        track_width_scale=1.5,
        finish_variant="relaxed",
        max_steps_scale=1.5,
    )

    assert calibrated["track_width"] == base_env["track_width"] * 1.5
    assert calibrated["obstacle"]["finish_pass_distance"] <= base_env["obstacle"]["finish_pass_distance"]
    assert calibrated["max_steps"] >= base_env["max_steps"]
    assert_human_view_env_contract(build_env_config(calibrated))


def test_materialize_calibration_specs_writes_all_variants_and_zero_contract_violations() -> None:
    specs = load_executable_specs()

    rows, violations = materialize_calibration_specs(specs)

    assert len(rows) == EXPECTED_BASE_SPEC_COUNT * len(TRACK_WIDTH_SCALES) * len(FINISH_VARIANTS) * len(MAX_STEPS_SCALES)
    assert violations == []
    assert {row["track_width_scale"] for row in rows} == set(TRACK_WIDTH_SCALES)
    assert {row["finish_variant"] for row in rows} == set(FINISH_VARIANTS)
    assert {row["max_steps_scale"] for row in rows} == set(MAX_STEPS_SCALES)
    assert all(row["contract_violation_count"] == 0 for row in rows)


def test_run_calibration_preflight_writes_no_rollout_matrix(tmp_path: Path) -> None:
    summary = run_calibration_preflight(output_dir=tmp_path)
    persisted = read_json(tmp_path / "summary.json")
    matrix_rows = (tmp_path / "calibration_matrix.csv").read_text(encoding="utf-8").splitlines()

    assert summary["result_class"] == "controller_family_task_quality_calibration_preflight_pass"
    assert persisted["base_spec_count"] == EXPECTED_BASE_SPEC_COUNT
    assert persisted["profile_count"] == EXPECTED_PROFILE_COUNT
    assert persisted["calibration_spec_count"] == EXPECTED_BASE_SPEC_COUNT * 12
    assert persisted["calibration_matrix_cell_count"] == EXPECTED_BASE_SPEC_COUNT * 12 * EXPECTED_PROFILE_COUNT
    assert persisted["contract_violation_count"] == 0
    assert persisted["environment_rollout_started"] is False
    assert persisted["guardrail_violation_count"] == 0
    assert len(matrix_rows) == persisted["calibration_matrix_cell_count"] + 1
