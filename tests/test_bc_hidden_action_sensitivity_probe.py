import numpy as np
import pandas as pd
import torch

from autodrift.bc_hidden_action_sensitivity_probe import (
    ALL_VARIANTS,
    build_hidden_action_sensitivity_rows,
    fusion_weight_chunk_summary,
    summarize_hidden_action_rows,
)
from autodrift.matched_history_intervention_gate import RecurrentSnapshot
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_fusion_weight_chunk_summary_reports_three_chunks():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=4,
        actor_encoder="human_view_online_gru",
    )
    assert model.response_context_fusion is not None
    first_layer = model.response_context_fusion[0]
    with torch.no_grad():
        first_layer.weight[:, :4].fill_(1.0)
        first_layer.weight[:, 4:8].fill_(2.0)
        first_layer.weight[:, 8:12].fill_(3.0)

    row = fusion_weight_chunk_summary(model, checkpoint_label="bc")

    assert row["checkpoint_label"] == "bc"
    assert row["chunk_dim"] == 4
    assert row["hidden_chunk_norm"] < row["context_chunk_norm"] < row["interaction_chunk_norm"]
    assert abs(row["hidden_chunk_share"] + row["context_chunk_share"] + row["interaction_chunk_share"] - 1.0) < 1e-6


def test_build_hidden_action_sensitivity_rows_emits_required_variants():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )
    device = next(model.parameters()).device
    left_obs = np.zeros(72, dtype=np.float32)
    right_obs = np.ones(72, dtype=np.float32) * 0.1
    left_hidden = torch.zeros((1, 8), dtype=torch.float32)
    right_hidden = torch.ones((1, 8), dtype=torch.float32) * 0.5
    delayed_hidden = torch.ones((1, 8), dtype=torch.float32) * 0.2
    snapshots = {
        (10, 0): RecurrentSnapshot(seed=10, step=0, observation=left_obs, hidden=torch.ones((1, 8)) * 0.1),
        (10, 4): RecurrentSnapshot(seed=10, step=4, observation=left_obs, hidden=left_hidden),
        (20, 3): RecurrentSnapshot(seed=20, step=3, observation=right_obs, hidden=right_hidden),
        (30, 2): RecurrentSnapshot(seed=30, step=2, observation=right_obs + 0.1, hidden=delayed_hidden),
    }
    pair_rows = pd.DataFrame(
        [
            {
                "checkpoint_label": "bc",
                "source_checkpoint_label": "bc",
                "probe_seed": 5910,
                "target": "future_yaw_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 4,
                "right_step": 3,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
            }
        ]
    )

    rows = build_hidden_action_sensitivity_rows(
        pair_rows=pair_rows,
        snapshots=snapshots,
        model=model,
        checkpoint_label="bc",
        surface="fresh",
        response_dim=HUMAN_VIEW_RESPONSE_FEATURE_DIM,
        delay_steps=4,
        min_action_distance=0.0,
        device=device,
    )
    variant_summary, correlation_summary = summarize_hidden_action_rows(rows)

    assert {row["variant"] for row in rows} == set(ALL_VARIANTS)
    assert all(row["checkpoint_label"] == "bc" for row in rows)
    assert all(row["surface"] == "fresh" for row in rows)
    assert len(variant_summary) == len(ALL_VARIANTS)
    assert len(correlation_summary) == len(ALL_VARIANTS)
