import numpy as np
import pytest

from autodrift.driver_like_input_profile_audit import P0_CURRENT_BASELINE, P1_DRIVER_LIKE_MINIMAL
from autodrift.driver_like_speed_cue_audit import (
    P5_DRIVER_LIKE_SPEEDOMETER,
    P6_DRIVER_LIKE_EGO_VELOCITY,
    build_speed_cue_feature_profiles,
    speed_cue_history_sequence,
    speed_cue_profile_spec_rows,
    summarize_speed_cue_deltas,
)


def test_build_speed_cue_feature_profiles_uses_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    profiles = build_speed_cue_feature_profiles(observations)

    expected_p5 = np.concatenate([observations[:, [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    expected_p6 = np.concatenate([observations[:, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    np.testing.assert_array_equal(profiles[P5_DRIVER_LIKE_SPEEDOMETER], expected_p5)
    np.testing.assert_array_equal(profiles[P6_DRIVER_LIKE_EGO_VELOCITY], expected_p6)
    assert profiles[P1_DRIVER_LIKE_MINIMAL].shape[1] == 70
    assert profiles[P0_CURRENT_BASELINE].shape[1] == 72


def test_speed_cue_history_sequence_preserves_history_axis():
    frames = np.arange(2 * 3 * 85, dtype=np.float32).reshape(2, 3, 85)

    sequence = speed_cue_history_sequence(frames, P6_DRIVER_LIKE_EGO_VELOCITY)

    assert sequence.shape == (2, 3, 72)
    np.testing.assert_array_equal(sequence[:, :, :12], frames[:, :, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]])
    np.testing.assert_array_equal(sequence[:, :, 12:], frames[:, :, 25:])


def test_speed_cue_history_sequence_rejects_unknown_profile():
    with pytest.raises(ValueError, match="unknown speed-cue profile"):
        speed_cue_history_sequence(np.zeros((1, 2, 85), dtype=np.float32), "missing")


def test_speed_cue_spec_rows_distinguish_deployable_cues():
    rows = {row["profile"]: row for row in speed_cue_profile_spec_rows()}

    assert rows[P5_DRIVER_LIKE_SPEEDOMETER]["deployable_cues"] == "vx"
    assert rows[P6_DRIVER_LIKE_EGO_VELOCITY]["deployable_cues"] == "vx vy"


def test_summarize_speed_cue_deltas_reports_gap_closure():
    rows = []
    for feature_set, test_r2, mae_improvement in (
        (P0_CURRENT_BASELINE, 0.20, 0.10),
        (P1_DRIVER_LIKE_MINIMAL, 0.05, 0.02),
        (P5_DRIVER_LIKE_SPEEDOMETER, 0.12, 0.06),
        (P6_DRIVER_LIKE_EGO_VELOCITY, 0.22, 0.11),
    ):
        rows.append(
            {
                "target": "future_yaw_response",
                "history_window_steps": 10,
                "history_mode": "raw",
                "feature_set": feature_set,
                "test_r2": test_r2,
                "mae_improvement": mae_improvement,
            }
        )

    summary = summarize_speed_cue_deltas(rows)

    assert len(summary) == 1
    assert summary[0]["p1_minus_p0_test_r2"] == pytest.approx(-0.15)
    assert summary[0]["speedometer_p5_minus_p1_test_r2"] == pytest.approx(0.07)
    assert summary[0]["ego_velocity_p6_minus_p1_test_r2"] == pytest.approx(0.17)
    assert summary[0]["ego_velocity_p6_minus_p0_test_r2"] == pytest.approx(0.02)
