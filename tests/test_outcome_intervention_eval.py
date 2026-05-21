import numpy as np
import torch

from autodrift.outcome_intervention_eval import (
    evaluate_policies,
    parse_checkpoint_policy,
)
from autodrift.train_ppo import ActorCritic


def _write_checkpoint(path, *, hidden_bias: float = 0.0):
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    with torch.no_grad():
        model.actor_mean.bias.fill_(hidden_bias)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {
                "actor_encoder": "human_view_online_gru",
                "actor_history_length": 1,
                "action_sequence_horizon": 1,
                "response_prediction_dim": 0,
                "response_prediction_horizon": 1,
                "log_std_init": -1.0,
                "log_std_min": -5.0,
                "log_std_max": -0.5,
            },
        },
        path,
    )


def test_parse_checkpoint_policy_requires_name_and_path():
    name, path = parse_checkpoint_policy("base=/tmp/model.pt")
    assert name == "base"
    assert str(path) == "/tmp/model.pt"


def test_evaluate_policies_writes_fixed_batch_comparable_summary(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((4, 72), dtype=np.float32),
        preferred_hidden=np.zeros((4, 8), dtype=np.float32),
        rejected_hidden=np.ones((4, 8), dtype=np.float32) * 0.2,
        preferred_action=np.zeros((4, 3), dtype=np.float32),
        weight=np.ones(4, dtype=np.float32),
    )
    checkpoint_a = tmp_path / "a.pt"
    checkpoint_b = tmp_path / "b.pt"
    _write_checkpoint(checkpoint_a, hidden_bias=0.0)
    _write_checkpoint(checkpoint_b, hidden_bias=0.1)

    summary, batch_losses = evaluate_policies(
        checkpoint_policies=[("a", checkpoint_a), ("b", checkpoint_b)],
        snippet_npz=snippet_path,
        device="cpu",
        batch_size=2,
        batches=3,
        seed=7,
        logprob_margin=0.05,
    )

    assert list(summary["policy"]) == ["a", "b"]
    assert set(batch_losses["policy"]) == {"a", "b"}
    assert len(batch_losses) == 6
    assert (summary["loss_mean"] >= 0.0).all()
