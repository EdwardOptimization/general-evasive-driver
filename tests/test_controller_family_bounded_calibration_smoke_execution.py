from autodrift.controller_family_bounded_calibration_smoke_execution import (
    TARGET_EPISODE_COUNT,
    aggregate_outcome_rows,
    calibration_executable_specs,
    calibration_workload_rows,
    load_bounded_calibration_specs,
)


def test_calibration_execution_inputs_preserve_bounded_smoke_shape() -> None:
    specs = calibration_executable_specs(load_bounded_calibration_specs())
    workload = calibration_workload_rows()

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["task_source_id"] for row in workload} == {row["calibration_spec_id"] for row in specs}
    assert all(row["workload_id"] == row["calibration_workload_id"] for row in workload)
    assert all("bounded_calibration_smoke" in row["strata"] for row in workload)


def test_aggregate_outcome_rows_reports_task_quality_rates() -> None:
    rows = [
        {
            "track_width_scale": "1.0",
            "finish_variant": "original",
            "max_steps_scale": "1.0",
            "outcome_bucket": "success_obstacle_pass",
            "min_clearance_margin": "1.0",
            "return": "2.0",
            "steps": "10",
            "success": "True",
            "collision": "False",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
        {
            "track_width_scale": "1.0",
            "finish_variant": "original",
            "max_steps_scale": "1.0",
            "outcome_bucket": "off_track_noncollision_noncompletion",
            "min_clearance_margin": "-0.5",
            "return": "-1.0",
            "steps": "8",
            "success": "False",
            "collision": "False",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
    ]

    [aggregate] = aggregate_outcome_rows(rows, ("track_width_scale", "finish_variant", "max_steps_scale"))

    assert aggregate["episode_count"] == 2
    assert aggregate["success_obstacle_pass_rate"] == 0.5
    assert aggregate["off_track_noncollision_noncompletion_rate"] == 0.5
    assert aggregate["collision_failure_rate"] == 0.0
    assert aggregate["all_selected_metrics_finite"] is True
