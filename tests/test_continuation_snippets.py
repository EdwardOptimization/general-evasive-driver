import numpy as np
import pandas as pd

from autodrift.continuation_snippets import (
    TracePolicySpec,
    build_action_delta_summary,
    parse_policy_specs,
    run_snippets,
)
from autodrift.dynamics import RandomizationConfig
from autodrift.env import DriftEnvConfig


def test_parse_policy_specs_combines_builtin_and_checkpoint_specs():
    specs = parse_policy_specs(["envelope_aes"], ["m37=runs/m37.pt@reset_recurrent_state"])

    assert specs[0].label == "envelope_aes"
    assert specs[0].kind == "envelope_aes"
    assert specs[1].label == "m37"
    assert specs[1].kind == "checkpoint"
    assert specs[1].ablation == "reset_recurrent_state"


def test_build_action_delta_summary_compares_common_step_prefix():
    steps = pd.DataFrame(
        [
            {"seed": 1, "policy": "base", "step": 0, "action_steer": 0.0, "action_throttle": 0.0, "action_brake": 0.0},
            {"seed": 1, "policy": "base", "step": 1, "action_steer": 1.0, "action_throttle": 0.0, "action_brake": 0.0},
            {"seed": 1, "policy": "candidate", "step": 0, "action_steer": 0.0, "action_throttle": 1.0, "action_brake": 0.0},
            {"seed": 1, "policy": "candidate", "step": 1, "action_steer": 1.0, "action_throttle": 2.0, "action_brake": 0.0},
        ]
    )

    summary = build_action_delta_summary(steps, "base").iloc[0]

    assert int(summary["common_steps"]) == 2
    assert np.isclose(summary["first_action_distance"], 1.0)
    assert np.isclose(summary["action_distance_mean"], 1.5)
    assert np.isclose(summary["throttle_delta_mean"], 1.5)


def test_run_snippets_writes_step_episode_and_observation_artifacts(tmp_path):
    env_config = DriftEnvConfig(
        max_steps=3,
        speed_range=(4.0, 4.0),
        randomization=RandomizationConfig(mu_range=(1.0, 1.0)),
    )
    specs = [TracePolicySpec(label="heuristic", kind="heuristic"), TracePolicySpec(label="aeb", kind="aeb")]

    manifest = run_snippets(
        seeds=[10],
        specs=specs,
        env_config=env_config,
        device="cpu",
        baseline_policy="heuristic",
        run_dir=tmp_path / "snippets",
    )

    steps = pd.read_csv(tmp_path / "snippets" / "steps.csv")
    episodes = pd.read_csv(tmp_path / "snippets" / "episodes.csv")
    action_delta = pd.read_csv(tmp_path / "snippets" / "action_delta_summary.csv")
    arrays = np.load(tmp_path / "snippets" / "observations.npz")

    assert manifest["observation_count"] == len(steps)
    assert set(episodes["policy"]) == {"heuristic", "aeb"}
    assert not action_delta.empty
    assert "post_clearance_margin" in steps.columns
    assert "min_clearance_margin" in episodes.columns
    assert arrays["observations"].shape[0] == len(steps)
    assert arrays["actions"].shape == (len(steps), 3)
