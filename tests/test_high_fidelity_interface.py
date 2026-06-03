import numpy as np
import pytest

from autodrift.env import DriftEnvConfig
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    OBSTACLE_SLOT_COUNT,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    RoadView,
    ActorView,
    canonical_p0_config,
    default_actor_view,
    physical_control_from_action,
    run_current_sim_p0_preflight,
    validate_actor_action,
)


def test_validate_actor_action_shape_and_physical_mapping():
    action = validate_actor_action(np.array([2.0, 0.0, -2.0], dtype=np.float32))

    assert action.tolist() == [1.0, 0.0, -1.0]
    np.testing.assert_allclose(physical_control_from_action(action), np.array([1.0, 0.5, 0.0], dtype=np.float32))

    with pytest.raises(ValueError, match="expected action shape"):
        validate_actor_action(np.zeros((1, ACTION_DIM), dtype=np.float32))
    with pytest.raises(ValueError, match="non-finite"):
        validate_actor_action(np.array([0.0, np.nan, 0.0], dtype=np.float32))


def test_p0_observation_extractor_shape_and_field_order():
    observation = P0ObservationExtractor().extract(default_actor_view())

    assert observation.shape == (P0_OBSERVATION_DIM,)
    assert np.isclose(observation[0], 8.0 / 20.0)
    assert np.isclose(observation[9], 0.05)
    assert np.isclose(observation[12], 5.0 / 80.0)
    assert np.isclose(observation[44], 1.0)
    assert np.isclose(observation[45], 25.0 / 80.0)


def test_p0_observation_extractor_rejects_incomplete_actor_view():
    actor_view = default_actor_view()
    bad_view = ActorView(
        dt=actor_view.dt,
        step_index=actor_view.step_index,
        ego=actor_view.ego,
        actuators=actor_view.actuators,
        road=RoadView(
            left_boundary_points_body=actor_view.road.left_boundary_points_body[:-1],
            right_boundary_points_body=actor_view.road.right_boundary_points_body,
        ),
        obstacles=actor_view.obstacles,
    )

    with pytest.raises(ValueError, match="left road points"):
        P0ObservationExtractor().extract(bad_view)

    bad_view = ActorView(
        dt=actor_view.dt,
        step_index=actor_view.step_index,
        ego=actor_view.ego,
        actuators=actor_view.actuators,
        road=actor_view.road,
        obstacles=actor_view.obstacles[: OBSTACLE_SLOT_COUNT - 1],
    )
    with pytest.raises(ValueError, match="obstacle slots"):
        P0ObservationExtractor().extract(bad_view)


def test_canonical_p0_config_rejects_privileged_or_stacked_config():
    assert canonical_p0_config(DriftEnvConfig())
    assert not canonical_p0_config(DriftEnvConfig(include_privileged_params=True))
    assert not canonical_p0_config(DriftEnvConfig(history_length=2))


def test_current_sim_p0_preflight_contract_flags():
    summary = run_current_sim_p0_preflight(seed=2473)

    assert summary["status_pass"] is True
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["step_observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM
    assert summary["p0_extractor_shape"] == P0_OBSERVATION_DIM
    assert summary["invalid_action_shape_rejected"] is True
    assert summary["actor_input_contract_changed"] is False
    assert summary["action_contract_changed"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["diagnostics_available_to_actor"] is False
    assert summary["external_high_fidelity_required"] is False
    assert summary["high_fidelity_simulation_run"] is False
