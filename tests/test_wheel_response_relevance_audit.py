import numpy as np
import pytest

from autodrift.latent_probe import ProbeResult
from autodrift.wheel_response_relevance_audit import (
    BODY_PLUS_WHEEL_FEATURE_SET,
    BODY_RESPONSE_FEATURE_SET,
    FULL_OBSERVATION_FEATURE_SET,
    WHEEL_RESPONSE_FEATURE_SET,
    build_wheel_feature_sets,
    summarize_wheel_gains,
)


def test_build_wheel_feature_sets_uses_expected_slices():
    observations = np.arange(170, dtype=np.float32).reshape(2, 85)

    feature_sets = build_wheel_feature_sets(observations)

    np.testing.assert_array_equal(feature_sets[BODY_RESPONSE_FEATURE_SET], observations[:, :12])
    np.testing.assert_array_equal(feature_sets[WHEEL_RESPONSE_FEATURE_SET], observations[:, 12:25])
    np.testing.assert_array_equal(feature_sets[BODY_PLUS_WHEEL_FEATURE_SET], observations[:, :25])
    np.testing.assert_array_equal(feature_sets[FULL_OBSERVATION_FEATURE_SET], observations)


def test_build_wheel_feature_sets_rejects_non_wheel_observation():
    with pytest.raises(ValueError):
        build_wheel_feature_sets(np.zeros((3, 24), dtype=np.float32))


def test_summarize_wheel_gains_compares_body_plus_wheel_to_body():
    results = [
        ProbeResult("mu_bucket", BODY_RESPONSE_FEATURE_SET, 10, 5, "low,high", 0.8, 0.40, 0.30, 0.10),
        ProbeResult("mu_bucket", WHEEL_RESPONSE_FEATURE_SET, 10, 5, "low,high", 0.9, 0.45, 0.30, 0.15),
        ProbeResult("mu_bucket", BODY_PLUS_WHEEL_FEATURE_SET, 10, 5, "low,high", 0.9, 0.60, 0.30, 0.30),
        ProbeResult("mu_bucket", FULL_OBSERVATION_FEATURE_SET, 10, 5, "low,high", 0.95, 0.70, 0.30, 0.40),
    ]

    gains = summarize_wheel_gains(results)

    assert len(gains) == 1
    assert gains[0].target == "mu_bucket"
    assert gains[0].body_plus_wheel_gain == pytest.approx(0.20)
    assert gains[0].wheel_vs_body_delta == pytest.approx(0.05)
