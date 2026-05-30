from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_bounded_calibration_smoke_preflight import base_spec_rows, load_calibration_specs
from autodrift.controller_family_off_track_dominance_localization import DEFAULT_OUTPUT_DIR as DEFAULT_M1718_OUTPUT_DIR
from autodrift.controller_family_off_track_repair_panel_preflight import (
    EXPECTED_REPAIR_PANEL_MATRIX_CELL_COUNT,
    EXPECTED_REPAIR_PANEL_SPEC_COUNT,
    EXPECTED_SELECTED_BASE_SPEC_COUNT,
    EXPECTED_TASK_FAMILY_COUNTS,
    REPAIR_VARIANT_PANEL,
    read_csv_rows,
    repair_panel_specs,
    run_off_track_repair_panel_preflight,
    select_repair_base_specs,
)


def test_select_repair_base_specs_keeps_target_task_budget() -> None:
    specs = load_calibration_specs()
    bases = base_spec_rows(specs)
    targets = read_csv_rows(DEFAULT_M1718_OUTPUT_DIR / "repair_target_slices.csv")

    selected, rejected = select_repair_base_specs(bases, targets)

    assert len(selected) == EXPECTED_SELECTED_BASE_SPEC_COUNT
    assert len(rejected) > 0
    assert {
        task_family: sum(row["task_family"] == task_family for row in selected)
        for task_family in EXPECTED_TASK_FAMILY_COUNTS
    } == EXPECTED_TASK_FAMILY_COUNTS
    assert all(int(row["target_slice_count"]) >= 1 for row in selected)
    assert all(row["selection_reason"] == "off_track_target_source_greedy" for row in selected)


def test_repair_panel_specs_keeps_only_four_repair_variants() -> None:
    specs = load_calibration_specs()
    bases = base_spec_rows(specs)
    targets = read_csv_rows(DEFAULT_M1718_OUTPUT_DIR / "repair_target_slices.csv")
    selected, _ = select_repair_base_specs(bases, targets)

    rows = repair_panel_specs(specs, {row["base_task_source_id"] for row in selected})

    assert len(rows) == EXPECTED_REPAIR_PANEL_SPEC_COUNT
    assert {row["repair_variant_label"] for row in rows} == {
        str(variant["repair_variant_label"]) for variant in REPAIR_VARIANT_PANEL
    }
    assert "wide_relaxed_extended" in {row["repair_variant_label"] for row in rows}


def test_run_off_track_repair_panel_preflight_writes_no_rollout_subset(tmp_path: Path) -> None:
    summary = run_off_track_repair_panel_preflight(output_dir=tmp_path)
    persisted = read_json(tmp_path / "summary.json")
    matrix_rows = (tmp_path / "repair_panel_matrix.csv").read_text(encoding="utf-8").splitlines()
    selected_rows = (tmp_path / "selected_base_specs.csv").read_text(encoding="utf-8").splitlines()
    spec_rows = (tmp_path / "repair_panel_specs.csv").read_text(encoding="utf-8").splitlines()

    assert summary["result_class"] == "off_track_repair_panel_preflight_pass"
    assert persisted["selected_task_family_counts"] == EXPECTED_TASK_FAMILY_COUNTS
    assert persisted["selected_base_spec_count"] == EXPECTED_SELECTED_BASE_SPEC_COUNT
    assert persisted["repair_panel_spec_count"] == EXPECTED_REPAIR_PANEL_SPEC_COUNT
    assert persisted["repair_panel_matrix_cell_count"] == EXPECTED_REPAIR_PANEL_MATRIX_CELL_COUNT
    assert persisted["variant_label_counts"]["wide_relaxed_extended"] == EXPECTED_SELECTED_BASE_SPEC_COUNT
    assert persisted["variants_per_base_spec_min"] == 4
    assert persisted["variants_per_base_spec_max"] == 4
    assert persisted["profiles_per_calibration_spec_min"] == 12
    assert persisted["profiles_per_calibration_spec_max"] == 12
    assert persisted["contract_violation_count"] == 0
    assert persisted["environment_rollout_started"] is False
    assert persisted["guardrail_violation_count"] == 0
    assert len(matrix_rows) == EXPECTED_REPAIR_PANEL_MATRIX_CELL_COUNT + 1
    assert len(selected_rows) == EXPECTED_SELECTED_BASE_SPEC_COUNT + 1
    assert len(spec_rows) == EXPECTED_REPAIR_PANEL_SPEC_COUNT + 1
