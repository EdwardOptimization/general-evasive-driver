from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_bounded_calibration_smoke_preflight import base_spec_rows, load_calibration_specs, read_csv_rows
from autodrift.controller_family_calibrated_scale_up_preflight import (
    DEFAULT_M1705_SELECTED_BASE_SPECS,
    EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT,
    EXPECTED_SCALE_UP_MATRIX_CELL_COUNT,
    EXPECTED_SELECTED_BASE_SPEC_COUNT,
    EXPECTED_TASK_FAMILY_COUNTS,
    VARIANT_PANEL,
    run_calibrated_scale_up_preflight,
    scale_up_specs,
    select_scale_up_base_specs,
)


def test_select_scale_up_base_specs_keeps_anchors_and_task_budget() -> None:
    specs = load_calibration_specs()
    bases = base_spec_rows(specs)
    anchors = read_csv_rows(DEFAULT_M1705_SELECTED_BASE_SPECS)

    selected, rejected = select_scale_up_base_specs(bases, anchors)

    anchor_ids = {row["base_task_source_id"] for row in anchors}
    selected_ids = {row["base_task_source_id"] for row in selected}
    assert len(selected) == EXPECTED_SELECTED_BASE_SPEC_COUNT
    assert anchor_ids.issubset(selected_ids)
    assert len(rejected) == len(bases) - len(selected)
    assert {
        task_family: sum(row["task_family"] == task_family for row in selected)
        for task_family in EXPECTED_TASK_FAMILY_COUNTS
    } == EXPECTED_TASK_FAMILY_COUNTS


def test_scale_up_specs_keeps_only_four_labeled_variants() -> None:
    specs = load_calibration_specs()
    bases = base_spec_rows(specs)
    anchors = read_csv_rows(DEFAULT_M1705_SELECTED_BASE_SPECS)
    selected, _ = select_scale_up_base_specs(bases, anchors)

    rows = scale_up_specs(specs, {row["base_task_source_id"] for row in selected})

    assert len(rows) == EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT
    assert {row["scale_up_variant_label"] for row in rows} == {
        str(variant["scale_up_variant_label"]) for variant in VARIANT_PANEL
    }
    assert all(row["base_task_source_id"] in {item["base_task_source_id"] for item in selected} for row in rows)


def test_run_calibrated_scale_up_preflight_writes_no_rollout_subset(tmp_path: Path) -> None:
    summary = run_calibrated_scale_up_preflight(output_dir=tmp_path)
    persisted = read_json(tmp_path / "summary.json")
    matrix_rows = (tmp_path / "scale_up_matrix.csv").read_text(encoding="utf-8").splitlines()
    selected_rows = (tmp_path / "selected_base_specs.csv").read_text(encoding="utf-8").splitlines()
    spec_rows = (tmp_path / "scale_up_calibration_specs.csv").read_text(encoding="utf-8").splitlines()

    assert summary["result_class"] == "controller_family_calibrated_scale_up_preflight_pass"
    assert persisted["selected_task_family_counts"] == EXPECTED_TASK_FAMILY_COUNTS
    assert persisted["selected_base_spec_count"] == EXPECTED_SELECTED_BASE_SPEC_COUNT
    assert persisted["scale_up_calibration_spec_count"] == EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT
    assert persisted["scale_up_matrix_cell_count"] == EXPECTED_SCALE_UP_MATRIX_CELL_COUNT
    assert persisted["variants_per_base_spec_min"] == 4
    assert persisted["variants_per_base_spec_max"] == 4
    assert persisted["profiles_per_calibration_spec_min"] == 12
    assert persisted["profiles_per_calibration_spec_max"] == 12
    assert persisted["contract_violation_count"] == 0
    assert persisted["environment_rollout_started"] is False
    assert persisted["guardrail_violation_count"] == 0
    assert len(matrix_rows) == EXPECTED_SCALE_UP_MATRIX_CELL_COUNT + 1
    assert len(selected_rows) == EXPECTED_SELECTED_BASE_SPEC_COUNT + 1
    assert len(spec_rows) == EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT + 1
