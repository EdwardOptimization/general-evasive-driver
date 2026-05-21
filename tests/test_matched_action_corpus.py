import numpy as np

from autodrift.env import DriftEnvConfig
from autodrift.matched_action_corpus import (
    build_matched_action_row,
    hybrid_privileged_observation,
    summarize_matched_actions,
    visible_observation_distances,
)


class _Snapshot:
    def __init__(self, observation: np.ndarray, hidden=None):
        self.condition = "test"
        self.seed = 1
        self.step = 20
        self.observation = observation
        self.hidden = hidden
        self.info = {
            "mu": float(observation[-10]) if len(observation) > 72 else 0.5,
            "brake_scale": 1.0,
            "steer_tau_scale": 1.0,
        }
        self.obstacle_distance = 12.0
        self.snapshot_score = 0.0


class _TailPolicy:
    is_online_recurrent = True

    def act_recurrent(self, observation, hidden=None, deterministic=True):
        del hidden, deterministic
        obs = np.asarray(observation, dtype=np.float32)
        action = np.array([obs[-1], obs[-2], obs[-3]], dtype=np.float32)
        return action, 0.0, 0.0, None


def test_visible_observation_distances_ignore_privileged_tail():
    config = DriftEnvConfig(history_length=1, action_history_mode="full")
    source = np.zeros(82, dtype=np.float32)
    paired = np.zeros(82, dtype=np.float32)
    paired[-1] = 5.0
    paired[20] = 0.4

    distances = visible_observation_distances(source, paired, config)

    assert np.isclose(distances["visible_observation_distance"], 0.4)
    assert distances["visible_response_distance"] == 0.0
    assert np.isclose(distances["visible_context_distance"], 0.4)


def test_hybrid_privileged_observation_replaces_only_tail():
    source = np.arange(82, dtype=np.float32)
    paired = np.arange(82, dtype=np.float32) + 100.0

    hybrid = hybrid_privileged_observation(source, paired)

    np.testing.assert_allclose(hybrid[:72], source[:72])
    np.testing.assert_allclose(hybrid[72:], paired[72:])


def test_build_matched_action_row_accepts_privileged_action_divergence():
    config = DriftEnvConfig(history_length=1, action_history_mode="full")
    nominal_obs = np.zeros(82, dtype=np.float32)
    perturbed_obs = np.zeros(82, dtype=np.float32)
    perturbed_obs[-1] = 0.25
    nominal = _Snapshot(nominal_obs)
    perturbed = _Snapshot(perturbed_obs)

    row = build_matched_action_row(
        7,
        nominal,
        perturbed,
        _TailPolicy(),
        config,
        max_visible_distance=0.1,
        max_response_distance=0.1,
        max_context_distance=0.1,
        min_action_distance=0.05,
    )

    assert row["pair_status"] == "paired"
    assert row["accepted_visible_match"]
    assert row["accepted_visible_total"]
    assert row["accepted_response_match"]
    assert row["accepted_context_match"]
    assert row["accepted_action_divergent"]
    assert row["accepted_paired_action_divergent"]
    assert not row["accepted_wrong_history_divergent"]
    assert row["accepted_privileged_packet_divergent"]
    assert row["visible_observation_distance"] == 0.0
    assert row["privileged_tail_distance"] == 0.25
    assert row["max_action_distance"] >= 0.25


def test_summarize_matched_actions_counts_accepted_rows():
    frame = np.array(
        [
            (True, True, True, False, True, 0.1, 0.0, 0.1, 0.2, 0.4, 0.05, 0.03, 0.2, 0.1, 0.4, 0.4),
            (True, False, False, False, False, 0.2, 0.1, 0.17, 0.3, 0.6, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1),
        ],
        dtype=[
            ("accepted_visible_match", bool),
            ("accepted_action_divergent", bool),
            ("accepted_paired_action_divergent", bool),
            ("accepted_wrong_history_divergent", bool),
            ("accepted_privileged_packet_divergent", bool),
            ("visible_observation_distance", float),
            ("visible_context_distance", float),
            ("hidden_state_distance", float),
            ("privileged_tail_distance", float),
            ("paired_action_distance", float),
            ("nominal_wrong_history_action_distance", float),
            ("perturbed_wrong_history_action_distance", float),
            ("nominal_privileged_packet_action_distance", float),
            ("perturbed_privileged_packet_action_distance", float),
            ("max_action_distance", float),
            ("action_divergence_score", float),
        ],
    )

    import pandas as pd

    summary = summarize_matched_actions(pd.DataFrame(frame))

    assert int(summary.loc[0, "pairs"]) == 2
    assert int(summary.loc[0, "accepted_visible_matches"]) == 2
    assert int(summary.loc[0, "accepted_action_divergent_pairs"]) == 1
    assert int(summary.loc[0, "accepted_paired_action_divergent_pairs"]) == 1
    assert int(summary.loc[0, "accepted_wrong_history_divergent_pairs"]) == 0
    assert int(summary.loc[0, "accepted_privileged_packet_divergent_pairs"]) == 1
    assert summary.loc[0, "action_divergent_rate"] == 0.5
    assert summary.loc[0, "privileged_packet_divergent_rate"] == 0.5
