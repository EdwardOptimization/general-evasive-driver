from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from autodrift.l2_teacher_corpus import (
    TEACHER_STACK_ARRAY_NAME,
    export_l2_teacher_corpus,
    extract_current_p0_frame,
    parse_seed_list,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM, PPOConfig, save_training_checkpoint


def _write_l2_teacher_config(path: Path, *, max_steps: int = 3) -> None:
    path.write_text(
        json.dumps(
            {
                "env": {
                    "max_steps": max_steps,
                    "history_length": 4,
                    "action_history_mode": "full",
                    "obstacle_relative_velocity_mode": "zero",
                    "road_lookahead_count": 8,
                    "obstacle_slots": 4,
                    "friction_limited_speed": False,
                    "obstacle": {
                        "enabled": False,
                    },
                    "friction_step": {
                        "enabled": False,
                    },
                }
            }
        ),
        encoding="utf-8",
    )


def _write_l2_teacher_checkpoint(path: Path) -> None:
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM * 4,
        act_dim=3,
        hidden_size=16,
        actor_encoder="temporal_gru",
        actor_history_length=4,
    )
    config = PPOConfig(
        hidden_size=16,
        actor_encoder="temporal_gru",
        actor_history_length=4,
        history_baseline_level="L2_finite_window",
        device="cpu",
    )
    save_training_checkpoint(
        model,
        config,
        {"history_baseline": {"level": "L2_finite_window"}},
        path,
    )


def test_extract_current_p0_frame_uses_current_frame_from_stack() -> None:
    stacked = np.arange(HUMAN_VIEW_OBS_DIM * 4, dtype=np.float32)

    current = extract_current_p0_frame(stacked, history_length=4)

    assert current.shape == (HUMAN_VIEW_OBS_DIM,)
    np.testing.assert_array_equal(current, np.arange(HUMAN_VIEW_OBS_DIM, dtype=np.float32))


def test_extract_current_p0_frame_rejects_noncanonical_student_dim() -> None:
    with pytest.raises(ValueError, match="canonical"):
        extract_current_p0_frame(np.zeros(80 * 4, dtype=np.float32), history_length=4)


def test_parse_seed_list_supports_ranges_and_explicit_values() -> None:
    assert parse_seed_list("18000:18002,18100", seed_start=None, episodes=None) == [
        18000,
        18001,
        18002,
        18100,
    ]
    assert parse_seed_list(None, seed_start=18010, episodes=3) == [18010, 18011, 18012]


def test_export_l2_teacher_corpus_keeps_l2_stack_out_of_student_arrays(tmp_path: Path) -> None:
    config_path = tmp_path / "l2_config.json"
    checkpoint_path = tmp_path / "teacher.pt"
    output_npz = tmp_path / "corpus.npz"
    summary_json = tmp_path / "summary.json"
    episodes_csv = tmp_path / "episodes.csv"
    _write_l2_teacher_config(config_path, max_steps=3)
    _write_l2_teacher_checkpoint(checkpoint_path)

    summary = export_l2_teacher_corpus(
        teacher_checkpoint=checkpoint_path,
        teacher_env_config=config_path,
        seeds=[18000, 18001],
        output_npz=output_npz,
        summary_json=summary_json,
        episodes_csv=episodes_csv,
        device="cpu",
    )

    data = np.load(output_npz)
    assert data["student_obs_seq"].shape[1] == HUMAN_VIEW_OBS_DIM
    assert data["teacher_action_seq"].shape[1] == 3
    assert data["done_seq"].dtype == np.bool_
    assert data["episode_start_seq"].tolist().count(True) == 2
    assert TEACHER_STACK_ARRAY_NAME not in data.files
    assert summary["student_obs_dim"] == HUMAN_VIEW_OBS_DIM
    assert summary["teacher_obs_dim"] == HUMAN_VIEW_OBS_DIM * 4
    assert summary["teacher_stack_stored"] is False
    assert summary["uses_public_frozen_source_rows"] is False
    assert summary["student_input_arrays"] == ["student_obs_seq"]
    assert output_npz.exists()
    assert summary_json.exists()
    assert episodes_csv.exists()
