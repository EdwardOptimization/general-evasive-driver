import numpy as np

from autodrift.env import DriftEnvConfig
from autodrift.hidden_envelope_probe import (
    CURRENT_RESPONSE,
    FULL_OBSERVATION,
    POLICY_FEATURES,
    RESET_POLICY_FEATURES,
    RESET_RESPONSE_HIDDEN,
    RESPONSE_HIDDEN,
    collect_hidden_envelope_dataset,
    response_feature_dim_for_model,
    summarize_hidden_envelope_gains,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_collect_hidden_envelope_dataset_records_policy_and_reset_hidden_features():
    env_config = DriftEnvConfig(max_steps=4, history_length=1, action_history_mode="full")
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    dataset = collect_hidden_envelope_dataset(
        model=model,
        env_config=env_config,
        episodes=2,
        seed=41,
        horizon_steps=2,
        sample_stride=1,
        max_samples=5,
        device=next(model.parameters()).device,
    )

    assert len(dataset.rows) == 5
    assert dataset.features[FULL_OBSERVATION].shape == (5, 72)
    assert dataset.features[CURRENT_RESPONSE].shape == (5, HUMAN_VIEW_RESPONSE_FEATURE_DIM)
    assert dataset.features[POLICY_FEATURES].shape == (5, 8)
    assert dataset.features[RESPONSE_HIDDEN].shape == (5, 8)
    assert dataset.features[RESET_POLICY_FEATURES].shape == (5, 8)
    assert dataset.features[RESET_RESPONSE_HIDDEN].shape == (5, 8)
    assert set(dataset.targets) == {
        "future_braking_deceleration",
        "future_yaw_response",
        "future_lateral_accel_response",
    }
    assert np.isfinite(dataset.features[RESPONSE_HIDDEN]).all()


def test_response_feature_dim_for_human_view_online_gru():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    assert response_feature_dim_for_model(model) == HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_summarize_hidden_envelope_gains_reports_history_lifts():
    rows = [
        {
            "target": "future_yaw_response",
            "feature_set": feature_set,
            "test_r2": test_r2,
            "mae_improvement": mae_improvement,
            "status": "ok",
        }
        for feature_set, test_r2, mae_improvement in [
            (FULL_OBSERVATION, 0.3, 0.1),
            (CURRENT_RESPONSE, 0.2, 0.05),
            (POLICY_FEATURES, 0.4, 0.12),
            (RESPONSE_HIDDEN, 0.35, 0.11),
            (RESET_POLICY_FEATURES, 0.25, 0.08),
            (RESET_RESPONSE_HIDDEN, 0.15, 0.04),
        ]
    ]

    summary = summarize_hidden_envelope_gains(rows)

    assert len(summary) == 1
    assert summary[0]["target"] == "future_yaw_response"
    assert np.isclose(summary[0]["response_hidden_minus_reset_test_r2"], 0.20)
    assert np.isclose(summary[0]["policy_features_minus_reset_test_r2"], 0.15)
    assert np.isclose(summary[0]["response_hidden_minus_reset_mae_improvement"], 0.07)
