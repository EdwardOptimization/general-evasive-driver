import csv

from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.hf0_source_only_fixture_smoke import admitted_source_only_fixture_rows
from autodrift.hf0_source_only_role_fixture_parameterization import (
    DIFFERENTIATION_L2_MIN_THRESHOLD,
    FIXTURE_PARAMETERIZATION_FIELDNAMES,
    RESET_DIFFERENTIATION_FIELDNAMES,
    ROLE_FAMILIES,
    build_source_only_role_fixture_specs,
    run_preflight,
    run_source_only_role_fixture_parameterization_preflight,
)
from autodrift.high_fidelity_interface import BackendResetRequest, P0_OBSERVATION_DIM, P0ObservationExtractor


def test_build_source_only_role_fixture_specs_match_admitted_fixture_catalog():
    admitted = {row.role_family: row.fixture_id for row in admitted_source_only_fixture_rows()}

    specs = build_source_only_role_fixture_specs()

    assert len(specs) == 3
    assert {spec.role_family for spec in specs} == set(ROLE_FAMILIES)
    assert {spec.fixture_id for spec in specs} == set(admitted.values())
    for spec in specs:
        assert spec.fixture_id == admitted[spec.role_family]
        assert len(spec.road.left_boundary_points_body) == 8
        assert len(spec.road.right_boundary_points_body) == 8
        assert len(spec.obstacles) == 4
        assert spec.obstacles[0].present == 1.0
        assert spec.diagnostic_tags["differentiation_reason"]


def test_four_wheel_backend_fixture_spec_reset_preserves_p0_shape_and_diagnostics():
    spec = build_source_only_role_fixture_specs()[1]
    backend = FourWheelHF0Backend(fixture_spec=spec)
    extractor = P0ObservationExtractor()

    try:
        reset_result = backend.reset(
            BackendResetRequest(
                seed=2496,
                scenario_spec_id=spec.fixture_id,
                role_family=spec.role_family,
            )
        )
        observation = extractor.extract(reset_result.actor_view)
    finally:
        backend.close()

    assert observation.shape == (P0_OBSERVATION_DIM,)
    assert reset_result.backend_info["source_only_fixture_spec_present"] is True
    assert reset_result.backend_info["source_only_fixture_id"] == spec.fixture_id
    assert reset_result.diagnostics["source_only_fixture_spec_present"] is True
    assert reset_result.diagnostics["source_only_fixture_role_family"] == spec.role_family
    assert reset_result.diagnostics["state"]["vx"] == spec.initial_state.vx
    assert reset_result.diagnostics["fault_scales"] == {
        "mu": (0.72, 0.95, 0.72, 0.95),
        "lateral_stiffness": (1.0, 1.0, 1.0, 1.0),
        "brake": (1.0, 1.0, 1.0, 1.0),
        "drive": (1.0, 1.0, 1.0, 1.0),
        "longitudinal_drag": (0.0, 0.0, 0.0, 0.0),
    }


def test_parameterization_preflight_verifies_reset_differentiation_without_policy_action():
    parameterization_rows, differentiation_rows, summary = (
        run_source_only_role_fixture_parameterization_preflight()
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "source_only_role_fixture_parameterization_preflight_pass"
    assert summary["spec_count"] == 3
    assert summary["reset_count"] == 3
    assert summary["all_reset_observations_shape_72"] is True
    assert summary["action_shape"] == 3
    assert summary["default_backend_behavior_checked"] is True
    assert summary["default_backend_spec_present"] is False
    assert summary["unique_initial_state_digest_count"] == 3
    assert summary["unique_fault_scale_digest_count"] >= 2
    assert summary["unique_obstacle_digest_count"] == 3
    assert summary["unique_reset_observation_digest_count"] == 3
    assert summary["pairwise_reset_observation_l2_min"] > DIFFERENTIATION_L2_MIN_THRESHOLD
    assert summary["pairwise_state_digest_unique"] is True
    assert summary["pairwise_obstacle_digest_unique"] is True
    assert summary["role_metadata_only"] is True
    assert summary["fixture_metadata_only"] is True
    assert summary["role_labels_enter_actor_input"] is False
    assert summary["fixture_labels_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["diagnostics_available_to_actor"] is False
    assert summary["policy_action"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["verdict_claim_made"] is False
    assert {row.role_family for row in parameterization_rows} == set(ROLE_FAMILIES)
    assert len(differentiation_rows) == 3
    assert all(row.reset_observation_l2 > DIFFERENTIATION_L2_MIN_THRESHOLD for row in differentiation_rows)


def test_run_preflight_writes_parameterization_artifacts(tmp_path):
    summary = run_preflight(
        tmp_path / "run",
        next_blocker="m2497-engineering-controller-source-only-role-fixture-parameterization-result-audit",
    )

    assert summary["status_pass"] is True
    assert summary["milestone"] == (
        "m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight"
    )
    assert summary["fixture_parameterization_rows"] == str(
        tmp_path / "run" / "fixture_parameterization_rows.csv"
    )
    assert summary["reset_differentiation_rows"] == str(
        tmp_path / "run" / "reset_differentiation_rows.csv"
    )

    with (tmp_path / "run" / "fixture_parameterization_rows.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        parameterization_rows = list(csv.DictReader(handle))
    with (tmp_path / "run" / "reset_differentiation_rows.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        differentiation_rows = list(csv.DictReader(handle))

    assert len(parameterization_rows) == 3
    assert len(differentiation_rows) == 3
    assert set(parameterization_rows[0]) == set(FIXTURE_PARAMETERIZATION_FIELDNAMES)
    assert set(differentiation_rows[0]) == set(RESET_DIFFERENTIATION_FIELDNAMES)
    assert {row["reset_observation_shape"] for row in parameterization_rows} == {
        str(P0_OBSERVATION_DIM)
    }
    assert {row["role_metadata_only"] for row in parameterization_rows} == {"True"}
