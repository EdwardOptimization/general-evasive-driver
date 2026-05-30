from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_bounded_calibration_smoke_preflight import (
    EXPECTED_BOUNDED_CALIBRATION_SPEC_COUNT,
    EXPECTED_BOUNDED_SMOKE_CELL_COUNT,
    EXPECTED_TASK_FAMILY_COUNTS,
    base_spec_rows,
    load_calibration_specs,
    run_bounded_calibration_smoke_preflight,
    select_source_diverse_base_specs,
)


def test_select_source_diverse_base_specs_keeps_task_family_budget() -> None:
    bases = base_spec_rows(load_calibration_specs())

    selected, rejected = select_source_diverse_base_specs(bases)

    assert len(selected) == sum(EXPECTED_TASK_FAMILY_COUNTS.values())
    assert len(rejected) == len(bases) - len(selected)
    assert {row["base_task_source_id"] for row in selected}.isdisjoint(
        {row["base_task_source_id"] for row in rejected}
    )
    assert {
        task_family: sum(row["task_family"] == task_family for row in selected)
        for task_family in EXPECTED_TASK_FAMILY_COUNTS
    } == EXPECTED_TASK_FAMILY_COUNTS


def test_run_bounded_calibration_smoke_preflight_writes_no_rollout_subset(tmp_path: Path) -> None:
    summary = run_bounded_calibration_smoke_preflight(output_dir=tmp_path)
    persisted = read_json(tmp_path / "summary.json")
    matrix_rows = (tmp_path / "bounded_smoke_matrix.csv").read_text(encoding="utf-8").splitlines()
    selected_rows = (tmp_path / "selected_base_specs.csv").read_text(encoding="utf-8").splitlines()
    spec_rows = (tmp_path / "bounded_calibration_specs.csv").read_text(encoding="utf-8").splitlines()

    assert summary["result_class"] == "controller_family_bounded_calibration_smoke_preflight_pass"
    assert persisted["selected_task_family_counts"] == EXPECTED_TASK_FAMILY_COUNTS
    assert persisted["selected_base_spec_count"] == sum(EXPECTED_TASK_FAMILY_COUNTS.values())
    assert persisted["bounded_calibration_spec_count"] == EXPECTED_BOUNDED_CALIBRATION_SPEC_COUNT
    assert persisted["bounded_smoke_matrix_cell_count"] == EXPECTED_BOUNDED_SMOKE_CELL_COUNT
    assert persisted["variants_per_base_spec_min"] == 12
    assert persisted["variants_per_base_spec_max"] == 12
    assert persisted["profiles_per_calibration_spec_min"] == 12
    assert persisted["profiles_per_calibration_spec_max"] == 12
    assert persisted["contract_violation_count"] == 0
    assert persisted["environment_rollout_started"] is False
    assert persisted["guardrail_violation_count"] == 0
    assert len(matrix_rows) == EXPECTED_BOUNDED_SMOKE_CELL_COUNT + 1
    assert len(selected_rows) == sum(EXPECTED_TASK_FAMILY_COUNTS.values()) + 1
    assert len(spec_rows) == EXPECTED_BOUNDED_CALIBRATION_SPEC_COUNT + 1
