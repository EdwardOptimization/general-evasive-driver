from __future__ import annotations

import numpy as np
import pytest
import torch

from autodrift.intervention_objectives import load_rejected_history_preference_snippets
from autodrift.train_ppo import (
    ActorCritic,
    PPOConfig,
    HUMAN_VIEW_OBS_DIM,
    rejected_history_preference_auxiliary_loss,
    validate_rejected_history_preference_aux_config,
)


def _write_preference_npz(path, *, rows: int = 4, obs_dim: int = HUMAN_VIEW_OBS_DIM, hidden_size: int = 16) -> None:
    rng = np.random.default_rng(123)
    np.savez_compressed(
        path,
        observation=rng.normal(size=(rows, obs_dim)).astype(np.float32),
        preferred_hidden=rng.normal(size=(rows, hidden_size)).astype(np.float32),
        rejected_hidden=rng.normal(size=(rows, hidden_size)).astype(np.float32),
        preferred_action=np.tanh(rng.normal(size=(rows, 2))).astype(np.float32),
        rejected_action=np.tanh(rng.normal(size=(rows, 2))).astype(np.float32),
        preferred_score=np.full(rows, 0.2, dtype=np.float32),
        rejected_score=np.full(rows, -0.1, dtype=np.float32),
        score_delta=np.full(rows, 0.3, dtype=np.float32),
        normal_margin=np.full(rows, 0.05, dtype=np.float32),
        wrong_history_margin=np.full(rows, -0.02, dtype=np.float32),
        margin_floor=np.zeros(rows, dtype=np.float32),
        weight=np.linspace(0.5, 1.0, rows, dtype=np.float32),
        row_id=np.arange(rows, dtype=np.int64),
        group_index=np.zeros(rows, dtype=np.int64),
        target_index=np.zeros(rows, dtype=np.int64),
    )


def test_rejected_history_preference_aux_config_validation(tmp_path):
    snapshot = tmp_path / "preference.npz"
    config = PPOConfig(
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        rejected_history_preference_aux_coef=0.05,
        rejected_history_preference_snapshot_npz=str(snapshot),
        rejected_history_preference_batch_size=4,
    )

    validate_rejected_history_preference_aux_config(config, uses_online_recurrent=True)
    validate_rejected_history_preference_aux_config(PPOConfig(), uses_online_recurrent=False)

    with pytest.raises(ValueError, match="requires online recurrent sequence training"):
        validate_rejected_history_preference_aux_config(
            PPOConfig(
                rejected_history_preference_aux_coef=0.05,
                rejected_history_preference_snapshot_npz=str(snapshot),
            ),
            uses_online_recurrent=False,
        )
    with pytest.raises(ValueError, match="snapshot_npz is required"):
        validate_rejected_history_preference_aux_config(
            PPOConfig(
                actor_encoder="human_view_online_gru",
                recurrent_sequence_training=True,
                rejected_history_preference_aux_coef=0.05,
            ),
            uses_online_recurrent=True,
        )
    with pytest.raises(ValueError, match="batch_size must be positive"):
        validate_rejected_history_preference_aux_config(
            PPOConfig(
                actor_encoder="human_view_online_gru",
                recurrent_sequence_training=True,
                rejected_history_preference_aux_coef=0.05,
                rejected_history_preference_snapshot_npz=str(snapshot),
                rejected_history_preference_batch_size=0,
            ),
            uses_online_recurrent=True,
        )


def test_rejected_history_preference_auxiliary_loss_is_differentiable(tmp_path):
    snapshot = tmp_path / "preference.npz"
    _write_preference_npz(snapshot)
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=2,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
    )
    snippets = load_rejected_history_preference_snippets(
        snapshot,
        device=torch.device("cpu"),
        obs_dim=HUMAN_VIEW_OBS_DIM,
        hidden_size=16,
        act_dim=2,
    )
    config = PPOConfig(
        rejected_history_preference_batch_size=4,
        rejected_history_preference_preferred_logprob_margin=0.05,
        rejected_history_preference_wrong_logprob_margin=0.05,
        rejected_history_preference_wrong_preference_coef=1.0,
    )

    loss = rejected_history_preference_auxiliary_loss(model, snippets, config)
    assert torch.isfinite(loss)
    loss.backward()
    assert any(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in model.parameters()
    )
