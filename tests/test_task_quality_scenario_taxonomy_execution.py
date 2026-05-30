from autodrift.artifacts import write_csv_rows
import autodrift.task_quality_scenario_taxonomy_execution as scenario_execution
from autodrift.task_quality_scenario_taxonomy_execution import (
    COLLISION_FINITE_FIELDS,
    OBSTACLE_PASS_FINITE_FIELDS,
    RECOVERY_SUCCESS_FINITE_FIELDS,
    SCENARIO_SEMANTICS_FIELDS,
    TARGET_EPISODE_COUNT,
    TARGET_SCENARIO_FAMILY_COUNT,
    TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT,
    _run_scenario_workload_cell,
    aggregate_outcome_rows,
    load_scenario_specs,
    load_unsupported_feature_rows,
    metric_completeness_rows,
    run_scenario_taxonomy_execution,
    scenario_taxonomy_workload_rows,
)
from autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1734_OUTPUT_DIR,
)
from autodrift.task_quality_outcome_semantics_materialization_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1743_OUTPUT_DIR,
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


def test_semantics_scenario_taxonomy_inputs_preserve_outcome_semantics() -> None:
    specs = load_scenario_specs(DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_specs.json")
    workload = scenario_taxonomy_workload_rows(
        scenario_specs_path=DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_specs.json",
        workload_path=DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_matrix.csv",
    )

    assert len(specs) == 72
    assert len(workload) == TARGET_EPISODE_COUNT
    assert {row["scenario_spec_id"] for row in workload} == {row["scenario_spec_id"] for row in specs}
    assert all(field in workload[0] for field in SCENARIO_SEMANTICS_FIELDS)
    assert {row["evaluation_role"] for row in workload} == {
        "benchmark",
        "diagnostic_stress",
        "mitigation_diagnostic",
    }
    assert {row["primary_metric_family"] for row in workload} >= {
        "avoidance_success",
        "controlled_drift_recovery",
        "hidden_dynamics_robustness",
    }
    assert all(row["labels_enter_actor_input"] is False for row in workload)
    assert all(row["training_scheduled"] == "False" for row in workload)


def test_run_scenario_workload_cell_preserves_semantics_passthrough(monkeypatch) -> None:
    workload = scenario_taxonomy_workload_rows(
        scenario_specs_path=DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_specs.json",
        workload_path=DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_matrix.csv",
    )
    workload_row = workload[0]

    def fake_run_workload_cell(**_: object) -> dict[str, object]:
        return {
            "workload_id": workload_row["workload_id"],
            "profile_name": workload_row["profile_name"],
            "obstacle_label": "aes_feasible",
        }

    monkeypatch.setattr(
        "autodrift.task_quality_scenario_taxonomy_execution.run_workload_cell",
        fake_run_workload_cell,
    )

    row = _run_scenario_workload_cell(
        workload_row=workload_row,
        executable_spec={"scenario_spec_id": workload_row["scenario_spec_id"]},
        profile_config={},
        model=None,
        profile_row={},
        eval_seed=1,
    )

    for field in SCENARIO_SEMANTICS_FIELDS:
        assert row[field] == workload_row[field]
    assert row["sampled_obstacle_label"] == "aes_feasible"
    assert row["controller_family_ranking_claim_made"] is False


def test_run_execution_uses_separate_executable_scenario_specs_path(monkeypatch, tmp_path) -> None:
    load_paths: list[str] = []

    workload_row = {
        "workload_id": "w0",
        "scenario_workload_id": "w0",
        "scenario_spec_id": "s0",
        "scenario_family_id": "S1",
        "scenario_family": "ordinary_stable_avoidance",
        "scenario_role": "normal",
        "profile_name": "p0",
        "obstacle_timing_bucket": "medium",
        "obstacle_lateral_bucket": "center",
        "road_boundary_bucket": "nominal",
        "hidden_dynamics_bucket": "nominal",
        "template_source_family": "template",
        "allowed_labels_metadata_only": "aes_feasible",
        "labels_enter_actor_input": False,
        "m1728_scenario_spec_id": "s0",
        "sampling_repair_source": "m1728_original",
        "sampling_repair_variant_id": "none",
        "sampling_repair_applied": False,
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
        "ranking_eligible_after_audit": True,
        "diagnostic_only_no_ranking_claim": False,
        "benchmark_row": True,
        "metric_required_benchmark_success": True,
        "metric_required_avoidance_success": True,
        "metric_required_controlled_drift_recovery_success": False,
        "metric_required_collision_mitigation_score": False,
        "metric_required_impact_severity_proxy": False,
        "metric_required_off_track_violation": True,
        "metric_required_off_track_severity_proxy": True,
        "metric_required_recovery_success": True,
        "metric_required_recovery_time_proxy": True,
        "metric_required_hidden_dynamics_robustness": False,
        "metric_required_diagnostic_only_no_ranking_claim": False,
    }

    def fake_load_scenario_specs(path):
        load_paths.append(str(path))
        return [{"scenario_spec_id": "s0", "env_config": {}}]

    def fake_run_cell(**_: object) -> dict[str, object]:
        row = _complete_metric_row(
            workload_id="w0",
            scenario_workload_id="w0",
            scenario_spec_id="s0",
            profile_name="p0",
        )
        row.update(
            {
                "scenario_family": "ordinary_stable_avoidance",
                "scenario_role": "normal",
                "hidden_dynamics_bucket": "nominal",
                "road_boundary_bucket": "nominal",
                "obstacle_timing_bucket": "medium",
                "obstacle_lateral_bucket": "center",
                "sampled_obstacle_label": "aes_feasible",
                "outcome_bucket": "success_obstacle_pass",
                "termination_reason": "obstacle_passed",
                "success": True,
                "return": 1.0,
                "steps": 10,
                "min_clearance_margin": 0.5,
                "action_rate_mean": 0.1,
                "high_sideslip_fraction": 0.0,
                "template_source_family": "template",
                "allowed_labels_metadata_only": "aes_feasible",
                "labels_enter_actor_input": False,
                "m1728_scenario_spec_id": "s0",
                "sampling_repair_source": "m1728_original",
                "sampling_repair_variant_id": "none",
                "sampling_repair_applied": False,
                **{field: workload_row[field] for field in SCENARIO_SEMANTICS_FIELDS},
            }
        )
        return row

    unsupported_path = tmp_path / "unsupported.csv"
    write_csv_rows(
        unsupported_path,
        [
            {
                "unsupported_feature": f"feature_{index}",
                "silently_approximated": False,
                "covered_by_current_preflight": False,
            }
            for index in range(TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT)
        ],
    )

    monkeypatch.setattr(scenario_execution, "load_scenario_specs", fake_load_scenario_specs)
    monkeypatch.setattr(scenario_execution, "scenario_taxonomy_workload_rows", lambda **_: [workload_row])
    monkeypatch.setattr(scenario_execution, "profile_artifact_rows", lambda **_: [{"profile_name": "p0"}])
    monkeypatch.setattr(scenario_execution, "_load_profile_cache", lambda *_args, **_kwargs: {"p0": ({}, None)})
    monkeypatch.setattr(scenario_execution, "_run_scenario_workload_cell", fake_run_cell)

    summary = run_scenario_taxonomy_execution(
        output_dir=tmp_path / "run",
        scenario_specs_path=tmp_path / "metadata_specs.json",
        executable_scenario_specs_path=tmp_path / "executable_specs.json",
        workload_path=tmp_path / "matrix.csv",
        unsupported_features_path=unsupported_path,
        resume=False,
    )

    assert load_paths == [str(tmp_path / "executable_specs.json")]
    assert summary["episode_count"] == 1
    assert summary["metric_completeness_failure_count"] == 0


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


def _complete_metric_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "workload_id": "w0",
        "scenario_workload_id": "w0",
        "scenario_spec_id": "s0",
        "profile_name": "p0",
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
        "ranking_eligible_after_audit": True,
        "diagnostic_only_no_ranking_claim": False,
        "benchmark_row": True,
        "metric_required_benchmark_success": True,
        "metric_required_avoidance_success": True,
        "metric_required_controlled_drift_recovery_success": False,
        "metric_required_collision_mitigation_score": False,
        "metric_required_impact_severity_proxy": False,
        "metric_required_off_track_violation": True,
        "metric_required_off_track_severity_proxy": True,
        "metric_required_recovery_success": True,
        "metric_required_recovery_time_proxy": True,
        "metric_required_hidden_dynamics_robustness": False,
        "metric_required_diagnostic_only_no_ranking_claim": False,
        "dt": 0.02,
        "track_width": 6.0,
        "max_abs_beta": 0.12,
        "max_abs_yaw_rate": 0.4,
        "max_off_track_overshoot": 0.0,
        "off_track_severity_proxy": 0.0,
        "collision_mitigation_score": 0.0,
        "recovery_success": True,
        "drift_used": False,
        "controlled_drift_recovery_success": True,
        "collision": False,
        "obstacle_passed_raw": True,
        "first_obstacle_pass_step": 50,
        "first_obstacle_pass_time_s": 1.0,
        "first_recovery_step": 75,
        "first_recovery_time_s": 1.5,
        "recovery_time_proxy": 0.5,
        "impact_speed_proxy": "",
        "impact_beta_abs": "",
        "impact_yaw_rate_abs": "",
        "impact_severity_proxy": "",
    }
    row.update(overrides)
    return row


