import csv

from autodrift.hf0_source_only_fixture_smoke import (
    FIXTURE_ACTION_SEQUENCES,
    admitted_source_only_fixture_rows,
    run_preflight,
    run_source_only_fixture_smoke,
)
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def test_admitted_source_only_fixture_rows_are_exact_limited_fixture_set():
    rows = admitted_source_only_fixture_rows()

    assert len(rows) == 3
    assert {row.surface_id for row in rows} == {SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}
    assert {row.fixture_admission_status for row in rows} == {"admitted_for_materialization"}
    assert {row.role_family for row in rows} == set(FIXTURE_ACTION_SEQUENCES)


def test_run_source_only_fixture_smoke_preserves_contract_and_diagnostics_boundary():
    smoke_rows, summary = run_source_only_fixture_smoke()

    assert summary["status_pass"] is True
    assert summary["result_class"] == "hf0_source_only_fixture_smoke_pass"
    assert summary["fixture_count"] == 3
    assert summary["reset_count"] == 3
    assert summary["step_count"] == 6
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["all_reset_observations_shape_72"] is True
    assert summary["all_step_observations_shape_72"] is True
    assert summary["all_action_shapes_3"] is True
    assert summary["fixture_labels_enter_actor_input"] is False
    assert summary["scenario_labels_enter_actor_input"] is False
    assert summary["feasibility_classes_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["policy_action"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["verdict_claim_made"] is False
    assert all(count == 4 for count in summary["diagnostic_wheel_force_counts"])

    for row in smoke_rows:
        assert row.reset_observation_shape == P0_OBSERVATION_DIM
        assert row.step_observation_shapes == (P0_OBSERVATION_DIM, P0_OBSERVATION_DIM)
        assert row.action_shape == ACTION_DIM
        assert row.backend_statuses == ("running", "running")


def test_run_preflight_writes_summary_and_fixture_smoke_rows(tmp_path):
    summary = run_preflight(
        tmp_path,
        next_blocker="m2485-high-fidelity-interface-source-only-fixture-smoke-result-audit",
    )

    assert summary["status_pass"] is True
    assert summary["fixture_count"] == 3
    assert summary["step_count"] == 6
    assert summary["fixture_smoke_rows"] == str(tmp_path / "fixture_smoke_rows.csv")

    rows_path = tmp_path / "fixture_smoke_rows.csv"
    with rows_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert {row["reset_observation_shape"] for row in rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["step_observation_shapes"] for row in rows} == {
        f"{P0_OBSERVATION_DIM};{P0_OBSERVATION_DIM}"
    }
    assert {row["action_shape"] for row in rows} == {str(ACTION_DIM)}
