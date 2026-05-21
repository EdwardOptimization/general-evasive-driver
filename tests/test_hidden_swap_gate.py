import numpy as np
import pandas as pd
import torch

from autodrift.env import DriftEnvConfig
from autodrift.hidden_swap_gate import (
    _is_snapshot_candidate,
    action_trajectory_distances,
    build_pair_row,
    hidden_state_distance,
    observation_distances,
    response_feature_indices,
    summarize_replays,
    zero_response_observation,
)


def test_response_feature_indices_cover_each_frame_response_stream():
    config = DriftEnvConfig(history_length=2, action_history_mode="full")

    assert response_feature_indices(config, 144) == list(range(12)) + list(range(72, 84))


def test_zero_response_observation_zeroes_all_response_frames():
    config = DriftEnvConfig(history_length=2, action_history_mode="full")
    observation = np.arange(144, dtype=np.float32)

    transformed = zero_response_observation(observation, config)

    np.testing.assert_allclose(transformed[:12], np.zeros(12, dtype=np.float32))
    np.testing.assert_allclose(transformed[72:84], np.zeros(12, dtype=np.float32))
    np.testing.assert_allclose(transformed[12:72], observation[12:72])
    np.testing.assert_allclose(transformed[84:], observation[84:])


def test_observation_distances_split_response_and_context_terms():
    config = DriftEnvConfig(history_length=1, action_history_mode="full")
    source = np.zeros(72, dtype=np.float32)
    paired = np.zeros(72, dtype=np.float32)
    paired[0] = 3.0
    paired[20] = 4.0

    distances = observation_distances(source, paired, config)

    assert distances["observation_distance"] == 5.0
    assert distances["response_observation_distance"] == 3.0
    assert distances["context_observation_distance"] == 4.0


def test_hidden_state_distance_reports_l2_distance():
    source = torch.zeros(1, 4)
    paired = torch.tensor([[0.0, 3.0, 4.0, 0.0]])

    assert hidden_state_distance(source, paired) == 5.0


def test_action_trajectory_distances_compare_common_prefix():
    actions = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 2.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 3.0], dtype=np.float32),
    ]
    reference = [
        np.array([0.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 0.0], dtype=np.float32),
    ]

    distances = action_trajectory_distances(actions, reference)

    assert distances["action_trajectory_compare_steps"] == 2
    assert np.isclose(distances["action_trajectory_distance_mean"], 1.5)
    assert np.isclose(distances["action_trajectory_distance_rms"], np.sqrt(2.5))
    assert distances["action_trajectory_distance_max"] == 2.0


def test_snapshot_candidate_waits_for_hidden_updates_after_friction():
    info = {
        "step": 12,
        "friction_step_applied": True,
        "friction_step_at": 11,
        "obstacle_distance": 8.0,
    }

    assert not _is_snapshot_candidate(
        info,
        min_probe_steps=1,
        require_friction_step=True,
        min_hidden_updates_after_friction=2,
    )
    assert _is_snapshot_candidate(
        {**info, "step": 13},
        min_probe_steps=1,
        require_friction_step=True,
        min_hidden_updates_after_friction=2,
    )


class _Snapshot:
    def __init__(self, observation: np.ndarray, step: int = 10, hidden=None):
        self.observation = observation
        self.step = step
        self.obstacle_distance = 12.0
        self.snapshot_score = 0.0
        self.hidden = hidden


def test_build_pair_row_marks_visible_match_acceptance():
    config = DriftEnvConfig(history_length=1, action_history_mode="full")
    nominal = _Snapshot(np.zeros(72, dtype=np.float32), hidden=torch.zeros(1, 2))
    perturbed = _Snapshot(np.full(72, 0.01, dtype=np.float32), hidden=torch.ones(1, 2))

    row = build_pair_row(7, nominal, perturbed, config, max_observation_distance=0.20)

    assert row["pair_status"] == "paired"
    assert row["accepted_match"]
    assert row["observation_distance"] < 0.20
    assert np.isclose(row["hidden_state_distance"], np.sqrt(2.0))


def test_summarize_replays_groups_by_condition_variant_and_match_flag():
    frame = pd.DataFrame(
        [
            {
                "source_condition": "nominal",
                "variant": "normal",
                "accepted_match": True,
                "seed": 1,
                "success": True,
                "return": 3.0,
                "terminated": False,
                "collision": False,
                "off_road": False,
                "spin_out": False,
                "obstacle_completed": True,
                "first_action_distance": 0.0,
                "action_trajectory_distance_mean": 0.0,
                "action_trajectory_distance_rms": 0.0,
                "action_trajectory_distance_max": 0.0,
                "action_trajectory_compare_steps": 10,
                "observation_distance": 0.1,
                "response_observation_distance": 0.05,
                "context_observation_distance": 0.09,
                "hidden_state_distance": 0.2,
            },
            {
                "source_condition": "nominal",
                "variant": "normal",
                "accepted_match": True,
                "seed": 2,
                "success": False,
                "return": -1.0,
                "terminated": True,
                "collision": True,
                "off_road": False,
                "spin_out": False,
                "obstacle_completed": False,
                "first_action_distance": 0.0,
                "action_trajectory_distance_mean": 0.2,
                "action_trajectory_distance_rms": 0.3,
                "action_trajectory_distance_max": 0.4,
                "action_trajectory_compare_steps": 5,
                "observation_distance": 0.3,
                "response_observation_distance": 0.10,
                "context_observation_distance": 0.28,
                "hidden_state_distance": 0.4,
            },
        ]
    )

    summary = summarize_replays(frame)

    assert int(summary.loc[0, "pairs"]) == 2
    assert summary.loc[0, "success_rate"] == 0.5
    assert summary.loc[0, "collision_rate"] == 0.5
    assert summary.loc[0, "return_mean"] == 1.0
    assert np.isclose(summary.loc[0, "hidden_state_distance_mean"], 0.3)
    assert np.isclose(summary.loc[0, "action_trajectory_distance_mean"], 0.1)
    assert np.isclose(summary.loc[0, "action_trajectory_distance_rms_mean"], 0.15)
    assert np.isclose(summary.loc[0, "action_trajectory_distance_max_mean"], 0.2)
    assert np.isclose(summary.loc[0, "action_trajectory_compare_steps_mean"], 7.5)
