import numpy as np
import pytest

from autodrift.ambiguous_history_resolution_audit import (
    EXTRA_P0_MISSING,
    EXTRA_RAW_WHEEL,
    H1_BODY_ONLY,
    H1_PLUS_RAW_WHEEL,
    P0_CURRENT_BASELINE,
    build_resolution_feature_profiles,
    evaluate_resolution_profiles,
    resolution_history_sequence,
    resolution_profile_spec_rows,
)


def test_resolution_feature_profiles_use_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    profiles = build_resolution_feature_profiles(observations)

    expected_h1 = np.concatenate([observations[:, [2, 3, 4, 5, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    expected_p0 = np.concatenate([observations[:, :12], observations[:, 25:]], axis=1)
    expected_raw = np.concatenate(
        [observations[:, [2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13]], observations[:, 25:]],
        axis=1,
    )
    np.testing.assert_array_equal(profiles[H1_BODY_ONLY], expected_h1)
    np.testing.assert_array_equal(profiles[P0_CURRENT_BASELINE], expected_p0)
    np.testing.assert_array_equal(profiles[H1_PLUS_RAW_WHEEL], expected_raw)
    np.testing.assert_array_equal(profiles[EXTRA_P0_MISSING], observations[:, [0, 1, 6]])
    np.testing.assert_array_equal(profiles[EXTRA_RAW_WHEEL], observations[:, [12, 13]])


def test_resolution_history_sequence_preserves_history_axis():
    frames = np.arange(2 * 3 * 85, dtype=np.float32).reshape(2, 3, 85)

    sequence = resolution_history_sequence(frames, EXTRA_P0_MISSING)

    assert sequence.shape == (2, 3, 3)
    np.testing.assert_array_equal(sequence, frames[:, :, [0, 1, 6]])


def test_resolution_history_sequence_rejects_unknown_profile():
    with pytest.raises(ValueError, match="unknown resolution profile"):
        resolution_history_sequence(np.zeros((1, 2, 85), dtype=np.float32), "missing")


def test_resolution_profile_rows_mark_extra_only_roles():
    rows = {row["profile"]: row for row in resolution_profile_spec_rows()}

    assert rows[H1_BODY_ONLY]["role"] == "base"
    assert rows[P0_CURRENT_BASELINE]["role"] == "full_candidate"
    assert rows[EXTRA_RAW_WHEEL]["role"] == "extra_only"


def test_evaluate_resolution_profiles_scores_extra_channel_resolution():
    observations = np.zeros((4, 85), dtype=np.float32)
    observations[:, 2] = [0.0, 0.01, 2.0, 2.01]
    observations[:, 25] = [0.0, 0.01, 2.0, 2.01]
    observations[:, 12] = [0.0, 4.0, 0.0, 0.1]
    observations[:, 13] = [0.0, 4.0, 0.0, 0.1]
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 3.0, 0.0, 0.1], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 3.0, 0.0, 0.1], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 3.0, 0.0, 0.1], dtype=np.float32),
    }
    pair_rows = [
        {
            "rank": 1,
            "sample_i": 0,
            "sample_j": 1,
            "episode_i": 0,
            "episode_j": 1,
            "step_i": 5,
            "step_j": 5,
            "phase_i": "pre_limit_nonpost",
            "phase_j": "pre_limit_nonpost",
        }
    ]

    pair_metrics, summary_rows = evaluate_resolution_profiles(
        observations=observations,
        targets=targets,
        pair_rows=pair_rows,
        min_extra_distance=0.25,
    )

    by_profile = {row["profile"]: row for row in summary_rows}
    assert by_profile[H1_BODY_ONLY]["resolved_fraction"] == pytest.approx(0.0)
    assert by_profile[EXTRA_RAW_WHEEL]["resolved_fraction"] == pytest.approx(1.0)
    raw_pair = [row for row in pair_metrics if row["profile"] == EXTRA_RAW_WHEEL][0]
    assert raw_pair["resolved"] is True
    assert raw_pair["profile_feature_distance"] > raw_pair["h1_feature_distance"]
