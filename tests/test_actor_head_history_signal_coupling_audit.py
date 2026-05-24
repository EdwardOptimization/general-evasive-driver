import numpy as np
import torch

from autodrift.actor_head_history_signal_coupling_audit import (
    classify_actor_head_coupling_result,
    compute_actor_head_coupling,
    parse_alphas,
)
from autodrift.train_ppo import ActorCritic


def test_parse_alphas_sorts_unique_values():
    assert parse_alphas("4,1,2,1") == (1.0, 2.0, 4.0)


def test_classify_actor_head_coupling_positive_requires_low_alpha_diversity():
    result = classify_actor_head_coupling_result(
        wrong_rows=100,
        wrong_low_alpha_rows=40,
        wrong_high_alpha_rows=80,
        unique_low_alpha_fault_pairs=4,
        wrong_projection_ratio_mean=0.2,
        reset_projection_ratio_mean=0.3,
        wrong_tanh_attenuation_mean=0.8,
        reset_tanh_attenuation_mean=0.8,
        wrong_feature_delta_mean=0.02,
        reset_feature_delta_mean=0.10,
        min_low_alpha_rows=30,
        min_unique_fault_pairs=4,
        projection_ratio_reset_fraction=0.5,
        tanh_attenuation_reset_fraction=0.5,
    )

    assert result == "actor_head_coupling_positive"


def test_classify_actor_head_coupling_projection_washout():
    result = classify_actor_head_coupling_result(
        wrong_rows=100,
        wrong_low_alpha_rows=10,
        wrong_high_alpha_rows=80,
        unique_low_alpha_fault_pairs=2,
        wrong_projection_ratio_mean=0.05,
        reset_projection_ratio_mean=0.2,
        wrong_tanh_attenuation_mean=0.8,
        reset_tanh_attenuation_mean=0.8,
        wrong_feature_delta_mean=0.05,
        reset_feature_delta_mean=0.10,
        min_low_alpha_rows=30,
        min_unique_fault_pairs=4,
        projection_ratio_reset_fraction=0.5,
        tanh_attenuation_reset_fraction=0.5,
    )

    assert result == "actor_head_projection_washout"


def test_compute_actor_head_coupling_reports_alpha_crossing():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")
    obs = np.zeros(72, dtype=np.float32)
    normal_hidden = torch.zeros(1, 16)
    variant_hidden = torch.ones(1, 16) * 0.5

    metrics = compute_actor_head_coupling(
        model=model,
        observation=obs,
        normal_hidden=normal_hidden,
        variant_hidden=variant_hidden,
        device=torch.device("cpu"),
        alphas=(0.0, 1.0, 16.0),
        action_threshold=0.0,
    )

    assert metrics["feature_delta_l2"] >= 0.0
    assert metrics["pre_tanh_delta_l2"] >= 0.0
    assert metrics["action_delta_l2"] >= 0.0
    assert metrics["alpha_to_action_threshold"] == 0.0
    assert "action_l2_at_alpha_16_0" in metrics
