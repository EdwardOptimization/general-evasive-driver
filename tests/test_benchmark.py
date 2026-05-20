import pandas as pd

from pathlib import Path

from autodrift.benchmark import add_buckets, build_segment_frame, parse_checkpoint_specs, summarize_segments


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


def test_add_buckets_labels_vehicle_road_hidden_params():
    frame = add_buckets(
        pd.DataFrame(
            [
                {
                    "policy": "m7",
                    "seed": 1,
                    "terminated": False,
                    "mu": 0.3,
                    "initial_mu": 0.3,
                    "mass_scale": 1.12,
                    "cg_shift": -0.06,
                    "brake_scale": 0.85,
                    "tire_stiffness_scale": 1.20,
                    "steer_tau_scale": 1.35,
                }
            ]
        )
    )
    row = frame.iloc[0]

    assert str(row["mu_bucket"]) == "low"
    assert str(row["mass_bucket"]) == "heavy"
    assert str(row["cg_bucket"]) == "rear"
    assert str(row["brake_bucket"]) == "weak"
    assert str(row["tire_bucket"]) == "strong"
    assert str(row["steering_tau_bucket"]) == "slow"


def test_parse_checkpoint_specs_uses_named_paths():
    assert parse_checkpoint_specs(["m7a=runs/a.pt", "m7b=runs/b.pt"]) == [
        ("m7a", Path("runs/a.pt"), "none"),
        ("m7b", Path("runs/b.pt"), "none"),
    ]


def test_parse_checkpoint_specs_accepts_observation_ablation():
    assert parse_checkpoint_specs(["m7a_noact=runs/a.pt@zero_action_history"]) == [
        ("m7a_noact", Path("runs/a.pt"), "zero_action_history")
    ]


def test_parse_checkpoint_specs_accepts_shuffled_history_ablation():
    assert parse_checkpoint_specs(["m7a_shuffle=runs/a.pt@shuffled_history"]) == [
        ("m7a_shuffle", Path("runs/a.pt"), "shuffled_history")
    ]
