import numpy as np
import torch

from autodrift.v4_residual_component_sensitivity import (
    DEFAULT_MASKS,
    _classify_component_roles,
    _parse_mask_names,
    classify_v4_residual_component_sensitivity,
    masked_residual_action_from_hidden,
)


def test_parse_mask_names_deduplicates_aliases():
    masks = _parse_mask_names("no_steer,throttle_brake,steer_only")
    assert [mask.name for mask in masks] == ["throttle_brake", "steer_only"]
    assert len(DEFAULT_MASKS) == 8


def test_masked_residual_action_applies_component_mask():
    class DummyModel:
        def recurrent_features_tensor(self, obs, hidden):
            return obs[:, :2], hidden + 1.0

        def actor_mean(self, features):
            return torch.zeros(features.shape[0], 3)

    class DummyHead(torch.nn.Module):
        def forward(self, features):
            return torch.tensor([[0.5, 0.25, -0.5]], dtype=torch.float32)

    action, next_hidden, base_action, raw_delta, masked_delta = masked_residual_action_from_hidden(
        DummyModel(),
        DummyHead(),
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        torch.zeros(1, 2),
        mask=np.array([1.0, 0.0, 1.0], dtype=np.float32),
        alpha=0.2,
        device=torch.device("cpu"),
    )

    assert np.allclose(base_action, np.zeros(3))
    assert np.allclose(raw_delta, np.array([0.5, 0.25, -0.5], dtype=np.float32))
    assert np.allclose(masked_delta, np.array([0.5, 0.0, -0.5], dtype=np.float32))
    assert np.allclose(action, np.array([0.1, 0.0, -0.1], dtype=np.float32))
    assert torch.allclose(next_hidden, torch.ones(1, 2))


def test_classify_component_sensitivity_actionable():
    assert (
        classify_v4_residual_component_sensitivity(
            actor_changed=False,
            residual_changed=False,
            optimizer_started=False,
            ppo_used=False,
            promoted=False,
            metadata_missing_rows=0,
            reconstruction_success_rate=1.0,
            actionable_count=1,
            attribution_count=0,
        )
        == "v4_residual_component_sensitivity_actionable_pareto"
    )


def test_classify_component_sensitivity_blocks_training():
    assert (
        classify_v4_residual_component_sensitivity(
            actor_changed=False,
            residual_changed=False,
            optimizer_started=True,
            ppo_used=False,
            promoted=False,
            metadata_missing_rows=0,
            reconstruction_success_rate=1.0,
            actionable_count=0,
            attribution_count=0,
        )
        == "v4_residual_component_sensitivity_metadata_artifact"
    )


def test_component_role_classification_uses_numeric_collision_count():
    rows = [
        {
            "mask_name": "all",
            "alpha": 0.2,
            "active_source_collision_count": 12,
            "active_source_min_margin": -0.01,
            "base_intervention_action_gap_mean": 0.04,
            "intervention_action_gap_mean": 0.05,
        },
        {
            "mask_name": "steer_only",
            "alpha": 0.2,
            "strict_normal_retention_pass": False,
            "active_source_min_margin": -0.008,
            "intervention_action_gap_mean": 0.045,
        },
        {
            "mask_name": "throttle_brake",
            "alpha": 0.2,
            "strict_normal_retention_pass": True,
            "active_source_min_margin": 0.01,
            "intervention_action_gap_mean": 0.041,
        },
    ]

    roles = {row["component"]: row for row in _classify_component_roles(rows)}

    assert roles["steer"]["harmful_component_evidence"] is True
    assert roles["steer"]["useful_component_evidence"] is True
    assert roles["throttle"]["harmful_component_evidence"] is False
    assert roles["throttle"]["useful_component_evidence"] is False
