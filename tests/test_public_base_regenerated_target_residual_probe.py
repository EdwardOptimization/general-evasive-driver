import pytest
import torch

from autodrift.public_base_regenerated_target_residual_probe import (
    classify_regenerated_target_residual_probe,
    target_weight_vector,
)


def test_target_weight_vector_joins_targets_and_labels():
    meta_rows = [
        {"contrast_group_id": "g0", "source_index": "0", "variant": "zero", "horizon": "6"},
        {"contrast_group_id": "g1", "source_index": "1", "variant": "zero", "horizon": "8"},
    ]
    target_rows = [
        {
            "contrast_group_id": "g0",
            "source_index": "0",
            "variant": "zero",
            "horizon": "6",
            "target_steer": "0.1",
            "target_throttle": "0.2",
            "target_brake": "0.3",
            "source_label": "strict_low_tail",
        }
    ]
    low_tail_rows = [dict(target_rows[0])]
    normal_actions = torch.zeros((2, 3), dtype=torch.float32)
    target_mask, low_tail_mask, target_actions, target_weights, rows, missing = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=normal_actions,
    )
    assert missing == set()
    assert target_mask.tolist() == [True, False]
    assert low_tail_mask.tolist() == [True, False]
    assert target_actions[0].tolist() == pytest.approx([0.1, 0.2, 0.3])
    assert target_weights[0].item() == 2.0
    assert rows[0]["target_available"] is True


def test_classify_regenerated_target_residual_probe():
    assert (
        classify_regenerated_target_residual_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_regenerated_target_probe_candidate"
    )
    assert (
        classify_regenerated_target_residual_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            candidate_count=0,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_regenerated_target_probe_no_candidate"
    )
