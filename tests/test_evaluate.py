import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import SEGMENT_NAMES, curvature_segment, run_episode


def test_curvature_segment_classifies_signed_curvature():
    assert curvature_segment(0.02) == "left_curve"
    assert curvature_segment(-0.02) == "right_curve"
    assert curvature_segment(0.0) == "near_zero"


def test_episode_row_includes_curvature_segment_metrics():
    env = AutoDriftEnv(
        DriftEnvConfig(
            max_steps=8,
            track_kind="figure_eight",
            speed_range=(4.0, 4.0),
            randomization=RandomizationConfig(mu_range=(1.0, 1.0)),
        )
    )

    row = run_episode(env, "heuristic", seed=23)

    segment_steps = sum(int(row[f"{segment}_steps"]) for segment in SEGMENT_NAMES)
    assert segment_steps == row["steps"]
    assert segment_steps > 0
    assert any(int(row[f"{segment}_steps"]) > 0 for segment in SEGMENT_NAMES)
    assert np.isfinite(row["lateral_rmse"])
