import torch

from autodrift.public_base_tail_weighted_residual_probe import (
    LOW_TAIL_GAP_THRESHOLD,
    classify_tail_weighted_probe,
    tail_alpha_metrics,
    tail_weight_vector,
)


def test_tail_weight_vector_marks_low_tail_rows():
    meta_rows = [
        {"contrast_group_id": "a", "source_index": "1", "variant": "zero", "horizon": "6"},
        {"contrast_group_id": "b", "source_index": "2", "variant": "zero", "horizon": "8"},
    ]
    low_tail_rows = [{"contrast_group_id": "a", "source_index": "1", "variant": "zero", "horizon": "6"}]
    deficits = {("a", "1", "zero", "6"): 0.03, ("b", "2", "zero", "8"): 0.01}
    weights, mask, rows, missing = tail_weight_vector(
        meta_rows=meta_rows,
        base_weights=torch.tensor([1.0, 1.0]),
        low_tail_rows=low_tail_rows,
        near_base_deficits=deficits,
    )
    assert missing == set()
    assert mask.tolist() == [True, False]
    assert weights[0] > weights[1]
    assert rows[0]["low_tail"] is True


def test_tail_alpha_metrics_candidate_gate():
    samples = {
        "normal_features": torch.zeros((2, 4)),
        "intervention_features": torch.ones((2, 4)),
        "normal_actions": torch.zeros((2, 3)),
        "intervention_actions": torch.zeros((2, 3)),
        "target_gaps": torch.full((2,), 0.02),
    }

    class FixedHead(torch.nn.Module):
        max_residual = 0.04

        def forward(self, features):
            if torch.all(features == 0):
                return torch.zeros((features.shape[0], 3))
            return torch.tensor([[0.03, 0.0, 0.0]]).repeat(features.shape[0], 1)

    alpha_rows, objective_rows = tail_alpha_metrics(
        samples=samples,
        meta_rows=[{"row": 0}, {"row": 1}],
        head=FixedHead(),
        alphas=(1.0,),
        near_base_gap_p10=0.005,
        near_base_gap_deficit_mean=0.01,
        near_base_low_tail_fraction=0.5,
        low_tail_gap_threshold=LOW_TAIL_GAP_THRESHOLD,
        low_tail_deficit_threshold=0.02,
    )
    assert alpha_rows[0]["normal_retention_pass"] is True
    assert alpha_rows[0]["tail_lift_pass"] is True
    assert alpha_rows[0]["exact_probe_candidate"] is True
    assert len(objective_rows) == 2


def test_classify_tail_weighted_probe():
    assert (
        classify_tail_weighted_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_low_tail_keys=0,
            candidate_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_tail_weighted_probe_candidate"
    )
    assert (
        classify_tail_weighted_probe(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_low_tail_keys=2,
            candidate_count=1,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_tail_weighted_probe_low_tail_join_blocked"
    )
