import pandas as pd

from pathlib import Path

from autodrift.benchmark import (
    add_buckets,
    build_segment_frame,
    load_seed_csv,
    parse_checkpoint_specs,
    summarize,
    summarize_segments,
)


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


def test_summarize_reports_clearance_margin_when_available():
    frame = add_buckets(
        pd.DataFrame(
            [
                {
                    "policy": "m7",
                    "seed": 1,
                    "terminated": False,
                    "success": True,
                    "return": 3.0,
                    "lateral_rmse": 0.1,
                    "lateral_peak": 0.2,
                    "beta_abs_error_mean": 0.1,
                    "beta_abs_peak": 0.2,
                    "high_sideslip_fraction": 0.0,
                    "speed_mean": 10.0,
                    "action_rate_mean": 0.1,
                    "collision": False,
                    "obstacle_completed": True,
                    "min_obstacle_clearance": 1.8,
                    "obstacle_collision_radius": 1.7,
                    "min_clearance_margin": 0.1,
                    "plan_horizon": 1,
                    "plan_action_rate_mean": 0.0,
                    "mu": 0.5,
                    "initial_mu": 0.5,
                    "mass_scale": 1.0,
                    "cg_shift": 0.0,
                    "brake_scale": 1.0,
                    "tire_stiffness_scale": 1.0,
                    "steer_tau_scale": 1.0,
                }
            ]
        )
    )

    summary = summarize(frame, ["policy"]).iloc[0]

    assert summary["min_clearance_margin_mean"] == 0.1
    assert summary["min_clearance_margin_min"] == 0.1
    assert summary["obstacle_collision_radius_mean"] == 1.7


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


def test_parse_checkpoint_specs_accepts_response_ablation():
    assert parse_checkpoint_specs(["m8_zero=runs/a.pt@zero_current_response"]) == [
        ("m8_zero", Path("runs/a.pt"), "zero_current_response")
    ]


def test_load_seed_csv_reads_seed_column(tmp_path):
    path = tmp_path / "seeds.csv"
    path.write_text("seed,obstacle_label\n12,aes_feasible\n15,drift_required\n", encoding="utf-8")

    assert load_seed_csv(path) == [12, 15]
