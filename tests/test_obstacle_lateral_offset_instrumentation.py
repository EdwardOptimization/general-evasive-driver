import numpy as np

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig


def _reset_lateral_offset(offset: float) -> tuple[float, tuple[int, ...]]:
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(10.0, 10.0),
            obstacle_relative_velocity_mode="zero",
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(24.0, 24.0),
                half_width_range=(0.75, 0.75),
                lateral_offset_range=(offset, offset),
                allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
                max_sample_attempts=1,
            ),
        )
    )
    obs, info = env.reset(seed=2280)
    return float(info["obstacle_lateral_offset"]), tuple(obs.shape)


def test_obstacle_lateral_offset_config_defaults_to_centerline() -> None:
    assert ObstacleTaskConfig().lateral_offset_range == (0.0, 0.0)

    lateral, obs_shape = _reset_lateral_offset(0.0)

    assert abs(lateral) < 1e-9
    assert obs_shape == (72,)


def test_obstacle_lateral_offset_config_accepts_positive_and_negative_offsets() -> None:
    config = build_env_config(
        {
            "obstacle": {
                "enabled": True,
                "lateral_offset_range": [-1.25, -1.25],
            }
        }
    )
    assert config.obstacle.lateral_offset_range == (-1.25, -1.25)

    left_lateral, left_shape = _reset_lateral_offset(1.2)
    right_lateral, right_shape = _reset_lateral_offset(-1.2)

    assert np.isclose(left_lateral, 1.2, atol=1e-9)
    assert np.isclose(right_lateral, -1.2, atol=1e-9)
    assert left_shape == right_shape == (72,)


def test_obstacle_lateral_offset_range_must_be_ordered() -> None:
    try:
        ObstacleTaskConfig(lateral_offset_range=(1.0, -1.0))
    except ValueError as exc:
        assert "lateral_offset_range" in str(exc)
    else:  # pragma: no cover - defensive branch.
        raise AssertionError("expected unordered lateral_offset_range to fail")
