import numpy as np
import pandas as pd

from autodrift.env import DriftEnvConfig
from autodrift.hidden_swap_gate import DecisionSnapshot
from autodrift.history_ablation_snippets import (
    build_history_ablation_rows,
    summarize_history_ablation,
)
from autodrift.snapshot_bank_relocation import outcome_intervention_arrays
from autodrift.train_ppo import ActorCritic


def _snapshot() -> DecisionSnapshot:
    return DecisionSnapshot(
        condition="normal",
        seed=7,
        step=12,
        observation=np.zeros(72, dtype=np.float32),
        hidden=None,
        env=None,
        info={"step": 12},
        obstacle_distance=10.0,
        snapshot_score=0.0,
    )


def test_build_history_ablation_rows_exports_reset_outcome_snippet(monkeypatch):
    def fake_replay_continuation(model, snapshot, *, env_config, variant, **kwargs):
        if variant == "normal":
            return (
                {
                    "variant": "normal",
                    "success": True,
                    "return": 5.0,
                    "min_clearance_margin": 0.08,
                    "terminal_reason": "obstacle_completed",
                    "first_steer": 0.2,
                    "first_throttle": -1.0,
                    "first_brake": 0.1,
                },
                [np.array([0.2, -1.0, 0.1], dtype=np.float32)],
            )
        margin = 0.03 if variant == "reset" else 0.07
        return (
            {
                "variant": variant,
                "success": True,
                "return": 4.0,
                "min_clearance_margin": margin,
                "terminal_reason": "obstacle_completed",
                "first_steer": 0.1,
                "first_throttle": -1.0,
                "first_brake": 0.1,
                "first_action_distance": 0.1,
                "action_trajectory_distance_mean": 0.1,
            },
            [np.array([0.1, -1.0, 0.1], dtype=np.float32)],
        )

    monkeypatch.setattr("autodrift.history_ablation_snippets.replay_continuation", fake_replay_continuation)
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")

    rows, replays, examples = build_history_ablation_rows(
        snapshot=_snapshot(),
        model=model,
        env_config=DriftEnvConfig(),
        max_continuation_steps=0,
        min_margin_gap=0.02,
        min_normal_margin=0.0,
        max_normal_margin=None,
        require_normal_success=True,
        outcome_export_min_margin_gap=0.0,
        outcome_export_boundary_margin_scale=0.2,
    )

    reset_row = next(row for row in rows if row["variant"] == "reset")
    zero_row = next(row for row in rows if row["variant"] == "zero_response")
    assert reset_row["accepted_outcome_sensitive"]
    assert not zero_row["accepted_outcome_sensitive"]
    assert len(replays) == 3
    assert len(examples) == 1
    arrays = outcome_intervention_arrays(examples)
    assert arrays["observation"].shape == (1, 72)
    assert arrays["preferred_hidden"].shape == (1, 8)
    assert arrays["rejected_hidden"].shape == (1, 8)
    assert arrays["preferred_action"].shape == (1, 3)


def test_summarize_history_ablation_counts_reset_and_zero_rows():
    frame = pd.DataFrame(
        [
            {"variant": "reset", "accepted_outcome_sensitive": True, "margin_gap": 0.05},
            {"variant": "zero_response", "accepted_outcome_sensitive": False, "margin_gap": 0.01},
        ]
    )
    metadata = pd.DataFrame([{"weight": 0.02}])

    summary = summarize_history_ablation(frame, metadata)

    assert int(summary.loc[0, "candidates"]) == 2
    assert int(summary.loc[0, "accepted_outcome_sensitive_rows"]) == 1
    assert int(summary.loc[0, "reset_accepted_rows"]) == 1
    assert int(summary.loc[0, "zero_response_accepted_rows"]) == 0
    assert np.isclose(summary.loc[0, "outcome_intervention_weight_sum"], 0.02)
