import csv

import pytest

from autodrift.hf0_scenario_taxonomy_mapping import (
    CURRENT_SIM_SURFACE_ID,
    ROLE_FAMILIES,
    SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
    ACTOR_VISIBLE_INPUTS,
    CURRENT_SIM_METADATA_ONLY_FIELDS,
    SurfaceRoleRow,
    build_surface_role_rows,
    run_mapping_preflight,
    validate_surface_role_rows,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def test_build_surface_role_rows_covers_surfaces_and_roles():
    rows = build_surface_role_rows()

    assert len(rows) == 10
    surfaces = {row.surface_id for row in rows}
    assert surfaces == {CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}

    for surface_id in surfaces:
        assert {row.role_family for row in rows if row.surface_id == surface_id} == set(ROLE_FAMILIES)

    assert any(
        row.surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
        and row.role_family == "stable_aes"
        and row.support_status == "limited_fixture"
        for row in rows
    )
    assert any(
        row.surface_id == CURRENT_SIM_SURFACE_ID
        and row.role_family == "stable_avoidable"
        and row.support_status == "supported"
        for row in rows
    )


def test_surface_role_rows_preserve_actor_contract_and_metadata_boundary():
    rows = build_surface_role_rows()
    validate_surface_role_rows(rows)

    for row in rows:
        assert row.actor_observation_shape == P0_OBSERVATION_DIM
        assert row.action_shape == ACTION_DIM
        assert "scenario_role_label" not in row.actor_visible_inputs
        assert "feasibility_class" not in row.actor_visible_inputs
        assert "scenario_role_label" in row.metadata_only_fields
        assert "feasibility_class" in row.metadata_only_fields


def test_run_mapping_preflight_writes_summary_and_csv(tmp_path):
    summary = run_mapping_preflight(
        tmp_path,
        next_blocker="m2481-high-fidelity-interface-scenario-taxonomy-fixture-design",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "hf0_scenario_taxonomy_mapping_materialization_pass"
    assert summary["surface_count"] == 2
    assert summary["row_count"] == 10
    assert summary["actor_observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["all_rows_preserve_observation_shape"] is True
    assert summary["all_rows_preserve_action_shape"] is True
    assert summary["scenario_labels_enter_actor_input"] is False
    assert summary["feasibility_classes_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["verdict_claim_made"] is False

    matrix_path = tmp_path / "surface_role_matrix.csv"
    assert matrix_path.exists()
    with matrix_path.open(newline="", encoding="utf-8") as handle:
        matrix_rows = list(csv.DictReader(handle))
    assert len(matrix_rows) == 10
    assert {row["actor_observation_shape"] for row in matrix_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in matrix_rows} == {str(ACTION_DIM)}


def test_validate_surface_role_rows_rejects_actor_label_leak():
    bad_row = SurfaceRoleRow(
        surface_id=CURRENT_SIM_SURFACE_ID,
        role_family="stable_avoidable",
        support_status="supported",
        actor_observation_shape=P0_OBSERVATION_DIM,
        action_shape=ACTION_DIM,
        actor_visible_inputs=ACTOR_VISIBLE_INPUTS + ("scenario_role_label",),
        metadata_only_fields=CURRENT_SIM_METADATA_ONLY_FIELDS,
        blocked_reason="",
        next_fixture_requirement="not_applicable",
    )

    with pytest.raises(ValueError, match="leaks metadata"):
        validate_surface_role_rows([bad_row])
