import csv

import pytest

from autodrift.hf0_scenario_taxonomy_fixtures import (
    ADMISSION_STATUSES,
    FixtureCatalogRow,
    build_fixture_catalog_rows,
    run_fixture_materialization_preflight,
    validate_fixture_catalog_rows,
)
from autodrift.hf0_scenario_taxonomy_mapping import (
    ACTOR_VISIBLE_INPUTS,
    CURRENT_SIM_METADATA_ONLY_FIELDS,
    CURRENT_SIM_SURFACE_ID,
    ROLE_FAMILIES,
    SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def test_fixture_catalog_covers_surfaces_roles_and_admissions():
    rows = build_fixture_catalog_rows()

    assert len(rows) == 10
    assert {row.surface_id for row in rows} == {CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}
    assert {row.fixture_admission_status for row in rows}.issubset(ADMISSION_STATUSES)

    for surface_id in (CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID):
        assert {row.role_family for row in rows if row.surface_id == surface_id} == set(ROLE_FAMILIES)

    assert sum(row.fixture_admission_status == "baseline_reference" for row in rows) == 5
    assert sum(row.fixture_admission_status == "diagnostic_reference_only" for row in rows) == 2
    assert sum(row.fixture_admission_status == "admitted_for_materialization" for row in rows) == 3


def test_fixture_catalog_preserves_contract_and_limited_admissions():
    rows = build_fixture_catalog_rows()
    validate_fixture_catalog_rows(rows)

    for row in rows:
        assert row.actor_observation_shape == P0_OBSERVATION_DIM
        assert row.action_shape == ACTION_DIM
        assert "scenario_role_label" not in row.actor_visible_inputs
        assert "feasibility_class" not in row.actor_visible_inputs
        assert "scenario_role_label" in row.metadata_only_fields
        assert "feasibility_class" in row.metadata_only_fields
        assert "fixture_admission_status" in row.metadata_only_fields

    current_sim_limited = [
        row
        for row in rows
        if row.surface_id == CURRENT_SIM_SURFACE_ID and row.source_support_status == "limited_fixture"
    ]
    source_only_limited = [
        row
        for row in rows
        if row.surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID and row.source_support_status == "limited_fixture"
    ]

    assert {row.fixture_admission_status for row in current_sim_limited} == {"diagnostic_reference_only"}
    assert {row.fixture_admission_status for row in source_only_limited} == {"admitted_for_materialization"}


def test_fixture_materialization_preflight_writes_summary_and_catalog(tmp_path):
    summary = run_fixture_materialization_preflight(
        tmp_path,
        next_blocker="m2483-high-fidelity-interface-source-only-fixture-smoke-design",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "hf0_scenario_taxonomy_fixture_materialization_pass"
    assert summary["surface_count"] == 2
    assert summary["catalog_row_count"] == 10
    assert summary["actor_observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["fixture_admission_status_counts"] == {
        "admitted_for_materialization": 3,
        "baseline_reference": 5,
        "diagnostic_reference_only": 2,
    }
    assert summary["current_sim_limited_reference_count"] == 2
    assert summary["source_only_admitted_fixture_count"] == 3
    assert summary["limited_rows_silently_upgraded"] is False
    assert summary["scenario_labels_enter_actor_input"] is False
    assert summary["feasibility_classes_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["verdict_claim_made"] is False

    catalog_path = tmp_path / "fixture_catalog.csv"
    with catalog_path.open(newline="", encoding="utf-8") as handle:
        catalog_rows = list(csv.DictReader(handle))
    assert len(catalog_rows) == 10
    assert {row["actor_observation_shape"] for row in catalog_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in catalog_rows} == {str(ACTION_DIM)}


def test_validate_fixture_catalog_rejects_silent_limited_upgrade():
    bad_row = FixtureCatalogRow(
        fixture_id="bad_current_sim_aes",
        surface_id=CURRENT_SIM_SURFACE_ID,
        role_family="stable_aes",
        source_support_status="limited_fixture",
        fixture_admission_status="baseline_reference",
        actor_observation_shape=P0_OBSERVATION_DIM,
        action_shape=ACTION_DIM,
        actor_visible_inputs=ACTOR_VISIBLE_INPUTS,
        metadata_only_fields=CURRENT_SIM_METADATA_ONLY_FIELDS + ("fixture_admission_status",),
        implementation_target="bad_upgrade",
        blocker_if_not_admitted="",
        next_check="not_applicable",
    )

    with pytest.raises(ValueError, match="silently upgraded"):
        validate_fixture_catalog_rows([bad_row])
