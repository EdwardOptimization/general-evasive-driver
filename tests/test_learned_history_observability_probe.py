import numpy as np
import pytest

from autodrift.learned_history_observability_probe import (
    P1_NO_ACTUATOR_ACTUALS_HISTORY,
    P1_NO_COMMANDS_HISTORY,
    P1_NO_IMU_HISTORY,
    P1_NO_WHEEL_HISTORY,
    P0_RESPONSE_HISTORY,
    P1_RESPONSE_HISTORY,
    metric_rows,
    response_history_sequence,
)


def test_response_history_sequence_slices_p0_and_p1_streams():
    frames = np.arange(2 * 3 * 85, dtype=np.float32).reshape(2, 3, 85)

    p0 = response_history_sequence(frames, P0_RESPONSE_HISTORY)
    p1 = response_history_sequence(frames, P1_RESPONSE_HISTORY)

    assert p0.shape == (2, 3, 12)
    assert p1.shape == (2, 3, 25)
    np.testing.assert_array_equal(p0, frames[:, :, :12])
    np.testing.assert_array_equal(p1, frames[:, :, :25])


def test_response_history_sequence_slices_ablation_profiles():
    frames = np.arange(2 * 3 * 85, dtype=np.float32).reshape(2, 3, 85)

    no_commands = response_history_sequence(frames, P1_NO_COMMANDS_HISTORY)
    no_actuators = response_history_sequence(frames, P1_NO_ACTUATOR_ACTUALS_HISTORY)
    no_imu = response_history_sequence(frames, P1_NO_IMU_HISTORY)
    no_wheel = response_history_sequence(frames, P1_NO_WHEEL_HISTORY)

    assert no_commands.shape == (2, 3, 22)
    assert no_actuators.shape == (2, 3, 21)
    assert no_imu.shape == (2, 3, 23)
    assert no_wheel.shape == (2, 3, 12)
    np.testing.assert_array_equal(no_wheel, frames[:, :, :12])


def test_response_history_sequence_rejects_unknown_profile():
    frames = np.zeros((2, 3, 85), dtype=np.float32)

    with pytest.raises(ValueError, match="unknown"):
        response_history_sequence(frames, "oracle")


def test_metric_rows_reports_target_metrics():
    train_targets = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32)
    test_targets = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    train_pred = train_targets.copy()
    test_pred = test_targets.copy()

    rows = metric_rows(
        profile="p",
        target_names=("a", "b"),
        train_targets=train_targets,
        test_targets=test_targets,
        train_pred=train_pred,
        test_pred=test_pred,
        history_window_steps=5,
        model_type="unit",
    )

    assert [row["target"] for row in rows] == ["a", "b"]
    assert rows[0]["profile"] == "p"
    assert rows[0]["model_type"] == "unit"
    assert rows[0]["history_window_steps"] == 5
    assert rows[0]["test_r2"] == pytest.approx(1.0)
    assert rows[0]["mae_improvement"] > 0.0
