import numpy as np
import torch

from autodrift.v4_residual_closed_loop_replay import (
    _alpha_summary_rows,
    classify_v4_residual_closed_loop_replay,
    residual_action_from_hidden,
)


def test_classify_v4_residual_closed_loop_candidate():
    assert (
        classify_v4_residual_closed_loop_replay(
            actor_backbone_changed=False,
            optimizer_started=False,
            ppo_used=False,
            promoted=False,
            metadata_missing_rows=0,
            reconstruction_success_rate=1.0,
            candidate_count=1,
            any_gap_lift=True,
            any_normal_regression=False,
        )
        == "v4_residual_closed_loop_replay_candidate"
    )


def test_classify_v4_residual_closed_loop_blocks_optimizer():
    assert (
        classify_v4_residual_closed_loop_replay(
            actor_backbone_changed=False,
            optimizer_started=True,
            ppo_used=False,
            promoted=False,
            metadata_missing_rows=0,
            reconstruction_success_rate=1.0,
            candidate_count=0,
            any_gap_lift=False,
            any_normal_regression=False,
        )
        == "v4_residual_closed_loop_replay_metadata_artifact"
    )


def test_alpha_summary_identifies_closed_loop_candidate():
    rows = []
    for alpha, gap, margin_gap, normal_drift in [
        (0.0, 0.02, 0.10, 0.0),
        (0.2, 0.03, 0.11, 0.001),
    ]:
        for idx in range(4):
            rows.append(
                {
                    "contrast_group_id": f"g{idx}",
                    "alpha": alpha,
                    "normal_success": True,
                    "normal_collision": False,
                    "normal_margin": 0.5,
                    "normal_first_action_drift_vs_base": normal_drift,
                    "intervention_success": False,
                    "intervention_collision": True,
                    "intervention_prefix_l2_mean": gap,
                    "margin_gap_from_normal": margin_gap,
                    "hard_negative_available": True,
                }
            )
    summary = _alpha_summary_rows(rows, alphas=(0.0, 0.2))
    by_alpha = {row["alpha"]: row for row in summary}
    assert by_alpha[0.2]["normal_retention_pass"] is True
    assert by_alpha[0.2]["closed_loop_gap_pass"] is True
    assert by_alpha[0.2]["closed_loop_replay_candidate"] is True


def test_residual_action_wrapper_adds_bounded_delta():
    class DummyModel:
        def recurrent_features_tensor(self, obs, hidden):
            return obs[:, :2], hidden + 1.0

        def actor_mean(self, features):
            return torch.zeros(features.shape[0], 3)

    class DummyHead(torch.nn.Module):
        def forward(self, features):
            return torch.ones(features.shape[0], 3) * 0.5

    action, next_hidden, base_action, delta = residual_action_from_hidden(
        DummyModel(),
        DummyHead(),
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        torch.zeros(1, 2),
        alpha=0.2,
        device=torch.device("cpu"),
    )
    assert np.allclose(base_action, np.zeros(3))
    assert np.allclose(delta, np.ones(3) * 0.5)
    assert np.allclose(action, np.ones(3) * 0.1)
    assert torch.allclose(next_hidden, torch.ones(1, 2))
