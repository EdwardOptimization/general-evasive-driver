from autodrift.task_quality_outcome_semantics_materialization_preflight import (
    EVALUATION_ROLES,
    PRIMARY_METRIC_FAMILIES,
    materialized_matrix_rows,
    materialized_spec_rows,
    metric_support_rows,
    outcome_semantics_registry_rows,
    run_outcome_semantics_materialization_preflight,
    unsupported_metric_gap_rows,
    validate_registry_metric_subsets,
)
from autodrift.task_quality_scenario_taxonomy_execution import load_scenario_specs
from autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight import repaired_scenario_matrix_rows


def test_semantics_registry_covers_roles_and_metric_families() -> None:
    rows = outcome_semantics_registry_rows()

    assert len(rows) == 6
    assert {row["evaluation_role"] for row in rows} == set(EVALUATION_ROLES)
    assert {row["primary_metric_family"] for row in rows} == set(PRIMARY_METRIC_FAMILIES)
    assert any(row["scenario_family"] == "unavoidable_mitigation" and row["evaluation_role"] == "mitigation_diagnostic" for row in rows)
    assert any(row["scenario_family"] == "off_track_boundary_stress" and row["diagnostic_only_no_ranking_claim"] for row in rows)


def test_metric_support_gaps_are_explicit_not_silent() -> None:
    support_rows = metric_support_rows()
    gap_rows = unsupported_metric_gap_rows()

    assert support_rows
    assert gap_rows
    assert all(row["silently_approximated"] is False for row in support_rows)
    assert any(row["metric_name"] == "impact_severity_proxy" for row in gap_rows)
    assert any(row["metric_name"] == "hidden_dynamics_robustness" for row in gap_rows)
    assert validate_registry_metric_subsets() == []


def test_materialized_specs_and_matrix_join_semantics() -> None:
    specs = load_scenario_specs("runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json")
    spec_rows = materialized_spec_rows(specs)
    matrix_rows = materialized_matrix_rows(
        repaired_scenario_matrix_rows(
            repaired_specs=specs,
            matrix_path="runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv",
        ),
        spec_rows,
    )

    assert len(spec_rows) == 72
    assert len(matrix_rows) == 864
    assert all("evaluation_role" in row for row in matrix_rows)
    assert all("primary_metric_family" in row for row in matrix_rows)
    assert any(row["benchmark_row"] is True for row in matrix_rows)
    assert any(row["diagnostic_only_no_ranking_claim"] is True for row in matrix_rows)


def test_outcome_semantics_materialization_smoke(tmp_path) -> None:
    summary = run_outcome_semantics_materialization_preflight(output_dir=tmp_path)

    assert summary["result_class"] == "task_quality_outcome_semantics_materialization_preflight_pass"
    assert summary["scenario_spec_count"] == 72
    assert summary["scenario_matrix_cell_count"] == 864
    assert summary["benchmark_role_present"] is True
    assert summary["diagnostic_stress_role_present"] is True
    assert summary["mitigation_diagnostic_role_present"] is True
    assert summary["unsupported_metric_gap_count"] > 0
    assert summary["registry_metric_error_count"] == 0
    assert summary["silent_unsupported_approximation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert (tmp_path / "outcome_semantics_registry.csv").exists()
    assert (tmp_path / "semantics_scenario_matrix.csv").exists()
