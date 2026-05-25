import numpy as np
import torch

from autodrift.v4_normal_margin_residual_calibration import (
    _augment_alpha_rows,
    calibrated_action_from_hidden,
    classify_v4_normal_margin_calibration,
)


def test_classify_normal_margin_calibration_candidate():
    assert (
        classify_v4_normal_margin_calibration(
            actor_changed=False,
            residual_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            candidate_count=1,
            any_gap_lift=True,
            any_normal_regression=False,
            calibrator_collapse=False,
            ppo_used=False,
            promoted=False,
        )
        == "v4_normal_margin_calibration_candidate"
    )


def test_classify_normal_margin_calibration_blocks_residual_mutation():
    assert (
        classify_v4_normal_margin_calibration(
            actor_changed=False,
            residual_changed=True,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            candidate_count=0,
            any_gap_lift=False,
            any_normal_regression=False,
            calibrator_collapse=False,
            ppo_used=False,
            promoted=False,
        )
        == "v4_normal_margin_calibration_metadata_artifact"
    )


def test_augment_alpha_rows_requires_strict_retention_and_active_margin():
    alpha_rows = [
        {
            "alpha": 0.125,
            "normal_success_rate": 1.0,
            "normal_collision_rate": 0.0,
            "closed_loop_gap_pass": True,
        },
        {
            "alpha": 0.15,
            "normal_success_rate": 0.995,
            "normal_collision_rate": 0.005,
            "closed_loop_gap_pass": True,
        },
    ]
    objective_rows = []
    for alpha, margin, collision in [(0.125, 0.00002, False), (0.15, -0.00001, True)]:
        objective_rows.append(
            {
                "alpha": alpha,
                "seed": 77025,
                "source_index": 12,
                "step": 24,
                "normal_margin": margin,
                "normal_collision": collision,
            }
        )

    augmented = _augment_alpha_rows(
        alpha_rows,
        objective_rows,
        active_alpha_0125_margin=0.000009,
    )
    by_alpha = {row["alpha"]: row for row in augmented}

    assert by_alpha[0.125]["strict_normal_retention_pass"] is True
    assert by_alpha[0.125]["active_source_margin_pass_vs_parent"] is True
    assert by_alpha[0.125]["normal_margin_calibration_candidate"] is True
    assert by_alpha[0.15]["strict_normal_retention_pass"] is False
    assert by_alpha[0.15]["normal_margin_calibration_candidate"] is False


def test_calibrated_action_wrapper_applies_gate_to_residual():
    class DummyModel:
        def recurrent_features_tensor(self, obs, hidden):
            return obs[:, :2], hidden + 1.0

        def actor_mean(self, features):
            return torch.zeros(features.shape[0], 3)

    class DummyHead(torch.nn.Module):
        def forward(self, features):
            return torch.ones(features.shape[0], 3) * 0.5

    class DummyGate(torch.nn.Module):
        def forward(self, features):
            return torch.ones(features.shape[0], 1) * 0.25

    action, next_hidden, base_action, raw_delta, calibrated_delta, gate = calibrated_action_from_hidden(
        DummyModel(),
        DummyHead(),
        DummyGate(),
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        torch.zeros(1, 2),
        alpha=0.2,
        device=torch.device("cpu"),
    )

    assert np.allclose(base_action, np.zeros(3))
    assert np.allclose(raw_delta, np.ones(3) * 0.5)
    assert np.allclose(calibrated_delta, np.ones(3) * 0.125)
    assert np.allclose(action, np.ones(3) * 0.025)
    assert gate == 0.25
    assert torch.allclose(next_hidden, torch.ones(1, 2))
