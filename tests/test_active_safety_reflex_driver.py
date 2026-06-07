import numpy as np
import pytest

from autodrift.active_safety_reflex_driver import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    ActiveSafetyReflexDriver,
    policy_config_fingerprint,
)
from autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight import (
    DEFAULT_POLICY_CONFIG,
)


def test_active_safety_reflex_driver_returns_bounded_direct_action() -> None:
    driver = ActiveSafetyReflexDriver()
    observation = np.zeros(72, dtype=np.float32)
    observation[44] = 1.0
    observation[45] = 0.25

    action = driver.act(observation)
    action_dict = driver.act_dict(observation)
    contract = driver.contract_dict()

    assert action.shape == (3,)
    assert np.all(np.isfinite(action))
    assert float(np.max(np.abs(action))) <= 1.0
    assert tuple(action_dict) == ACTION_COMPONENTS
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
    first = policy_config_fingerprint(DEFAULT_POLICY_CONFIG)
    second = policy_config_fingerprint(dict(DEFAULT_POLICY_CONFIG))

    assert first == second
    assert len(first) == 64
