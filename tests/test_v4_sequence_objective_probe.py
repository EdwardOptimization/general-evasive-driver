import torch

from autodrift.v4_sequence_objective_probe import (
    ResidualHead,
    _alpha_metrics,
    classify_v4_sequence_objective_probe,
)


def test_classify_v4_sequence_objective_probe_candidate():
    assert (
        classify_v4_sequence_objective_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            candidate_count=1,
            any_gap_lift=True,
            any_normal_drift=False,
            ppo_used=False,
            promoted=False,
        )
        == "v4_sequence_objective_probe_candidate"
    )


def test_classify_v4_sequence_objective_probe_blocks_ppo():
    assert (
        classify_v4_sequence_objective_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            candidate_count=0,
            any_gap_lift=False,
            any_normal_drift=False,
            ppo_used=True,
            promoted=False,
        )
        == "v4_sequence_objective_probe_metadata_artifact"
    )


def test_residual_head_is_bounded_and_zero_initialized():
    head = ResidualHead(feature_dim=4, hidden_dim=8, max_residual=0.04)
    output = head(torch.ones(3, 4))
    assert torch.allclose(output, torch.zeros_like(output))
    with torch.no_grad():
        head.net[-1].bias.fill_(10.0)
    bounded = head(torch.ones(3, 4))
    assert float(torch.max(torch.abs(bounded)).detach()) <= 0.04


def test_alpha_metrics_identifies_candidate_when_gap_lifts_without_drift():
    samples = {
        "normal_actions": torch.zeros(2, 3),
        "intervention_actions": torch.tensor([[0.03, 0.0, 0.0], [0.03, 0.0, 0.0]], dtype=torch.float32),
        "target_gaps": torch.tensor([0.035, 0.035], dtype=torch.float32),
        "hard_gaps": torch.tensor([0.0, 0.0], dtype=torch.float32),
        "hard_available": torch.tensor([0.0, 0.0], dtype=torch.float32),
    }
    meta = [
        {"contrast_group_id": "g1", "variant": "zero_command_obs"},
        {"contrast_group_id": "g2", "variant": "zero_command_obs"},
    ]

    class StaticHead(torch.nn.Module):
        def __call__(self, features):
            if torch.all(features == 0):
                return torch.zeros(features.shape[0], 3)
            return torch.full((features.shape[0], 3), 0.005)

    samples["normal_features"] = torch.zeros(2, 4)
    samples["intervention_features"] = torch.ones(2, 4)
    alpha_rows, objective_rows = _alpha_metrics(samples=samples, meta_rows=meta, head=StaticHead(), alphas=(1.0,))

    assert alpha_rows[0]["normal_retention_pass"] is True
    assert alpha_rows[0]["gap_lift_pass"] is True
    assert alpha_rows[0]["exact_probe_candidate"] is True
    assert len(objective_rows) == 2
