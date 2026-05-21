import numpy as np
import pandas as pd
import torch

from autodrift.matched_history_intervention_gate import (
    ACTION_VARIANTS,
    RecurrentSnapshot,
    build_action_intervention_rows,
    requested_snapshot_steps,
    summarize_action_interventions,
    zero_action_history_observation,
    zero_current_response_observation,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_requested_snapshot_steps_includes_left_delay():
    pairs = pd.DataFrame(
        [
            {
                "left_seed": 10,
                "left_step": 12,
                "right_seed": 20,
                "right_step": 9,
            }
        ]
    )

    requests = requested_snapshot_steps(pairs, delay_steps=5)

    assert requests[10] == {7, 12}
    assert requests[20] == {9}


def test_zero_observation_helpers_only_clear_expected_slots():
    observation = np.arange(20, dtype=np.float32)

    no_response = zero_current_response_observation(observation, response_dim=5)
    no_action = zero_action_history_observation(observation)

    np.testing.assert_allclose(no_response[:5], 0.0)
    np.testing.assert_allclose(no_response[5:], observation[5:])
    assert no_action[9] == 0.0
    assert no_action[10] == 0.0
    assert no_action[11] == 0.0
    np.testing.assert_allclose(no_action[:9], observation[:9])


def test_build_action_intervention_rows_emits_all_variants():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )
    device = next(model.parameters()).device
    left_obs = np.zeros(72, dtype=np.float32)
    right_obs = np.ones(72, dtype=np.float32) * 0.1
    left_hidden = torch.zeros((1, 8), dtype=torch.float32)
    right_hidden = torch.ones((1, 8), dtype=torch.float32) * 0.5
    snapshots = {
        (10, 0): RecurrentSnapshot(seed=10, step=0, observation=left_obs, hidden=left_hidden),
        (10, 4): RecurrentSnapshot(seed=10, step=4, observation=left_obs + 0.02, hidden=left_hidden + 0.2),
        (20, 3): RecurrentSnapshot(seed=20, step=3, observation=right_obs, hidden=right_hidden),
    }
    pair_rows = pd.DataFrame(
        [
            {
                "checkpoint_label": "candidate",
                "probe_seed": 9510,
                "target": "future_yaw_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 4,
                "right_step": 3,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
            }
        ]
    )

    rows = build_action_intervention_rows(
        pair_rows=pair_rows,
        snapshots=snapshots,
        model=model,
        response_dim=HUMAN_VIEW_RESPONSE_FEATURE_DIM,
        delay_steps=4,
        min_action_distance=0.0,
        device=device,
    )
    summary = summarize_action_interventions(rows)

    assert {row["variant"] for row in rows} == set(ACTION_VARIANTS)
    assert all(row["action_distance_above_threshold"] for row in rows)
    assert len(summary) == len(ACTION_VARIANTS)
