from autodrift.controller_family_calibrated_scale_up_execution import (
    TARGET_EPISODE_COUNT,
    TARGET_SCALE_UP_VARIANT_COUNT,
    aggregate_outcome_rows,
    load_scale_up_calibration_specs,
    scale_up_executable_specs,
    scale_up_workload_rows,
)


def test_scale_up_execution_inputs_preserve_calibrated_shape() -> None:
    specs = scale_up_executable_specs(load_scale_up_calibration_specs())
    workload = scale_up_workload_rows()

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["task_source_id"] for row in workload} == {row["calibration_spec_id"] for row in specs}
    assert all(row["workload_id"] == row["scale_up_workload_id"] for row in workload)
    assert all("calibrated_scale_up" in row["strata"] for row in workload)
    assert len({row["scale_up_variant_label"] for row in workload}) == TARGET_SCALE_UP_VARIANT_COUNT


def test_scale_up_variant_aggregate_reports_task_quality_rates() -> None:
    rows = [
        {
            "scale_up_variant_label": "mid_calibration_variant",
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
            "scale_up_variant_label": "mid_calibration_variant",
            "outcome_bucket": "collision_failure",
            "min_clearance_margin": "-0.5",
            "return": "-1.0",
            "steps": "8",
            "success": "False",
            "collision": "True",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
    ]

    [aggregate] = aggregate_outcome_rows(rows, ("scale_up_variant_label",))

    assert aggregate["episode_count"] == 2
    assert aggregate["success_obstacle_pass_rate"] == 0.5
    assert aggregate["collision_failure_rate"] == 0.5
    assert aggregate["all_selected_metrics_finite"] is True
