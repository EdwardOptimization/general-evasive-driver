import numpy as np
import pytest

from autodrift.p0_close_resolution_audit import (
    EXTRA_RAW_WHEEL_W25,
    P0_PLUS_RAW_WHEEL_W25,
    P0_W25,
    P0_W50,
    build_profile_features_by_name,
    evaluate_p0_close_resolution,
    read_p0_close_pair_rows,
    resolution_profile_spec_rows,
    select_profile_sequence,
)


def test_select_profile_sequence_uses_expected_indices():
    observations = np.arange(2 * 85, dtype=np.float32).reshape(2, 85)

    selected = select_profile_sequence(observations, (0, 12, 25))

    np.testing.assert_array_equal(selected, observations[:, [0, 12, 25]])


def test_build_profile_features_by_name_supports_long_history():
    obs25 = np.arange(2 * 25 * 85, dtype=np.float32).reshape(2, 25 * 85)
    obs50 = np.arange(2 * 50 * 85, dtype=np.float32).reshape(2, 50 * 85)

    profiles = build_profile_features_by_name({25: obs25, 50: obs50})

    assert profiles[P0_W25].shape == (2, 25 * 72)
    assert profiles[P0_W50].shape == (2, 50 * 72)
    assert profiles[EXTRA_RAW_WHEEL_W25].shape == (2, 25 * 2)


def test_read_p0_close_pair_rows_filters_surface(tmp_path):
    path = tmp_path / "pairs.csv"
    path.write_text(
        "surface,sample_i,sample_j\n"
        "h1_close_target_divergent,0,1\n"
        "p0_close_target_divergent,2,3\n",
        encoding="utf-8",
    )

    rows = read_p0_close_pair_rows(path)

    assert len(rows) == 1
    assert rows[0]["sample_i"] == "2"


def test_resolution_profile_spec_rows_include_required_candidates():
    rows = {row["profile"]: row for row in resolution_profile_spec_rows()}

    assert rows[P0_W25]["role"] == "base"
    assert rows[P0_W50]["role"] == "long_history_candidate"
    assert rows[P0_PLUS_RAW_WHEEL_W25]["role"] == "full_candidate"
    assert rows[EXTRA_RAW_WHEEL_W25]["role"] == "extra_only"


def test_evaluate_p0_close_resolution_scores_raw_wheel_extra_resolution():
    obs25 = np.zeros((4, 85), dtype=np.float32)
    obs50 = np.zeros((4, 50 * 85), dtype=np.float32)
    obs25[:, 0] = [0.0, 0.01, 2.0, 2.01]  # P0 is close for pair 0-1.
    obs25[:, 2] = [0.0, 0.01, 2.0, 2.01]
    obs25[:, 25] = [0.0, 0.01, 2.0, 2.01]
    obs25[:, 12] = [0.0, 5.0, 0.0, 0.1]  # raw wheel resolves pair 0-1.
    obs25[:, 13] = [0.0, 5.0, 0.0, 0.1]
    for frame in range(50):
        obs50[:, frame * 85 : (frame + 1) * 85] = obs25
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
    }
    pair_rows = [
        {
            "rank": 1,
            "surface": "p0_close_target_divergent",
            "sample_i": 0,
            "sample_j": 1,
            "episode_i": 0,
            "episode_j": 1,
            "step_i": 5,
            "step_j": 5,
        }
    ]

    pair_metrics, summary_rows = evaluate_p0_close_resolution(
        observations_by_window={25: obs25, 50: obs50},
        targets=targets,
        pair_rows=pair_rows,
        min_extra_distance=0.25,
    )

    by_profile = {row["profile"]: row for row in summary_rows}
    assert by_profile[P0_W25]["resolved_fraction"] == pytest.approx(0.0)
    assert by_profile[EXTRA_RAW_WHEEL_W25]["resolved_fraction"] == pytest.approx(1.0)
    raw_pair = [row for row in pair_metrics if row["profile"] == EXTRA_RAW_WHEEL_W25][0]
    assert raw_pair["profile_feature_distance"] > raw_pair["p0_feature_distance"]
