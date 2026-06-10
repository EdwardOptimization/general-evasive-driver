import numpy as np
import pytest

from autodrift.active_safety_reflex_driver import (
    ACTION_COMPONENTS,
    DRIVER_ID,
    INCUMBENT_MEASUREMENT_ID,
    OUTPUT_SEMANTICS,
    ActiveSafetyReflexDriver,
    policy_config_fingerprint,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as INCUMBENT_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)


def test_active_safety_reflex_driver_returns_bounded_direct_action() -> None:
    driver = ActiveSafetyReflexDriver()
    observation = np.zeros(72, dtype=np.float32)
    observation[44] = 1.0
    observation[45] = 0.25

    action = driver.act(observation)
    action_dict = driver.act_dict(observation)
    contract = driver.contract_dict()
    expected = v4_v2_fallback_no_regression_hard_safety_direct_action(observation, V4_POLICY_CONFIG)

    assert action.shape == (3,)
    assert np.allclose(action, expected)
    assert np.all(np.isfinite(action))
    assert float(np.max(np.abs(action))) <= 1.0
    assert tuple(action_dict) == ACTION_COMPONENTS
    assert contract["driver_id"] == DRIVER_ID
    assert contract["incumbent_policy_id"] == INCUMBENT_POLICY_ID
    assert contract["incumbent_measurement_id"] == INCUMBENT_MEASUREMENT_ID
    assert contract["observation_shape"] == 72
    assert contract["action_shape"] == 3
    assert contract["action_components"] == list(ACTION_COMPONENTS)
    assert contract["output_semantics"] == OUTPUT_SEMANTICS
    assert contract["runtime_base_policy_required"] is False
    assert contract["checkpoint_model_required"] is False


def test_active_safety_reflex_driver_rejects_non_deployable_observation() -> None:
    driver = ActiveSafetyReflexDriver()

    with pytest.raises(ValueError, match="expected observation shape"):
        driver.act(np.zeros(71, dtype=np.float32))

    bad = np.zeros(72, dtype=np.float32)
    bad[0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        driver.act(bad)


def test_policy_config_fingerprint_is_stable_for_same_config() -> None:
    first = policy_config_fingerprint(V4_POLICY_CONFIG)
    second = policy_config_fingerprint(dict(V4_POLICY_CONFIG))

    assert first == second
    assert len(first) == 64
