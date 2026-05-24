import numpy as np
import pandas as pd
import torch

from autodrift.bc_capability_repair_smoke import (
    recompute_action_anchor_mse,
    train_head_only_smoke,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


def _synthetic_arrays(row_count=32):
    rng = np.random.default_rng(5980)
    hidden = rng.normal(size=(row_count, 6)).astype(np.float32)
    targets = np.stack(
        [
            hidden[:, 0] * 0.5 + hidden[:, 1] * 0.1,
            hidden[:, 2] * -0.4,
            hidden[:, 3] * 0.2 + hidden[:, 4] * 0.3,
        ],
        axis=1,
    ).astype(np.float32)
    return {
        "student_obs_seq": np.zeros((row_count, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "anchor_action_seq": np.zeros((row_count, 3), dtype=np.float32),
        "capability_target_seq": targets,
        "done_seq": np.zeros((row_count,), dtype=np.bool_),
        "episode_start_seq": np.zeros((row_count,), dtype=np.bool_),
        "seed_seq": np.arange(row_count, dtype=np.int64),
        "episode_id_seq": np.arange(row_count, dtype=np.int64),
        "step_seq": np.arange(row_count, dtype=np.int64),
        "base_hidden_seq": np.zeros((row_count, 6), dtype=np.float32),
        "base_next_hidden_seq": hidden,
    }


def _synthetic_pairs(row_count=32):
    rows = []
    for left in range(row_count // 2):
        right = row_count - left - 1
        rows.append({"left_row": left, "right_row": right})
    return pd.DataFrame(rows)


def test_train_head_only_smoke_reduces_synthetic_losses():
    train_arrays = _synthetic_arrays()
    val_arrays = _synthetic_arrays()
    pairs = _synthetic_pairs()
    device = torch.device("cpu")

    _, _, summary = train_head_only_smoke(
        train_arrays=train_arrays,
        train_pairs=pairs,
        val_arrays=val_arrays,
        val_pairs=pairs,
        hidden_size=6,
        epochs=120,
        learning_rate=0.01,
        rank_loss_weight=0.25,
        seed=5980,
        device=device,
    )

    assert summary["train_final_regression_loss"] < summary["train_initial_regression_loss"]
    assert summary["validation_final_regression_loss"] < summary["validation_initial_regression_loss"]
    assert summary["train_final_rank_loss"] < summary["train_initial_rank_loss"]


def test_recompute_action_anchor_mse_is_zero_for_matching_actions():
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=6,
        actor_encoder="human_view_online_gru",
    )
    device = torch.device("cpu")
    row_count = 3
    arrays = {
        "student_obs_seq": np.zeros((row_count, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "base_hidden_seq": np.zeros((row_count, 6), dtype=np.float32),
        "anchor_action_seq": np.zeros((row_count, 3), dtype=np.float32),
    }
    anchors = []
    from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden

    for obs, hidden in zip(arrays["student_obs_seq"], arrays["base_hidden_seq"], strict=True):
        hidden_t = torch.as_tensor(hidden, dtype=torch.float32).unsqueeze(0)
        action, _ = deterministic_action_from_hidden(model, obs, hidden_t, device)
        anchors.append(action)
    arrays["anchor_action_seq"] = np.stack(anchors).astype(np.float32)

    assert recompute_action_anchor_mse(model, arrays, device=device) == 0.0
