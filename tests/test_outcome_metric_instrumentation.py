import math

import numpy as np

from autodrift.outcome_metric_instrumentation import (
    compute_episode_outcome_metrics,
    hidden_dynamics_aggregate_rows,
    outcome_metric_aggregate_fields,
    profile_hidden_dynamics_worst_rows,
)


def _info(
    step: int,
    *,
    beta: float = 0.05,
    yaw_rate: float = 0.2,
    speed: float = 8.0,
    lateral_error: float = 0.2,
    track_width: float = 5.0,
    passed: bool = False,
    collision: bool = False,
    margin: float = 1.0,
    termination_reason: str = "",
) -> dict:
    return {
        "step": step,
        "dt": 0.1,
        "track_width": track_width,
        "beta": beta,
        "yaw_rate": yaw_rate,
        "speed": speed,
        "lateral_error": lateral_error,
        "obstacle_passed_raw": passed,
        "obstacle_completed": passed,
        "collision": collision,
        "min_clearance_margin": margin,
        "termination_reason": termination_reason,
    }


def test_recovery_metrics_use_stable_hold_ending_at_obstacle_pass() -> None:
    rows = [_info(step, passed=step >= 5) for step in range(1, 7)]

    metrics = compute_episode_outcome_metrics(rows, default_dt=0.1, default_track_width=5.0)

    assert metrics["first_obstacle_pass_step"] == 5
    assert metrics["first_recovery_step"] == 5
    assert metrics["recovery_success"] is True
    assert metrics["recovery_time_proxy"] == 0.0
    assert metrics["controlled_drift_recovery_success"] is True
    assert metrics["drift_used"] is False


def test_collision_and_off_track_severity_metrics_are_logging_only_scores() -> None:
    rows = [
        _info(1, margin=0.4),
        _info(2, beta=0.4, yaw_rate=2.0, speed=10.0, collision=True, margin=-0.2),
        _info(3, lateral_error=5.4, termination_reason="off_track", margin=-0.2),
    ]

    metrics = compute_episode_outcome_metrics(rows, default_dt=0.1, default_track_width=5.0)

    assert metrics["impact_speed_proxy"] == 10.0
    assert metrics["impact_beta_abs"] == 0.4
    assert metrics["impact_yaw_rate_abs"] == 2.0
    assert np.isclose(metrics["impact_severity_proxy"], 11.4)
    assert np.isclose(metrics["collision_mitigation_score"], 11.4)
    assert np.isclose(metrics["max_off_track_overshoot"], 0.4)
    assert np.isclose(metrics["time_to_first_off_track_s"], 0.3)
    assert np.isclose(metrics["off_track_severity_proxy"], 0.4)


def test_post_offtrack_recoverability_window_uses_only_real_post_event_rows() -> None:
    rows = [
        _info(1, lateral_error=0.4, speed=8.0),
        _info(2, lateral_error=5.2, speed=7.8),
        _info(3, lateral_error=0.6, speed=7.7),
        _info(4, lateral_error=0.5, speed=7.8),
        _info(5, lateral_error=0.4, speed=7.9),
        _info(6, lateral_error=0.3, speed=8.0),
        _info(7, lateral_error=0.2, speed=8.1),
    ]

    metrics = compute_episode_outcome_metrics(rows, default_dt=0.1, default_track_width=5.0)

    assert np.isclose(metrics["max_off_track_overshoot"], 0.2)
    assert np.isclose(metrics["time_to_first_off_track_s"], 0.2)
    assert metrics["post_event_speed_mps_available"] is True
    assert np.isclose(metrics["post_event_speed_mps"], 8.1)
    assert metrics["post_event_yaw_rate_abs_available"] is True
    assert np.isclose(metrics["post_event_yaw_rate_abs"], 0.2)
    assert metrics["post_event_offtrack_overshoot_available"] is True
    assert np.isclose(metrics["post_event_offtrack_overshoot"], 0.0)
    assert metrics["recoverability_window_success_available"] is True
    assert metrics["recoverability_window_success"] is True


def test_terminal_event_without_post_rows_keeps_post_event_metrics_unavailable() -> None:
    rows = [
        _info(1, lateral_error=0.4, margin=0.5),
        _info(2, collision=True, margin=-0.1, termination_reason="obstacle_collision"),
    ]

    metrics = compute_episode_outcome_metrics(rows, default_dt=0.1, default_track_width=5.0)

    assert metrics["impact_speed_mps_available"] is True
    assert metrics["post_event_speed_mps_available"] is False
    assert metrics["post_event_yaw_rate_abs_available"] is False
    assert metrics["post_event_offtrack_overshoot_available"] is False
    assert metrics["recoverability_window_success_available"] is False
    assert metrics["recoverability_window_success"] is False


def test_outcome_metric_aggregate_fields_and_hidden_worst_rows() -> None:
    rows = [
        {
            "profile_name": "p0",
            "hidden_dynamics_bucket": "low_mu",
            "success": True,
            "collision": False,
            "termination_reason": "",
            "recovery_success": True,
            "recovery_time_proxy": 0.0,
            "controlled_drift_recovery_success": True,
            "drift_used": True,
            "impact_severity_proxy": math.nan,
            "collision_mitigation_score": 0.0,
            "max_off_track_overshoot": 0.0,
            "off_track_severity_proxy": 0.0,
        },
        {
            "profile_name": "p0",
            "hidden_dynamics_bucket": "high_mu",
            "success": False,
            "collision": True,
            "termination_reason": "obstacle_collision",
            "recovery_success": False,
            "recovery_time_proxy": math.nan,
            "controlled_drift_recovery_success": False,
            "drift_used": False,
            "impact_severity_proxy": 8.0,
            "collision_mitigation_score": 8.0,
            "max_off_track_overshoot": 0.2,
            "off_track_severity_proxy": 0.2,
        },
    ]

    aggregate = outcome_metric_aggregate_fields(rows)
    hidden = hidden_dynamics_aggregate_rows(rows)
    worst = profile_hidden_dynamics_worst_rows(rows)

    assert aggregate["recovery_success_rate"] == 0.5
    assert aggregate["controlled_drift_recovery_success_rate"] == 0.5
    assert aggregate["drift_used_rate"] == 0.5
    assert aggregate["impact_severity_proxy_mean"] == 8.0
    assert len(hidden) == 2
    assert worst == [
        {
            "profile_name": "p0",
            "hidden_dynamics_bucket_count": 2,
            "worst_bucket_success_rate": 0.0,
            "max_bucket_success_rate": 1.0,
            "success_rate_bucket_spread": 1.0,
            "worst_bucket_recovery_success_rate": 0.0,
            "worst_bucket_controlled_drift_recovery_success_rate": 0.0,
            "worst_bucket_collision_rate": 1.0,
            "worst_bucket_off_track_rate": 0.0,
            "diagnostic_only_no_ranking_claim": True,
        }
    ]
