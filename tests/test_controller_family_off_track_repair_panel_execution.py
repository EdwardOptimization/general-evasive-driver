from autodrift.controller_family_off_track_repair_panel_execution import (
    EXPECTED_REPAIR_VARIANT_LABELS,
    TARGET_EPISODE_COUNT,
    TARGET_REPAIR_VARIANT_COUNT,
    aggregate_outcome_rows,
    load_repair_panel_specs,
    repair_panel_executable_specs,
    repair_panel_workload_rows,
)


def test_repair_panel_execution_inputs_preserve_panel_shape() -> None:
    specs = repair_panel_executable_specs(load_repair_panel_specs())
    workload = repair_panel_workload_rows()

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["task_source_id"] for row in workload} == {row["calibration_spec_id"] for row in specs}
    assert all(row["workload_id"] == row["repair_panel_workload_id"] for row in workload)
    assert all("off_track_repair_panel" in row["strata"] for row in workload)
    assert len({row["repair_variant_label"] for row in workload}) == TARGET_REPAIR_VARIANT_COUNT
    assert {row["repair_variant_label"] for row in workload} == set(EXPECTED_REPAIR_VARIANT_LABELS)


def test_repair_variant_aggregate_reports_task_quality_rates() -> None:
    rows = [
        {
            "repair_variant_label": "wide_relaxed_extended",
            "outcome_bucket": "off_track_noncollision_noncompletion",
            "min_clearance_margin": "0.1",
            "return": "2.0",
            "steps": "10",
            "success": "False",
            "collision": "False",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
        {
            "repair_variant_label": "wide_relaxed_extended",
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

    [aggregate] = aggregate_outcome_rows(rows, ("repair_variant_label",))

    assert aggregate["episode_count"] == 2
    assert aggregate["collision_failure_rate"] == 0.5
    assert aggregate["off_track_noncollision_noncompletion_rate"] == 0.5
    assert aggregate["all_selected_metrics_finite"] is True
