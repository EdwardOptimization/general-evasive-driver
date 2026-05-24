from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.l2_teacher_corpus import TEACHER_STACK_ARRAY_NAME
from autodrift.l3_behavior_cloning import episode_slices, load_bc_corpus, train_l3_behavior_cloning
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


def _write_l3_env_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "env": {
                    "history_length": 1,
                    "action_history_mode": "full",
                    "obstacle_relative_velocity_mode": "zero",
                    "road_lookahead_count": 8,
                    "obstacle_slots": 4,
                    "wheel_observation_mode": "none",
                    "include_privileged_params": False,
                }
            }
        ),
        encoding="utf-8",
    )


def _write_corpus(path: Path, *, target_scale: float = 0.25, include_stack: bool = False) -> None:
    obs = np.zeros((6, HUMAN_VIEW_OBS_DIM), dtype=np.float32)
    obs[:, 0] = np.linspace(-0.4, 0.4, num=6, dtype=np.float32)
    actions = np.full((6, 3), target_scale, dtype=np.float32)
    arrays = {
        "student_obs_seq": obs,
        "teacher_action_seq": actions,
        "done_seq": np.asarray([False, False, True, False, False, True], dtype=np.bool_),
        "episode_start_seq": np.asarray([True, False, False, True, False, False], dtype=np.bool_),
        "episode_id_seq": np.asarray([0, 0, 0, 1, 1, 1], dtype=np.int64),
        "step_seq": np.asarray([0, 1, 2, 0, 1, 2], dtype=np.int64),
    }
    if include_stack:
        arrays[TEACHER_STACK_ARRAY_NAME] = np.zeros((6, HUMAN_VIEW_OBS_DIM * 4), dtype=np.float32)
    np.savez_compressed(path, **arrays)


def test_load_bc_corpus_rejects_teacher_stack_leakage(tmp_path: Path) -> None:
    corpus_path = tmp_path / "bad.npz"
    _write_corpus(corpus_path, include_stack=True)

    with pytest.raises(ValueError, match=TEACHER_STACK_ARRAY_NAME):
        load_bc_corpus(corpus_path)


def test_episode_slices_follow_episode_start_mask(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.npz"
    _write_corpus(corpus_path)

    corpus = load_bc_corpus(corpus_path)

    assert episode_slices(corpus) == [(0, 3), (3, 6)]


def test_train_l3_behavior_cloning_writes_p0_l3_checkpoint_and_improves_mse(tmp_path: Path) -> None:
    train_path = tmp_path / "train.npz"
    val_path = tmp_path / "val.npz"
    config_path = tmp_path / "l3_config.json"
    checkpoint_path = tmp_path / "checkpoint.pt"
    metrics_csv = tmp_path / "metrics.csv"
    summary_json = tmp_path / "summary.json"
    _write_corpus(train_path, target_scale=0.25)
    _write_corpus(val_path, target_scale=0.2)
    _write_l3_env_config(config_path)

    summary = train_l3_behavior_cloning(
        train_corpus_path=train_path,
        val_corpus_path=val_path,
        student_env_config=config_path,
        output_checkpoint=checkpoint_path,
        metrics_csv=metrics_csv,
        summary_json=summary_json,
        hidden_size=8,
        epochs=8,
        learning_rate=3e-3,
        seed=563,
        device="cpu",
    )

    assert summary["student_obs_dim"] == HUMAN_VIEW_OBS_DIM
    assert summary["actor_encoder"] == "human_view_online_gru"
    assert summary["teacher_stack_consumed_by_student"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["train_action_mse_delta"] < 0.0
    assert summary["val_action_mse_delta"] < 0.0
    model, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    assert model.obs_dim == HUMAN_VIEW_OBS_DIM
    assert model.actor_encoder == "human_view_online_gru"
    metadata = checkpoint["metadata"]["history_baseline"]
    assert metadata["level"] == "L3_online_gru"
    assert metadata["input_contract"] == "P0_human_view_no_wheel_no_oracle"
    assert metrics_csv.exists()
    assert summary_json.exists()
