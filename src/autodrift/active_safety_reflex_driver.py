"""Deployable direct-action active-safety reflex driver."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import to_jsonable
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    POLICY_ID as INCUMBENT_POLICY_ID,
    V4_POLICY_CONFIG,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


ACTION_COMPONENTS = ("steer", "throttle", "brake")
OUTPUT_SEMANTICS = "direct_action_clipped"
DRIVER_ID = "active_safety_reflex_driver_m3105_incumbent_v4_no_regression"
INCUMBENT_MEASUREMENT_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)


def policy_config_fingerprint(policy_config: Mapping[str, Any]) -> str:
    payload = json.dumps(to_jsonable(dict(policy_config)), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ActiveSafetyReflexDriverContract:
    driver_id: str
    incumbent_policy_id: str
    incumbent_measurement_id: str
    observation_shape: int
    action_shape: int
    action_components: tuple[str, str, str]
    output_semantics: str
    runtime_base_policy_required: bool
    checkpoint_model_required: bool
    recurrent_hidden_state_required: bool
    actor_input_contract: str
    policy_config_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_id": self.driver_id,
            "incumbent_policy_id": self.incumbent_policy_id,
            "incumbent_measurement_id": self.incumbent_measurement_id,
            "observation_shape": self.observation_shape,
            "action_shape": self.action_shape,
            "action_components": list(self.action_components),
            "output_semantics": self.output_semantics,
            "runtime_base_policy_required": self.runtime_base_policy_required,
            "checkpoint_model_required": self.checkpoint_model_required,
            "recurrent_hidden_state_required": self.recurrent_hidden_state_required,
            "actor_input_contract": self.actor_input_contract,
            "policy_config_sha256": self.policy_config_sha256,
        }


class ActiveSafetyReflexDriver:
    """Callable obs72-to-action3 safety-reflex layer.

    The runtime accepts only the actor-visible P0 observation vector and returns
    direct normalized [steer, throttle, brake]. It does not load a base policy,
    model checkpoint, recurrent hidden state, target label, or evaluator verdict.
    """

    def __init__(self, policy_config: Mapping[str, Any] | None = None):
        self.policy_config = deepcopy(dict(policy_config or V4_POLICY_CONFIG))
        self._contract = ActiveSafetyReflexDriverContract(
            driver_id=DRIVER_ID,
            incumbent_policy_id=INCUMBENT_POLICY_ID,
            incumbent_measurement_id=INCUMBENT_MEASUREMENT_ID,
            observation_shape=P0_OBSERVATION_DIM,
            action_shape=ACTION_DIM,
            action_components=ACTION_COMPONENTS,
            output_semantics=OUTPUT_SEMANTICS,
            runtime_base_policy_required=False,
            checkpoint_model_required=False,
            recurrent_hidden_state_required=False,
            actor_input_contract="actor_visible_obs72_only",
            policy_config_sha256=policy_config_fingerprint(self.policy_config),
        )

    @property
    def contract(self) -> ActiveSafetyReflexDriverContract:
        return self._contract

    def act(self, observation: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (P0_OBSERVATION_DIM,):
            raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
        if not np.all(np.isfinite(obs)):
            raise ValueError("observation contains non-finite values")
        action = v4_v2_fallback_no_regression_hard_safety_direct_action(obs, config=self.policy_config).astype(np.float32)
        if action.shape != (ACTION_DIM,):
            raise ValueError(f"internal action shape {action.shape} != {(ACTION_DIM,)}")
        if not np.all(np.isfinite(action)):
            raise ValueError("internal action contains non-finite values")
        return np.clip(action, -1.0, 1.0).astype(np.float32)

    def act_dict(self, observation: np.ndarray | list[float] | tuple[float, ...]) -> dict[str, float]:
        action = self.act(observation)
        return {component: float(action[index]) for index, component in enumerate(ACTION_COMPONENTS)}

    def contract_dict(self) -> dict[str, Any]:
        return self.contract.to_dict()


def active_safety_reflex_action(
    observation: np.ndarray | list[float] | tuple[float, ...],
    policy_config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    return ActiveSafetyReflexDriver(policy_config=policy_config).act(observation)
