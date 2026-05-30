from autodrift.artifacts import read_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight import (
    FAMILY_REPAIR_RULES,
    TARGET_RESET_STRESS_ROW_COUNT,
    repaired_scenario_matrix_rows,
    repaired_scenario_specs,
    run_reset_stress_cell,
    sampling_repair_delta_rows,
)
from autodrift.task_quality_scenario_taxonomy_execution import load_scenario_specs


def test_sampling_repair_specs_preserve_shape_and_mark_target_families() -> None:
    specs = repaired_scenario_specs()

    assert len(specs) == 72
    assert len({spec["scenario_family"] for spec in specs}) == 6
    assert all(spec["labels_enter_actor_input"] is False for spec in specs)
    assert all(spec["m1728_scenario_spec_id"] == spec["scenario_spec_id"] for spec in specs)
    for spec in specs:
        if spec["scenario_family"] in FAMILY_REPAIR_RULES:
            assert spec["sampling_repair_applied"] is True
            assert spec["sampling_repair_source"] == "m1733_family_repair_v1"
        else:
            assert spec["sampling_repair_applied"] is False


def test_sampling_repair_matrix_keeps_full_profile_product() -> None:
    specs = repaired_scenario_specs()
    matrix = repaired_scenario_matrix_rows(repaired_specs=specs)

    assert len(matrix) == TARGET_RESET_STRESS_ROW_COUNT
    assert len({row["scenario_spec_id"] for row in matrix}) == 72
    assert len({row["profile_name"] for row in matrix}) == 12
    assert all(row["reset_stress_scheduled"] is True for row in matrix)
    assert all(row["policy_rollout_scheduled"] is False for row in matrix)


def test_sampling_repair_delta_rows_capture_family_updates() -> None:
    original = load_scenario_specs()
    repaired = repaired_scenario_specs()
    rows = sampling_repair_delta_rows(original_specs=original, repaired_specs=repaired)

    assert rows
    assert any(row["config_path"] == "env_config.speed_range" for row in rows)
    assert any(row["config_path"] == "env_config.obstacle.distance_range" for row in rows)
    assert any(row["sampling_repair_variant_id"] == "no_sampling_repair_needed" for row in rows)


def test_sampling_repair_reset_stress_cell_repairs_stable_aes_sampling() -> None:
    specs = repaired_scenario_specs()
    matrix = [
        row
        for row in repaired_scenario_matrix_rows(repaired_specs=specs)
        if row["scenario_family"] == "aeb_infeasible_stable_aes" and row["profile_name"] == "L0_current_masked"
    ]
    spec_by_id = {spec["scenario_spec_id"]: spec for spec in specs}
    profiles = profile_artifact_rows(m1674_run_dir=DEFAULT_M1674_RUN_DIR)
    profile_config = read_json(next(row["config_path"] for row in profiles if row["profile_name"] == "L0_current_masked"))

    row = run_reset_stress_cell(
        matrix_row=matrix[0],
        repaired_spec=spec_by_id[matrix[0]["scenario_spec_id"]],
        profile_config=profile_config,
        eval_seed=173100 + 144,
    )

    assert row["reset_success"] is True
    assert row["sampled_obstacle_label"] == "aes_feasible"
    assert row["policy_rollout_started"] is False
