from autodrift.task_quality_scenario_taxonomy_execution import (
    TARGET_EPISODE_COUNT,
    TARGET_SCENARIO_FAMILY_COUNT,
    TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT,
    aggregate_outcome_rows,
    load_scenario_specs,
    load_unsupported_feature_rows,
    scenario_taxonomy_workload_rows,
)
from autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1734_OUTPUT_DIR,
)


def test_scenario_taxonomy_execution_inputs_preserve_metadata_join() -> None:
    specs = load_scenario_specs()
    workload = scenario_taxonomy_workload_rows()

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["scenario_spec_id"] for row in workload} == {row["scenario_spec_id"] for row in specs}
    assert all(row["workload_id"] == row["scenario_workload_id"] for row in workload)
    assert all("scenario_taxonomy" in row["strata"] for row in workload)
    assert len({row["profile_name"] for row in workload}) == 12
    assert len({row["scenario_family"] for row in workload}) == TARGET_SCENARIO_FAMILY_COUNT
    assert all(row["labels_enter_actor_input"] is False for row in workload)
    assert all(row["allowed_labels_metadata_only"] for row in workload)
    assert all(row["hidden_dynamics_bucket"] for row in workload)
    assert all(row["road_boundary_bucket"] for row in workload)
    assert all(row["obstacle_timing_bucket"] for row in workload)


def test_repaired_scenario_taxonomy_execution_inputs_preserve_repair_provenance() -> None:
    specs = load_scenario_specs(DEFAULT_M1734_OUTPUT_DIR / "repaired_scenario_specs.json")
    workload = scenario_taxonomy_workload_rows(
        scenario_specs_path=DEFAULT_M1734_OUTPUT_DIR / "repaired_scenario_specs.json",
        workload_path=DEFAULT_M1734_OUTPUT_DIR / "repaired_scenario_matrix.csv",
    )

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["scenario_spec_id"] for row in workload} == {row["scenario_spec_id"] for row in specs}
    assert any(row["sampling_repair_variant_id"] == "stable_aes_sampling_window_v1" for row in workload)
    assert any(row["sampling_repair_applied"] is True for row in workload)
    assert all(row["m1728_scenario_spec_id"] == row["scenario_spec_id"] for row in workload)
    assert all("scenario_taxonomy" in row["strata"] for row in workload)


def test_scenario_family_aggregate_reports_task_quality_rates() -> None:
    rows = [
        {
            "scenario_family": "drift_required_avoidance",
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
            "scenario_family": "drift_required_avoidance",
            "outcome_bucket": "off_track_noncollision_noncompletion",
            "min_clearance_margin": "0.1",
            "return": "-1.0",
            "steps": "8",
            "success": "False",
            "collision": "False",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
    ]

    [aggregate] = aggregate_outcome_rows(rows, ("scenario_family",))

    assert aggregate["episode_count"] == 2
    assert aggregate["success_obstacle_pass_rate"] == 0.5
    assert aggregate["off_track_noncollision_noncompletion_rate"] == 0.5
    assert aggregate["all_selected_metrics_finite"] is True


def test_sampled_label_aggregate_reports_task_quality_rates() -> None:
    rows = [
        {
            "sampled_obstacle_label": "aes_feasible",
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
            "sampled_obstacle_label": "aes_feasible",
            "outcome_bucket": "collision_failure",
            "min_clearance_margin": "-0.2",
            "return": "-1.0",
            "steps": "8",
            "success": "False",
            "collision": "True",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        },
    ]

    [aggregate] = aggregate_outcome_rows(rows, ("sampled_obstacle_label",))

    assert aggregate["episode_count"] == 2
    assert aggregate["success_obstacle_pass_rate"] == 0.5
    assert aggregate["collision_failure_rate"] == 0.5


def test_unsupported_feature_rows_preserve_explicit_boundary() -> None:
    rows = load_unsupported_feature_rows()

    assert len(rows) == TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT
    assert all(str(row["silently_approximated"]).lower() == "false" for row in rows)
    assert all(str(row["covered_by_current_preflight"]).lower() == "false" for row in rows)
