import numpy as np
import pytest

from autodrift.body_feedback_observability_audit import (
    H1_BODY_ONLY,
    P0_CURRENT_BASELINE,
    PASSENGER_BODY_RESPONSE,
    PASSENGER_BODY_SCENE,
    BODY_FEEDBACK_PROFILE_ORDER,
    build_body_feedback_feature_profiles,
    body_feedback_history_sequence,
    body_feedback_profile_spec_rows,
    find_ambiguous_body_history_pairs,
    summarize_pre_limit_deltas,
    summarize_slip_detection_deltas,
    train_ridge_binary_probe,
)


def test_body_feedback_feature_profiles_use_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    profiles = build_body_feedback_feature_profiles(observations)

    expected_passenger = observations[:, [2, 3, 4]]
    expected_passenger_scene = np.concatenate([observations[:, [2, 3, 4]], observations[:, 25:]], axis=1)
    expected_h1 = np.concatenate([observations[:, [2, 3, 4, 5, 7, 8, 9, 10, 11]], observations[:, 25:]], axis=1)
    expected_p0 = np.concatenate([observations[:, :12], observations[:, 25:]], axis=1)
    np.testing.assert_array_equal(profiles[PASSENGER_BODY_RESPONSE], expected_passenger)
    np.testing.assert_array_equal(profiles[PASSENGER_BODY_SCENE], expected_passenger_scene)
    np.testing.assert_array_equal(profiles[H1_BODY_ONLY], expected_h1)
    np.testing.assert_array_equal(profiles[P0_CURRENT_BASELINE], expected_p0)


def test_body_feedback_history_sequence_preserves_history_axis():
    frames = np.arange(2 * 3 * 85, dtype=np.float32).reshape(2, 3, 85)

    sequence = body_feedback_history_sequence(frames, H1_BODY_ONLY)

    assert sequence.shape == (2, 3, 69)
    np.testing.assert_array_equal(sequence[:, :, :9], frames[:, :, [2, 3, 4, 5, 7, 8, 9, 10, 11]])
    np.testing.assert_array_equal(sequence[:, :, 9:], frames[:, :, 25:])


def test_body_feedback_history_sequence_rejects_unknown_profile():
    with pytest.raises(ValueError, match="unknown body-feedback profile"):
        body_feedback_history_sequence(np.zeros((1, 2, 85), dtype=np.float32), "missing")


def test_body_feedback_profile_rows_mark_h1_and_exclusions():
    rows = {row["profile"]: row for row in body_feedback_profile_spec_rows()}

    assert rows[H1_BODY_ONLY]["feature_count_per_frame"] == 69
    assert rows[PASSENGER_BODY_RESPONSE]["role"] == "post_slip_detection_baseline"
    assert rows[P0_CURRENT_BASELINE]["feature_count_per_frame"] == 72


def test_ridge_binary_probe_reports_auc_for_separable_labels():
    features = np.asarray([[0.0], [0.1], [0.2], [1.0], [1.1], [1.2]], dtype=np.float32)
    labels = np.asarray([False, False, False, True, True, True])
    train_mask = np.asarray([True, True, False, True, True, False])

    result = train_ridge_binary_probe(
        features=features,
        labels=labels,
        train_mask=train_mask,
        target_name="post_slip",
        feature_set=PASSENGER_BODY_RESPONSE,
        ridge=1e-3,
    )

    assert result.status == "ok"
    assert result.test_auc == pytest.approx(1.0)
    assert result.test_balanced_accuracy == pytest.approx(1.0)


def test_summarize_slip_detection_deltas_compares_profiles():
    rows = []
    for profile, auc, balanced in (
        (PASSENGER_BODY_RESPONSE, 0.60, 0.55),
        (PASSENGER_BODY_SCENE, 0.70, 0.65),
        (H1_BODY_ONLY, 0.80, 0.75),
        (P0_CURRENT_BASELINE, 0.82, 0.76),
    ):
        rows.append(
            {
                "target": "post_slip",
                "history_window_steps": 10,
                "history_mode": "raw",
                "feature_set": profile,
                "test_auc": auc,
                "test_balanced_accuracy": balanced,
            }
        )

    summary = summarize_slip_detection_deltas(rows)

    assert len(summary) == 1
    assert summary[0]["passenger_scene_minus_body_auc"] == pytest.approx(0.10)
    assert summary[0]["h1_minus_passenger_scene_auc"] == pytest.approx(0.10)
    assert summary[0]["p0_minus_h1_auc"] == pytest.approx(0.02)


def test_summarize_pre_limit_deltas_compares_profiles():
    rows = []
    for profile, r2, mae_improvement in (
        (PASSENGER_BODY_RESPONSE, 0.05, 0.01),
        (PASSENGER_BODY_SCENE, 0.10, 0.02),
        (H1_BODY_ONLY, 0.25, 0.05),
        (P0_CURRENT_BASELINE, 0.30, 0.07),
    ):
        rows.append(
            {
                "target": "future_yaw_response",
                "history_window_steps": 25,
                "history_mode": "raw",
                "feature_set": profile,
                "test_r2": r2,
                "mae_improvement": mae_improvement,
            }
        )

    summary = summarize_pre_limit_deltas(rows)

    assert len(summary) == 1
    assert summary[0]["passenger_scene_minus_body_test_r2"] == pytest.approx(0.05)
    assert summary[0]["h1_minus_passenger_scene_test_r2"] == pytest.approx(0.15)
    assert summary[0]["p0_minus_h1_test_r2"] == pytest.approx(0.05)


def test_find_ambiguous_body_history_pairs_exports_close_feature_large_target_pairs():
    features = np.asarray(
        [
            [0.0, 0.0],
            [0.01, 0.01],
            [2.0, 2.0],
            [2.1, 2.1],
        ],
        dtype=np.float32,
    )
    targets = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [3.0, 3.0, 3.0],
            [0.1, 0.1, 0.1],
            [0.2, 0.2, 0.2],
        ],
        dtype=np.float32,
    )
    sample_rows = [
        {
            "episode": index,
            "seed": 100 + index,
            "step": 5,
            "sample_phase": "pre_limit_nonpost",
            "future_braking_deceleration": float(targets[index, 0]),
            "future_yaw_response": float(targets[index, 1]),
            "future_lateral_accel_response": float(targets[index, 2]),
        }
        for index in range(4)
    ]

    pairs, summary = find_ambiguous_body_history_pairs(
        features=features,
        targets=targets,
        sample_rows=sample_rows,
        seed=7,
        feature_quantile=0.34,
        target_quantile=0.50,
        max_pairs=3,
    )

    assert summary["pairs_found"] >= 1
    assert pairs[0]["sample_i"] == 0
    assert pairs[0]["sample_j"] == 1
    assert pairs[0]["target_distance"] > pairs[0]["feature_distance"]


def test_body_feedback_profile_order_is_stable():
    assert BODY_FEEDBACK_PROFILE_ORDER == (
        PASSENGER_BODY_RESPONSE,
        PASSENGER_BODY_SCENE,
        H1_BODY_ONLY,
        P0_CURRENT_BASELINE,
    )
