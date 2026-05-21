import numpy as np
import pytest

from autodrift.input_observability_audit import (
    P0_NO_WHEEL_RESPONSE_CONTEXT,
    P0_RESPONSE_ONLY,
    P1_RESPONSE_ONLY,
    P1_WHEEL_RESPONSE_CONTEXT,
    WHEEL_ONLY,
    build_input_feature_profiles,
    summarize_profile_gains,
    train_ridge_regression_probe,
)
from autodrift.input_observability_audit import RegressionProbeResult


def test_build_input_feature_profiles_uses_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    profiles = build_input_feature_profiles(observations)

    np.testing.assert_array_equal(profiles[P0_NO_WHEEL_RESPONSE_CONTEXT], np.concatenate([observations[:, :12], observations[:, 25:]], axis=1))
    np.testing.assert_array_equal(profiles[P1_WHEEL_RESPONSE_CONTEXT], observations)
    np.testing.assert_array_equal(profiles[P0_RESPONSE_ONLY], observations[:, :12])
    np.testing.assert_array_equal(profiles[P1_RESPONSE_ONLY], observations[:, :25])
    np.testing.assert_array_equal(profiles[WHEEL_ONLY], observations[:, 12:25])


def test_build_input_feature_profiles_rejects_non_wheel_frame():
    with pytest.raises(ValueError, match="wheel-response observations"):
        build_input_feature_profiles(np.zeros((3, 24), dtype=np.float32))


def test_train_ridge_regression_probe_beats_baseline_on_linear_target():
    rng = np.random.default_rng(7)
    features = rng.normal(size=(40, 3)).astype(np.float32)
    targets = 2.0 * features[:, 0] - 0.5 * features[:, 2] + 0.1
    train_mask = np.zeros(40, dtype=bool)
    train_mask[:30] = True

    result = train_ridge_regression_probe(
        features=features,
        targets=targets.astype(np.float32),
        train_mask=train_mask,
        target_name="linear",
        feature_set="features",
    )

    assert result.status == "ok"
    assert result.test_r2 > 0.99
    assert result.mae_improvement > 0.0


def test_summarize_profile_gains_reports_p1_minus_p0():
    results = [
        RegressionProbeResult("future_braking_deceleration", P0_NO_WHEEL_RESPONSE_CONTEXT, 10, 5, 0.2, 0.1, 1.0, 1.2, 0.2),
        RegressionProbeResult("future_braking_deceleration", P1_WHEEL_RESPONSE_CONTEXT, 10, 5, 0.5, 0.4, 0.7, 1.2, 0.5),
        RegressionProbeResult("future_braking_deceleration", P0_RESPONSE_ONLY, 10, 5, 0.1, 0.0, 1.1, 1.2, 0.1),
        RegressionProbeResult("future_braking_deceleration", P1_RESPONSE_ONLY, 10, 5, 0.3, 0.2, 0.9, 1.2, 0.3),
    ]

    rows = summarize_profile_gains(results)

    assert len(rows) == 1
    assert rows[0]["target"] == "future_braking_deceleration"
    assert rows[0]["p1_minus_p0_test_r2"] == pytest.approx(0.3)
    assert rows[0]["p1_response_minus_p0_response_test_r2"] == pytest.approx(0.2)
