import pytest

from autodrift.driver_like_input_profile_audit import (
    P0_CURRENT_BASELINE,
    P1_DRIVER_LIKE_MINIMAL,
    P2_DRIVER_LIKE_NO_STEERING_FEEL,
    P3_DRIVER_LIKE_RAW_WHEEL,
    P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
)
from autodrift.driver_like_learned_history_probe import aggregate_probe_rows


def test_aggregate_probe_rows_reports_mean_deltas():
    rows = []
    for target, scale in (("future_yaw_response", 1.0), ("future_braking_deceleration", 2.0)):
        rows.append(
            {
                "target": target,
                "history_window_steps": 50,
                "history_mode": "raw",
                "p1_minus_p0_test_r2": 0.1 * scale,
                "p1_minus_p0_mae_improvement": 0.2 * scale,
                "steer_proxy_p1_minus_p2_test_r2": 0.3 * scale,
                "steer_proxy_p1_minus_p2_mae_improvement": 0.4 * scale,
                "raw_wheel_p3_minus_p1_test_r2": 0.5 * scale,
                "raw_wheel_p3_minus_p1_mae_improvement": 0.6 * scale,
                "vparallel_p4_minus_p3_test_r2": 0.7 * scale,
                "vparallel_p4_minus_p3_mae_improvement": 0.8 * scale,
            }
        )

    aggregate = aggregate_probe_rows(rows)

    assert aggregate["mean_p1_minus_p0_test_r2"] == pytest.approx(0.15)
    assert aggregate["mean_p1_minus_p0_mae_improvement"] == pytest.approx(0.30)
    assert aggregate["mean_steer_proxy_p1_minus_p2_test_r2"] == pytest.approx(0.45)
    assert aggregate["mean_raw_wheel_p3_minus_p1_test_r2"] == pytest.approx(0.75)
    assert aggregate["mean_vparallel_p4_minus_p3_mae_improvement"] == pytest.approx(1.20)


def test_profile_names_remain_m143_contract():
    assert len(
        (
            P0_CURRENT_BASELINE,
            P1_DRIVER_LIKE_MINIMAL,
            P2_DRIVER_LIKE_NO_STEERING_FEEL,
            P3_DRIVER_LIKE_RAW_WHEEL,
            P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
        )
    ) == 5
    assert len(
        {
            P0_CURRENT_BASELINE,
            P1_DRIVER_LIKE_MINIMAL,
            P2_DRIVER_LIKE_NO_STEERING_FEEL,
            P3_DRIVER_LIKE_RAW_WHEEL,
            P4_DRIVER_LIKE_RAW_WHEEL_VPARALLEL,
        }
    ) == 5
