from pathlib import Path

import numpy as np
import torch

from autodrift.outcome_intervention_optimize import _trainable_parameters, optimize_outcome_intervention
from autodrift.train_ppo import ActorCritic


def _write_checkpoint(path):
    torch.manual_seed(11)
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
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


def test_optimize_outcome_intervention_writes_before_after_artifacts(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((12, 72), dtype=np.float32),
        preferred_hidden=np.zeros((12, 8), dtype=np.float32),
        rejected_hidden=np.ones((12, 8), dtype=np.float32),
        preferred_action=np.zeros((12, 3), dtype=np.float32),
        weight=np.ones(12, dtype=np.float32),
    )
    init_checkpoint = tmp_path / "init.pt"
    _write_checkpoint(init_checkpoint)

    summary, train_metrics, policy_summary = optimize_outcome_intervention(
        init_checkpoint=init_checkpoint,
        snippet_npz=snippet_path,
        device="cpu",
        steps=6,
        batch_size=4,
        learning_rate=1e-3,
        logprob_margin=0.05,
        seed=5,
        freeze_log_std=True,
        grad_clip_norm=1.0,
        log_interval=2,
        run_dir=tmp_path / "run",
        eval_batch_size=4,
        eval_batches=3,
        eval_seed=7,
    )

    assert (tmp_path / "run" / "optimized_checkpoint.pt").exists()
    assert (tmp_path / "run" / "summary.json").exists()
    assert (tmp_path / "run" / "train_metrics.csv").exists()
    assert list(policy_summary["policy"]) == ["before", "after"]
    assert len(train_metrics) >= 2
    assert np.isfinite(summary["before_loss_mean"])
    assert np.isfinite(summary["after_loss_mean"])
    assert summary["optimized_checkpoint"].name == "optimized_checkpoint.pt"


def test_actor_coupling_train_scope_excludes_response_gru():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")

    params = _trainable_parameters(model, freeze_log_std=True, train_scope="actor_coupling")
    param_ids = {id(parameter) for parameter in params}

    assert id(list(model.response_encoder.parameters())[0]) not in param_ids
    assert id(list(model.online_gru_cell.parameters())[0]) not in param_ids
    assert id(list(model.context_encoder.parameters())[0]) not in param_ids
    assert id(list(model.response_context_fusion.parameters())[0]) in param_ids
    assert id(list(model.actor_mean.parameters())[0]) in param_ids
    assert id(model.log_std) not in param_ids


def test_optimize_outcome_intervention_with_action_anchor_records_anchor_metrics(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((8, 72), dtype=np.float32),
        preferred_hidden=np.zeros((8, 8), dtype=np.float32),
        rejected_hidden=np.ones((8, 8), dtype=np.float32),
        preferred_action=np.zeros((8, 3), dtype=np.float32),
        weight=np.ones(8, dtype=np.float32),
    )
    init_checkpoint = tmp_path / "init.pt"
    _write_checkpoint(init_checkpoint)

    summary, train_metrics, _ = optimize_outcome_intervention(
        init_checkpoint=init_checkpoint,
        snippet_npz=snippet_path,
        device="cpu",
        steps=3,
        batch_size=4,
        learning_rate=1e-3,
        logprob_margin=0.05,
        seed=5,
        freeze_log_std=True,
        grad_clip_norm=1.0,
        log_interval=1,
        run_dir=tmp_path / "run",
        eval_batch_size=4,
        eval_batches=2,
        eval_seed=7,
        action_anchor_checkpoint=init_checkpoint,
        action_anchor_env_config=Path("configs/ppo_m24_human_view_gru_driver.json"),
        action_anchor_coef=0.1,
        action_anchor_episodes=2,
        action_anchor_seed=123,
        action_anchor_horizon_steps=1,
        action_anchor_sample_stride=8,
        action_anchor_max_samples=8,
        action_anchor_batch_size=4,
    )

    assert np.isfinite(summary["before_action_anchor_mse"])
    assert np.isfinite(summary["after_action_anchor_mse"])
    assert "action_anchor_loss" in train_metrics


def test_optimize_outcome_intervention_with_snippet_action_anchor_records_anchor_metrics(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((8, 72), dtype=np.float32),
        preferred_hidden=np.zeros((8, 8), dtype=np.float32),
        rejected_hidden=np.ones((8, 8), dtype=np.float32),
        preferred_action=np.zeros((8, 3), dtype=np.float32),
        weight=np.ones(8, dtype=np.float32),
    )
    init_checkpoint = tmp_path / "init.pt"
    _write_checkpoint(init_checkpoint)

    summary, train_metrics, _ = optimize_outcome_intervention(
        init_checkpoint=init_checkpoint,
        snippet_npz=snippet_path,
        device="cpu",
        steps=3,
        batch_size=4,
        learning_rate=1e-3,
        logprob_margin=0.05,
        seed=5,
        freeze_log_std=True,
        grad_clip_norm=1.0,
        log_interval=1,
        run_dir=tmp_path / "run",
        eval_batch_size=4,
        eval_batches=2,
        eval_seed=7,
        snippet_action_anchor_checkpoint=init_checkpoint,
        snippet_action_anchor_coef=0.1,
        snippet_action_anchor_batch_size=4,
    )

    assert summary["before_action_anchor_mse"] is None
    assert summary["after_action_anchor_mse"] is None
    assert np.isfinite(summary["before_snippet_action_anchor_mse"])
    assert np.isfinite(summary["after_snippet_action_anchor_mse"])
    assert summary["before_snippet_action_anchor_mse"] == 0.0
    assert "snippet_action_anchor_loss" in train_metrics
    assert (train_metrics["snippet_action_anchor_coef"] == 0.1).all()
