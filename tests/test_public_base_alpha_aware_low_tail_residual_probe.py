import torch

from autodrift.public_base_alpha_aware_low_tail_residual_probe import (
    classify_alpha_aware_low_tail_probe,
    low_tail_alpha_loss,
)


def test_low_tail_alpha_loss_penalizes_low_gap_and_deficit():
    gap = torch.tensor([0.01, 0.04], dtype=torch.float32)
    target_gaps = torch.tensor([0.05, 0.05], dtype=torch.float32)
    low_tail_mask = torch.tensor([True, False])
    floor_loss, deficit_loss, fraction_loss = low_tail_alpha_loss(
        gap=gap,
        target_gaps=target_gaps,
        low_tail_mask=low_tail_mask,
    )
    assert floor_loss.item() > 0.0
    assert deficit_loss.item() > 0.0
    assert fraction_loss.item() > 0.0


def test_low_tail_alpha_loss_zero_without_low_tail_rows():
    gap = torch.tensor([0.01, 0.04], dtype=torch.float32)
    target_gaps = torch.tensor([0.05, 0.05], dtype=torch.float32)
    low_tail_mask = torch.tensor([False, False])
    losses = low_tail_alpha_loss(gap=gap, target_gaps=target_gaps, low_tail_mask=low_tail_mask)
    assert [loss.item() for loss in losses] == [0.0, 0.0, 0.0]


def test_classify_alpha_aware_low_tail_probe():
    assert (
        classify_alpha_aware_low_tail_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_alpha_aware_low_tail_probe_candidate"
    )
    assert (
        classify_alpha_aware_low_tail_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=0,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_alpha_aware_low_tail_probe_no_candidate"
    )
