import numpy as np
import pytest

from autodrift.capability_step_temporal_sequence_objective import (
    sequence_lengths,
    temporal_preference_loss,
    weighted_mean,
)


def test_sequence_lengths_requires_nonempty_rows():
    mask = np.array([[True, True, False], [True, False, False]])

    assert sequence_lengths(mask).tolist() == [2.0, 1.0]

    with pytest.raises(ValueError):
        sequence_lengths(np.array([[False, False]]))


def test_weighted_mean_rejects_bad_shapes_and_nonfinite_values():
    assert weighted_mean(np.array([1.0, 3.0]), np.array([1.0, 3.0])) == 2.5

    with pytest.raises(ValueError):
        weighted_mean(np.array([1.0]), np.array([1.0, 2.0]))

    with pytest.raises(ValueError):
        weighted_mean(np.array([np.nan]), np.array([1.0]))


def test_temporal_preference_loss_uses_per_step_gap():
    loss = temporal_preference_loss(
        normal_logp=np.array([20.0, 8.0]),
        variant_on_normal_logp=np.array([10.0, 7.0]),
        lengths=np.array([10.0, 1.0]),
        margin=0.05,
    )

    expected = np.logaddexp(0.0, np.array([-0.95, -0.95]))
    assert np.allclose(loss, expected.astype(np.float32))
