import pandas as pd

from autodrift.benchmark import add_buckets, build_segment_frame, summarize_segments


def test_segment_summary_uses_per_episode_segment_metrics():
    frame = add_buckets(
        pd.DataFrame(
            [
                {
                    "policy": "checkpoint",
                    "seed": 1,
                    "terminated": False,
                    "mu": 0.9,
                    "initial_mu": 0.9,
                    "return": 1.0,
                    "left_curve_steps": 3,
                    "left_curve_lateral_rmse": 0.5,
                    "left_curve_beta_abs_error_mean": 0.2,
                    "left_curve_speed_mean": 6.0,
                    "left_curve_reward_mean": 1.1,
                    "right_curve_steps": 2,
                    "right_curve_lateral_rmse": 0.7,
                    "right_curve_beta_abs_error_mean": 0.3,
                    "right_curve_speed_mean": 5.0,
                    "right_curve_reward_mean": 0.9,
                    "near_zero_steps": 0,
                },
                {
                    "policy": "checkpoint",
                    "seed": 2,
                    "terminated": True,
                    "mu": 0.3,
                    "initial_mu": 0.3,
                    "return": -1.0,
                    "left_curve_steps": 4,
                    "left_curve_lateral_rmse": 1.5,
                    "left_curve_beta_abs_error_mean": 0.4,
                    "left_curve_speed_mean": 4.0,
                    "left_curve_reward_mean": 0.1,
                    "right_curve_steps": 0,
                    "near_zero_steps": 0,
                },
            ]
        )
    )

    segment_frame = build_segment_frame(frame)
    summary = summarize_segments(segment_frame)
    left = summary[summary["segment"] == "left_curve"].iloc[0]
    bucket_summary = summarize_segments(segment_frame, ["policy", "mu_bucket", "segment"])

    assert set(segment_frame["segment"]) == {"left_curve", "right_curve"}
    assert int(left["episodes"]) == 2
    assert int(left["steps_total"]) == 7
    assert left["success_rate"] == 0.5
    assert set(bucket_summary["mu_bucket"].astype(str)) == {"low", "high"}
