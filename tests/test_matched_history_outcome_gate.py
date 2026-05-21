import numpy as np

from autodrift.matched_history_outcome_gate import (
    OUTCOME_VARIANTS,
    replay_outcome_variant,
    summarize_outcome_interventions,
)
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_summarize_outcome_interventions_reports_normal_better_fraction():
    rows = [
        {
            "checkpoint_label": "candidate",
            "target": "future_yaw_response",
            "variant": "wrong_matched_history",
            "normal_success": True,
            "variant_success": False,
            "success_drop": True,
            "normal_better": True,
            "normal_margin": 0.4,
            "variant_margin": 0.1,
            "margin_gap": 0.3,
            "return": 1.0,
            "collision": True,
            "off_road": False,
            "obstacle_completed": False,
            "first_action_distance": 0.2,
            "action_trajectory_distance_mean": 0.3,
        },
        {
            "checkpoint_label": "candidate",
            "target": "future_yaw_response",
            "variant": "wrong_matched_history",
            "normal_success": True,
            "variant_success": True,
            "success_drop": False,
            "normal_better": False,
            "normal_margin": 0.4,
            "variant_margin": 0.5,
            "margin_gap": -0.1,
            "return": 2.0,
            "collision": False,
            "off_road": False,
            "obstacle_completed": True,
            "first_action_distance": 0.1,
            "action_trajectory_distance_mean": 0.2,
        },
    ]

    summary = summarize_outcome_interventions(rows)

    assert len(summary) == 1
    assert summary[0]["variant"] == "wrong_matched_history"
    assert np.isclose(summary[0]["success_drop_rate"], 0.5)
    assert np.isclose(summary[0]["normal_better_fraction"], 0.5)
    assert np.isclose(summary[0]["margin_gap_mean"], 0.1)


def test_replay_outcome_variant_runs_short_normal_continuation():
    config = DriftEnvConfig(max_steps=3, history_length=1, action_history_mode="full")
    env = AutoDriftEnv(config)
    obs, info = env.reset(seed=123)
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )
    device = next(model.parameters()).device
    snapshot = OutcomeSnapshot(
        seed=123,
        step=0,
        observation=obs.copy(),
        hidden=model.initial_hidden(1, device),
        env=env,
        info=dict(info),
    )

    result, actions = replay_outcome_variant(
        model=model,
        snapshot=snapshot,
        env_config=config,
        variant="normal",
        response_dim=HUMAN_VIEW_RESPONSE_FEATURE_DIM,
        variant_hidden=None,
        normal_first_action=None,
        normal_actions=None,
        max_continuation_steps=2,
        device=device,
    )

    assert "min_clearance_margin" in result
    assert result["variant"] == "normal"
    assert len(actions) >= 1
    assert "wrong_matched_history" in OUTCOME_VARIANTS
