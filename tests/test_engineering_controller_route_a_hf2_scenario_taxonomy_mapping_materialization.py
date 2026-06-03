import csv

from autodrift.engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization import (
    BINDING_FIELDNAMES,
    METADATA_FIELDNAMES,
    PILOT_GUARD_FIELDNAMES,
    ROUTE_ROLE_FIELDNAMES,
    build_metadata_boundary_checks,
    build_pilot_admission_guard_rows,
    build_route_role_mapping_rows,
    build_surface_fixture_binding_rows,
    materialize_route_a_hf2_scenario_taxonomy_mapping,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _source_matrix_rows():
    return _read_csv(
        __import__("pathlib").Path(
            "runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv"
        )
    )


def _source_fixture_rows():
    return _read_csv(
        __import__("pathlib").Path(
            "runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv"
        )
    )


def test_build_hf2_taxonomy_rows_preserve_boundaries():
    route_rows = build_route_role_mapping_rows()
    binding_rows = build_surface_fixture_binding_rows(_source_matrix_rows(), _source_fixture_rows())
    metadata_rows = build_metadata_boundary_checks()
    pilot_rows = build_pilot_admission_guard_rows(binding_rows)

    assert len(route_rows) == 5
    assert set(route_rows[0]) == set(ROUTE_ROLE_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in route_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in route_rows} == {ACTION_DIM}
    assert {row["feasibility_label_actor_visible"] for row in route_rows} == {False}
    assert {row["pilot_admission_allowed_by_mapping"] for row in route_rows} == {False}
    assert {row["status_pass"] for row in route_rows} == {True}

    assert len(binding_rows) == 10
    assert set(binding_rows[0]) == set(BINDING_FIELDNAMES)
    assert {row["actor_observation_shape"] for row in binding_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in binding_rows} == {ACTION_DIM}
    assert {row["support_status_preserved"] for row in binding_rows} == {True}
    assert {row["limited_or_reference_upgraded"] for row in binding_rows} == {False}
    assert {row["status_pass"] for row in binding_rows} == {True}
    assert any(row["binding_status"] == "materialization_candidate_binding" for row in binding_rows)
    assert any(row["binding_status"] == "diagnostic_reference_binding" for row in binding_rows)

    assert len(metadata_rows) == 7
    assert set(metadata_rows[0]) == set(METADATA_FIELDNAMES)
    assert {row["actor_visible_allowed"] for row in metadata_rows} == {False}
    assert {row["present_in_actor_field_map"] for row in metadata_rows} == {False}
    assert {row["status_pass"] for row in metadata_rows} == {True}

    assert len(pilot_rows) == 5
    assert set(pilot_rows[0]) == set(PILOT_GUARD_FIELDNAMES)
    assert {row["pilot_candidate_status"] for row in pilot_rows} == {
        "not_admitted_by_taxonomy_mapping"
    }
    assert {row["pilot_admission_claim_made"] for row in pilot_rows} == {False}
    assert {row["status_pass"] for row in pilot_rows} == {True}


def test_materialize_route_a_hf2_taxonomy_mapping_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2556.md"

    summary = materialize_route_a_hf2_scenario_taxonomy_mapping(
        output_dir,
        milestone="m2556-test",
        next_blocker="m2557-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization_pass"
    )
    assert summary["route_role_mapping_row_count"] == 5
    assert summary["route_role_mapping_all_pass"] is True
    assert summary["surface_fixture_binding_row_count"] == 10
    assert summary["surface_fixture_bindings_all_pass"] is True
    assert summary["metadata_boundary_check_count"] == 7
    assert summary["metadata_boundary_checks_all_pass"] is True
    assert summary["pilot_admission_guard_count"] == 5
    assert summary["pilot_admission_guards_all_pass"] is True
    assert summary["limited_or_reference_upgraded"] is False
    assert summary["metadata_labels_enter_actor_input"] is False
    assert summary["pilot_admission_claim_made"] is False
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False

    route_rows = _read_csv(output_dir / "hf2_route_role_mapping.csv")
    binding_rows = _read_csv(output_dir / "hf2_surface_fixture_binding.csv")
    metadata_rows = _read_csv(output_dir / "hf2_metadata_boundary_checks.csv")
    pilot_rows = _read_csv(output_dir / "hf2_pilot_admission_guard_rows.csv")
    gate_rows = _read_csv(output_dir / "materialization_gate_matrix.csv")

    assert len(route_rows) == 5
    assert len(binding_rows) == 10
    assert len(metadata_rows) == 7
    assert len(pilot_rows) == 5
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["actor_observation_shape"] for row in route_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in route_rows} == {str(ACTION_DIM)}
    assert {row["limited_or_reference_upgraded"] for row in binding_rows} == {"False"}
    assert {row["present_in_actor_field_map"] for row in metadata_rows} == {"False"}
    assert {row["pilot_admission_claim_made"] for row in pilot_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
