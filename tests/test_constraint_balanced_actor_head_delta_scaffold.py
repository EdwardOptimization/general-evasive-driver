from __future__ import annotations

import pytest
import torch
from torch import nn
from torch.distributions import Normal

from autodrift.constraint_balanced_actor_head_delta_scaffold import (
    ACTION_DIM,
    ConstraintBalancedActorHeadDeltaScaffold,
    forbidden_actor_input_keys,
    validate_actor_input_keys,
)
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


class TensorParent(nn.Module):
    def __init__(self, action: torch.Tensor) -> None:
        super().__init__()
        self.register_buffer("action", action.to(dtype=torch.float32))

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        return self.action.expand(observation.shape[:-1] + self.action.shape)


class DistributionParent(nn.Module):
    def forward(self, observation: torch.Tensor) -> Normal:
        mean = torch.stack(
            [
                observation[..., 0] * 0.1,
                observation[..., 1] * -0.1,
                observation[..., 2] * 0.05,
            ],
            dim=-1,
        )
        return Normal(mean, torch.ones_like(mean) * 0.1)


class ConstantResidual(nn.Module):
    def __init__(self, delta: torch.Tensor) -> None:
        super().__init__()
        self.register_buffer("delta", delta.to(dtype=torch.float32))

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        return self.delta.expand(observation.shape[:-1] + self.delta.shape)


def test_shape_contract_zero_delta_identity_against_parent_action() -> None:
    parent_action = torch.tensor([0.2, -0.3, 0.4])
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(parent_action),
        ConstantResidual(torch.zeros(ACTION_DIM)),
        residual_limit=0.1,
    )
    observation = torch.zeros((5, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)

    trace = scaffold.forward_with_trace(observation)

    assert trace.action.shape == (5, ACTION_DIM)
    assert torch.allclose(trace.parent_action, parent_action.expand_as(trace.action))
    assert torch.allclose(trace.residual_delta, torch.zeros_like(trace.action))
    assert torch.allclose(scaffold(observation), trace.parent_action)


def test_distribution_parent_uses_deployed_tanh_mean_action_path() -> None:
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        DistributionParent(),
        ConstantResidual(torch.zeros(ACTION_DIM)),
    )
    observation = torch.zeros((2, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)
    observation[:, 0] = 2.0
    observation[:, 1] = -1.0
    observation[:, 2] = 0.5

    action = scaffold(observation)

    expected_mean = torch.tensor([[0.2, 0.1, 0.025], [0.2, 0.1, 0.025]])
    assert torch.allclose(action, torch.tanh(expected_mean))


def test_residual_delta_is_bounded_before_action_combination() -> None:
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(ACTION_DIM)),
        ConstantResidual(torch.tensor([0.5, -0.2, 0.03])),
        residual_limit=[0.1, 0.05, 0.02],
    )
    observation = torch.zeros((3, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)

    trace = scaffold.forward_with_trace(observation)

    expected = torch.tensor([0.1, -0.05, 0.02]).expand_as(trace.action)
    assert torch.allclose(trace.residual_delta, expected)
    assert torch.allclose(trace.action, expected)


def test_combined_action_respects_action_range_contract() -> None:
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.tensor([0.95, -0.95, 0.0])),
        ConstantResidual(torch.tensor([0.2, -0.2, 0.1])),
        residual_limit=0.2,
        action_low=[-1.0, -1.0, -0.2],
        action_high=[1.0, 1.0, 0.05],
    )
    observation = torch.zeros((1, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)

    action = scaffold(observation)

    assert torch.allclose(action, torch.tensor([[1.0, -1.0, 0.05]]))


def test_forbidden_evaluator_and_privileged_actor_input_keys_are_rejected() -> None:
    forbidden = forbidden_actor_input_keys(["observation", "mu", "speed-ref", "verdict_label", "TTC"])

    assert forbidden == ("mu", "speed_ref", "ttc", "verdict_label")
    with pytest.raises(ValueError, match="forbidden evaluator or privileged keys"):
        validate_actor_input_keys(["observation", "oracle_stopping_distance"])

    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(ACTION_DIM)),
        ConstantResidual(torch.zeros(ACTION_DIM)),
    )
    observation = torch.zeros((1, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)
    with pytest.raises(ValueError, match="forbidden evaluator or privileged keys"):
        scaffold({"observation": observation, "path_error": torch.zeros(1)})
    with pytest.raises(ValueError, match="non-observation keys"):
        scaffold({"observation": observation, "benign_metadata": "not actor input"})
    assert torch.allclose(scaffold({"observation": observation}), torch.zeros((1, ACTION_DIM)))


def test_shape_mismatches_fail_before_candidate_interpretation() -> None:
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(ACTION_DIM)),
        ConstantResidual(torch.zeros(ACTION_DIM)),
    )
    with pytest.raises(ValueError, match="observation last dimension"):
        scaffold(torch.zeros((1, HUMAN_VIEW_OBS_DIM - 1)))

    bad_parent = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(2)),
        ConstantResidual(torch.zeros(ACTION_DIM)),
    )
    with pytest.raises(ValueError, match="actor output last dimension"):
        bad_parent(torch.zeros((1, HUMAN_VIEW_OBS_DIM)))

    bad_residual = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(ACTION_DIM)),
        ConstantResidual(torch.zeros(2)),
    )
    with pytest.raises(ValueError, match="actor output last dimension"):
        bad_residual(torch.zeros((1, HUMAN_VIEW_OBS_DIM)))


def test_scaffold_does_not_call_checkpoint_or_environment_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_side_effect(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("checkpoint side effect was called")

    monkeypatch.setattr(torch, "load", fail_side_effect)
    monkeypatch.setattr(torch, "save", fail_side_effect)
    scaffold = ConstraintBalancedActorHeadDeltaScaffold(
        TensorParent(torch.zeros(ACTION_DIM)),
        ConstantResidual(torch.zeros(ACTION_DIM)),
    )
    observation = torch.zeros((2, HUMAN_VIEW_OBS_DIM), dtype=torch.float32)

    assert torch.allclose(scaffold(observation), torch.zeros((2, ACTION_DIM)))