def test_metric_completeness_accepts_applicability_aware_nan_slots() -> None:
    pass_row = _complete_metric_row()
    collision_row = _complete_metric_row(
        workload_id="w1",
        scenario_workload_id="w1",
        collision=True,
        obstacle_passed_raw=False,
        recovery_success=False,
        controlled_drift_recovery_success=False,
        first_obstacle_pass_step="",
        first_obstacle_pass_time_s="",
        first_recovery_step="",
        first_recovery_time_s="",
        recovery_time_proxy="",
        impact_speed_proxy=8.0,
        impact_beta_abs=0.2,
        impact_yaw_rate_abs=0.6,
        impact_severity_proxy=8.16,
        collision_mitigation_score=8.16,
    )

    summary, failures = metric_completeness_rows([pass_row, collision_row])

    assert failures == []
    assert summary
    pass_fields = {row["field"] for row in summary if row["rule"] == "finite_when_obstacle_passed"}
    recovery_fields = {row["field"] for row in summary if row["rule"] == "finite_when_recovered"}
    collision_fields = {row["field"] for row in summary if row["rule"] == "finite_when_collision"}
    assert pass_fields == set(OBSTACLE_PASS_FINITE_FIELDS)
    assert recovery_fields == set(RECOVERY_SUCCESS_FINITE_FIELDS)
    assert collision_fields == set(COLLISION_FINITE_FIELDS)


def test_metric_completeness_reports_missing_applicable_fields() -> None:
    _, failures = metric_completeness_rows(
        [
            _complete_metric_row(
                collision=True,
                impact_speed_proxy="",
                impact_beta_abs=0.2,
                impact_yaw_rate_abs=0.6,
                impact_severity_proxy=8.16,
            )
        ]
    )

    assert [failure["field"] for failure in failures] == ["impact_speed_proxy"]
    assert failures[0]["rule"] == "finite_when_collision"
