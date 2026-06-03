import csv

from autodrift.engineering_controller_route_a_hf1_p0_parity_smoke_materialization import (
    ACTION_MAPPING_FIELDNAMES,
    ACTOR_FIELDNAMES,
    DIAGNOSTICS_FIELDNAMES,
    EXTERNAL_BOUNDARY_FIELDNAMES,
    VALUE_RANGE_FIELDNAMES,
    build_actor_visible_field_parity_rows,
    build_diagnostics_exclusion_checks,
    build_external_backend_boundary_checks,
    build_hf1_action_mapping_parity_checks,
    build_observation_value_range_checks,
    materialize_route_a_hf1_p0_parity_smoke,
)
from autodrift.high_fidelity_interface import ACTION_DIM, DIAGNOSTIC_ONLY_KEYS, P0_OBSERVATION_DIM


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_hf1_p0_parity_smoke_rows_pass():
    actor_rows = build_actor_visible_field_parity_rows()
    value_range_rows = build_observation_value_range_checks()
    action_rows = build_hf1_action_mapping_parity_checks()
    external_rows = build_external_backend_boundary_checks()
    diagnostics_rows = build_diagnostics_exclusion_checks()

    assert len(actor_rows) == 7
    assert set(actor_rows[0]) == set(ACTOR_FIELDNAMES)
    assert {row["observed_observation_shape"] for row in actor_rows} == {P0_OBSERVATION_DIM}
    assert {row["status_pass"] for row in actor_rows} == {True}
    assert sum(
        int(row["observed_count"])
        for row in actor_rows
        if row["row_id"] != "full_p0_extract"
    ) == P0_OBSERVATION_DIM

    assert len(value_range_rows) == 5
    assert set(value_range_rows[0]) == set(VALUE_RANGE_FIELDNAMES)
    assert {row["status_pass"] for row in value_range_rows} == {True}

    assert len(action_rows) == 7
    assert set(action_rows[0]) == set(ACTION_MAPPING_FIELDNAMES)
    assert {row["expected_action_shape"] for row in action_rows} == {ACTION_DIM}
    assert {row["status_pass"] for row in action_rows} == {True}

    assert len(external_rows) == 6
    assert set(external_rows[0]) == set(EXTERNAL_BOUNDARY_FIELDNAMES)
    assert {row["external_package_imported"] for row in external_rows} == {False}
    assert {row["external_backend_run"] for row in external_rows} == {False}
    assert {row["status_pass"] for row in external_rows} == {True}

    assert len(diagnostics_rows) == len(DIAGNOSTIC_ONLY_KEYS)
    assert set(diagnostics_rows[0]) == set(DIAGNOSTICS_FIELDNAMES)
    assert {row["actor_visible_allowed"] for row in diagnostics_rows} == {False}
    assert {row["present_in_actor_field_map"] for row in diagnostics_rows} == {False}
    assert {row["status_pass"] for row in diagnostics_rows} == {True}


def test_materialize_route_a_hf1_p0_parity_smoke_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2552.md"

    summary = materialize_route_a_hf1_p0_parity_smoke(
        output_dir,
        milestone="m2552-test",
        next_blocker="m2553-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf1_p0_parity_smoke_materialization_pass"
    )
    assert summary["actor_visible_field_parity_row_count"] == 7
    assert summary["actor_visible_field_parity_rows_all_pass"] is True
    assert summary["p0_index_coverage_count"] == P0_OBSERVATION_DIM
    assert summary["p0_index_coverage_complete"] is True
    assert summary["observation_value_range_check_count"] == 5
    assert summary["observation_value_range_checks_all_pass"] is True
    assert summary["action_mapping_check_count"] == 7
    assert summary["action_mapping_checks_all_pass"] is True
    assert summary["external_backend_boundary_check_count"] == 6
    assert summary["external_backend_boundary_checks_all_pass"] is True
    assert summary["diagnostics_exclusion_check_count"] == len(DIAGNOSTIC_ONLY_KEYS)
    assert summary["diagnostics_exclusion_checks_all_pass"] is True
    assert summary["diagnostic_only_keys_checked_count"] == len(DIAGNOSTIC_ONLY_KEYS)
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["external_high_fidelity_simulation_included"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False

    actor_rows = _read_csv(output_dir / "hf1_actor_visible_field_parity_rows.csv")
    value_range_rows = _read_csv(output_dir / "hf1_observation_value_range_checks.csv")
    action_rows = _read_csv(output_dir / "hf1_action_mapping_parity_checks.csv")
    external_rows = _read_csv(output_dir / "hf1_external_backend_boundary_checks.csv")
    diagnostics_rows = _read_csv(output_dir / "hf1_diagnostics_exclusion_checks.csv")
    gate_rows = _read_csv(output_dir / "materialization_gate_matrix.csv")

    assert len(actor_rows) == 7
    assert len(value_range_rows) == 5
    assert len(action_rows) == 7
    assert len(external_rows) == 6
    assert len(diagnostics_rows) == len(DIAGNOSTIC_ONLY_KEYS)
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["observed_observation_shape"] for row in actor_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["expected_action_shape"] for row in action_rows} == {str(ACTION_DIM)}
    assert {row["external_package_imported"] for row in external_rows} == {"False"}
    assert {row["external_backend_run"] for row in external_rows} == {"False"}
    assert {row["present_in_actor_field_map"] for row in diagnostics_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
