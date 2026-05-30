from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.task_quality_scenario_taxonomy_preflight import (
    EXPECTED_PROFILE_COUNT,
    EXPECTED_SCENARIO_FAMILY_COUNT,
    EXPECTED_SCENARIO_MATRIX_CELL_COUNT,
    EXPECTED_SCENARIO_SPEC_COUNT,
    EXPECTED_SCENARIO_SPECS_PER_FAMILY,
    materialize_scenario_specs,
    run_scenario_taxonomy_preflight,
    scenario_matrix_rows,
    unsupported_scenario_feature_rows,
)


def test_scenario_taxonomy_specs_preserve_family_balance() -> None:
    specs, violations = materialize_scenario_specs()

    family_counts: dict[str, int] = {}
    for spec in specs:
        family_counts[str(spec["scenario_family"])] = family_counts.get(str(spec["scenario_family"]), 0) + 1

    assert len(specs) == EXPECTED_SCENARIO_SPEC_COUNT
    assert len(family_counts) == EXPECTED_SCENARIO_FAMILY_COUNT
    assert set(family_counts.values()) == {EXPECTED_SCENARIO_SPECS_PER_FAMILY}
    assert not violations
    assert all(spec["labels_enter_actor_input"] is False for spec in specs)


def test_scenario_taxonomy_matrix_preserves_profile_controls() -> None:
    specs, _violations = materialize_scenario_specs()
    matrix = scenario_matrix_rows(specs)

    assert len(matrix) == EXPECTED_SCENARIO_MATRIX_CELL_COUNT
    assert len({row["profile_name"] for row in matrix}) == EXPECTED_PROFILE_COUNT
    assert all(row["scenario_workload_id"] == f"{row['scenario_spec_id']}::{row['profile_name']}" for row in matrix)
    assert all(row["environment_rollout_scheduled"] is False for row in matrix)
    assert all(row["training_scheduled"] is False for row in matrix)
    assert all(row["profile_specific_tuning"] is False for row in matrix)


def test_unsupported_fault_features_are_explicit_not_silently_approximated() -> None:
    rows = unsupported_scenario_feature_rows()

    assert rows
    assert all(row["silently_approximated"] is False for row in rows)
    assert {row["planned_family"] for row in rows} == {"hidden_dynamics_stress"}


def test_scenario_taxonomy_preflight_writes_required_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "m1728"
    summary = run_scenario_taxonomy_preflight(output_dir=output)

    assert summary["result_class"] == "task_quality_scenario_taxonomy_preflight_pass"
    assert summary["scenario_family_count"] == EXPECTED_SCENARIO_FAMILY_COUNT
    assert summary["scenario_spec_count"] == EXPECTED_SCENARIO_SPEC_COUNT
    assert summary["scenario_matrix_cell_count"] == EXPECTED_SCENARIO_MATRIX_CELL_COUNT
    assert summary["contract_violation_count"] == 0
    assert summary["silent_unsupported_approximation_count"] == 0
    assert (output / "scenario_taxonomy.json").exists()
    assert (output / "unsupported_scenario_features.csv").exists()
    assert len(read_json(output / "scenario_specs.json")["scenario_specs"]) == EXPECTED_SCENARIO_SPEC_COUNT
    assert len(read_csv_rows(output / "scenario_matrix.csv")) == EXPECTED_SCENARIO_MATRIX_CELL_COUNT
