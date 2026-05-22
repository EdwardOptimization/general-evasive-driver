import numpy as np
import pytest

from autodrift.driver_like_input_profile_audit import (
    P0_CURRENT_BASELINE,
    P1_DRIVER_LIKE_MINIMAL,
    P2_DRIVER_LIKE_NO_STEERING_FEEL,
    P3_DRIVER_LIKE_RAW_WHEEL,
    P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
    build_driver_like_feature_profiles,
    profile_spec_rows,
    summarize_profile_deltas,
)


def test_build_driver_like_feature_profiles_uses_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    profiles = build_driver_like_feature_profiles(observations)

    np.testing.assert_array_equal(profiles[P0_CURRENT_BASELINE], np.concatenate([observations[:, :12], observations[:, 25:]], axis=1))
    expected_p1 = np.concatenate([observations[:, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    expected_p2 = np.concatenate([observations[:, [2, 3, 4, 5, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    expected_p3 = np.concatenate([observations[:, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]], observations[:, 25:]], axis=1)
    expected_p4 = np.concatenate([observations[:, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]], observations[:, 25:]], axis=1)
    np.testing.assert_array_equal(profiles[P1_DRIVER_LIKE_MINIMAL], expected_p1)
    np.testing.assert_array_equal(profiles[P2_DRIVER_LIKE_NO_STEERING_FEEL], expected_p2)
    np.testing.assert_array_equal(profiles[P3_DRIVER_LIKE_RAW_WHEEL], expected_p3)
    np.testing.assert_array_equal(profiles[P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL], expected_p4)


def test_build_driver_like_feature_profiles_supports_history_windows():
    observations = np.arange(170, dtype=np.float32).reshape(1, 170)
    frame0 = observations[:, :85]
    frame1 = observations[:, 85:]

    profiles = build_driver_like_feature_profiles(observations)

    expected_p1 = np.concatenate(
        [
            frame0[:, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
            frame0[:, 25:],
            frame1[:, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
            frame1[:, 25:],
        ],
        axis=1,
    )
    np.testing.assert_array_equal(profiles[P1_DRIVER_LIKE_MINIMAL], expected_p1)


def test_build_driver_like_feature_profiles_rejects_partial_frame():
    with pytest.raises(ValueError, match="85-value"):
        build_driver_like_feature_profiles(np.zeros((3, 86), dtype=np.float32))


def test_profile_spec_rows_record_missing_sensor_limitations():
    rows = profile_spec_rows()
    by_profile = {row["profile"]: row for row in rows}

    assert by_profile[P1_DRIVER_LIKE_MINIMAL]["feature_count_per_frame"] == 70
    assert "steering_torque_or_eps_current" in by_profile[P1_DRIVER_LIKE_MINIMAL]["missing_intended_channels"]
    assert by_profile[P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL]["feature_count_per_frame"] == 74


def test_summarize_profile_deltas_compares_driver_like_profiles():
    rows = []
    for feature_set, test_r2, mae_improvement in (
        (P0_CURRENT_BASELINE, 0.10, 0.20),
        (P1_DRIVER_LIKE_MINIMAL, 0.15, 0.25),
        (P2_DRIVER_LIKE_NO_STEERING_FEEL, 0.12, 0.22),
        (P3_DRIVER_LIKE_RAW_WHEEL, 0.18, 0.28),
        (P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL, 0.17, 0.27),
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

    summary = summarize_profile_deltas(rows)

    assert len(summary) == 1
    assert summary[0]["p1_minus_p0_test_r2"] == pytest.approx(0.05)
    assert summary[0]["steer_proxy_p1_minus_p2_test_r2"] == pytest.approx(0.03)
    assert summary[0]["raw_wheel_p3_minus_p1_test_r2"] == pytest.approx(0.03)
    assert summary[0]["vparallel_p4_minus_p3_test_r2"] == pytest.approx(-0.01)
