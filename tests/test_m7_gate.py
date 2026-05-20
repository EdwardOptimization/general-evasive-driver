import pandas as pd
import pytest

from autodrift.m7_gate import append_seed_csv, compute_gate_summary, max_temporal_probe_lift


def test_compute_gate_summary_passes_when_success_ablation_sideslip_and_probe_pass():
    comparison = pd.DataFrame(
        [
            {"policy": "m5", "success_rate": 0.50},
            {"policy": "m7a", "success_rate": 0.56},
            {"policy": "m7b", "success_rate": 0.54},
        ]
    )
    ablation = pd.DataFrame(
        [
            {"policy": "m7a", "success_rate": 0.56},
            {"policy": "m7a_noact", "success_rate": 0.50},
            {"policy": "m7a_shuffle", "success_rate": 0.49},
            {"policy": "m7b", "success_rate": 0.54},
            {"policy": "m7b_noact", "success_rate": 0.51},
            {"policy": "m7b_shuffle", "success_rate": 0.50},
        ]
    )
    obstacle_labels = pd.DataFrame(
        [
            {"policy": "m7a", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.10},
            {"policy": "m7b", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.12},
        ]
    )
    probe = pd.DataFrame(
        [
            {"target": "mu_bucket", "feature_set": "latent", "test_accuracy": 0.72},
            {"target": "mu_bucket", "feature_set": "shuffled_history_latent", "test_accuracy": 0.65},
        ]
    )

    summary = compute_gate_summary(
        comparison=comparison,
        ablation=ablation,
        obstacle_labels=obstacle_labels,
        m7a_probe=probe,
        m7b_probe=None,
        min_success_delta=0.01,
        min_ablation_drop=0.02,
        max_aes_feasible_high_sideslip=0.15,
        min_probe_temporal_lift=0.02,
    )

    assert summary["status"] == "passed"
    assert summary["checks"]["success_beats_m5"]
    assert summary["checks"]["ablation_drop_present"]
    assert summary["checks"]["aes_feasible_sideslip_ok"]
    assert summary["checks"]["probe_temporal_lift_present"]


def test_compute_gate_summary_flags_missing_temporal_mechanism():
    comparison = pd.DataFrame(
        [
            {"policy": "m5", "success_rate": 0.58},
            {"policy": "m7a", "success_rate": 0.60},
            {"policy": "m7b", "success_rate": 0.60},
        ]
    )
    ablation = pd.DataFrame(
        [
            {"policy": "m7a", "success_rate": 0.60},
            {"policy": "m7a_noact", "success_rate": 0.60},
            {"policy": "m7a_shuffle", "success_rate": 0.60},
            {"policy": "m7b", "success_rate": 0.60},
            {"policy": "m7b_noact", "success_rate": 0.62},
            {"policy": "m7b_shuffle", "success_rate": 0.60},
        ]
    )
    obstacle_labels = pd.DataFrame(
        [
            {"policy": "m7a", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.35},
            {"policy": "m7b", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.20},
        ]
    )
    probe = pd.DataFrame(
        [
            {"target": "mu_bucket", "feature_set": "latent", "test_accuracy": 0.95},
            {"target": "mu_bucket", "feature_set": "shuffled_history_latent", "test_accuracy": 0.96},
        ]
    )

    summary = compute_gate_summary(
        comparison=comparison,
        ablation=ablation,
        obstacle_labels=obstacle_labels,
        m7a_probe=probe,
        m7b_probe=None,
        min_success_delta=0.01,
        min_ablation_drop=0.02,
        max_aes_feasible_high_sideslip=0.15,
        min_probe_temporal_lift=0.02,
    )

    assert summary["status"] == "needs_iteration"
    assert not summary["checks"]["ablation_drop_present"]
    assert not summary["checks"]["aes_feasible_sideslip_ok"]
    assert not summary["checks"]["probe_temporal_lift_present"]


def test_compute_gate_summary_requires_named_driver_when_requested():
    comparison = pd.DataFrame(
        [
            {"policy": "m5", "success_rate": 0.50},
            {"policy": "m7a", "success_rate": 0.70},
            {"policy": "m7b", "success_rate": 0.68},
            {"policy": "m8", "success_rate": 0.51},
        ]
    )
    ablation = pd.DataFrame(
        [
            {"policy": "m7a", "success_rate": 0.70},
            {"policy": "m7a_noact", "success_rate": 0.55},
            {"policy": "m7a_shuffle", "success_rate": 0.55},
            {"policy": "m7b", "success_rate": 0.68},
            {"policy": "m7b_noact", "success_rate": 0.55},
            {"policy": "m7b_shuffle", "success_rate": 0.55},
            {"policy": "m8", "success_rate": 0.51},
            {"policy": "m8_noact", "success_rate": 0.51},
            {"policy": "m8_shuffle", "success_rate": 0.51},
        ]
    )
    obstacle_labels = pd.DataFrame(
        [
            {"policy": "m7a", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.08},
            {"policy": "m7b", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.09},
            {"policy": "m8", "obstacle_label": "aes_feasible", "high_sideslip_fraction_mean": 0.16},
        ]
    )
    probe = pd.DataFrame(
        [
            {"target": "mu_bucket", "feature_set": "latent", "test_accuracy": 0.80},
            {"target": "mu_bucket", "feature_set": "shuffled_history_latent", "test_accuracy": 0.60},
        ]
    )

    summary = compute_gate_summary(
        comparison=comparison,
        ablation=ablation,
        obstacle_labels=obstacle_labels,
        m7a_probe=probe,
        m7b_probe=probe,
        driver_probe=probe,
        required_policy="m8",
        min_success_delta=0.02,
        min_ablation_drop=0.02,
        max_aes_feasible_high_sideslip=0.15,
        min_probe_temporal_lift=0.02,
    )

    assert summary["status"] == "needs_iteration"
    assert summary["metrics"]["selected_policy"] == "m8"
    assert not summary["checks"]["success_beats_m5"]
    assert not summary["checks"]["ablation_drop_present"]
    assert not summary["checks"]["aes_feasible_sideslip_ok"]


def test_max_temporal_probe_lift_uses_best_target_difference():
    frame = pd.DataFrame(
        [
            {"target": "mu_bucket", "feature_set": "latent", "test_accuracy": 0.70},
            {"target": "mu_bucket", "feature_set": "shuffled_history_latent", "test_accuracy": 0.68},
            {"target": "tire_bucket", "feature_set": "latent", "test_accuracy": 0.50},
            {"target": "tire_bucket", "feature_set": "shuffled_history_latent", "test_accuracy": 0.40},
        ]
    )

    assert max_temporal_probe_lift(frame) == pytest.approx(0.10)


def test_append_seed_csv_extends_command_only_when_requested(tmp_path):
    command = ["python", "-m", "autodrift.benchmark"]
    seed_csv = tmp_path / "seeds.csv"

    assert append_seed_csv(command, None) == command
    assert append_seed_csv(command, seed_csv) == command + ["--seed-csv", str(seed_csv)]
