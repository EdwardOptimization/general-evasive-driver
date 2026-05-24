import numpy as np
import torch

from autodrift.cross_fault_hidden_action_gap_audit import (
    classify_hidden_action_gap_result,
    compute_hidden_action_gaps,
)
from autodrift.train_ppo import ActorCritic


def test_classify_hidden_action_gap_result_positive_requires_rows_and_diversity():
    result = classify_hidden_action_gap_result(
        wrong_rows=100,
        wrong_raw_positive_rows=90,
        wrong_fused_positive_rows=80,
        wrong_action_positive_rows=60,
        wrong_outcome_positive_rows=50,
        wrong_joint_positive_rows=40,
        reset_action_positive_rows=20,
        reset_outcome_positive_rows=10,
        unique_wrong_joint_fault_pairs=4,
        min_positive_rows=30,
        min_unique_fault_pairs=4,
    )

    assert result == "history_incompatibility_positive"


def test_classify_hidden_action_gap_result_fusion_washout():
    result = classify_hidden_action_gap_result(
        wrong_rows=100,
        wrong_raw_positive_rows=90,
        wrong_fused_positive_rows=0,
        wrong_action_positive_rows=0,
        wrong_outcome_positive_rows=0,
        wrong_joint_positive_rows=0,
        reset_action_positive_rows=90,
        reset_outcome_positive_rows=10,
        unique_wrong_joint_fault_pairs=0,
        min_positive_rows=30,
        min_unique_fault_pairs=4,
    )

    assert result == "fusion_washout"


def test_classify_hidden_action_gap_result_reset_disruption_only():
    result = classify_hidden_action_gap_result(
        wrong_rows=100,
        wrong_raw_positive_rows=90,
        wrong_fused_positive_rows=80,
        wrong_action_positive_rows=10,
        wrong_outcome_positive_rows=5,
        wrong_joint_positive_rows=0,
        reset_action_positive_rows=90,
        reset_outcome_positive_rows=10,
        unique_wrong_joint_fault_pairs=0,
        min_positive_rows=30,
        min_unique_fault_pairs=4,
    )

    assert result == "reset_disruption_only"


def test_compute_hidden_action_gaps_uses_recurrent_boundaries():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")
    obs = np.zeros(72, dtype=np.float32)
    normal_hidden = torch.zeros(1, 16)
    variant_hidden = torch.ones(1, 16) * 0.2

    gaps = compute_hidden_action_gaps(
        model=model,
        observation=obs,
        normal_hidden=normal_hidden,
        variant_hidden=variant_hidden,
        device=torch.device("cpu"),
    )

    assert gaps["raw_hidden_l2"] > 0.0
    assert gaps["next_hidden_l2"] >= 0.0
    assert gaps["fused_feature_l2"] >= 0.0
    assert gaps["action_l2"] >= 0.0
    assert "raw_to_next_retention" in gaps
