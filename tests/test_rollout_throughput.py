import numpy as np
import pandas as pd

from autodrift.env import DriftEnvConfig
from autodrift.rollout_throughput import parse_int_list, run_throughput_case, summarize


def test_parse_int_list_reads_comma_separated_values():
    assert parse_int_list("1,2,8") == [1, 2, 8]


def test_run_throughput_case_reports_step_rate():
    row = run_throughput_case(
        env_config=DriftEnvConfig(max_steps=4),
        mode="sync",
        num_envs=2,
        rollout_steps=3,
        seed=9,
    )

    assert row["env_steps"] == 6
    assert row["env_steps_per_second"] > 0.0
    assert row["mode"] == "sync"
    assert row["num_envs"] == 2


def test_summarize_rollout_throughput_rows():
    rows = [
        {
            "mode": "sync",
            "num_envs": 2,
            "rollout_steps": 4,
            "seed": 1,
            "env_steps_per_second": 100.0,
            "elapsed_seconds": 0.08,
            "episode_count": 1,
            "termination_count": 0,
        },
        {
            "mode": "sync",
            "num_envs": 2,
            "rollout_steps": 4,
            "seed": 2,
            "env_steps_per_second": 120.0,
            "elapsed_seconds": 0.07,
            "episode_count": 3,
            "termination_count": 1,
        },
    ]

    summary = summarize(rows)

    assert isinstance(summary, pd.DataFrame)
    assert summary.loc[0, "repeats"] == 2
    assert np.isclose(summary.loc[0, "env_steps_per_second_mean"], 110.0)
